"""
Module: ui.tab_scraper
Description: Builds the Web Scraper tab (Target novel, Cloudflare cookie evasion,
             speed/retry options, detected novel dropdown, action buttons).
Author: Google Deepmind Agent
"""

import customtkinter as ctk


def build_scraper_tab(parent, app):
    """
    Constructs the responsive grid layout for Tab 1 (Web Scraper).
    Attaches all entry widgets and action buttons to `app`.
    """
    content_frame = ctk.CTkFrame(parent, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=6, pady=4)

    # Responsive grid distribution
    content_frame.columnconfigure(0, weight=1)
    content_frame.rowconfigure(0, weight=4)  # Card 1 (Target Novel & URL)
    content_frame.rowconfigure(1, weight=4)  # Card 2 (Cloudflare & Network)
    content_frame.rowconfigure(2, weight=3)  # Card 3 (Storage & Profiles)
    content_frame.rowconfigure(3, weight=0)  # Action Bar (Fixed at bottom)

    # -------------------------------------------------------------------------
    # Card 1: Target Novel and URL Settings
    # -------------------------------------------------------------------------
    card_novel = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_novel.grid(row=0, column=0, sticky="nsew", pady=(0, 8), padx=2)

    ctk.CTkLabel(
        card_novel,
        text="1. Target Novel and URL Settings",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(6, 2))

    # Row 1: Novel Folder Name & Content Tag
    r1 = ctk.CTkFrame(card_novel, fg_color="transparent")
    r1.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r1, text="Novel Folder Name:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_novel_name = ctk.CTkEntry(
        r1, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30
    )
    app.entry_novel_name.pack(side="left", fill="x", expand=True, padx=(0, 15))
    app.entry_novel_name.bind("<KeyRelease>", app._on_novel_name_changed)

    ctk.CTkLabel(r1, text="Content Tag / Selector:", width=145, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_selector = ctk.CTkEntry(
        r1, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30, width=130
    )
    app.entry_selector.pack(side="left")
    app.entry_selector.insert(0, "article")

    # Row 2: Chapter 1 URL & Derive Pattern
    r2 = ctk.CTkFrame(card_novel, fg_color="transparent")
    r2.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r2, text="Chapter 1 URL:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_ch1_url = ctk.CTkEntry(
        r2, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30
    )
    app.entry_ch1_url.pack(side="left", fill="x", expand=True, padx=(0, 10))
    app.entry_ch1_url.bind("<KeyRelease>", app._on_ch1_url_changed)

    btn_derive = ctk.CTkButton(
        r2, text="Derive Pattern", corner_radius=6, height=30,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._auto_detect_pattern
    )
    btn_derive.pack(side="left")

    # Row 3: URL Template
    r3 = ctk.CTkFrame(card_novel, fg_color="transparent")
    r3.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r3, text="URL Template (with {}):", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_url_pattern = ctk.CTkEntry(
        r3, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30
    )
    app.entry_url_pattern.pack(side="left", fill="x", expand=True)

    # Row 4: Start Chapter, End Chapter, Batch Size & Folder Chapter Detection
    r4 = ctk.CTkFrame(card_novel, fg_color="transparent")
    r4.pack(fill="x", expand=True, padx=12, pady=(2, 6))

    ctk.CTkLabel(r4, text="Start Chapter:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_start_ch = ctk.CTkEntry(
        r4, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=75, height=30
    )
    app.entry_start_ch.pack(side="left", padx=(0, 14))

    ctk.CTkLabel(r4, text="End Chapter:", width=85, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_end_ch = ctk.CTkEntry(
        r4, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=75, height=30
    )
    app.entry_end_ch.pack(side="left", padx=(0, 14))

    ctk.CTkLabel(r4, text="Batch Size:", width=75, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_batch_size = ctk.CTkEntry(
        r4, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=60, height=30
    )
    app.entry_batch_size.pack(side="left", padx=(0, 14))

    btn_detect_existing = ctk.CTkButton(
        r4, text="Detect in Folder", corner_radius=6, height=30, width=125,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._detect_existing_for_scraper
    )
    btn_detect_existing.pack(side="left")

    # -------------------------------------------------------------------------
    # Card 2: Cloudflare Evasion and Network Settings
    # -------------------------------------------------------------------------
    card_net = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_net.grid(row=1, column=0, sticky="nsew", pady=(0, 8), padx=2)

    ctk.CTkLabel(
        card_net,
        text="2. Cloudflare Evasion and Network Settings",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(6, 2))

    # Cookie Textbox
    r_cookie = ctk.CTkFrame(card_net, fg_color="transparent")
    r_cookie.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r_cookie, text="Browser Cookie String:", width=140, anchor="nw", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.txt_cookie = ctk.CTkTextbox(
        r_cookie, corner_radius=6, border_width=1, border_color=("#cbd5e1", "#334155"),
        height=50, font=("Consolas", 10), fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc")
    )
    app.txt_cookie.pack(side="left", fill="x", expand=True)

    # User Agent
    r_ua = ctk.CTkFrame(card_net, fg_color="transparent")
    r_ua.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r_ua, text="User-Agent:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_ua = ctk.CTkEntry(
        r_ua, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30
    )
    app.entry_ua.pack(side="left", fill="x", expand=True)

    # Delays, Timeout & Auto-retry
    r_speed = ctk.CTkFrame(card_net, fg_color="transparent")
    r_speed.pack(fill="x", expand=True, padx=12, pady=(2, 6))
    ctk.CTkLabel(r_speed, text="Safe Delay (seconds):", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_delay_min = ctk.CTkEntry(
        r_speed, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=55, height=30
    )
    app.entry_delay_min.pack(side="left")
    ctk.CTkLabel(r_speed, text=" to ", text_color=("#64748b", "#94a3b8")).pack(side="left", padx=4)
    app.entry_delay_max = ctk.CTkEntry(
        r_speed, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=55, height=30
    )
    app.entry_delay_max.pack(side="left", padx=(0, 18))

    ctk.CTkLabel(r_speed, text="Timeout (s):", width=75, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_timeout = ctk.CTkEntry(
        r_speed, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), width=55, height=30
    )
    app.entry_timeout.pack(side="left", padx=(0, 18))

    app.var_retry_until_success = ctk.BooleanVar(value=True)
    chk_retry = ctk.CTkCheckBox(
        r_speed, text="Auto-Retry Chapter on Timeout (Never Skip)",
        variable=app.var_retry_until_success, corner_radius=4,
        text_color=("#0f172a", "#f8fafc"), fg_color=("#18181b", "#f8fafc"),
        checkmark_color=("#ffffff", "#0f172a"), hover_color=("#27272a", "#e2e8f0")
    )
    chk_retry.pack(side="left")

    # -------------------------------------------------------------------------
    # Card 3: Storage Location and Detected Novel Folders
    # -------------------------------------------------------------------------
    card_storage = ctk.CTkFrame(
        content_frame,
        corner_radius=8,
        fg_color=("#f8fafc", "#1e293b"),
        border_width=1,
        border_color=("#cbd5e1", "#334155")
    )
    card_storage.grid(row=2, column=0, sticky="nsew", pady=(0, 8), padx=2)

    ctk.CTkLabel(
        card_storage,
        text="3. Storage Location and Detected Novel Folders",
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        text_color=("#0f172a", "#f8fafc")
    ).pack(anchor="w", padx=12, pady=(6, 2))

    # Row 1: Detected Novel Folder Selector
    r_detect = ctk.CTkFrame(card_storage, fg_color="transparent")
    r_detect.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r_detect, text="Detected Novel Folder:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.combo_detected_novels = ctk.CTkComboBox(
        r_detect, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"),
        button_color=("#e2e8f0", "#1e293b"), dropdown_fg_color=("#ffffff", "#1e293b"),
        dropdown_text_color=("#0f172a", "#f8fafc"), height=30,
        command=app._on_novel_dropdown_selected
    )
    app.combo_detected_novels.pack(side="left", fill="x", expand=True, padx=(0, 10))

    btn_refresh_novels = ctk.CTkButton(
        r_detect, text="Refresh", corner_radius=6, height=30, width=80,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._refresh_detected_novels
    )
    btn_refresh_novels.pack(side="left")

    # Row 2: Save Location
    r_path = ctk.CTkFrame(card_storage, fg_color="transparent")
    r_path.pack(fill="x", expand=True, padx=12, pady=2)
    ctk.CTkLabel(r_path, text="Save Location:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")
    app.entry_output_dir = ctk.CTkEntry(
        r_path, corner_radius=6, border_color=("#cbd5e1", "#334155"),
        fg_color=("#ffffff", "#0f172a"), text_color=("#0f172a", "#f8fafc"), height=30
    )
    app.entry_output_dir.pack(side="left", fill="x", expand=True, padx=(0, 10))
    btn_browse = ctk.CTkButton(
        r_path, text="Browse...", corner_radius=6, height=30, width=80,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._browse_directory
    )
    btn_browse.pack(side="left")

    # Row 3: Profile Management
    r_prof = ctk.CTkFrame(card_storage, fg_color="transparent")
    r_prof.pack(fill="x", expand=True, padx=12, pady=(2, 6))
    ctk.CTkLabel(r_prof, text="Profile Management:", width=140, anchor="w", text_color=("#334155", "#cbd5e1")).pack(side="left")

    btn_sp = ctk.CTkButton(
        r_prof, text="Save Profile", corner_radius=6, height=30,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._save_profile_file
    )
    btn_sp.pack(side="left", padx=(0, 8))

    btn_lp = ctk.CTkButton(
        r_prof, text="Load Profile", corner_radius=6, height=30,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._load_profile_file
    )
    btn_lp.pack(side="left", padx=(0, 8))

    btn_rd = ctk.CTkButton(
        r_prof, text="Reset Defaults", corner_radius=6, height=30,
        fg_color=("#ffffff", "#1e293b"), text_color=("#0f172a", "#f8fafc"),
        hover_color=("#f1f5f9", "#334155"), border_width=1, border_color=("#cbd5e1", "#475569"),
        command=app._load_default_config
    )
    btn_rd.pack(side="left")

    # -------------------------------------------------------------------------
    # Action Bar: Scraper Actions (Fixed at Bottom of Tab)
    # -------------------------------------------------------------------------
    frame_action = ctk.CTkFrame(content_frame, fg_color="transparent")
    frame_action.grid(row=3, column=0, sticky="ew", pady=(4, 6), padx=2)

    app.btn_start = ctk.CTkButton(
        frame_action,
        text="START SCRAPING NOVEL",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color=("#18181b", "#f8fafc"),
        hover_color=("#27272a", "#e2e8f0"),
        text_color=("#ffffff", "#0f172a"),
        corner_radius=8,
        height=40,
        command=app._start_scraping
    )
    app.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 8))

    app.btn_stop = ctk.CTkButton(
        frame_action,
        text="STOP",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        fg_color=("#e2e8f0", "#1e293b"),
        text_color_disabled=("#94a3b8", "#64748b"),
        corner_radius=8,
        height=40,
        state="disabled",
        command=app._stop_scraping
    )
    app.btn_stop.pack(side="left", padx=(0, 8))

    app.btn_open_folder = ctk.CTkButton(
        frame_action,
        text="Open Folder",
        font=ctk.CTkFont(family="Segoe UI", size=12),
        fg_color=("#ffffff", "#1e293b"),
        hover_color=("#f1f5f9", "#334155"),
        text_color=("#0f172a", "#f8fafc"),
        border_width=1,
        border_color=("#cbd5e1", "#475569"),
        corner_radius=8,
        height=40,
        command=app._open_output_folder
    )
    app.btn_open_folder.pack(side="left")
