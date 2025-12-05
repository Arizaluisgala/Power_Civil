"""
Sección acerca de la aplicación
"""
import flet as ft


class AcercaSection:
    """Sección con información sobre la aplicación"""

    def __init__(self, colors, height=None):
        self.colors = colors
    
    def create_acerca_section(self):
        """Crea la sección acerca de renovada y compacta"""
        return ft.Column([
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.PRECISION_MANUFACTURING, size=40, color=self.colors['primary']),
                            ft.Column([
                                ft.Text("MEMORIA METÁLICA", size=20, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                                ft.Text("Sistema Profesional v3.0", size=14, color=self.colors['text_secondary'])
                            ], spacing=4)
                        ], spacing=16),
                        
                        ft.Container(height=16),
                        ft.Divider(color=self.colors['border']),
                        ft.Container(height=16),
                        
                        ft.Column([
                            ft.Text("📋 Características:", size=14, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Text("• Generación automática de memorias de cálculo", size=13),
                            ft.Text("• Soporte para múltiples idiomas (Español/Inglés)", size=13),
                            ft.Text("• Integración con Excel y Word", size=13),
                            ft.Text("• Sistema de capturas de pantalla integrado", size=13),
                            ft.Text("• Interfaz moderna y profesional", size=13),
                            
                            ft.Container(height=12),
                            ft.Text("🛠️ Tecnologías:", size=14, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Text("• Python 3.x + Flet Framework", size=13),
                            ft.Text("• python-docx para manipulación de Word", size=13),
                            ft.Text("• openpyxl para procesamiento de Excel", size=13),
                            ft.Text("• Pillow para manejo de imágenes", size=13),
                            
                            ft.Container(height=12),
                            ft.Text("👨‍💻 Desarrollado para:", size=14, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Text("• Ingenieros estructurales", size=13),
                            ft.Text("• Consultores de construcción", size=13),
                            ft.Text("• Empresas de diseño estructural", size=13)
                        ], spacing=4)
                    ]),
                    padding=20
                ),
                elevation=2
            )
        ], spacing=0, expand=True)
