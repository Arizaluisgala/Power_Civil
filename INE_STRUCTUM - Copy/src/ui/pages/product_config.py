"""
Página de Configuración de Producto
INCLUYE: Tablas de deflexión (migradas desde proyecto)
"""
import streamlit as st
from src.models.product import Product, DeflectionVerification, HorizontalDeflectionVerification


class ProductConfigUI:
    """Interfaz de configuración de producto"""
    
    @staticmethod
    def render():
        """Renderizar formulario completo"""
        st.title("📦 Configuración de Producto")
        
        # Verificar que hay proyecto seleccionado
        if 'current_project' not in st.session_state or st.session_state.current_project is None:
            st.warning("⚠️ Debe configurar un proyecto primero")
            return
        
        # Datos generales del producto
        ProductConfigUI._render_general_info()
        
        st.markdown("---")
        
        # Factores sísmicos del producto
        ProductConfigUI._render_seismic_factors()
        
        st.markdown("---")
        
        # Tabla 1: Deflexiones Verticales
        ProductConfigUI._render_vertical_deflection_table()
        
        st.markdown("---")
        
        # Tabla 2: Deflexiones Horizontales
        ProductConfigUI._render_horizontal_deflection_table()
        
        st.markdown("---")
        
        # Botón Guardar
        ProductConfigUI._render_save_button()
    
    @staticmethod
    def _render_general_info():
        """Datos generales del producto"""
        st.subheader("📋 Datos Generales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_code = st.text_input(
                "Código de Producto*",
                placeholder="PROD-2025-001",
                key="product_code"
            )
            
            staad_path = st.text_input(
                "Ruta del modelo STAAD.Pro*",
                placeholder="C:/Proyectos/Modelo.std",
                key="staad_path"
            )
        
        with col2:
            product_name = st.text_input(
                "Nombre del Producto*",
                placeholder="Edificio Principal",
                key="product_name"
            )
            
            structural_system = st.selectbox(
                "Sistema Estructural*",
                options=[
                    "Special Moment Frame (SMF)",
                    "Intermediate Moment Frame (IMF)",
                    "Ordinary Moment Frame (OMF)",
                    "Special Concentrically Braced Frame (SCBF)",
                    "Eccentrically Braced Frame (EBF)"
                ],
                key="structural_system"
            )
    
    @staticmethod
    def _render_seismic_factors():
        """Factores sísmicos específicos del producto"""
        st.subheader("🌊 Factores Sísmicos del Producto")
        st.caption("Según ASCE 7-22 Table 12.2-1")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            r_factor = st.number_input(
                "Factor R (Response Modification)*",
                min_value=1.0,
                max_value=10.0,
                value=8.0,
                step=0.5,
                help="Típico: 8.0 para SMF, 5.0 para IMF",
                key="r_factor"
            )
        
        with col2:
            cd_factor = st.number_input(
                "Factor Cd (Deflection Amplification)*",
                min_value=1.0,
                max_value=10.0,
                value=5.5,
                step=0.5,
                help="Típico: 5.5 para SMF, 4.5 para IMF",
                key="cd_factor_product"
            )
        
        with col3:
            omega_factor = st.number_input(
                "Factor Ω₀ (Overstrength)*",
                min_value=1.0,
                max_value=5.0,
                value=3.0,
                step=0.5,
                help="Típico: 3.0 para SMF/IMF",
                key="omega_factor"
            )
    
    @staticmethod
    def _render_vertical_deflection_table():
        """Tabla 1: Deflexiones Verticales con SELECTOR DE TIPO"""
        st.subheader("📊 Tabla 1: Límites de Deflexión Vertical")
        st.caption("Cada grupo puede verificarse por FACTOR (L/denominador) O por LÍMITE ABSOLUTO (mm)")
        
        # Inicializar datos
        if 'deflection_table' not in st.session_state:
            st.session_state.deflection_table = [
                {"group": "VIGASPRIN", "c1": True, "c1_factor": True, "c1_denom": 240.0, "c1_limit": None, "c1_type": "Live Load (L)",
                 "c2": True, "c2_factor": True, "c2_denom": 360.0, "c2_limit": None, "c2_type": "Carga Muerta + Carga Viva (D+L)",
                 "c3": True, "c3_factor": True, "c3_denom": 120.0, "c3_limit": None, "c3_type": "Wind (W)"},
                {"group": "VIGASSEC", "c1": True, "c1_factor": True, "c1_denom": 240.0, "c1_limit": None, "c1_type": "Live Load (L)",
                 "c2": True, "c2_factor": True, "c2_denom": 360.0, "c2_limit": None, "c2_type": "Carga Muerta + Carga Viva (D+L)",
                 "c3": False, "c3_factor": True, "c3_denom": None, "c3_limit": None, "c3_type": ""},
            ]
        
        # Renderizar tabla
        for i, row in enumerate(st.session_state.deflection_table):
            with st.expander(f"📐 Grupo: **{row['group']}**", expanded=True):
                cols = st.columns([2, 3, 3, 3])
                
                # Columna 1: Nombre del grupo
                with cols[0]:
                    st.markdown(f"**{row['group']}**")
                
                # Columna 2: CASO 1
                with cols[1]:
                    st.markdown("**Caso 1**")
                    c1_enabled = st.checkbox("Habilitar", value=row['c1'], key=f"c1_en_{i}")
                    
                    if c1_enabled:
                        c1_factor = st.radio(
                            "Tipo",
                            options=["L/denominador", "Límite absoluto (mm)"],
                            index=0 if row['c1_factor'] else 1,
                            key=f"c1_type_{i}",
                            horizontal=True
                        )
                        
                        if c1_factor == "L/denominador":
                            c1_denom = st.number_input("Denominador", value=row['c1_denom'] or 240.0, key=f"c1_d_{i}")
                            c1_limit = None
                        else:
                            c1_denom = None
                            c1_limit = st.number_input("Límite (mm)", value=row['c1_limit'] or 25.0, key=f"c1_l_{i}")
                        
                        c1_type = st.text_input("Tipo de carga", value=row['c1_type'], key=f"c1_lt_{i}")
                
                # Columna 3: CASO 2
                with cols[2]:
                    st.markdown("**Caso 2**")
                    c2_enabled = st.checkbox("Habilitar", value=row['c2'], key=f"c2_en_{i}")
                    
                    if c2_enabled:
                        c2_factor = st.radio(
                            "Tipo",
                            options=["L/denominador", "Límite absoluto (mm)"],
                            index=0 if row['c2_factor'] else 1,
                            key=f"c2_type_{i}",
                            horizontal=True
                        )
                        
                        if c2_factor == "L/denominador":
                            c2_denom = st.number_input("Denominador", value=row['c2_denom'] or 360.0, key=f"c2_d_{i}")
                            c2_limit = None
                        else:
                            c2_denom = None
                            c2_limit = st.number_input("Límite (mm)", value=row['c2_limit'] or 20.0, key=f"c2_l_{i}")
                        
                        c2_type = st.text_input("Tipo de carga", value=row['c2_type'], key=f"c2_lt_{i}")
                
                # Columna 4: CASO 3
                with cols[3]:
                    st.markdown("**Caso 3**")
                    c3_enabled = st.checkbox("Habilitar", value=row['c3'], key=f"c3_en_{i}")
                    
                    if c3_enabled:
                        c3_factor = st.radio(
                            "Tipo",
                            options=["L/denominador", "Límite absoluto (mm)"],
                            index=0 if row['c3_factor'] else 1,
                            key=f"c3_type_{i}",
                            horizontal=True
                        )
                        
                        if c3_factor == "L/denominador":
                            c3_denom = st.number_input("Denominador", value=row['c3_denom'] or 120.0, key=f"c3_d_{i}")
                            c3_limit = None
                        else:
                            c3_denom = None
                            c3_limit = st.number_input("Límite (mm)", value=row['c3_limit'] or 30.0, key=f"c3_l_{i}")
                        
                        c3_type = st.text_input("Tipo de carga", value=row['c3_type'], key=f"c3_lt_{i}")
        
        # Botones de control
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("➕ Agregar Grupo"):
                st.session_state.deflection_table.append({
                    "group": "NUEVO_GRUPO",
                    "c1": False, "c1_factor": True, "c1_denom": None, "c1_limit": None, "c1_type": "",
                    "c2": False, "c2_factor": True, "c2_denom": None, "c2_limit": None, "c2_type": "",
                    "c3": False, "c3_factor": True, "c3_denom": None, "c3_limit": None, "c3_type": ""
                })
                st.rerun()
    
    @staticmethod
    def _render_horizontal_deflection_table():
        """Tabla 2: Deflexiones Horizontales con SELECTOR DE TIPO"""
        st.subheader("📊 Tabla 2: Límites de Deflexión Horizontal")
        st.caption("Cada grupo puede verificarse por FACTOR (H/denominador) O por LÍMITE ABSOLUTO (mm)")
        
        # Inicializar datos
        if 'horiz_deflection_table' not in st.session_state:
            st.session_state.horiz_deflection_table = [
                {"group": "COLUMNAS", "enabled": True, "use_factor": True, "denom": 400.0, "limit": None, "type": "Wind (W)"},
            ]
        
        # Renderizar tabla
        for i, row in enumerate(st.session_state.horiz_deflection_table):
            with st.expander(f"📐 Grupo: **{row['group']}**", expanded=True):
                cols = st.columns([2, 4])
                
                with cols[0]:
                    st.markdown(f"**{row['group']}**")
                    enabled = st.checkbox("Habilitar verificación", value=row['enabled'], key=f"h_en_{i}")
                
                with cols[1]:
                    if enabled:
                        use_factor = st.radio(
                            "Tipo de Verificación",
                            options=["H/denominador", "Límite absoluto (mm)"],
                            index=0 if row['use_factor'] else 1,
                            key=f"h_type_{i}",
                            horizontal=True
                        )
                        
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            if use_factor == "H/denominador":
                                denom = st.number_input("Denominador", value=row['denom'] or 400.0, key=f"h_d_{i}")
                                limit = None
                            else:
                                denom = None
                                limit = st.number_input("Límite (mm)", value=row['limit'] or 25.0, key=f"h_l_{i}")
                        
                        with col_b:
                            load_type = st.text_input("Tipo de carga", value=row['type'], key=f"h_lt_{i}")
    
    @staticmethod
    def _render_save_button():
        """Botón guardar producto"""
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("💾 Guardar Producto", type="primary", use_container_width=True):
                # TODO: Validar y crear objeto Product
                st.success("✅ Producto guardado exitosamente")
