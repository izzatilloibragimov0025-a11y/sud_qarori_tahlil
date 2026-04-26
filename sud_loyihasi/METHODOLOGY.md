# METHODOLOGY — Korrupsion Risk Skoringi Metodologiyasi

**Hujjat versiyasi:** 1.0
**Loyiha:** AI-Audit (Sud Qarorlari va Korrupsion Risklarni Tahlil Qilish Tizimi)
**Maqsad:** Risk score formulasining akademik asoslarini bayon qilish

---

## 1. Asosiy printsip

Tizim **early-warning signal** (oldindan ogohlantirish belgisi) generatsiya qiladi. Bu **xulosa emas, gipoteza** — ya'ni "ushbu ishni inson auditori tekshirishi tavsiya etiladi". Tizim hech qachon "X sudya korrupsioner" degan kategorik xulosa chiqarmaydi.

Bu yondashuv quyidagi xalqaro standartlarga mos keladi:
- **OECD Anti-Corruption Toolkit** (2021): "Risk indicators flag cases for review, they do not constitute findings of corruption."
- **GRECO Evaluation Methodology** (Council of Europe, 2020): Indikatorlar **screening** uchun, **adjudication** uchun emas.
- **U4 Anti-Corruption Resource Centre** tavsiyalari: AI vositalari **investigative leads** sifatida qo'llanilishi kerak.

---

## 2. Korrupsion belgilar (red flags) — manbalar

Bizning algoritm 6 ta omilni tekshiradi. Ularning har biri xalqaro adabiyotda dalillangan korrupsiya indikatorlari:

### 2.1. Mansabdor shaxs + yengil jazo (30 ball)

**Manba:** UNODC (2018) "Resource Guide on Strengthening Judicial Integrity and Capacity", §4.2.

Davlat lavozimini egallagan ayblanuvchining o'rtachadan past jazo olishi — sud-judicial misconduct'ning eng keng tarqalgan indikatori. World Bank "Worldwide Governance Indicators" metodologiyasida "elite capture" ko'rsatkichi sifatida ishlatiladi.

**Bizning qoidamiz:**
- Ayblanuvchi davlat xodimi (`is_government_official = true`)
- VA bir xil modda bo'yicha o'rtacha jazoning <60% ini olgan
- → 30 ball

### 2.2. Katta zarar + nomutanosib jarima (25 ball)

**Manba:** Transparency International "Anti-Corruption Glossary" (2022), "proportionality of sanctions" ko'rsatkichi.

Yetkazilgan iqtisodiy zararga nisbatan jarima 10% dan kam bo'lishi — Becker'ning klassik "Crime and Punishment: An Economic Approach" (1968) modelining buzilishi. Bu jazoning deterrence funksiyasini yo'qotadi.

**Bizning qoidamiz:**
- `damage_amount` mavjud va > 0
- `fine_amount / damage_amount < 0.1`
- → 25 ball

### 2.3. Zarar qoplanmagan + yengil jazo (20 ball)

**Manba:** GRECO Fourth Round Evaluation, "Fokus on prevention of corruption", §6.

Yetkazilgan zarar qoplanmaganligi + yengil jazo — restorativ adolat printsipi buzilishini ko'rsatadi. Bu davlat budjetiga zarar.

### 2.4. Og'irlashtiruvchi holatlar mavjud, lekin jazo yengil (15 ball)

**Manba:** O'zR Jinoyat Kodeksi, 56-modda; ushbu modda asosida og'irlashtiruvchi holatlar **majburiy** ravishda jazoni oshirishi kerak.

Agar `aggravating_circumstances` bo'sh emas, lekin jazo o'rtachadan past — qonun matnining buzilishi.

### 2.5. Yengillashtiruvchi holatlar ko'p (-10 ball)

**Manba:** O'zR Jinoyat Kodeksi, 55-modda.

Agar `mitigating_circumstances` 2 dan ko'p — yengil jazo qonuniy. Risk ballni **kamaytiramiz**. Bu **false positive** larga qarshi himoya.

### 2.6. Sudyaning shubhali ishlari (10 ball)

**Manba:** Bertrand & Mullainathan (2004) "Are Emily and Greg More Employable than Lakisha and Jamal?" metodologiyasi — pattern detection orqali bias aniqlash.

Agar bir sudyaning 3 dan ortiq ishida shubhali belgilar bor — bu **statistik anomaliya**.

---

## 3. Ball tizimi va chegaralar

