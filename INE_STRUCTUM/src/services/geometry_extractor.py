"""
Extractor de geometria del modelo STAAD.Pro
CON SOPORTE COMPLETO DE PHYSICAL MEMBERS Y GRUPOS
VERSION CORREGIDA
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.models.data_models import (
    Node, AnalyticalMember, PhysicalMember, 
    StructuralModel, MemberType
)
from src.services.staad_connector import STAADConnector
from src.services import geometry_extensions as geo_ext

class GeometryExtractor:
    """
    Extrae geometria completa del modelo STAAD
    Incluye Physical Members y clasificacion por grupos
    """
    
    def __init__(self, connector: STAADConnector):
        if not connector.is_connected:
            raise ValueError("Connector must be connected to STAAD.Pro")
        
        self.staad = connector.staad
        self.logger = logging.getLogger(__name__)
        self.conversion_factor = connector.get_conversion_factor_to_mm()
    
    def extract_complete_model(self) -> StructuralModel:
        """Extraccion completa de geometria CON PHYSICAL MEMBERS"""
        
        self.logger.info("="*60)
        self.logger.info("INICIANDO EXTRACCION COMPLETA DE GEOMETRIA")
        self.logger.info("="*60)
        
        model = StructuralModel()
        
        # PASO 1: Extraer nodos
        self.logger.info("\n[1/6] Extrayendo nodos...")
        model.nodes = self._extract_nodes()
        self.logger.info(f"Extraidos: {len(model.nodes)} nodos")
        
        # PASO 2: Extraer miembros analiticos
        self.logger.info("\n[2/6] Extrayendo miembros analiticos...")
        model.members = self._extract_members()
        self.logger.info(f"Extraidos: {len(model.members)} miembros")
        
        # PASO 3: Extraer PHYSICAL MEMBERS (CORREGIDO)
        self.logger.info("\n[3/6] Extrayendo Physical Members...")
        model.physical_members = self._extract_physical_members(model)
        self.logger.info(f"Extraidos: {len(model.physical_members)} Physical Members")
        
        # PASO 4: Extraer grupos (CORREGIDO)
        self.logger.info("\n[4/6] Extrayendo grupos desde STAAD...")
        model.groups = self._extract_groups()
        
        if len(model.groups) > 0:
            self.logger.info(f"Extraidos: {len(model.groups)} grupos desde STAAD")
            self._classify_members_from_groups(model)
        else:
            self.logger.warning("No se encontraron grupos, usando clasificacion geometrica...")
            self.logger.info("\n[5/6] Clasificando por GEOMETRIA (fallback)...")
            model.groups = self._classify_by_geometry(model)
            self.logger.info(f"Creados: {len(model.groups)} grupos por geometria")
        
        # PASO 6: Estadisticas
        self.logger.info("\n[6/6] Generando estadisticas...")
        self._print_statistics(model)
        
        self.logger.info("\n" + "="*60)
        self.logger.info("EXTRACCION COMPLETADA EXITOSAMENTE")
        self.logger.info("="*60)
        
        return model
    
    def _extract_nodes(self) -> Dict[int, Node]:
        """Extraer todos los nodos"""
        nodes = {}
        
        try:
            node_list = self.staad.Geometry.GetNodeList()
            total = len(node_list)
            
            for idx, node_id in enumerate(node_list, 1):
                if idx % 50 == 0:
                    self.logger.info(f"  Progreso: {idx}/{total}")
                
                coords = self.staad.Geometry.GetNodeCoordinates(node_id)
                x, y, z = coords
                
                nodes[node_id] = Node(id=node_id, x=x, y=y, z=z)
            
            return nodes
            
        except Exception as e:
            self.logger.error(f"Error extrayendo nodos: {str(e)}")
            return nodes
    
    def _extract_members(self) -> Dict[int, AnalyticalMember]:
        """Extraer miembros analiticos"""
        members = {}
        
        try:
            beam_list = self.staad.Geometry.GetBeamList()
            total = len(beam_list)
            
            for idx, beam_id in enumerate(beam_list, 1):
                if idx % 50 == 0:
                    self.logger.info(f"  Progreso: {idx}/{total}")
                
                incidence = self.staad.Geometry.GetMemberIncidence(beam_id)
                node_a, node_b = incidence
                
                length = self.staad.Geometry.GetBeamLength(beam_id)
                
                members[beam_id] = AnalyticalMember(
                    id=beam_id,
                    node_a=node_a,
                    node_b=node_b,
                    length=length,
                    group="_DESCONOCIDO"
                )
            
            return members
            
        except Exception as e:
            self.logger.error(f"Error extrayendo miembros: {str(e)}")
            return members
    
    def _extract_physical_members(self, model: StructuralModel) -> Dict[int, PhysicalMember]:
        """
        Extraer PHYSICAL MEMBERS usando funciones corregidas
        """
        physical_members = {}
        
        try:
            pm_count = self.staad.Geometry.GetPhysicalMemberCount()
            
            if pm_count == 0:
                self.logger.warning("  No hay Physical Members definidos")
                return physical_members
            
            self.logger.info(f"  Procesando {pm_count} Physical Members...")
            
            # USAR FUNCION CORREGIDA
            pm_list = geo_ext.GetPhysicalMemberList(self.staad.Geometry)
            
            if not pm_list:
                self.logger.warning("  GetPhysicalMemberList retorno lista vacia")
                pm_list = list(range(1, pm_count + 1))
            
            for idx, pm_id in enumerate(pm_list, 1):
                if idx % 10 == 0:
                    self.logger.info(f"    Progreso: {idx}/{len(pm_list)}")
                
                try:
                    # USAR FUNCION CORREGIDA
                    am_list = geo_ext.GetAnalyticalMembersForPhysicalMember(
                        self.staad.Geometry, pm_id
                    )
                    
                    if not am_list:
                        continue
                    
                    # Filtrar IDs validos
                    am_list = [am_id for am_id in am_list if am_id in model.members and am_id != 0]
                    
                    if not am_list:
                        continue
                    
                    # Calcular longitud total
                    total_length = sum(model.members[am_id].length for am_id in am_list)
                    
                    # Ordenar nodos
                    ordered_nodes = self._order_pm_nodes(am_list, model.members)
                    
                    if not ordered_nodes:
                        continue
                    
                    start_node = ordered_nodes[0]
                    end_node = ordered_nodes[-1]
                    
                    # Crear Physical Member
                    physical_members[pm_id] = PhysicalMember(
                        id=pm_id,
                        analytical_members=am_list,
                        total_length=total_length,
                        start_node=start_node,
                        end_node=end_node,
                        ordered_nodes=ordered_nodes
                    )
                    
                    # Asignar PM ID a miembros analiticos
                    for am_id in am_list:
                        model.members[am_id].physical_member_id = pm_id
                    
                except Exception as e:
                    self.logger.debug(f"    Error en PM {pm_id}: {str(e)}")
                    continue
            
            return physical_members
            
        except Exception as e:
            self.logger.error(f"Error extrayendo Physical Members: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return physical_members
    
    def _order_pm_nodes(self, am_list: List[int], members: Dict[int, AnalyticalMember]) -> List[int]:
        """Ordenar nodos de Physical Member"""
        if not am_list:
            return []
        
        nodes_set = set()
        connections = {}
        
        for am_id in am_list:
            if am_id not in members:
                continue
            
            member = members[am_id]
            node_a, node_b = member.node_a, member.node_b
            
            nodes_set.add(node_a)
            nodes_set.add(node_b)
            
            if node_a not in connections:
                connections[node_a] = []
            if node_b not in connections:
                connections[node_b] = []
            
            connections[node_a].append(node_b)
            connections[node_b].append(node_a)
        
        if not nodes_set:
            return []
        
        # Encontrar nodo inicial (extremo)
        start_node = min(nodes_set, key=lambda n: len(connections.get(n, [])))
        
        ordered = [start_node]
        visited = {start_node}
        
        current = start_node
        while len(ordered) < len(nodes_set):
            next_nodes = [n for n in connections.get(current, []) if n not in visited]
            
            if not next_nodes:
                break
            
            next_node = next_nodes[0]
            ordered.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return ordered
    
    def _extract_groups(self) -> Dict[str, List[int]]:
        """Extraer grupos usando funcion corregida"""
        groups = {}
        
        try:
            # USAR FUNCION CORREGIDA para obtener nombres de grupos de miembros
            group_names = geo_ext.GetGroupNames(self.staad.Geometry, grouptype=0)
            
            if not group_names:
                self.logger.warning("  No se encontraron grupos de miembros")
                return groups
            
            for group_name in group_names:
                try:
                    # USAR FUNCION CORREGIDA para obtener miembros del grupo
                    members = geo_ext.GetGroupEntities(self.staad.Geometry, group_name)
                    
                    if members:
                        groups[group_name] = members
                        self.logger.info(f"  Grupo '{group_name}': {len(members)} miembros")
                        
                except Exception as e:
                    self.logger.debug(f"  Error en grupo '{group_name}': {e}")
            
            return groups
            
        except Exception as e:
            self.logger.warning(f"  Error extrayendo grupos: {str(e)}")
            return groups
    
    def _classify_by_geometry(self, model: StructuralModel) -> Dict[str, List[int]]:
        """Clasificar por geometria (fallback)"""
        
        self.logger.info("  Analizando orientacion de miembros...")
        
        groups = {
            "_COLUMNAS_PRIN": [],
            "_VIGAS_PRIN": [],
            "_ARRIOST_HORIZ": [],
            "_DESCONOCIDO": []
        }
        
        for member_id, member in model.members.items():
            node_a = model.nodes[member.node_a]
            node_b = model.nodes[member.node_b]
            
            dx = node_b.x - node_a.x
            dy = node_b.y - node_a.y
            dz = node_b.z - node_a.z
            
            length = np.sqrt(dx**2 + dy**2 + dz**2)
            if length == 0:
                groups["_DESCONOCIDO"].append(member_id)
                member.group = "_DESCONOCIDO"
                member.member_type = MemberType.UNKNOWN
                continue
            
            dx_norm = dx / length
            dy_norm = dy / length
            dz_norm = dz / length
            
            vertical_threshold = 0.8
            horizontal_threshold = 0.15
            
            if abs(dy_norm) > vertical_threshold:
                groups["_COLUMNAS_PRIN"].append(member_id)
                member.group = "_COLUMNAS_PRIN"
                member.member_type = MemberType.COLUMN_PRIMARY
            elif abs(dy_norm) < horizontal_threshold:
                groups["_VIGAS_PRIN"].append(member_id)
                member.group = "_VIGAS_PRIN"
                member.member_type = MemberType.BEAM_PRIMARY
            else:
                groups["_ARRIOST_HORIZ"].append(member_id)
                member.group = "_ARRIOST_HORIZ"
                member.member_type = MemberType.BRACE_HORIZONTAL
        
        self.logger.info(f"  Columnas: {len(groups['_COLUMNAS_PRIN'])}")
        self.logger.info(f"  Vigas: {len(groups['_VIGAS_PRIN'])}")
        self.logger.info(f"  Arriostramientos: {len(groups['_ARRIOST_HORIZ'])}")
        
        return groups
    
    def _classify_members_from_groups(self, model: StructuralModel):
        """Clasificar miembros desde grupos de STAAD"""
        
        for group_name, member_ids in model.groups.items():
            for member_id in member_ids:
                if member_id in model.members:
                    model.members[member_id].group = group_name
                    model.members[member_id].member_type = MemberType.from_group_name(group_name)
        
        classified = sum(1 for m in model.members.values() if m.member_type != MemberType.UNKNOWN)
        
        self.logger.info(f"  Clasificados: {classified}/{len(model.members)} miembros")
    
    def _print_statistics(self, model: StructuralModel):
        """Estadisticas completas"""
        
        self.logger.info("\nESTADISTICAS DEL MODELO:")
        self.logger.info(f"  Nodos: {len(model.nodes)}")
        self.logger.info(f"  Miembros Analiticos: {len(model.members)}")
        self.logger.info(f"  Physical Members: {len(model.physical_members)}")
        self.logger.info(f"  Grupos: {len(model.groups)}")
        
        type_counts = {}
        for member in model.members.values():
            tipo = member.member_type
            type_counts[tipo] = type_counts.get(tipo, 0) + 1
        
        self.logger.info("\nMIEMBROS POR TIPO:")
        for tipo, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                self.logger.info(f"  {tipo.value}: {count}")
        
        deflection_members = len([m for m in model.members.values() 
                                if m.member_type.requires_deflection_check()])
        drift_members = len([m for m in model.members.values() 
                            if m.member_type.requires_drift_check()])
        
        self.logger.info("\nVERIFICACIONES REQUERIDAS:")
        self.logger.info(f"  Deflexion: {deflection_members} miembros")
        self.logger.info(f"  Deriva: {drift_members} miembros")
        
        if model.physical_members:
            avg_am_per_pm = np.mean([len(pm.analytical_members) for pm in model.physical_members.values()])
            self.logger.info(f"\nPHYSICAL MEMBERS:")
            self.logger.info(f"  Promedio AMs por PM: {avg_am_per_pm:.1f}")
