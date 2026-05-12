import google.generativeai as genai
import os
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Warning: No Google/Gemini API key found in environment variables.")
else:
    genai.configure(api_key=api_key)
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
