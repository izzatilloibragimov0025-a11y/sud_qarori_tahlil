"""
Grafiklar va vizualizatsiya yaratish
"""
import pandas as pd
from typing import Dict, List

class ChartGenerator:
    """Grafiklar uchun HTML/CSS kod yaratish"""
    
    @staticmethod
    def generate_bar_chart(data: Dict[str, float], title: str, color: str = "#3498db") -> str:
        """Bar chart HTML"""
        max_value = max(data.values()) if data else 1
        
        html = f'<div class="chart-container"><h3 class="chart-title">{title}</h3><div class="bar-chart">'
        
        for label, value in sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (value / max_value * 100) if max_value > 0 else 0
            html += f'''
            <div class="bar-item">
                <div class="bar-label">{label}</div>
                <div class="bar-wrapper">
                    <div class="bar-fill" style="width: {percentage}%; background: {color}"></div>
                    <div class="bar-value">{value:.1f}</div>
                </div>
            </div>
            '''
        
        html += '</div></div>'
        return html
    
    @staticmethod
    def generate_pie_chart(data: Dict[str, int], title: str) -> str:
        """Pie chart HTML (CSS-based)"""
        total = sum(data.values())
        if total == 0:
            return ""
        
        colors = ['#e74c3c', '#f39c12', '#27ae60', '#3498db', '#9b59b6']
        
        html = f'<div class="chart-container"><h3 class="chart-title">{title}</h3>'
        html += '<div class="pie-chart-container">'
        
        # Legend
        html += '<div class="pie-legend">'
        for i, (label, value) in enumerate(data.items()):
            percentage = (value / total * 100)
            color = colors[i % len(colors)]
            html += f'''
            <div class="legend-item">
                <div class="legend-color" style="background: {color}"></div>
                <div class="legend-text">{label}: {value} ({percentage:.1f}%)</div>
            </div>
            '''
        html += '</div>'
        
        # Simple visual representation
        html += '<div class="pie-visual">'
        cumulative = 0
        for i, (label, value) in enumerate(data.items()):
            percentage = (value / total * 100)
            color = colors[i % len(colors)]
            html += f'<div class="pie-segment" style="width: {percentage}%; background: {color}"></div>'
        html += '</div>'
        
        html += '</div></div>'
        return html
    
    @staticmethod
    def generate_timeline(cases_df: pd.DataFrame) -> str:
        """Vaqt bo'yicha timeline"""
        if 'date' not in cases_df.columns:
            return ""
        
        # Oylar bo'yicha guruhlash
        cases_df['month'] = pd.to_datetime(cases_df['date'], errors='coerce').dt.to_period('M')
        monthly_counts = cases_df.groupby('month').size().to_dict()
        
        html = '<div class="chart-container"><h3 class="chart-title">📅 Oylik Statistika</h3>'
        html += '<div class="timeline">'
        
        for month, count in sorted(monthly_counts.items()):
            if pd.notna(month):
                html += f'''
                <div class="timeline-item">
                    <div class="timeline-date">{month}</div>
                    <div class="timeline-count">{count} ta ish</div>
                </div>
                '''
        
        html += '</div></div>'
        return html
    
    @staticmethod
    def get_chart_styles() -> str:
        """Chart CSS stillari"""
        return """
        <style>
        .chart-container {
            margin: 30px 0;
            padding: 25px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .chart-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2c3e50;
        }
        
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .bar-item {
            display: grid;
            grid-template-columns: 200px 1fr;
            gap: 15px;
            align-items: center;
        }
        
        .bar-label {
            font-size: 13px;
            color: #2c3e50;
            font-weight: 500;
        }
        
        .bar-wrapper {
            position: relative;
            height: 30px;
            background: #ecf0f1;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .bar-fill {
            height: 100%;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
        }
        
        .bar-value {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .pie-chart-container {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        
        .pie-legend {
            flex: 1;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        
        .legend-text {
            font-size: 13px;
            color: #2c3e50;
        }
        
        .pie-visual {
            flex: 1;
            height: 40px;
            display: flex;
            border-radius: 8px;
            overflow: hidden;
        }
        
        .pie-segment {
            height: 100%;
        }
        
        .timeline {
            display: flex;
            gap: 15px;
            overflow-x: auto;
            padding: 10px 0;
        }
        
        .timeline-item {
            min-width: 120px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .timeline-date {
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        
        .timeline-count {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
        }
        </style>
        """
