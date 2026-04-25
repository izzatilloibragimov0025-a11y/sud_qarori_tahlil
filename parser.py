import os
import requests
import time

download_folder = "sud_pdf_fayllari"
os.makedirs(download_folder, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# Bizda tayyor, ochiq ID raqamlar bor (Tashqaridan qidirish shart emas!)
claim_ids = [
    1340426, 1502735, 1476730, 1485883, 1485848, 1529672, 1540114, 1534374,
    1524187, 1532764, 1539878, 1546876, 1577867, 1677342, 1681013, 1689607,
    1778578, 1877734, 1874335, 1932239, 1974656, 1977422, 1993799, 2022742,
    2040504, 2038723, 2092161, 2078601, 2090789, 2101568, 3107669, 3115589, 3097488, 3109388, 3096076, 3111267, 3103220, 3073833,
    3084644, 3103163, 3127862, 3126855, 3114349, 3111461, 3068480, 3084064,
    3081282, 3130711, 3130230, 3129436, 3129900, 3105362, 3099421, 3107677,
    3064492, 3092543, 3097887, 3097921, 3082226, 3114271
]

print(f"📥 60 ta tayyor PDF fayllarni tortib olish boshlandi...")

for i, claim_id in enumerate(claim_ids):
    # Bu fayl yuklash API'si, u ochiq! (404 bermaydi)
    pdf_url = f"https://publication.sud.uz/api/file/criminal/{claim_id}/"
    file_path = os.path.join(download_folder, f"ID_{claim_id}.pdf")
    
    try:
        pdf_response = requests.get(pdf_url, headers=headers)
        if pdf_response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(pdf_response.content)
            print(f"[{i+1}/60] Yuklandi: ID_{claim_id}.pdf ✅")
        time.sleep(1) 
    except Exception as e:
        print(f"Xato: {e}")

print("\n🎉 HAMMASI TAYYOR! AI GA O'TAMIZ!")