"""
Wave Email Classifier - Flask API
==================================
Wraps classify_email() as a REST API so watsonx Orchestrate can call it.

Run:
    pip install flask
    python api.py
"""

from flask import Flask, request, jsonify
from classify_emails import classify_email, load_emails

app = Flask(__name__)


# ── Route 1: Health check ────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Wave Email Classifier"})


# ── Route 2: Classify a single email ─────────────────────────────────────────
@app.route("/classify", methods=["POST"])
def classify_single():
    """
    Classify one email.

    Request body:
    {
        "id": "EMAIL-001",
        "from": "customer@gmail.com",
        "subject": "Lift not working",
        "body": "The lift in Tower B has not been working for 3 days..."
    }

    Response:
    {
        "email_id": "EMAIL-001",
        "category": "SERVICE_REQUEST",
        "sentiment": "NEGATIVE",
        "priority": "HIGH",
        "route_to": "Facilities / Project Team",
        "summary": "Lift not working in Tower B"
    }
    """
    body = request.get_json()

    if not body:
        return jsonify({"error": "Request body is required"}), 400

    required = ["id", "from", "subject", "body"]
    missing = [f for f in required if f not in body]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    result = classify_email(body)
    return jsonify(result), 200


# ── Route 3: Classify a batch of emails ──────────────────────────────────────
@app.route("/classify/batch", methods=["POST"])
def classify_batch():
    """
    Classify multiple emails at once.

    Request body:
    {
        "emails": [
            {"id": "E1", "from": "a@b.com", "subject": "...", "body": "..."},
            {"id": "E2", "from": "c@d.com", "subject": "...", "body": "..."}
        ]
    }

    Response:
    {
        "total": 2,
        "results": [ {...}, {...} ],
        "summary": {
            "COMPLAINT": 1,
            "SERVICE_REQUEST": 0,
            "GENERAL_QUERY": 1
        }
    }
    """
    body = request.get_json()

    if not body or "emails" not in body:
        return jsonify({"error": "'emails' array is required"}), 400

    emails = body["emails"]
    if not isinstance(emails, list) or len(emails) == 0:
        return jsonify({"error": "'emails' must be a non-empty array"}), 400

    results = [classify_email(e) for e in emails]

    summary = {"COMPLAINT": 0, "SERVICE_REQUEST": 0, "GENERAL_QUERY": 0}
    for r in results:
        summary[r["category"]] += 1

    return jsonify({
        "total": len(results),
        "results": results,
        "summary": summary
    }), 200


# ── Route 4: Run on the built-in dummy emails ─────────────────────────────────
@app.route("/classify/demo", methods=["GET"])
def classify_demo():
    """
    Runs classification on the 10 built-in dummy emails.
    No request body needed — just hit this URL in a browser or Postman.
    """
    emails = load_emails()
    results = [classify_email(e) for e in emails]

    summary = {"COMPLAINT": 0, "SERVICE_REQUEST": 0, "GENERAL_QUERY": 0}
    for r in results:
        summary[r["category"]] += 1

    return jsonify({
        "total": len(results),
        "results": results,
        "summary": summary
    }), 200


# ── Start server ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  Wave Email Classifier API is running!")
    print("  Health check : http://localhost:5000/health")
    print("  Demo run     : http://localhost:5000/classify/demo")
    print("  Single email : POST http://localhost:5000/classify")
    print("  Batch emails : POST http://localhost:5000/classify/batch\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
