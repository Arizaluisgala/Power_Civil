#!/usr/bin/env python3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # O 'Agg' si solo quieres guardar imágenes
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import filedialog

load_dotenv()

pd.set_option('display.max_rows', None)  # Mostrar todas las filas

def select_excel_file(file_path_excel=None):
    """
    Devuelve la ruta del archivo Excel. Si se proporciona file_path_excel y existe, la retorna.
    Si no, abre un diálogo para seleccionar el archivo. Si falla, pide la ruta manualmente.
    Retorna la ruta del archivo seleccionado o None si se cancela.
    """
    if file_path_excel and os.path.exists(file_path_excel):
        return file_path_excel

    try:
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Selecciona el archivo Excel",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        root.destroy()
        if file_path:
            return file_path
    except Exception:
        pass

    # Si falla el diálogo o no se selecciona archivo, pedir manualmente
    return manual_file_selection()

def manual_file_selection():
    """
    Pide al usuario que ingrese manualmente la ruta del archivo Excel.
    """
    print("\n" + "="*50)
    print("SELECCIÓN MANUAL DE ARCHIVO")
    print("="*50)
    print("Opciones:")
    print("1. Ingresa la ruta completa del archivo")
    print("2. Si el archivo está en el escritorio, solo ingresa el nombre")
    print("3. Presiona Enter para cancelar")
    print("-"*50)
    
    desktop_path = os.path.expanduser("~/Desktop")
    print(f"Ruta del escritorio: {desktop_path}")
    
    while True:
        try:
            user_input = input("\nRuta del archivo Excel: ").strip()
            
            if not user_input:
                print("Operación cancelada.")
                return None
            
            # Si no tiene ruta completa, buscar en el escritorio
            if not os.path.dirname(user_input):
                potential_path = os.path.join(desktop_path, user_input)
                if os.path.exists(potential_path):
                    print(f"Archivo encontrado en el escritorio: {potential_path}")
                    return potential_path
            
            # Verificar si la ruta existe
            if os.path.exists(user_input):
                # Verificar que sea un archivo Excel
                if user_input.lower().endswith((".xlsx", ".xls")):
                    print(f"Archivo Excel válido: {user_input}")
                    return user_input
                else:
                    print("El archivo no es un Excel (.xlsx o .xls)")
                    continue
            else:
                print("Archivo no encontrado. Verifica la ruta.")
                
                # Sugerencias útiles
                print("Sugerencias:")
                print(f"   - Si está en el escritorio: {desktop_path}")
                print("   - Usa comillas si la ruta tiene espacios: \"mi archivo.xlsx\"")
                print("   - Usa barras / o dobles barras \\")
                
                # Mostrar archivos Excel en el escritorio
                try:
                    excel_files = [f for f in os.listdir(desktop_path) 
                                 if f.lower().endswith((".xlsx", ".xls"))]
                    if excel_files:
                        print("Archivos Excel en el escritorio:")
                        for i, f in enumerate(excel_files[:5], 1):  # Mostrar máximo 5
                            print(f"   {i}. {f}")
                except:
                    pass
                    
        except (EOFError, KeyboardInterrupt):
            print("\nOperación cancelada.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            continue

def select_sheet_name(excel_file):
    """
    Permite al usuario seleccionar la hoja de cálculo si hay múltiples hojas.
    """
    try:
        # Leer las hojas disponibles
        excel_file_obj = pd.ExcelFile(excel_file)
        sheet_names = excel_file_obj.sheet_names
        
        if len(sheet_names) == 1:
            print(f"Usando la única hoja disponible: {sheet_names[0]}")
            return sheet_names[0]
        
        # Si hay múltiples hojas, mostrar opciones
        print(f"\nHojas disponibles en el archivo:")
        for i, sheet in enumerate(sheet_names, 1):
            print(f"{i}. {sheet}")
        
        while True:
            try:
                choice = input(f"\nSelecciona la hoja (1-{len(sheet_names)}) o presiona Enter para usar la primera: ").strip()
                if not choice:
                    print(f"Usando la primera hoja: {sheet_names[0]}")
                    return sheet_names[0]
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(sheet_names):
                    print(f"Seleccionada: {sheet_names[choice_idx]}")
                    return sheet_names[choice_idx]
                else:
                    print("Opción inválida. Intenta de nuevo.")
            except ValueError:
                print("Por favor ingresa un número válido.")
            except (EOFError, KeyboardInterrupt):
                print(f"\nUsando la primera hoja por defecto: {sheet_names[0]}")
                return sheet_names[0]
    
    except Exception as e:
        print(f"Error al leer las hojas del archivo: {e}")
        return "Sheet"  # Valor por defecto

def load_spectrum_data(excel_path: str, sheet_name: str) -> pd.DataFrame:
    """Carga los datos del espectro desde una hoja de Excel de forma más robusta, buscando dinámicamente los encabezados."""
    df_raw = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl"
    )

    start_row_idx = None
    
    # 1. Buscar la celda que contiene "Spectrum Data" (case-insensitive)
    for idx, row in df_raw.iterrows():
        for col_idx, cell_value in enumerate(row):
            if isinstance(cell_value, str) and "spectrum data" in cell_value.lower():
                start_row_idx = idx
                break
        if start_row_idx is not None:
            break
            
    if start_row_idx is None:
        raise ValueError("No se encontró el ancla 'Spectrum Data' en la hoja.")

    # 2. Buscar la fila de encabezados dinámicamente
    header_row_idx = None
    header_map = {}  # Mapa de nombre de columna a índice de columna

    # Búsqueda en un rango de filas después del ancla
    for idx in range(start_row_idx + 1, min(start_row_idx + 10, len(df_raw))):
        row = df_raw.iloc[idx]
        temp_headers = {}
        
        # Identificar columnas por contenido del encabezado
        for col_idx, cell_value in enumerate(row):
            if isinstance(cell_value, str):
                cell_lower = cell_value.lower().strip()
                if "lctitle" in cell_lower:
                    temp_headers["LCTitle"] = col_idx
                elif "period" in cell_lower:
                    temp_headers["Period"] = col_idx
                elif "acc" in cell_lower:  # Coincide con 'Acc.' o 'Acceleration'
                    temp_headers["Acc."] = col_idx
        
        # Si encontramos los encabezados clave, hemos localizado la fila
        if "LCTitle" in temp_headers and "Period" in temp_headers and "Acc." in temp_headers:
            header_row_idx = idx
            header_map = temp_headers
            break

    if header_row_idx is None:
        raise ValueError("No se encontró la fila de encabezados con 'LCTitle', 'Period' y 'Acc.' después del ancla.")

    # 3. Extraer los datos usando los índices de columna encontrados
    col_indices = [header_map["LCTitle"], header_map["Period"], header_map["Acc."]]
    df_data = df_raw.iloc[header_row_idx + 1:, col_indices].copy()
    df_data.columns = ["LCTitle", "Period", "Acc."]

    # Propagar el valor de LCTitle hacia abajo
    if 'LCTitle' in df_data.columns:
        df_data['LCTitle'] = df_data['LCTitle'].ffill()

    # Limpiar y convertir a numérico
    for col in ["Period", "Acc."]:
        if col in df_data.columns:
            df_data[col] = pd.to_numeric(df_data[col], errors='coerce')

    # Eliminar filas donde los valores numéricos son NaN o LCTitle es NaN
    df_data_cleaned = df_data.dropna(subset=["Period", "Acc.", "LCTitle"])

    return df_data_cleaned


