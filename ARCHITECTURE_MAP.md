# ARCHITECTURE MAP & MASTER DEVELOPER GUIDE
> **Project**: Modern Novel Scraper & Print-Ready Book Publisher  
> **Target Audience**: Future AI Agents & Developers maintaining this codebase.  
> **Key Goal**: Fast, zero-overhead navigation and modification without having to read through 2000+ lines of monolithic code.

---

## 1. Directory Tree & Architecture Overview

```
novel_scraper/
├── app_gui.py                 # [Controller] Main CustomTkinter UI entry point & event orchestrator
├── ARCHITECTURE_MAP.md        # [Documentation] This master reference guide
├── requirements.txt           # Python package dependencies
├── run_gui.bat                # Windows launcher batch script
├── last_session.json          # Persistent user session & profile state
├── sample_invincible_mumu.json# Sample scraping profile
│
├── core/                      # Pure Business Logic & Calculation Engines (No GUI dependencies)
│   ├── __init__.py
│   ├── book_engine.py         # Line calculations, Volume partitioning, Smart Pagination, DOCX/PDF export
│   ├── cleaner.py             # XML sanitization, HTML article cleanup, quote normalization
│   ├── scraper.py             # Cloudflare-evasive web scraping, URL patterns, batch writing
│   └── session_manager.py     # JSON state persistence, profile loading, folder auto-discovery
│
├── ui/                        # Presentation Layer (CustomTkinter Components)
│   ├── __init__.py
│   ├── theme.py               # Color palettes (Light/Dark), segmented buttons, console syntax colors
│   ├── tab_scraper.py         # Tab 1: Web Scraper controls, network settings, folder pickers
│   ├── tab_publisher.py       # Tab 2: Book Publisher controls, range detector, custom & mirror margins
│   └── smart_analyzer_dialog.py # Interactive 6-Tier Volume Partitioning & TOC Optimization modal (Full 1-Page TOC, Full 2-Page TOC, and Page-bound Tiers)
│
└── [Facades / Backwards-Compatibility Adapters]
    ├── word_exporter.py       # Re-exports all functions from core.book_engine
    ├── novel_cleaner.py       # Re-exports all functions from core.cleaner
    └── scraper_core.py        # Re-exports all classes & functions from core.scraper
```

---

## 2. Fast Lookup: "Where Do I Make Changes?"

| What You Need to Modify / Debug | File to Open | Primary Functions / Classes |
| :--- | :--- | :--- |
| **Smart Pagination Threshold** (Heading + 3 lines fit logic) | `core/book_engine.py` | `calculate_chapter_real_lines()`, `export_single_document()` |
| **Volume Balancing Algorithm** (Eliminate orphan stub volumes) | `core/book_engine.py` | `analyze_optimal_volume_splits()`, `split_chapters_into_volumes()` |
| **Table of Contents (TOC) Page Fit** (1 page vs 2 page check) | `core/book_engine.py` | `analyze_optimal_volume_splits()` |
| **Mirror Margins (Gáy Sách In 2 Mặt)** | `core/book_engine.py` | `export_single_document()` (`<w:mirrorMargins/>`) |
| **Word COM to PDF Conversion** | `core/book_engine.py` | `convert_docx_to_pdf()` |
| **Chapter Range Auto-Detection** (Scan .txt files) | `core/book_engine.py` | `detect_chapter_range_from_folder()`, `scan_and_collect_chapters()` |
| **XML / ASCII / Control Character Errors** | `core/cleaner.py` | `sanitize_xml_string()`, `repair_file_inplace()` |
| **HTML Chapter Scraping & Content Cleaning** | `core/cleaner.py` | `clean_html_article()`, `heal_raw_text()`, `heal_broken_lines()`, `repair_directory_inplace()` |
| **Scraper Requests, Retries, Cookies, Cloudflare** | `core/scraper.py` | `NovelScraper.scrape_chapter()`, `derive_pattern_from_url()` |
| **Auto-Detect Novel Folders from History** | `core/session_manager.py` | `discover_novel_folders()`, `save_session()`, `load_session()` |
| **Light / Dark Mode Palette & Contrast** | `ui/theme.py` | `THEME`, `setup_segmented_button_style()`, `update_console_colors()` |
| **Scraper Tab Controls & Responsive Grid** | `ui/tab_scraper.py` | `build_scraper_tab()` |
| **Publisher Tab Layout, Margins, Inputs** | `ui/tab_publisher.py` | `build_publisher_tab()` |
| **Smart Volume Analyzer Modal Dialog** | `ui/smart_analyzer_dialog.py` | `SmartVolumeAnalyzerDialog` (Arbitrary Start/End Chapter Range Support) |
| **GUI Event Handlers, Logging, Threading** | `app_gui.py` | `ModernNovelApp` methods (`_start_scraping`, `_start_publishing`, etc.) |

