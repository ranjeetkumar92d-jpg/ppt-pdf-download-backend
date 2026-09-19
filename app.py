import os
from io import BytesIO

import requests
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


@app.route("/")
def home():
    return "Backend is working!"


@app.route("/download")
def download():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "URL is missing"}), 400

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True
        )

        if response.status_code != 200:
            return jsonify({
                "error": f"File unavailable. Status: {response.status_code}"
            }), 400

        content_type = (
            response.headers.get("Content-Type", "")
            .split(";")[0]
            .lower()
        )

        if content_type == "application/pdf":
            return send_file(
                BytesIO(response.content),
                mimetype="application/pdf",
                as_attachment=True,
                download_name="download.pdf"
            )

        if content_type == "application/vnd.ms-powerpoint":
            return send_file(
                BytesIO(response.content),
                mimetype=content_type,
                as_attachment=True,
                download_name="download.ppt"
            )

        if content_type == (
            "application/vnd.openxmlformats-officedocument."
            "presentationml.presentation"
        ):
            return send_file(
                BytesIO(response.content),
                mimetype=content_type,
                as_attachment=True,
                download_name="download.pptx"
            )

        return jsonify({
            "error": "This URL is not a direct PDF, PPT or PPTX file."
        }), 400

    except requests.RequestException as e:
        return jsonify({
            "error": f"Request failed: {str(e)}"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port
    )
