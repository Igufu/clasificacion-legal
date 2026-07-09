import os 
from dotenv import load_dotenv
import pandas as pd
import pdfplumber
from google import genai

load_dotenv()

def test_llm_conn():
    client = genai.Client() # Detecta API key de manera autómatica :D
    print("Initiating API request...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Acknowledge this system test with a single word: 'Connected'."
    )
    print(f"API response: {response.text.strip()}")

if __name__ == "__main__":
    test_llm_conn()