---

## 3. Detailed Catalog of Modules & Functions

### `core/book_engine.py`
The central formatting, pagination, and document rendering engine.

- **`detect_chapter_range_from_folder(folder_path: str) -> dict`**
  - Scans `folder_path/raw/` and `folder_path/` for `.txt` files.
  - Parses chapter numbers using regex `r'^(CHAPTER|Chapter|Chương)\s+(\d+)\b'`.
  - Fallback to batch filename pattern `Chapters_{start}_to_{end}.txt`.
  - Returns: `{"total_files", "total_chapters", "min_chapter", "max_chapter", "missing_chapters", "chapter_numbers"}`.

- **`scan_and_collect_chapters(folder_path, file_paths=None, start_chapter=None, end_chapter=None) -> List[Tuple[int, str, str]]`**
  - Aggregates all chapter content from text files.
  - Automatically deduplicates and retains the longest/most complete version of each chapter.
  - Filters strictly between `[start_chapter, end_chapter]`.

- **`calculate_lines_per_page(printable_height_cm: float, body_font_size: int = 14) -> float`**
  - Dynamically computes printable body lines per page based on actual user margins and font size.
  - Scales proportionally to `printable_height_cm / 27.3` and `14.0 / body_font_size`.
  - Narrow margins (0.6cm top/bottom) yield ~34–36 lines/page (up to ~39 lines with 12pt font).

- **`calculate_chars_per_line(printable_width_cm: float, body_font_size: int = 14) -> int`**
  - Dynamically computes characters per line based on printable page width.
  - Scales with `(21.0 - inside_margin - outside_margin) / 17.8` and `14.0 / body_font_size`.

- **`calculate_toc_entries_per_page(printable_height_cm: float) -> int`**
  - Dynamically computes Table of Contents chapter capacity per page.
  - Standard 1.2cm margins: 32 chapters/page.
  - Narrow 0.6cm margins: 38–40 chapters/page!
  - Wide 2.0cm margins: ~28 chapters/page.

- **`analyze_optimal_volume_splits(chapters, inside_margin_cm=2.0, outside_margin_cm=1.2, top_margin_cm=1.2, bottom_margin_cm=1.2, body_font_size=14) -> Dict[str, VolumeSplitOption]`**
  - Analyzes total chapter line weights using the user's specific margin and font settings.
  - Adapts TOC quality rating dynamically based on `toc_entries_per_page`.

- **`split_chapters_into_volumes(chapters, target_pages_per_volume=300, chars_per_page=1800) -> List[List[Tuple[int, str, str]]]`**
  - Line-balanced volume partitioner.
  - Dynamically computes optimal number of volumes $K$ and distributes chapters evenly across $K$ volumes so that the final volume never becomes an orphan 2-chapter stub.

- **`export_single_document(...) -> str`**
  - Compiles chapters into an OpenXML Word (`.docx`) file.
  - **Mirror Margins**: Injects `<w:mirrorMargins/>` into `doc.settings.element` so that odd pages have inside margin on left, even pages have inside margin on right.
  - **Custom Margins**: Configurable `inside_margin_cm`, `outside_margin_cm`, `top_margin_cm`, `bottom_margin_cm`, `footer_distance_cm`.
  - **Redesigned Smart Pagination**:
    - Keeps track of estimated `lines_on_page` (capacity: 32 lines/page).
    - When starting a chapter: checks `lines_remaining = 32.0 - lines_on_page`.
    - If `lines_remaining >= 8.0` (Heading + ornament ~5 lines + at least 3 lines of text ~3 lines), the chapter starts on the same page.
    - Otherwise, cleanly issues `doc.add_page_break()` to prevent orphan headers.
    - Automatically attaches `<w:keepNext/>` to the chapter heading and first paragraph.

- **`convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool`**
  - High-fidelity conversion via Microsoft Word COM automation (`win32com.client`).
  - Preserves exact layout, fonts, headers, footers, and mirror margins.

---

### `core/cleaner.py`
Data sanitization and text normalization.

