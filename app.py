import re
import urllib.parse

import extraction
import requests
from flask import Flask, Response, jsonify, render_template, request

app = Flask(__name__)


def gen_gdrive_file_name(gdrive_id):
    url = f"https://drive.google.com/open?id={gdrive_id}"
    html = requests.get(url).text
    return extraction.Extractor().extract(html, source_url=url).title


def gdrive_extract_id(gdrive_link):
    match = re.match(
        r"^https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)/?.*$", gdrive_link
    )
    if match:
        return match.group(1)
    query_params = urllib.parse.parse_qs(urllib.parse.urlparse(gdrive_link).query)
    if "id" in query_params:
        return query_params["id"][0]
    return None


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


@app.route("/download")
@app.route("/dl")
def download_file_from_google_drive():
    id = request.args.get("id")
    stream = str(request.args.get("stream", "False")).lower()
    if id != "":
        if stream == "true":
            file_url = request.url[:-12]
            file_name = gen_gdrive_file_name(id)
            return render_template(
                "video.html", file_name=file_name, video_url=file_url
            )

        URL = "https://docs.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(URL, params={"id": id, "confirm": 1}, stream=True)
        token = get_confirm_token(response)
        if token:
            params = {"id": id, "confirm": token}
            response = session.get(URL, params=params, stream=True)

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        file_name = gen_gdrive_file_name(id)
        if file_name == "Error 404 (Not Found)!!1":
            return "File ID is Expired or Incorrect File ID.", 400
        headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
        return Response(
            generate(), headers=headers, content_type=response.headers["content-type"]
        )

    else:
        return "File ID is required.", 400


@app.route("/")
def home():
    return jsonify({"server": "running"})


if __name__ == "__main__":
    app.run()
