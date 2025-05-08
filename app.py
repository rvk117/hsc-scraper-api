from flask import Flask, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/scrape', methods=['GET'])
def run_scraper():
    try:
        result = subprocess.run(
            ["python3", "HSC_section_scrape.py"], 
            capture_output=True, 
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            return jsonify({"status": "error", "stderr": result.stderr}), 500

        return jsonify({"status": "success", "stdout": result.stdout})
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    return "HSC Scraper API is live!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(debug=True, host="0.0.0.0", port=port)

