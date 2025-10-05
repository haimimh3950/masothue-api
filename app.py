from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time, re

app = Flask(__name__)
CORS(app)

def shorten_company_name(raw):
    if not raw:
        return ""
    s = " ".join(raw.split())
    abbr = {
        "Doanh Nghiệp Tư Nhân": "DNTN",
        "Trách Nhiệm Hữu Hạn": "TNHH",
        "Một Thành Viên": "MTV",
        "Cổ Phần": "CP",
        "Kinh Doanh": "KD",
        "Thương Mại": "TM",
        "Dịch Vụ": "DV",
        "Sản Xuất": "SX",
        "Xây Dựng": "XD",
        "Vận Tải": "VT"
    }
    for k, v in abbr.items():
        s = re.sub(k, v, s, flags=re.I)
    # viết hoa chữ cái đầu
    s = " ".join([w.capitalize() if w.upper() not in abbr.values() else w.upper() for w in s.split()])
    return s

def normalize_address(addr):
    if not addr:
        return ""
    s = re.sub(r"(?i)^địa chỉ thuế[:\s]*", "", addr)
    s = re.sub(r",?\s*Việt Nam$", "", s)
    s = re.sub(r"(?i)(Tỉnh|Thành phố|Phường|Xã|Huyện|Thị xã|Thị trấn)\s+", "", s)
    return s.strip()

@app.route("/api/mst")
def api_mst():
    code = request.args.get("code", "").strip()
    if not re.match(r"^\d{10}(-\d{3})?$", code):
        return jsonify({"error":"MST không hợp lệ"}), 400
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Bước 1: mở trang tìm kiếm
        driver.get(f"https://www.masothue.com/Search?q={code}")
        time.sleep(1.5)

        # Bước 2: click vào dòng đầu tiên để vào link chi tiết
        try:
            first = driver.find_element(By.CSS_SELECTOR, "table.table-striped tbody tr td a")
            first.click()
            time.sleep(1.2)
        except:
            pass

        # Bước 3: lấy HTML của trang chi tiết
        html = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        name = soup.select_one("h1 span.copy")
        tax = soup.select_one("td[itemprop='taxID'] span.copy")
        addr = soup.select_one("td[itemprop='address'] span.copy")

        name_text = name.text.strip() if name else ""
        tax_text = tax.text.strip() if tax else code
        addr_text = addr.text.strip() if addr else ""

        if not name_text:
            return jsonify({"error":"Không tìm thấy thông tin doanh nghiệp."}), 404

        # Chuẩn hóa lại
        nameU = shorten_company_name(name_text)
        addrU = normalize_address(addr_text)

        return jsonify({
            "tax_code": tax_text,
            "name_unicode": nameU,
            "addr_unicode": addrU
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
