"""
INE-STRUCTUM - Aplicación Principal
Sistema de Verificación Estructural para STAAD.Pro

Autor: Luis Ariza - Inelectra
Fecha: Diciembre 2025
Versión: 1.0.0 Beta
"""

import flet as ft
from src.views.proyectos_page import ProyectosPage


class INEStructumApp:
    """Clase principal de la aplicación"""
    
    def __init__(self):
        self.page = None
        self.current_section = "inicio"
        
        # Paleta de colores profesional
        self.colors = {
            'primary': '#2563eb',
            'secondary': '#06b6d4',
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'background': '#f8fafc',
            'surface': '#ffffff',
            'text_primary': '#111827',
            'text_secondary': '#6b7280',
        }
        
        # SECCIONES DE LA APLICACIÓN
        self.sections = {
            'inicio': {'icon': '🏠', 'title': 'Inicio'},
            'proyectos': {'icon': '📁', 'title': 'Gestión de Proyectos'},
            'productos': {'icon': '📦', 'title': 'Gestión de Productos'},
            'verificaciones': {'icon': '✓', 'title': 'Verificaciones'},
            'reportes': {'icon': '📄', 'title': 'Reportes'},
            'configuracion': {'icon': '⚙️', 'title': 'Configuración'},
        }
    
    def main(self, page: ft.Page):
        """Inicializa la aplicación"""
        self.page = page
        
        # Configurar ventana principal
        page.title = "INE-STRUCTUM v1.0.0"
        page.window.width = 1280
        page.window.height = 800
        page.window.min_width = 1024
        page.window.min_height = 600
        page.bgcolor = self.colors['background']
        page.padding = 0
        
        # Crear interfaz completa
        page.add(self.create_main_layout())
    
    def create_main_layout(self):
        """Crea el layout principal con sidebar y contenido"""
        self.main_content = ft.Container(
            content=self.get_section_content(self.current_section),
            expand=True,
            padding=20
        )
        
        return ft.Column(
            [
                self.create_header(),
                ft.Row(
                    [
                        self.create_sidebar(),
                        self.main_content
                    ],
                    expand=True,
                    spacing=0
                ),
                self.create_footer()
            ],
            spacing=0,
            expand=True
        )
    
    def create_header(self):
        """Crea el header de la aplicación"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        "🏗️ INE-STRUCTUM",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color="#FFFFFF"
                    ),
                    ft.Text(
                        "v1.0.0 Beta",
                        size=14,
                        color="#FFFFFF",
                        opacity=0.8
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=self.colors['primary'],
            padding=20
        )
    
    def create_sidebar(self):
        """Crea el menú lateral de navegación"""
        menu_items = []
        
        for section_id, section_info in self.sections.items():
            is_active = section_id == self.current_section
            
            menu_item = ft.Container(
                content=ft.Row(
                    [
                        ft.Text(section_info['icon'], size=20),
                        ft.Text(
                            section_info['title'],
                            size=14,
                            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                            color="#FFFFFF" if is_active else self.colors['text_primary']
                        )
                    ],
                    spacing=10
                ),
                bgcolor=self.colors['primary'] if is_active else "transparent",
                padding=15,
                border_radius=8,
                ink=True,
                on_click=lambda e, sid=section_id: self.change_section(sid)
            )
            
            menu_items.append(menu_item)
        
        return ft.Container(
            content=ft.Column(
                menu_items,
                spacing=5,
                scroll=ft.ScrollMode.AUTO
            ),
            width=250,
            bgcolor=self.colors['surface'],
            padding=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color="#00000010"
            )
        )
    
    def create_footer(self):
        """Crea el footer de la aplicación"""
        return ft.Container(
            content=ft.Text(
                "© 2025 Inelectra - Luis Ariza",
                size=12,
                color="#6B7280",
                text_align=ft.TextAlign.CENTER
            ),
            bgcolor=self.colors['surface'],
            padding=10
        )
    
    def change_section(self, section_id):
        """Cambia la sección actual y actualiza la UI"""
        if section_id != self.current_section:
            self.current_section = section_id
            self.main_content.content = self.get_section_content(section_id)
            self.page.clean()
            self.page.add(self.create_main_layout())
    
    def get_section_content(self, section_id):
        """Retorna el contenido de la sección especificada"""
        if section_id == "inicio":
            return self.create_inicio_section()
        elif section_id == "proyectos":
            # Integración con la página de proyectos
            proyectos_page = ProyectosPage(self.page)
            return proyectos_page.build()
        elif section_id == "productos":
            return self.create_productos_section()
        elif section_id == "verificaciones":
            return self.create_verificaciones_section()
        elif section_id == "reportes":
            return self.create_reportes_section()
        elif section_id == "configuracion":
            return self.create_configuracion_section()
        else:
            return ft.Text("Sección no implementada")
    
    # ==================== SECCIONES ====================
    
    def create_inicio_section(self):
        """Pantalla de bienvenida"""
        return ft.Column(
            [
                ft.Text("Sistema de Verificación Estructural", size=28, weight=ft.FontWeight.BOLD),
                ft.Divider(height=20, color="transparent"),
                
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Bienvenido a INE-STRUCTUM", size=18),
                            ft.Divider(),
                            ft.Text("✅ Sistema inicializado correctamente", color=self.colors['success']),
                            ft.Divider(height=20, color="transparent"),
                            
                            ft.Text("Características principales:", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text("• Gestión de proyectos con parámetros sísmicos"),
                            ft.Text("• Gestión de productos (modelos STAAD)"),
                            ft.Text("• Generación automática de combinaciones ASCE/Eurocode"),
                            ft.Text("• Verificación de deflexiones y derivas"),
                            ft.Text("• Generación de reportes profesionales"),
                        ],
                        spacing=10
                    ),
                    bgcolor=self.colors['surface'],
                    padding=30,
                    border_radius=12,
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#00000010")
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
    
    def create_productos_section(self):
        """Gestión de productos (modelos STAAD)"""
        return ft.Column(
            [
                ft.Text("📦 Gestión de Productos", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("[Fase 4] Aquí se gestionarán productos y conexión con STAAD", 
                       color=self.colors['warning']),
                ft.Text("• Conectar archivo .std", size=14),
                ft.Text("• Importar casos de carga", size=14),
                ft.Text("• Generar combinaciones automáticas", size=14),
            ],
            scroll=ft.ScrollMode.AUTO
        )
    
    def create_verificaciones_section(self):
        """Verificaciones estructurales"""
        return ft.Column(
            [
                ft.Text("✓ Verificaciones Estructurales", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("[Fase 5] Aquí se realizarán las verificaciones", 
                       color=self.colors['warning']),
                ft.Text("• Deflexiones verticales", size=14),
                ft.Text("• Desplazamientos por viento", size=14),
                ft.Text("• Derivas sísmicas", size=14),
            ],
            scroll=ft.ScrollMode.AUTO
        )
    
    def create_reportes_section(self):
        """Generación de reportes"""
        return ft.Column(
            [
                ft.Text("📄 Generación de Reportes", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("[Fase 6] Aquí se generarán los reportes", 
                       color=self.colors['warning'])
            ],
            scroll=ft.ScrollMode.AUTO
        )
    
    def create_configuracion_section(self):
        """Configuración general"""
        return ft.Column(
            [
                ft.Text("⚙️ Configuración", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Text("[En desarrollo] Configuración general del sistema", 
                       color=self.colors['warning'])
            ],
            scroll=ft.ScrollMode.AUTO
        )
