# LIMITATIONS — Tizimning Cheklovlari va Yumshatish Strategiyasi

**Maqsad:** Loyihaning hozirgi cheklovlarini ochiq tan olish va ularni yumshatish (mitigation) strategiyalarini taqdim etish. Bu hujjat **hakamlar, foydalanuvchilar va mas'ul shaxslar** uchun.

---

## 1. Texnik cheklovlar

### 1.1. Ma'lumotlar hajmi

**Cheklov:** Hozirda taxminan 400 ta sud qarori tahlil qilinadi. publication.sud.uz da jami 447,622 ta jinoiy ish bor (2026-yil aprel ma'lumoti).

**Ta'siri:** Ayrim sudyalar bo'yicha 5–10 ta ish — statistik xulosa chiqarish uchun kam (kamida 30 ta tavsiya etiladi, Central Limit Theorem'ga ko'ra).

**Yumshatish:**
- Production fazasida butun bazani indekslash (1–2 oyda parser miqyoslash)
- Yetarli sample bo'lmagan sudyalar uchun **"Insufficient data"** belgisi avtomatik qo'yiladi
- Confidence interval har bir balling uchun ko'rsatiladi

### 1.2. AI extraction xatolari (DeepSeek)

**Cheklov:** Hozircha DeepSeek extraction'ning aniqlik darajasi tasdiqlanmagan. README'dagi "89.1%" — hech qanday ground truth bilan solishtirilmagan, bu **taxminiy raqam**.

**Ta'siri:** Yolg'on flag'lar (false positives) — sudyaga tuhmat xavfi.

**Yumshatish:**
- Listing API metadata'sidan kelgan maydonlar (sudya, modda, sud) **AI'ga muhtoj emas** — ular birlamchi manbadan to'g'ridan-to'g'ri keladi
- Validation set: 50 ta qo'lda annotatsiyalangan ish (kelajak)
- Har bir extracted maydon uchun "confidence" ko'rsatkichi
- Cross-validation: ayni ish 3 marta DeepSeek'ga yuboriladi, javoblar mos kelmasa flag

### 1.3. Hujjat formati (.doc va .pdf)

**Cheklov:** publication.sud.uz fayllarni `.doc` (Word 97–2003) formatida qaytaradi. Ko'pgina `.doc` parserlar shrift va kodlash bilan muammo qiladi.

**Ta'siri:** O'zbek (kirill) matnida xato belgilar; ba'zi fayllar to'g'ri o'qilmaydi.

**Yumshatish:**
- `python-docx2txt` + `antiword` + `LibreOffice headless` ketma-ket sinov
- Buzilgan fayllar uchun avtomatik flag → manual tekshiruv navbatiga
- OCR fallback (oxirgi chora)

### 1.4. Tilning xilma-xilligi

**Cheklov:** Sud qarorlari uch xil yozuvda: o'zbek-kirill (asosiy), o'zbek-lotin, rus tili. Sudya ismlari ko'pincha turli yozuvlarda ("О.Набиев", "Набиев О.", "Nabiyev O.").

**Ta'siri:** Bir sudya uch alohida shaxs deb hisoblanishi mumkin → statistika buziladi.

**Yumshatish:**
- Name normalization: transliteration table (kirill ↔ lotin)
- Fuzzy matching: `rapidfuzz` kutubxonasi orqali 90%+ o'xshashlik bo'lsa birlashtirish
- Manual mapping fayli (ambiguous holatlar uchun)

---

## 2. Metodologik cheklovlar

### 2.1. Legal context yo'qligi

**Cheklov:** Algoritm quyidagilarni hisobga olmaydi:
- **Plea bargain** (kelishuv bilan jazo kamayishi)
- **Tergovga hamkorlik** (qonuniy yengillik)
- **Birinchi marta jinoyat** (51-modda)
- **Voyaga yetmagan ayblanuvchi**
- **Yashirin ayblar** (multiple charges interaction)

**Ta'siri:** Qonuniy ravishda yengil jazo "shubhali" deb belgilanishi mumkin (false positive).

**Yumshatish:**
- DeepSeek prompt'ini kengaytirish (kelishuv borligini topish)
- METHODOLOGY ga ko'ra: yengillashtiruvchi holatlar **ko'p** bo'lsa, score **kamayadi** (-10)
- Disclaimer banner har bir tahlilda: "Bu signal, hukm emas"

### 2.2. Inflyatsiya korreksiyasi yo'q

**Cheklov:** 2018-yildagi 100 mln so'm va 2024-yildagi 100 mln so'm tenglashtiriladi. Lekin so'mning real qiymati 2.5 baravar tushgan.

**Ta'siri:** Eski ishlardagi "katta zarar" hozirgi pulda kichik bo'ladi.

**Yumshatish:** CBU O'rtacha kursi yoki CPI (Consumer Price Index) bo'yicha barcha summalarni 2026-yil pulgi normalize qilish. **TODO: keyingi versiya.**

### 2.3. Sudyalar bazasi statisi

**Cheklov:** Algoritm "har bir sudya bir xil ish hajmiga ega" deb taxmin qiladi. Aslida — Toshkent shahar sudyalari yiliga 500+ ish ko'radi, viloyat sudyalari 50.

**Ta'siri:** Tashkent sudyalari "ko'p shubhali ish" deb belgilanishi mumkin — chunki ular oddiygina ko'p ish ko'radi.

**Yumshatish:** **Foiz** ko'rsatkichini ishlatish (suspicious/total), absolute sonni emas.

### 2.4. Selection bias (manba muammosi)

**Cheklov:** publication.sud.uz **faqat e'lon qilingan** qarorlarni o'z ichiga oladi. Ba'zi ishlar (yopiq sud, milliy xavfsizlik) e'lon qilinmaydi.

**Ta'siri:** Eng yuqori darajadagi korrupsiya bizga ko'rinmaydi.

**Yumshatish:** Ochiq ravishda hujjatlash. Bu — **hayotiy chegara** (epistemic limit), ham bizning, ham har qanday boshqa tashqi tahlilchi uchun.

---

## 3. Huquqiy va etik cheklovlar

### 3.1. Defamation (tuhmat) xavfi

**Cheklov:** Aniq sudyaning ismini "korrupsion risk" bilan ommaga e'lon qilish — O'zR Fuqarolik Kodeksi 100-modda asosida da'vo keltirib chiqarishi mumkin.

**Yumshatish:**
- **Ichki audit versiyasi** (Adliya vazirligi, Bosh prokuratura) — to'liq ismlar bilan
- **Ommaviy versiya** — anonimlashtirilgan ("Sudya A", "Sudya B")
- **Right of reply:** Sudya o'z sahifasiga izoh qoldirish huquqi
- Har sahifada **disclaimer banner**: "Bu signal, hukm emas"
- Loyiha **MUSTAQIL FUQAROLIK TASHABBUSI** sifatida pozitsiyalanadi (jurnalist, hujjatchi tashkilot kabi himoya)

### 3.2. Algoritmik bias

**Cheklov:** Hozirgi heuristic algoritm **demografik bias**'ni hisobga olmaydi (yosh, jins, millat, ijtimoiy holat).

**Ta'siri:** Agar kelajakda ML modeli o'rgatilsa va u ma'lum guruhlarni tizimli ravishda yuqori risk deb belgilasa — bu **algoritmik diskriminatsiya**.

**Yumshatish:**
- Hozircha ML yo'q — faqat ochiq, tushuntirib bersa bo'ladigan qoidalar
- Kelajakda ML kiritilsa — fairness audit majburiy (Aequitas yoki Fairlearn)
- Ayblanuvchi demografik ma'lumotlari **sirayam ishlatilmaydi**, faqat sud va sudya ma'lumotlari

### 3.3. Ma'lumot maxfiyligi

**Cheklov:** publication.sud.uz da ayblanuvchilar ismlari mavjud (chunki ish ochiq).

**Ta'siri:** GDPR / O'zR "Shaxsiy ma'lumotlar to'g'risida"gi qonun.

**Yumshatish:**
- Ayblanuvchi ismlari ichki tahlilda saqlanadi, lekin **dashboard'da ko'rsatilmaydi**
- Faqat ish raqami va modda ko'rsatiladi

---

## 4. Loyiha holati (development stage)

**Bu loyiha hozirda:** **Proof-of-Concept (PoC) / Prototype** holatida.

**Production'gacha kerak:**
1. ✅ Pipeline ishlaydi (parser → AI → analyzer → dashboard) — TUGADI
2. ⏳ Validation dataset (200+ ground truth) — KEYINGI
3. ⏳ Huquqshunos ekspertiza — KEYINGI
4. ⏳ Adliya vazirligi bilan pilot — KEYINGI
5. ⏳ ML modeli (heuristic dan keyingisiga) — UZOQ MUDDATLI

**Vaqt taxmini:** Production darajasiga 4–6 oy + sud-huquq mutaxassislari komandasi.

---

## 5. Foydalanuvchi uchun disclaimer (UI'da ko'rinadi)

> ⚠️ **DIQQAT:**
> Ushbu tizim **yordamchi tahlil vositasi** bo'lib, sud xodimlari va auditorlar uchun mo'ljallangan. Tizim tomonidan generatsiya qilingan **risk ballari yakuniy xulosa emas** — ular shu ish bo'yicha qo'shimcha tekshiruv tavsiyasi sifatida qabul qilinishi kerak. Hech qanday qaror faqatgina ushbu tizim natijalariga asoslanib qabul qilinmaydi.

---

## 6. Hakamlarga javob: "Bu MVP nima darajada?"

To'g'ridan-to'g'ri javob:

> "Bu **Proof-of-Concept**. Ya'ni biz **texnik feasibility'ni** isbotladik: AI orqali sud qarorlarini avtomatik tahlil qilish va korrupsion belgilarni topish — texnik jihatdan **mumkin va arzon**.
>
> Production'gacha 4–6 oy ish kerak: validation dataset, huquqiy ekspertiza, davlat organlari bilan pilot. Lekin bizning loyihamiz shuni ko'rsatdiki, butun mamlakat sud arxivini AI bilan tahlil qilish — million dollarlik proyekt EMAS, balki **bir necha o'n ming dollarlik** masala. Bu davlat byudjeti uchun realistik raqam."

---

*So'nggi yangilanish: 2026-yil aprel*
