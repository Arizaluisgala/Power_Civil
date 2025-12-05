def validar_version(version):
    if version not in ["simple", "completa"]:
        raise ValueError("Opción de versión no reconocida. Usa 'simple' o 'completa'.")