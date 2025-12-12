"""
INE-STRUCTUM - Página de Gestión de Proyectos
VERSIÓN CON LÍNEAS GUÍA LIMITADAS (SIN ATRAVESAR EL GRÁFICO)
"""

import flet as ft
from datetime import datetime
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

STAAD_LOAD_TYPES = [
    "Dead", "Live", "Roof Live", "Wind", "Seismic-H", "Seismic-V",
    "Snow", "Fluids", "Soil", "Rain Water/Ice", "Moving",
    "Dust", "Traffic", "Temperature", "Accidental", "Flood",
    "Ice", "Wave", "Crane Hook", "Impact", "Push", "Gravity", "Mass", "None"
]

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
        self.form_modified = False
        self.current_overlay = None
        self.espectro_image = None
        
        self.btn_nuevo = ft.ElevatedButton(
            "Nuevo Proyecto", 
            icon=ft.Icons.ADD, 
            on_click=self.show_new_project_form,
            bgcolor="#2563eb", 
            color="#ffffff"
        )
        
        self.btn_volver = ft.ElevatedButton(
            "Volver", 
            icon=ft.Icons.ARROW_BACK, 
            on_click=self.go_back_with_confirmation,
            bgcolor="#64748b", 
            color="#ffffff",
            visible=False
        )
    
    def build(self):
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER, size=32, color="#f59e0b"),
                ft.Text("Gestión de Proyectos", size=28, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.btn_nuevo,
                self.btn_volver,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            height=80
        )
        
        self.content_container = ft.Container(content=self.build_projects_list(), expand=True)
        self.main_stack = ft.Stack([
            ft.Column([header, ft.Divider(height=20), self.content_container], expand=True, scroll=ft.ScrollMode.AUTO)
        ], expand=True)
        
        return self.main_stack
    
    def close_dialog(self):
        if self.current_overlay and self.current_overlay in self.main_stack.controls:
            self.main_stack.controls.remove(self.current_overlay)
            self.current_overlay = None
            self.page.update()
    
    def show_custom_dialog(self, title, content, buttons_config):
        def make_button_handler(callback):
            def handler(e):
                self.close_dialog()
                if callback:
                    callback(e)
            return handler
        
        buttons = []
        for btn_cfg in buttons_config:
            btn_type = btn_cfg.get("type", "text")
            handler = make_button_handler(btn_cfg.get("on_click"))
            
            if btn_type == "elevated":
                btn = ft.ElevatedButton(
                    btn_cfg["text"],
                    icon=btn_cfg.get("icon"),
                    on_click=handler,
                    bgcolor=btn_cfg.get("bgcolor"),
                    color=btn_cfg.get("color")
                )
            elif btn_type == "outlined":
                btn = ft.OutlinedButton(btn_cfg["text"], on_click=handler)
            else:
                btn = ft.TextButton(btn_cfg["text"], on_click=handler)
            
            buttons.append(btn)
        
        overlay_bg = ft.Container(bgcolor="#00000088", expand=True)
        
        dialog_card = ft.Container(
            content=ft.Column([
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color="#1e293b"),
                ft.Divider(height=20),
                content,
                ft.Container(height=20),
                ft.Row(buttons, alignment=ft.MainAxisAlignment.END, spacing=10)
            ], tight=True),
            bgcolor="#ffffff",
            padding=25,
            border_radius=12,
            width=650,
            shadow=ft.BoxShadow(spread_radius=5, blur_radius=20, color="#00000040")
        )
        
        dialog_container = ft.Container(
            content=ft.Column([dialog_card], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True
        )
        
        self.current_overlay = ft.Stack([overlay_bg, dialog_container], expand=True)
        self.main_stack.controls.append(self.current_overlay)
        self.page.update()
    
    def build_projects_list(self):
        if len(self.proyectos) == 0:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.FOLDER, size=80, color="#cbd5e1"),
                    ft.Text("No hay proyectos creados", size=18, color="#64748b"),
                    ft.Text("Haz clic en 'Nuevo Proyecto' para comenzar", size=14, color="#94a3b8"),
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
                    ft.Text(f"Inelectra: {proyecto['codigo_inelectra']}", size=14),
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
        self.form_modified = False
        
        self.btn_nuevo.visible = False
        self.btn_volver.visible = True
        
        self.content_container.content = self.build_project_form()
        self.page.update()
    
    def edit_project(self, proyecto):
        self.editing_project = proyecto
        self.showing_form = True
        self.codigo_diseno_seleccionado = proyecto.get("codigo_diseno")
        self.casos_de_carga = proyecto.get("casos_de_carga", [])
        self.form_modified = False
        
        self.btn_nuevo.visible = False
        self.btn_volver.visible = True
        
        self.content_container.content = self.build_project_form(proyecto)
        self.page.update()
    
    def delete_project(self, proyecto):
        self.proyectos = [p for p in self.proyectos if p != proyecto]
        self.content_container.content = self.build_projects_list()
        self.page.update()
    
    def go_back_with_confirmation(self, e):
        if self.form_modified:
            content = ft.Text("Hay cambios en el formulario. ¿Deseas salir sin guardar?", size=14)
            buttons = [
                {"text": "Salir sin guardar", "type": "elevated", "bgcolor": "#ef4444", "color": "#ffffff", "icon": ft.Icons.EXIT_TO_APP, "on_click": lambda e: self.cancel_form(None)},
                {"text": "Continuar editando", "type": "outlined", "on_click": None},
            ]
            self.show_custom_dialog("⚠️ Cambios sin guardar", content, buttons)
        else:
            self.cancel_form(None)
    
    def generar_espectro_minimalista(self):
        """Genera espectro con LÍNEAS GUÍA LIMITADAS (del punto al eje)"""
        try:
            ss = float(self.input_ss.value or 1.5)
            s1 = float(self.input_s1.value or 0.6)
            fa = float(self.input_fa.value or 1.0)
            fv = float(self.input_fv.value or 1.5)
            tl = float(self.input_tl.value or 8.0)
            
            sds = (2.0/3.0) * fa * ss
            sd1 = (2.0/3.0) * fv * s1
            t0 = 0.2 * (sd1 / sds) if sds > 0 else 0.0
            ts = sd1 / sds if sds > 0 else 0.0
            
            # CALCULAR LÍMITE DINÁMICO DEL EJE X
            t_max = max(tl * 1.3, 2.0)
            
            # Generar periodos hasta t_max
            periodos = np.linspace(0.0, t_max, 500)
            sa_values = []
            
            for t in periodos:
                if t < t0:
                    sa = sds * (0.4 + 0.6 * (t / t0))
                elif t <= ts:
                    sa = sds
                elif t <= tl:
                    sa = sd1 / t
                else:
                    sa = (sd1 * tl) / (t ** 2)
                sa_values.append(sa)
            
            # CALCULAR LÍMITE DINÁMICO DEL EJE Y
            sa_max = max(sa_values)
            sa_limite = sa_max * 1.08
            sa_tl = sd1 / tl if tl > 0 else 0
            
            # ESTILO MINIMALISTA
            fig = plt.figure(figsize=(10, 5.5), facecolor='white')
            ax = fig.add_subplot(111)
            
            # LÍNEAS GUÍA LIMITADAS (sin atravesar el gráfico)
            guia_color = '#cbd5e1'
            guia_style = (0, (3, 5))  # patrón de puntos
            guia_width = 1.0
            guia_alpha = 0.6
            
            # LÍNEAS VERTICALES (desde el punto hasta el eje X, es decir y=0)
            ax.plot([t0, t0], [0, sds], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            ax.plot([ts, ts], [0, sds], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            ax.plot([tl, tl], [0, sa_tl], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            
            # LÍNEAS HORIZONTALES (desde el punto hasta el eje Y, es decir x=0)
            ax.plot([0, t0], [sds, sds], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            ax.plot([0, ts], [sds, sds], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            ax.plot([0, tl], [sa_tl, sa_tl], color=guia_color, linestyle=guia_style, 
                   linewidth=guia_width, alpha=guia_alpha, zorder=2)
            
            # Curva principal
            ax.plot(periodos, sa_values, linewidth=2.2, color='#334155', alpha=0.9, zorder=5)
            
            # Puntos característicos
            ax.plot(t0, sds, 'o', markersize=7, color='#334155', markerfacecolor='white', 
                   markeredgewidth=2, zorder=10, label=f'T₀={t0:.3f}s')
            ax.plot(ts, sds, 's', markersize=7, color='#334155', markerfacecolor='white', 
                   markeredgewidth=2, zorder=10, label=f'Ts={ts:.3f}s')
            ax.plot(tl, sa_tl, 'd', markersize=7, color='#334155', markerfacecolor='white', 
                   markeredgewidth=2, zorder=10, label=f'TL={tl:.1f}s')
            
            # Grid minimalista
            ax.grid(True, linestyle='-', alpha=0.08, linewidth=0.8, color='#94a3b8', zorder=1)
            ax.set_axisbelow(True)
            
            # Ejes y etiquetas
            ax.set_xlabel('T (s)', fontsize=11, color='#475569', fontweight='500')
            ax.set_ylabel('Sa (g)', fontsize=11, color='#475569', fontweight='500')
            ax.set_title('Espectro de Diseño Elástico', fontsize=12, color='#1e293b', 
                        fontweight='600', pad=15, loc='left')
            
            # Leyenda minimalista
            legend = ax.legend(loc='upper right', fontsize=9, frameon=True, 
                             fancybox=False, shadow=False, framealpha=0.95,
                             edgecolor='#e2e8f0', facecolor='white')
            legend.get_frame().set_linewidth(1)
            
            # LÍMITES AJUSTADOS DINÁMICAMENTE
            ax.set_xlim(0, t_max)
            ax.set_ylim(0, sa_limite)
            
            # Spines minimalistas
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#cbd5e1')
            ax.spines['bottom'].set_color('#cbd5e1')
            ax.spines['left'].set_linewidth(1)
            ax.spines['bottom'].set_linewidth(1)
            
            # Ticks sutiles
            ax.tick_params(axis='both', which='major', labelsize=9, colors='#64748b', 
                          length=4, width=1, direction='out')
            
            # Guardar
            buf = io.BytesIO()
            plt.tight_layout(pad=1.5)
            plt.savefig(buf, format='png', dpi=130, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.read()).decode('utf-8')
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def actualizar_espectro(self, e=None):
        """Actualiza gráfico en tiempo real"""
        img_base64 = self.generar_espectro_minimalista()
        if img_base64 and self.espectro_image:
            self.espectro_image.src_base64 = img_base64
            self.page.update()
    
    def build_project_form(self, proyecto_data=None):
        is_edit = proyecto_data is not None
        title = "Editar Proyecto" if is_edit else "Nuevo Proyecto"
        
        self.input_nombre = ft.TextField(
            label="Nombre del Proyecto *",
            value=proyecto_data.get("nombre", "") if is_edit else "",
            hint_text="Ej: Edificio Torre Central",
            border_color="#cbd5e1",
            focused_border_color="#2563eb",
            width=800,
            on_change=lambda e: setattr(self, 'form_modified', True)
        )
        
        self.input_codigo_cliente = ft.TextField(
            label="Código Cliente *",
            value=proyecto_data.get("codigo_cliente", "") if is_edit else "",
            hint_text="Ej: CLI-2025-001",
            border_color="#cbd5e1",
            focused_border_color="#2563eb",
            width=390,
            on_change=lambda e: setattr(self, 'form_modified', True)
        )
        
        self.input_codigo_inelectra = ft.TextField(
            label="Código Inelectra *",
            value=proyecto_data.get("codigo_inelectra", "") if is_edit else "",
            hint_text="Ej: INE-PRJ-2025-045",
            border_color="#cbd5e1",
            focused_border_color="#2563eb",
            width=390,
            on_change=lambda e: setattr(self, 'form_modified', True)
        )
        
        self.archivo_formato = ft.Text("Ningún archivo seleccionado", color="#64748b", size=12)
        btn_seleccionar_formato = ft.ElevatedButton(
            "Seleccionar Plantilla",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=self.select_format_file
        )
        
        self.dropdown_codigo_diseno = ft.Dropdown(
            label="Código de Diseño *",
            hint_text="Selecciona un código",
            options=[
                ft.dropdown.Option("ASCE 7-22", "ASCE 7-22 - American Society of Civil Engineers"),
                ft.dropdown.Option("Eurocode 3", "Eurocode 3 - European Standard"),
            ],
            value=self.codigo_diseno_seleccionado,
            on_change=self.on_codigo_diseno_changed,
            border_color="#cbd5e1",
            focused_border_color="#2563eb",
            width=800
        )
        
        self.parametros_container = ft.Column(visible=bool(self.codigo_diseno_seleccionado))
        if self.codigo_diseno_seleccionado == "ASCE 7-22":
            self.parametros_container.controls = self.build_parametros_asce()
        
        form = ft.Column([
            ft.Text(title, size=24, weight=ft.FontWeight.BOLD, color="#1e293b"),
            ft.Divider(height=30, color="#e2e8f0"),
            ft.Text("📋 Información General", size=18, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Container(height=10),
            self.input_nombre,
            ft.Container(height=15),
            ft.Row([self.input_codigo_cliente, self.input_codigo_inelectra], spacing=15),
            ft.Container(height=25),
            ft.Divider(color="#e2e8f0"),
            ft.Container(height=15),
            ft.Text("📄 Formato de Reporte Base", size=16, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Text("Selecciona la plantilla Excel/Word para generar reportes", size=12, color="#64748b"),
            ft.Container(height=10),
            btn_seleccionar_formato,
            ft.Container(height=5),
            self.archivo_formato,
            ft.Container(height=25),
            ft.Divider(color="#e2e8f0"),
            ft.Container(height=15),
            ft.Text("⚙️ Código de Diseño", size=16, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Container(height=10),
            self.dropdown_codigo_diseno,
            ft.Container(height=20),
            self.parametros_container,
            ft.Container(height=30),
            ft.Divider(color="#e2e8f0"),
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Guardar Proyecto", icon=ft.Icons.SAVE, on_click=self.save_project_final, bgcolor="#10b981", color="#ffffff", height=50),
                ft.OutlinedButton("Cancelar", icon=ft.Icons.CANCEL, on_click=self.cancel_form, height=50),
            ], spacing=15),
        ], scroll=ft.ScrollMode.AUTO, spacing=0)
        
        return ft.Container(content=form, bgcolor="#ffffff", padding=30, border_radius=12, shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color="#00000010"))
    
    def on_codigo_diseno_changed(self, e):
        self.form_modified = True
        self.codigo_diseno_seleccionado = e.control.value
        if self.codigo_diseno_seleccionado == "ASCE 7-22":
            self.parametros_container.controls = self.build_parametros_asce()
            self.parametros_container.visible = True
        else:
            self.parametros_container.visible = False
            self.parametros_container.controls = []
        self.page.update()
    
    def build_parametros_asce(self):
        # 8 CAMPOS ESENCIALES
        self.input_ss = ft.TextField(label="Ss (g) *", value="1.5", width=190, on_change=lambda e: [setattr(self, 'form_modified', True), self.actualizar_espectro()])
        self.input_s1 = ft.TextField(label="S1 (g) *", value="0.6", width=190, on_change=lambda e: [setattr(self, 'form_modified', True), self.actualizar_espectro()])
        self.input_fa = ft.TextField(label="Fa *", value="1.0", width=190, on_change=lambda e: [setattr(self, 'form_modified', True), self.actualizar_espectro()])
        self.input_fv = ft.TextField(label="Fv *", value="1.5", width=190, on_change=lambda e: [setattr(self, 'form_modified', True), self.actualizar_espectro()])
        
        self.input_ie = ft.TextField(label="Ie *", value="1.0", width=190, on_change=lambda e: setattr(self, 'form_modified', True))
        self.input_tl = ft.TextField(label="TL (s) *", value="8.0", width=190, on_change=lambda e: [setattr(self, 'form_modified', True), self.actualizar_espectro()])
        self.dropdown_site_class = ft.Dropdown(label="Site Class *", options=[ft.dropdown.Option(x) for x in ["A","B","C","D","E","F"]], value="D", width=190, on_change=lambda e: setattr(self, 'form_modified', True))
        self.dropdown_risk_category = ft.Dropdown(label="Risk Category *", options=[ft.dropdown.Option(x) for x in ["I","II","III","IV"]], value="II", width=190, on_change=lambda e: setattr(self, 'form_modified', True))
        
        # Generar espectro inicial
        img_base64 = self.generar_espectro_minimalista()
        self.espectro_image = ft.Image(
            src_base64=img_base64,
            width=850,
            height=450,
            fit=ft.ImageFit.CONTAIN
        )
        
        if not self.casos_de_carga:
            self.casos_de_carga = [
                {"no": 1, "nombre": "DEAD", "tipo": "Dead", "descripcion": "Peso propio", "direccion": "None"},
                {"no": 2, "nombre": "LIVE", "tipo": "Live", "descripcion": "Carga viva", "direccion": "None"},
                {"no": 3, "nombre": "WINDX+", "tipo": "Wind", "descripcion": "Viento +X", "direccion": "X+"},
                {"no": 4, "nombre": "WINDX-", "tipo": "Wind", "descripcion": "Viento -X", "direccion": "X-"},
                {"no": 5, "nombre": "WINDZ+", "tipo": "Wind", "descripcion": "Viento +Z", "direccion": "Z+"},
                {"no": 6, "nombre": "WINDZ-", "tipo": "Wind", "descripcion": "Viento -Z", "direccion": "Z-"},
                {"no": 7, "nombre": "SEISMICX", "tipo": "Seismic-H", "descripcion": "Sismo X", "direccion": "X"},
                {"no": 8, "nombre": "SEISMICZ", "tipo": "Seismic-H", "descripcion": "Sismo Z", "direccion": "Z"},
            ]
        
        return [
            ft.Container(height=20),
            ft.Text("🔧 Configuración - ASCE 7-22", size=20, weight=ft.FontWeight.BOLD, color="#2563eb"),
            ft.Container(height=20),
            
            ft.Text("⚠️ Parámetros Sísmicos del Sitio", size=16, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Container(height=15),
            ft.Row([self.input_ss, self.input_s1, self.input_fa, self.input_fv], spacing=15),
            ft.Container(height=10),
            ft.Row([self.input_ie, self.input_tl, self.dropdown_site_class, self.dropdown_risk_category], spacing=15),
            
            ft.Container(height=25),
            ft.Divider(color="#e2e8f0"),
            ft.Container(height=20),
            
            ft.Text("📊 Espectro de Diseño Elástico", size=16, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Container(height=12),
            ft.Container(
                content=self.espectro_image,
                bgcolor="#ffffff",
                border_radius=8,
                padding=15,
                border=ft.border.all(1, "#e2e8f0")
            ),
            
            ft.Container(height=30),
            ft.Divider(color="#e2e8f0"),
            ft.Container(height=20),
            
            ft.Text("📋 Casos de Carga Primarios", size=16, weight=ft.FontWeight.BOLD, color="#475569"),
            ft.Container(height=15),
            self.build_casos_de_carga_table(),
        ]
    
    def build_casos_de_carga_table(self):
        header = ft.Container(
            content=ft.Row([
                ft.Text("No.", size=13, weight=ft.FontWeight.BOLD, width=50),
                ft.Text("Nombre", size=13, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Tipo STAAD", size=13, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Dirección", size=13, weight=ft.FontWeight.BOLD, expand=2),
                ft.Text("Descripción", size=13, weight=ft.FontWeight.BOLD, expand=2),
                ft.Container(width=130),
            ], spacing=10),
            bgcolor="#f1f5f9", padding=15, border_radius=8
        )
        
        rows = []
        for i, caso in enumerate(self.casos_de_carga):
            row = ft.Container(
                content=ft.Row([
                    ft.Text(str(caso["no"]), size=12, width=50),
                    ft.TextField(value=caso["nombre"], dense=True, text_size=12, expand=2, border_color="#cbd5e1", on_change=lambda e, idx=i: self.update_caso_field(idx, "nombre", e.control.value)),
                    ft.Dropdown(value=caso["tipo"], options=[ft.dropdown.Option(t) for t in STAAD_LOAD_TYPES], dense=True, text_size=12, expand=2, on_change=lambda e, idx=i: self.update_caso_field(idx, "tipo", e.control.value)),
                    ft.Dropdown(value=caso.get("direccion", "None"), options=[ft.dropdown.Option("None", "None"), ft.dropdown.Option("X", "X (Sismo)"), ft.dropdown.Option("Z", "Z (Sismo)"), ft.dropdown.Option("Y", "Y (Vertical)"), ft.dropdown.Option("X+", "+X (Viento)"), ft.dropdown.Option("X-", "-X (Viento)"), ft.dropdown.Option("Z+", "+Z (Viento)"), ft.dropdown.Option("Z-", "-Z (Viento)")], dense=True, text_size=12, expand=2, hint_text="Opcional", on_change=lambda e, idx=i: self.update_caso_field(idx, "direccion", e.control.value)),
                    ft.TextField(value=caso["descripcion"], dense=True, text_size=12, expand=2, border_color="#cbd5e1", on_change=lambda e, idx=i: self.update_caso_field(idx, "descripcion", e.control.value)),
                    ft.Row([
                        ft.IconButton(icon=ft.Icons.ARROW_UPWARD, icon_color="#2563eb", icon_size=18, disabled=(i==0), tooltip="Mover arriba", on_click=lambda e, idx=i: self.move_caso_up(idx)),
                        ft.IconButton(icon=ft.Icons.ARROW_DOWNWARD, icon_color="#2563eb", icon_size=18, disabled=(i==len(self.casos_de_carga)-1), tooltip="Mover abajo", on_click=lambda e, idx=i: self.move_caso_down(idx)),
                        ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ef4444", icon_size=18, tooltip="Eliminar", on_click=lambda e, idx=i: self.delete_caso(idx)),
                    ], spacing=0, width=130),
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=8, horizontal=10),
                border=ft.border.only(bottom=ft.BorderSide(1, "#e2e8f0"))
            )
            rows.append(row)
        
        buttons_row = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("Agregar Caso", icon=ft.Icons.ADD, on_click=self.add_caso_carga, height=40, bgcolor="#2563eb", color="#ffffff"),
                ft.IconButton(icon=ft.Icons.INFO_OUTLINED, icon_color="#2563eb", tooltip="Ver guía de tipos de carga", on_click=self.show_load_types_info, icon_size=24),
            ], spacing=10),
            padding=ft.padding.only(top=15)
        )
        
        info_box = ft.Container(
            content=ft.Text("🎯 La columna 'Dirección' identifica casos para combinaciones automáticas. Viento permite múltiples direcciones (+X, -X, +Z, -Z). Use 'None' para casos que no requieren dirección.", size=11, color="#64748b"),
            bgcolor="#f8fafc", padding=15, border_radius=8, margin=ft.margin.only(top=15), border=ft.border.all(1, "#e2e8f0")
        )
        
        return ft.Column([header, *rows, buttons_row, info_box], spacing=0)
    
    def update_caso_field(self, index, field, value):
        self.form_modified = True
        if 0 <= index < len(self.casos_de_carga):
            self.casos_de_carga[index][field] = value
    
    def move_caso_up(self, index):
        if index > 0:
            self.form_modified = True
            self.casos_de_carga[index], self.casos_de_carga[index-1] = self.casos_de_carga[index-1], self.casos_de_carga[index]
            self.casos_de_carga[index]["no"] = index + 1
            self.casos_de_carga[index-1]["no"] = index
            self.parametros_container.controls = self.build_parametros_asce()
            self.page.update()
    
    def move_caso_down(self, index):
        if index < len(self.casos_de_carga) - 1:
            self.form_modified = True
            self.casos_de_carga[index], self.casos_de_carga[index+1] = self.casos_de_carga[index+1], self.casos_de_carga[index]
            self.casos_de_carga[index]["no"] = index + 1
            self.casos_de_carga[index+1]["no"] = index + 2
            self.parametros_container.controls = self.build_parametros_asce()
            self.page.update()
    
    def delete_caso(self, index):
        if len(self.casos_de_carga) > 1:
            self.form_modified = True
            self.casos_de_carga.pop(index)
            for i, caso in enumerate(self.casos_de_carga):
                caso["no"] = i + 1
            self.parametros_container.controls = self.build_parametros_asce()
            self.page.update()
    
    def show_load_types_info(self, e):
        text_lines = []
        for load_type in STAAD_LOAD_TYPES:
            desc = LOAD_TYPE_DESCRIPTIONS.get(load_type, "Sin descripción")
            text_lines.append(f"• {load_type}\n  {desc}\n")
        
        full_text = "\n".join(text_lines)
        content = ft.Container(content=ft.Text(full_text, size=11, selectable=True), width=600, height=400)
        buttons = [{"text": "Cerrar", "type": "text", "on_click": None}]
        
        self.show_custom_dialog("ℹ️ Guía de Tipos de Carga STAAD.Pro", content, buttons)
    
    def add_caso_carga(self, e):
        self.form_modified = True
        next_no = len(self.casos_de_carga) + 1
        self.casos_de_carga.append({"no": next_no, "nombre": f"CASO{next_no}", "tipo": "Live", "direccion": "None", "descripcion": "Nuevo caso"})
        self.parametros_container.controls = self.build_parametros_asce()
        self.page.update()
    
    def select_format_file(self, e):
        self.form_modified = True
        
        def on_file_selected(e: ft.FilePickerResultEvent):
            if e.files:
                self.archivo_formato.value = f"✅ {e.files[0].name}"
                self.archivo_formato.color = "#10b981"
                self.page.update()
        
        file_picker = ft.FilePicker(on_result=on_file_selected)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(
            dialog_title="Seleccionar plantilla Excel/Word",
            allowed_extensions=["xlsx", "xls", "docx", "doc"],
            allow_multiple=False
        )
    
    def save_project_final(self, e):
        if not self.input_nombre.value:
            self.show_error("❌ El nombre del proyecto es obligatorio")
            return
        if not self.dropdown_codigo_diseno.value:
            self.show_error("❌ Debes seleccionar un código de diseño")
            return
        
        proyecto = {
            "nombre": self.input_nombre.value,
            "codigo_cliente": self.input_codigo_cliente.value,
            "codigo_inelectra": self.input_codigo_inelectra.value,
            "codigo_diseno": self.dropdown_codigo_diseno.value,
            "casos_de_carga": self.casos_de_carga.copy() if self.casos_de_carga else [],
            "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        
        if self.editing_project:
            idx = self.proyectos.index(self.editing_project)
            self.proyectos[idx] = proyecto
        else:
            self.proyectos.append(proyecto)
        
        self.showing_form = False
        self.form_modified = False
        self.btn_nuevo.visible = True
        self.btn_volver.visible = False
        self.content_container.content = self.build_projects_list()
        self.page.update()
        self.show_success("✅ Proyecto guardado exitosamente")
    
    def cancel_form(self, e):
        self.showing_form = False
        self.form_modified = False
        self.btn_nuevo.visible = True
        self.btn_volver.visible = False
        self.content_container.content = self.build_projects_list()
        self.page.update()
    
    def show_error(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="#ffffff"), bgcolor="#ef4444", duration=3000)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def show_success(self, msg):
        snack = ft.SnackBar(content=ft.Text(msg, color="#ffffff"), bgcolor="#10b981", duration=3000)
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
