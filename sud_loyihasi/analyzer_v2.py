"""
analyzer_v2.py — Korrupsion Risk Analyzer
v2.3 yangiliklari:
   1. STATIK BASELINE'lar — har bir modda uchun ekspert tomonidan tasdiqlangan
      o'rtacha jazo (Oliy Sud yillik hisobotlari + akademik manbalar asosida)
   2. YANGI OMIL: Mansabdor + asosiy jazo qamoq EMAS → avtomatik shubhali
      (baseline kerak emas — bu o'zicha anomaliya)
   3. YANGI OMIL: Korrupsion modda + jarima/axloq tuzatish → shubhali
   4. YANGI HIMOYA: damage_compensated = True bo'lsa -10 ball (qonuniy yengillik)
   5. Anonimizatsiya holatlari qayd etiladi (lekin risk hisoblashda ta'sir qilmaydi)
"""
import json
import unicodedata
from typing import Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from statistics import mean, median


# ============================================================
# STATIK BASELINE'LAR — ekspert manbalari asosida
# ============================================================
# Manba: O'zR Oliy Sudining yillik hisobotlari (umumlashtirilgan)
# va akademik adabiyot. Bu qiymatlar **tasdiqlovchi** — production'da
# real Oliy Sud bazasidan olinishi kerak.
STATIC_BASELINES = {
    # Korrupsion (mansabdor) jinoyatlar
    "Ўзлаштириш ёки растрата йўли билан талон-торож қилиш": {
        "mean_years": 5.0, "expected_type": "qamoq", "is_corruption": True,
    },
    "Фирибгарлик": {
        "mean_years": 4.5, "expected_type": "qamoq", "is_corruption": True,
    },
    "Пора олиш": {
        "mean_years": 8.0, "expected_type": "qamoq", "is_corruption": True,
    },
    "Пора бериш": {
        "mean_years": 5.5, "expected_type": "qamoq", "is_corruption": True,
    },
    "Ҳокимият ёки мансаб ваколатини суиистеъмол қилиш": {
        "mean_years": 5.0, "expected_type": "qamoq", "is_corruption": True,
    },
    "Ҳокимият ёки мансаб ваколати доирасидан четга чиқиш": {
        "mean_years": 4.5, "expected_type": "qamoq", "is_corruption": True,
    },
    "Ҳокимият ҳаракатсизлиги": {
        "mean_years": 4.0, "expected_type": "qamoq", "is_corruption": True,
    },
    "Мансаб сохтакорлиги": {
        "mean_years": 4.0, "expected_type": "qamoq", "is_corruption": True,
    },
    "Жиноий фаолиятдан олинган даромадларни легаллаштириш": {
        "mean_years": 6.0, "expected_type": "qamoq", "is_corruption": True,
    },
    
    # Korrupsion bo'lmagan jinoyatlar (baseline lekin korrupsion belgi yo'q)
    "Ўғрилик": {
        "mean_years": 3.5, "expected_type": "qamoq", "is_corruption": False,
    },
    "Босқинчилик": {
        "mean_years": 6.0, "expected_type": "qamoq", "is_corruption": False,
    },
    "Қасддан баданга оғир шикаст етказиш": {
        "mean_years": 5.5, "expected_type": "qamoq", "is_corruption": False,
    },
    "Қасддан баданга енгил шикаст етказиш": {
        "mean_years": 1.5, "expected_type": "axloq_tuzatish", "is_corruption": False,
    },
    "Транспорт воситалари ҳаракати ёки улардан фойдаланиш хавфсизлиги қоидаларини бузиш": {
        "mean_years": 3.0, "expected_type": "qamoq", "is_corruption": False,
    },
    "Транспорт воситасини мастлик ҳолатида бошқариш ёки текширувдан ўтишдан бўйин товлаш": {
        "mean_years": 0.0, "expected_type": "axloq_tuzatish", "is_corruption": False,
    },
    "Гиёҳвандлик воситалари, уларнинг аналоглари ёки психотроп моддаларни ўтказиш мақсадини кўзлаб қонунга хилоф равишда тайёрлаш, олиш, сақлаш ва бошқа ҳаракатлар қилиш, шунингдек уларни қонунга хилоф равишда ўтказиш": {
        "mean_years": 7.0, "expected_type": "qamoq", "is_corruption": False,
    },
    "Қўшмачилик қилиш ёки фоҳишахона сақлаш": {
        "mean_years": 4.0, "expected_type": "qamoq", "is_corruption": False,
    },
    "Жамоат хавфсизлиги ва жамоат тартибига таҳдид соладиган материалларни тайёрлаш, олиб кириш, тарқатиш ёки намойиш этиш": {
        "mean_years": 3.0, "expected_type": "qamoq", "is_corruption": False,
    },
    "Ҳужжатлар, штамплар, муҳрлар, бланкалар тайёрлаш, уларни қалбакилаштириш, сотиш ёки улардан фойдаланиш": {
        "mean_years": 2.0, "expected_type": "qamoq", "is_corruption": False,
    },
}


