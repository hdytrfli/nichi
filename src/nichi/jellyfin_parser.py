"""
Jellyfin subtitle filename parser
Handles parsing and formatting of Jellyfin subtitle naming conventions
"""

from pathlib import Path
from typing import Dict, Optional


class JellyfinParser:
    """Simple Jellyfin subtitle filename parser"""

    MODIFIERS = {"sdh", "forced", "cc", "hi"}

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, Optional[str]]:
        """
        Parse Jellyfin subtitle filename

        Logic:
        - Split filename into parts
        - Determine language position based on part count
        - Extract name, track, language, and modifier
        """
        path = Path(filename)
        extension = path.suffix
        parts = path.stem.split(".")
        part_count = len(parts)

        # Initialize result
        result = {
            "name": None,
            "track": None,
            "language": None,
            "modifier": None,
            "extension": extension,
        }

        if part_count < 2:
            # Not a valid jellyfin subtitle
            result["name"] = parts[0] if parts else None
            return result

        if part_count == 2:
            # name.language.srt
            result["name"] = parts[0]
            result["language"] = parts[1]

        elif part_count == 3:
            # name.track.language.srt OR name.language.modifier.srt
            if parts[2] in JellyfinParser.MODIFIERS:
                # name.language.modifier.srt
                result["name"] = parts[0]
                result["language"] = parts[1]
                result["modifier"] = parts[2]
            else:
                # name.track.language.srt
                result["name"] = parts[0]
                result["track"] = parts[1]
                result["language"] = parts[2]

        elif part_count == 4:
            # name.track.language.modifier.srt
            result["name"] = parts[0]
            result["track"] = parts[1]
            result["language"] = parts[2]
            result["modifier"] = parts[3]

        elif part_count >= 5:
            # name.extra.track.language.modifier.srt (language is 3rd from last)
            language_index = part_count - 3
            result["name"] = ".".join(parts[: language_index - 1])
            result["track"] = parts[language_index - 1]
            result["language"] = parts[language_index]
            result["modifier"] = parts[language_index + 1]

        return result

    @staticmethod
    def format_output_filename(input_filename: str, target_language: str) -> str:
        """Generate output filename with target language"""
        parsed = JellyfinParser.parse_filename(input_filename)

        parts = []
        if parsed["name"]:
            parts.append(parsed["name"])
        if parsed["track"]:
            parts.append(parsed["track"])

        parts.append(target_language)

        if parsed["modifier"]:
            parts.append(parsed["modifier"])

        return ".".join(parts) + (parsed["extension"] or ".srt")
