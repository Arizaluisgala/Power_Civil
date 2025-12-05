import pandas as pd
import os 
from dotenv import load_dotenv

load_dotenv()

def extract_tables_from_excel_materiales(file_path):
    """
    Extrae la tabla de materiales (hoja 'MC') ignorando filas vacías al inicio,
    y solo devuelve las filas y columnas que contienen datos.
    """
    try:
        xls = pd.ExcelFile(file_path)
        if 'MC' not in xls.sheet_names:
            print("Sheet 'MC' not found in the Excel file.")
            return {}

        mc_table = pd.read_excel(xls, sheet_name='MC', header=None)

        # Ignorar filas vacías al inicio
        first_data_row = 0
        for idx, row in mc_table.iterrows():
            if row.notna().any():
                first_data_row = idx
                break

        mc_table = mc_table.iloc[first_data_row:]  # Solo desde la primera fila con datos

        # Eliminar columnas y filas completamente vacías
        mc_table = mc_table.dropna(axis=1, how='all')
        mc_table = mc_table.dropna(axis=0, how='all')
        mc_table = mc_table.loc[:, mc_table.notna().any(axis=0)]
        mc_table = mc_table[mc_table.notna().any(axis=1)]

        # Restablecer el índice y poner la primera fila como encabezado si es texto
        mc_table = mc_table.reset_index(drop=True)
        if mc_table.shape[0] > 1 and mc_table.iloc[0].apply(lambda x: isinstance(x, str)).all():
            mc_table.columns = mc_table.iloc[0]
            mc_table = mc_table[1:].reset_index(drop=True)

        return {'MC': mc_table}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}
    
