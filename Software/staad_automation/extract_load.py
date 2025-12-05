from openstaad import Load 
from comtypes import client
import os
import sys

# Asegúrate de importar tu función de rangos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', )))
from scripts.extract_tables_of_excel import extract_tables_from_excel_rangos_de_combinaciones_de_carga

def extract_combinations_load(file_path=None):
    try:
        load = Load()
        staad = client.GetActiveObject("StaadPro.OpenSTAAD")
        if not staad:
            print("STAAD.Pro no está abierto o no se pudo conectar.")
            return []
    except Exception as e:
        print("STAAD.Pro no está abierto o no se pudo conectar.")
        return []

    # El archivo Excel debe ser el que el usuario pasa manualmente (por interfaz o argumento)
    if file_path is None:
        import inspect
        caller_locals = inspect.currentframe().f_back.f_locals
        file_path = caller_locals.get('excel_file_path') or caller_locals.get('excel_file_path_cargas')
    if not file_path or not os.path.isfile(file_path):
        # Fallback: variable de entorno o rutas por defecto
        file_path = os.getenv('EXCEL_TEMPLATE')
        if not file_path or not os.path.isfile(file_path):
            file_path = r'C:\Users\Narriet25056\Documents\Pasantia\Memorias_de_calculo\document\docx_inelectra\Limites de deflexion 5.xlsx'
            if not os.path.isfile(file_path):
                print(f"⚠️ No se encontró el archivo de combinaciones de carga en: {file_path}")
                return []
    try:
        rangos_dict = extract_tables_from_excel_rangos_de_combinaciones_de_carga(file_path)
    except Exception as e:
        print(f"Error al leer rangos de combinaciones de carga: {e}")
        return []
    headers = rangos_dict.get("headers", [])
    rango_inicial = rangos_dict.get("rango_inicial", [])
    rango_final = rangos_dict.get("rango_final", [])

    results = []
    for header, start, end in zip(headers, rango_inicial, rango_final):
        if start == "" or end == "":
            continue
        try:
            start = int(float(start))
            end = int(float(end))
        except Exception:
            continue
        for i in range(start, end + 1):
            try:
                load_type = load.GetLoadCaseTitle(i)
                if load_type:
                    results.append((i, load_type, header))
                    print(f"Load Case {i}: {load_type} ({header})")
            except Exception as e:
                continue
    return results

if __name__ == "__main__":
    combinations = extract_combinations_load()
    if combinations:
        print("Casos de carga combinados extraídos correctamente.")
    else:
        print("No se encontraron casos de carga combinados.")
