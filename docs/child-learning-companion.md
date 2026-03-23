# Child Learning Companion Integration

This repository now includes an optional child-focused project layer that stays compatible with the upstream BUD-E runtime.

## Added assets

- `skills/learning_companion.py`
- `prompts/child_learning_companion_system_prompt.txt`
- `.env.example`

## Why this integration is safe

- The new prompt file is opt-in. BUD-E still uses `system_prompt.txt` by default.
- You can switch prompts by setting `BUD_E_SYSTEM_PROMPT_FILE`.
- The new skills follow the same function signature used by `buddy.py`.
- The main prompt is rebuilt from its base version each turn, so LM skill descriptions do not accumulate repeatedly.

## How to enable child mode

1. Create a virtual environment and install `requirements.txt`.
2. Export the required API keys.
3. Export `BUD_E_SYSTEM_PROMPT_FILE=prompts/child_learning_companion_system_prompt.txt`.
4. Run `python3 buddy.py`.

## Default LLM setup

The project is configured to use Kimi by default.

- `MOONSHOT_API_KEY` is required.
- `KIMI_BASE_URL` defaults to `https://api.moonshot.cn/v1`.
- `KIMI_MODEL` defaults to `moonshot-v1-8k`.

## Running without wake words

If Porcupine is not configured yet, you can skip wake word detection during development:

1. Export `BUD_E_DISABLE_WAKE_WORD=1`.
2. Start `python3 buddy.py`.

The app will enter the conversation loop immediately instead of waiting for `hey-buddy`.

## Testing without microphone

If you want to validate the Kimi conversation flow before fixing microphone streaming:

1. Export `BUD_E_TEXT_MODE=1`.
2. Start `python3 buddy.py`.
3. Type into the terminal prompt instead of speaking.

## Browser-based testing

If you want other people to try Buddy without using the terminal, you can run the minimal web UI:

1. Start `python3 web_app.py`.
2. Open `http://127.0.0.1:8000` in a browser.

The current web UI supports text chat only. It keeps per-browser-session conversation memory in the Flask process and reuses the same prompt and skill pipeline as the terminal mode.
It also includes a parent settings panel that saves long-term child profile data to `child_profile.json`.

## Current child-focused skills

- `explain_for_child`
- `create_study_plan`
- `study_plan_keyword_skill`
- `update_child_profile`
- `child_profile_keyword_skill`

These are intentionally lightweight. They are meant to establish a safe project structure before adding subject-specific lesson skills.

## Minimal long-term memory

This project now stores a simple persistent child profile in `child_profile.json`.

Stored fields:

- `name`
- `age`
- `interests`
- `goals`
- `recent_topics`
- `parent_preferences`

The shared Buddy session loads this file and injects it into the system prompt so web and desktop sessions can personalize replies consistently.

You can override the file path with:

- `BUD_E_CHILD_PROFILE_FILE`

In the browser, these fields can now be edited directly from the parent settings panel instead of only through chat commands.

## Tool results and child-friendly wording

The shared Buddy session now supports a two-step response flow for keyword skills:

1. A local skill can provide factual output first.
2. The LLM then rewrites that factual result into child-friendly Chinese while keeping the tool result accurate.

If the LLM call fails, Buddy falls back to the original tool result.