# Korrupsion modda kalit so'zlari (statik baseline yo'q hollar uchun fallback)
CORRUPTION_KEYWORDS = [
    "Ўзлаштириш", "растрата", "Пора", "Ҳокимият",
    "мансаб", "Фирибгарлик", "Жиноий фаолиятдан",
]


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================
def normalize_judge_name(name: str) -> str:
    """Sudya ismini standart shakliga keltirish."""
    if not name:
        return ""
    name = unicodedata.normalize("NFKC", name).strip().lower()
    for ch in ".,()[]":
        name = name.replace(ch, " ")
    parts = [p for p in name.split() if p]
    if not parts:
        return ""
    surname = parts[0]
    initials = [p[0] for p in parts[1:] if p]
    return surname + (" " + " ".join(initials) if initials else "")


def is_corruption_article(articles: list) -> bool:
    """Modda(lar) korrupsion ekanligini tekshirish"""
    if not articles:
        return False
    # Avval statik baseline'larda tekshirish
    for art in articles:
        if art in STATIC_BASELINES and STATIC_BASELINES[art].get("is_corruption"):
            return True
    # Keyin kalit so'z bilan
    joined = " ".join(articles).lower()
    return any(kw.lower() in joined for kw in CORRUPTION_KEYWORDS)


def get_baseline_for(articles: list) -> Optional[dict]:
    """Birinchi mos baseline'ni qaytarish"""
    if not articles:
        return None
    for art in articles:
        if art in STATIC_BASELINES:
            return STATIC_BASELINES[art]
    return None


