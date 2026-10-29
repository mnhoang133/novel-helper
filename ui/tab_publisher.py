"""
Module: ui.tab_publisher
Description: Builds the Book Publisher tab (Source chapters, Metadata, Typography,
             Customizable Print Margins & Mirror Margins, Volume Splitting & Optimizer).
Author: Google Deepmind Agent
"""

import customtkinter as ctk
from ui.theme import setup_segmented_button_style
from ui.smart_analyzer_dialog import SmartVolumeAnalyzerDialog
from core.book_engine import VolumeSplitOption


def build_publisher_tab(parent, app):
    """
    Constructs the responsive layout for Tab 2 (Book Publisher).
    Attaches all entry widgets and action buttons to `app`.
    """
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=6, pady=4)

    # Responsive grid distribution
    content_frame.columnconfigure(0, weight=1)
    content_frame.rowconfigure(0, weight=3)  # Card 1: Source & Range
    content_frame.rowconfigure(1, weight=2)  # Card 2: Cover & Metadata
    content_frame.rowconfigure(2, weight=2)  # Card 3: Typography & Smart Pagination
    content_frame.rowconfigure(3, weight=3)  # Card 4: Margins & Book Binding
    content_frame.rowconfigure(4, weight=3)  # Card 5: Splitting, Optimizer & Formats
    content_frame.rowconfigure(5, weight=0)  # Action Bar (Fixed at bottom)

    # -------------------------------------------------------------------------
    # Card 1: Source Chapter Batch Files (.txt) & Range Selection
    # -------------------------------------------------------------------------
    card_src = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_src.grid(row=0, column=0, sticky="nsew", pady=(0, 6), padx=2)

    ctk.CTkLabel(
        card_src,
        text="1. Source Chapter Batch Files (.txt) & Publish Range",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(4, 1))

    # Row 1: Select Novel & Scan
    r_sel = ctk.CTkFrame(card_src, fg_color="transparent")
    r_sel.pack(fill="x", expand=True, padx=12, pady=1)
    ctk.CTkLabel(r_sel, text="Select Novel:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_pub_novels = ctk.CTkComboBox(
        r_sel, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"),
        button_color=("#e2e8f0", "#1e293b"), dropdown_fg_color=("#ffffff", "#1e293b"),
        dropdown_text_color=("#0f172a", "#f8fafc"), height=28,
        command=app._on_pub_novel_selected
    )
    app.combo_pub_novels.pack(side="left", fill="x", expand=True, padx=(0, 10))

    btn_wscan = ctk.CTkButton(
        r_sel, text="Scan Chapters", corner_radius=6, height=28, width=105,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._scan_chapters_for_pub
    )
    btn_wscan.pack(side="left")

    # Row 2: Chapters Folder Path
    r_dir = ctk.CTkFrame(card_src, fg_color="transparent")
    r_dir.pack(fill="x", expand=True, padx=12, pady=1)
    ctk.CTkLabel(r_dir, text="Chapters Folder:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_pub_src_dir = ctk.CTkEntry(
        r_dir, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=28
    )
    app.entry_pub_src_dir.pack(side="left", fill="x", expand=True, padx=(0, 10))
    btn_wbrowse = ctk.CTkButton(
        r_dir, text="Browse...", corner_radius=6, height=28, width=105,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._browse_pub_src_dir
    )
    btn_wbrowse.pack(side="left")

    # Row 3: Publish Chapter Range (Start & End)
    r_range = ctk.CTkFrame(card_src, fg_color="transparent")
    r_range.pack(fill="x", expand=True, padx=12, pady=1)
    ctk.CTkLabel(r_range, text="Publish Range:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    ctk.CTkLabel(r_range, text="Start Ch:", text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(0, 4))
    app.entry_pub_start_ch = ctk.CTkEntry(
        r_range, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=60, height=28
    )
    app.entry_pub_start_ch.pack(side="left", padx=(0, 12))

    ctk.CTkLabel(r_range, text="End Ch:", text_color=("#64748b", "#94a3b8")).pack(side="left", padx=(0, 4))
    app.entry_pub_end_ch = ctk.CTkEntry(
        r_range, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=60, height=28
    )
    app.entry_pub_end_ch.pack(side="left", padx=(0, 12))

    btn_auto_range = ctk.CTkButton(
        r_range, text="Auto Detect", corner_radius=6, height=28, width=100,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._auto_detect_pub_range
    )
    btn_auto_range.pack(side="left", padx=(0, 8))

    btn_all_range = ctk.CTkButton(
        r_range, text="All Chapters", corner_radius=6, height=28, width=95,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._set_pub_range_all
    )
    btn_all_range.pack(side="left")

    # Row 4: Scan result label
    app.lbl_scan_result = ctk.CTkLabel(
        card_src, text="Click 'Scan Chapters' to inspect available scraped chapters.",
        font=ctk.CTkFont(family="Segoe UI", size=11), text_color=("#64748b", "#94a3b8")
    )
    app.lbl_scan_result.pack(anchor="w", padx=12, pady=(1, 4))

    # -------------------------------------------------------------------------
    # Card 2: Book Cover & Metadata
    # -------------------------------------------------------------------------
    card_cover = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_cover.grid(row=1, column=0, sticky="nsew", pady=(0, 6), padx=2)

    ctk.CTkLabel(
        card_cover,
        text="2. Book Cover and Metadata Customization",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(4, 1))

    rc1 = ctk.CTkFrame(card_cover, fg_color="transparent")
    rc1.pack(fill="x", expand=True, padx=12, pady=1)
    ctk.CTkLabel(rc1, text="Book Title:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_book_title = ctk.CTkEntry(
        rc1, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=28
    )
    app.entry_book_title.pack(side="left", fill="x", expand=True, padx=(0, 15))
    app.entry_book_title.insert(0, "Invincible Mumu")

    ctk.CTkLabel(rc1, text="Author Name:", width=90, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_book_author = ctk.CTkEntry(
        rc1, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=160, height=28
    )
    app.entry_book_author.pack(side="left")
    app.entry_book_author.insert(0, "Web Novel Author")

    rc2 = ctk.CTkFrame(card_cover, fg_color="transparent")
    rc2.pack(fill="x", expand=True, padx=12, pady=(1, 4))
    ctk.CTkLabel(rc2, text="Subtitle / Series:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_book_subtitle = ctk.CTkEntry(
        rc2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=28
    )
    app.entry_book_subtitle.pack(side="left", fill="x", expand=True, padx=(0, 15))
    app.entry_book_subtitle.insert(0, "Official English Translation")

    ctk.CTkLabel(rc2, text="Imprint / Year:", width=90, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_book_imprint = ctk.CTkEntry(
        rc2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=160, height=28
    )
    app.entry_book_imprint.pack(side="left")
    app.entry_book_imprint.insert(0, "Print Edition • 2026")

    # -------------------------------------------------------------------------
    # Card 3: Typography and Smart Pagination
    # -------------------------------------------------------------------------
    card_typo = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_typo.grid(row=2, column=0, sticky="nsew", pady=(0, 6), padx=2)

    ctk.CTkLabel(
        card_typo,
        text="3. Typography and Smart Pagination (No Orphan Headings)",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(4, 1))

    rt1 = ctk.CTkFrame(card_typo, fg_color="transparent")
    rt1.pack(fill="x", expand=True, padx=12, pady=(1, 4))

    ctk.CTkLabel(rt1, text="Reading Font:", width=85, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_font = ctk.CTkComboBox(
        rt1, values=["Georgia", "Palatino Linotype", "Times New Roman", "Garamond"],
        corner_radius=6, border_color=("#cbd5e1", "#334155"), fg_color=("#ffffff", "#0f172a"),
        text_color=("#0f172a", "#f8fafc"), button_color=("#e2e8f0", "#1e293b"),
        dropdown_fg_color=("#ffffff", "#1e293b"), dropdown_text_color=("#0f172a", "#f8fafc"),
        width=130, height=28
    )
    app.combo_font.set("Georgia")
    app.combo_font.pack(side="left", padx=(0, 12))

    ctk.CTkLabel(rt1, text="Body Size:", width=65, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_body_size = ctk.CTkEntry(
        rt1, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=40, height=28
    )
    app.entry_body_size.insert(0, "14")
    app.entry_body_size.pack(side="left", padx=(0, 12))

    ctk.CTkLabel(rt1, text="Chapter Header:", width=95, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_ch_size = ctk.CTkComboBox(
        rt1, values=["24", "26", "28", "30", "32"], corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"),
        button_color=("#e2e8f0", "#1e293b"), dropdown_fg_color=("#ffffff", "#1e293b"),
        dropdown_text_color=("#0f172a", "#f8fafc"), width=55, height=28
    )
    app.combo_ch_size.set("28")
    app.combo_ch_size.pack(side="left", padx=(0, 12))

    ctk.CTkLabel(rt1, text="Align:", width=40, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_align = ctk.CTkComboBox(
        rt1, values=["Justify", "Left"], corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"),
        button_color=("#e2e8f0", "#1e293b"), dropdown_fg_color=("#ffffff", "#1e293b"),
        dropdown_text_color=("#0f172a", "#f8fafc"), width=75, height=28
    )
    app.combo_align.set("Justify")
    app.combo_align.pack(side="left", padx=(0, 12))

    app.var_smart_page = ctk.BooleanVar(value=True)
    app.chk_smart = ctk.CTkCheckBox(
        rt1, text="Smart Pagination (Cho phép viết nếu đủ tiêu đề + 3 dòng)",
        variable=app.var_smart_page, corner_radius=4,
        text_color=("#0f172a", "#f8fafc"), fg_color=("#18181b", "#f8fafc"),
        checkmark_color=("#ffffff", "#0f172a"), hover_color=("#27272a", "#e2e8f0")
    )
    app.chk_smart.pack(side="left")

    # -------------------------------------------------------------------------
    # Card 4: Page Margins & Book Binding (Mirror Margins)
    # -------------------------------------------------------------------------
    card_margins = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_margins.grid(row=3, column=0, sticky="nsew", pady=(0, 6), padx=2)

    ctk.CTkLabel(
        card_margins,
        text="4. Page Margins & Book Binding (Căn lề đóng gáy sách)",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(4, 1))

    # Row 1: Mirror Margins Checkbox & Explanation
    rm1 = ctk.CTkFrame(card_margins, fg_color="transparent")
    rm1.pack(fill="x", expand=True, padx=12, pady=1)

    app.var_mirror_margins = ctk.BooleanVar(value=True)
    app.chk_mirror = ctk.CTkCheckBox(
        rm1,
        text="Lề đối xứng in sách 2 mặt (Mirror Margins: Tự đổi Gáy sách trái ở trang lẻ, phải ở trang chẵn)",
        variable=app.var_mirror_margins, corner_radius=4,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        text_color=("#0f172a", "#f8fafc"), fg_color=("#18181b", "#f8fafc"),
        checkmark_color=("#ffffff", "#0f172a"), hover_color=("#27272a", "#e2e8f0"),
        command=app._on_margin_changed
    )
    app.chk_mirror.pack(side="left")

    # Row 2: Inside, Outside, Top, Bottom, Footer, Header
    rm2 = ctk.CTkFrame(card_margins, fg_color="transparent")
    rm2.pack(fill="x", expand=True, padx=12, pady=(1, 2))

    # Inside (Gáy dán)
    ctk.CTkLabel(rm2, text="Gáy dán (Inside):", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_margin_inside = ctk.CTkEntry(
        rm2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=45, height=28
    )
    app.entry_margin_inside.insert(0, "2.0")
    app.entry_margin_inside.pack(side="left", padx=(4, 10))
    app.entry_margin_inside.bind("<KeyRelease>", lambda e: app._on_margin_changed())

    # Outside (Mép ngoài)
    ctk.CTkLabel(rm2, text="Mép ngoài (Out):", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_margin_outside = ctk.CTkEntry(
        rm2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=45, height=28
    )
    app.entry_margin_outside.insert(0, "1.2")
    app.entry_margin_outside.pack(side="left", padx=(4, 10))
    app.entry_margin_outside.bind("<KeyRelease>", lambda e: app._on_margin_changed())

    # Top
    ctk.CTkLabel(rm2, text="Trên (Top):", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_margin_top = ctk.CTkEntry(
        rm2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=45, height=28
    )
    app.entry_margin_top.insert(0, "1.2")
    app.entry_margin_top.pack(side="left", padx=(4, 10))
    app.entry_margin_top.bind("<KeyRelease>", lambda e: app._on_margin_changed())

    # Bottom
    ctk.CTkLabel(rm2, text="Dưới (Bot):", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_margin_bottom = ctk.CTkEntry(
        rm2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=45, height=28
    )
    app.entry_margin_bottom.insert(0, "1.2")
    app.entry_margin_bottom.pack(side="left", padx=(4, 10))
    app.entry_margin_bottom.bind("<KeyRelease>", lambda e: app._on_margin_changed())

    # Footer
    ctk.CTkLabel(rm2, text="Footer:", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_footer_dist = ctk.CTkEntry(
        rm2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=45, height=28
    )
    app.entry_footer_dist.insert(0, "0.7")
    app.entry_footer_dist.pack(side="left", padx=(4, 10))

    btn_reset_margins = ctk.CTkButton(
        rm2, text="Reset lề chuẩn", corner_radius=6, height=28, width=100,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._reset_default_margins
    )
    btn_reset_margins.pack(side="left")

    # Row 3: Dynamic Live Margin Explanation / Preview
    app.lbl_margin_preview = ctk.CTkLabel(
        card_margins,
        text="[Lề đối xứng in 2 mặt] Trang lẻ: Trái (Gáy) 2.0cm, Phải (Mép) 1.2cm  |  Trang chẵn: Trái (Mép) 1.2cm, Phải (Gáy) 2.0cm",
        font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
        text_color=("#0284c7", "#38bdf8")
    )
    app.lbl_margin_preview.pack(anchor="w", padx=14, pady=(1, 5))

    # -------------------------------------------------------------------------
    # Card 5: Volume Splitting, Formats & Smart Volume Analyzer
    # -------------------------------------------------------------------------
    card_vol = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_vol.grid(row=4, column=0, sticky="nsew", pady=(0, 6), padx=2)

    ctk.CTkLabel(
        card_vol,
        text="5. Volume Splitting, Formats & Smart Volume Analyzer",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(4, 1))

    # Row 1: Splitting Mode & Smart Analyzer Button
    rv1 = ctk.CTkFrame(card_vol, fg_color="transparent")
    rv1.pack(fill="x", expand=True, padx=12, pady=1)

    ctk.CTkLabel(rv1, text="Splitting Mode:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.var_split_mode = ctk.StringVar(value="split")
    app.seg_split = ctk.CTkSegmentedButton(
        rv1,
        values=["Smart Balanced Volumes", "Single Complete Book"],
        variable=app.var_split_mode,
        corner_radius=6,
        height=28,
        selected_color=("#18181b", "#f8fafc"),
        selected_hover_color=("#27272a", "#e2e8f0"),
        unselected_color=("#e2e8f0", "#1e293b"),
        unselected_hover_color=("#cbd5e1", "#334155")
    )
    app.seg_split.set("Smart Balanced Volumes")
    app.seg_split.pack(side="left", fill="x", expand=True, padx=(0, 10))
    setup_segmented_button_style(app.seg_split)

    # Smart Analyzer Button
    btn_smart_analyzer = ctk.CTkButton(
        rv1,
        text="Phân tích & Tối ưu số trang",
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
        corner_radius=6,
        height=28,
        width=185,
        fg_color=("#0284c7", "#0369a1"),
        hover_color=("#0369a1", "#0284c7"),
        text_color="#ffffff",
        command=app._open_smart_analyzer_modal
    )
    btn_smart_analyzer.pack(side="right")

    # Row 2: Target Pages, Export Formats & TOC hint
    rv2 = ctk.CTkFrame(card_vol, fg_color="transparent")
    rv2.pack(fill="x", expand=True, padx=12, pady=(1, 4))
    ctk.CTkLabel(rv2, text="Target Pages/Vol:", width=130, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_target_pages = ctk.CTkEntry(
        rv2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=60, height=28
    )
    app.entry_target_pages.insert(0, "310")
    app.entry_target_pages.pack(side="left", padx=(0, 16))

    ctk.CTkLabel(rv2, text="Formats:", width=65, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_format = ctk.CTkComboBox(
        rv2, values=["Both DOCX and PDF", "DOCX Only", "PDF Only"], corner_radius=6,
        border_color=("#cbd5e1", "#334155"), fg_color=("#ffffff", "#0f172a"),
        text_color=("#0f172a", "#f8fafc"), button_color=("#e2e8f0", "#1e293b"),
        dropdown_fg_color=("#ffffff", "#1e293b"), dropdown_text_color=("#0f172a", "#f8fafc"),
        width=140, height=28
    )
    app.combo_format.set("Both DOCX and PDF")
    app.combo_format.pack(side="left", padx=(0, 12))

    app.lbl_toc_hint = ctk.CTkLabel(
        rv2,
        text="TOC Fit: 1 trang mục lục khít nhất khi mỗi tập có ≤ 32 chương; 2 trang khi ≤ 64 chương.",
        font=ctk.CTkFont(family="Segoe UI", size=10),
        text_color=("#64748b", "#94a3b8")
    )
    app.lbl_toc_hint.pack(side="left")

    # -------------------------------------------------------------------------
    # Action Bar: Publisher Action Buttons (Fixed at Bottom)
    # -------------------------------------------------------------------------
    frame_pact = ctk.CTkFrame(content_frame, fg_color="transparent")
    frame_pact.grid(row=5, column=0, sticky="ew", pady=(4, 6), padx=2)

    app.btn_publish = ctk.CTkButton(
        frame_pact,
        text="GENERATE PRINT-READY BOOK (DOCX / PDF)",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color=("#18181b", "#f8fafc"),
        hover_color=("#27272a", "#e2e8f0"),
        text_color=("#ffffff", "#0f172a"),
        corner_radius=8,
        height=40,
        command=app._start_publish_book
    )
    app.btn_publish.pack(side="left", fill="x", expand=True, padx=(0, 8))

    app.btn_clean_txt = ctk.CTkButton(
        frame_pact,
        text="Clean Raw Quotes",
        corner_radius=8,
        height=40,
        fg_color=("#ffffff", "#1e293b"),
        text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"),
        border_width=1,
        border_color=("#cbd5e1", "#475569"),
        command=app._repair_txt_files_in_folder
    )
    app.btn_clean_txt.pack(side="left", padx=(0, 8))

    app.btn_open_pdf = ctk.CTkButton(
        frame_pact,
        text="Open PDF Folder",
        corner_radius=8,
        height=40,
        fg_color=("#ffffff", "#1e293b"),
        text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"),
        border_width=1,
        border_color=("#cbd5e1", "#475569"),
        command=app._open_pdf_folder
    )
    app.btn_open_pdf.pack(side="left", padx=(0, 8))

    app.btn_open_doc = ctk.CTkButton(
        frame_pact,
        text="Open DOC Folder",
        corner_radius=8,
        height=40,
        fg_color=("#ffffff", "#1e293b"),
        text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"),
        border_width=1,
        border_color=("#cbd5e1", "#475569"),
        command=app._open_doc_folder
    )
    app.btn_open_doc.pack(side="left")
