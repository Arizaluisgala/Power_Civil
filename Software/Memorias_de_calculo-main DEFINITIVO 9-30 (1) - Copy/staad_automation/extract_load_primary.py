from openstaad import Load
from comtypes import client
import re


def extract_primary_loads():
    try:
        load = Load()
        # Validar si está conectado a STAAD.Pro
        staad = client.GetActiveObject("StaadPro.OpenSTAAD")
        if not staad:
            print("STAAD.Pro no está abierto o no se pudo conectar.")
            return []
    except Exception as e:
        print("STAAD.Pro no está abierto o no se pudo conectar.")
        return []

    try:
        load_primary_case_count = load.GetPrimaryLoadCaseCount()
    except Exception as e:
        print(f"Error al obtener el número de casos de carga primarios: {e}")
        return []

    results = []
    for i in range(1, load_primary_case_count + 1):
        try:
            load_title = load.GetLoadCaseTitle(i)
            match = re.match(
                r"(LOAD TYPE )?(\w+)( TITLE )?(.*)", load_title, re.IGNORECASE
            )
            if match:
                tipo = match.group(2).strip().upper()
                descripcion = match.group(4).strip()
                results.append((i, tipo, descripcion))
            else:
                results.append((i, "", load_title))
        except Exception as e:
            continue
    return results


if __name__ == "__main__":
    resultados = extract_primary_loads()
    print("\n{:<6} {:<10} {}".format("Caso", "Tipo", "Descripción"))
    print("-" * 50)
    for caso, tipo, desc in resultados:
        print("{:<6} {:<10} {}".format(caso, tipo, desc))
    print("Finished extracting primary loads.")
# extract_primary_loads()