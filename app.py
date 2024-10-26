import logging
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Replace with your actual cookie
COOKIE = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.1024terabox.com TRUE / FALSE 1734110657 browserid KkqiaAO3p12oizrUcNK5p-GY29s-vV1iigMPSjxVwsniG-0evN4Kk3YfGsM=
.1024terabox.com TRUE / FALSE 1731519259 lang en
.1024terabox.com TRUE / FALSE 1763514767 __bid_n 1928c0f31aeb2e65094207
.www.1024terabox.com TRUE / TRUE 1760462675 __stripe_mid ba71d03c-75a9-4504-aae2-ddc3d00744e07227ab
.1024terabox.com TRUE / TRUE 1760462688 ndus YQhUH3CteHuisY28unyKW-CLfFjxTknFOPm9rQkP
.1024terabox.com TRUE / FALSE 1763514768 _ga GA1.1.250660626.1728927138
www.1024terabox.com FALSE / FALSE 1731546766 ndut_fmt 9A1AAD656E4100E6655E3027B51639F402CF5DB5833899914679A0691EB248A8
.1024terabox.com TRUE / FALSE 1763514777 _ga_06ZNKL8C2E GS1.1.1728954768.2.0.1728954777.51.0.0
www.terabox.com FALSE / FALSE 0 csrfToken m11-xQY5Px2RsGgSaJp3BXGi
.terabox.com TRUE / FALSE 1734139217 browserid ouU6uRozT6X1tJt8SOFi2YjzGCYcUTAGDs6vbOk2vD5ITkUP2Bbo2ZEAUCI=
.terabox.com TRUE / FALSE 1731547254 lang en
.terabox.com TRUE / FALSE 1763515260 __bid_n 1928dc2ff82c89d1af4207
.ymg-api.terabox.com TRUE / TRUE 1763515263 ab_jid dc6e96b3fb153bbe713dd28f05fc110e392b
.terabox.com TRUE / TRUE 1760491244 ndus YQhUH3CteHuiBsaOUy0faM-WT6TLhlQ1UcX32w37
www.terabox.com FALSE / FALSE 1731547260 ndut_fmt 9C5DFE0581A745A9AD4B0B634DC2B5F5E49D67EB9E62DF923B9E72B16830D23A
.ymg-api.terabox.com TRUE / TRUE 1763515263 ab_bid 96b3fb153bbe713dd28f05fc110e392c0799
.terabox.com TRUE / TRUE 1728962463 ab_sr 1.0.1_MzBhNjVhMWZkOGM5YjhhOTU1MTk3ZTg2YWFkYzUxYmVlZmUzMjkwZTliMjE5NWM2ZjdkNmRkMGJjZjM2NzA1MDNhMGNkODUxNGI2YWI0NDkzMWFkZGYwM2QyMzhmZDRmNGQ4NDc1MzBjZGM4ZjM0ZGE0YzI5MmNlYTQxM2FkYTQ1NDUzNjA4NGQ5M2FmYTMyZTk2MDhhOTk1NzcwNTk4Mw==
.terabox.com TRUE / FALSE 0 ab_ymg_result {"data":"db3b45abc88381d662d3c3d6b94d25f188b52b76f8d486cfdfccfdc7599c6f81273db9bcd70dd1c5bf62080dd6964e8792daebccefc2f9d5ed8e423af125086031a0ea8169d6348818af2fe233c6f01a9b60428b82c9ce78dfeef2300292898faa2835199a4decb60d2b1e687784a99901e611ce1ac215d79cf950fd8a573de5","key_id":"66","sign":"e0cdc5eb"}
.terabox.com TRUE / FALSE 1763515265 _ga GA1.1.505789176.1728955266
.terabox.com TRUE / FALSE 1763515280 _ga_06ZNKL8C2E GS1.1.1728955265.1.1.1728955280.45.0.0"""

def get_data(url: str):
    try:
        session = requests.Session()
        headers = {
            "Cookie": COOKIE,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        }

        logging.info("Making request to URL: %s", url)
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        logging.info("Received response: %s", response.text)
        
        # Process the response as needed
        # Example: return JSON or relevant data
        return response.json()  # Adjust according to the expected response format

    except requests.RequestException as e:
        logging.error("Request failed: %s", str(e))
        return {"error": "Failed to retrieve the URL."}

@app.route('/download', methods=['GET'])
def download():
    try:
        url = request.args.get('url')
        if not url:
            logging.error("URL parameter is missing.")
            return jsonify({"error": "URL parameter is missing."}), 400

        data = get_data(url)
        if "error" in data:
            logging.error(data["error"])  # Log specific error from get_data
            return jsonify(data), 400
        
        return jsonify(data), 200

    except Exception as e:
        logging.exception("An error occurred while processing the request: %s", str(e))
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True)
