"""
Test de geometry_extractor con modelo real de STAAD.Pro
IMPORTANTE: Ejecutar con STAAD.Pro abierto y modelo cargado
"""

import sys
import logging

# Configurar logging para ver detalles
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

def main():
    print("\n" + "="*70)
    print(" TEST DE GEOMETRY_EXTRACTOR")
    print("="*70 + "\n")
    
    print("Pre-requisitos:")
    print("   1. STAAD.Pro abierto")
    print("   2. Modelo cargado (el que tiene 167 nodos, 292 miembros)")
    print("   3. Modelo analizado\n")
    
    input("Presiona ENTER cuando estes listo...")
    
    # Importar modulos
    print("\n1. Importando modulos...")
    try:
        from src.services.staad_connector import STAADConnector
        from src.services.geometry_extractor import GeometryExtractor
        print("   OK\n")
    except ImportError as e:
        print(f"   ERROR: {e}\n")
        return False
    
    # Conectar a STAAD
    print("2. Conectando a STAAD.Pro...")
    try:
        connector = STAADConnector()
        if not connector.connect():
            print("   ERROR: No se pudo conectar\n")
            return False
        print("   OK\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
        return False
    
    # Crear extractor
    print("3. Creando extractor de geometria...")
    try:
        extractor = GeometryExtractor(connector)
        print("   OK\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
        return False
    
    # Extraer geometria completa
    print("4. Extrayendo geometria completa...\n")
    try:
        model = extractor.extract_complete_model()
    except Exception as e:
        print(f"\n   ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar datos extraidos
    print("\n5. VERIFICACION DE DATOS EXTRAIDOS:")
    print(f"   Nodos: {len(model.nodes)}")
    print(f"   Miembros: {len(model.members)}")
    print(f"   Grupos: {len(model.groups)}")
    
    # Mostrar algunos nodos
    if len(model.nodes) > 0:
        print("\n   Primeros 3 nodos:")
        for node_id in list(model.nodes.keys())[:3]:
            node = model.nodes[node_id]
            print(f"      Nodo {node.id}: ({node.x:.3f}, {node.y:.3f}, {node.z:.3f})")
    
    # Mostrar algunos miembros
    if len(model.members) > 0:
        print("\n   Primeros 3 miembros:")
        for member_id in list(model.members.keys())[:3]:
            member = model.members[member_id]
            print(f"      Miembro {member.id}: Nodos {member.node_a}-{member.node_b}, L={member.length:.3f}m")
            print(f"         Grupo: {member.group}, Tipo: {member.member_type.value}")
    
    # Mostrar grupos
    if len(model.groups) > 0:
        print("\n   Grupos encontrados:")
        for group_name, members in model.groups.items():
            print(f"      {group_name}: {len(members)} miembros")
    
    # Estadisticas de clasificacion
    print("\n6. ESTADISTICAS DE CLASIFICACION:")
    
    vigas = model.get_beams()
    columnas = model.get_columns()
    req_deflexion = model.get_members_requiring_deflection_check()
    req_deriva = model.get_members_requiring_drift_check()
    
    print(f"   Total vigas: {len(vigas)}")
    print(f"   Total columnas: {len(columnas)}")
    print(f"   Requieren verificacion deflexion: {len(req_deflexion)}")
    print(f"   Requieren verificacion deriva: {len(req_deriva)}")
    
    # Cerrar conexion
    connector.close()
    
    print("\n" + "="*70)
    print("TEST COMPLETADO EXITOSAMENTE")
    print("="*70 + "\n")
    
    print("SIGUIENTE PASO:")
    print("   Crear results_extractor.py para extraer desplazamientos\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
