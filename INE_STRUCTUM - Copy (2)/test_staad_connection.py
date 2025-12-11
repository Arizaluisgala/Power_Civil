"""
Test de conexion real con STAAD.Pro - CORREGIDO v2
IMPORTANTE: Ejecutar con STAAD.Pro abierto y un modelo cargado
"""

import sys

def main():
    print("\n" + "="*70)
    print(" TEST DE CONEXION CON STAAD.PRO 2025")
    print("="*70 + "\n")
    
    print("Pre-requisitos:")
    print("   1. STAAD.Pro debe estar abierto")
    print("   2. Un modelo debe estar cargado")
    print("   3. El modelo debe estar analizado (con resultados)\n")
    
    input("Presiona ENTER cuando estes listo...")
    
    # Importar openstaadpy
    print("\n1. Importando openstaadpy...")
    try:
        from openstaadpy import os_analytical
        print("   OK - Modulo importado\n")
    except ImportError as e:
        print(f"   ERROR: {e}\n")
        return False
    
    # Conectar a STAAD
    print("2. Conectando a STAAD.Pro...")
    try:
        staad = os_analytical.connect()
        print("   Conexion establecida")
        print(f"   Tipo de objeto: {type(staad).__name__}\n")
    except Exception as e:
        print(f"   ERROR: {e}")
        print("\nAsegurate de que STAAD.Pro este abierto con un modelo\n")
        return False
    
    # Obtener información del modelo
    print("3. Obteniendo informacion del modelo...\n")
    
    try:
        # Version - El objeto staad YA ES Root
        version = staad.GetApplicationVersion()
        print(f"   Version STAAD.Pro: {version}")
        
        # Unidades
        length = staad.GetInputUnitForLength()
        force = staad.GetInputUnitForForce()
        base = staad.GetBaseUnit()
        print(f"   Sistema de unidades: {base}")
        print(f"   Unidad longitud: {length}")
        print(f"   Unidad fuerza: {force}")
        
        # Geometria - Acceder a traves de propiedades
        geom = staad.Geometry
        node_count = geom.GetNodeCount()
        print(f"   Cantidad de nodos: {node_count}")
        
        beam_list = geom.GetBeamList()
        print(f"   Cantidad de miembros: {len(beam_list)}")
        
        # Grupos
        try:
            groups = geom.GetGroupList()
            print(f"   Cantidad de grupos: {len(groups)}")
            if groups and len(groups) > 0:
                print(f"   Primeros grupos: {', '.join(groups[:5])}")
        except Exception as e:
            print(f"   No se pudieron obtener grupos: {e}")
        
        # Casos de carga
        try:
            load = staad.Load
            lc_count = load.GetPrimaryLoadCaseCount()
            print(f"   Casos de carga primarios: {lc_count}")
        except Exception as e:
            print(f"   No se pudieron obtener casos de carga: {e}")
        
        # Verificar resultados
        output = staad.Output
        has_results = output.AreResultsAvailable()
        print(f"   Resultados disponibles: {'Si' if has_results else 'No'}")
        
        if not has_results:
            print("\n   ADVERTENCIA: El modelo no tiene resultados")
            print("   Por favor analiza el modelo en STAAD.Pro primero\n")
        
        # Test adicional: Obtener coordenadas del primer nodo
        if node_count > 0:
            try:
                node_list = geom.GetNodeList()
                first_node = node_list[0]
                coords = geom.GetNodeCoordinates(first_node)
                print(f"\n   Test de lectura - Nodo {first_node}: X={coords[0]:.3f}, Y={coords[1]:.3f}, Z={coords[2]:.3f}")
            except Exception as e:
                print(f"\n   No se pudo leer coordenadas: {e}")
        
    except Exception as e:
        print(f"   ERROR obteniendo datos: {e}\n")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("TODAS LAS PRUEBAS EXITOSAS")
    print("="*70 + "\n")
    
    print("ESTRUCTURA CORRECTA DETECTADA:")
    print("   - Conexion: staad = os_analytical.connect()")
    print("   - Root: staad.GetApplicationVersion()")
    print("   - Geometria: staad.Geometry.GetNodeCount()")
    print("   - Cargas: staad.Load.GetPrimaryLoadCaseCount()")
    print("   - Resultados: staad.Output.AreResultsAvailable()\n")
    
    print("Siguiente paso: Crear modulo staad_connector.py con la estructura correcta\n")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
