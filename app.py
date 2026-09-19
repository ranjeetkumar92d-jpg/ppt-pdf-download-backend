import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches

app = Flask(__name__)
# सभी वेबसाइट्स (जैसे Blogger) को डेटा एक्सेस करने की अनुमति दें
CORS(app)

# ताकि वेबसाइट को लगे कि कोई असली ब्राउज़र रिक्वेस्ट भेज रहा है
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

@app.route("/")
def home():
    return "Backend status: Running and Active!"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "SlideShare URL is missing"}), 400

    if "slideshare.net" not in url:
        return jsonify({"error": "Only valid SlideShare links are supported"}), 400

    try:
        # SlideShare पेज का HTML मंगाएं
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to open page. Status: {response.status_code}"}), 400

        soup = BeautifulSoup(response.text, "html.parser")
        
        # सभी स्लाइड्स की इमेजेस के लिंक्स निकालें
        images = soup.find_all("img", class_="SlideImage")
        if not images:
            images = [img for img in soup.find_all("img") if "slide" in img.get("src", "").lower() or img.get("data-full")]

        if not images:
            return jsonify({"error": "Slides could not be extracted from this page"}), 404

        # नई प्रेजेंटेशन फ़ाइल का स्ट्रक्चर तैयार करें
        prs = Presentation()
        prs.slide_width = Inches(13.33)  # 16:9 वाइडस्क्रीन साइज़
        prs.slide_height = Inches(7.5)
        
        # बिल्कुल खाली (Blank) स्लाइड का लेआउट चुनें
        blank_layout = prs.slide_layouts[6]

        # एक-एक करके हर स्लाइड को डाउनलोड करके PPTX में जोड़ें
        for img_tag in images:
            img_url = img_tag.get("data-full") or img_tag.get("data-normal") or img_tag.get("src")
            if not img_url:
                continue

            # इमेज को सीधे रैम (Memory) में डाउनलोड करें, सर्वर की हार्ड डिस्क पर नहीं
            img_data = requests.get(img_url, headers=HEADERS, timeout=10).content
            img_stream = BytesIO(img_data)

            # प्रेजेंटेशन में नई स्लाइड जोड़ें और इमेज फिट करें
            slide = prs.slides.add_slide(blank_layout)
            slide.shapes.add_picture(img_stream, 0, 0, width=prs.slide_width, height=prs.slide_height)

        # फाइनल फाइल को बिना सेव किए सीधे यूजर के ब्राउज़र में भेजें
        output_stream = BytesIO()
        prs.save(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name="slideshare_presentation.pptx"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render क्लाउड के लिए पोर्ट कॉन्फ़िगरेशन
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