def get_spectrum_axes(excel_path: str, sheet_name: str = "Sheet") -> dict:
    """
    Busca la tabla de 'Spectrum Parameters' a partir de las columnas 'L/C' y 'Parameter' 
    y devuelve un dict {load_case: eje}, donde eje es X, Y o Z.
    """
    print(f"Buscando ejes de espectro en: {excel_path} - Hoja: {sheet_name}")
    try:
        # 1) Carga toda la hoja sin encabezados
        df = pd.read_excel(excel_path, sheet_name=sheet_name,
                           header=None, engine="openpyxl")
        
        # 2) Encuentra la fila que contiene ambos 'L/C' y 'Parameter'
        mask = df.apply(
            lambda row: row.astype(str).str.contains("L/C|Load Case|Case", case=False).any() 
                      and row.astype(str).str.contains("Parameter", case=False).any(),
            axis=1
        )
        if not mask.any():
            print("No se encontró la fila de encabezados con 'L/C' y 'Parameter'.")
            return {}
        header_idx = mask[mask].index[0]
        print(f"Fila de encabezado encontrada en el índice: {header_idx}")
        
        # 3) Identifica los índices de columna exactos
        header = df.iloc[header_idx].astype(str)
        col_LC    = header.str.contains("L/C|Load Case|Case", case=False).idxmax()
        col_param = header.str.contains("Parameter", case=False).idxmax()
        print(f"Índice de columna para 'L/C': {col_LC}")
        print(f"Índice de columna para 'Parameter': {col_param}")
        
        # 4) Recorre las filas debajo de los encabezados
        axes = {}
        current_lc = None
        for i in range(header_idx + 1, len(df)):
            lc_val    = df.iat[i, col_LC]
            param_val = df.iat[i, col_param]
            
            # Descomentar para depuración detallada
            # print(f"Fila {i}: L/C='{lc_val}', Parameter='{param_val}'")

            # si aparece un nuevo L/C no nulo, actualizamos current_lc
            if pd.notna(lc_val):
                try:
                    current_lc = int(float(lc_val))
                except:
                    current_lc = None
            
            # si current_lc válido y Parameter es X/Y/Z, registramos
            if current_lc is not None and pd.notna(param_val):
                eje = str(param_val).strip().upper()
                if eje in ("X", "Y", "Z"):
                    axes[current_lc] = eje
                    print(f"Eje encontrado: L/C={current_lc}, Eje={eje}")
        
        if not axes:
            print("No se encontraron pares Load Case ↔ Eje en la hoja.")
        else:
            print(f"Pares Load Case ↔ Eje encontrados: {axes}")
        return axes
    except Exception as e:
        print(f"Error al buscar ejes de espectro: {e}")
        return {}


