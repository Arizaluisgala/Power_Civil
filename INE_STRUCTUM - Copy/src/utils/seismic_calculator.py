"""
Calculadora de parámetros sísmicos según ASCE 7-22
"""
from src.models.project import SeismicParameters, SiteClass, RiskCategory


class ASCESeismicCalculator:
    """Calculadora de parámetros sísmicos ASCE 7-22 Chapter 11"""
    
    # Tabla 11.4-1: Site Coefficient Fa
    FA_TABLE = {
        SiteClass.A: {0.25: 0.8, 0.5: 0.8, 0.75: 0.8, 1.0: 0.8, 1.25: 0.8},
        SiteClass.B: {0.25: 0.9, 0.5: 0.9, 0.75: 0.9, 1.0: 0.9, 1.25: 0.9},
        SiteClass.C: {0.25: 1.3, 0.5: 1.3, 0.75: 1.2, 1.0: 1.2, 1.25: 1.2},
        SiteClass.D: {0.25: 1.6, 0.5: 1.4, 0.75: 1.2, 1.0: 1.1, 1.25: 1.0},
        SiteClass.E: {0.25: 2.4, 0.5: 1.7, 0.75: 1.3, 1.0: 1.1, 1.25: 0.9},
    }
    
    # Tabla 11.4-2: Site Coefficient Fv
    FV_TABLE = {
        SiteClass.A: {0.1: 0.8, 0.2: 0.8, 0.3: 0.8, 0.4: 0.8, 0.5: 0.8},
        SiteClass.B: {0.1: 0.8, 0.2: 0.8, 0.3: 0.8, 0.4: 0.8, 0.5: 0.8},
        SiteClass.C: {0.1: 1.5, 0.2: 1.5, 0.3: 1.5, 0.4: 1.5, 0.5: 1.5},
        SiteClass.D: {0.1: 2.4, 0.2: 2.2, 0.3: 2.0, 0.4: 1.9, 0.5: 1.8},
        SiteClass.E: {0.1: 4.2, 0.2: 3.3, 0.3: 2.8, 0.4: 2.4, 0.5: 2.2},
    }
    
    @staticmethod
    def calculate_fa(ss: float, site_class: SiteClass) -> float:
        """Calcular Fa por interpolación de Table 11.4-1"""
        if site_class == SiteClass.F:
            return None  # Requiere análisis específico
        
        table = ASCESeismicCalculator.FA_TABLE.get(site_class, {})
        keys = sorted(table.keys())
        
        # Interpolar
        for i, key in enumerate(keys):
            if ss <= key:
                if i == 0:
                    return table[key]
                # Interpolación lineal
                x0, x1 = keys[i-1], key
                y0, y1 = table[x0], table[x1]
                return y0 + (ss - x0) * (y1 - y0) / (x1 - x0)
        
        return table[keys[-1]]  # Extrapolar con último valor
    
    @staticmethod
    def calculate_fv(s1: float, site_class: SiteClass) -> float:
        """Calcular Fv por interpolación de Table 11.4-2"""
        if site_class == SiteClass.F:
            return None
        
        table = ASCESeismicCalculator.FV_TABLE.get(site_class, {})
        keys = sorted(table.keys())
        
        for i, key in enumerate(keys):
            if s1 <= key:
                if i == 0:
                    return table[key]
                x0, x1 = keys[i-1], key
                y0, y1 = table[x0], table[x1]
                return y0 + (s1 - x0) * (y1 - y0) / (x1 - x0)
        
        return table[keys[-1]]
    
    @staticmethod
    def calculate_design_parameters(params: SeismicParameters) -> SeismicParameters:
        """Calcular SMS, SM1, SDS, SD1 y SDC"""
        # 1. Calcular Fa y Fv si no están dados
        if params.fa is None:
            params.fa = ASCESeismicCalculator.calculate_fa(params.ss, params.site_class)
        
        if params.fv is None:
            params.fv = ASCESeismicCalculator.calculate_fv(params.s1, params.site_class)
        
        # 2. Calcular SMS y SM1 (Section 11.4.4)
        if params.fa is not None:
            params.sms = params.fa * params.ss
            params.sds = (2.0 / 3.0) * params.sms
        
        if params.fv is not None:
            params.sm1 = params.fv * params.s1
            params.sd1 = (2.0 / 3.0) * params.sm1
        
        # 3. Determinar SDC (Table 11.6-1 y 11.6-2)
        # Simplificado - usar el mayor de ambas tablas
        sdc_from_sds = ASCESeismicCalculator._get_sdc_from_sds(params.sds)
        sdc_from_sd1 = ASCESeismicCalculator._get_sdc_from_sd1(params.sd1)
        
        # El SDC es el MAYOR de ambos
        sdc_order = ['A', 'B', 'C', 'D', 'E']
        params.sdc = max(sdc_from_sds, sdc_from_sd1, key=lambda x: sdc_order.index(x))
        
        return params
    
    @staticmethod
    def _get_sdc_from_sds(sds: float) -> str:
        """Determinar SDC desde SDS (simplificado para Risk Cat II)"""
        if sds < 0.167:
            return 'A'
        elif sds < 0.33:
            return 'B'
        elif sds < 0.50:
            return 'C'
        elif sds < 0.75:
            return 'D'
        else:
            return 'E'
    
    @staticmethod
    def _get_sdc_from_sd1(sd1: float) -> str:
        """Determinar SDC desde SD1 (simplificado para Risk Cat II)"""
        if sd1 < 0.067:
            return 'A'
        elif sd1 < 0.133:
            return 'B'
        elif sd1 < 0.20:
            return 'C'
        elif sd1 < 0.30:
            return 'D'
        else:
            return 'E'
