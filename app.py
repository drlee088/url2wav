import os
import shutil
from flask import Flask, render_template, request, Response, send_from_directory
import yt_dlp
from threading import Thread
from queue import Queue

app = Flask(__name__)
DOWNLOADS_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

log_queue = Queue()

def clear_downloads():
    if os.path.exists(DOWNLOADS_FOLDER):
        shutil.rmtree(DOWNLOADS_FOLDER)
    os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

def download_audio(url):
    clear_downloads()
    log_queue.put(f"Procesando URL: {url} en formato audio\n")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192"
        }],
        "progress_hooks": [progress_hook]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        log_queue.put("✅ Descarga completada!\n")
    except Exception as e:
        err_text = str(e)
        if "Sign in to confirm you’re not a bot" in err_text:
            log_queue.put("❌ Error: Este video requiere login o no es público.\n")
        else:
            log_queue.put(f"❌ Error: {err_text}\n")

def progress_hook(d):
    if d['status'] == 'downloading':
        log_queue.put(f"[download] {d['_percent_str']} de {d['_total_bytes_str']} a {d['_speed_str']}\n")
    elif d['status'] == 'finished':
        log_queue.put(f"[ExtractAudio] Destino: {d['filename']}\n")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            Thread(target=download_audio, args=(url,)).start()
    return render_template("index.html")

@app.route("/logs")
def logs():
    def generate():
        while True:
            msg = log_queue.get()
            yield f"data: {msg}\n\n"
    return Response(generate(), mimetype="text/event-stream")

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOADS_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

