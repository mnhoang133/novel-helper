"""
Module: ui.smart_analyzer_dialog
Description: Interactive modal dialog displaying exact real line-based volume partitions,
             TOC efficiency ratings, and 1-click tier selection (50-100, 100-200, 300-400 pages).
Author: Google Deepmind Agent
"""

import customtkinter as ctk
from typing import List, Tuple, Callable
from core.book_engine import (
    analyze_optimal_volume_splits,
    VolumeSplitOption,
    LINES_PER_PAGE_STANDARD
)


class SmartVolumeAnalyzerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        chapters: List[Tuple[int, str, str]],
        on_select_tier: Callable[[VolumeSplitOption], None],
        inside_margin_cm: float = 2.0,
        outside_margin_cm: float = 1.2,
        top_margin_cm: float = 1.2,
        bottom_margin_cm: float = 1.2,
        body_font_size: int = 14
    ):
        super().__init__(parent)
        self.title("Smart Volume Analyzer & TOC Optimizer")
        self.geometry("800x660")
        self.minsize(740, 600)
        self.transient(parent)
        self.grab_set()

        self.chapters = chapters
        self.on_select_tier = on_select_tier
        self.inside_margin_cm = float(inside_margin_cm)
        self.outside_margin_cm = float(outside_margin_cm)
        self.top_margin_cm = float(top_margin_cm)
        self.bottom_margin_cm = float(bottom_margin_cm)
        self.body_font_size = int(body_font_size)

        # Background matches parent theme
        self.configure(fg_color=("#eceff4", "#0b0f19"))

        self._build_ui()

    def _build_ui(self):
        # 1. Header Banner
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 6))

        lbl_title = ctk.CTkLabel(
            header,
            text="Phân tích & Tối ưu Phân tập Sách in (Physical Book Analyzer)",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        lbl_title.pack(anchor="w")

        total_ch = len(self.chapters)
        min_c = self.chapters[0][0] if self.chapters else 0
        max_c = self.chapters[-1][0] if self.chapters else 0

        # Run analysis dynamically adapted to user margins
        analysis = analyze_optimal_volume_splits(
            self.chapters,
            inside_margin_cm=self.inside_margin_cm,
            outside_margin_cm=self.outside_margin_cm,
            top_margin_cm=self.top_margin_cm,
            bottom_margin_cm=self.bottom_margin_cm,
            body_font_size=self.body_font_size
        )

        first_opt = next(iter(analysis.values())) if analysis else None
        l_per_p = first_opt.lines_per_page if first_opt else 32.0
        c_per_l = first_opt.chars_per_line if first_opt else 68
        toc_cap = first_opt.toc_entries_per_page if first_opt else 32

        lbl_desc = ctk.CTkLabel(
            header,
            text=(
                f"Đã đọc thực tế {total_ch} chương (Ch {min_c} đến Ch {max_c}). "
                f"Các mốc phân tập dưới đây được tính toán dựa trên đúng thông số căn lề và cỡ chữ bạn đã nhập, "
                f"tối ưu số chương vừa khít với sức chứa của trang mục lục."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748b", "#94a3b8"),
            wraplength=750,
            justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(2, 6))

        # Dynamic Metrics Banner
        meta_frame = ctk.CTkFrame(header, fg_color=("#e2e8f0", "#1e293b"), corner_radius=6)
        meta_frame.pack(fill="x", pady=(2, 6))

        meta_txt = (
            f"[Căn lề áp dụng]: Gáy {self.inside_margin_cm}cm • Mép {self.outside_margin_cm}cm • Trên/Dưới {self.top_margin_cm}/{self.bottom_margin_cm}cm • Font {self.body_font_size}pt\n"
            f"[Sức chứa trang in]: ~{l_per_p} dòng/trang • ~{c_per_l} ký tự/dòng  |  Mục lục: ~{toc_cap} chương/trang (Tự động thích ứng)"
        )
        ctk.CTkLabel(
            meta_frame,
            text=meta_txt,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            justify="left"
        ).pack(anchor="w", padx=12, pady=6)

        # 2. Scrollable Container for the 3 Tiers
        content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        content.pack(fill="both", expand=True, padx=20, pady=(4, 12))

        for tier_key, opt in analysis.items():
            self._render_tier_card(content, opt)

        # 3. Bottom Close Button
        btn_close = ctk.CTkButton(
            self,
            text="Đóng",
            width=100,
            height=34,
            fg_color=("#e2e8f0", "#1e293b"),
            hover_color=("#cbd5e1", "#334155"),
            text_color=("#334155", "#cbd5e1"),
            command=self.destroy
        )
        btn_close.pack(anchor="e", padx=20, pady=(0, 16))

    def _render_tier_card(self, parent, opt: VolumeSplitOption):
        # Card container
        border_col = ("#38bdf8", "#0284c7") if opt.is_recommended else ("#cbd5e1", "#334155")
        border_w = 2 if opt.is_recommended else 1

        card = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=("#f8fafc", "#1e293b"),
            border_width=border_w,
            border_color=border_col
        )
        card.pack(fill="x", pady=6)

        # Top row: Tier title + badge
        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 4))

        lbl_name = ctk.CTkLabel(
            top_row,
            text=opt.tier_name,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        lbl_name.pack(side="left")

        if opt.is_recommended:
            badge = ctk.CTkLabel(
                top_row,
                text="  [TỐI ƯU KHÍT MỤC LỤC & ĐỀU CHƯƠNG]  ",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                fg_color=("#0284c7", "#0369a1"),
                text_color="#ffffff",
                corner_radius=6
            )
            badge.pack(side="left", padx=10)

        # Apply Button
        btn_apply = ctk.CTkButton(
            top_row,
            text="Áp dụng mốc này",
            width=140,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#18181b", "#f8fafc"),
            hover_color=("#27272a", "#e2e8f0"),
            text_color=("#ffffff", "#0f172a"),
            command=lambda o=opt: self._apply_and_close(o)
        )
        btn_apply.pack(side="right")

        # Stats Row
        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=4)

        stat_1 = f"• Tổng: {opt.num_volumes} tập"
        stat_2 = f"• Bình quân: ~{opt.avg_chapters_per_vol} chương/tập"
        stat_3 = f"• Ước tính: ~{opt.avg_pages_per_vol} trang/tập"

        ctk.CTkLabel(
            stats_row,
            text=f"{stat_1}   |   {stat_2}   |   {stat_3}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#334155", "#cbd5e1")
        ).pack(anchor="w")

        # TOC Evaluation Row
        toc_color = ("#15803d", "#4ade80") if ("Khít" in opt.toc_quality_rating or "Vừa vặn" in opt.toc_quality_rating) else ("#b45309", "#fbbf24")
        ctk.CTkLabel(
            card,
            text=f"Mục lục (TOC): {opt.toc_quality_rating}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=toc_color
        ).pack(anchor="w", padx=16, pady=(2, 4))

        # Preview of volume ranges
        preview_parts = []
        for vr in opt.volume_ranges[:6]:
            preview_parts.append(f"Tập {vr[0]}: Ch {vr[1]}-{vr[2]} (~{vr[3]:.0f}p)")
        if len(opt.volume_ranges) > 6:
            preview_parts.append(f"... +{len(opt.volume_ranges) - 6} tập nữa")

        ctk.CTkLabel(
            card,
            text="Chi tiết phân bổ: " + "   •   ".join(preview_parts),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=("#64748b", "#94a3b8")
        ).pack(anchor="w", padx=16, pady=(0, 12))

    def _apply_and_close(self, opt: VolumeSplitOption):
        if self.on_select_tier:
            self.on_select_tier(opt)
        self.destroy()
