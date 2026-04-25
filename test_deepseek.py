#!/usr/bin/env python3
"""
DeepSeek ni tezkor test qilish - 1 ta PDF bilan
"""
import os
import sys
from deepseek_extractor import DeepSeekExtractor

def main():
    print("🧪 DEEPSEEK TEZKOR TEST")
    print("=" * 50)
    
    # API kalitini olish
    api_key = None
    
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DEEPSEEK_API_KEY='):
                    api_key = line.split('=')[1].strip()
                    break
    
    if not api_key or api_key == 'your_api_key_here':
        print("❌ API kaliti topilmadi!")
        print("💡 Avval setup_deepseek.py ni ishga tushiring")
        return
    
    # PDF faylni tanlash
    pdf_folder = "sud_pdf_fayllari"
    
    if not os.path.exists(pdf_folder):
        print(f"❌ '{pdf_folder}' papkasi yo'q!")
        return
    
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ PDF fayllar yo'q!")
        return
    
    # Birinchi PDF ni tanlash
    test_pdf = pdf_files[0]
    pdf_path = os.path.join(pdf_folder, test_pdf)
    
    print(f"📄 Test fayli: {test_pdf}")
    
    # Extractor yaratish
    try:
        extractor = DeepSeekExtractor(api_key)
    except Exception as e:
        print(f"❌ Xato: {e}")
        return
    
    # Test qilish
    print("\n🚀 Tahlil boshlanmoqda...")
    result = extractor.extract_from_pdf(pdf_path)
    
    # Natijani ko'rsatish
    print("\n📊 NATIJA:")
    print("-" * 50)
    
    if 'error' in result:
        print(f"❌ Xato: {result['error']}")
        return
    
    # Asosiy ma'lumotlar
    fields = [
        ('Ish raqami', 'case_id'),
        ('Sana', 'date'),
        ('Sudya', 'judge_full_name'),
        ('Sud', 'court'),
        ('Ayblanuvchi', 'defendant_name'),
        ('Lavozim', 'defendant_position'),
        ('Mansabdor', 'is_government_official'),
        ('Jinoyat', 'crime_type'),
        ('Moddalar', 'articles'),
        ('Zarar', 'damage_amount'),
        ('Jarima', 'fine_amount'),
        ('Jazo (yil)', 'punishment_years'),
    ]
    
    found_count = 0
    
    for label, key in fields:
        value = result.get(key)
        if value is not None and value != "" and value != []:
            print(f"✅ {label}: {value}")
            found_count += 1
        else:
            print(f"❌ {label}: topilmadi")
    
    # Statistika
    total_fields = len(fields)
    success_rate = (found_count / total_fields) * 100
    
    print(f"\n📈 STATISTIKA:")
    print(f"   Topildi: {found_count}/{total_fields}")
    print(f"   Muvaffaqiyat: {success_rate:.0f}%")
    
    if success_rate >= 80:
        print("🎉 A'lo! DeepSeek juda yaxshi ishlayapti!")
    elif success_rate >= 60:
        print("👍 Yaxshi! Ba'zi ma'lumotlar topilmadi, lekin asosiysi bor")
    else:
        print("⚠️  Kam ma'lumot topildi. PDF sifatini tekshiring")
    
    print(f"\n💾 To'liq natija: {result}")

if __name__ == "__main__":
    main()