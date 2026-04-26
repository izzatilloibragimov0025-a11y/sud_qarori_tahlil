"""
inspect_data.py — DeepSeek extraction natijalarini tahlil qilish

Bu skript extracted_data.json faylini o'qib:
1. Har bir maydon uchun topilish foizini ko'rsatadi
2. Asosiy maydonlar (mansabdor, zarar, jarima, jazo) taqsimotini chiqaradi
3. Sudyalar va sudlar bo'yicha statistika
4. Risk score 0 bo'lishining sabablarini tahlil qiladi

ISHLATISH:
    python inspect_data.py
    python inspect_data.py extracted_data.json risk_analysis.json
"""
import sys
import json
from pathlib import Path
from collections import Counter


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def banner(text):
    print(f"\n{'='*70}\n  {text}\n{'='*70}")


def field_coverage(data, fields):
    """Har bir maydon uchun topilish foizi"""
    total = len(data)
    coverage = {}
    
    for f in fields:
        non_empty = 0
        for item in data:
            if "error" in item:
                continue
            v = item.get(f)
            # Topilgan deb hisoblash mezonlari
            if v is None:
                continue
            if isinstance(v, str) and not v.strip():
                continue
            if isinstance(v, list) and not v:
                continue
            non_empty += 1
        coverage[f] = (non_empty, total, non_empty / total * 100 if total else 0)
    return coverage