def leyenda_espectro(eje, lang="es"):
    eje_str = str(eje).strip().upper()
    if lang == "es":
        if eje_str == "X":
            return "Espectro de diseño modificado (Eje X)"
        elif eje_str == "Z":
            return "Espectro de diseño modificado (Eje Z)"
        elif eje_str == "Y":
            return "Espectro de diseño modificado (Eje Y)"
        else:
            return "Espectro de diseño modificado (Eje no identificado)"
    else:
        if eje_str == "X":
            return "Modified design spectrum (Axis X)"
        elif eje_str == "Z":
            return "Modified design spectrum (Axis Z)"
        elif eje_str == "Y":
            return "Modified design spectrum (Axis Y)"
        else:
            return "Modified design spectrum (Axis not identified)"

def plot_spectrum(df: pd.DataFrame, x_col: str, y_col: str, axes_dict=None, lang="es", output_dir="output/spectrums"):
    import numpy as np
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    for case, group in df.groupby('LCTitle'):
        eje = axes_dict.get(case, "")
        leyenda = leyenda_espectro(eje, lang)
        leyenda_inf = ""  # Puedes personalizar este texto si lo necesitas
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            group[x_col], group[y_col],
            linestyle='-', linewidth=2, color='green'
        )
        ax.set_xlabel("Te(s)")
        ax.set_ylabel("a ´ (1/g)")
        ax.set_title(leyenda, pad=20)
        ax.grid(True, which='both', linestyle='--', alpha=0.7)
        ax.set_xticks(np.arange(0, group[x_col].max() + 0.5, 0.5))
        ax.set_yticks(np.arange(0, group[y_col].max() + 0.1, 0.1))
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        # Leyenda abajo de la gráfica
        plt.figtext(0.5, 0.01, leyenda_inf, ha="center", fontsize=10)
        plt.tight_layout(rect=[0, 0.03, 1, 1])  # deja espacio abajo para la leyenda
        img_path = os.path.join(output_dir, f"spectrum_case_{int(case)}.png")
        plt.savefig(img_path, dpi=150)
        plt.close(fig)
        image_paths.append(img_path)
    return image_paths
    
