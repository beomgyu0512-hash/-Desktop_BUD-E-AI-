import os
import threading
import uuid

from flask import Flask, jsonify, render_template, request

from api_configs.configs import get_llm_config
from buddy_session import BuddySession
from child_profile import load_child_profile, save_child_profile


HOST = os.getenv("BUD_E_WEB_HOST", "127.0.0.1")
PORT = int(os.getenv("BUD_E_WEB_PORT", "8000"))
llm_config = get_llm_config()


app = Flask(__name__)
sessions: dict[str, BuddySession] = {}
sessions_lock = threading.Lock()


def get_session(session_id: str | None) -> tuple[str, BuddySession]:
    if session_id:
        with sessions_lock:
            existing_session = sessions.get(session_id)
        if existing_session is not None:
            return session_id, existing_session

    new_session_id = uuid.uuid4().hex
    new_session = BuddySession()
    with sessions_lock:
        sessions[new_session_id] = new_session
    return new_session_id, new_session


def normalize_profile_payload(payload: dict) -> dict:
    return {
        "name": (payload.get("name") or "").strip(),
        "age": (payload.get("age") or "").strip(),
        "interests": [item.strip() for item in (payload.get("interests") or []) if item.strip()],
        "goals": [item.strip() for item in (payload.get("goals") or []) if item.strip()],
        "recent_topics": [item.strip() for item in (payload.get("recent_topics") or []) if item.strip()],
        "parent_preferences": (payload.get("parent_preferences") or "").strip(),
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "provider": llm_config["default_model"]})


@app.get("/api/profile")
def get_profile():
    return jsonify(load_child_profile())


@app.post("/api/profile")
def update_profile():
    payload = request.get_json(silent=True) or {}
    profile = normalize_profile_payload(payload)
    saved_profile = save_child_profile(profile)

    with sessions_lock:
        for session in sessions.values():
            session.refresh_child_profile()

    return jsonify({"ok": True, "profile": saved_profile})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    session_id = payload.get("session_id")

    if not message:
        return jsonify({"error": "message is required"}), 400

    session_id, session = get_session(session_id)

    try:
        reply = session.reply(message)
    except Exception as exc:
        return jsonify({"error": str(exc), "session_id": session_id}), 500

    return jsonify({"reply": reply, "session_id": session_id})


@app.post("/api/reset")
def reset():
    payload = request.get_json(silent=True) or {}
    session_id = payload.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    with sessions_lock:
        sessions.pop(session_id, None)

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
