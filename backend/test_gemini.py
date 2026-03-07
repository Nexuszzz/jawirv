"""Test Gemini 3 Flash direct call."""
import os
from langchain_google_genai import ChatGoogleGenerativeAI

api_key = os.environ.get("GOOGLE_API_KEY", "")
if not api_key:
    raise ValueError("GOOGLE_API_KEY harus di-set di environment/.env")

llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    google_api_key=api_key
)

try:
    response = llm.invoke("What is 2+2?")
    print("SUCCESS!")
    print(response.content)
except Exception as e:
    print(f"ERROR: {e}")
