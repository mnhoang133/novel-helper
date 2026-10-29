"""
Module: app_gui
Description: Main GUI Application for Universal Novel Scraper & Physical Book Publisher.
             Coordinates UI tabs, background threads, and core engines.
Author: Google Deepmind Agent
"""

import os
import re
import sys
import json
import glob
import queue
import threading
import subprocess
from datetime import datetime
from typing import Optional, List, Dict

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Import core business engines
from core.scraper import NovelScraper, derive_pattern_from_url
from core.cleaner import repair_file_inplace, sanitize_xml_string
from core.book_engine import (
    scan_and_collect_chapters,
    detect_chapter_range_from_folder,
    split_chapters_into_volumes,
    export_single_document,
    convert_docx_to_pdf,
    VolumeSplitOption,
    calculate_lines_per_page,
    calculate_chars_per_line,
    calculate_toc_entries_per_page,
    generate_export_diagnostics
)
from core.session_manager import (
    APP_DIR,
    SESSION_FILE,
    DEFAULT_CONFIG,
    load_session,
    save_session,
    discover_novel_folders
)

# Import UI builders and theme system
from ui.theme import (
    setup_segmented_button_style,
    update_console_colors
)
from ui.tab_scraper import build_scraper_tab
from ui.tab_publisher import build_publisher_tab
from ui.smart_analyzer_dialog import SmartVolumeAnalyzerDialog

# Initial Appearance Setup
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


