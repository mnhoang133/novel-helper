"""
Module: core.book_engine
Description: Master facade consolidating typography metrics, chapter scanning,
             volume partitioning, Word document building, and PDF conversion.
Author: Google Deepmind Agent
"""

from core.page_metrics import (
    LINES_PER_PAGE_STANDARD,
    CHARS_PER_LINE_STANDARD,
    TOC_ENTRIES_PER_PAGE,
    calculate_lines_per_page,
    calculate_chars_per_line,
    calculate_toc_entries_per_page,
    calculate_chapter_real_lines,
    estimate_chapter_pages
)

from core.chapter_scanner import (
    parse_chapters_from_text,
    detect_chapter_range_from_folder,
    scan_and_collect_chapters
)

from core.volume_splitter import (
    VolumeSplitOption,
    analyze_optimal_volume_splits,
    split_chapters_into_volumes
)

from core.docx_builder import (
    export_single_document,
    add_xml_field
)

from core.pdf_converter import (
    convert_docx_to_pdf
)

from core.diagnostics import (
    generate_export_diagnostics
)

__all__ = [
    "LINES_PER_PAGE_STANDARD",
    "CHARS_PER_LINE_STANDARD",
    "TOC_ENTRIES_PER_PAGE",
    "calculate_lines_per_page",
    "calculate_chars_per_line",
    "calculate_toc_entries_per_page",
    "calculate_chapter_real_lines",
    "estimate_chapter_pages",
    "parse_chapters_from_text",
    "detect_chapter_range_from_folder",
    "scan_and_collect_chapters",
    "VolumeSplitOption",
    "analyze_optimal_volume_splits",
    "split_chapters_into_volumes",
    "export_single_document",
    "add_xml_field",
    "convert_docx_to_pdf",
    "generate_export_diagnostics"
]
