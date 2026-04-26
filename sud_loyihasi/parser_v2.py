"""
parser_v2.py — Publication.sud.uz dan yuklab olish

"""
import os
import json
import time
import random
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter


LISTING_API = "https://publication.sud.uz/criminal/findAll"
FILE_API    = "https://publication.sud.uz/api/file/criminal"

OUTPUT_DIR     = "sud_fayllari"
METADATA_FILE  = "listing_metadata.json"
PROGRESS_FILE  = "download_progress.json"

TARGET_COUNT          = 400
MAX_PAGES_TO_SCAN     = 80

# Tezlik sozlamalari 
BASE_DELAY            = 2.5   
JITTER                = 1.0    
COOLDOWN_AFTER_FAILS  = 60     
MAX_CONSECUTIVE_FAILS = 5

# Filter
PREFERRED_INSTANCE = 1
PREFERRED_DOC_TYPES = ["Айблов ҳукми"]

CORRUPTION_KEYWORDS = [
    "Ўзлаштириш", "растрата",
    "Пора бериш", "Пора олиш",
    "Ҳокимият", "мансаб",
    "Фирибгарлик",
    "Жиноий фаолиятдан",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "uz,en-US;q=0.9,en;q=0.8,ru;q=0.7",
    "Connection": "keep-alive",
}



def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    adapter = HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=0)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def smart_get(session, url, timeout=30, max_attempts=4):
    """
    Aqlli GET so'rov: ConnectTimeout/ConnectionError bo'lsa,
    exponential backoff bilan qayta urinadi (2, 4, 8, 16 sekund).
    """
    for attempt in range(1, max_attempts + 1):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"       HTTP {r.status_code}, {wait:.1f} sek kutish "
                      f"(urinish {attempt}/{max_attempts})")
                time.sleep(wait)
                continue
            return r
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == max_attempts:
                return None
            wait = 2 ** attempt + random.uniform(0, 1)
            err_short = str(e).split(":")[0][:50]
            print(f"       Ulanish muammosi ({err_short}), {wait:.1f} sek kutish "
                  f"(urinish {attempt}/{max_attempts})")
            time.sleep(wait)
    return None



def fetch_page(session, page, size=30):
    url = f"{LISTING_API}?size={size}&page={page}&court_type=CRIMINAL"
    r = smart_get(session, url, timeout=30)
    if r is None or r.status_code != 200:
        return None
    try:
        outer = r.json()
        if isinstance(outer.get("data"), str):
            return json.loads(outer["data"])
        return outer
    except Exception as e:
        print(f"       JSON parse xato: {e}")
        return None


def is_relevant_case(case):
    if case.get("instance") != PREFERRED_INSTANCE:
        return False
    doc_types = case.get("claimDocumentType") or []
    if not any(dt in PREFERRED_DOC_TYPES for dt in doc_types):
        return False
    if not case.get("claimId"):
        return False
    return True


def is_corruption_related(case):
    articles = case.get("claimArticles") or []
    joined = " ".join(articles).lower()
    return any(kw.lower() in joined for kw in CORRUPTION_KEYWORDS)


def download_file(session, claim_id, output_path):
    url = f"{FILE_API}/{claim_id}/"
    r = smart_get(session, url, timeout=60)
    if r is None:
        return False, "ulanib bo'lmadi"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"

    ctype = r.headers.get("Content-Type", "").lower()
    if "pdf" in ctype:
        ext = ".pdf"
    elif "msword" in ctype or "officedocument" in ctype:
        ext = ".doc"
    else:
        ext = ".bin"

    final_path = output_path.with_suffix(ext)
    final_path.write_bytes(r.content)
    return True, ext


def smart_delay():
    """Tasodifiy jitter bilan kutish — bot-like pattern'dan qochish"""
    delay = BASE_DELAY + random.uniform(-JITTER * 0.5, JITTER)
    delay = max(1.0, delay)
    time.sleep(delay)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"downloaded_ids": [], "last_page": 0, "metadata": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)



