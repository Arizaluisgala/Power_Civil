import sys
import os
# Añadir la raíz del proyecto (donde está staad_automation) al sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
from staad_automation.extract_name_project import get_project_name

# Extrae el nombre del proyecto STAAD
try:
    name = get_project_name()
    # Obtiene la ruta de conexión de STAAD
    staad = get_path_of_staad_connect()
except Exception as e:
    print(f"Advertencia: Error al obtener información del proyecto STAAD: {e}")
    name = None
    staad = None

def get_images(name, carpeta_destino=None):
    """
    Busca las 5 imágenes principales del proyecto STAAD y las retorna en un diccionario con claves específicas.
    Busca por nombre de clave en el archivo, no por número.
    
    Args:
        name: Nombre del proyecto STAAD
        carpeta_destino: Carpeta donde buscar las imágenes. Si no se especifica, usa la carpeta del proyecto.
    """
    import glob
    
    # Verificar que tenemos los datos necesarios
    if not name:
        print("No se pudo obtener el nombre del proyecto STAAD")
        return {}
    
    # Buscar la carpeta con el nombre base del archivo .STD (sin extensión)
    if carpeta_destino:
        project_dir = carpeta_destino
        print(f"🔍 Buscando imágenes en la carpeta especificada: {project_dir}")
    elif staad:
        parent_dir = os.path.dirname(staad)
        std_base = os.path.splitext(os.path.basename(staad))[0]
        project_dir = os.path.join(parent_dir, std_base)
        if not os.path.isdir(project_dir):
            print(f"❌ No se encontró la carpeta de imágenes '{std_base}' en '{parent_dir}'")
            return {clave: None for clave in [
                "Isometría 3D",
                "Dimensiones",
                "Nodos",
                "Vigas",
                "Perfiles"
            ]}
        print(f"🔍 Carpeta de imágenes encontrada: {project_dir}")
    else:
        print("No se pudo determinar la ubicación del proyecto STAAD")
        return {clave: None for clave in [
            "Isometría 3D",
            "Dimensiones",
            "Nodos",
            "Vigas",
            "Perfiles"
        ]}
    
    # Diccionario de salida con claves y su orden esperado
    claves = [
        "Isometría 3D",
        "Dimensiones",
        "Nodos",
        "Vigas",
        "Perfiles"
    ]
    
    resultado = {clave: None for clave in claves}
    
    if not os.path.exists(project_dir):
        print(f"El directorio del proyecto '{project_dir}' no existe.")
        return resultado
    
    print(f"📁 Explorando directorio: {project_dir}")
    
    # Buscar imágenes por nombre de clave
    for clave in claves:
        found = False
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"):
            try:
                patron_busqueda = os.path.join(project_dir, ext)
                archivos_encontrados = glob.glob(patron_busqueda)
                print(f"  🔍 Buscando {clave} en {len(archivos_encontrados)} archivos {ext}")
                
                for img in archivos_encontrados:
                    nombre_archivo = os.path.basename(img).lower()
                    clave_busqueda = clave.lower()
                    
                    # Busqueda más flexible
                    if (clave_busqueda in nombre_archivo or 
                        clave_busqueda.replace(" ", "_") in nombre_archivo or
                        clave_busqueda.replace(" ", "") in nombre_archivo):
                        resultado[clave] = img
                        found = True
                        print(f"  ✅ Encontrada imagen para '{clave}': {os.path.basename(img)}")
                        break
                        
                if found:
                    break
            except Exception as e:
                print(f"Error al buscar imágenes con extensión {ext}: {e}")
                continue
        
        if not found:
            print(f"  ❌ No se encontró imagen para '{clave}'")
    
    return resultado


if __name__ == "__main__":
    # Ejecutar la función y mostrar el resultado
    imagenes = get_images(name)
    for clave, ruta in imagenes.items():
        if ruta:
            print(f"{clave}: {ruta}")
        else:
            print(f"{clave}: No se encontró la imagen correspondiente.")