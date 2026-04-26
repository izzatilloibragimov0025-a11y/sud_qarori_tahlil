"""
deepseek_extractor_v2.py — Tahsillangan AI extraction
v2.2 yangiliklari:
   1. Matn limit 8000 → 30000 belgi (sud qarorlarining oxiri ham yetib boradi)
   2. Smart chunking — agar matn 30K dan uzun bo'lsa, boshi+oxiri yuboriladi
   3. Yaxshilangan prompt — jarima ham asosiy jazo bo'lishi mumkin
   4. Mansabdor definition kengroq (O'zR JK 234-modda)
   5. Anonimizatsiya holatlarini qabul qilish

ISHLATISH:
    from deepseek_extractor_v2 import DeepSeekExtractor, batch_extract
"""
import os
import json
import time
from pathlib import Path
from openai import OpenAI


# ============================================================
# JSON Schema validation uchun
# ============================================================
EXPECTED_FIELDS = {
    "case_id":        {"type": (str, type(None))},
    "decision_date":  {"type": (str, type(None))},
    "defendant_name":          {"type": (str, type(None))},
    "defendant_position":      {"type": (str, type(None))},
    "is_government_official":  {"type": (bool, type(None))},
    "damage_amount":           {"type": (int, float, type(None)), "min": 0},
    "damage_compensated":      {"type": (bool, type(None))},
    "punishment_years":        {"type": (int, float, type(None)), "min": 0, "max": 50},
    "fine_amount":             {"type": (int, float, type(None)), "min": 0},
    "additional_punishment":   {"type": (list, type(None))},
    "mitigating_circumstances":   {"type": (list, type(None))},
    "aggravating_circumstances":  {"type": (list, type(None))},
    "plea_bargain":            {"type": (bool, type(None))},
    "cooperation_with_investigation": {"type": (bool, type(None))},
    "primary_punishment_type": {"type": (str, type(None))},  # YANGI: asosiy jazo turi
    "is_anonymized":           {"type": (bool, type(None))},  # YANGI
}


# ============================================================
# CHUNKING — uzun matnlarni aqlli kesib olish
# ============================================================
MAX_TEXT_LEN = 30000  # 30K belgi (~10K token)


def smart_chunk(text: str) -> str:
    """Agar matn uzun bo'lsa, eng muhim qismlarini olish.
    
    Sud qarorlarida:
    - Boshi: ish raqami, sana, sud, ayblanuvchi (taxminan 5K belgi)
    - O'rtasi: faktlar va dalillar (kerak emas darajada katta)
    - Oxiri: HUKM qismi — jazo, jarima, asoslar (eng muhim)
    """
    if len(text) <= MAX_TEXT_LEN:
        return text
    
    head_size = 8000
    tail_size = 20000
    
    head = text[:head_size]
    tail = text[-tail_size:]
    
    return f"{head}\n\n[...faktlar va dalillar qisqartirildi...]\n\n{tail}"


