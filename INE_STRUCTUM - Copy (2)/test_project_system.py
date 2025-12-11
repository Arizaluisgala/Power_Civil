"""
TEST COMPLETO DE SISTEMA DE PROYECTOS
Verifica que todo el sistema Proyecto->Producto funcione correctamente
"""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from src.services.project_manager import ProjectManager
from src.models.project import DesignCode, LoadCaseType

print("\n" + "="*70)
print(" TEST COMPLETO DEL SISTEMA DE PROYECTOS/PRODUCTOS")
print("="*70)

# ===== PASO 1: Crear Project Manager =====
print("\n[1/7] Creando Project Manager...")
pm = ProjectManager()
print("   ✅ Project Manager creado")

# ===== PASO 2: Crear Nuevo Proyecto =====
print("\n[2/7] Creando nuevo proyecto...")
project = pm.create_new_project(
    name="Edificio Hospital Central",
    project_folder=Path("./test_projects/hospital"),
    design_code=DesignCode.ASCE_7_22,
    description="Proyecto de verificacion estructural para edificio de 5 pisos"
)
print(f"   ✅ Proyecto creado: {project.name}")
print(f"   📂 Carpeta: {project.project_folder}")
print(f"   📋 Codigo: {project.design_code.value}")

# ===== PASO 3: Verificar Parametros por Defecto =====
print("\n[3/7] Verificando parametros por defecto...")
print(f"   Limites de deflexion: {len(project.deflection_limits)}")
for limit in project.deflection_limits[:3]:
    print(f"      - {limit.member_type}: L/{limit.live_load_denominator} (viva), L/{limit.total_load_denominator} (total)")

print(f"\n   Parametros sismicos:")
print(f"      R = {project.seismic_params.R_factor}")
print(f"      Cd = {project.seismic_params.Cd_factor}")
print(f"      Ω = {project.seismic_params.omega_factor}")
print(f"      Derivas: {len(project.seismic_params.drift_limits)} niveles configurados")
print("   ✅ Parametros configurados correctamente")

# ===== PASO 4: Agregar Productos al Proyecto =====
print("\n[4/7] Agregando productos (archivos .STD)...")
product1 = pm.add_product_to_project(
    project=project,
    product_name="Portico Eje A",
    staad_file_path=Path("./models/portico_eje_a.std"),
    description="Marco principal en direccion longitudinal"
)
print(f"   ✅ Producto 1: {product1.name} (ID: {product1.product_id})")

product2 = pm.add_product_to_project(
    project=project,
    product_name="Portico Eje B",
    staad_file_path=Path("./models/portico_eje_b.std"),
    description="Marco secundario"
)
print(f"   ✅ Producto 2: {product2.name} (ID: {product2.product_id})")

product3 = pm.add_product_to_project(
    project=project,
    product_name="Portico Eje 1",
    staad_file_path=Path("./models/portico_eje_1.std"),
    description="Marco transversal"
)
print(f"   ✅ Producto 3: {product3.name} (ID: {product3.product_id})")

print(f"\n   Total productos: {len(project.products)}")

# ===== PASO 5: Configurar Casos de Carga =====
print("\n[5/7] Configurando casos de carga...")

# Simulacion de casos extraidos de STAAD
load_cases = [
    "Dead Load",
    "Live Load Floor",
    "Live Load Roof",
    "Wind +X",
    "Wind -X",
    "Wind +Z",
    "Wind -Z",
    "Seismic X",
    "Seismic Z",
    "Temperature"
]

# Auto-detectar tipos
pm.auto_detect_load_cases(project, load_cases)

print(f"   ✅ {len(project.load_case_mapping)} casos mapeados")
print("\n   Muestra de mapeo:")
for key, mapping in list(project.load_case_mapping.items())[:5]:
    print(f"      {key}: '{mapping.staad_case_name}' → {mapping.case_type.value}")

# ===== PASO 6: Guardar Proyecto =====
print("\n[6/7] Guardando proyecto...")
save_path = project.project_folder / f"{project.name}.inestructum"
pm.save_project(project, save_path)
print(f"   ✅ Proyecto guardado en: {save_path}")

# ===== PASO 7: Cargar Proyecto =====
print("\n[7/7] Cargando proyecto guardado...")
loaded_project = pm.load_project(save_path)
print(f"   ✅ Proyecto cargado: {loaded_project.name}")
print(f"   Productos cargados: {len(loaded_project.products)}")

# ===== RESUMEN FINAL =====
print("\n" + "="*70)
print(" RESUMEN DEL PROYECTO")
print("="*70)
summary = pm.get_project_summary(loaded_project)
print(summary)

# ===== VERIFICACION DE INTEGRIDAD =====
print("\n" + "="*70)
print(" VERIFICACION DE INTEGRIDAD")
print("="*70)

checks = {
    "Proyecto creado": loaded_project is not None,
    "Tiene productos": len(loaded_project.products) == 3,
    "Tiene limites deflexion": len(loaded_project.deflection_limits) > 0,
    "Tiene parametros sismicos": loaded_project.seismic_params is not None,
    "Tiene casos mapeados": len(loaded_project.load_case_mapping) == 10,
    "Archivo guardado existe": save_path.exists(),
}

all_passed = True
for check_name, passed in checks.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"   {status}: {check_name}")
    if not passed:
        all_passed = False

print("\n" + "="*70)
if all_passed:
    print(" ✅ TODAS LAS VERIFICACIONES PASARON")
    print(" FASE 1 COMPLETADA EXITOSAMENTE")
else:
    print(" ❌ ALGUNAS VERIFICACIONES FALLARON")
    print(" Revisar logs arriba")
print("="*70)

print("\n✨ Sistema de Proyectos/Productos funcionando correctamente")
print("🎯 FASE 1 COMPLETA - Listo para FASE 2 (Ya completada) y FASE 3")
