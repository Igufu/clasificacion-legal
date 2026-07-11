import pandas as pd
import pdfplumber
import json

def load_training_set(csv_path: str) -> str:
    try:
        # agarrar training set del csv
        df = pd.read_csv(csv_path)
        df_filtered = df.fillna("") # TODO: ver si es mejor dejar null o whitespace
        training_set = df_filtered.head(5)
        json_str = training_set.to_json(orient="records", indent=2, force_ascii=False)

        # cargar el prompt
        prompt_segment = f"### Classification Examples (Golden Set)\n\n{json_str}\n"
        return prompt_segment  
    except Exception as e:
        return f"Error processing CSV file: {e}"

# para testear 
if __name__ == "__main__":
    CSV_FILE = "../src/data/data.csv"
    examples_string = load_training_set(CSV_FILE)
    print("=== TRAINING SET JSON OUTPUT ===")
    print(examples_string)