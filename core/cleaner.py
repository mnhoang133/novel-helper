"""
Module: core.cleaner
Description: Universal text sanitizer, quote healer, and XML compatibility layer.
Author: Google Deepmind Agent
"""

import os
import re
from typing import Tuple
from bs4 import BeautifulSoup

# Regex matching all XML 1.0 illegal characters:
# Disallows ASCII control characters 0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F,
# Unicode surrogates 0xD800-0xDFFF, and non-characters 0xFFFE, 0xFFFF
_ILLEGAL_XML_CHARS_RE = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]'
)


def sanitize_xml_string(text: str) -> str:
    """
    Strips XML 1.0 incompatible characters, null bytes, and non-printable control characters.
    Guarantees that strings passed to python-docx / lxml never raise ValueError.
    """
    if not text:
        return ""
    return _ILLEGAL_XML_CHARS_RE.sub("", str(text))


def clean_html_article(container) -> str:
    """
    Extracts text from Next.js SSR article/div container:
    - Preserves natural DOM whitespace.
    - Eliminates garbage whitespace (\xa0, \u200b, \ufeff).
    - Heals orphaned dialogue quotation marks.
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
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def heal_raw_text(raw_text: str) -> str:
    """
    Cleans raw chapter text:
    - Removes XML incompatible control codes.
    - Reconnects orphaned quotes to preceding dialogue lines.
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
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def repair_file_inplace(filepath: str) -> Tuple[bool, int, int]:
    """
    Reads a .txt file, heals dialogue quotes and XML compliance, and saves with utf-8-sig.
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
