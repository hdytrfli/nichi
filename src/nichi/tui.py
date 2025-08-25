"""
Simplified Terminal User Interface
Main controller that orchestrates UI components and operations
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

sys.path.append(str(Path(__file__).parent.parent))

from nichi.converter import VTTToSRTConverter
from nichi.organizer import FileOrganizer
from nichi.translator import SRTTranslator
from .ui_components import UIComponents
from .user_input import UserInput
from .operations import Operations


class ExtendedVideoOrganizerTUI:
    """Main TUI controller - simplified and modular"""

    def __init__(self, working_directory: str):
        self.working_directory = working_directory
        self.console = Console()

        # Initialize services
        self.converter = VTTToSRTConverter()
        self.organizer = FileOrganizer()
        self.translator = SRTTranslator()

        # Initialize UI components
        self.ui = UIComponents(self.console)
        self.input_handler = UserInput(self.console)
        self.operations = Operations(
            self.converter, self.organizer, self.translator, self.console
        )

    def clear_screen(self):
        """Clear the console"""
        os.system("cls" if os.name == "nt" else "clear")

    def handle_menu_choice(self, choice: str):
        """Handle user menu selection"""
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

    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.console.print(self.ui.create_header(self.working_directory))
            self.console.print(self.ui.create_menu())

            choice = self.input_handler.get_menu_choice()

            if choice == "8":
                if self.input_handler.confirm_exit():
                    self.console.print(
                        Panel(
                            "Thank you for using Video File Organizer!", style="green"
                        )
                    )
                    break
                else:
                    continue

            self.clear_screen()
            self.handle_menu_choice(choice)

            if choice != "8":
                self.input_handler.wait_for_continue()
