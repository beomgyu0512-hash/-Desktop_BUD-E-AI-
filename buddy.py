# Import necessary modules

# subprocess: Allows running system commands from within Python
import subprocess

# os: Provides functions for interacting with the operating system (e.g., environment variables, file operations)
import os

# signal: Allows handling of system signals (not used in this script, but imported for potential future use)
import signal

# asyncio: Supports asynchronous programming, enabling concurrent execution of code
import asyncio

# load_dotenv: A function from the dotenv library to load environment variables from a .env file
from dotenv import load_dotenv

# shutil: Offers high-level file operations (e.g., copying, moving files)
import shutil

# requests: A library for making HTTP requests to web services or APIs
import requests

# time: Provides various time-related functions (e.g., delays, timing operations)
import time

# threading: Enables creation and management of threads for concurrent execution
import threading

# clipboard: Allows interaction with the system clipboard (copy/paste operations)
import clipboard

# json: Provides functions for working with JSON data (encoding/decoding)
import json

# base64: Offers functions for encoding and decoding data using base64
import base64

# io: Provides tools for working with various types of I/O (input/output)
import io

# PIL (Python Imaging Library): A library for opening, manipulating, and saving images
from PIL import Image
from PIL import ImageGrab

# Event: A threading primitive that allows communication between threads
from threading import Event

# re: Provides support for regular expressions in Python
import re

# random: Offers functions for generating random numbers, making selections, etc.
import random

# sounddevice: A library for playing and recording audio
import sounddevice as sd

# soundfile: A library for reading and writing sound files
import soundfile as sf

# importlib.util: Provides utilities for working with import statements
import importlib.util

# ModuleType: A type hint for module objects
from types import ModuleType

# Import the sys module for accessing Python interpreter variables
import sys
import inspect

# Import configurations from a local module
from api_configs.configs import get_llm_config, get_tts_config, get_asr_config

# Import custom functions from local modules
from stream_tts import stream_audio_from_text
from stream_asr import get_transcript
from wake_words import get_wake_words, WakeWordEngine

# Import LangChain components for natural language processing tasks
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
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

# Get configuration for text-to-speech (TTS)
tts_config = get_tts_config()

# Set the default TTS API to use
tts_api = tts_config["default_api"]

# Set the TTS model to use
tts_model = tts_config["apis"][tts_api]["model"]

# Set the API key for the TTS service
tts_api_key = tts_config["apis"][tts_api]["api_key"]


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
            if re.match(r'^\s*def\s+\w+\s*\(', lines[i + 1]):
                function_name = re.findall(r'def\s+(\w+)\s*\(', lines[i + 1])[0]
                skill_function_names.add(function_name)

    return skill_function_names


# Define a function to import all functions from a specified directory
def import_all_functions_from_directory(directory: str) -> dict:
    # Initialize an empty dictionary to store activated skills
    activated_skills = {}

    # Iterate through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file is a Python script
        if filename.endswith('.py'):
            # Remove the .py extension to get the module name
            module_name = filename[:-3]
            # Construct the full file path
            filepath = os.path.join(directory, filename)

            # Create a module specification from the file
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            # Create a module based on the specification
            module = importlib.util.module_from_spec(spec)
            # Execute the module
            spec.loader.exec_module(module)
            skill_function_names = extract_skill_function_names_from_file(filepath)

            # Iterate over all attributes in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                is_module_function = inspect.isfunction(attr) and attr.__module__ == module.__name__
                if is_module_function and attr_name in skill_function_names:
                    # Add the function to the activated_skills dictionary
                    activated_skills[attr_name] = attr
                    # Make the function globally accessible
                    globals()[attr_name] = attr
                    
                    # Print information about the imported function
                    if debug_enabled():
                        print(f"Imported function: {attr_name} from module {module_name}")

    # Return the dictionary of activated skills
    return activated_skills

# Define a function to extract activated skills from a directory based on a keyword
def extract_activated_skills_from_directory(directory: str, keyword: str = "KEYWORD ACTIVATED SKILL:") -> dict:
    # Initialize an empty dictionary to store activated skills
    activated_skills = {}

    # Iterate through all files in the specified directory
    for filename in os.listdir(directory):
        # Check if the file is a Python script
        if filename.endswith('.py'):
            # Construct the full file path
            filepath = os.path.join(directory, filename)

            # Read the contents of the file
            with open(filepath, 'r') as file:
                lines = file.readlines()

            # Search for functions with the specified keyword comment
            for i in range(len(lines) - 1):
                # Check if the current line contains the keyword (case-insensitive)
                if keyword.lower() in lines[i].lower():
                    # Check if the next line is a function definition
                    if re.match(r'^\s*def\s+\w+\s*\(', lines[i + 1]):
                        # Extract the function name using regex
                        function_name = re.findall(r'def\s+(\w+)\s*\(', lines[i + 1])[0]
                        # Extract the comment text after the keyword
                        comment = lines[i].strip().split(keyword)[-1].strip()

                        # Store the function name and comment in the dictionary
                        activated_skills[function_name] = comment

    # Return the dictionary of activated skills
    return activated_skills
    



