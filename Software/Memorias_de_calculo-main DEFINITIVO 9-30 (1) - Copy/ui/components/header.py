"""
Componente del header de la aplicación
"""
import flet as ft
import os


class HeaderComponent:
    """Componente del header principal"""
    
    def __init__(self, colors):
        self.colors = colors
    
    def create_modern_header(self):
        """Crea un header premium con diseño ultra-moderno y profesional"""
        logo_path = os.getenv("CANVA_LOGO", "")
        print("DEBUG LOGO_PATH:", logo_path, "EXISTE:", os.path.exists(logo_path))
        
        # Icono/Logo más grande y visible
        if logo_path and os.path.exists(logo_path):
            logo_widget = ft.Image(
                src=logo_path,
                width=80,
                height=80,
                fit=ft.ImageFit.CONTAIN
            )
        else:
            logo_widget = ft.Icon(
                ft.Icons.PRECISION_MANUFACTURING,
                size=48,
                color=ft.colors.WHITE,
                opacity=0.95
            )

        return ft.Container(
            content=ft.Row([
                # Logo minimalista sin cajas feas
                ft.Container(
                    content=logo_widget,
                    padding=ft.padding.only(left=32),
                    alignment=ft.alignment.center_left
                ),
                # Título central
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "GENERADOR DE MEMORIAS DE CÁLCULO",
                            size=26,
                            weight=ft.FontWeight.W_700,
                            color=ft.colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                            style=ft.TextStyle(
                                letter_spacing=1.5,
                                height=1.2
                            )
                        ),
                        ft.Container(
                            content=ft.Text(
                                "Sistema Profesional de Ingeniería Estructural",
                                size=13,
                                color=ft.colors.with_opacity(0.9, ft.colors.WHITE),
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_300,
                                style=ft.TextStyle(letter_spacing=0.8)
                            ),
                            margin=ft.margin.only(top=2)
                        )
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                ),
                # Información de versión
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.VERIFIED_OUTLINED, color=ft.colors.WHITE, size=18, opacity=0.9),
                            ft.Text(
                                "v3.1.0",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.colors.WHITE,
                                style=ft.TextStyle(letter_spacing=0.5)
                            )
                        ], spacing=6, alignment=ft.MainAxisAlignment.END),
                        ft.Text(
                            "INELECTRA",
                            size=11,
                            color=ft.colors.with_opacity(0.85, ft.colors.WHITE),
                            weight=ft.FontWeight.W_500,
                            style=ft.TextStyle(letter_spacing=1.2)
                        )
                    ], 
                    spacing=2, 
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.END
                    ),
                    padding=ft.padding.only(right=32),
                    alignment=ft.alignment.center_right
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=85,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[
                    ft.colors.with_opacity(0.85, self.colors['primary']),
                    self.colors['primary'],
                    self.colors['primary_dark']
                ]
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
