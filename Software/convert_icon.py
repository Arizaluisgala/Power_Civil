from PIL import Image
import os

# Definir rutas
png_path = os.path.join("assets", "icon.png")
ico_path = os.path.join("assets", "icon.ico")

# Convertir la imagen
try:
    img = Image.open(png_path)
    img.save(ico_path, format='ICO', sizes=[(32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Imagen convertida a {ico_path}")
except Exception as e:
    print(f"Error al convertir la imagen: {e}")
