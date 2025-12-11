"""
Modelos de datos para el sistema INE STRUCTUM
Representa entidades estructurales de STAAD.Pro
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import numpy as np

# ============================================
# ENUMERACIONES
# ============================================

class LoadType(Enum):
    '''Tipos de carga segun normativa'''
    DEAD = "MUERTA"
    LIVE = "VIVA"
    WIND = "VIENTO"
    SEISMIC = "SISMO"
    SNOW = "NIEVE"
    COMBINATION = "COMBINACION"
    ENVELOPE = "ENVOLVENTE"

class MemberType(Enum):
    '''Tipos de miembros estructurales - GRUPOS REALES DE LA MACRO'''
    # Columnas
    COLUMN_PRIMARY = "_COLUMNAS_PRIN"
    COLUMN_SECONDARY = "_COLUMNAS_SEC"
    
    # Vigas
    BEAM_PRIMARY = "_VIGAS_PRIN"
    BEAM_SECONDARY = "_VIGAS_SEC"
    BEAM_CORREAS = "_VIGAS_CORREAS"
    BEAM_VOLADIZO = "_VIGAS_VOLADIZO"
    
    # Arriostramientos
    BRACE_VERTICAL = "_ARRIOST_VERT"
    BRACE_HORIZONTAL = "_ARRIOST_HORIZ"
    
    # Elementos especiales
    GIANT = "_GIGANTES"
    CARRIL_TRACK = "_VIGA_CARRIL_TR"
    FUNDATION = "_FUNDACION"
    MONORRIEL = "_MONORRIEL"
    GRUA = "_VIGA_GRUA"
    
    # Desconocido
    UNKNOWN = "_DESCONOCIDO"
    
    @classmethod
    def from_group_name(cls, group_name: str) -> 'MemberType':
        '''Obtener MemberType desde nombre de grupo'''
        group_upper = group_name.upper().strip()
        
        # Mapeo de nombres de grupo a tipos
        mapping = {
            "_COLUMNAS_PRIN": cls.COLUMN_PRIMARY,
            "_COLUMNAS_SEC": cls.COLUMN_SECONDARY,
            "_VIGAS_PRIN": cls.BEAM_PRIMARY,
            "_VIGAS_SEC": cls.BEAM_SECONDARY,
            "_VIGAS_CORREAS": cls.BEAM_CORREAS,
            "_VIGAS_VOLADIZO": cls.BEAM_VOLADIZO,
            "_ARRIOST_VERT": cls.BRACE_VERTICAL,
            "_ARRIOST_HORIZ": cls.BRACE_HORIZONTAL,
            "_GIGANTES": cls.GIANT,
            "_VIGA_CARRIL_TR": cls.CARRIL_TRACK,
            "_FUNDACION": cls.FUNDATION,
            "_MONORRIEL": cls.MONORRIEL,
            "_VIGA_GRUA": cls.GRUA,
        }
        
        return mapping.get(group_upper, cls.UNKNOWN)
    
    def is_column(self) -> bool:
        '''Verificar si es una columna'''
        return self in [self.COLUMN_PRIMARY, self.COLUMN_SECONDARY]
    
    def is_beam(self) -> bool:
        '''Verificar si es una viga'''
        return self in [
            self.BEAM_PRIMARY, 
            self.BEAM_SECONDARY, 
            self.BEAM_CORREAS, 
            self.BEAM_VOLADIZO,
            self.CARRIL_TRACK,
            self.MONORRIEL,
            self.GRUA
        ]
    
    def is_brace(self) -> bool:
        '''Verificar si es un arriostamiento'''
        return self in [self.BRACE_VERTICAL, self.BRACE_HORIZONTAL]
    
    def requires_deflection_check(self) -> bool:
        '''Verificar si requiere verificacion de deflexion'''
        # Todas las vigas y arriostramientos horizontales
        return self.is_beam() or self == self.BRACE_HORIZONTAL
    
    def requires_drift_check(self) -> bool:
        '''Verificar si requiere verificacion de deriva'''
        # Solo columnas
        return self.is_column()
    
    def get_default_deflection_limit(self) -> float:
        '''Obtener limite de deflexion por defecto (L/XXX)'''
        if self == self.BEAM_PRIMARY:
            return 240.0  # L/240
        elif self == self.BEAM_SECONDARY:
            return 240.0
        elif self == self.BEAM_CORREAS:
            return 180.0  # L/180
        elif self == self.BEAM_VOLADIZO:
            return 180.0
        elif self == self.BRACE_HORIZONTAL:
            return 180.0
        elif self == self.CARRIL_TRACK:
            return 400.0  # L/400 (mas restrictivo)
        elif self == self.MONORRIEL:
            return 400.0
        elif self == self.GRUA:
            return 600.0  # L/600 (muy restrictivo)
        else:
            return 240.0  # Default

class NormType(Enum):
    '''Normas de diseno soportadas'''
    ACI = "ACI 318"
    ASCE = "ASCE 7"
    EUROCODE = "EUROCODE 2"
    NSR10 = "NSR-10"

# ============================================
# MODELOS GEOMETRICOS
# ============================================

@dataclass
class Node:
    '''Nodo del modelo estructural'''
    id: int
    x: float
    y: float
    z: float
    displacements: Dict[int, np.ndarray] = field(default_factory=dict)
    
    def get_displacement(self, load_case: int) -> Optional[np.ndarray]:
        '''Obtener desplazamiento para un caso de carga'''
        return self.displacements.get(load_case)
    
    def distance_to(self, other: 'Node') -> float:
        '''Calcular distancia a otro nodo'''
        return np.sqrt(
            (self.x - other.x)**2 + 
            (self.y - other.y)**2 + 
            (self.z - other.z)**2
        )

@dataclass
class AnalyticalMember:
    '''Miembro analitico individual'''
    id: int
    node_a: int
    node_b: int
    length: float
    group: str = "_DESCONOCIDO"
    member_type: MemberType = MemberType.UNKNOWN
    
    def get_direction_vector(self, nodes: Dict[int, Node]) -> np.ndarray:
        '''Obtener vector director del miembro'''
        node_a = nodes[self.node_a]
        node_b = nodes[self.node_b]
        
        dx = node_b.x - node_a.x
        dy = node_b.y - node_a.y
        dz = node_b.z - node_a.z
        
        return np.array([dx, dy, dz])
    
    def is_vertical(self, nodes: Dict[int, Node], tolerance: float = 0.1) -> bool:
        '''Verificar si el miembro es vertical (columna)'''
        direction = self.get_direction_vector(nodes)
        
        # Normalizar
        length = np.linalg.norm(direction)
        if length == 0:
            return False
        
        direction_normalized = direction / length
        
        # Vector vertical (eje Y)
        vertical = np.array([0, 1, 0])
        
        # Producto punto (coseno del angulo)
        cos_angle = abs(np.dot(direction_normalized, vertical))
        
        # Si cos(angle) > 0.9, el miembro es casi vertical (< 25 grados)
        return cos_angle > (1 - tolerance)

@dataclass
class PhysicalMember:
    '''Physical Member (agrupacion de miembros analiticos)'''
    id: int
    analytical_members: List[int]
    total_length: float
    start_node: int
    end_node: int
    ordered_nodes: List[int] = field(default_factory=list)
    member_type: MemberType = MemberType.UNKNOWN
    
    def get_all_nodes(self, members: Dict[int, AnalyticalMember]) -> List[int]:
        '''Obtener todos los nodos ordenados del PM'''
        if self.ordered_nodes:
            return self.ordered_nodes
        
        # Recolectar todos los nodos
        nodes_set = set()
        for am_id in self.analytical_members:
            if am_id in members:
                member = members[am_id]
                nodes_set.add(member.node_a)
                nodes_set.add(member.node_b)
        
        self.ordered_nodes = sorted(list(nodes_set))
        return self.ordered_nodes

# ============================================
# MODELOS DE RESULTADOS
# ============================================

@dataclass
class DeflectionResult:
    '''Resultado de verificacion de deflexion'''
    member_id: int
    pm_id: Optional[int]
    load_case: int
    load_type: LoadType
    max_deflection_y: float  # mm
    max_deflection_z: float  # mm
    verification_length: float  # m
    verification_coeff: float  # L/180, L/240, etc.
    permissible_deflection: float  # mm
    complies: bool
    ratio: float  # deflection/permissible
    location: float = 0.0  # Distancia desde inicio
    group_name: str = "_DESCONOCIDO"
    
    def get_status_color(self) -> str:
        '''Color segun estado de cumplimiento'''
        if not self.complies:
            return "red"
        elif self.ratio > 0.9:
            return "orange"
        else:
            return "green"

@dataclass
class DriftResult:
    '''Resultado de deriva de entrepiso'''
    story_name: str
    story_height: float  # m
    load_case: int
    load_type: LoadType
    drift_x: float  # mm
    drift_z: float  # mm
    drift_ratio_x: float
    drift_ratio_z: float
    limit: float  # 0.01 tipico
    complies: bool
    max_drift_ratio: float
    critical_column_id: Optional[int] = None
    
    def get_drift_percentage(self, axis: str = 'max') -> float:
        '''Obtener deriva como porcentaje'''
        if axis == 'x':
            return self.drift_ratio_x * 100
        elif axis == 'z':
            return self.drift_ratio_z * 100
        else:
            return max(self.drift_ratio_x, self.drift_ratio_z) * 100

# ============================================
# MODELOS DE CONFIGURACION
# ============================================

@dataclass
class AnalysisParameters:
    '''Parametros de analisis del proyecto'''
    norm: NormType = NormType.ACI
    deflection_limits: Dict[MemberType, float] = field(default_factory=dict)
    drift_limit: float = 0.01
    load_factors: Dict[LoadType, float] = field(default_factory=dict)
    unit_system: str = "Metric"
    
    def __post_init__(self):
        '''Inicializar limites por defecto'''
        if not self.deflection_limits:
            # Usar limites especificos de cada tipo
            self.deflection_limits = {
                MemberType.BEAM_PRIMARY: 240,
                MemberType.BEAM_SECONDARY: 240,
                MemberType.BEAM_CORREAS: 180,
                MemberType.BEAM_VOLADIZO: 180,
                MemberType.BRACE_HORIZONTAL: 180,
                MemberType.CARRIL_TRACK: 400,
                MemberType.MONORRIEL: 400,
                MemberType.GRUA: 600,
            }
        
        if not self.load_factors:
            self.load_factors = {
                LoadType.DEAD: 1.0,
                LoadType.LIVE: 1.0,
                LoadType.WIND: 0.7,
                LoadType.SEISMIC: 1.0,
            }

@dataclass
class ProjectInfo:
    '''Informacion del proyecto'''
    name: str
    code: str
    description: str = ""
    engineer: str = ""
    company: str = "INELECTRA"
    norm: NormType = NormType.ACI
    staad_file_path: str = ""
    excel_output_path: str = ""

@dataclass
class StructuralModel:
    '''Modelo estructural completo'''
    nodes: Dict[int, Node] = field(default_factory=dict)
    members: Dict[int, AnalyticalMember] = field(default_factory=dict)
    physical_members: Dict[int, PhysicalMember] = field(default_factory=dict)
    groups: Dict[str, List[int]] = field(default_factory=dict)
    load_cases: List[int] = field(default_factory=list)
    load_types: Dict[int, LoadType] = field(default_factory=dict)
    project_info: Optional[ProjectInfo] = None
    parameters: Optional[AnalysisParameters] = None
    
    def get_members_by_group(self, group_name: str) -> List[AnalyticalMember]:
        '''Obtener miembros de un grupo'''
        if group_name not in self.groups:
            return []
        
        return [self.members[mid] for mid in self.groups[group_name] 
                if mid in self.members]
    
    def get_columns(self) -> List[AnalyticalMember]:
        '''Obtener todas las columnas'''
        return [m for m in self.members.values() 
                if m.member_type.is_column()]
    
    def get_beams(self) -> List[AnalyticalMember]:
        '''Obtener todas las vigas'''
        return [m for m in self.members.values() 
                if m.member_type.is_beam()]
    
    def get_members_requiring_deflection_check(self) -> List[AnalyticalMember]:
        '''Obtener miembros que requieren verificacion de deflexion'''
        return [m for m in self.members.values() 
                if m.member_type.requires_deflection_check()]
    
    def get_members_requiring_drift_check(self) -> List[AnalyticalMember]:
        '''Obtener miembros que requieren verificacion de deriva'''
        return [m for m in self.members.values() 
                if m.member_type.requires_drift_check()]
