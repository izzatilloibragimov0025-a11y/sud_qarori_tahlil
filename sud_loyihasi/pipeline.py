"""
pipeline.py — To'liq quvvatlash zanjiri (end-to-end)
v1.1: listing_metadata.json topilmasa, download_progress.json dan tiklanadi

Ishlash zanjiri:
    1. .doc/.pdf fayllar  →  matn (doc_converter)
    2. matn + listing      →  extracted_data (deepseek_extractor_v2)
    3. extracted_data      →  risk_analysis (analyzer_v2)

ISHLATISH:
    python pipeline.py            # to'liq pipeline
    python pipeline.py --skip-ai  # AI extraction'ni o'tkazib (test uchun)
"""
import os
import sys
import json
import time
from pathlib import Path

from doc_converter import batch_convert
from deepseek_extractor_v2 import batch_extract
from analyzer_v2 import RiskAnalyzer


# ============================================================
# KONFIGURATSIYA
# ============================================================
INPUT_DIR             = "sud_fayllari"
TEXT_DIR              = "matnlar"
LISTING_METADATA_PATH = "listing_metadata.json"
PROGRESS_PATH         = "download_progress.json"  # YANGI: fallback manba
EXTRACTED_DATA_PATH   = "extracted_data.json"
RISK_ANALYSIS_PATH    = "risk_analysis.json"


def banner(text: str):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def get_api_key() -> str:
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("DEEPSEEK_API_KEY", "")


def ensure_listing_metadata() -> bool:
    """listing_metadata.json mavjudligini ta'minlash.
    Agar yo'q bo'lsa, download_progress.json dan tiklanadi.
    
    Returns:
        True — fayl mavjud yoki tiklandi
        False — hech qanday yo'l yo'q
    """
    if Path(LISTING_METADATA_PATH).exists():
        return True
    
    # Fallback: parser progress fayldan olamiz
    if not Path(PROGRESS_PATH).exists():
        return False
    
    print(f"   ⚠  {LISTING_METADATA_PATH} topilmadi — {PROGRESS_PATH} dan tiklanmoqda...")
    
    try:
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            progress = json.load(f)
        metadata = progress.get("metadata", [])
        
        if not metadata:
            print(f"   ✗ {PROGRESS_PATH} da metadata bo'sh")
            return False
        
        with open(LISTING_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"   ✓ Tiklandi: {len(metadata)} ta yozuv → {LISTING_METADATA_PATH}")
        return True
    except Exception as e:
        print(f"   ✗ Tiklab bo'lmadi: {e}")
        return False


