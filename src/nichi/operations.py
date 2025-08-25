"""
Core operations for the video organizer
Handles the main business logic for file operations
"""

import os
from typing import List, Optional, Callable

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

    def __init__(self, converter, organizer, translator, console: Console):
        self.converter = converter
        self.organizer = organizer
        self.translator = translator
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

    def translate_single_file(self, working_directory: str):
        """Handle translation of a single SRT file"""
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
                        description=f"Translating batch",
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

        # Show results
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
