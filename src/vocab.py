#!/usr/bin/env python3
"""Vocabulary service with SM-2 algorithm."""

import os
import time
from typing import Optional
from db import Database, Word, Translation, Language
from translation import ProviderRegistry
from constants import AUTOSTART_DIR, AUTOSTART_FILE, APP_NAME
from wotd import get_word_source, WordSourceType


class VocabService:
    """Vocabulary service with spaced repetition."""

    def __init__(self, db_path: str):
        self.db = Database(db_path)
        self.db.connect()
        self.db.init_schema()

    def get_settings(self) -> dict:
        """Get app settings."""
        return {
            "review_interval": int(self.db.get_setting("review_interval", "3600")),
            "source_lang": self.db.get_setting("source_lang", "en"),
            "target_lang": self.db.get_setting("target_lang", "ru"),
            "translation_provider": self.db.get_setting("translation_provider", "google_direct"),
        }

    def get_languages(self) -> list:
        """Get all available languages."""
        return self.db.get_all_languages()

    def save_settings(self, settings: dict):
        """Save app settings."""
        for key, value in settings.items():
            self.set_setting(key, str(value))
        
        if "autostart" in settings:
            self._set_autostart(settings["autostart"] == "true")

    def set_setting(self, key: str, value: str):
        """Set a single setting."""
        self.db.set_setting(key, value)

    def get_setting(self, key: str, default: str = None) -> str:
        """Get a single setting."""
        return self.db.get_setting(key, default)

    def _set_autostart(self, enable: bool):
        """Enable or disable autostart."""
        if enable:
            os.makedirs(AUTOSTART_DIR, exist_ok=True)
            script_path = os.path.dirname(os.path.abspath(__file__))
            # venv is in project root, not in src/
            venv_python = os.path.join(os.path.dirname(script_path), "venv", "bin", "python3")
            exec_path = os.path.join(script_path, "vocab_gui.py")
            
            if os.path.exists(venv_python):
                python_exec = venv_python
            else:
                python_exec = "python3"
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Vocab App
Exec={python_exec} {exec_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            with open(AUTOSTART_FILE, "w") as f:
                f.write(desktop_content)
        else:
            if os.path.exists(AUTOSTART_FILE):
                os.remove(AUTOSTART_FILE)

    def add_word(self, phrase: str, translation: str = None, auto_translate: bool = False) -> dict:
        """Add a new word or add translation to existing word.
        
        Args:
            phrase: The word/phrase to add
            translation: Optional manual translation
            auto_translate: If True, auto-translate when no translation provided
            
        Returns:
            dict with word info (id, phrase)
        """
        phrase = phrase.strip().lower()

        existing = self.db.get_word_by_phrase(phrase)
        
        if existing:
            # Word exists - add/update translation if provided or auto_translate
            target_lang = self.db.get_setting("target_lang", "ru") or "ru"

            if translation:
                self.db.add_translation(existing["id"], translation, target_lang)
            elif auto_translate:
                provider_name = self.db.get_setting("translation_provider", "google_direct") or "google_direct"
                source_lang = self.db.get_setting("source_lang", "en") or "en"
                provider = ProviderRegistry.get(provider_name)
                trans = provider.translate(phrase, target_lang, source_lang)
                if trans:
                    self.db.add_translation(existing["id"], trans, target_lang)
            return existing

        # New word
        word_id = self.db.add_word(phrase)

        if translation:
            target_lang = self.db.get_setting("target_lang", "ru") or "ru"
            self.db.add_translation(word_id, translation, target_lang)
        elif auto_translate:
            provider_name = self.db.get_setting("translation_provider", "google_direct") or "google_direct"
            source_lang = self.db.get_setting("source_lang", "en") or "en"
            provider = ProviderRegistry.get(provider_name)
            target_lang = self.db.get_setting("target_lang", "ru") or "ru"
            trans = provider.translate(phrase, target_lang, source_lang)
            if trans:
                self.db.add_translation(word_id, trans, target_lang)

        return self.db.get_word_by_phrase(phrase)

    def get_next_word(self) -> Optional[dict]:
        """Get next word due for review with translation in current target language."""
        target_lang = self.db.get_setting("target_lang", "ru") or "ru"
        words = self.db.get_due_words(limit=10, target_lang=target_lang)
        return words[0] if words else None

    def review_word(self, word_id: int, quality: int = 3):
        """Review a word with SM-2 quality rating (0-5).

        Quality values:
        0 - complete blackout
        1 - incorrect response, correct one remembered
        2 - incorrect response, correct one seemed easy
        3 - correct response with serious difficulty
        4 - correct response after hesitation
        5 - perfect response
        """
        stats = self.db.get_word_stats(word_id)

        if stats:
            interval = stats["interval_days"]
            ease = stats["ease_factor"]
            due = stats.get("due_date", 0)
        else:
            interval = 1
            ease = 2.5
            due = 0

        now = int(time.time())

        # SM-2 algorithm
        if quality < 3:
            # Failed - reset interval
            new_interval = 1
            new_ease = max(1.3, ease - 0.2)
        else:
            # Passed - increase interval
            new_ease = ease + 0.1 - (quality - 3) * 0.08
            new_ease = max(1.3, new_ease)

            if due == 0 or now >= due:
                new_interval = int(interval * new_ease * 0.5)
                new_interval = max(1, new_interval)
            else:
                # Normal progression
                new_interval = int(interval * new_ease)
                new_interval = min(new_interval, 180)  # Max 180 days

        new_due = now + new_interval * 86400

        self.db.update_word_stats(word_id, new_interval, new_due, new_ease)
        self.db.record_review(word_id)

    def skip_word(self, word_id: int):
        """Skip word - move to end of queue by updating due date."""
        self.db.record_review(word_id)
        
        # Update due date to push to end of queue (small interval)
        stats = self.db.get_word_stats(word_id)
        if stats:
            current_interval = stats.get("interval_days", 1)
        else:
            current_interval = 1
        
        # Move due date forward by a small amount (10 minutes) to deprioritize
        new_due = int(time.time()) + 600  # 10 minutes from now
        
        self.db.update_word_stats(word_id, current_interval, new_due, stats.get("ease_factor", 2.5) if stats else 2.5)

    def delete_word(self, phrase: str):
        """Delete a word."""
        self.db.delete_word(phrase)

    def get_translation(self, word_id: int) -> Optional[str]:
        """Get translation for a word."""
        target_lang = self.db.get_setting("target_lang", "ru") or "ru"
        return self.db.get_translation(word_id, target_lang)

    def get_language_abbreviation(self, lang_code: str) -> str:
        """Get language abbreviation for a code."""
        lang = self.db.get_language_by_code(lang_code)
        return lang.abbreviation if lang else lang_code.upper()

    def format_interval(self, interval: int) -> str:
        """Format interval days to human-readable string."""
        if interval == 1:
            return "1 day"
        elif interval < 30:
            return f"{interval} days"
        elif interval < 365:
            return f"{interval // 30} mo"
        else:
            return f"{interval // 365} yr"

    def get_next_word_notification(self) -> Optional[str]:
        """Get next word and format notification body. Also saves phrase to temp file.
        
        Returns:
            Notification body string or None if no word
        """
        word = self.get_next_word()
        if not word:
            return None
        
        phrase = word.get("phrase", "")
        interval = word.get("interval_days", 1)
        
        translation, trans_lang = self.get_translation_with_lang(word["id"])
        
        interval_str = self.format_interval(interval)
        abbrev = self.get_language_abbreviation(trans_lang) if trans_lang else "—"
        
        body = f"<b>{phrase}</b> [{interval_str}]"
        if translation:
            body += f"\n→ {translation} [{abbrev}]"
        
        # Save to temp file for --delete hotkey
        from constants import TEMP_PHRASE_FILE
        with open(TEMP_PHRASE_FILE, "w") as f:
            f.write(phrase)
        
        # Skip word after getting it
        self.skip_word(word["id"])
        
        return body

    def get_translation_with_lang(self, word_id: int) -> tuple[Optional[str], Optional[str]]:
        """Get translation and its language code."""
        target_lang = self.db.get_setting("target_lang", "ru") or "ru"
        translation = self.db.get_translation(word_id, target_lang)
        return translation, target_lang

    def get_words(self, search: str = None, target_lang: str = None) -> list:
        """Get all words with optional search and language filter."""
        return self.db.get_all_words(search, target_lang)

    def update_word(self, word_id: int, phrase: str, translation: str = None):
        """Update word phrase and optionally translation."""
        word = self.db.session.query(Word).filter_by(id=word_id).first()
        if word:
            word.phrase = phrase.lower()
            if translation:
                target_lang = self.db.get_setting("target_lang", "ru") or "ru"
                lang = self.db.get_language_by_code(target_lang)
                if lang:
                    existing_trans = self.db.session.query(Translation).filter_by(
                        word_id=word_id, language_id=lang.id
                    ).first()
                    if existing_trans:
                        existing_trans.translation = translation
                    else:
                        trans = Translation(word_id=word_id, language_id=lang.id, translation=translation)
                        self.db.session.add(trans)
            self.db._commit()

    def delete_word_by_id(self, word_id: int):
        """Delete a word by ID."""
        word = self.db.session.query(Word).filter_by(id=word_id).first()
        if word:
            self.db.session.delete(word)
            self.db._commit()

    def delete_translation(self, word_id: int, target_lang: str):
        """Delete only translation for specific language, not the word.
        If no translations left, delete the word itself."""
        lang = self.db.get_language_by_code(target_lang)
        if lang:
            trans = self.db.session.query(Translation).filter_by(
                word_id=word_id, language_id=lang.id
            ).first()
            if trans:
                self.db.session.delete(trans)
                
                # Check if word has any other translations
                remaining = self.db.session.query(Translation).filter_by(word_id=word_id).count()
                if remaining == 0:
                    # No translations left, delete the word
                    word = self.db.session.query(Word).filter_by(id=word_id).first()
                    if word:
                        self.db.session.delete(word)
                
                self.db._commit()

    def close(self):
        """Close database connection."""
        self.db.close()

    def remove_session(self):
        """Remove database session (for thread cleanup)."""
        self.db.remove_session()

    def get_language_counts(self) -> dict:
        """Get word count per language."""
        return self.db.get_language_counts()

    def get_stats(self) -> dict:
        """Get statistics."""
        return self.db.get_stats()

    def test_translation_api(self) -> bool:
        """Test if translation API works."""
        try:
            provider_name = self.db.get_setting("translation_provider", "google_direct")
            provider = ProviderRegistry.get(provider_name)
            source_lang = self.db.get_setting("source_lang", "en") or "en"
            target_lang = self.db.get_setting("target_lang", "ru") or "ru"
            result = provider.translate("hello", target_lang, source_lang)
            return bool(result)
        except:
            return False

    def export_csv(self, filepath: str):
        """Export words to CSV."""
        self.db.export_csv(filepath)

    def is_wotd_enabled(self) -> bool:
        """Check if Word of the Day is enabled."""
        enabled = self.db.get_setting("wotd_enabled", "false")
        return enabled == "true"

    def get_wotd_level(self) -> str:
        """Get the configured WOTD level."""
        return self.db.get_setting("wotd_level", "B2")

    def get_word_of_the_day(self) -> Optional[dict]:
        """Get Word of the Day with translation.
        
        Returns:
            dict with word, level, translation, or None if disabled or translation fails
        """
        if not self.is_wotd_enabled():
            return None

        if self.db.get_wotd_today():
            return None

        level = self.get_wotd_level()
        source = get_word_source(WordSourceType.LOCAL)
        
        word_data = source.get_word(level)
        if not word_data:
            return None

        word = word_data["word"]
        word_level = word_data["level"]

        provider_name = self.db.get_setting("translation_provider", "google_direct")
        provider = ProviderRegistry.get(provider_name)
        source_lang = self.db.get_setting("source_lang", "en") or "en"
        target_lang = self.db.get_setting("target_lang", "ru")

        translation = provider.translate(word, target_lang, source_lang)
        
        if not translation:
            return None

        self.db.mark_wotd_shown(word, word_level)

        return {
            "word": word,
            "level": word_level,
            "translation": translation,
            "target_lang": target_lang
        }

    def get_quiz_words(self, count: int, lang_code: str, pool: str = "all") -> list:
        """Get words for a quiz."""
        return self.db.get_quiz_words(count, lang_code, pool)

    def count_words_with_translation(self, lang_code: str) -> int:
        """Count words that have a translation in the given language."""
        return self.db.count_words_with_translation(lang_code)

    def start_quiz_session(self, quiz_type: str, lang_code: str, total: int) -> int:
        """Create a quiz session, return its ID."""
        return self.db.create_quiz_session(quiz_type, lang_code, total)

    def record_quiz_answer(self, session_id: int, word_id: int, correct: bool,
                           response_ms: int, correct_answer: str, user_answer: str):
        """Record a quiz answer and update spaced repetition stats."""
        self.db.record_quiz_answer(session_id, word_id, correct, response_ms,
                                   correct_answer, user_answer)
        # Update SM-2: correct = quality 4, wrong = quality 1
        self.review_word(word_id, quality=4 if correct else 1)

    def finish_quiz_session(self, session_id: int):
        """Finish a quiz session."""
        self.db.finish_quiz_session(session_id)

    def get_quiz_history(self, limit: int = 20) -> list:
        """Get recent quiz sessions."""
        return self.db.get_quiz_history(limit)

    def get_quiz_session_detail(self, session_id: int):
        """Get full quiz session detail."""
        return self.db.get_quiz_session_detail(session_id)

    def get_quiz_stats(self) -> dict:
        """Get aggregate quiz stats."""
        return self.db.get_quiz_stats()

    def save_wotd_to_vocab(self, word: str, translation: str = None) -> tuple[dict|None, bool]:
        """Save WOTD word to user's vocabulary.
        
        Returns:
            tuple of (result dict, success bool)
        """
        try:
            result = self.add_word(word, translation, auto_translate=(translation is None))
            return result, True
        except Exception as e:
            print(f"Failed to save WOTD to vocab: {e}")
            return None, False
