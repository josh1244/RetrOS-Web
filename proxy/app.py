from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/generate-style", methods=["POST"])
def generate_style():
    data = request.get_json(silent=True) or {}
    return jsonify({"error": "not_implemented", "received": data}), 501


@app.route("/api/fetch-page", methods=["POST"])
def fetch_page_endpoint():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        logger.warning("fetch-page request missing URL")
        return jsonify({"error": "missing_url"}), 400
    try:
        result = fetcher.fetch_page(url)
        return jsonify(result), 200
    except fetcher.FetchError as e:
        logger.error(f"Fetch error for {url}: {e}")
        return jsonify({"error": "fetch_failed", "message": str(e)}), 502

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999, debug=True)
