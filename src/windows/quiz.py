#!/usr/bin/env python3
"""Quiz windows: setup, quiz, and results."""

import random
import time
from difflib import SequenceMatcher

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango


def _normalize(text):
    """Normalize text for comparison."""
    return text.strip().lower()


def _check_answer(user_input, correct_answer):
    """Check answer with typo tolerance.

    Returns:
        (is_correct, is_typo) - is_typo means accepted but with a typo
    """
    u = _normalize(user_input)
    c = _normalize(correct_answer)
    if not u:
        return False, False
    if u == c:
        return True, False
    # Allow typo: similarity >= 0.8 and at least 3 chars
    if len(c) >= 3:
        ratio = SequenceMatcher(None, u, c).ratio()
        if ratio >= 0.8:
            return True, True
    return False, False


class QuizSetupWindow(Gtk.Window):
    """Quiz setup screen."""

    def __init__(self, vocab_service):
        super().__init__(title="Vocabulary Quiz")
        self.vocab_service = vocab_service
        self.set_default_size(400, 380)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.build_ui()

    def build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_left(20)
        box.set_margin_right(20)
        self.add(box)

        # Title
        title = Gtk.Label()
        title.set_markup("<b>Quiz Setup</b>")
        box.pack_start(title, False, False, 0)

        # Language
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lang_box.pack_start(Gtk.Label("Language:"), False, False, 0)
        self.lang_combo = Gtk.ComboBoxText()
        settings = self.vocab_service.get_settings()
        current_lang = settings.get("target_lang", "ru")
        lang_counts = self.vocab_service.get_language_counts()

        # Add current language first
        current_count = lang_counts.get(current_lang, (None, 0))[1]
        if current_count > 0:
            self.lang_combo.append(current_lang, f"{current_lang.upper()} ({current_count})")

        languages = self.vocab_service.get_languages()
        for lang in sorted(languages, key=lambda l: l.name):
            if lang.code == current_lang:
                continue
            name, count = lang_counts.get(lang.code, (lang.name, 0))
            if count > 0:
                self.lang_combo.append(lang.code, f"{name} ({count})")

        self.lang_combo.set_active_id(current_lang if current_count > 0 else None)
        self.lang_combo.connect("changed", self._on_lang_changed)
        lang_box.pack_start(self.lang_combo, True, True, 0)
        box.pack_start(lang_box, False, False, 0)

        # Question count
        count_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        count_box.pack_start(Gtk.Label("Questions:"), False, False, 0)
        self.count_combo = Gtk.ComboBoxText()
        for n in ["5", "10", "20", "All"]:
            self.count_combo.append(n, n)
        self.count_combo.set_active_id("10")
        count_box.pack_start(self.count_combo, True, True, 0)
        box.pack_start(count_box, False, False, 0)

        # Quiz type
        type_frame = Gtk.Frame(label="Direction")
        type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        type_box.set_margin_top(8)
        type_box.set_margin_bottom(8)
        type_box.set_margin_left(8)
        type_box.set_margin_right(8)
        source_lang = settings.get("source_lang", "en").upper()
        self.type_en = Gtk.RadioButton.new_with_label(None, f"{source_lang} -> Translation")
        self.type_trans = Gtk.RadioButton.new_with_label_from_widget(self.type_en, f"Translation -> {source_lang}")
        self.type_mixed = Gtk.RadioButton.new_with_label_from_widget(self.type_en, "Mixed")
        type_box.pack_start(self.type_en, False, False, 0)
        type_box.pack_start(self.type_trans, False, False, 0)
        type_box.pack_start(self.type_mixed, False, False, 0)
        type_frame.add(type_box)
        box.pack_start(type_frame, False, False, 0)

        # Word pool
        pool_frame = Gtk.Frame(label="Word Pool")
        pool_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pool_box.set_margin_top(8)
        pool_box.set_margin_bottom(8)
        pool_box.set_margin_left(8)
        pool_box.set_margin_right(8)
        self.pool_all = Gtk.RadioButton.new_with_label(None, "All words (random)")
        self.pool_due = Gtk.RadioButton.new_with_label_from_widget(self.pool_all, "Due words first")
        self.pool_weak = Gtk.RadioButton.new_with_label_from_widget(self.pool_all, "Weakest words")
        pool_box.pack_start(self.pool_all, False, False, 0)
        pool_box.pack_start(self.pool_due, False, False, 0)
        pool_box.pack_start(self.pool_weak, False, False, 0)
        pool_frame.add(pool_box)
        box.pack_start(pool_frame, False, False, 0)

        # Status / warning
        self.status_label = Gtk.Label("")
        self.status_label.set_xalign(0)
        box.pack_start(self.status_label, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.start_btn = Gtk.Button(label="Start Quiz")
        self.start_btn.connect("clicked", self._on_start)
        btn_box.pack_end(self.start_btn, False, False, 0)

        history_btn = Gtk.Button(label="Quiz History")
        history_btn.connect("clicked", self._on_history)
        btn_box.pack_start(history_btn, False, False, 0)

        box.pack_start(btn_box, False, False, 0)

        self._update_status()

    def _on_lang_changed(self, widget):
        self._update_status()

    def _update_status(self):
        lang = self.lang_combo.get_active_id()
        if not lang:
            self.status_label.set_text("Select a language")
            self.start_btn.set_sensitive(False)
            return
        count = self.vocab_service.count_words_with_translation(lang)
        if count == 0:
            self.status_label.set_text("No words with translations in this language")
            self.start_btn.set_sensitive(False)
        else:
            self.status_label.set_text(f"{count} words available")
            self.start_btn.set_sensitive(True)

    def _get_quiz_type(self):
        if self.type_en.get_active():
            return "source_to_target"
        if self.type_trans.get_active():
            return "target_to_source"
        return "mixed"

    def _get_pool(self):
        if self.pool_due.get_active():
            return "due"
        if self.pool_weak.get_active():
            return "weakest"
        return "all"

    def _on_start(self, widget):
        lang = self.lang_combo.get_active_id()
        if not lang:
            return

        count_str = self.count_combo.get_active_id()
        count = 0 if count_str == "All" else int(count_str)

        quiz_type = self._get_quiz_type()
        pool = self._get_pool()

        words = self.vocab_service.get_quiz_words(count, lang, pool)
        if not words:
            self.status_label.set_text("No words found")
            return

        win = QuizWindow(self.vocab_service, words, quiz_type, lang)
        win.show_all()
        self.destroy()

    def _on_history(self, widget):
        win = QuizHistoryWindow(self.vocab_service)
        win.show_all()


class QuizWindow(Gtk.Window):
    """Active quiz screen."""

    def __init__(self, vocab_service, words, quiz_type, lang_code):
        super().__init__(title="Quiz")
        self.vocab_service = vocab_service
        self.words = words
        self.quiz_type = quiz_type
        self.lang_code = lang_code
        self.current_idx = 0
        self.results = []  # list of dicts per question
        self.quiz_start = time.time()
        self.question_start = None
        self._advance_timeout = None

        self.session_id = self.vocab_service.start_quiz_session(
            quiz_type, lang_code, len(words)
        )

        self.set_default_size(500, 300)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.build_ui()
        self._show_question()

    def build_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_box.set_margin_top(20)
        self.main_box.set_margin_bottom(20)
        self.main_box.set_margin_left(20)
        self.main_box.set_margin_right(20)
        self.add(self.main_box)

        # Progress
        self.progress_label = Gtk.Label("")
        self.main_box.pack_start(self.progress_label, False, False, 0)

        self.progress_bar = Gtk.ProgressBar()
        self.main_box.pack_start(self.progress_bar, False, False, 0)

        # Prompt
        self.prompt_label = Gtk.Label("")
        self.prompt_label.set_line_wrap(True)
        self.prompt_label.modify_font(Pango.FontDescription("18"))
        self.main_box.pack_start(self.prompt_label, True, True, 0)

        # Answer entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.answer_entry = Gtk.Entry()
        self.answer_entry.set_placeholder_text("Type your answer...")
        self.answer_entry.connect("activate", self._on_submit)
        entry_box.pack_start(self.answer_entry, True, True, 0)

        self.submit_btn = Gtk.Button(label="Submit")
        self.submit_btn.connect("clicked", self._on_submit)
        entry_box.pack_start(self.submit_btn, False, False, 0)

        self.main_box.pack_start(entry_box, False, False, 0)

        # Feedback label
        self.feedback_label = Gtk.Label("")
        self.feedback_label.set_line_wrap(True)
        self.main_box.pack_start(self.feedback_label, False, False, 0)

        # Bottom buttons
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.skip_btn = Gtk.Button(label="Skip")
        self.skip_btn.connect("clicked", self._on_skip)
        bottom.pack_start(self.skip_btn, False, False, 0)

        self.quit_btn = Gtk.Button(label="End Quiz")
        self.quit_btn.connect("clicked", self._on_end_quiz)
        bottom.pack_end(self.quit_btn, False, False, 0)

        self.main_box.pack_start(bottom, False, False, 0)

    def _get_direction(self):
        """Get direction for current question."""
        if self.quiz_type == "source_to_target":
            return "source_to_target"
        if self.quiz_type == "target_to_source":
            return "target_to_source"
        # mixed
        return random.choice(["source_to_target", "target_to_source"])

    def _show_question(self):
        if self.current_idx >= len(self.words):
            self._finish_quiz()
            return

        word = self.words[self.current_idx]
        direction = self._get_direction()
        self._current_direction = direction

        total = len(self.words)
        self.progress_label.set_text(f"Question {self.current_idx + 1} / {total}")
        self.progress_bar.set_fraction((self.current_idx) / total)

        if direction == "source_to_target":
            prompt = word["phrase"]
            self._correct_answer = word["translation"]
        else:
            prompt = word["translation"]
            self._correct_answer = word["phrase"]

        self.prompt_label.set_markup(f"<b>{prompt}</b>")
        self.answer_entry.set_text("")
        self.answer_entry.set_sensitive(True)
        self.submit_btn.set_sensitive(True)
        self.skip_btn.set_sensitive(True)
        self.feedback_label.set_text("")
        self.answer_entry.grab_focus()
        self.question_start = time.time()

    def _on_submit(self, widget):
        user_answer = self.answer_entry.get_text().strip()
        if not user_answer:
            return
        response_ms = int((time.time() - self.question_start) * 1000)
        is_correct, is_typo = _check_answer(user_answer, self._correct_answer)
        self._record_answer(is_correct, response_ms, user_answer)

        if is_correct and is_typo:
            self.feedback_label.set_markup(
                f'<span foreground="green">Correct!</span> (typo: expected "{self._correct_answer}")'
            )
        elif is_correct:
            self.feedback_label.set_markup('<span foreground="green">Correct!</span>')
        else:
            self.feedback_label.set_markup(
                f'<span foreground="red">Wrong</span> — correct answer: <b>{self._correct_answer}</b>'
            )

        self.answer_entry.set_sensitive(False)
        self.submit_btn.set_sensitive(False)
        self.skip_btn.set_sensitive(False)

        delay = 1000 if is_correct else 2000
        self._advance_timeout = GLib.timeout_add(delay, self._advance)

    def _on_skip(self, widget):
        response_ms = int((time.time() - self.question_start) * 1000)
        self._record_answer(False, response_ms, "")
        self.feedback_label.set_markup(
            f'<span foreground="orange">Skipped</span> — answer: <b>{self._correct_answer}</b>'
        )
        self.answer_entry.set_sensitive(False)
        self.submit_btn.set_sensitive(False)
        self.skip_btn.set_sensitive(False)
        self._advance_timeout = GLib.timeout_add(1500, self._advance)

    def _record_answer(self, correct, response_ms, user_answer):
        word = self.words[self.current_idx]
        self.vocab_service.record_quiz_answer(
            self.session_id, word["id"], correct, response_ms,
            self._correct_answer, user_answer,
        )
        self.results.append({
            "phrase": word["phrase"],
            "translation": word["translation"],
            "correct": correct,
            "response_ms": response_ms,
            "correct_answer": self._correct_answer,
            "user_answer": user_answer,
            "direction": self._current_direction,
        })

    def _advance(self):
        self._advance_timeout = None
        self.current_idx += 1
        self._show_question()
        return False

    def _on_end_quiz(self, widget):
        self._finish_quiz()

    def _finish_quiz(self):
        if self._advance_timeout:
            GLib.source_remove(self._advance_timeout)
            self._advance_timeout = None
        self.vocab_service.finish_quiz_session(self.session_id)
        total_time = time.time() - self.quiz_start
        win = QuizResultsWindow(self.vocab_service, self.session_id,
                                self.results, total_time)
        win.show_all()
        self.destroy()


class QuizResultsWindow(Gtk.Window):
    """Quiz results screen."""

    def __init__(self, vocab_service, session_id, results, total_time):
        super().__init__(title="Quiz Results")
        self.vocab_service = vocab_service
        self.session_id = session_id
        self.results = results
        self.total_time = total_time
        self.set_default_size(600, 500)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.build_ui()

    def build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_left(20)
        box.set_margin_right(20)
        self.add(box)

        # Score
        correct = sum(1 for r in self.results if r["correct"])
        total = len(self.results)
        pct = (correct / total * 100) if total > 0 else 0

        score_label = Gtk.Label()
        score_label.set_markup(f"<big><b>{correct} / {total} ({pct:.0f}%)</b></big>")
        box.pack_start(score_label, False, False, 0)

        # Time
        minutes = int(self.total_time) // 60
        seconds = int(self.total_time) % 60
        time_label = Gtk.Label(f"Time: {minutes}m {seconds}s")
        box.pack_start(time_label, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 5)

        # Per-word breakdown
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        box.pack_start(scrolled, True, True, 0)

        model = Gtk.ListStore(str, str, str, str, str)
        treeview = Gtk.TreeView(model=model)

        columns = [
            ("", 30),
            ("Prompt", 180),
            ("Your Answer", 180),
            ("Correct Answer", 180),
            ("Time", 60),
        ]
        for i, (title, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, renderer, text=i)
            col.set_fixed_width(width)
            treeview.append_column(col)

        for r in self.results:
            mark = "+" if r["correct"] else "-"
            if r["direction"] == "source_to_target":
                prompt = r["phrase"]
            else:
                prompt = r["translation"]
            user_ans = r["user_answer"] or "(skipped)"
            time_str = f"{r['response_ms'] / 1000:.1f}s"
            model.append([mark, prompt, user_ans, r["correct_answer"], time_str])

        scrolled.add(treeview)

        # Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Retry mistakes
        wrong = [r for r in self.results if not r["correct"]]
        if wrong:
            retry_btn = Gtk.Button(label=f"Retry Mistakes ({len(wrong)})")
            retry_btn.connect("clicked", self._on_retry)
            btn_box.pack_start(retry_btn, False, False, 0)

        new_btn = Gtk.Button(label="New Quiz")
        new_btn.connect("clicked", self._on_new)
        btn_box.pack_start(new_btn, False, False, 0)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda w: self.destroy())
        btn_box.pack_end(close_btn, False, False, 0)

        box.pack_start(btn_box, False, False, 0)

    def _on_retry(self, widget):
        wrong = [r for r in self.results if not r["correct"]]
        words = [
            {"id": r.get("word_id", 0), "phrase": r["phrase"], "translation": r["translation"]}
            for r in wrong
        ]
        # Get word IDs from the session detail
        detail = self.vocab_service.get_quiz_session_detail(self.session_id)
        if detail:
            id_map = {a["phrase"]: a["word_id"] for a in detail["answers"]}
            for w in words:
                w["id"] = id_map.get(w["phrase"], w["id"])

        win = QuizWindow(self.vocab_service, words,
                         detail["quiz_type"] if detail else "mixed",
                         detail["language_code"] if detail else "ru")
        win.show_all()
        self.destroy()

    def _on_new(self, widget):
        win = QuizSetupWindow(self.vocab_service)
        win.show_all()
        self.destroy()


