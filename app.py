import os
import re
from io import BytesIO
import requests
from flask import Flask, request, send_file, jsonify
from PIL import Image

app = Flask(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

@app.route("/")
def home():
    return "Backend is working perfectly!"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL is missing"}), 400

    # ===== SLIDESHARE SCRAPING LOGIC =====
    if "slideshare.net" in url:
        try:
            page_response = requests.get(url, headers=HEADERS, timeout=30)
            
            if page_response.status_code != 200:
                return jsonify({"error": f"SlideShare blocked the request. Status: {page_response.status_code}"}), 400

            html_text = page_response.text
            
            # Regex se images nikalna
            raw_urls = re.findall(r'(https?://[^"\'\s>,\\]+\.(?:jpg|jpeg|png|webp))', html_text)
            
            image_urls = []
            for src in raw_urls:
                src = src.replace('\\/', '/') 
                if "slidesharecdn.com" in src and "profile" not in src:
                    if src not in image_urls:
                        image_urls.append(src)

            if not image_urls:
                return jsonify({"error": "Slide images code mein nahi mil payin. Regex search failed."}), 400

            unique_slides = {}
            for img_url in image_urls:
                parts = img_url.split('-')
                if len(parts) > 1:
                    key = '-'.join(parts[:-1]) 
                    if key not in unique_slides or "2048" in img_url or "1024" in img_url:
                        unique_slides[key] = img_url
                else:
                    unique_slides[img_url] = img_url
                    
            final_image_urls = list(unique_slides.values())
            final_image_urls.sort()

            # Sabhi slides download karke PDF banana
            slide_images = []
            for img_url in final_image_urls:
                img_data = requests.get(img_url, headers=HEADERS).content
                img_obj = Image.open(BytesIO(img_data)).convert('RGB')
                slide_images.append(img_obj)

            pdf_bytes = BytesIO()
            if slide_images:
                slide_images[0].save(pdf_bytes, format='PDF', save_all=True, append_images=slide_images[1:])
            pdf_bytes.seek(0)

            return send_file(
                pdf_bytes, 
                mimetype="application/pdf", 
                as_attachment=True, 
                download_name="SlideShare_Presentation.pdf"
            )

        except Exception as e:
            return jsonify({"error": f"SlideShare processing failed: {str(e)}"}), 500
    # ============================

    # ===== NORMAL DIRECT FILES LOGIC =====
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if response.status_code != 200:
            return jsonify({"error": f"File unavailable. Status: {response.status_code}"}), 400
        
        content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
        
        if content_type == "application/pdf":
            return send_file(BytesIO(response.content), mimetype="application/pdf", as_attachment=True, download_name="document.pdf")
        if content_type in ["application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation"]:
            return send_file(BytesIO(response.content), mimetype=content_type, as_attachment=True, download_name="presentation.pptx")
        
        return jsonify({"error": "This URL is not a direct PDF, PPT or PPTX file."}), 400

    except requests.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
