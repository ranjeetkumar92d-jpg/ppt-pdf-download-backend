import os
from io import BytesIO

import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


@app.route("/")
def home():
    return "Backend status: Running and Active!"


@app.route("/download")
def download():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "URL is missing"}), 400

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code != 200:
            return jsonify({
                "error": f"File unavailable. Status: {response.status_code}"
            }), 400

        content_type = response.headers.get(
            "Content-Type", ""
        ).split(";")[0].lower()

        # Direct PDF
        if content_type == "application/pdf":
            return send_file(
                BytesIO(response.content),
                mimetype="application/pdf",
                as_attachment=True,
                download_name="download.pdf"
            )

        # Direct PPT
        if content_type == "application/vnd.ms-powerpoint":
            return send_file(
                BytesIO(response.content),
                mimetype="application/vnd.ms-powerpoint",
                as_attachment=True,
                download_name="download.ppt"
            )

        # Direct PPTX
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
            "error": "URL is not a direct PDF, PPT or PPTX file."
        }), 400

    except requests.RequestException as e:
        return jsonify({
            "error": f"Request failed: {str(e)}"
        }), 500


@app.route("/images-to-ppt")
def images_to_ppt():
    """
    Converts publicly accessible/authorized image URLs
    into a PPTX presentation.
    """

    urls = request.args.get("urls")

    if not urls:
        return jsonify({
            "error": "Image URLs are missing"
        }), 400

    try:
        from pptx import Presentation
        from pptx.util import Inches

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        blank_layout = prs.slide_layouts[6]

        for image_url in urls.split(","):
            image_url = image_url.strip()

            if not image_url:
                continue

            response = requests.get(
                image_url,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code != 200:
                continue

            image = Image.open(
                BytesIO(response.content)
            ).convert("RGB")

            image_stream = BytesIO()
            image.save(image_stream, format="JPEG")
            image_stream.seek(0)

            slide = prs.slides.add_slide(blank_layout)

            slide.shapes.add_picture(
                image_stream,
                0,
                0,
                width=prs.slide_width,
                height=prs.slide_height
            )

        if len(prs.slides) == 0:
            return jsonify({
                "error": "No valid images found."
            }), 400

        output = BytesIO()
        prs.save(output)
        output.seek(0)

        return send_file(
            output,
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            ),
            as_attachment=True,
            download_name="presentation.pptx"
        )

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port
    )
