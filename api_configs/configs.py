import os

from dotenv import load_dotenv

load_dotenv()
llm_config = {
    "default_model": "kimi",
    "models": {
        "kimi": {
            "model_name": os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
            "temperature": 0,
            "api_key": os.getenv("MOONSHOT_API_KEY"),
            "base_url": os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1"),
        },
        "together": {
            "model": "meta-llama/Llama-3-8b-chat-hf",
            "max_tokens": 400,
            "api_key": os.getenv("TOGETHER_API_KEY"),
        },
        "groq": {
            "model_name": "llama3-8b-8192",
            "temperature": 0,
            "api_key": os.getenv("GROQ_API_KEY"),
        },
        "openai_gpt4": {
            "model_name": "gpt-4-0125-preview",
            "temperature": 0.5,
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        "openai_gpt35": {
            "model_name": "gpt-3.5-turbo-0125",
            "temperature": 0.5,
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    }
}


tts_config = {
    "default_api": "deepgram",
    "apis": {
        "deepgram": {
            "model": "aura-helios-en",

            "api_key": os.getenv("DEEPGRAM_API_KEY"),
                    },
              }
}



asr_config = {
    "default_api": "deepgram",
    "apis": {
        "deepgram": {
            "model": "nova-2",
            "language":"en-US",
            "sample_rate":16000,

            "api_key": os.getenv("DEEPGRAM_API_KEY"),
                    },
              }
}


def get_llm_config():
	return llm_config
	

def get_tts_config():
	return tts_config

def get_asr_config():
	return asr_config
