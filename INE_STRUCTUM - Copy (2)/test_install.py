"""Test de instalación de openstaadpy"""

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

# Test 2: Importar osanalytical
print("\n2. Importando osanalytical...")
try:
    from openstaadpy import osanalytical
    print("   OK")
except ImportError as e:
    print(f"   ERROR: {e}")
    exit(1)

# Test 3: Ver submódulos disponibles
print("\n3. Submodulos disponibles:")
submodules = [attr for attr in dir(openstaadpy) if not attr.startswith('_')]
for mod in submodules[:10]:
    print(f"   - {mod}")
if len(submodules) > 10:
    print(f"   ... y {len(submodules)-10} mas")

# Test 4: Verificar función connect
print("\n4. Verificando funcion connect...")
if hasattr(osanalytical, 'connect'):
    print("   Funcion connect disponible")
else:
    print("   Funcion connect no encontrada")

print("\n" + "="*60)
print("INSTALACION VERIFICADA EXITOSAMENTE")
print("="*60 + "\n")

print("Siguiente paso: Ejecutar test_staad_connection.py con STAAD.Pro abierto")
