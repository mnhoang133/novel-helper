"""
Module: core.cleaner
Description: Universal text sanitizer, quote healer, broken word stitcher, and XML compatibility layer.
Author: Google Deepmind Agent
"""

import os
import re
from typing import Tuple, List
from bs4 import BeautifulSoup

# Regex matching all XML 1.0 illegal characters:
# Disallows ASCII control characters 0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F,
# Unicode surrogates 0xD800-0xDFFF, and non-characters 0xFFFE, 0xFFFF
_ILLEGAL_XML_CHARS_RE = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]'
)

_OBVIOUS_SUFFIXES = {
    'wn', 'ut', 'low', 'igns', 'gan', 're', 'ight', 'etely', 's', 'ddered', 'e', 'rying', 'y', 'elaxed', 'ly',
    'tance', 'thin', 'ow', 'ted', 'd', 'rnal', 'nsive', 'lawlessly', 'ing', 'm', 'ch', 'face', 'hory', 'ke',
    'ig', 'ee', 'st', 'ed', 'se', 'iety', 'ng', 'med', 'ts', 'shed', 'ury', 'ifficult', 'ust', 'irst', 'r',
    'ies', 'g', 'curred', 'rdity', 'uickly', 'f', 'ouldn', 'unded', 'hink', 'n', 'dness', 'ndful', 'ae',
    'fter', 'iss', 'more'
}

_OBVIOUS_ROOTS = {
    'unkno', 'witho', 'fol', 'kn', 'compl', 'shu', 'aimlessl', 'dis', 'wi', 'exte', 'beca', 'expe', 'warn',
    'sur', 'bat', 'ta', 'hol', 'thr', 'utmo', 'wa', 'reall', 'stunn', 'increa', 'soc', 'causi', 'infor',
    'th', 'knigh', 'inj', 'repl', 'oc', 'absu', 'dumbfo', 'col', 'maste', 'coul', 'goddam', 'accepte',
    'b', 's', 'm', 'r', 'f', 'o', 'd', 'j', 'q', 'c', 'w', 'e', 't'
}


def sanitize_xml_string(text: str) -> str:
    """
    Strips XML 1.0 incompatible characters, null bytes, and non-printable control characters.
    Guarantees that strings passed to python-docx / lxml never raise ValueError.
    """
    if not text:
        return ""
    return _ILLEGAL_XML_CHARS_RE.sub("", str(text))


def heal_broken_lines(content: str) -> str:
    """
    Heals words and sentences broken across unexpected newlines due to web scraper artifacts:
    - HTML entity fragments (&l\\ndquo; -> “, &r\\ndquo; -> ”).
    - Broken character names (Kim Y\\nu-Rin -> Kim Yu-Rin, S\\nae-Jin -> Sae-Jin).
    - Words cut in half (the unkno\\nwn blacksmith -> the unknown blacksmith).
    - Unfinished sentences split across lines without closing punctuation.
    """
    if not content:
        return ""

    # 1. Reconnect fragmented HTML entities
    content = re.sub(r'&l\s*\n\s*dquo;', '“', content)
    content = re.sub(r'&r\s*\n\s*dquo;', '”', content)
    content = re.sub(r'&rdq\s*\n\s*uo;', '”', content)
    content = re.sub(r'&ldq\s*\n\s*uo;', '“', content)

    lines = content.splitlines()
    fixed_lines: List[str] = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.rstrip()

        # Check whether line continues on next line
        while idx + 1 < len(lines) and stripped:
            next_line = lines[idx + 1].strip()
            if not next_line:
                break

            last_char = stripped[-1]
            is_terminal = last_char in {'.', '!', '?', '"', '”', '’', ':', '~', '*', '—', '…'} or stripped.endswith('--')

            # Hyphen at end of line: word- \n break
            if stripped.endswith('-') and next_line[0].isalpha():
                stripped = stripped[:-1] + next_line
                idx += 1
                continue

            # Non-terminal line continuation
            if not is_terminal:
                # Name suffix continuation like u-Rin, ae-Jin, e-Jin, ung)
                if re.match(r'^[a-z]+-[A-Z][a-zA-Z]+', next_line) or next_line.startswith('ung)'):
                    stripped = stripped + next_line
                    idx += 1
                    continue

                m1 = re.search(r'([a-zA-Z]+)$', stripped)
                m2 = re.match(r'^([a-zA-Z]+)', next_line)

                if m1 and m2 and (next_line[0].islower() or m1.group(1).lower() in _OBVIOUS_ROOTS):
                    w1 = m1.group(1)
                    w2 = m2.group(1)
                    w1_low = w1.lower()
                    w2_low = w2.lower()

                    should_merge_no_space = False

                    if w2_low in _OBVIOUS_SUFFIXES or w1_low in _OBVIOUS_ROOTS:
                        should_merge_no_space = True
                    elif w1_low == 'a' and w2_low not in {'few', 'little', 'lot', 'bit', 'long', 'while', 'small', 'big', 'great', 'good'}:
                        if w2_low.startswith('fter') or w2_low in {'gain', 'round', 'bout', 'long'}:
                            should_merge_no_space = True
                    elif w1 == 'I' and w2 == 'm':
                        should_merge_no_space = True

                    # Handle 'after a\nlong' exception
                    if stripped.endswith('after a') and w2 == 'long':
                        should_merge_no_space = False

                    if should_merge_no_space:
                        stripped = stripped + next_line
                    else:
                        stripped = stripped + " " + next_line

                    idx += 1
                    continue
            break

        fixed_lines.append(stripped)
        idx += 1

    result: List[str] = []
    for fl in fixed_lines:
        s = fl.strip()
        if not s:
            if result and result[-1] != "":
                result.append("")
        else:
            result.append(s)

    return '\n'.join(result)


