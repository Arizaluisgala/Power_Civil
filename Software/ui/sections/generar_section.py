"""
Sección de generación de memoria
"""
import flet as ft
import os
import threading


class GenerarSection:
    """Sección para generación de memoria de cálculo"""

    def __init__(self, colors, on_validate, on_generate, height=None):
        self.colors = colors
        self.on_validate = on_validate
        self.on_generate = on_generate
        self.height = height if height is not None else 700

    @staticmethod
    def get_screen_height(page):
        """Obtiene el alto de la pantalla actual usando Flet Page."""
        return page.height if page and hasattr(page, 'height') else 700
    
    def create_status_summary(self, archivos, project_data, config_data, capturadas, total_slots, agregar_imagenes):
        """Crea un resumen del estado del sistema"""
        # Verificar archivos (5 archivos: plantilla, logo, excel, excel_cargas, excel_sismo)
        archivos_requeridos = ["plantilla", "logo", "excel", "excel_cargas", "excel_sismo"]
        archivos_ok = all(archivos.get(k) for k in archivos_requeridos)
        archivos_cargados = sum(1 for k in archivos_requeridos if archivos.get(k))

        # Verificar datos (6 campos principales)
        campos_datos = [
            'NOMBRE DEL PROYECTO', 'Emisión', 'MM/DD/AAAA',
            'NOMBRE DEL DOCUMENTO', 'Rev', 'CODIGO COMPAÑIA'
        ]
        datos_ok = all(project_data.get(k) for k in campos_datos)
        datos_cargados = sum(1 for k in campos_datos if project_data.get(k))

        # Verificar configuración del proyecto
        estructura_ok = bool(config_data.get('estructura', '').strip())
        idioma_ok = config_data.get('idioma', '').strip() in ['es', 'en']
        config_ok = estructura_ok and idioma_ok
        campos_config_completados = sum([estructura_ok, idioma_ok])

        capturas_ok = len(capturadas) >= total_slots if agregar_imagenes else True

        status_items = [
            ("📁 Archivos", archivos_ok, f"{archivos_cargados}/5 archivos cargados"),
            ("📝 Datos", datos_ok, f"{datos_cargados}/6 campos completados"),
            ("⚙️ Configuración", config_ok, f"{campos_config_completados}/2 configuraciones establecidas"),
            ("📸 Capturas", capturas_ok, f"{len(capturadas)}/{total_slots} capturas realizadas")
        ]

        status_rows = []
        for icon_title, is_ok, description in status_items:
            color = self.colors['success'] if is_ok else self.colors['error']
            icon = "check_circle" if is_ok else ft.Icons.ERROR
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
    
    def create_generar_section(self, archivos, project_data, config_data, capturadas, total_slots, agregar_imagenes, page=None, on_notify=None):
        """Crea la sección de generación con un log en la propia página."""
        if page is not None and hasattr(page, 'height'):
            altura = page.height
        else:
            altura = self.height

        log_view = ft.ListView(expand=True, spacing=5, auto_scroll=True)

        def mostrar_animacion_exito(ruta_archivo):
            if page:
                def abrir_archivo(e):
                    import os
                    os.startfile(os.path.dirname(ruta_archivo))
                
                file_name = os.path.basename(ruta_archivo)
                file_path = os.path.dirname(ruta_archivo)

                page.dialog = ft.AlertDialog(
                    modal=True,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("¡Memoria generada con éxito!", size=18, weight=ft.FontWeight.BOLD, color=self.colors['success']),
                            ft.Container(height=18),
                            ft.Icon("check_circle", color=self.colors['success'], size=48),
                            ft.Container(height=18),
                            ft.Text(f"Archivo: {file_name}", size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Ubicación: {file_path}", size=12, color=self.colors['text_secondary']),
                            ft.Container(height=24),
                            ft.ElevatedButton(
                                "Abrir carpeta",
                                icon=ft.Icons.FOLDER_OPEN,
                                bgcolor=self.colors['warning'],
                                color=ft.colors.BLACK,
                                on_click=abrir_archivo,
                                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                                height=44
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=32,
                        bgcolor=ft.colors.WHITE,
                        border_radius=18,
                        alignment=ft.alignment.center
                    ),
                    open=True
                )
                page.update()

        def handle_generate(e):
            generate_button = e.control
            is_valid, errors = self.on_validate()
            p = page

            if not is_valid:
                error_dialog = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("❌ Errores de Validación"),
                    content=ft.Column([ft.Text(error) for error in errors]),
                    actions=[
                        ft.TextButton("Cerrar", on_click=lambda _: setattr(error_dialog, 'open', False) or p.update())
                    ]
                )
                p.dialog = error_dialog
                error_dialog.open = True
                p.update()
                return

            log_view.controls.clear()
            log_view.parent.visible = True
            generate_button.disabled = True
            p.update()

            class UILogger:
                def __init__(self, lv, p):
                    self.lv = lv
                    self.page = p
                def write(self, message):
                    if message.strip():
                        self.lv.controls.append(ft.Text(message.strip(), font_family="monospace"))
                        self.page.update()
                def flush(self):
                    pass

            logger = UILogger(log_view, p)

            def generate_in_background():
                import sys
                original_stdout = sys.stdout
                sys.stdout = logger
                
                try:
                    resultado = self.on_generate(e, None)
                    
                    if resultado and resultado["ruta"]:
                        mostrar_animacion_exito(resultado["ruta"])
                    else:
                        error_msg = resultado.get('error', 'Error desconocido') if resultado else 'Error desconocido'
                        print(f"[FATAL] La generación falló: {error_msg}")

                finally:
                    sys.stdout = original_stdout
                    generate_button.disabled = False
                    if p:
                        p.update()

            thread = threading.Thread(target=generate_in_background)
            thread.start()

        generate_button = ft.ElevatedButton(
            "📄 Generar Memoria",
            icon=ft.Icons.ROCKET_LAUNCH,
            on_click=handle_generate,
            bgcolor=self.colors['success'],
            color=ft.colors.WHITE,
            height=50,
            expand=True
        )

        log_container = ft.Container(
            content=log_view,
            border=ft.border.all(1, self.colors['border']),
            border_radius=8,
            padding=10,
            height=300, # Altura fija para scrolling
            visible=False
        )

        return ft.Container(
            content=ft.Column([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("🚀 Generación de Memoria", size=18, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=10),
                            ft.Text(
                                "Verifica que todos los archivos y datos están completos antes de generar.",
                                size=13,
                                color=self.colors['text_secondary']
                            ),
                            ft.Container(height=15),
                            self.create_status_summary(archivos, project_data, config_data, capturadas, total_slots, agregar_imagenes)
                        ]),
                        padding=16
                    ),
                    elevation=2
                ),
                ft.Container(height=12),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("⚡ Acciones", size=18, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=15),
                            ft.Row([generate_button], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Container(height=10),
                            log_container
                        ]),
                        padding=16
                    ),
                    elevation=2
                )
            ], spacing=0, expand=True),
            height=altura,
            expand=False
        )

    def handle_generate(self, e, page):
        # Esta función ya no se usa directamente, se anidó para arreglar el scope
        pass

    def handle_generate(self, e, page):
        is_valid, errors = self.on_validate()
        p = page

        if not is_valid:
            error_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("❌ Errores de Validación"),
                content=ft.Column([ft.Text(error) for error in errors]),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda _: setattr(error_dialog, 'open', False) or p.update())
                ]
            )
            p.dialog = error_dialog
            error_dialog.open = True
            p.update()
            return

        # Limpiar log y hacerlo visible
        self.log_view.controls.clear()
        self.log_view.parent.visible = True
        self.generate_button.disabled = True
        p.update()

        class UILogger:
            def __init__(self, lv, p):
                self.lv = lv
                self.page = p
            def write(self, message):
                if message.strip():
                    self.lv.controls.append(ft.Text(message.strip(), font_family="monospace"))
                    self.page.update()
            def flush(self):
                pass

        logger = UILogger(self.log_view, p)

        def generate_in_background():
            import sys
            original_stdout = sys.stdout
            sys.stdout = logger
            
            try:
                resultado = self.on_generate(e, None)
                
                if resultado and resultado["ruta"]:
                    self.mostrar_animacion_exito(resultado["ruta"])
                else:
                    error_msg = resultado.get('error', 'Error desconocido') if resultado else 'Error desconocido'
                    print(f"[FATAL] La generación falló: {error_msg}")

            finally:
                sys.stdout = original_stdout
                self.generate_button.disabled = False
                if p:
                    p.update()

        thread = threading.Thread(target=generate_in_background)
        thread.start()

        return ft.Container(
            content=ft.Column([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("🚀 Generación de Memoria", size=18, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=10),
                            ft.Text(
                                "Verifica que todos los archivos y datos están completos antes de generar.",
                                size=13,
                                color=self.colors['text_secondary']
                            ),
                            ft.Container(height=15),
                            self.create_status_summary(archivos, project_data, config_data, capturadas, total_slots, agregar_imagenes)
                        ]),
                        padding=16
                    ),
                    elevation=2
                ),
                ft.Container(height=12),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("⚡ Acciones", size=18, weight=ft.FontWeight.BOLD, color=self.colors['primary']),
                            ft.Container(height=15),
                            ft.Row([
                                ft.ElevatedButton(
                                    "📄 Generar Memoria",
                                    icon=ft.Icons.ROCKET_LAUNCH,
                                    on_click=handle_generate,
                                    bgcolor=self.colors['success'],
                                    color=ft.colors.WHITE,
                                    height=50,
                                    expand=True
                                )
                            ], alignment=ft.MainAxisAlignment.CENTER)
                        ]),
                        padding=16
                    ),
                    elevation=2
                )
            ], spacing=0, expand=True),
            height=altura,
            expand=False
        )
