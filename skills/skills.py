import clipboard
import json
import random
from PIL import Image
from PIL import ImageGrab

from pynput import keyboard
import threading

from pyautogui import screenshot
import io
import requests
import json
import base64
import os
import re
import subprocess
import time 

import sys

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




def open_site(url):
    # Use subprocess.Popen to open the browser
    process = subprocess.Popen(['xdg-open', url])
    
    # Wait for 2 seconds
    time.sleep(1)
    
    # Kill the process
    process.terminate()  # Safely terminate the process
    # If terminate doesn't kill the process, you can use kill():
    # process.kill()
    
def extract_urls_to_open(input_string):
    # Define a regular expression pattern to find URLs within <open-url> tags
    pattern = r"<open-url>(https?://[^<]+)</open-url>"
    
    # Use re.findall to extract all occurrences of the pattern
    urls = re.findall(pattern, input_string)
    
    return urls

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
