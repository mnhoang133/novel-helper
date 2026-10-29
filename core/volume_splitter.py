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
    tier_name: str               # e.g. "Tập vừa (200-300 trang)", "Tối ưu khít Mục lục"
    num_volumes: int
    target_pages: int
    avg_chapters_per_vol: int
    avg_pages_per_vol: float
    toc_pages_per_vol: int
    toc_fill_percentage: float
    toc_quality_rating: str      # e.g. "Tối ưu khít (1 trang mục lục, lấp đầy 92%)"
    is_recommended: bool
    summary_text: str
    volume_ranges: List[Tuple[int, int, int, float]]  # [(vol_idx, start_ch, end_ch, est_pages), ...]
    lines_per_page: float = 32.0
    chars_per_line: int = 68
    toc_entries_per_page: int = 32
    badge_text: str = ""


def partition_chapters_balanced(
    chapter_metrics: List[Tuple[int, float]],
    k: int,
    lines_per_page: float
) -> List[Tuple[int, int, int, float]]:
    """
    Partitions chapters into k groups with mathematically equalized chapter counts
    (difference between any two volumes is at most 1 chapter) and estimated pages.
    Returns: [(v_idx, start_ch, end_ch, est_pages), ...]
    """
    total = len(chapter_metrics)
    k = max(1, min(k, total))
    base_ch = total // k
    rem_ch = total % k

    vol_ranges = []
    curr_idx = 0
    for v in range(1, k + 1):
        count = base_ch + (1 if v <= rem_ch else 0)
        group = chapter_metrics[curr_idx : curr_idx + count]
        start_ch = group[0][0]
        end_ch = group[-1][0]
        group_lines = sum(item[1] for item in group)
        est_p = round((group_lines / lines_per_page) + 2.0, 1)  # +2 for cover and TOC
        vol_ranges.append((v, start_ch, end_ch, est_p))
        curr_idx += count

    return vol_ranges


def _evaluate_toc_quality(avg_ch: float, toc_cap: int) -> Tuple[int, float, str]:
    """Computes TOC page count, fill percentage, and descriptive rating."""
    if avg_ch <= toc_cap:
        toc_pages = 1
        toc_fill = round((avg_ch / float(toc_cap)) * 100.0, 1)
        if toc_fill >= 75:
            toc_quality = f"Tối ưu khít (1 trang mục lục, lấp đầy {toc_fill:.0f}%)"
        else:
            toc_quality = f"Vừa vặn (1 trang mục lục, {avg_ch:.0f}/{toc_cap} chap, lấp đầy {toc_fill:.0f}%)"
    elif avg_ch <= toc_cap * 2:
        toc_pages = 2
        p2_entries = avg_ch - toc_cap
        toc_fill = round((p2_entries / float(toc_cap)) * 100.0, 1)
        if toc_fill >= 70:
            toc_quality = f"Tối ưu khít (2 trang mục lục, trang 2 lấp đầy {toc_fill:.0f}%)"
        elif toc_fill <= 25:
            toc_quality = f"Cảnh báo tràn nhẹ (Trang 2 mục lục chỉ có {p2_entries:.0f} chương, lãng phí giấy)"
        else:
            toc_quality = f"Ổn định (2 trang mục lục, {avg_ch:.0f}/{toc_cap * 2} chap)"
    else:
        toc_pages = math.ceil(avg_ch / float(toc_cap))
        toc_fill = 50.0
        toc_quality = f"~ {toc_pages} trang mục lục ({avg_ch:.0f} chương)"
    return toc_pages, toc_fill, toc_quality


