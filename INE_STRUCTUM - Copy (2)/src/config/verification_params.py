"""
Parametros de verificacion por codigo de diseño
Limites de deflexion y deriva segun ASCE 7-22, Eurocode 8, etc.
"""

from typing import Dict, List
from src.models.project import DeflectionLimit, DriftLimit, DesignCode

class VerificationParameters:
    """
    Base de datos de parametros de verificacion por norma
    """
    
    @staticmethod
    def get_deflection_limits(code: DesignCode) -> List[DeflectionLimit]:
        """
        Obtener limites de deflexion segun codigo
        """
        if code in [DesignCode.ASCE_7_22, DesignCode.ASCE_7_16]:
            return VerificationParameters._asce_deflection_limits()
        elif code == DesignCode.EUROCODE_8:
            return VerificationParameters._eurocode_deflection_limits()
        elif code == DesignCode.NSR_10:
            return VerificationParameters._nsr10_deflection_limits()
        else:
            return VerificationParameters._default_deflection_limits()
    
    @staticmethod
    def get_default_drift_limits(code: DesignCode, story_height: float = 3.5) -> List[DriftLimit]:
        """
        Obtener limites de deriva sismica por defecto segun codigo
        """
        if code in [DesignCode.ASCE_7_22, DesignCode.ASCE_7_16]:
            return [
                DriftLimit(
                    story_height_m=story_height,
                    drift_limit_percent=0.020,  # 2.0% para estructuras normales
                    code_reference="ASCE 7-22 Table 12.12-1"
                )
            ]
        elif code == DesignCode.EUROCODE_8:
            return [
                DriftLimit(
                    story_height_m=story_height,
                    drift_limit_percent=0.010,  # 1.0% (nu=0.5 para alta ductilidad)
                    code_reference="Eurocode 8 Section 4.4.3.2"
                )
            ]
        elif code == DesignCode.NSR_10:
            return [
                DriftLimit(
                    story_height_m=story_height,
                    drift_limit_percent=0.010,  # 1.0%
                    code_reference="NSR-10 A.6.4.2"
                )
            ]
        else:
            return [
                DriftLimit(
                    story_height_m=story_height,
                    drift_limit_percent=0.015,  # 1.5% conservador
                    code_reference="Default conservative value"
                )
            ]
    
    @staticmethod
    def _asce_deflection_limits() -> List[DeflectionLimit]:
        """
        ASCE 7-22 / IBC 2021 - Tabla 1604.3
        """
        return [
            # VIGAS - ROOF (Techos)
            DeflectionLimit(
                member_type="BEAM_ROOF",
                live_load_denominator=240.0,  # L/240
                total_load_denominator=180.0,  # L/180
                code_reference="IBC 2021 Table 1604.3 - Roof beams"
            ),
            
            # VIGAS - FLOOR (Pisos)
            DeflectionLimit(
                member_type="BEAM_PRIMARY",
                live_load_denominator=360.0,  # L/360
                total_load_denominator=240.0,  # L/240
                code_reference="IBC 2021 Table 1604.3 - Floor beams"
            ),
            
            # VIGAS SECUNDARIAS
            DeflectionLimit(
                member_type="BEAM_SECONDARY",
                live_load_denominator=360.0,  # L/360
                total_load_denominator=240.0,  # L/240
                code_reference="IBC 2021 Table 1604.3 - Floor beams"
            ),
            
            # VIGAS VOLADIZO
            DeflectionLimit(
                member_type="BEAM_CANTILEVER",
                live_load_denominator=180.0,  # L/180
                total_load_denominator=120.0,  # L/120 (mas permisivo)
                code_reference="IBC 2021 Table 1604.3 - Cantilevers"
            ),
            
            # COLUMNAS (generalmente no tienen limite de deflexion, solo deriva)
            DeflectionLimit(
                member_type="COLUMN_PRIMARY",
                live_load_denominator=999999.0,  # No aplica
                total_load_denominator=999999.0,  # No aplica
                code_reference="N/A - Check drift instead"
            ),
            
            # ARRIOSTRAMIENTOS (sin limite especifico)
            DeflectionLimit(
                member_type="BRACE_HORIZONTAL",
                live_load_denominator=240.0,  # Conservador
                total_load_denominator=180.0,
                code_reference="Engineering judgment"
            ),
        ]
    
    @staticmethod
    def _eurocode_deflection_limits() -> List[DeflectionLimit]:
        """
        Eurocode 1 - EN 1990 - Annex A1.4
        """
        return [
            # VIGAS - Techos
            DeflectionLimit(
                member_type="BEAM_ROOF",
                live_load_denominator=250.0,  # L/250
                total_load_denominator=200.0,  # L/200
                code_reference="EN 1990 Annex A1.4.3"
            ),
            
            # VIGAS - Pisos
            DeflectionLimit(
                member_type="BEAM_PRIMARY",
                live_load_denominator=300.0,  # L/300
                total_load_denominator=250.0,  # L/250
                code_reference="EN 1990 Annex A1.4.3"
            ),
            
            # VIGAS SECUNDARIAS
            DeflectionLimit(
                member_type="BEAM_SECONDARY",
                live_load_denominator=300.0,
                total_load_denominator=250.0,
                code_reference="EN 1990 Annex A1.4.3"
            ),
            
            # VOLADIZOS
            DeflectionLimit(
                member_type="BEAM_CANTILEVER",
                live_load_denominator=150.0,  # L/150
                total_load_denominator=100.0,
                code_reference="EN 1990 Annex A1.4.3"
            ),
            
            # COLUMNAS
            DeflectionLimit(
                member_type="COLUMN_PRIMARY",
                live_load_denominator=999999.0,
                total_load_denominator=999999.0,
                code_reference="N/A"
            ),
        ]
    
    @staticmethod
    def _nsr10_deflection_limits() -> List[DeflectionLimit]:
        """
        NSR-10 Colombia - Titulo B
        """
        return [
            # Similar a ASCE pero con valores colombianos
            DeflectionLimit(
                member_type="BEAM_ROOF",
                live_load_denominator=240.0,
                total_load_denominator=180.0,
                code_reference="NSR-10 B.2.5.1"
            ),
            
            DeflectionLimit(
                member_type="BEAM_PRIMARY",
                live_load_denominator=360.0,
                total_load_denominator=240.0,
                code_reference="NSR-10 B.2.5.1"
            ),
            
            DeflectionLimit(
                member_type="BEAM_SECONDARY",
                live_load_denominator=360.0,
                total_load_denominator=240.0,
                code_reference="NSR-10 B.2.5.1"
            ),
            
            DeflectionLimit(
                member_type="BEAM_CANTILEVER",
                live_load_denominator=180.0,
                total_load_denominator=120.0,
                code_reference="NSR-10 B.2.5.1"
            ),
            
            DeflectionLimit(
                member_type="COLUMN_PRIMARY",
                live_load_denominator=999999.0,
                total_load_denominator=999999.0,
                code_reference="N/A"
            ),
        ]
    
    @staticmethod
    def _default_deflection_limits() -> List[DeflectionLimit]:
        """
        Limites conservadores por defecto
        """
        return [
            DeflectionLimit(
                member_type="BEAM_ROOF",
                live_load_denominator=240.0,
                total_load_denominator=180.0,
                code_reference="Default conservative"
            ),
            DeflectionLimit(
                member_type="BEAM_PRIMARY",
                live_load_denominator=360.0,
                total_load_denominator=240.0,
                code_reference="Default conservative"
            ),
            DeflectionLimit(
                member_type="BEAM_SECONDARY",
                live_load_denominator=360.0,
                total_load_denominator=240.0,
                code_reference="Default conservative"
            ),
            DeflectionLimit(
                member_type="BEAM_CANTILEVER",
                live_load_denominator=180.0,
                total_load_denominator=120.0,
                code_reference="Default conservative"
            ),
            DeflectionLimit(
                member_type="COLUMN_PRIMARY",
                live_load_denominator=999999.0,
                total_load_denominator=999999.0,
                code_reference="N/A"
            ),
        ]
    
    @staticmethod
    def get_seismic_factors(code: DesignCode, system_type: str = "special_moment_frame") -> Dict[str, float]:
        """
        Obtener factores sismicos tipicos por codigo y tipo de sistema
        """
        if code in [DesignCode.ASCE_7_22, DesignCode.ASCE_7_16]:
            systems = {
                "special_moment_frame": {"R": 8.0, "Cd": 5.5, "Omega": 3.0},
                "intermediate_moment_frame": {"R": 5.0, "Cd": 4.5, "Omega": 3.0},
                "ordinary_moment_frame": {"R": 3.0, "Cd": 2.5, "Omega": 3.0},
                "special_concentrically_braced": {"R": 6.0, "Cd": 5.0, "Omega": 2.0},
                "eccentrically_braced": {"R": 8.0, "Cd": 4.0, "Omega": 2.0},
                "shear_wall": {"R": 6.0, "Cd": 5.0, "Omega": 2.5},
            }
            return systems.get(system_type, {"R": 5.0, "Cd": 4.5, "Omega": 2.5})
        
        elif code == DesignCode.EUROCODE_8:
            systems = {
                "special_moment_frame": {"q": 6.5, "nu": 0.5},
                "intermediate_moment_frame": {"q": 4.5, "nu": 0.5},
                "ordinary_moment_frame": {"q": 3.0, "nu": 0.5},
                "braced_frame": {"q": 4.0, "nu": 0.5},
                "shear_wall": {"q": 4.5, "nu": 0.5},
            }
            return systems.get(system_type, {"q": 4.0, "nu": 0.5})
        
        else:
            return {"R": 5.0, "Cd": 4.5, "Omega": 2.5}
