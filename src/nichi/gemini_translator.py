"""
Google Gemini translation service
High-performance translator for SRT subtitles with concurrent processing and cache management
"""

import re
import asyncio
import random
import hashlib
import json
import shutil
from pathlib import Path
from typing import List, Callable, Optional, Tuple
import google.generativeai as genai
from google.api_core.exceptions import (
    ResourceExhausted,
    PermissionDenied,
    NotFound,
    InternalServerError,
    ServiceUnavailable,
    DeadlineExceeded,
)
from .env_loader import EnvLoader


class GeminiTranslator:
    """High-performance Google Gemini translator for subtitles"""

    LANGUAGES = {
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

    def __init__(self):
        # Load environment variables
        EnvLoader.load_env()

        # Get API key with better error message
        api_key = EnvLoader.get_api_key()
        genai.configure(api_key=api_key)

        # Configure model with system instruction
        model_name = EnvLoader.get_config_value(
            "GEMINI_MODEL_NAME", "gemini-2.0-flash-exp"
        )

        system_instruction = """You are a professional subtitle translator with expertise in multiple languages and cultural contexts. 
        Your role is to provide accurate, natural, and contextually appropriate translations that preserve the original meaning, 
        tone, and timing of subtitles while adapting to the linguistic conventions of the target language."""

        self.model = genai.GenerativeModel(
            model_name=model_name, system_instruction=system_instruction
        )

        # Load configuration
        self.batch_size = int(
            EnvLoader.get_config_value("TRANSLATION_BATCH_SIZE", "200")
        )
        self.max_retries = int(EnvLoader.get_config_value("GEMINI_MAX_RETRIES", "3"))
        self.base_delay = float(EnvLoader.get_config_value("GEMINI_BASE_DELAY", "1.0"))
        self.max_delay = float(EnvLoader.get_config_value("GEMINI_MAX_DELAY", "60.0"))
        self.max_concurrent = int(
            EnvLoader.get_config_value("MAX_CONCURRENT_REQUESTS", "5")
        )

        self.cache_dir = Path.home() / ".config" / "nichi" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        return self.LANGUAGES.get(code.lower(), code)

    def get_cache_info(self) -> dict:
        """Get information about cache usage"""
        if not self.cache_dir.exists():
            return {"cache_dir": str(self.cache_dir), "files": 0, "size": 0}

        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files if f.exists())

        return {
            "cache_dir": str(self.cache_dir),
            "files": len(cache_files),
            "size": total_size,
            "size_mb": 0 if total_size == 0 else round(total_size / (1024 * 1024), 2),
        }

    def clear_cache(self) -> Tuple[bool, str, dict]:
        """
        Clear translation cache

        Returns:
            Tuple of (success: bool, message: str, cache_info: dict)
        """
        try:
            cache_info_before = self.get_cache_info()

            if cache_info_before["files"] == 0:
                return True, "Cache is already empty", cache_info_before

            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

            cache_info_after = self.get_cache_info()
            message = f"Cleared {cache_info_before['files']} cache files ({cache_info_before['size_mb']} MB)"
            return True, message, cache_info_after

        except Exception as e:
            return False, f"Failed to clear cache: {str(e)}", self.get_cache_info()

    def _get_cache_key(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> str:
        """Generate cache key hash from translation parameters"""
        cache_data = {
            "texts": texts,
            "target_language": target_language,
            "source_language": source_language,
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _get_cached_translation(self, cache_key: str) -> Optional[List[str]]:
        """Retrieve cached translation if available"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    return cached_data.get("translations")
            except (json.JSONDecodeError, IOError):
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        return None

    def _save_cached_translation(self, cache_key: str, translations: List[str]) -> None:
        """Save translation to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_data = {
                "translations": translations,
                "timestamp": asyncio.get_event_loop().time(),
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass  # Silently fail if cache write fails

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Retrieve cached raw Gemini response if available"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    return cached_data.get("raw_response")
            except (json.JSONDecodeError, IOError):
                # Remove corrupted cache file
                cache_file.unlink(missing_ok=True)
        return None

    def _save_cached_response(self, cache_key: str, raw_response: str) -> None:
        """Save raw Gemini response to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_data = {
                "raw_response": raw_response,
                "timestamp": asyncio.get_event_loop().time(),
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass  # Silently fail if cache write fails

    def _parse_gemini_response(
        self, raw_response: str, original_texts: List[str]
    ) -> List[str]:
        """Parse raw Gemini response into translations with simplified logic"""
        if not raw_response:
            return original_texts

        translations = []
        lines = raw_response.strip().split("\n")
        current_translation = ""
        expected_number = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with expected number
            number_match = re.match(rf"^{expected_number}\.\s*(.*)", line)
            if number_match:
                # Save previous translation if we have one
                if current_translation and len(translations) == expected_number - 2:
                    translations.append(current_translation.strip())

                # Start new translation
                current_translation = number_match.group(1)
                expected_number += 1
            else:
                # Continuation of current translation (preserve line breaks)
                if current_translation:
                    current_translation += "\n" + line

        # Don't forget the last translation
        if current_translation:
            translations.append(current_translation.strip())

        # Ensure we have exactly the same number of translations as input
        while len(translations) < len(original_texts):
            translations.append(original_texts[len(translations)])

        return translations[: len(original_texts)]

    def _get_translation_prompt(
        self, source_lang_str: str, target_lang_str: str, batch_text: str
    ) -> str:
        """Generate translation prompt with language-specific instructions"""

        base_instructions = [
            "1. Maintain original tone and style",
            "2. Keep non-dialogue cues like [music] or (laughs) unchanged",
            "3. Translate idioms to natural equivalents, not literally",
            "4. Make sure gender-specific terms are translated correctly based on context (e.g., in English 'good looking' can be 'tampan' or 'cantik' in Indonesian)",
            "5. Return ONLY the numbered translations, no explanations",
            "6. [CRITICAL] Subtitle can be multi-line, YOU MUST PRESERVE LINE BREAKS WITH \\n, THIS IS VERY IMPORTANT, DO NOT ADD ANOTHER NUMBER TO THE LINES WITHOUT NUMBER!",
            "7. [CRITICAL] Each numbered item (1., 2., 3., etc.) represents ONE subtitle timing, if there's no number in the front means it's new line on the same number, DO NOT SPLIT THEM! [VERY IMPORTANT]",
            "8. [CRITICAL] If there are XML tags in the subtitle, preserve them exactly",
            "9. [CRITICAL] Use standard Indonesian subtitle conventions: prefer 'Aku' and 'Kamu' over colloquial 'Gue' and 'Lo'",
            "10. [CRITICAL] Avoid outdated or overly formal terms like 'Bung' - use modern, natural Indonesian",
            "11. [CRITICAL] Instead of using 'Bro' for 'Dude' translation use the character if possible or just remove the word if the meaning doesn't change",
            "12. [CRITICAL] Use contemporary Indonesian that sounds natural in modern subtitles",
        ]

        instructions = "\n".join(base_instructions)
        prompt = f"""Translate the following subtitle text from {source_lang_str} to {target_lang_str}.

        Instructions:
        {instructions}

        Text to translate:
        {batch_text}
        """

        return prompt

    async def translate_batch(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> List[str]:
        """Translate a batch of texts using improved prompt and parsing"""
        if not texts:
            return []

        cache_key = self._get_cache_key(texts, target_language, source_language)
        cached_response = self._get_cached_response(cache_key)

        if cached_response:
            # Parse cached response
            return self._parse_gemini_response(cached_response, texts)

        source_lang_str = (
            self.get_language_name(source_language)
            if source_language
            else "the detected language"
        )
        target_lang_str = self.get_language_name(target_language)

        # Create numbered list for translation with better formatting
        numbered_texts = []
        for i, text in enumerate(texts):
            clean_text = text.strip()
            numbered_texts.append(f"{i+1}. {clean_text}")

        batch_text = "\n".join(numbered_texts)

        # DEBUG export the text to cache
        self._save_cached_response(cache_key + "_debug", batch_text)

        prompt = self._get_translation_prompt(
            source_lang_str, target_lang_str, batch_text
        )

        response = await asyncio.to_thread(self.model.generate_content, prompt)

        if not response or not response.text:
            return texts  # Return original if no response

        raw_response = response.text.strip()

        self._save_cached_response(cache_key, raw_response)

        return self._parse_gemini_response(raw_response, texts)

    async def translate_batch_with_retry(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> Tuple[List[str], bool, Optional[str]]:
        """Translate with retry logic and detailed error handling"""
        if not texts:
            return [], True, None

        last_error_message = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await self.translate_batch(
                    texts, target_language, source_language
                )
                return result, True, None

            except ResourceExhausted as e:
                last_error_message = f"Rate limit exceeded: {str(e)}"
                if attempt == self.max_retries:
                    return texts, False, last_error_message

                delay = min(
                    self.base_delay * (2**attempt) + random.uniform(0, 1),
                    self.max_delay,
                )
                await asyncio.sleep(delay)

            except (PermissionDenied, NotFound) as e:
                last_error_message = str(e)
                return texts, False, last_error_message

            except (InternalServerError, ServiceUnavailable, DeadlineExceeded) as e:
                last_error_message = str(e)
                if attempt == self.max_retries:
                    return texts, False, last_error_message

                delay = min(
                    self.base_delay * (2**attempt) + random.uniform(0, 1),
                    self.max_delay,
                )
                await asyncio.sleep(delay)

            except Exception as e:
                last_error_message = str(e)
                if attempt == self.max_retries:
                    return texts, False, last_error_message

                delay = min(
                    self.base_delay * (2**attempt) + random.uniform(0, 1),
                    self.max_delay,
                )
                await asyncio.sleep(delay)

        return texts, False, last_error_message or "Translation failed"

    async def translate_batches_concurrent(
        self,
        batch_groups: List[List[str]],
        target_language: str,
        source_language: str = None,
    ) -> Tuple[List[List[str]], List[bool], List[Optional[str]]]:
        """Translate multiple batches concurrently - KEY PERFORMANCE IMPROVEMENT"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def translate_single_batch_safe(texts):
            async with semaphore:
                return await self.translate_batch_with_retry(
                    texts, target_language, source_language
                )

        # Process all batches concurrently
        tasks = [translate_single_batch_safe(batch) for batch in batch_groups]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        translations = []
        success_flags = []
        error_messages = []

        for result in results:
            if isinstance(result, tuple) and len(result) == 3:
                translation, success, error_msg = result
                translations.append(translation)
                success_flags.append(success)
                error_messages.append(error_msg)
            else:
                # Fallback for unexpected results
                translations.append(batch_groups[len(translations)])
                success_flags.append(False)
                error_messages.append("Unexpected error occurred")

        return translations, success_flags, error_messages

    def translate_texts(
        self,
        texts: List[str],
        target_language: str,
        source_language: str = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[str]:
        """Translate list of texts with concurrent processing for maximum performance"""
        if not texts:
            return []

        # Split into batches
        batches = [
            texts[i : i + self.batch_size]
            for i in range(0, len(texts), self.batch_size)
        ]

        total_batches = len(batches)
        all_translations = []

        async def translate_all_batches():
            # Use concurrent processing instead of sequential
            translated_batch_results, success_flags, error_messages = (
                await self.translate_batches_concurrent(
                    batches, target_language, source_language
                )
            )

            # Process results
            for batch_idx, (translated_batch, success, error_msg) in enumerate(
                zip(translated_batch_results, success_flags, error_messages)
            ):
                if progress_callback:
                    progress_callback(batch_idx + 1, total_batches)

                all_translations.extend(translated_batch)

                # Log errors if needed (you can add error callback here)
                if not success and error_msg:
                    print(f"Warning: Batch {batch_idx + 1} failed: {error_msg}")

        asyncio.run(translate_all_batches())
        return all_translations
