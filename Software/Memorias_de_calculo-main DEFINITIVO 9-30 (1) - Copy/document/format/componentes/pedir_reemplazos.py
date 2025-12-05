def pedir_reemplazos(textos):
    reemplazos = {}
    for txt in textos:
        low = txt.lower()
        if 'rev' in low:
            reemplazos[txt] = "Rev:"
            continue  # No preguntar, usar por defecto
        elif 'emision' in low:
            reemplazos[txt] = "EMISIÓN:"
            continue  # No preguntar, usar por defecto
        val = input(f"Ingrese el valor para '{txt}': ").strip()
        reemplazos[txt] = val.upper() if val else txt
    else:
        # Si faltan textos en reemplazos, usa el nombre del campo como valor por defecto
        for txt in textos:
            if txt not in reemplazos:
                reemplazos[txt] = txt
    return reemplazos