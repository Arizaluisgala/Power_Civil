"""
INE-STRUCTUM - Aplicación Principal
VERSIÓN PROFESIONAL con layout centrado y márgenes proporcionales
"""

import flet as ft
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from views.proyectos_page import ProyectosPage


def main(page: ft.Page):
    page.title = "INE-STRUCTUM"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    logo_structum_path = "assets/logo_structum.png"
    
    def on_exit(e):
        page.window_destroy()
    
    # ==================== HEADER ====================
    header = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Image(src=logo_structum_path, width=45, height=45, fit=ft.ImageFit.CONTAIN) if os.path.exists(logo_structum_path) else ft.Text("🏗️", size=35),
                padding=ft.padding.only(left=15, right=10)
            ),
            ft.Text("INE-STRUCTUM", size=24, weight=ft.FontWeight.BOLD, color="#ffffff"),
            ft.Container(expand=True),
            ft.ElevatedButton("Salir", icon=ft.Icons.LOGOUT, on_click=on_exit, bgcolor="#ef4444", color="#ffffff", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
            ft.Container(width=15),
        ], alignment=ft.MainAxisAlignment.START),
        gradient=ft.LinearGradient(begin=ft.alignment.center_left, end=ft.alignment.center_right, colors=["#1e3a8a", "#2563eb", "#3b82f6", "#60a5fa"]),
        padding=15,
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=10, color="#00000020", offset=ft.Offset(0, 2))
    )
    
    # ==================== CONTENIDO ====================
    proyectos_view = ProyectosPage(page)
    
    # Contenedor con ancho máximo y padding proporcional
    content_wrapper = ft.Container(
        content=ft.Container(
            content=proyectos_view.build(),
            bgcolor="#ffffff",
            border_radius=12,
            padding=30,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=15, color="#00000010", offset=ft.Offset(0, 2))
        ),
        padding=ft.padding.symmetric(horizontal=40, vertical=30),
        expand=True,
        bgcolor="#f8fafc"
    )
    
    # ==================== NAVEGACIÓN ====================
    def on_nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            content_wrapper.content.content = proyectos_view.build()
        elif idx == 1:
            content_wrapper.content.content = ft.Container(
                content=ft.Text("Gestión de Productos - En desarrollo", size=20, color="#64748b"),
                padding=30
            )
        elif idx == 2:
            content_wrapper.content.content = ft.Container(
                content=ft.Text("Análisis - En desarrollo", size=20, color="#64748b"),
                padding=30
            )
        elif idx == 3:
            content_wrapper.content.content = ft.Container(
                content=ft.Text("Reportes - En desarrollo", size=20, color="#64748b"),
                padding=30
            )
        page.update()
    
    # NavigationRail
    nav_rail = ft.Container(
        content=ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.FOLDER_OUTLINED, selected_icon=ft.Icons.FOLDER, label="Proyectos"),
                ft.NavigationRailDestination(icon=ft.Icons.PRECISION_MANUFACTURING_OUTLINED, selected_icon=ft.Icons.PRECISION_MANUFACTURING, label="Productos"),
                ft.NavigationRailDestination(icon=ft.Icons.ANALYTICS_OUTLINED, selected_icon=ft.Icons.ANALYTICS, label="Análisis"),
                ft.NavigationRailDestination(icon=ft.Icons.DESCRIPTION_OUTLINED, selected_icon=ft.Icons.DESCRIPTION, label="Reportes"),
            ],
            on_change=on_nav_change,
            bgcolor="transparent"
        ),
        expand=True,
        alignment=ft.alignment.top_center,
    )
    
    # Copyright
    copyright_box = ft.Container(
        content=ft.Column([
            ft.Divider(height=1, color="#00000030"),
            ft.Text("© 2025 INELECTRA", size=11, color="#ffffff", text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=10,
    )
    
    # Barra lateral
    sidebar = ft.Container(
        content=ft.Column([nav_rail, copyright_box], spacing=0),
        width=130,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=["#d97706", "#f59e0b", "#fbbf24", "#fcd34d"]
        ),
    )
    
    # ==================== LAYOUT ====================
    page.add(
        ft.Column([
            header,
            ft.Container(
                content=ft.Row([sidebar, ft.VerticalDivider(width=1, color="#e5e7eb"), content_wrapper], spacing=0),
                expand=True
            )
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