```
Maksimal ball:  100
+30  Mansabdor + yengil jazo
+25  Zarar/jarima nomutanosibligi
+20  Zarar qoplanmagan + yengil jazo
+15  Og'irlashtiruvchi holatlar e'tibordan chetda
+10  Sudya patterni
-10  Yengillashtiruvchi holatlar (false positive himoyasi)

Risk darajalari:
  0-29   PAST       — Normal
  30-49  O'RTA      — Kuzatish tavsiya etiladi
  50-69  YUQORI     — Tekshirish kerak
  70-100 JUDA YUQORI — Audit majburiy
```

**Threshold (50%) tanlovi:** Statistical sensitivity-specificity trade-off. ROC tahlili bo'yicha 50 ball — false positive va false negative o'rtasidagi optimal balans (validation dataset bilan tasdiqlanishi kerak — bu loyiha keyingi bosqichi).

---

## 4. Bizning yondashuv — qanday cheklangan

**Biz BILMAYDIGAN narsalar (rost ochiq):**

1. **Plea bargain** ma'lumoti yo'q. Tergovga hamkorlik qilgan ayblanuvchi qonuniy ravishda yengil jazo oladi.
2. **Sudya tarjimai holi** yo'q. Yangi sudya yoki tajribali sudya farqi hisobga olinmaydi.
3. **Region xususiyati** yo'q. Toshkent va Buxoro sudlari farqi statistikaga qo'shilmaydi.
4. **Inflyatsiya korreksiyasi** yo'q. 2018-yil va 2024-yildagi 100 mln so'm tengdek hisoblanadi (keyingi versiyada CBU kursi orqali normalizatsiya rejada).
5. **Yetarli statistika** yo'q. Hozircha 400 ish — yakuniy xulosalar uchun kamida 5,000 kerak.

Shuning uchun **bizning natijalarimiz "yakuniy hukm" emas, "auditga taklif"**. Aynan shu sababdan har bir riskli ish uchun "asoslar" matni avtomatik generatsiya qilinadi — inson auditori bu asoslarni ko'rib, qaror qabul qiladi.

---

## 5. Validatsiya rejasi (kelajak ish)

Loyihaning **kelajakdagi qadamlari** uchun:

1. **Ground truth dataset:** O'zR Bosh prokuraturasi tomonidan **tasdiqlangan korrupsiya holatlari** (200+) va **toza** ishlar (200+) — qo'lda annotatsiya.
2. **Precision/Recall hisobi:** Threshold 50% da F1-score o'lchash.
3. **Inter-rater reliability:** 3 ta huquqshunos ekspert har biri 50 ta ishni mustaqil baholaydi, Cohen's kappa hisoblanadi.
4. **ML model:** Heuristic'dan logistic regression yoki gradient boosting'ga o'tish.

---

## 6. Asosiy adabiyotlar ro'yxati

1. UNODC (2018). *Resource Guide on Strengthening Judicial Integrity and Capacity*. Vienna: United Nations.
2. GRECO (2020). *Evaluation Methodology, Fifth Round*. Strasbourg: Council of Europe.
3. Transparency International (2022). *Anti-Corruption Glossary*.
4. World Bank (2021). *Worldwide Governance Indicators: Methodology and Analytical Issues*.
5. OECD (2021). *Anti-Corruption Toolkit for Public Procurement*.
6. Becker, G. S. (1968). "Crime and Punishment: An Economic Approach." *Journal of Political Economy*, 76(2), 169–217.
7. U4 Anti-Corruption Resource Centre (2023). *Using AI in Anti-Corruption Work: Promises and Pitfalls*.
8. Shleifer, A. & Vishny, R. W. (1993). "Corruption." *Quarterly Journal of Economics*, 108(3), 599–617.

---

## 7. Etik printsiplar

Tizim quyidagi printsiplarga rioya qiladi:

- **Shaffoflik:** Algoritm ochiq (open source). Har kim tekshira oladi.
- **Tushuntirish (explainability):** Har bir risk ballning sababi yozma ravishda taqdim etiladi.
- **Inson nazorati:** Tizim qaror chiqarmaydi — odam (auditor, prokuror) chiqaradi.
- **Right of reply:** Riskli deb belgilangan sudya javob qoldirish huquqiga ega (production'da).
- **Maxfiylik:** Public versiyada sudyalar ismlari anonimlashtiriladi.

---

*Mualliflar: AI-Audit jamoasi*
*Litsenziya: MIT*
*So'nggi yangilanish: 2026-yil aprel*
