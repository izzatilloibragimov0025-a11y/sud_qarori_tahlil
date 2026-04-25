"""
DeepSeek bilan PDF dan ma'lumot ajratish
Oddiy va tushunarli versiya
"""
import pdfplumber
import json
import os
from openai import OpenAI

class DeepSeekExtractor:
    """DeepSeek yordamida PDF dan ma'lumot ajratish"""
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: DeepSeek API kaliti
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        print("✅ DeepSeek client tayyor")
    
    def extract_from_pdf(self, pdf_path: str) -> dict:
        """PDF dan ma'lumot ajratish"""
        print(f"\n📄 {os.path.basename(pdf_path)} tahlil qilinmoqda...")
        
        # 1. PDF dan matnni olish
        text = self._read_pdf(pdf_path)
        
        if not text or len(text) < 100:
            return {"error": "PDF dan matn o'qib bo'lmadi", "file_name": os.path.basename(pdf_path)}
        
        print(f"   📝 Matn o'qildi: {len(text)} belgi")
        
        # 2. DeepSeek ga so'rov yuborish
        print(f"   🤖 DeepSeek ga yuborilmoqda...")
        extracted_data = self._ask_deepseek(text)
        
        # 3. Fayl nomini qo'shish
        extracted_data['file_name'] = os.path.basename(pdf_path)
        
        print(f"   ✅ Tahlil tugadi")
        return extracted_data
    
    def _read_pdf(self, pdf_path: str) -> str:
        """PDF dan matnni o'qish"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = '\n'.join([page.extract_text() or '' for page in pdf.pages])
                return text
        except Exception as e:
            print(f"   ❌ Xato: {e}")
            return ""
    
    def _ask_deepseek(self, text: str) -> dict:
        """DeepSeek dan ma'lumot so'rash"""
        
        # Matnni qisqartirish (8000 belgigacha)
        text = text[:8000]
        
        prompt = f"""
Sud qarori matnidan quyidagi ma'lumotlarni JSON formatda ajratib ber.
Agar biror ma'lumot topilmasa, null qo'y.

