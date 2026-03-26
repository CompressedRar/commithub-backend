"""
routes/AI.py  — backend proxy for Groq AI calls.

Register in app.py:
    from routes.AI import ai
    app.register_blueprint(ai)

The frontend calls POST /api/v1/ai/convert-tense  and  POST /api/v1/ai/create-description
instead of hitting api.groq.com directly.
This keeps GROQ_API_KEY server-side only.
"""

import os
import requests
from flask import Blueprint, request, jsonify
from utils.decorators import token_required

ai = Blueprint("ai", __name__, url_prefix="/api/v1/ai")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

def _call_groq(messages: list) -> str:
    """Make a single request to Groq and return the text content."""
    groq_key = os.getenv("GROQ_API_KEY")   # never sent to the browser
    print(groq_key)
    resp = requests.post(
        GROQ_API_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {groq_key}",
        },
        json={"model": GROQ_MODEL, "messages": messages},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


@ai.route("/convert-tense", methods=["POST"])
@token_required()
def convert_tense():
    """Convert a sentence to past tense.
    Body: { "sentence": "..." }
    """
    data = request.get_json(silent=True) or {}
    sentence = data.get("sentence", "").strip()
    if not sentence:
        return jsonify(error="sentence is required"), 400

    result = _call_groq([{
        "role": "user",
        "content": f"convert this to past tense no explanations and no periods: {sentence}"
    }])
    return jsonify(result=result), 200


@ai.route("/create-description", methods=["POST"])
@token_required()
def create_description():
    """Generate a one-sentence task description.
    Body: { "data": "..." }
    """
    data = request.get_json(silent=True) or {}
    content = data.get("data", "").strip()
    if not content:
        return jsonify(error="data is required"), 400

    result = _call_groq([
        {
            "role": "system",
            "content": "create a brief one sentence description with target quantity target timeframe or deadline based on this data no explanations:"
        },
        {"role": "user", "content": content}
    ])
    return jsonify(result=result), 200