"""
Página de Configuración de Proyecto - ASCE 7-22 / AISC 360-22
ACTUALIZADO: Todos los campos se despliegan al seleccionar código
"""
import streamlit as st
from src.models.project import (
    Project, DesignCode, SiteClass, RiskCategory, LoadType, 
    LoadDirection, LoadCase, SeismicParameters, WindDriftParameters, 
    SeismicDriftParameters
)
from src.utils.seismic_calculator import ASCESeismicCalculator
from typing import Optional


class ProjectConfigUI:
    """Interfaz de configuración de proyecto"""
    
    @staticmethod
    def render():
        """Renderizar formulario completo"""
        st.title("⚙️ Configuración de Proyecto")
        
        # Inicializar session state
        if 'current_project' not in st.session_state:
            st.session_state.current_project = None
        
        # Sección 1: Datos Generales
        ProjectConfigUI._render_general_info()
        
        # Sección 2: Código de Diseño (TRIGGER)
        design_code = ProjectConfigUI._render_design_code()
        
        # Si hay código seleccionado, mostrar TODO
        if design_code:
            st.markdown("---")
            
            # Sección 3: Parámetros Sísmicos
            seismic_params = ProjectConfigUI._render_seismic_parameters()
            
            st.markdown("---")
            
            # Sección 4: Casos de Carga Primarios
            load_cases = ProjectConfigUI._render_load_cases()
            
            st.markdown("---")
            
            # Sección 5: Parámetros de Drift por VIENTO
            wind_drift = ProjectConfigUI._render_wind_drift_parameters()
            
            st.markdown("---")
            
            # Sección 6: Parámetros de Drift SÍSMICO
            seismic_drift = ProjectConfigUI._render_seismic_drift_parameters()
            
            st.markdown("---")
            
            # Botón Guardar (solo guarda, no activa nada)
            ProjectConfigUI._render_save_button(
                design_code, seismic_params, load_cases, 
                wind_drift, seismic_drift
            )
    
    # ========================================================================
    # SECCIÓN 1: DATOS GENERALES
    # ========================================================================
    
    @staticmethod
    def _render_general_info():
        """Renderizar datos generales del proyecto"""
        st.subheader("📋 Datos Generales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            project_code = st.text_input(
                "Código de Proyecto*",
                placeholder="PROJ-2025-001",
                key="project_code"
            )
            
            client = st.text_input(
                "Cliente*",
                placeholder="Empresa ABC S.A.",
                key="client"
            )
            
            engineer = st.text_input(
                "Ingeniero Responsable*",
                placeholder="Ing. Juan Pérez",
                key="engineer"
            )
        
        with col2:
            project_name = st.text_input(
                "Nombre del Proyecto*",
                placeholder="Edificio Oficinas Torre Central",
                key="project_name"
            )
            
            location = st.text_input(
                "Ubicación*",
                placeholder="Miami, FL, USA",
                key="location"
            )
    
    # ========================================================================
    # SECCIÓN 2: CÓDIGO DE DISEÑO (TRIGGER)
    # ========================================================================
    
    @staticmethod
    def _render_design_code() -> Optional[DesignCode]:
        """Renderizar selector de código de diseño"""
        st.subheader("📐 Código de Diseño")
        
        design_code_str = st.selectbox(
            "Seleccione el código de diseño*",
            options=["", "ASCE 7-22 / AISC 360-22 / ACI 318-19"],
            key="design_code"
        )
        
        if design_code_str == "ASCE 7-22 / AISC 360-22 / ACI 318-19":
            return DesignCode.ASCE722
        
        return None
    
    # ========================================================================
    # SECCIÓN 3: PARÁMETROS SÍSMICOS
    # ========================================================================
    
    @staticmethod
    def _render_seismic_parameters() -> SeismicParameters:
        """Renderizar parámetros del espectro sísmico"""
        st.subheader("🌍 Parámetros del Espectro de Respuesta Sísmica")
        st.caption("Referencia: ASCE 7-22 Chapter 11")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ss = st.number_input(
                "Ss (aceleración espectral, periodo corto)*",
                min_value=0.0,
                max_value=3.0,
                value=1.5,
                step=0.01,
                format="%.3f",
                key="ss"
            )
            
            site_class_str = st.selectbox(
                "Clase de Sitio*",
                options=["D", "A", "B", "C", "E", "F"],
                key="site_class"
            )
            
            tl = st.number_input(
                "TL (periodo de transición largo, seg)*",
                min_value=0.0,
                max_value=20.0,
                value=8.0,
                step=0.5,
                key="tl"
            )
        
        with col2:
            s1 = st.number_input(
                "S1 (aceleración espectral, 1 seg)*",
                min_value=0.0,
                max_value=2.0,
                value=0.6,
                step=0.01,
                format="%.3f",
                key="s1"
            )
            
            st.markdown("**Factores de Amplificación**")
            st.caption("(Calculados automáticamente)")
            
            # Crear parámetros temporales para cálculo
            site_class = SiteClass[site_class_str]
            temp_params = SeismicParameters(ss=ss, s1=s1, site_class=site_class, tl=tl)
            
            # Calcular
            calculated = ASCESeismicCalculator.calculate_design_parameters(temp_params)
            
            st.info(f"**Fa:** {calculated.fa:.3f}")
            st.info(f"**Fv:** {calculated.fv:.3f}")
        
        with col3:
            st.markdown("**Parámetros de Diseño**")
            st.caption("(Automático)")
            
            st.success(f"**SMS:** {calculated.sms:.3f}")
            st.success(f"**SM1:** {calculated.sm1:.3f}")
            st.success(f"**SDS:** {calculated.sds:.3f}")
            st.success(f"**SD1:** {calculated.sd1:.3f}")
            st.success(f"**SDC:** {calculated.sdc}")
        
        return calculated
    
    # ========================================================================
    # SECCIÓN 4: CASOS DE CARGA PRIMARIOS
    # ========================================================================
    
    @staticmethod
    def _render_load_cases() -> list:
        """Renderizar tabla de casos de carga primarios"""
        st.subheader("📋 Casos de Carga Primarios")
        
        # Inicializar datos por defecto
        if 'load_cases_data' not in st.session_state:
            st.session_state.load_cases_data = [
                {"no": 1, "name": "DEAD", "type": "Dead", "direction": "-", "seismic_x": False},
                {"no": 2, "name": "SDL", "type": "Super Dead", "direction": "-", "seismic_x": False},
                {"no": 3, "name": "LIVE", "type": "Live", "direction": "-", "seismic_x": False},
                {"no": 5, "name": "WIND_X+", "type": "Wind", "direction": "+X", "seismic_x": False},
                {"no": 6, "name": "WIND_X-", "type": "Wind", "direction": "-X", "seismic_x": False},
                {"no": 7, "name": "WIND_Z+", "type": "Wind", "direction": "+Z", "seismic_x": False},
                {"no": 8, "name": "WIND_Z-", "type": "Wind", "direction": "-Z", "seismic_x": False},
                {"no": 9, "name": "SEISMIC_X", "type": "Seismic", "direction": "X", "seismic_x": True},
                {"no": 10, "name": "SEISMIC_Z", "type": "Seismic", "direction": "Z", "seismic_x": False},
            ]
        
        # Renderizar tabla editable
        st.caption("Clasificación y dirección de casos de carga")
        
        # Headers
        cols = st.columns([1, 3, 2, 2, 1.5])
        cols[0].markdown("**No.**")
        cols[1].markdown("**Nombre**")
        cols[2].markdown("**Tipo**")
        cols[3].markdown("**Dirección**")
        cols[4].markdown("**Sismo X?**")
        
        # Filas
        load_cases = []
        for i, lc_data in enumerate(st.session_state.load_cases_data):
            cols = st.columns([1, 3, 2, 2, 1.5])
            
            with cols[0]:
                st.text(str(lc_data["no"]))
            
            with cols[1]:
                name = st.text_input(
                    "Nombre", 
                    value=lc_data["name"], 
                    key=f"lc_name_{i}",
                    label_visibility="collapsed"
                )
            
            with cols[2]:
                load_type = st.selectbox(
                    "Tipo",
                    options=["Dead", "Super Dead", "Live", "Roof Live", "Snow", "Wind", "Seismic", "Temperature"],
                    index=["Dead", "Super Dead", "Live", "Roof Live", "Snow", "Wind", "Seismic", "Temperature"].index(lc_data["type"]),
                    key=f"lc_type_{i}",
                    label_visibility="collapsed"
                )
            
            with cols[3]:
                direction = st.selectbox(
                    "Dirección",
                    options=["-", "+X", "-X", "+Y", "-Y", "+Z", "-Z", "X", "Y", "Z"],
                    index=["-", "+X", "-X", "+Y", "-Y", "+Z", "-Z", "X", "Y", "Z"].index(lc_data["direction"]),
                    key=f"lc_dir_{i}",
                    label_visibility="collapsed"
                )
            
            with cols[4]:
                seismic_x = st.checkbox(
                    "X?",
                    value=lc_data["seismic_x"],
                    key=f"lc_sx_{i}",
                    label_visibility="collapsed"
                )
            
            # Crear objeto LoadCase
            lc = LoadCase(
                staad_number=lc_data["no"],
                name=name,
                load_type=LoadType[load_type.upper().replace(" ", "")],
                direction=LoadDirection[direction.replace("+", "PLUS_").replace("-", "MINUS_").replace("X", "X").replace("Y", "Y").replace("Z", "Z")] if direction != "-" else LoadDirection.NONE,
                is_seismic_x=seismic_x
            )
            load_cases.append(lc)
        
        # Botones de control
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ Agregar Fila"):
                st.session_state.load_cases_data.append({
                    "no": len(st.session_state.load_cases_data) + 1,
                    "name": f"CASO_{len(st.session_state.load_cases_data) + 1}",
                    "type": "Live",
                    "direction": "-",
                    "seismic_x": False
                })
                st.rerun()
        
        with col2:
            if st.button("🗑️ Eliminar Última") and len(st.session_state.load_cases_data) > 0:
                st.session_state.load_cases_data.pop()
                st.rerun()
        
        return load_cases
    
    # ========================================================================
    # SECCIÓN 5: PARÁMETROS DE DRIFT POR VIENTO
    # ========================================================================
    
    @staticmethod
    def _render_wind_drift_parameters() -> WindDriftParameters:
        """Renderizar parámetros de drift por viento"""
        st.subheader("🌬️ Parámetros de Drift por Viento")
        st.caption("Referencia: ASCE 7-22 Appendix C.1.2")
        
        check_wind = st.checkbox(
            "☑️ Verificar drift por viento",
            value=True,
            key="check_wind_drift"
        )
        
        if check_wind:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Límite de drift total (edificio completo)**")
                total_denominator = st.selectbox(
                    "Seleccione límite",
                    options=[400, 500, 600],
                    format_func=lambda x: f"H/{x}",
                    key="wind_total_denom"
                )
            
            with col2:
                st.markdown("**Límite de drift de entrepiso**")
                story_denominator = st.selectbox(
                    "Seleccione límite",
                    options=[200, 300, 400, 600],
                    format_func=lambda x: f"h/{x}",
                    key="wind_story_denom"
                )
            
            return WindDriftParameters(
                check_wind_drift=True,
                total_drift_denominator=total_denominator,
                story_drift_denominator=story_denominator
            )
        
        return WindDriftParameters(check_wind_drift=False)
    
    # ========================================================================
    # SECCIÓN 6: PARÁMETROS DE DRIFT SÍSMICO
    # ========================================================================
    
    @staticmethod
    def _render_seismic_drift_parameters() -> SeismicDriftParameters:
        """Renderizar parámetros de drift sísmico"""
        st.subheader("🏗️ Parámetros de Drift Sísmico")
        st.caption("Referencia: ASCE 7-22 Table 12.12-1")
        
        col1, col2 = st.columns(2)
        
        with col1:
            risk_cat_str = st.selectbox(
                "Categoría de Riesgo Sísmico*",
                options=["I", "II", "III", "IV"],
                index=1,
                key="risk_category"
            )
            
            is_shear_wall = st.checkbox(
                "Estructura con muros de cortante (Δa/hsx ≤ 0.020)",
                value=False,
                key="is_shear_wall"
            )
            
            cd_factor = st.number_input(
                "Factor de amplificación Cd*",
                min_value=1.0,
                max_value=10.0,
                value=5.5,
                step=0.5,
                help="Típico: 5.5 para SMF, 4.5 para IMF, 5.0 para SCBF",
                key="cd_factor"
            )
        
        with col2:
            # Determinar límite automático
            risk_cat = RiskCategory[risk_cat_str]
            
            if is_shear_wall or risk_cat in [RiskCategory.III, RiskCategory.IV]:
                default_limit = 0.020
            else:
                default_limit = 0.025
            
            drift_limit = st.number_input(
                "Límite de drift de entrepiso (Δa/hsx)*",
                min_value=0.001,
                max_value=0.050,
                value=default_limit,
                step=0.001,
                format="%.3f",
                key="drift_limit"
            )
            
            story_height = st.number_input(
                "Altura típica de entrepiso (hsx, metros)*",
                min_value=2.0,
                max_value=10.0,
                value=3.5,
                step=0.1,
                key="story_height"
            )
        
        st.info(f"""
        **Fórmula de verificación:** Δa = Cd × δxe ≤ {drift_limit:.3f} × hsx
        
        Donde:
        - **Δa:** Drift amplificado de diseño
        - **Cd:** Factor de amplificación = {cd_factor}
        - **δxe:** Deflexión elástica del análisis STAAD
        - **hsx:** Altura del piso = {story_height} m
        """)
        
        return SeismicDriftParameters(
            risk_category=risk_cat,
            is_shear_wall=is_shear_wall,
            drift_limit=drift_limit,
            cd_factor=cd_factor,
            story_height_m=story_height
        )
    
    # ========================================================================
    # SECCIÓN 7: BOTÓN GUARDAR
    # ========================================================================
    
    @staticmethod
    def _render_save_button(design_code, seismic_params, load_cases, wind_drift, seismic_drift):
        """Renderizar botón de guardar"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("💾 Guardar Proyecto", type="primary", use_container_width=True):
                # Validar campos obligatorios
                if not st.session_state.get("project_code"):
                    st.error("❌ Debe ingresar el código de proyecto")
                    return
                
                if not st.session_state.get("project_name"):
                    st.error("❌ Debe ingresar el nombre del proyecto")
                    return
                
                # Crear objeto Project
                project = Project(
                    project_code=st.session_state.project_code,
                    project_name=st.session_state.project_name,
                    client=st.session_state.get("client", ""),
                    location=st.session_state.get("location", ""),
                    engineer=st.session_state.get("engineer", ""),
                    design_code=design_code,
                    load_cases=load_cases,
                    seismic_params=seismic_params,
                    wind_drift=wind_drift,
                    seismic_drift=seismic_drift
                )
                
                # Guardar en session state
                st.session_state.current_project = project
                
                st.success("✅ Proyecto guardado exitosamente")
                
                # TODO: Guardar en base de datos/JSON
