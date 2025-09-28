import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in the .env file.")

# Configure the generative AI client
genai.configure(api_key=GOOGLE_API_KEY)

print("--- Available Generative Models ---")
print("Listing all models that support the 'generateContent' method:")

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"- {model.name}")
except Exception as e:
    print(f"\nAn error occurred while trying to list the models: {e}")
    print("Please ensure your API key is correct and has the necessary permissions.")

print("\n--- End of List ---")
print("Please copy one of the model names from the list above (e.g., 'models/gemini-pro') and we will use it in the code.")