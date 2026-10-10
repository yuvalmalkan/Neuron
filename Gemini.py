__author__ = "Yuval Malkan"

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types # Import the types module for configurations

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gemini(prompt: str) -> str:
    # Removed the duplicate file reading - the full complex prompt already comes from OsintLogic

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", # Enforce clean JSON without Markdown wrappers
            max_output_tokens=4096,                # Increase the output token limit to prevent truncation
        )
    )
    return response.text


#multi-prompt chat
def start_chat():
    chat = client.chats.create(model="gemini-3.5-flash-lite")
    return chat

def send_message(chat, message: str) -> str:
    response = chat.send_message(message)
    return response.text


if __name__ == "__main__":
    user = input(" ")
    print(ask_gemini(user))