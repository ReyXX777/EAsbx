# list_models.py
import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY environment variable is not set.")
else:
    client = genai.Client(api_key=api_key)
    print("Fetching available models for your API key...\n")
    try:
        models = client.models.list()
        for m in models:
            # Print the model name (e.g., 'models/gemini-2.0-flash')
            print(f"Model Name: {m.name}")
    except Exception as e:
        print(f"Error fetching models: {e}")