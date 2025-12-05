import flet as ft
import os
import time
import threading
import math


class PremiumNotificationManager:
    """Gestor de notificaciones premium con UI/UX profesional impactante"""
    
    def __init__(self, page: ft.Page, colors: dict):
        self.page = page
        self.colors = colors
        self.current_notification = None
        self.animation_container = None
        
    def show_generation_progress(self, mensaje="Generando memoria de cálculo..."):
        """Muestra notificación de progreso ultra profesional"""
        try:
            self._close_current_notification()
            
            # Crear elementos animados
            progress_ring = ft.ProgressRing(
                color="#FFFFFF",
                bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                width=60,
                height=60,
                stroke_width=4
            )
            
            # Contenedor del anillo con rotación infinita
            rotating_container = ft.Container(
                content=progress_ring,
                animate_rotation=ft.animation.Animation(
                    duration=2000,
                    curve=ft.AnimationCurve.LINEAR
                )
            )
            
            # Texto principal con animación de aparición
            main_text = ft.Text(
                "🚀 Generando Memoria",
                size=20,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER
            )
            
            # Subtexto con animación
            sub_text = ft.Text(
                mensaje,
                size=14,
                color=ft.colors.with_opacity(0.9, "#FFFFFF"),
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS
            )
            
            # Puntos animados para simular carga
            dots_container = ft.Row([
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=ft.colors.with_opacity(0.6, "#FFFFFF"),
                    border_radius=4,
                    animate=ft.animation.Animation(
                        duration=1000,
                        curve=ft.AnimationCurve.EASE_IN_OUT
                    )
                ),
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=ft.colors.with_opacity(0.6, "#FFFFFF"),
                    border_radius=4,
                    animate=ft.animation.Animation(
                        duration=1000,
                        curve=ft.AnimationCurve.EASE_IN_OUT
                    )
                ),
                ft.Container(
                    width=8,
                    height=8,
                    bgcolor=ft.colors.with_opacity(0.6, "#FFFFFF"),
                    border_radius=4,
                    animate=ft.animation.Animation(
                        duration=1000,
                        curve=ft.AnimationCurve.EASE_IN_OUT
                    )
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6
            )
            
            # Botón de cancelar elegante
            cancel_button = ft.Container(
                content=ft.Icon(
                    ft.icons.CLOSE_ROUNDED,
                    color="#FFFFFF",
                    size=20
                ),
                width=36,
                height=36,
                bgcolor=ft.colors.with_opacity(0.15, "#FFFFFF"),
                border_radius=18,
                on_click=self._close_current_notification,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                tooltip="Cancelar"
            )
            
            # Contenido principal de la notificación
            notification_content = ft.Container(
                content=ft.Column([
                    # Header con botón de cerrar
                    ft.Row([
                        ft.Container(expand=True),
                        cancel_button
                    ], alignment=ft.MainAxisAlignment.END),
                    
                    # Espacio
                    ft.Container(height=10),
                    
                    # Icono de carga rotatorio
                    ft.Container(
                        content=rotating_container,
                        alignment=ft.alignment.center
                    ),
                    
                    # Espacio
                    ft.Container(height=20),
                    
                    # Textos
                    main_text,
                    ft.Container(height=8),
                    sub_text,
                    
                    # Espacio
                    ft.Container(height=20),
                    
                    # Puntos animados
                    dots_container,
                    
                    # Espacio final
                    ft.Container(height=10)
                    
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
                ),
                width=380,
                height=280,
                padding=ft.padding.all(24),
                bgcolor=ft.colors.with_opacity(0.95, "#1E3A8A"),  # Azul profundo
                border_radius=20,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=30,
                    color=ft.colors.with_opacity(0.4, "#1E3A8A"),
                    offset=ft.Offset(0, 8)
                ),
                border=ft.border.all(1, ft.colors.with_opacity(0.2, "#FFFFFF")),
                animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
            )
            
            # Overlay con efecto glassmorphism
            self.current_notification = ft.Container(
                content=notification_content,
                bgcolor=ft.colors.with_opacity(0.8, "#000000"),
                alignment=ft.alignment.center,
                animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
                expand=True
            )
            
            # Agregar al overlay
            self.page.overlay.append(self.current_notification)
            self.page.update()
            
            # Iniciar animación de rotación
            rotating_container.rotate = 0
            rotating_container.update()
            
            # Animar puntos de carga
            self._animate_loading_dots(dots_container)
            
        except Exception as ex:
            print(f"Error creando notificación de progreso: {ex}")
    
    def show_success_notification(self, mensaje="Memoria generada exitosamente", ruta_archivo=None):
        """Muestra notificación de éxito ultra profesional"""
        try:
            self._close_current_notification()
            
            def abrir_archivo(e=None):
                if ruta_archivo and os.path.exists(ruta_archivo):
                    try:
                        os.startfile(ruta_archivo)
                    except:
                        os.startfile(os.path.dirname(ruta_archivo))
                self._close_current_notification()
            
            # Icono de éxito con animación
            success_icon = ft.Container(
                content=ft.Icon(
                    ft.icons.CHECK_CIRCLE_ROUNDED,
                    color="#FFFFFF",
                    size=48
                ),
                width=80,
                height=80,
                bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                border_radius=40,
                animate_scale=ft.animation.Animation(600, ft.AnimationCurve.BOUNCE_OUT),
                animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
            )
            
            # Texto principal
            main_text = ft.Text(
                "✨ ¡Éxito Total!",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER
            )
            
            # Subtexto
            sub_text = ft.Text(
                mensaje,
                size=16,
                color=ft.colors.with_opacity(0.9, "#FFFFFF"),
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS
            )
            
            # Botón de abrir archivo premium
            open_button = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.FOLDER_OPEN_ROUNDED, color="#10B981", size=20),
                    ft.Container(width=8),
                    ft.Text("Abrir Archivo", color="#10B981", size=16, weight=ft.FontWeight.W_600)
                ], alignment=ft.MainAxisAlignment.CENTER),
                width=200,
                height=48,
                bgcolor="#FFFFFF",
                border_radius=24,
                on_click=abrir_archivo,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=15,
                    color=ft.colors.with_opacity(0.3, "#FFFFFF"),
                    offset=ft.Offset(0, 4)
                )
            ) if ruta_archivo else ft.Container(height=0)
            
            # Botón de cerrar
            close_button = ft.Container(
                content=ft.Text("Cerrar", color="#FFFFFF", size=14, weight=ft.FontWeight.W_500),
                width=80,
                height=36,
                bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                border_radius=18,
                on_click=self._close_current_notification,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                alignment=ft.alignment.center
            )
            
            # Contenido principal
            notification_content = ft.Container(
                content=ft.Column([
                    # Espacio superior
                    ft.Container(height=20),
                    
                    # Icono de éxito
                    ft.Container(
                        content=success_icon,
                        alignment=ft.alignment.center
                    ),
                    
                    # Espacio
                    ft.Container(height=24),
                    
                    # Textos
                    main_text,
                    ft.Container(height=12),
                    sub_text,
                    
                    # Espacio
                    ft.Container(height=32),
                    
                    # Botones
                    open_button,
                    ft.Container(height=16),
                    close_button,
                    
                    # Espacio final
                    ft.Container(height=20)
                    
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
                ),
                width=400,
                height=320,
                padding=ft.padding.all(24),
                bgcolor=ft.colors.with_opacity(0.95, "#10B981"),  # Verde esmeralda
                border_radius=20,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=30,
                    color=ft.colors.with_opacity(0.4, "#10B981"),
                    offset=ft.Offset(0, 8)
                ),
                border=ft.border.all(1, ft.colors.with_opacity(0.3, "#FFFFFF")),
                animate=ft.animation.Animation(400, ft.AnimationCurve.BOUNCE_OUT)
            )
            
            # Overlay
            self.current_notification = ft.Container(
                content=notification_content,
                bgcolor=ft.colors.with_opacity(0.8, "#000000"),
                alignment=ft.alignment.center,
                animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
                expand=True
            )
            
            # Agregar al overlay
            self.page.overlay.append(self.current_notification)
            self.page.update()
            
            # Animar icono de éxito
            success_icon.scale = 0.3
            success_icon.update()
            time.sleep(0.1)
            success_icon.scale = 1.0
            success_icon.update()
            
        except Exception as ex:
            print(f"Error creando notificación de éxito: {ex}")
    
    def show_error_notification(self, mensaje="Ha ocurrido un error"):
        """Muestra notificación de error ultra profesional"""
        try:
            self._close_current_notification()
            
            # Icono de error con animación
            error_icon = ft.Container(
                content=ft.Icon(
                    ft.icons.ERROR_ROUNDED,
                    color="#FFFFFF",
                    size=48
                ),
                width=80,
                height=80,
                bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                border_radius=40,
                animate_scale=ft.animation.Animation(600, ft.AnimationCurve.BOUNCE_OUT),
                animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
            )
            
            # Texto principal
            main_text = ft.Text(
                "❌ Error Detectado",
                size=24,
                weight=ft.FontWeight.BOLD,
                color="#FFFFFF",
                text_align=ft.TextAlign.CENTER
            )
            
            # Subtexto
            sub_text = ft.Text(
                mensaje,
                size=16,
                color=ft.colors.with_opacity(0.9, "#FFFFFF"),
                text_align=ft.TextAlign.CENTER,
                max_lines=3,
                overflow=ft.TextOverflow.ELLIPSIS
            )
            
            # Botón de cerrar
            close_button = ft.Container(
                content=ft.Text("Entendido", color="#FFFFFF", size=16, weight=ft.FontWeight.W_600),
                width=150,
                height=48,
                bgcolor=ft.colors.with_opacity(0.2, "#FFFFFF"),
                border_radius=24,
                on_click=self._close_current_notification,
                animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_OUT),
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=15,
                    color=ft.colors.with_opacity(0.3, "#FFFFFF"),
                    offset=ft.Offset(0, 4)
                )
            )
            
            # Contenido principal
            notification_content = ft.Container(
                content=ft.Column([
                    # Espacio superior
                    ft.Container(height=20),
                    
                    # Icono de error
                    ft.Container(
                        content=error_icon,
                        alignment=ft.alignment.center
                    ),
                    
                    # Espacio
                    ft.Container(height=24),
                    
                    # Textos
                    main_text,
                    ft.Container(height=12),
                    sub_text,
                    
                    # Espacio
                    ft.Container(height=32),
                    
                    # Botón
                    close_button,
                    
                    # Espacio final
                    ft.Container(height=20)
                    
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
                ),
                width=400,
                height=300,
                padding=ft.padding.all(24),
                bgcolor=ft.colors.with_opacity(0.95, "#EF4444"),  # Rojo vibrante
                border_radius=20,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=30,
                    color=ft.colors.with_opacity(0.4, "#EF4444"),
                    offset=ft.Offset(0, 8)
                ),
                border=ft.border.all(1, ft.colors.with_opacity(0.3, "#FFFFFF")),
                animate=ft.animation.Animation(400, ft.AnimationCurve.BOUNCE_OUT)
            )
            
            # Overlay
            self.current_notification = ft.Container(
                content=notification_content,
                bgcolor=ft.colors.with_opacity(0.8, "#000000"),
                alignment=ft.alignment.center,
                animate_opacity=ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT),
                expand=True
            )
            
            # Agregar al overlay
            self.page.overlay.append(self.current_notification)
            self.page.update()
            
            # Animar icono de error
            error_icon.scale = 0.3
            error_icon.update()
            time.sleep(0.1)
            error_icon.scale = 1.0
            error_icon.update()
            
        except Exception as ex:
            print(f"Error creando notificación de error: {ex}")
    
    def _close_current_notification(self, e=None):
        """Cierra la notificación actual con animación"""
        try:
            if self.current_notification and self.current_notification in self.page.overlay:
                # Animar salida
                self.current_notification.animate_opacity = ft.animation.Animation(200, ft.AnimationCurve.EASE_IN)
                self.current_notification.opacity = 0
                self.current_notification.update()
                
                # Remover después de la animación
                def remove_notification():
                    time.sleep(0.3)
                    try:
                        if self.current_notification in self.page.overlay:
                            self.page.overlay.remove(self.current_notification)
                            self.current_notification = None
                            self.page.update()
                    except:
                        pass
                
                threading.Thread(target=remove_notification, daemon=True).start()
                
        except Exception as ex:
            print(f"Error cerrando notificación: {ex}")
    
    def _animate_loading_dots(self, dots_container):
        """Anima los puntos de carga"""
        def animate_dots():
            try:
                counter = 0
                while self.current_notification:
                    for i, dot in enumerate(dots_container.controls):
                        if not self.current_notification:
                            break
                        
                        # Calcular delay basado en el índice
                        delay = i * 0.2
                        
                        # Animar opacidad
                        if (counter + i) % 3 == 0:
                            dot.bgcolor = ft.colors.with_opacity(1.0, "#FFFFFF")
                        else:
                            dot.bgcolor = ft.colors.with_opacity(0.3, "#FFFFFF")
                        
                        dot.update()
                    
                    counter += 1
                    time.sleep(0.6)
                    
            except Exception as ex:
                print(f"Error animando puntos: {ex}")
        
        threading.Thread(target=animate_dots, daemon=True).start()


