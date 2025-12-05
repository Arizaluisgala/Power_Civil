import os
import sys
from docx import Document

# Add project root to sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)

from document.format.secciones.seccion_9 import verificacion_de_desplazamientos_por_viento
from document.format.secciones.seccion_10 import verificacion_por_sismo

if __name__ == "__main__":
    print("--- Iniciando prueba de extracción de tablas ---")

    # Create a new document
    document = Document()

    # Test data
    excel_file = os.path.join(project_root, 'XtraReport.xlsx')
    idioma = "es"

    # Test seccion_10
    print("\n--- Probando seccion_10 (sismo) ---")
    try:
        verificacion_por_sismo(document, idioma, excel_file)
        print("✔️ seccion_10 ejecutada.")
    except Exception as e:
        print(f"❌ Error en seccion_10: {e}")

    # Test seccion_9
    print("\n--- Probando seccion_9 (viento) ---")
    try:
        verificacion_de_desplazamientos_por_viento(document, idioma, excel_file)
        print("✔️ seccion_9 ejecutada.")
    except Exception as e:
        print(f"❌ Error en seccion_9: {e}")

    # Save the document
    output_path = os.path.join(project_root, 'test_table_extraction_output.docx')
    try:
        document.save(output_path)
        print(f"\n✔️ Documento de prueba guardado en: {output_path}")
    except Exception as e:
        print(f"\n❌ Error al guardar el documento: {e}")

    print("\n--- Prueba finalizada ---")