def extract_tables_from_excel_soportes_asignados_a_la_estructura(file_path):
    try:
        # Extraigo la tabla de soportes asignados a la estructura del excel que me viene por path con loatdev
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        
        # Segunda tabla a extraer la de soportes asignados a la estructura que en el excel esta en una hoja llamada Soporte
        if 'Soporte' in xls.sheet_names: # Verifico si la hoja 'Soporte' existe
        # Extraigo tres columnas a b c y todas las filas bajando hasta que encuentre una fila vacia 
            soporte_table = pd.read_excel(xls, sheet_name='Soporte', usecols='A:C') # Extraigo la tabla de la hoja 'Soporte'
            soporte_table = soporte_table.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías
            soporte_table = soporte_table.dropna(axis=0, how='all')  # Eliminar filas completamente vacías
            soporte_table = soporte_table.loc[:, soporte_table.notna().any(axis=0)]  # Extraer solo columnas con datos
            # Extraer solo las filas que tienen datos en la columnnas
            soporte_table = soporte_table[soporte_table.notna().any(axis=1)]
            return {'Soporte': soporte_table}  # Retorno la tabla de soportes como un DataFrame
        else:
            print("Sheet 'Soporte' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}
    
def extract_tables_from_excel_miembros_fisicos(file_path):
    try:
        # Extraigo tabla de miembros fisicos PM    
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        
        # Extraigo la tabla de miembros fisicos PM que en el excel esta en una hoja llamada PM
        if 'PM' in xls.sheet_names:  # Verifico si la hoja 'PM' existe
            # Extraigo desde la columna A hasta la columna E 
            # Transofomo la primera fila de esas columas que el texto sea en español o ingles 
            pm_table = pd.read_excel(xls, sheet_name='PM', usecols='A:E')  # Extraigo la tabla de la hoja 'PM'
            # Elimino la columna que trae los números de la fila
            pm_table = pm_table.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías
            pm_table = pm_table.dropna(axis=0, how='all')  # Eliminar filas completamente vacías
            pm_table = pm_table.loc[:, pm_table.notna().any(axis=0)]  # Extraer solo columnas con datos 
            pm_table = pm_table[pm_table.notna().any(axis=1)]  # Extraer solo las filas que tienen datos
            return {'PM': pm_table}  # Retorno la tabla de miembros fisicos PM como un DataFrame
        else:
            print("Sheet 'PM' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}    
    
def extract_tables_from_excel_rangos_de_combinaciones_de_carga(file_path):
    """
    Extrae de la hoja "Rangos" los encabezados (fila 11) y los valores de "rango inicial"
    (fila 15) y "rango final" (fila 16) de las columnas D:H. Si ambas filas 15 y 16 están
    vacías, busca la primera fila no vacía en columna D a partir de la fila 20 y la usa como
    "rango inicial", y la siguiente fila como "rango final".
    
    Retorna un dict con:
        {
          "headers": [...],        # lista de strings, valores de fila 11, columnas D–H
          "rango_inicial": [...],  # lista de valores (floats o strings) de la fila 15 o la encontrada
          "rango_final": [...],    # lista de valores de la fila 16 o la siguiente a la encontrada
        }
    """
    try:
        # 1) Leer todo el sheet "Rangos" sin usar ninguna fila como header
        xls = pd.ExcelFile(file_path)
        if 'Rangos' not in xls.sheet_names:
            print("Sheet 'Rangos' no encontrada en el archivo")
            return {}

        df = pd.read_excel(xls, sheet_name='Rangos', header=None)

        # 2) Cabeceras en fila 11 (índice 10), columnas D(3) a H(7)
        if df.shape[0] < 11:
            raise ValueError("La hoja 'Rangos' no tiene al menos 11 filas.")
        headers = df.iloc[10, 3:8].tolist()

        # 3) Leer “rango inicial” fila 15 (índice 14), columnas D–H
        rango_inicial = df.iloc[14, 3:8].tolist()
        # 4) Leer “rango final” fila 16 (índice 15), columnas D–H
        rango_final = df.iloc[15, 3:8].tolist()

        # 5) Comprobar si ambas filas 15 y 16 están completamente vacías (todas las celdas NaN)
        is_inicial_empty = all(pd.isna(x) for x in rango_inicial)
        is_final_empty = all(pd.isna(x) for x in rango_final)

        if is_inicial_empty and is_final_empty:
            # Buscar desde fila 20 (índice 19) hacia abajo la primera fila cuyo valor en columna D no sea NaN
            encontrado = False
            for idx in range(19, len(df)):
                celda_d = df.iat[idx, 3]  # columna D
                if not pd.isna(celda_d):
                    # Tomamos esta fila como “rango_inicial”
                    rango_inicial = df.iloc[idx, 3:8].tolist()
                    # Intentamos tomar la siguiente fila (idx+1) como “rango_final”, si existe
                    if idx + 1 < len(df):
                        rango_final = df.iloc[idx + 1, 3:8].tolist()
                    else:
                        rango_final = [None] * 5
                    encontrado = True
                    break

            if not encontrado:
                # Si no se encuentra ninguna fila no vacía desde la 20, devolvemos vacíos
                rango_inicial = [None] * 5
                rango_final = [None] * 5

        # 6) Convertir NaN a cadenas vacías para que Word no imprima “nan”
        rango_inicial = ["" if pd.isna(x) else x for x in rango_inicial]
        rango_final   = ["" if pd.isna(x) else x for x in rango_final]
        headers       = ["" if pd.isna(x) else str(x) for x in headers]

        return {
            "headers":        headers,
            "rango_inicial":  rango_inicial,
            "rango_final":    rango_final
        }

    except Exception as e:
        print(f"Error al leer rangos de combinaciones de carga: {e}")
        return {}
        
def _extract_generic_table(file_path, sheet_name, table_key):
    """Función genérica y robusta para extraer una tabla de una hoja."""
    try:
        xls = pd.ExcelFile(file_path)
        if sheet_name not in xls.sheet_names:
            print(f"Sheet '{sheet_name}' not found in the Excel file.")
            return {}

        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        # Encontrar la primera fila con datos para usarla como encabezado
        header_row_index = -1
        for i, row in df.iterrows():
            if row.notna().sum() > 1:  # Considerar una fila como encabezado si tiene más de un valor
                header_row_index = i
                break
        
        if header_row_index != -1:
            table = pd.read_excel(xls, sheet_name=sheet_name, header=header_row_index)
            table = table.dropna(axis=1, how='all') # Eliminar columnas completamente vacías
            table = table.dropna(axis=0, how='all') # Eliminar filas completamente vacías
            return {table_key: table}
        else:
            print(f"Could not find a valid table in '{sheet_name}' sheet.")
            return {}
    except Exception as e:
        print(f"Error reading sheet '{sheet_name}': {e}")
        return {}

def extract_tables_from_excel_verificacion_por_deflexion(file_path):
    """Extrae la tabla de verificación por deflexión de forma dinámica."""
    return _extract_generic_table(file_path, 'Verificación Deflexiones', 'Verificación Deflexiónes')

def extract_tables_from_excel_verificacion_por_deflexion_horizontales(file_path):
    """Extrae la tabla de verificación por deflexión horizontal (derivas) de forma dinámica."""
    return _extract_generic_table(file_path, 'Verificación Deflexiones H', 'Verificación Deflexiónes H')

def extract_tables_from_excel_viento(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        if 'Viento' not in xls.sheet_names:
            print("Sheet 'Viento' not found in the Excel file.")
            return {}

        df = pd.read_excel(xls, sheet_name='Viento', header=None)

        header_row_index = -1
        for i, row in df.iterrows():
            if row.notna().sum() > 1:
                header_row_index = i
                break
        
        if header_row_index != -1:
            viento_table = pd.read_excel(xls, sheet_name='Viento', header=header_row_index)
            viento_table = viento_table.dropna(axis=1, how='all')
            viento_table = viento_table.dropna(axis=0, how='all')
            viento_table = viento_table.loc[:, viento_table.notna().any(axis=0)]
            viento_table = viento_table[viento_table.notna().any(axis=1)]
            return {'Viento': viento_table}
        else:
            print("Could not find table in 'Viento' sheet.")
            return {}

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}

def extract_tables_from_excel_sismo(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        if 'Sismo' not in xls.sheet_names:
            print("Sheet 'Sismo' not found in the Excel file.")
            return {}

        df = pd.read_excel(xls, sheet_name='Sismo', header=None)

        header_row_index = -1
        for i, row in df.iterrows():
            if row.notna().sum() > 1:
                header_row_index = i
                break
        
        if header_row_index != -1:
            sismo_table = pd.read_excel(xls, sheet_name='Sismo', header=header_row_index)
            sismo_table = sismo_table.dropna(axis=1, how='all')
            sismo_table = sismo_table.dropna(axis=0, how='all')
            sismo_table = sismo_table.loc[:, sismo_table.notna().any(axis=0)]
            sismo_table = sismo_table[sismo_table.notna().any(axis=1)]
            return {'Sismo': sismo_table}
        else:
            print("Could not find table in 'Sismo' sheet.")
            return {}

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}

def extract_tables_from_excel_deflexion_componentes(file_path):
    try:
        # Extraigo la tabla de verificación por deflexión del excel que me viene por path con loatdev
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        # Extraigo la tabla de verificación por deflexión que en el excel esta en una hoja llamada Deflexión
        if 'Deflexiones (Componentes)' in xls.sheet_names:  # Verifico si la hoja 'Deflexión' existe
            deflexion_table_d = pd.read_excel(xls, sheet_name='Deflexiones (Componentes)')  # Extraigo la tabla de la hoja 'Deflexión'
            deflexion_table_d = deflexion_table_d.dropna(axis=1, how='all') # Eliminar columnas completamente vacías
            deflexion_table_d = deflexion_table_d.dropna(axis=0, how='all') # Eliminar filas completamente vacías
            deflexion_table_d = deflexion_table_d.loc[:, deflexion_table_d.notna().any(axis=0)] # Extraer solo columnas con datos
            deflexion_table_d = deflexion_table_d[deflexion_table_d.notna().any(axis=1)] # Extraer solo las filas que tienen datos
            return {'Deflexiones': deflexion_table_d} # Retorno la tabla de verificación por deflexión como un DataFrame
        else:
            print("Sheet 'Verificación de deflexiones' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}   
    
def extract_tables_from_excel_ratios(file_path):
    try:
        # Extraigo la tabla de ratios del excel que me viene por path con loatdev
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        # Extraigo la tabla de ratios que en el excel esta en una hoja llamada Ratios
        if 'Ratios' in xls.sheet_names:  # Verifico si la hoja 'Ratios' existe
            ratios_table = pd.read_excel(xls, sheet_name='Ratios')  # Extraigo la tabla de la hoja 'Ratios'
            ratios_table = ratios_table.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías
            ratios_table = ratios_table.dropna(axis=0, how='all')  # Eliminar filas completamente vacías
            ratios_table = ratios_table.loc[:, ratios_table.notna().any(axis=0)]  # Extraer solo columnas con datos
            # Extraer solo las filas que tienen datos
            ratios_table = ratios_table[ratios_table.notna().any(axis=1)]
            return {'Ratios': ratios_table}  # Retorno la tabla de ratios como un DataFrame
        else:
            print("Sheet 'Ratios' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}        
       
def extract_tables_from_excel_computos(file_path):
    try:
        # Extraigo la tabla de ratios del excel que me viene por path con loatdev
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        # Extraigo la tabla de ratios que en el excel esta en una hoja llamada Ratios
        if 'Cómputos' in xls.sheet_names:  # Verifico si la hoja 'Ratios' existe
            ratios_table = pd.read_excel(xls, sheet_name='Cómputos')  # Extraigo la tabla de la hoja 'Ratios'
            ratios_table = ratios_table.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías
            ratios_table = ratios_table.dropna(axis=0, how='all')  # Eliminar filas completamente vacías
            ratios_table = ratios_table.loc[:, ratios_table.notna().any(axis=0)]  # Extraer solo columnas con datos
            # Extraer solo las filas que tienen datos
            ratios_table = ratios_table[ratios_table.notna().any(axis=1)]
            return {'CP': ratios_table}  # Retorno la tabla de ratios como un DataFrame
        else:
            print("Sheet 'Computos' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}         

def extract_tables_from_excel_reacciones(file_path):
    try:
        # Extraigo la tabla de ratios del excel que me viene por path con loatdev
        xls = pd.ExcelFile(file_path)  # Cargar el archivo Excel
        # Extraigo la tabla de ratios que en el excel esta en una hoja llamada Ratios
        if 'Reacciones' in xls.sheet_names:  # Verifico si la hoja 'Ratios' existe
            ratios_table = pd.read_excel(xls, sheet_name='Reacciones')  # Extraigo la tabla de la hoja 'Ratios'
            ratios_table = ratios_table.dropna(axis=1, how='all')  # Eliminar columnas completamente vacías
            ratios_table = ratios_table.dropna(axis=0, how='all')  # Eliminar filas completamente vacías
            ratios_table = ratios_table.loc[:, ratios_table.notna().any(axis=0)]  # Extraer solo columnas con datos
            # Extraer solo las filas que tienen datos
            ratios_table = ratios_table[ratios_table.notna().any(axis=1)]
            return {'R': ratios_table}  # Retorno la tabla de ratios como un DataFrame
        else:
            print("Sheet 'Reacciones' not found in the Excel file.")
            return {}
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {}        

if __name__ == "__main__":
    # Ejemplo de uso
    file_path = os.getenv('EXCEL_TEMPLATE')  # Reemplaza con la ruta a tu archivo Excel
    tables = extract_tables_from_excel_deflexion_componentes(file_path)
    
    if tables:
        for sheet_name, df in tables.items():
            print(f"Table from sheet '{sheet_name}':")
            print(df)
    else:
        print("No tables extracted.")
