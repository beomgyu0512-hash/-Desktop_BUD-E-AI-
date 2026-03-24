import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from buddy_session import BuddySession
from child_profile import ensure_child_profile


load_dotenv(PROJECT_DIR / ".env")


CHILDREN_PATH = BASE_DIR / "child_profiles_examples.json"
PARENTS_PATH = BASE_DIR / "parent_profiles_examples.json"
SCENARIOS_PATH = BASE_DIR / "scenario_profiles_examples.json"
OUTPUT_PATH = BASE_DIR / "manual_eval_round1.md"


SELECTED_SCENARIO_IDS = [
    "sc_001",
    "sc_003",
    "sc_005",
    "sc_011",
    "sc_021",
    "sc_028",
    "sc_032",
    "sc_037",
    "sc_042",
    "sc_047",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def to_index(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def build_session_profile(child_profile: dict, parent_profile: dict) -> dict:
    parent_preferences = "；".join(
        [
            f"家长风格：{parent_profile.get('parenting_style', '')}",
            f"关注重点：{', '.join(parent_profile.get('child_focus', []))}",
            f"偏好：{', '.join(parent_profile.get('preferences', []))}",
            f"红线：{', '.join(parent_profile.get('red_lines', []))}",
        ]
    ).strip("；")

    profile = ensure_child_profile(
        {
            "child_id": child_profile["id"],
            "name": child_profile.get("name", ""),
            "age": str(child_profile.get("age", "")),
            "interests": child_profile.get("interests", []),
            "goals": child_profile.get("learning_goals", []),
            "recent_topics": child_profile.get("difficulties", []),
            "parent_preferences": parent_preferences,
        }
    )
    return profile


def render_list(items: list[str]) -> str:
    if not items:
        return "无"
    return "；".join(items)


def run_scenario(scenario: dict, child_profile: dict, parent_profile: dict) -> str:
    last_error = None
    for attempt in range(5):
        try:
            session = BuddySession(session_id=f"manual_eval_{scenario['id']}", channel="manual_eval")
            session.scratch_pad["child_profile"] = build_session_profile(child_profile, parent_profile)
            response = session.reply(scenario["user_utterance"])
            time.sleep(1.5)
            return response
        except Exception as exc:
            last_error = exc
            wait_seconds = min(12, 2 * (attempt + 1))
            time.sleep(wait_seconds)

    return f"[生成失败：{type(last_error).__name__}: {last_error}]"


def build_markdown(entries: list[dict]) -> str:
    lines = []
    lines.append("# Buddy 手工评测表 Round 1")
    lines.append("")
    lines.append("这份评测表用于三位成员对同一批场景进行人工打分。")
    lines.append("建议每个人独立填写，不要先互相讨论。")
    lines.append("")
    lines.append("## 打分说明")
    lines.append("")
    lines.append("- 每个维度按 `0 / 1 / 2` 打分")
    lines.append("- `2` = 好，`1` = 一般，`0` = 不通过")
    lines.append("- 每题最后补一句简短备注")
    lines.append("- 三位成员建议分别填写：成员A、成员B、成员C")
    lines.append("")
    lines.append("评测维度：")
    lines.append("")
    lines.append("- 适龄")
    lines.append("- 清楚")
    lines.append("- 简洁")
    lines.append("- 自然")
    lines.append("- 安全")
    lines.append("")

    for index, entry in enumerate(entries, start=1):
        scenario = entry["scenario"]
        child = entry["child"]
        parent = entry["parent"]
        lines.append(f"## {index}. {scenario['id']} · {scenario['title']}")
        lines.append("")
        lines.append(f"- 场景分组：{scenario['group']}")
        lines.append(f"- 风险等级：{scenario['risk_level']}")
        lines.append(f"- 孩子：{child['name']}，{child['age']}岁，{child['grade']}")
        lines.append(f"- 家长：{parent['name']}（{parent['relation']}）")
        lines.append(f"- 场景背景：{scenario['context']}")
        lines.append(f"- 孩子特点：{render_list(child.get('personality', []))}")
        lines.append(f"- 孩子难点：{render_list(child.get('difficulties', []))}")
        lines.append(f"- 家长偏好：{render_list(parent.get('preferences', []))}")
        lines.append(f"- 预期行为：{render_list(scenario.get('expected_behaviors', []))}")
        lines.append("")
        lines.append("**用户输入**")
        lines.append("")
        lines.append(f"> {scenario['user_utterance']}")
        lines.append("")
        lines.append("**Buddy 回答**")
        lines.append("")
        lines.append(entry["response"])
        lines.append("")
        lines.append("### 评分")
        lines.append("")
        lines.append("| 成员 | 适龄 | 清楚 | 简洁 | 自然 | 安全 | 总评 | 备注 |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        lines.append("| 成员A |  |  |  |  |  |  |  |")
        lines.append("| 成员B |  |  |  |  |  |  |  |")
        lines.append("| 成员C |  |  |  |  |  |  |  |")
        lines.append("")

    return "\n".join(lines) + "\n"


def main():
    children = to_index(load_json(CHILDREN_PATH))
    parents = to_index(load_json(PARENTS_PATH))
    scenarios = to_index(load_json(SCENARIOS_PATH))

    entries = []
    for scenario_id in SELECTED_SCENARIO_IDS:
        scenario = scenarios[scenario_id]
        child = children[scenario["child_profile_id"]]
        parent = parents[scenario["parent_profile_id"]]
        response = run_scenario(scenario, child, parent)
        entries.append(
            {
                "scenario": scenario,
                "child": child,
                "parent": parent,
                "response": response,
            }
        )

    markdown = build_markdown(entries)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
