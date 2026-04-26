# ARCHITECTURE — Texnik Arxitektura Hujjati

**Loyiha:** AI-Audit (Sud Qarorlari Tahlil Tizimi)

---

## 1. Yuqori darajadagi diagramma

```
┌─────────────────────────────────────────────────────────────────┐
│                  publication.sud.uz (manba)                      │
│              447,622 ta jinoiy ish, ochiq baza                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. PARSER LAYER (parser_v2.py)                                  │
│  • Listing API'dan smart filter (instance=1, "Айблов ҳукми")    │
│  • Korrupsion moddalar prioriteti                                │
│  • Retry + cooldown + jitter                                     │
│  • Resume support (download_progress.json)                       │
│                                                                  │
│  Output: sud_fayllari/*.doc + listing_metadata.json              │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. CONVERTER LAYER (doc_converter.py)                           │
│  • .doc → matn (LibreOffice headless / antiword)                 │
│  • Encoding fix (cp1251 → utf-8)                                 │
│  • Buzilgan fayllarni flag                                       │
│                                                                  │
│  Output: text/*.txt                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. EXTRACTION LAYER (deepseek_extractor_v2.py)                  │
│  • Listing metadata bilan birgalikda (sudya, modda allaqachon    │
│    ma'lum) — DeepSeek faqat raqamlarni topadi                    │
│  • Validation: tip tekshiruv, range tekshiruv                    │
│  • Cross-validation (3x retry, javob mos kelishi)                │
│                                                                  │
│  Output: extracted_data.json                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. ANALYSIS LAYER (analyzer_v2.py)                              │
│  • METHODOLOGY.md ga asoslangan formula                          │
│  • Sudyalar nominal-normalize qilish                             │
│  • Statistika va sudyalar reytingi                               │
│  • Audit log har bir tahlil uchun                                │
│                                                                  │
│  Output: risk_analysis.json + audit_log.csv                      │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. PRESENTATION LAYER (dashboard.html + app.py)                 │
│  • 4 ta bo'lim: Overview, Risk Cases, Comparison, Judges         │
│  • Disclaimer banner (har sahifada)                              │
│  • Anonimlashtirish toggle (public vs internal mode)             │
│  • Real-time PDF upload (Flask app)                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Loyiha papka tuzilmasi (yangi)

```
ai-audit/
├── README.md                    # Asosiy hujjat
├── METHODOLOGY.md               # Algoritm asoslari
├── LIMITATIONS.md               # Cheklovlar
├── ARCHITECTURE.md              # Bu hujjat
├── LICENSE                      # MIT
├── requirements.txt             # Python dependencies
├── .gitignore
├── .env.example                 # Misol uchun (haqiqiy .env emas)
│
├── src/                         # Backend kodlar
│   ├── __init__.py
│   ├── parser_v2.py             # publication.sud.uz dan yuklab olish
│   ├── doc_converter.py         # .doc → matn
│   ├── deepseek_extractor.py    # AI extraction
│   ├── analyzer.py              # Risk hisoblash
│   ├── name_normalizer.py       # Sudyalar ismini yagonalashtirish
│   └── audit_logger.py          # Har bir tahlilni saqlash
│
├── web/                         # Frontend
│   ├── app.py                   # Flask
│   ├── dashboard.html           # Asosiy dashboard
│   ├── static/
│   │   ├── style.css
│   │   └── dashboard.js
│   └── templates/
│       ├── upload.html
│       └── case_detail.html
│
├── data/                        # Ma'lumotlar (gitignore)
│   ├── raw/                     # Yuklab olingan .doc fayllar
│   ├── text/                    # Konvertatsiya qilingan matnlar
│   ├── listing_metadata.json    # Listing API'dan kelgan metadata
│   ├── extracted_data.json      # DeepSeek natijalari
│   ├── risk_analysis.json       # Tahlil natijalari
│   ├── audit_log.csv            # Audit log
│   └── download_progress.json   # Parser progress
│
├── docs/                        # Qo'shimcha hujjatlar
│   ├── METHODOLOGY_v2.md
│   ├── DEPLOYMENT.md
│   └── presentation.pdf
│
└── tests/                       # Birlik testlar (kelajak)
    ├── test_parser.py
    ├── test_extractor.py
    └── test_analyzer.py
