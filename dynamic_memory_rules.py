import re
from dataclasses import dataclass


MAX_CAPTURE_CHARS = 1200


GENERIC_USER_PATTERNS = [
    r"^(你好|您好|hi|hello|hey)$",
    r"^(谢谢|多谢|thank you|thanks)$",
    r"^(再见|bye|goodbye)$",
    r"^(嗯|哦|好|好的|行|可以)$",
]

GENERIC_ASSISTANT_PATTERNS = [
    r"^(好的|收到|明白了|可以的)[。！! ]*$",
    r"^(你好|您好)[。！! ]*$",
    r"^新对话已经开始.*$",
]

EPHEMERAL_PATTERNS = [
    r"现在几点",
    r"几点了",
    r"what time is it",
    r"current time",
    r"今天几号",
    r"天气",
    r"temperature",
    r"你是谁",
]

SENSITIVE_PATTERNS = [
    r"身份证",
    r"护照",
    r"银行卡",
    r"信用卡",
    r"cvv",
    r"验证码",
    r"密码",
    r"password",
    r"家庭住址",
    r"home address",
    r"\b1\d{10}\b",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
]

MEMORY_SIGNAL_PATTERNS = [
    r"我叫",
    r"名字",
    r"年龄",
    r"岁",
    r"喜欢",
    r"不喜欢",
    r"更喜欢",
    r"兴趣",
    r"目标",
    r"想学",
    r"最近在学",
    r"最近学",
    r"家长希望",
    r"家长偏好",
    r"总是",
    r"经常",
    r"老是",
    r"容易",
    r"不会",
    r"总错",
    r"卡住",
    r"需要",
    r"一步一步",
    r"用故事",
    r"用例子",
    r"鼓励",
    r"害怕",
    r"自信",
    r"擅长",
    r"薄弱",
]

LEARNING_SUMMARY_PATTERNS = [
    r"最近.*(容易|总是|经常|老是)",
    r"最近.*(进步|提高|更熟练|更自信)",
    r"(分数|口算|阅读|拼写|单词|加减法|乘法|除法).*(容易|困难|薄弱|卡住|进步)",
    r"(更适合|比较适合|喜欢用).*(图|故事|例子|一步一步|练习)",
]

RAW_EXERCISE_LOG_PATTERNS = [
    r"第\d+题",
    r"题号",
    r"答对\d+题",
    r"答错\d+题",
    r"\b[a-d]\b",
    r"正确答案",
    r"标准答案",
]


@dataclass
class MemoryCaptureDecision:
    should_store: bool
    reason: str
    user_message: str
    assistant_message: str


def _normalize_text(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > MAX_CAPTURE_CHARS:
        cleaned = cleaned[:MAX_CAPTURE_CHARS].rstrip()
    return cleaned


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in patterns)


def evaluate_dynamic_memory_capture(user_message: str, assistant_message: str) -> MemoryCaptureDecision:
    cleaned_user = _normalize_text(user_message)
    cleaned_assistant = _normalize_text(assistant_message)

    if not cleaned_user or not cleaned_assistant:
        return MemoryCaptureDecision(False, "empty_content", cleaned_user, cleaned_assistant)

    combined = f"{cleaned_user}\n{cleaned_assistant}"

    if _matches_any(combined, SENSITIVE_PATTERNS):
        return MemoryCaptureDecision(False, "sensitive_content", cleaned_user, cleaned_assistant)

    if _matches_any(cleaned_user, EPHEMERAL_PATTERNS):
        return MemoryCaptureDecision(False, "ephemeral_request", cleaned_user, cleaned_assistant)

    if _matches_any(cleaned_user, GENERIC_USER_PATTERNS) and _matches_any(cleaned_assistant, GENERIC_ASSISTANT_PATTERNS):
        return MemoryCaptureDecision(False, "generic_exchange", cleaned_user, cleaned_assistant)

    if _matches_any(combined, RAW_EXERCISE_LOG_PATTERNS):
        return MemoryCaptureDecision(False, "raw_exercise_log", cleaned_user, cleaned_assistant)

    if len(cleaned_user) < 8 and len(cleaned_assistant) < 24:
        return MemoryCaptureDecision(False, "too_short", cleaned_user, cleaned_assistant)

    if _matches_any(combined, MEMORY_SIGNAL_PATTERNS):
        return MemoryCaptureDecision(True, "memory_signal", cleaned_user, cleaned_assistant)

    if _matches_any(combined, LEARNING_SUMMARY_PATTERNS):
        return MemoryCaptureDecision(True, "learning_summary", cleaned_user, cleaned_assistant)

    if len(cleaned_user) + len(cleaned_assistant) >= 180:
        return MemoryCaptureDecision(True, "substantive_exchange", cleaned_user, cleaned_assistant)

    return MemoryCaptureDecision(False, "low_value_exchange", cleaned_user, cleaned_assistant)
