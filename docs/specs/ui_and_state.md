# SPEC: User Interface, Reactive State & Theme System

## 1. Appearance & Theme System (`ui/theme.py`)
- Dark & Light mode palettes fine-tuned for high contrast and readability:
  - **Light Mode**: Background `#f1f5f9` (prevents eye strain compared to harsh `#ffffff`), Card containers `#ffffff`, Accent `#0284c7`.
  - **Dark Mode**: Background `#0b0f19`, Card containers `#151d2f`.
- Text color rules: Black text on white buttons in Light mode, white text on dark buttons in Dark mode. No illegible overlapping colors.
- Zero-emoji policy across all buttons and UI labels.

---

## 2. Dynamic Live Margin Preview
In Tab 2 (`ui/tab_publisher.py`):
- `lbl_margin_preview` automatically updates as the user types:
  `[Lề đối xứng in 2 mặt] Trang lẻ: Trái (Gáy) 1.2cm, Phải (Mép) 0.6cm | Trang chẵn: Trái (Mép) 0.6cm, Phải (Gáy) 1.2cm`
- Automatically enforces safe gutter elevation if inside $\le$ outside when mirror margins is active.

---

## 3. Session & Profile Persistence (`core/session_manager.py`)
- Saves UI state to `last_session.json` on app close or profile save.
- Preserves folder history (`recent_novels`) to prevent accidentally exporting over other novel projects.
