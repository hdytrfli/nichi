"""
VTT to SRT converter module
Handles conversion of WebVTT subtitle files to SRT format
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


class VTTToSRTConverter:
    """Converter class for WebVTT to SRT subtitle format conversion"""

    def __init__(self):
        self.cue_count = 0

    def format_timestamp(self, timestamp: str) -> str:
        """
        Convert WebVTT timestamp to SRT format

        Parameters:
            timestamp: WebVTT timestamp string (e.g., '00:01:02.5', '01:02:03.456')

        Returns:
            Formatted SRT timestamp string (HH:MM:SS,mmm)
        """
        normalized_timestamp = timestamp.replace(",", ".").strip()
        parts = normalized_timestamp.split(":")

        if len(parts) == 2:
            hours = 0
            minutes = int(parts[0])
            seconds_part = parts[1]
        elif len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_part = parts[2]
        else:
            return "00:00:00,000"

        if "." in seconds_part:
            seconds_string, milliseconds_string = seconds_part.split(".", 1)
            seconds = int(seconds_string)
            milliseconds = int((milliseconds_string + "000")[:3])
        else:
            seconds = int(seconds_part)
            milliseconds = 0

        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def parse_vtt_content(self, content: str) -> List[Tuple[str, str, str]]:
        """
        Parse VTT content and extract cues

        Parameters:
            content: Raw VTT file content

        Returns:
            List of tuples containing (start_time, end_time, text)
        """
        normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized_content.split("\n")

        cues = []
        line_pointer = 0

        while line_pointer < len(lines):
            while line_pointer < len(lines) and lines[line_pointer].strip() == "":
                line_pointer += 1

            if line_pointer >= len(lines):
                break

            current_line = lines[line_pointer].strip()

            if current_line.startswith("WEBVTT"):
                line_pointer += 1
                continue

            if current_line.startswith(("NOTE", "STYLE", "REGION")):
                line_pointer += 1
                while line_pointer < len(lines) and lines[line_pointer].strip() != "":
                    line_pointer += 1
                continue

            if "-->" not in lines[line_pointer] and lines[line_pointer].strip() != "":
                line_pointer += 1

            if line_pointer >= len(lines) or "-->" not in lines[line_pointer]:
                line_pointer += 1
                continue

            timestamp_line = lines[line_pointer]
            line_pointer += 1

            if "-->" in timestamp_line:
                timestamp_parts = timestamp_line.split("-->", 1)
                start_raw = timestamp_parts[0].strip()
                end_part = timestamp_parts[1].strip()
                end_raw = end_part.split(" ", 1)[0].strip()

                start_time = self.format_timestamp(start_raw)
                end_time = self.format_timestamp(end_raw)
            else:
                line_pointer += 1
                continue

            text_lines = []
            while line_pointer < len(lines) and lines[line_pointer].strip() != "":
                text_lines.append(lines[line_pointer])
                line_pointer += 1

            cues.append((start_time, end_time, "\n".join(text_lines)))

        return cues

    def generate_srt_content(self, cues: List[Tuple[str, str, str]]) -> str:
        """
        Generate SRT format content from cues

        Parameters:
            cues: List of tuples containing (start_time, end_time, text)

        Returns:
            Complete SRT formatted content string
        """
        srt_lines = []
        cue_index = 1

        for start_time, end_time, subtitle_text in cues:
            srt_lines.append(str(cue_index))
            srt_lines.append(f"{start_time} --> {end_time}")

            if subtitle_text:
                srt_lines.append(subtitle_text)

            srt_lines.append("")
            cue_index += 1

        return "\n".join(srt_lines).rstrip() + "\n"

    def convert_file(self, source_path: str, destination_path: str) -> int:
        """
        Convert a single VTT file to SRT format

        Parameters:
            source_path: Path to the source VTT file
            destination_path: Path where the SRT file will be saved

        Returns:
            Number of subtitle cues converted
        """
        with open(source_path, "r", encoding="utf-8-sig") as file:
            content = file.read()

        cues = self.parse_vtt_content(content)
        srt_content = self.generate_srt_content(cues)

        with open(destination_path, "w", encoding="utf-8") as file:
            file.write(srt_content)

        self.cue_count = len(cues)
        return len(cues)

    def convert_directory(
        self, directory_path: str, output_directory: str = None
    ) -> List[Tuple[str, int]]:
        """
        Convert all VTT files in a directory to SRT format

        Parameters:
            directory_path: Directory containing VTT files
            output_directory: Directory where SRT files will be saved (optional)

        Returns:
            List of tuples containing (filename, cue_count) for each converted file
        """
        if output_directory is None:
            output_directory = directory_path

        Path(output_directory).mkdir(exist_ok=True)

        vtt_files = [
            filename
            for filename in os.listdir(directory_path)
            if filename.lower().endswith(".vtt")
        ]

        converted_files = []

        for vtt_filename in vtt_files:
            base_name = os.path.splitext(vtt_filename)[0]
            source_path = os.path.join(directory_path, vtt_filename)
            destination_path = os.path.join(output_directory, f"{base_name}.en.srt")

            if os.path.exists(destination_path):
                continue

            cue_count = self.convert_file(source_path, destination_path)
            converted_files.append((vtt_filename, cue_count))

        return converted_files
