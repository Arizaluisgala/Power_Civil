"""
Gestor de Proyectos y Productos
Maneja la creacion, carga, guardado y operaciones sobre proyectos
"""

import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import uuid

from src.models.project import (
    Project, Product, DesignCode, 
    SeismicParameters, WindParameters,
    LoadCaseMapping, LoadCaseType
)
from src.config.verification_params import VerificationParameters

class ProjectManager:
    """
    Gestor centralizado de proyectos
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_project: Optional[Project] = None
        self.current_product: Optional[Product] = None
    
    def create_new_project(
        self,
        name: str,
        project_folder: Path,
        design_code: DesignCode = DesignCode.ASCE_7_22,
        description: str = ""
    ) -> Project:
        """
        Crear nuevo proyecto con configuracion por defecto
        """
        self.logger.info(f"Creando nuevo proyecto: {name}")
        
        # Crear carpeta del proyecto si no existe
        project_folder = Path(project_folder)
        project_folder.mkdir(parents=True, exist_ok=True)
        
        # Crear proyecto
        project = Project(
            name=name,
            description=description,
            project_folder=project_folder,
            design_code=design_code
        )
        
        # Configurar parametros por defecto segun norma
        self._setup_default_parameters(project, design_code)
        
        self.current_project = project
        
        self.logger.info(f"Proyecto creado: {project.name}")
        return project
    
    def _setup_default_parameters(self, project: Project, code: DesignCode):
        """
        Configurar parametros por defecto segun norma
        """
        # Obtener limites de deflexion por codigo
        project.deflection_limits = VerificationParameters.get_deflection_limits(code)
        
        # Configurar parametros sismicos basicos
        seismic_factors = VerificationParameters.get_seismic_factors(
            code, 
            system_type="special_moment_frame"
        )
        
        if code in [DesignCode.ASCE_7_22, DesignCode.ASCE_7_16]:
            project.seismic_params = SeismicParameters(
                design_code=code,
                R_factor=seismic_factors["R"],
                Cd_factor=seismic_factors["Cd"],
                omega_factor=seismic_factors["Omega"]
            )
        elif code == DesignCode.EUROCODE_8:
            project.seismic_params = SeismicParameters(
                design_code=code,
                R_factor=1.0,  # No aplica en Eurocode
                Cd_factor=1.0,  # No aplica
                q_factor=seismic_factors["q"],
                nu_factor=seismic_factors["nu"]
            )
        
        # Configurar derivas por defecto
        project.seismic_params.drift_limits = VerificationParameters.get_default_drift_limits(code)
        
        # Configurar parametros de viento
        project.wind_params = WindParameters()
        
        self.logger.info(f"Parametros configurados para {code.value}")
    
    def add_product_to_project(
        self,
        project: Project,
        product_name: str,
        staad_file_path: Path,
        description: str = ""
    ) -> Product:
        """
        Agregar producto (.STD) al proyecto
        """
        self.logger.info(f"Agregando producto: {product_name}")
        
        # Generar ID unico
        product_id = str(uuid.uuid4())[:8]
        
        # Crear producto
        product = Product(
            product_id=product_id,
            name=product_name,
            description=description,
            staad_file_path=Path(staad_file_path)
        )
        
        # Agregar al proyecto
        project.add_product(product)
        
        self.logger.info(f"Producto agregado: {product_name} (ID: {product_id})")
        return product
    
    def save_project(self, project: Project, filepath: Optional[Path] = None) -> None:
        """
        Guardar proyecto a archivo JSON
        """
        if filepath is None:
            # Guardar en carpeta del proyecto
            filepath = project.project_folder / f"{project.name}.inestructum"
        
        filepath = Path(filepath)
        
        self.logger.info(f"Guardando proyecto en: {filepath}")
        project.save(filepath)
        self.logger.info("Proyecto guardado exitosamente")
    
    def load_project(self, filepath: Path) -> Project:
        """
        Cargar proyecto desde archivo JSON
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Archivo de proyecto no encontrado: {filepath}")
        
        self.logger.info(f"Cargando proyecto desde: {filepath}")
        project = Project.load(filepath)
        
        self.current_project = project
        self.logger.info(f"Proyecto cargado: {project.name}")
        
        return project
    
    def set_load_case_mapping(
        self,
        project: Project,
        staad_case_number: int,
        staad_case_name: str,
        case_type: LoadCaseType,
        description: str = ""
    ) -> None:
        """
        Mapear caso de carga de STAAD a tipo
        """
        mapping_key = f"LC{staad_case_number}"
        
        mapping = LoadCaseMapping(
            staad_case_number=staad_case_number,
            staad_case_name=staad_case_name,
            case_type=case_type,
            description=description
        )
        
        project.load_case_mapping[mapping_key] = mapping
        
        self.logger.info(
            f"Caso de carga mapeado: LC{staad_case_number} '{staad_case_name}' -> {case_type.value}"
        )
    
    def auto_detect_load_cases(
        self,
        project: Project,
        load_case_names: List[str]
    ) -> None:
        """
        Detectar automaticamente tipos de casos de carga desde nombres
        """
        self.logger.info("Auto-detectando tipos de casos de carga...")
        
        for idx, case_name in enumerate(load_case_names, start=1):
            case_name_lower = case_name.lower()
            
            # Detectar tipo basado en palabras clave
            if any(kw in case_name_lower for kw in ["dead", "muerta", "pp", "permanente"]):
                case_type = LoadCaseType.DEAD
            elif any(kw in case_name_lower for kw in ["live", "viva", "cv", "sobrecarga"]):
                if "roof" in case_name_lower or "techo" in case_name_lower:
                    case_type = LoadCaseType.LIVE_ROOF
                else:
                    case_type = LoadCaseType.LIVE
            elif any(kw in case_name_lower for kw in ["wind", "viento"]):
                if "+x" in case_name_lower or "px" in case_name_lower:
                    case_type = LoadCaseType.WIND_X_POS
                elif "-x" in case_name_lower or "nx" in case_name_lower:
                    case_type = LoadCaseType.WIND_X_NEG
                elif "+z" in case_name_lower or "pz" in case_name_lower:
                    case_type = LoadCaseType.WIND_Z_POS
                elif "-z" in case_name_lower or "nz" in case_name_lower:
                    case_type = LoadCaseType.WIND_Z_NEG
                else:
                    case_type = LoadCaseType.OTHER
            elif any(kw in case_name_lower for kw in ["seismic", "sismo", "earthquake"]):
                if "x" in case_name_lower and "y" not in case_name_lower:
                    case_type = LoadCaseType.SEISMIC_X
                elif "z" in case_name_lower:
                    case_type = LoadCaseType.SEISMIC_Z
                elif "y" in case_name_lower:
                    case_type = LoadCaseType.SEISMIC_Y
                else:
                    case_type = LoadCaseType.OTHER
            elif any(kw in case_name_lower for kw in ["temp", "temperature", "thermal"]):
                case_type = LoadCaseType.TEMPERATURE
            elif any(kw in case_name_lower for kw in ["settlement", "asentamiento"]):
                case_type = LoadCaseType.SETTLEMENT
            else:
                case_type = LoadCaseType.OTHER
            
            self.set_load_case_mapping(
                project,
                staad_case_number=idx,
                staad_case_name=case_name,
                case_type=case_type,
                description=f"Auto-detected from name: {case_name}"
            )
        
        self.logger.info(f"Auto-deteccion completada: {len(load_case_names)} casos mapeados")
    
    def get_project_summary(self, project: Project) -> str:
        """
        Generar resumen del proyecto
        """
        lines = [
            "="*60,
            f"PROYECTO: {project.name}",
            "="*60,
            f"Descripcion: {project.description}",
            f"Codigo de diseño: {project.design_code.value}",
            f"Carpeta: {project.project_folder}",
            f"Creado: {project.created_date.strftime('%Y-%m-%d %H:%M')}",
            f"Modificado: {project.modified_date.strftime('%Y-%m-%d %H:%M')}",
            "",
            f"Productos: {len(project.products)}",
        ]
        
        for product in project.products.values():
            lines.append(f"  - {product.name} ({product.product_id})")
            lines.append(f"    Archivo: {product.staad_file_path.name}")
            if product.last_analyzed:
                lines.append(f"    Ultimo analisis: {product.last_analyzed.strftime('%Y-%m-%d %H:%M')}")
        
        lines.append("")
        lines.append(f"Casos de carga mapeados: {len(project.load_case_mapping)}")
        lines.append(f"Limites de deflexion: {len(project.deflection_limits)}")
        
        # Parametros sismicos
        if project.seismic_params:
            lines.append("")
            lines.append("PARAMETROS SISMICOS:")
            lines.append(f"  R = {project.seismic_params.R_factor}")
            lines.append(f"  Cd = {project.seismic_params.Cd_factor}")
            if project.seismic_params.q_factor:
                lines.append(f"  q = {project.seismic_params.q_factor}")
        
        lines.append("="*60)
        
        return "\n".join(lines)
