import os 
import json
import time
from dotenv import load_dotenv
import pandas as pd
import pdfplumber
from google import genai
from google.genai import types

load_dotenv()

def clean_json_response(text_response):
    """Removes Markdown formatting if the model wraps the JSON."""
    text_response = text_response.strip()
    if text_response.startswith("```json"):
        text_response = text_response[7:]
    if text_response.startswith("```"):
        text_response = text_response[3:]
    if text_response.endswith("```"):
        text_response = text_response[:-3]
    return text_response.strip()

def main():
    client = genai.Client()
    
    # Paths from your environment
    document_pdf_path = "./src/data/Document_for_processing.pdf"
    guideline_pdf_path = "./src/data/guideline.pdf"
    aux_guideline_pdf_path = "./src/data/inst-9-to-17.pdf"
    categories_path = "./src/data/categories.csv"
    examples_path = "./src/data/json_batches/all_examples.json"
    
    # 1. Format the categories
    coding_fields_df = pd.read_csv(categories_path)
    categories_prompt = "Use the following Coding Fields and descriptions:\n\n"
    for index, row in coding_fields_df.iterrows():
        categories_prompt += f"- {row['Coding Fields']}: {row.get('Description', '')}\n"

    # 2. Load few-shot examples
    with open(examples_path, 'r', encoding='utf-8') as file:
        all_examples = json.load(file)
    
    few_shot_subset = all_examples[:3] + all_examples[20:21]
    base_prompt = """
    Task: You are classifying a legal document. The first PDF is the document to be processed. 
    The second and third PDFs are the classification guideline and its auxiliary instructions. 
    Extract the institutional statements from the document being processed and map them to the 
    defined coding fields following the guideline. Output the results in a strict JSON list 
    format [{}, {}].\n\n
    """
    
    for i, example in enumerate(few_shot_subset, start=1):
        base_prompt += f"Example {i}:\nInput text: \"{example.get('Raw Statement', '')}\"\nExtraction:\n"
        for key, value in example.items():
            if key != "Raw Statement" and str(value).strip() != "":
                base_prompt += f"- {key}: {value}\n"
        base_prompt += "\n"

    # 3. Determine total pages using pdfplumber on the document being processed
    print(f"Analyzing page count for {document_pdf_path}...")
    with pdfplumber.open(document_pdf_path) as pdf:
        total_pages = len(pdf.pages)

    # 4. Upload PDFs to Gemini File API
    print("Uploading PDFs to Gemini...")
    document = client.files.upload(file=document_pdf_path)
    guideline = client.files.upload(file=guideline_pdf_path)
    aux_guideline = client.files.upload(file=aux_guideline_pdf_path)

    # 5. Batch processing loop
    pages_per_batch = 5
    all_extracted_statements = []

    for start_page in range(1, total_pages + 1, pages_per_batch):
        end_page = min(start_page + pages_per_batch - 1, total_pages)
        print(f"Processing pages {start_page} to {end_page} of {total_pages}...")

        # Inject the page constraints into the prompt
        batch_prompt = base_prompt + f'''
        \nCRITICAL INSTRUCTION: Extract statements ONLY from Page {start_page} to Page {end_page} 
        of the first provided document (Document_for_processing.pdf). 
        Do not extract statements from any other pages, 
        and do not extract statements from the guideline PDFs.
        '''
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=[
                    document,
                    guideline,
                    aux_guideline,
                    batch_prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction=categories_prompt,
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )

            clean_text = clean_json_response(response.text)
            batch_results = json.loads(clean_text)
            
            if isinstance(batch_results, list):
                all_extracted_statements.extend(batch_results)
            else:
                all_extracted_statements.append(batch_results)


            time.sleep(2) 

        except Exception as e:
            print(f"Error processing pages {start_page}-{end_page}: {e}")
            break 

   
    output_filename = "extraction_results.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(all_extracted_statements, f, indent=2, ensure_ascii=False)
    
    print(f"Extraction complete. {len(all_extracted_statements)} statements saved to {output_filename}.")

if __name__ == "__main__":
    main()