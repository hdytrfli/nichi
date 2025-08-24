"""
SRT Translator module
Provides functionality to translate SRT subtitle files using Google Gemini AI
Supports Jellyfin subtitle formatting with proper language codes
"""

import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
import random

import google.generativeai as genai
from dotenv import load_dotenv


@dataclass
class SRTEntry:
    """Represents a single SRT subtitle entry"""

    index: int
    start_time: str
    end_time: str
    text: str


class SRTParser:
    """Parser for SRT subtitle files"""

    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse and validate SRT time format"""
        pattern = r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
        if re.match(pattern, time_str):
            return time_str
        raise ValueError(f"Invalid time format: {time_str}")

    @staticmethod
    def parse_srt_file(file_path: str) -> List[SRTEntry]:
        """Parse SRT file and return list of SRT entries"""
        entries = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
        except UnicodeDecodeError:
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read().strip()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode file: {file_path}")

        blocks = re.split(r"\n\s*\n", content)

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            try:
                index = int(lines[0])

                time_line = lines[1]
                time_match = re.match(
                    r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
                    time_line,
                )
                if not time_match:
                    continue

                start_time = SRTParser.parse_time(time_match.group(1))
                end_time = SRTParser.parse_time(time_match.group(2))

                text = "\n".join(lines[2:]).strip()

                entries.append(
                    SRTEntry(
                        index=index, start_time=start_time, end_time=end_time, text=text
                    )
                )

            except (ValueError, IndexError) as e:
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


class JellyfinFormatter:
    """Handle Jellyfin subtitle file naming conventions"""

    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """
        Parse Jellyfin subtitle filename format

        Returns:
            Dict with 'base', 'sdh', 'language', 'extension' keys
        """
        path = Path(filename)
        name = path.stem
        extension = path.suffix

        sdh = ""
        language = ""

        if name.endswith(".sdh.en"):
            base = name[:-7]
            sdh = "sdh"
            language = "en"
        elif name.endswith(".sdh.id"):
            base = name[:-7]
            sdh = "sdh"
            language = "id"
        elif name.endswith(".en"):
            base = name[:-3]
            language = "en"
        elif name.endswith(".id"):
            base = name[:-3]
            language = "id"
        else:
            parts = name.split(".")
            if len(parts) >= 2 and parts[-1] in [
                "en",
                "id",
                "es",
                "fr",
                "de",
                "it",
                "pt",
                "ru",
                "ja",
                "ko",
                "zh",
                "ar",
                "hi",
                "th",
                "vi",
                "nl",
                "sv",
                "da",
                "no",
                "fi",
                "pl",
                "tr",
            ]:
                language = parts[-1]
                if len(parts) >= 3 and parts[-2] == "sdh":
                    sdh = "sdh"
                    base = ".".join(parts[:-2])
                else:
                    base = ".".join(parts[:-1])
            else:
                base = name

        return {"base": base, "sdh": sdh, "language": language, "extension": extension}

    @staticmethod
    def format_output_filename(input_filename: str, target_language: str) -> str:
        """
        Generate output filename maintaining Jellyfin format

        Args:
            input_filename: Original filename
            target_language: Target language code

        Returns:
            Formatted output filename
        """
        parsed = JellyfinFormatter.parse_filename(input_filename)

        parts = [parsed["base"]]

        if parsed["sdh"]:
            parts.append("sdh")

        parts.append(target_language)

        return f"{'.'.join(parts)}{parsed['extension']}"


class GeminiTranslator:
    """Google Gemini AI translator for SRT subtitles"""

    def __init__(self):

        cwd_env = Path.cwd() / ".env"
        script_env = Path(__file__).parent.parent / ".env"

        if cwd_env.exists():
            load_dotenv(cwd_env)
        elif script_env.exists():
            load_dotenv(script_env)
        else:
            load_dotenv()

        api_key = os.getenv("GOOGLE_AI_API_KEY")
        project_id = os.getenv("GOOGLE_AI_PROJECT_ID")
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-exp")

        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)

        if project_id:
            genai.configure(project=project_id)

        self.model = genai.GenerativeModel(model_name)

        self.language_names = {
            "en": "English",
            "id": "Indonesian",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "th": "Thai",
            "vi": "Vietnamese",
            "nl": "Dutch",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish",
            "pl": "Polish",
            "tr": "Turkish",
        }

        self.max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
        self.base_delay = float(os.getenv("GEMINI_BASE_DELAY", "1.0"))
        self.max_delay = float(os.getenv("GEMINI_MAX_DELAY", "60.0"))

    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        return self.language_names.get(code.lower(), code)

    async def translate_batch_with_retry(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> Tuple[List[str], bool]:
        """Translate a batch with retry logic and exponential backoff"""
        if not texts:
            return [], True

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.translate_batch(
                    texts, target_language, source_language
                )
                return result, True

            except Exception as e:
                if attempt == self.max_retries:
                    print(
                        f"Batch translation failed after {self.max_retries + 1} attempts: {e}"
                    )
                    return texts, False  # Return original texts as fallback

                delay = min(
                    self.base_delay * (2**attempt) + random.uniform(0, 1),
                    self.max_delay,
                )
                print(
                    f"Batch translation attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

        return texts, False

    async def translate_batch(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> List[str]:
        """Translate a batch of texts using Gemini"""
        if not texts:
            return []

        try:
            source_lang_str = (
                f"from {self.get_language_name(source_language)}"
                if source_language
                else "from the detected language"
            )
            target_lang_str = self.get_language_name(target_language)

            numbered_texts = []
            for i, text in enumerate(texts):
                clean_text = text.strip()
                numbered_texts.append(f"{i+1}. {clean_text}")

            batch_text = "\n".join(numbered_texts)

            prompt = f"""Translate these subtitle texts {source_lang_str} to {target_lang_str}. 
            Keep exact numbering, preserve line breaks with \\n, maintain music/sound notations. 
            Return only the numbered translations:

            {batch_text}"""

            response = await asyncio.to_thread(self.model.generate_content, prompt)

            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")

            translated_content = response.text.strip()

            translations = []
            lines = translated_content.split("\n")
            current_translation = ""
            current_number = 1

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                number_match = re.match(rf"^{current_number}\.\s*(.*)", line)
                if number_match:

                    if current_translation and len(translations) == current_number - 2:
                        translations.append(current_translation.strip())

                    current_translation = number_match.group(1)
                    current_number += 1
                else:

                    if current_translation:
                        current_translation += "\n" + line
                    else:

                        current_translation = line

            if current_translation:
                translations.append(current_translation.strip())

            if len(translations) != len(texts):

                translation_lines = [
                    line for line in translated_content.split("\n") if line.strip()
                ]
                translations = []

                for i, original_text in enumerate(texts):
                    if i < len(translation_lines):

                        clean_translation = re.sub(
                            r"^\d+\.\s*", "", translation_lines[i].strip()
                        )
                        translations.append(
                            clean_translation if clean_translation else original_text
                        )
                    else:
                        translations.append(original_text)

            final_translations = translations[: len(texts)]
            while len(final_translations) < len(texts):
                final_translations.append(texts[len(final_translations)])

            return final_translations

        except Exception as e:
            raise Exception(f"Translation error: {str(e)}")

    async def translate_batches_concurrent(
        self,
        batch_groups: List[List[str]],
        target_language: str,
        source_language: str = None,
        max_concurrent: int = 5,
    ) -> Tuple[List[List[str]], List[bool]]:
        """Translate multiple batches concurrently with error tracking"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def translate_single_batch_safe(texts):
            async with semaphore:
                return await self.translate_batch_with_retry(
                    texts, target_language, source_language
                )

        tasks = [translate_single_batch_safe(batch) for batch in batch_groups]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        translations = []
        success_flags = []

        for result in results:
            if isinstance(result, tuple):
                translation, success = result
                translations.append(translation)
                success_flags.append(success)
            else:
                # Fallback for unexpected results
                translations.append(batch_groups[len(translations)])
                success_flags.append(False)

        return translations, success_flags

    def translate_srt_entries(
        self,
        entries: List[SRTEntry],
        target_language: str,
        source_language: str = None,
        batch_size: int = 200,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        max_concurrent: int = 5,
    ) -> List[SRTEntry]:
        """Translate SRT entries using optimized batch processing with robust error handling"""
        if not entries:
            return []

        translated_entries = []

        batches = []
        batch_texts_groups = []

        for batch_idx in range(0, len(entries), batch_size):
            batch_entries = entries[batch_idx : batch_idx + batch_size]
            batch_texts = [entry.text for entry in batch_entries]
            batches.append(batch_entries)
            batch_texts_groups.append(batch_texts)

        total_batches = len(batches)
        successful_batches = 0
        failed_batches = 0

        if progress_callback:
            progress_callback(0, total_batches)

        try:
            translated_batch_results, success_flags = asyncio.run(
                self.translate_batches_concurrent(
                    batch_texts_groups, target_language, source_language, max_concurrent
                )
            )

            for batch_idx, (batch_entries, translated_texts, success) in enumerate(
                zip(batches, translated_batch_results, success_flags)
            ):
                if success:
                    successful_batches += 1
                else:
                    failed_batches += 1
                    print(
                        f"Batch {batch_idx + 1}/{total_batches} failed - using original text"
                    )

                if not translated_texts or len(translated_texts) == 0:
                    translated_texts = [entry.text for entry in batch_entries]

                while len(translated_texts) < len(batch_entries):
                    translated_texts.append(batch_entries[len(translated_texts)].text)

                for j, entry in enumerate(batch_entries):
                    if j < len(translated_texts) and translated_texts[j] is not None:
                        text_to_use = translated_texts[j]
                    else:
                        text_to_use = entry.text

                    translated_entry = SRTEntry(
                        index=entry.index,
                        start_time=entry.start_time,
                        end_time=entry.end_time,
                        text=text_to_use,
                    )
                    translated_entries.append(translated_entry)

                if progress_callback:
                    progress_callback(batch_idx + 1, total_batches)

            if failed_batches > 0:
                print(
                    f"Translation completed: {successful_batches}/{total_batches} batches successful, {failed_batches} failed"
                )
            else:
                print(
                    f"Translation completed successfully: {successful_batches}/{total_batches} batches processed"
                )

        except Exception as e:
            print(f"Critical translation process error: {e}")
            if progress_callback:
                progress_callback(total_batches, total_batches)
            return entries

        return translated_entries


