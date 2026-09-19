from flask import Flask, request, send_file
from io import BytesIO
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is working!"

@app.route("/download")
def download():
    url = request.args.get("url")

    if not url:
        return "URL missing", 400

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        return "File unavailable", 400

    return send_file(
        BytesIO(response.content),
        as_attachment=True,
        download_name="file.pdf"
    )

if __name__ == "__main__":
    app.run()
