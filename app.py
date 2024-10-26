import re
from urllib.parse import parse_qs, urlparse
import requests
from flask import Flask, request, jsonify

# Replace with your actual COOKIE value
COOKIE = {
    "COOKIE": "csrfToken=m_zbAV1arBvXCvTgmFvSluXY; browserid=EAaVwqpE6IPuBWAbOmlwEa-HARfMNQSSWLn9wiOXV1pWAEArqSzqtnmnkqM=; lang=en; TSID=RgCB6tEItxCB33EMPKyzutFSBMmUxfjl; __bid_n=190fa81594548da7784207; _ga=GA1.1.1547073603.1722189820; ndus=YuaYNCMteHuiIaOZqGpTf8Z9-n1Si4erYpgWHcaX; ab_sr=1.0.1_ODA4NTRlNzE0MjVkYzczZjZjNmQ3NGI0MzZjNTIxNGI1MThmNjdmZTNlM2I1ZmU5N2E0NmY5Mjg2OTdjMDg5NzM2NDhiZWRlNGFjY2RiZTNhNzQ2YmEwNzAwNzJhZGQ3ZDNiOTY3ZjNjYjVhZGZiODA4ZWU5ZDUxZjZkMjk0NTYzOWYyYzVkZDFhZmRmM2RhNjUyNDA5YTBjZjk0MDVlZg==; ndut_fmt=426D9C20125DC8DFB9349A68EB0F767398283E07567B9C028271312D315A284E; _ga_06ZNKL8C2E=GS1.1.1722189819.1.1.1722191121.52.0.0"
}

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
    surl = query_params.get("surl", [])
    return surl[0] if surl else None

def get_formatted_size(size):
    """Convert bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_data(url: str):
    r = requests.Session()
    headersList = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }

    response = r.get(url, headers=headersList)
    default_thumbnail = find_between(response.text, 'og:image" content="', '"')
    logid = find_between(response.text, "dp-logid=", "&")
    jsToken = find_between(response.text, "fn%28%22", "%22%29")
    bdstoken = find_between(response.text, 'bdstoken":"', '"')
    shorturl = extract_surl_from_url(response.url)

    if not shorturl:
        return {"error": "Invalid URL or surl parameter not found"}

    reqUrl = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken}&dp-logid={logid}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"

    response = r.get(reqUrl, headers=headersList)

    if not response.status_code == 200:
        return {"error": "Failed to retrieve data from Terabox"}

    r_j = response.json()
    if r_j["errno"]:
        return {"error": "Error retrieving file list"}

    file_data = r_j.get("list", [])
    if not file_data:
        return {"error": "No files found"}

    first_file = file_data[0]
    direct_link = requests.head(first_file["dlink"], headers=headersList).headers.get("location")

    data = {
        "file_name": first_file.get("server_filename"),
        "link": first_file.get("dlink"),
        "direct_link": direct_link,
        "thumb": first_file.get("thumbs", {}).get("url3", default_thumbnail),
        "size": get_formatted_size(int(first_file["size"])),
        "sizebytes": int(first_file["size"]),
    }

    return data

@app.route('/download', methods=['GET'])
def download():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    result = get_data(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