class QuizHistoryWindow(Gtk.Window):
    """Quiz history list."""

    def __init__(self, vocab_service):
        super().__init__(title="Quiz History")
        self.vocab_service = vocab_service
        self.set_default_size(550, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.build_ui()

    def build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(15)
        box.set_margin_bottom(15)
        box.set_margin_left(15)
        box.set_margin_right(15)
        self.add(box)

        # Aggregate stats
        stats = self.vocab_service.get_quiz_stats()
        stats_label = Gtk.Label()
        stats_label.set_markup(
            f"Total quizzes: <b>{stats['total_quizzes']}</b>  |  "
            f"Avg score: <b>{stats['avg_score']}%</b>  |  "
            f"Best: <b>{stats['best_score']}%</b>"
        )
        box.pack_start(stats_label, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(sep, False, False, 5)

        # History list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        box.pack_start(scrolled, True, True, 0)

        model = Gtk.ListStore(str, str, str, str, str)
        treeview = Gtk.TreeView(model=model)

        columns = [
            ("Date", 140),
            ("Type", 100),
            ("Lang", 50),
            ("Score", 80),
            ("Questions", 80),
        ]
        for i, (title, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(title, renderer, text=i)
            col.set_fixed_width(width)
            treeview.append_column(col)

        from datetime import datetime, timezone
        history = self.vocab_service.get_quiz_history(50)
        for s in history:
            dt = datetime.fromtimestamp(s["finished_at"], tz=timezone.utc)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
            type_map = {"source_to_target": "Src->Tgt", "target_to_source": "Tgt->Src", "mixed": "Mixed"}
            type_str = type_map.get(s["quiz_type"], s["quiz_type"])
            score_str = f"{s['score_pct']:.0f}%"
            q_str = f"{s['correct_count']}/{s['total_questions']}"
            model.append([date_str, type_str, s["language_code"].upper(), score_str, q_str])

        scrolled.add(treeview)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda w: self.destroy())
        box.pack_start(close_btn, False, False, 0)
