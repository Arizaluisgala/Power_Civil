"""
Componente del footer de la aplicación
"""
import flet as ft


class FooterComponent:
    """Componente del footer de la aplicación"""
    
    def __init__(self, colors):
        self.colors = colors
    
    def create_footer(self):
        """Crea el footer elegante con el mismo estilo del header"""
        return ft.Container(
            content=ft.Row([
                # Logo y título en el footer
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.ENGINEERING, color=ft.colors.WHITE, size=20, opacity=0.9),
                        ft.Container(width=8),
                        ft.Column([
                            ft.Text(
                                "Sistema Profesional de Memorias de Cálculo",
                                color=ft.colors.WHITE,
                                size=13,
                                weight=ft.FontWeight.W_600,
                                style=ft.TextStyle(letter_spacing=0.5)
                            ),
                            ft.Text(
                                "Ingeniería Estructural Automatizada",
                                color=ft.colors.with_opacity(0.85, ft.colors.WHITE),
                                size=10,
                                weight=ft.FontWeight.W_300,
                                style=ft.TextStyle(letter_spacing=0.3)
                            )
                        ], spacing=1)
                    ], spacing=0),
                    expand=True
                ),
                # Información de copyright estilizada
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"© {2025} Inelectra DevOps",
                            color=ft.colors.WHITE,
                            size=11,
                            weight=ft.FontWeight.W_500,
                            style=ft.TextStyle(letter_spacing=0.5)
                        ),
                        ft.Text(
                            "Todos los derechos reservados",
                            color=ft.colors.with_opacity(0.8, ft.colors.WHITE),
                            size=9,
                            weight=ft.FontWeight.W_300
                        )
                    ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END)
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[
                    self.colors['primary_dark'],
                    self.colors['primary'],
                    ft.colors.with_opacity(0.85, self.colors['primary'])
                ]
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
                offset=ft.Offset(0, -2)
            ),
            height=70,
            alignment=ft.alignment.center
        )
