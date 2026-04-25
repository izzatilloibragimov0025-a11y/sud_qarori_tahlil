#!/usr/bin/env python3
"""
Korrupsiya Aniqlash Dashboard - Mavjud Modullar Bilan
"""
import json
import pandas as pd
from datetime import datetime
from collections import Counter, defaultdict
from advanced_analyzer import AdvancedKorrupsiyaAnalyzer

def create_corruption_dashboard():
    """Korrupsiya aniqlash dashboard - advanced_analyzer ishlatib"""
    
    # Ma'lumotlarni o'qish
    with open('deepseek_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid = [r for r in data if 'error' not in r]
    
    # DataFrame yaratish
    df = pd.DataFrame(valid)
    
    # AdvancedKorrupsiyaAnalyzer ishlatish
    analyzer = AdvancedKorrupsiyaAnalyzer(df)
    
    # Barcha ishlarni tahlil qilish
    analyzed_df = analyzer.analyze_all_cases()
    
    # Sudyalar reytingi
    judge_rating = analyzer.get_judge_rating()
    
    # Statistika
    stats = analyzer.get_statistics()
    
    # Risk case larni dict ga o'girish
    risk_cases = []
    for _, row in analyzed_df.iterrows():
        case = valid[_] if _ < len(valid) else {}
        risk_cases.append({
            'case': case,
            'risk_score': row['corruption_score'],
            'risk_level': row['corruption_level'],
            'risk_color': get_risk_color(row['corruption_score']),
            'risk_factors': row['reasons'].split(' | ') if row['reasons'] else []
        })
    
    # Statistika hisoblash
    total = len(risk_cases)
    high_risk = sum(1 for rc in risk_cases if rc['risk_score'] >= 50)
    medium_risk = sum(1 for rc in risk_cases if 30 <= rc['risk_score'] < 50)
    low_risk = sum(1 for rc in risk_cases if rc['risk_score'] < 30)
    
    avg_risk = sum(rc['risk_score'] for rc in risk_cases) / total if total > 0 else 0
    
    # Shubhali sudyalar
    suspicious_judges = judge_rating[judge_rating['avg_corruption_score'] >= 30].to_dict('records')
    
    # HTML yaratish
    html = generate_html(risk_cases, suspicious_judges, stats, high_risk, medium_risk, low_risk, avg_risk)
    
    return html

def get_risk_color(score):
    """Risk rangini aniqlash"""
    if score >= 70:
        return "#dc2626"
    elif score >= 50:
        return "#ea580c"
    elif score >= 30:
        return "#f59e0b"
    else:
        return "#10b981"

def generate_html(risk_cases, suspicious_judges, stats, high_risk, medium_risk, low_risk, avg_risk):
    """HTML yaratish"""
    
    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Korrupsiya Aniqlash Tizimi - Sud Qarorlari Monitoring</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 16px;
        }}
        
        .alert-banner {{
            background: #fef3c7;
            color: #92400e;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #f59e0b;
        }}
        
        .alert-banner strong {{
            display: block;
            margin-bottom: 5px;
            font-size: 18px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-icon {{
            font-size: 40px;
            margin-bottom: 15px;
        }}
        
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            opacity: 0.8;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card.danger {{
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        }}
        
        .stat-card.warning {{
            background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
        }}
        
        .stat-card.success {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            color: #1e293b;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .card h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #dc2626;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.3s ease;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #dc2626;
        }}
        
        .risk-item {{
            background: #f8fafc;
            border-left: 5px solid;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: transform 0.2s ease;
        }}
        
        .risk-item:hover {{
            transform: translateX(5px);
        }}
        
        .risk-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .risk-title {{
            font-weight: 600;
            font-size: 16px;
        }}
        
        .risk-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            color: white;
        }}
        
        .risk-details {{
            color: #64748b;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        
        .risk-factors {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }}
        
        .risk-factors ul {{
            list-style: none;
            padding: 0;
        }}
        
        .risk-factors li {{
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
        }}
        
        .risk-factors li:before {{
            content: "⚠️";
            position: absolute;
            left: 0;
        }}
        
        .judge-item {{
            background: #f8fafc;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            border-left: 5px solid;
        }}
        
        .judge-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .judge-name {{
            font-weight: 600;
            font-size: 18px;
        }}
        
        .judge-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }}
        
        .judge-stat {{
            background: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        
        .judge-stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #dc2626;
        }}
        
        .judge-stat-label {{
            font-size: 12px;
            color: #64748b;
            margin-top: 5px;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #94a3b8;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>
                <span>🚨</span>
                <span>Korrupsiya Aniqlash Tizimi</span>
            </h1>
            <p>Sud Qarorlarini AI Tahlili va Shubhali Holatlarni Aniqlash | {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </div>
        
        <!-- Alert Banner -->
        {f'''
        <div class="alert-banner">
            <strong>⚠️ DIQQAT: {high_risk} ta yuqori xavfli ish aniqlandi!</strong>
            <p>{len(suspicious_judges)} ta sudyada shubhali faoliyat belgilari mavjud. Batafsil tahlil quyida.</p>
        </div>
        ''' if high_risk > 0 or suspicious_judges else ''}
        
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card danger">
                <div class="stat-icon">🔴</div>
                <div class="stat-value">{high_risk}</div>
                <div class="stat-label">Yuqori Xavf (50%+)</div>
            </div>
            
            <div class="stat-card warning">
                <div class="stat-icon">🟡</div>
                <div class="stat-value">{medium_risk}</div>
                <div class="stat-label">O'rta Xavf (30-49%)</div>
            </div>
            
            <div class="stat-card success">
                <div class="stat-icon">🟢</div>
                <div class="stat-value">{low_risk}</div>
                <div class="stat-label">Past Xavf (<30%)</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-value">{avg_risk:.1f}%</div>
                <div class="stat-label">O'rtacha Risk</div>
            </div>
        </div>
        
        <!-- High Risk Cases -->
        <div class="card">
            <h2>🚨 Yuqori Xavfli Ishlar</h2>
            <input type="text" class="search-box" id="caseSearch" placeholder="🔍 Qidirish: ish raqami, sudya, ayblanuvchi, jinoyat...">
            
            <div id="riskCases">
                {generate_risk_cases_html([rc for rc in risk_cases if rc['risk_score'] >= 50])}
            </div>
        </div>
        
        <!-- Suspicious Judges -->
        <div class="card">
            <h2>👨‍⚖️ Shubhali Sudyalar</h2>
            <input type="text" class="search-box" id="judgeSearch" placeholder="🔍 Sudya nomini qidirish...">
            
            <div id="judgeList">
                {generate_judges_html(suspicious_judges)}
            </div>
        </div>
        
        <!-- Medium Risk Cases -->
        <div class="card">
            <h2>🟡 O'rta Xavfli Ishlar</h2>
            <div id="mediumRiskCases">
                {generate_risk_cases_html([rc for rc in risk_cases if 30 <= rc['risk_score'] < 50])}
            </div>
        </div>
    </div>
    
    <script>
        // Case search
        document.getElementById('caseSearch').addEventListener('keyup', function() {{
            const searchValue = this.value.toLowerCase();
            const cases = document.querySelectorAll('#riskCases .risk-item');
            
            cases.forEach(caseItem => {{
                const text = caseItem.textContent.toLowerCase();
                caseItem.style.display = text.includes(searchValue) ? '' : 'none';
            }});
        }});
        
        // Judge search
        document.getElementById('judgeSearch').addEventListener('keyup', function() {{
            const searchValue = this.value.toLowerCase();
            const judges = document.querySelectorAll('#judgeList .judge-item');
            
            judges.forEach(judgeItem => {{
                const text = judgeItem.textContent.toLowerCase();
                judgeItem.style.display = text.includes(searchValue) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>"""
    
    return html

def generate_risk_cases_html(risk_cases):
    """Risk case lar uchun HTML"""
    if not risk_cases:
        return '<div class="no-results">🎉 Shubhali ishlar topilmadi</div>'
    
    html = ""
    for rc in risk_cases:
        case = rc['case']
        html += f'''
        <div class="risk-item" style="border-left-color: {rc['risk_color']}">
            <div class="risk-header">
                <div class="risk-title">
                    📄 {case.get('file_name', 'Noma\'lum')} - {case.get('case_id', '-')}
                </div>
                <div class="risk-badge" style="background: {rc['risk_color']}">
                    {rc['risk_score']:.0f}% - {rc['risk_level']}
                </div>
            </div>
            
            <div class="risk-details">
                <strong>👨‍⚖️ Sudya:</strong> {case.get('judge_full_name', '-')} | 
                <strong>👤 Ayblanuvchi:</strong> {case.get('defendant_name', '-')} | 
                <strong>⚖️ Jinoyat:</strong> {case.get('crime_type', '-')}
                {f" | <strong>👔 Lavozim:</strong> {case.get('defendant_position')}" if case.get('defendant_position') else ""}
            </div>
            
            {f"""
            <div class="risk-factors">
                <strong>⚠️ Shubhali Belgilar:</strong>
                <ul>
                    {''.join([f'<li>{factor}</li>' for factor in rc['risk_factors']])}
                </ul>
            </div>
            """ if rc['risk_factors'] else ""}
        </div>
        '''
    
    return html

def generate_judges_html(judges):
    """Sudyalar uchun HTML"""
    if not judges:
        return '<div class="no-results">🎉 Shubhali sudyalar topilmadi</div>'
    
    html = ""
    for judge in judges:
        avg_risk = judge.get('avg_corruption_score', 0)
        color = "#dc2626" if avg_risk >= 50 else "#ea580c" if avg_risk >= 30 else "#10b981"
        
        html += f'''
        <div class="judge-item" style="border-left-color: {color}">
            <div class="judge-header">
                <div class="judge-name">👨‍⚖️ {judge.get('judge_name', '-')}</div>
                <div class="risk-badge" style="background: {color}">
                    O'rtacha Risk: {avg_risk:.1f}%
                </div>
            </div>
            
            <div class="judge-stats">
                <div class="judge-stat">
                    <div class="judge-stat-value">{judge.get('total_cases', 0)}</div>
                    <div class="judge-stat-label">Jami Ishlar</div>
                </div>
                
                <div class="judge-stat">
                    <div class="judge-stat-value" style="color: #dc2626">{judge.get('high_risk_cases', 0)}</div>
                    <div class="judge-stat-label">Yuqori Xavf</div>
                </div>
                
                <div class="judge-stat">
                    <div class="judge-stat-value" style="color: #10b981">{judge.get('low_risk_cases', 0)}</div>
                    <div class="judge-stat-label">Past Xavf</div>
                </div>
                
                <div class="judge-stat">
                    <div class="judge-stat-value" style="color: #f59e0b">{judge.get('official_cases', 0)}</div>
                    <div class="judge-stat-label">Mansabdorlar</div>
                </div>
                
                <div class="judge-stat">
                    <div class="judge-stat-value" style="color: #dc2626">{judge.get('high_risk_percentage', 0):.1f}%</div>
                    <div class="judge-stat-label">Xavf Foizi</div>
                </div>
            </div>
        </div>
        '''
    
    return html

if __name__ == "__main__":
    print("🚨 Korrupsiya Aniqlash Dashboard yaratilmoqda...")
    print("📊 AdvancedKorrupsiyaAnalyzer ishlatilmoqda...")
    
    html = create_corruption_dashboard()
    
    with open('korrupsiya_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("✅ Dashboard yaratildi: korrupsiya_dashboard.html")
    print("🌐 Brauzerda ochish uchun: korrupsiya_dashboard.html")
