"""
Facade Module: scraper_core
Description: Backward-compatible facade re-exporting functions from core.scraper.
"""

from core.scraper import (
    derive_pattern_from_url,
    NovelScraper
)

__all__ = [
    "derive_pattern_from_url",
    "NovelScraper"
]
