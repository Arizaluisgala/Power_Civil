import pandas as pd
import os
from scripts.table_spectrum import load_spectrum_data, get_spectrum_axes

# --- Configuración ---
EXCEL_FILE = 'c:\\Users\\ereyes25052\\Desktop\\Programación\\Memorias_de_calculo-main 9-10\\test\\XtraReport.xlsx'
SHEET_NAME = "Sheet" # Asumimos la hoja por defecto, cámbiala si es necesario

# --- Función de prueba ---
def test_excel_loading(excel_path, sheet_name):
    if not os.path.exists(excel_path):
        print(f"❌ Error: El archivo no existe en la ruta: {excel_path}")
        return

    print(f"--- Probando la carga de datos desde '{excel_path}' (Hoja: '{sheet_name}') ---")
    
    try:
        # 1. Probar la carga de datos del espectro
        print("\n--- 1. Probando load_spectrum_data() ---")
        df_spectrum = load_spectrum_data(excel_path, sheet_name)
        print("✅ load_spectrum_data() ejecutado con éxito.")
        print("Primeras 5 filas de datos extraídos:")
        print(df_spectrum.head())
        print("\nÚltimas 5 filas de datos extraídos:")
        print(df_spectrum.tail())
        print(f"\nTipos de datos de las columnas: \n{df_spectrum.dtypes}")
        print(f"\nCasos de carga (LCTitle) encontrados: {df_spectrum['LCTitle'].unique()}")

    except Exception as e:
        print(f"❌ Error en load_spectrum_data(): {e}")

    try:
        # 2. Probar la obtención de los ejes
        print("\n--- 2. Probando get_spectrum_axes() ---")
        axes_dict = get_spectrum_axes(excel_path, sheet_name)
        print("✅ get_spectrum_axes() ejecutado con éxito.")
        if axes_dict:
            print("Diccionario de Ejes (Load Case -> Eje) encontrado:")
            print(axes_dict)
        else:
            print("⚠️ No se encontró el diccionario de ejes. La tabla 'Spectrum Parameters' podría faltar o tener un formato inesperado.")
            
    except Exception as e:
        print(f"❌ Error en get_spectrum_axes(): {e}")

# --- Ejecución ---
if __name__ == "__main__":
    # Primero, intentemos leer la hoja por defecto "Sheet"
    test_excel_loading(EXCEL_FILE, "Sheet")
    
    # Si eso falla, a menudo los reportes de STAAD usan nombres como "Response Spectrum"
    print("\n--- Intentando con un nombre de hoja alternativo: 'Response Spectrum' ---")
    test_excel_loading(EXCEL_FILE, "Response Spectrum")