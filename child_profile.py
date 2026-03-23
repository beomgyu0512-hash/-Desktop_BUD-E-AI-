import json
import os
from pathlib import Path


DEFAULT_CHILD_PROFILE_PATH = "child_profile.json"


def get_child_profile_path() -> Path:
    return Path(os.getenv("BUD_E_CHILD_PROFILE_FILE", DEFAULT_CHILD_PROFILE_PATH))


def default_child_profile() -> dict:
    return {
        "name": "",
        "age": "",
        "interests": [],
        "goals": [],
        "recent_topics": [],
        "parent_preferences": "",
    }


def load_child_profile() -> dict:
    path = get_child_profile_path()
    if not path.exists():
        return default_child_profile()

    try:
        with open(path, "r", encoding="utf-8") as file:
            profile = json.load(file)
    except Exception:
        return default_child_profile()

    merged = default_child_profile()
    merged.update(profile)
    return merged


def save_child_profile(profile: dict) -> dict:
    normalized = default_child_profile()
    normalized.update(profile or {})

    path = get_child_profile_path()
    with open(path, "w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2)

    return normalized


def format_child_profile_for_prompt(profile: dict) -> str:
    interests = ", ".join(profile.get("interests", [])) or "unknown"
    goals = ", ".join(profile.get("goals", [])) or "unknown"
    recent_topics = ", ".join(profile.get("recent_topics", [])) or "unknown"
    parent_preferences = profile.get("parent_preferences") or "unknown"
    name = profile.get("name") or "unknown"
    age = profile.get("age") or "unknown"

    return (
        "\nChild profile memory:\n"
        f"- name: {name}\n"
        f"- age: {age}\n"
        f"- interests: {interests}\n"
        f"- goals: {goals}\n"
        f"- recent_topics: {recent_topics}\n"
        f"- parent_preferences: {parent_preferences}\n"
        "- Use this memory when it helps personalize teaching.\n"
        "- Do not invent missing profile details.\n"
    )
