"""
UI components for the video organizer TUI
Handles display formatting and user interface elements
"""

import os
from typing import List, Dict
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.align import Align


class UIComponents:
    """Reusable UI components for the TUI"""

    def __init__(self, console: Console):
        self.console = console

    def create_header(self, working_directory: str) -> Panel:
        """Create application header panel"""
        title_text = Text("VIDEO FILE ORGANIZER", style="bold blue")
        directory_text = Text(f"Directory: {working_directory}", style="dim")
        content = Align.left(f"{title_text}\n{directory_text}")
        return Panel(content, box=box.SQUARE, style="blue")

    def create_menu(self) -> Panel:
        """Create menu panel"""
        menu_items = [
            "[bold green]1.[/] Convert VTT files to SRT format",
            "[bold green]2.[/] Organize MP4 and subtitle files into folders",
            "[bold green]3.[/] Convert VTT files and then organize",
            "[bold green]4.[/] Show current directory contents",
            "[bold green]5.[/] Change working directory",
            "[bold cyan]6.[/] Translate SRT file to another language",
            "[bold cyan]7.[/] Show available languages for translation",
            "[bold cyan]8.[/] Adjust subtitle timing",
            "[bold cyan]9.[/] Compare two Subtitle files",
            "[bold magenta]10.[/] Manage translation cache",
            "[bold red]11.[/] Exit",
        ]
        menu_text = "\n".join(menu_items)
        return Panel(menu_text, title="Available Actions", box=box.ROUNDED)

    def show_directory_contents(self, working_directory: str):
        """Display current directory contents in organized tables"""
        try:
            items = os.listdir(working_directory)
            if not items:
                self.console.print(Panel("Directory is empty", style="yellow"))
                return

            # Categorize files
            video_files = [item for item in items if item.lower().endswith(".mp4")]
            vtt_files = [item for item in items if item.lower().endswith(".vtt")]
            srt_files = [item for item in items if item.lower().endswith(".srt")]
            folders = [
                item
                for item in items
                if os.path.isdir(os.path.join(working_directory, item))
            ]

            tables = []

            # Create tables for each file type
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
                    folder_table.add_row(folder)
                tables.append(folder_table)

            if tables:
                self.console.print(Columns(tables, equal=True, expand=True))
            else:
                self.console.print(Panel("No relevant files found", style="dim"))

        except Exception as error:
            self.console.print(Panel(f"Error reading directory: {error}", style="red"))

    def show_file_selection_table(self, files: List[str], title: str) -> Table:
        """Create a table for file selection"""
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Index", style="cyan", width=8)
        table.add_column("Filename", style="green")

        for i, filename in enumerate(files, 1):
            table.add_row(str(i), filename)

        return table

    def show_languages_table(
        self, languages: Dict[str, str], default_lang: str
    ) -> Table:
        """Create a table showing available languages"""
        table = Table(title="Available Languages", box=box.ROUNDED)
        table.add_column("Code", style="cyan", width=8)
        table.add_column("Language", style="green")
        table.add_column("Default", style="yellow", width=10)

        for code, name in sorted(languages.items()):
            is_default = "Yes" if code == default_lang else ""
            table.add_row(code, name, is_default)

        return table

    def show_cache_info_table(self, cache_info: dict) -> Table:
        """Create a table showing translation cache information"""
        table = Table(title="Translation Cache Information", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Cache Directory", cache_info["cache_dir"])
        table.add_row("Cache Files", str(cache_info["files"]))
        table.add_row("Total Size", f"{cache_info['size_mb']} MB")

        if cache_info["files"] > 0:
            avg_size = (
                cache_info["size"] / cache_info["files"]
                if cache_info["files"] > 0
                else 0
            )
            table.add_row("Average File Size", f"{avg_size / 1024:.1f} KB")

        return table

    def show_cache_clear_results(self, message: str, cache_info: dict) -> Table:
        """Create a table showing cache clear results"""
        table = Table(title="Cache Clear Results", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Operation", "Cache Clear")
        table.add_row("Result", message)
        table.add_row("Remaining Files", str(cache_info["files"]))
        table.add_row("Remaining Size", f"{cache_info['size_mb']} MB")

        return table

    def show_translation_results(
        self,
        input_file: str,
        output_file: str,
        total_entries: int,
        translated_entries: int,
        target_lang: str,
        source_lang: str = None,
    ) -> Table:
        """Create a table showing translation results"""
        table = Table(title="Translation Complete", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Input File", input_file)
        table.add_row("Output File", output_file)
        table.add_row("Total Entries", str(total_entries))
        table.add_row("Translated Entries", str(translated_entries))
        table.add_row("Target Language", target_lang)
        if source_lang:
            table.add_row("Source Language", source_lang)

        return table

    def show_batch_translation_results(
        self, successful: List[dict], failed: List[tuple], target_lang: str
    ) -> Table:
        """Create a table showing batch translation results"""
        table = Table(
            title=f"Batch Translation Results (Target: {target_lang})", box=box.ROUNDED
        )
        table.add_column("Input File", style="cyan")
        table.add_column("Output File", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Entries", style="blue", justify="right")

        # Add successful translations
        for result in successful:
            table.add_row(
                result["input"], result["output"], "✓ Success", str(result["entries"])
            )

        # Add failed translations
        for input_file, error in failed:
            table.add_row(input_file, "N/A", f"✗ Failed", "0")

        return table

    def show_timing_adjustment_results(
        self,
        input_file: str,
        output_file: str,
        backup_file: str,
        entries_processed: int,
        offset_ms: int,
    ) -> Table:
        """Create a table showing timing adjustment results"""
        table = Table(title="Timing Adjustment Complete", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        offset_seconds = offset_ms / 1000
        direction = "Forward" if offset_ms > 0 else "Backward"

        table.add_row("Original File", input_file)
        table.add_row("Adjusted File", output_file)
        table.add_row("Backup Created", backup_file)
        table.add_row("Entries Processed", str(entries_processed))
        table.add_row("Time Adjustment", f"{abs(offset_seconds):.3f}s {direction}")
        table.add_row("Offset (ms)", f"{offset_ms:+d}")

        return table

    def show_conversion_results(self, converted_files: List[tuple]) -> Table:
        """Create a table showing VTT conversion results"""
        table = Table(
            title=f"Conversion Results ({len(converted_files)} files)", box=box.ROUNDED
        )
        table.add_column("Source File", style="yellow")
        table.add_column("Output File", style="green")
        table.add_column("Cues", style="cyan", justify="right")

        for filename, cue_count in converted_files:
            output_name = f"{os.path.splitext(filename)[0]}.en.srt"
            table.add_row(filename, output_name, str(cue_count))

        return table

    def show_organization_results(self, created_folders: List[str]) -> Table:
        """Create a table showing organization results"""
        table = Table(
            title=f"Created Folders ({len(created_folders)})", box=box.ROUNDED
        )
        table.add_column("Folder Name", style="blue")

        for folder_name in created_folders:
            table.add_row(folder_name)

        return table
