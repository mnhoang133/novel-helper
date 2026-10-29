"""
Module: core.docx_builder
Description: Builds professional, print-ready Word (.docx) documents featuring:
             - Two-sided Mirror Margins (<w:mirrorMargins/>) & Alternating Footers (<w:evenAndOddHeaders/>)
             - Smart Safe Binding Gutter protection
             - Redesigned Smart Pagination (Rule of 8.0 Lines)
             - Dynamic line counting & character metrics
Author: Google Deepmind Agent
"""

import os
import re
import math
import docx
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from typing import List, Tuple, Optional, Callable

from core.cleaner import sanitize_xml_string
from core.page_metrics import calculate_lines_per_page, calculate_chars_per_line


def add_xml_field(run, field_name: str):
    """Inserts a dynamic Word XML field (e.g., PAGE, TOC) into a text run."""
    fldSimple = OxmlElement('w:fldSimple')
    fldSimple.set(qn('w:instr'), field_name)
    run._r.append(fldSimple)


def export_single_document(
    chapters: List[Tuple[int, str, str]],
    output_docx_path: str,
    novel_title: str = "Invincible Mumu",
    subtitle: str = "Complete Edition",
    author: str = "Web Novel Author",
    imprint_note: str = "Print Edition • 2026",
    font_name: str = "Georgia",
    body_font_size: int = 14,
    chapter_font_size: int = 28,
    text_alignment: str = "justify",
    smart_pagination: bool = True,
    # Customizable Margins (Physical Book Printing Standard)
    inside_margin_cm: float = 2.0,      # Gáy sách / Binding Gutter
    outside_margin_cm: float = 1.2,     # Mép ngoài / Outer Margin
    top_margin_cm: float = 1.2,
    bottom_margin_cm: float = 1.2,
    footer_distance_cm: float = 0.7,
    header_distance_cm: float = 0.7,
    mirror_margins: bool = True,        # Lề đối xứng trang chẵn/lẻ
    on_progress: Optional[Callable[[int, int, str], None]] = None
) -> str:
    """
    Creates a professionally formatted physical-book Word document (.docx).

    Features:
    - Customizable page margins with validation limits.
    - True Mirror Margins (<w:mirrorMargins/>) for 2-sided book printing:
      Odd pages get 2.0cm on the left (inside); Even pages get 2.0cm on the right (inside)!
    - Redesigned Smart Pagination:
      If vertical space remains on the page to fit Chapter Heading + Ornament + AT LEAST 3 LINES,
      the chapter is allowed to start immediately without wasting page whitespace!
      Applies keep_with_next on heading and first paragraph so headings are never orphaned.
    - Clean cover page with title, subtitle, author, imprint, chapter range.
    - Automatic Table of Contents.
    - True book page numbering: Bottom right.
    """
    total = len(chapters)
    if total == 0:
        raise ValueError("No chapters to export!")

    # Bounds validation
    inside_margin_cm = max(0.5, min(5.0, float(inside_margin_cm)))
    outside_margin_cm = max(0.5, min(4.0, float(outside_margin_cm)))
    top_margin_cm = max(0.5, min(3.5, float(top_margin_cm)))
    bottom_margin_cm = max(0.5, min(3.5, float(bottom_margin_cm)))
    footer_distance_cm = max(0.3, min(2.5, float(footer_distance_cm)))
    header_distance_cm = max(0.3, min(2.5, float(header_distance_cm)))

    # Smart Mirror Margins Protection:
    # For physical book printing, the binding gutter (inside margin) MUST be wider
    # than the outer margin so text isn't swallowed by the spine during binding.
    # If inside <= outside (e.g. user set all margins to 0.6cm),
    # auto-elevate inside margin to safe binding width: max(1.2, round(outside * 2.0, 1))
    if mirror_margins:
        if inside_margin_cm <= outside_margin_cm:
            inside_margin_cm = max(1.2, round(outside_margin_cm * 2.0, 1))

    # Dynamic line and character capacity based on actual margins & font size
    printable_height_cm = max(15.0, 29.7 - (top_margin_cm + bottom_margin_cm))
    printable_width_cm = max(10.0, 21.0 - (inside_margin_cm + outside_margin_cm))
    lines_per_page = calculate_lines_per_page(printable_height_cm, body_font_size)
    chars_per_line = calculate_chars_per_line(printable_width_cm, body_font_size)

    # Sanitize metadata
    novel_title = sanitize_xml_string(novel_title)
    subtitle = sanitize_xml_string(subtitle)
    author = sanitize_xml_string(author)
    imprint_note = sanitize_xml_string(imprint_note)

    doc = docx.Document()

    # ----------------- SECTION MARGINS & MIRROR MARGINS -----------------
    sec = doc.sections[0]
    sec.left_margin = Cm(inside_margin_cm)     # Inside margin (Gáy sách)
    sec.right_margin = Cm(outside_margin_cm)   # Outside margin (Mép ngoài)
    sec.top_margin = Cm(top_margin_cm)
    sec.bottom_margin = Cm(bottom_margin_cm)
    sec.footer_distance = Cm(footer_distance_cm)
    sec.header_distance = Cm(header_distance_cm)
    sec.different_first_page_header_footer = True

    # Enable Mirror Margins and Even/Odd Headers in OpenXML for physical two-sided printing
    if mirror_margins:
        try:
            doc.settings.element.append(parse_xml(r'<w:mirrorMargins %s/>' % nsdecls('w')))
            doc.settings.element.append(parse_xml(r'<w:evenAndOddHeaders %s/>' % nsdecls('w')))
        except Exception:
            pass

    # ----------------- FOOTER: BOOK NUMBERING -----------------
    # Odd page footer: Right aligned (outer edge of odd pages)
    footer = sec.footer
    p_footer = footer.paragraphs[0]
    p_footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_num = p_footer.add_run()
    r_num.font.name = font_name
    r_num.font.size = Pt(10)
    r_num.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    add_xml_field(r_num, "PAGE")

    if mirror_margins:
        # Even page footer: Left aligned (outer edge of even pages)
        footer_even = sec.even_page_footer
        p_footer_even = footer_even.paragraphs[0]
        p_footer_even.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r_num_even = p_footer_even.add_run()
        r_num_even.font.name = font_name
        r_num_even.font.size = Pt(10)
        r_num_even.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        add_xml_field(r_num_even, "PAGE")

    # Clean cover page footer
    sec.first_page_footer.paragraphs[0].text = ""

    # ----------------- COVER PAGE (TITLE PAGE) -----------------
    if on_progress:
        on_progress(0, total, "Formatting cover page...")

    p_cover_top = doc.add_paragraph()
    p_cover_top.paragraph_format.space_before = Pt(70)

    # Novel Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run(novel_title.upper())
    r_title.font.name = font_name
    r_title.font.size = Pt(30)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    p_title.paragraph_format.space_after = Pt(14)

    # Subtitle
    if subtitle:
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_sub = p_sub.add_run(subtitle)
        r_sub.font.name = font_name
        r_sub.font.size = Pt(14)
        r_sub.font.italic = True
        r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
        p_sub.paragraph_format.space_after = Pt(24)

    # Author
    if author:
        p_author = doc.add_paragraph()
        p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_auth = p_author.add_run(f"by {author}")
        r_auth.font.name = font_name
        r_auth.font.size = Pt(13)
        r_auth.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        p_author.paragraph_format.space_after = Pt(120)

    # Imprint note / Chapter range at bottom of cover
    min_ch = chapters[0][0]
    max_ch = chapters[-1][0]
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_text = sanitize_xml_string(f"Chapters {min_ch} to {max_ch} • {total} Chapters Total\n{imprint_note}")
    r_meta = p_meta.add_run(meta_text)
    r_meta.font.name = font_name
    r_meta.font.size = Pt(10)
    r_meta.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    doc.add_page_break()

    # ----------------- TABLE OF CONTENTS -----------------
    if on_progress:
        on_progress(0, total, "Generating Table of Contents...")

    p_toc_heading = doc.add_paragraph()
    p_toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_toc_heading.paragraph_format.space_before = Pt(24)
    p_toc_heading.paragraph_format.space_after = Pt(24)
    r_toc_h = p_toc_heading.add_run("TABLE OF CONTENTS")
    r_toc_h.font.name = font_name
    r_toc_h.font.size = Pt(20)
    r_toc_h.font.bold = True
    r_toc_h.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    p_toc = doc.add_paragraph()
    p_toc.paragraph_format.space_after = Pt(24)
    run_toc_field = p_toc.add_run()
    add_xml_field(run_toc_field, r'TOC \o "1-1" \h \z \u')

    doc.add_page_break()

    # ----------------- CHAPTERS & SMART PAGINATION -----------------
    lines_on_current_page = 0.0

    for i, (ch_num, title, body) in enumerate(chapters):
        if on_progress:
            on_progress(i + 1, total, f"Adding Chapter {ch_num} ({i + 1}/{total})...")

        # Check if we should insert a page break before this chapter
        if i > 0:
            if not smart_pagination:
                # Standard mode: Every chapter starts on a new page
                doc.add_page_break()
                lines_on_current_page = 0.0
            else:
                # REDESIGNED SMART PAGINATION:
                # Check space remaining on current page (using dynamic page capacity)
                lines_remaining = lines_per_page - lines_on_current_page
                # Heading + ornament takes ~4.5 lines. 3 lines of text = 3 lines. Total required = 7.5 lines.
                if lines_remaining >= 8.0:
                    # Plenty of space! Allow chapter to start on current page.
                    # Insert decorative separator with spacing
                    p_sep = doc.add_paragraph()
                    p_sep.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p_sep.paragraph_format.space_before = Pt(24)
                    p_sep.paragraph_format.space_after = Pt(16)
                    p_sep.paragraph_format.keep_with_next = True
                    r_sep = p_sep.add_run("✦   ✦   ✦")
                    r_sep.font.name = font_name
                    r_sep.font.size = Pt(11)
                    r_sep.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
                    lines_on_current_page += 2.0
                else:
                    # Not enough room to fit heading + 3 lines cleanly!
                    # Page break to prevent awkward orphan headings.
                    doc.add_page_break()
                    lines_on_current_page = 0.0

        # Chapter Header (Prominent, 26-30pt)
        h = doc.add_heading(level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        h.paragraph_format.space_before = Pt(20) if lines_on_current_page == 0 else Pt(10)
        h.paragraph_format.space_after = Pt(8)
        h.paragraph_format.keep_with_next = True  # NEVER separate heading from content

        r_ch_title = h.add_run(sanitize_xml_string(f"CHAPTER {ch_num}"))
        r_ch_title.font.name = font_name
        r_ch_title.font.size = Pt(chapter_font_size)
        r_ch_title.font.bold = True
        r_ch_title.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

        # Subtle Chapter ornament
        p_div = doc.add_paragraph()
        p_div.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_div.paragraph_format.space_after = Pt(14)
        p_div.paragraph_format.keep_with_next = True  # Keep ornament with text
        r_div = p_div.add_run("~ ✦ ~")
        r_div.font.name = font_name
        r_div.font.size = Pt(11)
        r_div.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

        lines_on_current_page += 4.5

        # Chapter body paragraphs
        lines = [sanitize_xml_string(line.strip()) for line in body.splitlines() if line.strip()]

        for p_idx, line in enumerate(lines):
            if re.match(r'^(CHAPTER|Chapter|Chương)\s+\d+', line, re.IGNORECASE):
                continue

            p = doc.add_paragraph()
            if text_alignment == "left":
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.space_after = Pt(7)

            # Keep the first paragraph with the heading so Word will never break between them
            if p_idx == 0:
                p.paragraph_format.keep_with_next = True

            r_p = p.add_run(line)
            r_p.font.name = font_name
            r_p.font.size = Pt(body_font_size)
            r_p.font.color.rgb = RGBColor(0x11, 0x18, 0x27)

            # Dynamic line counting for this paragraph based on printable width
            p_lines = max(1, math.ceil(len(line) / chars_per_line)) + 0.3
            lines_on_current_page += p_lines
            if lines_on_current_page >= lines_per_page:
                lines_on_current_page = lines_on_current_page % lines_per_page

    os.makedirs(os.path.dirname(os.path.abspath(output_docx_path)), exist_ok=True)
    doc.save(output_docx_path)
    return output_docx_path
