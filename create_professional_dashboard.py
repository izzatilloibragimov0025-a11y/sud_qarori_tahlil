#!/usr/bin/env python3
"""
Professional Dashboard - Davlat Tashkilotlari Uchun
Oddiy, Chiroyli, Qulay
"""
import json
import pandas as pd
from datetime import datetime
from collections import Counter
from advanced_analyzer import AdvancedKorrupsiyaAnalyzer

def create_dashboard():
    """Professional dashboard yaratish"""
    
    # Ma'lumotlarni o'qish
    with open('deepseek_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid = [r for r in data if 'error' not in r]
    df = pd.DataFrame(valid)
    
    # Analyzer
    analyzer = AdvancedKorrupsiyaAnalyzer(df)
    analyzed_df = analyzer.analyze_all_cases()
    judge_rating = analyzer.get_judge_rating()
    stats = analyzer.get_statistics()
    
    # Statistika
    total = len(valid)
    high_risk = stats['high_risk_cases']
    medium_risk = stats['medium_risk_cases']
    low_risk = stats['low_risk_cases']
    
    # Jinoyat turlari
    crimes = [r.get('crime_type') for r in valid if r.get('crime_type')]
    crime_counter = Counter(crimes)
    
    # Moddalar
    all_articles = []
    for r in valid:
        articles = r.get('articles')
        if articles and isinstance(articles, list):
            all_articles.extend([str(a) for a in articles])
    article_counter = Counter(all_articles)
    
    # HTML
    html = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sud Qarorlari Monitoring Tizimi</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚖️</text></svg>">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Times New Roman', Times, serif;
            background: #f5f5f5;
            color: #333;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
            color: white;
            padding: 30px 50px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .logo-icon {{
            font-size: 48px;
        }}
        
        .logo-text h1 {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .logo-text p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .header-date {{
            text-align: right;
            font-size: 14px;
        }}
        
        .nav {{
            background: white;
            padding: 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .nav-container {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            gap: 0;
        }}
        
        .nav-item {{
            flex: 1;
            padding: 15px 20px;
            text-align: center;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            background: white;
            color: #333;
            font-weight: 500;
        }}
        
        .nav-item:hover {{
            background: #f0f9ff;
            border-bottom-color: #1e40af;
        }}
        
        .nav-item.active {{
            background: #1e40af;
            color: white;
            border-bottom-color: #1e40af;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }}
        
        .section {{
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        
        .section.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 5px solid;
            transition: transform 0.2s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}
        
        .stat-card.danger {{ border-left-color: #dc2626; }}
        .stat-card.warning {{ border-left-color: #f59e0b; }}
        .stat-card.success {{ border-left-color: #10b981; }}
        .stat-card.info {{ border-left-color: #3b82f6; }}
        
        .stat-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .stat-icon {{
            font-size: 36px;
        }}
        
        .stat-value {{
            font-size: 42px;
            font-weight: bold;
            color: #1e293b;
        }}
        
        .stat-label {{
            color: #64748b;
            font-size: 14px;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .card {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .card-title {{
            font-size: 20px;
            font-weight: bold;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .search-box {{
            width: 100%;
            max-width: 400px;
            padding: 12px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.3s ease;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #1e40af;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f8fafc;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e5e7eb;
            font-size: 14px;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
        }}
        
        tr:hover {{
            background: #f8fafc;
        }}
        
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-danger {{ background: #fee2e2; color: #991b1b; }}
        .badge-warning {{ background: #fef3c7; color: #92400e; }}
        .badge-success {{ background: #d1fae5; color: #065f46; }}
        .badge-info {{ background: #dbeafe; color: #1e40af; }}
        
        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .chart-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #1e293b;
        }}
        
        .chart-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .chart-item:last-child {{
            border-bottom: none;
        }}
        
        .chart-label {{
            color: #475569;
            font-size: 14px;
        }}
        
        .chart-value {{
            font-weight: 600;
            color: #1e293b;
        }}
        
        .chart-bar {{
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 10px;
            margin-top: 8px;
            overflow: hidden;
        }}
        
        .chart-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #1e40af 0%, #3b82f6 100%);
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        
        .footer {{
            background: #1e293b;
            color: white;
            padding: 30px 50px;
            margin-top: 50px;
            text-align: center;
        }}
        
        .footer p {{
            opacity: 0.8;
            font-size: 14px;
        }}
        
        @media print {{
            .nav, .search-box {{ display: none; }}
            .stat-card {{ break-inside: avoid; }}
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .chart-container {{
                grid-template-columns: 1fr;
            }}
            
            .nav-container {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <div class="header-top">
            <div class="logo">
                <div class="logo-icon">⚖️</div>
                <div class="logo-text">
                    <h1>O'ZBEKISTON RESPUBLIKASI</h1>
                    <p>Sud Qarorlari Monitoring va Tahlil Tizimi</p>
                </div>
            </div>
            <div class="header-date">
                <div><strong>Hisobot sanasi:</strong></div>
                <div>{datetime.now().strftime('%d.%m.%Y')}</div>
                <div>{datetime.now().strftime('%H:%M')}</div>
            </div>
        </div>
    </div>
    
    <!-- Navigation -->
    <div class="nav">
        <div class="nav-container">
            <div class="nav-item active" onclick="showSection('overview')">📊 Umumiy Ko'rinish</div>
            <div class="nav-item" onclick="showSection('cases')">📋 Ishlar Ro'yxati</div>
            <div class="nav-item" onclick="showSection('judges')">👨‍⚖️ Sudyalar</div>
            <div class="nav-item" onclick="showSection('statistics')">📈 Statistika</div>
        </div>
    </div>
    
    <div class="container">
        <!-- Overview Section -->
        <div id="overview" class="section active">
            <div class="stats-grid">
                <div class="stat-card info">
                    <div class="stat-header">
                        <div class="stat-icon">📁</div>
                    </div>
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Jami Tahlil Qilingan Ishlar</div>
                </div>
                
                <div class="stat-card danger">
                    <div class="stat-header">
                        <div class="stat-icon">🔴</div>
                    </div>
                    <div class="stat-value">{high_risk}</div>
                    <div class="stat-label">Yuqori Xavfli Ishlar</div>
                </div>
                
                <div class="stat-card warning">
                    <div class="stat-header">
                        <div class="stat-icon">🟡</div>
                    </div>
                    <div class="stat-value">{medium_risk}</div>
                    <div class="stat-label">O'rta Xavfli Ishlar</div>
                </div>
                
                <div class="stat-card success">
                    <div class="stat-header">
                        <div class="stat-icon">🟢</div>
                    </div>
                    <div class="stat-value">{low_risk}</div>
                    <div class="stat-label">Past Xavfli Ishlar</div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-card">
                    <div class="chart-title">📊 Eng Ko'p Jinoyat Turlari</div>
                    {''.join([f'''
                    <div class="chart-item">
                        <div>
                            <div class="chart-label">{crime}</div>
                            <div class="chart-bar">
                                <div class="chart-bar-fill" style="width: {count/max(crime_counter.values())*100}%"></div>
                            </div>
                        </div>
                        <div class="chart-value">{count} ta</div>
                    </div>
                    ''' for crime, count in crime_counter.most_common(5)])}
                </div>
                
                <div class="chart-card">
                    <div class="chart-title">📜 Eng Ko'p Qo'llaniladigan Moddalar</div>
                    {''.join([f'''
                    <div class="chart-item">
                        <div>
                            <div class="chart-label">{article}-modda</div>
                            <div class="chart-bar">
                                <div class="chart-bar-fill" style="width: {count/max(article_counter.values())*100}%"></div>
                            </div>
                        </div>
                        <div class="chart-value">{count} ta</div>
                    </div>
                    ''' for article, count in article_counter.most_common(5)])}
                </div>
            </div>
        </div>
        
        <!-- Cases Section -->
        <div id="cases" class="section">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📋 Barcha Ishlar</div>
                    <input type="text" class="search-box" id="caseSearch" placeholder="🔍 Qidirish: ish raqami, sudya, ayblanuvchi...">
                </div>
                
                <table id="casesTable">
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Ish Raqami</th>
                            <th>Sana</th>
                            <th>Sudya</th>
                            <th>Ayblanuvchi</th>
                            <th>Jinoyat</th>
                            <th>Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{i+1}</td>
                            <td><strong>{row.get('case_id', '-')}</strong></td>
                            <td>{valid[i].get('date', '-')}</td>
                            <td>{row.get('judge', '-')}</td>
                            <td>{row.get('defendant', '-')}</td>
                            <td>{row.get('crime_type', '-')}</td>
                            <td>
                                <span class="badge badge-{'danger' if row['corruption_score'] >= 50 else 'warning' if row['corruption_score'] >= 30 else 'success'}">
                                    {row['corruption_score']:.0f}% - {row['corruption_level']}
                                </span>
                            </td>
                        </tr>
                        ''' for i, (_, row) in enumerate(analyzed_df.iterrows())])}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Judges Section -->
        <div id="judges" class="section">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">👨‍⚖️ Sudyalar Reytingi</div>
                    <input type="text" class="search-box" id="judgeSearch" placeholder="🔍 Sudya nomini qidirish...">
                </div>
                
                <table id="judgesTable">
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Sudya</th>
                            <th>Jami Ishlar</th>
                            <th>Yuqori Xavf</th>
                            <th>O'rta Xavf</th>
                            <th>Past Xavf</th>
                            <th>O'rtacha Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td>{i+1}</td>
                            <td><strong>{row['judge_name']}</strong></td>
                            <td>{row['total_cases']}</td>
                            <td><span class="badge badge-danger">{row['high_risk_cases']}</span></td>
                            <td><span class="badge badge-warning">{row.get('medium_risk_cases', 0)}</span></td>
                            <td><span class="badge badge-success">{row.get('low_risk_cases', 0)}</span></td>
                            <td><strong>{row['avg_corruption_score']:.1f}%</strong></td>
                        </tr>
                        ''' for i, row in enumerate(judge_rating.to_dict('records'))])}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Statistics Section -->
        <div id="statistics" class="section">
            <div class="stats-grid">
                <div class="stat-card info">
                    <div class="stat-icon">👔</div>
                    <div class="stat-value">{stats['official_cases']}</div>
                    <div class="stat-label">Mansabdorlar Ishlari</div>
                </div>
                
                <div class="stat-card info">
                    <div class="stat-icon">👨‍⚖️</div>
                    <div class="stat-value">{stats['judges_count']}</div>
                    <div class="stat-label">Sudyalar Soni</div>
                </div>
                
                <div class="stat-card info">
                    <div class="stat-icon">⚖️</div>
                    <div class="stat-value">{stats['crime_types_count']}</div>
                    <div class="stat-label">Jinoyat Turlari</div>
                </div>
                
                <div class="stat-card info">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">{stats['avg_corruption_score']:.1f}%</div>
                    <div class="stat-label">O'rtacha Risk Darajasi</div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">💰 Moliyaviy Ko'rsatkichlar</div>
                <table>
                    <tr>
                        <td><strong>Jami Zarar:</strong></td>
                        <td style="text-align: right;"><strong>{stats['total_damage']:,.0f} so'm</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Jami Jarima:</strong></td>
                        <td style="text-align: right;"><strong>{stats['total_fines']:,.0f} so'm</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Jarima/Zarar Nisbati:</strong></td>
                        <td style="text-align: right;"><strong>{stats['total_fines']/stats['total_damage']*100:.2f}%</strong></td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Footer -->
    <div class="footer">
        <p>© {datetime.now().year} O'zbekiston Respublikasi Sud Tizimi</p>
        <p>Sud Qarorlari Monitoring va Tahlil Tizimi</p>
    </div>
    
    <script>
        // Section navigation
        function showSection(sectionId) {{
            // Hide all sections
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            
            // Show selected section
            document.getElementById(sectionId).classList.add('active');
            event.target.classList.add('active');
        }}
        
        // Case search
        document.getElementById('caseSearch').addEventListener('keyup', function() {{
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#casesTable tbody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchValue) ? '' : 'none';
            }});
        }});
        
        // Judge search
        document.getElementById('judgeSearch').addEventListener('keyup', function() {{
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#judgesTable tbody tr');
            
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchValue) ? '' : 'none';
            }});
        }});
        
        // Animate bars on load
        window.addEventListener('load', function() {{
            const bars = document.querySelectorAll('.chart-bar-fill');
            bars.forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>"""
    
    return html

if __name__ == "__main__":
    print("=" * 60)
    print("📊 Professional Dashboard Yaratilmoqda...")
    print("=" * 60)
    
    html = create_dashboard()
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("\n✅ Dashboard yaratildi!")
    print("\n📁 Fayl: index.html")
    print("🌐 Ochish: Faylni ikki marta bosing yoki brauzerga torting")
    print("\n" + "=" * 60)
