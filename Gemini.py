__author__ = "Yuval Malkan"

import os
from dotenv import load_dotenv
from google import genai


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text





#multi-prompt chat
def start_chat():
    chat = client.chats.create(model="gemini-2.0-flash")
    return chat

def send_message(chat, message: str) -> str:
    response = chat.send_message(message)
    return response.text



if __name__ == "__main__":
    user = input(" ")
    print(ask_gemini(user))