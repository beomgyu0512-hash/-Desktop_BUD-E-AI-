import os
import re
import threading
import uuid

from flask import Flask, jsonify, render_template, request

from buddy import (
    conditional_execution,
    extract_opening_and_closing_tags,
    keyword_activated_skills_dict,
    lm_activated_skills_dict,
    llm_config,
    parse_list_of_lists,
)
from llm_definition import LanguageModelProcessor


HOST = os.getenv("BUD_E_WEB_HOST", "127.0.0.1")
PORT = int(os.getenv("BUD_E_WEB_PORT", "8000"))


class BuddyWebSession:
    def __init__(self):
        self.llm = LanguageModelProcessor(llm_config)
        self.scratch_pad = {}
        self.lock = threading.Lock()

    def _run_keyword_skills(self, message: str) -> str:
        all_skill_responses = []

        for function_name, serialized_conditions in keyword_activated_skills_dict.items():
            try:
                condition_list = parse_list_of_lists(serialized_conditions)
                skill_response, updated_conversation, updated_scratch_pad = conditional_execution(
                    function_name,
                    message,
                    self.llm.conversation,
                    self.scratch_pad,
                    condition_list,
                )
                self.llm.conversation = updated_conversation
                self.scratch_pad = updated_scratch_pad
                if skill_response.strip():
                    all_skill_responses.append(skill_response.strip())
            except Exception:
                continue

        return "\n".join(all_skill_responses).strip()

    def _run_lm_skills(self, message: str, llm_response: str) -> str | None:
        for function_name, skill_instruction in lm_activated_skills_dict.items():
            opening_tag, closing_tag = extract_opening_and_closing_tags(skill_instruction)
            if not opening_tag or not closing_tag:
                continue
            if opening_tag.lower() not in llm_response.lower():
                continue
            if closing_tag.lower() not in llm_response.lower():
                continue

            opening_tag_name = re.escape(opening_tag[1:-1])
            closing_tag_name = re.escape(closing_tag[2:-1])
            pattern = rf"<{opening_tag_name}>(.*?)</{closing_tag_name}>"
            matches = re.findall(pattern, llm_response, flags=re.IGNORECASE | re.DOTALL)
            if not matches:
                continue

            try:
                skill_response, updated_conversation, updated_scratch_pad = conditional_execution(
                    function_name,
                    message,
                    self.llm.conversation,
                    self.scratch_pad,
                    [],
                    matches[0].strip(),
                )
                self.llm.conversation = updated_conversation
                self.scratch_pad = updated_scratch_pad
                if skill_response.strip():
                    return skill_response.strip()
            except Exception:
                continue

        return None

    def reply(self, message: str) -> str:
        cleaned_message = (message or "").strip()
        if not cleaned_message:
            raise ValueError("message is empty")

        with self.lock:
            keyword_response = self._run_keyword_skills(cleaned_message)
            if keyword_response:
                return keyword_response

            system_prompt = self.llm.base_system_prompt
            for skill_instruction in lm_activated_skills_dict.values():
                system_prompt += "\n" + skill_instruction
            self.llm.update_system_prompt(system_prompt)

            llm_response = self.llm.process(cleaned_message)
            lm_skill_response = self._run_lm_skills(cleaned_message, llm_response)
            return lm_skill_response or llm_response


app = Flask(__name__)
sessions: dict[str, BuddyWebSession] = {}
sessions_lock = threading.Lock()


def get_session(session_id: str | None) -> tuple[str, BuddyWebSession]:
    if session_id:
        with sessions_lock:
            existing_session = sessions.get(session_id)
        if existing_session is not None:
            return session_id, existing_session

    new_session_id = uuid.uuid4().hex
    new_session = BuddyWebSession()
    with sessions_lock:
        sessions[new_session_id] = new_session
    return new_session_id, new_session


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "provider": llm_config["default_model"]})


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