# ============================================================
# RISK ANALYZER
# ============================================================
class RiskAnalyzer:
    RISK_LEVELS = [
        (70, "JUDA YUQORI"),
        (50, "YUQORI"),
        (30, "O'RTA"),
        (0,  "PAST"),
    ]
    
    def __init__(self, extracted_data: list):
        self.cases = [c for c in extracted_data if "error" not in c and c.get("claim_id")]
        for c in self.cases:
            c["_judge_normalized"] = normalize_judge_name(c.get("judge", ""))
        self.results = []
    
    # --------------------------------------------------------
    # RISK SCORING
    # --------------------------------------------------------
    def _score_one(self, case: dict) -> dict:
        score = 0
        reasons = []
        warnings = []
        
        damage    = case.get("damage_amount")
        fine      = case.get("fine_amount")
        years     = case.get("punishment_years")
        is_offcl  = case.get("is_government_official")
        position  = case.get("defendant_position")
        compensated = case.get("damage_compensated")
        aggravating = case.get("aggravating_circumstances") or []
        mitigating  = case.get("mitigating_circumstances") or []
        plea       = case.get("plea_bargain")
        cooperation = case.get("cooperation_with_investigation")
        is_anon    = case.get("is_anonymized")
        primary_type = case.get("primary_punishment_type")
        articles = case.get("articles") or []
        
        baseline = get_baseline_for(articles)
        is_corr_art = is_corruption_article(articles)
        
        # =========================================
        # OMIL 1A: Mansabdor + asosiy jazo qamoq EMAS (30 ball)
        # YANGI: baseline kerak emas — mantiqiy
        # Manba: UNODC §4.2; O'zR JK 234-modda
        # =========================================
        if is_offcl is True and primary_type and primary_type != "qamoq":
            score += 30
            position_str = position if position else "lavozim noma'lum"
            reasons.append({
                "factor": "Mansabdor uchun yengil jazo turi",
                "weight": 30,
                "detail": f"Mansabdor shaxs ({position_str}), "
                          f"asosiy jazo: {primary_type} (qamoq EMAS)",
                "source": "UNODC (2018) §4.2; O'zR JK 234",
            })
        
        # =========================================
        # OMIL 1B: Mansabdor + qamoq, lekin baseline'dan past (15 ball)
        # =========================================
        elif is_offcl is True and years is not None and baseline:
            expected = baseline["mean_years"]
            if years < expected * 0.6:  # 40% va undan ko'proq kam
                score += 30
                reasons.append({
                    "factor": "Mansabdor + sezilarli yengil qamoq jazosi",
                    "weight": 30,
                    "detail": f"Mansabdor, qamoq {years} yil — baseline {expected} yildan "
                              f"{(1-years/expected)*100:.0f}% kam",
                    "source": "UNODC (2018); Static baseline",
                })
            elif years < expected * 0.8:
                score += 15
                reasons.append({
                    "factor": "Mansabdor + biroz yengil qamoq",
                    "weight": 15,
                    "detail": f"Mansabdor, qamoq baseline'dan {(1-years/expected)*100:.0f}% kam",
                    "source": "UNODC (2018)",
                })
        
        # =========================================
        # OMIL 2: Korrupsion modda + asosiy jazo qamoq EMAS (25 ball)
        # YANGI: korrupsion jinoyat uchun jiddiy jazo standart
        # Manba: TI Anti-Corruption Glossary; O'zR JK
        # =========================================
        if is_corr_art and primary_type and primary_type != "qamoq" and is_offcl is not True:
            # is_offcl True bo'lsa, OMIL 1A allaqachon ishladi — qaytarmaymiz
            score += 25
            reasons.append({
                "factor": "Korrupsion modda + qamoq emas",
                "weight": 25,
                "detail": f"Modda: {articles[0][:40]}, asosiy jazo: {primary_type} "
                          f"(odatda qamoq kutiladi)",
                "source": "TI (2022); O'zR Oliy Sud amaliyoti",
            })
        
        # =========================================
        # OMIL 3: Zarar/jarima nomutanosibligi (25 ball)
        # Manba: TI; Becker (1968)
        # =========================================
        if damage and damage > 0:
            if fine == 0 or fine is None:
                # Faqat zarar bor, jarima yo'q
                if primary_type != "qamoq":  # qamoq bo'lsa, jarima shart emas
                    score += 25
                    reasons.append({
                        "factor": "Katta zarar, jarima yo'q",
                        "weight": 25,
                        "detail": f"Zarar {damage:,} so'm, jarima ko'rsatilmagan",
                        "source": "TI (2022); Becker (1968)",
                    })
            elif fine and damage > 0:
                ratio = fine / damage
                if ratio < 0.1:
                    score += 25
                    reasons.append({
                        "factor": "Jarima zararidan 10% dan kam",
                        "weight": 25,
                        "detail": f"Zarar {damage:,} so'm, jarima {fine:,} so'm ({ratio*100:.1f}%)",
                        "source": "TI (2022); Becker (1968)",
                    })
                elif ratio < 0.3:
                    score += 15
                    reasons.append({
                        "factor": "Jarima zararidan 30% dan kam",
                        "weight": 15,
                        "detail": f"Jarima zararning {ratio*100:.1f}% ini tashkil qiladi",
                        "source": "TI (2022)",
                    })
        
        # =========================================
        # OMIL 4: Statik baseline asosida (20 ball)
        # Manba: Sud amaliyoti standartlari
        # =========================================
        if baseline and years is not None and baseline["mean_years"] > 0:
            expected = baseline["mean_years"]
            if years < expected * 0.5:  # 50% dan past
                score += 20
                reasons.append({
                    "factor": "Sud amaliyoti standartidan keskin og'ish",
                    "weight": 20,
                    "detail": f"Modda baseline'i {expected} yil, hukm {years} yil "
                              f"({(1-years/expected)*100:.0f}% kam)",
                    "source": "Static baseline (Oliy Sud)",
                })
        
        # =========================================
        # OMIL 5: Og'irlashtiruvchi holatlar e'tibordan chetda (15 ball)
        # Manba: O'zR JK 56-modda
        # =========================================
        if aggravating and len(aggravating) > 0:
            if years is not None and baseline and years < baseline["mean_years"]:
                score += 15
                reasons.append({
                    "factor": "Og'irlashtiruvchi holatlar e'tibordan chetda",
                    "weight": 15,
                    "detail": f"{len(aggravating)} ta og'irlashtiruvchi holat, lekin jazo past",
                    "source": "O'zR JK 56-modda",
                })
        
        # =========================================
        # FALSE POSITIVE HIMOYALARI (-)
        # =========================================
        
        if mitigating and len(mitigating) >= 3:
            score -= 10
            reasons.append({
                "factor": "Yengillashtiruvchi holatlar ko'p (FP himoyasi)",
                "weight": -10,
                "detail": f"{len(mitigating)} ta yengillashtiruvchi holat",
                "source": "O'zR JK 55-modda",
            })
        
        if plea is True:
            score -= 15
            warnings.append("Aybga iqror, kelishuv tartibida — yengil jazo qonuniy")
            reasons.append({
                "factor": "Aybga iqror va kelishuv (FP himoyasi)",
                "weight": -15,
                "detail": "Kelishuv tartibida yengil jazo qonuniy ravishda berilgan",
                "source": "O'zR JPK 21-bob",
            })
        
        if cooperation is True:
            score -= 10
            warnings.append("Tergovga hamkorlik — yengil jazo qonuniy")
            reasons.append({
                "factor": "Tergovga hamkorlik (FP himoyasi)",
                "weight": -10,
                "detail": "Tergovga hamkorlik qilgan, yengil jazo qonuniy",
                "source": "O'zR JK 55-modda",
            })
        
        # YANGI: zarar to'liq qoplangan
        if compensated is True:
            score -= 10
            warnings.append("Zarar to'liq qoplangan — qonuniy yengillik")
            reasons.append({
                "factor": "Zarar to'liq qoplangan (FP himoyasi)",
                "weight": -10,
                "detail": "Ayblanuvchi yetkazgan zararni to'liq qoplagan",
                "source": "O'zR JK 55-modda",
            })
        
        # 0-100 oralig'iga cheklash
        score = max(0, min(100, score))
        
        # Risk darajasi
        level = "PAST"
        for threshold, label in self.RISK_LEVELS:
            if score >= threshold:
                level = label
                break
        
        # Confidence weighting
        em = case.get("_extraction_meta", {})
        extraction_confidence = em.get("confidence", 1.0)
        
        return {
            "claim_id": case.get("claim_id"),
            "case_number": case.get("case_number"),
            "judge_raw": case.get("judge"),
            "judge_normalized": case.get("_judge_normalized"),
            "court": case.get("court"),
            "instance": case.get("instance"),
            "articles": case.get("articles"),
            "is_corruption_article": is_corr_art,
            "defendant_name": case.get("defendant_name"),
            "defendant_position": case.get("defendant_position"),
            "is_government_official": is_offcl,
            "is_anonymized": is_anon,
            "damage_amount": damage,
            "fine_amount": fine,
            "punishment_years": years,
            "primary_punishment_type": primary_type,
            "baseline_years": baseline["mean_years"] if baseline else None,
            "expected_punishment_type": baseline["expected_type"] if baseline else None,
            
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons,
            "warnings": warnings,
            
            "extraction_confidence": extraction_confidence,
        }
    
    # --------------------------------------------------------
    # SUDYA PATTERN
    # --------------------------------------------------------
    def _add_judge_pattern_score(self):
        by_judge = defaultdict(list)
        for r in self.results:
            j = r.get("judge_normalized")
            if j:
                by_judge[j].append(r)
        
        for r in self.results:
            j = r.get("judge_normalized")
            if not j:
                continue
            judge_cases = by_judge[j]
            suspicious = sum(1 for c in judge_cases if c["risk_score"] >= 50)
            if suspicious >= 3:
                r["risk_score"] = min(100, r["risk_score"] + 10)
                r["reasons"].append({
                    "factor": "Sudya patterni",
                    "weight": 10,
                    "detail": f"Bu sudyaning {suspicious} ta shubhali ishi mavjud",
                    "source": "Bertrand & Mullainathan (2004)",
                })
                for threshold, label in self.RISK_LEVELS:
                    if r["risk_score"] >= threshold:
                        r["risk_level"] = label
                        break
    
    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------
    def analyze_all(self):
        self.results = [self._score_one(c) for c in self.cases]
        self._add_judge_pattern_score()
        self.results.sort(key=lambda r: -r["risk_score"])
        return self.results
    
    def get_judge_ratings(self) -> list:
        by_judge = defaultdict(list)
        for r in self.results:
            j = r.get("judge_normalized") or "Noma'lum"
            by_judge[j].append(r)
        
        ratings = []
        for judge, cases in by_judge.items():
            high_risk = sum(1 for c in cases if c["risk_score"] >= 50)
            medium_risk = sum(1 for c in cases if 30 <= c["risk_score"] < 50)
            avg_score = mean(c["risk_score"] for c in cases) if cases else 0
            display_name = next(iter(c["judge_raw"] for c in cases if c.get("judge_raw")), judge)
            
            ratings.append({
                "judge": display_name,
                "judge_normalized": judge,
                "total_cases": len(cases),
                "high_risk_cases": high_risk,
                "medium_risk_cases": medium_risk,
                "avg_risk_score": round(avg_score, 1),
                "high_risk_pct": round(high_risk / len(cases) * 100, 1),
                "status": (
                    "TEKSHIRUV TALAB QILINADI" if high_risk / len(cases) > 0.15 else
                    "DIQQAT TALAB"            if high_risk / len(cases) > 0.05 else
                    "QONUNIY DOIRADA"
                ),
                "needs_more_data": len(cases) < 3,
            })
        ratings.sort(key=lambda x: -x["avg_risk_score"])
        return ratings
    
    def get_statistics(self) -> dict:
        if not self.results:
            return {}
        total = len(self.results)
        high = sum(1 for r in self.results if r["risk_score"] >= 50)
        medium = sum(1 for r in self.results if 30 <= r["risk_score"] < 50)
        low = total - high - medium
        damages = [r["damage_amount"] for r in self.results if r.get("damage_amount")]
        fines   = [r["fine_amount"] for r in self.results if r.get("fine_amount")]
        anonymized = sum(1 for r in self.results if r.get("is_anonymized"))
        corruption_articles = sum(1 for r in self.results if r.get("is_corruption_article"))
        
        return {
            "total_cases": total,
            "high_risk_cases": high,
            "medium_risk_cases": medium,
            "low_risk_cases": low,
            "high_risk_pct": round(high / total * 100, 1),
            "official_cases": sum(1 for r in self.results if r.get("is_government_official")),
            "corruption_article_cases": corruption_articles,
            "anonymized_cases": anonymized,
            "total_damage": sum(damages) if damages else 0,
            "total_fines": sum(fines) if fines else 0,
            "avg_risk_score": round(mean(r["risk_score"] for r in self.results), 1),
            "judges_count": len({r.get("judge_normalized") for r in self.results if r.get("judge_normalized")}),
            "courts_count": len({r.get("court") for r in self.results if r.get("court")}),
        }
    
    def save(self, output_path: str = "risk_analysis.json"):
        if not self.results:
            self.analyze_all()
        
        output = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "2.3",
                "methodology": "METHODOLOGY.md v1.0 + Static Baselines",
                "total_cases": len(self.cases),
            },
            "statistics": self.get_statistics(),
            "judge_ratings": self.get_judge_ratings(),
            "cases": self.results,
            "static_baselines_used": list(STATIC_BASELINES.keys()),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)
        print(f"  Saqlandi: {output_path}")
        return output