def main():
    extracted_path = sys.argv[1] if len(sys.argv) > 1 else "extracted_data.json"
    risk_path     = sys.argv[2] if len(sys.argv) > 2 else "risk_analysis.json"
    
    if not Path(extracted_path).exists():
        print(f"✗ {extracted_path} topilmadi")
        sys.exit(1)
    
    extracted = load_json(extracted_path)
    valid = [c for c in extracted if "error" not in c]
    
    banner(f"DIAGNOSTIKA: {extracted_path}")
    print(f"  Jami yozuvlar: {len(extracted)}")
    print(f"  Valid:         {len(valid)}")
    print(f"  Xatolar:       {len(extracted) - len(valid)}")
    
    # ====================================================
    # 1. MAYDONLAR TOPILISHI
    # ====================================================
    banner("1. MAYDONLAR TOPILISHI (DeepSeek nima topdi)")
    
    fields_to_check = [
        # Listing'dan kelishi kerak
        ("claim_id",                "Listing"),
        ("judge",                   "Listing"),
        ("court",                   "Listing"),
        ("articles",                "Listing"),
        # AI topishi kerak
        ("defendant_name",          "AI"),
        ("defendant_position",      "AI"),
        ("is_government_official",  "AI"),
        ("damage_amount",           "AI"),
        ("damage_compensated",      "AI"),
        ("punishment_years",        "AI"),
        ("fine_amount",             "AI"),
        ("aggravating_circumstances", "AI"),
        ("mitigating_circumstances", "AI"),
        ("plea_bargain",            "AI"),
        ("cooperation_with_investigation", "AI"),
    ]
    
    coverage = field_coverage(valid, [f for f, _ in fields_to_check])
    
    print(f"\n  {'Maydon':<35} {'Manba':<10} {'Topildi':<15}")
    print(f"  {'-'*35} {'-'*10} {'-'*15}")
    for field, source in fields_to_check:
        n, t, pct = coverage[field]
        bar = "█" * int(pct / 5)
        marker = "✓" if pct >= 70 else "⚠" if pct >= 30 else "✗"
        print(f"  {marker} {field:<33} {source:<10} {n:>2}/{t:<2} ({pct:>5.1f}%)  {bar}")
    
    # ====================================================
    # 2. ASOSIY QIYMATLAR TAQSIMOTI
    # ====================================================
    banner("2. RISK ANALIZIGA MUHIM MAYDONLAR")
    
    # Mansabdor
    officials = sum(1 for c in valid if c.get("is_government_official") is True)
    not_officials = sum(1 for c in valid if c.get("is_government_official") is False)
    unknown_official = len(valid) - officials - not_officials
    print(f"\n  is_government_official:")
    print(f"     Mansabdor (true):   {officials}")
    print(f"     Mansabdor emas:     {not_officials}")
    print(f"     Aniqlanmadi (null): {unknown_official}")
    
    # Lavozimlar
    positions = [c.get("defendant_position") for c in valid if c.get("defendant_position")]
    if positions:
        print(f"\n  Topilgan lavozimlar ({len(positions)} ta):")
        for p in positions[:10]:
            print(f"     - {p}")
    
    # Zarar
    damages = [c.get("damage_amount") for c in valid if c.get("damage_amount")]
    if damages:
        print(f"\n  Zarar (damage_amount):")
        print(f"     Topilgan: {len(damages)}/{len(valid)}")
        print(f"     Eng kam:  {min(damages):>15,} so'm")
        print(f"     Eng ko'p: {max(damages):>15,} so'm")
        print(f"     O'rtacha: {sum(damages)//len(damages):>15,} so'm")
    else:
        print(f"\n  ⚠  Zarar hech qaerda topilmadi")
    
    # Jarima
    fines = [c.get("fine_amount") for c in valid if c.get("fine_amount")]
    if fines:
        print(f"\n  Jarima (fine_amount):")
        print(f"     Topilgan: {len(fines)}/{len(valid)}")
        print(f"     Eng kam:  {min(fines):>15,} so'm")
        print(f"     Eng ko'p: {max(fines):>15,} so'm")
    else:
        print(f"\n  ⚠  Jarima hech qaerda topilmadi")
    
    # Jazo (qamoq yili)
    punishments = [c.get("punishment_years") for c in valid if c.get("punishment_years")]
    if punishments:
        print(f"\n  Jazo (punishment_years):")
        print(f"     Topilgan: {len(punishments)}/{len(valid)}")
        print(f"     Eng kam:  {min(punishments)} yil")
        print(f"     Eng ko'p: {max(punishments)} yil")
        print(f"     Qiymatlar: {sorted(punishments)}")
    else:
        print(f"\n  ⚠  Jazo hech qaerda topilmadi (analyzer baseline qila olmaydi)")
    
    # ====================================================
    # 3. MODDALAR TAQSIMOTI
    # ====================================================
    banner("3. MODDALAR TAQSIMOTI (baseline imkoniyati)")
    
    article_counter = Counter()
    for c in valid:
        for art in c.get("articles", []) or []:
            article_counter[art] += 1
    
    print(f"\n  Eng ko'p uchragan moddalar (baseline uchun >=3 ta kerak):")
    for art, cnt in article_counter.most_common(10):
        marker = "✓" if cnt >= 3 else "⚠"
        baseline_status = "baseline mavjud" if cnt >= 3 else "yetarli emas"
        print(f"     {marker} [{cnt:>2}x] {art[:60]:<60} ({baseline_status})")
    
    eligible_articles = sum(1 for c in article_counter.values() if c >= 3)
    total_articles = len(article_counter)
    print(f"\n  Baseline qilish mumkin bo'lgan moddalar: {eligible_articles}/{total_articles}")
    
    # ====================================================
    # 4. RISK ANALIZ DIAGNOSTIKASI
    # ====================================================
    if Path(risk_path).exists():
        banner("4. RISK ANALIZ NIMA UCHUN 0 BERDI?")
        risk_data = load_json(risk_path)
        baselines = risk_data.get("punishment_baselines", {})
        
        print(f"\n  Hisoblangan baseline'lar:")
        valid_baselines = {a: b for a, b in baselines.items() if b.get("mean") is not None}
        if valid_baselines:
            for art, b in valid_baselines.items():
                print(f"     ✓ {art[:50]:<50} mean={b['mean']} yil (n={b['n']})")
        else:
            print(f"     ✗ Hech qanday baseline hisoblanmadi")
            print(f"        (har bir moddada <3 ta ish bor)")
        
        # Nima uchun OMIL 1 ishlamadi
        print(f"\n  OMIL 1 (Mansabdor + yengil jazo, 30 ball):")
        official_with_punishment = sum(1 for c in valid 
                                       if c.get("is_government_official") is True 
                                       and c.get("punishment_years"))
        print(f"     Mansabdor + jazo bor: {official_with_punishment} ta ish")
        print(f"     ⇒ Bu omil 0 marta tetiklandi")
        
        # OMIL 2
        print(f"\n  OMIL 2 (Zarar/jarima nomutanosibligi, 25 ball):")
        damage_no_fine = sum(1 for c in valid 
                            if c.get("damage_amount") and not c.get("fine_amount"))
        print(f"     Zarar bor, jarima yo'q: {damage_no_fine} ta ish")
        if damage_no_fine > 0:
            print(f"     ⇒ Bu omil tetiklanishi kerak edi!")
    
    # ====================================================
    # 5. NAMUNA YOZUV
    # ====================================================
    banner("5. NAMUNA YOZUV (birinchi ish)")
    
    if valid:
        sample = valid[0]
        # Maxsus maydonlarni ko'rsatish
        for key in ["claim_id", "case_number", "judge", "court", 
                   "defendant_name", "defendant_position",
                   "is_government_official", "damage_amount", 
                   "fine_amount", "punishment_years",
                   "aggravating_circumstances", "mitigating_circumstances",
                   "plea_bargain"]:
            v = sample.get(key)
            print(f"     {key:<32}: {v}")
    
    print()


if __name__ == "__main__":
    main()
