"""
Module: core.page_metrics
Description: Dynamic physical page dimension math, printable lines, characters per line,
             and Table of Contents capacity calculations based on user margins and typography.
Author: Google Deepmind Agent
"""

import math

# Reference standards: A4 paper with standard 1.2cm margins, 14pt Georgia font
LINES_PER_PAGE_STANDARD = 32.0   # A4 (27.3cm printable height), 14pt font, 1.3 line spacing + 7pt space_after
CHARS_PER_LINE_STANDARD = 68     # A4 (17.8cm printable width), 14pt Georgia font
TOC_ENTRIES_PER_PAGE = 32        # Standard Table of Contents capacity per page


def calculate_lines_per_page(printable_height_cm: float, body_font_size: int = 14) -> float:
    """
    Dynamically computes printable body lines per page based on user margins and font size.
    Base reference: 27.3cm printable height (A4 with 1.2cm top/bottom) & 14pt font = 32 lines.
    - Narrow margins (e.g. 0.6cm top/bottom, 28.5cm height) -> ~34 lines (or ~39 lines if 12pt).
    - Wide margins (e.g. 2.0cm top/bottom, 25.7cm height) -> ~30 lines.
    """
    scale_h = printable_height_cm / 27.3
    scale_font = 14.0 / max(8, body_font_size)
    lines = 32.0 * scale_h * scale_font
    return max(18.0, min(65.0, round(lines, 1)))


def calculate_chars_per_line(printable_width_cm: float, body_font_size: int = 14) -> int:
    """
    Dynamically computes average characters per line based on printable page width.
    Base reference: 17.8cm printable width (A4 with 2.0cm inside & 1.2cm outside) & 14pt font = 68 chars.
    - Narrow margins (e.g. 1.2cm inside & 0.6cm outside = 19.2cm) -> ~73 chars/line.
    - Wide margins (e.g. 2.5cm inside & 1.5cm outside = 17.0cm) -> ~64 chars/line.
    """
    scale_w = printable_width_cm / 17.8
    scale_font = 14.0 / max(8, body_font_size)
    chars = 68.0 * scale_w * scale_font
    return max(40, min(130, int(round(chars))))


def calculate_toc_entries_per_page(printable_height_cm: float) -> int:
    """
    Dynamically computes how many chapter entries fit on 1 Table of Contents page.
    TOC title + header spacing occupies ~3.2cm. Each TOC row takes ~0.65cm.
    - Standard 1.2cm margins (27.3cm height): ~32 chapters/page.
    - Narrow 0.6cm margins (28.5cm height): ~38-40 chapters/page!
    - Wide 2.0cm margins (25.7cm height): ~26-28 chapters/page.
    """
    avail_h = max(10.0, printable_height_cm - 3.2)
    entries = int(avail_h / 0.65)
    return max(18, min(50, entries))


def calculate_chapter_real_lines(body: str, chars_per_line: int = CHARS_PER_LINE_STANDARD) -> float:
    """
    Calculates the exact printable line count for a chapter body.
    Includes:
    - Heading (CHAPTER X) + Ornament + Vertical spacing: ~5 lines
    - Paragraph text lines: ceil(len(paragraph) / chars_per_line)
    - Paragraph spacing (7pt): ~0.3 line per paragraph
    """
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return 5.0

    total_lines = 5.0  # Heading + ornament overhead

    for p in lines:
        p_len = len(p)
        text_lines = max(1, math.ceil(p_len / chars_per_line))
        total_lines += text_lines + 0.3  # paragraph spacing

    return total_lines


def estimate_chapter_pages(body: str, chars_per_page: int = 1800) -> float:
    """Estimates physical book pages for a chapter based on standard line calculations."""
    lines = calculate_chapter_real_lines(body)
    return max(0.5, lines / LINES_PER_PAGE_STANDARD)
