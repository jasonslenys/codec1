#!/usr/bin/env python3
"""Flask web application for MP4 to H.264 converter."""

import os
import uuid
import threading
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    Response,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from converter import MP4Converter

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024 * 1024  # 10GB max upload

# Storage for uploads and conversions
UPLOAD_DIR = Path(__file__).parent / "uploads"
OUTPUT_DIR = Path(__file__).parent / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Track conversion progress
conversion_progress = {}
conversion_status = {}


def cleanup_old_files():
    """Remove files older than 1 hour."""
    import time
    now = time.time()
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for file in directory.iterdir():
            if file.is_file() and (now - file.stat().st_mtime) > 3600:
                file.unlink()


@app.route("/")
def landing():
    """Render the landing page."""
    return render_template("landing.html")


@app.route("/converter")
def converter():
    """Render the converter page."""
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Handle file upload."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return jsonify({"error": "Invalid file type. Please upload a video file."}), 400

    # Generate unique ID for this conversion
    job_id = str(uuid.uuid4())

    # Save uploaded file
    input_filename = f"{job_id}_input{Path(file.filename).suffix}"
    input_path = UPLOAD_DIR / input_filename
    file.save(input_path)

    # Get conversion settings
    crf = int(request.form.get("crf", 23))
    preset = request.form.get("preset", "medium")

    # Initialize progress tracking
    conversion_progress[job_id] = 0
    conversion_status[job_id] = "processing"

    # Start conversion in background thread
    output_filename = f"{job_id}_output.mp4"
    output_path = OUTPUT_DIR / output_filename

    def run_conversion():
        try:
            converter = MP4Converter()

            def progress_callback(progress):
                conversion_progress[job_id] = progress

            converter.convert(
                str(input_path),
                str(output_path),
                crf=crf,
                preset=preset,
                overwrite=True,
                progress_callback=progress_callback,
            )
            conversion_status[job_id] = "completed"
            conversion_progress[job_id] = 100

            # Clean up input file
            input_path.unlink()

        except Exception as e:
            conversion_status[job_id] = f"error: {str(e)}"
            # Clean up on error
            if input_path.exists():
                input_path.unlink()
            if output_path.exists():
                output_path.unlink()

    thread = threading.Thread(target=run_conversion)
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/progress/<job_id>")
def progress(job_id):
    """Stream conversion progress via Server-Sent Events."""
    def generate():
        import time
        while True:
            progress = conversion_progress.get(job_id, 0)
            status = conversion_status.get(job_id, "unknown")

            yield f"data: {{'progress': {progress}, 'status': '{status}'}}\n\n"

            if status == "completed" or status.startswith("error"):
                break

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


@app.route("/status/<job_id>")
def status(job_id):
    """Get conversion status."""
    progress = conversion_progress.get(job_id, 0)
    status = conversion_status.get(job_id, "unknown")
    return jsonify({"progress": progress, "status": status})


@app.route("/download/<job_id>")
def download(job_id):
    """Download converted file."""
    output_path = OUTPUT_DIR / f"{job_id}_output.mp4"

    if not output_path.exists():
        return jsonify({"error": "File not found"}), 404

    return send_file(
        output_path,
        as_attachment=True,
        download_name="converted_h264.mp4",
        mimetype="video/mp4",
    )


@app.route("/cleanup/<job_id>", methods=["POST"])
def cleanup(job_id):
    """Clean up files after download."""
    output_path = OUTPUT_DIR / f"{job_id}_output.mp4"
    if output_path.exists():
        output_path.unlink()

    # Clean up tracking
    conversion_progress.pop(job_id, None)
    conversion_status.pop(job_id, None)

    return jsonify({"status": "cleaned"})


def main():
    """Run the web application."""
    import argparse

    parser = argparse.ArgumentParser(description="MP4 to H.264 Converter Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print(f"\n MP4 to H.264 Converter")
    print(f"   Running at: http://localhost:{args.port}")
    print(f"   Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == "__main__":
    main()
