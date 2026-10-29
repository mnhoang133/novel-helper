# ARCHITECTURE MASTER INDEX

> **Quick Routing Guide for Developers & AI Agents**  
> Use this index to jump straight to the exact documentation file and code module for your task. Never spend time scanning unrelated files.

---

## 1. Quick Task Router

| What You Need To Modify / Debug | Read This Spec | Source File | Pre-built Test Tool |
| :--- | :--- | :--- | :--- |
| **Mirror Margins, Gáy Dán, Facing Footers** | [`docs/specs/margins_and_binding.md`](file:///docs/specs/margins_and_binding.md) | `core/docx_builder.py` | `python tools/inspect_docx.py <file>` |
| **Dynamic Page Math & TOC Capacity** | [`docs/specs/volume_and_toc_math.md`](file:///docs/specs/volume_and_toc_math.md) | `core/page_metrics.py`, `core/volume_splitter.py` | `python tools/simulate_splitting.py <dir>` |
| **Smart Pagination (Rule 8.0 Lines)** | [`docs/specs/smart_pagination.md`](file:///docs/specs/smart_pagination.md) | `core/docx_builder.py` | `tools/inspect_docx.py` |
| **Cloudflare Bypass, Cookies & Retries** | [`docs/specs/scraper_and_cleaner.md`](file:///docs/specs/scraper_and_cleaner.md) | `core/scraper.py` | `scraper_cli.py` |
| **XML Errors & Text Normalization** | [`docs/specs/scraper_and_cleaner.md`](file:///docs/specs/scraper_and_cleaner.md) | `core/cleaner.py` | `app_gui.py` (Repair button) |
| **Export Diagnostics & Audit Logs** | [`docs/specs/diagnostics_and_tools.md`](file:///docs/specs/diagnostics_and_tools.md) | `core/diagnostics.py` | `print/last_export_report.txt` |
| **UI Themes, Layouts & Modal Dialogs** | [`docs/specs/ui_and_state.md`](file:///docs/specs/ui_and_state.md) | `ui/*.py`, `app_gui.py` | `run_gui.bat` |

---

## 2. Codebase Organization

```
novel_scraper/
├── app_gui.py                 # Main event controller (< 900 lines)
├── run_gui.bat                # 1-click Windows launcher
├── docs/                      # 2-Tier Documentation System
│   ├── INDEX.md               # [You are here] Master routing table
│   └── specs/                 # Domain-specific technical specifications
│       ├── margins_and_binding.md
│       ├── volume_and_toc_math.md
│       ├── smart_pagination.md
│       ├── scraper_and_cleaner.md
│       ├── diagnostics_and_tools.md
│       └── ui_and_state.md
├── core/                      # Micro-modular backend modules (< 250 lines each)
│   ├── book_engine.py         # Consolidated master facade
│   ├── page_metrics.py        # Line, character, and TOC math
│   ├── volume_splitter.py     # Balanced volume partitioning
│   ├── docx_builder.py        # Word OpenXML document generation
│   ├── pdf_converter.py       # Word COM to PDF automation
│   ├── chapter_scanner.py     # Text parsing and chapter deduplication
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
