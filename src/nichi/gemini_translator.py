"""
Google Gemini translation service
High-performance translator for SRT subtitles with concurrent processing
"""

import os
import re
import asyncio
import random
from typing import List, Callable, Optional, Tuple
import google.generativeai as genai
from google.api_core.exceptions import (
    ResourceExhausted,
    GoogleAPICallError,
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

        # Configure model
        model_name = EnvLoader.get_config_value(
            "GEMINI_MODEL_NAME", "gemini-2.0-flash-exp"
        )
        self.model = genai.GenerativeModel(model_name)

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

    def get_language_name(self, code: str) -> str:
        """Get full language name from code"""
        return self.LANGUAGES.get(code.lower(), code)

    async def translate_batch(
        self, texts: List[str], target_language: str, source_language: str = None
    ) -> List[str]:
        """Translate a batch of texts using optimized parsing"""
        if not texts:
            return []

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

        prompt = f"""
        Translate the following subtitle text from {source_lang_str} to {target_lang_str}.

        Instructions:
        1. Maintain original tone and style
        2. Keep non-dialogue cues like [music] or (laughs) unchanged
        3. Translate idioms to natural equivalents, not literally
        4. Use proper gender-specific terms when needed
        5. For multi-line subtitles, preserve line breaks
        6. Return ONLY the numbered translations, no explanations

        Text to translate:
        {batch_text}
        """

        response = await asyncio.to_thread(self.model.generate_content, prompt)

        if not response or not response.text:
            return texts  # Return original if no response

        # Enhanced parsing logic from the old code
        translated_content = response.text.strip()
        translations = []
        lines = translated_content.split("\n")
        current_translation = ""
        current_number = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line starts with the expected number
            number_match = re.match(rf"^{current_number}\.\s*(.*)", line)
            if number_match:
                # If we have a previous translation, save it
                if current_translation and len(translations) == current_number - 2:
                    translations.append(current_translation.strip())

                # Start new translation
                current_translation = number_match.group(1)
                current_number += 1
            else:
                # This is a continuation of the current translation
                if current_translation:
                    current_translation += "\n" + line
                else:
                    # Orphaned line - treat as standalone translation
                    current_translation = line

        # Don't forget the last translation
        if current_translation:
            translations.append(current_translation.strip())

        # Fallback parsing if the above didn't work well
        if len(translations) != len(texts):
            translation_lines = [
                line for line in translated_content.split("\n") if line.strip()
            ]
            translations = []

            for i, original_text in enumerate(texts):
                if i < len(translation_lines):
                    # Clean the numbered prefix
                    clean_translation = re.sub(
                        r"^\d+\.\s*", "", translation_lines[i].strip()
                    )
                    translations.append(
                        clean_translation if clean_translation else original_text
                    )
                else:
                    translations.append(original_text)

        # Ensure we have the same number of translations as input
        final_translations = translations[: len(texts)]
        while len(final_translations) < len(texts):
            final_translations.append(texts[len(final_translations)])

        return final_translations

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
