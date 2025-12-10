"""
Diagnostico: Verificar grupos en STAAD
"""
import sys
sys.path.insert(0, 'src')

from services.staad_connector import STAADConnector
from services import geometry_extensions as geo_ext

print("\n" + "="*60)
print("DIAGNOSTICO DE GRUPOS EN STAAD")
print("="*60)

connector = STAADConnector()
if not connector.connect():
    print("Error: No se pudo conectar a STAAD.Pro")
    sys.exit(1)

print(f"\nConectado exitosamente")
print(f"Nodos: {connector.staad.Geometry.GetNodeCount()}")
print(f"Miembros: {connector.staad.Geometry.GetMemberCount()}")

# Probar los 3 tipos de grupos
for group_type, type_name in [(0, "MEMBER"), (1, "NODE"), (2, "PLATE")]:
    try:
        count = connector.staad.Geometry.GetGroupCount(group_type)
        print(f"\n{type_name} Groups: {count}")
        
        if count > 0:
            names = geo_ext.GetGroupNames(connector.staad.Geometry, group_type)
            print(f"  Nombres encontrados: {len(names)}")
            
            # Mostrar todos los nombres
            for idx, name in enumerate(names, 1):
                entities = geo_ext.GetGroupEntities(connector.staad.Geometry, name)
                print(f"  {idx}. '{name}': {len(entities)} entidades")
                if entities and len(entities) <= 10:
                    print(f"      IDs: {entities}")
                elif entities:
                    print(f"      Primeros IDs: {entities[:10]}")
                    
    except Exception as e:
        print(f"  Error en {type_name}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("DIAGNOSTICO COMPLETADO")
print("="*60)
connector.close()
