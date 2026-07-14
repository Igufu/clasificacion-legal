import os 
from dotenv import load_dotenv
import pandas as pd
import pdfplumber
#import torch
#from transformers import AutoTokenizer, AutoModelForCasualLM, pipeline
from google import genai
from datasets import load_dataset
import json

client = genai.Client() # Detecta API key de manera autómatica :D

ds = load_dataset("csv", data_files="./src/data/data.csv")
coding_fields_df = pd.read_csv("./src/data/categories.csv")
categories_prompt = "Use the following Coding Fields and descriptions:\n\n"
for index, row in coding_fields_df.iterrows():
    categories_prompt += f"- {row['Coding Fields']}: {row.get('Description', '')}\n"

main_guideline = client.files.upload(file="./src/data/guideline.pdf")
aux_guideline = client.files.upload(file="./src/data/inst-9-to-17.pdf")

with open('./src/data/json_batches/lote_001.json', 'r', encoding='utf-8') as file:
        all_examples = json.load(file)

few_shot_subset = all_examples[:3]

prompt = """
a
"""



load_dotenv()

def test_llm_conn():
    '''
    client = genai.Client() # Detecta API key de manera autómatica :D
    print("Initiating API request...")
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Acknowledge this system test with a single word: 'Connected'."
    )
    print(f"API response: {response.text.strip()}")
    '''
if __name__ == "__main__":
    print(categories_prompt)
    #test_llm_conn()