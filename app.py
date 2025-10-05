from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time, re

app = Flask(__name__)
CORS(app)

def shorten_company_name(raw):
    if not raw: return ""
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
    return s

def normalize_address(addr):
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
        # Cấu hình Chrome headless
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(f"https://www.masothue.com/Search?q={code}")
        time.sleep(2)

        try:
            first = driver.find_element(By.CSS_SELECTOR, ".table.table-striped tbody tr td a")
            first.click()
            time.sleep(1)
        except:
            pass

        soup = BeautifulSoup(driver.page_source, "html.parser")
        name = soup.select_one("h1 span.copy")
        tax = soup.select_one("td[itemprop='taxID'] span.copy")
        addr = soup.select_one("td[itemprop='address'] span.copy")

        name = name.text.strip() if name else ""
        tax = tax.text.strip() if tax else code
        addr = addr.text.strip() if addr else ""

        driver.quit()

        nameU = shorten_company_name(name)
        addrU = normalize_address(addr)

        return jsonify({
            "name_unicode": nameU,
            "tax_code": tax,
            "addr_unicode": addrU
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
