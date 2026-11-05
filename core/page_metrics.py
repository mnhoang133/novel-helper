"""
Module: core.page_metrics
Description: Dynamic physical page dimension math, printable lines, characters per line,
             and Table of Contents capacity calculations based on user margins and typography.
Author: Google Deepmind Agent
"""

import math

# Reference standards: A4 paper with standard 1.2cm margins, 12pt font, 1.2 line spacing + 5pt space_after
LINES_PER_PAGE_STANDARD = 36.0   # A4 (27.3cm printable height), 12pt font, 1.2 line spacing + 5pt space_after
CHARS_PER_LINE_STANDARD = 72     # A4 (17.8cm printable width), 12pt font
TOC_ENTRIES_PER_PAGE = 34        # Standard Table of Contents capacity per page


def calculate_lines_per_page(
    printable_height_cm: float,
    body_font_size: int = 12,
    line_spacing: float = 1.2,
    space_after_pt: float = 5.0
) -> float:
    """
    Dynamically computes printable body lines per page based on user margins, font size,
    line spacing, and paragraph spacing.
    - Uses exact point dimensions: printable_height_cm * 28.3465 pt.
    - Each line slot = (body_font_size * line_spacing) + amortized paragraph spacing.
    """
    h_pt = max(10.0, printable_height_cm) * 28.3465
    line_h = max(8.0, float(body_font_size)) * max(1.0, min(2.0, float(line_spacing)))
    # Amortized paragraph spacing: ~4 lines per average novel paragraph
    amortized_p_space = max(0.0, float(space_after_pt)) / 4.0
    slot = line_h + amortized_p_space
    lines = h_pt / slot
    return max(18.0, min(80.0, round(lines, 1)))


def calculate_chars_per_line(printable_width_cm: float, body_font_size: int = 12) -> int:
    """
    Dynamically computes average characters per line based on printable page width and font size.
    Base reference: 17.8cm printable width & 12pt font = 72 chars.
    """
    scale_w = printable_width_cm / 17.8
    scale_font = 12.0 / max(8, body_font_size)
    chars = 72.0 * scale_w * scale_font
    return max(40, min(140, int(round(chars))))


def calculate_toc_entries_per_page(printable_height_cm: float) -> int:
    """
    Dynamically computes how many chapter entries fit on 1 Table of Contents page.
    TOC title + header spacing occupies ~2.6cm. Each TOC row takes ~0.60cm.
    - Standard 1.2cm bottom margin (27.9cm height): ~40-42 chapters/page.
    - Narrow margins: up to 45 chapters/page.
    """
    avail_h = max(10.0, printable_height_cm - 2.6)
    entries = int(avail_h / 0.60)
    return max(18, min(50, entries))


def calculate_chapter_real_lines(
    body: str,
    chars_per_line: int = CHARS_PER_LINE_STANDARD,
    space_after_pt: float = 5.0
) -> float:
    """
    Calculates the exact printable line count for a chapter body.
    Includes:
    - Heading (CHAPTER X) + Ornament + Vertical spacing: ~4.5 lines
    - Paragraph text lines: ceil(len(paragraph) / chars_per_line)
    - Paragraph spacing: space_after_pt converted to line fraction
    """
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return 4.5

    total_lines = 4.5  # Heading + ornament overhead
    p_spacing_line_fraction = max(0.0, float(space_after_pt)) / 14.4  # relative to 12pt * 1.2

    for p in lines:
        p_len = len(p)
        text_lines = max(1, math.ceil(p_len / chars_per_line))
        total_lines += text_lines + p_spacing_line_fraction

    return total_lines


def estimate_chapter_pages(
    body: str,
    lines_per_page: float = LINES_PER_PAGE_STANDARD,
    chars_per_line: int = CHARS_PER_LINE_STANDARD,
    space_after_pt: float = 5.0
) -> float:
    """Estimates physical book pages for a chapter based on real line calculations."""
    lines = calculate_chapter_real_lines(body, chars_per_line=chars_per_line, space_after_pt=space_after_pt)
    return max(0.5, lines / max(15.0, lines_per_page))
