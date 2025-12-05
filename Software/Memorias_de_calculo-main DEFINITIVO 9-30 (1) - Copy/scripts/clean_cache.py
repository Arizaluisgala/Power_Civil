#!/usr/bin/env python3
"""
Script para limpiar la caché de Python y forzar recarga de módulos
"""
import os
import sys
import shutil
import importlib

def clean_python_cache():
    """Limpia todos los archivos de caché de Python"""
    # Carpeta raíz del proyecto
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    exclude_folders = {os.path.join(project_root, 'venv_vir'), os.path.join(project_root, 'virenv')}

    for root, dirs, files in os.walk(project_root):
        # Saltar carpetas de entornos virtuales
        if any(root.startswith(exclude) for exclude in exclude_folders):
            continue
        # Limpiar archivos .pyc
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Eliminado: {file_path}")
                except Exception as e:
                    print(f"Error eliminando {file_path}: {e}")
        # Limpiar directorios __pycache__
        for dir_name in dirs:
            if dir_name == '__pycache__':
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Eliminado directorio: {dir_path}")
                except Exception as e:
                    print(f"Error eliminando directorio {dir_path}: {e}")

def reload_modules():
    """Recarga módulos específicos"""
    modules_to_reload = [
        'scripts.extract_tables_of_excel',
        'secciones.seccion_9',
        'secciones.seccion_7',
        'secciones.seccion_8',
        
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
                print(f"Módulo recargado: {module_name}")
            except Exception as e:
                print(f"Error recargando {module_name}: {e}")

if __name__ == "__main__":
    print("Limpiando caché de Python...")
    clean_python_cache()
    print("🔄 Recargando módulos...")
    reload_modules()
    print("✅ Limpieza completada!")
