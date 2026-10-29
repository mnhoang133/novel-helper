"""
Facade Module: word_exporter
Description: Backward-compatible facade re-exporting functions from core.book_engine.
"""

from core.book_engine import (
    add_xml_field,
    convert_docx_to_pdf,
    parse_chapters_from_text,
    detect_chapter_range_from_folder,
    scan_and_collect_chapters,
    calculate_chapter_real_lines,
    estimate_chapter_pages,
    VolumeSplitOption,
    analyze_optimal_volume_splits,
    split_chapters_into_volumes,
    export_single_document,
    LINES_PER_PAGE_STANDARD,
    CHARS_PER_LINE_STANDARD,
    TOC_ENTRIES_PER_PAGE
)

__all__ = [
    "add_xml_field",
    "convert_docx_to_pdf",
    "parse_chapters_from_text",
    "detect_chapter_range_from_folder",
    "scan_and_collect_chapters",
    "calculate_chapter_real_lines",
    "estimate_chapter_pages",
    "VolumeSplitOption",
    "analyze_optimal_volume_splits",
    "split_chapters_into_volumes",
    "export_single_document",
    "LINES_PER_PAGE_STANDARD",
    "CHARS_PER_LINE_STANDARD",
    "TOC_ENTRIES_PER_PAGE"
]
