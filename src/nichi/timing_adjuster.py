"""
SRT timing adjustment utility
Allows adding/subtracting time offsets from all subtitle entries
"""

import re
from typing import List, Optional
from datetime import datetime, timedelta


class SRTTimingAdjuster:
    """Utility for adjusting SRT subtitle timing"""

    @staticmethod
    def parse_srt_time(time_str: str) -> timedelta:
        """
        Parse SRT time format (HH:MM:SS,mmm) to timedelta

        Args:
            time_str: Time string in format "HH:MM:SS,mmm"

        Returns:
            timedelta object
        """
        # Parse format: HH:MM:SS,mmm
        match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", time_str)
        if not match:
            raise ValueError(f"Invalid time format: {time_str}")

        hours, minutes, seconds, milliseconds = map(int, match.groups())

        return timedelta(
            hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds
        )

    @staticmethod
    def format_srt_time(td: timedelta) -> str:
        """
        Format timedelta back to SRT time format

        Args:
            td: timedelta object

        Returns:
            Time string in format "HH:MM:SS,mmm"
        """
        # Handle negative times by setting to 00:00:00,000
        if td.total_seconds() < 0:
            return "00:00:00,000"

        total_seconds = int(td.total_seconds())
        milliseconds = int(td.microseconds / 1000)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        # Ensure we don't exceed 23:59:59,999
        if hours > 23:
            hours = 23
            minutes = 59
            seconds = 59
            milliseconds = 999

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def adjust_timing(time_str: str, offset_ms: int) -> str:
        """
        Adjust a single time string by offset in milliseconds

        Args:
            time_str: Original time string
            offset_ms: Offset in milliseconds (positive or negative)

        Returns:
            Adjusted time string
        """
        try:
            original_time = SRTTimingAdjuster.parse_srt_time(time_str)
            offset = timedelta(milliseconds=offset_ms)
            adjusted_time = original_time + offset
            return SRTTimingAdjuster.format_srt_time(adjusted_time)
        except ValueError:
            # Return original if parsing fails
            return time_str

    @staticmethod
    def adjust_srt_entries(entries: List, offset_ms: int) -> List:
        """
        Adjust timing for all SRT entries

        Args:
            entries: List of SRTEntry objects
            offset_ms: Offset in milliseconds (positive or negative)

        Returns:
            List of adjusted SRTEntry objects
        """
        adjusted_entries = []

        for entry in entries:
            # Create new entry with adjusted times
            adjusted_entry = type(entry)(
                index=entry.index,
                start_time=SRTTimingAdjuster.adjust_timing(entry.start_time, offset_ms),
                end_time=SRTTimingAdjuster.adjust_timing(entry.end_time, offset_ms),
                text=entry.text,
            )
            adjusted_entries.append(adjusted_entry)

        return adjusted_entries

    @staticmethod
    def adjust_srt_file_with_backup(input_path: str, offset_ms: int) -> tuple:
        """
        Adjust timing for an entire SRT file, backing up original with .og extension

        Args:
            input_path: Path to input SRT file
            offset_ms: Offset in milliseconds (positive or negative)

        Returns:
            Tuple of (success: bool, message: str, entries_processed: int, backup_path: str)
        """
        try:
            import shutil
            from pathlib import Path

            # Import here to avoid circular imports
            from .srt_parser import SRTParser

            input_file = Path(input_path)

            # Create backup filename with .og extension
            backup_path = input_file.with_suffix(".og" + input_file.suffix)

            # Parse the original file
            entries = SRTParser.parse_srt_file(input_path)
            if not entries:
                return False, "No valid subtitle entries found", 0, ""

            # Create backup of original file
            shutil.copy2(input_path, backup_path)

            # Adjust timing
            adjusted_entries = SRTTimingAdjuster.adjust_srt_entries(entries, offset_ms)

            # Write the adjusted file to the original location
            SRTParser.write_srt_file(adjusted_entries, input_path)

            offset_seconds = offset_ms / 1000
            direction = "forward" if offset_ms > 0 else "backward"
            message = f"Adjusted {len(adjusted_entries)} entries by {abs(offset_seconds):.3f}s {direction}"

            return True, message, len(adjusted_entries), str(backup_path)

        except Exception as e:
            return False, f"Error adjusting timing: {str(e)}", 0, ""

    @staticmethod
    def validate_offset(offset_input: str) -> Optional[int]:
        """
        Validate and convert offset input to milliseconds

        Args:
            offset_input: User input string

        Returns:
            Offset in milliseconds or None if invalid
        """
        try:
            offset_ms = int(float(offset_input.strip()))
            # Limit to reasonable range (±10 minutes)
            max_offset = 10 * 60 * 1000  # 10 minutes in ms
            if abs(offset_ms) > max_offset:
                return None
            return offset_ms
        except (ValueError, TypeError):
            return None
