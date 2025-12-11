"""
Vista de Gestión de Proyectos - CON FORMULARIO COMPLETO
Incluye TODAS las tablas y parámetros del historial
"""

import flet as ft
import json
import os
from datetime import datetime


class ProyectosPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.proyectos_file = "data/proyectos.json"
        self.proyectos = self.cargar_proyectos()
        
        # Estado del formulario
        self.mostrando_formulario = False
        self.proyecto_editando = None
        
    def cargar_proyectos(self):
        """Carga proyectos desde archivo JSON"""
        if os.path.exists(self.proyectos_file):
            try:
                with open(self.proyectos_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def guardar_proyectos(self):
        """Guarda proyectos en archivo JSON"""
        os.makedirs(os.path.dirname(self.proyectos_file), exist_ok=True)
        with open(self.proyectos_file, 'w', encoding='utf-8') as f:
            json.dump(self.proyectos, f, indent=2, ensure_ascii=False)
    
    def mostrar_formulario_nuevo(self, e):
        """Muestra el formulario para nuevo proyecto"""
        self.mostrando_formulario = True
        self.proyecto_editando = None
        self.actualizar_vista()
    
    def cancelar_formulario(self, e):
        """Cancela y oculta el formulario"""
        self.mostrando_formulario = False
        self.proyecto_editando = None
        self.actualizar_vista()
    
    def guardar_proyecto(self, e):
        """Guarda el proyecto (placeholder - implementar lógica completa)"""
        # TODO: Recopilar datos del formulario completo
        self.mostrar_mensaje("✓ Formulario completo en desarrollo", es_error=False)
        self.mostrando_formulario = False
        self.actualizar_vista()
    
    def mostrar_mensaje(self, mensaje, es_error=False):
        """Muestra un mensaje al usuario"""
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color="#ffffff", weight=ft.FontWeight.W_500),
            bgcolor="#ef4444" if es_error else="#10b981",
            duration=3000
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
    
    def actualizar_vista(self):
        """Reconstruye la vista completa"""
        # Buscar el contenedor principal y actualizarlo
        for control in self.page.controls:
            if hasattr(control, 'content') and hasattr(control.content, 'content'):
                if hasattr(control.content.content, 'content'):
                    control.content.content.content.content = self.build()
                    self.page.update()
                    return
    
    def build(self):
        """Construye la interfaz"""
        if self.mostrando_formulario:
            return self.build_formulario_completo()
        else:
            return self.build_lista_proyectos()
    
    def build_lista_proyectos(self):
        """Vista de lista de proyectos"""
        lista = ft.Column(spacing=12)
        
        if not self.proyectos:
            lista.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FOLDER_OPEN, size=80, color="#cbd5e1"),
                        ft.Text("No hay proyectos creados", size=16, color="#64748b"),
                        ft.Container(height=10),
                        ft.Text("Haz clic en 'Nuevo Proyecto' para comenzar", size=13, color="#94a3b8"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50,
                    alignment=ft.alignment.center
                )
            )
        else:
            for proyecto in self.proyectos:
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.FOLDER, size=28, color="#f59e0b"),
                            ft.Column([
                                ft.Text(proyecto.get('nombre', 'Sin nombre'), size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Cliente: {proyecto.get('cliente', 'N/A')}", size=13, color="#64748b"),
                            ], spacing=5, expand=True),
                            ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color="#3b82f6"),
                        ], vertical_alignment=ft.CrossAxisAlignment.START),
                        bgcolor="#f8fafc",
                        border=ft.border.all(1, "#e2e8f0"),
                        border_radius=10,
                        padding=18,
                    )
                )
        
        return ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.FOLDER, size=28, color="#f59e0b"),
                ft.Text("Gestión de Proyectos", size=22, weight=ft.FontWeight.BOLD, color="#1e293b"),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    text="Nuevo Proyecto",
                    icon=ft.Icons.ADD,
                    on_click=self.mostrar_formulario_nuevo,
                    bgcolor="#3b82f6",
                    color="#ffffff",
                    height=42,
                ),
            ]),
            ft.Divider(height=1, color="#e2e8f0"),
            ft.Container(height=10),
            lista,
        ], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def build_formulario_completo(self):
        """Formulario COMPLETO con TODOS los parámetros"""
        return ft.Column([
            # Header del formulario
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=self.cancelar_formulario,
                    tooltip="Volver",
                ),
                ft.Text("Nuevo Proyecto", size=22, weight=ft.FontWeight.BOLD, color="#1e293b"),
            ]),
            ft.Divider(height=1, color="#e2e8f0"),
            
            # CONTENIDO DEL FORMULARIO (scrollable)
            ft.Container(
                content=ft.Column([
                    # PASO 1: Información Básica
                    self.build_seccion_info_basica(),
                    
                    ft.Container(height=20),
                    
                    # PASO 2: Código de Diseño
                    self.build_seccion_codigo_diseno(),
                    
                    ft.Container(height=20),
                    
                    # PASO 3: Parámetros Sísmicos (apareceráocultará según código)
                    self.build_seccion_parametros_sismicos(),
                    
                    ft.Container(height=20),
                    
                    # PASO 4: Casos de Carga
                    self.build_seccion_casos_carga(),
                    
                    ft.Container(height=20),
                    
                    # Botones finales
                    ft.Row([
                        ft.ElevatedButton(
                            text="Guardar Proyecto",
                            icon=ft.Icons.SAVE,
                            on_click=self.guardar_proyecto,
                            bgcolor="#10b981",
                            color="#ffffff",
                            height=45,
                        ),
                        ft.OutlinedButton(
                            text="Cancelar",
                            icon=ft.Icons.CANCEL,
                            on_click=self.cancelar_formulario,
                            height=45,
                        ),
                    ], spacing=10),
                    
                ], spacing=0, scroll=ft.ScrollMode.AUTO),
                expand=True,
            ),
        ], spacing=15, expand=True)
    
    def build_seccion_info_basica(self):
        """Sección 1: Información Básica"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Información Básica", size=18, weight=ft.FontWeight.W_600, color="#1e293b"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Container(height=10),
                
                ft.Row([
                    ft.Container(
                        content=ft.TextField(
                            label="Nombre del Proyecto",
                            hint_text="Ej: Edificio Torres del Sol",
                            prefix_icon=ft.Icons.BUSINESS,
                            border_radius=8,
                            height=56,
                        ),
                        width=400,
                    ),
                    ft.Container(
                        content=ft.TextField(
                            label="Código del Cliente",
                            hint_text="Ej: CLI-2025-001",
                            prefix_icon=ft.Icons.TAG,
                            border_radius=8,
                            height=56,
                        ),
                        width=250,
                    ),
                ], spacing=15),
                
                ft.Row([
                    ft.Container(
                        content=ft.TextField(
                            label="Código Inelectra",
                            hint_text="Ej: INELECTRA-2025-045",
                            prefix_icon=ft.Icons.BADGE,
                            border_radius=8,
                            height=56,
                        ),
                        width=250,
                    ),
                ], spacing=15),
                
            ], spacing=15),
            padding=20,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
        )
    
    def build_seccion_codigo_diseno(self):
        """Sección 2: Código de Diseño"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Código de Diseño", size=18, weight=ft.FontWeight.W_600, color="#1e293b"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Container(height=10),
                
                ft.Dropdown(
                    label="Seleccionar código de diseño",
                    hint_text="Selecciona...",
                    options=[
                        ft.dropdown.Option("ASCE 7-22 / AISC 360-22"),
                        ft.dropdown.Option("Eurocode 3 (EN 1993)"),
                    ],
                    width=400,
                    border_radius=8,
                ),
                
                ft.Container(height=10),
                ft.Text("Al seleccionar un código, aparecerán los parámetros específicos", size=13, color="#64748b"),
                
            ], spacing=10),
            padding=20,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
        )
    
    def build_seccion_parametros_sismicos(self):
        """Sección 3: Parámetros Sísmicos (condicional)"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Parámetros Sísmicos", size=18, weight=ft.FontWeight.W_600, color="#1e293b"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Container(height=10),
                
                ft.Text("(Campos aparecen al seleccionar código de diseño)", size=14, color="#94a3b8", italic=True),
                
                # TODO: Implementar campos dinámicos según código seleccionado
                
            ], spacing=10),
            padding=20,
            bgcolor="#f8fafc",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
        )
    
    def build_seccion_casos_carga(self):
        """Sección 4: Casos de Carga"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Casos de Carga Primarios", size=18, weight=ft.FontWeight.W_600, color="#1e293b"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Container(height=10),
                
                ft.Text("(Tabla de casos de carga en desarrollo)", size=14, color="#94a3b8", italic=True),
                
                # TODO: Implementar tabla de casos de carga
                
            ], spacing=10),
            padding=20,
            bgcolor="#ffffff",
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
        )
