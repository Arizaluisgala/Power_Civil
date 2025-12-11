'''Test de data_models con grupos reales'''

print("\n" + "="*60)
print("TEST DE MODELOS DE DATOS - GRUPOS REALES")
print("="*60 + "\n")

try:
    from src.models.data_models import (
        Node, AnalyticalMember, StructuralModel,
        MemberType, LoadType, NormType,
        AnalysisParameters, ProjectInfo  # AGREGADO
    )
    print("OK - Todos los modelos importados\n")
    
    # Test 1: Verificar todos los grupos
    print("1. GRUPOS DEFINIDOS:")
    for member_type in MemberType:
        print(f"   - {member_type.value}")
    
    # Test 2: Clasificacion desde nombre de grupo
    print("\n2. TEST DE CLASIFICACION:")
    test_groups = [
        "_COLUMNAS_PRIN",
        "_VIGAS_PRIN",
        "_ARRIOST_HORIZ",
        "_VIGA_GRUA",
        "_MONORRIEL",
        "_DESCONOCIDO_XYZ"
    ]
    
    for group in test_groups:
        member_type = MemberType.from_group_name(group)
        print(f"   Grupo '{group}' -> {member_type.value}")
    
    # Test 3: Metodos de verificacion
    print("\n3. TEST DE METODOS:")
    beam_type = MemberType.BEAM_PRIMARY
    column_type = MemberType.COLUMN_PRIMARY
    brace_type = MemberType.BRACE_HORIZONTAL
    
    print(f"   {beam_type.value}:")
    print(f"      - Es viga: {beam_type.is_beam()}")
    print(f"      - Es columna: {beam_type.is_column()}")
    print(f"      - Requiere deflexion: {beam_type.requires_deflection_check()}")
    print(f"      - Limite default: L/{beam_type.get_default_deflection_limit()}")
    
    print(f"\n   {column_type.value}:")
    print(f"      - Es viga: {column_type.is_beam()}")
    print(f"      - Es columna: {column_type.is_column()}")
    print(f"      - Requiere deriva: {column_type.requires_drift_check()}")
    
    # Test 4: Crear modelo con miembros de diferentes grupos
    print("\n4. TEST DE MODELO:")
    model = StructuralModel()
    
    # Crear nodos
    for i in range(1, 5):
        model.nodes[i] = Node(id=i, x=i*5.0, y=0.0, z=0.0)
    
    # Crear miembros de diferentes tipos
    model.members[1] = AnalyticalMember(
        id=1, node_a=1, node_b=2, length=5.0,
        group="_VIGAS_PRIN",
        member_type=MemberType.BEAM_PRIMARY
    )
    
    model.members[2] = AnalyticalMember(
        id=2, node_a=2, node_b=3, length=5.0,
        group="_COLUMNAS_PRIN",
        member_type=MemberType.COLUMN_PRIMARY
    )
    
    model.members[3] = AnalyticalMember(
        id=3, node_a=3, node_b=4, length=5.0,
        group="_VIGA_GRUA",
        member_type=MemberType.GRUA
    )
    
    print(f"   Nodos: {len(model.nodes)}")
    print(f"   Miembros: {len(model.members)}")
    print(f"   Vigas: {len(model.get_beams())}")
    print(f"   Columnas: {len(model.get_columns())}")
    print(f"   Requieren deflexion: {len(model.get_members_requiring_deflection_check())}")
    print(f"   Requieren deriva: {len(model.get_members_requiring_drift_check())}")
    
    # Test 5: Parametros con limites por grupo
    print("\n5. TEST DE PARAMETROS:")
    params = AnalysisParameters()
    print("   Limites de deflexion por tipo:")
    for member_type, limit in params.deflection_limits.items():
        print(f"      {member_type.value}: L/{limit}")
    
    print("\n" + "="*60)
    print("TODOS LOS TESTS PASARON EXITOSAMENTE")
    print("="*60 + "\n")
    
    print("SIGUIENTE PASO:")
    print("   Crear geometry_extractor.py para extraer geometria de STAAD.Pro\n")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
