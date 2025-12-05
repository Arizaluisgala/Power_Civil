def validar_idioma(idioma):
    if idioma not in ["español", "ingles", "es", "en"]:
        raise ValueError("Idioma no reconocido. Usa 'español' o 'ingles'.")