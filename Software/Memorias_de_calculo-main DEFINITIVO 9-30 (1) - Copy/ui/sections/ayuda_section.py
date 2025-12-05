"""
Sección de ayuda del sistema
"""
import flet as ft


class AyudaSection:
    """Sección de ayuda y guía de uso"""

    def __init__(self, colors, total_slots, height=None):
        self.colors = colors
        self.total_slots = total_slots
        self.height = height if height is not None else 700

    @staticmethod
    def get_screen_height(page):
        """Obtiene el alto de la pantalla actual usando Flet Page."""
        return page.height if page and hasattr(page, 'height') else 700

    def create_ayuda_section(self, page=None):
        """Crea la sección de ayuda renovada y compacta con altura dinámica"""
        altura = self.height
        if page is not None:
            altura = self.get_screen_height(page) - 120  # margen para header/footer
            if altura < 400:
                altura = 400
        return ft.Container(
            content=ft.Column([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("❓ Guía de Uso", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=12),
                            ft.ExpansionTile(
                                title=ft.Text("1. 📁 Configuración de Archivos", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text("Cómo cargar los archivos necesarios", size=12),
                                controls=[
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("• Plantilla Word: Documento base con formato predefinido", size=13),
                                            ft.Text("• Logo: Imagen corporativa (PNG, JPG, etc.)", size=13),
                                            ft.Text("• Excel Principal: Archivo con cálculos estructurales", size=13),
                                            ft.Text("• Excel Cargas: Archivo con análisis de cargas", size=13)
                                        ], spacing=6),
                                        padding=ft.padding.all(12)
                                    )
                                ]
                            ),
                            ft.ExpansionTile(
                                title=ft.Text("2. 📝 Datos del Proyecto", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text("Información que aparecerá en el documento", size=12),
                                controls=[
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("• Complete todos los campos requeridos", size=13),
                                            ft.Text("• Los códigos identifican empresa y contratista", size=13),
                                            ft.Text("• Las fechas deben estar en formato correcto", size=13),
                                            ft.Text("• El nombre del proyecto aparecerá en portada", size=13)
                                        ], spacing=6),
                                        padding=ft.padding.all(12)
                                    )
                                ]
                            ),
                            ft.ExpansionTile(
                                title=ft.Text("3. 📸 Capturas de Pantalla", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text("Cómo capturar imágenes del software", size=12),
                                controls=[
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("• Haga clic en 'Nueva Captura'", size=13),
                                            ft.Text("• Seleccione el área con el mouse", size=13),
                                            ft.Text("• La imagen se guardará automáticamente", size=13),
                                            ft.Text("• Puede capturar hasta " + str(self.total_slots) + " imágenes", size=13)
                                        ], spacing=6),
                                        padding=ft.padding.all(12)
                                    )
                                ]
                            ),
                            ft.ExpansionTile(
                                title=ft.Text("4. 🚀 Generación Final", weight=ft.FontWeight.BOLD, size=14),
                                subtitle=ft.Text("Crear la memoria de cálculo", size=12),
                                controls=[
                                    ft.Container(
                                        content=ft.Column([
                                            ft.Text("• Valide que todos los datos estén completos", size=13),
                                            ft.Text("• Haga clic en 'Generar Memoria'", size=13),
                                            ft.Text("• El documento se creará en la carpeta output", size=13),
                                            ft.Text("• Revise el archivo generado antes de entregar", size=13)
                                        ], spacing=6),
                                        padding=ft.padding.all(12)
                                    )
                                ]
                            )
                        ], spacing=8),
                        padding=16
                    ),
                    elevation=2
                )
            ], spacing=0, expand=True),
            height=altura,
            expand=False
        )
