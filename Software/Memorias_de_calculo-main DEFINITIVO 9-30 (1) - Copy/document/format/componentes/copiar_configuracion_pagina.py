def copiar_configuracion_pagina(seccion_base, seccion_nueva):
    """
    Copia la configuración de página (márgenes, tamaño, orientación) de una sección base a una nueva sección.
    """
    atributos = [
        'left_margin', 'right_margin', 'top_margin', 'bottom_margin',
        'page_width', 'page_height', 'orientation'
    ]
    for atributo in atributos:
        if hasattr(seccion_base, atributo) and hasattr(seccion_nueva, atributo):
            setattr(seccion_nueva, atributo, getattr(seccion_base, atributo))
        else:
            raise AttributeError(f"Ambas secciones deben tener el atributo '{atributo}'")