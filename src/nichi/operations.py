"""
Core operations for the video organizer
Simplified diff feature using external tools like git diff or system diff
"""

import os
import subprocess
import shutil
from typing import List, Optional, Callable

from nichi.converter import VTTToSRTConverter
from nichi.organizer import FileOrganizer
from nichi.timing_adjuster import SRTTimingAdjuster
from nichi.translator import SRTTranslator
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)

from .ui_components import UIComponents
from .user_input import UserInput


class Operations:
    """Core operations for file handling"""

    def __init__(
        self,
        converter: VTTToSRTConverter,
        organizer: FileOrganizer,
        translator: SRTTranslator,
        timing_adjuster: SRTTimingAdjuster,
        console: Console,
    ):
        self.converter = converter
        self.organizer = organizer
        self.translator = translator
        self.timing_adjuster = timing_adjuster
        self.console = console
        self.ui = UIComponents(console)
        self.input_handler = UserInput(console)

    def get_srt_files(self, directory: str) -> List[str]:
        """Get list of SRT files in directory"""
        try:
            items = os.listdir(directory)
            return [item for item in items if item.lower().endswith(".srt")]
        except Exception:
            return []

    def _get_available_diff_tools(self) -> List[tuple]:
        """Get available diff tools on the system"""
        tools = []

        if shutil.which("git"):
            tools.append(("git", "Git difftool"))

        return tools

    def _run_git_diff(self, file1_path: str, file2_path: str):
        """Run git difftool on two files"""
        try:
            cmd = [
                "git",
                "difftool",
                "--no-index",
                "--no-prompt",
                "--tool=vimdiff",
                file1_path,
                file2_path,
            ]
            result = subprocess.run(cmd, check=False, shell=True)
            return True
        except Exception as e:
            self.console.print(Panel(f"Failed to run git difftool: {e}", style="red"))
            return False

    def compare_srt_files(self, working_directory: str):
        """Handle SRT file comparison using git difftool"""
        srt_files = self.get_srt_files(working_directory)
        if len(srt_files) < 2:
            self.console.print(
                Panel("Need at least 2 SRT files to compare", style="yellow")
            )
            return

        if not shutil.which("git"):
            self.console.print(
                Panel(
                    "Git is not available. Please install git to use diff functionality.",
                    style="red",
                )
            )
            return

        # Show file selection table only once at the beginning
        file_table = self.ui.show_file_selection_table(srt_files, "Available SRT Files")
        self.console.print(file_table)

        self.console.print("\nSelect files to compare:")
        first_file = self.input_handler.select_file_from_list(
            srt_files, "First file", default=1
        )
        second_file = self.input_handler.select_file_from_list(
            srt_files, "Second file", default=2
        )

        if not first_file or not second_file:
            return

        # Get file paths
        first_path = os.path.join(working_directory, first_file)
        second_path = os.path.join(working_directory, second_file)

        self.console.print(
            f"\n[bold blue]Opening diff with git difftool...[/bold blue]"
        )

        success = self._run_git_diff(first_path, second_path)

        if not success:
            self.console.print(
                Panel(
                    "Failed to run git difftool. Make sure git is properly configured with a diff tool.",
                    style="red",
                )
            )

    def manage_translation_cache(self):
        """Handle translation cache management"""
        try:
            # Get cache info
            cache_info = self.translator.translator.get_cache_info()

            # Show current cache status
            cache_table = self.ui.show_cache_info_table(cache_info)
            self.console.print(cache_table)

            if cache_info["files"] == 0:
                self.console.print(Panel("Translation cache is empty", style="yellow"))
                return

            # Ask user if they want to clear cache
            if self.input_handler.confirm_cache_clear(cache_info):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                ) as progress:
                    task = progress.add_task(
                        "Clearing translation cache...", total=None
                    )

                    success, message, new_cache_info = (
                        self.translator.translator.clear_cache()
                    )

                    if success:
                        result_table = self.ui.show_cache_clear_results(
                            message, new_cache_info
                        )
                        self.console.print(result_table)
                        self.console.print(
                            Panel("Cache cleared successfully!", style="green")
                        )
                    else:
                        self.console.print(
                            Panel(f"Failed to clear cache: {message}", style="red")
                        )
            else:
                self.console.print(Panel("Cache clearing cancelled", style="yellow"))

        except Exception as e:
            self.console.print(Panel(f"Error managing cache: {e}", style="red"))

    def translate_single_file(self, working_directory: str):
        """Handle translation of a single SRT file with proper progress tracking"""
        srt_files = self.get_srt_files(working_directory)
        if not srt_files:
            self.console.print(Panel("No SRT files found in directory", style="yellow"))
            return

        # Show file selection table
        file_table = self.ui.show_file_selection_table(srt_files, "Available SRT Files")
        self.console.print(file_table)

        # Get file selection
        selected_file = self.input_handler.select_file_from_list(srt_files, "SRT file")
        if not selected_file:
            return

        # Get target language
        languages = self.translator.get_available_languages()
        default_target = self.translator.get_default_target_language()
        target_lang = self.input_handler.prompt_for_language(
            "Enter target language", languages, default_target
        )
        if not target_lang:
            self.console.print(Panel("Translation cancelled", style="yellow"))
            return

        # Get source language
        detected_source = self.translator.detect_source_language(selected_file)
        source_lang = self.input_handler.prompt_for_language(
            "Enter source language (or press enter for auto-detect)",
            languages,
            detected_source,
        )

        # Check if output exists
        expected_output = self.translator.formatter.format_output_filename(
            selected_file, target_lang
        )
        if os.path.exists(os.path.join(working_directory, expected_output)):
            if not self.input_handler.confirm_overwrite(expected_output):
                self.console.print(Panel("Translation cancelled", style="yellow"))
                return

        # Perform translation with progress
        input_path = os.path.join(working_directory, selected_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:

            task = progress.add_task("Preparing translation...", total=100)

            def progress_callback(current: int, total: int):
                if total > 0:
                    completed = int((current / total) * 100)
                    progress.update(
                        task,
                        completed=completed,
                        total=100,
                        description=f"Translating batch {current}/{total}",
                    )

            try:
                total_entries, translated_entries, output_filename = (
                    self.translator.translate_file(
                        input_path,
                        target_lang,
                        source_lang,
                        progress_callback=progress_callback,
                    )
                )
                progress.update(task, completed=100, description="Translation complete")

            except Exception as error:
                progress.stop()
                self.console.print(Panel(f"Translation failed: {error}", style="red"))
                return

        result_table = self.ui.show_translation_results(
            selected_file,
            output_filename,
            total_entries,
            translated_entries,
            target_lang,
            source_lang,
        )
        self.console.print(result_table)
        self.console.print(Panel("Translation completed successfully!", style="green"))

    def adjust_subtitle_timing(self, working_directory: str):
        """Handle subtitle timing adjustment with backup to .old file"""
        srt_files = self.get_srt_files(working_directory)
        if not srt_files:
            self.console.print(Panel("No SRT files found in directory", style="yellow"))
            return

        # Show file selection table
        file_table = self.ui.show_file_selection_table(srt_files, "Available SRT Files")
        self.console.print(file_table)

        # Get file selection
        selected_file = self.input_handler.select_file_from_list(srt_files, "SRT file")
        if not selected_file:
            return

        # Get timing offset
        offset_ms = self.input_handler.prompt_for_timing_offset()
        if offset_ms is None:
            self.console.print(Panel("Timing adjustment cancelled", style="yellow"))
            return

        # Perform timing adjustment
        input_path = os.path.join(working_directory, selected_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Adjusting subtitle timing...", total=None)

            try:
                success, message, entries_processed, backup_filename = (
                    self.timing_adjuster.adjust_srt_file_with_backup(
                        input_path, offset_ms
                    )
                )

                if success:
                    # Show results
                    result_table = self.ui.show_timing_adjustment_results(
                        selected_file,
                        selected_file,  # Same filename (original is now the adjusted version)
                        backup_filename,  # Backup filename
                        entries_processed,
                        offset_ms,
                    )
                    self.console.print(result_table)
                    self.console.print(
                        Panel(
                            f"Timing adjustment completed: {message}\nOriginal backed up as: {backup_filename}",
                            style="green",
                        )
                    )
                else:
                    self.console.print(
                        Panel(f"Timing adjustment failed: {message}", style="red")
                    )

            except Exception as error:
                progress.stop()
                self.console.print(
                    Panel(f"Timing adjustment failed: {error}", style="red")
                )

    def convert_vtt_files(self, working_directory: str):
        """Handle VTT to SRT conversion"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Converting VTT files...", total=None)

            try:
                converted_files = self.converter.convert_directory(working_directory)
            except Exception as error:
                self.console.print(
                    Panel(f"Error during conversion: {error}", style="red")
                )
                return

        if not converted_files:
            self.console.print(
                Panel("No VTT files found or all already converted", style="yellow")
            )
        else:
            result_table = self.ui.show_conversion_results(converted_files)
            self.console.print(result_table)

    def organize_files(self, working_directory: str):
        """Handle file organization"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Organizing files...", total=None)

            try:
                results = self.organizer.organize_directory(working_directory)
            except Exception as error:
                self.console.print(
                    Panel(f"Error during organization: {error}", style="red")
                )
                return

        if not results["created_folders"]:
            self.console.print(
                Panel("No files to organize or folders already exist", style="yellow")
            )
        else:
            folder_table = self.ui.show_organization_results(results["created_folders"])
            self.console.print(folder_table)

    def convert_and_organize(self, working_directory: str):
        """Handle conversion followed by organization"""
        self.console.print(Panel("Step 1: Converting VTT files", style="blue"))
        self.convert_vtt_files(working_directory)

        self.console.print(Panel("Step 2: Organizing files", style="blue"))
        self.organize_files(working_directory)

    def show_available_languages(self):
        """Display available languages for translation"""
        try:
            languages = self.translator.get_available_languages()
            default_lang = self.translator.get_default_target_language()

            lang_table = self.ui.show_languages_table(languages, default_lang)
            self.console.print(lang_table)

        except Exception as e:
            self.console.print(Panel(f"Error getting languages: {e}", style="red"))
