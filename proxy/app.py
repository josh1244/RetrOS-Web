from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/generate-style", methods=["POST"])
def generate_style():
    data = request.get_json(silent=True) or {}
    return jsonify({"error": "not_implemented", "received": data}), 501

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999, debug=True)
