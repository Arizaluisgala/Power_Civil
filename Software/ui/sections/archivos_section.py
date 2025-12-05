"""
Sección de gestión de archivos
"""
import flet as ft
import os


class ArchivosSection:
    """Sección para gestión de archivos del proyecto"""

    def __init__(self, colors, archivos, on_file_select_callback, on_refresh_callback, height=None):
        self.colors = colors
        self.archivos = archivos
        self.on_file_select_callback = on_file_select_callback
        self.on_refresh_callback = on_refresh_callback
        self.height = height if height is not None else 700
        self.setup_fields()

    @staticmethod
    def get_screen_height(page):
        """Obtiene el alto de la pantalla actual usando Flet Page."""
        return page.height if page and hasattr(page, 'height') else 700
    
    def setup_fields(self):
        """Configura los campos de la sección"""
        self.connected_std_file_field = ft.TextField(
            label="🔗 Archivo STAAD Conectado",
            read_only=True,
            expand=True,
            border_color=self.colors['success'],
            focused_border_color=self.colors['success'],
            border_radius=12,
            prefix_icon=ft.Icons.LINK,
            value=""
        )

        self.archivo_plantilla = ft.TextField(
            label="📄 Plantilla Word (.docx)",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.Icons.DESCRIPTION,
            value=os.path.basename(self.archivos["plantilla"]) if self.archivos["plantilla"] else ""
        )
        
        self.archivo_logo = ft.TextField(
            label="🖼️ Logo de la Empresa",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.Icons.IMAGE,
            value=os.path.basename(self.archivos["logo"]) if self.archivos["logo"] else ""
        )
        
        self.archivo_excel = ft.TextField(
            label="📊 Excel Principal",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.Icons.TABLE_CHART,
            value=os.path.basename(self.archivos["excel"]) if self.archivos["excel"] else ""
        )
        
        self.archivo_excel_cargas = ft.TextField(
            label="📈 Excel del Reporte del Staad Pro",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.Icons.ANALYTICS,
            value=os.path.basename(self.archivos["excel_cargas"]) if self.archivos["excel_cargas"] else ""
        )
        
        self.archivo_excel_sismo = ft.TextField(
            label="🌊 Excel del Sismo",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.Icons.WAVES,
            value=os.path.basename(self.archivos["excel_sismo"]) if self.archivos["excel_sismo"] else ""
        )

    def update_connected_std_file(self, file_path):
        """Actualiza el campo del archivo STAAD conectado."""
        if file_path and os.path.exists(file_path):
            self.connected_std_file_field.value = os.path.basename(file_path)
            self.connected_std_file_field.border_color = self.colors['success']
            self.connected_std_file_field.focused_border_color = self.colors['success']
        else:
            self.connected_std_file_field.value = "No se ha detectado un archivo .std"
            self.connected_std_file_field.border_color = self.colors['error']
            self.connected_std_file_field.focused_border_color = self.colors['error']

    def update_file_field(self, file_type, file_path):
        """Actualiza un campo de archivo específico"""
        filename = os.path.basename(file_path) if file_path else ""
        
        field_map = {
            "plantilla": self.archivo_plantilla,
            "logo": self.archivo_logo,
            "excel": self.archivo_excel,
            "excel_cargas": self.archivo_excel_cargas,
            "excel_sismo": self.archivo_excel_sismo
        }
        
        field = field_map.get(file_type)
        if field:
            field.value = filename
    
    def create_archivos_section(self, estructura_field, idioma_dropdown, tipo_memoria_switch, seccion8_switch, cargas_switch):
        """Crea la sección de archivos renovada con pregunta para carga manual"""
        return ft.Column([
            # Sección de archivos - más compacta
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📁 Archivos del Proyecto", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Row([
                            self.connected_std_file_field,
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                on_click=self.on_refresh_callback,
                                tooltip="Refrescar Detección de STAAD"
                            )
                        ]),
                        ft.Container(height=12),
                        
                        ft.ExpansionTile(
                            title=ft.Text("¿Desea cargar manualmente la plantilla Word y el logo?", size=13),
                            controls=[
                                ft.Container(
                                    content=ft.Row([
                                        self.archivo_plantilla,
                                        ft.ElevatedButton(
                                            "Cambiar",
                                            icon=ft.Icons.FOLDER_OPEN,
                                            on_click=lambda e: self.on_file_select_callback("plantilla"),
                                            bgcolor=self.colors['secondary'],
                                            color=ft.colors.WHITE,
                                            height=40
                                        )
                                    ], spacing=12),
                                    margin=ft.margin.only(bottom=12)
                                ),
                                ft.Container(
                                    content=ft.Row([
                                        self.archivo_logo,
                                        ft.ElevatedButton(
                                            "Cambiar",
                                            icon=ft.Icons.FOLDER_OPEN,
                                            on_click=lambda e: self.on_file_select_callback("logo"),
                                            bgcolor=self.colors['secondary'],
                                            color=ft.colors.WHITE,
                                            height=40
                                        )
                                    ], spacing=12),
                                    margin=ft.margin.only(bottom=12)
                                )
                            ]
                        ),
                        
                        # Excel y Excel de cargas siempre visibles
                        ft.Container(
                            content=ft.Row([
                                self.archivo_excel,
                                ft.ElevatedButton(
                                    "Seleccionar",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: self.on_file_select_callback("excel"),
                                    bgcolor=self.colors['secondary'],
                                    color=ft.colors.WHITE,
                                    height=40
                                )
                            ], spacing=12),
                            margin=ft.margin.only(bottom=12)
                        ),
                        
                        ft.Container(
                            content=ft.Row([
                                self.archivo_excel_cargas,
                                ft.ElevatedButton(
                                    "Seleccionar",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: self.on_file_select_callback("excel_cargas"),
                                    bgcolor=self.colors['secondary'],
                                    color=ft.colors.WHITE,
                                    height=40
                                )
                            ], spacing=12),
                            margin=ft.margin.only(bottom=12)
                        ),
                        
                        ft.Container(
                            content=ft.Row([
                                self.archivo_excel_sismo,
                                ft.ElevatedButton(
                                    "Seleccionar",
                                    icon=ft.Icons.FOLDER_OPEN,
                                    on_click=lambda e: self.on_file_select_callback("excel_sismo"),
                                    bgcolor=self.colors['secondary'],
                                    color=ft.colors.WHITE,
                                    height=40
                                )
                            ], spacing=12)
                        )
                    ]),
                    padding=16
                ),
                elevation=2
            ),
            
            ft.Container(height=12),
            
            # Sección de configuración
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("⚙️ Configuración del Proyecto", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Row([
                            estructura_field,
                            idioma_dropdown
                        ], spacing=12),
                        ft.Container(height=15),
                        ft.Row([tipo_memoria_switch, seccion8_switch, cargas_switch], spacing=25)
                    ]),
                    padding=16
                ),
                elevation=2
            )
        ], spacing=0, expand=True)