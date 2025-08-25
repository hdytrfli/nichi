"""
SRT file parser and writer
Simple utilities for handling SRT subtitle files
"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class SRTEntry:
    """Represents a single SRT subtitle entry"""

    index: int
    start_time: str
    end_time: str
    text: str


class SRTParser:
    """Simple SRT file parser"""

    @staticmethod
    def parse_srt_file(file_path: str) -> List[SRTEntry]:
        """Parse SRT file and return list of entries"""
        entries = []

        # Try different encodings
        content = None
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    content = file.read().strip()
                break
            except UnicodeDecodeError:
                continue

        if not content:
            return entries

        blocks = re.split(r"\n\s*\n", content)

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])

                # Parse time line
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                    lines[1],
                )
                if not time_match:
                    continue

                start_time = time_match.group(1)
                end_time = time_match.group(2)
                text = "\n".join(lines[2:]).strip()

                entries.append(
                    SRTEntry(
                        index=index, start_time=start_time, end_time=end_time, text=text
                    )
                )

            except (ValueError, IndexError):
                continue

        return entries

    @staticmethod
    def write_srt_file(entries: List[SRTEntry], file_path: str):
        """Write SRT entries to file"""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in entries:
                file.write(f"{entry.index}\n")
                file.write(f"{entry.start_time} --> {entry.end_time}\n")
                file.write(f"{entry.text}\n\n")
