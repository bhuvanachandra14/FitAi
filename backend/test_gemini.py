import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-flash-latest')
    print("Testing connection to gemini-flash-latest...")
    response = model.generate_content("Hello")
    print("Success! Response:", response.text)
except Exception as e:
    print(e)