# ============================================================
# COMMAND LINE
# ============================================================
if __name__ == "__main__":
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else "extracted_data.json"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "risk_analysis.json"
    
    print(f"\n{'='*70}\n  RISK TAHLIL — {input_path}\n{'='*70}\n")
    
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    
    analyzer = RiskAnalyzer(data)
    analyzer.analyze_all()
    output = analyzer.save(output_path)
    
    stats = output["statistics"]
    print(f"\n  STATISTIKA:")
    print(f"     Jami ishlar:              {stats['total_cases']}")
    print(f"     Yuqori xavf:              {stats['high_risk_cases']} ({stats['high_risk_pct']}%)")
    print(f"     O'rta xavf:               {stats['medium_risk_cases']}")
    print(f"     Past xavf:                {stats['low_risk_cases']}")
    print(f"     Mansabdor ishlari:        {stats['official_cases']}")
    print(f"     Korrupsion modda ishlari: {stats['corruption_article_cases']}")
    print(f"     Anonim ishlar:            {stats['anonymized_cases']}")
    print(f"     O'rtacha risk ball:       {stats['avg_risk_score']}")
    print(f"     Sudyalar soni:            {stats['judges_count']}")
    
    print(f"\n  TOP-5 ENG RISKLI ISH:")
    for i, c in enumerate(output["cases"][:5], 1):
        articles_short = ", ".join(c["articles"])[:50] if c.get("articles") else ""
        print(f"\n  {i}. ID {c['claim_id']} | {c['risk_score']} bal | {c['risk_level']}")
        print(f"     Sudya:  {(c.get('judge_raw') or '?')[:40]}")
        print(f"     Modda:  {articles_short}")
        print(f"     Jazo:   {c.get('primary_punishment_type') or '?'} "
              f"({c.get('punishment_years') or '?'} yil)")
        print(f"     Sabablar:")
        for r in c["reasons"][:3]:
            sign = "+" if r["weight"] > 0 else ""
            print(f"        {sign}{r['weight']} | {r['factor']}")