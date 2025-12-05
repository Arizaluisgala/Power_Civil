"""
Aplicación principal modularizada - Generador de Memorias de Cálculo
"""
import flet as ft
import os
import sys
import pythoncom
import glob
import time
import json
pythoncom.CoInitialize()
from dotenv import load_dotenv
load_dotenv()
# Cargar variables de entorno desde .env
parent_dir = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(parent_dir, ".env"))
sys.path.append(os.path.join(parent_dir, "document", "format"))
sys.path.append(os.path.join(parent_dir, "scripts"))
sys.path.append(parent_dir)

# Importar módulos de la aplicacióna
from document.format.memoria_de_calculo import crear_memoria_de_calculo
from scripts.config import IMAGE_SLOTS
from scripts.screenshots import select_region_and_save
from staad_automation.extract_name_project import (
    salida,
    get_project_name,
    encontrar_excel_entre_los_archivos_donde_esta_el_std
)

# Importar componentes de la UI
from components.header import HeaderComponent
from components.sidebar import SidebarComponent
from components.footer import FooterComponent
from components.content_card import ContentCardComponent

# Importar secciones
from sections.archivos_section import ArchivosSection
from sections.datos_section import DatosSection
from sections.capturas_section import CapturaSection
from sections.generar_section import GenerarSection
from sections.ayuda_section import AyudaSection
from sections.acerca_section import AcercaSection

PROJECTS_FILE = "projects.json"

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not in a bundle, so the base path is the project root
        # os.path.dirname(__file__) is ui/, so '..' is the project root
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)

