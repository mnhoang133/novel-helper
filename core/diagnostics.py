"""
Module: core.diagnostics
Description: Generates detailed, transparent export diagnostics reports (last_export_report.txt)
             recording exact margins, OpenXML tags, dynamic page capacities, and file output paths.
Author: Google Deepmind Agent
"""

import os
import datetime
from typing import List, Dict, Any, Optional


def generate_export_diagnostics(
    output_dir: str,
    novel_title: str,
    author: str,
    volumes: List[Any],
    inside_margin_cm: float,
    outside_margin_cm: float,
    top_margin_cm: float,
    bottom_margin_cm: float,
    footer_distance_cm: float,
    mirror_margins: bool,
    lines_per_page: float,
    chars_per_line: int,
    toc_capacity: int,
    created_files: List[str]
) -> str:
    """
    Writes a human and AI readable diagnostics summary into `output_dir/last_export_report.txt`.
    Provides immediate observability into exact layout geometry and prevents debugging black boxes.
    """
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "last_export_report.txt")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Safe binding elevation check
    safe_elevation_triggered = mirror_margins and (inside_margin_cm > outside_margin_cm and inside_margin_cm >= 1.2)

    lines = [
        "=" * 70,
        "  PRINT PUBLICATION DIAGNOSTICS & AUDIT REPORT",
        "=" * 70,
        f"Generated At      : {now_str}",
        f"Novel Title       : {novel_title}",
        f"Author            : {author}",
        f"Total Volumes     : {len(volumes)}",
        "",
        "--- [1. MARGINS & PHYSICAL BOOK BINDING] ---",
        f"Mirror Margins    : {'ENABLED (Facing pages for 2-sided book printing)' if mirror_margins else 'DISABLED (Uniform margins)'}",
        f"Inside (Gáy dán)  : {inside_margin_cm:.1f} cm",
        f"Outside (Mép ngoài): {outside_margin_cm:.1f} cm",
        f"Top Margin        : {top_margin_cm:.1f} cm",
        f"Bottom Margin     : {bottom_margin_cm:.1f} cm",
        f"Footer Distance   : {footer_distance_cm:.1f} cm",
        "",
        "Effective Geometry Applied to OpenXML Document:",
        f"  • Odd Pages (Trang lẻ) : Left={inside_margin_cm:.1f}cm (Gáy), Right={outside_margin_cm:.1f}cm (Mép ngoài)",
        f"  • Even Pages (Trang chẵn): Left={outside_margin_cm:.1f}cm (Mép ngoài), Right={inside_margin_cm:.1f}cm (Gáy)",
        f"  • Footer Numbering     : Odd pages -> Bottom-Right | Even pages -> Bottom-Left",
        "",
        "--- [2. DYNAMIC PAGE CAPACITY & TOC EFFICIENCY] ---",
        f"Printable Width   : {21.0 - (inside_margin_cm + outside_margin_cm):.1f} cm",
        f"Printable Height  : {29.7 - (top_margin_cm + bottom_margin_cm):.1f} cm",
        f"Lines Per Page    : ~{lines_per_page:.1f} body lines/page",
        f"Chars Per Line    : ~{chars_per_line} characters/line",
        f"TOC Page Capacity : ~{toc_capacity} chapters per single TOC page",
        "",
        "--- [3. VOLUMES BREAKDOWN] ---"
    ]

    for v_idx, v_info in enumerate(volumes):
        # v_info is either (v_num, v_title, v_chapters) or dict
        if isinstance(v_info, (tuple, list)):
            v_num = v_info[0]
            v_title = v_info[1]
            ch_list = v_info[2]
            start_ch = ch_list[0][0] if ch_list else 0
            end_ch = ch_list[-1][0] if ch_list else 0
            count_ch = len(ch_list)
            lines.append(f"  • Volume {v_num:02d}: Ch {start_ch} to Ch {end_ch} ({count_ch} chapters)")
        else:
            lines.append(f"  • {v_info}")

    lines.extend([
        "",
        "--- [4. GENERATED FILES] ---"
    ])
    for f in created_files:
        lines.append(f"  -> {os.path.basename(f)}")

    lines.extend([
        "",
        "=" * 70,
        "End of Diagnostics Report."
    ])

    report_content = "\n".join(lines)
    try:
        with open(report_path, "w", encoding="utf-8") as fp:
            fp.write(report_content)
    except Exception as e:
        print(f"Failed to write diagnostics report: {e}")

    return report_path
