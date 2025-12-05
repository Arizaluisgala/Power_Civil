"""
Componente del sidebar de navegación
"""
import flet as ft


class SidebarComponent:
    """Componente del menú lateral de navegación"""
    
    def __init__(self, colors, current_section, change_section_callback, close_app_callback, height=850):
        self.colors = colors
        self.current_section = current_section
        self.change_section_callback = change_section_callback
        self.close_app_callback = close_app_callback
        self.height = height
    
    def _handle_close_app(self, e):
        """Maneja el cierre de la aplicación con confirmación"""
        try:
            # Llamar al callback de cierre
            if self.close_app_callback:
                self.close_app_callback(e)
        except Exception as ex:
            print(f"Error en sidebar close: {ex}")
            # Fallback: forzar cierre directo
            try:
                import sys, os
                os._exit(0)
            except:
                pass
    
    def create_sidebar_menu(self):
        """Crea un menú lateral premium con diseño glassmorphism"""
        menu_items = [
            ("📁", "Archivos", "archivos", "Gestión de archivos del proyecto"),
            ("📝", "Proyecto", "datos", "Información del documento"),
            ("📸", "Capturas", "capturas", "Gestión de imágenes"),
            ("🚀", "Generar", "generar", "Crear memoria de cálculo"),
            ("❓", "Ayuda", "ayuda", "Guía de uso del sistema"),
            ("ℹ️", "Acerca de", "acerca", "Información del software")
        ]
        
        buttons = []
        for icon, title, section, description in menu_items:
            is_active = self.current_section == section
            
            # Botón con efecto hover y animaciones suaves
            button = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Text(icon, size=22),
                            width=40,
                            alignment=ft.alignment.center
                        ),
                        ft.Column([
                            ft.Text(
                                title,
                                size=15,
                                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500,
                                color=ft.colors.WHITE if is_active else self.colors['text_primary']
                            ),
                            ft.Text(
                                description,
                                size=11,
                                color=ft.colors.with_opacity(0.8, ft.colors.WHITE) if is_active else self.colors['text_secondary'],
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=3, expand=True)
                    ], spacing=12, alignment=ft.MainAxisAlignment.START)
                ]),
                bgcolor=self.colors['primary'] if is_active else ft.colors.TRANSPARENT,
                border_radius=16,
                padding=ft.padding.symmetric(horizontal=18, vertical=14),
                margin=ft.margin.only(bottom=8),
                on_click=lambda e, s=section: self.change_section_callback(s),
                ink=True,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color=ft.colors.with_opacity(0.1, self.colors['primary']),
                    offset=ft.Offset(0, 2)
                ) if is_active else None,
                border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])) if not is_active else None
            )
            buttons.append(button)
        
        # Botón de salir con diseño premium y mejor funcionalidad
        exit_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.LOGOUT, color=ft.colors.WHITE, size=22),
                ft.Text("Salir del Sistema", color=ft.colors.WHITE, size=15, weight=ft.FontWeight.W_600)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            bgcolor=self.colors['error'],
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            margin=ft.margin.only(top=24),
            on_click=self._handle_close_app,
            ink=True,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.colors.with_opacity(0.3, self.colors['error']),
                offset=ft.Offset(0, 2)
            )
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Column(
                        [*buttons],
                        spacing=0,
                        expand=True
                    ),
                    exit_button
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            width=320,
            height=self.height,  # Ahora el alto es dinámico
            bgcolor=self.colors['surface'],
            padding=18,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 3)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border']))
        )

# Función para obtener el alto de la pantalla desde Flet
def get_screen_height(page):
    """Obtiene el alto de la pantalla actual usando Flet Page."""
    return page.height
