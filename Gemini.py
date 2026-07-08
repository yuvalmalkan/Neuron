__author__ = "Yuval Malkan"

import os
from dotenv import load_dotenv
from google import genai


load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def ask_gemini(prompt: str) -> str:
    with open("AIPROMPT.txt", "r") as f:
        system_prompt = f.read()

    combined_prompt = f"{system_prompt}\n\nUSER INPUT\n{prompt}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=combined_prompt
    )
    return response.text




#multi-prompt chat
def start_chat():
    chat = client.chats.create(model="gemini-2.5-flash")
    return chat

def send_message(chat, message: str) -> str:
    response = chat.send_message(message)
    return response.text



if __name__ == "__main__":
    user = input(" ")
    print(ask_gemini(user))