```

---

## 3. Ma'lumotlar oqimi (data flow)

### 3.1. Bitta ish uchun to'liq pipeline:

```
1. parser_v2.py
   GET /criminal/findAll?page=N → 30 ta ish metadata
   filter: instance=1, "Айблов ҳукми"
   GET /api/file/criminal/{claimId}/ → ID_{claimId}.doc

2. doc_converter.py
   ID_{claimId}.doc → ID_{claimId}.txt (utf-8)

3. deepseek_extractor.py
   ID_{claimId}.txt + listing_metadata[claimId] →
     {
       "case_id": "...",
       "judge": "...",  # listing'dan keladi (validatsiya uchun)
       "articles": [...],  # listing'dan keladi
       "damage_amount": 50000000,  # AI topadi
       "fine_amount": 1000000,     # AI topadi
       "punishment_years": 3.5,    # AI topadi
       "is_government_official": true,  # AI topadi
       "aggravating_circumstances": [...],  # AI topadi
       "mitigating_circumstances": [...],   # AI topadi
       "confidence": 0.92  # validation natijasi
     }

4. analyzer.py
   extracted_data → risk_score (0-100), risk_level, reasons
   ham metodologiyaga ko'ra (METHODOLOGY.md)

5. dashboard.html
   risk_analysis.json → vizual ko'rinish
```

---

## 4. Texnologiyalar stacki

| Layer       | Texnologiya             | Asos |
|-------------|-------------------------|------|
| Parser      | Python + requests       | Sodda, ishonchli, asynch keraksiz |
| .doc convert | LibreOffice headless   | O'zbek kirill bilan eng yaxshi ishlovchi |
| AI Extract  | DeepSeek API            | Arzon ($0.001/PDF), o'zbek/rus tilini biladi |
| Analysis    | Pandas + NumPy          | Statistika va data manipulation uchun standart |
| Backend     | Flask                   | Yengil, MVP uchun yetarli |
| Frontend    | HTML + vanilla JS       | Build step yo'q, oddiy deploy |
| Deploy      | Firebase Hosting / GitHub Pages | Bepul, oddiy |

**Nega React, Vue yoki boshqa SPA frameworks YO'Q:**
MVP uchun complexity ko'p, hech qanday foyda bermaydi. Vanilla JS bilan barcha funksionallik bemalol amalga oshadi.

---

## 5. Xavfsizlik

### 5.1. API kalitlar
- `.env` fayl `.gitignore` da
- `.env.example` namuna sifatida public
- Hech qachon hardcode emas

### 5.2. Audit log
Har bir tahlil quyidagi formatda saqlanadi:
```csv
timestamp, claim_id, user, risk_score, risk_level, judge_anon_id
```

Bu **kim, qachon, nimani ko'rdi** ni kuzatish imkonini beradi.

### 5.3. Anonimlashtirish (public mode)
Public versiyada sudya ismlari `SHA-256(judge_name)` ning birinchi 8 belgilari bilan almashtiriladi:
```
"Набиев Отабек Олимджонович" → "Sudya #a3f1c8b2"
```

Internal versiyada (Adliya vazirligi xodimlari uchun) — to'liq ismlar.

---

## 6. Miqyoslash (scaling)

### 6.1. Hozirgi cheklovlar:
- Parser: 1 ish/2.5 sek = 1,440 ish/soat
- DeepSeek: 1 ish/3 sek = 1,200 ish/soat
- 447K ta ishni qayta ishlash: ~310 soat ≈ 13 sutka

### 6.2. Kelajak optimizatsiyalari:
- Parallel parsing (aiohttp): 10x tezroq
- DeepSeek batch API: 5x tezroq
- Caching: bir xil ish qayta tahlil qilinmaydi
- Background queue (Celery + Redis): production'da

---

## 7. Monitoring va metrika

**Tracked metrics:**
- Parser success rate (%)
- DeepSeek extraction confidence (avg)
- Risk score taqsimoti (histogram)
- Sudyalar bo'yicha ish soni
- Time-to-flag (ishni tahlil qilish vaqti)

**Alarm shartlar:**
- Parser fail > 20% → email
- DeepSeek confidence < 70% → manual review
- Bir xil sudya 5+ marta yuqori risk → senior auditor

---

*So'nggi yangilanish: 2026-yil aprel*