- **`sanitize_xml_string(value: str) -> str`**
  - Removes NULL bytes (`\x00`) and XML 1.0 incompatible control characters (`\x00-\x08`, `\x0B-\x0C`, `\x0E-\x1F`).
  - Eliminates the `All strings must be XML compatible` python-docx crash.

- **`clean_html_article(html_content: str, selector: str = "article") -> str`**
  - Uses BeautifulSoup to strip ads, script, style, nav, and iframe tags while preserving chapter text paragraphs.

- **`heal_raw_text(text: str) -> str`**
  - Normalizes curly quotes (`“”‘’`), fixes dangling punctuation, and eliminates broken control characters.

- **`repair_file_inplace(file_path: str) -> Tuple[bool, int, str]`**
  - Opens a `.txt` file with UTF-8 / UTF-8-sig / Latin-1 fallbacks, sanitizes control characters, and rewrites clean UTF-8.

---

### `core/scraper.py`
Evasive web scraping and chapter fetching.

- **`NovelScraper` class**
  - Manages `cloudscraper.Session` with custom browser cookies and User-Agent headers.
  - `scrape_chapter(ch_num: int, url_template: str, selector: str, ...) -> Tuple[str, str, int]`
  - Implements exponential jitter delay and configurable auto-retry backoff on timeout/network drops.

- **`derive_pattern_from_url(first_chapter_url: str) -> Tuple[str, int]`**
  - Automatically turns `https://novellunar.com/novel/mumu/chapter/1` into `https://novellunar.com/novel/mumu/chapter/{}` and extracts starting chapter `1`.

- **`save_chapter_batch(novel_dir: str, batch_chapters: list, start_c: int, end_c: int)`**
  - Saves batch chapters into `raw/Chapters_{start}_to_{end}.txt`.

---

### `core/session_manager.py`
Persistent configuration and discovery.

- **`load_session(config_path: str) -> dict`**
  - Loads `last_session.json` merged over robust default configurations (including all margins and pagination settings).

- **`save_session(config_path: str, data: dict)`**
  - Safely writes session state with UTF-8 encoding and indented JSON.

- **`discover_novel_folders(base_save_dir: str, current_folder: str = "") -> List[str]`**
  - Inspects subdirectories in `base_save_dir` containing `.txt` files or `raw/` subfolders.
  - Prioritizes most recently modified novel folders.

---

### `ui/theme.py`
Visual styling and theme configuration.

- **`THEME` dictionary**
  - Contains fine-tuned hex palettes for `"light"` and `"dark"` modes.
  - Light mode uses a calm background (`#f1f5f9`) and soft card panels (`#ffffff`) to prevent eye fatigue.
  - Dark mode uses deep slate surfaces (`#0b0f19`, `#151d2f`).

- **`setup_segmented_button_style(seg_btn, mode="Light")`**
  - Ensures clean rounded tab pills with crisp active/inactive foreground contrast.

- **`update_console_colors(textbox, mode="Light")`**
  - Sets console syntax highlighting tags: `info` (blue), `success` (emerald green), `warning` (amber), `error` (crimson), and `accent` (violet).

---

### `ui/tab_scraper.py` & `ui/tab_publisher.py`
User interface builders.

- **`build_scraper_tab(parent, app) -> ctk.CTkFrame`**
  - Card 1: Target Novel, URL Template, Start/End chapters, Batch size.
  - Card 2: Cloudflare Evasion (Cookie String, User-Agent, Safe Delay, Timeout, Auto-Retry).
  - Card 3: Storage Location & Novel Profile history dropdown.
  - Action buttons: "START SCRAPING NOVEL", "STOP", "OPEN FOLDER".

- **`build_publisher_tab(parent, app) -> ctk.CTkFrame`**
  - Card 1: Source Folder & Chapter Range (`entry_pub_start_ch`, `entry_pub_end_ch`, "Auto Detect", "All Chapters").
  - Card 2: Book Metadata & Typography (Title, Author, Subtitle, Year, Font, Font Size, Alignment).
  - Card 3: Page Margins & Book Binding:
    - Mirror Margins Checkbox (`chk_pub_mirror_margins`).
    - Inside Margin (Gáy dán): default 2.0 cm.
    - Outside Margin (Mép ngoài): default 1.2 cm.
    - Top & Bottom Margins: default 1.2 cm.
    - Footer Distance: default 0.7 cm.
    - "Khôi phục mặc định" (Reset Margins) button.
  - Card 4: Volume Splitting & Optimization:
    - Target Pages entry & Smart Pagination checkbox.
    - **"[Analyze] Phân tích & Tối ưu số trang (Smart Volume Analyzer)"** button.
    - Format dropdown (DOCX, PDF, Cả hai).
  - Action buttons: "GENERATE PRINT-READY BOOK", "Sửa lỗi ký tự XML file TXT", "OPEN FOLDER".