def analyze_optimal_volume_splits(
    chapters: List[Tuple[int, str, str]],
    inside_margin_cm: float = 2.0,
    outside_margin_cm: float = 1.2,
    top_margin_cm: float = 1.2,
    bottom_margin_cm: float = 1.2,
    body_font_size: int = 14
) -> Dict[str, VolumeSplitOption]:
    """
    Analyzes all chapters and calculates balanced volume partitions for:
    1. Special Tier: Khít Mục lục & Đều chương (Full TOC 1-2 trang, bất kể số trang)
    2. Tier 1: Tập mỏng (50 - 100 trang)
    3. Tier 2: Tập chuẩn (100 - 200 trang)
    4. Tier 3: Tập vừa (200 - 300 trang)
    5. Tier 4: Tập dày (300 - 400 trang)
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
    results = {}

    # -------------------------------------------------------------------------
    # 1. SPECIAL TIER 1: TỐI ƯU 1 TRANG MỤC LỤC (FULL 1-PAGE TOC)
    # -------------------------------------------------------------------------
    best_k_1p = 1
    best_score_1p = -999.0

    for cand_k in range(1, min(total_chapters + 1, 30)):
        avg_ch_cand = total_chapters / float(cand_k)
        if avg_ch_cand <= toc_entries_per_page:
            fill_cand = (avg_ch_cand / float(toc_entries_per_page)) * 100.0
            score = 100.0 - abs(95.0 - fill_cand) * 1.5
            if 15 <= avg_ch_cand <= 45:
                score += 5.0
            if score > best_score_1p:
                best_score_1p = score
                best_k_1p = cand_k

    opt_ranges_1p = partition_chapters_balanced(chapter_metrics, best_k_1p, lines_per_page)
    opt_avg_ch_1p = round(total_chapters / float(best_k_1p))
    opt_avg_pg_1p = round(sum(vr[3] for vr in opt_ranges_1p) / float(best_k_1p), 1)
    toc_p1, toc_f1, toc_q1 = _evaluate_toc_quality(opt_avg_ch_1p, toc_entries_per_page)

    tier_label_1p = "Tier Tối ưu 1: Khít 1 trang Mục lục (Full 1 trang TOC)"
    summary_1p = (
        f"TỐI ƯU 1 TRANG MỤC LỤC: Chia đều {best_k_1p} tập (~{opt_avg_ch_1p} chương/tập, chênh lệch tối đa 1 chương).\n"
        f"Ước tính: ~{opt_avg_pg_1p} trang/tập. Đánh giá Mục lục: {toc_q1}"
    )

    results[tier_label_1p] = VolumeSplitOption(
        tier_name=tier_label_1p,
        num_volumes=best_k_1p,
        target_pages=int(round(opt_avg_pg_1p)),
        avg_chapters_per_vol=opt_avg_ch_1p,
        avg_pages_per_vol=opt_avg_pg_1p,
        toc_pages_per_vol=toc_p1,
        toc_fill_percentage=toc_f1,
        toc_quality_rating=toc_q1,
        is_recommended=True,
        summary_text=summary_1p,
        volume_ranges=opt_ranges_1p,
        lines_per_page=lines_per_page,
        chars_per_line=chars_per_line,
        toc_entries_per_page=toc_entries_per_page,
        badge_text="[TỐI ƯU 1 TRANG TOC - ĐỀU CHƯƠNG]"
    )

    # -------------------------------------------------------------------------
    # 2. SPECIAL TIER 2: TỐI ƯU 2 TRANG MỤC LỤC (FULL 2-PAGE TOC - CUỐN DÀY / CHAP NGẮN)
    # -------------------------------------------------------------------------
    if total_chapters > toc_entries_per_page:
        best_k_2p = 1
        best_score_2p = -999.0

        for cand_k in range(1, min(total_chapters + 1, 30)):
            avg_ch_cand = total_chapters / float(cand_k)
            if toc_entries_per_page < avg_ch_cand <= toc_entries_per_page * 2:
                p2 = avg_ch_cand - toc_entries_per_page
                fill_p2 = (p2 / float(toc_entries_per_page)) * 100.0
                score = 100.0 - abs(95.0 - fill_p2) * 1.5
                if 45 <= avg_ch_cand <= 85:
                    score += 5.0
                if score > best_score_2p:
                    best_score_2p = score
                    best_k_2p = cand_k

        if best_score_2p > -900.0:
            opt_ranges_2p = partition_chapters_balanced(chapter_metrics, best_k_2p, lines_per_page)
            opt_avg_ch_2p = round(total_chapters / float(best_k_2p))
            opt_avg_pg_2p = round(sum(vr[3] for vr in opt_ranges_2p) / float(best_k_2p), 1)
            toc_p2, toc_f2, toc_q2 = _evaluate_toc_quality(opt_avg_ch_2p, toc_entries_per_page)

            tier_label_2p = "Tier Tối ưu 2: Khít 2 trang Mục lục (Full 2 trang TOC - Cuốn dày / Chap ngắn)"
            summary_2p = (
                f"TỐI ƯU 2 TRANG MỤC LỤC: Chia đều {best_k_2p} tập (~{opt_avg_ch_2p} chương/tập, chênh lệch tối đa 1 chương).\n"
                f"Ước tính: ~{opt_avg_pg_2p} trang/tập. Đánh giá Mục lục: {toc_q2}"
            )

            results[tier_label_2p] = VolumeSplitOption(
                tier_name=tier_label_2p,
                num_volumes=best_k_2p,
                target_pages=int(round(opt_avg_pg_2p)),
                avg_chapters_per_vol=opt_avg_ch_2p,
                avg_pages_per_vol=opt_avg_pg_2p,
                toc_pages_per_vol=toc_p2,
                toc_fill_percentage=toc_f2,
                toc_quality_rating=toc_q2,
                is_recommended=True,
                summary_text=summary_2p,
                volume_ranges=opt_ranges_2p,
                lines_per_page=lines_per_page,
                chars_per_line=chars_per_line,
                toc_entries_per_page=toc_entries_per_page,
                badge_text="[TỐI ƯU 2 TRANG TOC - CUỐN DÀY]"
            )

    # -------------------------------------------------------------------------
    # 2. STANDARD PAGE BOUND TIERS (50-100, 100-200, 200-300, 300-400)
    # -------------------------------------------------------------------------
    standard_tiers = [
        ("Tier 1: Tập mỏng (50 - 100 trang)", 50, 100, 75),
        ("Tier 2: Tập chuẩn (100 - 200 trang)", 100, 200, 150),
        ("Tier 3: Tập vừa (200 - 300 trang)", 200, 300, 250),
        ("Tier 4: Tập dày (300 - 400 trang)", 300, 400, 350),
    ]

    for tier_label, min_p, max_p, ideal_p in standard_tiers:
        raw_k = total_body_pages / float(ideal_p)
        k = max(1, round(raw_k))

        avg_p = total_body_pages / float(k)
        if avg_p < min_p and k > 1:
            k = max(1, math.floor(total_body_pages / float(min_p)))
        elif avg_p > max_p:
            k = max(1, math.ceil(total_body_pages / float(max_p)))

        # Partition chapters mathematically evenly
        vol_ranges = partition_chapters_balanced(chapter_metrics, k, lines_per_page)
        actual_k = len(vol_ranges)
        avg_ch = round(total_chapters / float(actual_k))
        avg_pg = round(sum(vr[3] for vr in vol_ranges) / float(actual_k), 1)

        toc_pages, toc_fill, toc_quality = _evaluate_toc_quality(avg_ch, toc_entries_per_page)

        summary = (
            f"Chia đều thành {actual_k} tập • Trung bình ~{avg_ch} chương/tập (~{avg_pg} trang/tập).\n"
            f"Đánh giá Mục lục: {toc_quality}"
        )

        opt = VolumeSplitOption(
            tier_name=tier_label,
            num_volumes=actual_k,
            target_pages=int(round(avg_pg)),
            avg_chapters_per_vol=avg_ch,
            avg_pages_per_vol=avg_pg,
            toc_pages_per_vol=toc_pages,
            toc_fill_percentage=toc_fill,
            toc_quality_rating=toc_quality,
            is_recommended=False,
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
    Guarantees equalized chapter distribution so no volume differs from another by more than 1 chapter.
    """
    if not chapters:
        return []

    total_chapters = len(chapters)
    total_body_lines = sum(
        calculate_chapter_real_lines(ch[2], chars_per_line=chars_per_line)
        for ch in chapters
    )
    total_pages = (total_body_lines / lines_per_page) + 2.0  # +2 cover + TOC

    # Target volumes K
    k = max(1, round(total_pages / float(target_pages_per_volume)))
    base_ch = total_chapters // k
    rem_ch = total_chapters % k

    volumes = []
    curr_idx = 0
    for v_idx in range(1, k + 1):
        count = base_ch + (1 if v_idx <= rem_ch else 0)
        vol_chapters = chapters[curr_idx : curr_idx + count]
        start_ch = vol_chapters[0][0]
        end_ch = vol_chapters[-1][0]
        vol_title = f"Volume {v_idx:02d} (Chapters {start_ch}–{end_ch})"
        volumes.append((v_idx, vol_title, vol_chapters))
        curr_idx += count

    return volumes
