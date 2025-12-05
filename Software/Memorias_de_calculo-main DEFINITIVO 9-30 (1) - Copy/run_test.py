import os
from scripts.table_spectrum import generar_spectrums_from_excel

# --- Configuración ---
EXCEL_FILE = 'c:\\Users\\ereyes25052\\Desktop\\Programación\\Memorias_de_calculo-main 9-10\\XtraReport.xlsx'

# --- Ejecución ---
if __name__ == "__main__":
    print(f"--- Iniciando prueba con el archivo: {EXCEL_FILE} ---")
    # Llama a la función principal, sin especificar la hoja para que itere sobre todas
    resultados = generar_spectrums_from_excel(excel_file=EXCEL_FILE, lang="es")
    
    if resultados:
        print(f"\n\n--- Prueba finalizada con éxito ---")
        print(f"Se generaron {len(resultados)} imágenes de espectro:")
        for img_path, eje in resultados:
            print(f"  - Ruta: {img_path}, Eje: {eje if eje else 'No especificado'}")
    else:
        print("\n\n--- Prueba finalizada, no se generaron imágenes ---")
        print("Revisa los mensajes de información y error de cada hoja.")