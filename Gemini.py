
from google import genai


client = genai.Client(api_key="YOUR_GEMINI_API_KEY")


response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Summarize this person's social media activity: ..."
)

print(response.text)