"""
INE-STRUCTUM - Punto de entrada principal
Ejecuta la aplicación Flet
"""

import flet as ft
from src.app import INEStructumApp


def main(page: ft.Page):
    """Función principal que ejecuta la aplicación"""
    app = INEStructumApp()
    app.main(page)


if __name__ == "__main__":
    print("🚀 Iniciando INE-STRUCTUM...")
    ft.app(target=main)