# Define a function to execute functions in a specific order based on their names
def execute_functions_in_order(activated_skills: dict):
    # Sort the function names both numerically and alphabetically
    # This uses a complex sorting key that splits the name into numeric and non-numeric parts
    sorted_function_names = sorted(activated_skills.keys(), key=lambda x: [int(y) if y.isdigit() else y for y in re.split('([0-9]+)', x)])

    # Iterate through the sorted function names
    for function_name in sorted_function_names:
        print(f"Executing {function_name}...")
        # Execute each function stored in the activated_skills dictionary
        activated_skills[function_name]()

# Define the directory where skill functions are stored
skills_directory = 'skills'

# Import all functions from the skills directory
skills_dict = import_all_functions_from_directory(skills_directory)

# Extract skills that are activated by a specific keyword
keyword_activated_skills_dict = extract_activated_skills_from_directory(skills_directory, "KEYWORD ACTIVATED SKILL:")    
if debug_enabled():
    print(keyword_activated_skills_dict)

# Extract skills that are activated by a language model
lm_activated_skills_dict = extract_activated_skills_from_directory(skills_directory, "LM ACTIVATED SKILL:")    
if debug_enabled():
    print(lm_activated_skills_dict)


def wake_words_disabled() -> bool:
    value = os.getenv("BUD_E_DISABLE_WAKE_WORD", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def text_input_mode_enabled() -> bool:
    value = os.getenv("BUD_E_TEXT_MODE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


# Define a function for conditional execution of skills
def conditional_execution(function_name, transcription_response, conversation, scratch_pad, conditions_list=[], LMGeneratedParameters=""):
    """
    Executes a function based on a list of conditions, passing additional parameters
    and handling return values.

    Args:
    function_name (str): The name of the function to execute.
    transcription_response (str): The current transcription response.
    conversation (object): Current state or context of the conversation.
    scratch_pad (dict): A dictionary to store data across function calls.
    conditions_list (list of list of str): Conditions that trigger the function execution.
    LMGeneratedParameters (str): Additional parameters generated by the language model.

    Returns:
    tuple: A tuple containing updated conversation, scratch_pad, and skill_response from the executed function.
    """
    # Try to get the function from the global namespace
    function_to_run = globals().get(function_name)
    
    # If not found in globals, try to get it from the current module
    if function_to_run is None:
        current_module = sys.modules[__name__]
        function_to_run = getattr(current_module, function_name, None)
    
    # Raise an error if the function is not found
    if function_to_run is None:
        raise ValueError(f"The specified function '{function_name}' is not defined.")
    
    # Raise an error if the function is not callable
    if not callable(function_to_run):
        raise ValueError(f"The function '{function_name}' is not callable.")
    
    # Check conditions and execute the function if conditions are met
    if len(conditions_list) > 0:
        for condition in conditions_list:
            # Check if all substrings in the condition are present in the transcription_response
            if all(substring.lower() in transcription_response.lower() for substring in condition):
                # Execute the function if the condition is met
                skill_response, updated_conversation, updated_scratch_pad = function_to_run(transcription_response, conversation, scratch_pad, LMGeneratedParameters)
                return skill_response, updated_conversation, updated_scratch_pad
    else:
        # If no conditions are specified, execute the function anyway
        skill_response, updated_conversation, updated_scratch_pad = function_to_run(transcription_response, conversation, scratch_pad, LMGeneratedParameters)
        return skill_response, updated_conversation, updated_scratch_pad    
    
    # If no conditions are met, return unchanged objects and None for skill_response
    return "", conversation, scratch_pad            

# Define a function to parse a string representation of a list of lists
def parse_list_of_lists(input_str):
    """
    Parses a string representing a list of lists, where each sublist contains strings.
    The function handles irregular spacing and variations in quote usage.
    
    Args:
    input_str (str): A string representation of a list of lists.
    
    Returns:
    list of list of str: The parsed list of lists.
    """
    # Normalize the string by replacing single quotes with double quotes
    normalized_str = re.sub(r"\'", "\"", input_str)

    # Extract the sublists using a regular expression that captures contents inside brackets
    sublist_matches = re.findall(r'\[(.*?)\]', normalized_str)
    
    # Process each match to extract individual string elements
    result = []
    for sublist in sublist_matches:
        # Extract string elements inside the quotes
        strings = re.findall(r'\"(.*?)\"', sublist)
        result.append(strings)

    return result


# Define TextToSpeech class
class TextToSpeech:
    def __init__(self):
        self.player_process = None
        self.should_stop = False
        self.listener = None

    @staticmethod
    def is_installed(lib_name: str) -> bool:
        """Check if a command exists in the system's path"""
        return shutil.which(lib_name) is not None

    def stop(self):
        # Stop the TTS playback and keyboard listener
        self.should_stop = True
        if self.player_process:
            self.player_process.terminate()
            self.player_process = None
        if self.listener:
            self.listener.stop()

    def on_activate(self):
        # Callback for hotkey activation
        print("Hotkey activated - stopping TTS.")
        self.stop()

    def speak(self, text, stop_event: Event):
        # Check if ffplay is installed (required for audio streaming)
        if not self.is_installed("ffplay"):
            raise ValueError("ffplay not found, necessary to stream audio.")

        from pynput import keyboard

        # Setup hotkey listener for Ctrl+Shift to stop TTS
        with keyboard.GlobalHotKeys({'<ctrl>+<shift>': self.on_activate}) as self.listener:
            # Prepare ffplay command for audio playback
            player_command = ["ffplay", "-autoexit", "-", "-nodisp"]
            self.player_process = subprocess.Popen(
                player_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            try:
                # Generate audio stream from text
                audio_stream_generator = stream_audio_from_text(text, tts_api_key, tts_model)
                for chunk in audio_stream_generator:
                    # Check for stop conditions
                    if stop_event.is_set() or self.should_stop:
                        break
                    if chunk:
                        try:
                            # Write audio chunk to ffplay process
                            self.player_process.stdin.write(chunk)
                            self.player_process.stdin.flush()
                        except BrokenPipeError:
                            print("TTS playback stopped.")
                            break
            finally:
                # Clean up resources
                if self.player_process and self.player_process.stdin:
                    self.player_process.stdin.close()
                if self.player_process:
                    self.player_process.wait()
                self.player_process = None
                
                

def save_scratch_pad_to_file(scratch_pad, filename="ScratchPad.json"):
    """
    Saves the dictionary 'scratch_pad' to a file specified by 'filename'.
    """
    with open(filename, "w") as file:
        json.dump(scratch_pad, file, indent=4)

def load_scratch_pad_from_file(filename="ScratchPad.json"):
    """
    Loads a dictionary from a file specified by 'filename'.
    """
    with open(filename, "r") as file:
        return json.load(file)

def extract_opening_and_closing_tags(input_string):
    """
    Extracts the first opening and closing tags from the input string.

    Args:
    input_string (str): The string to search for tags.

    Returns:
    tuple: A tuple containing the first opening tag and the first closing tag.
    """
    # Regex to find tags
    tags = re.findall(r'<[^>]+>', input_string)
    
    if not tags:
        return None, None  # Return None if no tags are found

    # Find the first opening tag
    opening_tag = next((tag for tag in tags if not tag.startswith('</')), None)
    # Find the first closing tag after the first opening tag
    closing_tag = next((tag for tag in tags if tag.startswith('</') and tag[2:-1] in opening_tag), None)

    return opening_tag, closing_tag

class ConversationManager:
    def __init__(self):
        self.transcription_response = ""
        self.llm = LanguageModelProcessor(llm_config)
        self.tts = TextToSpeech()
        self.stop_event = asyncio.Event()
        self.conversation_active = False
        self.ScratchPad = {}  # Scratch pad for skill functions to store persistent variables

        # Try to load existing scratch pad, if it fails, use an empty dictionary
        try:
            self.ScratchPad = load_scratch_pad_from_file()
        except:
            pass

    async def start_conversation(self):
        self.conversation_active = True
        await self.main()

    async def speak_response(self, response):
        if text_input_mode_enabled():
            return
        tts_task = asyncio.to_thread(self.tts.speak, response, self.stop_event)
        try:
            await tts_task
        except Exception as e:
            print(f"TTS error: {e}")

    async def main(self):
        def handle_full_sentence(full_sentence):
            self.transcription_response = full_sentence

        while self.conversation_active:
            self.stop_event.clear()
            self.tts = TextToSpeech()  # Create a new TTS instance for each response

            if text_input_mode_enabled():
                self.transcription_response = (await asyncio.to_thread(input, "You: ")).strip()
            else:
                print("Listening for your command...")
                await get_transcript(handle_full_sentence)
            
            if "goodbye" in self.transcription_response.lower():
                self.conversation_active = False
                break

            if not self.transcription_response.strip():
                continue

            all_skill_responses = ""
            matched_keyword_skill = False
            # Process keyword-activated skills
            for keyword_activated_function in keyword_activated_skills_dict:
                skill_response = ""
                if debug_enabled():
                    print(keyword_activated_function)
                condition_list = parse_list_of_lists(keyword_activated_skills_dict[keyword_activated_function])
                try:
                    skill_response, updated_conversation, updated_scratch_pad = conditional_execution(
                        keyword_activated_function, self.transcription_response, 
                        self.llm.conversation, self.ScratchPad, condition_list
                    )
                    self.llm.conversation = updated_conversation
                    self.ScratchPad = updated_scratch_pad
                    if skill_response.strip():
                        matched_keyword_skill = True
                        all_skill_responses += "\n" + skill_response
                except:
                    pass
     
            if debug_enabled():
                print(self.transcription_response + all_skill_responses)

            if matched_keyword_skill:
                final_skill_response = all_skill_responses.strip()
                print(f"AI: {final_skill_response}")
                await self.speak_response(final_skill_response)
                self.transcription_response = ""
                continue
            
            # Start from the base prompt each turn so LM skill descriptions do not duplicate endlessly.
            system_prompt = self.llm.base_system_prompt
            for lm_activated_skill in lm_activated_skills_dict:
                system_prompt += "\n" + lm_activated_skills_dict[lm_activated_skill]
            self.llm.update_system_prompt(system_prompt)

            #test  = self.llm.llm_call_without_memory("1+1=?")
            #print(test)
            
            # Process the transcription and generate a response
            llm_response = self.llm.process(self.transcription_response + all_skill_responses)
            if debug_enabled():
                print("llm_response", str(llm_response))

            # Process LM-activated skills
            perform_lm_skill = False
            for lm_activated_function in lm_activated_skills_dict:
                skill_response = ""
                if debug_enabled():
                    print(lm_activated_function)
                opening_tag, closing_tag = extract_opening_and_closing_tags(lm_activated_skills_dict[lm_activated_function])
                if debug_enabled():
                    print(opening_tag, closing_tag)
                
                if (opening_tag and closing_tag and 
                    opening_tag.lower() in llm_response.lower() and 
                    closing_tag.lower() in llm_response.lower()):  
                    perform_lm_skill = True
                    opening_tag_name = re.escape(opening_tag[1:-1])
                    closing_tag_name = re.escape(closing_tag[2:-1])

                    pattern = rf"<{opening_tag_name}>(.*?)</{closing_tag_name}>"
                    LMGeneratedParameters = re.findall(pattern, llm_response)
                    LMGeneratedParameters = LMGeneratedParameters[0]
                    if debug_enabled():
                        print("LMGeneratedParameters", LMGeneratedParameters)
               
                    try:
                        skill_response, updated_conversation, updated_scratch_pad = conditional_execution(
                            lm_activated_function, self.transcription_response, 
                            self.llm.conversation, self.ScratchPad, [], LMGeneratedParameters
                        )
                        self.llm.conversation = updated_conversation
                        self.ScratchPad = updated_scratch_pad
                        break  # Allow only 1 LM activated function to get executed
                    except:
                        pass

            if perform_lm_skill:
                print(f"AI: {skill_response}")
                await self.speak_response(skill_response)
            else:
                print(f"AI: {llm_response}")
                await self.speak_response(llm_response)           		             
            self.transcription_response = ""

        print("Conversation ended. Listening for wake words again...")

async def main():
    conversation_manager = ConversationManager()

    if wake_words_disabled():
        print("Wake word disabled. Starting conversation immediately...")
        await conversation_manager.start_conversation()
        return

    wake_words = get_wake_words()
    wake_word_engine = WakeWordEngine(wake_words, conversation_manager.start_conversation)
    wake_word_engine.initialize()
    print("Listening for wake words...")
    await wake_word_engine.detect()




if __name__ == "__main__":
    asyncio.run(main())
