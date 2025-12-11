"""
Extensiones de geometria para Physical Members
VERSION FUNCIONAL - Acceso correcto a SAFEARRAY
"""

from comtypes import automation
import ctypes

def GetPhysicalMemberList(staad_obj):
    """
    Obtiene lista de Physical Members
    SOLUCION: Extraer directamente desde variant.value
    """
    try:
        geometry_com = staad_obj._geometry if hasattr(staad_obj, '_geometry') else staad_obj
        
        no_p_members = geometry_com.GetPhysicalMemberCount()
        
        if no_p_members == 0:
            return []
        
        # Crear SAFEARRAY
        safe_list = automation._midlSAFEARRAY(ctypes.c_long).create([0] * no_p_members)
        
        # Crear VARIANT
        lista_variant = automation.VARIANT()
        lista_variant.vt = automation.VT_ARRAY | automation.VT_I4 | automation.VT_BYREF
        lista_variant._.c_void_p = ctypes.addressof(safe_list)
        
        # Llamar API
        geometry_com.GetPhysicalMemberList(lista_variant)
        
        # EXTRACCION CORRECTA: Acceder al array interno
        if hasattr(lista_variant, 'value') and lista_variant.value is not None:
            # El variant tiene un array interno
            return list(lista_variant.value[0])
        else:
            # Acceso directo al safearray
            return [int(safe_list[0][i]) for i in range(no_p_members)]
        
    except Exception as e:
        print(f"Error en GetPhysicalMemberList: {e}")
        import traceback
        traceback.print_exc()
        return []


def GetAnalyticalMembersForPhysicalMember(staad_obj, p_member: int):
    """
    Obtiene miembros analiticos de un Physical Member
    SOLUCION: Extraer correctamente desde SAFEARRAY
    """
    try:
        geometry_com = staad_obj._geometry if hasattr(staad_obj, '_geometry') else staad_obj
        
        no_am = geometry_com.GetAnalyticalMemberCountForPhysicalMember(p_member)
        
        if no_am == 0:
            return []
        
        # Crear SAFEARRAY
        safe_list = automation._midlSAFEARRAY(ctypes.c_long).create([0] * no_am)
        
        # Crear VARIANT
        var_member_list = automation.VARIANT()
        var_member_list.vt = automation.VT_ARRAY | automation.VT_I4 | automation.VT_BYREF
        var_member_list._.c_void_p = ctypes.addressof(safe_list)
        
        # Llamar API COM
        geometry_com.GetAnalyticalMembersForPhysicalMember(
            p_member,
            no_am,
            var_member_list
        )
        
        # EXTRACCION CORRECTA
        if hasattr(var_member_list, 'value') and var_member_list.value is not None:
            return list(var_member_list.value[0])
        else:
            return [int(safe_list[0][i]) for i in range(no_am)]
        
    except Exception as e:
        print(f"Error en GetAnalyticalMembersForPhysicalMember PM {p_member}: {e}")
        return []


def GetGroupNames(staad_obj, grouptype: int = 0):
    """
    Obtiene nombres de grupos
    grouptype: 0=Member groups, 1=Node groups, 2=Plate groups
    """
    try:
        geometry_com = staad_obj._geometry if hasattr(staad_obj, '_geometry') else staad_obj
        
        group_count = geometry_com.GetGroupCount(grouptype)
        
        if group_count == 0:
            return []
        
        # Crear SAFEARRAY de BSTR
        safe_array = automation._midlSAFEARRAY(automation.BSTR).create([automation.BSTR()] * group_count)
        
        # Crear VARIANT
        group_names_variant = automation.VARIANT()
        group_names_variant.vt = automation.VT_ARRAY | automation.VT_BSTR | automation.VT_BYREF
        group_names_variant._.c_void_p = ctypes.addressof(safe_array)
        
        # Llamar API
        geometry_com.GetGroupNames(grouptype, group_names_variant)
        
        # EXTRACCION CORRECTA
        if hasattr(group_names_variant, 'value') and group_names_variant.value is not None:
            return [str(name) for name in group_names_variant.value[0]]
        else:
            return [str(safe_array[0][i]) for i in range(group_count)]
        
    except Exception as e:
        print(f"Error en GetGroupNames: {e}")
        import traceback
        traceback.print_exc()
        return []


def GetGroupEntities(staad_obj, group_name: str):
    """
    Obtiene IDs de entidades en un grupo
    """
    try:
        geometry_com = staad_obj._geometry if hasattr(staad_obj, '_geometry') else staad_obj
        
        entity_count = geometry_com.GetGroupEntityCount(group_name)
        
        if entity_count == 0:
            return []
        
        # Crear SAFEARRAY
        safe_list = automation._midlSAFEARRAY(ctypes.c_long).create([0] * entity_count)
        
        # Crear VARIANT
        lista_variant = automation.VARIANT()
        lista_variant.vt = automation.VT_ARRAY | automation.VT_I4 | automation.VT_BYREF
        lista_variant._.c_void_p = ctypes.addressof(safe_list)
        
        # Llamar API
        geometry_com.GetGroupEntities(group_name, lista_variant)
        
        # EXTRACCION CORRECTA
        if hasattr(lista_variant, 'value') and lista_variant.value is not None:
            return list(lista_variant.value[0])
        else:
            return [int(safe_list[0][i]) for i in range(entity_count)]
        
    except Exception as e:
        print(f"Error en GetGroupEntities para {group_name}: {e}")
        import traceback
        traceback.print_exc()
        return []
