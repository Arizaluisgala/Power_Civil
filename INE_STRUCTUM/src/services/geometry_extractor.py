"""
Extractor de geometria del modelo STAAD.Pro
CON SOPORTE COMPLETO DE PHYSICAL MEMBERS Y GRUPOS
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from src.models.data_models import (
    Node, AnalyticalMember, PhysicalMember, 
    StructuralModel, MemberType
)
from src.services.staad_connector import STAADConnector

class GeometryExtractor:
    '''
    Extrae geometria completa del modelo STAAD
    Incluye Physical Members y clasificacion por grupos
    '''
    
    def __init__(self, connector: STAADConnector):
        if not connector.is_connected:
            raise ValueError("Connector must be connected to STAAD.Pro")
        
        self.staad = connector.staad
        self.logger = logging.getLogger(__name__)
        self.conversion_factor = connector.get_conversion_factor_to_mm()
    
    def extract_complete_model(self) -> StructuralModel:
        '''Extraccion completa de geometria CON PHYSICAL MEMBERS'''
        
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
        
        # PASO 3: Extraer PHYSICAL MEMBERS (CRITICO)
        self.logger.info("\n[3/6] Extrayendo Physical Members...")
        model.physical_members = self._extract_physical_members(model)
        self.logger.info(f"Extraidos: {len(model.physical_members)} Physical Members")
        
        # PASO 4: Extraer grupos (fallback si no disponible)
        self.logger.info("\n[4/6] Intentando extraer grupos desde STAAD...")
        groups_from_staad = self._extract_groups_safe()
        
        if len(groups_from_staad) > 1 or list(groups_from_staad.keys())[0] != "_DESCONOCIDO":
            model.groups = groups_from_staad
            self.logger.info(f"Extraidos: {len(model.groups)} grupos desde STAAD")
            self._classify_members_from_groups(model)
        else:
            self.logger.warning("No se pudieron extraer grupos desde STAAD")
            self.logger.info("\n[5/6] Clasificando por GEOMETRIA (fallback)...")
            model.groups = self._classify_by_geometry(model)
            self.logger.info(f"Creados: {len(model.groups)} grupos por geometria")
        
        # PASO 6: Estadisticas
        self.logger.info("\n[6/6] Generando estadisticas...")
        self._print_statistics(model)
        
        self.logger.info("\n" + "="*60)
        self.logger.info("EXTRACCION COMPLETADA")
        self.logger.info("="*60)
        
        return model
    
    def _extract_nodes(self) -> Dict[int, Node]:
        '''Extraer todos los nodos'''
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
        '''Extraer miembros analiticos'''
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
        '''
        Extraer PHYSICAL MEMBERS completos
        ESTA ES LA FUNCION CLAVE PARA TU WORKFLOW
        '''
        physical_members = {}
        
        try:
            # Obtener lista de Physical Members
            pm_count = self.staad.Geometry.GetPhysicalMemberCount()
            
            if pm_count == 0:
                self.logger.warning("  No hay Physical Members definidos en el modelo")
                return physical_members
            
            self.logger.info(f"  Procesando {pm_count} Physical Members...")
            
            # Obtener IDs de todos los PMs
            pm_list_array = []
            self.staad.Geometry.GetPhysicalMemberList(pm_list_array)
            pm_list = list(pm_list_array)
            
            for idx, pm_id in enumerate(pm_list, 1):
                if idx % 10 == 0:
                    self.logger.info(f"    Progreso: {idx}/{len(pm_list)}")
                
                try:
                    # Obtener miembros analiticos del PM
                    am_count = self.staad.Geometry.GetAnalyticalMemberCountForPhysicalMember(pm_id)
                    
                    am_list_array = []
                    self.staad.Geometry.GetAnalyticalMembersForPhysicalMember(pm_id, am_list_array)
                    am_list = list(am_list_array)
                    
                    # Calcular longitud total y nodos extremos
                    total_length = sum(model.members[am_id].length for am_id in am_list if am_id in model.members)
                    
                    # Ordenar nodos (similar a tu VBA)
                    ordered_nodes = self._order_pm_nodes(am_list, model.members)
                    
                    start_node = ordered_nodes[0] if ordered_nodes else 0
                    end_node = ordered_nodes[-1] if ordered_nodes else 0
                    
                    # Crear Physical Member
                    physical_members[pm_id] = PhysicalMember(
                        id=pm_id,
                        analytical_members=am_list,
                        total_length=total_length,
                        start_node=start_node,
                        end_node=end_node,
                        ordered_nodes=ordered_nodes
                    )
                    
                except Exception as e:
                    self.logger.warning(f"    Error procesando PM {pm_id}: {str(e)}")
                    continue
            
            return physical_members
            
        except Exception as e:
            self.logger.error(f"Error extrayendo Physical Members: {str(e)}")
            return physical_members
    
    def _order_pm_nodes(self, am_list: List[int], members: Dict[int, AnalyticalMember]) -> List[int]:
        '''
        Ordenar nodos de Physical Member
        Similar a tu logica VBA de ordenamiento
        '''
        if not am_list:
            return []
        
        # Recolectar todos los nodos
        nodes_set = set()
        connections = {}  # node -> [connected_nodes]
        
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
        
        # Encontrar nodo inicial (con menos conexiones, tipicamente extremo)
        start_node = min(nodes_set, key=lambda n: len(connections.get(n, [])))
        
        # Ordenar desde el inicio
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
    
    def _extract_groups_safe(self) -> Dict[str, List[int]]:
        '''Extraer grupos (con fallback)'''
        groups = {}
        
        try:
            if hasattr(self.staad.Geometry, 'GetGroupList'):
                group_list = self.staad.Geometry.GetGroupList()
                
                for group_name in group_list:
                    try:
                        members = self.staad.Geometry.GetGroupMemberList(group_name)
                        groups[group_name] = list(members)
                        self.logger.info(f"  Grupo '{group_name}': {len(members)} miembros")
                    except:
                        pass
            else:
                groups["_DESCONOCIDO"] = []
            
            return groups
            
        except Exception as e:
            self.logger.warning(f"  No se pudieron extraer grupos: {str(e)}")
            return {"_DESCONOCIDO": []}
    
    def _classify_by_geometry(self, model: StructuralModel) -> Dict[str, List[int]]:
        '''Clasificar por geometria (fallback)'''
        
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
            
            # Clasificar
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
        '''Clasificar miembros desde grupos de STAAD'''
        
        for group_name, member_ids in model.groups.items():
            for member_id in member_ids:
                if member_id in model.members:
                    model.members[member_id].group = group_name
                    model.members[member_id].member_type = MemberType.from_group_name(group_name)
        
        classified = sum(1 for m in model.members.values() if m.member_type != MemberType.UNKNOWN)
        
        self.logger.info(f"  Clasificados: {classified}")
    
    def _print_statistics(self, model: StructuralModel):
        '''Estadisticas completas'''
        
        self.logger.info("\nESTADISTICAS DEL MODELO:")
        self.logger.info(f"  Nodos: {len(model.nodes)}")
        self.logger.info(f"  Miembros Analiticos: {len(model.members)}")
        self.logger.info(f"  Physical Members: {len(model.physical_members)}")
        self.logger.info(f"  Grupos: {len(model.groups)}")
        
        # Miembros por tipo
        type_counts = {}
        for member in model.members.values():
            tipo = member.member_type
            type_counts[tipo] = type_counts.get(tipo, 0) + 1
        
        self.logger.info("\nMIEMBROS POR TIPO:")
        for tipo, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                self.logger.info(f"  {tipo.value}: {count}")
        
        # Verificaciones requeridas
        deflection_members = len([m for m in model.members.values() 
                                if m.member_type.requires_deflection_check()])
        drift_members = len([m for m in model.members.values() 
                            if m.member_type.requires_drift_check()])
        
        self.logger.info("\nVERIFICACIONES REQUERIDAS:")
        self.logger.info(f"  Deflexion: {deflection_members} miembros")
        self.logger.info(f"  Deriva: {drift_members} miembros")
        
        # Estadisticas de PMs
        if model.physical_members:
            avg_am_per_pm = np.mean([len(pm.analytical_members) for pm.analytical_members in model.physical_members.values()])
            self.logger.info(f"\nPHYSICAL MEMBERS:")
            self.logger.info(f"  Promedio AMs por PM: {avg_am_per_pm:.1f}")