KERAKLI MA'LUMOTLAR:
1. case_id - Ish raqami (masalan: "123-2024", "1-1209-1901/8")
2. date - Qaror sanasi
3. judge_full_name - Sudya to'liq ismi (masalan: "О.Набиев", "Ж.Турдимурадов")
4. court - Sud nomi
5. defendant_name - Ayblanuvchi F.I.O.
6. defendant_position - Ayblanuvchi lavozimi (agar bor bo'lsa)
7. is_government_official - Mansabdor shaxsmi? (true/false)
8. crime_type - Jinoyat turi (masalan: "хищение", "взяточничество", "мошенничество")
9. articles - Jinoyat kodeksi moddalari ro'yxati (masalan: ["167", "228"])
10. article_parts - Modda qismlari ro'yxati (masalan: ["1", "2"])
11. damage_amount - Zarar miqdori (faqat raqam, so'mda)
12. damage_compensated - Zarar qoplanganmi? (true/false/null)
13. punishment_years - Ozodlikdan mahrum qilish muddati (faqat raqam, yillarda)
14. fine_amount - Jarima miqdori (faqat raqam, so'mda)
15. additional_punishment - Qo'shimcha jazolar ro'yxati
16. mitigating_circumstances - Yengillashtiruvchi holatlar ro'yxati
17. aggravating_circumstances - Og'irlashtiruvchi holatlar ro'yxati

MUHIM QOIDALAR:
- Faqat JSON formatda javob ber, boshqa hech narsa yozma
- Raqamlarni string emas, number sifatida ber
- Agar ma'lumot yo'q bo'lsa, null qo'y
- "punishment_years" - faqat OZODLIKDAN MAHRUM QILISH muddati!
  * "озодликдан маҳрум қилиш" yoki "лишение свободы" bo'lsa - bu qamoq
  * "мансабдорлик ишларида ишлаш ҳуқуқидан маҳрум" - bu qamoq EMAS, null qo'y
- "fine_amount" va "damage_amount" - faqat raqam, "so'm" so'zisiz
- "articles" - faqat raqamlar, "ЖК" yoki "модда" so'zlarisiz

SUD QARORI MATNI:
{text}

JSON:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Siz sud qarorlaridan ma'lumot ajratuvchi mutaxassiz. Faqat JSON formatda javob bering, boshqa hech narsa yozmang."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            
            # JSON ni tozalash
            result_text = result_text.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.startswith('```'):
                result_text = result_text[3:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            # JSON parse qilish
            data = json.loads(result_text)
            
            # Token statistikasi
            print(f"   📊 Token: {response.usage.total_tokens} (input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})")
            
            return data
            
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON xatosi: {e}")
            print(f"   📝 Javob: {result_text[:200]}...")
            return {"error": "JSON parse xatosi"}
        except Exception as e:
            print(f"   ❌ DeepSeek xatosi: {e}")
            return {"error": str(e)}


def main():
    """Asosiy dastur"""
    print("=" * 100)
    print("🤖 DEEPSEEK PDF EXTRACTOR")
    print("=" * 100)
    
    # API kalitini olish
    api_key = None
    
    # .env fayldan o'qishga harakat
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DEEPSEEK_API_KEY='):
                    api_key = line.split('=')[1].strip()
                    print("✅ API kaliti .env fayldan o'qildi")
                    break
    
    # Agar .env da yo'q bo'lsa, so'rash
    if not api_key:
        api_key = input("\nDeepSeek API kalitingizni kiriting: ").strip()
    
    if not api_key:
        print("❌ API kaliti kiritilmadi!")
        return
    
    # Extractor yaratish
    try:
        extractor = DeepSeekExtractor(api_key)
    except Exception as e:
        print(f"❌ Xato: {e}")
        return
    
    # Test PDF larni tanlash
    pdf_folder = "sud_pdf_fayllari"
    
    if not os.path.exists(pdf_folder):
        print(f"❌ '{pdf_folder}' papkasi topilmadi!")
        return
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ '{pdf_folder}' da PDF fayllar topilmadi!")
        return
    
    print(f"\n📁 {len(pdf_files)} ta PDF fayl topildi")
    
    # Nechta PDF tahlil qilish
    count = input(f"\nNechta PDF tahlil qilish kerak? (1-{len(pdf_files)}, Enter = 5): ").strip()
    
    if not count:
        count = 5
    else:
        try:
            count = int(count)
            count = min(count, len(pdf_files))
        except:
            count = 5
    
    print(f"\n🚀 {count} ta PDF tahlil qilinadi...")
    
    # Tahlil qilish
    results = []
    total_tokens = 0
    
    for i, pdf_file in enumerate(pdf_files[:count], 1):
        print(f"\n[{i}/{count}]", end=" ")
        pdf_path = os.path.join(pdf_folder, pdf_file)
        
        data = extractor.extract_from_pdf(pdf_path)
        results.append(data)
    
    # Natijalarni ko'rsatish
    print("\n" + "=" * 100)
    print("📊 NATIJALAR")
    print("=" * 100)
    
    for i, data in enumerate(results, 1):
        print(f"\n{i}. {data.get('file_name')}")
        print("-" * 100)
        
        if 'error' in data:
            print(f"   ❌ Xato: {data['error']}")
            continue
        
        print(f"   Ish raqami: {data.get('case_id') or '❌'}")
        print(f"   Sudya: {data.get('judge_full_name') or '❌'}")
        print(f"   Ayblanuvchi: {data.get('defendant_name') or '❌'}")
        print(f"   Jinoyat: {data.get('crime_type') or '❌'}")
        
        # Moddalarni xavfsiz chiqarish
        articles = data.get('articles')
        if articles and isinstance(articles, list) and len(articles) > 0:
            print(f"   Moddalar: {', '.join(map(str, articles))}")
        else:
            print(f"   Moddalar: ❌")
        
        if data.get('punishment_years'):
            print(f"   Jazo: ✅ {data.get('punishment_years')} yil")
        else:
            print(f"   Jazo: ⚠️  Topilmadi")
        
        if data.get('fine_amount'):
            print(f"   Jarima: ✅ {data.get('fine_amount'):,.0f} so'm")
        else:
            print(f"   Jarima: ⚠️  Topilmadi")
    
    # Statistika
    print("\n" + "=" * 100)
    print("📈 STATISTIKA")
    print("=" * 100)
    
    valid_results = [r for r in results if 'error' not in r]
    total = len(valid_results)
    
    if total > 0:
        stats = {
            'Ish raqami': sum(1 for r in valid_results if r.get('case_id')),
            'Sudya': sum(1 for r in valid_results if r.get('judge_full_name')),
            'Ayblanuvchi': sum(1 for r in valid_results if r.get('defendant_name')),
            'Jinoyat': sum(1 for r in valid_results if r.get('crime_type')),
            'Moddalar': sum(1 for r in valid_results if r.get('articles') and isinstance(r.get('articles'), list) and len(r.get('articles')) > 0),
            'Jazo': sum(1 for r in valid_results if r.get('punishment_years')),
            'Jarima': sum(1 for r in valid_results if r.get('fine_amount')),
            'Zarar': sum(1 for r in valid_results if r.get('damage_amount')),
        }
        
        print(f"\nJami: {total} ta PDF")
        for key, value in stats.items():
            pct = value/total*100 if total > 0 else 0
            status = "✅" if pct >= 70 else "⚠️" if pct >= 40 else "❌"
            print(f"{status} {key}: {value}/{total} ({pct:.0f}%)")
        
        # JSON ga saqlash
        output_file = 'deepseek_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 Natijalar '{output_file}' ga saqlandi")
    
    print("\n" + "=" * 100)
    print("✅ TAHLIL TUGADI!")
    print("=" * 100)


if __name__ == "__main__":
    main()
