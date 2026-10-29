"""
Module: core.scraper
Description: HTTP scraper backend with Cloudflare cookie handling,
             auto-retries, rate limiting, and batch text file export.
Author: Google Deepmind Agent
"""

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import Callable, Optional, Dict, List, Tuple

from core.cleaner import clean_html_article, heal_raw_text, sanitize_xml_string


def derive_pattern_from_url(url: str) -> str:
    """
    Derives chapter template URL from Chapter 1 URL.
    Examples:
      'https://novellunar.com/novel/invincible-mumu/chapter/1' -> 'https://novellunar.com/novel/invincible-mumu/chapter/{}'
      'https://example.com/read/chapter-1/' -> 'https://example.com/read/chapter-{}/'
    """
    url = url.strip()
    if not url:
        return ""
    if "{}" in url or "{chapter_num}" in url:
        return url

    pattern = re.sub(r'(/|_|-|chapter/|chap/|ch-?)(\d+)(/|\.html)?$', r'\g<1>{}\3', url, flags=re.IGNORECASE)
    if pattern != url:
        return pattern

    matches = list(re.finditer(r'\d+', url))
    if matches:
        last_match = matches[-1]
        start, end = last_match.span()
        return url[:start] + "{}" + url[end:]

    return url + "/{}"


class NovelScraper:
    def __init__(
        self,
        url_pattern: str,
        start_chapter: int,
        end_chapter: int,
        batch_size: int = 5,
        output_dir: str = "Invincible_Mumu_Novel",
        headers: Optional[Dict[str, str]] = None,
        delay_min: float = 8.0,
        delay_max: float = 15.0,
        timeout: float = 20.0,
        content_selector: str = "article",
        max_retries: int = 5,
        retry_until_success: bool = True,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_progress: Optional[Callable[[int, int, float], None]] = None,
        on_batch_saved: Optional[Callable[[str, int], None]] = None,
        on_finished: Optional[Callable[[int, int, int], None]] = None,
    ):
        self.url_pattern = url_pattern.strip()
        self.start_chapter = int(start_chapter)
        self.end_chapter = int(end_chapter)
        self.batch_size = max(1, int(batch_size))
        self.output_dir = output_dir.strip() or "Novel_Output"
        self.headers = headers or {}
        self.delay_min = max(0.5, float(delay_min))
        self.delay_max = max(self.delay_min, float(delay_max))
        self.timeout = max(5.0, float(timeout))
        self.content_selector = content_selector.strip() or "article"
        self.max_retries = max(1, int(max_retries))
        self.retry_until_success = retry_until_success

        # Callbacks
        self.on_log = on_log or (lambda msg, tag: None)
        self.on_progress = on_progress or (lambda curr, total, pct: None)
        self.on_batch_saved = on_batch_saved or (lambda filename, count: None)
        self.on_finished = on_finished or (lambda s, e, t: None)

        self._stop_requested = False
        self.is_running = False

    def stop(self):
        """Requests safe scraper termination."""
        self._stop_requested = True

    def _sleep_interruptible(self, seconds: float) -> bool:
        """Interruptible sleep allowing immediate UI response to Stop."""
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self._stop_requested:
                return False
            time.sleep(min(0.3, max(0.05, end_time - time.time())))
        return True

    def _init_session(self) -> requests.Session:
        session = requests.Session()
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="155", "Google Chrome";v="155"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        if self.headers:
            default_headers.update(self.headers)
        session.headers.update(default_headers)
        return session

    def _fetch_chapter_html(self, session: requests.Session, chapter_num: int) -> Optional[str]:
        if "{chapter_num}" in self.url_pattern:
            url = self.url_pattern.format(chapter_num=chapter_num)
        else:
            url = self.url_pattern.format(chapter_num)

        attempt = 0
        while True:
            if self._stop_requested:
                return None

            attempt += 1
            try:
                self.on_log(f"Chapter {chapter_num}: Requesting {url} (Attempt {attempt})...", "info")
                resp = session.get(url, timeout=self.timeout)

                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 403:
                    self.on_log(f"Chapter {chapter_num}: 403 Forbidden (Cloudflare Challenge or expired cookies)!", "error")
                elif resp.status_code == 404:
                    self.on_log(f"Chapter {chapter_num}: 404 Not Found at {url}", "warning")
                    return None
                elif resp.status_code == 429:
                    self.on_log(f"Chapter {chapter_num}: 429 Rate Limited. Backing off 30s...", "warning")
                    if not self._sleep_interruptible(30.0):
                        return None
                    continue
                else:
                    self.on_log(f"Chapter {chapter_num}: HTTP status {resp.status_code}", "warning")

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                self.on_log(f"Chapter {chapter_num}: Network timeout / connection error: {e}", "warning")
            except Exception as e:
                self.on_log(f"Chapter {chapter_num}: Unexpected request exception: {e}", "error")

            if not self.retry_until_success and attempt >= self.max_retries:
                self.on_log(f"Chapter {chapter_num}: Reached max retry limit ({self.max_retries}). Skipping.", "error")
                return None

            backoff = min(60.0, (2 ** min(attempt, 5)) * 3.0 + random.uniform(2.0, 5.0))
            self.on_log(f"Chapter {chapter_num}: Retrying in {backoff:.1f}s (Attempt {attempt + 1})...", "warning")
            if not self._sleep_interruptible(backoff):
                return None

    def _parse_chapter_content(self, html: str, chapter_num: int) -> Optional[Tuple[str, str]]:
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Strip noisy elements
        for tag in soup(["script", "style", "noscript", "iframe", "button", "nav", "footer", "header"]):
            tag.decompose()

        for sel in [".ads", ".ad-container", ".advertisement", "#disqus_thread", ".comments", ".navigation"]:
            for el in soup.select(sel):
                el.decompose()

        # Extract content container
        container = soup.select_one(self.content_selector)
        if not container:
            for fallback in ["article", ".chapter-content", ".entry-content", ".reading-content", "#chapter-content"]:
                container = soup.select_one(fallback)
                if container:
                    break

        if not container:
            return None

        # Extract title
        title_el = soup.find(["h1", "h2"])
        title_text = title_el.get_text().strip() if title_el else f"Chapter {chapter_num}"
        title_text = sanitize_xml_string(title_text)

        body_text = clean_html_article(container)
        body_text = heal_raw_text(body_text)

        if not body_text or len(body_text) < 100:
            return None

        return title_text, body_text

    def _save_batch_file(self, batch_chapters: List[Tuple[int, str, str]]):
        if not batch_chapters:
            return

        start_c = batch_chapters[0][0]
        end_c = batch_chapters[-1][0]

        raw_dir = os.path.join(self.output_dir, "raw")
        os.makedirs(raw_dir, exist_ok=True)

        filename = f"Chapters_{start_c}_to_{end_c}.txt"
        filepath = os.path.join(raw_dir, filename)

        blocks = []
        for ch_num, title, body in batch_chapters:
            clean_title = sanitize_xml_string(title)
            clean_body = sanitize_xml_string(body)
            header = f"CHAPTER {ch_num}: {clean_title}" if str(ch_num) not in clean_title else clean_title
            blocks.append(f"{header}\n\n{clean_body}\n")

        full_content = "\n" + ("=" * 70) + "\n\n".join(blocks)
        full_content = sanitize_xml_string(full_content)

        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(full_content)

        self.on_log(f"Saved batch file: {filename} ({len(batch_chapters)} chapters)", "success")
        self.on_batch_saved(filename, len(batch_chapters))

    def run(self):
        self._stop_requested = False
        self.is_running = True
        total_ch = self.end_chapter - self.start_chapter + 1
        success_count = 0
        error_count = 0

        self.on_log(
            f"Starting scraper for Chapters {self.start_chapter} to {self.end_chapter} (Total: {total_ch}). "
            f"Batch size: {self.batch_size}, Destination: {os.path.join(self.output_dir, 'raw')}",
            "info"
        )

        session = self._init_session()
        batch_buffer: List[Tuple[int, str, str]] = []

        try:
            for idx, ch_num in enumerate(range(self.start_chapter, self.end_chapter + 1), start=1):
                if self._stop_requested:
                    self.on_log("Scraping stopped by user request.", "warning")
                    break

                html = self._fetch_chapter_html(session, ch_num)
                if not html:
                    error_count += 1
                    self.on_log(f"Chapter {ch_num}: Extraction failed.", "error")
                    continue

                parsed = self._parse_chapter_content(html, ch_num)
                if not parsed:
                    error_count += 1
                    self.on_log(f"Chapter {ch_num}: Failed to parse text from '{self.content_selector}' selector.", "error")
                    continue

                title, body = parsed
                batch_buffer.append((ch_num, title, body))
                success_count += 1

                self.on_log(f"Chapter {ch_num}: Successfully extracted ({len(body)} chars).", "success")
                pct = (idx / total_ch) * 100.0
                self.on_progress(idx, total_ch, pct)

                # Save when batch size is reached
                if len(batch_buffer) >= self.batch_size:
                    self._save_batch_file(batch_buffer)
                    batch_buffer.clear()

                # Polite random delay
                if idx < total_ch and not self._stop_requested:
                    sleep_sec = random.uniform(self.delay_min, self.delay_max)
                    self.on_log(f"Safe delay: Sleeping {sleep_sec:.1f}s before next chapter...", "info")
                    if not self._sleep_interruptible(sleep_sec):
                        break

            # Flush any remaining chapters in the buffer
            if batch_buffer:
                self._save_batch_file(batch_buffer)
                batch_buffer.clear()

        finally:
            self.is_running = False
            self.on_log(
                f"Finished scraping session. Success: {success_count}/{total_ch}, Errors: {error_count}.",
                "success" if error_count == 0 else "warning"
            )
            self.on_finished(success_count, error_count, total_ch)
