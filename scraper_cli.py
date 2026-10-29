"""
=============================================================================
PRODUCTION-READY NOVEL SCRAPER WITH ANTI-BOT EVASION (CLOUDFLARE BYPASS)
Target Website : novellunar.com
Target Novel   : Invincible Mumu (Chapters 1 to 177)
Technology     : Python 3, requests, BeautifulSoup4
Batching       : 5 chapters per file (Chapters_X_to_Y.txt)
=============================================================================
"""

import os
import time
import random
import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional, List
from novel_cleaner import clean_html_article, heal_raw_text

# =============================================================================
# 1. ANTI-BOT & NETWORK CONFIGURATION
# =============================================================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Cookie": "cf_clearance=_XSHG9iik6URzvUldWHj.OenYItPFWB4yHMpoNa0mrI-1793187408-1.2.1.1-dSaWrbEV0ur5n2FaW4lf7UucwHZhpamKVva4EVvwoOYnL3Rq0y4Ay3R7VCxT_iCqujGcVy.7CF.y5AFQWUnrqeXvojCARrYIM_2CyHN660uxtn8dWylqcYL5BsY1rzGCiIr7xQApHk3JpnMBY_LEUibF6hLQFAp6mt4eW9tYY2D6.ju6j_obqV4BHRi6Mw_jExD6pXXmSfsSTj1rWsj_N9OfipPH43PlxZAOSGe6Ys9LN9HSJt7UE3ZLuSTjOo_C4yTCKP_J8V.oFHm4laJAkJ3BHHEtvYGvDb4bTDO4gFeIIFS3TZRrXLtfys7EQasb06hMyvtgPrh1H9lLVWv.HOvDpO96rh06ebKZikjUnSbvfIUO0WlpWQYApyLyYAl7n8c1YXY2de8aBgRaBwcO5Mqi4d4udsGMSXxykq.jfd7y6E2iOpB5S2iIZJTxv_jb.LSHwT4Do3WDeKmjwiXF6HRnCoojazstKdRhImmcXBSSfQpLRtFN0_SJJuGZSBGNTblG5coyXIfWdzr4PaX.fQ; _ga=GA1.1.1735907276.1793187425; __Secure-next-auth.callback-url=https%3A%2F%2Fnovellunar.com; __Host-next-auth.csrf-token=7dedbb1395124f2576054468d55d05cb620ff9c87bf8232bbd71171ce2abd358%7C46f7a3ee42e38c78f35585176a5273e7e19957b6099003f02b7867d720394cdd; _ga_6PBHV8YLG6=GS2.1.s1793190874$o2$g1$t1793190876$j58$l0$h0",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="155", "Google Chrome";v="155"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

# =============================================================================
# 2. GENERAL SETTINGS
# =============================================================================
BASE_URL = "https://novellunar.com/novel/invincible-mumu/chapter/{}"
START_CHAPTER = 1
END_CHAPTER = 177
BATCH_SIZE = 5
OUTPUT_DIR = "Invincible_Mumu_Novel"
REQUEST_TIMEOUT = 25
MIN_DELAY = 8.0   # Giây nghỉ tối thiểu
MAX_DELAY = 15.0  # Giây nghỉ tối đa
MAX_RETRIES = 5   # Số lần thử lại tối đa cho mỗi chapter bị lỗi
RETRY_UNTIL_SUCCESS = True  # Thử lại liên tục đến khi cào được thành công, không bỏ sót


def init_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def fetch_and_parse_chapter(session: requests.Session, chapter_num: int) -> Tuple[bool, str, Optional[str]]:
    url = BASE_URL.format(chapter_num)
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)

        if response.status_code == 403:
            return False, "", "HTTP 403 Forbidden: Cloudflare chặn request. Cần làm mới Cookie."
        elif response.status_code == 404:
            return False, "", f"HTTP 404 Not Found: Chapter {chapter_num} không tồn tại tại {url}."
        elif response.status_code != 200:
            return False, "", f"HTTP Error {response.status_code}: {response.reason}"

        soup = BeautifulSoup(response.content, "html.parser")
        article = soup.find("article")

        if not article:
            article = soup.select_one(".reading-content, .entry-content, #chapter-content, .chapter-content")

        if not article:
            return False, "", "Thiếu thẻ <article>: Không tìm thấy khối chứa nội dung truyện trong HTML."

        chapter_text = clean_html_article(article)

        if not chapter_text or len(chapter_text.strip()) < 20:
            return False, "", "Nội dung chapter trống hoặc ngắn bất thường (< 20 ký tự)."

        return True, chapter_text, None

    except requests.exceptions.Timeout:
        return False, "", f"Hết thời gian chờ (Timeout sau {REQUEST_TIMEOUT}s)."
    except requests.exceptions.RequestException as e:
        return False, "", f"Lỗi kết nối mạng: {str(e)}"
    except Exception as e:
        return False, "", f"Lỗi không xác định: {str(e)}"


