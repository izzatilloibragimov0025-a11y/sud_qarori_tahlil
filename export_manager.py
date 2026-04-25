"""
Turli formatlarda export qilish
"""
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime

class ExportManager:
    """Ma'lumotlarni turli formatlarda export qilish"""
    
    @staticmethod
    def export_to_csv(analyzed_df: pd.DataFrame, filename: str = "tahlil_natijasi.csv"):
        """CSV formatda export"""
        analyzed_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ CSV ga saqlandi: {filename}")
    
    @staticmethod
    def export_to_json_detailed(cases_df: pd.DataFrame, analyzed_df: pd.DataFrame, 
                                judge_rating: pd.DataFrame, stats: Dict, 
                                filename: str = "tahlil_full.json"):
        """Batafsil JSON export"""
        
        result = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '2.0',
                'total_cases': len(cases_df)
            },
            'statistics': stats,
            'cases': {
                'all': analyzed_df.to_dict('records'),
                'high_risk': analyzed_df[analyzed_df['corruption_score'] >= 50].to_dict('records'),
                'medium_risk': analyzed_df[(analyzed_df['corruption_score'] >= 30) & 
                                          (analyzed_df['corruption_score'] < 50)].to_dict('records'),
                'low_risk': analyzed_df[analyzed_df['corruption_score'] < 30].to_dict('records')
            },
            'judges': {
                'rating': judge_rating.to_dict('records'),
                'suspicious': judge_rating[judge_rating['avg_corruption_score'] >= 50].to_dict('records')
            },
            'insights': ExportManager._generate_insights(analyzed_df, judge_rating, stats)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"✅ Batafsil JSON ga saqlandi: {filename}")
    
    @staticmethod
    def _generate_insights(analyzed_df: pd.DataFrame, judge_rating: pd.DataFrame, stats: Dict) -> Dict:
        """Avtomatik xulosalar"""
        insights = {
            'summary': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Umumiy xulosa
        high_risk_pct = (stats['high_risk_cases'] / stats['total_cases'] * 100) if stats['total_cases'] > 0 else 0
        insights['summary'].append(f"{stats['total_cases']} ta ish tahlil qilindi")
        insights['summary'].append(f"{high_risk_pct:.1f}% yuqori xavfli ishlar")
        
        # Ogohlantirishlar
        if high_risk_pct > 30:
            insights['warnings'].append("DIQQAT: Yuqori xavfli ishlar foizi juda yuqori!")
        
        if len(judge_rating) > 0:
            suspicious_judges = judge_rating[judge_rating['avg_corruption_score'] >= 50]
            if len(suspicious_judges) > 0:
                insights['warnings'].append(f"{len(suspicious_judges)} ta shubhali sudya aniqlandi")
        
        # Tavsiyalar
        insights['recommendations'].append("Yuqori xavfli ishlarni batafsil tekshirish tavsiya etiladi")
        insights['recommendations'].append("Shubhali sudyalarning barcha ishlarini qayta ko'rib chiqish kerak")
        
        if stats['official_cases'] > 0:
            insights['recommendations'].append("Mansabdor shaxslar bilan bog'liq ishlarni alohida monitoring qilish")
        
        return insights
    
    @staticmethod
    def export_summary_report(stats: Dict, judge_rating: pd.DataFrame, 
                            filename: str = "qisqacha_hisobot.txt"):
        """Qisqacha matnli hisobot"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("SUD QARORLARI TAHLIL TIZIMI - QISQACHA HISOBOT\n")
            f.write("O'zbekiston Respublikasi\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Sana: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
            
            f.write("UMUMIY STATISTIKA:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Jami ishlar: {stats['total_cases']}\n")
            f.write(f"Yuqori xavfli: {stats['high_risk_cases']} ({stats['high_risk_cases']/stats['total_cases']*100:.1f}%)\n")
            f.write(f"O'rta xavfli: {stats['medium_risk_cases']} ({stats['medium_risk_cases']/stats['total_cases']*100:.1f}%)\n")
            f.write(f"Past xavfli: {stats['low_risk_cases']} ({stats['low_risk_cases']/stats['total_cases']*100:.1f}%)\n")
            f.write(f"Mansabdorlar: {stats['official_cases']}\n")
            f.write(f"O'rtacha xavf: {stats['avg_corruption_score']:.1f}%\n\n")
            
            f.write("ENG SHUBHALI SUDYALAR:\n")
            f.write("-" * 80 + "\n")
            for idx, judge in judge_rating.head(5).iterrows():
                f.write(f"{idx+1}. {judge['judge_name']}\n")
                f.write(f"   Jami ishlar: {judge['total_cases']}\n")
                f.write(f"   Xavfli ishlar: {judge['high_risk_cases']} ({judge['high_risk_percentage']:.1f}%)\n")
                f.write(f"   O'rtacha xavf: {judge['avg_corruption_score']:.1f}%\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("Maxfiy - Faqat xizmat foydalanish uchun\n")
        
        print(f"✅ Qisqacha hisobot saqlandi: {filename}")
