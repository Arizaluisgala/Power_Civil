
def format_number(value):
    """
    Formatea un número para que tenga 2 decimales o 2 cifras significativas.
    Los enteros se mantienen sin cambios.
    """
    if isinstance(value, (int, float)):
        # Si es un entero, o un flotante que es un entero
        if value == int(value):
            return str(int(value))
        # Si es un flotante muy pequeño
        if abs(value) < 0.01 and abs(value) > 0:
            return f"{value:.2g}"
        # Otros flotantes
        return f"{value:.2f}"
    return str(value)

def format_decimal_2(value):
    """
    Formatea un número para que siempre tenga 2 decimales.
    """
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)
