"""
Sección de capturas de pantalla - Versión profesional
"""
import flet as ft
import base64


class CapturaSection:
    """Sección para gestión de capturas de pantalla"""

    def __init__(self, page, colors, config_data, capturadas, total_slots, slots_ordenados,
                 on_config_change, on_capture, on_clear, on_delete_capture, height=None):
        self.page = page
        self.colors = colors
        self.config_data = config_data
        self.capturadas = capturadas
        self.total_slots = total_slots
        self.slots_ordenados = slots_ordenados
        self.on_config_change = on_config_change
        self.on_capture = on_capture
        self.on_clear = on_clear
        self.on_delete_capture = on_delete_capture
        self.height = height if height is not None else 700
        
        # Componentes para la previsualización
        self.preview_image = ft.Image(border_radius=ft.border_radius.all(12))
        self.preview_container = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Vista Previa", size=16, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE_ROUNDED,
                        on_click=self.hide_preview,
                        tooltip="Cerrar previsualización",
                        icon_color=self.colors['text_secondary'],
                        icon_size=20
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                ft.Container(
                    content=self.preview_image,
                    padding=10,
                    border=ft.border.all(1, self.colors['border']),
                    border_radius=12,
                    bgcolor=self.colors['background']
                )
            ]),
            padding=ft.padding.symmetric(horizontal=18, vertical=12),
            border_radius=8,
            bgcolor=ft.colors.with_opacity(0.03, self.colors['primary']),
            visible=False,
            animate=ft.animation.Animation(300, "easeOut"),
            margin=ft.margin.only(bottom=10)
        )
        
        self.setup_components()

    @staticmethod
    def get_screen_height(page):
        """Obtiene el alto de la pantalla actual usando Flet Page."""
        return page.height if page and hasattr(page, 'height') else 700
    
    def setup_components(self):
        """Configura los componentes de la sección"""
        self.agregar_imagenes_checkbox = ft.Switch(
            label="Incluir imágenes en memoria de cálculo",
            value=self.config_data['agregar_imagenes'],
            on_change=self.on_config_change,
            active_color=self.colors['primary'],
            thumb_color=ft.colors.WHITE,
            inactive_thumb_color=ft.colors.GREY_400,
            inactive_track_color=ft.colors.GREY_300
        )

        self.lista_capturas = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, tight=True)

        self.progress_text = ft.Text(
            f"{len(self.capturadas)} de {self.total_slots} completadas",
            size=12,
            weight=ft.FontWeight.W_500,
            color=self.colors['success'] if len(self.capturadas) == self.total_slots else self.colors['text_primary']
        )

        self.progress_bar = ft.ProgressBar(
            value=len(self.capturadas) / self.total_slots if self.total_slots > 0 else 0,
            color=self.colors['success'],
            bgcolor=ft.colors.with_opacity(0.2, self.colors['border']),
            height=5
        )
    
    def show_preview(self, e, image_path):
        """Muestra una previsualización de la imagen en la misma interfaz."""
        print(f"[DEBUG] Mostrando previsualización en la interfaz para: {image_path}")
        try:
            with open(image_path, "rb") as f:
                encoded_string = base64.b64encode(f.read()).decode("utf-8")
            
            self.preview_image.src_base64 = encoded_string
            self.preview_container.visible = True
            self.preview_container.update()
            self.page.update()
            print("[DEBUG] Previsualización en interfaz actualizada.")
        except Exception as ex:
            print(f"[ERROR] Error al mostrar la previsualización en interfaz: {ex}")

    def hide_preview(self, e):
        """Oculta la previsualización de la imagen."""
        self.preview_container.visible = False
        self.preview_container.update()
        self.page.update()

    def update_lista_capturas(self):
        """Actualiza la lista visual de capturas"""
        if not hasattr(self, 'lista_capturas'):
            return
            
        self.lista_capturas.controls.clear()
        
        if not self.config_data['agregar_imagenes']:
            self.lista_capturas.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=self.colors['warning'], size=20),
                        ft.Text(
                            "Las imágenes están deshabilitadas en la configuración",
                            size=13,
                            color=self.colors['text_secondary'],
                            weight=ft.FontWeight.W_400
                        )
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border_radius=6,
                    bgcolor=ft.colors.with_opacity(0.08, self.colors['warning']),
                    border=ft.border.all(1, ft.colors.with_opacity(0.2, self.colors['warning']))
                )
            )
        else:
            slots_a_mostrar = self.slots_ordenados if self.total_slots == len(self.slots_ordenados) else {k: v for k, v in list(self.slots_ordenados.items())[:self.total_slots]}
            
            for slot_num, descripcion in slots_a_mostrar.items():
                capturada = slot_num in self.capturadas
                es_automatica = slot_num <= 5
                
                if capturada:
                    if es_automatica:
                        color = self.colors['primary']
                        icon = ft.Icons.AUTO_MODE
                        estado_text = "Automática"
                        badge_bg = self.colors['primary']
                    else:
                        color = self.colors['success']
                        icon = ft.Icons.CHECK_CIRCLE_OUTLINE
                        estado_text = "Capturada"
                        badge_bg = self.colors['success']
                    
                    action_button = ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.IMAGE_SEARCH,
                            icon_color=self.colors['primary'],
                            tooltip="Previsualizar imagen",
                            on_click=lambda e, path=self.capturadas[slot_num]: self.show_preview(e, path),
                            icon_size=18
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=self.colors['error'],
                            tooltip="Eliminar captura",
                            on_click=lambda e, s=slot_num: self.on_delete_capture(s),
                            icon_size=18
                        )
                    ])
                else:
                    color = self.colors['text_secondary']
                    icon = ft.Icons.RADIO_BUTTON_UNCHECKED
                    estado_text = "Disponible" if es_automatica else "Pendiente"
                    badge_bg = self.colors['text_secondary']
                    action_button = ft.IconButton(
                        icon=ft.Icons.CAMERA_ALT_OUTLINED,
                        icon_color=self.colors['primary'],
                        tooltip="Realizar captura para este slot",
                        on_click=lambda e, s=slot_num: self.on_capture(e, s),
                        icon_size=18
                    )

                slot_colors = {
                    1: ft.colors.BLUE_600, 2: ft.colors.GREEN_600, 3: ft.colors.ORANGE_600,
                    4: ft.colors.PURPLE_600, 5: ft.colors.RED_600, 6: ft.colors.TEAL_600,
                    7: ft.colors.INDIGO_600, 8: ft.colors.PINK_600, 9: ft.colors.AMBER_600,
                    10: ft.colors.DEEP_ORANGE_600, 11: ft.colors.CYAN_600, 12: ft.colors.LIME_600,
                    13: ft.colors.DEEP_PURPLE_600, 14: ft.colors.BROWN_600, 15: ft.colors.BLUE_GREY_600
                }
                slot_color = slot_colors.get(slot_num, self.colors['primary'])
                
                badge = ft.Container(
                    content=ft.Text(estado_text, size=9, color=ft.colors.WHITE, weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    bgcolor=badge_bg,
                    border_radius=10
                )

                slot_indicator = ft.Container(
                    content=ft.Text(str(slot_num), size=11, color=ft.colors.WHITE, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                    width=24, height=24, bgcolor=slot_color, border_radius=12, alignment=ft.alignment.center
                )

                slot_card = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            slot_indicator,
                            ft.Container(width=6),
                            ft.Icon(icon, color=color, size=16),
                            ft.Container(width=4),
                            ft.Column([
                                ft.Text(descripcion, size=12, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
                                ft.Text(f"Slot {slot_num}", size=10, color=self.colors['text_secondary'], weight=ft.FontWeight.W_400)
                            ], spacing=1, expand=True)
                        ], spacing=0, expand=True),
                        ft.Row([
                            badge,
                            action_button
                        ], spacing=6, alignment=ft.MainAxisAlignment.END)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    margin=ft.margin.only(bottom=3),
                    bgcolor=ft.colors.with_opacity(0.04, slot_color) if capturada else ft.colors.with_opacity(0.02, slot_color),
                    border=ft.border.all(1, ft.colors.with_opacity(0.3, slot_color) if capturada else ft.colors.with_opacity(0.15, slot_color))
                )
                
                self.lista_capturas.controls.append(slot_card)
        
        if hasattr(self, 'progress_text') and hasattr(self, 'progress_bar'):
            automaticas = sum(1 for slot in self.capturadas.keys() if slot <= 5)
            manuales = sum(1 for slot in self.capturadas.keys() if slot > 5)
            total_automaticas_posibles = min(5, self.total_slots)
            total_manuales_posibles = max(0, self.total_slots - 5)
            
            progress_text = f"{len(self.capturadas)} de {self.total_slots} completadas"
            if total_automaticas_posibles > 0:
                progress_text += f" ({automaticas} automáticas"
                if total_manuales_posibles > 0:
                    progress_text += f", {manuales} manuales)"
                else:
                    progress_text += ")"
            else:
                progress_text += f" ({manuales} manuales)"
            
            self.progress_text.value = progress_text
            self.progress_text.color = self.colors['success'] if len(self.capturadas) == self.total_slots else self.colors['text_primary']
            self.progress_bar.value = len(self.capturadas) / self.total_slots if self.total_slots > 0 else 0
    
    def create_capturas_section(self, page=None):
        """Crea la sección de capturas con diseño profesional y previsualización integrada"""
        self.update_lista_capturas()
        altura = self.height
        if page is not None:
            altura = self.get_screen_height(page) - 120
            if altura < 400:
                altura = 400
        
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("Gestión de Capturas", size=16, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
                        ft.Container(expand=True),
                        self.agregar_imagenes_checkbox
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=18, vertical=12),
                    bgcolor=ft.colors.with_opacity(0.02, self.colors['primary']),
                    border_radius=8
                ),
                ft.Container(height=8),
                self.preview_container,  # Contenedor de previsualización
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.PURPLE_700, size=15),
                        ft.Text(
                            "Las primeras 5 imágenes se cargan automáticamente desde STAAD cuando están disponibles.",
                            size=11,
                            color=ft.Colors.PURPLE_800,
                            weight=ft.FontWeight.W_500
                        )
                    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=14, vertical=8),
                    bgcolor=ft.Colors.PURPLE_50,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.PURPLE_200)
                ),
                ft.Container(height=8),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Progreso", size=13, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
                            ft.Container(expand=True),
                            self.progress_text
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(height=6),
                        self.progress_bar
                    ]),
                    padding=ft.padding.symmetric(horizontal=18, vertical=10),
                    bgcolor=ft.colors.with_opacity(0.02, self.colors['border']),
                    border_radius=6,
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border']))
                ),
                ft.Container(height=8),
                ft.Row([
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CAMERA_ALT, size=14),
                                ft.Text("Nueva Captura", size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                            on_click=lambda e: self.on_capture(e, None),
                            bgcolor=self.colors['primary'],
                            color=ft.colors.WHITE,
                            height=36,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6), elevation={"hovered": 4})
                        ),
                        expand=True
                    ),
                    ft.Container(width=8),
                    ft.Container(
                        content=ft.OutlinedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CLEAR_ALL, size=14),
                                ft.Text("Limpiar Todo", size=12, weight=ft.FontWeight.W_500)
                            ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                            on_click=self.on_clear,
                            height=36,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=6),
                                color=self.colors['error'],
                                overlay_color=ft.colors.with_opacity(0.1, self.colors['error'])
                            )
                        ),
                        expand=True
                    )
                ], tight=True),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Estado de Capturas", size=14, weight=ft.FontWeight.W_600, color=self.colors['text_primary']),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(
                                    f"{len(self.capturadas)}/{self.total_slots}",
                                    size=12,
                                    weight=ft.FontWeight.W_500,
                                    color=self.colors['text_secondary'],
                                ),
                                bgcolor="e2e1e1",
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                border_radius=4,
                                border=ft.border.all(1, ft.colors.with_opacity(0.2, self.colors['border']))
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=6),
                        ft.Container(
                            content=self.lista_capturas,
                            expand=True,
                            border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])),
                            border_radius=6,
                            padding=8,
                            bgcolor="#f8f9fa",
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                        )
                    ], spacing=0, expand=True),
                    padding=ft.padding.symmetric(horizontal=18, vertical=12),
                    bgcolor="#e2e1e1",
                    border_radius=8,
                    border=ft.border.all(1, ft.colors.with_opacity(0.1, self.colors['border'])),
                    expand=True
                )
            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0),
            padding=ft.padding.all(16),
            height=altura,
            expand=True
        )
