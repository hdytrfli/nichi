"""
User input handling for the video organizer TUI
Manages prompts, validation, and user interactions including diff feature
"""

import os
from typing import List, Optional, Dict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt


class UserInput:
    """Handle user input and validation"""

    def __init__(self, console: Console):
        self.console = console

    def get_menu_choice(self) -> str:
        """Get user menu choice"""
        choices = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        return Prompt.ask("Enter your choice", choices=choices)

    def select_file_from_list(
        self, files: List[str], file_type: str = "file", default: int = 1
    ) -> Optional[str]:
        """
        Let user select a file from a list

        Args:
            files: List of filenames
            file_type: Type description for prompts

        Returns:
            Selected filename or None if cancelled
        """
        if not files:
            self.console.print(
                Panel(f"No {file_type}s found in directory", style="yellow")
            )
            return None

        try:
            file_index = (
                IntPrompt.ask(f"Select {file_type} (1-{len(files)})", default=default)
                - 1
            )
            if file_index < 0 or file_index >= len(files):
                self.console.print(Panel("Invalid file selection", style="red"))
                return None
            return files[file_index]
        except (ValueError, KeyboardInterrupt):
            self.console.print(Panel("Selection cancelled", style="yellow"))
            return None

    def prompt_for_language(
        self,
        prompt_text: str,
        available_languages: Dict[str, str],
        default_code: str = None,
    ) -> Optional[str]:
        """
        Prompt user for language selection

        Args:
            prompt_text: Text to display in prompt
            available_languages: Dict of language codes to names
            default_code: Default language code

        Returns:
            Selected language code or None if cancelled
        """
        if default_code and default_code in available_languages:
            default_display = f"{default_code} - {available_languages[default_code]}"
        else:
            default_display = default_code

        user_input = Prompt.ask(prompt_text, default=default_display)

        if not user_input:
            return None

        user_input = user_input.strip()

        # Check if it's a direct code match
        if user_input.lower() in available_languages:
            return user_input.lower()

        # Check if it's in "code - name" format
        if " - " in user_input:
            code = user_input.split(" - ")[0].strip().lower()
            if code in available_languages:
                return code

        return user_input

    def prompt_for_timing_offset(self) -> Optional[int]:
        """
        Prompt user for timing offset in milliseconds

        Returns:
            Offset in milliseconds or None if cancelled/invalid
        """
        # Show help information
        help_panel = Panel(
            "Enter timing offset in milliseconds:\n"
            "• Positive values (e.g., 1000) delay subtitles by that amount\n"
            "• Negative values (e.g., -1500) advance subtitles by that amount\n"
            "• Examples: 1000 = +1 second, -2500 = -2.5 seconds\n"
            "• Range: ±600000 ms (±10 minutes)\n"
            "• Original file will be backed up with .old extension",
            title="Timing Adjustment Help",
            style="dim",
        )
        self.console.print(help_panel)

        while True:
            try:
                user_input = Prompt.ask(
                    "Enter offset in milliseconds (or 'cancel' to abort)", default="0"
                )

                if user_input.lower() in ["cancel", "c", "quit", "q"]:
                    return None

                offset_ms = int(float(user_input.strip()))

                # Validate range (±10 minutes)
                max_offset = 10 * 60 * 1000  # 10 minutes in ms
                if abs(offset_ms) > max_offset:
                    self.console.print(
                        Panel(
                            f"Offset too large. Maximum allowed: ±{max_offset} ms (±10 minutes)",
                            style="red",
                        )
                    )
                    continue

                # Confirm the adjustment
                offset_seconds = offset_ms / 1000
                direction = "delayed" if offset_ms > 0 else "advanced"

                if offset_ms == 0:
                    confirmation_text = "No timing adjustment will be made. Continue?"
                else:
                    confirmation_text = (
                        f"Subtitles will be {direction} by {abs(offset_seconds):.3f} seconds.\n"
                        f"Original file will be backed up with .old extension. Continue?"
                    )

                if Confirm.ask(confirmation_text):
                    return offset_ms
                else:
                    continue

            except (ValueError, TypeError):
                self.console.print(
                    Panel(
                        "Invalid input. Please enter a number (e.g., 1000, -1500)",
                        style="red",
                    )
                )
                continue
            except KeyboardInterrupt:
                return None

    def confirm_overwrite(self, filename: str) -> bool:
        """Ask user to confirm file overwrite"""
        return Confirm.ask(f"Output file '{filename}' exists. Overwrite?")

    def change_directory(self, current_directory: str) -> Optional[str]:
        """
        Handle directory change with validation

        Args:
            current_directory: Current working directory

        Returns:
            New directory path or None if cancelled/invalid
        """
        current_panel = Panel(f"Current: {current_directory}", style="dim")
        self.console.print(current_panel)

        new_directory = Prompt.ask(
            "Enter new directory path", default=current_directory
        )

        if not new_directory or new_directory == current_directory:
            self.console.print(Panel("Directory change cancelled", style="yellow"))
            return None

        expanded_path = os.path.expanduser(new_directory)
        absolute_path = os.path.abspath(expanded_path)

        if os.path.exists(absolute_path) and os.path.isdir(absolute_path):
            self.console.print(
                Panel(f"Directory changed to: {absolute_path}", style="green")
            )
            return absolute_path
        else:
            self.console.print(Panel("Invalid directory path", style="red"))
            return None

    def confirm_exit(self) -> bool:
        """Ask user to confirm exit"""
        return Confirm.ask("Are you sure you want to exit?", default="y")

    def wait_for_continue(self):
        """Wait for user to press enter"""
        Prompt.ask("Press enter to continue", default="enter")
