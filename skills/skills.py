import json
import random
from PIL import Image
import threading
import io
import requests
import json
import base64
import os
import re
import subprocess
import time 

import sys
from urllib.parse import unquote, urlparse
from pathlib import Path

try:
    import clipboard
except Exception:
    clipboard = None

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

try:
    from pyautogui import screenshot
except Exception:
    screenshot = None

# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add the parent directory to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../api_configs')))


from florence2 import handle_captioning_florence2
from florence2 import handle_ocr_florence2
from florence2 import send_image_for_captioning_florence2
from florence2 import send_image_for_ocr_florence2

from hyprlab import send_image_for_captioning_and_ocr_hyprlab_gpt4o


from dl_yt_subtitles import download_youtube_video_info, extract_and_concat_subtitle_text, find_first_youtube_url, extract_title, extract_description

# Import configurations from a local module
from api_configs.configs import get_llm_config, get_tts_config, get_asr_config


# Import LangChain components for natural language processing tasks
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


# Import configurations from a local module
from api_configs.configs import get_llm_config, get_tts_config, get_asr_config

from llm_definition import get_llm, LanguageModelProcessor


from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain

# Get configuration for the language model
llm_config = get_llm_config()

llm = LanguageModelProcessor(llm_config)

# YOU CAN CALL THE STANDARD LLM LIKE THIS WITHOUT MEMORY TO MAKE LLM CALLS WITHIN SKILLS
# llm_response = llm.llm_call_without_memory("2+3=?")
# print("llm_response", str(llm_response))




# URL of the API
url = 'https://api.hyprlab.io/v1/chat/completions'
HYPRLAB_API_KEY = "hypr-lab-xxxxxxx" # os.getenv("HYPRLAB_API_KEY")

florence2_server_url = "http://213.173.96.19:5002/" 


def desktop_feature_unavailable_response(feature_name, conversation, scratch_pad):
    skill_response = f"{feature_name} is not available in this server environment."
    return skill_response, conversation, scratch_pad



def send_image_for_captioning_and_ocr_hyprlab_gpt4o (img_byte_arr):
	
	#print(HYPRLAB_API_KEY)
	# Headers for the request
	headers = {
	    'Content-Type': 'application/json',
	    'Authorization': f'Bearer {HYPRLAB_API_KEY}'
	}

	encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')

	# Data to be sent
	data = {
	    "model": "gpt-4o",
	    "messages": [
		{
		    "role": "system",
		    "content": "You are ChatGPT, a large language model trained by OpenAI.\nCarefully heed the user's instructions.\nRespond using Markdown"
		},
		{
		    "role": "user",
		    "content": [
		        {
		            "type": "text",
		            "text": "Describe this image with many details including texts, equations, diagrams & tables. Describe what can be seen with many details and explain what can be seen where. If there is any excercise or problem in it, provide a brief, correct solution."
		        },
		        {
		            "type": "image_url",
		            "image_url": {
		                "url": f"data:image/jpeg;base64,{encoded_image}",
		                "detail": "high"
		            }
		        }
		    ]
		}
	    ]
	}

	# Send request and receive response
	response = requests.post(url, headers=headers, json=data)
       
	# Output response
	print(response.status_code)
	print(response.text)
	response_dict = json.loads(response.text)
	
	return response_dict["choices"][0]["message"]["content"]




