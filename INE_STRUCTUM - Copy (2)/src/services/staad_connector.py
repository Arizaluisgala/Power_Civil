"""
Conector con STAAD.Pro usando openstaadpy
Maneja la conexion y operaciones basicas
"""

import logging
from typing import Optional, Dict, List
from pathlib import Path

try:
    from openstaadpy import os_analytical
    OPENSTAAD_AVAILABLE = True
except ImportError:
    OPENSTAAD_AVAILABLE = False
    print("openstaadpy no esta instalado")

class STAADConnectionError(Exception):
    '''Excepcion personalizada para errores de conexion'''
    pass

class STAADConnector:
    '''
    Gestor de conexion con STAAD.Pro
    
    Uso:
        connector = STAADConnector()
        if connector.connect():
            # usar connector.staad para acceder a API
            pass
    '''
    
    def __init__(self):
        self.staad = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
        if not OPENSTAAD_AVAILABLE:
            self.logger.error("openstaadpy no disponible")
    
    def connect(self, file_path: Optional[str] = None) -> bool:
        '''
        Conectar a instancia activa de STAAD.Pro
        
        Args:
            file_path: Ruta opcional del archivo .std a abrir
            
        Returns:
            True si conexion exitosa
        '''
        if not OPENSTAAD_AVAILABLE:
            self.logger.error("Cannot connect: openstaadpy not installed")
            return False
        
        try:
            self.logger.info("Intentando conectar a STAAD.Pro...")
            self.staad = os_analytical.connect()
            
            # Verificar version (staad es directamente OSRoot)
            version = self.staad.GetApplicationVersion()
            self.logger.info(f"Conectado a STAAD.Pro version {version}")
            
            # Abrir archivo si se especifico
            if file_path:
                success = self.open_file(file_path)
                if not success:
                    return False
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error al conectar: {str(e)}")
            self.is_connected = False
            return False
    
    def open_file(self, file_path: str) -> bool:
        '''
        Abrir archivo STAAD
        
        Args:
            file_path: Ruta completa del archivo .std
            
        Returns:
            True si se abrio correctamente
        '''
        if not self.staad:
            self.logger.error("No hay conexion activa")
            return False
        
        try:
            path = Path(file_path).resolve()
            
            if not path.exists():
                self.logger.error(f"Archivo no existe: {file_path}")
                return False
            
            self.logger.info(f"Abriendo archivo: {path}")
            self.staad.OpenSTAADFile(str(path))
            self.logger.info("Archivo abierto correctamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al abrir archivo: {str(e)}")
            return False
    
    def verify_analysis(self) -> bool:
        '''
        Verificar que el modelo este analizado
        
        Returns:
            True si hay resultados disponibles
        '''
        if not self.is_connected:
            return False
        
        try:
            has_results = self.staad.Output.AreResultsAvailable()
            
            if not has_results:
                self.logger.warning("El modelo no tiene resultados")
            
            return has_results
            
        except Exception as e:
            self.logger.error(f"Error al verificar analisis: {str(e)}")
            return False
    
    def get_base_units(self) -> Dict[str, str]:
        '''
        Obtener unidades base del modelo
        
        Returns:
            Diccionario con unidades
        '''
        if not self.is_connected:
            return {}
        
        try:
            units = {
                'length': self.staad.GetInputUnitForLength(),
                'force': self.staad.GetInputUnitForForce(),
                'base': self.staad.GetBaseUnit()
            }
            
            self.logger.info(f"Unidades del modelo: {units}")
            return units
            
        except Exception as e:
            self.logger.error(f"Error al obtener unidades: {str(e)}")
            return {}
    
    def get_conversion_factor_to_mm(self) -> float:
        '''
        Obtener factor de conversion de unidades del modelo a mm
        
        Returns:
            Factor multiplicador
        '''
        units = self.get_base_units()
        length_unit = units.get('length', '').lower()
        
        # Factores de conversion a mm
        factors = {
            'm': 1000.0,
            'meter': 1000.0,
            'cm': 10.0,
            'mm': 1.0,
            'ft': 304.8,
            'feet': 304.8,
            'in': 25.4,
            'inch': 25.4
        }
        
        return factors.get(length_unit, 1000.0)  # Default: metros
    
    def close(self):
        '''Cerrar conexion con STAAD'''
        if self.staad:
            try:
                self.logger.info("Cerrando conexion con STAAD.Pro")
                self.staad = None
                self.is_connected = False
            except Exception as e:
                self.logger.error(f"Error al cerrar: {str(e)}")
    
    def __enter__(self):
        '''Context manager entry'''
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        '''Context manager exit'''
        self.close()
