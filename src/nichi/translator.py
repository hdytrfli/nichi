"""
Main SRT translator
Combines all components for simple subtitle translation
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple

from .srt_parser import SRTParser, SRTEntry
from .gemini_translator import GeminiTranslator
from .jellyfin_parser import JellyfinParser
from .env_loader import EnvLoader


class SRTTranslator:
    """Main SRT translation class"""

    def __init__(self):
        self.parser = SRTParser()
        self.translator = GeminiTranslator()
        self.formatter = JellyfinParser()

    def get_available_languages(self) -> Dict[str, str]:
        """Get available language codes and names"""
        return self.translator.LANGUAGES.copy()

    def get_default_target_language(self) -> str:
        """Get default target language from environment"""
        return EnvLoader.get_config_value("DEFAULT_TARGET_LANGUAGE", "id")

    def detect_source_language(self, filename: str) -> Optional[str]:
        """Detect source language from filename"""
        parsed = self.formatter.parse_filename(filename)
        return parsed["language"]

    def translate_file(
        self,
        input_path: str,
        target_language: str,
        source_language: str = None,
        output_path: str = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int, str]:
        """
        Translate an SRT file

        Returns:
            Tuple of (total_entries, translated_entries, output_filename)
        """
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Parse SRT file
        entries = self.parser.parse_srt_file(input_path)
        if not entries:
            raise ValueError("No valid subtitle entries found")

        # Determine output path
        if output_path is None:
            output_filename = self.formatter.format_output_filename(
                input_file.name, target_language
            )
            output_path = input_file.parent / output_filename
        else:
            output_filename = Path(output_path).name

        # Extract texts for translation
        texts = [entry.text for entry in entries]

        # Translate texts
        translated_texts = self.translator.translate_texts(
            texts, target_language, source_language, progress_callback
        )

        # Create translated entries
        translated_entries = []
        for entry, translated_text in zip(entries, translated_texts):
            translated_entries.append(
                SRTEntry(
                    index=entry.index,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    text=translated_text,
                )
            )

        # Write output file
        self.parser.write_srt_file(translated_entries, str(output_path))

        return len(entries), len(translated_entries), output_filename