class MemoriaApp:
    """Clase principal de la aplicación modularizada"""
    
    def __init__(self):
        # Configurar tema de colores
        self.colors = {
            'primary': '#2563eb',
            'primary_light': '#3b82f6',
            'primary_dark': '#1d4ed8',
            'secondary': '#06b6d4',
            'accent': '#8b5cf6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444',
            'surface': '#ffffff',
            'background': '#f8fafc',
            'card': '#ffffff',
            'text_primary': '#111827',
            'text_secondary': '#6b7280',
            'border': '#e5e7eb',
            'shadow': 'rgba(0, 0, 0, 0.1)',
            'gradient_start': '#3b82f6',
            'gradient_end': '#1d4ed8',
            'glass': 'rgba(255, 255, 255, 0.8)',
            'notification_bg': 'rgba(0, 0, 0, 0.8)'
        }
        
        # Estado de la aplicación
        self.page = None
        self.capturadas = {}
        self.total_slots = 6
        self.version = "simple"
        self.idioma = "es"
        self.mostrar_seccion_8 = False
        self.archivo_key_actual = None
        self.seccion_actual = "archivos"
        
        # Datos de la aplicación
        self.archivos = {
            "plantilla": "",
            "logo": "",
            "excel": "",
            "excel_cargas": "",
            "excel_sismo": ""
        }
        
        self.project_data = {
            'NOMBRE DEL PROYECTO': '',
            'Emisión': '',
            'MM/DD/AAAA': '',
            'NOMBRE DEL DOCUMENTO': '',
            'Rev': '',
            '.: XX': '',
            'CODIGO COMPAÑIA': '',
            'CODIGO CONTRATISTA': ''
        }
        
        self.config_data = {
            'estructura': '',
            'idioma': 'es',
            'version': 'simple',
            'mostrar_seccion_8': False,
            'agregar_imagenes': True,
            'mostrar_cargas': True
        }

        self.saved_projects = self._load_saved_projects()
        
        # Mapeo de slots ordenados
        self.slots_ordenados = {v[0]: v[1] for v in sorted(IMAGE_SLOTS.values(), key=lambda x: x[0])}
        
        # Componentes de la UI
        self.header_component = None
        self.sidebar_component = None
        self.footer_component = None
        self.content_card_component = None
        self.notification_bar = None
        
        # Secciones
        self.archivos_section = None
        self.datos_section = None
        self.capturas_section = None
        self.generar_section = None
        self.ayuda_section = None
        self.acerca_section = None
        
        # Referencias UI
        self.main_content = None
        self.picker = None
        self.current_sidebar = None
        self.body_row = None

    def _load_saved_projects(self):
        try:
            if os.path.exists(PROJECTS_FILE):
                with open(PROJECTS_FILE, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
        return {}

    def _save_projects(self):
        try:
            with open(PROJECTS_FILE, 'w') as f:
                json.dump(self.saved_projects, f, indent=4)
            return True
        except IOError:
            return False

    def show_notification(self, message, color=None):
        if not self.notification_bar:
            return
        self.notification_bar.content = ft.Text(message)
        self.notification_bar.bgcolor = color or self.colors['success']
        self.notification_bar.open = True
        self.page.update()

    def load_project(self, project_name):
        if project_name in self.saved_projects:
            self.project_data.update(self.saved_projects[project_name])
            self.datos_section.update_project_fields(self.project_data)
            self.show_notification(f"Proyecto '{project_name}' cargado.", self.colors['primary'])
            self.page.update()

    def save_project(self):
        project_name = self.project_data.get('NOMBRE DEL PROYECTO')
        if not project_name or not project_name.strip():
            self.show_notification("El nombre del proyecto no puede estar vacío.", self.colors['error'])
            return
        
        self.saved_projects[project_name] = self.project_data.copy()
        if self._save_projects():
            self.show_notification(f"Proyecto '{project_name}' guardado exitosamente.")
            self.datos_section.update_projects_dropdown(list(self.saved_projects.keys()))
            self.page.update()
        else:
            self.show_notification("Error al guardar el proyecto.", self.colors['error'])

    def delete_project(self, project_name):
        if project_name in self.saved_projects:
            del self.saved_projects[project_name]
            if self._save_projects():
                self.show_notification(f"Proyecto '{project_name}' eliminado.", self.colors['error'])
                self.datos_section.update_projects_dropdown(list(self.saved_projects.keys()), selected_value=None)
                self.datos_section.clear_project_fields()
                self.page.update()
            else:
                self.show_notification("Error al eliminar el proyecto.", self.colors['error'])

    def update_connected_file(self, file_path):
        if self.archivos_section:
            self.archivos_section.update_connected_std_file(file_path)
            if self.page:
                self.page.update()
    
    def _buscar_archivo_por_patrones(self, directorio, patrones, tipo_archivo):
        """
        Busca archivos Excel usando patrones flexibles que manejan variaciones en nombres
        """
        import re
        try:
            posibles = glob.glob(os.path.join(directorio, "*"))
            archivos_excel = [f for f in posibles if f.endswith(('.xlsx', '.xls', '.xlsm'))]
            print(f"[DEBUG] Buscando {tipo_archivo} en {len(archivos_excel)} archivos Excel")
            for archivo in archivos_excel:
                nombre_archivo = os.path.basename(archivo).lower()
                # Limpiar el nombre removiendo números y espacios extra
                nombre_limpio = re.sub(r'\d+', '', nombre_archivo)  # Remover números
                nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio)  # Normalizar espacios
                nombre_limpio = nombre_limpio.strip()
                print(f"[DEBUG] Evaluando archivo: {nombre_archivo} -> limpio: {nombre_limpio}")
                for patron in patrones:
                    patron_lower = patron.lower()
                    # Crear diferentes variaciones del patrón
                    variaciones = [
                        patron_lower,  # Patrón original
                        patron_lower.replace(' ', ''),  # Sin espacios
                        patron_lower.replace('ó', 'o'),  # Sin acentos
                        patron_lower.replace('í', 'i'),  # Sin acentos
                        re.sub(r'[áàäâ]', 'a', patron_lower),  # Normalizar a
                        re.sub(r'[éèëê]', 'e', patron_lower),  # Normalizar e
                        re.sub(r'[íìïî]', 'i', patron_lower),  # Normalizar i
                        re.sub(r'[óòöô]', 'o', patron_lower),  # Normalizar o
                        re.sub(r'[úùüû]', 'u', patron_lower),  # Normalizar u
                    ]
                    for variacion in variaciones:
                        if variacion in nombre_limpio or variacion in nombre_archivo:
                            print(f"[INFO] {tipo_archivo} encontrado con patrón '{patron}': {os.path.basename(archivo)}")
                            return archivo
            print(f"[DEBUG] No se encontró {tipo_archivo} con ningún patrón")
            return None
        except Exception as e:
            print(f"[ERROR] Error en búsqueda de {tipo_archivo}: {e}")
            return None

    def _load_automatic_files(self, e=None):
        """Carga archivos automáticos desde .env y STAAD"""
        print("[DEBUG] Iniciando carga automática de archivos...")

        # Cargar automáticamente plantilla desde .env si existe
        plantilla_env = os.getenv("TEMPLATE_PATH", None)
        if plantilla_env and os.path.exists(plantilla_env):
            self.archivos["plantilla"] = plantilla_env
            print(f"[INFO] Plantilla cargada desde .env: {os.path.basename(plantilla_env)}")
        else:
            # Si no hay .env, usar la plantilla por defecto "reporte de staad _LA.docx"
            try:
                default_template_path = resource_path("reporte de staad _LA.docx")
                if os.path.exists(default_template_path):
                    self.archivos["plantilla"] = default_template_path
                    print(f"[INFO] Plantilla por defecto cargada: {os.path.basename(default_template_path)}")
                else:
                    print(f"[WARNING] No se encontró la plantilla por defecto en: {default_template_path}")
            except Exception as e:
                print(f"[ERROR] No se pudo cargar la plantilla por defecto: {e}")

        # Logo es opcional - solo cargar desde .env si existe, pero no es requerido
        logo_env = os.getenv("LOGO_PATH", None)
        if logo_env and os.path.exists(logo_env):
            self.archivos["logo"] = logo_env
            print(f"[INFO] Logo cargado automáticamente desde .env: {os.path.basename(logo_env)}")
        else:
            print("[INFO] Logo no configurado - se usará el logo del documento de plantilla")

        # Buscar todos los archivos .std abiertos
        try:
            from staad_automation.get_path_of_staad_connetc import get_all_staad_paths
            std_paths = get_all_staad_paths()  # Debe retornar lista de rutas
        except ImportError:
            # Fallback si no existe la función, usar la original
            try:
                from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
                std_path = get_path_of_staad_connect()
                std_paths = [std_path] if std_path else []
            except Exception as e:
                print(f"[ERROR] Error al obtener ruta STAAD: {e}")
                std_paths = []
        except Exception as e:
            print(f"[ERROR] Error al obtener rutas STAAD: {e}")
            std_paths = []

        # Si hay más de un archivo .std, preguntar al usuario cuál usar
        if len(std_paths) > 1:
            self._mostrar_selector_staad(std_paths)
            return  # Esperar selección antes de continuar
        elif len(std_paths) == 1:
            std_path = std_paths[0]
            self.update_connected_file(std_path)
        else:
            std_path = None
            self.update_connected_file(None)

        if std_path and os.path.exists(std_path):
            std_dir = os.path.dirname(std_path)
            print(f"[DEBUG] Directorio STAAD encontrado: {std_dir}")

            # Definir patrones de búsqueda para cada tipo de Excel
            configuracion_busqueda = {
                "excel": {
                    "patrones": [
                        "límites de deflexión",
                        "limites de deflexion", 
                        "límites deflexión",
                        "limites deflexion",
                        "deflexion",
                        "deflexión",
                        "limite",
                        "limits",
                        "deflection limits",
                        "deflection"
                    ],
                    "descripcion": "Excel principal (Límites de deflexión)"
                },
                "excel_cargas": {
                    "patrones": [
                        "xtrareport",
                        "xtra report",
                        "extra report", 
                        "extrareport",
                        "reporte",
                        "report",
                        "cargas",
                        "loads",
                        "loading"
                    ],
                    "descripcion": "Excel de cargas (XtraReport)"
                },
                "excel_sismo": {
                    "patrones": [
                        "sismo",
                        "seismic",
                        "earthquake",
                        "espectro",
                        "spectrum",
                        "sismic",
                        "seismo",
                        "modal"
                    ],
                    "descripcion": "Excel de sismo (Espectro sísmico)"
                }
            }

            # Buscar cada tipo de Excel
            for tipo_excel, config in configuracion_busqueda.items():
                archivo_encontrado = self._buscar_archivo_por_patrones(
                    std_dir, 
                    config["patrones"], 
                    config["descripcion"]
                )

                if archivo_encontrado:
                    self.archivos[tipo_excel] = archivo_encontrado
                else:
                    print(f"[WARNING] No se encontró {config['descripcion']}")

        # Cargar imágenes automáticas
        self.cargar_imagenes_automaticas_staad()

    def _mostrar_selector_staad(self, rutas):
        """Muestra un diálogo para seleccionar el archivo .std si hay más de uno"""
        opciones = [ft.dropdown.Option(ruta, os.path.basename(ruta)) for ruta in rutas]
        self.staad_selector = ft.Dropdown(
            label="Selecciona el archivo STAAD a usar",
            options=opciones,
            width=500,
            border_color=self.colors['primary'],
            border_radius=12,
            on_change=self._on_staad_selected
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Archivos STAAD abiertos"),
            content=self.staad_selector,
            actions=[
                ft.TextButton("Aceptar", on_click=self._on_staad_aceptar)
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _on_staad_selected(self, e):
        """Callback al seleccionar un archivo STAAD"""
        self.staad_selector.value = e.control.value
        self.page.update()

    def _on_staad_aceptar(self, e):
        """Callback al aceptar la selección STAAD"""
        seleccionado = self.staad_selector.value
        if seleccionado:
            self.page.dialog.open = False
            self.page.update()
            self.update_connected_file(seleccionado)
            # Continuar flujo con el archivo seleccionado
            self._load_automatic_files_con_ruta(seleccionado)

    def _load_automatic_files_con_ruta(self, std_path):
        """Carga los archivos automáticos usando la ruta seleccionada de STAAD"""
        self.update_connected_file(std_path)
        if std_path and os.path.exists(std_path):
            std_dir = os.path.dirname(std_path)
            print(f"[DEBUG] Directorio STAAD seleccionado: {std_dir}")
            # ...repetir lógica de búsqueda de excels e imágenes...
            # Definir patrones de búsqueda para cada tipo de Excel
            configuracion_busqueda = {
                "excel": {
                    "patrones": [
                        "límites de deflexión",
                        "limites de deflexion", 
                        "límites deflexión",
                        "limites deflexion",
                        "deflexion",
                        "deflexión",
                        "limite",
                        "limits",
                        "deflection limits",
                        "deflection"
                    ],
                    "descripcion": "Excel principal (Límites de deflexión)"
                },
                "excel_cargas": {
                    "patrones": [
                        "xtrareport",
                        "xtra report",
                        "extra report", 
                        "extrareport",
                        "reporte",
                        "report",
                        "cargas",
                        "loads",
                        "loading"
                    ],
                    "descripcion": "Excel de cargas (XtraReport)"
                },
                "excel_sismo": {
                    "patrones": [
                        "sismo",
                        "seismic",
                        "earthquake",
                        "espectro",
                        "spectrum",
                        "sismic",
                        "seismo",
                        "modal"
                    ],
                    "descripcion": "Excel de sismo (Espectro sísmico)"
                }
            }
            # Buscar cada tipo de Excel
            for tipo_excel, config in configuracion_busqueda.items():
                archivo_encontrado = self._buscar_archivo_por_patrones(
                    std_dir, 
                    config["patrones"], 
                    config["descripcion"]
                )
                if archivo_encontrado:
                    self.archivos[tipo_excel] = archivo_encontrado
                else:
                    print(f"[WARNING] No se encontró {config['descripcion']}")
            # Cargar imágenes automáticas
            self.cargar_imagenes_automaticas_staad()
    
    def _buscar_excel_inteligente(self):
        """Busca el archivo Excel principal usando patrones flexibles"""
        try:
            from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
            std_path = get_path_of_staad_connect()
            
            if not std_path or not os.path.exists(std_path):
                return None
            
            std_dir = os.path.dirname(std_path)
            posibles = glob.glob(os.path.join(std_dir, "*.xlsx")) + glob.glob(os.path.join(std_dir, "*.xls"))
            
            # Patrones de búsqueda en orden de prioridad
            patrones_limites = [
                "límites de deflexión",
                "limites de deflexion", 
                "límites deflexión",
                "limites deflexion",
                "deflexion",
                "deflexión"
            ]
            
            # Buscar por patrones de prioridad
            for patron in patrones_limites:
                for f in posibles:
                    nombre_archivo = os.path.basename(f).lower()
                    if patron in nombre_archivo:
                        print(f"[INFO] Encontrado Excel principal por patrón '{patron}': {os.path.basename(f)}")
                        return f
            
            # Si no encuentra nada por patrones, usar la función original como fallback
            return encontrar_excel_entre_los_archivos_donde_esta_el_std()
            
        except Exception as e:
            print(f"[ERROR] Error en búsqueda inteligente de Excel: {e}")
            return None
    
    def cargar_imagenes_automaticas_staad(self):
        """Busca y carga hasta 5 imágenes automáticas desde la carpeta del proyecto STAAD"""
        try:
            from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
            from staad_automation.extract_name_project import get_project_name
            from staad_automation.get_images_static_of_staad import get_images
            
            std_path = get_path_of_staad_connect()
            if not std_path or not os.path.exists(std_path):
                print("No se encontró el archivo .std abierto.")
                return 0
            
            project_name = os.path.splitext(os.path.basename(std_path))[0]
            imagenes_dict = get_images(project_name)
            count = 0
            
            for idx, clave in enumerate(["Isometría 3D", "Dimensiones", "Nodos", "Vigas", "Perfiles"]):
                ruta = imagenes_dict.get(clave)
                if ruta and os.path.exists(ruta):
                    self.capturadas[idx+1] = ruta
                    count += 1
            return count
        except Exception as e:
            print(f"Error en cargar_imagenes_automaticas_staad: {e}")
            return 0
    
    def main(self, page: ft.Page):
        """Función principal que inicializa la aplicación"""
        self.page = page
        
        # Configurar página
        self._setup_page()
        
        # Inicializar componentes
        self._initialize_components()

        # Cargar archivos automáticos
        self._load_automatic_files()
        
        # Configurar UI
        self._setup_ui()
        
        # Mostrar mensajes de carga automática
        self._show_auto_load_messages()
    
    def _setup_page(self):
        """Configura las propiedades básicas de la página"""
        self.page.title = "Memoria Metálica - Sistema Profesional v3.1.0"
        self.page.window_resizable = True
        self.page.bgcolor = self.colors['background']
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        
        # Configurar SnackBar para notificaciones
        self.notification_bar = ft.SnackBar(content=ft.Text(""), duration=4000)
        self.page.overlay.append(self.notification_bar)
        
        # Agregar listener para resize de ventana
        self.page.on_resize = self.on_page_resize
        
        # Configurar FilePicker
        self.picker = ft.FilePicker(on_result=self.on_file_selected)
        self.page.overlay.append(self.picker)
    
    def _initialize_components(self):
        """Inicializa todos los componentes de la UI"""
        self.header_component = HeaderComponent(self.colors)
        self.sidebar_component = SidebarComponent(
            self.colors, 
            self.seccion_actual, 
            self.cambiar_seccion, 
            self.close_app
        )
        self.footer_component = FooterComponent(self.colors)
        self.content_card_component = ContentCardComponent(self.colors)
    
        # Secciones
        self.archivos_section = ArchivosSection(
            self.colors, 
            self.archivos, 
            self.seleccionar_archivo,
            self._load_automatic_files
        )
        
        self.datos_section = DatosSection(
            self.colors,
            self.project_data,
            self.update_project_data,
            self.idioma,
            saved_projects=list(self.saved_projects.keys()),
            load_project_callback=self.load_project,
            save_project_callback=self.save_project,
            delete_project_callback=self.delete_project
        )
        
        self.capturas_section = CapturaSection(
            self.page,
            self.colors,
            self.config_data,
            self.capturadas,
            self.total_slots,
            self.slots_ordenados,
            self.on_agregar_imagenes_change,
            self.capturar_imagen,
            self.limpiar_capturas,
            self.eliminar_captura
        )
        
        self.generar_section = GenerarSection(
            self.colors,
            self.validar_datos,
            self.generar_memoria
        )
        
        self.ayuda_section = AyudaSection(self.colors, self.total_slots)
        self.acerca_section = AcercaSection(self.colors)
    
    def _setup_ui(self):
        """Configura la interfaz de usuario principal con un layout responsivo."""
        self.current_sidebar = self.sidebar_component.create_sidebar_menu()
        self.main_content = ft.Column(
            [self.get_current_section_content()], 
            expand=True
        )

        self.body_row = ft.Row(
            [self.current_sidebar, self.main_content],
            expand=True
        )

        main_layout = ft.Column(
            [
                self.header_component.create_modern_header(),
                self.body_row,
                self.footer_component.create_footer()
            ],
            expand=True
        )

        self.page.add(main_layout)
    
    def get_current_section_content(self):
        """Obtiene el contenido de la sección actual"""
        content = None
        title = ""
        
        if self.seccion_actual == "archivos":
            # Crear campos de configuración aquí
            estructura_field = ft.TextField(
                label="🏗️ Nombre de la Estructura",
                expand=True,
                border_color=self.colors['primary'],
                focused_border_color=self.colors['secondary'],
                border_radius=12,
                value=self.config_data['estructura'],
                on_change=self.on_estructura_change
            )
            idioma_dropdown = ft.Dropdown(
                label="🌐 Idioma",
                options=[
                    ft.dropdown.Option("es", "Español"),
                    ft.dropdown.Option("en", "English")
                ],
                value=self.config_data['idioma'],
                width=200,
                border_color=self.colors['primary'],
                border_radius=12,
                on_change=self.on_idioma_change
            )
            tipo_memoria_switch = ft.Switch(
                label="Completa",
                value=self.config_data['version'] == "completa",
                on_change=self.on_tipo_memoria_change,
                active_color=self.colors['primary'],
                thumb_color=ft.Colors.WHITE,
                inactive_thumb_color=ft.Colors.GREY_300,
                inactive_track_color=ft.Colors.GREY_200
            )
            seccion8_switch = ft.Switch(
                label="Incluir deflexión horizontal",
                value=self.config_data['mostrar_seccion_8'],
                on_change=self.on_seccion8_change,
                active_color=self.colors['primary'],
                thumb_color=ft.Colors.WHITE,
                inactive_thumb_color=ft.Colors.GREY_300,
                inactive_track_color=ft.Colors.GREY_200
            )
            cargas_switch = ft.Switch(
                label="Incluir tablas de cargas",
                value=self.config_data.get('mostrar_cargas', True),
                on_change=self.on_cargas_change,
                active_color=self.colors['primary'],
                thumb_color=ft.Colors.WHITE,
                inactive_thumb_color=ft.Colors.GREY_300,
                inactive_track_color=ft.Colors.GREY_200
            )
            content = self.archivos_section.create_archivos_section(
                estructura_field, idioma_dropdown, tipo_memoria_switch, seccion8_switch, cargas_switch
            )
            title = "📁 Gestión de Archivos"
        elif self.seccion_actual == "datos":
            content = self.datos_section.create_datos_section(self.page)
            title = "📊 Datos del Proyecto"
        elif self.seccion_actual == "capturas":
            content = self.capturas_section.create_capturas_section()
            title = "📸 Capturas de Pantalla"
        elif self.seccion_actual == "generar":
            # Pasar notification_manager explícitamente para overlays
            content = self.generar_section.create_generar_section(
                self.archivos, self.project_data, self.config_data, 
                self.capturadas, self.total_slots, self.config_data['agregar_imagenes'],
                page=self.page
            )
            title = "⚙️ Generar Memoria"
        elif self.seccion_actual == "ayuda":
            content = self.ayuda_section.create_ayuda_section()
            title = "❓ Ayuda del Sistema"
        elif self.seccion_actual == "acerca":
            content = self.acerca_section.create_acerca_section()
            title = "ℹ️ Acerca del Software"
        else:
            # Fallback a archivos
            content = self.archivos_section.create_archivos_section(
                estructura_field, idioma_dropdown, tipo_memoria_switch, seccion8_switch
            )
            title = "📁 Gestión de Archivos"

        return self.content_card_component.create_content_card(title, content, expand=True)
    
    def _show_auto_load_messages(self):
        """Muestra mensajes de archivos cargados automáticamente"""
        archivos_cargados = []
        archivos_faltantes = []
        
        # Verificar plantilla
        if self.archivos["plantilla"]:
            archivos_cargados.append(f"[Plantilla] Plantilla: {os.path.basename(self.archivos['plantilla'])}")
        else:
            archivos_faltantes.append("[Plantilla] Plantilla")
        
        # Logo (opcional)
        if self.archivos["logo"]:
            archivos_cargados.append(f"[Logo] Logo personalizado: {os.path.basename(self.archivos['logo'])}")
        else:
            archivos_cargados.append("[Logo] Logo: Se usará el del documento plantilla (predeterminado)")
        
        # Excel principal
        if self.archivos["excel"]:
            archivos_cargados.append(f"[Excel] Límites de deflexión: {os.path.basename(self.archivos['excel'])}")
        else:
            archivos_faltantes.append("[Excel] Excel de límites de deflexión")
        
        # Excel de cargas (opcional)
        if self.archivos["excel_cargas"]:
            archivos_cargados.append(f"[Cargas] Cargas (XtraReport): {os.path.basename(self.archivos['excel_cargas'])}")
        else:
            archivos_faltantes.append(" Excel de cargas (XtraReport) - opcional")
        
        # Excel de sismo (opcional)
        if self.archivos["excel_sismo"]:
            archivos_cargados.append(f"[Sismo] Espectro sísmico: {os.path.basename(self.archivos['excel_sismo'])}")
        else:
            archivos_faltantes.append("[Sismo] Excel de sismo - opcional")
        
        # Todas las notificaciones deshabilitadas
        pass
    
    def on_page_resize(self, e):
        """Maneja los cambios de tamaño de ventana para responsividad"""
        self.page.update()
    
    def cambiar_seccion(self, nueva_seccion):
        """Cambia la sección actual y actualiza la UI."""
        if nueva_seccion != self.seccion_actual:
            self.seccion_actual = nueva_seccion
            self.sidebar_component.current_section = nueva_seccion
            
            # Re-render sidebar and content
            new_sidebar = self.sidebar_component.create_sidebar_menu()
            new_content = self.get_current_section_content()
            
            self.body_row.controls[0] = new_sidebar
            self.main_content.controls[0] = new_content
            
            self.page.update()
    
    def close_app(self, e):
        """Cierra la aplicación de manera segura - método específico para Flet"""
        try:
            # El método más efectivo en Flet es cerrar la página
            if self.page:
                # Limpiar componentes
                self.page.controls.clear()
                self.page.update()
                
                # Usar el método window_destroy si existe
                if hasattr(self.page, 'window_destroy'):
                    self.page.window_destroy()
                elif hasattr(self.page, 'window_close'):
                    self.page.window_close()
                
            # Force exit
            import sys
            sys.exit(0)
            
        except Exception as ex:
            print(f"Error al cerrar aplicación: {ex}")
            # Método de último recurso
            try:
                import os
                os._exit(0)
            except:
                # Último recurso: matar el proceso Python
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/f", "/im", "python.exe"], shell=True, capture_output=True)
                except:
                    pass
    
    def seleccionar_archivo(self, tipo_archivo):
        """Selecciona un archivo del tipo especificado"""
        self.archivo_key_actual = tipo_archivo
        # ...existing code...

        # Configurar el picker según el tipo de archivo
        if tipo_archivo == "plantilla":
            self.picker.pick_files(
                dialog_title="Seleccionar Plantilla Word",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["docx"],
                allow_multiple=False
            )
        elif tipo_archivo == "logo":
            self.picker.pick_files(
                dialog_title="Seleccionar Logo",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False
            )
        elif tipo_archivo in ["excel", "excel_cargas", "excel_sismo"]:
            self.picker.pick_files(
                dialog_title=f"Seleccionar {'Excel Principal' if tipo_archivo == 'excel' else 'Excel de Cargas' if tipo_archivo == 'excel_cargas' else 'Excel de Sismo'}",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["xlsx", "xls", "xlsm"],
                allow_multiple=False
            )
    
    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Maneja la selección de archivos"""
        if not e.files or not self.archivo_key_actual:
            return
        try:
            archivo_seleccionado = e.files[0]
            archivo_path = archivo_seleccionado.path
            archivo_nombre = archivo_seleccionado.name
            if not os.path.exists(archivo_path):
                return
            # Validar extensión según tipo
            extension = os.path.splitext(archivo_nombre)[1].lower()
            validaciones = {
                "plantilla": [".docx"],
                "logo": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
                "excel": [".xlsx", ".xls", ".xlsm"],
                "excel_cargas": [".xlsx", ".xls", ".xlsm"],
                "excel_sismo": [".xlsx", ".xls", ".xlsm"]
            }
            if self.archivo_key_actual in validaciones:
                extensiones_validas = validaciones[self.archivo_key_actual]
                if extension not in extensiones_validas:
                    return
            # Guardar la ruta del archivo
            self.archivos[self.archivo_key_actual] = archivo_path
            # Actualizar el campo en la UI
            self.archivos_section.update_file_field(self.archivo_key_actual, archivo_path)
            self.page.update()
            self.archivo_key_actual = None
        except Exception as ex:
            self.archivo_key_actual = None
    
    def update_project_data(self, key, value):
        """Actualiza los datos del proyecto"""
        self.project_data[key] = value
    
    def on_estructura_change(self, e):
        """Maneja cambios en el nombre de la estructura"""
        self.config_data['estructura'] = e.control.value
    
    def on_idioma_change(self, e):
        """Maneja cambios en el idioma"""
        self.config_data['idioma'] = e.control.value
        self.idioma = e.control.value
        
        # Actualizar la sección de datos con el nuevo idioma
        if self.datos_section:
            self.datos_section.update_language(self.idioma)
    
    def on_tipo_memoria_change(self, e):
        """Maneja cambios en el tipo de memoria"""
        self.config_data['version'] = "completa" if e.control.value else "simple"
        self.version = self.config_data['version']
        self.total_slots = 29 if self.version == "completa" else 6
        
        # Actualizar capturas section
        self.capturas_section.total_slots = self.total_slots
        self.capturas_section.update_lista_capturas()
        self.page.update()
    
    def on_seccion8_change(self, e):
        """Maneja cambios en la sección 8"""
        self.config_data['mostrar_seccion_8'] = e.control.value
        self.mostrar_seccion_8 = e.control.value

    def on_cargas_change(self, e):
        """Maneja cambios en la sección de cargas"""
        self.config_data['mostrar_cargas'] = e.control.value
    
    def on_agregar_imagenes_change(self, e):
        """Maneja cambios en agregar imágenes"""
        self.config_data['agregar_imagenes'] = e.control.value
        self.capturas_section.config_data['agregar_imagenes'] = e.control.value
        self.capturas_section.update_lista_capturas()
        self.page.update()
    
    def capturar_imagen(self, e, slot_num=None):
        """Inicia el proceso de captura de imagen, para un slot específico o el siguiente disponible."""
        try:
            target_slot = None
            
            if slot_num is not None:
                # Captura para un slot específico
                if slot_num in self.capturadas:
                    self.show_notification(f"El Slot {slot_num} ya tiene una imagen asignada.", self.colors['warning'])
                    return
                target_slot = slot_num
            else:
                # Captura para el siguiente slot disponible
                slots_disponibles = [s for s in range(1, self.total_slots + 1) if s not in self.capturadas]
                if not slots_disponibles:
                    self.show_notification("Todos los slots de captura están llenos.", self.colors['warning'])
                    return
                target_slot = slots_disponibles[0]

            # Minimizar ventana temporalmente
            self.page.window_minimized = True
            self.page.update()
            time.sleep(0.2) # Pequeña pausa para asegurar que la ventana se minimice

            # Realizar captura
            screenshot_path = select_region_and_save()

            # Restaurar ventana
            self.page.window_minimized = False
            self.page.update()

            if screenshot_path and os.path.exists(screenshot_path):
                self.capturadas[target_slot] = screenshot_path
                self.capturas_section.capturadas = self.capturadas
                self.capturas_section.update_lista_capturas()
                self.page.update()
                self.show_notification(f"¡Captura exitosa! Imagen guardada en Slot {target_slot}.", self.colors['success'])
            else:
                # No mostrar error si el usuario cancela la captura (screenshot_path será None)
                if screenshot_path is not None:
                    self.show_notification("Error al guardar la captura.", self.colors['error'])

        except Exception as ex:
            self.page.window_minimized = False
            self.page.update()
            self.show_notification(f"Error durante la captura: {str(ex)}", self.colors['error'])
    
    def eliminar_captura(self, slot_num):
        """Elimina una captura específica"""
        if slot_num in self.capturadas:
            try:
                if os.path.exists(self.capturadas[slot_num]):
                    os.remove(self.capturadas[slot_num])
                del self.capturadas[slot_num]
                self.capturas_section.capturadas = self.capturadas
                self.capturas_section.update_lista_capturas()
                self.page.update()
            except Exception as ex:
                self.show_notification(f"[ERROR] Error al eliminar: {str(ex)}", self.colors['error'])
    
    def limpiar_capturas(self, e):
        """Limpia todas las capturas"""
        def confirmar_limpieza(e):
            try:
                for path in self.capturadas.values():
                    if os.path.exists(path):
                        os.remove(path)
                self.capturadas.clear()
                self.capturas_section.capturadas = self.capturadas
                self.capturas_section.update_lista_capturas()
                self.page.update()
            except Exception as ex:
                self.show_notification(f"[ERROR] Error al limpiar: {str(ex)}", self.colors['error'])
            dialog.open = False
            self.page.update()

        def cancelar_limpieza(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("[WARNING] Confirmar limpieza"),
            content=ft.Text("¿Estás seguro de que quieres eliminar todas las capturas?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_limpieza),
                ft.TextButton("Sí, eliminar todo", on_click=confirmar_limpieza, 
                             style=ft.ButtonStyle(color=self.colors['error']))
            ]
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def validar_datos(self, e=None):
        """Valida que todos los datos estén completos y devuelve una tupla (bool, [errores])"""
        errores = []
        # Validar archivos requeridos (logo es opcional)
        archivos_requeridos = ["plantilla"]
        for archivo in archivos_requeridos:
            if not self.archivos[archivo]:
                errores.append(f"[ERROR] Falta seleccionar el archivo: {archivo.upper()}")
            elif not os.path.exists(self.archivos[archivo]):
                errores.append(f"[ERROR] No se encuentra el archivo: {archivo.upper()}")
        # Validar logo solo si está configurado
        if self.archivos.get("logo") and not os.path.exists(self.archivos["logo"]):
            errores.append("[ERROR] El archivo de logo especificado no existe")
        
        # Devolver resultado
        if errores:
            return (False, errores)
        else:
            return (True, [])

    def generar_memoria(self, e, progress_callback_ui=None):
        """Genera la memoria de cálculo."""
        import time

        def ui_callback(progress, description):
            if progress_callback_ui:
                progress_callback_ui.value = f"{int(progress * 100)}% - {description}"
                self.page.update()
            time.sleep(0.1)

        try:
            pythoncom.CoInitialize()
            
            imagenes_preparadas = {}
            if self.config_data.get('agregar_imagenes', True):
                for slot_num, ruta_imagen in self.capturadas.items():
                    if os.path.exists(ruta_imagen):
                        imagenes_preparadas[slot_num] = ruta_imagen

            try:
                from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
                std_path = get_path_of_staad_connect()
            except Exception as e:
                std_path = None
                ui_callback(0, f"Error al obtener ruta de STAAD: {e}")


            if std_path and os.path.exists(std_path):
                carpeta_destino = os.path.dirname(std_path)
                nombre_base = os.path.splitext(os.path.basename(std_path))[0]
                nombre_archivo = f"{nombre_base}.docx"
                ruta_completa_salida = os.path.join(carpeta_destino, nombre_archivo)
            else:
                nombre_archivo = get_project_name()
                if nombre_archivo:
                    nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
                    nombre_archivo = f"{nombre_sin_extension}.docx"
                else:
                    nombre_archivo = "memoria_de_calculo.docx"
                
                ruta_salida = salida()
                if not os.path.exists(ruta_salida):
                    os.makedirs(ruta_salida)
                ruta_completa_salida = os.path.join(ruta_salida, nombre_archivo)

            default_logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.png'))

            parametros = {
                'plantilla_path': self.archivos["plantilla"],
                'logo_path': self.archivos.get("logo", ""),
                'default_logo_path': default_logo_path,
                'excel_file_path': self.archivos["excel"],
                'excel_file_path_cargas': self.archivos.get("excel_cargas", ""),
                'excel_file_path_sismo': self.archivos.get("excel_sismo", ""),
                'estructura': self.config_data['estructura'],
                'idioma': self.config_data['idioma'],
                'version': self.config_data['version'],
                'mostrar_seccion_8': "s" if self.config_data['mostrar_seccion_8'] else "n",
                'mostrar_cargas': "s" if self.config_data.get('mostrar_cargas', True) else "n",
                'tomar_imagenes': "s" if self.config_data['agregar_imagenes'] else "n",
                'reemplazos': self.project_data.copy(),
                'output_path': ruta_completa_salida,
                'image_slots': imagenes_preparadas,
                'progress_callback': ui_callback
            }

            gen_result = crear_memoria_de_calculo(**parametros)
            
            if gen_result.get("success"):
                return {"ruta": gen_result.get("output_path"), "error": None}
            else:
                return {"ruta": None, "error": gen_result.get("error", "Error desconocido")}

        except Exception as ex:
            import traceback
            traceback.print_exc()
            return {"ruta": None, "error": str(ex)}

        finally:
            pythoncom.CoUninitialize()


def main():
    """Función principal de la aplicación"""
    app = MemoriaApp()
    ft.app(target=app.main, assets_dir="assets")


if __name__ == "__main__":
    main()