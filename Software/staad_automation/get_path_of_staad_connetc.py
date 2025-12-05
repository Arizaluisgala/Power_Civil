import os

# Intenta importar Root solo si STAAD está abierto
try:
    from openstaad.root import Root
    root = Root()
except Exception as e:
    root = None

def get_path_of_staad_connect():
    """
    Obtiene la ruta del ejecutable de STAAD Connect.
    Retorna None si STAAD no está abierto.
    """
    print("Intentando obtener Root...")
    try:
        import pythoncom
        pythoncom.CoInitialize()
        from openstaad.root import Root
        root = Root()
    except Exception as e:
        print(f"Error al inicializar Root: {e}")
        return None
    try:
        get_file = root.GetSTAADFile
        staad_file = get_file()
        print(f"Ruta obtenida: {staad_file}")
        if staad_file:
            return staad_file
        else:
            print("No se obtuvo ruta de archivo.")
            return None
    except Exception as e:
        print(f"Error al obtener ruta de STAAD: {e}")
        return None
    
def transforma_el_std_a_txt(path_std):
    """
    Transforma un archivo .std/.STD a .txt sin sobrescribir el original.
    Además, imprime el contenido leído por consola.
    Si el archivo no existe o no puede leerse, retorna None.
    """
    input_file = path_std
    # Cambia la extensión a .txt, sin importar mayúsculas/minúsculas
    if input_file is None or not os.path.isfile(input_file):
        print("Archivo .std no encontrado o ruta inválida.")
        return None

    if input_file.lower().endswith('.std'):
        output_file = input_file[:-4] + '.txt'
    else:
        output_file = input_file + '.txt'

    try:
        with open(input_file, 'r') as file:
            content = file.read()
            print("Contenido del archivo .std:\n")
            print(content)  # Imprime el contenido en consola

        with open(output_file, 'w') as file:
            file.write(content)

        return output_file
    except Exception as e:
        print(f"Error al transformar el archivo: {e}")
        return None


if __name__ == "__main__":
    # Obtiene la ruta del archivo STAAD Connect
    path_staad = get_path_of_staad_connect()
    
    if path_staad:
        print(f"Ruta del archivo STAAD Connect: {path_staad}")
        
    else:
        print("No se pudo obtener la ruta del archivo STAAD Connect.")