def save_batch_to_file(batch_records: List[Tuple[int, str, bool, Optional[str]]], batch_start: int, batch_end: int) -> str:
    save_dir = OUTPUT_DIR if os.path.basename(os.path.normpath(OUTPUT_DIR)).lower() == "raw" else os.path.join(OUTPUT_DIR, "raw")
    os.makedirs(save_dir, exist_ok=True)
    filename = f"Chapters_{batch_start}_to_{batch_end}.txt"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "w", encoding="utf-8-sig") as f:
        for ch_num, content, success, err_msg in batch_records:
            f.write(f"CHAPTER {ch_num}\n\n")
            if success:
                f.write(content)
            else:
                f.write(f"[ERROR: Không thể tải Chapter {ch_num}. Lý do: {err_msg}]")
            f.write("\n\n")

    return filepath


def run_scraper():
    print("=" * 75)
    print("[START] BAT DAU CAO TRUYEN: INVINCIBLE MUMU")
    print(f"Khoang Chapter : {START_CHAPTER} den {END_CHAPTER} (Tong: {END_CHAPTER - START_CHAPTER + 1})")
    print(f"Thu muc luu    : {os.path.abspath(OUTPUT_DIR)}")
    print(f"Dong goi batch : {BATCH_SIZE} chapters -> 1 file .txt")
    print(f"Che do thu lai : {'BAT (Thu lai den khi thanh cong)' if RETRY_UNTIL_SUCCESS else f'Toi da {MAX_RETRIES} lan'}")
    print("=" * 75)

    session = init_session()
    current_batch = []
    batch_start = START_CHAPTER
    successful_downloads = 0
    failed_downloads = 0

    total_chapters = END_CHAPTER - START_CHAPTER + 1

    for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
        idx = ch_num - START_CHAPTER + 1

        # Vong lap thu lai cho chapter
        attempt = 0
        success = False
        content = ""
        error_msg = ""

        while not success:
            attempt += 1
            if attempt == 1:
                print(f"[{idx}/{total_chapters}] Dang tai Chapter {ch_num}...", end=" ", flush=True)
            else:
                print(f"   [RETRY {attempt}] Dang cao lai Chapter {ch_num}...", end=" ", flush=True)

            success, content, error_msg = fetch_and_parse_chapter(session, ch_num)

            if success:
                successful_downloads += 1
                retry_str = f" (sau {attempt} lan)" if attempt > 1 else ""
                print(f"[OK] ({len(content)} ky tu){retry_str}")
                current_batch.append((ch_num, content, True, None))
                break
            else:
                print(f"[FAIL] - {error_msg}")

                # Lam moi session neu dut mang / timeout
                if "Timeout" in error_msg or "ket noi" in error_msg or "Connection" in error_msg:
                    try:
                        session.close()
                        session = init_session()
                    except Exception:
                        pass

                if not RETRY_UNTIL_SUCCESS and attempt >= MAX_RETRIES:
                    failed_downloads += 1
                    current_batch.append((ch_num, "", False, error_msg))
                    break

                retry_sleep = round(random.uniform(MIN_DELAY, MAX_DELAY), 2)
                print(f"   [WAIT] Cho {retry_sleep}s truoc khi cao lai Chapter {ch_num}...")
                time.sleep(retry_sleep)

        # Luu batch
        is_last_chapter = (ch_num == END_CHAPTER)
        if len(current_batch) >= BATCH_SIZE or is_last_chapter:
            batch_end = ch_num
            saved_file = save_batch_to_file(current_batch, batch_start, batch_end)
            print(f"   [SAVED] Da luu batch: {os.path.basename(saved_file)} ({len(current_batch)} chapters)")

            current_batch = []
            batch_start = ch_num + 1

        # Nghi ngoi giua cac chapter
        if not is_last_chapter and success:
            sleep_duration = round(random.uniform(MIN_DELAY, MAX_DELAY), 2)
            print(f"   [WAIT] Nghi {sleep_duration}s de mo phong nguoi doc...")
            time.sleep(sleep_duration)

    print("\n" + "=" * 75)
    print("[COMPLETE] HOAN TAT!")
    print(f"Tổng chapters : {total_chapters}")
    print(f"Thành công    : {successful_downloads}")
    print(f"Lỗi / Bỏ qua  : {failed_downloads}")
    print(f"Thư mục       : {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 75)


if __name__ == "__main__":
    run_scraper()
