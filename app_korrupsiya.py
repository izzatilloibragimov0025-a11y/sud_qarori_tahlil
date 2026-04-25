#!/usr/bin/env python3
"""
Flask Web Application - Korrupsiya Aniqlash Tizimi
"""
from flask import Flask, request, jsonify, send_file
import os
import json
from werkzeug.utils import secure_filename
from deepseek_extractor import DeepSeekExtractor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_api_key():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DEEPSEEK_API_KEY='):
                    return line.split('=')[1].strip()
    return None

@app.route('/')
def index():
    """Korrupsiya dashboard"""
    return send_file('korrupsiya_dashboard.html')

@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """PDF yuklash va tahlil qilish"""
    if 'file' not in request.files:
        return jsonify({'error': 'Fayl topilmadi'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'Fayl tanlanmadi'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Faqat PDF fayllar qabul qilinadi'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        api_key = get_api_key()
        if not api_key:
            return jsonify({'error': 'API kaliti topilmadi'}), 500
        
        extractor = DeepSeekExtractor(api_key)
        result = extractor.extract_from_pdf(filepath)
        
        os.remove(filepath)
        
        # Risk hisoblash
        risk_score = calculate_risk(result)
        result['risk_score'] = risk_score['score']
        result['risk_level'] = risk_score['level']
        result['risk_factors'] = risk_score['factors']
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_risk(case):
    """Bitta ish uchun risk hisoblash"""
    score = 0
    factors = []
    
    # Mansabdor
    if case.get('is_government_official'):
        score += 30
        factors.append("Mansabdor shaxs")
        
        if not case.get('punishment_years'):
            score += 20
            factors.append("Jazo ma'lumoti yo'q")
    
    # Zarar va jarima
    damage = case.get('damage_amount') or 0
    fine = case.get('fine_amount') or 0
    
    if damage > 0:
        if fine == 0:
            score += 25
            factors.append(f"Zarar {damage:,.0f} so'm, jarima yo'q")
        elif fine > 0 and fine < damage * 0.1:
            score += 20
            factors.append(f"Jarima juda kam ({fine/damage*100:.1f}%)")
    
    # Zarar qoplanmagan
    if case.get('damage_compensated') == False and damage > 0:
        score += 15
        factors.append("Zarar qoplanmagan")
    
    # Og'irlashtiruvchi holatlar
    aggravating = case.get('aggravating_circumstances')
    if aggravating and len(aggravating) > 0:
        score += 10
        factors.append(f"{len(aggravating)} ta og'irlashtiruvchi holat")
    
    # Daraja
    if score >= 70:
        level = "JUDA YUQORI"
    elif score >= 50:
        level = "YUQORI"
    elif score >= 30:
        level = "O'RTA"
    else:
        level = "PAST"
    
    return {
        'score': max(0, min(100, score)),
        'level': level,
        'factors': factors
    }

@app.route('/upload')
def upload_page():
    """PDF yuklash sahifasi"""
    html = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 PDF Yuklash - Korrupsiya Aniqlash</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 700px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #dc2626;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        p {
            color: #64748b;
            margin-bottom: 30px;
        }
        
        .upload-area {
            border: 3px dashed #cbd5e0;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        
        .upload-area:hover {
            border-color: #dc2626;
            background: #fef2f2;
        }
        
        .upload-icon {
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s ease;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .result {
            margin-top: 30px;
            padding: 25px;
            border-radius: 10px;
            display: none;
        }
        
        .result.success {
            background: #f0fdf4;
            border: 2px solid #10b981;
            display: block;
        }
        
        .result.warning {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            display: block;
        }
        
        .result.danger {
            background: #fef2f2;
            border: 2px solid #dc2626;
            display: block;
        }
        
        .result.error {
            background: #fef2f2;
            border: 2px solid #dc2626;
            display: block;
        }
        
        .risk-badge {
            display: inline-block;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 18px;
            font-weight: 700;
            color: white;
            margin: 15px 0;
        }
        
        .risk-factors {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        .risk-factors ul {
            list-style: none;
            padding: 0;
        }
        
        .risk-factors li {
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }
        
        .risk-factors li:before {
            content: "⚠️";
            position: absolute;
            left: 0;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #dc2626;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #dc2626;
            text-decoration: none;
            font-weight: 600;
        }
        
        .back-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚨 Sud Qarorini Tahlil Qilish</h1>
        <p>PDF faylni yuklang, AI korrupsiya xavfini baholaydi</p>
        
        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📄</div>
            <div class="upload-text">PDF faylni bu yerga tashlang yoki bosib tanlang</div>
        </div>
        
        <input type="file" id="fileInput" accept=".pdf">
        
        <button class="btn" id="uploadBtn" disabled>🔍 Tahlil Qilish</button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>AI tahlil qilmoqda... Iltimos kuting</p>
        </div>
        
        <div class="result" id="result"></div>
        
        <a href="/" class="back-link">← Dashboardga qaytish</a>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        
        let selectedFile = null;
        
        uploadArea.addEventListener('click', () => fileInput.click());
        
        fileInput.addEventListener('change', (e) => {
            selectedFile = e.target.files[0];
            if (selectedFile) {
                uploadArea.querySelector('.upload-text').textContent = selectedFile.name;
                uploadBtn.disabled = false;
            }
        });
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#dc2626';
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.style.borderColor = '#cbd5e0';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                selectedFile = files[0];
                fileInput.files = files;
                uploadArea.querySelector('.upload-text').textContent = selectedFile.name;
                uploadBtn.disabled = false;
            }
        });
        
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            uploadBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                loading.style.display = 'none';
                
                if (data.error) {
                    result.className = 'result error';
                    result.innerHTML = `<strong>❌ Xato:</strong> ${data.error}`;
                } else {
                    const riskColor = data.risk_score >= 70 ? '#dc2626' : 
                                     data.risk_score >= 50 ? '#ea580c' :
                                     data.risk_score >= 30 ? '#f59e0b' : '#10b981';
                    
                    const resultClass = data.risk_score >= 50 ? 'danger' :
                                       data.risk_score >= 30 ? 'warning' : 'success';
                    
                    result.className = `result ${resultClass}`;
                    result.innerHTML = `
                        <h2 style="margin-bottom: 15px;">📊 Tahlil Natijalari</h2>
                        
                        <div class="risk-badge" style="background: ${riskColor}">
                            🚨 Korrupsiya Xavfi: ${data.risk_score}% - ${data.risk_level}
                        </div>
                        
                        <div style="margin-top: 20px;">
                            <strong>📄 Ish raqami:</strong> ${data.case_id || '-'}<br>
                            <strong>👨‍⚖️ Sudya:</strong> ${data.judge_full_name || '-'}<br>
                            <strong>👤 Ayblanuvchi:</strong> ${data.defendant_name || '-'}<br>
                            <strong>⚖️ Jinoyat:</strong> ${data.crime_type || '-'}<br>
                            <strong>📜 Moddalar:</strong> ${data.articles ? data.articles.join(', ') : '-'}<br>
                            <strong>👔 Mansabdor:</strong> ${data.is_government_official ? 'Ha ⚠️' : 'Yo\'q'}
                        </div>
                        
                        ${data.risk_factors && data.risk_factors.length > 0 ? `
                        <div class="risk-factors">
                            <strong>⚠️ Shubhali Belgilar:</strong>
                            <ul>
                                ${data.risk_factors.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                    `;
                }
                
                uploadBtn.disabled = false;
            } catch (error) {
                loading.style.display = 'none';
                result.className = 'result error';
                result.innerHTML = `<strong>❌ Xato:</strong> ${error.message}`;
                uploadBtn.disabled = false;
            }
        });
    </script>
</body>
</html>"""
    return html

if __name__ == '__main__':
    print("=" * 60)
    print("🚨 Korrupsiya Aniqlash Web Tizimi")
    print("=" * 60)
    print("\n📊 Dashboard: http://localhost:5000")
    print("📤 PDF Yuklash: http://localhost:5000/upload")
    print("\n⏹️  To'xtatish: Ctrl+C\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
