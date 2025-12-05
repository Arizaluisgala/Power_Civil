"""
Sección de datos del proyecto con DatePicker y gestión de proyectos guardados.
"""
import flet as ft
from datetime import datetime

class DatosSection:
    """Sección para gestión de datos del proyecto"""

    def __init__(self, colors, project_data, update_callback, idioma='es', height=None, 
                 saved_projects=None, load_project_callback=None, save_project_callback=None, 
                 delete_project_callback=None):
        self.colors = colors
        self.project_data = project_data
        self.update_callback = update_callback
        self.idioma = idioma
        self.height = height if height is not None else 700
        self.page = None
        
        self.saved_projects = saved_projects or []
        self.load_project_callback = load_project_callback
        self.save_project_callback = save_project_callback
        self.delete_project_callback = delete_project_callback
        
        self.setup_fields()

    @staticmethod
    def get_screen_height(page):
        """Obtiene el alto de la pantalla actual usando Flet Page."""
        return page.height if page and hasattr(page, 'height') else 700
    
    def setup_fields(self):
        """Configura los campos del proyecto y los controles de guardado/carga."""
        self.project_nombre = ft.TextField(
            label="NOMBRE DEL PROYECTO",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('NOMBRE DEL PROYECTO', ''),
            on_change=lambda e: self.update_callback('NOMBRE DEL PROYECTO', e.control.value)
        )

        self.project_documento = ft.TextField(
            label="NOMBRE DEL DOCUMENTO",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('NOMBRE DEL DOCUMENTO', ''),
            on_change=lambda e: self.update_callback('NOMBRE DEL DOCUMENTO', e.control.value)
        )

        self.project_fecha = ft.TextField(
            label="MM/DD/AAAA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('MM/DD/AAAA', ''),
            read_only=True,
            suffix_icon=ft.Icons.CALENDAR_MONTH,
            on_click=self._open_date_picker,
            helper_text="Haz clic para seleccionar fecha"
        )

        self.date_picker = ft.DatePicker(
            first_date=datetime(2020, 1, 1),
            last_date=datetime(2030, 12, 31),
            date_picker_entry_mode=ft.DatePickerEntryMode.CALENDAR,
            on_change=self._on_date_change,
            on_dismiss=self._on_date_dismiss,
        )

        self.project_xx = ft.TextField(
            label="Número de Revisión",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('.: XX', ''),
            on_change=lambda e: self.update_callback('.: XX', e.control.value),
            helper_text="Ej: 01, 02, 03..."
        )

        self.project_codigo_compania = ft.TextField(
            label="CODIGO COMPAÑIA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('CODIGO COMPAÑIA', ''),
            on_change=lambda e: self.update_callback('CODIGO COMPAÑIA', e.control.value)
        )

        self.project_codigo_contratista = ft.TextField(
            label="CODIGO CONTRATISTA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data.get('CODIGO CONTRATISTA', ''),
            on_change=lambda e: self.update_callback('CODIGO CONTRATISTA', e.control.value)
        )

        # Controles para guardar y cargar proyectos
        self.projects_dropdown = ft.Dropdown(
            label="Proyectos guardados",
            options=[ft.dropdown.Option(name) for name in self.saved_projects],
            width=400,
            border_color=self.colors['primary'],
            border_radius=12,
            on_change=self._on_project_selected
        )

        self.save_button = ft.IconButton(
            icon=ft.Icons.SAVE,
            tooltip="Guardar Proyecto Actual",
            on_click=self._save_project,
            icon_color=self.colors['primary'],
            icon_size=20
        )
        
        self.delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip="Eliminar Proyecto Seleccionado",
            on_click=self._delete_project,
            icon_color=self.colors['error'],
            icon_size=20
        )

        self._set_automatic_values()

    def _set_automatic_values(self):
        self.update_callback('Rev', 'Rev')
        if self.idioma == 'en':
            self.update_callback('Emisión', 'Issue')
        else:
            self.update_callback('Emisión', 'Emisión')

    def update_language(self, new_language):
        self.idioma = new_language
        self._set_automatic_values()

    def _open_date_picker(self, e):
        try:
            if self.project_fecha.value and self.project_fecha.value.strip():
                date_parts = self.project_fecha.value.split('/')
                if len(date_parts) == 3:
                    month, day, year = map(int, date_parts)
                    self.date_picker.value = datetime(year, month, day)
        except:
            self.date_picker.value = datetime.now()
        e.page.open(self.date_picker)

    def _on_date_change(self, e):
        if self.date_picker.value:
            formatted_date = self.date_picker.value.strftime("%m/%d/%Y")
            self.project_fecha.value = formatted_date
            self.update_callback('MM/DD/AAAA', formatted_date)
            e.page.update()

    def _on_date_dismiss(self, e):
        pass

    def _on_project_selected(self, e):
        if self.load_project_callback:
            self.load_project_callback(e.control.value)

    def _save_project(self, e):
        if self.save_project_callback:
            self.save_project_callback()

    def _delete_project(self, e):
        if self.delete_project_callback and self.projects_dropdown.value:
            self.delete_project_callback(self.projects_dropdown.value)

    def clear_project_fields(self):
        """Limpia los campos de texto del proyecto."""
        self.project_nombre.value = ''
        self.project_documento.value = ''
        self.project_fecha.value = ''
        self.project_xx.value = ''
        self.project_codigo_compania.value = ''
        self.project_codigo_contratista.value = ''
        if self.page:
            self.page.update()

    def update_project_fields(self, project_data):
        """Actualiza los campos de texto con los datos de un proyecto cargado."""
        self.project_nombre.value = project_data.get('NOMBRE DEL PROYECTO', '')
        self.project_documento.value = project_data.get('NOMBRE DEL DOCUMENTO', '')
        self.project_fecha.value = project_data.get('MM/DD/AAAA', '')
        self.project_xx.value = project_data.get('.: XX', '')
        self.project_codigo_compania.value = project_data.get('CODIGO COMPAÑIA', '')
        self.project_codigo_contratista.value = project_data.get('CODIGO CONTRATISTA', '')
        # Actualizar la UI
        if self.page:
            self.page.update()

    def update_projects_dropdown(self, saved_projects, selected_value=None):
        """Actualiza las opciones del dropdown de proyectos."""
        self.projects_dropdown.value = selected_value # Set value first
        self.projects_dropdown.options.clear()
        self.projects_dropdown.options.extend([ft.dropdown.Option(name) for name in saved_projects])
        if self.page:
            self.page.update()

    def create_datos_section(self, page=None):
        self.page = page
        
        return ft.Column(
            controls=[
                self.date_picker,
                # Gestión de Proyectos
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("📂 Gestión de Proyectos", size=15, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Row(
                                [
                                    self.projects_dropdown,
                                    self.save_button,
                                    self.delete_button
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER
                            )
                        ]),
                        padding=14
                    ),
                    elevation=2
                ),
                ft.Container(height=8),
                
                # Información Principal
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("📋 Información Principal", size=15, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Container(content=self.project_nombre, margin=ft.margin.only(bottom=8)),
                            ft.Container(content=self.project_documento, margin=ft.margin.only(bottom=0))
                        ], tight=True),
                        padding=14
                    ),
                    elevation=2
                ),
                ft.Container(height=8),

                # Fechas y Versiones
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("📅 Fecha y Revisión", size=15, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Row([self.project_fecha, self.project_xx], spacing=10, tight=True)
                        ], tight=True),
                        padding=14
                    ),
                    elevation=2
                ),
                ft.Container(height=8),

                # Códigos de Identificación
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("🏢 Códigos de Identificación", size=15, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=8),
                            ft.Row([self.project_codigo_compania, self.project_codigo_contratista], spacing=10, tight=True)
                        ], tight=True),
                        padding=14
                    ),
                    elevation=2
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )