from flask import Flask, request, send_file
from io import BytesIO
import requests
from urllib.parse import urlparse

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is working!"

@app.route("/download")
def download():
    url = request.args.get("url")

    if not url:
        return "URL missing", 400

    try:
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            return "File unavailable", 400

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        # Only allow PDF and PowerPoint files
        allowed_types = {
            "application/pdf": ("download.pdf", "application/pdf"),
            "application/vnd.ms-powerpoint":
                ("download.ppt", "application/vnd.ms-powerpoint"),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                ("download.pptx",
                 "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        }

        if content_type not in allowed_types:
            return "This URL is not a direct PDF/PPT/PPTX file.", 400

        filename, mimetype = allowed_types[content_type]

        return send_file(
            BytesIO(response.content),
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except Exception:
        return "Download failed", 500


if __name__ == "__main__":
    app.run()
