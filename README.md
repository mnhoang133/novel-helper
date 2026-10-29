# Universal Novel Scraper & Print-Ready Book Publisher (DOCX / PDF)

A production-grade Python desktop application and headless CLI suite designed to scrape web novels, bypass Cloudflare bot protections, and compile chapters into physical print-ready **Word (.docx)** and **PDF** book volumes with automatic Tables of Contents, balanced volume partitioning, and true two-sided book binding margins.

---

## Project Architecture

```
novel_scraper/
├── app_gui.py                 # Modern CustomTkinter Desktop Controller
├── run_gui.bat                # 1-Click Windows Launcher for Desktop App
├── requirements.txt           # Python package dependencies
├── ARCHITECTURE_MAP.md        # Comprehensive technical manual
├── docs/                      # 2-Tier Modular Documentation System
│   ├── INDEX.md               # Quick routing table for developers & AI agents
│   └── specs/                 # Deep-dive domain technical specifications
│       ├── margins_and_binding.md
│       ├── volume_and_toc_math.md
│       ├── smart_pagination.md
│       ├── scraper_and_cleaner.md
│       ├── diagnostics_and_tools.md
│       └── ui_and_state.md
├── core/                      # Micro-modular backend engines (< 250 lines each)
│   ├── book_engine.py         # Consolidated master facade
│   ├── page_metrics.py        # Dynamic line, character, and TOC math
│   ├── volume_splitter.py     # Balanced volume partitioning
│   ├── docx_builder.py        # Word OpenXML document builder
│   ├── pdf_converter.py       # Microsoft Word COM to PDF automation
│   ├── chapter_scanner.py     # File discovery, parsing & deduplication
│   ├── cleaner.py             # XML sanitization and quote healing
│   ├── scraper.py             # Cloudflare evasive HTTP scraper
│   ├── session_manager.py     # Profile & history persistence
│   └── diagnostics.py         # Automated export audit reports
├── ui/                        # Presentation Layer
│   ├── theme.py               # Light/Dark palettes & console coloring
│   ├── tab_scraper.py         # Scraper GUI tab
│   ├── tab_publisher.py       # Publisher GUI tab
│   └── smart_analyzer_dialog.py # 3-Tier volume analyzer dialog
└── tools/                     # Pre-built 0.5s Diagnostic CLI Tools
    ├── inspect_docx.py        # Inspects OpenXML margins, tags, footers
    └── simulate_splitting.py  # Fast volume & TOC simulation
```

---

## Key Features

### 1. Two-Sided Book Printing & Mirror Margins (`<w:mirrorMargins/>`)
- Native OpenXML `<w:mirrorMargins/>` and `<w:evenAndOddHeaders/>` support.
- **Smart Safe Binding**: Inside gutter automatically maintains safe binding width ($\ge 1.2\text{ cm}$) so text is never swallowed by spine glue or thread.
  - **Odd Pages (Trang lẻ)**: Left edge is Inside (Gáy dán), Right edge is Outside (Mép ngoài). Page number bottom-right.
  - **Even Pages (Trang chẵn)**: Left edge is Outside (Mép ngoài), Right edge is Inside (Gáy dán). Page number bottom-left.

### 2. Dynamic Physical Page Math & TOC Optimization
- **Dynamic Capacity**: Automatically calculates lines per page, characters per line, and Table of Contents entries per page adapted to user margins.
- **Narrow Margins**: Narrow margins (0.6cm) expand TOC capacity to **38–40 chapters/page** (safely exceeding the 32-chapter standard).
- **Smart Volume Balancer**: Partitions chapters evenly across $K$ volumes, eliminating awkward 2-chapter stubs in the final volume.

### 3. Redesigned Smart Pagination (Rule of 8.0 Lines)
- Dynamically checks available vertical space on the current page.
- If $\ge 8.0\text{ lines}$ remain (Heading + Ornament + at least 3 lines of text), the new chapter starts immediately with an ornamental divider.
- If $< 8.0\text{ lines}$, cleanly inserts a page break to prevent orphan headings at the bottom of the page.
- Attaches `<w:keepNext/>` to heading, ornament, and the first paragraph.

### 4. Automated Export Diagnostics & Observability
- Every publication automatically outputs `print/last_export_report.txt` recording input parameters, effective OpenXML margins, capacity math, and generated files.
- Zero black-box debugging.

### 5. Resilient Cloudflare Scraping
- Custom cookies and User-Agent headers with randomized safe delay jitter.
- Automatic retry backoff loop on timeouts or HTTP 429/503 to ensure zero skipped chapters.

---

## Quick Start

### Launching the Desktop UI
Double-click [`run_gui.bat`](file:///run_gui.bat) or run:
```powershell
python app_gui.py
```

### Pre-built Diagnostic Tools
- **Inspect any generated Word file in 0.2s**:
  ```powershell
  python tools/inspect_docx.py "path/to/novel_Volume_01.docx"
  ```
- **Simulate volume splits and TOC fit without generating Word/PDF**:
  ```powershell
  python tools/simulate_splitting.py "novel_folder" 1.2 0.6 0.6 0.6
  ```
