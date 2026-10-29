"""
Module: core.session_manager
Description: State persistence, configuration profiles, and novel directory discovery.
Author: Google Deepmind Agent
"""

import os
import json
from typing import Dict, List, Optional, Tuple

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SESSION_FILE = os.path.join(APP_DIR, "last_session.json")

DEFAULT_CONFIG = {
    "novel_name": "Invincible_Mumu_Novel",
    "chapter_1_url": "https://novellunar.com/novel/invincible-mumu/chapter/1",
    "url_pattern": "https://novellunar.com/novel/invincible-mumu/chapter/{}",
    "start_chapter": 6,
    "end_chapter": 177,
    "batch_size": 5,
    "content_selector": "article",
    "cookie": "",
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/155.0.0.0 Safari/537.36"
    ),
    "delay_min": 8.0,
    "delay_max": 15.0,
    "timeout": 25.0,
    "retry_until_success": True,
    "max_retries": 5,
    "output_dir": os.path.join(APP_DIR, "Invincible_Mumu_Novel"),
    # Publisher fields
    "pub_start_chapter": 6,
    "pub_end_chapter": 177,
    "book_title": "Invincible Mumu",
    "book_author": "Web Novel Author",
    "book_subtitle": "Official English Translation",
    "book_imprint": "Print Edition • 2026",
    "reading_font": "Georgia",
    "body_font_size": 14,
    "chapter_font_size": 28,
    "align_mode": "Justify",
    "smart_pagination": True,
    "split_mode": "split",
    "target_pages": 310,
    "export_format": "Both DOCX and PDF",
    # Page Margins & Book Binding
    "inside_margin_cm": 2.0,      # Gáy sách / Inside
    "outside_margin_cm": 1.2,     # Mép ngoài / Outside
    "top_margin_cm": 1.2,
    "bottom_margin_cm": 1.2,
    "footer_distance_cm": 0.7,
    "header_distance_cm": 0.7,
    "mirror_margins": True        # Lề đối xứng trang chẵn / lẻ
}


def load_session() -> Tuple[dict, Dict[str, dict], str, List[str]]:
    """
    Loads last active session data from last_session.json.
    Returns: (current_config, saved_novel_configs, last_active_novel, recent_novels)
    """
    if not os.path.isfile(SESSION_FILE):
        return DEFAULT_CONFIG.copy(), {}, "", []

    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        loaded_cfg = data.get("current_config", {})
        current_config = DEFAULT_CONFIG.copy()
        current_config.update(loaded_cfg)
        saved_configs = data.get("saved_novel_configs", {})
        last_novel = data.get("last_active_novel", "")
        recents = data.get("recent_novels", [])
        return current_config, saved_configs, last_novel, recents
    except Exception as e:
        print(f"Error loading session: {e}")
        return DEFAULT_CONFIG.copy(), {}, "", []


def save_session(
    current_config: dict,
    saved_novel_configs: Dict[str, dict],
    last_active_novel: str,
    recent_novels: List[str]
) -> bool:
    """
    Saves current session state into last_session.json.
    """
    payload = {
        "last_active_novel": last_active_novel,
        "recent_novels": recent_novels,
        "current_config": current_config,
        "saved_novel_configs": saved_novel_configs
    }
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving session: {e}")
        return False


def discover_novel_folders(base_dir: str = APP_DIR) -> Dict[str, str]:
    """
    Scans project directory and history to detect novel folders containing raw/ or txt files.
    Returns: {novel_name: absolute_folder_path}
    """
    discovered: Dict[str, str] = {}

    if os.path.isdir(base_dir):
        for name in sorted(os.listdir(base_dir)):
            full = os.path.join(base_dir, name)
            if os.path.isdir(full) and not name.startswith('.') and name not in ('__pycache__', 'core', 'ui', 'assets'):
                discovered[name] = full

    # Supplement with session history
    if os.path.isfile(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
            recents = sdata.get("recent_novels", [])
            for r in recents:
                if os.path.isdir(r):
                    name = os.path.basename(os.path.normpath(r))
                    if name not in discovered:
                        discovered[name] = r
        except Exception:
            pass

    return discovered
