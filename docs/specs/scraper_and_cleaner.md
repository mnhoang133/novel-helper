# 🌐 SPEC: Web Scraping & Data Sanitization

## 1. Cloudflare Evasion Architecture (`core/scraper.py`)
- **Engine**: `cloudscraper.Session` with custom browser cookie string and User-Agent headers.
- **Delay Jitter**: Configurable randomized pause (`delay_min` to `delay_max`) between chapter requests.
- **Auto-Retry with Backoff**: When network drops or Cloudflare returns HTTP 429/503, applies exponential backoff instead of skipping chapters.
- **Batching**: Chapters are written in blocks (e.g. 5 chapters per `.txt` file) to prevent memory bloating and allow resume.

---

## 2. Text Normalization & XML Sanitization (`core/cleaner.py`)
- **XML 1.0 Control Character Removal**:
  Removes NULL bytes (`\x00`) and ASCII control characters (`\x00-\x08`, `\x0B-\x0C`, `\x0E-\x1F`).
  Eliminates the common `ValueError: All strings must be XML compatible: Unicode or ASCII, no NULL bytes or control characters` error.
- **Quote Normalization**:
  Repairs dangling quotation marks (`“”‘’`), converts corrupt quote entities, and normalizes hyphens/em-dashes.
- **HTML DOM Cleanup**:
  BeautifulSoup article extraction strips `<script>`, `<style>`, `<nav>`, `<iframe>`, and ad containers while preserving text paragraphs.
- **In-place File Repair**:
  `repair_file_inplace(path)` detects file encoding (UTF-8, UTF-8-sig, Latin-1), cleans invalid bytes, and rewrites clean UTF-8.
