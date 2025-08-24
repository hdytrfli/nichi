"""
Extended Terminal User Interface module
Adds translation functionality to the existing video organizer
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
)
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.align import Align

sys.path.append(str(Path(__file__).parent.parent))

from nichi.converter import VTTToSRTConverter
from nichi.organizer import FileOrganizer
from nichi.translator import SRTTranslator


class ExtendedVideoOrganizerTUI:
    """Extended Rich-based Terminal User Interface with translation capabilities"""

    def __init__(self, working_directory: str):
        self.working_directory = working_directory
        self.converter = VTTToSRTConverter()
        self.organizer = FileOrganizer()
        try:
            self.translator = SRTTranslator()
            self.translation_available = True
            self.default_target_language = self.translator.get_default_target_language()
        except Exception as e:
            self.translation_available = False
            self.translation_error = str(e)
            self.default_target_language = "id"
        self.console = Console()

    def create_header(self) -> Panel:
        """
        Create application header panel with translation status

        Returns:
            Rich Panel with application title and current directory
        """
        title_text = Text("VIDEO FILE ORGANIZER", style="bold blue")
        directory_text = Text(f"Directory: {self.working_directory}", style="dim")

        if self.translation_available:
            status_text = Text(
                f"✅ Translation Ready (Default: {self.default_target_language})",
                style="green",
            )
        else:
            status_text = Text("❌ Translation Unavailable", style="red")

        content = Align.center(f"{title_text}\n{directory_text}\n{status_text}")
        return Panel(content, box=box.SQUARE, style="blue")

    def create_menu(self) -> Panel:
        """
        Create extended menu panel with translation options

        Returns:
            Rich Panel with menu options
        """
        menu_items = [
            "[bold green]1.[/] Convert VTT files to SRT format",
            "[bold green]2.[/] Organize MP4 and subtitle files into folders",
            "[bold green]3.[/] Convert VTT files and then organize",
            "[bold green]4.[/] Show current directory contents",
            "[bold green]5.[/] Change working directory",
        ]

        if self.translation_available:
            menu_items.extend(
                [
                    "[bold cyan]6.[/] Translate SRT file to another language",
                    "[bold cyan]7.[/] Translate all SRT files in directory",
                    "[bold cyan]8.[/] Show available languages for translation",
                ]
            )
            menu_items.append("[bold red]9.[/] Exit")
        else:
            menu_items.extend(
                [
                    "[dim]6. Translate SRT file (Unavailable - Check .env file)",
                    "[dim]7. Translate all SRT files (Unavailable - Check .env file)",
                    "[dim]8. Show available languages (Unavailable - Check .env file)",
                ]
            )
            menu_items.append("[bold red]9.[/] Exit")

        menu_text = "\n".join(menu_items)
        return Panel(menu_text, title="Available Actions", box=box.ROUNDED)

    def get_user_choice(self) -> str:
        """
        Get user menu choice using Rich prompt

        Returns:
            User's menu selection as string
        """
        if self.translation_available:
            choices = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
        else:
            choices = ["1", "2", "3", "4", "5", "9"]

        return Prompt.ask("Enter your choice", choices=choices, default="1")

    def show_directory_contents(self):
        """Display current directory contents in organized tables"""
        try:
            items = os.listdir(self.working_directory)
            if not items:
                self.console.print(Panel("Directory is empty", style="yellow"))
                return

            video_files = [item for item in items if item.lower().endswith(".mp4")]
            vtt_files = [item for item in items if item.lower().endswith(".vtt")]
            srt_files = [
                item for item in items if item.lower().endswith((".srt", ".en.srt"))
            ]
            folders = [
                item
                for item in items
                if os.path.isdir(os.path.join(self.working_directory, item))
            ]

            tables = []

            if video_files:
                video_table = Table(
                    title=f"MP4 Files ({len(video_files)})", box=box.MINIMAL
                )
                video_table.add_column("Filename", style="cyan")
                for video_file in sorted(video_files):
                    video_table.add_row(video_file)
                tables.append(video_table)

            if vtt_files:
                vtt_table = Table(
                    title=f"VTT Files ({len(vtt_files)})", box=box.MINIMAL
                )
                vtt_table.add_column("Filename", style="yellow")
                for vtt_file in sorted(vtt_files):
                    vtt_table.add_row(vtt_file)
                tables.append(vtt_table)

            if srt_files:
                srt_table = Table(
                    title=f"SRT Files ({len(srt_files)})", box=box.MINIMAL
                )
                srt_table.add_column("Filename", style="green")
                for srt_file in sorted(srt_files):
                    srt_table.add_row(srt_file)
                tables.append(srt_table)

            if folders:
                folder_table = Table(title=f"Folders ({len(folders)})", box=box.MINIMAL)
                folder_table.add_column("Folder Name", style="blue")
                for folder in sorted(folders):
                    folder_table.add_row(f"📁 {folder}")
                tables.append(folder_table)

            if tables:
                self.console.print(Columns(tables, equal=True, expand=True))
            else:
                self.console.print(Panel("No relevant files found", style="dim"))

        except PermissionError:
            self.console.print(
                Panel("Permission denied to access directory", style="red")
            )
        except Exception as error:
            self.console.print(Panel(f"Error reading directory: {error}", style="red"))

    def show_available_languages(self):
        """Display available languages for translation"""
        if not self.translation_available:
            self.console.print(
                Panel(f"Translation unavailable: {self.translation_error}", style="red")
            )
            return

        try:
            languages = self.translator.get_available_languages()
            lang_table = Table(
                title="Available Languages for Translation", box=box.ROUNDED
            )
            lang_table.add_column("Code", style="cyan", width=8)
            lang_table.add_column("Language", style="green")
            lang_table.add_column("Default", style="yellow", width=10)

            for code, name in sorted(languages.items()):
                is_default = "✓" if code == self.default_target_language else ""
                lang_table.add_row(code, name, is_default)

            self.console.print(lang_table)

        except Exception as e:
            self.console.print(Panel(f"Error getting languages: {e}", style="red"))

    def get_srt_files(self) -> List[str]:
        """Get list of SRT files in current directory"""
        try:
            items = os.listdir(self.working_directory)
            return [item for item in items if item.lower().endswith(".srt")]
        except Exception:
            return []

    def extract_source_language_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract source language code from filename

        Args:
            filename: SRT filename to analyze

        Returns:
            Language code if found, None otherwise
        """
        import re

        base_name = os.path.splitext(filename)[0]

        patterns = [
            r"\.([a-z]{2})$",  # .en, .id, .fr etc
            r"_([a-z]{2})$",  # _en, _id, _fr etc
            r"\.([a-z]{2,3})$",  # .eng, .ind etc
        ]

        for pattern in patterns:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                lang_code = match.group(1).lower()
                lang_mapping = {
                    "eng": "en",
                    "ind": "id",
                    "spa": "es",
                    "fra": "fr",
                    "deu": "de",
                    "jpn": "ja",
                    "kor": "ko",
                    "chi": "zh",
                }
                return lang_mapping.get(lang_code, lang_code)

        return "en"

    def translate_single_file(self):
        """Handle translation of a single SRT file with progress tracking"""
        if not self.translation_available:
            self.console.print(
                Panel(f"Translation unavailable: {self.translation_error}", style="red")
            )
            return

        srt_files = self.get_srt_files()
        if not srt_files:
            self.console.print(Panel("No SRT files found in directory", style="yellow"))
            return

        file_table = Table(title="Available SRT Files", box=box.ROUNDED)
        file_table.add_column("Index", style="cyan", width=8)
        file_table.add_column("Filename", style="green")

        for i, filename in enumerate(srt_files, 1):
            file_table.add_row(str(i), filename)

        self.console.print(file_table)

        try:
            file_index = (
                IntPrompt.ask(f"Select file (1-{len(srt_files)})", default=1) - 1
            )

            if file_index < 0 or file_index >= len(srt_files):
                self.console.print(Panel("Invalid file selection", style="red"))
                return

            selected_file = srt_files[file_index]

        except (ValueError, KeyboardInterrupt):
            self.console.print(Panel("File selection cancelled", style="yellow"))
            return

        target_lang = Prompt.ask(
            f"Enter target language code",
            default=self.default_target_language,
        )
        if not target_lang:
            self.console.print(Panel("Translation cancelled", style="yellow"))
            return

        detected_source = self.extract_source_language_from_filename(selected_file)
        source_lang = Prompt.ask(
            f"Enter source language code",
            default=detected_source,
        )
        source_lang = source_lang if source_lang else None

        input_path = os.path.join(self.working_directory, selected_file)

        if self.translation_available:
            expected_output = self.translator.formatter.format_output_filename(
                selected_file, target_lang
            )
        else:
            base_name = os.path.splitext(selected_file)[0]
            expected_output = f"{base_name}.{target_lang}.srt"

        if os.path.exists(os.path.join(self.working_directory, expected_output)):
            if not Confirm.ask(
                f"Output file '{expected_output}' may already exist. Continue?"
            ):
                self.console.print(Panel("Translation cancelled", style="yellow"))
                return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:

            batch_task = progress.add_task("Preparing translation...", total=100)

            def progress_callback(current_batch: int, total_batches: int):
                if total_batches > 0:
                    percentage = min(100, int((current_batch / total_batches) * 100))
                    progress.update(
                        batch_task,
                        completed=percentage,
                        description=f"Translating batch {current_batch}/{total_batches}",
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

                progress.update(
                    batch_task, completed=100, description="Translation complete"
                )
                progress.remove_task(batch_task)
                self.console.clear()

                if translated_entries > 0:
                    result_table = Table(title="Translation Complete", box=box.ROUNDED)
                    result_table.add_column("Property", style="cyan")
                    result_table.add_column("Value", style="green")

                    result_table.add_row("Input File", selected_file)
                    result_table.add_row("Output File", output_filename)
                    result_table.add_row("Total Entries", str(total_entries))
                    result_table.add_row("Translated Entries", str(translated_entries))
                    result_table.add_row("Target Language", target_lang)
                    if source_lang:
                        result_table.add_row("Source Language", source_lang)

                    self.console.print(result_table)
                    self.console.print(
                        Panel("✅ Translation completed successfully!", style="green")
                    )
                else:
                    self.console.print(Panel("No entries to translate", style="yellow"))

            except Exception as error:
                progress.remove_task(batch_task)
                self.console.clear()
                self.console.print(
                    Panel(f"Error during translation: {error}", style="red")
                )

    def translate_directory(self):
        """Handle translation of all SRT files in directory with enhanced progress tracking"""
        if not self.translation_available:
            self.console.print(
                Panel(f"Translation unavailable: {self.translation_error}", style="red")
            )
            return

        srt_files = self.get_srt_files()
        if not srt_files:
            self.console.print(Panel("No SRT files found in directory", style="yellow"))
            return

        self.console.print(Panel(f"Found {len(srt_files)} SRT files", style="blue"))

        target_lang = Prompt.ask(
            f"Enter target language code",
            default=self.default_target_language,
        )
        if not target_lang:
            self.console.print(Panel("Translation cancelled", style="yellow"))
            return

        source_lang = Prompt.ask(
            "Enter source language code",
            default="auto-detect",
        )
        source_lang = source_lang if source_lang != "auto-detect" else None

        existing_files = []
        for srt_file in srt_files:
            if self.translation_available:
                output_filename = self.translator.formatter.format_output_filename(
                    srt_file, target_lang
                )
            else:
                base_name = os.path.splitext(srt_file)[0]
                output_filename = f"{base_name}.{target_lang}.srt"

            if os.path.exists(os.path.join(self.working_directory, output_filename)):
                existing_files.append(output_filename)

        if existing_files:
            self.console.print(
                Panel(
                    f"Found {len(existing_files)} existing translated files",
                    style="yellow",
                )
            )
            if not Confirm.ask("Overwrite existing translations?"):
                self.console.print(Panel("Translation cancelled", style="yellow"))
                return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:

            file_task = progress.add_task("Translating files...", total=len(srt_files))

            def progress_callback(current_file: int, total_files: int, filename: str):
                progress.update(
                    file_task,
                    completed=current_file,
                    description=f"Processing: {filename}",
                )

            try:
                results = self.translator.translate_directory(
                    self.working_directory,
                    target_lang,
                    source_lang,
                    progress_callback=progress_callback,
                )

                progress.update(
                    file_task,
                    completed=len(srt_files),
                    description="All files processed",
                )
                progress.remove_task(file_task)
                self.console.clear()

                if results:
                    result_table = Table(
                        title=f"Translation Results ({len(results)} files)",
                        box=box.ROUNDED,
                    )
                    result_table.add_column("Input File", style="cyan")
                    result_table.add_column("Output File", style="green")
                    result_table.add_column("Entries", style="yellow", justify="right")

                    total_entries = 0
                    for input_file, output_file, entry_count in results:
                        result_table.add_row(input_file, output_file, str(entry_count))
                        total_entries += entry_count

                    self.console.print(result_table)
                    self.console.print(
                        Panel(
                            f"✅ Batch translation completed! Total entries translated: {total_entries}",
                            style="green",
                        )
                    )
                else:
                    self.console.print(
                        Panel("No files were translated", style="yellow")
                    )

            except Exception as error:
                progress.remove_task(file_task)
                self.console.clear()
                self.console.print(
                    Panel(f"Error during batch translation: {error}", style="red")
                )

    def convert_vtt_files(self):
        """Handle VTT to SRT conversion with progress indication"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Converting VTT files...", total=None)

            try:
                converted_files = self.converter.convert_directory(
                    self.working_directory
                )
                progress.remove_task(task)
                self.console.clear()

                if not converted_files:
                    self.console.print(
                        Panel(
                            "No VTT files found or all files already converted",
                            style="yellow",
                        )
                    )
                else:
                    result_table = Table(
                        title=f"Conversion Results ({len(converted_files)} files)",
                        box=box.ROUNDED,
                    )
                    result_table.add_column("Source File", style="yellow")
                    result_table.add_column("Output File", style="green")
                    result_table.add_column("Cues", style="cyan", justify="right")

                    for filename, cue_count in converted_files:
                        output_name = f"{os.path.splitext(filename)[0]}.en.srt"
                        result_table.add_row(filename, output_name, str(cue_count))

                    self.console.print(result_table)

            except Exception as error:
                progress.remove_task(task)
                self.console.clear()
                self.console.print(
                    Panel(f"Error during conversion: {error}", style="red")
                )

    def organize_files(self):
        """Handle file organization with progress indication"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Organizing files...", total=None)

            try:
                results = self.organizer.organize_directory(self.working_directory)
                progress.remove_task(task)
                self.console.clear()

                if not results["created_folders"]:
                    self.console.print(
                        Panel(
                            "No files to organize or folders already exist",
                            style="yellow",
                        )
                    )
                else:
                    folder_table = Table(
                        title=f'Created Folders ({len(results["created_folders"])})',
                        box=box.ROUNDED,
                    )
                    folder_table.add_column("Folder Name", style="blue")

                    for folder_name in results["created_folders"]:
                        folder_table.add_row(f"📁 {folder_name}")

                    self.console.print(folder_table)

                    if results["processed_files"]:
                        operations_table = Table(
                            title="File Operations", box=box.MINIMAL
                        )
                        operations_table.add_column("Operation", style="green")

                        for operation in results["processed_files"]:
                            operations_table.add_row(operation)

                        self.console.print(operations_table)

            except Exception as error:
                progress.remove_task(task)
                self.console.clear()
                self.console.print(
                    Panel(f"Error during organization: {error}", style="red")
                )

    def convert_and_organize(self):
        """Handle conversion followed by organization"""
        self.console.print(Panel("Step 1: Converting VTT files", style="blue"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Converting VTT files...", total=None)

            try:
                converted_files = self.converter.convert_directory(
                    self.working_directory
                )
                progress.remove_task(task)
                self.console.clear()

                self.console.print(Panel("Step 2: Organizing files", style="blue"))

                task = progress.add_task("Organizing files...", total=None)
                results = self.organizer.organize_directory(self.working_directory)

                progress.remove_task(task)
                self.console.clear()

                if converted_files or results["created_folders"]:
                    if converted_files:
                        result_table = Table(
                            title=f"Converted Files ({len(converted_files)})",
                            box=box.ROUNDED,
                        )
                        result_table.add_column("VTT → SRT", style="green")
                        result_table.add_column("Cues", style="cyan", justify="right")

                        for filename, cue_count in converted_files:
                            output_name = f"{os.path.splitext(filename)[0]}.en.srt"
                            result_table.add_row(
                                f"{filename} → {output_name}", str(cue_count)
                            )

                        self.console.print(result_table)

                    if results["created_folders"]:
                        folder_table = Table(
                            title=f'Created Folders ({len(results["created_folders"])})',
                            box=box.ROUNDED,
                        )
                        folder_table.add_column("Folder Name", style="blue")

                        for folder_name in results["created_folders"]:
                            folder_table.add_row(f"📁 {folder_name}")

                        self.console.print(folder_table)
                else:
                    self.console.print(
                        Panel(
                            "No operations performed - files may already be processed",
                            style="yellow",
                        )
                    )

            except Exception as error:
                progress.remove_task(task)
                self.console.clear()
                self.console.print(Panel(f"Error during process: {error}", style="red"))

    def change_directory(self):
        """Handle directory change with validation"""
        current_dir_panel = Panel(f"Current: {self.working_directory}", style="dim")
        self.console.print(current_dir_panel)

        new_directory = Prompt.ask(
            "Enter new directory path", default=self.working_directory
        )

        if not new_directory or new_directory == self.working_directory:
            self.console.print(Panel("Directory change cancelled", style="yellow"))
            return

        expanded_path = os.path.expanduser(new_directory)
        absolute_path = os.path.abspath(expanded_path)

        if os.path.exists(absolute_path) and os.path.isdir(absolute_path):
            self.working_directory = absolute_path
            self.console.print(
                Panel(f"Directory changed to: {self.working_directory}", style="green")
            )
        else:
            self.console.print(
                Panel(
                    "Invalid directory path. Please check the path and try again.",
                    style="red",
                )
            )

    def clear(self):
        """Clear the console"""
        os.system("cls" if os.name == "nt" else "clear")

    def run(self):
        """Main application loop with Rich interface"""
        while True:
            self.clear()
            self.console.print(self.create_header())
            self.console.print(self.create_menu())
            choice = self.get_user_choice()
            self.clear()

            if choice == "1":
                self.convert_vtt_files()
            elif choice == "2":
                self.organize_files()
            elif choice == "3":
                self.convert_and_organize()
            elif choice == "4":
                self.show_directory_contents()
            elif choice == "5":
                self.change_directory()
            elif choice == "6" and self.translation_available:
                self.translate_single_file()
            elif choice == "7" and self.translation_available:
                self.translate_directory()
            elif choice == "8" and self.translation_available:
                self.show_available_languages()
            elif choice == "9":
                if Confirm.ask("Are you sure you want to exit?"):
                    self.console.print(
                        Panel(
                            "Thank you for using Video File Organizer!", style="green"
                        )
                    )
                    break
                else:
                    continue

            if choice != "9":
                Prompt.ask("Press enter to continue", default="enter")
