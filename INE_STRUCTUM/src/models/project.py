"""
Modelos de datos para sistema Proyecto -> Producto
JERARQUIA: Proyecto (global) -> Productos (archivos .STD individuales)
VERSION COMPLETA CON DESERIALIZACION
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

class DesignCode(Enum):
    """Codigos de diseño soportados"""
    ASCE_7_22 = "ASCE 7-22"
    ASCE_7_16 = "ASCE 7-16"
    EUROCODE_8 = "Eurocode 8"
    NSR_10 = "NSR-10"

class LoadCaseType(Enum):
    """Tipos de casos de carga"""
    DEAD = "Dead"
    LIVE = "Live"
    LIVE_ROOF = "LiveRoof"
    WIND_X_POS = "Wind+X"
    WIND_X_NEG = "Wind-X"
    WIND_Z_POS = "Wind+Z"
    WIND_Z_NEG = "Wind-Z"
    SEISMIC_X = "SeismicX"
    SEISMIC_Z = "SeismicZ"
    SEISMIC_Y = "SeismicY"
    TEMPERATURE = "Temperature"
    SETTLEMENT = "Settlement"
    OTHER = "Other"

@dataclass
class LoadCaseMapping:
    """Mapeo de casos de carga del modelo STAAD al tipo"""
    staad_case_number: int
    staad_case_name: str
    case_type: LoadCaseType
    description: str = ""

@dataclass
class DeflectionLimit:
    """Limites de deflexion para un tipo de miembro"""
    member_type: str
    live_load_denominator: float
    total_load_denominator: float
    absolute_limit_mm: Optional[float] = None
    code_reference: str = ""

@dataclass
class DriftLimit:
    """Limites de deriva sismica"""
    story_height_m: float
    drift_limit_percent: float
    code_reference: str = ""

@dataclass
class SeismicParameters:
    """Parametros sismicos del proyecto"""
    design_code: DesignCode = DesignCode.ASCE_7_22
    R_factor: float = 5.0
    Cd_factor: float = 4.5
    omega_factor: float = 1.0
    q_factor: Optional[float] = None
    nu_factor: Optional[float] = None
    seismic_cases: Dict[str, int] = field(default_factory=dict)
    importance_factor: float = 1.0
    drift_limits: List[DriftLimit] = field(default_factory=list)

@dataclass
class WindParameters:
    """Parametros de viento del proyecto"""
    wind_cases: Dict[str, int] = field(default_factory=dict)
    displacement_limit_h_over: float = 500.0
    code_reference: str = ""

@dataclass
class Product:
    """
    PRODUCTO: Archivo .STD individual con verificaciones especificas
    Pertenece a un PROYECTO
    """
    product_id: str
    name: str
    description: str = ""
    staad_file_path: Path = field(default_factory=Path)
    parent_project: Optional['Project'] = None
    custom_seismic_params: Optional[SeismicParameters] = None
    custom_deflection_limits: Optional[List[DeflectionLimit]] = None
    last_analyzed: Optional[datetime] = None
    is_valid: bool = False
    verification_results: dict = field(default_factory=dict)
    
    def get_seismic_params(self) -> SeismicParameters:
        """Obtener parametros sismicos (custom o del proyecto)"""
        if self.custom_seismic_params:
            return self.custom_seismic_params
        elif self.parent_project and self.parent_project.seismic_params:
            return self.parent_project.seismic_params
        else:
            return SeismicParameters()
    
    def get_deflection_limits(self) -> List[DeflectionLimit]:
        """Obtener limites de deflexion (custom o del proyecto)"""
        if self.custom_deflection_limits:
            return self.custom_deflection_limits
        elif self.parent_project:
            return self.parent_project.deflection_limits
        else:
            return []
    
    def to_dict(self) -> dict:
        """Serializar a diccionario"""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "staad_file_path": str(self.staad_file_path),
            "last_analyzed": self.last_analyzed.isoformat() if self.last_analyzed else None,
            "is_valid": self.is_valid
        }

@dataclass
class Project:
    """
    PROYECTO: Contenedor global con configuracion comun
    Puede tener multiples PRODUCTOS (.STD files)
    """
    name: str
    description: str = ""
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    project_folder: Path = field(default_factory=Path)
    design_code: DesignCode = DesignCode.ASCE_7_22
    seismic_params: Optional[SeismicParameters] = None
    wind_params: Optional[WindParameters] = None
    load_case_mapping: Dict[str, LoadCaseMapping] = field(default_factory=dict)
    deflection_limits: List[DeflectionLimit] = field(default_factory=list)
    products: Dict[str, Product] = field(default_factory=dict)
    
    def add_product(self, product: Product) -> None:
        """Agregar producto al proyecto"""
        self.products[product.product_id] = product
        product.parent_project = self
    
    def remove_product(self, product_id: str) -> None:
        """Remover producto del proyecto"""
        if product_id in self.products:
            del self.products[product_id]
    
    def save(self, filepath: Path) -> None:
        """Guardar proyecto a JSON"""
        data = {
            "name": self.name,
            "description": self.description,
            "created_date": self.created_date.isoformat(),
            "modified_date": datetime.now().isoformat(),
            "project_folder": str(self.project_folder),
            "design_code": self.design_code.value,
            "seismic_params": self._serialize_seismic_params() if self.seismic_params else None,
            "wind_params": self._serialize_wind_params() if self.wind_params else None,
            "load_case_mapping": self._serialize_load_cases(),
            "deflection_limits": self._serialize_deflection_limits(),
            "products": {pid: p.to_dict() for pid, p in self.products.items()}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: Path) -> 'Project':
        """Cargar proyecto desde JSON - DESERIALIZACION COMPLETA"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Crear proyecto base
        project = cls(
            name=data["name"],
            description=data.get("description", ""),
            project_folder=Path(data["project_folder"]),
            design_code=DesignCode(data["design_code"])
        )
        
        # Restaurar fechas
        project.created_date = datetime.fromisoformat(data["created_date"])
        project.modified_date = datetime.fromisoformat(data["modified_date"])
        
        # Restaurar parametros sismicos
        if data.get("seismic_params"):
            sp_data = data["seismic_params"]
            project.seismic_params = SeismicParameters(
                design_code=DesignCode(sp_data["design_code"]),
                R_factor=sp_data["R_factor"],
                Cd_factor=sp_data["Cd_factor"],
                omega_factor=sp_data.get("omega_factor", 1.0),
                q_factor=sp_data.get("q_factor"),
                nu_factor=sp_data.get("nu_factor"),
                seismic_cases=sp_data.get("seismic_cases", {}),
                importance_factor=sp_data.get("importance_factor", 1.0),
                drift_limits=[
                    DriftLimit(
                        story_height_m=dl["story_height_m"],
                        drift_limit_percent=dl["drift_limit_percent"],
                        code_reference=dl["code_reference"]
                    )
                    for dl in sp_data.get("drift_limits", [])
                ]
            )
        
        # Restaurar parametros de viento
        if data.get("wind_params"):
            wp_data = data["wind_params"]
            project.wind_params = WindParameters(
                wind_cases=wp_data.get("wind_cases", {}),
                displacement_limit_h_over=wp_data.get("displacement_limit_h_over", 500.0),
                code_reference=wp_data.get("code_reference", "")
            )
        
        # Restaurar casos de carga
        for key, lc_data in data.get("load_case_mapping", {}).items():
            project.load_case_mapping[key] = LoadCaseMapping(
                staad_case_number=lc_data["staad_case_number"],
                staad_case_name=lc_data["staad_case_name"],
                case_type=LoadCaseType(lc_data["case_type"]),
                description=lc_data.get("description", "")
            )
        
        # Restaurar limites de deflexion
        for dl_data in data.get("deflection_limits", []):
            project.deflection_limits.append(
                DeflectionLimit(
                    member_type=dl_data["member_type"],
                    live_load_denominator=dl_data["live_load_denominator"],
                    total_load_denominator=dl_data["total_load_denominator"],
                    absolute_limit_mm=dl_data.get("absolute_limit_mm"),
                    code_reference=dl_data.get("code_reference", "")
                )
            )
        
        # Restaurar productos
        for pid, prod_data in data.get("products", {}).items():
            product = Product(
                product_id=prod_data["product_id"],
                name=prod_data["name"],
                description=prod_data.get("description", ""),
                staad_file_path=Path(prod_data["staad_file_path"]),
                last_analyzed=datetime.fromisoformat(prod_data["last_analyzed"]) if prod_data.get("last_analyzed") else None,
                is_valid=prod_data.get("is_valid", False)
            )
            project.add_product(product)
        
        return project
    
    def _serialize_seismic_params(self) -> dict:
        """Serializar parametros sismicos"""
        return {
            "design_code": self.seismic_params.design_code.value,
            "R_factor": self.seismic_params.R_factor,
            "Cd_factor": self.seismic_params.Cd_factor,
            "omega_factor": self.seismic_params.omega_factor,
            "q_factor": self.seismic_params.q_factor,
            "nu_factor": self.seismic_params.nu_factor,
            "seismic_cases": self.seismic_params.seismic_cases,
            "importance_factor": self.seismic_params.importance_factor,
            "drift_limits": [
                {
                    "story_height_m": dl.story_height_m,
                    "drift_limit_percent": dl.drift_limit_percent,
                    "code_reference": dl.code_reference
                }
                for dl in self.seismic_params.drift_limits
            ]
        }
    
    def _serialize_wind_params(self) -> dict:
        """Serializar parametros de viento"""
        return {
            "wind_cases": self.wind_params.wind_cases,
            "displacement_limit_h_over": self.wind_params.displacement_limit_h_over,
            "code_reference": self.wind_params.code_reference
        }
    
    def _serialize_load_cases(self) -> dict:
        """Serializar mapeo de casos de carga"""
        return {
            key: {
                "staad_case_number": lc.staad_case_number,
                "staad_case_name": lc.staad_case_name,
                "case_type": lc.case_type.value,
                "description": lc.description
            }
            for key, lc in self.load_case_mapping.items()
        }
    
    def _serialize_deflection_limits(self) -> list:
        """Serializar limites de deflexion"""
        return [
            {
                "member_type": dl.member_type,
                "live_load_denominator": dl.live_load_denominator,
                "total_load_denominator": dl.total_load_denominator,
                "absolute_limit_mm": dl.absolute_limit_mm,
                "code_reference": dl.code_reference
            }
            for dl in self.deflection_limits
        ]