# Función helper para usar fácilmente
def create_premium_notification_manager(page: ft.Page, colors: dict = None):
    """Crea una instancia del gestor de notificaciones premium"""
    if colors is None:
        colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'error': '#F44336',
            'warning': '#FF9800'
        }
    
    return PremiumNotificationManager(page, colors)


# Ejemplo de uso
def main(page: ft.Page):
    """Función de ejemplo para probar las notificaciones"""
    page.title = "Premium Notifications Demo"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    
    # Crear el gestor de notificaciones
    notification_manager = create_premium_notification_manager(page)
    
    def show_progress(e):
        notification_manager.show_generation_progress("Generando memoria de cálculo detallada...")
        
        # Simular proceso y mostrar éxito después de 5 segundos
        def simulate_process():
            time.sleep(5)
            notification_manager.show_success_notification(
                "Memoria generada exitosamente",
                "C:/temp/memoria_calculo.pdf"
            )
        
        threading.Thread(target=simulate_process, daemon=True).start()
    
    def show_error(e):
        notification_manager.show_error_notification(
            "No se pudo generar la memoria de cálculo. Verifique los datos ingresados."
        )
    
    # Botones de prueba
    page.add(
        ft.Column([
            ft.Text("Premium Notifications Demo", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=20),
            ft.ElevatedButton("Generar Memoria", on_click=show_progress, bgcolor="#2196F3"),
            ft.ElevatedButton("Mostrar Error", on_click=show_error, bgcolor="#F44336"),
        ])
    )

if __name__ == "__main__":
    ft.app(target=main)