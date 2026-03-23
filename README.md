# BUD-E explains itself

<p align="center">
  <a href="https://youtu.be/RYdWd7hRZQk">
    <img src="https://github.com/LAION-AI/Desktop_BUD-E/blob/main/BUD-E-Yt.jpg?raw=true" alt="BUD-E Framework Introduction">
  </a>
</p>

## Project Vision

BUD-E, short for "Buddy", is an innovative voice assistant framework designed to be a plug-and-play interface that allows seamless interaction with open-source AI models and API interfaces. The framework aims to empower anyone to contribute and innovate, particularly in education and research, by maintaining a low entry threshold for writing new skills and building a supportive community.

## Key Features and Flexibility

BUD-E integrates several core components including a speech-to-text model, a language model, and a text-to-speech model. These components are interchangeable and can be accessed either locally or through APIs. The framework supports integration with services from leading providers like OpenAI and Anthropic, or allows users to deploy their own models using open-source frameworks like Ollama or VLLM.

### Skills Interface

Any Python function can become a skill, allowing the voice assistant to handle tasks ranging from processing screenshots with captioning and OCR models to interacting with clipboard contents including text, images, and links. BUD-E supports dynamic skill activation, either by allowing the language model to choose a skill from a "menu" that gets dynamically added to the system prompt or through direct keywords said by the user. 
Skills get dynamically added from the "skills" folder to the system, without any need to change the main code (buddy.py). Think of it as similar to adding mods to the "Mods" folder in Minecraft.

## Community and Educational Focus

BUD-E is dedicated to fostering a community-centric development environment with a strong emphasis on education and research. The framework encourages the development of skills that aid in educational content delivery, such as navigating through specific online courses or generating custom learning paths from YouTube playlists.

## Installation Instructions

The current version of BUD-E currently uses Deepgram for the audio service and Groq the LLM. For the wake word detection it uses Porcupine from Pico Voice ( https://picovoice.ai/platform/porcupine/ ). We are working on a stack of open source models that can very soon run it completely local or on your own API server.

Recommendation: Make a venv and install everything in the venv. Make sure your microphone works.

Set your API keys here:
```sh
echo 'export PORCUPINE_API_KEY="yourporcupineapikeyhere"' >> ~/.bashrc
echo 'export MOONSHOT_API_KEY="yourkimiapikeyhere"' >> ~/.bashrc
echo 'export KIMI_BASE_URL="https://api.moonshot.cn/v1"' >> ~/.bashrc
echo 'export KIMI_MODEL="moonshot-v1-8k"' >> ~/.bashrc
echo 'export DEEPGRAM_API_KEY="yourdeepgramapikeyhere"' >> ~/.bashrc
source ~/.bashrc
```

Clone the repository and install the required packages:
```sh
git clone https://github.com/christophschuhmann/Desktop_BUD-E
pip install -U -r requirements.txt
python3 buddy.py
```

## Child Learning Companion Layer

This fork also includes an optional child-focused project layer:

- child-oriented prompt at `prompts/child_learning_companion_system_prompt.txt`
- starter educational skills at `skills/learning_companion.py`
- setup notes at `docs/child-learning-companion.md`

To enable the child-focused prompt for a run:
```sh
export BUD_E_SYSTEM_PROMPT_FILE=prompts/child_learning_companion_system_prompt.txt
python3 buddy.py
```

To run without a wake word during development:
```sh
export BUD_E_DISABLE_WAKE_WORD=1
python3 buddy.py
```

To test without microphone input:
```sh
export BUD_E_TEXT_MODE=1
python3 buddy.py
```

## Browser UI

This fork also includes a minimal browser-based Buddy chat UI.

Start it with:
```sh
python3 web_app.py
```

Then open:
```sh
http://127.0.0.1:8000
```

Optional environment variables:

- `BUD_E_WEB_HOST` defaults to `127.0.0.1`
- `BUD_E_WEB_PORT` defaults to `8000`

The current web version is text-only. It reuses the same prompt and skill pipeline as the terminal flow, including local keyword skills such as telling the current time.

It now also includes a parent settings panel that edits the persistent child profile directly from the browser.
The panel can update:

- child name
- age
- interests
- learning goals
- recent topics
- parent preferences

To let other devices on the same local network open it:
```sh
BUD_E_WEB_HOST=0.0.0.0 python3 web_app.py
```

Then open `http://YOUR_LAN_IP:8000` from another device on the same Wi-Fi.

For deployment notes, see `docs/deployment.md`.

## Desktop App

This fork also includes a minimal PySide6 desktop client for local text chat.

Start it with:
```sh
python3 desktop_app.py
```

The desktop app reuses the same session, prompt, and skill pipeline as the web version, but runs as a local native window.

## Default LLM provider

This fork is configured to use the Kimi API by default through Moonshot's OpenAI-compatible endpoint.

Required environment variables:

- `MOONSHOT_API_KEY`
- `KIMI_BASE_URL` defaults to `https://api.moonshot.cn/v1`
- `KIMI_MODEL` defaults to `moonshot-v1-8k`

## Long-term child memory

This fork now includes a minimal persistent child profile stored in:

- `child_profile.json`

The shared Buddy session injects this memory into the system prompt for personalization.

Current profile fields:

- `name`
- `age`
- `interests`
- `goals`
- `recent_topics`
- `parent_preferences`

You can move the file by setting:

- `BUD_E_CHILD_PROFILE_FILE`

The browser-based parent settings panel reads and writes this file through `/api/profile`.

## Skills

### Types of Skills
BUD-E supports two types of skills: LM Activated Skills and Keyword Activated Skills.

#### LM Activated Skills
These are Python functions that the language model (LM) can call when it deems the function useful for a given request. Each LM Activated Skill requires a specific comment structure before the function definition.

Example:
```python
# LM ACTIVATED SKILL: TITLE: Weather Report DESCRIPTION: Provides the current weather for a given location. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <weather_report> ... </weather_report> Example: <weather_report> Hamburg </weather_report>
def weather_report(location):
    # Implementation to fetch and return weather report for the location
    pass
```

#### Keyword Activated Skills
These skills are activated based on specific keyword combinations present in the user's input. They also require a specific comment structure before the function definition.

Example:
```python
# KEYWORD ACTIVATED SKILL: [["weather", "report"], ["forecast", "today"]]
def weather_report_skill():
    # Implementation to fetch and return today's weather forecast
    pass
```

### Skill Usage
Skills in the BUD-E framework are used either by the language model dynamically choosing the appropriate skill or by the user triggering them through specific keywords. The integration of skills is seamless, allowing for an intuitive and flexible interaction with the voice assistant.


## Call for Collaboration

This project is led by LAION, with support from Intel, Camb AI, Alignment Labs, the Max Planck Institute for Intelligent Systems in Tübingen, and the Tübingen AI Center. We invite collaboration from open-source communities, educational and research institutions, and interested companies to help scale BUD-E’s impact.

We encourage contributions that push the boundaries of educational and research tools, leveraging the collective creativity and expertise of the global open-source community.
