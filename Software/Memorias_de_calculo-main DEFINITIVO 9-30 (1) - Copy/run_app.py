"""
Punto de entrada principal para la aplicación Memoria Metálica
Ejecuta la versión modularizada desde la carpeta ui/
"""
import sys
import os
import codecs

# --- Inicio del Parche de Codificación para Windows ---
# Forzar la salida estándar y de error a UTF-8 para manejar emojis y caracteres especiales.
# Esto es necesario porque la consola de Windows a menudo usa una codificación incompatible (cp1252).
# Se comprueba si sys.stdout/sys.stderr no son None, lo que ocurre en entornos sin consola (ejecutables de GUI).
if sys.stdout and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        print("✔️ Salida estándar configurada a UTF-8.")
    except Exception as e:
        print(f"⚠️ No se pudo configurar la salida estándar a UTF-8: {e}")

if sys.stderr and sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        print("✔️ Salida de error configurada a UTF-8.")
    except Exception as e:
        print(f"⚠️ No se pudo configurar la salida de error a UTF-8: {e}")
# --- Fin del Parche de Codificación ---


# Agregar la carpeta ui al path para las importaciones
ui_path = os.path.join(os.path.dirname(__file__), "ui")
sys.path.insert(0, ui_path)

# Importar y ejecutar la aplicación modular
from ui.main import main

if __name__ == "__main__":
    print("Iniciando Memoria Metálica - Sistema Profesional v3.1.0")
    print("Cargando aplicación modularizada...")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Aplicación cerrada por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        input("Presiona Enter para cerrar...")