# KEYWORD ####DEACTIVATED### ACTIVATED SKILL:[ ["have a look"], [ "buddy look"], ["look buddy"], ["buddy, look" ], ["look, buddy" ]  ]
def get_caption_from_clipboard_gpt4o_hyprlab(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    # Check clipboard content

    
    skill_response = "What BUD-E is seeing: "
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    if ImageGrab is None and clipboard is None:
        return desktop_feature_unavailable_response("Clipboard access", conversation, scratch_pad)


    try:
       content = ImageGrab.grabclipboard()
    except:
        content = clipboard.paste()
        print(type(content))
        if isinstance(content, str):
            if ("https://www.youtu" in content or "https://youtu" in content ) and len(content)<100:
                print("Analyzing Youtube Video")
                video_metadata= download_youtube_video_info(find_first_youtube_url(content))
                print(video_metadata)
                subtitle_text= extract_and_concat_subtitle_text(str(video_metadata))
                print(subtitle_text)
                print(len(subtitle_text))
                skill_response+= subtitle_text [:6000] 
                print(skill_response)
                return skill_response , updated_conversation, updated_scratch_pad 
                
            else:
              print("Returning text from the clipboard...")
              skill_response+= content
              return skill_response , updated_conversation, updated_scratch_pad 
    print(content)
    print(type(content))
    
    
    if isinstance(content, Image.Image):
        print("Processing an image from the clipboard...")
        if content.mode != 'RGB':
            content = content.convert('RGB')
            
        # Save image to a byte array
        img_byte_arr = io.BytesIO()
        content.save(img_byte_arr, format='JPEG', quality=60)
        img_byte_arr = img_byte_arr.getvalue()


        # Send image for captioning and return the result
        combined_caption = send_image_for_captioning_and_ocr_hyprlab_gpt4o(img_byte_arr)

        print(combined_caption)
        
        skill_response += combined_caption
   
  
        return   skill_response, updated_conversation, updated_scratch_pad   

    else:
        skill_response += "No image or text data found in the clipboard."

        return skill_response, updated_conversation, updated_scratch_pad 


# KEYWORD ####DEACTIVATED### ACTIVATED SKILL:[ ["have a look", "screen"], [ "buddy look at the screen"], ["look buddy at the screen"], ["buddy, look at the screen" ], ["look, buddy" , "screenshot"]  ]
def get_caption_from_screenshot_gpt4o_hyprlab(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):

    
    skill_response = "What BUD-E is seeing: "
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    if screenshot is None:
        return desktop_feature_unavailable_response("Screenshot capture", conversation, scratch_pad)



    # Take a screenshot and open it with PIL
    print("Taking a screenshot...")
    screenshot_image = screenshot()  # Uses PyAutoGUI to take a screenshot
    width, height = screenshot_image.size
    new_height = 500
    new_width = int((new_height / height) * width)
    
    # Resizing with the correct resampling filter
    resized_image = screenshot_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save the resized image as JPEG
    img_byte_arr = io.BytesIO()
    resized_image.save(img_byte_arr, format='JPEG', quality=70)
    screenshot_image.save(img_byte_arr, format='JPEG', quality=70)
    img_byte_arr = img_byte_arr.getvalue()

    # Send image for captioning and return the result
    combined_caption = send_image_for_captioning_and_ocr_hyprlab_gpt4o(img_byte_arr)
   
    print(combined_caption)

    skill_response += combined_caption
   
  
    return skill_response , updated_conversation, updated_scratch_pad 


# KEYWORD ACTIVATED SKILL:[ ["have a look", "screen"], ["look buddy at the screen"], ["buddy, look at the screen" ], ["look, buddy" , "screenshot"]  ]
def get_caption_from_screenshot_florence2(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):


    skill_response = "What BUD-E is seeing: "
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    if screenshot is None:
        return desktop_feature_unavailable_response("Screenshot capture", conversation, scratch_pad)


    # Take a screenshot and open it with PIL
    print("Taking a screenshot...")
    screenshot_image = screenshot()  # Uses PyAutoGUI to take a screenshot
    #width, height = screenshot_image.size
    #new_height = 800
    #new_width = int((new_height / height) * width)
    
    # Resizing with the correct resampling filter
    #resized_image = screenshot_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Save the resized image as JPEG
    img_byte_arr = io.BytesIO()
    #resized_image.save(img_byte_arr, format='JPEG', quality=60)
    screenshot_image.save(img_byte_arr, format='JPEG', quality=60)
    img_byte_arr = img_byte_arr.getvalue()

    # Send image for captioning and return the result
    #caption = send_image_for_captioning(img_byte_arr)
    #ocr_result= send_image_for_ocr(img_byte_arr)
    #print(ocr_result)
    #caption += "\nOCR RESULTS:\n"+ocr_result
    
    results = {}
    
    thread1 = threading.Thread(target=handle_captioning_florence2, args=(img_byte_arr, results))
    thread2 = threading.Thread(target=handle_ocr_florence2, args=(img_byte_arr, results))

    # Start threads
    thread1.start()
    #time.sleep(2)
    thread2.start()

    # Wait for threads to complete
    thread1.join()
    thread2.join()
    print(results)
    # Combine results and print
    combined_caption = results['caption'] + "\nOCR RESULTS:\n"+ results['ocr']

    skill_response += combined_caption
        
    return  skill_response, updated_conversation, updated_scratch_pad   






# KEYWORD ACTIVATED SKILL:[ ["have a look"], [ "buddy look"], ["look buddy"], ["buddy, look" ], ["look, buddy" ]  ]
def get_caption_from_clipboard_florence2(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):

    skill_response = "What BUD-E is seeing: "
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    if ImageGrab is None and clipboard is None:
        return desktop_feature_unavailable_response("Clipboard access", conversation, scratch_pad)



    # Check clipboard content

    try:
       content = ImageGrab.grabclipboard()
    except:
        content = clipboard.paste()
        print(type(content))
        if isinstance(content, str):
            if "https://www.youtu" in content and len(content)<100:
                video_metadata= download_youtube_video_info(find_first_youtube_url(content))
                title = extract_title(str(video_metadata))
                desc = extract_description(str(video_metadata))
                subtitle_text= extract_and_concat_subtitle_text(str(video_metadata))
                
                #print(subtitle_text)
                #print(len(subtitle_text))
                skill_response+= f"Title: {title} \n Description: {desc} \n{subtitle_text[:8000] }"
                
                return skill_response , updated_conversation, updated_scratch_pad 
                
            else:
              print("Returning text from the clipboard...")
              skill_response+= content
              return skill_response , updated_conversation, updated_scratch_pad 
    print(content)
    print(type(content))



    if isinstance(content, Image.Image):
        print("Processing an image from the clipboard...")
        if content.mode != 'RGB':
            content = content.convert('RGB')
            
        # Save image to a byte array
        img_byte_arr = io.BytesIO()
        content.save(img_byte_arr, format='JPEG', quality=60)
        img_byte_arr = img_byte_arr.getvalue()

        results = {}
        
        # Define tasks for threads
        thread1 = threading.Thread(target=handle_captioning_florence2, args=(img_byte_arr, results))
        thread2 = threading.Thread(target=handle_ocr_florence2, args=(img_byte_arr, results))

        # Start threads
        thread1.start()
        thread2.start()

        # Wait for threads to complete
        thread1.join()
        thread2.join()

        # Combine results and return
        combined_caption = results.get('caption', '') + "\nOCR RESULTS:\n" + results.get('ocr', '')
        skill_response += combined_caption

        return  skill_response, updated_conversation, updated_scratch_pad   

    else:
        skill_response += "No image or text data found in the clipboard."

        return  skill_response, updated_conversation, updated_scratch_pad     





# KEYWORD ACTIVATED SKILL: [["twinkle twinkle little star"], ["twinkle, twinkle, little, star"], ["twinkle twinkle, little star"], ["twinkle, twinkle little star"] , ["Twinkle, twinkle, little star"], ["twinkle, little star"], ["twinkle little star"]]
def print_twinkling_star(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    # Simulated animation of a twinkling star using ASCII art

    star_frames = [
        """
             ☆ 
            ☆☆☆
           ☆☆☆☆☆
            ☆☆☆
             ☆
        """,
        """
             ✦
            ✦✦✦
           ✦✦✦✦✦
            ✦✦✦
             ✦
        """
    ]

    skill_response = "Twinkle, twinkle, little star!\n"
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    for _ in range(3):  # Loop to display the animation multiple times
        for frame in star_frames:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console window
            print(skill_response + frame)
            time.sleep(0.5)  # Wait for half a second before showing the next frame

    return skill_response, updated_conversation, updated_scratch_pad




def launch_with_default_app(target):
    if sys.platform == "darwin":
        subprocess.Popen(["open", target])
        return

    if os.name == "nt":
        os.startfile(target)
        return

    subprocess.Popen(["xdg-open", target])


def open_site(url):
    launch_with_default_app(url)


def normalize_local_path(raw_path):
    candidate = (raw_path or "").strip().strip('"').strip("'")
    if not candidate:
        return None

    if candidate.startswith("file://"):
        parsed = urlparse(candidate)
        candidate = unquote(parsed.path)

    candidate = os.path.expanduser(candidate)

    if not os.path.isabs(candidate):
        candidate = os.path.abspath(candidate)

    if not os.path.exists(candidate):
        return None

    return candidate


def describe_local_target(path):
    if os.path.isdir(path):
        return "文件夹"

    extension = os.path.splitext(path)[1].lower()
    if extension in {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}:
        return "视频"
    if extension in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}:
        return "音频"
    return "文件"


def get_downloads_directory():
    return os.path.expanduser("~/Downloads")


def media_extensions_for_kind(media_kind):
    if media_kind == "video":
        return {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
    if media_kind == "audio":
        return {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
    return set()


def infer_media_kind_from_text(text):
    normalized = (text or "").lower()
    if any(token in normalized for token in ["视频", "影片", "movie", "video"]):
        return "video"
    if any(token in normalized for token in ["音频", "音乐", "歌曲", "录音", "audio", "music", "song"]):
        return "audio"
    if any(token in normalized for token in ["文件夹", "folder", "directory"]):
        return "folder"
    return "file"


def extract_search_terms(text):
    normalized = (text or "").strip().lower()
    stop_tokens = [
        "打开", "本地", "最近", "下载", "的", "一个", "一下", "帮我", "请", "视频", "音频", "文件",
        "文件夹", "路径", "latest", "recent", "download", "downloads", "video", "audio", "file", "folder",
    ]
    tokens = re.split(r"[\s,，;；/]+", normalized)
    return [token for token in tokens if token and token not in stop_tokens]


def find_recent_download(media_kind="file", query_text=""):
    downloads_dir = Path(get_downloads_directory())
    if not downloads_dir.exists():
        return None

    extensions = media_extensions_for_kind(media_kind)
    candidates = []
    for entry in downloads_dir.iterdir():
        if entry.name.startswith("."):
            continue
        if media_kind == "folder":
            if not entry.is_dir():
                continue
        elif media_kind in {"video", "audio"}:
            if not entry.is_file() or entry.suffix.lower() not in extensions:
                continue
        else:
            if not entry.exists():
                continue

        try:
            modified_time = entry.stat().st_mtime
        except OSError:
            continue
        candidates.append((modified_time, entry))

    if not candidates:
        return None

    search_terms = extract_search_terms(query_text)
    candidates.sort(key=lambda item: item[0], reverse=True)

    if search_terms:
        filtered = []
        for modified_time, entry in candidates:
            name = entry.name.lower()
            if all(term in name for term in search_terms):
                filtered.append((modified_time, entry))
        if filtered:
            candidates = filtered

    return str(candidates[0][1])


def choose_local_path(selection_type="file"):
    if sys.platform == "darwin":
        if selection_type == "folder":
            script = 'POSIX path of (choose folder with prompt "请选择要打开的文件夹")'
        else:
            script = 'POSIX path of (choose file with prompt "请选择要打开的文件")'
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                check=True,
            )
            selected = result.stdout.strip()
            return normalize_local_path(selected)
        except Exception:
            return None

    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.update()
        if selection_type == "folder":
            selected = filedialog.askdirectory(title="请选择要打开的文件夹")
        else:
            selected = filedialog.askopenfilename(title="请选择要打开的文件")
        root.destroy()
        return normalize_local_path(selected)
    except Exception:
        return None
    
def extract_urls_to_open(input_string):
    # Define a regular expression pattern to find URLs within <open-url> tags
    pattern = r"<open-url>(https?://[^<]+)</open-url>"
    
    # Use re.findall to extract all occurrences of the pattern
    urls = re.findall(pattern, input_string)
    
    return urls


# LM ACTIVATED SKILL: SKILL TITLE: Open Local Path DESCRIPTION: Opens a local file, audio file, video file, or folder on the current computer using the default system app. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <open-local-path> /absolute/path/to/file </open-local-path> Example: <open-local-path> /Users/name/Movies/lesson.mp4 </open-local-path>
def open_local_path(transcription_response, conversation, scratch_pad, path_to_open):
    normalized_path = normalize_local_path(path_to_open)
    if not normalized_path:
        skill_response = (
            "我没有找到要打开的本地路径。请提供存在的本地文件、音频、视频或文件夹路径。"
        )
        return skill_response, conversation, scratch_pad

    launch_with_default_app(normalized_path)
    target_type = describe_local_target(normalized_path)
    skill_response = f"我已经帮你打开这个本地{target_type}：{normalized_path}"
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["打开本地视频"], ["打开本地音频"], ["打开路径"], ["打开本地文件"], ["打开文件夹"]]
def open_local_path_from_clipboard(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    if clipboard is None:
        skill_response = "当前环境不支持读取剪贴板。请直接把本地路径发给我。"
        return skill_response, conversation, scratch_pad

    clipboard_content = clipboard.paste()
    normalized_path = normalize_local_path(clipboard_content)
    if not normalized_path:
        skill_response = (
            "我还没有在剪贴板里找到可打开的本地路径。你可以先复制文件路径，再让我打开本地视频、音频或文件夹。"
        )
        return skill_response, conversation, scratch_pad

    launch_with_default_app(normalized_path)
    target_type = describe_local_target(normalized_path)
    skill_response = f"我已经从剪贴板路径打开这个本地{target_type}：{normalized_path}"
    return skill_response, conversation, scratch_pad


# LM ACTIVATED SKILL: SKILL TITLE: Open Recent Download DESCRIPTION: Finds and opens the most recent downloaded local video, audio file, file, or folder from the Downloads directory. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <open-recent-download> video </open-recent-download> Example: <open-recent-download> 最近下载的视频 </open-recent-download>
def open_recent_download(transcription_response, conversation, scratch_pad, request_text):
    request = (request_text or transcription_response or "").strip()
    media_kind = infer_media_kind_from_text(request)
    normalized_kind = "file" if media_kind not in {"video", "audio", "folder"} else media_kind
    target_path = find_recent_download(normalized_kind, request)
    if not target_path:
        skill_response = "我没有在下载目录里找到符合条件的最近文件。你可以换一个说法，或者直接让我打开本地路径。"
        return skill_response, conversation, scratch_pad

    launch_with_default_app(target_path)
    target_type = describe_local_target(target_path)
    skill_response = f"我已经帮你打开最近下载的这个{target_type}：{target_path}"
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["最近下载的视频"], ["最近下载的音频"], ["最近下载的文件"], ["最近下载的文件夹"]]
def open_recent_download_keyword_skill(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    return open_recent_download(transcription_response, conversation, scratch_pad, transcription_response)


# LM ACTIVATED SKILL: SKILL TITLE: Choose Local File DESCRIPTION: Opens a native file picker on the local computer and then opens the selected file or folder using the default system app. USAGE INSTRUCTIONS: To use this skill, call it with the following tags: <choose-local-file> file </choose-local-file> Example: <choose-local-file> folder </choose-local-file>
def choose_and_open_local_path(transcription_response, conversation, scratch_pad, request_text):
    request = (request_text or transcription_response or "").strip()
    selection_type = infer_media_kind_from_text(request)
    selection_type = "folder" if selection_type == "folder" else "file"
    selected_path = choose_local_path(selection_type)
    if not selected_path:
        skill_response = "我没有拿到要打开的本地路径。可能是你取消了选择，或者当前环境不支持文件选择器。"
        return skill_response, conversation, scratch_pad

    launch_with_default_app(selected_path)
    target_type = describe_local_target(selected_path)
    skill_response = f"我已经通过文件选择器打开这个本地{target_type}：{selected_path}"
    return skill_response, conversation, scratch_pad


# KEYWORD ACTIVATED SKILL: [["选择文件"], ["选择视频"], ["选择音频"], ["选择文件夹"], ["打开文件选择器"]]
def choose_and_open_local_path_keyword_skill(transcription_response, conversation, scratch_pad, LMGeneratedParameters=""):
    return choose_and_open_local_path(transcription_response, conversation, scratch_pad, transcription_response)

# LM ACTIVATED SKILL: SKILL TITLE: Review scientific literature. DESCRIPTION: Sends a question to the Ask Open Research Knowledge Graph Service that retrieves relevant abstracts from 76+ million scientific papers. USAGE INSTRUCTIONS: Whenever the user asks you to review the scientific literature for a certain question, you reply with the question inside the tags <open-askorkg> ... </open-askorkg>, like e.g. if the user asks you to review the scientific literature for the question 'Is it possible to cure aging?', you output only: <open-askorkg>Is it possible to cure aging?</open-askorkg> and nothing more.
def send_question_to_askorkg(transcription_response, conversation, scratch_pad, question_for_askorkg):

    
    open_site(f"https://ask.orkg.org/search?query={question_for_askorkg}")
    skill_response = random.choice([
                    "Sure! I will use the Ask Open Knowledge Graph service to analyze the question: {0}",
                    "Got it! Let's see what Ask Open Knowledge Graph has on: {0}",
                    "I'm on it! Checking Ask Open Knowledge Graph for information about: {0}",
                    "Excellent question! I'll consult Ask Open Knowledge Graph about: {0}",
                    "One moment! I'll look that up on Ask Open Knowledge Graph for you about: {0}"
                ]).format(question_for_askorkg)
    print ("SUCCESS")
    return  skill_response, conversation, scratch_pad
    
    
# LM ACTIVATED SKILL: SKILL TITLE: Search English Wikipedia. DESCRIPTION: This skill enables the BUD-E voice assistant to search and retrieve content from English Wikipedia based on user-provided keywords. USAGE INSTRUCTIONS: To search for content on Wikipedia, use the command with the tags <open-wikipedia> ... </open-wikipedia>. For example, if the user wants to find information on 'Quantum Computing', you should respond with: <open-wikipedia>Quantum Computing</open-wikipedia>.
def search_en_wikipedia(transcription_response, conversation, scratch_pad, wikipedia_search_keywords):
    open_site(f"https://en.wikipedia.org/w/index.php?search={wikipedia_search_keywords}")
    
    skill_response = random.choice([
                    "Alright, I'm searching Wikipedia for: {0}",
                    "Okay, let's check Wikipedia for details on: {0}",
                    "Looking up Wikipedia to find information on: {0}",
                    "Searching Wikipedia for: {0}",
                    "I'm on it, finding information on Wikipedia about: {0}"
                ]).format(wikipedia_search_keywords)
    print("SUCCESS")
    return skill_response, conversation, scratch_pad
    
    
    
import wikipediaapi

# Wikipedia API initialization
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='en_wiki_api/1.0 (me@example.com)'  # Example User-Agent
)

def get_wikipedia_content(topic):
    """
    This function retrieves the content of a Wikipedia article on a given topic.
    """
    page = wiki_wiki.page(topic)
    if page.exists():
        return page.text, page.fullurl
    else:
        return "No article found.", None


# LM ACTIVATED SKILL: SKILL TITLE: Search Google in Browser. DESCRIPTION: Uses a custom function to open a browser to Google's search page for any specified topic. USAGE INSTRUCTIONS: To activate this skill, use the command within the tags <open-google> ... </open-google>. For example, if the user asks 'Search Google for quantum mechanics', you should output: <open-google>quantum mechanics</open-google>.
def search_google(transcription_response, conversation, scratch_pad, search_query):
    # Using a simulated function to construct and open the Google search URL
    open_site(f"https://www.google.com/search?q={search_query}")

    skill_response = f"I'm searching Google for: {search_query}"
    updated_conversation = conversation
    updated_scratch_pad = scratch_pad

    print("Google search initiated!")
    return skill_response, updated_conversation, updated_scratch_pad


# WORK IN PROGRESS
# LM ####DEACTIVATED### ACTIVATED SKILL: SKILL TITLE: Deep Search and Summarize Wikipedia. DESCRIPTION: This skill performs a deep search in English Wikipedia on a specified topic and summarizes all the results found. USAGE INSTRUCTIONS: To perform a deep search and summarize, use the command with the tags <deep-wikipedia> ... </deep-wikipedia>. For example, if the user wants to find information on 'Quantum Computing', you should respond with: <deep-wikipedia>Quantum Computing</deep-wikipedia>.
def deep_search_and_summarize_wikipedia(transcription_response, conversation, scratch_pad, topic):
    """
    This skill searches English Wikipedia for a given topic and summarizes the results.
    """
    print("START")
    # Fetch the content from Wikipedia
    raw_text, source_url = get_wikipedia_content(topic)
    print("#############")
    print(raw_text, source_url)
    print(llm.llm_call_without_memory("3+6=?"))
    
    #if raw_text == "No article found.":
    #    skill_response = f"No article found for the topic: {topic}"
    #    return skill_response, conversation, scratch_pad
    
    # Instruction for the LLM to summarize the text
    instruction = f"Summarize the following text to 500 words with respect to what is important and provide at the end source URLs with explanations : {raw_text[:5000]}"
    summary = llm.llm_call_without_memory(instruction)
    print("summary", summary)
    # Form the final response
    skill_response = f"Here is a summary of the Wikipedia article on '{topic}':\n\n{summary}\n\nSource: {source_url}"
    print(skill_response)
    return skill_response, conversation, scratch_pad
