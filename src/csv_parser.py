import pandas as pd
import json
import os

def create_and_save_json_batches(csv_path: str, output_folder: str, batch_size: int = 35):
    """
    Lee un CSV ignorando la primera fila de agrupadores, lo divide en lotes
    y guarda cada lote como un archivo JSON separado en tu PC.
    """
    try:
        # 1. header=1 le dice a pandas que la fila 2 (índice 1) tiene los nombres reales de las columnas.
        # Esto elimina todos los "Unnamed".
        df = pd.read_csv(csv_path, header=1)
        
        # 2. Rellenar celdas vacías con strings vacíos
        df_filtered = df.fillna("") 
        
        # 3. Crear la carpeta de destino si no existe
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"Carpeta creada: {output_folder}")
            
        total_rows = len(df_filtered)
        saved_files = []
        
        # 4. Iterar en bloques de tamaño batch_size
        for i in range(0, total_rows, batch_size):
            batch_df = df_filtered.iloc[i : i + batch_size]
            
            # Convertir el lote a una lista de diccionarios (orient="records")
            # Se usa el método to_dict() para luego guardarlo con la librería 'json' estándar
            batch_records = batch_df.to_dict(orient="records")
            
            batch_number = (i // batch_size) + 1
            file_name = f"full_{batch_number:03d}.json" # Nombres como lote_001.json
            file_path = os.path.join(output_folder, file_name)
            
            # 5. Guardar el archivo JSON en el disco
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(batch_records, f, indent=2, ensure_ascii=False)
                
            saved_files.append(file_path)
            
        return saved_files  
        
    except Exception as e:
        print(f"Error procesando el archivo: {e}")
        return []

# Bloque de ejecución
if __name__ == "__main__":
    # Asegúrate de poner la ruta correcta a tu CSV
    CSV_FILE = "../src/data/data.csv"
    
    # Carpeta donde se guardarán todos los archivos JSON (relativa al script)
    OUTPUT_DIR = "../src/data/json_batches" 
    
    # Ejecutar la función (puedes ajustar el tamaño del lote aquí)
    archivos_generados = create_and_save_json_batches(CSV_FILE, OUTPUT_DIR, batch_size=500)
    
    print(f"\n¡Éxito! Se generaron {len(archivos_generados)} archivos JSON.")
    for archivo in archivos_generados:
        print(f"Guardado: {archivo}")