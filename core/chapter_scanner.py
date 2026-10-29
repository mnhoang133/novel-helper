"""
Module: core.chapter_scanner
Description: Scanning, discovery, parsing, and deduplication of chapter text files.
Author: Google Deepmind Agent
"""

import os
import re
import glob
from typing import List, Tuple, Dict, Optional
from core.cleaner import heal_raw_text, sanitize_xml_string


def parse_chapters_from_text(raw_text: str) -> List[Tuple[int, str, str]]:
    """
    Extracts individual chapters from raw text matching: 'CHAPTER {num}' or 'Chương {num}'
    Returns: [(chapter_num, title, clean_body), ...]
    """
    pattern = re.compile(r'^(CHAPTER|Chapter|Chương)\s+(\d+)\b[^\n]*', re.MULTILINE | re.IGNORECASE)
    matches = list(pattern.finditer(raw_text))

    if not matches:
        return []

    chapters = []
    for i, m in enumerate(matches):
        ch_num = int(m.group(2))
        title = sanitize_xml_string(m.group(0).strip())
        start_idx = m.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)

        body = raw_text[start_idx:end_idx].strip()
        clean_body = heal_raw_text(body)
        clean_body = sanitize_xml_string(clean_body)
        chapters.append((ch_num, title, clean_body))

    return chapters


def detect_chapter_range_from_folder(folder_path: str) -> dict:
    """
    Scans a novel folder (both raw/ and root) and detects chapter numbers from:
    1. Parsing inside .txt files (matching 'CHAPTER {num}' or 'Chapter {num}' or 'Chương {num}').
    2. Fallback to batch filenames ('Chapters_{start}_to_{end}.txt').
    """
    if not os.path.isdir(folder_path):
        return {
            "total_files": 0,
            "total_chapters": 0,
            "min_chapter": None,
            "max_chapter": None,
            "missing_chapters": [],
            "chapter_numbers": []
        }

    raw_sub = os.path.join(folder_path, "raw")
    found_files = []
    if os.path.isdir(raw_sub):
        found_files.extend(glob.glob(os.path.join(raw_sub, "*.txt")))
    found_files.extend(glob.glob(os.path.join(folder_path, "*.txt")))
    file_paths = list(set(found_files))

    ch_set = set()
    pat = re.compile(r'^(CHAPTER|Chapter|Chương)\s+(\d+)\b', re.MULTILINE | re.IGNORECASE)

    for fp in file_paths:
        try:
            with open(fp, "r", encoding="utf-8-sig", errors="ignore") as f:
                content = f.read()
        except Exception:
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

        for m in pat.finditer(content):
            try:
                ch_set.add(int(m.group(2)))
            except ValueError:
                pass

    # Fallback to filename parsing if no headers found inside text
    if not ch_set:
        fn_pat = re.compile(r'Chapters?_(\d+)(?:_to_(\d+))?', re.IGNORECASE)
        for fp in file_paths:
            m = fn_pat.search(os.path.basename(fp))
            if m:
                s = int(m.group(1))
                e = int(m.group(2)) if m.group(2) else s
                for c in range(s, e + 1):
                    ch_set.add(c)

    sorted_ch = sorted(ch_set)
    min_c = sorted_ch[0] if sorted_ch else None
    max_c = sorted_ch[-1] if sorted_ch else None
    missing = [c for c in range(min_c, max_c + 1) if c not in ch_set] if (min_c and max_c) else []

    return {
        "total_files": len(file_paths),
        "total_chapters": len(sorted_ch),
        "min_chapter": min_c,
        "max_chapter": max_c,
        "missing_chapters": missing,
        "chapter_numbers": sorted_ch
    }


def scan_and_collect_chapters(
    folder_path: str,
    file_paths: Optional[List[str]] = None,
    start_chapter: Optional[int] = None,
    end_chapter: Optional[int] = None
) -> List[Tuple[int, str, str]]:
    """
    Scans and aggregates all chapters from batch .txt files in numerical order.
    Searches both folder_path/raw/ and folder_path/ root automatically.
    Removes duplicates, taking the longest/most complete version.
    Supports optional filtering by start_chapter and end_chapter.
    """
    if not file_paths:
        raw_sub = os.path.join(folder_path, "raw")
        found_files = []
        if os.path.isdir(raw_sub):
            found_files.extend(glob.glob(os.path.join(raw_sub, "*.txt")))
        found_files.extend(glob.glob(os.path.join(folder_path, "*.txt")))
        file_paths = list(set(found_files))

    all_chapters_dict: Dict[int, Tuple[str, str]] = {}

    for fp in file_paths:
        try:
            with open(fp, "r", encoding="utf-8-sig", errors="ignore") as f:
                content = f.read()
        except Exception:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        parsed = parse_chapters_from_text(content)
        for ch_num, title, body in parsed:
            if start_chapter is not None and ch_num < start_chapter:
                continue
            if end_chapter is not None and ch_num > end_chapter:
                continue
            if ch_num not in all_chapters_dict or len(body) > len(all_chapters_dict[ch_num][1]):
                all_chapters_dict[ch_num] = (title, body)

    sorted_chapters = []
    for ch_num in sorted(all_chapters_dict.keys()):
        title, body = all_chapters_dict[ch_num]
        sorted_chapters.append((ch_num, title, body))

    return sorted_chapters
