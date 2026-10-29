"""
Module: ui.theme
Description: Dynamic theme management, color palettes, and contrast styling
             for CustomTkinter widgets across Light and Dark appearance modes.
Author: Google Deepmind Agent
"""

import customtkinter as ctk

# Color definitions
COLORS = {
    "light": {
        "window_bg": "#eceff4",
        "tabview_bg": "#f4f6f9",
        "card_bg": "#f8fafc",
        "card_border": "#cbd5e1",
        "text_primary": "#0f172a",
        "text_secondary": "#475569",
        "text_muted": "#64748b",
        "input_bg": "#ffffff",
        "input_border": "#cbd5e1",
        "input_text": "#0f172a",
        "btn_primary_bg": "#18181b",
        "btn_primary_text": "#ffffff",
        "btn_primary_hover": "#27272a",
        "btn_secondary_bg": "#ffffff",
        "btn_secondary_text": "#0f172a",
        "btn_secondary_border": "#cbd5e1",
        "btn_secondary_hover": "#f1f5f9",
        "btn_disabled_bg": "#e2e8f0",
        "btn_disabled_text": "#94a3b8",
        "btn_danger_bg": "#be123c",
        "btn_danger_hover": "#9f1239",
        "console_bg": "#eef2f6",
        "console_text": "#334155",
        "console_border": "#cbd5e1",
        "tag_time": "#64748b",
        "tag_info": "#0284c7",
        "tag_success": "#15803d",
        "tag_warning": "#b45309",
        "tag_error": "#b91c1c",
    },
    "dark": {
        "window_bg": "#0b0f19",
        "tabview_bg": "#111827",
        "card_bg": "#1e293b",
        "card_border": "#334155",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "text_muted": "#94a3b8",
        "input_bg": "#0f172a",
        "input_border": "#334155",
        "input_text": "#f8fafc",
        "btn_primary_bg": "#f8fafc",
        "btn_primary_text": "#0f172a",
        "btn_primary_hover": "#e2e8f0",
        "btn_secondary_bg": "#1e293b",
        "btn_secondary_text": "#f8fafc",
        "btn_secondary_border": "#475569",
        "btn_secondary_hover": "#334155",
        "btn_disabled_bg": "#1e293b",
        "btn_disabled_text": "#64748b",
        "btn_danger_bg": "#e11d48",
        "btn_danger_hover": "#be123c",
        "console_bg": "#090d16",
        "console_text": "#e2e8f0",
        "console_border": "#334155",
        "tag_time": "#94a3b8",
        "tag_info": "#38bdf8",
        "tag_success": "#4ade80",
        "tag_warning": "#fbbf24",
        "tag_error": "#f87171",
    }
}


def setup_segmented_button_style(sb: ctk.CTkSegmentedButton):
    """
    Ensures selected and unselected buttons within CTkSegmentedButton
    have maximum contrast in both Light and Dark mode.
    """
    def update_styles():
        curr = sb.get()
        mode = ctk.get_appearance_mode()
        for name, btn in sb._buttons_dict.items():
            if name == curr:
                if mode == "Light":
                    btn.configure(fg_color="#18181b", hover_color="#27272a", text_color="#ffffff")
                else:
                    btn.configure(fg_color="#f8fafc", hover_color="#e2e8f0", text_color="#0f172a")
            else:
                if mode == "Light":
                    btn.configure(fg_color="#e2e8f0", hover_color="#cbd5e1", text_color="#334155")
                else:
                    btn.configure(fg_color="#1e293b", hover_color="#334155", text_color="#94a3b8")

    orig_select = sb._select_button_by_value

    def custom_select(val):
        orig_select(val)
        update_styles()

    orig_unselect = getattr(sb, '_unselect_button_by_value', None)
    if orig_unselect:
        def custom_unselect(val):
            orig_unselect(val)
            update_styles()
        sb._unselect_button_by_value = custom_unselect

    sb._select_button_by_value = custom_select
    sb.update_styles = update_styles
    update_styles()


def update_console_colors(txt_log: ctk.CTkTextbox, mode: str):
    """Updates textbox colors and syntax tags based on theme mode."""
    p = COLORS["light" if mode == "Light" else "dark"]
    txt_log.configure(
        fg_color=p["console_bg"],
        text_color=p["console_text"],
        border_color=p["console_border"],
        border_width=1
    )
    txt_log.tag_config("time", foreground=p["tag_time"])
    txt_log.tag_config("info", foreground=p["tag_info"])
    txt_log.tag_config("success", foreground=p["tag_success"])
    txt_log.tag_config("warning", foreground=p["tag_warning"])
    txt_log.tag_config("error", foreground=p["tag_error"])
