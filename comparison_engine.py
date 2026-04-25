"""
O'xshash ishlarni taqqoslash va farqlarni aniqlash
"""
import pandas as pd
from typing import List, Dict, Tuple

class CaseComparisonEngine:
    """Ishlarni taqqoslash va farqlarni aniqlash"""
    
    def __init__(self, cases_df: pd.DataFrame):
        self.df = cases_df
    
    def find_similar_cases_detailed(self, case_id: str) -> List[Dict]:
        """Berilgan ishga o'xshash ishlarni topish"""
        target_case = self.df[self.df['case_id'] == case_id].iloc[0] if len(self.df[self.df['case_id'] == case_id]) > 0 else None
        
        if target_case is None:
            return []
        
        similar_cases = []
        
        # Bir xil jinoyat turi
        same_crime = self.df[
            (self.df['crime_type'] == target_case['crime_type']) &
            (self.df['case_id'] != case_id)
        ]
        
        for _, case in same_crime.iterrows():
            similarity_score = self._calculate_similarity(target_case, case)
            differences = self._find_differences(target_case, case)
            
            similar_cases.append({
                'case_id': case['case_id'],
                'similarity_score': similarity_score,
                'differences': differences,
                'case_data': case.to_dict()
            })
        
        return sorted(similar_cases, key=lambda x: x['similarity_score'], reverse=True)[:5]
    
    def _calculate_similarity(self, case1: pd.Series, case2: pd.Series) -> float:
        """Ikkita ish o'rtasidagi o'xshashlik foizi"""
        score = 0
        total = 0
        
        # Jinoyat turi
        if case1.get('crime_type') == case2.get('crime_type'):
            score += 20
        total += 20
        
        # Moddalar
        if str(case1.get('articles')) == str(case2.get('articles')):
            score += 15
        total += 15
        
        # Mansabdor
        if case1.get('is_government_official') == case2.get('is_government_official'):
            score += 15
        total += 15
        
        # Zarar miqdori (±30% oralig'ida)
        if pd.notna(case1.get('damage_amount')) and pd.notna(case2.get('damage_amount')):
            ratio = min(case1['damage_amount'], case2['damage_amount']) / max(case1['damage_amount'], case2['damage_amount'])
            if ratio >= 0.7:
                score += 20
        total += 20
        
        # Zarar qoplangan
        if case1.get('damage_compensated') == case2.get('damage_compensated'):
            score += 10
        total += 10
        
        # Og'irlashtiruvchi holatlar
        if len(case1.get('aggravating_circumstances', [])) == len(case2.get('aggravating_circumstances', [])):
            score += 10
        total += 10
        
        # Yengillashtiruvchi holatlar
        if len(case1.get('mitigating_circumstances', [])) == len(case2.get('mitigating_circumstances', [])):
            score += 10
        total += 10
        
        return (score / total * 100) if total > 0 else 0
    
    def _find_differences(self, case1: pd.Series, case2: pd.Series) -> List[str]:
        """Farqlarni topish"""
        differences = []
        
        # Jazo farqi
        if pd.notna(case1.get('punishment_years')) and pd.notna(case2.get('punishment_years')):
            diff = abs(case1['punishment_years'] - case2['punishment_years'])
            if diff > 1:
                differences.append(f"Jazo farqi: {diff:.1f} yil")
        
        # Jarima farqi
        if pd.notna(case1.get('fine_amount')) and pd.notna(case2.get('fine_amount')):
            diff_pct = abs(case1['fine_amount'] - case2['fine_amount']) / max(case1['fine_amount'], case2['fine_amount']) * 100
            if diff_pct > 30:
                differences.append(f"Jarima farqi: {diff_pct:.0f}%")
        
        # Sudya farqi
        if case1.get('judge_full_name') != case2.get('judge_full_name'):
            differences.append(f"Turli sudyalar: {case1.get('judge_full_name')} vs {case2.get('judge_full_name')}")
        
        # Zarar qoplangan farqi
        if case1.get('damage_compensated') != case2.get('damage_compensated'):
            differences.append("Zarar qoplash holati farq qiladi")
        
        return differences
    
    def generate_comparison_report(self, case_id: str) -> str:
        """Taqqoslash hisoboti HTML"""
        similar_cases = self.find_similar_cases_detailed(case_id)
        
        if not similar_cases:
            return "<p>O'xshash ishlar topilmadi</p>"
        
        html = '<div class="comparison-section">'
        html += f'<h3>Ish #{case_id} ga o\'xshash ishlar</h3>'
        
        for i, similar in enumerate(similar_cases, 1):
            html += f'''
            <div class="comparison-card">
                <div class="comparison-header">
                    <span class="comparison-rank">#{i}</span>
                    <span class="comparison-case">Ish #{similar['case_id']}</span>
                    <span class="comparison-score">{similar['similarity_score']:.0f}% o'xshash</span>
                </div>
                <div class="comparison-differences">
                    <strong>Farqlar:</strong>
                    <ul>
                        {''.join([f'<li>{diff}</li>' for diff in similar['differences']])}
                    </ul>
                </div>
            </div>
            '''
        
        html += '</div>'
        return html
