"""
Modelos de datos para Proyecto
ACTUALIZADO: Enfoque ASCE 7-22 / AISC 360-22 / ACI 318
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class DesignCode(Enum):
    """Códigos de diseño soportados"""
    ASCE722 = "ASCE 7-22"
    AISC36022 = "AISC 360-22"
    ACI318 = "ACI 318-19"


class SiteClass(Enum):
    """Clase de sitio sísmico según ASCE 7-22 Table 20.3-1"""
    A = "A - Hard rock"
    B = "B - Rock"
    C = "C - Very dense soil and soft rock"
    D = "D - Stiff soil"
    E = "E - Soft clay soil"
    F = "F - Soils requiring site response analysis"


class RiskCategory(Enum):
    """Categoría de riesgo sísmico según ASCE 7-22 Table 1.5-1"""
    I = "I - Low hazard"
    II = "II - Standard occupancy"
    III = "III - Substantial public hazard"
    IV = "IV - Essential facilities"


class LoadType(Enum):
    """Tipos de carga según STAAD.Pro"""
    DEAD = "Dead"
    SUPERDEAD = "Super Dead"
    LIVE = "Live"
    ROOFLIVE = "Roof Live"
    SNOW = "Snow"
    WIND = "Wind"
    SEISMIC = "Seismic"
    TEMPERATURE = "Temperature"
    FLUID = "Fluid"
    SOIL = "Soil"
    ACCIDENTAL = "Accidental"


class LoadDirection(Enum):
    """Dirección de carga"""
    PLUS_X = "+X"
    MINUS_X = "-X"
    PLUS_Y = "+Y"
    MINUS_Y = "-Y"
    PLUS_Z = "+Z"
    MINUS_Z = "-Z"
    NONE = "-"


@dataclass
class LoadCase:
    """Caso de carga primario"""
    staad_number: int
    name: str
    load_type: LoadType
    direction: LoadDirection = LoadDirection.NONE
    is_seismic_x: bool = False  # Para clasificación de sismo en X
    is_seismic_z: bool = False  # Para clasificación de sismo en Z
    is_vertical_seismic: bool = False  # Para componente vertical


@dataclass
class SeismicParameters:
    """Parámetros sísmicos según ASCE 7-22 Chapter 11"""
    # Aceleraciones espectrales
    ss: float = 0.0  # Short-period spectral acceleration
    s1: float = 0.0  # 1-second spectral acceleration
    
    # Clase de sitio y factores
    site_class: SiteClass = SiteClass.D
    fa: Optional[float] = None  # Automático si None
    fv: Optional[float] = None  # Automático si None
    
    # Periodo de transición
    tl: float = 8.0  # Typical default
    
    # Resultados calculados (automático)
    sms: Optional[float] = None  # Fa × Ss
    sm1: Optional[float] = None  # Fv × S1
    sds: Optional[float] = None  # (2/3) × SMS
    sd1: Optional[float] = None  # (2/3) × SM1
    sdc: Optional[str] = None  # A, B, C, D, E, F


@dataclass
class WindDriftParameters:
    """Parámetros de deriva por viento según ASCE 7-22 Appendix C"""
    check_wind_drift: bool = False
    
    # Drift total del edificio
    total_drift_denominator: Optional[int] = 400  # H/400, H/500, H/600
    use_custom_total: bool = False
    custom_total_mm: Optional[float] = None
    
    # Drift de entrepiso
    story_drift_denominator: Optional[int] = 300  # h/300
    use_custom_story: bool = False
    custom_story_mm: Optional[float] = None


@dataclass
class SeismicDriftParameters:
    """Parámetros de deriva sísmica según ASCE 7-22 Table 12.12-1"""
    risk_category: RiskCategory = RiskCategory.II
    
    # Tipo de estructura
    is_shear_wall: bool = False
    is_risk_iii_iv: bool = False
    
    # Límite de deriva (default según tabla)
    drift_limit: float = 0.020  # 2.0% para Risk Cat I/II general
    
    # Factor de amplificación
    cd_factor: float = 5.5  # Típico para SMF
    
    # Altura típica de entrepiso
    story_height_m: float = 3.5


@dataclass
class DeflectionVerification:
    """Verificación de deflexión individual - CON SELECTOR DE TIPO"""
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
class Project:
    """Proyecto de verificación estructural - ENFOQUE ASCE"""
    # Identificación
    project_code: str
    project_name: str
    client: str
    location: str
    engineer: str
    
    # Código de diseño
    design_code: DesignCode = DesignCode.ASCE722
    
    # Casos de carga primarios
    load_cases: List[LoadCase] = field(default_factory=list)
    
    # Parámetros sísmicos
    seismic_params: SeismicParameters = field(default_factory=SeismicParameters)
    
    # Parámetros de deriva
    wind_drift: WindDriftParameters = field(default_factory=WindDriftParameters)
    seismic_drift: SeismicDriftParameters = field(default_factory=SeismicDriftParameters)
    
    # NOTA: Las tablas de deflexión se movieron a Product
    
    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    modified_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario para JSON"""
        return {
            "project_code": self.project_code,
            "project_name": self.project_name,
            "client": self.client,
            "location": self.location,
            "engineer": self.engineer,
            "design_code": self.design_code.value,
            "load_cases": [
                {
                    "staad_number": lc.staad_number,
                    "name": lc.name,
                    "load_type": lc.load_type.value,
                    "direction": lc.direction.value,
                    "is_seismic_x": lc.is_seismic_x,
                    "is_seismic_z": lc.is_seismic_z,
                    "is_vertical_seismic": lc.is_vertical_seismic
                }
                for lc in self.load_cases
            ],
            "seismic_params": {
                "ss": self.seismic_params.ss,
                "s1": self.seismic_params.s1,
                "site_class": self.seismic_params.site_class.value,
                "fa": self.seismic_params.fa,
                "fv": self.seismic_params.fv,
                "tl": self.seismic_params.tl,
                "sms": self.seismic_params.sms,
                "sm1": self.seismic_params.sm1,
                "sds": self.seismic_params.sds,
                "sd1": self.seismic_params.sd1,
                "sdc": self.seismic_params.sdc
            },
            "wind_drift": {
                "check_wind_drift": self.wind_drift.check_wind_drift,
                "total_drift_denominator": self.wind_drift.total_drift_denominator,
                "use_custom_total": self.wind_drift.use_custom_total,
                "custom_total_mm": self.wind_drift.custom_total_mm,
                "story_drift_denominator": self.wind_drift.story_drift_denominator,
                "use_custom_story": self.wind_drift.use_custom_story,
                "custom_story_mm": self.wind_drift.custom_story_mm
            },
            "seismic_drift": {
                "risk_category": self.seismic_drift.risk_category.value,
                "is_shear_wall": self.seismic_drift.is_shear_wall,
                "is_risk_iii_iv": self.seismic_drift.is_risk_iii_iv,
                "drift_limit": self.seismic_drift.drift_limit,
                "cd_factor": self.seismic_drift.cd_factor,
                "story_height_m": self.seismic_drift.story_height_m
            },
            "created_date": self.created_date,
            "modified_date": self.modified_date
        }
