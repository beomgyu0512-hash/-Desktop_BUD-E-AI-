import re
import threading

from api_configs.configs import get_llm_config
from child_profile import format_child_profile_for_prompt, load_child_profile, save_child_profile
from llm_definition import LanguageModelProcessor
from skill_runtime import (
    conditional_execution,
    extract_opening_and_closing_tags,
    load_skill_registry,
    parse_list_of_lists,
)


llm_config = get_llm_config()
skill_registry = load_skill_registry("skills")


class BuddySession:
    def __init__(self):
        self.llm = LanguageModelProcessor(llm_config)
        self.scratch_pad = {"child_profile": load_child_profile()}
        self.lock = threading.Lock()

    def _build_system_prompt(self) -> str:
        profile = self.scratch_pad.get("child_profile", load_child_profile())
        system_prompt = self.llm.base_system_prompt
        system_prompt += format_child_profile_for_prompt(profile)
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
            self.llm.update_system_prompt(self._build_system_prompt())

            if keyword_response:
                try:
                    return self.llm.process(self._build_tool_result_prompt(cleaned_message, keyword_response))
                except Exception:
                    return keyword_response

            llm_response = self.llm.process(cleaned_message)
            lm_skill_response = self._run_lm_skills(cleaned_message, llm_response)
            return lm_skill_response or llm_response
