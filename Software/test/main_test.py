"""
Aplicación principal modularizada - Generador de Memorias de Cálculo
Versión corregida con mejoras de responsividad y UI
"""
import flet as ft
import os
import sys
import pythoncom
import glob
import time
pythoncom.CoInitialize()
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
parent_dir = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(parent_dir, ".env"))
sys.path.append(os.path.join(parent_dir, "document", "format"))
sys.path.append(os.path.join(parent_dir, "scripts"))
sys.path.append(parent_dir)

# Importar módulos de la aplicación
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

# Importar notificaciones
from notifications.notification_manager import NotificationManager


class MemoriaApp:
    """Clase principal de la aplicación modularizada"""
    
    def __init__(self):
        # Configurar tema de colores mejorado
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
            'background': '#f1f5f9',  # Mejorado para mejor contraste
            'background_alt': '#e2e8f0',  # Color alternativo para el área principal
            'card': '#ffffff',
            'sidebar_bg': '#ffffff',  # Fondo específico para sidebar
            'content_bg': '#f8fafc',  # Fondo específico para contenido
            'text_primary': '#111827',
            'text_secondary': '#6b7280',
            'border': '#e5e7eb',
            'border_light': '#f1f5f9',
            'shadow': 'rgba(0, 0, 0, 0.1)',
            'gradient_start': '#3b82f6',
            'gradient_end': '#1d4ed8',
            'glass': 'rgba(255, 255, 255, 0.95)',
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
            'Dev': '',
            '.: XX': '',
            'CODIGO COMPAÑIA': '',
            'CODIGO CONTRATISTA': ''
        }
        
        self.config_data = {
            'estructura': '',
            'idioma': 'es',
            'version': 'simple',
            'mostrar_seccion_8': False,
            'agregar_imagenes': True
        }
        
        # Mapeo de slots ordenados
        self.slots_ordenados = {v[0]: v[1] for v in sorted(IMAGE_SLOTS.values(), key=lambda x: x[0])}
        
        # Componentes de la UI
        self.header_component = None
        self.sidebar_component = None
        self.footer_component = None
        self.content_card_component = None
        self.notification_manager = None
        
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
        self.main_layout = None
        
        # Cargar archivos automáticos
        self._load_automatic_files()
    
    def _buscar_archivo_por_patrones(self, directorio, patrones, tipo_archivo):
        """
        Busca archivos Excel usando patrones flexibles que manejan variaciones en nombres
        """
        import re
        
        try:
            posibles = glob.glob(os.path.join(directorio, "*"))
            archivos_excel = [f for f in posibles if f.endswith(('.xlsx', '.xls'))]
            
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

    def _load_automatic_files(self):
        """Carga archivos automáticos desde .env y STAAD"""
        print("[DEBUG] Iniciando carga automática de archivos...")
        
        # Cargar automáticamente plantilla desde .env si existe
        plantilla_env = os.getenv("TEMPLATE_PATH", None)
        if plantilla_env and os.path.exists(plantilla_env):
            self.archivos["plantilla"] = plantilla_env
            print(f"[INFO] Plantilla cargada desde .env: {os.path.basename(plantilla_env)}")
        
        # Logo es opcional - solo cargar desde .env si existe, pero no es requerido
        logo_env = os.getenv("CANVA_LOGO", None)
        if logo_env and os.path.exists(logo_env):
            self.archivos["logo"] = logo_env
            print(f"[INFO] Logo cargado automáticamente desde .env: {os.path.basename(logo_env)}")
        else:
            print("[INFO] Logo no configurado - se usará el logo del documento de plantilla")
        
        # Buscar el archivo .std abierto usando get_path_of_staad_connect
        try:
            from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
            std_path = get_path_of_staad_connect()
        except Exception as e:
            print(f"[ERROR] Error al obtener ruta STAAD: {e}")
            std_path = None

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
        
        # Configurar UI
        self._setup_ui()
        
        # Mostrar mensajes de carga automática
        self._show_auto_load_messages()
    
    def _setup_page(self):
        """Configura las propiedades básicas de la página"""
        try:
            if hasattr(self.page, 'window_screen') and self.page.window_screen:
                self.page.window_width = self.page.window_screen.width
                self.page.window_height = self.page.window_screen.height
            else:
                self.page.window_width = 1280
                self.page.window_height = 720
        except Exception:
            self.page.window_width = 1280
            self.page.window_height = 720
        
        self.page.title = "Memoria Metálica - Sistema Profesional v3.1.0"
        self.page.window_maximized = True
        self.page.window_resizable = True
        self.page.bgcolor = self.colors['background']
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.HIDDEN
        
        # Agregar listener para resize de ventana
        self.page.on_resize = self.on_page_resize
        
        # Configurar FilePicker
        self.picker = ft.FilePicker(on_result=self.on_file_selected)
        self.page.overlay.append(self.picker)
    
    def _initialize_components(self):
        """Inicializa todos los componentes de la UI"""
        # Componentes principales
        self.header_component = HeaderComponent(self.colors)
        self.sidebar_component = SidebarComponent(
            self.colors, 
            self.seccion_actual, 
            self.cambiar_seccion, 
            self.close_app
        )
        self.footer_component = FooterComponent(self.colors)
        self.content_card_component = ContentCardComponent(self.colors)
        self.notification_manager = NotificationManager(self.page, self.colors)
        
        # Secciones
        self.archivos_section = ArchivosSection(
            self.colors, 
            self.archivos, 
            self.seleccionar_archivo
        )
        
        self.datos_section = DatosSection(
            self.colors,
            self.project_data,
            self.update_project_data
        )
        
        self.capturas_section = CapturaSection(
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
        """Configura la interfaz de usuario completa con mejor responsividad"""
        # Crear componentes principales
        header = self.header_component.create_modern_header()
        sidebar = self.sidebar_component.create_sidebar_menu()
        self.current_sidebar = sidebar
        
        # Contenido principal con mejor centrado y espaciado
        self.main_content = ft.Container(
            content=self.get_current_section_content(),
            expand=True,
            padding=ft.padding.all(20),
            alignment=ft.alignment.center,  # Centrar contenido
            bgcolor=self.colors['content_bg'],
            border_radius=12,
            margin=ft.margin.all(8),
            border=ft.border.all(1, self.colors['border_light']),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
        
        # Área de contenido principal con mejor separación visual
        content_area = ft.Container(
            content=ft.Row([
                # Sidebar con fondo diferenciado
                ft.Container(
                    content=sidebar,
                    bgcolor=self.colors['sidebar_bg'],
                    border_radius=12,
                    padding=8,
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=8,
                        color=ft.colors.with_opacity(0.06, ft.colors.BLACK),
                        offset=ft.Offset(0, 2)
                    )
                ),
                # Separador visual
                ft.Container(width=12),
                # Contenido principal
                self.main_content
            ], 
            expand=True, 
            alignment=ft.MainAxisAlignment.START, 
            spacing=0
            ),
            expand=True,
            padding=ft.padding.all(12),
            bgcolor=self.colors['background_alt'],
            alignment=ft.alignment.top_left,
        )
        
        # Footer fijo en la parte inferior
        footer = self.footer_component.create_footer()
        
        # Layout principal con estructura flexbox mejorada
        self.main_layout = ft.Container(
            content=ft.Column([
                # Header fijo
                ft.Container(
                    content=header,
                    bgcolor=self.colors['surface'],
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=4,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                        offset=ft.Offset(0, 2)
                    )
                ),
                # Área de contenido que se expande
                content_area,
                # Footer fijo en la parte inferior
                ft.Container(
                    content=footer,
                    bgcolor=self.colors['surface'],
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=4,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                        offset=ft.Offset(0, -2)
                    )
                )
            ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=0,
                tight=True  # Evita espacios extra
            ),
            bgcolor=self.colors['background'],
            expand=True,
            padding=0,
            margin=0
        )
        
        # Limpiar página y agregar layout
        self.page.clean()
        self.page.add(self.main_layout)
        self.page.update()
    
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
                thumb_color=ft.colors.WHITE,
                inactive_thumb_color=ft.colors.GREY_300,
                inactive_track_color=ft.colors.GREY_200
            )
            
            seccion8_switch = ft.Switch(
                label="Incluir deflexión horizontal",
                value=self.config_data['mostrar_seccion_8'],
                on_change=self.on_seccion8_change,
                active_color=self.colors['primary'],
                thumb_color=ft.colors.WHITE,
                inactive_thumb_color=ft.colors.GREY_300,
                inactive_track_color=ft.colors.GREY_200
            )
            
            content = self.archivos_section.create_archivos_section(
                estructura_field, idioma_dropdown, tipo_memoria_switch, seccion8_switch
            )
            title = "📁 Gestión de Archivos"
            
        elif self.seccion_actual == "datos":
            content = self.datos_section.create_datos_section()
            title = "📝 Datos del Proyecto"
            
        elif self.seccion_actual == "capturas":
            content = self.capturas_section.create_capturas_section()
            title = "📸 Capturas de Pantalla"
            
        elif self.seccion_actual == "generar":
            content = self.generar_section.create_generar_section(
                self.archivos, self.project_data, self.config_data, 
                self.capturadas, self.total_slots, self.config_data['agregar_imagenes']
            )
            title = "🚀 Generar Memoria"
            
        elif self.seccion_actual == "ayuda":
            content = self.ayuda_section.create_ayuda_section()
            title = "❓ Ayuda del Sistema"
            
        elif self.seccion_actual == "acerca":
            content = self.acerca_section.create_acerca_section()
            title = "ℹ️ Acerca del Software"
        
        else:
            # Fallback a archivos
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
                thumb_color=ft.colors.WHITE,
                inactive_thumb_color=ft.colors.GREY_300,
                inactive_track_color=ft.colors.GREY_200
            )
            
            seccion8_switch = ft.Switch(
                label="Incluir deflexión horizontal",
                value=self.config_data['mostrar_seccion_8'],
                on_change=self.on_seccion8_change,
                active_color=self.colors['primary'],
                thumb_color=ft.colors.WHITE,
                inactive_thumb_color=ft.colors.GREY_300,
                inactive_track_color=ft.colors.GREY_200
            )
            
            content = self.archivos_section.create_archivos_section(
                estructura_field, idioma_dropdown, tipo_memoria_switch, seccion8_switch
            )
            title = "📁 Gestión de Archivos"
        
        return self.content_card_component.create_content_card(title, content)
    
    def _show_auto_load_messages(self):
        """Muestra mensajes de archivos cargados automáticamente"""
        archivos_cargados = []
        archivos_faltantes = []
        
        # Verificar plantilla
        if self.archivos["plantilla"]:
            archivos_cargados.append(f"📄 Plantilla: {os.path.basename(self.archivos['plantilla'])}")
        else:
            archivos_faltantes.append("📄 Plantilla")
        
        # Logo (opcional)
        if self.archivos["logo"]:
            archivos_cargados.append(f"🖼️ Logo personalizado: {os.path.basename(self.archivos['logo'])}")
        else:
            archivos_cargados.append("🖼️ Logo: Se usará el del documento plantilla (predeterminado)")
        
        # Excel principal
        if self.archivos["excel"]:
            archivos_cargados.append(f"📊 Límites de deflexión: {os.path.basename(self.archivos['excel'])}")
        else:
            archivos_faltantes.append("📊 Excel de límites de deflexión")
        
        # Excel de cargas (opcional)
        if self.archivos["excel_cargas"]:
            archivos_cargados.append(f"📋 Cargas (XtraReport): {os.path.basename(self.archivos['excel_cargas'])}")
        else:
            archivos_faltantes.append("📋 Excel de cargas (XtraReport) - opcional")
        
        # Excel de sismo (opcional)
        if self.archivos["excel_sismo"]:
            archivos_cargados.append(f"🌍 Espectro sísmico: {os.path.basename(self.archivos['excel_sismo'])}")
        else:
            archivos_faltantes.append("🌍 Excel de sismo - opcional")
        
        # Mostrar archivos cargados
        if archivos_cargados:
            for archivo in archivos_cargados:
                if "predeterminado" in archivo or "personalizado" in archivo:
                    self.notification_manager.mostrar_mensaje(archivo, "info")
                else:
                    self.notification_manager.mostrar_mensaje(archivo, "success")
        
        # Mensaje resumen
        archivos_requeridos_cargados = sum(1 for k in ["plantilla", "excel"] if self.archivos[k])
        archivos_opcionales_cargados = sum(1 for k in ["excel_cargas", "excel_sismo"] if self.archivos[k])
        
        if archivos_requeridos_cargados == 2:
            mensaje_resumen = f"✅ Archivos principales listos"
            if archivos_opcionales_cargados > 0:
                mensaje_resumen += f" + {archivos_opcionales_cargados} opcionales"
            mensaje_resumen += f" | Total: {archivos_requeridos_cargados + archivos_opcionales_cargados} archivos"
            self.notification_manager.mostrar_mensaje(mensaje_resumen, "success")
        else:
            mensaje_resumen = f"⚠️ Archivos faltantes: {2 - archivos_requeridos_cargados} requeridos"
            if archivos_opcionales_cargados > 0:
                mensaje_resumen += f" | {archivos_opcionales_cargados} opcionales cargados"
            self.notification_manager.mostrar_mensaje(mensaje_resumen, "warning")
        
        # Cargar datos del proyecto desde STAAD si es posible
        self._load_project_data_from_staad()
        
        # Contar imágenes cargadas automáticamente
        imagenes_cargadas = len(self.capturadas)
        if imagenes_cargadas > 0:
            self.notification_manager.mostrar_mensaje(
                f"📸 {imagenes_cargadas} imágenes cargadas automáticamente desde STAAD",
                "success"
            )
        else:
            self.notification_manager.mostrar_mensaje(
                "📸 No se encontraron imágenes automáticas - usar captura manual",
                "info"
            )
    
    def _load_project_data_from_staad(self):
        """Carga datos del proyecto desde STAAD automáticamente"""
        try:
            # Intentar obtener el nombre del proyecto desde STAAD
            project_name = get_project_name()
            if project_name:
                self.project_data['NOMBRE DEL PROYECTO'] = project_name
                self.config_data['estructura'] = project_name
                
                # Actualizar datos en la sección correspondiente
                if self.datos_section:
                    self.datos_section.update_project_data(self.project_data)
                
                self.notification_manager.mostrar_mensaje(
                    f"🏗️ Proyecto cargado: {project_name}",
                    "success"
                )
        except Exception as e:
            print(f"[WARNING] No se pudo cargar el nombre del proyecto desde STAAD: {e}")
    
    def on_page_resize(self, e):
        """Maneja el redimensionamiento de la página"""
        if self.page and self.main_layout:
            self.page.update()
    
    def cambiar_seccion(self, seccion):
        """Cambia a una sección diferente"""
        if seccion != self.seccion_actual:
            self.seccion_actual = seccion
            
            # Actualizar sidebar
            if self.current_sidebar:
                self.current_sidebar.content = self.sidebar_component.create_sidebar_menu()
            
            # Actualizar contenido principal
            if self.main_content:
                self.main_content.content = self.get_current_section_content()
            
            self.page.update()
    
    def seleccionar_archivo(self, tipo_archivo):
        """Inicia el proceso de selección de archivo"""
        self.archivo_key_actual = tipo_archivo
        
        # Configurar filtros según el tipo de archivo
        if tipo_archivo == "plantilla":
            self.picker.allowed_extensions = ["docx", "doc"]
            self.picker.dialog_title = "Seleccionar Plantilla de Word"
        elif tipo_archivo == "logo":
            self.picker.allowed_extensions = ["png", "jpg", "jpeg", "bmp", "gif"]
            self.picker.dialog_title = "Seleccionar Logo"
        elif tipo_archivo in ["excel", "excel_cargas", "excel_sismo"]:
            self.picker.allowed_extensions = ["xlsx", "xls"]
            self.picker.dialog_title = "Seleccionar Archivo Excel"
        
        self.picker.pick_files(allow_multiple=False)
    
    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Maneja la selección de archivos"""
        if e.files and self.archivo_key_actual:
            archivo_seleccionado = e.files[0]
            ruta_archivo = archivo_seleccionado.path
            
            # Validar que el archivo existe
            if os.path.exists(ruta_archivo):
                self.archivos[self.archivo_key_actual] = ruta_archivo
                
                # Actualizar la UI
                self.main_content.content = self.get_current_section_content()
                self.page.update()
                
                # Mostrar notificación
                nombre_archivo = os.path.basename(ruta_archivo)
                tipo_nombres = {
                    "plantilla": "Plantilla",
                    "logo": "Logo",
                    "excel": "Excel principal",
                    "excel_cargas": "Excel de cargas",
                    "excel_sismo": "Excel de sismo"
                }
                
                self.notification_manager.mostrar_mensaje(
                    f"✅ {tipo_nombres.get(self.archivo_key_actual, 'Archivo')} seleccionado: {nombre_archivo}",
                    "success"
                )
            else:
                self.notification_manager.mostrar_mensaje(
                    "❌ Error: El archivo seleccionado no existe",
                    "error"
                )
        
        self.archivo_key_actual = None
    
    def on_estructura_change(self, e):
        """Maneja el cambio en el nombre de la estructura"""
        self.config_data['estructura'] = e.control.value
        # También actualizar en project_data para mantener sincronía
        self.project_data['NOMBRE DEL PROYECTO'] = e.control.value
    
    def on_idioma_change(self, e):
        """Maneja el cambio de idioma"""
        self.config_data['idioma'] = e.control.value
        self.idioma = e.control.value
        
        # Actualizar UI si es necesario
        self.main_content.content = self.get_current_section_content()
        self.page.update()
    
    def on_tipo_memoria_change(self, e):
        """Maneja el cambio de tipo de memoria"""
        self.config_data['version'] = "completa" if e.control.value else "simple"
        self.version = self.config_data['version']
        
        # Actualizar total de slots según el tipo
        if self.version == "completa":
            self.total_slots = 6
        else:
            self.total_slots = 6  # Mantener 6 slots para ambos tipos
        
        # Actualizar sección de capturas
        if self.capturas_section:
            self.capturas_section.total_slots = self.total_slots
        
        # Actualizar UI
        self.main_content.content = self.get_current_section_content()
        self.page.update()
    
    def on_seccion8_change(self, e):
        """Maneja el cambio de mostrar sección 8"""
        self.config_data['mostrar_seccion_8'] = e.control.value
        self.mostrar_seccion_8 = e.control.value
    
    def on_agregar_imagenes_change(self, e):
        """Maneja el cambio de agregar imágenes"""
        self.config_data['agregar_imagenes'] = e.control.value
        
        # Actualizar UI de capturas
        if self.capturas_section:
            self.capturas_section.agregar_imagenes = e.control.value
        
        # Actualizar contenido
        self.main_content.content = self.get_current_section_content()
        self.page.update()
    
    def update_project_data(self, field, value):
        """Actualiza los datos del proyecto"""
        self.project_data[field] = value
        
        # Si es el nombre del proyecto, también actualizar estructura
        if field == 'NOMBRE DEL PROYECTO':
            self.config_data['estructura'] = value
    
    def capturar_imagen(self, slot_num):
        """Captura una imagen para el slot especificado"""
        try:
            # Usar la función de captura de pantalla
            resultado = select_region_and_save(slot_num)
            
            if resultado and os.path.exists(resultado):
                self.capturadas[slot_num] = resultado
                
                # Actualizar UI
                self.main_content.content = self.get_current_section_content()
                self.page.update()
                
                self.notification_manager.mostrar_mensaje(
                    f"📸 Imagen capturada para slot {slot_num}",
                    "success"
                )
            else:
                self.notification_manager.mostrar_mensaje(
                    f"❌ Error al capturar imagen para slot {slot_num}",
                    "error"
                )
        except Exception as e:
            print(f"Error en capturar_imagen: {e}")
            self.notification_manager.mostrar_mensaje(
                f"❌ Error al capturar imagen: {str(e)}",
                "error"
            )
    
    def eliminar_captura(self, slot_num):
        """Elimina una captura específica"""
        if slot_num in self.capturadas:
            # Eliminar archivo si existe
            try:
                if os.path.exists(self.capturadas[slot_num]):
                    os.remove(self.capturadas[slot_num])
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
            
            # Eliminar del diccionario
            del self.capturadas[slot_num]
            
            # Actualizar UI
            self.main_content.content = self.get_current_section_content()
            self.page.update()
            
            self.notification_manager.mostrar_mensaje(
                f"🗑️ Imagen eliminada del slot {slot_num}",
                "info"
            )
    
    def limpiar_capturas(self):
        """Limpia todas las capturas"""
        # Eliminar archivos
        for ruta in self.capturadas.values():
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
            except Exception as e:
                print(f"Error al eliminar archivo: {e}")
        
        # Limpiar diccionario
        self.capturadas.clear()
        
        # Actualizar UI
        self.main_content.content = self.get_current_section_content()
        self.page.update()
        
        self.notification_manager.mostrar_mensaje(
            "🧹 Todas las capturas han sido eliminadas",
            "info"
        )
    
    def validar_datos(self):
        """Valida que todos los datos necesarios estén completos"""
        errores = []
        
        # Validar archivos requeridos
        if not self.archivos["plantilla"] or not os.path.exists(self.archivos["plantilla"]):
            errores.append("📄 Plantilla de Word requerida")
        
        if not self.archivos["excel"] or not os.path.exists(self.archivos["excel"]):
            errores.append("📊 Excel de límites de deflexión requerido")
        
        # Validar datos del proyecto
        campos_requeridos = ['NOMBRE DEL PROYECTO', 'NOMBRE DEL DOCUMENTO']
        for campo in campos_requeridos:
            if not self.project_data.get(campo, '').strip():
                errores.append(f"📝 {campo} requerido")
        
        # Validar estructura
        if not self.config_data['estructura'].strip():
            errores.append("🏗️ Nombre de la estructura requerido")
        
        # Validar imágenes si están habilitadas
        if self.config_data['agregar_imagenes'] and not self.capturadas:
            errores.append("📸 Al menos una imagen es requerida")
        
        return errores
    
    def generar_memoria(self):
        """Genera la memoria de cálculo"""
        try:
            # Validar datos
            errores = self.validar_datos()
            if errores:
                for error in errores:
                    self.notification_manager.mostrar_mensaje(error, "error")
                return
            
            # Mostrar mensaje de inicio
            self.notification_manager.mostrar_mensaje(
                "🚀 Iniciando generación de memoria...",
                "info"
            )
            
            # Preparar datos para la generación
            datos_generacion = {
                'archivos': self.archivos.copy(),
                'project_data': self.project_data.copy(),
                'config_data': self.config_data.copy(),
                'capturadas': self.capturadas.copy(),
                'version': self.version,
                'idioma': self.idioma,
                'mostrar_seccion_8': self.mostrar_seccion_8
            }
            
            # Generar memoria
            resultado = crear_memoria_de_calculo(datos_generacion)
            
            if resultado:
                self.notification_manager.mostrar_mensaje(
                    f"✅ Memoria generada exitosamente: {os.path.basename(resultado)}",
                    "success"
                )
                
                # Intentar abrir el archivo generado
                try:
                    os.startfile(resultado)
                except Exception as e:
                    print(f"No se pudo abrir el archivo automáticamente: {e}")
            else:
                self.notification_manager.mostrar_mensaje(
                    "❌ Error al generar la memoria",
                    "error"
                )
        
        except Exception as e:
            print(f"Error en generar_memoria: {e}")
            self.notification_manager.mostrar_mensaje(
                f"❌ Error al generar memoria: {str(e)}",
                "error"
            )
    
    def close_app(self):
        """Cierra la aplicación"""
        self.page.window_close()


def main():
    """Función principal para ejecutar la aplicación"""
    app = MemoriaApp()
    ft.app(target=app.main, assets_dir="assets")


if __name__ == "__main__":
    main()