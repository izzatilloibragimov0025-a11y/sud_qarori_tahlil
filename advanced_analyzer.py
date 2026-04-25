import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

class AdvancedKorrupsiyaAnalyzer:
    """Kengaytirilgan korrupsiya tahlil tizimi"""
    
    def __init__(self, cases_df: pd.DataFrame):
        self.df = cases_df
        
    def calculate_corruption_score(self, case: Dict) -> Tuple[float, str, List[str]]:
        """
        Har bir ish uchun korrupsiya ehtimoli foizini hisoblash
        Returns: (score, level, reasons)
        """
        score = 0
        reasons = []
        max_score = 100
        
        # 1. Mansabdor shaxs + yumshoq jazo (30 ball)
        if case.get('is_government_official'):
            avg_punishment = self._get_average_punishment_for_crime(case.get('crime_type'))
            if avg_punishment and case.get('punishment_years'):
                if case['punishment_years'] < avg_punishment * 0.6:
                    score += 30
                    reasons.append(f"Mansabdor shaxsga o'rtachadan 40% kam jazo ({case['punishment_years']:.1f} yil vs {avg_punishment:.1f} yil)")
                elif case['punishment_years'] < avg_punishment * 0.8:
                    score += 15
                    reasons.append(f"Mansabdor shaxsga o'rtachadan 20% kam jazo")
        
        # 2. Katta zarar + kichik jazo (25 ball)
        if case.get('damage_amount') and case.get('fine_amount'):
            damage = case['damage_amount']
            fine = case['fine_amount']
            
            if fine < damage * 0.1:  # Jarima zararning 10% dan kam
                score += 25
                reasons.append(f"Jarima zararning {(fine/damage*100):.1f}% ni tashkil qiladi (juda kam)")
            elif fine < damage * 0.3:
                score += 15
                reasons.append(f"Jarima zararning {(fine/damage*100):.1f}% ni tashkil qiladi")
        
        # 3. Zarar qoplanmagan + yumshoq jazo (20 ball)
        if case.get('damage_compensated') == False:
            if case.get('punishment_years'):
                avg_punishment = self._get_average_punishment_for_crime(case.get('crime_type'))
                if avg_punishment and case['punishment_years'] < avg_punishment:
                    score += 20
                    reasons.append("Zarar qoplanmagan, lekin yumshoq jazo berilgan")
        
        # 4. Og'irlashtiruvchi holatlar bor, lekin jazo yumshoq (15 ball)
        if case.get('aggravating_circumstances') and len(case['aggravating_circumstances']) > 0:
            avg_punishment = self._get_average_punishment_for_crime(case.get('crime_type'))
            if avg_punishment and case.get('punishment_years'):
                if case['punishment_years'] < avg_punishment:
                    score += 15
                    reasons.append(f"Og'irlashtiruvchi holatlar mavjud ({len(case['aggravating_circumstances'])} ta), lekin jazo yumshoq")
        
        # 5. Yengillashtiruvchi holatlar ko'p (10 ball kamayadi)
        if case.get('mitigating_circumstances') and len(case['mitigating_circumstances']) > 2:
            score -= 10
            reasons.append(f"Yengillashtiruvchi holatlar ko'p ({len(case['mitigating_circumstances'])} ta)")
        
        # 6. Sudya tarixida ko'p shubhali ishlar (10 ball)
        judge_suspicious_count = self._get_judge_suspicious_count(case.get('judge_full_name'))
        if judge_suspicious_count > 3:
            score += 10
            reasons.append(f"Sudyaning {judge_suspicious_count} ta shubhali ishi mavjud")
        
        # Score ni 0-100 oralig'ida saqlash
        score = max(0, min(100, score))
        
        # Daraja aniqlash
        if score >= 70:
            level = "JUDA YUQORI"
        elif score >= 50:
            level = "YUQORI"
        elif score >= 30:
            level = "O'RTA"
        else:
            level = "PAST"
        
        return score, level, reasons
    
    def _get_average_punishment_for_crime(self, crime_type: str) -> float:
        """Jinoyat turi uchun o'rtacha jazo"""
        if not crime_type or pd.isna(crime_type):
            return None
        
        crime_cases = self.df[self.df['crime_type'] == crime_type]
        punishments = crime_cases['punishment_years'].dropna()
        
        if len(punishments) > 0:
            return punishments.mean()
        return None
    
    def _get_judge_suspicious_count(self, judge_name: str) -> int:
        """Sudyaning shubhali ishlari soni"""
        if not judge_name or pd.isna(judge_name):
            return 0
        
        judge_cases = self.df[self.df['judge_full_name'] == judge_name]
        
        # Shubhali ishlarni hisoblash
        suspicious_count = 0
        for _, case in judge_cases.iterrows():
            avg_punishment = self._get_average_punishment_for_crime(case.get('crime_type'))
            if avg_punishment and case.get('punishment_years'):
                if case['punishment_years'] < avg_punishment * 0.7:
                    suspicious_count += 1
        
        return suspicious_count
    
    def analyze_all_cases(self) -> pd.DataFrame:
        """Barcha ishlarni tahlil qilish"""
        results = []
        
        for idx, case in self.df.iterrows():
            score, level, reasons = self.calculate_corruption_score(case.to_dict())
            
            results.append({
                'case_id': case.get('case_id'),
                'file_name': case.get('file_name'),
                'judge': case.get('judge_full_name'),
                'defendant': case.get('defendant_name'),
                'position': case.get('defendant_position'),
                'is_official': case.get('is_government_official'),
                'crime_type': case.get('crime_type'),
                'articles': case.get('articles'),
                'damage_amount': case.get('damage_amount'),
                'fine_amount': case.get('fine_amount'),
                'punishment_years': case.get('punishment_years'),
                'corruption_score': score,
                'corruption_level': level,
                'reasons': ' | '.join(reasons) if reasons else 'Shubhali belgilar topilmadi'
            })
        
        return pd.DataFrame(results).sort_values('corruption_score', ascending=False)
    
    def get_judge_rating(self) -> pd.DataFrame:
        """Sudyalar reytingi"""
        judge_stats = []
        
        for judge in self.df['judge_full_name'].unique():
            if pd.isna(judge):
                continue
            
            judge_cases = self.df[self.df['judge_full_name'] == judge]
            
            # Har bir ish uchun corruption score hisoblash
            scores = []
            for _, case in judge_cases.iterrows():
                score, _, _ = self.calculate_corruption_score(case.to_dict())
                scores.append(score)
            
            avg_score = np.mean(scores) if scores else 0
            high_risk_count = sum(1 for s in scores if s >= 50)
            
            judge_stats.append({
                'judge_name': judge,
                'total_cases': len(judge_cases),
                'avg_corruption_score': avg_score,
                'high_risk_cases': high_risk_count,
                'high_risk_percentage': (high_risk_count / len(judge_cases) * 100) if len(judge_cases) > 0 else 0,
                'avg_punishment': judge_cases['punishment_years'].mean(),
                'official_cases': judge_cases['is_government_official'].sum()
            })
        
        return pd.DataFrame(judge_stats).sort_values('avg_corruption_score', ascending=False)
    
    def get_statistics(self) -> Dict:
        """Umumiy statistika"""
        analyzed = self.analyze_all_cases()
        
        return {
            'total_cases': len(self.df),
            'high_risk_cases': len(analyzed[analyzed['corruption_score'] >= 50]),
            'medium_risk_cases': len(analyzed[(analyzed['corruption_score'] >= 30) & (analyzed['corruption_score'] < 50)]),
            'low_risk_cases': len(analyzed[analyzed['corruption_score'] < 30]),
            'official_cases': self.df['is_government_official'].sum(),
            'total_damage': self.df['damage_amount'].sum(),
            'total_fines': self.df['fine_amount'].sum(),
            'avg_corruption_score': analyzed['corruption_score'].mean(),
            'judges_count': self.df['judge_full_name'].nunique(),
            'crime_types_count': self.df['crime_type'].nunique()
        }
