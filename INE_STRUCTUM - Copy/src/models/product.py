"""
Modelos de datos para Producto
ACTUALIZADO: Incluye tablas de deflexión (migradas desde Project)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class DeflectionVerification:
    """Verificación de deflexión vertical - CON SELECTOR DE TIPO"""
    group_name: str
    
    # CASO 1
    case1_enabled: bool = False
    case1_use_factor: bool = True  # True = L/denom, False = límite absoluto
    case1_denominator: Optional[float] = None  # Para L/240
    case1_limit_mm: Optional[float] = None  # Para límite absoluto
    case1_load_type: str = "Live Load (L)"
    
    # CASO 2
    case2_enabled: bool = False
    case2_use_factor: bool = True
    case2_denominator: Optional[float] = None
    case2_limit_mm: Optional[float] = None
    case2_load_type: str = "Carga Muerta + Carga Viva (D+L)"
    
    # CASO 3
    case3_enabled: bool = False
    case3_use_factor: bool = True
    case3_denominator: Optional[float] = None
    case3_limit_mm: Optional[float] = None
    case3_load_type: str = "Wind (W)"


@dataclass
class HorizontalDeflectionVerification:
    """Verificación de deflexión horizontal - CON SELECTOR DE TIPO"""
    group_name: str
    enabled: bool = False
    
    use_factor: bool = True  # True = H/denom, False = límite absoluto
    denominator: Optional[float] = None  # Para H/400
    limit_mm: Optional[float] = None  # Para límite absoluto
    load_type: str = "Wind (W)"


@dataclass
class Product:
    """Producto dentro de un proyecto"""
    # Identificación
    product_code: str
    project_code: str  # FK al proyecto padre
    product_name: str
    
    # Modelo STAAD
    staad_model_path: str
    
    # Sistema estructural
    structural_system: str = "Special Moment Frame"  # SMF, IMF, OMF, etc.
    
    # Factores sísmicos específicos del producto
    r_factor: float = 8.0  # Response modification factor
    cd_factor: float = 5.5  # Deflection amplification factor
    omega_factor: float = 3.0  # Overstrength factor
    
    # Tablas de verificación (MIGRADAS DESDE PROJECT)
    deflection_verifications: List[DeflectionVerification] = field(default_factory=list)
    horizontal_deflection_verifications: List[HorizontalDeflectionVerification] = field(default_factory=list)
    
    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    modified_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para JSON"""
        return {
            "product_code": self.product_code,
            "project_code": self.project_code,
            "product_name": self.product_name,
            "staad_model_path": self.staad_model_path,
            "structural_system": self.structural_system,
            "r_factor": self.r_factor,
            "cd_factor": self.cd_factor,
            "omega_factor": self.omega_factor,
            "deflection_verifications": [
                {
                    "group_name": dv.group_name,
                    "case1_enabled": dv.case1_enabled,
                    "case1_use_factor": dv.case1_use_factor,
                    "case1_denominator": dv.case1_denominator,
                    "case1_limit_mm": dv.case1_limit_mm,
                    "case1_load_type": dv.case1_load_type,
                    "case2_enabled": dv.case2_enabled,
                    "case2_use_factor": dv.case2_use_factor,
                    "case2_denominator": dv.case2_denominator,
                    "case2_limit_mm": dv.case2_limit_mm,
                    "case2_load_type": dv.case2_load_type,
                    "case3_enabled": dv.case3_enabled,
                    "case3_use_factor": dv.case3_use_factor,
                    "case3_denominator": dv.case3_denominator,
                    "case3_limit_mm": dv.case3_limit_mm,
                    "case3_load_type": dv.case3_load_type
                }
                for dv in self.deflection_verifications
            ],
            "horizontal_deflection_verifications": [
                {
                    "group_name": hv.group_name,
                    "enabled": hv.enabled,
                    "use_factor": hv.use_factor,
                    "denominator": hv.denominator,
                    "limit_mm": hv.limit_mm,
                    "load_type": hv.load_type
                }
                for hv in self.horizontal_deflection_verifications
            ],
            "created_date": self.created_date,
            "modified_date": self.modified_date
        }
