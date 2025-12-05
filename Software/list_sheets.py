import pandas as pd

# --- Configuración ---
EXCEL_FILE = 'c:\\Users\\ereyes25052\\Desktop\\Programación\\Memorias_de_calculo-main 9-10\\XtraReport.xlsx'
SHEET_NAME = "Sheet"

# --- Ejecución ---
if __name__ == "__main__":
    print(f"--- Mostrando el contenido completo de la hoja '{SHEET_NAME}' en el archivo: {EXCEL_FILE} ---")
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=None)
        print(df.to_string())
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
