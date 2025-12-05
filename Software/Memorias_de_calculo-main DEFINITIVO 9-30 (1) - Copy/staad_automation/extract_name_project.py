# Obtenemos la ruta staad del proyecto actual
import os 


try:
    from openstaad.root import Root
    root = Root()
except Exception as e:
    root = None
    print(f"Error al inicializar Root: {e}")
    
    
def crear_salida():
    """
    Obtiene la ruta del proyecto actual de STAAD Connect en esa ruta deben haber los archivos del proyecto pues hay por defecto guardara la memoria en caso de que no tenga std en documentos.
    """    
    
    try:
        print("Intentando obtener Root...")
        if root is None:
            print("Root es None. ¿Está STAAD abierto?")
            return None
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
    
def salida():
    """Recibe la ruta y se la pasa a la variable output_path, que es la ruta donde se guardará el archivo de salida y si es None guarda en documentos del disco c por defecto.
    """
    output_path = crear_salida()
    if output_path is None:
        # Si no se obtiene una ruta válida, usar la carpeta de documentos por defecto
        output_path = os.path.join(os.path.expanduser("~"), "Documents", "STAAD_Projects")
        print(f"Ruta de salida por defecto: {output_path}")
        os.makedirs(output_path, exist_ok=True)
        return output_path
    else:
        # Si se obtuvo una ruta de archivo, usar su directorio
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

def get_project_name():
    """
    Obtiene el nombre del proyecto actual de STAAD Connect.
    Si no se puede obtener desde STAAD, busca el primer archivo .STD en la carpeta actual.
    Retorna el nombre del proyecto (con extensión) o 'memoria de calculo' si no hay nada.
    """
    try:
        staad_file = crear_salida()
        if staad_file:
            project_name = os.path.basename(staad_file)
            print(f"Nombre del proyecto: {project_name}")
            return project_name
        else:
            # Buscar el primer archivo .STD en la carpeta actual
            cwd = os.getcwd()
            stds = [f for f in os.listdir(cwd) if f.lower().endswith('.std')]
            if stds:
                print(f"Nombre del proyecto (por archivo .STD en cwd): {stds[0]}")
                return stds[0]
            print("No se pudo obtener el nombre del proyecto. Usando nombre por defecto 'memoria de calculo'.")
            return "memoria de calculo"
    except Exception as e:
        print(f"Error al obtener el nombre del proyecto: {e}")
        return None
   

def encontrar_excel_entre_los_archivos_donde_esta_el_std():
    """
    Busca el archivo Excel entre los archivos del proyecto donde está el archivo .std. con un nommbre especifico.
    Retorna la ruta del archivo Excel si se encuentra, o None si no se encuentra.
    """
    try:
        staad_file = crear_salida()
        if staad_file:
            project_dir = os.path.dirname(staad_file)
            excel_file = os.path.join(project_dir, "Excel", "Límites de deflexión.xlsx")
            if os.path.exists(excel_file):
                print(f"Archivo Excel encontrado: {excel_file}")
                return excel_file
            else:
                print("No se encontró el archivo Excel en la ruta staad.")
                return None
    except Exception as e:
        print(f"Error al buscar el archivo Excel: {e}")
        return None
    

if __name__ == "__main__":
    # Ejemplo de uso
    print("Ruta del proyecto:", crear_salida())
    print("Nombre del proyecto:", get_project_name())
    print("Ruta del archivo Excel:", encontrar_excel_entre_los_archivos_donde_esta_el_std())
    print("Ruta de salida:", salida())