def main():
    print("=" * 80)
    print("  SUD QARORLARI YUKLAB OLISH — parser_v2.1")
    print("=" * 80)

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(exist_ok=True)

    progress = load_progress()
    downloaded = set(progress["downloaded_ids"])
    metadata = progress.get("metadata", [])
    start_page = progress.get("last_page", 0)

    print(f"  Allaqachon yuklangan : {len(downloaded)} ta")
    print(f"  Boshlanadigan sahifa : {start_page}")
    print(f"  Maqsad               : {TARGET_COUNT} ta fayl")
    print(f"  Tezlik               : ~{BASE_DELAY:.0f} sek/so'rov (jitter +/-{JITTER:.0f})")
    print(f"  Filter               : instance=1, 'Айблов ҳукми'")
    print(f"  Saqlanadigan papka   : {out_dir.absolute()}")
    print()

    session = make_session()
    page = start_page
    pages_without_relevant = 0
    consecutive_fails = 0

    while len(downloaded) < TARGET_COUNT and page < MAX_PAGES_TO_SCAN:
        print(f"\n  Sahifa {page} olinyapti...")
        data = fetch_page(session, page)

        if not data:
            consecutive_fails += 1
            if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                print(f"\n  >>> {MAX_CONSECUTIVE_FAILS} ta ketma-ket xato. "
                      f"{COOLDOWN_AFTER_FAILS} sekund cooldown...")
                time.sleep(COOLDOWN_AFTER_FAILS)
                consecutive_fails = 0
            page += 1
            smart_delay()
            continue
        consecutive_fails = 0

        cases = data.get("content", [])
        total_in_db = data.get("totalElements", 0)

        if page == start_page and total_in_db:
            print(f"  Saytda jami: {total_in_db:,} ta jinoiy ish")

        relevant = [c for c in cases if is_relevant_case(c)]
        relevant.sort(key=lambda c: not is_corruption_related(c))

        print(f"  Sahifada {len(cases)} ish, ulardan {len(relevant)} tasi mos keladi")

        if not relevant:
            pages_without_relevant += 1
            if pages_without_relevant >= 5:
                print("  5 ta sahifada hech narsa topilmadi - to'xtatilmoqda")
                break
        else:
            pages_without_relevant = 0

        for case in relevant:
            if len(downloaded) >= TARGET_COUNT:
                break

            claim_id = case["claimId"]
            if claim_id in downloaded:
                continue

            judge = (case.get("judge") or "?").strip()[:35]
            articles = case.get("claimArticles") or []
            article_short = articles[0][:30] if articles else "?"
            corr_flag = "[K]" if is_corruption_related(case) else "   "

            base_path = out_dir / f"ID_{claim_id}"
            print(f"  {corr_flag} [{len(downloaded)+1:>3}/{TARGET_COUNT}] "
                  f"ID {claim_id} | {judge:<35} | {article_short}")

            success, info = download_file(session, claim_id, base_path)

            if success:
                downloaded.add(claim_id)
                metadata.append(case)
                consecutive_fails = 0

                if len(downloaded) % 10 == 0:
                    progress.update(
                        downloaded_ids=list(downloaded),
                        metadata=metadata,
                        last_page=page,
                    )
                    save_progress(progress)
            else:
                print(f"       Yuklab bo'lmadi: {info}")
                consecutive_fails += 1

                if consecutive_fails >= MAX_CONSECUTIVE_FAILS:
                    print(f"\n  >>> {MAX_CONSECUTIVE_FAILS} ta ketma-ket xato. "
                          f"{COOLDOWN_AFTER_FAILS} sek cooldown - server tinchlanishi uchun...")
                    progress.update(
                        downloaded_ids=list(downloaded),
                        metadata=metadata,
                        last_page=page,
                    )
                    save_progress(progress)
                    time.sleep(COOLDOWN_AFTER_FAILS)
                    consecutive_fails = 0
                    print("  >> Davom etilmoqda...\n")

            smart_delay()

        page += 1

    # Yakuniy saqlash
    progress.update(
        downloaded_ids=list(downloaded),
        metadata=metadata,
        last_page=page,
    )
    save_progress(progress)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Hisobot
    print("\n" + "=" * 80)
    print(f"  YAKUN: {len(downloaded)} ta fayl yuklandi")
    print(f"  Fayllar  : {OUTPUT_DIR}/")
    print(f"  Metadata : {METADATA_FILE}")
    print(f"  Progress : {PROGRESS_FILE} (resume uchun)")
    print("=" * 80)

    if metadata:
        corr_count = sum(1 for m in metadata if is_corruption_related(m))
        print(f"\n  Korrupsiya bilan bog'liq ishlar: {corr_count} / {len(metadata)} "
              f"({corr_count*100//max(1,len(metadata))}%)")

        judges = {}
        for m in metadata:
            j = (m.get("judge") or "Noma'lum").strip()
            judges[j] = judges.get(j, 0) + 1
        top_judges = sorted(judges.items(), key=lambda x: -x[1])[:10]
        print("\n  Top-10 sudyalar (ko'p ish bo'yicha):")
        for j, c in top_judges:
            print(f"     {c:>3}  {j}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  >>> Foydalanuvchi to'xtatdi. Progress saqlangan, qaytadan ishga tushiring.")