class SRTTranslator:
    """Main SRT translation class with Jellyfin format support"""

    def __init__(self):
        self.parser = SRTParser()
        self.translator = GeminiTranslator()
        self.formatter = JellyfinFormatter()

    def get_available_languages(self) -> Dict[str, str]:
        """Get available language codes and names"""
        return self.translator.language_names.copy()

    def get_default_target_language(self) -> str:
        """Get default target language from environment or return 'id'"""

        cwd_env = Path.cwd() / ".env"
        script_env = Path(__file__).parent.parent / ".env"

        if cwd_env.exists():
            load_dotenv(cwd_env)
        elif script_env.exists():
            load_dotenv(script_env)
        else:
            load_dotenv()

        return os.getenv("DEFAULT_TARGET_LANGUAGE", "id")

    def detect_source_language(self, filename: str) -> Optional[str]:
        """Detect source language from filename"""
        parsed = self.formatter.parse_filename(filename)
        return parsed["language"] if parsed["language"] else None

    def translate_file(
        self,
        input_path: str,
        target_language: str,
        source_language: str = None,
        batch_size: int = 200,
        output_path: str = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        max_concurrent: int = 5,
    ) -> Tuple[int, int, str]:
        """
        Translate an SRT file with Jellyfin formatting and optimized processing

        Args:
            input_path: Path to input SRT file
            target_language: Target language code
            source_language: Source language code (optional, will detect from filename)
            batch_size: Number of entries to translate at once (default: 200)
            output_path: Custom output path (optional)
            progress_callback: Callback function for progress updates (current, total)
            max_concurrent: Maximum concurrent batch processing (default: 5)

        Returns:
            Tuple of (total_entries, translated_entries, output_filename)
        """
        try:
            input_file = Path(input_path)

            if not input_file.exists():
                return 0, 0, ""

            if source_language is None:
                source_language = self.detect_source_language(input_file.name)

            entries = self.parser.parse_srt_file(input_path)
            if not entries:
                return 0, 0, ""

            if output_path is None:
                output_filename = self.formatter.format_output_filename(
                    input_file.name, target_language
                )
                final_output_path = input_file.parent / output_filename
            else:
                final_output_path = Path(output_path)
                output_filename = final_output_path.name

            translated_entries = self.translator.translate_srt_entries(
                entries,
                target_language,
                source_language,
                batch_size,
                progress_callback,
                max_concurrent,
            )

            if not translated_entries:
                translated_entries = entries

            self.parser.write_srt_file(translated_entries, str(final_output_path))

            return len(entries), len(translated_entries), output_filename

        except Exception as e:
            print(f"File translation error: {e}")
            return 0, 0, ""

    def translate_directory(
        self,
        directory_path: str,
        target_language: str,
        source_language: str = None,
        filter_language: str = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[Tuple[str, str, int]]:
        """
        Translate all SRT files in a directory with Jellyfin formatting

        Args:
            directory_path: Directory containing SRT files
            target_language: Target language code
            source_language: Source language code (optional)
            filter_language: Only translate files with this source language (optional)
            progress_callback: Callback function for progress updates (current, total, filename)

        Returns:
            List of (input_file, output_file, entry_count) tuples
        """
        results = []

        try:
            directory = Path(directory_path)

            if not directory.exists() or not directory.is_dir():
                return results

            srt_files = list(directory.glob("*.srt"))
            total_files = len(srt_files)

            if progress_callback:
                progress_callback(0, total_files, "Starting...")

            for file_idx, srt_file in enumerate(srt_files, 1):
                try:
                    if progress_callback:
                        progress_callback(
                            file_idx - 1, total_files, f"Processing {srt_file.name}"
                        )

                    parsed = self.formatter.parse_filename(srt_file.name)

                    if parsed["language"] == target_language:
                        continue

                    if filter_language and parsed["language"] != filter_language:
                        continue

                    output_filename = self.formatter.format_output_filename(
                        srt_file.name, target_language
                    )
                    output_path = directory / output_filename

                    if output_path.exists():
                        continue

                    detected_source = (
                        parsed["language"] if parsed["language"] else source_language
                    )

                    total_entries, translated_entries, _ = self.translate_file(
                        str(srt_file),
                        target_language,
                        detected_source,
                        output_path=str(output_path),
                    )

                    if translated_entries > 0:
                        results.append(
                            (srt_file.name, output_filename, translated_entries)
                        )

                    if progress_callback:
                        progress_callback(
                            file_idx, total_files, f"Completed {srt_file.name}"
                        )

                except Exception as e:
                    print(f"Error translating {srt_file.name}: {e}")
                    if progress_callback:
                        progress_callback(
                            file_idx, total_files, f"Failed {srt_file.name}"
                        )
                    continue

        except Exception as e:
            print(f"Directory translation error: {e}")

        return results
