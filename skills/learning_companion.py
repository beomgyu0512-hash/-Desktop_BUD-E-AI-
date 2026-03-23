"""Child-focused BUD-E skills kept compatible with the current buddy.py skill runner."""

from datetime import datetime
from child_profile import load_child_profile, save_child_profile


# LM ACTIVATED SKILL: TITLE: Explain for a Child DESCRIPTION: Rewrites a concept into an age-appropriate explanation for a child. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <explain_for_child> concept or question </explain_for_child> Example: <explain_for_child> What is gravity? </explain_for_child>
def explain_for_child(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    request = (LMGeneratedParameters or transcription_response or "").strip()
    request = " ".join(request.split())
    if not request:
        request = "the topic the child just asked about"

    skill_response = (
        f"Let's learn about {request}. "
        "I will explain it simply, give one everyday example, "
        "and end with one short check question."
    )
    return skill_response, conversation, scratch_pad


# LM ACTIVATED SKILL: TITLE: Create Study Plan DESCRIPTION: Creates a short study session plan for a child around one topic. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <create_study_plan> topic: fractions; age: 8; duration: 10 minutes </create_study_plan> Example: <create_study_plan> topic: solar system; age: 7; duration: 12 minutes </create_study_plan>
def create_study_plan(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    request = (LMGeneratedParameters or transcription_response or "").strip()
    request = " ".join(request.split())
    if not request:
        request = "topic: learning practice; age: child; duration: 10 minutes"

    skill_response = (
        f"Here is a short child-friendly study plan for {request}. "
        "Start with one warm-up question, teach the core idea in two small steps, "
        "do two practice prompts, then finish with a recap."
    )
    return skill_response, conversation, scratch_pad


# LM ACTIVATED SKILL: TITLE: Tell Current Time DESCRIPTION: Returns the current local time for the child in a short, friendly format. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <tell_current_time> now </tell_current_time> Example: <tell_current_time> 现在几点 </tell_current_time>
def tell_current_time(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    now = datetime.now()
    skill_response = f"现在是{now.hour}点{now.minute:02d}分。"
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["study plan"], ["learning plan"], ["practice with me"]]
def study_plan_keyword_skill(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    skill_response = (
        "I can help build a short learning plan. "
        "Tell me the topic, the child's age, and how many minutes you want."
    )
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["现在几点"], ["几点了"], ["what time is it"], ["current time"]]
def tell_current_time_keyword_skill(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    now = datetime.now()
    skill_response = f"现在是{now.hour}点{now.minute:02d}分。"
    return skill_response, conversation, scratch_pad


# LM ACTIVATED SKILL: TITLE: Update Child Profile DESCRIPTION: Saves important long-term learning details about the child, such as name, age, interests, goals, recent topics, or parent preferences. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <update_child_profile> name: Mia; age: 8; interests: space, drawing; goals: reading confidence; parent_preferences: short sessions </update_child_profile> Example: <update_child_profile> name: Leo; age: 7; interests: dinosaurs, math; recent_topics: fractions </update_child_profile>
def update_child_profile(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    profile = scratch_pad.get("child_profile", load_child_profile())
    payload = (LMGeneratedParameters or transcription_response or "").strip()

    for item in [segment.strip() for segment in payload.split(";") if segment.strip()]:
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if key in {"name", "age", "parent_preferences"}:
            profile[key] = value
        elif key in {"interests", "goals", "recent_topics"}:
            profile[key] = [entry.strip() for entry in value.split(",") if entry.strip()]

    saved_profile = save_child_profile(profile)
    scratch_pad["child_profile"] = saved_profile

    summary_parts = []
    if saved_profile.get("name"):
        summary_parts.append(f"姓名：{saved_profile['name']}")
    if saved_profile.get("age"):
        summary_parts.append(f"年龄：{saved_profile['age']}")
    if saved_profile.get("interests"):
        summary_parts.append(f"兴趣：{', '.join(saved_profile['interests'])}")
    if saved_profile.get("goals"):
        summary_parts.append(f"目标：{', '.join(saved_profile['goals'])}")
    if saved_profile.get("recent_topics"):
        summary_parts.append(f"最近主题：{', '.join(saved_profile['recent_topics'])}")
    if saved_profile.get("parent_preferences"):
        summary_parts.append(f"家长偏好：{saved_profile['parent_preferences']}")

    skill_response = "我已经记住这些长期学习信息：" + "；".join(summary_parts) if summary_parts else "我还没有收到可保存的孩子资料。"
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["记住这个孩子"], ["更新孩子资料"], ["保存孩子信息"], ["家长设置"]]
def child_profile_keyword_skill(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    skill_response = (
        "你可以告诉我孩子的长期信息，比如：姓名、年龄、兴趣、学习目标、最近在学什么、家长偏好。"
        "例如：更新孩子资料 name: Mia; age: 8; interests: space, drawing; goals: reading confidence"
    )
    return skill_response, conversation, scratch_pad
