"""
Module: ui.smart_analyzer_dialog
Description: Interactive modal dialog displaying exact real line-based volume partitions,
             TOC efficiency ratings, range filtering, and 1-click tier selection.
Author: Google Deepmind Agent
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import List, Tuple, Callable, Optional
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
        body_font_size: int = 14,
        all_chapters: Optional[List[Tuple[int, str, str]]] = None,
        on_range_changed: Optional[Callable[[int, int], None]] = None
    ):
        super().__init__(parent)
        self.title("Smart Volume Analyzer & TOC Optimizer")
        self.geometry("820x680")
        self.minsize(760, 620)
        self.transient(parent)
        self.grab_set()

        self.chapters = list(chapters)
        self.all_chapters = list(all_chapters if all_chapters is not None else chapters)
        self.on_select_tier = on_select_tier
        self.on_range_changed = on_range_changed
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
        header.pack(fill="x", padx=20, pady=(16, 4))

        lbl_title = ctk.CTkLabel(
            header,
            text="Phân tích & Tối ưu Phân tập Sách in (Physical Book Analyzer)",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=("#0f172a", "#f8fafc")
        )
        lbl_title.pack(anchor="w")

        # Range selector row
        range_frame = ctk.CTkFrame(header, fg_color="transparent")
        range_frame.pack(fill="x", pady=(6, 4))

        ctk.CTkLabel(
            range_frame,
            text="Phạm vi phân tích:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#334155", "#cbd5e1")
        ).pack(side="left", padx=(0, 6))

        cur_min = self.chapters[0][0] if self.chapters else 1
        cur_max = self.chapters[-1][0] if self.chapters else 1

        ctk.CTkLabel(range_frame, text="Từ Ch:", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(0, 4))
        self.entry_start = ctk.CTkEntry(range_frame, width=65, height=26, corner_radius=5)
        self.entry_start.insert(0, str(cur_min))
        self.entry_start.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(range_frame, text="Đến Ch:", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(0, 4))
        self.entry_end = ctk.CTkEntry(range_frame, width=65, height=26, corner_radius=5)
        self.entry_end.insert(0, str(cur_max))
        self.entry_end.pack(side="left", padx=(0, 10))

        btn_filter = ctk.CTkButton(
            range_frame,
            text="Cập nhật phạm vi",
            width=125,
            height=26,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=("#0284c7", "#0369a1"),
            hover_color=("#0369a1", "#075985"),
            text_color="#ffffff",
            command=self._on_update_range
        )
        btn_filter.pack(side="left", padx=(0, 8))

        btn_all = ctk.CTkButton(
            range_frame,
            text="Tất cả (1-End)",
            width=105,
            height=26,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=("#ffffff", "#1e293b"),
            hover_color=("#f1f5f9", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            border_width=1,
            border_color=("#cbd5e1", "#475569"),
            command=self._on_reset_all_range
        )
        btn_all.pack(side="left")

        # Range description label
        self.lbl_desc = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=("#64748b", "#94a3b8"),
            wraplength=770,
            justify="left"
        )
        self.lbl_desc.pack(anchor="w", pady=(2, 4))

        # Dynamic Metrics Banner
        meta_frame = ctk.CTkFrame(header, fg_color=("#e2e8f0", "#1e293b"), corner_radius=6)
        meta_frame.pack(fill="x", pady=(2, 4))

        printable_h = max(15.0, 29.7 - (self.top_margin_cm + self.bottom_margin_cm))
        printable_w = max(10.0, 21.0 - (self.inside_margin_cm + self.outside_margin_cm))
        from core.page_metrics import calculate_lines_per_page, calculate_chars_per_line, calculate_toc_entries_per_page
        l_per_p = calculate_lines_per_page(printable_h, self.body_font_size)
        c_per_l = calculate_chars_per_line(printable_w, self.body_font_size)
        toc_cap = calculate_toc_entries_per_page(printable_h)

        meta_txt = (
            f"[Căn lề áp dụng]: Gáy {self.inside_margin_cm}cm • Mép {self.outside_margin_cm}cm • Trên/Dưới {self.top_margin_cm}/{self.bottom_margin_cm}cm • Font {self.body_font_size}pt\n"
            f"[Sức chứa trang in]: ~{l_per_p} dòng/trang • ~{c_per_l} ký tự/dòng  |  Mục lục: ~{toc_cap} chương/trang"
        )
        ctk.CTkLabel(
            meta_frame,
            text=meta_txt,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=("#0f172a", "#f8fafc"),
            justify="left"
        ).pack(anchor="w", padx=12, pady=5)

        # 2. Scrollable Container for Tier Cards
        self.content = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0
        )
        self.content.pack(fill="both", expand=True, padx=20, pady=(4, 10))

        # 3. Bottom Close Button
        btn_close = ctk.CTkButton(
            self,
            text="Đóng",
            width=100,
            height=32,
            fg_color=("#e2e8f0", "#1e293b"),
            hover_color=("#cbd5e1", "#334155"),
            text_color=("#334155", "#cbd5e1"),
            command=self.destroy
        )
        btn_close.pack(anchor="e", padx=20, pady=(0, 14))

        self._refresh_analysis()

    def _refresh_analysis(self):
        # Clear existing cards
        for widget in self.content.winfo_children():
            widget.destroy()

        if not self.chapters:
            self.lbl_desc.configure(text="Không có chương nào trong phạm vi được chọn.")
            return

        total_ch = len(self.chapters)
        min_c = self.chapters[0][0]
        max_c = self.chapters[-1][0]

        self.lbl_desc.configure(
            text=(
                f"Đang phân tích {total_ch} chương (Chương {min_c} đến {max_c}). "
                f"Các mốc phân tập được tính toán riêng biệt cho phạm vi này, "
                f"đảm bảo các tập sách chia đều chương và tối ưu mục lục hoàn hảo."
            )
        )

        analysis = analyze_optimal_volume_splits(
            self.chapters,
            inside_margin_cm=self.inside_margin_cm,
            outside_margin_cm=self.outside_margin_cm,
            top_margin_cm=self.top_margin_cm,
            bottom_margin_cm=self.bottom_margin_cm,
            body_font_size=self.body_font_size
        )

        for tier_key, opt in analysis.items():
            self._render_tier_card(self.content, opt)

    def _on_update_range(self):
        s_raw = self.entry_start.get().strip()
        e_raw = self.entry_end.get().strip()
        s_val = int(s_raw) if s_raw.isdigit() else None
        e_val = int(e_raw) if e_raw.isdigit() else None

        if s_val is not None and e_val is not None and e_val < s_val:
            messagebox.showerror("Lỗi phạm vi", f"Chương kết thúc ({e_val}) không thể nhỏ hơn chương bắt đầu ({s_val})!")
            return

        filtered = [
            ch for ch in self.all_chapters
            if (s_val is None or ch[0] >= s_val) and (e_val is None or ch[0] <= e_val)
        ]

        if not filtered:
            messagebox.showwarning("Thông báo", f"Không tìm thấy chương nào trong khoảng Ch {s_val} đến Ch {e_val}.")
            return

        self.chapters = filtered
        self._refresh_analysis()

    def _on_reset_all_range(self):
        if not self.all_chapters:
            return
        self.chapters = list(self.all_chapters)
        first_c = self.chapters[0][0]
        last_c = self.chapters[-1][0]
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, str(first_c))
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, str(last_c))
        self._refresh_analysis()

    def _render_tier_card(self, parent, opt: VolumeSplitOption):
        badge_str = getattr(opt, "badge_text", "")
        if opt.is_recommended:
            if "2 TRANG" in badge_str:
                border_col = ("#34d399", "#059669")
            else:
                border_col = ("#38bdf8", "#0284c7")
            border_w = 2
        else:
            border_col = ("#cbd5e1", "#334155")
            border_w = 1

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

        if badge_str:
            badge_color = ("#0284c7", "#0369a1") if "1 TRANG" in badge_str else ("#059669", "#047857")
            badge = ctk.CTkLabel(
                top_row,
                text=f"  {badge_str}  ",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                fg_color=badge_color,
                text_color="#ffffff",
                corner_radius=6
            )
            badge.pack(side="left", padx=10)
        elif opt.is_recommended:
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
        if self.on_range_changed and self.chapters:
            self.on_range_changed(self.chapters[0][0], self.chapters[-1][0])
        if self.on_select_tier:
            self.on_select_tier(opt)
        self.destroy()
