"""
INE-STRUCTUM - Página de Gestión de Proyectos
Con opción None en Dirección y diálogo info completo
"""

import flet as ft
from datetime import datetime


STAAD_LOAD_TYPES = [
    "Dead", "Live", "Roof Live", "Wind", "Seismic-H", "Seismic-V",
    "Snow", "Fluids", "Soil", "Rain Water/Ice", "Moving",
    "Dust", "Traffic", "Temperature", "Accidental", "Flood",
    "Ice", "Wave", "Crane Hook", "Impact", "Push", "Gravity", "Mass", "None"
]

# Descripciones de cada tipo de carga
LOAD_TYPE_DESCRIPTIONS = {
    "Dead": "Cargas permanentes: peso propio de la estructura, acabados, instalaciones fijas. Factor de carga típico: 1.2 (ASCE 7-22 Eq. 2.3-1)",
    "Live": "Sobrecargas de uso: personas, muebles, equipos móviles. Factor de carga típico: 1.6 (ASCE 7-22 Eq. 2.3-1)",
    "Roof Live": "Sobrecarga de mantenimiento en techos. Factor de carga típico: 1.6 o 0.5 según combinación (ASCE 7-22)",
    "Wind": "Cargas de viento sobre la estructura. Factor de carga típico: 1.0 (strength) o menor para serviceability",
    "Seismic-H": "Fuerzas sísmicas horizontales (X o Z). Factor de carga típico: 1.0 (ASCE 7-22 Eq. 2.3-6)",
    "Seismic-V": "Fuerzas sísmicas verticales (Y). Factor de carga típico: 0.2*SDS (ASCE 7-22 Section 12.4.2.2)",
    "Snow": "Carga de nieve acumulada. Factor de carga típico: 1.6 (ASCE 7-22 Eq. 2.3-1)",
    "Fluids": "Presión de fluidos: tanques, tuberías con presión interna. Factor de carga típico: 1.6 (F)",
    "Soil": "Presión lateral de suelo. Factor de carga típico: 1.6 (H) (ASCE 7-22 Eq. 2.3-1)",
    "Rain Water/Ice": "Agua de lluvia o hielo acumulado. Factor de carga típico: 1.6 (R)",
    "Moving": "Cargas móviles: puentes grúa, cargas rodantes. Incluir impacto. Factor típico: 1.6",
    "Dust": "Presión de materiales granulares o polvo. Factor de carga típico: según caso específico",
    "Traffic": "Cargas de tráfico vehicular. Factor de carga típico: 1.75 (según AASHTO)",
    "Temperature": "Efectos térmicos: expansión, contracción. Factor de carga típico: 1.2 (T) o 0.5 según combinación",
    "Accidental": "Cargas excepcionales: impactos, explosiones. Factor de carga típico: caso específico",
    "Flood": "Cargas de inundación. Factor de carga típico: 1.0 (Fa)",
    "Ice": "Carga de hielo atmosférico. Factor de carga típico: 1.0 (Di) según combinación",
    "Wave": "Cargas de oleaje. Factor de carga típico: caso específico",
    "Crane Hook": "Carga vertical del gancho de grúa. Incluir factores de impacto según CMAA",
    "Impact": "Cargas de impacto: colisiones, frenado. Factor de carga típico: caso específico",
    "Push": "Fuerzas de empuje lateral. Factor de carga típico: según caso",
    "Gravity": "Usado para análisis P-Delta. No se combina directamente.",
    "Mass": "Masa para análisis dinámico. No lleva factor de carga.",
    "None": "Sin clasificar. NO se incluirá en combinaciones automáticas. Use solo para casos especiales que combinará manualmente."
}


class ProyectosPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.showing_form = False
        self.editing_project = None
        self.codigo_diseno_seleccionado = None
        self.proyectos = []
        self.casos_de_carga = []
    
    def build(self):
        header = ft.Row([
            ft.Text("📁 Gestión de Proyectos", size=28, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton("Nuevo Proyecto", icon=ft.Icons.ADD, on_click=self.show_new_project_form,
                            bgcolor="#2563eb", color="#ffffff"),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        self.content_container = ft.Container(content=self.build_projects_list(), expand=True, padding=20)
        return ft.Column([header, ft.Divider(height=20), self.content_container], expand=True, scroll=ft.ScrollMode.AUTO)
    
    def build_projects_list(self):
        if len(self.proyectos) == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER_OPEN, size=80, color="#cbd5e1"),
                    ft.Text("No hay proyectos creados", size=18, color="#64748b"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center, expand=True
            )
        
        cards = [self.build_project_card(p) for p in self.proyectos]
        return ft.Column(cards, spacing=15, scroll=ft.ScrollMode.AUTO)
    
    def build_project_card(self, proyecto):
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(proyecto["nombre"], size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Cliente: {proyecto['codigo_cliente']}", size=14),
                    ft.Text(f"Norma: {proyecto['codigo_diseno']}", size=14, color="#2563eb"),
                ], spacing=5, expand=True),
                ft.Column([
                    ft.ElevatedButton("Editar", icon=ft.Icons.EDIT, on_click=lambda e, p=proyecto: self.edit_project(p)),
                    ft.OutlinedButton("Eliminar", icon=ft.Icons.DELETE, on_click=lambda e, p=proyecto: self.delete_project(p)),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#ffffff", padding=20, border_radius=12, border=ft.border.all(1, "#e2e8f0"),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color="#00000010")
        )
    
    def show_new_project_form(self, e):
        self.editing_project = None
        self.showing_form = True
        self.codigo_diseno_seleccionado = None
        self.casos_de_carga = []
        self.content_container.content = self.build_project_form()
        self.page.update()
    
    def edit_project(self, proyecto):
        self.editing_project = proyecto
        self.showing_form = True
        self.codigo_diseno_seleccionado = proyecto.get("codigo_diseno")
        self.content_container.content = self.build_project_form(proyecto)
        self.page.update()
    
    def delete_project(self, proyecto):
        self.proyectos = [p for p in self.proyectos if p != proyecto]
        self.content_container.content = self.build_projects_list()
        self.page.update()
    
    def build_project_form(self, proyecto_data=None):
        is_edit = proyecto_data is not None
        title = "Editar Proyecto" if is_edit else "Nuevo Proyecto"
        
        self.input_nombre = ft.TextField(label="Nombre del Proyecto *", value=proyecto_data.get("nombre", "") if is_edit else "")
        self.input_codigo_cliente = ft.TextField(label="Código Cliente *", value=proyecto_data.get("codigo_cliente", "") if is_edit else "")
        self.input_codigo_inelectra = ft.TextField(label="Código Inelectra *", value=proyecto_data.get("codigo_inelectra", "") if is_edit else "")
        
        self.archivo_formato = ft.Text("Ningún archivo seleccionado", color="#64748b", size=12)
        btn_seleccionar_formato = ft.ElevatedButton("Seleccionar Plantilla", icon=ft.Icons.UPLOAD_FILE, on_click=self.select_format_file)
        
        self.dropdown_codigo_diseno = ft.Dropdown(
            label="Código de Diseño *",
            options=[
                ft.dropdown.Option("ASCE 7-22", "ASCE 7-22 - American Society of Civil Engineers"),
                ft.dropdown.Option("Eurocode 3", "Eurocode 3 - European Standard"),
            ],
            value=self.codigo_diseno_seleccionado,
            on_change=self.on_codigo_diseno_changed
        )
        
        self.parametros_container = ft.Column(visible=False)
        
        form = ft.Column([
            ft.Text(title, size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(height=20),
            ft.Text("📋 Información General", size=18, weight=ft.FontWeight.BOLD),
            self.input_nombre,
            ft.Row([self.input_codigo_cliente, self.input_codigo_inelectra], spacing=10),
            ft.Divider(height=10),
            ft.Text("📄 Formato de Reporte Base", size=16, weight=ft.FontWeight.BOLD),
            btn_seleccionar_formato,
            self.archivo_formato,
            ft.Divider(height=10),
            ft.Text("⚙ Código de Diseño", size=16, weight=ft.FontWeight.BOLD),
            self.dropdown_codigo_diseno,
            ft.Divider(height=20),
            self.parametros_container,
            ft.Divider(height=30),
            ft.Row([
                ft.ElevatedButton("💾 Guardar Proyecto", icon=ft.Icons.SAVE, on_click=self.save_project_final,
                                bgcolor="#10b981", color="#ffffff", height=50),
                ft.OutlinedButton("Cancelar", icon=ft.Icons.CANCEL, on_click=self.cancel_form, height=50),
            ], spacing=10),
        ], scroll=ft.ScrollMode.AUTO, spacing=15)
        
        return ft.Container(content=form, bgcolor="#ffffff", padding=30, border_radius=12,
                          shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#00000010"))
    
    def on_codigo_diseno_changed(self, e):
        self.codigo_diseno_seleccionado = e.control.value
        if self.codigo_diseno_seleccionado == "ASCE 7-22":
            self.parametros_container.controls = self.build_parametros_asce()
            self.parametros_container.visible = True
        else:
            self.parametros_container.visible = False
        self.page.update()
    
    def build_parametros_asce(self):
        self.input_ss = ft.TextField(label="Ss (g) *", value="1.5", expand=True)
        self.input_s1 = ft.TextField(label="S1 (g) *", value="0.6", expand=True)
        self.input_fa = ft.TextField(label="Fa *", value="1.0", expand=True)
        self.input_fv = ft.TextField(label="Fv *", value="1.5", expand=True)
        self.input_tl = ft.TextField(label="TL (s) *", value="8.0")
        self.dropdown_site_class = ft.Dropdown(label="Site Class *", options=[ft.dropdown.Option(x) for x in ["A","B","C","D","E","F"]], value="D")
        self.dropdown_risk_category = ft.Dropdown(label="Risk Category *", options=[ft.dropdown.Option(x) for x in ["I","II","III","IV"]], value="II")
        
        if not self.casos_de_carga:
            self.casos_de_carga = [
                {"no": 1, "nombre": "DEAD", "tipo": "Dead", "descripcion": "Peso propio", "direccion": None},
                {"no": 2, "nombre": "LIVE", "tipo": "Live", "descripcion": "Carga viva", "direccion": None},
                {"no": 3, "nombre": "WINDX+", "tipo": "Wind", "descripcion": "Viento +X", "direccion": "X+"},
                {"no": 4, "nombre": "WINDX-", "tipo": "Wind", "descripcion": "Viento -X", "direccion": "X-"},
                {"no": 5, "nombre": "WINDZ+", "tipo": "Wind", "descripcion": "Viento +Z", "direccion": "Z+"},
                {"no": 6, "nombre": "WINDZ-", "tipo": "Wind", "descripcion": "Viento -Z", "direccion": "Z-"},
                {"no": 7, "nombre": "SEISMICX", "tipo": "Seismic-H", "descripcion": "Sismo X", "direccion": "X"},
                {"no": 8, "nombre": "SEISMICZ", "tipo": "Seismic-H", "descripcion": "Sismo Z", "direccion": "Z"},
            ]
        
        return [
            ft.Text("🔧 Configuración - ASCE 7-22", size=20, weight=ft.FontWeight.BOLD, color="#2563eb"),
            ft.Divider(height=10),
            ft.Text("⚠ Parámetros Sísmicos del Sitio", size=18, weight=ft.FontWeight.BOLD),
            ft.Row([self.input_ss, self.input_s1], spacing=10),
            ft.Row([self.input_fa, self.input_fv], spacing=10),
            self.input_tl,
            self.dropdown_site_class,
            self.dropdown_risk_category,
            ft.Divider(height=20),
            ft.Text("📋 Casos de Carga Primarios", size=18, weight=ft.FontWeight.BOLD),
            self.build_casos_de_carga_table(),
        ]
    
    def build_casos_de_carga_table(self):
        header = ft.Container(
            content=ft.Row([
                ft.Text("No.", size=12, weight=ft.FontWeight.BOLD, width=40),
                ft.Text("Nombre", size=12, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Tipo STAAD", size=12, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Dirección", size=12, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Descripción", size=12, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Acciones", size=12, weight=ft.FontWeight.BOLD, width=120),
            ], spacing=10),
            bgcolor="#f1f5f9", padding=10, border_radius=8
        )
        
        rows = []
        for i, caso in enumerate(self.casos_de_carga):
            row = ft.Container(
                content=ft.Row([
                    ft.Text(str(caso["no"]), size=12, width=40),
                    ft.TextField(value=caso["nombre"], dense=True, text_size=12, expand=2),
                    ft.Dropdown(value=caso["tipo"], options=[ft.dropdown.Option(t) for t in STAAD_LOAD_TYPES], 
                               dense=True, text_size=12, expand=2),
                    ft.Dropdown(
                        value=caso.get("direccion"),
                        options=[
                            ft.dropdown.Option("None", "None"),
                            ft.dropdown.Option("X", "X (Sismo)"),
                            ft.dropdown.Option("Z", "Z (Sismo)"),
                            ft.dropdown.Option("Y", "Y (Vertical)"),
                            ft.dropdown.Option("X+", "+X (Viento)"),
                            ft.dropdown.Option("X-", "-X (Viento)"),
                            ft.dropdown.Option("Z+", "+Z (Viento)"),
                            ft.dropdown.Option("Z-", "-Z (Viento)"),
                        ],
                        dense=True, text_size=12, expand=2, hint_text="Opcional"
                    ),
                    ft.TextField(value=caso["descripcion"], dense=True, text_size=12, expand=2),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_color="#2563eb", icon_size=16, disabled=(i==0)),
                        ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_color="#2563eb", icon_size=16, disabled=(i==len(self.casos_de_carga)-1)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ef4444", icon_size=16),
                    ], spacing=2, width=120),
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=5)
            )
            rows.append(row)
        
        buttons_row = ft.Row([
            ft.ElevatedButton("➕ Agregar Caso", on_click=self.add_caso_carga, height=35),
            ft.IconButton(icon=ft.Icons.INFO_OUTLINED, icon_color="#2563eb", tooltip="Info tipos de carga",
                         on_click=self.show_load_types_info),
        ], spacing=10)
        
        info_box = ft.Container(
            content=ft.Text(
                "🎯 La columna 'Dirección' identifica casos para combinaciones automáticas. "
                "Viento permite múltiples direcciones (+X, -X, +Z, -Z).",
                size=11, color="#64748b"
            ),
            bgcolor="#f8fafc", padding=15, border_radius=8, margin=ft.margin.only(top=10)
        )
        
        return ft.Column([header, *rows, buttons_row, info_box])
    
    def show_load_types_info(self, e):
        # Crear contenido scrollable con TODAS las descripciones
        descriptions_widgets = []
        for load_type in STAAD_LOAD_TYPES:
            desc = LOAD_TYPE_DESCRIPTIONS.get(load_type, "Sin descripción")
            descriptions_widgets.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"• {load_type}", size=13, weight=ft.FontWeight.BOLD, color="#2563eb"),
                        ft.Text(desc, size=12, color="#475569"),
                    ], spacing=3),
                    padding=ft.padding.only(bottom=10)
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Text("ℹ️ Guía Completa de Tipos de Carga STAAD.Pro", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(descriptions_widgets, spacing=5, scroll=ft.ScrollMode.AUTO),
                width=700,
                height=500
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.close_dialog())],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()
    
    def add_caso_carga(self, e):
        next_no = len(self.casos_de_carga) + 1
        self.casos_de_carga.append({"no": next_no, "nombre": f"CASO{next_no}", "tipo": "Live", 
                                    "direccion": None, "descripcion": "Nuevo caso"})
        self.parametros_container.controls = self.build_parametros_asce()
        self.page.update()
    
    def select_format_file(self, e):
        self.archivo_formato.value = "Plantilla_Inelectra_2025.xlsx"
        self.page.update()
    
    def save_project_final(self, e):
        if not self.input_nombre.value or not self.dropdown_codigo_diseno.value:
            self.show_error("Completa los campos obligatorios")
            return
        
        proyecto = {
            "nombre": self.input_nombre.value,
            "codigo_cliente": self.input_codigo_cliente.value,
            "codigo_inelectra": self.input_codigo_inelectra.value,
            "codigo_diseno": self.dropdown_codigo_diseno.value,
            "casos_de_carga": self.casos_de_carga.copy(),
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        if self.editing_project:
            idx = self.proyectos.index(self.editing_project)
            self.proyectos[idx] = proyecto
        else:
            self.proyectos.append(proyecto)
        
        self.showing_form = False
        self.content_container.content = self.build_projects_list()
        self.page.update()
        self.show_success("✅ Proyecto guardado")
    
    def cancel_form(self, e):
        self.showing_form = False
        self.content_container.content = self.build_projects_list()
        self.page.update()
    
    def show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="#ffffff"), bgcolor="#ef4444")
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="#ffffff"), bgcolor="#10b981")
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
