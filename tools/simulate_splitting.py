"""
Tool: simulate_splitting.py
Description: Fast simulation tool to calculate real printable lines, dynamic TOC capacity,
             and balanced volume partitions without generating Word/PDF documents.
Usage: python tools/simulate_splitting.py <novel_folder> [inside_cm] [outside_cm] [top_cm] [bottom_cm] [start_ch] [end_ch]
"""

import sys
import os

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.chapter_scanner import scan_and_collect_chapters
from core.volume_splitter import analyze_optimal_volume_splits

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/simulate_splitting.py <novel_folder> [inside_cm] [outside_cm] [top_cm] [bottom_cm] [start_ch] [end_ch]")
        sys.exit(1)

    folder = sys.argv[1]
    inside_m = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    outside_m = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
    top_m = float(sys.argv[4]) if len(sys.argv) > 4 else 1.2
    bot_m = float(sys.argv[5]) if len(sys.argv) > 5 else 1.2
    start_c = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6].isdigit() else None
    end_c = int(sys.argv[7]) if len(sys.argv) > 7 and sys.argv[7].isdigit() else None

    range_txt = f" (Ch {start_c} to {end_c})" if (start_c or end_c) else " (All Chapters)"
    print(f"Scanning chapters in: {folder}{range_txt}")
    chapters = scan_and_collect_chapters(folder, start_chapter=start_c, end_chapter=end_c)
    if not chapters:
        print("No chapters found in specified folder/range.")
        sys.exit(1)

    print(f"Total Chapters Found: {len(chapters)} (Ch {chapters[0][0]} to Ch {chapters[-1][0]})")
    print(f"Margins Applied     : Inside={inside_m}cm, Outside={outside_m}cm, Top/Bottom={top_m}/{bot_m}cm")

    results = analyze_optimal_volume_splits(
        chapters,
        inside_margin_cm=inside_m,
        outside_margin_cm=outside_m,
        top_margin_cm=top_m,
        bottom_margin_cm=bot_m
    )

    first = next(iter(results.values()))
    print(f"\n--- DYNAMIC PAGE CAPACITIES ---")
    print(f"Body Lines / Page   : ~{first.lines_per_page} lines")
    print(f"Characters / Line   : ~{first.chars_per_line} chars")
    print(f"TOC Entries / Page  : ~{first.toc_entries_per_page} chapters/page\n")

    print(f"--- 5-TIER PARTITION SIMULATION ---")
    for key, opt in results.items():
        print(f"\n[{opt.tier_name}]")
        print(f"  • Volumes Count     : {opt.num_volumes} volumes")
        print(f"  • Average Pages/Vol : ~{opt.avg_pages_per_vol} pages")
        print(f"  • Average Chaps/Vol : ~{opt.avg_chapters_per_vol} chapters")
        print(f"  • TOC Fit Rating    : {opt.toc_quality_rating}")
        sample_vols = [f"V{vr[0]}: Ch{vr[1]}-{vr[2]} (~{vr[3]:.0f}p)" for vr in opt.volume_ranges[:4]]
        if len(opt.volume_ranges) > 4:
            sample_vols.append(f"... +{len(opt.volume_ranges)-4} more")
        print(f"  • Volume Breakdown  : {' | '.join(sample_vols)}")

if __name__ == "__main__":
    main()
