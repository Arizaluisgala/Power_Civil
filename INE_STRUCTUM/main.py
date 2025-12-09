"""
INE STRUCTUM - Software de Verificación Estructural
Punto de entrada principal de la aplicación

Autor: Luis Ariza - Inelectra
Fecha: Diciembre 2025
"""

import sys
from pathlib import Path

# Agregar directorio src al path de Python
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """
    Función principal que inicia la aplicación
    """
    print("=" * 60)
    print("INE STRUCTUM - Inicializando...")
    print("=" * 60)
    
    # TODO: Aquí inicializaremos la aplicación después
    print("\n✅ Configuración exitosa!")
    print("📋 Próximo paso: Crear entorno virtual")
    

if __name__ == "__main__":
    main()
