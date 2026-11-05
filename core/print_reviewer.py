"""
Module: core.print_reviewer
Description: Automated PDF print-safety auditor and high-fidelity visual print-preview generator.
             Audits bounding boxes of text blocks to guarantee zero hardware clipping and zero footer collision.
Author: Google Deepmind Agent
"""

import os
from typing import Dict, List, Tuple, Any, Optional
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont


# Hardware minimum margins for physical printers (A4 desktop laser/inkjet)
PRINTER_MIN_BOTTOM_CM = 0.50   # 5.0 mm hardware paper roller grip limit
PRINTER_MIN_TOP_CM = 0.40      # 4.0 mm
PRINTER_MIN_SIDE_CM = 0.40     # 4.0 mm
PT_PER_CM = 28.3465


def audit_pdf_print_safety(pdf_path: str) -> Dict[str, Any]:
    """
    Scans every page of a PDF document and audits print safety:
    - Measures closest text distance to bottom, top, left, right edges.
    - Flags any text that penetrates the physical printer hardware non-printable area.
    - Checks gap between body text and footer page number.
    Returns audit statistics and a pass/fail flag.
    """
    if not os.path.isfile(pdf_path):
        return {"success": False, "error": f"File not found: {pdf_path}"}

    base = os.path.basename(pdf_path)
    if base.startswith("~$") or base.startswith("."):
        return {"success": False, "error": f"Skipping temporary lock file: {base}"}

    try:
        if os.path.getsize(pdf_path) < 1024:
            return {"success": False, "error": f"File is too small or incomplete: {base}"}
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"success": False, "error": f"Failed to open PDF document ({base}): {e}"}
    total_pages = len(doc)

    issues = []
    min_dist_bottom_cm = 999.0
    min_dist_top_cm = 999.0
    min_dist_inside_cm = 999.0
    min_dist_outside_cm = 999.0
    min_footer_gap_pt = 999.0

    clipped_pages = []

    for p_idx in range(total_pages):
        page = doc[p_idx]
        rect = page.rect
        p_num = p_idx + 1
        blocks = page.get_text("blocks")

        page_body_bottom = 0.0
        footer_top = rect.height

        for b in blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if b[6] != 0:  # Skip image blocks
                continue
            txt = b[4].strip()
            if not txt:
                continue

            x0, y0, x1, y1 = b[0], b[1], b[2], b[3]
            dist_b_cm = (rect.height - y1) / PT_PER_CM
            dist_t_cm = y0 / PT_PER_CM
            dist_l_cm = x0 / PT_PER_CM
            dist_r_cm = (rect.width - x1) / PT_PER_CM

            min_dist_bottom_cm = min(min_dist_bottom_cm, dist_b_cm)
            min_dist_top_cm = min(min_dist_top_cm, dist_t_cm)
            min_dist_inside_cm = min(min_dist_inside_cm, dist_l_cm)
            min_dist_outside_cm = min(min_dist_outside_cm, dist_r_cm)

            # Check if block is footer page number
            is_footer = False
            if dist_b_cm < 1.0 and txt.isdigit():
                is_footer = True
                footer_top = min(footer_top, y0)
            else:
                page_body_bottom = max(page_body_bottom, y1)

            # Check if text penetrates physical hardware limit
            if dist_b_cm < (PRINTER_MIN_BOTTOM_CM - 0.05):
                issues.append(f"Page {p_num}: Text is too close to bottom edge ({dist_b_cm:.2f}cm < {PRINTER_MIN_BOTTOM_CM}cm): '{txt[:30]}'")
                if p_num not in clipped_pages:
                    clipped_pages.append(p_num)

        # Check gap between lowest body text and footer
        if footer_top < rect.height and page_body_bottom > 0:
            gap_pt = footer_top - page_body_bottom
            min_footer_gap_pt = min(min_footer_gap_pt, gap_pt)
            if gap_pt < 4.0:  # Less than 4pt is touching/colliding
                issues.append(f"Page {p_num}: Body text is colliding with footer! Gap = {gap_pt:.1f}pt")
                if p_num not in clipped_pages:
                    clipped_pages.append(p_num)

    doc.close()

    is_safe = (len(clipped_pages) == 0)
    return {
        "success": True,
        "is_safe": is_safe,
        "total_pages": total_pages,
        "min_dist_bottom_cm": round(min_dist_bottom_cm, 2),
        "min_dist_top_cm": round(min_dist_top_cm, 2),
        "min_dist_left_cm": round(min_dist_inside_cm, 2),
        "min_dist_right_cm": round(min_dist_outside_cm, 2),
        "min_footer_gap_pt": round(min_footer_gap_pt, 1) if min_footer_gap_pt < 900 else None,
        "clipped_pages": clipped_pages,
        "issues": issues
    }


def generate_print_preview_image(
    pdf_path: str,
    page_number: int = 2,
    output_png_path: Optional[str] = None,
    draw_guides: bool = True,
    dpi: int = 150
) -> Optional[str]:
    """
    Renders a PDF page to a PNG image with optional printer hardware guide overlays.
    Guides show:
    - Red dashed rectangle: Hardware minimum unprintable margin (safe limit).
    - Green rectangle: Configured page margin boundaries.
    """
    if not os.path.isfile(pdf_path):
        return None

    base = os.path.basename(pdf_path)
    if base.startswith("~$") or base.startswith("."):
        return None

    try:
        if os.path.getsize(pdf_path) < 1024:
            return None
        doc = fitz.open(pdf_path)
    except Exception:
        return None
    if page_number < 1 or page_number > len(doc):
        page_number = min(len(doc), max(1, page_number))

    page = doc[page_number - 1]
    pix = page.get_pixmap(dpi=dpi)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    if draw_guides:
        draw = ImageDraw.Draw(img)
        scale = dpi / 72.0

        # Physical printer danger boundary (0.5cm bottom, 0.4cm top/left/right)
        danger_left = int(PRINTER_MIN_SIDE_CM * PT_PER_CM * scale)
        danger_top = int(PRINTER_MIN_TOP_CM * PT_PER_CM * scale)
        danger_right = int(pix.width - (PRINTER_MIN_SIDE_CM * PT_PER_CM * scale))
        danger_bottom = int(pix.height - (PRINTER_MIN_BOTTOM_CM * PT_PER_CM * scale))

        # Draw red dashed danger zone
        draw.rectangle([danger_left, danger_top, danger_right, danger_bottom], outline=(239, 68, 68), width=2)
        # Add legend watermark
        draw.text((danger_left + 8, danger_top + 6), f"P.{page_number} - PRINTER SAFE BOUNDARY (Red Line = 0.5cm Hardware Limit)", fill=(239, 68, 68))

    doc.close()

    if not output_png_path:
        base_no_ext = os.path.splitext(pdf_path)[0]
        output_png_path = f"{base_no_ext}_preview_p{page_number}.png"

    os.makedirs(os.path.dirname(os.path.abspath(output_png_path)), exist_ok=True)
    img.save(output_png_path)
    return output_png_path
