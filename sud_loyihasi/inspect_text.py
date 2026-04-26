"""
inspect_text.py — Matn fayllarida jazo va jarima haqida so'zlar bor-yo'qligini tekshirish

Maqsad: agar punishment_years va fine_amount 0% topilgan bo'lsa,
sabab nima ekanligini bilish:
   - Matnda yo'q (manba muammosi) → boshqa strategiya kerak
   - Matnda bor (DeepSeek topa olmadi) → prompt yaxshilash kerak

ISHLATISH:
    python inspect_text.py
    python inspect_text.py matnlar/
"""
import re
import sys
from pathlib import Path
from collections import Counter

# Kalit so'zlar (kirill uzbek + rus)
PATTERNS = {
    "QAMOQ JAZOSI": [
        r"озодликдан\s+маҳрум",
        r"озодликдан\s+махрум", 
        r"лишен[ия]+\s+свобод",
        r"ozodlikdan\s+mahrum",
    ],
    "AXLOQ TUZATISH": [
        r"ахлоқ\s+тузатиш",
        r"исправительн",
        r"axloq\s+tuzatish",
    ],
    "JARIMA": [
        r"жарима",
        r"штраф",
        r"jarima",
    ],
    "SHARTLI": [
        r"шартли",
        r"условн",
        r"shartli",
    ],
    "MAJBURIY ISH": [
        r"мажбурий\s+меҳнат",
        r"мажбурий\s+ишлар",
        r"majburiy\s+ish",
    ],
    "OZODLIKNI CHEKLASH": [
        r"озодликни\s+чеклаш",
        r"ограничени[ея]+\s+свобод",
    ],
    "MUDDATLAR (yil/oy/kun)": [
        r"\d+\s*йил",
        r"\d+\s*ой",
        r"\d+\s*кун",
        r"\d+\s+(йилга|йили|ойлик)",
    ],
    "PUL SUMMA (so'm)": [
        r"\d{1,3}[\s.,]\d{3}[\s.,]\d{3}\s*сўм",  # 1.000.000 so'm
        r"\d+\s*минг\s*сўм",
        r"\d+\s*миллион",
        r"\d+\s*млн",
    ],
    "MANSABDOR / LAVOZIM": [
        r"мансабдор",
        r"раҳбар",
        r"бошлиқ",
        r"директор",
        r"мудир",
        r"ҳисобчи",  # buxgalter
        r"бошқарувчи",
        r"вакили",
        r"должностн",
    ],
    "AYBNI TAN OLISH (kelishuv)": [
        r"айбини\s+тан\s+олган",
        r"айбини\s+бўйнига\s+олган",
        r"чин\s+кўнгилдан\s+пушаймон",
    ],
}


def search_patterns(text: str) -> dict:
    """Matn ichida kalit so'zlarni qidirish"""
    found = {}
    for category, patterns in PATTERNS.items():
        matches = []
        for pat in patterns:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                # Atrofini ham olib chiqish (kontekst)
                start = max(0, m.start() - 30)
                end = min(len(text), m.end() + 50)
                context = text[start:end].replace("\n", " ").strip()
                matches.append(context[:100])
                if len(matches) >= 2:
                    break
            if len(matches) >= 2:
                break
        if matches:
            found[category] = matches
    return found


def analyze_file(filepath: Path) -> dict:
    """Bitta faylni tahlil qilish"""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e)}
    
    return {
        "size": len(text),
        "lines": text.count("\n"),
        "found": search_patterns(text),
    }


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "matnlar"
    folder_path = Path(folder)
    
    if not folder_path.exists():
        print(f"✗ {folder} papkasi topilmadi")
        sys.exit(1)
    
    files = sorted(folder_path.glob("*.txt"))
    if not files:
        print(f"✗ {folder} da .txt fayllar yo'q")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"  MATN FAYLLARI TAHLILI ({len(files)} ta fayl)")
    print(f"{'='*70}\n")
    
    # Umumiy statistika
    category_count = Counter()
    detail = []
    
    for filepath in files:
        result = analyze_file(filepath)
        if "error" in result:
            print(f"  ✗ {filepath.name}: {result['error']}")
            continue
        
        for category in result["found"]:
            category_count[category] += 1
        
        detail.append({"file": filepath.name, **result})
    
    # ====================================================
    # 1. UMUMIY HISOBOT
    # ====================================================
    print(f"  {'KATEGORIYA':<35} {'TOPILGAN':<15} {'%':<8}")
    print(f"  {'-'*35} {'-'*15} {'-'*8}")
    
    for category in PATTERNS.keys():
        cnt = category_count.get(category, 0)
        pct = cnt / len(files) * 100 if files else 0
        bar = "█" * int(pct / 5)
        marker = "✓" if pct >= 70 else "⚠" if pct >= 30 else "✗"
        print(f"  {marker} {category:<33} {cnt:>2}/{len(files):<2} ({pct:>5.1f}%)  {bar}")
    
    # ====================================================
    # 2. XULOSA — MUAMMO QAERDA?
    # ====================================================
    print(f"\n{'='*70}")
    print(f"  XULOSA")
    print(f"{'='*70}\n")
    
    qamoq_pct = category_count.get("QAMOQ JAZOSI", 0) / len(files) * 100
    jarima_pct = category_count.get("JARIMA", 0) / len(files) * 100
    muddat_pct = category_count.get("MUDDATLAR (yil/oy/kun)", 0) / len(files) * 100
    
    if qamoq_pct < 30 and jarima_pct < 30:
        print("  📌 MANBA MUAMMOSI:")
        print("     Matnlarda jazo va jarima haqida so'zlar JUDA KAM uchraydi.")
        print("     Demak hujjatlar to'liq sud qarori EMAS — apellyatsiya ajrimi,")
        print("     ish bekor qilish, yoki qisman hujjat bo'lishi mumkin.")
        print("     ⇒ Yechim: filterni 'instance=1' va 'Айблов ҳукми' dan boshqacha qilish")
    elif muddat_pct >= 70 and qamoq_pct >= 50:
        print("  📌 PROMPT MUAMMOSI:")
        print("     Matnlarda jazo va muddatlar haqida ma'lumot bor,")
        print("     lekin DeepSeek ularni topa olmadi.")
        print("     ⇒ Yechim: prompt'ni yaxshilash, ko'proq misol berish")
    else:
        print("  📌 ARALASH MUAMMO:")
        print("     Hujjatlarning bir qismida jazo bor, boshqalarida yo'q.")
        print("     ⇒ Yechim: hujjat sifatini classification + prompt yaxshilash")
    
    # ====================================================
    # 3. NAMUNA: birinchi 3 ta fayl uchun batafsil
    # ====================================================
    print(f"\n{'='*70}")
    print(f"  NAMUNA: birinchi 3 ta fayl batafsil")
    print(f"{'='*70}")
    
    for d in detail[:3]:
        print(f"\n  📄 {d['file']} ({d['size']:,} belgi, {d['lines']} qator)")
        if d["found"]:
            for category, matches in d["found"].items():
                print(f"     ✓ {category}:")
                for m in matches[:1]:
                    print(f"        \"{m}\"")
        else:
            print(f"     ✗ Hech qanday kalit so'z topilmadi")
    
    print()


if __name__ == "__main__":
    main()
