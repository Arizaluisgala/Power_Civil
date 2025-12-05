import pandas as pd

def extraer_tablas_cb_especifico_dict(filepath, sheet_names=['CB', 'Cortante Basal', 'Base Shear'], cols='D:H'):
    """
    Extrae tablas de una hoja de cálculo, probando una lista de posibles nombres de hoja.
    Usa filas 7,8 13,14 18,19 23,24 28,29 33,34 como encabezados y los datos debajo hasta la siguiente fila vacía.
    Devuelve una lista de dicts: {'headers': [...], 'rows': [[...], ...]}
    """
    df = None
    sheet_name_found = None
    for sheet_name in sheet_names:
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, usecols=cols, header=None, dtype=str)
            sheet_name_found = sheet_name
            break  # Si tiene éxito, sal del bucle
        except Exception as e:
            print(f"No se encontró la hoja '{sheet_name}'. Intentando con la siguiente...")
    
    if df is None:
        raise ValueError(f"No se encontró ninguna de las hojas de cálculo esperadas: {sheet_names}")

    # Índices de encabezados (Python es base 0)
    encabezado_indices = [(6,7), (12,13), (17,18), (22,23), (27,28), (32,33)]
    tablas = []

    # --- Añadir la tabla especial de filas 4 y 5, solo columnas D y F ---
    try:
        df_full = pd.read_excel(filepath, sheet_name=sheet_name_found, header=None, dtype=str)
        # Filas 4 y 5 son índices 3 y 4
        rows_4_5 = df_full.iloc[3:5, [3, 5]]  # D=3, F=5
        # Encabezados
        headers_4_5 = [str(df_full.iloc[2, 3]).strip() if pd.notna(df_full.iloc[2, 3]) else "D",
                       str(df_full.iloc[2, 5]).strip() if pd.notna(df_full.iloc[2, 5]) else "F"]
        data_rows_4_5 = []
        for _, row in rows_4_5.iterrows():
            data_rows_4_5.append([str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "",
                                  str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""])
        # Solo agregar si hay algún dato
        if any(any(cell for cell in row) for row in data_rows_4_5):
            tablas.append({'headers': headers_4_5, 'rows': data_rows_4_5})
    except Exception as e:
        pass

    # --- El resto de tablas normales ---
    for idx1, idx2 in encabezado_indices:
        if idx2 >= len(df):
            continue
        header_row_1 = df.iloc[idx1].tolist()
        header_row_2 = df.iloc[idx2].tolist()
        # Combinar encabezados
        headers = []
        for h1, h2 in zip(header_row_1, header_row_2):
            h1 = str(h1).strip() if pd.notna(h1) else ""
            h2 = str(h2).strip() if pd.notna(h2) else ""
            if h1 and h2:
                headers.append(f"{h1} {h2}")
            elif h1:
                headers.append(h1)
            elif h2:
                headers.append(h2)
            else:
                headers.append("")
        # Buscar datos debajo hasta fila vacía o siguiente encabezado
        data_rows = []
        start_idx = idx2 + 1
        # El siguiente encabezado empieza en el siguiente par, o hasta el final
        next_header = None
        for pair in encabezado_indices:
            if pair[0] > idx1:
                next_header = pair[0]
                break
        end_idx = next_header if next_header is not None else len(df)
        for i in range(start_idx, end_idx):
            row = df.iloc[i].tolist()
            if all((pd.isna(val) or str(val).strip() == "") for val in row):
                break
            data_rows.append([str(val).strip() if pd.notna(val) else "" for val in row])
        # Solo agregar si hay datos
        if any(any(cell for cell in row) for row in data_rows):
            tablas.append({'headers': headers, 'rows': data_rows})
    return tablas
