import pandas as pd
import json
import os
from pathlib import Path

def create_and_save_json_batches(csv_path: str, output_folder: str, batch_size: int = 35):
    """
    Lee un CSV ignorando la primera fila de agrupadores, lo divide en lotes
    y guarda cada lote como un archivo JSON separado en tu PC.
    """
    try:
        df = pd.read_csv(csv_path, header=1)
        df_filtered = df.fillna("")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Carpeta creada: {output_folder}")

        total_rows = len(df_filtered)
        saved_files = []

        for i in range(0, total_rows, batch_size):
            batch_df = df_filtered.iloc[i : i + batch_size]
            batch_records = batch_df.to_dict(orient="records")

            batch_number = (i // batch_size) + 1
            file_name = f"full_{batch_number:03d}.json"
            file_path = os.path.join(output_folder, file_name)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(batch_records, f, indent=2, ensure_ascii=False)
                
            saved_files.append(file_path)
            
        return saved_files  
        
    except Exception as e:
        print(f"Error procesando el archivo: {e}")
        return []

if __name__ == "__main__":
    DATA_DIR = Path(__file__).resolve().parent / "data"
    CSV_FILE = DATA_DIR / "data.csv"
    OUTPUT_DIR = DATA_DIR / "json_batches"

    archivos_generados = create_and_save_json_batches(CSV_FILE, OUTPUT_DIR, batch_size=500)
    
    print(f"\n¡Éxito! Se generaron {len(archivos_generados)} archivos JSON.")
    for archivo in archivos_generados:
        print(f"Guardado: {archivo}")