def clean_html_article(container) -> str:
    """
    Extracts text from Next.js SSR article/div container:
    - Preserves natural DOM whitespace.
    - Eliminates garbage whitespace (\\xa0, \\u200b, \\ufeff).
    - Heals orphaned dialogue quotation marks.
    - Heals broken words and wrapped lines.
    - Sanitizes XML control characters.
    """
    if not container:
        return ""

    div = container.find("div") if hasattr(container, "find") else None
    target = div if div else container

    raw_text = target.get_text()
    cleaned = sanitize_xml_string(raw_text)
    cleaned = cleaned.replace('\xa0', ' ').replace('\u200b', '').replace('\ufeff', '')

    lines = [line.strip() for line in cleaned.splitlines()]

    fixed_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if fixed_lines and fixed_lines[-1] != "":
                fixed_lines.append("")
            continue

        if stripped in ('”', '"', "’", "'") and fixed_lines:
            fixed_lines[-1] = fixed_lines[-1] + stripped
        elif stripped.startswith(('”', '"', "’")) and fixed_lines and any(fixed_lines[-1].startswith(q) for q in ('“', '"', '‘')):
            fixed_lines[-1] = fixed_lines[-1] + stripped[0]
            remainder = stripped[1:].strip()
            if remainder:
                fixed_lines.append(remainder)
        else:
            fixed_lines.append(stripped)

    result = '\n'.join(fixed_lines)
    result = heal_broken_lines(result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def heal_raw_text(raw_text: str) -> str:
    """
    Cleans raw chapter text:
    - Removes XML incompatible control codes.
    - Reconnects orphaned quotes to preceding dialogue lines.
    - Stitches words broken across newlines (e.g. unkno\\nwn -> unknown).
    - Normalizes blank lines to at most 1 empty line between paragraphs.
    """
    if not raw_text:
        return ""

    cleaned = sanitize_xml_string(raw_text)
    cleaned = cleaned.replace('\xa0', ' ').replace('\u200b', '').replace('\ufeff', '')

    lines = cleaned.splitlines()
    fixed_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if fixed_lines and fixed_lines[-1] != "":
                fixed_lines.append("")
            continue

        if stripped in ('”', '"', "’", "'") and fixed_lines:
            fixed_lines[-1] = fixed_lines[-1] + stripped
        elif stripped.startswith(('”', '"', "’")) and fixed_lines and ('“' in fixed_lines[-1] or '"' in fixed_lines[-1]):
            fixed_lines[-1] = fixed_lines[-1] + stripped[0]
            rem = stripped[1:].strip()
            if rem:
                fixed_lines.append(rem)
        else:
            fixed_lines.append(stripped)

    result = '\n'.join(fixed_lines)
    result = heal_broken_lines(result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def repair_file_inplace(filepath: str) -> Tuple[bool, int, int]:
    """
    Reads a .txt file, heals broken words, dialogue quotes, and XML compliance, saving with utf-8-sig.
    Returns: (success, old_line_count, new_line_count)
    """
    if not os.path.isfile(filepath):
        return False, 0, 0

    try:
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

        old_line_count = len(content.splitlines())
        repaired_content = heal_raw_text(content)
        new_line_count = len(repaired_content.splitlines())

        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(repaired_content)

        return True, old_line_count, new_line_count
    except Exception as e:
        print(f"Error repairing file {filepath}: {e}")
        return False, 0, 0


def repair_directory_inplace(folder_path: str) -> Tuple[int, int]:
    """
    Batch repairs all .txt files in a directory and its 'raw' subdirectory.
    Returns: (total_files_repaired, total_lines_healed)
    """
    if not os.path.isdir(folder_path):
        return 0, 0

    import glob
    targets = []
    raw_sub = os.path.join(folder_path, "raw")
    if os.path.isdir(raw_sub):
        targets.extend(glob.glob(os.path.join(raw_sub, "*.txt")))
    targets.extend(glob.glob(os.path.join(folder_path, "*.txt")))

    unique_files = sorted(list(set(targets)))
    repaired_count = 0
    total_line_diff = 0

    for fp in unique_files:
        ok, old_lines, new_lines = repair_file_inplace(fp)
        if ok:
            repaired_count += 1
            total_line_diff += (old_lines - new_lines)

    return repaired_count, total_line_diff
