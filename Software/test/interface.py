import flet as ft
import os
import sys
import pythoncom
import glob
import time
pythoncom.CoInitialize()
from dotenv import load_dotenv
# Cargar variables de entorno desde .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.path.append(os.path.join(os.path.dirname(__file__), "document", "format"))
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

from document.format.memoria_de_calculo import crear_memoria_de_calculo
from scripts.config import IMAGE_SLOTS
from scripts.screenshots import select_region_and_save
from staad_automation.extract_name_project import (
    salida,
    get_project_name,
    encontrar_excel_entre_los_archivos_donde_esta_el_std
)


# Mapeo: número de slot -> descripción
SLOTS_ORDENADOS = {v[0]: v[1] for v in sorted(IMAGE_SLOTS.values(), key=lambda x: x[0])}

class MemoriaApp:
    def cargar_imagenes_automaticas_staad(self):
        """Busca y carga hasta 5 imágenes automáticas desde la carpeta del proyecto STAAD (.std)."""
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
    def recargar_env(self):
        """Recarga el archivo .env y actualiza las variables de entorno usadas en la app."""
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
        # Actualizar rutas de archivos desde el .env
        plantilla_env = os.getenv("TEMPLATE_PATH", None)
        logo_env = os.getenv("LOGO_PATH", None)
        if plantilla_env and os.path.exists(plantilla_env):
            self.archivos["plantilla"] = plantilla_env
        if logo_env and os.path.exists(logo_env):
            self.archivos["logo"] = logo_env
        # Si tienes más variables dependientes del .env, actualízalas aquí
        # Por ejemplo, si usas CANVA_LOGO en el header, podrías forzar update de UI aquí
        if self.page:
            self.page.update()
    def __init__(self):
        self.page = None
        self.capturadas = {}
        self.total_slots = 6
        self.version = "simple"
        self.idioma = "es"
        self.mostrar_seccion_8 = False
        self.archivo_key_actual = None
        self.seccion_actual = "archivos"
        # Archivos del proyecto
        self.archivos = {
            "plantilla": "",
            "logo": "",
            "excel": "",
            "excel_cargas": "",
            "excel_sismo": ""
        }
        # Cargar automáticamente plantilla y logo desde .env si existen
        plantilla_env = os.getenv("TEMPLATE_PATH", None)
        logo_env = os.getenv("CANVA_LOGO", None)
        # Siempre cargar por defecto desde .env si existen
        if plantilla_env and os.path.exists(plantilla_env):
            self.archivos["plantilla"] = plantilla_env
        if logo_env and os.path.exists(logo_env):
            self.archivos["logo"] = logo_env
        # Si el usuario quiere cambiar, lo puede hacer después manualmente
        # Tema moderno y elegante - UI/UX de nivel empresarial
        self.colors = {
            'primary': '#2563eb',           # Azul profesional moderno
            'primary_light': '#3b82f6',     # Azul claro
            'primary_dark': '#1d4ed8',      # Azul oscuro
            'secondary': '#06b6d4',         # Cyan vibrante
            'accent': '#8b5cf6',            # Violeta elegante
            'success': '#10b981',           # Verde esmeralda
            'warning': '#f59e0b',           # Ámbar
            'error': '#ef4444',             # Rojo coral
            'surface': '#ffffff',           # Blanco puro
            'background': '#f8fafc',        # Gris muy claro
            'card': '#ffffff',              # Blanco para tarjetas
            'text_primary': '#111827',      # Gris muy oscuro
            'text_secondary': '#6b7280',    # Gris medio
            'border': '#e5e7eb',            # Gris claro para bordes
            'shadow': 'rgba(0, 0, 0, 0.1)', # Sombra sutil
            'gradient_start': '#3b82f6',    # Inicio de gradiente
            'gradient_end': '#1d4ed8',      # Final de gradiente
            'glass': 'rgba(255, 255, 255, 0.8)', # Efecto cristal
            'notification_bg': 'rgba(0, 0, 0, 0.8)'  # Fondo de notificaciones
        }

        # Estado persistente de datos del proyecto
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
        
        # Configuración persistente
        self.config_data = {
            'estructura': '',
            'idioma': 'es',
            'version': 'simple',
            'mostrar_seccion_8': False,
            'agregar_imagenes': True
        }

    def on_page_resize(self, e):
        """Maneja los cambios de tamaño de ventana para responsividad"""
        try:
            # Recalcula anchos/altos
            self.page.window_width = e.window_width
            self.page.window_height = e.window_height  # Corregido typo

            # Ajustar el sidebar responsivamente si existe
            if self.current_sidebar and hasattr(e, 'window_width'):
                # El sidebar ocupará 1/4 del ancho en pantallas grandes, mínimo 280px, máximo 350px
                sidebar_width = max(280, min(350, int(e.window_width * 0.25)))
                self.current_sidebar.width = sidebar_width
            # Forzar update de toda la página para refrescar layout
            self.page.update()
        except Exception as ex:
            print(f"Error en resize: {ex}")

    def main(self, page: ft.Page):
        self.page = page
        # Ajustar ventana al área visible del sistema operativo
        try:
            if hasattr(page, 'window_screen') and page.window_screen:
                page.window_width = page.window_screen.width
                page.window_height = page.window_screen.height
            else:
                page.window_width = 1280
                page.window_height = 720
        except Exception:
            page.window_width = 1280
            page.window_height = 720
        page.title = "Memoria Metálica - Sistema Profesional v3.1.0"
        page.window_maximized = True
        page.window_resizable = True
        page.bgcolor = self.colors['background']
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.scroll = ft.ScrollMode.HIDDEN  # Evitar scroll general
        
        # Agregar listener para resize de ventana
        page.on_resize = self.on_page_resize
        
        # Configurar FilePicker
        self.picker = ft.FilePicker(on_result=self.on_file_selected)
        page.overlay.append(self.picker)  # IMPORTANTE: Debe estar en overlay

        # Mostrar mensaje de carga automática
        if self.archivos["plantilla"]:
            self.mostrar_mensaje(f"Plantilla cargada automáticamente: {os.path.basename(self.archivos['plantilla'])}", "info")
        if self.archivos["logo"]:
            self.mostrar_mensaje(f"Logo cargado automáticamente: {os.path.basename(self.archivos['logo'])}", "info")

        # Buscar el archivo .std abierto usando get_path_of_staad_connect
        try:
            from staad_automation.get_path_of_staad_connetc import get_path_of_staad_connect
            std_path = get_path_of_staad_connect()
        except Exception:
            std_path = None

        if std_path and os.path.exists(std_path):
            std_dir = os.path.dirname(std_path)
            # Excel principal
            excel_path = None
            posibles = glob.glob(os.path.join(std_dir, "*"))
            for f in posibles:
                if os.path.basename(f).lower() == "límites de deflexión.xlsx".lower():
                    excel_path = f
                    break
            if excel_path and os.path.exists(excel_path):
                self.archivos["excel"] = excel_path
                self.mostrar_mensaje(f"Excel principal cargado automáticamente: {os.path.basename(excel_path)}", "info")
            # Excel de cargas
            excel_cargas_path = None
            for f in posibles:
                nombre_archivo = os.path.basename(f).lower()
                if "xtrareport" in nombre_archivo or ("reporte" in nombre_archivo and f.endswith(('.xlsx', '.xls'))):
                    excel_cargas_path = f
                    break
            if excel_cargas_path and os.path.exists(excel_cargas_path):
                self.archivos["excel_cargas"] = excel_cargas_path
                self.mostrar_mensaje(f"Excel de cargas cargado automáticamente: {os.path.basename(excel_cargas_path)}", "info")
            # Excel de sismo
            excel_sismo_path = None
            for f in posibles:
                nombre_archivo = os.path.basename(f).lower()
                if "sismo" in nombre_archivo and f.endswith(('.xlsx', '.xls')):
                    excel_sismo_path = f
                    break
            if excel_sismo_path and os.path.exists(excel_sismo_path):
                self.archivos["excel_sismo"] = excel_sismo_path
                self.mostrar_mensaje(f"Excel de sismo cargado automáticamente: {os.path.basename(excel_sismo_path)}", "info")
            # Cargar imágenes automáticas
            imagenes_automaticas = self.cargar_imagenes_automaticas_staad()
            if imagenes_automaticas > 0:
                print(f"🎯 Se cargaron {imagenes_automaticas} imágenes automáticamente desde STAAD")
            else:
                print("⚠️ No se encontraron imágenes automáticas en STAAD. Se requerirán capturas manuales.")
        else:
            print("No se encontró el archivo .std abierto o la ruta no existe.")

        # AGREGAR ESTA LÍNEA PARA FORZAR LA ACTUALIZACIÓN
        page.update()
        self.setup_ui()

    def create_modern_header(self):
        """Crea un header premium con diseño ultra-moderno y profesional"""
        logo_path = os.getenv("CANVA_LOGO", "")
        print("DEBUG LOGO_PATH:", logo_path, "EXISTE:", os.path.exists(logo_path))
        # Icono/Logo más grande y visible
        if logo_path and os.path.exists(logo_path):
            logo_widget = ft.Image(
                src=logo_path,
                width=80,  # Más grande
                height=80,  # Más grande
                fit=ft.ImageFit.CONTAIN
            )
        else:
            logo_widget = ft.Icon(
                ft.Icons.PRECISION_MANUFACTURING,
                size=48,  # Más grande
                color=ft.colors.WHITE,
                opacity=0.95
            )

        return ft.Container(
            content=ft.Row([
                # Logo minimalista sin cajas feas
                ft.Container(
                    content=logo_widget,
                    padding=ft.padding.only(left=32),
                    alignment=ft.alignment.center_left
                ),
                # ...existing code...
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "GENERADOR DE MEMORIAS DE CÁLCULO",
                            size=26,
                            weight=ft.FontWeight.W_700,
                            color=ft.colors.WHITE,
                            text_align=ft.TextAlign.CENTER,
                            style=ft.TextStyle(
                                letter_spacing=1.5,
                                height=1.2
                            )
                        ),
                        ft.Container(
                            content=ft.Text(
                                "Sistema Profesional de Ingeniería Estructural",
                                size=13,
                                color=ft.colors.with_opacity(0.9, ft.colors.WHITE),
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_300,
                                style=ft.TextStyle(letter_spacing=0.8)
                            ),
                            margin=ft.margin.only(top=2)
                        )
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0
                    ),
                    alignment=ft.alignment.center,
                    expand=True
                ),
                # ...existing code...
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.VERIFIED_OUTLINED, color=ft.colors.WHITE, size=18, opacity=0.9),
                            ft.Text(
                                "v3.0",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.colors.WHITE,
                                style=ft.TextStyle(letter_spacing=0.5)
                            )
                        ], spacing=6, alignment=ft.MainAxisAlignment.END),
                        ft.Text(
                            "INELECTRA",
                            size=11,
                            color=ft.colors.with_opacity(0.85, ft.colors.WHITE),
                            weight=ft.FontWeight.W_500,
                            style=ft.TextStyle(letter_spacing=1.2)
                        )
                    ], 
                    spacing=2, 
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.END
                    ),
                    padding=ft.padding.only(right=32),
                    alignment=ft.alignment.center_right
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            height=85,  # Altura más generosa para el logo grande
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[
                    ft.colors.with_opacity(0.85, self.colors['primary']),
                    self.colors['primary'],
                    self.colors['primary_dark']
                ]
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

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
            is_active = self.seccion_actual == section
            
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
                on_click=lambda e, s=section: self.cambiar_seccion(s),
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
        
        # Botón de salir con diseño premium
        exit_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.LOGOUT, color=ft.colors.WHITE, size=22),
                ft.Text("Salir del Sistema", color=ft.colors.WHITE, size=15, weight=ft.FontWeight.W_600)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            bgcolor=self.colors['error'],
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            margin=ft.margin.only(top=24),
            on_click=self.close_app,
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
            content=ft.Column([
                ft.Container(height=16),  # Reducido
                *buttons,
                ft.Container(height=20),  # Reducido
                exit_button,
                ft.Container(height=12)   # Reducido
            ]),
            width=320,  # Reducido ligeramente
            bgcolor=self.colors['surface'],
            padding=18,  # Padding reducido
            border_radius=15,  # Bordes menos redondeados
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 3)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border']))
        )

    def close_app(self, e):
        """Cierra la aplicación de manera segura"""
        try:
            # Intentar cerrar la ventana primero
            if self.page and hasattr(self.page, 'window_close'):
                self.page.window_close()
            # Esperar un momento y luego forzar salida
            import time
            time.sleep(0.1)
        except Exception as ex:
            print(f"Error al cerrar ventana: {ex}")
        finally:
            # Forzar salida del proceso
            try:
                sys.exit(0)
            except:
                os._exit(0)
                
    def create_content_card(self, title, content):
        """Crea una tarjeta de contenido premium con efectos modernos"""
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
                content
            ]),
            bgcolor=self.colors['surface'],
            border_radius=20,
            padding=32,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.08, ft.colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )

    def create_archivos_section(self):
        """Sección de archivos renovada con pregunta para carga manual"""
        self.archivo_plantilla = ft.TextField(
            label="📄 Plantilla Word (.docx)",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.icons.DESCRIPTION,
            value=os.path.basename(self.archivos["plantilla"]) if self.archivos["plantilla"] else ""
        )
        self.archivo_logo = ft.TextField(
            label="🖼️ Logo de la Empresa",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.icons.IMAGE,
            value=os.path.basename(self.archivos["logo"]) if self.archivos["logo"] else ""
        )
        self.archivo_excel = ft.TextField(
            label="📊 Excel Principal",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.icons.TABLE_CHART,
            value=os.path.basename(self.archivos["excel"]) if self.archivos["excel"] else ""
        )
        
        self.archivo_excel_cargas = ft.TextField(
            label="📈 Excel de Cargas",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.icons.ANALYTICS,
            value=os.path.basename(self.archivos["excel_cargas"]) if self.archivos["excel_cargas"] else ""
        )
        
        self.archivo_excel_sismo = ft.TextField(
            label="🌊 Excel de Sismo",
            read_only=True,
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            prefix_icon=ft.icons.WAVES,
            value=os.path.basename(self.archivos["excel_sismo"]) if self.archivos["excel_sismo"] else ""
        )

        # Configuración
        self.estructura_field = ft.TextField(
            label="🏗️ Nombre de la Estructura",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.config_data['estructura'],
            on_change=self.on_estructura_change
        )

        self.idioma_dropdown = ft.Dropdown(
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

        self.tipo_memoria_switch = ft.Switch(
            label="Completa",
            value=self.config_data['version'] == "completa",
            on_change=self.on_tipo_memoria_change,
            active_color=self.colors['primary'],
            thumb_color=ft.colors.WHITE,
            inactive_thumb_color=ft.colors.GREY_300,
            inactive_track_color=ft.colors.GREY_200
        )
        self.seccion8_switch = ft.Switch(
            label="Incluir deflexión horizontal",
            value=self.config_data['mostrar_seccion_8'],
            on_change=self.on_seccion8_change,
            active_color=self.colors['primary'],
            thumb_color=ft.colors.WHITE,
            inactive_thumb_color=ft.colors.GREY_300,
            inactive_track_color=ft.colors.GREY_200
        )

        return ft.Column([
            # Sección de archivos - más compacta
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📁 Archivos del Proyecto", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        
                        ft.ExpansionTile(
                            title=ft.Text("¿Desea cargar manualmente la plantilla Word y el logo?", size=13),
                            controls=[
                                ft.Container(
                                    content=ft.Row([
                                        self.archivo_plantilla,
                                        ft.ElevatedButton(
                                            "Cambiar",
                                            icon=ft.icons.FOLDER_OPEN,
                                            on_click=lambda e: self.seleccionar_archivo("plantilla"),
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
                                            icon=ft.icons.FOLDER_OPEN,
                                            on_click=lambda e: self.seleccionar_archivo("logo"),
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
                                    icon=ft.icons.FOLDER_OPEN,
                                    on_click=lambda e: self.seleccionar_archivo("excel"),
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
                                    icon=ft.icons.FOLDER_OPEN,
                                    on_click=lambda e: self.seleccionar_archivo("excel_cargas"),
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
                                    icon=ft.icons.FOLDER_OPEN,
                                    on_click=lambda e: self.seleccionar_archivo("excel_sismo"),
                                    bgcolor=self.colors['secondary'],
                                    color=ft.colors.WHITE,
                                    height=40
                                )
                            ], spacing=12)
                        )
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            ),
            
            ft.Container(height=12),  # Espacio reducido
            
            # Sección de configuración
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("⚙️ Configuración del Proyecto", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Row([
                            self.estructura_field,
                            self.idioma_dropdown
                        ], spacing=12),
                        ft.Container(height=15),
                        ft.Row([self.tipo_memoria_switch, self.seccion8_switch], spacing=25)
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll, expand para usar todo el espacio

    def create_datos_section(self):
        """Sección de datos del proyecto renovada"""
        # Crear campos del proyecto con referencias estables
        self.project_nombre = ft.TextField(
            label="NOMBRE DEL PROYECTO",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['NOMBRE DEL PROYECTO'],
            on_change=lambda e: self.update_project_data('NOMBRE DEL PROYECTO', e.control.value)
        )
        
        self.project_documento = ft.TextField(
            label="NOMBRE DEL DOCUMENTO",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['NOMBRE DEL DOCUMENTO'],
            on_change=lambda e: self.update_project_data('NOMBRE DEL DOCUMENTO', e.control.value)
        )
        
        self.project_emision = ft.TextField(
            label="Emisión",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['Emisión'],
            on_change=lambda e: self.update_project_data('Emisión', e.control.value)
        )
        
        self.project_fecha = ft.TextField(
            label="MM/DD/AAAA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['MM/DD/AAAA'],
            on_change=lambda e: self.update_project_data('MM/DD/AAAA', e.control.value)
        )
        
        self.project_dev = ft.TextField(
            label="Dev",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['Dev'],
            on_change=lambda e: self.update_project_data('Dev', e.control.value)
        )
        
        self.project_xx = ft.TextField(
            label=".: XX",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['.: XX'],
            on_change=lambda e: self.update_project_data('.: XX', e.control.value)
        )
        
        self.project_codigo_compania = ft.TextField(
            label="CODIGO COMPAÑIA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['CODIGO COMPAÑIA'],
            on_change=lambda e: self.update_project_data('CODIGO COMPAÑIA', e.control.value)
        )
        
        self.project_codigo_contratista = ft.TextField(
            label="CODIGO CONTRATISTA",
            expand=True,
            border_color=self.colors['primary'],
            focused_border_color=self.colors['secondary'],
            border_radius=12,
            value=self.project_data['CODIGO CONTRATISTA'],
            on_change=lambda e: self.update_project_data('CODIGO CONTRATISTA', e.control.value)
        )

        return ft.Column([
            # Información Principal
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📋 Información Principal", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Container(content=self.project_nombre, margin=ft.margin.only(bottom=12)),
                        ft.Container(content=self.project_documento, margin=ft.margin.only(bottom=0))
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            ),

            ft.Container(height=12),

            # Fechas y Versiones
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📅 Fechas y Versiones", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Row([self.project_emision, self.project_fecha], spacing=12),
                        ft.Container(height=12),
                        ft.Row([self.project_dev, self.project_xx], spacing=12)
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            ),

            ft.Container(height=12),

            # Códigos de Identificación
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🏢 Códigos de Identificación", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=12),
                        ft.Row([self.project_codigo_compania, self.project_codigo_contratista], spacing=12)
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll, expand para usar todo el espacio

    def create_capturas_section(self):
        """Sección de capturas renovada con scroll optimizado solo donde es necesario"""
        self.agregar_imagenes_checkbox = ft.Switch(
            label="Incluir imágenes en la memoria de cálculo",
            value=self.config_data['agregar_imagenes'],
            on_change=self.on_agregar_imagenes_change,
            active_color=self.colors['primary'],
            thumb_color=ft.colors.WHITE,
            inactive_thumb_color=ft.colors.GREY_300,
            inactive_track_color=ft.colors.GREY_200
        )

        self.lista_capturas = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.update_lista_capturas()

        self.progress_text = ft.Text(
            f"Progreso: {len(self.capturadas)}/{self.total_slots} (🤖0/{min(5, self.total_slots)} + 📷0/{max(0, self.total_slots - 5)})",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=self.colors['success'] if len(self.capturadas) == self.total_slots else self.colors['primary']
        )

        self.progress_bar = ft.ProgressBar(
            value=len(self.capturadas) / self.total_slots if self.total_slots > 0 else 0,
            color=self.colors['success'],
            bgcolor=self.colors['border'],
            height=8
        )

        # Contenedor principal sin scroll
        return ft.Column([
            # Configuración de capturas - Compacta
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("📸 Configuración de Capturas", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(expand=True),
                            self.agregar_imagenes_checkbox
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.Container(height=8),
                        
                        ft.Container(
                            content=ft.Text(
                                "💡 Las primeras 5 imágenes se cargan automáticamente desde STAAD si están disponibles.",
                                size=11,
                                color=self.colors['text_secondary'],
                                italic=True
                            ),
                            padding=ft.padding.all(8),
                            bgcolor=ft.colors.with_opacity(0.08, self.colors['primary']),
                            border_radius=6
                        ),
                        
                        ft.Container(height=12),
                        
                        ft.Row([
                            ft.ElevatedButton(
                                "📷 Nueva Captura",
                                icon=ft.icons.CAMERA_ALT,
                                on_click=self.capturar_imagen,
                                bgcolor=self.colors['secondary'],
                                color=ft.colors.WHITE,
                                height=40,
                                expand=True
                            ),
                            ft.Container(width=10),
                            ft.ElevatedButton(
                                "🗑️ Limpiar Todo",
                                icon=ft.icons.DELETE_SWEEP,
                                on_click=self.limpiar_capturas,
                                bgcolor=self.colors['warning'],
                                color=ft.colors.WHITE,
                                height=40,
                                expand=True
                            )
                        ])
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            ),

            ft.Container(height=10),

            # Progreso - Compacto
            ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text("📊 Progreso", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=5),
                            self.progress_text
                        ], expand=True),
                        ft.Container(width=20),
                        ft.Container(
                            content=self.progress_bar,
                            width=200,
                            alignment=ft.alignment.center_right
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=16
                ),
                elevation=2
            ),

            ft.Container(height=10),

            # Lista de capturas con scroll interno limitado
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("📋 Estado de las Capturas", size=16, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=10),
                        ft.Container(
                            content=self.lista_capturas,
                            height=300,  # Altura fija para que el scroll sea interno
                            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])),
                            border_radius=8,
                            padding=8
                        )
                    ]),
                    padding=16
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll aquí, expand para usar todo el espacio

    def create_generar_section(self):
        """Sección de generación renovada y compacta"""
        return ft.Column([
            # Estado del sistema
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("🚀 Generación de Memoria", size=ft.Size(18, 18), weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=10),
                        ft.Text(
                            "Verifica que todos los archivos y datos están completos antes de generar.",
                            size=13,
                            color=self.colors['text_secondary']
                        ),
                        ft.Container(height=15),
                        self.create_status_summary()
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            ),

            ft.Container(height=12),

            # Acciones de generación
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("⚡ Acciones", size=18, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                        ft.Container(height=15),
                        ft.Row([
                            ft.ElevatedButton(
                                "🔍 Validar Datos",
                                icon=ft.icons.VERIFIED,
                                on_click=self.validar_datos,
                                bgcolor=self.colors['warning'],
                                color=ft.colors.WHITE,
                                height=50,
                                expand=True
                            ),
                            ft.ElevatedButton(
                                "📄 Generar Memoria",
                                icon=ft.icons.ROCKET_LAUNCH,
                                on_click=self.generar_memoria,
                                bgcolor=self.colors['success'],
                                color=ft.colors.WHITE,
                                height=50,
                                expand=True
                            )
                        ], spacing=15)
                    ]),
                    padding=16  # Padding reducido
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll, expand para usar todo el espacio

    def create_ayuda_section(self):
        """Sección de ayuda renovada y compacta"""
        return ft.Column([
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
                    padding=16  # Padding reducido
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll, expand para usar todo el espacio

    def create_acerca_section(self):
        """Sección acerca de renovada y compacta"""
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
                    padding=20  # Padding ligeramente reducido
                ),
                elevation=2
            )
        ], spacing=0, expand=True)  # Sin scroll, expand para usar todo el espacio

    def create_status_summary(self):
        """Crea un resumen del estado del sistema"""
        # Verificar archivos
        archivos_ok = all(self.archivos.values())
        datos_ok = all(self.project_data.values())
        
        # Verificar configuración del proyecto (estructura e idioma son obligatorios)
        estructura_ok = bool(self.config_data.get('estructura', '').strip())
        idioma_ok = self.config_data.get('idioma', '').strip() in ['es', 'en']
        config_ok = estructura_ok and idioma_ok
        
        capturas_ok = len(self.capturadas) >= self.total_slots if self.config_data['agregar_imagenes'] else True
        
        # Contadores para el resumen
        campos_config_completados = sum([estructura_ok, idioma_ok])
        
        status_items = [
            ("📁 Archivos", archivos_ok, f"{sum(1 for x in self.archivos.values() if x)}/4 archivos cargados"),
            ("📝 Datos", datos_ok, f"{sum(1 for x in self.project_data.values() if x)}/8 campos completados"),
            ("⚙️ Configuración", config_ok, f"{campos_config_completados}/2 configuraciones establecidas"),
            ("📸 Capturas", capturas_ok, f"{len(self.capturadas)}/{self.total_slots} capturas realizadas")
        ]
        
        status_rows = []
        for icon_title, is_ok, description in status_items:
            color = self.colors['success'] if is_ok else self.colors['error']
            icon = ft.icons.CHECK_CIRCLE if is_ok else ft.icons.ERROR
            
            status_rows.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Text(icon_title, size=14, weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(description, size=12, color=self.colors['text_secondary'])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=8, horizontal=15),
                    bgcolor=ft.colors.with_opacity(0.1, color),
                    border_radius=8,
                    margin=ft.margin.only(bottom=8)
                )
            )
        
        return ft.Column(status_rows, spacing=0)

    def setup_ui(self):
        """Configura la interfaz de usuario con diseño optimizado sin scroll innecesario"""
        header = self.create_modern_header()
        sidebar = self.create_sidebar_menu()
        
        # Guardar referencia para resize
        self.current_sidebar = sidebar
        
        self.main_content = ft.Container(
            content=self.get_current_section_content(),
            expand=True,
            padding=8,
            alignment=ft.alignment.top_left,
            bgcolor=self.colors['surface'],
            border_radius=10,
            margin=0,
            width=None,
            height=None,
        )
        
        # Footer elegante con el mismo estilo del header
        footer = ft.Container(
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
            padding=ft.padding.symmetric(horizontal=32, vertical=16),  # Mismo padding del header
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
                blur_radius=12,  # Misma sombra del header
                color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
                offset=ft.Offset(0, -2)  # Sombra hacia arriba
            ),
            height=70,  # Altura definida similar al header
            alignment=ft.alignment.center
        )
        
        # Layout principal responsivo y con footer fijo
        main_layout = ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=ft.Row([
                        sidebar,
                        ft.Container(width=8),
                        self.main_content
                    ], expand=True, alignment=ft.MainAxisAlignment.START, spacing=0),
                    expand=True,
                    padding=8,
                    alignment=ft.alignment.top_left,
                ),
                footer
            ],
                expand=True,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=0,
            ),
            bgcolor=self.colors['background'],
            border_radius=10,
            margin=0,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=18,
                color=ft.colors.with_opacity(0.10, ft.colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )
        self.page.add(main_layout)
        self.page.update()

    def get_current_section_content(self):
        """Obtiene el contenido de la sección actual"""
        content_map = {
            "archivos": self.create_archivos_section(),
            "datos": self.create_datos_section(),
            "capturas": self.create_capturas_section(),
            "generar": self.create_generar_section(),
            "ayuda": self.create_ayuda_section(),
            "acerca": self.create_acerca_section()
        }
        
        content = content_map.get(self.seccion_actual, self.create_archivos_section())
        title = {
            "archivos": "📁 Gestión de Archivos",
            "datos": "📝 Datos del Proyecto", 
            "capturas": "📸 Capturas de Pantalla",
            "generar": "🚀 Generar Memoria",
            "ayuda": "❓ Ayuda del Sistema",
            "acerca": "ℹ️ Acerca del Software"
        }.get(self.seccion_actual, "📁 Gestión de Archivos")
        
        return self.create_content_card(title, content)

    def cambiar_seccion(self, nueva_seccion):
        """Cambia la sección actual"""
        if nueva_seccion != self.seccion_actual:
            self.seccion_actual = nueva_seccion
            
            # Actualizar contenido principal
            self.main_content.content = self.get_current_section_content()
            
            # Recrear sidebar para actualizar estado activo
            sidebar = self.create_sidebar_menu()
            
            # Actualizar la referencia para responsividad
            self.current_sidebar = sidebar
            
            # Actualizar la página
            self.page.controls[0].content.controls[1].content.controls[0] = sidebar
            self.page.update()

    def seleccionar_archivo(self, tipo_archivo):
        """Selecciona un archivo del tipo especificado - VERSIÓN MEJORADA Y CORREGIDA"""
        self.archivo_key_actual = tipo_archivo

        # Caso especial para Excel principal: buscar primero en la carpeta del proyecto STAAD
        if tipo_archivo == "excel":
            excel_path = encontrar_excel_entre_los_archivos_donde_esta_el_std()
            if excel_path and os.path.exists(excel_path):
                self.archivos["excel"] = excel_path
                if hasattr(self, 'archivo_excel'):
                    self.archivo_excel.value = os.path.basename(excel_path)
                    self.page.update()
                    self.mostrar_mensaje(f"✅ {os.path.basename(excel_path)} cargado automáticamente desde el proyecto STAAD", "success")
                    self.archivo_key_actual = None
                    return
            else:
                print("[INFO] No se encontró el Excel principal en la carpeta del STAAD. El usuario debe seleccionarlo manualmente.")

        # Si el archivo ya está definido por variable de entorno, usarlo directamente (solo para plantilla y logo)
        env_map = {
            "plantilla": os.getenv("TEMPLATE_PATH", None),
            "logo": os.getenv("LOGO_PATH", None),
        }
        if tipo_archivo in env_map and env_map[tipo_archivo] and os.path.exists(env_map[tipo_archivo]):
            self.archivos[tipo_archivo] = env_map[tipo_archivo]
            # Actualizar el campo correspondiente en la UI
            field_map = {
                "plantilla": getattr(self, 'archivo_plantilla', None),
                "logo": getattr(self, 'archivo_logo', None),
            }
            field = field_map.get(tipo_archivo)
            if field:
                field.value = os.path.basename(env_map[tipo_archivo]) + " (por defecto .env)"
                self.page.update()
                self.mostrar_mensaje(f"✅ {os.path.basename(env_map[tipo_archivo])} cargado por defecto desde .env", "info")
                self.archivo_key_actual = None
                return

        # Si no se encontró, pedirlo al usuario
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
                allowed_extensions=["xlsx", "xls"],
                allow_multiple=False
            )
        else:
            # Fallback para cualquier archivo
            self.picker.pick_files(
                dialog_title=f"Seleccionar {tipo_archivo}",
                allow_multiple=False
            )

    def on_file_selected(self, e: ft.FilePickerResultEvent):
        """Maneja la selección de archivos - VERSIÓN MEJORADA"""
        if not e.files:
            self.mostrar_mensaje("❌ No se seleccionó ningún archivo", "warning")
            return
            
        if not self.archivo_key_actual:
            self.mostrar_mensaje("❌ Error interno: tipo de archivo no definido", "error")
            return
        
        try:
            archivo_seleccionado = e.files[0]
            archivo_path = archivo_seleccionado.path
            archivo_nombre = archivo_seleccionado.name
            
            # Validar que el archivo existe
            if not os.path.exists(archivo_path):
                self.mostrar_mensaje("❌ El archivo seleccionado no existe", "error")
                return
            
            # Validar extensión según tipo
            extension = os.path.splitext(archivo_nombre)[1].lower()
            
            validaciones = {
                "plantilla": [".docx"],
                "logo": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
                "excel": [".xlsx", ".xls"],
                "excel_cargas": [".xlsx", ".xls"],
                "excel_sismo": [".xlsx", ".xls"]
            }
            
            if self.archivo_key_actual in validaciones:
                extensiones_validas = validaciones[self.archivo_key_actual]
                if extension not in extensiones_validas:
                    self.mostrar_mensaje(
                        f"❌ Extensión no válida. Se esperaba: {', '.join(extensiones_validas)}", 
                        "error"
                    )
                    return
            
            # Guardar la ruta del archivo
            self.archivos[self.archivo_key_actual] = archivo_path
            
            # Actualizar el campo correspondiente en la UI
            field_map = {
                "plantilla": getattr(self, 'archivo_plantilla', None),
                "logo": getattr(self, 'archivo_logo', None),
                "excel": getattr(self, 'archivo_excel', None),
                "excel_cargas": getattr(self, 'archivo_excel_cargas', None),
                "excel_sismo": getattr(self, 'archivo_excel_sismo', None)
            }
            
            field = field_map.get(self.archivo_key_actual)
            if field:
                field.value = archivo_nombre
            
            # Actualizar la página
            self.page.update()
            
            # Mostrar mensaje de éxito
            self.mostrar_mensaje(f"✅ {archivo_nombre} cargado correctamente", "success")
            
            # Limpiar la referencia
            self.archivo_key_actual = None
            
        except Exception as ex:
            self.mostrar_mensaje(f"❌ Error al procesar archivo: {str(ex)}", "error")
            self.archivo_key_actual = None

    def on_estructura_change(self, e):
        """Maneja cambios en el nombre de la estructura"""
        self.config_data['estructura'] = e.control.value

    def on_idioma_change(self, e):
        """Maneja cambios en el idioma"""
        self.config_data['idioma'] = e.control.value
        self.idioma = e.control.value

    def on_tipo_memoria_change(self, e):
        self.config_data['version'] = "completa" if e.control.value else "simple"
        self.version = self.config_data['version']
        self.total_slots = 29 if self.version == "completa" else 6
        self.update_lista_capturas()
        self.page.update()

    def on_seccion8_change(self, e):
        """Maneja cambios en la sección 8"""
        self.config_data['mostrar_seccion_8'] = e.control.value
        self.mostrar_seccion_8 = e.control.value

    def on_agregar_imagenes_change(self, e):
        """Maneja cambios en agregar imágenes"""
        self.config_data['agregar_imagenes'] = e.control.value
        self.update_lista_capturas()
        self.page.update()

    def update_project_data(self, key, value):
        """Actualiza los datos del proyecto"""
        self.project_data[key] = value

    def capturar_imagen(self, e):
        """Inicia el proceso de captura de imagen"""
        try:
            # Verificar qué slots están disponibles para captura manual
            slots_faltantes = []
            for slot_num in range(1, self.total_slots + 1):
                if slot_num not in self.capturadas:
                    slots_faltantes.append(slot_num)
            
            if not slots_faltantes:
                self.mostrar_mensaje("✅ Ya tienes todas las capturas necesarias", "info")
                return
            
            # Mostrar información sobre qué slot se está capturando
            primer_slot_faltante = slots_faltantes[0]
            descripcion_slot = SLOTS_ORDENADOS.get(primer_slot_faltante, f"Slot {primer_slot_faltante}")
            
            # Minimizar ventana temporalmente
            self.page.window_minimized = True
            self.page.update()
                        
            # Realizar captura
            screenshot_path = select_region_and_save()
            
            # Restaurar ventana
            self.page.window_minimized = False
            self.page.update()
            
            if screenshot_path and os.path.exists(screenshot_path):
                # Asignar al primer slot disponible
                self.capturadas[primer_slot_faltante] = screenshot_path
                self.update_lista_capturas()
                self.mostrar_mensaje(f"✅ Captura {primer_slot_faltante} guardada: {descripcion_slot}", "success")
            else:
                self.mostrar_mensaje("❌ Error al realizar la captura", "error")
                
        except Exception as ex:
            self.page.window_minimized = False
            self.page.update()
            self.mostrar_mensaje(f"❌ Error en captura: {str(ex)}", "error")

    def eliminar_captura(self, slot_num):
        """Elimina una captura específica"""
        if slot_num in self.capturadas:
            try:
                # Eliminar archivo físico si existe
                if os.path.exists(self.capturadas[slot_num]):
                    os.remove(self.capturadas[slot_num])
                
                # Eliminar de la lista
                del self.capturadas[slot_num]
                self.update_lista_capturas()
                self.mostrar_mensaje(f"✅ Captura {slot_num} eliminada", "success")
                
            except Exception as ex:
                self.mostrar_mensaje(f"❌ Error al eliminar: {str(ex)}", "error")

    def limpiar_capturas(self, e):
        """Limpia todas las capturas"""
        def confirmar_limpieza(e):
            try:
                # Eliminar archivos físicos
                for path in self.capturadas.values():
                    if os.path.exists(path):
                        os.remove(path)
                
                # Limpiar diccionario
                self.capturadas.clear()
                self.update_lista_capturas()
                self.mostrar_mensaje("✅ Todas las capturas han sido eliminadas", "success")
                
            except Exception as ex:
                self.mostrar_mensaje(f"❌ Error al limpiar: {str(ex)}", "error")
            
            dialog.open = False
            self.page.update()

        def cancelar_limpieza(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Confirmar limpieza"),
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

    def update_lista_capturas(self):     
        """Actualiza la lista visual de capturas"""
        if not hasattr(self, 'lista_capturas'):
            return
            
        self.lista_capturas.controls.clear()
        
        if not self.config_data['agregar_imagenes']:
            self.lista_capturas.controls.append(
                ft.Container(
                    content=ft.Text(
                        "📝 Las imágenes están deshabilitadas en la configuración",
                        size=14,
                        color=self.colors['text_secondary'],
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                    border_radius=8,
                    bgcolor=ft.colors.with_opacity(0.1, self.colors['warning'])
                )
            )
        else:
            # Mostrar slots según la versión
            slots_a_mostrar = SLOTS_ORDENADOS if self.total_slots == len(SLOTS_ORDENADOS) else {k: v for k, v in list(SLOTS_ORDENADOS.items())[:self.total_slots]}
            
            for slot_num, descripcion in slots_a_mostrar.items():
                capturada = slot_num in self.capturadas
                
                # Determinar si es una imagen automática (slots 1-5 solamente)
                es_automatica = slot_num <= 5
                
                # Color e icono según estado
                if capturada:
                    if es_automatica:
                        color = self.colors['primary']  # Azul para automáticas
                        icon = ft.icons.AUTO_AWESOME
                        estado_text = "🤖 Automática"
                        action_button = ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=self.colors['error'],
                            tooltip="Eliminar captura",
                            on_click=lambda e, s=slot_num: self.eliminar_captura(s)
                        )
                    else:
                        color = self.colors['success']  # Verde para manuales
                        icon = ft.icons.CHECK_CIRCLE
                        estado_text = "✅ Manual"
                        action_button = ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=self.colors['error'],
                            tooltip="Eliminar captura",
                            on_click=lambda e, s=slot_num: self.eliminar_captura(s)
                        )
                else:
                    color = self.colors['error']
                    icon = ft.icons.RADIO_BUTTON_UNCHECKED
                    if es_automatica:
                        estado_text = "⚠️ Disponible auto"
                    else:
                        estado_text = "❌ Captura manual"
                    action_button = ft.Container()

                slot_card = ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=20),
                        ft.Column([
                            ft.Text(f"Slot {slot_num}", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(descripcion, size=11, color=self.colors['text_secondary'])
                        ], spacing=2, expand=True),
                        ft.Text(estado_text, size=12, color=color),
                        action_button
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    margin=ft.margin.only(bottom=5),
                    bgcolor=ft.colors.with_opacity(0.05, color),
                    border_radius=8,
                    border=ft.border.all(1, ft.colors.with_opacity(0.2, color))
                )
                
                self.lista_capturas.controls.append(slot_card)
        # Actualizar progreso
        if hasattr(self, 'progress_text') and hasattr(self, 'progress_bar'):
            # Contar automáticas vs manuales (solo 5 automáticas disponibles)
            automaticas = sum(1 for slot in self.capturadas.keys() if slot <= 5)
            manuales = sum(1 for slot in self.capturadas.keys() if slot > 5)
            total_automaticas_posibles = min(5, self.total_slots)  # Máximo 5 automáticas
            total_manuales_posibles = max(0, self.total_slots - 5)  # El resto son manuales
            
            progress_text = f"Progreso: {len(self.capturadas)}/{self.total_slots} "
            if total_automaticas_posibles > 0:
                progress_text += f"(🤖{automaticas}/{total_automaticas_posibles}"
                if total_manuales_posibles > 0:
                    progress_text += f" + 📷{manuales}/{total_manuales_posibles})"
                else:
                    progress_text += ")"
            else:
                progress_text += f"(📷{manuales}/{total_manuales_posibles})"
            
            self.progress_text.value = progress_text
            self.progress_text.color = self.colors['success'] if len(self.capturadas) == self.total_slots else self.colors['primary']
            self.progress_bar.value = len(self.capturadas) / self.total_slots if self.total_slots > 0 else 0
   
    def validar_datos(self, e=None):
        """Valida que todos los datos estén completos"""
        errores = []
        
        # Validar archivos requeridos
        archivos_requeridos = ["plantilla", "excel"]
        for archivo in archivos_requeridos:
            if not self.archivos[archivo]:
                errores.append(f"❌ Falta seleccionar el archivo: {archivo.upper()}")
            elif not os.path.exists(self.archivos[archivo]):
                errores.append(f"❌ No se encuentra el archivo: {archivo.upper()} en la ruta: {self.archivos[archivo]}")
        
        # Validar todos los campos del proyecto con nombres más descriptivos
        campos_requeridos = {
            'NOMBRE DEL PROYECTO': 'Nombre del Proyecto',
            'Emisión': 'Número de Emisión',
            'MM/DD/AAAA': 'Fecha (MM/DD/AAAA)',
            'NOMBRE DEL DOCUMENTO': 'Nombre del Documento',
            'Dev': 'Desarrollado por (Dev)',
            '.: XX': 'Número de Revisión (.: XX)',
            'CODIGO COMPAÑIA': 'Código de Compañía',
            'CODIGO CONTRATISTA': 'Código de Contratista'
        }
        
        for campo_key, campo_nombre in campos_requeridos.items():
            valor = self.project_data.get(campo_key, "").strip()
            if not valor:
                errores.append(f"❌ Falta completar: {campo_nombre}")
        
        # Validar configuración del proyecto - AMBOS CAMPOS SON OBLIGATORIOS
        if not self.config_data.get('estructura', '').strip():
            errores.append("❌ Falta especificar el nombre de la estructura en Configuración del Proyecto")
        
        # Validar idioma - también es obligatorio
        idioma_actual = self.config_data.get('idioma', '').strip()
        if not idioma_actual or idioma_actual not in ['es', 'en']:
            errores.append("❌ Debe seleccionar un idioma válido (Español o Inglés) en Configuración del Proyecto")
        
        # Validar capturas si están habilitadas
        if self.config_data.get('agregar_imagenes', True):
            capturas_requeridas = self.total_slots
            capturas_actuales = len(self.capturadas)
            if capturas_actuales < capturas_requeridas:
                errores.append(f"❌ Faltan capturas de imágenes: {capturas_actuales}/{capturas_requeridas} completadas")
        
        # Mostrar resultado con notificaciones mejoradas
        if errores:
            mensaje_detallado = f"""⚠️ Se encontraron {len(errores)} elemento(s) pendiente(s) para completar:

{chr(10).join(errores)}

📋 Por favor complete todos los campos marcados antes de generar la memoria de cálculo."""
            
            self.mostrar_dialogo("📋 Validación Incompleta", mensaje_detallado, "warning")
            self.mostrar_mensaje(f"⚠️ Faltan {len(errores)} elemento(s) por completar. Revise la lista de pendientes.", "warning", 5000)
            return False
        else:
            mensaje_exito = """✅ Validación exitosa - Todos los datos están completos

🎯 Elementos validados correctamente:
• Archivos requeridos (plantilla y Excel)
• Datos del proyecto (8/8 campos)
• Configuración del proyecto (estructura e idioma)
• Imágenes requeridas

El sistema está listo para generar la memoria de cálculo."""
            
            self.mostrar_dialogo("✅ Validación Exitosa", mensaje_exito, "success")
            self.mostrar_mensaje("✅ Validación completada. Todos los requisitos han sido cumplidos.", "success", 4000)
            return True

    def generar_memoria(self, e):
        """Genera la memoria de cálculo con sistema de notificaciones simplificado y garantizado"""
        import threading
        import time
        
        print("🔍 DEBUG: Función generar_memoria iniciada")
        
        # Validar datos primero
        if not self.validar_datos():
            print("🔍 DEBUG: Validación falló")
            self.crear_notificacion_flotante("❌ Validación incompleta. Complete todos los campos requeridos.", "error")
            return
        
        print("🔍 DEBUG: Validación exitosa")
        # Mostrar notificación de progreso central
        self.mostrar_notificacion_progreso("Iniciando generación de memoria de cálculo...")
        
        # Crear componentes de progreso simples
        self.progress_text = ft.Text(
            "Preparando generación...",
            size=16,
            color=self.colors['text_primary'],
            text_align=ft.TextAlign.CENTER
        )
        
        self.progress_bar = ft.ProgressBar(
            color=self.colors['primary'],
            bgcolor=ft.colors.with_opacity(0.2, self.colors['primary']),
            height=8,
            value=0
        )
        
        # Crear diálogo simple y robusto
        self.progress_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.BUILD, size=50, color=self.colors['primary']),
                        alignment=ft.alignment.center
                    ),
                    ft.Container(height=15),
                    ft.Text(
                        "Generando Memoria de Cálculo", 
                        size=18, 
                        weight=ft.FontWeight.BOLD, 
                        color=self.colors['text_primary'],
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    self.progress_text,
                    ft.Container(height=15),
                    self.progress_bar
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5),
                padding=40,
                width=450,
                height=280
            ),
            actions=[],
            bgcolor=self.colors['surface']
        )
        
        # Mostrar diálogo
        self.page.dialog = self.progress_dialog
        self.progress_dialog.open = True
        self.page.update()
        
        print("🔍 DEBUG: Diálogo mostrado")
        
        def ejecutar_generacion():
            """Función que ejecuta la generación en segundo plano"""
            start_time = time.time()
            
            try:
                print("🔍 DEBUG: Iniciando generación en hilo separado")
                
                # Inicializar COM
                pythoncom.CoInitialize()
                
                # Actualizar progreso
                self.actualizar_progreso(0.1, "Preparando archivos...", "Configurando componentes del sistema")
                
                # Preparar imágenes
                imagenes_preparadas = {}
                if self.config_data.get('agregar_imagenes', True):
                    for slot_num, ruta_imagen in self.capturadas.items():
                        if os.path.exists(ruta_imagen):
                            imagenes_preparadas[slot_num] = ruta_imagen
                
                self.actualizar_progreso(0.2, "Configurando rutas...", "Procesando archivos de entrada")
                
                # Nombre del archivo
                nombre_archivo = get_project_name()
                if nombre_archivo:
                    nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
                    nombre_archivo = f"{nombre_sin_extension}.docx"
                else:
                    nombre_archivo = "memoria_de_calculo.docx"
                
                ruta_salida = salida()
                ruta_completa_salida = os.path.join(ruta_salida, nombre_archivo)
                
                self.actualizar_progreso(0.3, "Iniciando generación...", "Ejecutando motor de documentos")
                
                # Parámetros
                parametros = {
                    'plantilla_path': self.archivos["plantilla"],
                    'logo_path': self.archivos.get("logo", ""),
                    'excel_file_path': self.archivos["excel"],
                    'excel_file_path_cargas': self.archivos.get("excel_cargas", ""),
                    'estructura': self.config_data['estructura'],
                    'idioma': self.config_data['idioma'],
                    'version': self.config_data['version'],
                    'mostrar_seccion_8': self.config_data['mostrar_seccion_8'],
                    'tomar_imagenes': "s" if self.config_data['agregar_imagenes'] else "n",
                    'reemplazos': self.project_data.copy(),
                    'output_path': ruta_completa_salida,
                    'image_slots': imagenes_preparadas,
                    'progress_callback': self.callback_progreso_memoria
                }
                
                print("🔍 DEBUG: Llamando crear_memoria_de_calculo")
                resultado = crear_memoria_de_calculo(**parametros)
                print(f"🔍 DEBUG: Resultado: {resultado}")
                
                # CORRECCIÓN: Si resultado es None pero vemos "✅ Documento guardado" en consola, es éxito
                if resultado is None:
                    # Verificar si el archivo se creó exitosamente
                    if os.path.exists(ruta_completa_salida):
                        print("🔍 DEBUG: Archivo existe, considerando como éxito")
                        resultado = {
                            'success': True,
                            'output_path': ruta_completa_salida,
                            'stats': 'Proceso completado exitosamente'
                        }
                    else:
                        print("🔍 DEBUG: Archivo no existe, considerando como error")
                        resultado = {
                            'success': False,
                            'error': 'El archivo no se generó correctamente'
                        }
                elif not isinstance(resultado, dict):
                    # Si no es un diccionario, crear uno basado en el tipo de resultado
                    if resultado:
                        resultado = {
                            'success': True,
                            'output_path': ruta_completa_salida,
                            'stats': 'Proceso completado'
                        }
                    else:
                        resultado = {
                            'success': False,
                            'error': 'Error desconocido en la generación'
                        }
                
                elapsed = time.time() - start_time
                
                # Cerrar diálogo
                print("🔍 DEBUG: Cerrando diálogo de progreso")
                self.cerrar_dialogo_progreso()
                
                # Mostrar resultado con sistema garantizado
                print("🔍 DEBUG: Mostrando resultado final")
                if resultado.get('success', False):
                    print("🔍 DEBUG: Resultado exitoso - mostrando notificaciones de éxito")
                    self.mostrar_resultado_final_garantizado(
                        exito=True,
                        archivo=nombre_archivo,
                        ruta=os.path.dirname(ruta_completa_salida),
                        tiempo=elapsed
                    )
                else:
                    error_msg = resultado.get('error', 'Error desconocido')
                    print(f"🔍 DEBUG: Resultado con error - mostrando notificaciones de error: {error_msg}")
                    self.mostrar_resultado_final_garantizado(
                        exito=False,
                        error=error_msg,
                        tiempo=elapsed
                    )
                
            except Exception as ex:
                print(f"🔍 DEBUG: Error en generación: {ex}")
                elapsed = time.time() - start_time
                print("🔍 DEBUG: Cerrando diálogo por error")
                self.cerrar_dialogo_progreso()
                print("🔍 DEBUG: Mostrando notificaciones de error crítico")
                self.mostrar_resultado_final_garantizado(
                    exito=False,
                    error=str(ex),
                    tiempo=elapsed,
                    critico=True
                )
            
            finally:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass
        
        # Ejecutar en hilo separado
        print("🔍 DEBUG: Iniciando hilo")
        threading.Thread(target=ejecutar_generacion, daemon=True).start()
        
    def crear_dialogo_progreso_moderno(self):
        """Crea un diálogo de progreso moderno y profesional"""
        # Texto de progreso principal
        self.progress_text = ft.Text(
            "Preparando generación...",
            size=16,
            color=self.colors['text_primary'],
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500
        )
        
        # Texto de subtarea
        self.progress_subtitle = ft.Text(
            "Inicializando sistema...",
            size=12,
            color=self.colors['text_secondary'],
            text_align=ft.TextAlign.CENTER,
            italic=True
        )
        
        # Barra de progreso moderna
        self.progress_bar = ft.ProgressBar(
            color=self.colors['primary'],
            bgcolor=ft.colors.with_opacity(0.1, self.colors['primary']),
            height=6,
            value=0,
            border_radius=0  # Bordes cuadrados para consistencia
        )
        
        # Indicador de porcentaje
        self.progress_percentage = ft.Text(
            "0%",
            size=14,
            color=self.colors['primary'],
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )
        
        # Crear icono animado (spinner)
        self.progress_icon = ft.Container(
            content=ft.ProgressRing(
                width=50,
                height=50,
                stroke_width=4,
                color=self.colors['primary'],
                bgcolor=ft.colors.with_opacity(0.1, self.colors['primary'])
            ),
            alignment=ft.alignment.center
        )
        
        # Contenedor principal del diálogo
        self.dialog_content = ft.Container(
            content=ft.Column([
                # Icono animado
                self.progress_icon,
                ft.Container(height=20),
                
                # Título principal
                ft.Text(
                    "Generando Memoria de Cálculo", 
                    size=20, 
                    weight=ft.FontWeight.BOLD, 
                    color=self.colors['text_primary'],
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),
                
                # Descripción
                ft.Text(
                    "El sistema está procesando los datos y generando el documento...",
                    size=13,
                    color=self.colors['text_secondary'],
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2
                ),
                ft.Container(height=25),
                
                # Estado actual
                self.progress_text,
                ft.Container(height=5),
                self.progress_subtitle,
                ft.Container(height=20),
                
                # Barra de progreso con porcentaje
                ft.Column([
                    ft.Row([
                        ft.Container(expand=True),
                        self.progress_percentage
                    ]),
                    ft.Container(height=8),
                    self.progress_bar
                ], spacing=0),
                
                ft.Container(height=20),
                
                # Información adicional
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.INFO_OUTLINED,
                            size=16,
                            color=self.colors['primary']
                        ),
                        ft.Container(width=8),
                        ft.Text(
                            "Este proceso puede tomar unos momentos...",
                            size=11,
                            color=self.colors['text_secondary'],
                            italic=True
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.all(12),
                    bgcolor=ft.colors.with_opacity(0.05, self.colors['primary']),
                    border_radius=0,  # Bordes cuadrados
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['primary']))
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=40,
        width=500,
        height=380,
        bgcolor=self.colors['surface'],
        border_radius=0,  # Bordes cuadrados para consistencia
        border=ft.border.all(2, ft.Colors.with_opacity(0.1, self.colors['primary'])),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=25,
            color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
            offset=ft.Offset(0, 10)
        )
    )
    
    def actualizar_progreso(self, progreso, texto_principal, texto_secundario=""):
        """Actualiza el progreso del diálogo moderno"""
        try:
            if hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.value = progreso
                
            if hasattr(self, 'progress_text') and self.progress_text:
                self.progress_text.value = texto_principal
                
            if hasattr(self, 'progress_subtitle') and self.progress_subtitle:
                self.progress_subtitle.value = texto_secundario
                
            if hasattr(self, 'progress_percentage') and self.progress_percentage:
                self.progress_percentage.value = f"{int(progreso * 100)}%"
                
            if self.page:
                self.page.update()
                
        except Exception as ex:
            print(f"Error actualizando progreso: {ex}")

    def crear_dialogo_progreso(self):
        """Crea un diálogo de progreso moderno y profesional"""
        # Texto de progreso principal
        self.progress_text = ft.Text(
            "Preparando generación...",
            size=16,
            color=self.colors['text_primary'],
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_500
        )
        
        # Texto de subtarea
        self.progress_subtitle = ft.Text(
            "Inicializando sistema...",
            size=12,
            color=self.colors['text_secondary'],
            text_align=ft.TextAlign.CENTER,
            italic=True
        )
        
        # Barra de progreso moderna
        self.progress_bar = ft.ProgressBar(
            color=self.colors['primary'],
            bgcolor=ft.colors.with_opacity(0.1, self.colors['primary']),
            height=6,
            value=0,
            border_radius=0  # Bordes cuadrados para consistencia
        )
        
        # Indicador de porcentaje
        self.progress_percentage = ft.Text(
            "0%",
            size=14,
            color=self.colors['primary'],
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER
        )
        
        # Crear icono animado (spinner)
        self.progress_icon = ft.Container(
            content=ft.ProgressRing(
                width=50,
                height=50,
                stroke_width=4,
                color=self.colors['primary'],
                bgcolor=ft.colors.with_opacity(0.1, self.colors['primary'])
            ),
            alignment=ft.alignment.center
        )
        
        # Contenedor principal del diálogo
        self.dialog_content = ft.Container(
            content=ft.Column([
                # Icono animado
                self.progress_icon,
                ft.Container(height=20),
                
                # Título principal
                ft.Text(
                    "Generando Memoria de Cálculo", 
                    size=20, 
                    weight=ft.FontWeight.BOLD, 
                    color=self.colors['text_primary'],
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),
                
                # Descripción
                ft.Text(
                    "El sistema está procesando los datos y generando el documento...",
                    size=13,
                    color=self.colors['text_secondary'],
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2
                ),
                ft.Container(height=25),
                
                # Estado actual
                self.progress_text,
                ft.Container(height=5),
                self.progress_subtitle,
                ft.Container(height=20),
                
                # Barra de progreso con porcentaje
                ft.Column([
                    ft.Row([
                        ft.Container(expand=True),
                        self.progress_percentage
                    ]),
                    ft.Container(height=8),
                    self.progress_bar
                ], spacing=0),
                
                ft.Container(height=20),
                
                # Información adicional
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.INFO_OUTLINED,
                            size=16,
                            color=self.colors['primary']
                        ),
                        ft.Container(width=8),
                        ft.Text(
                            "Este proceso puede tomar unos momentos...",
                            size=11,
                            color=self.colors['text_secondary'],
                            italic=True
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.all(12),
                    bgcolor=ft.colors.with_opacity(0.05, self.colors['primary']),
                    border_radius=0,  # Bordes cuadrados
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['primary']))
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        padding=40,
        width=500,
        height=380,
        bgcolor=self.colors['surface'],
        border_radius=0,  # Bordes cuadrados para consistencia
        border=ft.border.all(2, ft.colors.with_opacity(0.1, self.colors['primary'])),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=25,
            color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
            offset=ft.Offset(0, 10)
        )
    )

    def mostrar_resultado_final_garantizado(self, exito, archivo=None, ruta=None, tiempo=None, error=None, critico=False):
        """Muestra el resultado final de la generación con notificaciones garantizadas"""
        try:
            if exito:
                mensaje_exito = f"""✅ Memoria de cálculo generada exitosamente

📂 Archivo: {archivo}
📍 Ruta: {ruta}
⏱️ Tiempo de generación: {tiempo:.2f} segundos

El archivo ha sido guardado en la ubicación especificada. Puede abrirlo directamente desde el explorador de archivos o desde la carpeta de salida del proyecto."""
                
                self.mostrar_dialogo("✅ Generación Completa", mensaje_exito, "success")
                # Mostrar notificación central de éxito con botón para abrir archivo
                ruta_completa = os.path.join(ruta, archivo) if ruta and archivo else None
                self.mostrar_notificacion_exito(
                    f"Memoria de cálculo generada exitosamente\n📂 {archivo}",
                    ruta_archivo=ruta_completa
                )
            else:
                mensaje_error = f"""❌ Error en la generación de la memoria

Detalles del error:
{error}

Por favor revise los detalles y vuelva a intentar la generación. Asegúrese de que todos los archivos y datos estén correctos."""
                
                if critico:
                    mensaje_error = "🚨 " + mensaje_error
                
                self.mostrar_dialogo("❌ Error en la Generación", mensaje_error, "error")
                self.crear_notificacion_flotante("❌ Error en la generación", "error")
        
        except Exception as ex:
            print(f"Error mostrando resultado final: {ex}")
            self.crear_notificacion_flotante("Error al mostrar el resultado final", "error")

    def mostrar_dialogo(self, titulo, contenido, tipo="info"):
        """Muestra un diálogo simple con título y contenido"""
        try:
            icono = {
                "info": ft.icons.INFO_OUTLINE,
                "success": ft.icons.CHECK_CIRCLE_OUTLINE,
                "error": ft.icons.ERROR_OUTLINE,
                "warning": ft.icons.WARNING
            }.get(tipo, ft.icons.INFO_OUTLINE)
            
            color = {
                "info": self.colors['primary'],
                "success": self.colors['success'],
                "error": self.colors['error'],
                "warning": self.colors['warning']
            }.get(tipo, self.colors['primary'])
            
            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Row([
                    ft.Icon(icono, color=color, size=30),
                    ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD)
                ]),
                content=ft.Text(contenido, size=14),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda e: dialogo.close())
                ],
                bgcolor=self.colors['surface'],
                border_radius=10,
                border=ft.border.all(1, color),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                )
            )
            
            self.page.dialog = dialogo
            dialogo.open = True
            self.page.update()
            
        except Exception as ex:
            print(f"Error mostrando diálogo: {ex}")

    def mostrar_mensaje(self, texto, tipo="info", duracion=4000):
        """Sistema de notificaciones premium con diseño moderno"""
        # Mapeo de colores y iconos más sofisticado
        notification_config = {
            "success": {
                "color": self.colors['success'],
                "icon": ft.icons.CHECK_CIRCLE_ROUNDED,
                "bg_color": ft.colors.with_opacity(0.95, self.colors['success'])
            },
            "error": {
                "color": self.colors['error'],
                "icon": ft.icons.ERROR_ROUNDED,
                "bg_color": ft.colors.with_opacity(0.95, self.colors['error'])
            },
            "warning": {
                "color": self.colors['warning'],
                "icon": ft.icons.WARNING_ROUNDED,
                "bg_color": ft.colors.with_opacity(0.95, self.colors['warning'])
            },
            "info": {
                "color": self.colors['primary'],
                "icon": ft.icons.INFO_ROUNDED,
                "bg_color": ft.colors.with_opacity(0.95, self.colors['primary'])
            }
        }
        
        config = notification_config.get(tipo, notification_config["info"])
        
        # Crear notificación premium con glassmorphism
        notification_content = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(
                        config["icon"], 
                        color=ft.colors.WHITE, 
                        size=24
                    ),
                    width=40,
                    height=40,
                    bgcolor=ft.colors.with_opacity(0.2, ft.colors.WHITE),
                    border_radius=20,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    content=ft.Text(
                        texto,
                        color=ft.colors.WHITE,
                        size=15,
                        weight=ft.FontWeight.W_500,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    expand=True,
                    padding=ft.padding.only(left=12, right=8)
                )
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=config["bg_color"],
            border_radius=16,
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.colors.with_opacity(0.3, config["color"]),
                offset=ft.Offset(0, 8)
            ),
            border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.WHITE)),
            animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
        
        snackbar = ft.SnackBar(
            content=notification_content,
            bgcolor=ft.Colors.TRANSPARENT,
            duration=duracion,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=ft.margin.all(20),
            padding=ft.padding.all(0),
            shape=ft.RoundedRectangleBorder(radius=16)
        )
        
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

    def crear_notificacion_flotante(self, mensaje, tipo="info", duracion=4000, mostrar_boton_archivo=False, ruta_archivo=None):
        """Crea una notificación central con overlay para enfocar la atención del usuario"""
        try:
            print(f"🔔 Creando notificación central: {tipo} - {mensaje}")
            
            # Configuración de colores e iconos
            configuracion = {
                "success": {
                    "color": self.colors['success'],
                    "icon": ft.Icons.CHECK_CIRCLE_ROUNDED,
                    "bg_color": "#4CAF50",
                    "accent_color": "#45A049"
                },
                "error": {
                    "color": self.colors['error'],
                    "icon": ft.Icons.ERROR_ROUNDED,
                    "bg_color": "#F44336",
                    "accent_color": "#E53935"
                },
                "warning": {
                    "color": self.colors['warning'],
                    "icon": ft.Icons.WARNING_ROUNDED,
                    "bg_color": "#FF9800",
                    "accent_color": "#F57C00"
                },
                "info": {
                    "color": self.colors['primary'],
                    "icon": ft.Icons.INFO_ROUNDED,
                    "bg_color": "#2196F3",
                    "accent_color": "#1976D2"
                },
                "loading": {
                    "color": self.colors['primary'],
                    "icon": ft.Icons.AUTORENEW,
                    "bg_color": "#2196F3",
                    "accent_color": "#1976D2"
                }
            }
            
            config = configuracion.get(tipo, configuracion["info"])
            
            # Función para cerrar la notificación
            def cerrar_notificacion(e=None):
                if hasattr(self, 'overlay_notificacion') and self.overlay_notificacion:
                    self.page.overlay.remove(self.overlay_notificacion)
                    self.overlay_notificacion = None
                    self.page.update()
            
            # Función para abrir archivo (si corresponde)
            def abrir_archivo(e=None):
                if ruta_archivo and os.path.exists(ruta_archivo):
                    try:
                        os.startfile(ruta_archivo)
                    except:
                        # Abrir la carpeta contenedora si no se puede abrir el archivo
                        os.startfile(os.path.dirname(ruta_archivo))
                # Auto-cerrar después de abrir archivo
                cerrar_notificacion()
            
            # Botones según el tipo de notificación
            botones = []
            if mostrar_boton_archivo and ruta_archivo:
                botones.append(
                    ft.ElevatedButton(
                        "📂 Abrir Archivo",
                        on_click=abrir_archivo,
                        bgcolor=config["accent_color"],
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(
                            elevation=2,
                            shape=ft.RoundedRectangleBorder(radius=8)
                        ),
                        height=32  # Más compacto
                    )
                )
                # También agregar un botón de cerrar con el mismo estilo que abrir archivo
                botones.append(
                    ft.ElevatedButton(
                        "Cerrar",
                        on_click=cerrar_notificacion,
                        bgcolor="#FFFFFF",
                        color=config["bg_color"],
                        style=ft.ButtonStyle(
                            elevation=2,
                            shape=ft.RoundedRectangleBorder(radius=8)
                        ),
                        height=32
                    )
                )
            
            # Crear el icono animado para loading
            icono_widget = ft.Icon(
                config["icon"],
                color=ft.colors.WHITE,
                size=24  # Más pequeño y proporcional
            )
            
            # Si es tipo loading, hacer el icono giratorio
            if tipo == "loading":
                icono_widget = ft.Container(
                    content=ft.ProgressRing(
                        color=ft.colors.WHITE,
                        width=24,
                        height=24,
                        stroke_width=3
                    ),
                    animate_rotation=ft.Animation(1000, ft.AnimationCurve.LINEAR)
                )
            
            # Crear la tarjeta de notificación súper compacta
            notification_card = ft.Container(
                content=ft.Column([
                    # Encabezado con contenido y botón X (solo si no hay botones de acción)
                    ft.Row([
                        # Contenido principal
                        ft.Expanded(
                            child=ft.Row([
                                icono_widget,
                                ft.Container(width=10),
                                ft.Expanded(
                                    child=ft.Column([
                                        ft.Text(
                                            self._get_notification_title(tipo),
                                            size=15,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.WHITE
                                        ),
                                        ft.Text(
                                            mensaje,
                                            size=12,
                                            color=ft.colors.WHITE70,
                                            max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS
                                        )
                                    ], spacing=2, tight=True)
                                )
                            ], tight=True)
                        ),
                        # Botón X más visible cuando no hay botones de acción
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            icon_color=ft.colors.WHITE,
                            icon_size=18,
                            on_click=cerrar_notificacion,
                            tooltip="Cerrar",
                            style=ft.ButtonStyle(
                                bgcolor=ft.colors.with_opacity(0.2, ft.colors.WHITE),
                                shape=ft.CircleBorder()
                            )
                        ) if not botones else ft.Container(width=0)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, tight=True),
                    
                    # Botones de acción (más compactos)
                    ft.Container(
                        content=ft.Row(
                            botones,
                            alignment=ft.MainAxisAlignment.END,
                            spacing=8,
                            tight=True
                        ),
                        margin=ft.margin.only(top=8) if botones else ft.margin.all(0)
                    ) if botones else ft.Container(height=0)
                ], spacing=0, tight=True),  # Sin espacio extra y compacto
                
                # Estilo del contenedor súper compacto
                width=360,
                padding=ft.padding.only(left=16, right=16, top=12, bottom=4),  # Padding reducido abajo
                bgcolor=config["bg_color"],
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.colors.with_opacity(0.25, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                ),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
            )
            
            # Crear overlay que cubre toda la pantalla con opacidad
            self.overlay_notificacion = ft.Container(
                content=notification_card,
                width=self.page.width if self.page.width else 800,
                height=self.page.height if self.page.height else 600,  # Altura completa de la pantalla
                bgcolor=ft.colors.with_opacity(0.6, ft.colors.BLACK),
                alignment=ft.alignment.center,  # Centrado en el medio
                animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
                top=0,  # Desde la parte superior
                left=0,
                right=0
            )
            
            # Agregar al overlay de la página
            self.page.overlay.append(self.overlay_notificacion)
            self.page.update()
            
            # Auto-cerrar después del tiempo especificado (solo si no es loading)
            if tipo != "loading" and duracion > 0:
                def auto_cerrar():
                    time.sleep(duracion / 1000)
                    try:
                        cerrar_notificacion()
                    except:
                        pass
                
                import threading
                threading.Thread(target=auto_cerrar, daemon=True).start()
            
            print("✅ Notificación central creada exitosamente")
            
        except Exception as ex:
            print(f"❌ Error creando notificación central: {ex}")
            # Fallback a snackbar si falla
            try:
                snackbar = ft.SnackBar(
                    content=ft.Text(mensaje),
                    bgcolor=self.colors.get('error', '#F44336')
                )
                self.page.overlay.append(snackbar)
                snackbar.open = True
                self.page.update()
            except:
                pass

    def _get_notification_title(self, tipo):
        """Obtiene el título apropiado para cada tipo de notificación"""
        titulos = {
            "success": "✅ Éxito",
            "error": "❌ Error",
            "warning": "⚠️ Advertencia",
            "info": "ℹ️ Información",
            "loading": "🔄 Procesando..."
        }
        return titulos.get(tipo, "ℹ️ Notificación")

    def mostrar_notificacion_progreso(self, mensaje="Generando memoria de cálculo...", progreso=None):
        """Muestra una notificación de progreso compacta y elegante"""
        try:
            # Cerrar notificación anterior si existe
            if hasattr(self, 'overlay_notificacion') and self.overlay_notificacion:
                self.page.overlay.remove(self.overlay_notificacion)
            
            # Función para cerrar la notificación
            def cerrar_notificacion(e=None):
                if hasattr(self, 'overlay_notificacion') and self.overlay_notificacion:
                    self.page.overlay.remove(self.overlay_notificacion)
                    self.overlay_notificacion = None
                    self.page.update()
            
            # Crear barra de progreso más delgada y elegante
            if progreso is not None:
                progress_bar = ft.ProgressBar(
                    value=progreso,
                    color="#FFFFFF",
                    bgcolor=ft.colors.with_opacity(0.3, "#FFFFFF"),
                    height=4
                )
                porcentaje_text = ft.Text(
                    f"{int(progreso * 100)}%",
                    size=11,
                    color="#FFFFFF",
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER
                )
            else:
                progress_bar = ft.ProgressBar(
                    color="#FFFFFF",
                    bgcolor=ft.colors.with_opacity(0.3, "#FFFFFF"),
                    height=4
                )
                porcentaje_text = ft.Text(
                    "Procesando...",
                    size=11,
                    color="#FFFFFF",
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER
                )
            
            # Crear contenido súper compacto
            notification_content = ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.ProgressRing(
                            color="#FFFFFF",
                            width=18,
                            height=18,
                            stroke_width=2
                        ),
                        animate_rotation=ft.animation.Animation(1000, ft.AnimationCurve.LINEAR)
                    ),
                    ft.Container(width=10),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "🔄 Generando Memoria",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color="#FFFFFF"
                            ),
                            ft.Text(
                                mensaje,
                                size=11,
                                color=ft.colors.with_opacity(0.9, "#FFFFFF")
                            )
                        ], spacing=1),
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_color="#FFFFFF",
                        icon_size=18,
                        on_click=cerrar_notificacion,
                        tooltip="Cerrar",
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                            shape=ft.CircleBorder()
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=6),
                ft.Column([
                    progress_bar,
                    ft.Container(height=2),
                    porcentaje_text
                ], spacing=0)
            ], spacing=0)
            
            # Tarjeta compacta y elegante - ALTURA FIJA PEQUEÑA
            notification_card = ft.Container(
                content=notification_content,
                width=340,
                height=120,  # ALTURA FIJA PEQUEÑA
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                bgcolor="#2196F3",
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.colors.with_opacity(0.4, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                ),
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT)
            )
            
            # Overlay SIN altura ni ancho fijo - se adapta automáticamente
            self.overlay_notificacion = ft.Container(
                content=notification_card,
                bgcolor=ft.colors.with_opacity(0.75, ft.colors.BLACK),
                alignment=ft.alignment.center,
                animate_opacity=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                expand=True  # Se expande para llenar el espacio disponible
            )
            
            self.page.overlay.append(self.overlay_notificacion)
            self.page.update()
            
        except Exception as ex:
            print(f"Error creando notificación de progreso: {ex}")

    def mostrar_notificacion_exito(self, mensaje, ruta_archivo=None):
        """Muestra una notificación de éxito compacta con opción de abrir archivo"""
        try:
            # Cerrar notificación anterior si existe
            if hasattr(self, 'overlay_notificacion') and self.overlay_notificacion:
                self.page.overlay.remove(self.overlay_notificacion)
            
            def cerrar_notificacion(e=None):
                if hasattr(self, 'overlay_notificacion') and self.overlay_notificacion:
                    self.page.overlay.remove(self.overlay_notificacion)
                    self.overlay_notificacion = None
                    self.page.update()
            
            def abrir_archivo(e=None):
                if ruta_archivo and os.path.exists(ruta_archivo):
                    try:
                        os.startfile(ruta_archivo)
                    except:
                        os.startfile(os.path.dirname(ruta_archivo))
                cerrar_notificacion()
            
            notification_content = ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.icons.CHECK_CIRCLE,
                        color="#FFFFFF",
                        size=18
                    ),
                    ft.Container(width=8),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "✅ ¡Memoria Generada!",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color="#FFFFFF"
                            ),
                            ft.Text(
                                mensaje,
                                size=10,
                                color=ft.colors.with_opacity(0.9, "#FFFFFF"),
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=0),
                        expand=True
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_color="#FFFFFF",
                        icon_size=16,
                        on_click=cerrar_notificacion,
                        tooltip="Cerrar",
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                            shape=ft.CircleBorder()
                        )
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.ElevatedButton(
                    "📂 Abrir Archivo",
                    on_click=abrir_archivo,
                    bgcolor="#FFFFFF",
                    color="#4CAF50",
                    style=ft.ButtonStyle(
                        elevation=2,
                        shape=ft.RoundedRectangleBorder(radius=6)
                    ),
                    height=32
                ) if ruta_archivo else ft.Container(height=0)
            ], spacing=0, tight=True)
            
            # Tarjeta de éxito con ALTURA FIJA PEQUEÑA
            notification_card = ft.Container(
                content=notification_content,
                width=300,
                height=100 if ruta_archivo else 80,  # ALTURA FIJA PEQUEÑA
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor="#4CAF50",
                border_radius=10,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=12,
                    color=ft.colors.with_opacity(0.4, ft.colors.BLACK),
                    offset=ft.Offset(0, 4)
                ),
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT)
            )
            
            # Overlay SIN dimensiones fijas - se adapta automáticamente
            self.overlay_notificacion = ft.Container(
                content=notification_card,
                bgcolor=ft.colors.with_opacity(0.75, ft.colors.BLACK),
                alignment=ft.alignment.center,
                animate_opacity=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                expand=True  # Se expande automáticamente
            )
            
            self.page.overlay.append(self.overlay_notificacion)
            self.page.update()
            
        except Exception as ex:
            print(f"Error creando notificación de éxito: {ex}")
            self.crear_notificacion_flotante(mensaje, "success")

    def _get_notification_title(self, tipo):
        """Obtiene el título apropiado para cada tipo de notificación"""
        titulos = {
            "success": "✅ Éxito",
            "error": "❌ Error", 
            "warning": "⚠️ Advertencia",
            "info": "ℹ️ Información",
            "loading": "🔄 Procesando..."
        }
        return titulos.get(tipo, "ℹ️ Notificación")

    def callback_progreso_memoria(self, mensaje, progreso=None):
        """Callback para actualizar el progreso de la generación de memoria"""
        try:
            if hasattr(self, 'progress_text') and self.progress_text:
                self.progress_text.value = mensaje
                
            if progreso is not None and hasattr(self, 'progress_bar') and self.progress_bar:
                self.progress_bar.value = progreso
                
            if hasattr(self, 'progress_percentage') and self.progress_percentage:
                self.progress_percentage.value = f"{int(progreso * 100)}%" if progreso else ""
                
            if self.page:
                self.page.update()
                
        except Exception as ex:
            print(f"Error en callback_progreso_memoria: {ex}")

    def cerrar_dialogo_progreso(self):
        """Cierra el diálogo de progreso"""
        try:
            if hasattr(self, 'dialog_progreso') and self.dialog_progreso and self.dialog_progreso.open:
                self.dialog_progreso.open = False
                if self.page:
                    self.page.update()
        except Exception as ex:
            print(f"Error cerrando diálogo de progreso: {ex}")

def main():
    """Función principal de la aplicación"""
    app = MemoriaApp()
    ft.app(target=app.main, assets_dir="assets")

if __name__ == "__main__":
    main()  