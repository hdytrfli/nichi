"""Main Terminal User Interface controller."""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from nichi.core.converter import VTTToSRTConverter
from nichi.core.organizer import FileOrganizer
from nichi.core.timing import SRTTimingAdjuster
from nichi.core.translator import SRTTranslator
from nichi.ui.components import UIComponents
from nichi.ui.input import UserInput


class ExtendedVideoOrganizerTUI:
    """Main TUI controller - simplified and modular with diff feature."""

    def __init__(self, working_directory: str):
        self.working_directory = working_directory
        self.console = Console()

        # Initialize services
        self.converter = VTTToSRTConverter()
        self.organizer = FileOrganizer()
        self.translator = SRTTranslator()
        self.timing_adjuster = SRTTimingAdjuster()

        # Initialize UI components
        self.ui = UIComponents(self.console)
        self.input_handler = UserInput(self.console)

        # Import and initialize operations here to avoid circular import
        from nichi.core.operations import Operations
        self.operations = Operations(
            self.converter,
            self.organizer,
            self.translator,
            self.timing_adjuster,
            self.console,
        )

    def clear_screen(self):
        """Clear the console."""
        if os.name == "nt":
            clear_command = "cls"
        else:
            clear_command = "clear"
        os.system(clear_command)

    def handle_menu_choice(self, choice: str):
        """Handle user menu selection."""
        if choice == "1":
            self.operations.convert_vtt_files(self.working_directory)
        elif choice == "2":
            self.operations.organize_files(self.working_directory)
        elif choice == "3":
            self.operations.convert_and_organize(self.working_directory)
        elif choice == "4":
            self.ui.show_directory_contents(self.working_directory)
        elif choice == "5":
            new_dir = self.input_handler.change_directory(self.working_directory)
            if new_dir:
                self.working_directory = new_dir
        elif choice == "6":
            self.operations.translate_single_file(self.working_directory)
        elif choice == "7":
            self.operations.show_available_languages()
        elif choice == "8":
            self.operations.adjust_subtitle_timing(self.working_directory)
        elif choice == "9":
            self.operations.compare_srt_files(self.working_directory)
        elif choice == "10":
            self.operations.manage_translation_cache()

    def run(self):
        """Main application loop."""
        while True:
            self.clear_screen()
            header_panel = self.ui.create_header(self.working_directory)
            self.console.print(header_panel)
            menu_panel = self.ui.create_menu()
            self.console.print(menu_panel)

            choice = self.input_handler.get_menu_choice()

            if choice == "11":
                exit_confirmation = self.input_handler.confirm_exit()
                if exit_confirmation:
                    success_message = "Thank you for using Video File Organizer!"
                    success_panel = Panel(success_message, style="green")
                    self.console.print(success_panel)
                    break
                else:
                    continue

            self.clear_screen()
            self.handle_menu_choice(choice)

            if choice != "11":
                self.input_handler.wait_for_continue()