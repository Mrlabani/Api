import re
import logging
from urllib.parse import parse_qs, urlparse
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use the provided cookie
COOKIE = "browserid=KkqiaAO3p12oizrUcNK5p-GY29s-vV1iigMPSjxVwsniG-0evN4Kk3YfGsM=; lang=en; __bid_n=1928c0f31aeb2e65094207; __stripe_mid=ba71d03c-75a9-4504-aae2-ddc3d00744e07227ab; ndus=YQhUH3CteHuisY28unyKW-CLfFjxTknFOPm9rQkP; _ga=GA1.1.250660626.1728927138; ndut_fmt=9A1AAD656E4100E6655E3027B51639F402CF5DB5833899914679A0691EB248A8; _ga_06ZNKL8C2E=GS1.1.1728954768.2.0.1728954777.51.0.0; csrfToken=m11-xQY5Px2RsGgSaJp3BXGi"

# URL patterns for Terabox
def check_url_patterns(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]
    return any(re.search(pattern, url) for pattern in patterns)

def get_urls_from_string(string: str) -> list[str]:
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    return [url for url in urls if check_url_patterns(url)]

def find_between(data: str, first: str, last: str) -> str | None:
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None

def extract_surl_from_url(url: str) -> str | None:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("surl", [None])[0]

def get_data(url: str):
    session = requests.Session()
    headers = {
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    response = session.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses

    default_thumbnail = find_between(response.text, 'og:image" content="', '"')
    logid = find_between(response.text, "dp-logid=", "&")
    jsToken = find_between(response.text, "fn%28%22", "%22%29")
    shorturl = extract_surl_from_url(response.url)

    if not shorturl:
        logging.error("Short URL could not be extracted.")
        return {"error": "Invalid URL."}

    req_url = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken}&dp-logid={logid}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"
    response = session.get(req_url, headers=headers)
    response.raise_for_status()  # Raise an error for bad responses

    data = response.json()
    if data["errno"]:
        logging.error("Error in response data.")
        return {"error": "Error fetching data."}

    if "list" not in data or not data["list"]:
        logging.error("No files found.")
        return {"error": "No files found."}

    file_info = data["list"][0]
    direct_link_response = session.head(file_info["dlink"], headers=headers)
    direct_link = direct_link_response.headers.get("location")

    return {
        "file_name": file_info.get("server_filename"),
        "link": file_info.get("dlink"),
        "direct_link": direct_link,
        "thumb": file_info.get("thumbs", {}).get("url3") or default_thumbnail,
        "size": file_info.get("size"),
    }

@app.route('/download', methods=['GET'])
def download():
    try:
        url = request.args.get('url')
        if not url:
            logging.error("URL parameter is missing.")
            return jsonify({"error": "URL parameter is missing."}), 400

        data = get_data(url)
        if "error" in data:
            return jsonify(data), 400
        
        return jsonify(data), 200

    except Exception as e:
        logging.exception("An error occurred while processing the request.")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True)
