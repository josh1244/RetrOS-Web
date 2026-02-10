from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import time
import re
import fetcher
import ai_generator
from css_generator_llm import generate_css_with_llm, get_ai_status

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Valid eras for validation
VALID_ERAS = ["web1996", "win95", "win98", "winxp"]

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

def _validate_request_data(data):
    """
    Validate POST /api/generate-style request body.
    
    Returns: (is_valid, error_message, sanitized_data)
    """
    errors = []
    sanitized = {}
    
    # Validate domain (required)
    domain = data.get("domain", "").strip()
    if not domain:
        errors.append("domain is required")
    elif len(domain) > 255:
        errors.append("domain exceeds maximum length (255 characters)")
    elif not re.match(r"^[a-zA-Z0-9\-\.]+\.[a-zA-Z0-9\-\.]+", domain):
        errors.append("domain format is invalid")
    else:
        sanitized["domain"] = domain
    
    # Validate era (optional, defaults to win95)
    era = data.get("era", "win95").strip().lower()
    if era not in VALID_ERAS:
        errors.append(f"era must be one of: {', '.join(VALID_ERAS)}")
    else:
        sanitized["era"] = era
    
    # Validate dom_digest (optional)
    dom_digest = data.get("dom_digest", "").strip()
    if len(dom_digest) > 1024:
        errors.append("dom_digest exceeds maximum length (1024 characters)")
    else:
        sanitized["dom_digest"] = dom_digest
    
    # Validate feedback (optional)
    feedback = data.get("feedback")
    if feedback:
        if isinstance(feedback, str):
            if len(feedback) > 500:
                errors.append("feedback exceeds maximum length (500 characters)")
            else:
                sanitized["feedback"] = feedback.strip()
        elif isinstance(feedback, dict):
            # Expected format for feedback
            sanitized["feedback"] = feedback
        else:
            errors.append("feedback must be string or object")
    
    # HTML is optional
    html_content = data.get("html", "").strip()
    if html_content and len(html_content) > 10 * 1024 * 1024:  # 10MB max
        errors.append("html exceeds maximum size (10MB)")
    else:
        sanitized["html"] = html_content
    
    return (len(errors) == 0, errors, sanitized)


