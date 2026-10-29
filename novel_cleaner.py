"""
Facade Module: novel_cleaner
Description: Backward-compatible facade re-exporting functions from core.cleaner.
"""

from core.cleaner import (
    sanitize_xml_string,
    clean_html_article,
    heal_raw_text,
    repair_file_inplace
)

__all__ = [
    "sanitize_xml_string",
    "clean_html_article",
    "heal_raw_text",
    "repair_file_inplace"
]
