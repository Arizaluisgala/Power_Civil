"""
INE-STRUCTUM - Aplicación Principal
Con logos de Inelectra y Structum integrados
"""

import flet as ft
import os
from views.proyectos_page import ProyectosPage


def main(page: ft.Page):
    page.title = "INE-STRUCTUM"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # Verificar si los logos existen
    logo_structum_path = "assets/logo_structum.png"
    logo_inelectra_path = "assets/logo_inelectra.png"
    
    # ==================== HEADER CON GRADIENTE Y LOGOS ====================
    header_content = [
        # Logo Structum (cubo estructura)
        ft.Container(
            content=ft.Image(
                src=logo_structum_path if os.path.exists(logo_structum_path) else None,
                width=40,
                height=40,
                fit=ft.ImageFit.CONTAIN
            ) if os.path.exists(logo_structum_path) else ft.Icon(ft.Icons.ACCOUNT_BALANCE, size=30, color="#ffffff"),
            padding=10
        ),
        # Título
        ft.Text("INE-STRUCTUM", size=24, weight=ft.FontWeight.BOLD, color="#ffffff"),
        ft.Container(expand=True),
        # Logo Inelectra (derecha)
        ft.Container(
            content=ft.Image(
                src=logo_inelectra_path if os.path.exists(logo_inelectra_path) else None,
                width=120,
                height=35,
                fit=ft.ImageFit.CONTAIN
            ) if os.path.exists(logo_inelectra_path) else ft.Text("INELECTRA", color="#ffffff", size=14),
            padding=10
        ),
        ft.IconButton(
            icon=ft.Icons.ACCOUNT_CIRCLE,
            icon_color="#ffffff",
            tooltip="Usuario"
        ),
        ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color="#ffffff",
            tooltip="Configuración"
        ),
    ]
    
    header = ft.Container(
        content=ft.Row(header_content, alignment=ft.MainAxisAlignment.START),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa"]  # Gradiente azul Inelectra
        ),
        padding=15,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color="#00000020",
            offset=ft.Offset(0, 2)
        )
    )
    
    # ==================== CONTENIDO PRINCIPAL ====================
    proyectos_view = ProyectosPage(page)
    
    content_area = ft.Container(
        content=proyectos_view.build(),
        expand=True,
        bgcolor="#f8fafc"
    )
    
    # ==================== RAIL DE NAVEGACIÓN ====================
    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            content_area.content = proyectos_view.build()
        elif idx == 1:
            content_area.content = ft.Text("Gestión de Productos - En desarrollo", size=20)
        elif idx == 2:
            content_area.content = ft.Text("Análisis - En desarrollo", size=20)
        elif idx == 3:
            content_area.content = ft.Text("Reportes - En desarrollo", size=20)
        page.update()
    
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.FOLDER_OUTLINED,
                selected_icon=ft.Icons.FOLDER,
                label="Proyectos"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ACCOUNT_BALANCE_OUTLINED,  # Icono de estructura
                selected_icon=ft.Icons.ACCOUNT_BALANCE,
                label="Productos"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ANALYTICS_OUTLINED,
                selected_icon=ft.Icons.ANALYTICS,
                label="Análisis"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DESCRIPTION_OUTLINED,
                selected_icon=ft.Icons.DESCRIPTION,
                label="Reportes"
            ),
        ],
        on_change=on_nav_change,
        bgcolor="#ffffff",
    )
    
    # ==================== LAYOUT PRINCIPAL ====================
    page.add(
        ft.Column(
            [
                header,
                ft.Row(
                    [
                        rail,
                        ft.VerticalDivider(width=1),
                        content_area,
                    ],
                    expand=True,
                    spacing=0
                )
            ],
            spacing=0,
            expand=True
        )
    )


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