def main(skip_ai: bool = False):
    start_time = time.time()
    
    banner("AI-AUDIT PIPELINE — TO'LIQ QUVVATLASH ZANJIRI")
    
    # ====================================================
    # 0. PRE-FLIGHT CHECKS
    # ====================================================
    print("Pre-flight checklist:\n")
    
    if not Path(INPUT_DIR).exists():
        print(f"   ✗ {INPUT_DIR}/ papkasi topilmadi")
        print("     Avval parser_v2.py ni ishlating")
        sys.exit(1)
    
    files = list(Path(INPUT_DIR).glob("*.doc")) + list(Path(INPUT_DIR).glob("*.pdf")) + \
            list(Path(INPUT_DIR).glob("*.docx"))
    print(f"   ✓ {INPUT_DIR}/: {len(files)} ta fayl")
    
    if not ensure_listing_metadata():
        print(f"\n   ✗ {LISTING_METADATA_PATH} ham, {PROGRESS_PATH} ham topilmadi")
        print("     Parser_v2.py ni ishga tushirib, hech bo'lmaganda 1 ta fayl yuklab oling")
        sys.exit(1)
    
    with open(LISTING_METADATA_PATH, encoding="utf-8") as f:
        listing = json.load(f)
    print(f"   ✓ {LISTING_METADATA_PATH}: {len(listing)} ta yozuv")
    
    # Sinxronlik tekshiruvi: nechta fayl, nechta metadata?
    if abs(len(files) - len(listing)) > 2:
        print(f"   ⚠  Diqqat: {len(files)} ta fayl, lekin {len(listing)} ta metadata")
        print(f"      (ba'zi yozuvlar mos kelmasligi mumkin)")
    
    if not skip_ai:
        api_key = get_api_key()
        if not api_key:
            print("   ✗ DEEPSEEK_API_KEY topilmadi (.env yoki environment'da)")
            sys.exit(1)
        print(f"   ✓ DeepSeek API kaliti mavjud (...{api_key[-4:]})")
    
    # ====================================================
    # 1. DOC → TEXT
    # ====================================================
    banner("BOSQICH 1/3: HUJJATLARNI MATNGA AYLANTIRISH")
    
    text_files = list(Path(TEXT_DIR).glob("*.txt")) if Path(TEXT_DIR).exists() else []
    
    if len(text_files) >= len(files):
        print(f"   ✓ {TEXT_DIR}/ papkasida {len(text_files)} ta matn fayli mavjud — o'tkazib yuborildi")
        print(f"     (Qaytadan konvertatsiya qilish uchun {TEXT_DIR}/ papkasini o'chiring)")
    else:
        manifest = batch_convert(INPUT_DIR, TEXT_DIR, "conversion_manifest.json")
        if manifest["stats"]["succeeded"] == 0:
            print("\n   ✗ Hech qanday fayl konvertatsiya qilinmadi")
            print("\n   YORDAM:")
            print("   - .doc fayllarni ochish uchun LibreOffice yoki MS Word kerak")
            print("   - LibreOffice (bepul): https://www.libreoffice.org/download/")
            print("   - Yoki Windows Word ishlatish: pip install pywin32")
            sys.exit(1)
    
    # ====================================================
    # 2. AI EXTRACTION
    # ====================================================
    banner("BOSQICH 2/3: AI BILAN MA'LUMOT AJRATISH (DeepSeek)")
    
    if skip_ai and Path(EXTRACTED_DATA_PATH).exists():
        print(f"   --skip-ai: mavjud {EXTRACTED_DATA_PATH} ishlatiladi")
        with open(EXTRACTED_DATA_PATH, encoding="utf-8") as f:
            extracted = json.load(f)
    else:
        extracted = batch_extract(
            text_dir=TEXT_DIR,
            listing_metadata_path=LISTING_METADATA_PATH,
            output_path=EXTRACTED_DATA_PATH,
            api_key=get_api_key(),
        )
    
    if not extracted:
        print("\n   ✗ AI extraction natijasi bo'sh")
        sys.exit(1)
    
    # ====================================================
    # 3. RISK ANALYSIS
    # ====================================================
    banner("BOSQICH 3/3: KORRUPSION RISK TAHLILI")
    
    analyzer = RiskAnalyzer(extracted)
    analyzer.analyze_all()
    output = analyzer.save(RISK_ANALYSIS_PATH)
    
    stats = output["statistics"]
    
    print("\n   STATISTIKA:")
    print(f"      Jami ishlar:        {stats['total_cases']}")
    print(f"      Yuqori xavf:        {stats['high_risk_cases']} ({stats['high_risk_pct']}%)")
    print(f"      O'rta xavf:         {stats['medium_risk_cases']}")
    print(f"      Mansabdor ishlari:  {stats['official_cases']}")
    print(f"      O'rtacha risk:      {stats['avg_risk_score']}")
    print(f"      Sudyalar:           {stats['judges_count']}")
    
    # ====================================================
    # YAKUN
    # ====================================================
    elapsed = time.time() - start_time
    
    banner(f"PIPELINE TUGADI ({elapsed:.0f} sekund)")
    
    print("Yaratilgan fayllar:")
    print(f"   ✓ {TEXT_DIR}/                   — matn fayllari")
    print(f"   ✓ {EXTRACTED_DATA_PATH}     — AI extraction natijasi")
    print(f"   ✓ {RISK_ANALYSIS_PATH}      — risk tahlili (asosiy natija)")
    print(f"   ✓ conversion_manifest.json — konvertatsiya hisoboti")
    
    print("\nKEYINGI QADAM:")
    print("   python create_dashboard.py")
    print("   (yoki dashboard.html ni brauzerda oching)\n")


if __name__ == "__main__":
    skip_ai = "--skip-ai" in sys.argv
    main(skip_ai=skip_ai)