import re
from urllib.parse import parse_qs, urlparse
import requests
from flask import Flask, jsonify, request
import logging
from config import COOKIE
from tools import get_formatted_size

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

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
    
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False

def get_urls_from_string(string: str) -> list[str]:
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    return urls[0] if urls else []

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
    logging.info(f"Fetching data for URL: {url}")

    if not check_url_patterns(url):
        logging.error("Invalid Terabox URL.")
        return {"error": "Invalid Terabox URL"}, 400

    session = requests.Session()
    headers = {
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    # Step 1: Get the initial response
    response = session.get(url, headers=headers)
    logging.info(f"Initial response status code: {response.status_code}")

    if response.status_code != 200:
        logging.error(f"Failed to access the provided URL: {response.text}")
        return {"error": "Failed to access the provided URL"}, 404

    default_thumbnail = find_between(response.text, 'og:image" content="', '"')
    logid = find_between(response.text, "dp-logid=", "&")
    jsToken = find_between(response.text, "fn%28%22", "%22%29")
    bdstoken = find_between(response.text, 'bdstoken":"', '"')
    shorturl = extract_surl_from_url(response.url)
    
    if not shorturl:
        return {"error": "Short URL could not be extracted."}, 400

    reqUrl = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken}&dp-logid={logid}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"

    response = session.get(reqUrl, headers=headers)
    logging.info(f"List response status code: {response.status_code}")

    if response.status_code != 200:
        logging.error(f"Failed to fetch list: {response.text}")
        return {"error": "Failed to fetch list."}, 404

    r_j = response.json()
    if r_j.get("errno"):
        logging.error(f"Error in response: {r_j['errno']}")
        return {"error": "Error in response from Terabox."}, 400

    if "list" not in r_j or not r_j["list"]:
        return {"error": "No files found."}, 404

    file_info = r_j["list"][0]
    direct_response = session.head(file_info["dlink"], headers=headers)
    direct_link = direct_response.headers.get("location")

    data = {
        "file_name": file_info.get("server_filename"),
        "link": file_info.get("dlink"),
        "direct_link": direct_link,
        "thumb": file_info.get("thumbs", {}).get("url3", default_thumbnail),
        "size": get_formatted_size(int(file_info["size"])),
        "sizebytes": int(file_info["size"])
    }

    return data

@app.route('/download', methods=['GET'])
def download():
    try:
        url = request.args.get('url')
        if not url:
            logging.error("URL parameter is missing.")
            return jsonify({"error": "URL parameter is missing."}), 400
        
        data = get_data(url)
        return jsonify(data), (data.get('error') and 400) or 200
    
    except Exception as e:
        logging.exception("An error occurred while processing the request.")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
