"""
Componente para crear tarjetas de contenido
"""
import flet as ft


class ContentCardComponent:
    """Componente para crear tarjetas de contenido premium"""
    
    def __init__(self, colors):
        self.colors = colors
    
    def create_content_card(self, title, content, expand=False):
        """Crea una tarjeta de contenido premium con efectos modernos."""
        return ft.Container(
            content=ft.Column([
                # Header de la tarjeta con gradiente sutil
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            title,
                            size=26,
                            weight=ft.FontWeight.W_700,
                            color=self.colors['primary']
                        ),
                        ft.Container(
                            width=4,
                            height=30,
                            bgcolor=self.colors['accent'],
                            border_radius=2
                        )
                    ], spacing=16, alignment=ft.MainAxisAlignment.START),
                    padding=ft.padding.only(bottom=24)
                ),
                # Contenido principal
                ft.Column(
                    [content],
                    scroll=ft.ScrollMode.ADAPTIVE,
                    expand=True
                )
            ]),
            bgcolor=self.colors['surface'],
            border_radius=20,
            padding=20,
            expand=expand,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
