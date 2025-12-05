# capture_area.py - Versión Mejorada - CORREGIDA MULTIMONITOR
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv
import os
import sys
import time
from datetime import datetime
import mss
from PIL import Image

load_dotenv()

class ScreenshotCapture:
    def __init__(self):
        self.start = None
        self.end = None
        self.rect = None
        self.canvas = None
        self.root = None
        self.countdown_active = False
        self.delay_seconds = int(os.getenv("CAPTURE_DELAY", "3"))
        self.captured_file = None  # AÑADIDO: Para almacenar la ruta del archivo
        self.monitor_area = self.get_monitor_area()  # (left, top, right, bottom)

    def get_monitor_area(self):
        # Detectar el área total de todos los monitores
        with mss.mss() as sct:
            monitors = sct.monitors[1:]  # [0] es el área virtual completa, [1:] son los monitores
            left = min(m['left'] for m in monitors)
            top = min(m['top'] for m in monitors)
            right = max(m['left'] + m['width'] for m in monitors)
            bottom = max(m['top'] + m['height'] for m in monitors)
            return (left, top, right, bottom)

    def show_countdown(self, delay=None):
        """Muestra countdown antes de la captura"""
        if delay is None:
            delay = self.delay_seconds
            
        countdown_window = tk.Tk()
        countdown_window.title("📸 Preparando Captura")
        width = 300
        height = 180
        countdown_window.geometry(f"{width}x{height}")
        countdown_window.configure(bg='#2c3e50')
        countdown_window.resizable(False, False)
        countdown_window.attributes('-topmost', True)
        
        # Centrar ventana
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - (width // 2)
        y = (countdown_window.winfo_screenheight() // 2) - (height // 2)
        countdown_window.geometry(f"+{x}+{y}")
        
        # Título
        tk.Label(
            countdown_window,
            text="🎯 Captura de Pantalla",
            font=('Arial', 14, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        ).pack(pady=15)
        
        # Instrucciones
        tk.Label(
            countdown_window,
            text="Ve a la ventana que deseas capturar\nEl selector aparecerá en:",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#2c3e50',
            justify='center'
        ).pack(pady=5)
        
        # Countdown display
        countdown_label = tk.Label(
            countdown_window,
            text=str(delay),
            font=('Arial', 28, 'bold'),
            fg='#e74c3c',
            bg='#2c3e50'
        )
        countdown_label.pack(pady=15)
        
        # Botón cancelar
        tk.Button(
            countdown_window,
            text="Cancelar",
            command=countdown_window.destroy,
            font=('Arial', 9),
            bg='#95a5a6',
            fg='white',
            relief='flat'
        ).pack(pady=5)
        
        self.countdown_active = True
        
        def update_countdown(remaining):
            if remaining > 0 and self.countdown_active:
                countdown_label.config(text=str(remaining))
                # Cambiar color según tiempo restante
                if remaining <= 1:
                    countdown_label.config(fg='#e74c3c')  # Rojo
                elif remaining <= 2:
                    countdown_label.config(fg='#f39c12')  # Naranja
                else:
                    countdown_label.config(fg='#27ae60')  # Verde
                countdown_window.after(1000, lambda: update_countdown(remaining - 1))
            else:
                countdown_window.destroy()
                if self.countdown_active:
                    self.start_selection()
        
        update_countdown(delay)
        countdown_window.mainloop()

    def start_selection(self):
        """Inicia el proceso de selección de área"""
        # Crear ventana de selección que cubra todos los monitores
        left, top, right, bottom = self.monitor_area
        width = right - left
        height = bottom - top
        self.root = tk.Tk()
        self.root.attributes("-alpha", 0.4)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.geometry(f"{width}x{height}+{left}+{top}")
        # Fondo gris claro
        self.root.configure(bg='#e5e5e5')
        self.canvas = tk.Canvas(
            self.root,
            cursor="crosshair",
            bg="#e5e5e5",  # gris claro
            highlightthickness=0,
            width=width,
            height=height
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        time.sleep(0.1)
        self.show_instructions(width)
        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", self.cancel_selection)
        self.root.bind("<Return>", self.on_button_release)
        self.root.focus_set()
        self.root.mainloop()

    def show_instructions(self, width=None):
        """Muestra instrucciones en pantalla"""
        if width is None:
            width = self.root.winfo_screenwidth()
        self.canvas.create_text(
            width // 2, 60,
            text="🎯 Arrastra para seleccionar el área que deseas capturar",
            fill='white',
            font=('Arial', 16, 'bold'),
            tags='instructions'
        )
        self.canvas.create_text(
            width // 2, 90,
            text="ESC = Cancelar | ENTER = Confirmar selección",
            fill='#bdc3c7',
            font=('Arial', 12),
            tags='instructions'
        )

    def on_button_press(self, event):
        """Maneja el evento de botón presionado"""
        self.start = (event.x, event.y)
        # Limpiar instrucciones
        self.canvas.delete('instructions')
        # Crear rectángulo inicial con borde rojo y sin relleno
        self.rect = self.canvas.create_rectangle(
            self.start[0], self.start[1],
            self.start[0], self.start[1],
            outline="#e53935",  # rojo fuerte
            width=3,
            fill='',
            dash=()
        )

    def on_move(self, event):
        """Maneja el movimiento del ratón durante la selección"""
        if self.rect and self.start:
            # Actualizar rectángulo
            self.canvas.coords(self.rect, self.start[0], self.start[1], event.x, event.y)
            # Mostrar dimensiones
            self.canvas.delete('dimensions')
            width = abs(event.x - self.start[0])
            height = abs(event.y - self.start[1])
            # Calcular posición del texto
            text_x = event.x + 15 if event.x < self.canvas.winfo_width() - 150 else event.x - 150
            text_y = event.y - 15 if event.y > 50 else event.y + 25
            self.canvas.create_text(
                text_x, text_y,
                text=f"📏 {width} × {height} px",
                fill='#e53935',  # rojo fuerte
                font=('Arial', 12, 'bold'),
                anchor='nw',
                tags='dimensions'
            )

    def on_button_release(self, event=None):
        """Maneja el evento de botón liberado"""
        if event:
            self.end = (event.x, event.y)
        elif self.start:
            self.end = self.start
            
        self.root.quit()
        self.root.destroy()
        
        # Procesar captura
        self.process_capture()

    def cancel_selection(self, event=None):
        """Cancela la selección"""
        print("❌ Captura cancelada por el usuario")
        self.captured_file = None  # AÑADIDO
        self.root.quit()
        self.root.destroy()

    def process_capture(self):
        """Procesa y guarda la captura"""
        if not self.start or not self.end:
            print("❌ No se seleccionó ninguna área")
            self.captured_file = None  # AÑADIDO
            return None
            
        x1, y1 = self.start
        x2, y2 = self.end
        # Ajustar a coordenadas absolutas de todos los monitores
        left, top, _, _ = self.monitor_area
        abs_x1 = min(x1, x2) + left
        abs_y1 = min(y1, y2) + top
        abs_x2 = max(x1, x2) + left
        abs_y2 = max(y1, y2) + top
        
        # Validar área mínima
        if abs(abs_x2 - abs_x1) < 10 or abs(abs_y2 - abs_y1) < 10:
            messagebox.showwarning("Área muy pequeña", "El área seleccionada es muy pequeña para ser capturada.")
            self.captured_file = None  # AÑADIDO
            return None
        
        try:
            with mss.mss() as sct:
                monitor = {"left": abs_x1, "top": abs_y1, "width": abs_x2 - abs_x1, "height": abs_y2 - abs_y1}
                sct_img = sct.grab(monitor)
                img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            
            # Generar nombre de archivo
            output_file = self.get_output_path()
            
            # Guardar imagen
            img.save(output_file, "PNG", optimize=True)
            
            # AÑADIDO: Almacenar la ruta del archivo
            self.captured_file = output_file
            
            # Información de la captura
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            success_message = (
                f"✅ Captura guardada exitosamente!\n\n"
                f"📍 Ubicación: {output_file}\n"
                f"📏 Dimensiones: {img.width} × {img.height} píxeles\n"
                f"💾 Tamaño: {file_size_mb:.2f} MB"
            )
            
            # Crear una ventana raíz temporal para el messagebox
            root = tk.Tk()
            root.withdraw() # Ocultar la ventana raíz
            messagebox.showinfo("Captura Exitosa", success_message)
            root.destroy()

            return output_file
            
        except Exception as e:
            messagebox.showerror("Error de Captura", f"Ocurrió un error al guardar la captura:\n{e}")
            self.captured_file = None  # AÑADIDO
            return None

    def get_output_path(self):
        """Genera la ruta de salida para el archivo de forma robusta."""
        import sys
        
        # Determinar la ruta base (ya sea para script o para ejecutable)
        if getattr(sys, 'frozen', False):
            # Estamos en un ejecutable (congelado por PyInstaller)
            base_dir = os.path.dirname(sys.executable)
        else:
            # Estamos ejecutando como un script normal
            # Asumimos que el script se ejecuta desde la raíz del proyecto
            base_dir = os.getcwd() 

        # Definir la carpeta de capturas relativa a la ruta base
        output_dir = os.path.join(base_dir, "data", "capturas")
        
        # Crear directorio si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captura_{timestamp}.png"
        
        return os.path.join(output_dir, filename)

def select_region_and_save(output_path="capture.png", delay=None):
    """
    Función principal CORREGIDA para captura de región
    
    Args:
        output_path (str): Ruta de salida (se usa solo si no hay OUTPUT_PATH_SCREENSHOTS en .env)
        delay (int): Segundos de delay antes de mostrar selector (None para usar .env)
    
    Returns:
        str: Ruta del archivo guardado o None si falló
    """
    try:
        capture = ScreenshotCapture()
        
        # Mostrar countdown
        if delay is not None:
            capture.delay_seconds = delay
            
        capture.show_countdown()
        
        # CORREGIDO: Retornar la ruta del archivo capturado
        return capture.captured_file
        
    except KeyboardInterrupt:
        print("\n❌ Captura interrumpida por el usuario")
        return None
    except Exception as e:
        print(f"❌ Error durante la captura: {e}")
        return None

def quick_capture(delay=3):
    """Captura rápida con delay personalizado"""
    return select_region_and_save(delay=delay)

def main():
    """Función principal"""
    print("🎯 Iniciando capturador de pantalla mejorado...")

    result = select_region_and_save()
    if result:
        print(f"🎯 Archivo guardado en: {result}")
    else:
        print("❌ No se pudo capturar la imagen")

if __name__ == "__main__":
    main()