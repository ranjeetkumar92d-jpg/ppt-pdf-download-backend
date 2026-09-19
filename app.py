import os
from io import BytesIO
import requests
from flask import Flask, request, send_file, jsonify
from bs4 import BeautifulSoup
from PIL import Image

app = Flask(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

@app.route("/")
def home():
    return "Backend is working!"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL is missing"}), 400

    # ===== SLIDESHARE LOGIC =====
    if "slideshare.net" in url:
        try:
            page_response = requests.get(url, headers=HEADERS, timeout=30)
            soup = BeautifulSoup(page_response.content, 'html.parser')
            
            # SlideShare ki images nikalne ka naya smart logic
            image_urls = []
            
            # SlideShare commonly in tags me image chupata hai
            for img in soup.find_all(['img', 'source']):
                # Har possible attribute check karein jisme link ho sakta hai
                possible_srcs = [
                    img.get('data-full'), 
                    img.get('data-normal'), 
                    img.get('srcset'), 
                    img.get('src'), 
                    img.get('content')
                ]
                
                for src in possible_srcs:
                    if src and isinstance(src, str) and "slidesharecdn.com" in src.lower():
                        # Agar srcset me multiple links hain, toh sabse high quality nikalna
                        best_img_url = src.split(',')[-1].split(' ')[0].strip()
                        
                        # Sirf image files ko hi allow karein
                        if best_img_url not in image_urls and any(ext in best_img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                            image_urls.append(best_img_url)
                        break # Ek tag se ek hi best link chahiye

            if not image_urls:
                return jsonify({"error": "Slide images HTML mein nahi mil payin. Website structure change ho gaya hoga."}), 400

            slide_images = []
            for img_url in image_urls:
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
                download_name="slideshare_presentation.pdf"
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
            return send_file(BytesIO(response.content), mimetype="application/pdf", as_attachment=True, download_name="download.pdf")
        if content_type == "application/vnd.ms-powerpoint":
            return send_file(BytesIO(response.content), mimetype=content_type, as_attachment=True, download_name="download.ppt")
        if content_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
            return send_file(BytesIO(response.content), mimetype=content_type, as_attachment=True, download_name="download.pptx")
        
        return jsonify({"error": "This URL is not a direct PDF, PPT or PPTX file."}), 400

    except requests.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
