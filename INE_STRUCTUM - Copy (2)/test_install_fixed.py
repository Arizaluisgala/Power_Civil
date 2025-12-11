"""Test de instalación de openstaadpy - CORREGIDO"""

print("\n" + "="*60)
print("VERIFICACION DE INSTALACION - OPENSTAADPY")
print("="*60 + "\n")

# Test 1: Importar módulo principal
print("1. Importando openstaadpy...")
try:
    import openstaadpy
    print(f"   OK - {openstaadpy.__file__}")
except ImportError as e:
    print(f"   ERROR: {e}")
    exit(1)

# Test 2: Ver estructura del módulo
print("\n2. Explorando estructura de openstaadpy...")
attributes = dir(openstaadpy)
print(f"   Atributos encontrados: {len(attributes)}")

# Mostrar atributos relevantes (no privados)
public_attrs = [attr for attr in attributes if not attr.startswith('_')]
print("\n   Atributos publicos:")
for attr in public_attrs[:15]:
    print(f"   - {attr}")
if len(public_attrs) > 15:
    print(f"   ... y {len(public_attrs)-15} mas")

# Test 3: Intentar diferentes formas de importar
print("\n3. Probando diferentes importaciones...")

# Opción 1: osanalytical directo
try:
    from openstaadpy import osanalytical
    print("   OK - osanalytical importado directamente")
    HAS_OSANALYTICAL = True
except ImportError:
    print("   NO - osanalytical no disponible directamente")
    HAS_OSANALYTICAL = False

# Opción 2: os_analytical con guion bajo
if not HAS_OSANALYTICAL:
    try:
        from openstaadpy import os_analytical
        print("   OK - os_analytical (con guion bajo) importado")
        HAS_OSANALYTICAL = True
        # Crear alias
        osanalytical = os_analytical
    except ImportError:
        print("   NO - os_analytical tampoco disponible")

# Opción 3: Verificar si existe como atributo
if not HAS_OSANALYTICAL:
    if hasattr(openstaadpy, 'os_analytical'):
        print("   OK - os_analytical existe como atributo")
        os_analytical = getattr(openstaadpy, 'os_analytical')
        HAS_OSANALYTICAL = True

# Test 4: Verificar función connect
print("\n4. Verificando funcion connect...")
if HAS_OSANALYTICAL:
    try:
        # Intentar con el módulo correcto
        if 'os_analytical' in dir():
            if hasattr(os_analytical, 'connect'):
                print("   OK - Funcion connect disponible en os_analytical")
            else:
                print("   ADVERTENCIA - connect no encontrado")
                # Mostrar funciones disponibles
                funcs = [f for f in dir(os_analytical) if not f.startswith('_')]
                print(f"   Funciones disponibles: {', '.join(funcs[:5])}")
        elif 'osanalytical' in dir():
            if hasattr(osanalytical, 'connect'):
                print("   OK - Funcion connect disponible en osanalytical")
    except Exception as e:
        print(f"   ERROR: {e}")
else:
    print("   NO SE PUDO VERIFICAR - Modulo no importado")

print("\n" + "="*60)
if HAS_OSANALYTICAL:
    print("INSTALACION VERIFICADA - CON ADVERTENCIAS")
    print("="*60 + "\n")
    print("NOTA: Usar 'from openstaadpy import os_analytical' en lugar de 'osanalytical'")
else:
    print("INSTALACION INCOMPLETA")
    print("="*60 + "\n")

print("\nSiguiente paso: Ejecutar test_staad_connection_fixed.py con STAAD.Pro abierto")
