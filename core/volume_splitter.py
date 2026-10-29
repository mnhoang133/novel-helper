"""
Module: core.volume_splitter
Description: Balanced chapter-volume partitioning engine that prevents orphan last volumes,
             with Table of Contents capacity analysis adapted dynamically to user margins.
Author: Google Deepmind Agent
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict
from core.page_metrics import (
    calculate_lines_per_page,
    calculate_chars_per_line,
    calculate_toc_entries_per_page,
    calculate_chapter_real_lines,
    LINES_PER_PAGE_STANDARD,
    CHARS_PER_LINE_STANDARD
)


@dataclass
class VolumeSplitOption:
    tier_name: str               # "Mỏng (50-100 trang)", "Chuẩn (100-200 trang)", "Dày (300-400 trang)"
    num_volumes: int
    target_pages: int
    avg_chapters_per_vol: int
    avg_pages_per_vol: float
    toc_pages_per_vol: int
    toc_fill_percentage: float
    toc_quality_rating: str      # "Tối ưu khít 1 trang", "Vừa vặn", "Cảnh báo tràn nhẹ"
    is_recommended: bool
    summary_text: str
    volume_ranges: List[Tuple[int, int, int, float]]  # [(vol_idx, start_ch, end_ch, est_pages), ...]
    lines_per_page: float = 32.0
    chars_per_line: int = 68
    toc_entries_per_page: int = 32


def analyze_optimal_volume_splits(
    chapters: List[Tuple[int, str, str]],
    inside_margin_cm: float = 2.0,
    outside_margin_cm: float = 1.2,
    top_margin_cm: float = 1.2,
    bottom_margin_cm: float = 1.2,
    body_font_size: int = 14
) -> Dict[str, VolumeSplitOption]:
    """
    Analyzes all chapters and calculates balanced volume partitions for 3 standard book tiers
    using DYNAMIC page height, margins, and font size parameters:
    1. Tier 1: Thin / Pocket (50-100 pages)
    2. Tier 2: Standard Trade (100-200 pages)
    3. Tier 3: Thick / Omnibus (300-400 pages)

    Guarantees:
    - Equalized volume distribution (no awkward 2-chapter stub on the final volume).
    - Real line-count precision adapted to user margins.
    - TOC page fitting analysis (adapts to narrow margins >32 chap or wide margins <32 chap).
    """
    if not chapters:
        return {}

    # Dynamic page dimensions based on user inputs
    printable_height_cm = max(15.0, 29.7 - (top_margin_cm + bottom_margin_cm))
    printable_width_cm = max(10.0, 21.0 - (inside_margin_cm + outside_margin_cm))
    lines_per_page = calculate_lines_per_page(printable_height_cm, body_font_size)
    chars_per_line = calculate_chars_per_line(printable_width_cm, body_font_size)
    toc_entries_per_page = calculate_toc_entries_per_page(printable_height_cm)

    total_chapters = len(chapters)
    chapter_metrics = []
    total_body_lines = 0.0

    for ch_num, title, body in chapters:
        lines = calculate_chapter_real_lines(body, chars_per_line=chars_per_line)
        chapter_metrics.append((ch_num, lines))
        total_body_lines += lines

    total_body_pages = total_body_lines / lines_per_page

    # Target page bounds for each tier
    tiers = [
        ("Tier 1: Tập mỏng (50 - 100 trang)", 50, 100, 75),
        ("Tier 2: Tập chuẩn (100 - 200 trang)", 100, 200, 160),
        ("Tier 3: Tập dày (300 - 400 trang)", 250, 400, 320),
    ]

    results = {}

    for tier_label, min_p, max_p, ideal_p in tiers:
        raw_k = total_body_pages / ideal_p
        k = max(1, round(raw_k))

        avg_p = total_body_pages / k
        if avg_p < min_p and k > 1:
            k = max(1, math.floor(total_body_pages / min_p))
            avg_p = total_body_pages / k
        elif avg_p > max_p:
            k = max(1, math.ceil(total_body_pages / max_p))
            avg_p = total_body_pages / k

        # Balanced partition of chapters into k groups
        target_lines_per_vol = total_body_lines / float(k)
        vol_ranges = []

        curr_start = 0
        curr_lines = 0.0
        v_idx = 1

        for c_idx, (ch_num, c_lines) in enumerate(chapter_metrics):
            curr_lines += c_lines
            remaining_chapters = total_chapters - (c_idx + 1)
            remaining_volumes = k - v_idx

            should_cut = False
            if remaining_volumes > 0:
                if remaining_chapters <= remaining_volumes:
                    should_cut = True
                elif curr_lines >= target_lines_per_vol:
                    should_cut = True

            if should_cut:
                start_ch = chapter_metrics[curr_start][0]
                end_ch = ch_num
                est_p = round((curr_lines / lines_per_page) + 2.0, 1)  # +2 for cover and TOC
                vol_ranges.append((v_idx, start_ch, end_ch, est_p))
                curr_start = c_idx + 1
                curr_lines = 0.0
                v_idx += 1

        # Add remaining chapters to final volume
        if curr_start < total_chapters:
            start_ch = chapter_metrics[curr_start][0]
            end_ch = chapter_metrics[-1][0]
            est_p = round((curr_lines / lines_per_page) + 2.0, 1)
            vol_ranges.append((v_idx, start_ch, end_ch, est_p))

        actual_k = len(vol_ranges)
        avg_ch = round(total_chapters / actual_k)
        avg_pg = round(sum(vr[3] for vr in vol_ranges) / actual_k, 1)

        # TOC Fit Analysis adapted to actual page capacity
        if avg_ch <= toc_entries_per_page:
            toc_pages = 1
            toc_fill = round((avg_ch / float(toc_entries_per_page)) * 100.0, 1)
            if toc_fill >= 70:
                toc_quality = f"Tối ưu khít (1 trang mục lục, lấp đầy {toc_fill:.0f}%)"
            else:
                toc_quality = f"Vừa vặn (1 trang mục lục, {avg_ch}/{toc_entries_per_page} chap)"
        elif avg_ch <= toc_entries_per_page * 2:
            toc_pages = 2
            p2_entries = avg_ch - toc_entries_per_page
            toc_fill = round((p2_entries / float(toc_entries_per_page)) * 100.0, 1)
            if toc_fill >= 70:
                toc_quality = f"Tối ưu khít (2 trang mục lục, trang 2 lấp đầy {toc_fill:.0f}%)"
            elif toc_fill <= 20:
                toc_quality = f"Cảnh báo tràn nhẹ (Trang 2 mục lục chỉ có {p2_entries} chương, lãng phí giấy)"
            else:
                toc_quality = f"Ổn định (2 trang mục lục, {avg_ch}/{toc_entries_per_page * 2} chap)"
        else:
            toc_pages = math.ceil(avg_ch / float(toc_entries_per_page))
            toc_quality = f"~ {toc_pages} trang mục lục ({avg_ch} chương)"

        is_recom = ("Tối ưu khít" in toc_quality or actual_k in (3, 4, 5))

        summary = (
            f"Chia thành {actual_k} tập • Trung bình ~{avg_ch} chương/tập (~{avg_pg} trang/tập).\n"
            f"Đánh giá Mục lục: {toc_quality}"
        )

        opt = VolumeSplitOption(
            tier_name=tier_label,
            num_volumes=actual_k,
            target_pages=int(round(avg_pg)),
            avg_chapters_per_vol=avg_ch,
            avg_pages_per_vol=avg_pg,
            toc_pages_per_vol=toc_pages,
            toc_fill_percentage=toc_fill if 'toc_fill' in locals() else 50.0,
            toc_quality_rating=toc_quality,
            is_recommended=is_recom,
            summary_text=summary,
            volume_ranges=vol_ranges,
            lines_per_page=lines_per_page,
            chars_per_line=chars_per_line,
            toc_entries_per_page=toc_entries_per_page
        )
        results[tier_label] = opt

    return results


def split_chapters_into_volumes(
    chapters: List[Tuple[int, str, str]],
    target_pages_per_volume: int = 250,
    lines_per_page: float = LINES_PER_PAGE_STANDARD,
    chars_per_line: int = CHARS_PER_LINE_STANDARD
) -> List[Tuple[int, str, List[Tuple[int, str, str]]]]:
    """
    Splits chapter list into balanced book volumes based on target page count.
    Uses balanced chapter-volume partitioning to prevent orphan last volumes.
    """
    if not chapters:
        return []

    total_chapters = len(chapters)
    chapter_metrics = []
    total_body_lines = 0.0

    for ch in chapters:
        lines = calculate_chapter_real_lines(ch[2], chars_per_line=chars_per_line)
        chapter_metrics.append((ch, lines))
        total_body_lines += lines

    total_pages = (total_body_lines / lines_per_page) + 2.0  # +2 cover + TOC

    # Target volumes K
    k = max(1, round(total_pages / float(target_pages_per_volume)))
    target_lines_per_vol = total_body_lines / float(k)

    volumes = []
    curr_vol_chapters = []
    curr_vol_lines = 0.0
    v_idx = 1

    for c_idx, (ch_tuple, c_lines) in enumerate(chapter_metrics):
        curr_vol_chapters.append(ch_tuple)
        curr_vol_lines += c_lines

        remaining_chapters = total_chapters - (c_idx + 1)
        remaining_volumes = k - v_idx

        should_cut = False
        if remaining_volumes > 0:
            if remaining_chapters <= remaining_volumes:
                should_cut = True
            elif curr_vol_lines >= target_lines_per_vol:
                should_cut = True

        if should_cut:
            start_ch = curr_vol_chapters[0][0]
            end_ch = curr_vol_chapters[-1][0]
            vol_title = f"Volume {v_idx} (Chapters {start_ch}–{end_ch})"
            volumes.append((v_idx, vol_title, curr_vol_chapters))
            curr_vol_chapters = []
            curr_vol_lines = 0.0
            v_idx += 1

    if curr_vol_chapters:
        start_ch = curr_vol_chapters[0][0]
        end_ch = curr_vol_chapters[-1][0]
        vol_title = f"Volume {v_idx} (Chapters {start_ch}–{end_ch})"
        volumes.append((v_idx, vol_title, curr_vol_chapters))

    return volumes