def generar_spectrums_from_excel(excel_file=None, lang="es", sheet_name=None, output_dir="output/spectrums"):
    """
    Genera las gráficas de espectro a partir de un archivo Excel.
    Si no se proporciona excel_file, abre un diálogo para seleccionarlo.
    Si no se proporciona sheet_name, itera sobre todas las hojas.
    Retorna una lista de tuplas (ruta_imagen, eje).
    """
    if excel_file is None:
        excel_file = select_excel_file()
        if excel_file is None:
            print("Operación cancelada por el usuario.")
            return []

    all_results = []
    
    if sheet_name:
        sheet_names_to_try = [sheet_name]
    else:
        try:
            excel_file_obj = pd.ExcelFile(excel_file)
            sheet_names_to_try = excel_file_obj.sheet_names
        except Exception as e:
            print(f"Error al leer las hojas del archivo: {e}")
            return []

    for s_name in sheet_names_to_try:
        print(f"Procesando archivo: {excel_file}")
        print(f"Hoja seleccionada: {s_name}")

        try:
            df_spectrum = load_spectrum_data(excel_file, sheet_name=s_name)
            axes_dict = get_spectrum_axes(excel_file, sheet_name=s_name)

            x_column = "Period"
            y_column = "Acc."

            if x_column not in df_spectrum.columns or y_column not in df_spectrum.columns:
                raise ValueError(
                    f"No se encontraron las columnas '{x_column}' y/o '{y_column}' en los datos. "
                    f"Columnas disponibles: {list(df_spectrum.columns)}"
                )

            # Generar imágenes y asociar eje
            import numpy as np
            os.makedirs(output_dir, exist_ok=True)
            result = []
            for case, group_df in df_spectrum.groupby('LCTitle'):
                group = group_df.sort_values(by=x_column).reset_index(drop=True)
                
                case_int = 0 # Default value
                try:
                    case_int = int(float(case))
                    eje = axes_dict.get(case_int, "")
                except (ValueError, TypeError):
                    eje = ""

                leyenda = leyenda_espectro(eje, lang)
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(
                    group[x_column], group[y_column],
                    linestyle='-', linewidth=2, color='green'
                )
                ax.set_xlabel("Te(s)")
                ax.set_ylabel("a ´ (1/g)")
                ax.set_title(leyenda, pad=20)
                ax.grid(True, which='both', linestyle='--', alpha=0.7)

                # Ajustar la escala del gráfico a los datos
                ax.set_xlim(0, group[x_column].max() * 1.05)
                ax.set_ylim(0, group[y_column].max() * 1.1)

                # Consider only the first third of the data for finding the plateau
                first_third_idx = len(group) // 3
                group_first_third = group.iloc[:first_third_idx]

                if not group_first_third.empty:
                    # Identify the plateau value from the first third
                    rounded_acc_values_ft = group_first_third[y_column].round(3)
                    value_counts_ft = rounded_acc_values_ft.value_counts()

                    if not value_counts_ft.empty:
                        plateau_value = value_counts_ft.idxmax()

                        # Find all indices in the whole group where this value appears
                        rounded_acc_values_full = group[y_column].round(3)
                        plateau_indices = group.index[rounded_acc_values_full == plateau_value].tolist()

                        if plateau_indices:
                            # Find the first continuous block of indices
                            first_block_start = plateau_indices[0]
                            first_block_end = first_block_start
                            for i in range(1, len(plateau_indices)):
                                if plateau_indices[i] == first_block_end + 1:
                                    first_block_end = plateau_indices[i]
                                else:
                                    break
                            
                            # Get the corresponding period (x) values for the first block
                            x_plateau_for_pos = group.loc[first_block_start:first_block_end, x_column]
                            
                            if not x_plateau_for_pos.empty:
                                x_text_pos = (x_plateau_for_pos.min() + x_plateau_for_pos.max()) / 2
                            else: # Fallback
                                x_text_pos = group.loc[first_block_start, x_column]
                        else: # Fallback
                            x_text_pos = group[x_column].mean()
                    else:
                        # Fallback
                        plateau_value = group[y_column].max()
                        x_text_pos = group[x_column].mean()
                else:
                    # Fallback for very short data
                    plateau_value = group[y_column].max()
                    x_text_pos = group[x_column].mean()


                ax.text(x_text_pos, plateau_value, f'{plateau_value:.3f}', color='darkred', 
                        va='bottom', ha='center', fontsize=10, fontweight='bold',
                        bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', boxstyle='round,pad=0.2'))

                plt.tight_layout(rect=[0, 0.03, 1, 1])
                
                # Generar nombre de archivo con el eje
                img_filename = f"spectrum_case_{case_int}"
                if eje:
                    img_filename += f"_eje_{eje}"
                img_filename += ".png"
                img_path = os.path.join(output_dir, img_filename)

                plt.savefig(img_path, dpi=150)
                plt.close(fig)
                result.append((img_path, eje))
            
            all_results.extend(result)
            print(f"Se encontraron y procesaron datos en la hoja '{s_name}'.")

        except ValueError as e:
            # This is expected if the sheet doesn't contain the spectrum data
            print(f"No se encontraron datos de espectro en la hoja '{s_name}': {e}")
        except Exception as e:
            print(f"Error procesando la hoja '{s_name}': {e}")
            
    return all_results

def main():
    """Función principal para ejecutar el script de forma interactiva."""
    print("=== Generador de Gráficas de Espectro ===")
    print("Este script generará gráficas de espectro desde un archivo Excel.")
    
    try:
        # Seleccionar idioma
        while True:
            try:
                lang_choice = input("\nSelecciona el idioma (es/en) [es]: ").strip().lower()
                if not lang_choice:
                    lang = "es"
                    break
                elif lang_choice in ["es", "en"]:
                    lang = lang_choice
                    break
                else:
                    print("Opción inválida. Usa 'es' para español o 'en' para inglés.")
            except EOFError:
                print("\nUsando configuración por defecto: idioma español")
                lang = "es"
                break
        
        # Seleccionar directorio de salida
        try:
            output_choice = input(f"\nDirectorio de salida [output/spectrums]: ").strip()
            output_dir = output_choice if output_choice else "output/spectrums"
        except EOFError:
            print("Usando directorio por defecto: output/spectrums")
            output_dir = "output/spectrums"
        
        print(f"\nConfiguración:")
        print(f"  - Idioma: {lang}")
        print(f"  - Directorio de salida: {output_dir}")
        
        print(f"\nAhora selecciona el archivo Excel...")
        
        # Generar las gráficas
        rutas = generar_spectrums_from_excel(lang=lang, output_dir=output_dir)
        
        if rutas:
            print(f"Se generaron {len(rutas)} gráfica(s) exitosamente:")
            for ruta in rutas:
                print(f"  - {ruta}")
            print(f"\nLas imágenes se guardaron en: {os.path.abspath(output_dir)}")
        else:
            print("No se generaron gráficas.")
            
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

# --- Bloque de test opcional ---
if __name__ == "__main__":
    # Verificar si se está ejecutando directamente o con argumentos
    import sys
    
    if len(sys.argv) > 1:
        # Modo compatible con versión anterior (con archivo especificado)
        load_dotenv()
        excel_file = sys.argv[1] if len(sys.argv) > 1 else os.getenv('REPORT_FILE_PATH', 'XtraReport.xlsx')
        lang = sys.argv[2] if len(sys.argv) > 2 else "es"
        try:
            rutas = generar_spectrums_from_excel(excel_file, lang)
            print("Imágenes generadas:", rutas)
        except Exception as e:
            print("Error:", e)
    else:
        # Modo interactivo
        main()