class ModernNovelApp(ctk.CTk):
    """
    Main Application Window.
    Coordinates the Web Scraper, Physical Book Publisher, and Console Monitor.
    """
    def __init__(self):
        super().__init__()
        self.title("Universal Novel Scraper & Physical Book Publisher")
        self.geometry("980x850")
        self.minsize(940, 800)

        # Window background: Zinc-slate in light, deep obsidian in dark
        self.configure(fg_color=("#eceff4", "#0b0f19"))

        # State tracking
        self.active_scraper: Optional[NovelScraper] = None
        self.log_queue = queue.Queue()
        self.exported_files: List[str] = []
        self.novel_paths_map: Dict[str, str] = {}
        self.saved_novel_configs: Dict[str, dict] = {}
        self._is_scraping = False
        self._is_publishing = False

        self._build_ui()
        self._load_startup_config()

        # Apply initial theme styling to custom components
        self._apply_theme("Light")

        # Save session when window is closed
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Thread-safe log processing loop
        self.after(100, self._process_log_queue)

    def _build_ui(self):
        # ----------------- HEADER BANNER & THEME SWITCH -----------------
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(10, 4))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="y")

        lbl_title = ctk.CTkLabel(
            title_box,
            text="Universal Novel Scraper & Physical Book Publisher",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            title_box,
            text="Next.js SSR Extraction & Professional Print-Ready Book Publisher (Mirror Margins & Smart Pagination)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748b", "#94a3b8")
        )
        lbl_sub.pack(anchor="w")

        # Light / Dark Mode Toggle Switch (Top-Right)
        mode_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        mode_box.pack(side="right", anchor="e")

        self.switch_theme = ctk.CTkSwitch(
            mode_box,
            text="Dark Mode",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#334155", "#cbd5e1"),
            progress_color="#18181b",
            fg_color="#cbd5e1",
            command=self._toggle_theme
        )
        self.switch_theme.pack(side="right")
        self.switch_theme.deselect()

        # ----------------- MAIN TABVIEW -----------------
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=8,
            fg_color=("#f4f6f9", "#111827"),
            segmented_button_fg_color=("#e2e8f0", "#1e293b"),
            segmented_button_selected_color=("#18181b", "#f8fafc"),
            segmented_button_selected_hover_color=("#27272a", "#e2e8f0"),
            segmented_button_unselected_color=("#e2e8f0", "#1e293b"),
            segmented_button_unselected_hover_color=("#cbd5e1", "#334155")
        )
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        tab_scraper = self.tabview.add("Web Scraper")
        tab_publisher = self.tabview.add("Book Publisher")

        build_scraper_tab(tab_scraper, self)
        build_publisher_tab(tab_publisher, self)
        self._build_bottom_monitor()

        # Hook dynamic button styling for tabview
        setup_segmented_button_style(self.tabview._segmented_button)

        def on_tab_switched():
            if hasattr(self.tabview, '_segmented_button') and hasattr(self.tabview._segmented_button, 'update_styles'):
                self.tabview._segmented_button.update_styles()
        self.tabview.configure(command=on_tab_switched)

    def _build_bottom_monitor(self):
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=16, pady=(0, 10))

        # Progress bar
        prog_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        prog_row.pack(fill="x", pady=(0, 4))

        self.prog_bar = ctk.CTkProgressBar(
            prog_row, height=8, corner_radius=4,
            progress_color=("#18181b", "#38bdf8"), fg_color=("#cbd5e1", "#334155")
        )
        self.prog_bar.set(0)
        self.prog_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.lbl_progress = ctk.CTkLabel(
            prog_row, text="Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#475569", "#94a3b8")
        )
        self.lbl_progress.pack(side="right")

        # Compact terminal log with syntax-colored tags
        self.txt_log = ctk.CTkTextbox(
            bottom_frame,
            height=80,
            corner_radius=8,
            font=("Consolas", 10)
        )
        self.txt_log.pack(fill="x")

    # =========================================================================
    # THEME TOGGLING & BUTTON STYLES
    # =========================================================================
    def _toggle_theme(self):
        if self.switch_theme.get() == 1:
            self._apply_theme("Dark")
        else:
            self._apply_theme("Light")

    def _apply_theme(self, mode: str):
        ctk.set_appearance_mode(mode)

        if hasattr(self, 'switch_theme'):
            if mode == "Dark":
                self.switch_theme.select()
                self.switch_theme.configure(text="Dark Mode")
            else:
                self.switch_theme.deselect()
                self.switch_theme.configure(text="Light Mode")

        # Update segmented buttons
        if hasattr(self, 'tabview') and hasattr(self.tabview, '_segmented_button'):
            if hasattr(self.tabview._segmented_button, 'update_styles'):
                self.tabview._segmented_button.update_styles()

        if hasattr(self, 'seg_split') and hasattr(self.seg_split, 'update_styles'):
            self.seg_split.update_styles()

        # Update action buttons (Start, Stop, Publish)
        self._update_action_button_styles()

        # Update console colors and tags
        if hasattr(self, 'txt_log'):
            update_console_colors(self.txt_log, mode)

    def _update_action_button_styles(self):
        """Dynamically style action buttons (Start, Stop, Publish) based on theme and state."""
        if not hasattr(self, 'btn_start') or not hasattr(self, 'btn_stop') or not hasattr(self, 'btn_publish'):
            return

        mode = ctk.get_appearance_mode()
        is_scraping = bool(getattr(self, '_is_scraping', False))
        is_publishing = bool(getattr(self, '_is_publishing', False))

        # 1. Scraper buttons
        if is_scraping:
            if mode == "Light":
                self.btn_start.configure(
                    state="disabled", fg_color="#e2e8f0", text_color_disabled="#94a3b8",
                    text="SCRAPING IN PROGRESS..."
                )
                self.btn_stop.configure(
                    state="normal", fg_color="#be123c", text_color="#ffffff", hover_color="#9f1239"
                )
            else:
                self.btn_start.configure(
                    state="disabled", fg_color="#1e293b", text_color_disabled="#64748b",
                    text="SCRAPING IN PROGRESS..."
                )
                self.btn_stop.configure(
                    state="normal", fg_color="#e11d48", text_color="#ffffff", hover_color="#be123c"
                )
        else:
            if mode == "Light":
                self.btn_start.configure(
                    state="normal", fg_color="#18181b", text_color="#ffffff", hover_color="#27272a",
                    text="START SCRAPING NOVEL"
                )
                self.btn_stop.configure(
                    state="disabled", fg_color="#e2e8f0", text_color_disabled="#94a3b8"
                )
            else:
                self.btn_start.configure(
                    state="normal", fg_color="#f8fafc", text_color="#0f172a", hover_color="#e2e8f0",
                    text="START SCRAPING NOVEL"
                )
                self.btn_stop.configure(
                    state="disabled", fg_color="#1e293b", text_color_disabled="#64748b"
                )

        # 2. Publisher button
        if is_publishing:
            if mode == "Light":
                self.btn_publish.configure(
                    state="disabled", fg_color="#e2e8f0", text_color_disabled="#94a3b8",
                    text="GENERATING BOOK (PLEASE WAIT)..."
                )
            else:
                self.btn_publish.configure(
                    state="disabled", fg_color="#1e293b", text_color_disabled="#64748b",
                    text="GENERATING BOOK (PLEASE WAIT)..."
                )
        else:
            if mode == "Light":
                self.btn_publish.configure(
                    state="normal", fg_color="#18181b", text_color="#ffffff", hover_color="#27272a",
                    text="GENERATE PRINT-READY BOOK (DOCX / PDF)"
                )
            else:
                self.btn_publish.configure(
                    state="normal", fg_color="#f8fafc", text_color="#0f172a", hover_color="#e2e8f0",
                    text="GENERATE PRINT-READY BOOK (DOCX / PDF)"
                )

    # =========================================================================
    # NOVEL DISCOVERY & PERSISTENCE
    # =========================================================================
    def _refresh_detected_novels(self) -> List[str]:
        self.novel_paths_map = discover_novel_folders()
        names = list(self.novel_paths_map.keys())
        if hasattr(self, 'combo_detected_novels'):
            self.combo_detected_novels.configure(values=names)
        if hasattr(self, 'combo_pub_novels'):
            self.combo_pub_novels.configure(values=names)
        return names

    def _switch_to_novel(self, novel_name: str, folder_path: str):
        if not folder_path or not os.path.isdir(folder_path):
            folder_path = os.path.join(APP_DIR, novel_name)

        self.entry_novel_name.delete(0, "end")
        self.entry_novel_name.insert(0, novel_name)

        self.entry_output_dir.delete(0, "end")
        self.entry_output_dir.insert(0, folder_path)

        self.entry_pub_src_dir.delete(0, "end")
        self.entry_pub_src_dir.insert(0, folder_path)

        if hasattr(self, 'combo_detected_novels'):
            self.combo_detected_novels.set(novel_name)
        if hasattr(self, 'combo_pub_novels'):
            self.combo_pub_novels.set(novel_name)

        clean_title = novel_name.replace("_", " ")
        self.entry_book_title.delete(0, "end")
        self.entry_book_title.insert(0, clean_title)

        if novel_name in self.saved_novel_configs:
            self._apply_dict_to_ui(self.saved_novel_configs[novel_name])
        else:
            cfg_in_dir = os.path.join(folder_path, f"{novel_name}_config.json")
            if os.path.isfile(cfg_in_dir):
                try:
                    with open(cfg_in_dir, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    self._apply_dict_to_ui(cfg)
                except Exception:
                    pass
            else:
                info = detect_chapter_range_from_folder(folder_path)
                if info["min_chapter"] is not None and info["max_chapter"] is not None:
                    self.entry_start_ch.delete(0, "end")
                    self.entry_start_ch.insert(0, str(info["min_chapter"]))
                    self.entry_end_ch.delete(0, "end")
                    self.entry_end_ch.insert(0, str(info["max_chapter"]))

        self._scan_chapters_for_pub()
        self.log_message(f"Switched active novel to: {novel_name}", "info")
        self._save_current_session()

    def _on_novel_dropdown_selected(self, choice: str):
        if choice in self.novel_paths_map:
            self._switch_to_novel(choice, self.novel_paths_map[choice])

    def _on_pub_novel_selected(self, choice: str):
        if choice in self.novel_paths_map:
            self._switch_to_novel(choice, self.novel_paths_map[choice])

    def _on_novel_name_changed(self, event=None):
        name = self.entry_novel_name.get().strip()
        if not name:
            return
        curr_out = self.entry_output_dir.get().strip()
        base_dir = os.path.dirname(curr_out) if curr_out else APP_DIR
        new_path = os.path.join(base_dir, name)
        self.entry_output_dir.delete(0, "end")
        self.entry_output_dir.insert(0, new_path)
        self.entry_pub_src_dir.delete(0, "end")
        self.entry_pub_src_dir.insert(0, new_path)
        self.entry_book_title.delete(0, "end")
        self.entry_book_title.insert(0, name.replace("_", " "))

    def _save_current_session(self):
        try:
            cfg = self._get_ui_dict()
            novel_name = cfg["novel_name"]
            if novel_name:
                self.saved_novel_configs[novel_name] = cfg
            recents = list(self.novel_paths_map.values())
            save_session(cfg, self.saved_novel_configs, novel_name, recents)
        except Exception as e:
            self.log_message(f"Notice: Failed to persist session: {e}", "warning")

    def _load_startup_config(self):
        current_cfg, saved_configs, last_novel, recents = load_session()
        self.saved_novel_configs = saved_configs
        self._refresh_detected_novels()

        if current_cfg:
            self._apply_dict_to_ui(current_cfg)
            if last_novel:
                if hasattr(self, 'combo_detected_novels'):
                    self.combo_detected_novels.set(last_novel)
                if hasattr(self, 'combo_pub_novels'):
                    self.combo_pub_novels.set(last_novel)
            self.log_message(f"Restored last used novel session: {last_novel or 'Previous Session'}", "info")
            if not self.entry_pub_start_ch.get() or not self.entry_pub_end_ch.get():
                self._scan_chapters_for_pub()
            else:
                self.after(200, self._scan_chapters_for_pub)
            return

        self._load_default_config()
        self._scan_chapters_for_pub()

    def _on_close(self):
        self._save_current_session()
        self.destroy()

    # =========================================================================
    # LOGGING PIPELINE
    # =========================================================================
    def log_message(self, message: str, tag: Optional[str] = None):
        now_str = datetime.now().strftime("%H:%M:%S")
        if not tag:
            low = message.lower()
            if any(w in low for w in ["✓", "thành công", "cào thành công", "đã lưu", "saved", "complete", "hoàn thành", "repaired"]):
                tag = "success"
            elif any(w in low for w in ["✗", "thất bại", "lỗi", "error", "failed", "exception"]):
                tag = "error"
            elif any(w in low for w in ["⏳", "nghỉ", "warning", "thử lại", "timeout", "cảnh báo", "notice"]):
                tag = "warning"
            else:
                tag = "info"
        self.log_queue.put((now_str, message, tag))

    def _process_log_queue(self):
        while not self.log_queue.empty():
            now_str, msg, tag = self.log_queue.get_nowait()
            self.txt_log.insert("end", f"[{now_str}] ", "time")
            self.txt_log.insert("end", f"{msg}\n", tag)
            self.txt_log.see("end")
        self.after(100, self._process_log_queue)

    # =========================================================================
    # SCRAPER CONTROLLER
    # =========================================================================
    def _on_ch1_url_changed(self, event=None):
        url = self.entry_ch1_url.get().strip()
        if url and not self.entry_url_pattern.get().strip():
            derived = derive_pattern_from_url(url)
            self.entry_url_pattern.delete(0, "end")
            self.entry_url_pattern.insert(0, derived)

    def _auto_detect_pattern(self):
        url = self.entry_ch1_url.get().strip()
        if not url:
            messagebox.showwarning("Notice", "Please enter Chapter 1 URL first.")
            return
        derived = derive_pattern_from_url(url)
        self.entry_url_pattern.delete(0, "end")
        self.entry_url_pattern.insert(0, derived)
        self.log_message(f"Derived Pattern: {derived}", "info")

    def _detect_existing_for_scraper(self):
        folder = self.entry_output_dir.get().strip()
        if not os.path.isdir(folder):
            messagebox.showwarning("Notice", f"Novel folder does not exist yet:\n{folder}")
            return

        info = detect_chapter_range_from_folder(folder)
        if info["total_chapters"] == 0:
            messagebox.showinfo("Chapter Detection", f"No existing chapter .txt files found in:\n{folder}\n\nYou can start scraping from Chapter 1.")
            return

        min_ch = info["min_chapter"]
        max_ch = info["max_chapter"]
        tot = info["total_chapters"]
        next_ch = max_ch + 1

        ans = messagebox.askyesnocancel(
            "Detected Existing Chapters",
            f"Found {tot} chapter(s) from .txt files in folder:\n\n"
            f"• Available Range: Chapter {min_ch} to Chapter {max_ch}\n"
            f"• Next Chapter to scrape: {next_ch}\n\n"
            f"Click [Yes] to continue scraping from next chapter ({next_ch}).\n"
            f"Click [No] to set range to existing chapters ({min_ch} -> {max_ch}).\n"
            f"Click [Cancel] to keep current inputs."
        )

        if ans is True:
            self.entry_start_ch.delete(0, "end")
            self.entry_start_ch.insert(0, str(next_ch))
            self.log_message(f"Auto-set Start Chapter to {next_ch} (continuing after existing Ch {max_ch}).", "info")
        elif ans is False:
            self.entry_start_ch.delete(0, "end")
            self.entry_start_ch.insert(0, str(min_ch))
            self.entry_end_ch.delete(0, "end")
            self.entry_end_ch.insert(0, str(max_ch))
            self.log_message(f"Auto-set scraping range to existing chapters: Ch {min_ch} to Ch {max_ch}.", "info")

    def _start_scraping(self):
        try:
            cfg = self._get_ui_dict()
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please check numerical input values: {e}")
            return

        pattern = cfg["url_pattern"]
        if not pattern or ("{}" not in pattern and "{chapter_num}" not in pattern):
            messagebox.showerror("URL Error", "URL Template must contain '{}' placeholder!")
            return

        if cfg["end_chapter"] < cfg["start_chapter"]:
            messagebox.showerror("Error", "End Chapter cannot be smaller than Start Chapter!")
            return

        headers = {}
        if cfg["user_agent"]:
            headers["User-Agent"] = cfg["user_agent"]
        if cfg["cookie"]:
            headers["Cookie"] = cfg["cookie"]

        self._save_current_session()

        self._is_scraping = True
        self._update_action_button_styles()
        self.prog_bar.set(0)
        total_ch = cfg["end_chapter"] - cfg["start_chapter"] + 1
        self.lbl_progress.configure(text=f"Initializing (0/{total_ch})")

        self.active_scraper = NovelScraper(
            url_pattern=cfg["url_pattern"],
            start_chapter=cfg["start_chapter"],
            end_chapter=cfg["end_chapter"],
            batch_size=cfg["batch_size"],
            output_dir=cfg["output_dir"],
            headers=headers,
            delay_min=cfg["delay_min"],
            delay_max=cfg["delay_max"],
            timeout=cfg["timeout"],
            content_selector=cfg["content_selector"],
            max_retries=cfg.get("max_retries", 5),
            retry_until_success=cfg.get("retry_until_success", True),
            on_log=self.log_message,
            on_progress=lambda curr, tot, pct: self.after(0, lambda: self._apply_progress(curr, tot, pct)),
            on_batch_saved=lambda fname, count: None,
            on_finished=lambda s, e, t: self.after(0, lambda: self._finish_scraper_state(s, e, t))
        )

        threading.Thread(target=self.active_scraper.run, daemon=True).start()

    def _stop_scraping(self):
        if self.active_scraper:
            self.btn_stop.configure(state="disabled")
            self.log_message("Sending stop request to scraper...", "warning")
            self.active_scraper.stop()

    def _apply_progress(self, current_count: int, total_count: int, percentage: float):
        self.prog_bar.set(min(1.0, max(0.0, percentage / 100.0)))
        self.lbl_progress.configure(text=f"Chapter {current_count}/{total_count} ({percentage:.1f}%)")

    def _finish_scraper_state(self, success_count: int, error_count: int, total: int):
        self._is_scraping = False
        self._update_action_button_styles()
        self.lbl_progress.configure(text=f"Finished: {success_count}/{total} OK")
        messagebox.showinfo(
            "Scraping Completed",
            f"Scraping session finished!\n\n"
            f"- Successful: {success_count}/{total}\n"
            f"- Errors: {error_count}\n\n"
            f"Switch to 'Book Publisher' tab to assemble chapters into formatted DOCX/PDF!"
        )

    # =========================================================================
    # PUBLISHER CONTROLLER & SMART OPTIMIZER
    # =========================================================================
    def _scan_chapters_for_pub(self):
        folder = self.entry_pub_src_dir.get().strip()
        if not os.path.isdir(folder):
            self.lbl_scan_result.configure(text=f"Directory does not exist: {os.path.basename(folder) or folder}", text_color="#dc2626")
            return

        info = detect_chapter_range_from_folder(folder)
        if info["total_chapters"] == 0:
            self.lbl_scan_result.configure(text=f"No chapters found in '{os.path.basename(folder)}'.", text_color="#dc2626")
            self.log_message(f"No chapters found in: {folder}", "warning")
            return

        min_ch = info["min_chapter"]
        max_ch = info["max_chapter"]
        total_ch = info["total_chapters"]

        if hasattr(self, 'entry_pub_start_ch'):
            self.entry_pub_start_ch.delete(0, "end")
            self.entry_pub_start_ch.insert(0, str(min_ch))
        if hasattr(self, 'entry_pub_end_ch'):
            self.entry_pub_end_ch.delete(0, "end")
            self.entry_pub_end_ch.insert(0, str(max_ch))

        is_light = (ctk.get_appearance_mode() == "Light")
        success_color = "#15803d" if is_light else "#4ade80"
        warning_color = "#b45309" if is_light else "#fbbf24"

        if info["missing_chapters"]:
            miss_preview = ", ".join(map(str, info["missing_chapters"][:5]))
            if len(info["missing_chapters"]) > 5:
                miss_preview += "..."
            msg = f"Ready: {total_ch} chaps (Ch {min_ch} to {max_ch}). Notice: missing {len(info['missing_chapters'])} chap(s): {miss_preview}"
            self.lbl_scan_result.configure(text=msg, text_color=warning_color)
            self.log_message(msg, "warning")
        else:
            msg = f"Ready: Detected {total_ch} chapters (Ch {min_ch} to Ch {max_ch}). Range set: {min_ch} -> {max_ch}."
            self.lbl_scan_result.configure(text=msg, text_color=success_color)
            self.log_message(f"Detected {total_ch} chapters from .txt files (Ch {min_ch} to Ch {max_ch}) in {folder}", "success")

    def _auto_detect_pub_range(self):
        self._scan_chapters_for_pub()

    def _set_pub_range_all(self):
        folder = self.entry_pub_src_dir.get().strip()
        info = detect_chapter_range_from_folder(folder)
        if info["min_chapter"] is not None and info["max_chapter"] is not None:
            self.entry_pub_start_ch.delete(0, "end")
            self.entry_pub_start_ch.insert(0, str(info["min_chapter"]))
            self.entry_pub_end_ch.delete(0, "end")
            self.entry_pub_end_ch.insert(0, str(info["max_chapter"]))
            self.log_message(f"Reset publish range to all available chapters: Ch {info['min_chapter']} to Ch {info['max_chapter']}", "info")

    def _on_margin_changed(self):
        """Updates dynamic live preview of odd/even margin placement and enforces safe inside binding."""
        if not hasattr(self, 'lbl_margin_preview') or not hasattr(self, 'entry_margin_inside'):
            return
        try:
            inside_txt = self.entry_margin_inside.get().strip()
            outside_txt = self.entry_margin_outside.get().strip()
            top_txt = self.entry_margin_top.get().strip()
            bot_txt = self.entry_margin_bottom.get().strip()
            inside = float(inside_txt or 2.0)
            outside = float(outside_txt or 1.2)
            top = float(top_txt or 1.2)
            bot = float(bot_txt or 1.2)
        except ValueError:
            return

        is_mirror = self.var_mirror_margins.get() if hasattr(self, 'var_mirror_margins') else True
        if is_mirror:
            # If inside is smaller than or equal to outside, auto-elevate inside to safe binding width
            if inside <= outside:
                inside = max(1.2, round(outside * 2.0, 1))
                self.entry_margin_inside.delete(0, "end")
                self.entry_margin_inside.insert(0, str(inside))
            self.lbl_margin_preview.configure(
                text=f"[Lề đối xứng in 2 mặt] Trang lẻ: Trái (Gáy) {inside}cm, Phải (Mép) {outside}cm  |  Trang chẵn: Trái (Mép) {outside}cm, Phải (Gáy) {inside}cm",
                text_color=("#0284c7", "#38bdf8")
            )
        else:
            self.lbl_margin_preview.configure(
                text=f"[Lề thường] Trái: {inside}cm | Phải: {outside}cm | Trên: {top}cm | Dưới: {bot}cm",
                text_color=("#64748b", "#94a3b8")
            )

    def _reset_default_margins(self):
        """Resets margin entries to physical book printing standard."""
        self.entry_margin_inside.delete(0, "end")
        self.entry_margin_inside.insert(0, "2.0")
        self.entry_margin_outside.delete(0, "end")
        self.entry_margin_outside.insert(0, "1.2")
        self.entry_margin_top.delete(0, "end")
        self.entry_margin_top.insert(0, "1.2")
        self.entry_margin_bottom.delete(0, "end")
        self.entry_margin_bottom.insert(0, "1.2")
        self.entry_footer_dist.delete(0, "end")
        self.entry_footer_dist.insert(0, "0.7")
        self.var_mirror_margins.set(True)
        self._on_margin_changed()
        self.log_message("Reset margins to standard: Inside 2.0cm, Outside 1.2cm, Top/Bottom 1.2cm, Mirror Margins ON.", "info")

    def _open_smart_analyzer_modal(self):
        """Opens the Smart Volume Analyzer & TOC Optimizer Dialog adapted to user margins."""
        folder = self.entry_pub_src_dir.get().strip()
        if not os.path.isdir(folder):
            messagebox.showwarning("Notice", f"Source directory does not exist:\n{folder}")
            return

        chapters = scan_and_collect_chapters(folder)
        if not chapters:
            messagebox.showwarning("Notice", "No chapters found to analyze. Please scan or download chapters first.")
            return

        try:
            inside_m = float(self.entry_margin_inside.get().strip() or 2.0)
            outside_m = float(self.entry_margin_outside.get().strip() or 1.2)
            top_m = float(self.entry_margin_top.get().strip() or 1.2)
            bot_m = float(self.entry_margin_bottom.get().strip() or 1.2)
            body_size = int(self.entry_body_size.get().strip() or 14)
        except Exception:
            inside_m, outside_m, top_m, bot_m, body_size = 2.0, 1.2, 1.2, 1.2, 14

        def on_tier_applied(opt: VolumeSplitOption):
            self.seg_split.set("Smart Balanced Volumes")
            self.entry_target_pages.delete(0, "end")
            self.entry_target_pages.insert(0, str(opt.target_pages))
            self.log_message(
                f"Applied {opt.tier_name}: Target set to {opt.target_pages} pages/vol ({opt.num_volumes} volumes total). {opt.toc_quality_rating}",
                "success"
            )
            messagebox.showinfo(
                "Đã áp dụng mốc phân tập",
                f"Đã chọn: {opt.tier_name}\n\n"
                f"• Phân chia thành: {opt.num_volumes} tập cân bằng\n"
                f"• Ước tính: ~{opt.avg_pages_per_vol} trang/tập (~{opt.avg_chapters_per_vol} chương/tập)\n"
                f"• Mục lục: {opt.toc_quality_rating}"
            )

        SmartVolumeAnalyzerDialog(
            self,
            chapters,
            on_tier_applied,
            inside_margin_cm=inside_m,
            outside_margin_cm=outside_m,
            top_margin_cm=top_m,
            bottom_margin_cm=bot_m,
            body_font_size=body_size
        )

    def _repair_txt_files_in_folder(self):
        folder = self.entry_pub_src_dir.get().strip()
        if not os.path.isdir(folder):
            messagebox.showwarning("Notice", "Please specify a valid chapters folder.")
            return

        raw_dir = os.path.join(folder, "raw")
        found_txt = []
        if os.path.isdir(raw_dir):
            found_txt.extend(glob.glob(os.path.join(raw_dir, "*.txt")))
        found_txt.extend(glob.glob(os.path.join(folder, "*.txt")))
        txt_files = list(set(found_txt))
        if not txt_files:
            messagebox.showwarning("Notice", "No .txt files found.")
            return

        repaired_count = 0
        for fp in txt_files:
            success, old_l, new_l = repair_file_inplace(fp)
            if success:
                repaired_count += 1
                self.log_message(f"Repaired quotes: {os.path.basename(fp)} ({old_l} -> {new_l} lines)", "success")

        messagebox.showinfo("Success", f"Cleaned {repaired_count} files (UTF-8-BOM encoded, quotes fixed).")

    def _start_publish_book(self):
        folder = self.entry_pub_src_dir.get().strip()
        if not os.path.isdir(folder):
            messagebox.showwarning("Notice", f"Source folder does not exist: {folder}")
            return

        pub_start_raw = self.entry_pub_start_ch.get().strip() if hasattr(self, 'entry_pub_start_ch') else ""
        pub_end_raw = self.entry_pub_end_ch.get().strip() if hasattr(self, 'entry_pub_end_ch') else ""

        pub_start = int(pub_start_raw) if pub_start_raw.isdigit() else None
        pub_end = int(pub_end_raw) if pub_end_raw.isdigit() else None

        if pub_start is not None and pub_end is not None and pub_end < pub_start:
            messagebox.showerror("Range Error", f"Publish End Chapter ({pub_end}) cannot be smaller than Start Chapter ({pub_start})!")
            return

        # Margins & Binding
        try:
            inside_m = float(self.entry_margin_inside.get() or 2.0)
            outside_m = float(self.entry_margin_outside.get() or 1.2)
            top_m = float(self.entry_margin_top.get() or 1.2)
            bot_m = float(self.entry_margin_bottom.get() or 1.2)
            foot_dist = float(self.entry_footer_dist.get() or 0.7)
        except ValueError:
            messagebox.showerror("Margin Error", "Margin values must be valid numbers (e.g. 2.0, 1.2, 0.7)")
            return

        mirror_m = self.var_mirror_margins.get()

        book_title = sanitize_xml_string(self.entry_book_title.get().strip() or "Novel")
        author = sanitize_xml_string(self.entry_book_author.get().strip() or "Author")
        subtitle = sanitize_xml_string(self.entry_book_subtitle.get().strip())
        imprint = sanitize_xml_string(self.entry_book_imprint.get().strip())
        font_name = self.combo_font.get() or "Georgia"
        body_size = int(self.entry_body_size.get() or 14)
        ch_size = int(self.combo_ch_size.get() or 28)
        align_mode = "left" if self.combo_align.get() == "Left" else "justify"
        smart_page = self.var_smart_page.get()
        split_mode = "split" if "Smart" in self.seg_split.get() else "all"
        target_pages = int(self.entry_target_pages.get() or 250)
        export_format = self.combo_format.get()

        self._save_current_session()

        self._is_publishing = True
        self._update_action_button_styles()
        self.prog_bar.set(0)
        self.lbl_progress.configure(text="Preparing publication...")

        def publish_worker():
            try:
                self.log_message(f"Loading chapters from: {folder}...", "info")
                chapters = scan_and_collect_chapters(folder, start_chapter=pub_start, end_chapter=pub_end)
                if not chapters:
                    self._is_publishing = False
                    self.after(0, self._update_action_button_styles)
                    range_txt = f"within range Ch {pub_start} to Ch {pub_end}" if (pub_start or pub_end) else ""
                    self.after(0, lambda: messagebox.showerror("Error", f"No chapters found {range_txt} to export!"))
                    return

                total_ch = len(chapters)
                range_desc = f"Chapters {chapters[0][0]} to {chapters[-1][0]}"
                self.log_message(f"Total {total_ch} chapters collected ({range_desc}). Mode: {split_mode.upper()}", "info")

                # Determine volumes using balanced partitioning with dynamic page capacity
                if split_mode == "split":
                    p_h = max(15.0, 29.7 - (top_m + bot_m))
                    p_w = max(10.0, 21.0 - (inside_m + outside_m))
                    l_per_p = calculate_lines_per_page(p_h, body_size)
                    c_per_l = calculate_chars_per_line(p_w, body_size)
                    volumes = split_chapters_into_volumes(
                        chapters,
                        target_pages_per_volume=target_pages,
                        lines_per_page=l_per_p,
                        chars_per_line=c_per_l
                    )
                else:
                    min_ch = chapters[0][0]
                    max_ch = chapters[-1][0]
                    volumes = [(1, f"Complete Edition (Chapters {min_ch}–{max_ch})", chapters)]

                self.log_message(f"Divided into {len(volumes)} volume(s). Generating documents...", "info")

                created_files = []
                clean_title = re.sub(r'[^\w\-_\. ]', '_', book_title).replace(" ", "_")

                base_dir = folder
                if os.path.basename(os.path.normpath(base_dir)).lower() == "raw":
                    base_dir = os.path.dirname(base_dir)

                doc_dir = os.path.join(base_dir, "print", "doc")
                pdf_dir = os.path.join(base_dir, "print", "pdf")
                os.makedirs(doc_dir, exist_ok=True)
                os.makedirs(pdf_dir, exist_ok=True)

                for v_idx, (v_num, v_title, v_chapters) in enumerate(volumes):
                    v_start = v_chapters[0][0]
                    v_end = v_chapters[-1][0]

                    if len(volumes) > 1:
                        base_name = f"{clean_title}_Volume_{v_num:02d}_Ch_{v_start}_to_{v_end}"
                        vol_sub = f"Volume {v_num} • Chapters {v_start}–{v_end}"
                    else:
                        base_name = f"{clean_title}_Complete_Ch_{v_start}_to_{v_end}"
                        vol_sub = subtitle or f"Chapters {v_start}–{v_end}"

                    docx_filename = base_name + ".docx"
                    pdf_filename = base_name + ".pdf"

                    docx_path = os.path.join(doc_dir, docx_filename)
                    pdf_path = os.path.join(pdf_dir, pdf_filename)

                    self.log_message(f"Writing [{v_idx+1}/{len(volumes)}]: {docx_filename}...", "info")

                    def prog_cb(curr, tot, msg):
                        pct = ((v_idx + (curr / tot)) / len(volumes)) * 100.0
                        self.after(0, lambda: self._apply_progress(curr, tot, pct))

                    # Export DOCX with Mirror Margins and Redesigned Smart Pagination
                    export_single_document(
                        chapters=v_chapters,
                        output_docx_path=docx_path,
                        novel_title=book_title,
                        subtitle=vol_sub,
                        author=author,
                        imprint_note=imprint,
                        font_name=font_name,
                        body_font_size=body_size,
                        chapter_font_size=ch_size,
                        text_alignment=align_mode,
                        smart_pagination=smart_page,
                        inside_margin_cm=inside_m,
                        outside_margin_cm=outside_m,
                        top_margin_cm=top_m,
                        bottom_margin_cm=bot_m,
                        footer_distance_cm=foot_dist,
                        mirror_margins=mirror_m,
                        on_progress=prog_cb
                    )

                    if "DOCX" in export_format:
                        created_files.append(docx_path)
                        self.log_message(f"Saved DOCX: {os.path.basename(docx_path)}", "success")

                    if "PDF" in export_format:
                        self.log_message(f"Rendering PDF with automatic TOC for Volume {v_num}...", "info")
                        pdf_ok = convert_docx_to_pdf(docx_path, pdf_path)
                        if pdf_ok:
                            created_files.append(pdf_path)
                            self.log_message(f"Saved PDF: {os.path.basename(pdf_path)}", "success")
                        else:
                            self.log_message(f"Failed to render PDF for {docx_filename}", "warning")

                        if export_format == "PDF Only" and os.path.isfile(docx_path):
                            try:
                                os.remove(docx_path)
                            except Exception:
                                pass

                # Write transparent publication audit report
                print_base_dir = os.path.join(base_dir, "print")
                generate_export_diagnostics(
                    output_dir=print_base_dir,
                    novel_title=book_title,
                    author=author,
                    volumes=volumes,
                    inside_margin_cm=inside_m,
                    outside_margin_cm=outside_m,
                    top_margin_cm=top_m,
                    bottom_margin_cm=bot_m,
                    footer_distance_cm=foot_dist,
                    mirror_margins=mirror_m,
                    lines_per_page=l_per_p if 'l_per_p' in locals() else 32.0,
                    chars_per_line=c_per_l if 'c_per_l' in locals() else 68,
                    toc_capacity=calculate_toc_entries_per_page(max(15.0, 29.7 - (top_m + bot_m))),
                    created_files=created_files
                )
                self.log_message("Saved publication audit report: print/last_export_report.txt", "info")

                self.exported_files = created_files

                def on_done():
                    self._is_publishing = False
                    self._update_action_button_styles()
                    self.lbl_progress.configure(text=f"Publication Complete ({len(created_files)} files)")
                    ans = messagebox.askyesno(
                        "Publication Complete",
                        f"Successfully generated {len(created_files)} publication file(s) in:\n\n{folder}\n\nWould you like to open the PDF folder now?"
                    )
                    if ans:
                        self._open_pdf_folder()

                self.after(0, on_done)

            except Exception as e:
                self._is_publishing = False
                self.after(0, self._update_action_button_styles)
                self.log_message(f"Error publishing book: {e}", "error")
                self.after(0, lambda: messagebox.showerror("Publication Error", str(e)))

        threading.Thread(target=publish_worker, daemon=True).start()

    # =========================================================================
    # FOLDER OPENERS & PROFILES
    # =========================================================================
    def _browse_directory(self):
        curr = self.entry_output_dir.get().strip()
        folder = filedialog.askdirectory(initialdir=curr if os.path.isdir(curr) else APP_DIR)
        if folder:
            name = os.path.basename(os.path.normpath(folder))
            self.novel_paths_map[name] = os.path.abspath(folder)
            self._refresh_detected_novels()
            self._switch_to_novel(name, os.path.abspath(folder))

    def _browse_pub_src_dir(self):
        curr = self.entry_pub_src_dir.get().strip()
        folder = filedialog.askdirectory(initialdir=curr if os.path.isdir(curr) else APP_DIR)
        if folder:
            name = os.path.basename(os.path.normpath(folder))
            self.novel_paths_map[name] = os.path.abspath(folder)
            self._refresh_detected_novels()
            self._switch_to_novel(name, os.path.abspath(folder))

    def _open_output_folder(self):
        self._open_dir_path(self.entry_output_dir.get().strip())

    def _open_pdf_folder(self):
        base = self.entry_pub_src_dir.get().strip()
        target = os.path.join(base, "print", "pdf")
        self._open_dir_path(target if os.path.isdir(target) else base)

    def _open_doc_folder(self):
        base = self.entry_pub_src_dir.get().strip()
        target = os.path.join(base, "print", "doc")
        self._open_dir_path(target if os.path.isdir(target) else base)

    def _open_dir_path(self, folder: str):
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")

    def _load_default_config(self):
        self._apply_dict_to_ui(DEFAULT_CONFIG)
        self.log_message("Loaded default configuration (Invincible Mumu).", "info")

    def _get_ui_dict(self) -> dict:
        cookie_text = self.txt_cookie.get("1.0", "end").strip()
        if cookie_text.lower().startswith("cookie:"):
            cookie_text = cookie_text[7:].strip()

        return {
            "novel_name": self.entry_novel_name.get().strip(),
            "chapter_1_url": self.entry_ch1_url.get().strip(),
            "url_pattern": self.entry_url_pattern.get().strip(),
            "start_chapter": int(self.entry_start_ch.get() or 1),
            "end_chapter": int(self.entry_end_ch.get() or 1),
            "batch_size": int(self.entry_batch_size.get() or 5),
            "content_selector": self.entry_selector.get().strip() or "article",
            "cookie": cookie_text,
            "user_agent": self.entry_ua.get().strip(),
            "delay_min": float(self.entry_delay_min.get() or 8.0),
            "delay_max": float(self.entry_delay_max.get() or 15.0),
            "timeout": float(self.entry_timeout.get() or 25.0),
            "retry_until_success": self.var_retry_until_success.get(),
            "max_retries": 5,
            "output_dir": self.entry_output_dir.get().strip(),
            # Publisher fields
            "pub_start_chapter": int(self.entry_pub_start_ch.get()) if (hasattr(self, 'entry_pub_start_ch') and self.entry_pub_start_ch.get().strip().isdigit()) else None,
            "pub_end_chapter": int(self.entry_pub_end_ch.get()) if (hasattr(self, 'entry_pub_end_ch') and self.entry_pub_end_ch.get().strip().isdigit()) else None,
            "book_title": self.entry_book_title.get().strip() if hasattr(self, 'entry_book_title') else "",
            "book_author": self.entry_book_author.get().strip() if hasattr(self, 'entry_book_author') else "",
            "book_subtitle": self.entry_book_subtitle.get().strip() if hasattr(self, 'entry_book_subtitle') else "",
            "book_imprint": self.entry_book_imprint.get().strip() if hasattr(self, 'entry_book_imprint') else "",
            "reading_font": self.combo_font.get() if hasattr(self, 'combo_font') else "Georgia",
            "body_font_size": int(self.entry_body_size.get() or 14) if hasattr(self, 'entry_body_size') else 14,
            "chapter_font_size": int(self.combo_ch_size.get() or 28) if hasattr(self, 'combo_ch_size') else 28,
            "align_mode": self.combo_align.get() if hasattr(self, 'combo_align') else "Justify",
            "smart_pagination": self.var_smart_page.get() if hasattr(self, 'var_smart_page') else True,
            "split_mode": self.var_split_mode.get() if hasattr(self, 'var_split_mode') else "split",
            "target_pages": int(self.entry_target_pages.get() or 250) if hasattr(self, 'entry_target_pages') else 250,
            "export_format": self.combo_format.get() if hasattr(self, 'combo_format') else "Both DOCX and PDF",
            # Margins & Binding
            "inside_margin_cm": float(self.entry_margin_inside.get() or 2.0) if hasattr(self, 'entry_margin_inside') else 2.0,
            "outside_margin_cm": float(self.entry_margin_outside.get() or 1.2) if hasattr(self, 'entry_margin_outside') else 1.2,
            "top_margin_cm": float(self.entry_margin_top.get() or 1.2) if hasattr(self, 'entry_margin_top') else 1.2,
            "bottom_margin_cm": float(self.entry_margin_bottom.get() or 1.2) if hasattr(self, 'entry_margin_bottom') else 1.2,
            "footer_distance_cm": float(self.entry_footer_dist.get() or 0.7) if hasattr(self, 'entry_footer_dist') else 0.7,
            "mirror_margins": self.var_mirror_margins.get() if hasattr(self, 'var_mirror_margins') else True
        }

    def _apply_dict_to_ui(self, cfg: dict):
        self.entry_novel_name.delete(0, "end")
        self.entry_novel_name.insert(0, cfg.get("novel_name", ""))

        self.entry_ch1_url.delete(0, "end")
        self.entry_ch1_url.insert(0, cfg.get("chapter_1_url", ""))

        self.entry_url_pattern.delete(0, "end")
        self.entry_url_pattern.insert(0, cfg.get("url_pattern", ""))

        self.entry_start_ch.delete(0, "end")
        self.entry_start_ch.insert(0, str(cfg.get("start_chapter", 6)))

        self.entry_end_ch.delete(0, "end")
        self.entry_end_ch.insert(0, str(cfg.get("end_chapter", 177)))

        self.entry_batch_size.delete(0, "end")
        self.entry_batch_size.insert(0, str(cfg.get("batch_size", 5)))

        self.entry_selector.delete(0, "end")
        self.entry_selector.insert(0, cfg.get("content_selector", "article"))

        self.txt_cookie.delete("1.0", "end")
        self.txt_cookie.insert("1.0", cfg.get("cookie", ""))

        self.entry_ua.delete(0, "end")
        self.entry_ua.insert(0, cfg.get("user_agent", DEFAULT_CONFIG["user_agent"]))

        self.entry_delay_min.delete(0, "end")
        self.entry_delay_min.insert(0, str(cfg.get("delay_min", 8.0)))

        self.entry_delay_max.delete(0, "end")
        self.entry_delay_max.insert(0, str(cfg.get("delay_max", 15.0)))

        self.entry_timeout.delete(0, "end")
        self.entry_timeout.insert(0, str(cfg.get("timeout", 25.0)))

        self.var_retry_until_success.set(cfg.get("retry_until_success", True))

        out_d = cfg.get("output_dir", "")
        self.entry_output_dir.delete(0, "end")
        self.entry_output_dir.insert(0, out_d)
        self.entry_pub_src_dir.delete(0, "end")
        self.entry_pub_src_dir.insert(0, out_d)

        # Publisher metadata
        if hasattr(self, 'entry_book_title') and "book_title" in cfg:
            self.entry_book_title.delete(0, "end")
            self.entry_book_title.insert(0, cfg["book_title"])
        if hasattr(self, 'entry_book_author') and "book_author" in cfg:
            self.entry_book_author.delete(0, "end")
            self.entry_book_author.insert(0, cfg["book_author"])
        if hasattr(self, 'entry_book_subtitle') and "book_subtitle" in cfg:
            self.entry_book_subtitle.delete(0, "end")
            self.entry_book_subtitle.insert(0, cfg["book_subtitle"])
        if hasattr(self, 'entry_book_imprint') and "book_imprint" in cfg:
            self.entry_book_imprint.delete(0, "end")
            self.entry_book_imprint.insert(0, cfg["book_imprint"])
        if hasattr(self, 'combo_font') and "reading_font" in cfg:
            self.combo_font.set(cfg["reading_font"])
        if hasattr(self, 'entry_body_size') and "body_font_size" in cfg:
            self.entry_body_size.delete(0, "end")
            self.entry_body_size.insert(0, str(cfg["body_font_size"]))
        if hasattr(self, 'combo_ch_size') and "chapter_font_size" in cfg:
            self.combo_ch_size.set(str(cfg["chapter_font_size"]))
        if hasattr(self, 'combo_align') and "align_mode" in cfg:
            self.combo_align.set(cfg["align_mode"])
        if hasattr(self, 'var_smart_page') and "smart_pagination" in cfg:
            self.var_smart_page.set(cfg["smart_pagination"])
        if hasattr(self, 'entry_target_pages') and "target_pages" in cfg:
            self.entry_target_pages.delete(0, "end")
            self.entry_target_pages.insert(0, str(cfg["target_pages"]))
        if hasattr(self, 'combo_format') and "export_format" in cfg:
            self.combo_format.set(cfg["export_format"])
        if hasattr(self, 'entry_pub_start_ch') and "pub_start_chapter" in cfg and cfg["pub_start_chapter"] is not None:
            self.entry_pub_start_ch.delete(0, "end")
            self.entry_pub_start_ch.insert(0, str(cfg["pub_start_chapter"]))
        if hasattr(self, 'entry_pub_end_ch') and "pub_end_chapter" in cfg and cfg["pub_end_chapter"] is not None:
            self.entry_pub_end_ch.delete(0, "end")
            self.entry_pub_end_ch.insert(0, str(cfg["pub_end_chapter"]))

        # Margins & Binding
        if hasattr(self, 'entry_margin_inside') and "inside_margin_cm" in cfg:
            self.entry_margin_inside.delete(0, "end")
            self.entry_margin_inside.insert(0, str(cfg["inside_margin_cm"]))
        if hasattr(self, 'entry_margin_outside') and "outside_margin_cm" in cfg:
            self.entry_margin_outside.delete(0, "end")
            self.entry_margin_outside.insert(0, str(cfg["outside_margin_cm"]))
        if hasattr(self, 'entry_margin_top') and "top_margin_cm" in cfg:
            self.entry_margin_top.delete(0, "end")
            self.entry_margin_top.insert(0, str(cfg["top_margin_cm"]))
        if hasattr(self, 'entry_margin_bottom') and "bottom_margin_cm" in cfg:
            self.entry_margin_bottom.delete(0, "end")
            self.entry_margin_bottom.insert(0, str(cfg["bottom_margin_cm"]))
        if hasattr(self, 'entry_footer_dist') and "footer_distance_cm" in cfg:
            self.entry_footer_dist.delete(0, "end")
            self.entry_footer_dist.insert(0, str(cfg["footer_distance_cm"]))
        if hasattr(self, 'var_mirror_margins') and "mirror_margins" in cfg:
            self.var_mirror_margins.set(cfg["mirror_margins"])
        self._on_margin_changed()

    def _save_profile_file(self):
        cfg = self._get_ui_dict()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Profile", "*.json")],
            initialfile=f"{cfg['novel_name'] or 'profile'}_config.json"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self.log_message(f"Saved configuration profile: {file_path}", "success")
                messagebox.showinfo("Success", f"Configuration profile saved:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save profile: {e}")

    def _load_profile_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Profile", "*.json"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self._apply_dict_to_ui(cfg)
                self.log_message(f"Loaded profile: {file_path}", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load profile: {e}")


if __name__ == "__main__":
    app = ModernNovelApp()
    app.mainloop()
