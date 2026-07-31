from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import pdfplumber
from google import genai
from datasets import load_dataset
from google.genai import types
import json

DATA_DIR = Path(__file__).resolve().parent / "data"


def main():
    load_dotenv()
    client = genai.Client()

    ds = load_dataset("csv", data_files=str(DATA_DIR / "data.csv"))
    coding_fields_df = pd.read_csv(DATA_DIR / "categories.csv")
    categories_prompt = "Use the following Coding Fields and descriptions:\n\n"
    for index, row in coding_fields_df.iterrows():
        categories_prompt += f"- {row['Coding Fields']}: {row.get('Description', '')}\n"

    main_guideline = client.files.upload(file=DATA_DIR / "guideline.pdf")
    aux_guideline = client.files.upload(file=DATA_DIR / "inst-9-to-17.pdf")

    with open(DATA_DIR / "json_batches" / "all_examples.json", 'r', encoding='utf-8') as file:
            all_examples = json.load(file)

    few_shot_subset = all_examples[:3]

    few_shot_prompt = """
    Task: Analyze the provided PDF documents. Extract the institutional statements and map them to the defined coding fields. Output the results in JSON format.\n\n
    """

    for i, example in enumerate(few_shot_subset, start=1):
        few_shot_prompt += f"Example {i}:\n"
        few_shot_prompt += f"Input text: \"{example.get('Raw Statement', '')}\"\n"
        few_shot_prompt += "Extraction:\n"
        
        for key, value in example.items():
            if key != "Raw Statement" and str(value).strip() != "":
                few_shot_prompt += f"- {key}: {value}\n"
        
        few_shot_prompt += "\n"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                main_guideline, 
                aux_guideline, 
                few_shot_prompt
            ],
            config=types.GenerateContentConfig(
                system_instruction=categories_prompt,
                temperature=0.0,
                response_mime_type="application/json"
            )
        )
        output_dir = Path(__file__).resolve().parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "extraction_results.json", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(response.text)


if __name__ == "__main__":
    main()