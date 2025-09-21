from flask import Flask, render_template, request, Response
import yt_dlp
import os
import threading
import time

app = Flask(__name__)
DOWNLOADS_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)

logs_dict = {}

def download_audio(job_id, url):
    logs = []
    logs_dict[job_id] = logs

    def log(msg):
        logs.append(msg)
        print(msg, flush=True)

    def progress_hook(d):
        log(str(d))

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOADS_FOLDER, "%(title)s.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }],
            "progress_hooks": [progress_hook],
            "logger": None
        }

        log(f"Procesando URL: {url} en formato audio")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        log("✅ Descarga finalizada.")
    except Exception as e:
        log(f"❌ Error: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route("/start_download", methods=["POST"])
def start_download():
    url = request.form.get("url")
    job_id = str(time.time())
    thread = threading.Thread(target=download_audio, args=(job_id, url))
    thread.start()
    return {"job_id": job_id}

@app.route("/stream/<job_id>")
def stream(job_id):
    def event_stream():
        last_index = 0
        while True:
            logs = logs_dict.get(job_id, [])
            if last_index < len(logs):
                for line in logs[last_index:]:
                    yield f"data: {line}\n\n"
                last_index = len(logs)
            if "✅ Descarga finalizada." in logs or any("❌ Error" in l for l in logs):
                break
            time.sleep(0.3)
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True)
