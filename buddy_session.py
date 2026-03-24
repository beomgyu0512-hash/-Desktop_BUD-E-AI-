import os
import re
import threading

from analytics_logger import log_event
from api_configs.configs import get_llm_config
from child_profile import format_child_profile_for_prompt, load_child_profile, save_child_profile
from dynamic_memory import format_dynamic_memories_for_prompt, get_dynamic_memory_adapter
from dynamic_memory_rules import evaluate_dynamic_memory_capture
from llm_definition import LanguageModelProcessor
from skill_runtime import (
    conditional_execution,
    extract_opening_and_closing_tags,
    load_skill_registry,
    parse_list_of_lists,
)


llm_config = get_llm_config()
skill_registry = load_skill_registry("skills")


def debug_enabled() -> bool:
    value = os.getenv("BUD_E_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


class BuddySession:
    def __init__(self, session_id: str | None = None, channel: str = "local"):
        self.llm = LanguageModelProcessor(llm_config)
        self.scratch_pad = {"child_profile": load_child_profile()}
        self.dynamic_memory = get_dynamic_memory_adapter()
        self.lock = threading.Lock()
        self.session_id = session_id
        self.channel = channel

    def _build_system_prompt(self, relevant_memories=None) -> str:
        profile = self.scratch_pad.get("child_profile", load_child_profile())
        system_prompt = self.llm.base_system_prompt
        system_prompt += format_child_profile_for_prompt(profile)
        system_prompt += format_dynamic_memories_for_prompt(relevant_memories or [])
        for skill_instruction in skill_registry.lm_activated_skills.values():
            system_prompt += "\n" + skill_instruction
        return system_prompt

    def get_child_profile(self) -> dict:
        profile = self.scratch_pad.get("child_profile")
        if not profile:
            profile = load_child_profile()
            self.scratch_pad["child_profile"] = profile
        return profile

    def refresh_child_profile(self) -> dict:
        profile = load_child_profile()
        self.scratch_pad["child_profile"] = profile
        return profile

    def set_child_profile(self, profile: dict) -> dict:
        saved_profile = save_child_profile(profile)
        self.scratch_pad["child_profile"] = saved_profile
        return saved_profile

    def _search_dynamic_memories(self, message: str):
        child_profile = self.get_child_profile()
        child_id = child_profile.get("child_id", "default_child")

        try:
            memories = self.dynamic_memory.search(query=message, user_id=child_id, limit=3)
            log_event(
                "memory_recall",
                {
                    "session_id": self.session_id,
                    "channel": self.channel,
                    "child_id": child_id,
                    "provider": self.dynamic_memory.provider_name,
                    "query": message,
                    "results_count": len(memories),
                },
            )
            return memories
        except Exception:
            return []

    def _capture_dynamic_memory(self, user_message: str, assistant_message: str):
        child_profile = self.get_child_profile()
        child_id = child_profile.get("child_id", "default_child")
        decision = evaluate_dynamic_memory_capture(user_message, assistant_message)
        log_event(
            "memory_capture_decision",
            {
                "session_id": self.session_id,
                "channel": self.channel,
                "child_id": child_id,
                "provider": self.dynamic_memory.provider_name,
                "should_store": decision.should_store,
                "reason": decision.reason,
                "user_message": decision.user_message,
                "assistant_message": decision.assistant_message,
            },
        )

        if debug_enabled():
            print(f"Dynamic memory capture decision: {decision.reason} (store={decision.should_store})")

        if not decision.should_store:
            return

        try:
            self.dynamic_memory.capture_turn(
                user_id=child_id,
                user_message=decision.user_message,
                assistant_message=decision.assistant_message,
            )
            log_event(
                "memory_capture",
                {
                    "session_id": self.session_id,
                    "channel": self.channel,
                    "child_id": child_id,
                    "provider": self.dynamic_memory.provider_name,
                    "reason": decision.reason,
                },
            )
        except Exception:
            return

    def _run_keyword_skills(self, message: str) -> str:
        all_skill_responses = []

        for function_name, serialized_conditions in skill_registry.keyword_activated_skills.items():
            try:
                condition_list = parse_list_of_lists(serialized_conditions)
                skill_response, updated_conversation, updated_scratch_pad = conditional_execution(
                    skill_registry.functions,
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

    def _build_tool_result_prompt(self, user_message: str, tool_result: str) -> str:
        return (
            f"User request: {user_message}\n"
            f"Tool result: {tool_result}\n"
            "Use the tool result faithfully. Reply in child-friendly Chinese, keep it short, warm, and clear. "
            "If useful, personalize the wording using the stored child profile. "
            "Do not say you used a tool. Do not invent facts beyond the tool result."
        )

    def _run_lm_skills(self, message: str, llm_response: str) -> str | None:
        for function_name, skill_instruction in skill_registry.lm_activated_skills.items():
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
                    skill_registry.functions,
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
            relevant_memories = self._search_dynamic_memories(cleaned_message)
            self.llm.update_system_prompt(self._build_system_prompt(relevant_memories))
            child_id = self.get_child_profile().get("child_id", "default_child")

            if keyword_response:
                try:
                    final_response = self.llm.process(self._build_tool_result_prompt(cleaned_message, keyword_response))
                    log_event(
                        "chat_turn",
                        {
                            "session_id": self.session_id,
                            "channel": self.channel,
                            "child_id": child_id,
                            "user_message": cleaned_message,
                            "assistant_message": final_response,
                            "keyword_skill_response": keyword_response,
                            "dynamic_memory_results": len(relevant_memories),
                            "response_source": "keyword_skill_plus_llm",
                        },
                    )
                    self._capture_dynamic_memory(cleaned_message, final_response)
                    return final_response
                except Exception:
                    log_event(
                        "chat_turn",
                        {
                            "session_id": self.session_id,
                            "channel": self.channel,
                            "child_id": child_id,
                            "user_message": cleaned_message,
                            "assistant_message": keyword_response,
                            "dynamic_memory_results": len(relevant_memories),
                            "response_source": "keyword_skill_only",
                        },
                    )
                    self._capture_dynamic_memory(cleaned_message, keyword_response)
                    return keyword_response

            llm_response = self.llm.process(cleaned_message)
            lm_skill_response = self._run_lm_skills(cleaned_message, llm_response)
            final_response = lm_skill_response or llm_response
            log_event(
                "chat_turn",
                {
                    "session_id": self.session_id,
                    "channel": self.channel,
                    "child_id": child_id,
                    "user_message": cleaned_message,
                    "assistant_message": final_response,
                    "dynamic_memory_results": len(relevant_memories),
                    "response_source": "lm_skill" if lm_skill_response else "llm",
                },
            )
            self._capture_dynamic_memory(cleaned_message, final_response)
            return final_response