---

### `ui/smart_analyzer_dialog.py`
Modal dialog for volume balancing and TOC fit analysis.

- **`SmartVolumeAnalyzerDialog(parent, chapters, on_select_tier)`**
  - Displays:
    - Total detected chapters and estimated total book pages.
    - 5 Interactive Tier Cards (Tối ưu Khít Mục lục & Đều chương, Mỏng 50-100 trang, Chuẩn 100-200 trang, Vừa 200-300 trang, Dày 300-400 trang).
    - For each tier: Volume count, Average pages per volume, Average chapters per volume, and **TOC Fit Rating** (e.g. `[TOC Fit] Rất khít (1 trang mục lục, lấp đầy 91%)`).
    - Detailed chapter breakdown per volume (e.g. `Tập 1: Chap 1 -> 26 (~308 trang)`).
  - "Áp dụng cấu hình này" button: Immediately sets target pages in Tab 2 and closes the dialog.

---

### `app_gui.py`
The master application controller.

- Connects UI events to asynchronous background worker threads (`threading.Thread`).
- Redirects log messages to the syntax-highlighted console textbox via `log_message(text, tag)`.
- Handles profile load/save, folder auto-detection, scraping loop, XML file repair, and book export workflows.

---

## 4. Key Mathematical Formulas & Rules

### A. Smart Pagination (Rule of 8.0 Lines)
- Standard page height holds **32 lines** of text.
- Starting a chapter requires:
  $$\text{Heading + ornament + spacing} \approx 5.0\text{ lines}$$
  $$\text{Minimum body text to prevent orphan header} = 3.0\text{ lines}$$
  $$\text{Required Minimum Remaining Space} = 8.0\text{ lines}$$
- If $\text{lines\_on\_page} \le 32.0 - 8.0 = 24.0$, chapter continues on the current page.
- Otherwise, a page break is inserted.

### B. Balanced Volume Splitting
To prevent a trailing 2-chapter volume stub:
$$K = \max\left(1, \text{round}\left(\frac{\text{Total Printable Lines}}{\text{Target Volume Lines}}\right)\right)$$
$$\text{Average Target Lines per Volume} = \frac{\text{Total Printable Lines}}{K}$$
Chapters are then partitioned into $K$ roughly equal segments using continuous line accumulation, guaranteeing every volume has a balanced thickness.

### C. TOC Page Fitting
- 1 TOC page holds up to **32 chapter entries**.
- Volumes with $\le 32$ chapters consume exactly 1 TOC page.
- Volumes with $33 - 64$ chapters consume exactly 2 TOC pages.
- Volumes near 33–36 chapters generate a warning about wasted blank space on the second TOC page.

### D. Mirror Margins (Gáy Sách In 2 Mặt) & Smart Safe Binding
- OpenXML elements `<w:mirrorMargins/>` and `<w:evenAndOddHeaders/>` enable facing pages.
- `left_margin` becomes the **Inside (Gáy dán)** margin:
  - On odd pages (trang lẻ): applied to the **left edge** (phía gáy sách).
  - On even pages (trang chẵn): applied to the **right edge** (phía gáy sách).
- `right_margin` becomes the **Outside (Mép ngoài)** margin:
  - On odd pages: applied to the **right edge**.
  - On even pages: applied to the **left edge**.
- **Smart Safe Binding Rule**:
  If the user sets `inside_margin <= outside_margin` (e.g. setting both to 0.6cm to save paper), the system automatically elevates inside margin to $\max(1.2, \text{outside} \times 2.0)$ so that text is never swallowed by the binding glue or spine!
  - Odd pages (e.g. Page 7): Left = 1.2 cm, Right = 0.6 cm.
  - Even pages (e.g. Page 6): Left = 0.6 cm, Right = 1.2 cm.
- **Two-Sided Footers**:
  - Odd pages: page number is aligned **Right** (outer edge).
  - Even pages: page number is aligned **Left** (outer edge).
  - First page (Cover): page number is suppressed.
- `right_margin` becomes the **Outside (Mép ngoài)** margin.
- Default values: Inside = 2.0 cm, Outside = 1.2 cm, Top/Bottom = 1.2 cm, Footer = 0.7 cm.
