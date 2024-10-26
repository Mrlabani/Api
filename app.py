import re
from urllib.parse import parse_qs, urlparse
import requests
from flask import Flask, jsonify, request
from config import COOKIE  # Ensure your COOKIE is correctly set in the config
from tools import get_formatted_size  # Adjust import as necessary

app = Flask(__name__)

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

def extract_surl_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("surl", [None])[0]

def get_data(url):
    if not check_url_patterns(url):
        return {"error": "Invalid Terabox URL"}, 400

    session = requests.Session()
    headers = {
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    # Step 1: Get the initial response
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": "Failed to access the provided URL"}, 404

    # Step 2: Parse response for necessary tokens and parameters
    logid = re.search(r"dp-logid=(.*?)(?:&|$)", response.text)
    jsToken = re.search(r"fn%28%22(.*?)%22%29", response.text)
    shorturl = extract_surl_from_url(response.url)

    if not logid or not jsToken or not shorturl:
        return {"error": "Failed to extract necessary tokens"}, 400

    # Step 3: Prepare the request for file list
    req_url = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken.group(1)}&dp-logid={logid.group(1)}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"
    response = session.get(req_url, headers=headers)

    if response.status_code != 200 or response.json().get("errno"):
        return {"error": "Failed to retrieve file information"}, 404

    data = response.json().get("list", [])
    if not data:
        return {"error": "No files found"}, 404

    file_info = data[0]  # Assuming you want the first file
    direct_link = requests.head(file_info["dlink"], headers=headers).headers.get("location")

    result = {
        "file_name": file_info.get("server_filename"),
        "link": file_info.get("dlink"),
        "direct_link": direct_link,
        "thumb": file_info.get("thumbs", {}).get("url3", None),
        "size": get_formatted_size(int(file_info["size"])),
        "sizebytes": int(file_info["size"])
    }

    return result

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is missing."}), 400

    data = get_data(url)
    return jsonify(data), (data.get('error') and 400) or 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