class DeepSeekExtractor:
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        if not api_key:
            raise ValueError("DeepSeek API kaliti kerak")
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model
    
    # --------------------------------------------------------
    # PROMPT — yaxshilangan, sud qarorlari uchun moslashtirilgan
    # --------------------------------------------------------
    def _build_prompt(self, text: str, meta: dict) -> str:
        meta = meta or {}
        known_judge   = (meta.get("judge") or "").strip()
        known_court   = (meta.get("dbName") or "").strip()
        known_case    = (meta.get("caseNumber") or "").strip()
        known_articles = meta.get("claimArticles") or []
        
        context_lines = []
        if known_judge:
            context_lines.append(f"- Sudya: {known_judge}")
        if known_court:
            context_lines.append(f"- Sud: {known_court}")
        if known_case:
            context_lines.append(f"- Ish raqami: {known_case}")
        if known_articles:
            context_lines.append(f"- Moddalar: {', '.join(known_articles)}")
        context = "\n".join(context_lines) if context_lines else "(yo'q)"
        
        # Smart chunking
        text = smart_chunk(text)
        
        return f"""Quyidagi O'zbekiston sud qarori (jinoiy ish) matnidan strukturalangan ma'lumot ajratib ber.

KONTEKSTUAL MA'LUMOT (allaqachon bizda bor):
{context}

DIQQAT! O'ZBEKISTON SUD AMALIYOTI XUSUSIYATLARI:
1. Asosiy jazo TURLARI (har biri alohida modda):
   - "озодликдан маҳрум қилиш" → qamoq jazosi (punishment_years ga raqam)
   - "ахлоқ тузатиш ишлари" → axloq tuzatish (punishment_years EMAS)
   - "озодликни чеклаш" → ozodlikni cheklash (punishment_years EMAS)
   - "жарима" → JARIMA (fine_amount ga raqam)
   - "мажбурий жамоат ишлари" → majburiy ishlar (punishment_years EMAS)

2. Bir hukmda asosiy jazo + qo'shimcha jazo bo'lishi mumkin:
   - "6.512.000 сўм жарима + 1 йилга лавозим эгаллаш ҳуқуқидан маҳрум" 
     → fine_amount=6512000, additional_punishment=["1 yil lavozimdan mahrum qilish"]
   - "5 йил озодликдан маҳрум + мол-мулкини мусодара қилиш"
     → punishment_years=5, additional_punishment=["mol-mulkni musodara qilish"]

3. Shartli hukm ham qamoq deb hisoblanadi:
   - "3 йил шартли" → punishment_years=3 (lekin matn'da "shartli" deb yozilsa qayd et)

4. ANONIMIZATSIYA: ba'zi qarorlarda F.I.O. yashirilgan (X.X.X., Ф.И.Ш., ваколатли вакил va h.k.).
   Bunday holatlarda: defendant_name = "ANONYMIZED" deb belgilang. is_anonymized = true.

KERAKLI MA'LUMOTLAR (JSON formatda qaytar):

1. case_id — ish raqami (kontekstda bor bo'lsa, shuni qaytar)
2. decision_date — qaror sanasi (YYYY-MM-DD yoki null)
3. defendant_name — ayblanuvchi F.I.O. (yashirilgan bo'lsa "ANONYMIZED")
4. defendant_position — lavozim (matn'da bor bo'lsa: "ҳисобчи", "директор", "мудир", "раҳбар", va h.k.)
5. is_government_official — Mansabdor shaxsmi? (true/false). 
   O'zR JK 234-moddasi bo'yicha:
   TRUE: davlat tashkilotida rahbarlik (mudir, direktor, rais, boshliq, dekan, bosh shifokor),
         davlat boshqaruv organlarida (vazirlik, hokimlik), pravookhrana (politsiya, prokuratura,
         sud, ICHKI ISHLAR), davlat ta'lim/sog'liq/moliya tashkilotlarida lavozim
   FALSE: tadbirkor (xususiy), ishchi, ishsiz, pensioner, oddiy fuqaro lavozimsiz
   MISOL: "Янгиер кўмир мудири" → TRUE, "буxgalter" → matnda davlat tashkiloti bo'lsa TRUE
6. damage_amount — yetkazilgan moddiy zarar (raqam, so'mda. "26.841.200 сўм" → 26841200)
7. damage_compensated — zarar qoplangan? (true/false/null)
   "зарарни тўлиқ қоплаганлиги" yoki "зарарни тўлади" → true
8. punishment_years — OZODLIKDAN MAHRUM QILISH muddati yillarda (raqam, NULL agar yo'q)
   - "5 йилга озодликдан маҳрум" → 5
   - "3 йил 6 ой озодликдан маҳрум" → 3.5
   - "ахлоқ тузатиш ишлари" → null
   - "жарима жазоси" (asosiy) → null
9. fine_amount — JARIMA miqdori (so'mda, raqam yoki null)
   - "6.512.000 сўм миқдорида жарима жазоси тайинланган" → 6512000
   - "энг кам иш ҳақининг 50 баравари жарима" → mlni hisoblang yoki null
10. primary_punishment_type — Asosiy jazo turi (kalit so'z):
    "qamoq" / "jarima" / "axloq_tuzatish" / "ozodlikni_cheklash" / "shartli_qamoq" / "boshqa"
11. additional_punishment — qo'shimcha jazolar ro'yxati
    Misollar: ["1 yil lavozimdan mahrum qilish"], ["mol-mulkdan mahrum qilish"]
12. mitigating_circumstances — yengillashtiruvchi holatlar (matnda topilganlar)
13. aggravating_circumstances — og'irlashtiruvchi holatlar
14. plea_bargain — Aybga iqror, kelishuv tartibida ishlangani aniqmi? (true/false/null)
    "айбини бўйнига олган", "айбини тан олган", "пушаймон бўлган" → true
15. cooperation_with_investigation — Tergovga hamkorlik (true/false/null)
    "тергов давомида ёрдам берган", "ҳамкорлик қилган" → true
16. is_anonymized — F.I.O. yashirilganmi? (true agar ayblanuvchi nomi X.X.X. yoki Ф.И.Ш.)

QAT'IY QOIDALAR:
- Faqat JSON qaytar, hech qanday tushuntirish yozma
- Pul: faqat raqam, "so'm" so'zisiz
- Topilmagan maydonlar uchun: null
- Hukm qismi (HUKM ҚИЛДИ / Ҳ У К М) qarorning OXIRIDA bo'ladi — albatta o'sha qismni o'qing!

SUD QARORI MATNI:
{text}

JSON JAVOB:"""
    
    # --------------------------------------------------------
    # API chaqiruvi
    # --------------------------------------------------------
    def _call_api(self, prompt: str, max_retries: int = 2) -> dict:
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system",
                         "content": "Siz O'zbekiston sud qarorlaridan strukturalangan ma'lumot ajratuvchi mutaxassissiz. "
                                    "Hujjatning HUKM qismiga (oxirgi qism) maxsus e'tibor bering. "
                                    "Faqat JSON qaytaring, hech qanday tushuntirish yozmang."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                )
                
                raw = response.choices[0].message.content.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.startswith("```"):
                    raw = raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
                
                data = json.loads(raw)
                data["__tokens"] = response.usage.total_tokens
                return data
            except json.JSONDecodeError as e:
                last_error = f"JSON parse: {e}"
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
        return {"__error": last_error}
    
    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------
    def _validate(self, data: dict) -> tuple[bool, list, float]:
        issues = []
        valid_fields = 0
        total_fields = len(EXPECTED_FIELDS)
        
        for field, schema in EXPECTED_FIELDS.items():
            value = data.get(field)
            expected_types = schema["type"]
            if not isinstance(value, expected_types):
                issues.append(f"{field}: noto'g'ri tip ({type(value).__name__})")
                continue
            if value is not None and isinstance(value, (int, float)):
                if "min" in schema and value < schema["min"]:
                    issues.append(f"{field}: qiymat juda kichik ({value})")
                    continue
                if "max" in schema and value > schema["max"]:
                    issues.append(f"{field}: qiymat juda katta ({value})")
                    continue
            valid_fields += 1
        
        # Mantiqiy tekshiruvlar
        if data.get("damage_amount") and data.get("fine_amount"):
            if data["fine_amount"] > data["damage_amount"] * 100:
                issues.append("fine_amount damage_amount dan 100x ko'p — shubhali")
        if data.get("punishment_years") is not None:
            if data["punishment_years"] > 30:
                issues.append(f"punishment_years juda katta: {data['punishment_years']}")
        
        # YANGI: agar barcha jazo maydonlari null bo'lsa, lekin matn katta bo'lsa — ogohlantirish
        if (data.get("punishment_years") is None and 
            data.get("fine_amount") is None and 
            not data.get("primary_punishment_type")):
            issues.append("Hech qanday jazo topilmadi — matnni qayta tekshiring")
        
        confidence = valid_fields / total_fields
        is_valid = confidence >= 0.7
        return is_valid, issues, confidence
    
    # --------------------------------------------------------
    # ASOSIY EXTRACTION
    # --------------------------------------------------------
    def extract(self, text: str = None, text_path: str = None,
                listing_metadata: dict = None) -> dict:
        if text is None and text_path:
            try:
                text = Path(text_path).read_text(encoding="utf-8")
            except Exception as e:
                return {"__error": f"Matn o'qib bo'lmadi: {e}"}
        
        if not text or len(text) < 100:
            return {"__error": "Matn juda qisqa yoki bo'sh"}
        
        meta = listing_metadata or {}
        
        prompt = self._build_prompt(text, meta)
        result = self._call_api(prompt)
        
        if "__error" in result:
            return result
        
        tokens_used = result.pop("__tokens", 0)
        is_valid, issues, confidence = self._validate(result)
        
        merged = {
            "claim_id": meta.get("claimId"),
            "case_number": meta.get("caseNumber") or result.get("case_id"),
            "judge": meta.get("judge"),
            "court": meta.get("dbName"),
            "instance": meta.get("instance"),
            "articles": meta.get("claimArticles") or [],
            "document_type": meta.get("claimDocumentType") or [],
            
            "decision_date": result.get("decision_date"),
            "defendant_name": result.get("defendant_name"),
            "defendant_position": result.get("defendant_position"),
            "is_government_official": result.get("is_government_official"),
            "damage_amount": result.get("damage_amount"),
            "damage_compensated": result.get("damage_compensated"),
            "punishment_years": result.get("punishment_years"),
            "fine_amount": result.get("fine_amount"),
            "primary_punishment_type": result.get("primary_punishment_type"),
            "additional_punishment": result.get("additional_punishment") or [],
            "mitigating_circumstances": result.get("mitigating_circumstances") or [],
            "aggravating_circumstances": result.get("aggravating_circumstances") or [],
            "plea_bargain": result.get("plea_bargain"),
            "cooperation_with_investigation": result.get("cooperation_with_investigation"),
            "is_anonymized": result.get("is_anonymized"),
            
            "_extraction_meta": {
                "confidence": round(confidence, 2),
                "is_valid": is_valid,
                "issues": issues,
                "tokens_used": tokens_used,
                "model": self.model,
                "text_length": len(text),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        }
        
        return merged


# ============================================================
# BATCH PROCESSOR
# ============================================================
def batch_extract(text_dir: str, listing_metadata_path: str,
                  output_path: str = "extracted_data.json",
                  api_key: str = None, max_files: int = None) -> list:
    if not api_key:
        if os.path.exists(".env"):
            with open(".env", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
    if not api_key:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY topilmadi")
    
    with open(listing_metadata_path, encoding="utf-8") as f:
        listing = json.load(f)
    meta_by_id = {item["claimId"]: item for item in listing if item.get("claimId")}
    
    text_files = sorted(Path(text_dir).glob("ID_*.txt"))
    if max_files:
        text_files = text_files[:max_files]
    
    print(f"\n{'='*70}")
    print(f"  DeepSeek Extraction v2.2 — {len(text_files)} ta fayl")
    print(f"  (matn limit: {MAX_TEXT_LEN:,} belgi, smart chunking yoqilgan)")
    print(f"{'='*70}\n")
    
    extractor = DeepSeekExtractor(api_key)
    results = []
    total_tokens = 0
    
    for i, txt_path in enumerate(text_files, 1):
        try:
            claim_id = int(txt_path.stem.split("_")[1])
        except (IndexError, ValueError):
            print(f"[{i}] Fayl nomidan ID ajratib bo'lmadi: {txt_path.name}")
            continue
        
        meta = meta_by_id.get(claim_id, {})
        judge_short = (meta.get("judge") or "?")[:30]
        
        print(f"[{i}/{len(text_files)}] ID {claim_id} | {judge_short}")
        
        result = extractor.extract(text_path=str(txt_path), listing_metadata=meta)
        
        if "__error" in result:
            print(f"   ✗ XATO: {result['__error']}")
            results.append({"claim_id": claim_id, "error": result["__error"]})
            continue
        
        em = result["_extraction_meta"]
        total_tokens += em["tokens_used"]
        
        status = "✓" if em["is_valid"] else "⚠"
        print(f"   {status} confidence={em['confidence']}, "
              f"tokens={em['tokens_used']:,}, "
              f"text_len={em['text_length']:,}")
        
        # Asosiy natijalar
        details = []
        if result.get("damage_amount"):
            details.append(f"zarar={result['damage_amount']:,}")
        if result.get("fine_amount"):
            details.append(f"jarima={result['fine_amount']:,}")
        if result.get("punishment_years"):
            details.append(f"qamoq={result['punishment_years']}y")
        if result.get("primary_punishment_type"):
            details.append(f"jazo_turi={result['primary_punishment_type']}")
        if result.get("is_government_official"):
            details.append("MANSABDOR")
        if result.get("is_anonymized"):
            details.append("ANONIM")
        if details:
            print(f"     {' | '.join(details)}")
        
        results.append(result)
        time.sleep(0.5)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    valid = [r for r in results if "error" not in r]
    avg_conf = sum(r["_extraction_meta"]["confidence"] for r in valid) / max(1, len(valid))
    
    # YANGI: muhim maydonlar topilish foizi
    fields_found = {
        "punishment_years": sum(1 for r in valid if r.get("punishment_years") is not None),
        "fine_amount":      sum(1 for r in valid if r.get("fine_amount") is not None),
        "damage_amount":    sum(1 for r in valid if r.get("damage_amount") is not None),
        "is_official":      sum(1 for r in valid if r.get("is_government_official") is True),
        "primary_type":     sum(1 for r in valid if r.get("primary_punishment_type")),
    }
    
    # To'g'ri narx hisoblash: $0.14 / 1M token (input), $0.28 / 1M token (output)
    # Taxminiy o'rtacha: $0.20 / 1M token
    cost_usd = total_tokens * 0.20 / 1_000_000
    
    print(f"\n{'='*70}")
    print(f"  YAKUN: {len(valid)}/{len(results)} muvaffaqiyatli")
    print(f"  O'rtacha confidence: {avg_conf:.0%}")
    print(f"  Jami token: {total_tokens:,} (~${cost_usd:.4f})")
    print(f"\n  Muhim maydonlar topilishi:")
    for field, count in fields_found.items():
        pct = count / max(1, len(valid)) * 100
        print(f"     {field:<20} {count:>2}/{len(valid):<2} ({pct:>5.1f}%)")
    print(f"\n  Saqlandi: {output_path}")
    print(f"{'='*70}\n")
    
    return results


if __name__ == "__main__":
    batch_extract(
        text_dir="matnlar",
        listing_metadata_path="listing_metadata.json",
        output_path="extracted_data.json",
    )