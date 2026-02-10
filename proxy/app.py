from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import fetcher
import ai_generator
from css_generator_llm import generate_css_with_llm, get_ai_status

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
    domain = data.get("domain", "unknown")
    era = data.get("era", "win95")
    dom_digest = data.get("dom_digest", "")
    feedback = data.get("feedback")
    html_content = data.get("html", "")  # Raw HTML or empty
    
    logger.info(f"Generating style for domain={domain}, era={era}")
    
    # If no HTML provided, try to fetch it
    if not html_content:
        url = f"https://{domain}" if domain and not domain.startswith("http") else domain
        if url and url.startswith("http"):
            try:
                fetch_result = fetcher.fetch_page(url)
                if fetch_result.get("status") == "ok":
                    # For now, we don't have the actual HTML from fetcher
                    # (it returns metadata). In a full implementation, fetcher would return HTML.
                    logger.warning("HTML not returned from fetcher, using template")
                    html_content = f"<html><body><h1>{domain}</h1></body></html>"
            except Exception as e:
                logger.warning(f"Could not fetch page: {e}")
                html_content = f"<html><body><h1>{domain}</h1></body></html>"
        else:
            html_content = f"<html><body><h1>Sample Page</h1></body></html>"
    
    try:
        # Use LLM pipeline
        result = generate_css_with_llm(html_content, era, dom_digest, feedback)
        
        if result["status"] in ["ok", "fallback"]:
            return jsonify(result), 200
        else:
            # Error
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"CSS generation failed: {e}")
        return jsonify({"error": "generation_failed", "message": str(e)}), 500


@app.route("/api/ai-status", methods=["GET"])
def ai_status():
    """Get status of the AI engine."""
    status = get_ai_status()
    return jsonify(status), 200


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
