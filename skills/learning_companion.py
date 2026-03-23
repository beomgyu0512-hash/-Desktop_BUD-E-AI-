"""Child-focused BUD-E skills kept compatible with the current buddy.py skill runner."""

from datetime import datetime


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
