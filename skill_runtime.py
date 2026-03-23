import importlib.util
import inspect
import os
import re
from dataclasses import dataclass


SKILL_COMMENT_KEYWORDS = ("KEYWORD ACTIVATED SKILL:", "LM ACTIVATED SKILL:")


def debug_enabled() -> bool:
    value = os.getenv("BUD_E_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def extract_skill_function_names_from_file(filepath: str, keywords=SKILL_COMMENT_KEYWORDS) -> set[str]:
    skill_function_names = set()

    with open(filepath, "r") as file:
        lines = file.readlines()

    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for i in range(len(lines) - 1):
        if any(keyword in lines[i].lower() for keyword in lowered_keywords):
            if re.match(r"^\s*def\s+\w+\s*\(", lines[i + 1]):
                function_name = re.findall(r"def\s+(\w+)\s*\(", lines[i + 1])[0]
                skill_function_names.add(function_name)

    return skill_function_names


def import_all_functions_from_directory(directory: str) -> dict[str, callable]:
    activated_skills = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".py"):
            continue

        module_name = filename[:-3]
        filepath = os.path.join(directory, filename)
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        skill_function_names = extract_skill_function_names_from_file(filepath)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            is_module_function = inspect.isfunction(attr) and attr.__module__ == module.__name__
            if is_module_function and attr_name in skill_function_names:
                activated_skills[attr_name] = attr
                if debug_enabled():
                    print(f"Imported function: {attr_name} from module {module_name}")

    return activated_skills


def extract_activated_skills_from_directory(directory: str, keyword: str) -> dict[str, str]:
    activated_skills = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".py"):
            continue

        filepath = os.path.join(directory, filename)
        with open(filepath, "r") as file:
            lines = file.readlines()

        for i in range(len(lines) - 1):
            if keyword.lower() in lines[i].lower():
                if re.match(r"^\s*def\s+\w+\s*\(", lines[i + 1]):
                    function_name = re.findall(r"def\s+(\w+)\s*\(", lines[i + 1])[0]
                    comment = lines[i].strip().split(keyword)[-1].strip()
                    activated_skills[function_name] = comment

    return activated_skills


def parse_list_of_lists(input_str):
    normalized_str = re.sub(r"\'", "\"", input_str)
    sublist_matches = re.findall(r"\[(.*?)\]", normalized_str)

    result = []
    for sublist in sublist_matches:
        strings = re.findall(r"\"(.*?)\"", sublist)
        result.append(strings)

    return result


def conditional_execution(function_map, function_name, transcription_response, conversation, scratch_pad, conditions_list=None, lm_generated_parameters=""):
    if conditions_list is None:
        conditions_list = []

    function_to_run = function_map.get(function_name)
    if function_to_run is None:
        raise ValueError(f"The specified function '{function_name}' is not defined.")

    if not callable(function_to_run):
        raise ValueError(f"The function '{function_name}' is not callable.")

    if conditions_list:
        for condition in conditions_list:
            if all(substring.lower() in transcription_response.lower() for substring in condition):
                return function_to_run(transcription_response, conversation, scratch_pad, lm_generated_parameters)
    else:
        return function_to_run(transcription_response, conversation, scratch_pad, lm_generated_parameters)

    return "", conversation, scratch_pad


def extract_opening_and_closing_tags(input_string):
    tags = re.findall(r"<[^>]+>", input_string)
    if not tags:
        return None, None

    opening_tag = next((tag for tag in tags if not tag.startswith("</")), None)
    closing_tag = next((tag for tag in tags if tag.startswith("</") and opening_tag and tag[2:-1] in opening_tag), None)
    return opening_tag, closing_tag


@dataclass
class SkillRegistry:
    functions: dict[str, callable]
    keyword_activated_skills: dict[str, str]
    lm_activated_skills: dict[str, str]


def load_skill_registry(directory: str = "skills") -> SkillRegistry:
    functions = import_all_functions_from_directory(directory)
    keyword_activated_skills = extract_activated_skills_from_directory(directory, "KEYWORD ACTIVATED SKILL:")
    lm_activated_skills = extract_activated_skills_from_directory(directory, "LM ACTIVATED SKILL:")

    if debug_enabled():
        print(keyword_activated_skills)
        print(lm_activated_skills)

    return SkillRegistry(
        functions=functions,
        keyword_activated_skills=keyword_activated_skills,
        lm_activated_skills=lm_activated_skills,
    )