@app.route("/api/generate-style", methods=["POST"])
@limiter.limit("100/minute")
def generate_style():
    """
    Generate CSS styles for a domain in a given era.
    
    Request body:
    {
        "domain": "example.com" (required),
        "era": "win95" (optional, default: win95),
        "dom_digest": "hash123" (optional),
        "feedback": "Make it simpler" (optional),
        "html": "<html>...</html>" (optional)
    }
    
    Response:
    {
        "status": "ok" | "fallback" | "error",
        "css": "/* generated CSS */",
        "metadata": {
            "era": "win95",
            "domain": "example.com",
            "generated_at": "2026-02-09T10:30:45Z",
            "generation_ms": 1234,
            "fallback": false,
            "model_status": "ready" | "loading" | "unavailable"
        },
        "cacheKey": "example.com-win95-hash123",
        "error": "error_code" (only if status=error),
        "message": "error description" (only if status=error)
    }
    """
    request_start_time = time.time()
    
    # Get and parse JSON
    try:
        data = request.get_json(silent=True) or {}
    except Exception as e:
        logger.error(f"Invalid JSON in request: {e}")
        return jsonify({
            "status": "error",
            "error": "invalid_json",
            "message": "Request body must be valid JSON"
        }), 400
    
    # Validate request data
    is_valid, validation_errors, sanitized = _validate_request_data(data)
    if not is_valid:
        logger.warning(f"Request validation failed: {validation_errors}")
        return jsonify({
            "status": "error",
            "error": "validation_failed",
            "message": "Request validation failed",
            "details": validation_errors
        }), 400
    
    domain = sanitized["domain"]
    era = sanitized["era"]
    dom_digest = sanitized.get("dom_digest", "")
    feedback = sanitized.get("feedback")
    html_content = sanitized.get("html", "")
    
    logger.info(f"Generating style: domain={domain}, era={era}, dom_digest={dom_digest[:16] if dom_digest else 'none'}")
    
    # If no HTML provided, try to fetch it
    if not html_content:
        url = f"https://{domain}" if domain and not domain.startswith("http") else domain
        if url and url.startswith("http"):
            try:
                logger.debug(f"Fetching page from {url}")
                fetch_result = fetcher.fetch_page(url)
                if fetch_result.get("status") == "ok":
                    # For now, we don't have the actual HTML from fetcher
                    # (it returns metadata). In a full implementation, fetcher would return HTML.
                    logger.debug("HTML not returned from fetcher, using template")
                    html_content = f"<html><body><h1>{domain}</h1></body></html>"
            except Exception as e:
                logger.warning(f"Could not fetch page {url}: {e}")
                html_content = f"<html><body><h1>{domain}</h1></body></html>"
        else:
            html_content = f"<html><body><h1>Sample Page</h1></body></html>"
    
    try:
        # Use LLM pipeline
        logger.debug(f"Starting CSS generation for {domain}")
        result = generate_css_with_llm(html_content, era, dom_digest, feedback)
        
        # Add timing info
        generation_ms = int((time.time() - request_start_time) * 1000)
        if "metadata" not in result:
            result["metadata"] = {}
        result["metadata"]["generation_ms"] = generation_ms
        
        # Generate cache key
        cache_key = f"{domain}-{era}-{dom_digest[:32] if dom_digest else 'default'}"
        result["cacheKey"] = cache_key
        
        if result["status"] in ["ok", "fallback"]:
            logger.info(f"CSS generation successful for {domain}: {generation_ms}ms (status={result['status']})")
            return jsonify(result), 200
        else:
            # Error case
            logger.error(f"CSS generation error for {domain}: {result.get('message', 'Unknown error')}")
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"CSS generation failed for {domain}: {e}")
        generation_ms = int((time.time() - request_start_time) * 1000)
        return jsonify({
            "status": "error",
            "error": "generation_failed",
            "message": "CSS generation encountered an internal error",
            "details": str(e) if app.debug else None,
            "metadata": {
                "domain": domain,
                "era": era,
                "generation_ms": generation_ms
            }
        }), 500


@app.route("/api/ai-status", methods=["GET"])
def ai_status():
    """Get status of the AI engine."""
    logger.debug("AI status requested")
    status = get_ai_status()
    return jsonify(status), 200


@app.route("/api/fetch-page", methods=["POST"])
@limiter.limit("50/minute")
def fetch_page_endpoint():
    """
    Fetch and analyze a web page.
    
    Request body:
    {
        "url": "https://example.com" (required)
    }
    
    Response:
    {
        "status": "ok" | "error",
        "url": "https://example.com",
        "domain": "example.com",
        "title": "Page Title",
        "headers": {...},
        "error": "error_code" (only if status=error),
        "message": "error description" (only if status=error)
    }
    """
    try:
        data = request.get_json(silent=True) or {}
    except Exception as e:
        logger.error(f"Invalid JSON in fetch-page request: {e}")
        return jsonify({"error": "invalid_json", "message": "Request body must be valid JSON"}), 400
    
    url = data.get("url", "").strip()
    if not url:
        logger.warning("fetch-page request missing URL")
        return jsonify({
            "status": "error",
            "error": "missing_url",
            "message": "URL is required"
        }), 400
    
    if len(url) > 2048:
        logger.warning(f"fetch-page request URL too long: {len(url)}")
        return jsonify({
            "status": "error",
            "error": "url_too_long",
            "message": "URL exceeds maximum length (2048 characters)"
        }), 400
    
    try:
        logger.info(f"Fetching page: {url}")
        result = fetcher.fetch_page(url)
        return jsonify(result), 200
    except fetcher.FetchError as e:
        logger.error(f"Fetch error for {url}: {e}")
        return jsonify({
            "status": "error",
            "error": "fetch_failed",
            "message": str(e),
            "url": url
        }), 502
    except Exception as e:
        logger.exception(f"Unexpected error fetching {url}: {e}")
        return jsonify({
            "status": "error",
            "error": "internal_error",
            "message": "An internal error occurred while fetching the page"
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999, debug=True)
