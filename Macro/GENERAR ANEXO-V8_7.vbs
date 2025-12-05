'#Reference {420B2830-E718-11CF-893D-00A0C9054228}#1.0#0#C:\Windows\System32\scrrun.dll#Microsoft Scripting Runtime
'#Reference {00020813-0000-0000-C000-000000000046}#1.9#0#C:\Program Files\Microsoft Office\Root\Office16\EXCEL.EXE#Microsoft Excel 16.0 Object Library
'#Reference {00020813-0000-0000-C000-000000000046}#1.8#0#C:\Program Files\Microsoft Office\Office15\EXCEL.EXE#Microsoft Excel 15.0 Object Library
' VBA Code for STAAD.Pro Macro Editor
' Título: Verificación de Deflexiones y Derivas
' Autor: [Luis Ariza/Inelectra] 
' Versión: 8.7
' Fecha: 26-09-2025
' Descripción:
' Esta macro integra la extracción de geometría, el análisis de deflexiones para vigas/arriostramientos
' y el análisis de derivas para columnas de un modelo de STAAD.Pro.
' Lee los parámetros de verificación de un archivo Excel llamado "Límites de deflexión.xlsx",
' extrae los resultados de deflexión y desplazamiento de STAAD, los compara con los límites
' permisibles y exporta un informe detallado a varias hojas del mismo archivo Excel.

Option Explicit

' --- Variables Globales ---
' Se declaran a nivel de módulo para ser accesibles desde todas las subrutinas,
' facilitando el manejo de errores y el acceso a objetos comunes como Excel y OpenSTAAD.

' --- Variables para la gestión de archivos ---
Dim g_sourceFilePath As String          ' Ruta completa del archivo Excel de plantilla (si es necesario copiarlo).
Dim g_outputFilePath As String          ' Ruta completa del archivo Excel de resultados ("Límites de deflexión.xlsx") en la carpeta del modelo.

' --- Variables para la interoperabilidad con otras aplicaciones ---
Dim g_objExcel As Object                ' Objeto principal de la aplicación Excel. Para manipular Excel.
Dim g_objWorkbook As Object             ' Objeto del libro de trabajo de Excel ("Límites de deflexión.xlsx").
Dim g_objOpenSTAAD As Object            ' Objeto principal de OpenSTAAD. Es la puerta de enlace para interactuar con STAAD.Pro.

' --- Variables globales para el manejo de Casos de Carga ---
' Almacenan de forma centralizada todos los casos de carga a analizar, leídos desde Excel.
Dim g_finalLoadCasesArray() As Long     ' Array que contendrá la lista final y consolidada de TODOS los IDs de casos de carga a procesar.
Dim g_finalLoadCaseTypesArray() As String ' Array paralelo a g_finalLoadCasesArray. Almacena el tipo de carga ("1", "2", "3", "4", "Viento", "Sismo").
Dim g_overallLoadCaseIndex As Long      ' Contador/Índice para gestionar el llenado de los dos arrays de casos de carga globales.

' --- Diccionarios Globales para Precarga de Datos (Optimización de Rendimiento) ---
' Estos diccionarios cargan una vez los datos geométricos de Excel en la memoria,
' evitando lecturas repetitivas y lentas del archivo dentro de bucles.

' Clave: ID de Miembro (Long), Valor: Array(ID_NodoA, ID_NodoB, Longitud, ID_MiembroFisico, NombreGrupo)
Dim g_memberNodesDict As Object
' Clave: ID_Nodo (Long), Valor: Array(Coord_X, Coord_Y, Coord_Z)
Dim g_nodeCoordsDict As Object
' Clave: ID_PM (Long), Valor: Array(NodosOrdenados) - CACHÉ PARA OPTIMIZACIÓN
Dim g_pmOrderedNodesCache As Object
' Clave: ID_PM (Long), Valor: Array(IDs_MiembrosAnaliticos) - CACHÉ PARA OPTIMIZACIÓN
Dim g_pmAnalyticalMembersDict As Object
' Clave: "MemberID_LCID" (String), Valor: RowIndex (Long) - ÍNDICE PARA BÚSQUEDA RÁPIDA
Dim g_resultsIndexDict As Object

' Clave: "NodeID_LCID" (String), Valor: Array(dx, dy, dz, rx, ry, rz)
Dim g_nodalDisplacementsDict As Object

' --- Array Global para Almacenar Resultados Crudos de la API ---
' Se eleva a nivel de módulo para ser accesible por las subrutinas de reporte.
Dim resultsArray() As Variant
Dim resultCount As Long

' --- Variables Globales para Unidades y Conversión ---
' Se elevan a nivel de módulo para ser accesibles por todas las subrutinas.
Dim conversionFactorToMM As Double
Dim conversionFactorToM As Double

' --- Constantes ---
' Valores fijos utilizados en la macro para mejorar la legibilidad y facilitar el mantenimiento.
Const STAAD_LENGTH_UNIT As Long = 1             ' Constante de OpenSTAAD que representa la unidad de longitud del modelo (para la función GetUnit).
Const MIN_COLUMN_SEGMENT_HEIGHT_M As Double = 0.67 ' Altura mínima (en metros) que debe tener un tramo de columna para ser considerado en el cálculo de deriva. Evita tramos muy pequeños o irrelevantes.

' --- Declaración de función para pausas (Sleep) ---
' ESTA LÍNEA DEBE ESTAR EN LA PARTE SUPERIOR DEL MÓDULO, FUERA DE CUALQUIER SUBRUTINA
Private Declare Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)

' --- Parámetros de Diseño Globales (Reemplazo de la estructura Type para compatibilidad) ---
' Hoja "Acero"
Dim g_VigasTechos_Tipo1 As Double, g_VigasTechos_Tipo2 As Double, g_VigasTechos_Tipo3 As Double
' *** INICIO DE LA MODIFICACIÓN ***
' Renombrado para mayor claridad y separación de grupos
Dim g_VigasCorreas_Tipo1 As Double, g_VigasCorreas_Tipo2 As Double, g_VigasCorreas_Tipo3 As Double
Dim g_VigasPrin_Tipo1 As Double, g_VigasPrin_Tipo2 As Double, g_VigasPrin_Tipo3 As Double
' Nuevas variables para los grupos separados
Dim g_VigasSec_Tipo1 As Double, g_VigasSec_Tipo2 As Double, g_VigasSec_Tipo3 As Double
Dim g_ArriostHoriz_Tipo1 As Double, g_ArriostHoriz_Tipo2 As Double, g_ArriostHoriz_Tipo3 As Double
' *** FIN DE LA MODIFICACIÓN ***
Dim g_VigasVoladizo_Tipo1 As Double, g_VigasVoladizo_Tipo2 As Double, g_VigasVoladizo_Tipo3 As Double
' Hoja "Otros"
Dim g_VigaCarrilTR_Tipo4 As Double, g_VigaCarrilUR_Tipo4 As Double
Dim g_Monorriel_Tipo4 As Double, g_PuenteGrua_Tipo4 As Double
' Hoja "Rangos"
Dim g_FactorVientoServicio As Double, g_FactorVientoUltimas As Double
Dim g_FactorSismoServicio As Double, g_FactorSismoUltimas As Double
Dim g_FactorSismoModServicioX As Double
Dim g_FactorSismoModServicioZ As Double
Dim g_FactorSismoModUltimasX As Double
Dim g_FactorSismoModUltimasZ As Double


'===============================================================================================================================
' SUBRUTINA PRINCIPAL
' Punto de entrada de la macro. Orquesta todo el flujo de trabajo:
' 1. Conexión a STAAD y Excel.
' 2. Validación y preparación de archivos.
' 3. Llamada a la extracción de geometría.
' 4. Ejecución del análisis de deflexiones y derivas.
' 5. Limpieza de recursos.
'===============================================================================================================================
''===============================================================================================================================
' SUBRUTINA PRINCIPAL (VERSIÓN 3.1 - REVISADA Y OPTIMIZADA)
' Esta es la versión completamente reescrita de la subrutina principal.
' Implementa la arquitectura de 4 fases para un rendimiento máximo y correcciones de ingeniería.
'===============================================================================================================================
Sub Main()
    ' --- Inicio del Proceso y Declaraciones Locales Consolidadas ---
    Debug.Print "--- Inicio de Sub Main (Versión 4.1 - Refactorizada) ---"
    
    ' Llama a la subrutina para generar vistas gráficas primero.
    Call Vistas
    If Err.Number <> 0 Then
        Debug.Print "ERROR: La subrutina 'Vistas' falló. Abortando el resto de la ejecución."
        GoTo CleanUpAndExit
    End If

    ' --- BLOQUE ÚNICO DE DECLARACIÓN DE VARIABLES PARA SUB MAIN ---
    
    ' -- Variables de gestión de archivos y entorno --
    Dim stdFile As String
    Dim staadDir As String
    Dim outputFileName As String
    Dim fileIsValid As Boolean
    Dim errorMessages As String
    
    ' -- Variables de Objeto para Hojas de Excel --
    Dim objSheetDeflexionesComp As Object, objSheetVerificacion As Object, objSheetVerificacionH As Object
    Dim objSheetPM As Object, objSheetNodos As Object, objSheetViento As Object, objSheetSismo As Object
    
    ' -- Variables para Unidades y Conversión --
    Dim currentLengthUnit As Variant
    
    ' -- Variables para FASE A: Recolección de Datos --

    Dim memberCount As Long
    Dim memberID As Long, loadCaseID As Long
    Dim memberNodeData As Variant, nodeA_ID_current As Long, nodeB_ID_current As Long
    Dim physicalMemberID_current As Long, memberGroup_current As String
    Dim actualLengthForVerification As Double, analyticalMemberLength As Double
    Dim startNodeDisp() As Double, endNodeDisp() As Double
    ReDim startNodeDisp(0 To 5)
    ReDim endNodeDisp(0 To 5)
    Dim maxLocalDY As Double, maxLocalDX As Double
    
    ' -- Variables para FASE B: Procesamiento en Memoria --
    Dim nodalDispKey As String
    Dim nodeA_ID As Long, nodeB_ID As Long
    Dim dispArray(0 To 5) As Double
    Dim pmCalculatedDeflectionsDict As Object
    Dim pmKey As String, pmKeyH As String
    Dim maxAbsoluteCombinedDeflectionY As Double, maxAbsoluteCombinedDeflectionHorizontal As Double
    Dim coefL_X_Deflexion As Double, deflectionPermissible_Deflexion As Double
    Dim cumpleNorma_Deflexion As String, relacionDeflexion_Deflexion As Double
    Dim calculatedDeflection As Double, calculatedDeflectionH As Double
    
    ' -- Variables genéricas para bucles e iteraciones --
    Dim i As Long, j As Long
    Dim dictKey As Variant
    
    ' Establece el manejador de errores principal para toda la subrutina.
    On Error GoTo MainErrorHandler

' *** SISTEMA DE MEDICIÓN DE TIEMPOS (V8.2) ***
Dim timeStart As Double, timeEnd As Double, timeTotalExecution As Double
Dim timePhase1 As Double, timePhase2 As Double, timePhase3 As Double, timePhase4 As Double
Dim timePhaseA As Double, timePhaseB As Double, timePhaseC As Double, timePhaseD As Double, timePhase6 As Double
Dim timeStamp As Double

timeStart = Timer
Debug.Print "=========================================="
Debug.Print "INICIO DE EJECUCIÓN: " & Format(Now, "hh:nn:ss")
Debug.Print "=========================================="


    ' --- 1. Conexiones y Preparación de Archivos ---
    Debug.Print "Iniciando Fase 1: Conexiones y Preparación de Archivos..."
    
    On Error Resume Next
    Set g_objOpenSTAAD = GetObject(, "StaadPro.OpenSTAAD")
    On Error GoTo MainErrorHandler
    If g_objOpenSTAAD Is Nothing Then
        MsgBox "No se pudo obtener el objeto OpenSTAAD. Por favor, asegúrate de que STAAD.Pro está ejecutándose.", vbCritical
        Exit Sub
    End If
    
    g_objOpenSTAAD.GetSTAADFile stdFile, "TRUE"
    If stdFile = "" Then
        MsgBox "No hay ningún archivo de STAAD abierto actualmente.", vbExclamation
        Set g_objOpenSTAAD = Nothing
        Exit Sub
    End If
    
    staadDir = Left(stdFile, InStrRev(stdFile, "\"))
    outputFileName = "Límites de deflexión.xlsx"
    g_outputFilePath = staadDir & outputFileName

' --- VERIFICACIÓN CRÍTICA: Comprobar si el modelo está analizado ---
Debug.Print "Verificando si el modelo está analizado..."

On Error Resume Next
Dim resultsAvailable As Long
resultsAvailable = g_objOpenSTAAD.Output.AreResultsAvailable
On Error GoTo MainErrorHandler

If resultsAvailable = 0 Then
    MsgBox "ADVERTENCIA CRÍTICA:" & vbCrLf & vbCrLf & _
           "El modelo de STAAD.Pro NO ha sido analizado." & vbCrLf & vbCrLf & _
           "Por favor:" & vbCrLf & _
           "1. Ejecute el análisis en STAAD.Pro (botón 'Run Analysis')" & vbCrLf & _
           "2. Espere a que complete exitosamente" & vbCrLf & _
           "3. Vuelva a ejecutar esta macro" & vbCrLf & vbCrLf & _
           "Sin resultados de análisis, todas las deflexiones serán 0.", _
           vbCritical + vbOKOnly, "Modelo No Analizado"
    
    ' Cerrar conexiones y salir
    Set g_objOpenSTAAD = Nothing
    Exit Sub
End If

Debug.Print "✓ Modelo analizado correctamente. Continuando..."


    ' *** CIERRE FORZADO DE INSTANCIAS PREVIAS (V8.2) ***
    Debug.Print ""
    Debug.Print "=========================================="
    Debug.Print "VERIFICACIÓN DE ARCHIVOS ABIERTOS"
    Debug.Print "=========================================="
    
    Dim wasFileOpen As Boolean
    wasFileOpen = ForceCloseExcelFile(outputFileName)
    
    If wasFileOpen Then
        Debug.Print "✓ Se cerró una instancia previa del archivo."
        Debug.Print "  La macro puede continuar de forma segura."
    Else
        Debug.Print "✓ No se encontraron instancias previas del archivo."
    End If
    Debug.Print "=========================================="
    Debug.Print ""

    
    If Dir(g_outputFilePath) <> "" Then
        fileIsValid = ValidateExcelFile(g_outputFilePath)
        If Not fileIsValid Then
            MsgBox "Se encontró un archivo '" & outputFileName & "' pero no es válido. Se intentará eliminar.", vbExclamation
            On Error Resume Next
            Kill g_outputFilePath
            On Error GoTo 0 ' Restaurar manejador de errores por defecto
            If Dir(g_outputFilePath) <> "" Then
                MsgBox "Error: No se pudo eliminar el archivo existente. Asegúrate de que no esté abierto.", vbCritical
                GoTo CleanUpAndExit
            End If
            GoTo RequestNewFile
        End If
    Else
RequestNewFile:
        g_sourceFilePath = InputBox("El archivo de plantilla no se encontró. Por favor, ingrese la ruta completa:", "Ingresar Ruta de Plantilla")
        If g_sourceFilePath = "" Then
            MsgBox "Operación cancelada por el usuario.", vbExclamation
            GoTo CleanUpAndExit
        End If
        If Left(g_sourceFilePath, 1) = """" Then g_sourceFilePath = Mid(g_sourceFilePath, 2, Len(g_sourceFilePath) - 2)
        If Dir(g_sourceFilePath) = "" Then
            MsgBox "Error: El archivo de origen especificado no existe.", vbCritical
            GoTo CleanUpAndExit
        End If
        
        If ValidateExcelFile(g_sourceFilePath) Then
            On Error GoTo FileCopyError
            FileCopy g_sourceFilePath, g_outputFilePath
            On Error GoTo MainErrorHandler
        Else
            MsgBox "La plantilla de Excel proporcionada no cumple con el formato requerido.", vbExclamation
            GoTo CleanUpAndExit
        End If
    End If
    
    On Error GoTo ExcelError
    Set g_objExcel = CreateObject("Excel.Application")
    g_objExcel.ScreenUpdating = False
    g_objExcel.DisplayAlerts = False
    Set g_objWorkbook = g_objExcel.Workbooks.Open(g_outputFilePath)
    If g_objWorkbook Is Nothing Then
        MsgBox "No se pudo abrir el libro de trabajo de Excel.", vbCritical
        GoTo CleanUpAndExit
    End If
timePhase1 = Timer - timeStart
Debug.Print "Fase 1 completada. TIEMPO: " & Format(timePhase1, "0.00") & " segundos"
timeStamp = Timer ' Actualizar timestamp para siguiente fase


    ' --- 2. Extracción de Geometría y Preparación de Hojas ---
    Debug.Print "Iniciando Fase 2: Extracción de Geometría y Preparación de Hojas..."
    Call ProcessGeometryDataToExcel(g_objOpenSTAAD, g_objExcel, g_objWorkbook)

    ' Carga los datos recién extraídos a los diccionarios en memoria.
    Call PreloadGeometryFromExcel(g_objWorkbook)
    
    Set objSheetDeflexionesComp = g_objWorkbook.Sheets("Deflexiones (Componentes)")
    Set objSheetVerificacion = g_objWorkbook.Sheets("Verificación Deflexiones")
    Set objSheetVerificacionH = g_objWorkbook.Sheets("Verificación Deflexiones H")
    Set objSheetPM = g_objWorkbook.Sheets("PM")
    Set objSheetNodos = g_objWorkbook.Sheets("Nodos")
    If Not SheetExists(g_objWorkbook, "Viento") Then g_objWorkbook.Sheets.Add(After:=g_objWorkbook.Sheets(g_objWorkbook.Sheets.Count)).Name = "Viento"
    Set objSheetViento = g_objWorkbook.Sheets("Viento")
    If Not SheetExists(g_objWorkbook, "Sismo") Then g_objWorkbook.Sheets.Add(After:=g_objWorkbook.Sheets(g_objWorkbook.Sheets.Count)).Name = "Sismo"
    Set objSheetSismo = g_objWorkbook.Sheets("Sismo")
    
    Call ClearSheetContents(g_objWorkbook, "Deflexiones (Componentes)")
    Call ClearSheetContents(g_objWorkbook, "Verificación Deflexiones")
    Call ClearSheetContents(g_objWorkbook, "Verificación Deflexiones H")
    Call ClearSheetContents(g_objWorkbook, "Viento")
    Call ClearSheetContents(g_objWorkbook, "Sismo")
    
    ' Escritura de encabezados
    Call WriteDeflexionesCompHeaders(objSheetDeflexionesComp)
    Call WriteVerificacionHeaders(objSheetVerificacion, "Max DY (mm)")
    Call WriteVerificacionHeaders(objSheetVerificacionH, "Max DH (mm)")
timePhase2 = Timer - timeStamp
Debug.Print "Fase 2 completada. TIEMPO: " & Format(timePhase2, "0.00") & " segundos"
timeStamp = Timer


    ' --- 3. Precarga de Parámetros y Unidades ---
    Debug.Print "Iniciando Fase 3: Precarga de Parámetros y Unidades..."

    On Error Resume Next
    currentLengthUnit = g_objOpenSTAAD.GetUnit(STAAD_LENGTH_UNIT)
    If Err.Number <> 0 Then
        Debug.Print "Advertencia: Error al obtener unidad de longitud. Asumiendo Metros."
        Err.Clear
        currentLengthUnit = 0 ' STAAD_LENGTH_METER
    End If
    On Error GoTo MainErrorHandler
    
    Select Case currentLengthUnit
        Case 0 ' STAAD_LENGTH_METER
            conversionFactorToMM = 1000#
            conversionFactorToM = 1#
        Case 1 ' STAAD_LENGTH_CENTIMETER
            conversionFactorToMM = 10#
            conversionFactorToM = 0.01
        Case 2 ' STAAD_LENGTH_MILLIMETER
            conversionFactorToMM = 1#
            conversionFactorToM = 0.001
        Case 3 ' STAAD_LENGTH_INCH
            conversionFactorToMM = 25.4
            conversionFactorToM = 0.0254
        Case 4 ' STAAD_LENGTH_FOOT
            conversionFactorToMM = 304.8
            conversionFactorToM = 0.3048
        Case Else
            conversionFactorToMM = 1000#
            conversionFactorToM = 1#
    End Select
    
    ' Precarga de todos los coeficientes de diseño desde Excel a variables globales.
    Call PreloadDesignParameters(g_objWorkbook)
timePhase3 = Timer - timeStamp
Debug.Print "Fase 3 completada. TIEMPO: " & Format(timePhase3, "0.00") & " segundos"
timeStamp = Timer

    
 ' --- 4. Recopilación y Clasificación de Casos de Carga (Lógica Mejorada) ---
Debug.Print "Iniciando Fase 4: Recopilación y Clasificación de Casos de Carga..."

' Diccionarios para almacenar las listas maestras y las listas de derivas
Dim servicioCasesDict As Object, ultimasCasesDict As Object
Dim vientoCasesDict As Object, sismoCasesDict As Object
Set servicioCasesDict = CreateObject("Scripting.Dictionary")
Set ultimasCasesDict = CreateObject("Scripting.Dictionary")
Set vientoCasesDict = CreateObject("Scripting.Dictionary")
Set sismoCasesDict = CreateObject("Scripting.Dictionary")

errorMessages = ""

' --- PASO 4.1: Leer las listas de referencia y las listas de derivas ---
' Leer Casos de Servicio (Columna D de hoja Rangos)
Call CollectLoadCasesToList(g_objWorkbook, "Rangos", 4, 15, 16, 20, servicioCasesDict, errorMessages)
' Leer Casos de Carga Últimas (Columna E de hoja Rangos)
Call CollectLoadCasesToList(g_objWorkbook, "Rangos", 5, 15, 16, 20, ultimasCasesDict, errorMessages)
' Leer Casos para Deriva por Viento (Columna F de hoja Rangos)
Call CollectLoadCasesToList(g_objWorkbook, "Rangos", 6, 15, 16, 20, vientoCasesDict, errorMessages)
' Leer Casos para Deriva por Sismo (Columna G de hoja Rangos)
Call CollectLoadCasesToList(g_objWorkbook, "Rangos", 7, 15, 16, 20, sismoCasesDict, errorMessages)

' Leer el resto de casos de carga para deflexiones (Acero y Otros)
' Estos se añadirán directamente a los arrays globales como antes.
g_overallLoadCaseIndex = -1
ReDim g_finalLoadCasesArray(0 To -1)
ReDim g_finalLoadCaseTypesArray(0 To -1)
Call CollectLoadCasesFromSheet(g_objWorkbook, "Acero", Array(4, 5, 6), Array("1", "2", "3"), 12, 15, 16, 19, errorMessages)
Call CollectLoadCasesFromSheet(g_objWorkbook, "Otros", Array(3), Array("4"), 10, 13, 14, 17, errorMessages)

' --- PASO 4.2: Filtrar y clasificar los casos de deriva ---

' Clasificar Viento
For Each dictKey In vientoCasesDict.Keys
    If servicioCasesDict.Exists(dictKey) Then
        ' Es un caso de Viento y de Servicio
        g_overallLoadCaseIndex = g_overallLoadCaseIndex + 1
        ReDim Preserve g_finalLoadCasesArray(0 To g_overallLoadCaseIndex)
        ReDim Preserve g_finalLoadCaseTypesArray(0 To g_overallLoadCaseIndex)
        g_finalLoadCasesArray(g_overallLoadCaseIndex) = dictKey
        g_finalLoadCaseTypesArray(g_overallLoadCaseIndex) = "Viento-Servicio"
    End If
    If ultimasCasesDict.Exists(dictKey) Then
        ' Es un caso de Viento y de Cargas Últimas
        g_overallLoadCaseIndex = g_overallLoadCaseIndex + 1
        ReDim Preserve g_finalLoadCasesArray(0 To g_overallLoadCaseIndex)
        ReDim Preserve g_finalLoadCaseTypesArray(0 To g_overallLoadCaseIndex)
        g_finalLoadCasesArray(g_overallLoadCaseIndex) = dictKey
        g_finalLoadCaseTypesArray(g_overallLoadCaseIndex) = "Viento-Ultimas"
    End If
Next dictKey

' Clasificar Sismo
For Each dictKey In sismoCasesDict.Keys
    If servicioCasesDict.Exists(dictKey) Then
        ' Es un caso de Sismo y de Servicio
        g_overallLoadCaseIndex = g_overallLoadCaseIndex + 1
        ReDim Preserve g_finalLoadCasesArray(0 To g_overallLoadCaseIndex)
        ReDim Preserve g_finalLoadCaseTypesArray(0 To g_overallLoadCaseIndex)
        g_finalLoadCasesArray(g_overallLoadCaseIndex) = dictKey
        g_finalLoadCaseTypesArray(g_overallLoadCaseIndex) = "Sismo-Servicio"
    End If
    If ultimasCasesDict.Exists(dictKey) Then
        ' Es un caso de Sismo y de Cargas Últimas
        g_overallLoadCaseIndex = g_overallLoadCaseIndex + 1
        ReDim Preserve g_finalLoadCasesArray(0 To g_overallLoadCaseIndex)
        ReDim Preserve g_finalLoadCaseTypesArray(0 To g_overallLoadCaseIndex)
        g_finalLoadCasesArray(g_overallLoadCaseIndex) = dictKey
        g_finalLoadCaseTypesArray(g_overallLoadCaseIndex) = "Sismo-Ultimas"
    End If
Next dictKey

' Liberar diccionarios intermedios
Set servicioCasesDict = Nothing
Set ultimasCasesDict = Nothing
Set vientoCasesDict = Nothing
Set sismoCasesDict = Nothing

' --- PASO 4.3: Verificación final ---
If errorMessages <> "" Then
    MsgBox "Se encontraron errores en la configuración de casos de carga:" & vbCrLf & errorMessages, vbCritical
    GoTo CleanUpAndExit
End If
If g_overallLoadCaseIndex < 0 Then
    MsgBox "No se encontraron casos de carga válidos para analizar en las hojas de configuración.", vbExclamation
    GoTo CleanUpAndExit
End If
timePhase4 = Timer - timeStamp
Debug.Print "Fase 4 completada. Se analizarán " & (g_overallLoadCaseIndex + 1) & " combinaciones."
Debug.Print "TIEMPO FASE 4: " & Format(timePhase4, "0.00") & " segundos"
timeStamp = Timer


    memberCount = g_memberNodesDict.Count
    ' Array para guardar datos: 1-6: Info, 7-12: Despl A, 13-18: Despl B, 19: Panza Y, 20: Panza X (DZ local)
    ReDim resultsArray(1 To memberCount * (g_overallLoadCaseIndex + 1), 1 To 35)

    resultCount = 0

    ' Declaración de variables para el bucle de recolección
    
    ' --- OPTIMIZACIÓN 1: Caché de Desplazamientos Nodales ---
    Dim g_nodeCache As Object
    Set g_nodeCache = CreateObject("Scripting.Dictionary")
    
    ' --- OPTIMIZACIÓN 2: Caché de Nodos Ordenados PM (Inicialización) ---
    Set g_pmOrderedNodesCache = CreateObject("Scripting.Dictionary")
    Set g_pmAnalyticalMembersDict = CreateObject("Scripting.Dictionary")
    Set g_resultsIndexDict = CreateObject("Scripting.Dictionary")
    
    Dim nodeKeyA As String, nodeKeyB As String
    
    ' --- OPTIMIZACIÓN 2: Variable para filtrar cálculo de deflexiones ---
    Dim isBeamOrBrace As Boolean

    For Each dictKey In g_memberNodesDict.Keys
        memberID = dictKey
        memberNodeData = g_memberNodesDict.Item(memberID)
        nodeA_ID_current = memberNodeData(0)
        nodeB_ID_current = memberNodeData(1)
        analyticalMemberLength = memberNodeData(2)
        physicalMemberID_current = memberNodeData(3)
        memberGroup_current = CStr(memberNodeData(4))
        
        If physicalMemberID_current <> 0 Then
            actualLengthForVerification = GetPMLengthFromSheet(objSheetPM, physicalMemberID_current)
            If actualLengthForVerification = 0 Then actualLengthForVerification = analyticalMemberLength
        Else
            actualLengthForVerification = analyticalMemberLength
        End If
        
        For i = 0 To g_overallLoadCaseIndex
            loadCaseID = g_finalLoadCasesArray(i)
            resultCount = resultCount + 1
            
            ' Guardar datos básicos
            resultsArray(resultCount, 1) = memberID
            resultsArray(resultCount, 2) = physicalMemberID_current
            resultsArray(resultCount, 3) = memberGroup_current
            resultsArray(resultCount, 4) = actualLengthForVerification
            resultsArray(resultCount, 5) = loadCaseID
            
            ' --- OPTIMIZACIÓN: Indexar para búsqueda rápida ---
            If Not g_resultsIndexDict Is Nothing Then
                Dim indexKey As String
                indexKey = memberID & "_" & loadCaseID
                If Not g_resultsIndexDict.Exists(indexKey) Then
                    g_resultsIndexDict.Add indexKey, resultCount
                End If
            End If
            resultsArray(resultCount, 6) = g_finalLoadCaseTypesArray(i)
            
            ' Recolectar desplazamientos en los extremos (CON CACHÉ)
            nodeKeyA = nodeA_ID_current & "_" & loadCaseID
            If g_nodeCache.Exists(nodeKeyA) Then
                startNodeDisp = g_nodeCache.Item(nodeKeyA)
            Else
                Call GetMemberEndDisplacementsWrapper(g_objOpenSTAAD.Output, nodeA_ID_current, loadCaseID, startNodeDisp)
                g_nodeCache.Add nodeKeyA, startNodeDisp
            End If
            
            nodeKeyB = nodeB_ID_current & "_" & loadCaseID
            If g_nodeCache.Exists(nodeKeyB) Then
                endNodeDisp = g_nodeCache.Item(nodeKeyB)
            Else
                Call GetMemberEndDisplacementsWrapper(g_objOpenSTAAD.Output, nodeB_ID_current, loadCaseID, endNodeDisp)
                g_nodeCache.Add nodeKeyB, endNodeDisp
            End If
            
            For j = 0 To 5
                resultsArray(resultCount, 7 + j) = startNodeDisp(j)
                resultsArray(resultCount, 13 + j) = endNodeDisp(j)
            Next j

            ' Calcular y guardar la panza real usando la API (MÉTODO V7 RESTAURADO)
            ' OPTIMIZACIÓN: Solo calcular para vigas y elementos que lo requieran
            isBeamOrBrace = ((memberGroup_current = "_VIGAS_PRIN" Or memberGroup_current = "_VIGAS_SEC" Or memberGroup_current = "_VIGAS_CORREAS" Or memberGroup_current = "_VIGAS_TECHOS" Or memberGroup_current = "_VIGAS_VOLADIZO") Or (memberGroup_current = "_ARRIOST_PRIN" Or memberGroup_current = "_ARRIOST_HORIZ" Or memberGroup_current = "_ARRIOST_VERT") Or _
                             (memberGroup_current = "_VIGA_CARRIL_TR" Or memberGroup_current = "_VIGA_CARRIL_UR") Or memberGroup_current = "_MONORRIEL" Or _
                             memberGroup_current = "_PUENTE_GRUA" Or memberGroup_current = "_VIGAS_VOLADIZO")

            If analyticalMemberLength > 0.001 And isBeamOrBrace Then
                Call GetMaxLocalDeflectionFromPoints(memberID, loadCaseID, analyticalMemberLength, conversionFactorToMM, g_objOpenSTAAD.Output, 1, maxLocalDY)
                Call GetMaxLocalDeflectionFromPoints(memberID, loadCaseID, analyticalMemberLength, conversionFactorToMM, g_objOpenSTAAD.Output, 2, maxLocalDX)

            Else
                maxLocalDY = 0
                maxLocalDX = 0
            End If

            resultsArray(resultCount, 19) = maxLocalDY
            resultsArray(resultCount, 20) = maxLocalDX
        Next i
    Next dictKey
    
    ' Limpiar caché temporal
    ' OPTIMIZACIÓN 3: Reutilizar el caché en lugar de destruirlo y reconstruirlo
    ' Set g_nodeCache = Nothing  <-- SE ELIMINA ESTA LÍNEA
    
' FASE A completada: resultCount registros
timePhaseA = Timer - timeStamp
Debug.Print "=========================================="
Debug.Print "*** FASE A COMPLETADA ***"
Debug.Print "Registros procesados: " & resultCount
Debug.Print "TIEMPO: " & Format(timePhaseA, "0.00") & " segundos (" & Format(timePhaseA/60, "0.0") & " min)"
Debug.Print "=========================================="
timeStamp = Timer

' PASO B.1: Precarga de desplazamientos nodales
' OPTIMIZACIÓN 3: Asignación directa del diccionario ya construido
Set g_nodalDisplacementsDict = g_nodeCache
Set g_nodeCache = Nothing ' Liberar la referencia original, pero el objeto sigue vivo en g_nodalDisplacementsDict

Debug.Print g_nodalDisplacementsDict.Count & " registros de desplazamiento nodal únicos cacheados (Reutilizados)."

' (El bucle redundante anterior ha sido eliminado)

Debug.Print g_nodalDisplacementsDict.Count & " registros de desplazamiento nodal únicos cacheados."


' *** PASO B.2: Inicializar caché de deflexiones para PMs (V7 LAZY-LOADING RESTAURADO) ***
Debug.Print "Inicializando caché inteligente de deflexiones para Physical Members..."
Set pmCalculatedDeflectionsDict = CreateObject("Scripting.Dictionary")
Debug.Print "Caché inicializado. Cálculos se realizarán bajo demanda durante PASO B.3."


' *** PASO B.3: Bucle principal - Lazy-loading V7 restaurado ***
Debug.Print "Procesando verificaciones (cálculo bajo demanda)..."

For i = 1 To resultCount
    memberID = resultsArray(i, 1)
    physicalMemberID_current = resultsArray(i, 2)
    memberGroup_current = resultsArray(i, 3)
    actualLengthForVerification = resultsArray(i, 4)
    loadCaseID = resultsArray(i, 5)
    
    Dim currentEnvTypeRead As String
    currentEnvTypeRead = resultsArray(i, 6)
    
    If (memberGroup_current = "_VIGAS_PRIN" Or memberGroup_current = "_VIGAS_SEC" Or memberGroup_current = "_VIGAS_CORREAS" Or memberGroup_current = "_VIGAS_TECHOS" Or memberGroup_current = "_VIGAS_VOLADIZO") Or (memberGroup_current = "_ARRIOST_PRIN" Or memberGroup_current = "_ARRIOST_HORIZ" Or memberGroup_current = "_ARRIOST_VERT") Or _
       (memberGroup_current = "_VIGA_CARRIL_TR" Or memberGroup_current = "_VIGA_CARRIL_UR") Or memberGroup_current = "_MONORRIEL" Or _
       memberGroup_current = "_PUENTE_GRUA" Then
        
        '--- LÓGICA PARA VIGAS ---
        If memberGroup_current = "_VIGAS_VOLADIZO" Then
            '✅ CORRECCIÓN: Calcular deflexión RELATIVA entre extremos
            ' Obtener desplazamientos de ambos nodos
            Dim dispAY As Double, dispBY As Double
            Dim dispAX As Double, dispBX As Double
            
            ' Nodo A: columnas 7-12 (índice +1 para DY, +0 para DX)
            dispAY = resultsArray(i, 7 + 1)   ' DY del nodo A
            dispAX = resultsArray(i, 7 + 0)   ' DX del nodo A
            
            ' Nodo B: columnas 13-18 (índice +1 para DY, +0 para DX)
            dispBY = resultsArray(i, 13 + 1)  ' DY del nodo B
            dispBX = resultsArray(i, 13 + 0)  ' DX del nodo B
            
            ' Calcular deflexión relativa (diferencia absoluta entre extremos)
            maxAbsoluteCombinedDeflectionY = Abs((dispBY - dispAY) * conversionFactorToMM)
            maxAbsoluteCombinedDeflectionHorizontal = Abs((dispBX - dispAX) * conversionFactorToMM)
        Else
            If physicalMemberID_current <> 0 Then
                ' *** LAZY-LOADING V7: Calcular solo si NO está en caché ***
                pmKey = physicalMemberID_current & "_" & loadCaseID
                
                ' VERTICAL: Calcular si no está en caché
                If Not pmCalculatedDeflectionsDict.Exists(pmKey) Then
                    calculatedDeflection = CalculatePhysicalMemberMaxLocalDeflection(physicalMemberID_current, loadCaseID, objSheetPM, conversionFactorToMM)
                    pmCalculatedDeflectionsDict.Add pmKey, calculatedDeflection
                End If
                maxAbsoluteCombinedDeflectionY = pmCalculatedDeflectionsDict.Item(pmKey)
                
                ' HORIZONTAL: Calcular solo si no está en caché
                pmKeyH = physicalMemberID_current & "_" & loadCaseID & "_H"
                If Not pmCalculatedDeflectionsDict.Exists(pmKeyH) Then
                    calculatedDeflectionH = GetMaxPanzaHorizontalForPM(physicalMemberID_current, loadCaseID)
                    pmCalculatedDeflectionsDict.Add pmKeyH, calculatedDeflectionH
                End If
                maxAbsoluteCombinedDeflectionHorizontal = pmCalculatedDeflectionsDict.Item(pmKeyH)

            Else
                ' Miembros analíticos usan la panza calculada en FASE A
                maxAbsoluteCombinedDeflectionY = resultsArray(i, 19)
                maxAbsoluteCombinedDeflectionHorizontal = resultsArray(i, 20)
            End If
        End If
        
        coefL_X_Deflexion = GetDeflectionCoefficient(memberGroup_current, currentEnvTypeRead)
        
        ' ✅ GUARDAR EN COLUMNAS CORRECTAS (21 y 27)
        resultsArray(i, 21) = maxAbsoluteCombinedDeflectionY
        resultsArray(i, 27) = maxAbsoluteCombinedDeflectionHorizontal
        
        If coefL_X_Deflexion > 0 Then
            deflectionPermissible_Deflexion = (actualLengthForVerification * 1000) / coefL_X_Deflexion
            
            ' Verificación Vertical (columnas 23-26)
            Call VerifyDeflection(maxAbsoluteCombinedDeflectionY, deflectionPermissible_Deflexion, cumpleNorma_Deflexion, relacionDeflexion_Deflexion)
            resultsArray(i, 23) = coefL_X_Deflexion
            resultsArray(i, 24) = deflectionPermissible_Deflexion
            resultsArray(i, 25) = cumpleNorma_Deflexion
            resultsArray(i, 26) = relacionDeflexion_Deflexion
            
            ' Verificación Horizontal (columnas 28-31)
            Call VerifyDeflection(maxAbsoluteCombinedDeflectionHorizontal, deflectionPermissible_Deflexion, cumpleNorma_Deflexion, relacionDeflexion_Deflexion)
            resultsArray(i, 28) = coefL_X_Deflexion
            resultsArray(i, 29) = deflectionPermissible_Deflexion
            resultsArray(i, 30) = cumpleNorma_Deflexion
            resultsArray(i, 31) = relacionDeflexion_Deflexion
        Else
            resultsArray(i, 25) = "N/A"
            resultsArray(i, 30) = "N/A"
        End If
    End If
Next i

Debug.Print "FASE B completada. Cálculos en memoria finalizados."

timePhaseB = Timer - timeStamp
Debug.Print "=========================================="
Debug.Print "*** FASE B COMPLETADA ***"
Debug.Print "TIEMPO: " & Format(timePhaseB, "0.00") & " segundos (" & Format(timePhaseB/60, "0.0") & " min)"
Debug.Print "=========================================="
timeStamp = Timer


    ' --- FASE C: ESCRITURA EN BLOQUE A EXCEL ---
    Debug.Print "Iniciando FASE C: Escritura en bloque de " & resultCount & " filas a Excel..."
    If resultCount > 0 Then
        objSheetDeflexionesComp.Range("A2").Resize(resultCount, 35).Value = resultsArray

    End If
    Debug.Print "FASE C completada. Escritura en bloque finalizada."
timePhaseC = Timer - timeStamp
Debug.Print "=========================================="
Debug.Print "*** FASE C COMPLETADA ***"
Debug.Print "Filas escritas a Excel: " & resultCount
Debug.Print "TIEMPO: " & Format(timePhaseC, "0.00") & " segundos"
Debug.Print "=========================================="
timeStamp = Timer


' --- FASE D: CONSOLIDACIÓN DE RESULTADOS (DESDE EL ARRAY EN MEMORIA) ---
    Debug.Print "Iniciando FASE D: Consolidación de resultados desde la memoria..."
    Call ConsolidateBeamResultsFromArray(resultsArray, objSheetVerificacion, "Vertical")
    Call ConsolidateBeamResultsFromArray(resultsArray, objSheetVerificacionH, "Horizontal")

    ' --- Llamadas a la nueva lógica de reporte de derivas de entrepiso ---
    Call GenerateStoryDriftReport(objSheetViento, "Viento")
    Call GenerateStoryDriftReport(objSheetSismo, "Sismo")

    Debug.Print "FASE D completada. Consolidación finalizada."
timePhaseD = Timer - timeStamp
Debug.Print "=========================================="
Debug.Print "*** FASE D COMPLETADA ***"
Debug.Print "TIEMPO: " & Format(timePhaseD, "0.00") & " segundos"
Debug.Print "=========================================="
timeStamp = Timer


    ' --- 6. Llamadas a Procesos Adicionales ---
    Debug.Print "Iniciando Fase 6: Ejecución de procesos adicionales..."
    Call MS_Process
    If Err.Number <> 0 Then
        Debug.Print "ERROR: MS_Process terminó con un error."
        GoTo CleanUpAndExit
    End If
    
    Call Ratios_Process
    If Err.Number <> 0 Then
        Debug.Print "ERROR: Ratios_Process terminó con un error."
        GoTo CleanUpAndExit
    End If
    
    Call Computos_Process
    If Err.Number <> 0 Then
        Debug.Print "ERROR: Computos_Process terminó con un error."
        GoTo CleanUpAndExit
    End If
    Debug.Print "Fase 6 completada."
timePhase6 = Timer - timeStamp
Debug.Print "=========================================="
Debug.Print "*** FASE 6 COMPLETADA (MS/Ratios/Computos) ***"
Debug.Print "TIEMPO: " & Format(timePhase6, "0.00") & " segundos"
Debug.Print "=========================================="


CleanUpAndExit:
    ' *** REPORTE FINAL DE TIEMPOS (V8.2) ***
    timeEnd = Timer
    timeTotalExecution = timeEnd - timeStart
    
    Debug.Print ""
    Debug.Print "=========================================="
    Debug.Print "========== REPORTE FINAL DE TIEMPOS =========="
    Debug.Print "=========================================="
    Debug.Print "Fase 1 (Conexiones):        " & Format(timePhase1, "0.00") & " s"
    Debug.Print "Fase 2 (Geometría):         " & Format(timePhase2, "0.00") & " s"
    Debug.Print "Fase 3 (Parámetros):        " & Format(timePhase3, "0.00") & " s"
    Debug.Print "Fase 4 (Casos de Carga):    " & Format(timePhase4, "0.00") & " s"
    Debug.Print "FASE A (Recolección API):   " & Format(timePhaseA, "0.00") & " s (" & Format(timePhaseA/60, "0.0") & " min)"
    Debug.Print "FASE B (Cálculos Memoria):  " & Format(timePhaseB, "0.00") & " s (" & Format(timePhaseB/60, "0.0") & " min)"
    Debug.Print "FASE C (Escritura Excel):   " & Format(timePhaseC, "0.00") & " s"
    Debug.Print "FASE D (Consolidación):     " & Format(timePhaseD, "0.00") & " s"
    Debug.Print "Fase 6 (MS/Ratios/Computos):" & Format(timePhase6, "0.00") & " s"
    Debug.Print "=========================================="
    Debug.Print "*** TIEMPO TOTAL DE EJECUCIÓN: " & Format(timeTotalExecution, "0.00") & " segundos ***"
    Debug.Print "*** EQUIVALENTE A: " & Format(timeTotalExecution/60, "0.0") & " MINUTOS ***"
    Debug.Print "=========================================="
    Debug.Print "FIN DE EJECUCIÓN: " & Format(Now, "hh:nn:ss")
    Debug.Print "=========================================="
    
    Debug.Print "--- Iniciando CleanUpAndExit de Main ---"
    
    ' *** GUARDAR Y CERRAR CON MANEJO DE ERRORES MEJORADO ***
    On Error Resume Next
    If Not g_objWorkbook Is Nothing Then
        Debug.Print "Guardando archivo Excel..."
        
        ' Intentar guardar múltiples veces si falla
        Dim saveAttempt As Integer
        Dim saveFailed As Boolean
        saveFailed = True
        
        For saveAttempt = 1 To 3
            g_objWorkbook.Save
            If Err.Number = 0 Then
                Debug.Print "✓ Archivo guardado exitosamente."
                saveFailed = False
                Exit For
            Else
                Debug.Print "⚠ Intento " & saveAttempt & " de guardado falló. Error: " & Err.Description
                Err.Clear
                Sleep 500 ' Esperar medio segundo antes de reintentar
            End If
        Next saveAttempt
        
        If saveFailed Then
            Debug.Print "✗ ERROR CRÍTICO: No se pudo guardar el archivo después de 3 intentos."
            MsgBox "ADVERTENCIA: No se pudo guardar el archivo 'Límites de deflexión.xlsx'." & vbCrLf & _
                   "Es posible que esté bloqueado por otro proceso." & vbCrLf & vbCrLf & _
                   "Por favor, cierre todas las instancias de Excel y ejecute la macro nuevamente.", _
                   vbExclamation, "Error al Guardar"
        End If
        
        g_objWorkbook.Close SaveChanges:=False ' Ya intentamos guardar arriba
        Set g_objWorkbook = Nothing
    End If
    If Not g_objExcel Is Nothing Then
        g_objExcel.DisplayAlerts = True
        g_objExcel.ScreenUpdating = True
        g_objExcel.Quit
        Set g_objExcel = Nothing
    End If
    If Not g_objOpenSTAAD Is Nothing Then Set g_objOpenSTAAD = Nothing
    Set g_memberNodesDict = Nothing
    Set g_memberNodesDict = Nothing
    Set g_nodeCoordsDict = Nothing
    Set g_pmOrderedNodesCache = Nothing
    Set g_pmAnalyticalMembersDict = Nothing
    Set g_resultsIndexDict = Nothing
    On Error GoTo 0
    Debug.Print "--- Fin de Sub Main ---"
MsgBox "La data del modelo se ha exportado con éxito." & vbCrLf & vbCrLf & _
       "Tiempo total de ejecución: " & Format(timeTotalExecution/60, "0.0") & " minutos", _
       vbInformation, "Proceso Terminado"

    Exit Sub

' --- Manejadores de Errores Específicos ---
FileCopyError:
    MsgBox "Error al copiar el archivo:" & vbCrLf & Err.Description, vbCritical
    Resume CleanUpAndExit
ExcelError:
    MsgBox "Error general al procesar Excel:" & vbCrLf & Err.Description, vbCritical
    Resume CleanUpAndExit
MainErrorHandler:
    MsgBox "Se produjo un error inesperado en la macro principal: " & Err.Description & vbCrLf & "(Número de error: " & Err.Number & ")", vbCritical
    Resume CleanUpAndExit
End Sub
'===============================================================================================================================
' SUBRUTINA DE PROCESAMIENTO DE GEOMETRÍA
' Propósito: Extraer toda la información geométrica del modelo de STAAD (nodos, miembros, grupos, etc.)
' y escribirla de forma estructurada en las hojas "Nodos", "Elementos" y "PM" del archivo Excel.
' Esta subrutina actúa como el extractor de datos primario.
' Parámetros:
'   objOpenStaad: El objeto de conexión a OpenSTAAD.
'   objExcel: El objeto de la aplicación Excel.
'   objWorkbook: El objeto del libro de trabajo de Excel.
'===============================================================================================================================
'===============================================================================================================================
' SUBRUTINA DE PROCESAMIENTO DE GEOMETRÍA
' Propósito: Extraer toda la información geométrica del modelo de STAAD (nodos, miembros, grupos, etc.)
' y escribirla de forma estructurada en las hojas "Nodos", "Elementos" y "PM" del archivo Excel.
'===============================================================================================================================
Sub ProcessGeometryDataToExcel(ByVal objOpenStaad As Object, ByVal objExcel As Object, ByVal objWorkbook As Object)

    Debug.Print "--- Inicio de ProcessGeometryDataToExcel ---"

    ' --- Variables Locales para ProcessGeometryDataToExcel ---
    Dim geom As Object
    Dim i As Long, k As Long, m As Long, g As Long, e As Long
    Dim excelRowNodes As Long, excelRowElements As Long, excelRowPM As Long
    Dim nodeIDs() As Long, nodeCount As Long, nodeCoords(2) As Double, currentNodeID As Long
    Dim memberIDs() As Long, memberCount As Long, currentMemberID As Long
    Dim NodeA As Long, NodeB As Long, pMemberLength As Double
    Dim phyMemberIDs() As Long, phyMemberCount As Long, currentPhyMemberID As Long
    Dim analyticalMembersOfPhyMember() As Long, numAnalyticalMembersOfPhyMember As Long
    Dim analyticalMembersString As String, foundPhyMemberID As Long
    Dim memberGroupNames() As String, numMemberGroups As Long, currentGroupName As String
    Dim entitiesInGroup() As Long, numEntitiesInGroup As Long
    Dim foundGroupNames(0 To 4) As String, groupCountForMember As Long
    Dim wsNodes As Object, wsElements As Object, wsPM As Object
    Dim totalLength As Double, nodeCounts As Object, dictKey As Variant, startNode As String, endNode As String

    On Error GoTo GeometryErrorHandler
    Debug.Print "  ProcessGeometryDataToExcel: Manejo de errores configurado."

    ' --- Obtener objeto de Geometría de OpenSTAAD ---
    Set geom = objOpenStaad.Geometry
    If geom Is Nothing Then
        MsgBox "Error Crítico: No se pudo obtener el objeto Geometry de OpenSTAAD.", vbCritical
        GoTo GeometryCleanUp
    End If
    Debug.Print "  ProcessGeometryDataToExcel: Objeto Geometry obtenido con éxito."

    ' --- 1. Procesar Hoja "Nodos" ---
    Set wsNodes = objWorkbook.Sheets("Nodos")
    wsNodes.Cells.ClearContents
    wsNodes.Cells(1, 1).Value = "ID del Nodo"
    wsNodes.Cells(1, 2).Value = "Coordenada X"
    wsNodes.Cells(1, 3).Value = "Coordenada Y"
    wsNodes.Cells(1, 4).Value = "Coordenada Z"
    excelRowNodes = 2
    nodeCount = geom.GetNodeCount()
    If nodeCount > 0 Then
        ReDim nodeIDs(nodeCount - 1)
        geom.GetNodeList nodeIDs
        For i = 0 To nodeCount - 1
            currentNodeID = nodeIDs(i)
            geom.GetNodeCoordinates currentNodeID, nodeCoords(0), nodeCoords(1), nodeCoords(2)
            wsNodes.Cells(excelRowNodes, 1).Value = currentNodeID
            wsNodes.Cells(excelRowNodes, 2).Value = Round(nodeCoords(0), 3)
            wsNodes.Cells(excelRowNodes, 3).Value = Round(nodeCoords(1), 3)
            wsNodes.Cells(excelRowNodes, 4).Value = Round(nodeCoords(2), 3)
            excelRowNodes = excelRowNodes + 1
        Next i
    End If
    Debug.Print "  ProcessGeometryDataToExcel: Datos de " & (excelRowNodes - 2) & " nodos escritos."

    ' --- OPTIMIZACIÓN: Obtener listas de Miembros Físicos y Grupos una sola vez ---
    phyMemberCount = geom.GetPhysicalMemberCount()
    If phyMemberCount > 0 Then
        ReDim phyMemberIDs(phyMemberCount - 1)
        geom.GetPhysicalMemberList phyMemberIDs
    End If
    numMemberGroups = geom.GetGroupCount(2) ' El '2' especifica grupos de tipo "Miembro".
    If numMemberGroups > 0 Then
        ReDim memberGroupNames(numMemberGroups - 1)
        geom.GetGroupNames 2, memberGroupNames
    End If
    Debug.Print "  ProcessGeometryDataToExcel: Listas de " & phyMemberCount & " PMs y " & numMemberGroups & " Grupos precargadas."

    ' --- 2. Procesar Hoja "Elementos" (Miembros Analíticos) ---
    Set wsElements = objWorkbook.Sheets("Elementos")
    wsElements.Cells.ClearContents
    wsElements.Cells(1, 1).Value = "ID del Elemento"
    wsElements.Cells(1, 2).Value = "Nodo A"
    wsElements.Cells(1, 3).Value = "Nodo B"
    wsElements.Cells(1, 4).Value = "Longitud (m)"
    wsElements.Cells(1, 5).Value = "Id del physical member"
    For g = 1 To 5
        wsElements.Cells(1, 5 + g).Value = "Grupo " & g
    Next g
    
    excelRowElements = 2
    memberCount = geom.GetMemberCount()
    If memberCount > 0 Then
        ReDim memberIDs(memberCount - 1)
        geom.GetBeamList memberIDs
        
        For i = 0 To memberCount - 1
            currentMemberID = memberIDs(i)
            geom.GetMemberIncidence currentMemberID, NodeA, NodeB
            pMemberLength = geom.GetBeamLength(currentMemberID)
            
            foundPhyMemberID = 0
            If phyMemberCount > 0 Then
                For k = 0 To phyMemberCount - 1
                    numAnalyticalMembersOfPhyMember = geom.GetAnalyticalMemberCountForPhysicalMember(phyMemberIDs(k))
                    If numAnalyticalMembersOfPhyMember > 0 Then
                        ReDim analyticalMembersOfPhyMember(numAnalyticalMembersOfPhyMember - 1)
                        geom.GetAnalyticalMembersForPhysicalMember phyMemberIDs(k), numAnalyticalMembersOfPhyMember, analyticalMembersOfPhyMember
                        For m = 0 To UBound(analyticalMembersOfPhyMember)
                            If analyticalMembersOfPhyMember(m) = currentMemberID Then
                                foundPhyMemberID = phyMemberIDs(k)
                                Exit For
                            End If
                        Next m
                    End If
                    If foundPhyMemberID <> 0 Then Exit For
                Next k
            End If

            For g = 0 To 4
                foundGroupNames(g) = ""
            Next g
            groupCountForMember = 0
            If numMemberGroups > 0 Then
                For g = 0 To numMemberGroups - 1
                    currentGroupName = memberGroupNames(g)
                    numEntitiesInGroup = geom.GetGroupEntityCount(currentGroupName)
                    If numEntitiesInGroup > 0 Then
                        ReDim entitiesInGroup(numEntitiesInGroup - 1)
                        geom.GetGroupEntities currentGroupName, entitiesInGroup
                        For e = 0 To UBound(entitiesInGroup)
                            If entitiesInGroup(e) = currentMemberID Then
                                If groupCountForMember < 5 Then
                                    foundGroupNames(groupCountForMember) = currentGroupName
                                    groupCountForMember = groupCountForMember + 1
                                End If
                                Exit For
                            End If
                        Next e
                    End If
                Next g
            End If

            wsElements.Cells(excelRowElements, 1).Value = currentMemberID
            wsElements.Cells(excelRowElements, 2).Value = NodeA
            wsElements.Cells(excelRowElements, 3).Value = NodeB
            wsElements.Cells(excelRowElements, 4).Value = Round(pMemberLength, 3)
            wsElements.Cells(excelRowElements, 5).Value = foundPhyMemberID
            For g = 0 To 4
                wsElements.Cells(excelRowElements, 6 + g).Value = foundGroupNames(g)
            Next g
            excelRowElements = excelRowElements + 1
        Next i
    End If
    Debug.Print "  ProcessGeometryDataToExcel: Datos de " & (excelRowElements - 2) & " elementos escritos."
    
    ' --- 3. Procesar Hoja "PM" (Miembros Físicos) ---
    Set wsPM = objWorkbook.Sheets("PM")
    wsPM.Cells.ClearContents
    wsPM.Cells(1, 1).Value = "ID Physical Member"
    wsPM.Cells(1, 2).Value = "Elementos Analíticos (IDs)"
    wsPM.Cells(1, 3).Value = "Longitud Total (m)"
    wsPM.Cells(1, 4).Value = "Nodo Inicial"
    wsPM.Cells(1, 5).Value = "Nodo Final"
    excelRowPM = 2
    
    If phyMemberCount > 0 Then
        ' Precargar datos de la hoja "Elementos" recién escrita para no leerla en cada iteración.
        ' Esto evita leer desde el disco repetidamente y mejora mucho el rendimiento.
        Dim elementosData As Variant
        Dim lastRow As Long
        lastRow = wsElements.Cells(wsElements.Rows.Count, "A").End(xlUp).Row
        If lastRow > 1 Then
            elementosData = wsElements.Range("A2:E" & lastRow).Value
        End If

        For k = 0 To phyMemberCount - 1
            currentPhyMemberID = phyMemberIDs(k)
            wsPM.Cells(excelRowPM, 1).Value = currentPhyMemberID
            
            numAnalyticalMembersOfPhyMember = geom.GetAnalyticalMemberCountForPhysicalMember(currentPhyMemberID)
            If numAnalyticalMembersOfPhyMember > 0 Then
                ReDim analyticalMembersOfPhyMember(numAnalyticalMembersOfPhyMember - 1)
                geom.GetAnalyticalMembersForPhysicalMember currentPhyMemberID, numAnalyticalMembersOfPhyMember, analyticalMembersOfPhyMember
                
                ' --- OPTIMIZACIÓN: Guardar en caché global ---
                If Not g_pmAnalyticalMembersDict Is Nothing Then
                    g_pmAnalyticalMembersDict.Add currentPhyMemberID, analyticalMembersOfPhyMember
                End If
                
                analyticalMembersString = ""
                For m = 0 To UBound(analyticalMembersOfPhyMember)
                    analyticalMembersString = analyticalMembersString & analyticalMembersOfPhyMember(m)
                    If m < UBound(analyticalMembersOfPhyMember) Then
                        analyticalMembersString = analyticalMembersString & ", "
                    End If
                Next m
                wsPM.Cells(excelRowPM, 2).Value = analyticalMembersString
                
                totalLength = 0
                Set nodeCounts = CreateObject("Scripting.Dictionary")
                
                ' En lugar de leer la hoja "Elementos", iterar sobre el array en memoria "elementosData"
                If IsArray(elementosData) Then
                    For m = 1 To UBound(elementosData, 1)
                        ' Si el Miembro Físico en la fila actual del array coincide con el que estamos procesando
                        If CLng(elementosData(m, 5)) = currentPhyMemberID Then
                            ' Sumar su longitud
                            totalLength = totalLength + CDbl(elementosData(m, 4))
                            ' Contar la aparición de sus nodos
                            nodeCounts(CStr(elementosData(m, 2))) = nodeCounts(CStr(elementosData(m, 2))) + 1 ' Nodo A
                            nodeCounts(CStr(elementosData(m, 3))) = nodeCounts(CStr(elementosData(m, 3))) + 1 ' Nodo B
                        End If
                    Next m
                End If
                
                wsPM.Cells(excelRowPM, 3).Value = Round(totalLength, 3)
                
                startNode = ""
                endNode = ""
                For Each dictKey In nodeCounts.Keys
                    If nodeCounts(dictKey) = 1 Then
                        If startNode = "" Then
                            startNode = dictKey
                        Else
                            endNode = dictKey
                        End If
                    End If
                Next dictKey
                
                If IsNumeric(startNode) Then wsPM.Cells(excelRowPM, 4).Value = CLng(startNode)
                If IsNumeric(endNode) Then wsPM.Cells(excelRowPM, 5).Value = CLng(endNode)
            End If
            excelRowPM = excelRowPM + 1
        Next k
    End If
    Debug.Print "  ProcessGeometryDataToExcel: Datos de " & (excelRowPM - 2) & " physical members escritos."

    Debug.Print "--- Fin de ProcessGeometryDataToExcel ---"

GeometryCleanUp:
    ' Liberar todos los objetos locales de la memoria para evitar fugas.
    Set geom = Nothing
    Set wsNodes = Nothing
    Set wsElements = Nothing
    Set wsPM = Nothing
    Exit Sub
GeometryErrorHandler:
    MsgBox "Se produjo un error en el procesamiento de la geometría: " & Err.Description, vbCritical, "Error en Geometría"
    Debug.Print "Error en GeometryErrorHandler: " & Err.Description & " (" & Err.Number & ")"
    Resume GeometryCleanUp
End Sub
'===============================================================================================================================

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: PreloadGeometryFromExcel (VERSIÓN MEJORADA CON SOPORTE MULTI-GRUPO)
' Propósito: Lee los datos de geometría desde las hojas de Excel (previamente llenadas)
'            y los carga en los diccionarios globales en memoria para un acceso ultra-rápido.
'            Esta versión mejorada lee múltiples columnas de grupo y prioriza el grupo más
'            relevante para los cálculos de la macro.
'-------------------------------------------------------------------------------------------------------------------------------
Sub PreloadGeometryFromExcel(ByVal wb As Object)
    Debug.Print "--- Iniciando precarga de geometría desde Excel a la memoria (con lógica multi-grupo) ---"
    
    ' Inicializar los diccionarios globales
    Set g_memberNodesDict = CreateObject("Scripting.Dictionary")
    Set g_nodeCoordsDict = CreateObject("Scripting.Dictionary")
    
    Dim wsNodes As Object
    Dim wsElements As Object
    Set wsNodes = wb.Sheets("Nodos")
    Set wsElements = wb.Sheets("Elementos")
    
    Dim lastRow As Long
    Dim dataArray As Variant
    Dim i As Long
    
    ' --- Cargar Coordenadas de Nodos ---
    lastRow = wsNodes.Cells(wsNodes.Rows.Count, "A").End(xlUp).Row
    If lastRow >= 2 Then
        dataArray = wsNodes.Range("A2:D" & lastRow).Value
        If IsArray(dataArray) Then
            For i = 1 To UBound(dataArray, 1)
                Dim nodeID As Long
                Dim xCoord As Double
                Dim yCoord As Double
                Dim zCoord As Double
                
                nodeID = CLng(dataArray(i, 1))
                xCoord = CDbl(dataArray(i, 2))
                yCoord = CDbl(dataArray(i, 3))
                zCoord = CDbl(dataArray(i, 4))
                
                If Not g_nodeCoordsDict.Exists(nodeID) Then
                    g_nodeCoordsDict.Add nodeID, Array(xCoord, yCoord, zCoord)
                End If
            Next i
        End If
    End If
    Debug.Print "Datos de " & g_nodeCoordsDict.Count & " nodos precargados en diccionario."
    
    ' --- Cargar Datos de Miembros (LÓGICA MEJORADA) ---
    lastRow = wsElements.Cells(wsElements.Rows.Count, "A").End(xlUp).Row
    If lastRow >= 2 Then
        ' AMPLIACIÓN DEL RANGO: Leemos hasta la columna K para capturar hasta 6 grupos (F, G, H, I, J, K)
        dataArray = wsElements.Range("A2:K" & lastRow).Value
        If IsArray(dataArray) Then
            For i = 1 To UBound(dataArray, 1)
                Dim memberID As Long
                Dim nodeA As Long
                Dim nodeB As Long
                Dim length As Double
                Dim pmID As Long
                
                memberID = CLng(dataArray(i, 1))
                nodeA = CLng(dataArray(i, 2))
                nodeB = CLng(dataArray(i, 3))
                length = CDbl(dataArray(i, 4))
                pmID = CLng(dataArray(i, 5))
                
                ' --- INICIO DE LA NUEVA LÓGICA DE BÚSQUEDA DE GRUPO ---
                Dim currentGroupName As String
                Dim finalGroupName As String
                Dim j As Long ' Iterador para las columnas de grupo
                Dim foundRelevantGroup As Boolean
                
                ' Por defecto, asignamos el primer grupo (columna F, índice 6 en el array)
                finalGroupName = CStr(dataArray(i, 6))
                foundRelevantGroup = False
                
                ' Bucle para iterar a través de las columnas de grupo (de F a K, índices 6 a 11)
                For j = 6 To UBound(dataArray, 2)
                    currentGroupName = CStr(dataArray(i, j))
                    
                    ' Si la celda del grupo está vacía, no hay más grupos en esta fila, salimos del bucle.
                    If currentGroupName = "" Then
                        Exit For
                    End If
                    
                    ' Verificamos si el grupo actual es uno de los que se usan para los cálculos.
                    ' Esta lista debe coincidir con los grupos que se verifican en la subrutina Main.
                    If currentGroupName Like "_VIGAS*" Or _
                       currentGroupName Like "_ARRIOST*" Or _
                       currentGroupName Like "*CARRIL*" Or _
                       currentGroupName = "_MONORRIEL" Or _
                       currentGroupName = "_PUENTE_GRUA" Or _
                       currentGroupName Like "*_COLUMNAS_*" Then
                       
                        ' Si encontramos un grupo relevante, lo asignamos como el definitivo y salimos del bucle.
                        finalGroupName = currentGroupName
                        foundRelevantGroup = True
                        Exit For
                    End If
                Next j
                ' --- FIN DE LA NUEVA LÓGICA DE BÚSQUEDA DE GRUPO ---
                
                If Not g_memberNodesDict.Exists(memberID) Then
                    ' Añadimos el miembro al diccionario con el grupo más relevante que encontramos.
                    g_memberNodesDict.Add memberID, Array(nodeA, nodeB, length, pmID, finalGroupName)
                End If
            Next i
        End If
    End If
    Debug.Print "Datos de " & g_memberNodesDict.Count & " miembros precargados en diccionario."
    
    Debug.Print "--- Precarga de geometría completada ---"
End Sub

' --- SECCIÓN DE FUNCIONES AUXILIARES (HELPERS) ---
' Estas son subrutinas y funciones de propósito general que son llamadas desde
' diferentes partes del código para realizar tareas específicas y repetitivas.
'===============================================================================================================================

'-------------------------------------------------------------------------------------------------------------------------------
' Función: ValidateExcelFile
' Propósito: Verifica si un archivo Excel en una ruta específica es "válido". La validez
'            significa que se puede abrir y que contiene un conjunto mínimo de hojas de cálculo requeridas.
' Parámetros:
'   filePath (String): La ruta completa del archivo Excel a validar.
' Retorna: Boolean - True si el archivo es válido, False en caso contrario.
'-------------------------------------------------------------------------------------------------------------------------------
Function ValidateExcelFile(ByVal filePath As String) As Boolean
    Debug.Print "Iniciando validación de archivo Excel: " & filePath
    Dim objExcelVal As Object           ' Instancia temporal de Excel para la validación.
    Dim objWorkbookVal As Object        ' Libro de trabajo temporal para la validación.
    Dim requiredSheets() As String      ' Array con los nombres de las hojas obligatorias.
    Dim sheetName As Variant            ' Variable para iterar sobre el array de hojas.
    Dim allRequiredSheetsFound As Boolean ' Bandera para rastrear si se encontraron todas las hojas.

    ValidateExcelFile = False ' Asumir que es inválido hasta que se demuestre lo contrario.

    On Error GoTo ValidationExcelError

    ' Crear una instancia de Excel temporal y oculta.
    Set objExcelVal = CreateObject("Excel.Application")
    If objExcelVal Is Nothing Then
         Debug.Print "Error de validación: No se pudo iniciar o conectar con Excel."
         Exit Function
    End If
    objExcelVal.Visible = False
    objExcelVal.DisplayAlerts = False

    ' Intentar abrir el libro de trabajo.
    Set objWorkbookVal = objExcelVal.Workbooks.Open(filePath)
    If objWorkbookVal Is Nothing Then
         Debug.Print "Error de validación: No se pudo abrir el archivo Excel: " & filePath
         GoTo CleanUpValidation
    End If

    ' Definir aquí las hojas que SON OBLIGATORIAS para que el archivo se considere válido.
    requiredSheets = Split("Concreto,Acero,Otros,Rangos", ",")
    allRequiredSheetsFound = True

    ' Iterar por cada nombre de hoja requerida y verificar si existe.
    For Each sheetName In requiredSheets
        If Not SheetExists(objWorkbookVal, CStr(sheetName)) Then
            Debug.Print "  Hoja requerida no encontrada: " & sheetName
            allRequiredSheetsFound = False ' Si falta una, el archivo es inválido.
            Exit For
        End If
    Next sheetName

    ' Si se encontraron todas las hojas, la validación es exitosa.
    If allRequiredSheetsFound Then
        ValidateExcelFile = True
        Debug.Print "Validación de archivo: Éxito (todas las hojas requeridas encontradas)."
    Else
        ValidateExcelFile = False
        Debug.Print "Validación de archivo: Falló (faltan hojas requeridas)."
    End If

CleanUpValidation: ' Etiqueta para la limpieza.
    On Error Resume Next ' Ignorar errores durante la limpieza.
    If Not objWorkbookVal Is Nothing Then objWorkbookVal.Close SaveChanges:=False
    If Not objExcelVal Is Nothing Then objExcelVal.Quit
    Set objWorkbookVal = Nothing
    Set objExcelVal = Nothing
    On Error GoTo 0
    Exit Function

ValidationExcelError: ' Manejador de errores para la validación.
    MsgBox "Error inesperado durante la validación del archivo Excel: " & Err.Description, vbCritical
    ValidateExcelFile = False
    Resume CleanUpValidation ' Intentar limpiar antes de salir.
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: SheetExists
' Propósito: Comprueba de forma segura si una hoja de cálculo con un nombre dado existe en un libro de trabajo.
' Parámetros:
'   wb (Object): El objeto del libro de trabajo de Excel donde se buscará.
'   sheetName (String): El nombre de la hoja a buscar.
' Retorna: Boolean - True si la hoja existe, False si no.
'-------------------------------------------------------------------------------------------------------------------------------
Function SheetExists(ByVal wb As Object, ByVal sheetName As String) As Boolean
    Dim ws As Object
    On Error Resume Next ' Desactiva el manejador de errores temporalmente.
    Set ws = wb.Sheets(sheetName) ' Intenta asignar la hoja a una variable.
    On Error GoTo 0 ' Reactiva el manejador de errores.
    ' Si la asignación tuvo éxito (ws no es Nothing), la hoja existe.
    SheetExists = Not ws Is Nothing
    Set ws = Nothing
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetCellValue
' Propósito: Obtiene de forma segura el valor de una celda, evitando errores si la hoja no existe.
' Parámetros:
'   wb (Object): El libro de trabajo.
'   sheetName (String): El nombre de la hoja donde está la celda.
'   cellAddress (String): La dirección de la celda (ej. "A1", "F9").
' Retorna: Variant - El valor de la celda, o Empty si la hoja no existe.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetCellValue(ByVal wb As Object, ByVal sheetName As String, ByVal cellAddress As String) As Variant
    On Error Resume Next
    If SheetExists(wb, sheetName) Then
        GetCellValue = wb.Sheets(sheetName).Range(cellAddress).Value
    Else
        GetCellValue = Empty ' Retorna un valor vacío si la hoja no se encuentra.
    End If
    On Error GoTo 0
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: DoesFileExist
' Propósito: Comprueba de forma simple si un archivo existe en una ruta de disco.
' Parámetros:
'   filePath (String): La ruta completa del archivo a verificar.
' Retorna: Boolean - True si el archivo existe, False si no.
'-------------------------------------------------------------------------------------------------------------------------------
Function DoesFileExist(ByVal filePath As String) As Boolean
    DoesFileExist = (Dir(filePath) <> "")
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: IsEnvelopeIDExisting
' Propósito: Verifica si un ID de envolvente de carga ya existe en el modelo de STAAD.Pro.
'-------------------------------------------------------------------------------------------------------------------------------
Function IsEnvelopeIDExisting(ByVal objOpenStaad As Object, ByVal envID As Long) As Boolean
    Dim existingIDs() As Long, nExistingEnvelopes As Long, i As Long
    IsEnvelopeIDExisting = False
    If objOpenStaad Is Nothing Then Exit Function
    On Error Resume Next
    nExistingEnvelopes = objOpenStaad.Load.GetEnvelopeCount()
    If nExistingEnvelopes > 0 Then
        ReDim existingIDs(nExistingEnvelopes - 1)
        objOpenStaad.Load.GetEnvelopeIDs existingIDs
        For i = 0 To nExistingEnvelopes - 1
            If existingIDs(i) = envID Then
                IsEnvelopeIDExisting = True
                Exit For
            End If
        Next i
    End If
    On Error GoTo 0
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: FindNextAvailableEnvelopeID
' Propósito: Busca en el modelo de STAAD.Pro y devuelve el primer número entero disponible para un nuevo ID de envolvente.
'-------------------------------------------------------------------------------------------------------------------------------
Function FindNextAvailableEnvelopeID(ByVal objOpenStaad As Object) As Long
    Dim existingIDs() As Long, nExistingEnvelopes As Long, i As Long, temp As Long, swapped As Boolean
    Dim nextID As Long
    nextID = 1 ' Comienza la búsqueda desde 1.
    If objOpenStaad Is Nothing Then FindNextAvailableEnvelopeID = 1: Exit Function
    On Error Resume Next
    nExistingEnvelopes = objOpenStaad.Load.GetEnvelopeCount()
    If nExistingEnvelopes > 0 Then
        ReDim existingIDs(nExistingEnvelopes - 1)
        objOpenStaad.Load.GetEnvelopeIDs existingIDs
        ' Ordenar la lista de IDs existentes para una búsqueda eficiente (algoritmo de burbuja).
        Do
            swapped = False
            For i = 0 To nExistingEnvelopes - 2
                If existingIDs(i) > existingIDs(i + 1) Then
                    temp = existingIDs(i)
                    existingIDs(i) = existingIDs(i + 1)
                    existingIDs(i + 1) = temp
                    swapped = True
                End If
            Next i
        Loop While swapped
        ' Encontrar el primer "hueco" en la secuencia ordenada.
        For i = 0 To nExistingEnvelopes - 1
            If existingIDs(i) = nextID Then
                nextID = nextID + 1
            Else
                Exit For
            End If
        Next i
    End If
    FindNextAvailableEnvelopeID = nextID
    On Error GoTo 0
End Function
'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: GetNodeDisplacementWrapper
' Propósito: Es un "envoltorio" seguro para la función GetNodeDisplacements de OpenSTAAD.
'            Maneja los errores que puedan ocurrir si STAAD no puede devolver el desplazamiento
'            para un nodo y caso de carga específicos, evitando que la macro se detenga.
' Parámetros:
'   outputObj (Object): El objeto Output de OpenSTAAD.
'   nodeID (Long): El ID del nodo a consultar.
'   loadCaseID (Long): El ID del caso de carga a consultar.
'   (Por Referencia) globalDX, globalDY, globalDZ: Variables que se llenarán con los desplazamientos en mm.
'-------------------------------------------------------------------------------------------------------------------------------

' --- INICIO: NUEVAS ESTRUCTURAS Y FUNCIONES PARA CÁLCULO OPTIMIZADO DE DEFLEXIONES ---

Sub GetMemberEndDisplacementsWrapper(ByVal objOutput As Object, ByVal nodeID As Long, ByVal loadCaseID As Long, ByRef displacementsArray() As Double)
    Dim i As Integer
    Dim returnValue As Boolean
    
    On Error Resume Next
    returnValue = objOutput.GetNodeDisplacements(nodeID, loadCaseID, displacementsArray)
    
    If Err.Number <> 0 Or Not returnValue Then
        ' Asignar desplazamientos cero para nodos problemáticos
        For i = 0 To 5
            displacementsArray(i) = 0
        Next i
        Err.Clear
    End If
    On Error GoTo 0
End Sub


' Subrutina: ClearSheetContents
' Propósito: Limpia completamente una hoja de cálculo, incluyendo contenido, colores de fondo y formato de fuente.
'-------------------------------------------------------------------------------------------------------------------------------
Sub ClearSheetContents(ByVal wb As Object, ByVal sheetName As String)
    Dim ws As Object
    On Error Resume Next
    Set ws = wb.Sheets(sheetName)
    If Not ws Is Nothing Then
        ws.Cells.ClearContents
        ws.Cells.Interior.ColorIndex = xlNone
        ws.Cells.Font.Bold = False
        ws.Columns.AutoFit
        If Err.Number <> 0 Then Debug.Print "ADVERTENCIA: No se pudo limpiar la hoja '" & sheetName & "'. Razón: " & Err.Description
    Else
        Debug.Print "ADVERTENCIA: No se encontró la hoja '" & sheetName & "' al intentar limpiar."
    End If
    Set ws = Nothing
    On Error GoTo 0
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: WriteHeaders
' Propósito: Escribe un array de texto como encabezados en una fila, aplicando formato de negrita.
'-------------------------------------------------------------------------------------------------------------------------------
Sub WriteHeaders(ByVal wb As Object, ByVal sheetName As String, ByVal headers As Variant, ByVal startRow As Long, ByVal startCol As Long)
    On Error GoTo ErrorHandler_WriteHeaders
    Dim ws As Object
    Set ws = wb.Sheets(sheetName)
    Dim j As Long
    For j = 0 To UBound(headers)
        ws.Cells(startRow, startCol + j).Value = headers(j)
        ws.Cells(startRow, startCol + j).Font.Bold = True
    Next j
    Exit Sub
ErrorHandler_WriteHeaders:
    Debug.Print "Error en WriteHeaders para la hoja " & sheetName & ": " & Err.Description
End Sub

Function GetSortedColumnNodes(ByVal physicalMemberID As Long) As Long()
    Dim nodesDict As Object
    Set nodesDict = CreateObject("Scripting.Dictionary")
    Dim analyticalMembers() As Long, numAnalyticalMembers As Long, i As Long, j As Long
    Dim sortedNodeIDs() As Long, tempNode As Long
    
    On Error GoTo ErrorHandler_GetSortedNodes
    
    numAnalyticalMembers = g_objOpenSTAAD.Geometry.GetAnalyticalMemberCountForPhysicalMember(physicalMemberID)
    If numAnalyticalMembers <= 0 Then GoTo ExitWithError
    
    ReDim analyticalMembers(numAnalyticalMembers - 1)
    g_objOpenSTAAD.Geometry.GetAnalyticalMembersForPhysicalMember physicalMemberID, numAnalyticalMembers, analyticalMembers
    
    ' Recopilar todos los nodos únicos y sus coordenadas Y
    For i = LBound(analyticalMembers) To UBound(analyticalMembers)
        If g_memberNodesDict.Exists(analyticalMembers(i)) Then
            Dim memberData As Variant
            memberData = g_memberNodesDict.Item(analyticalMembers(i))
            Dim nodeA As Long
            nodeA = memberData(0)
            Dim nodeB As Long
            nodeB = memberData(1)
            If Not nodesDict.Exists(nodeA) And g_nodeCoordsDict.Exists(nodeA) Then nodesDict.Add nodeA, g_nodeCoordsDict.Item(nodeA)(1)
            If Not nodesDict.Exists(nodeB) And g_nodeCoordsDict.Exists(nodeB) Then nodesDict.Add nodeB, g_nodeCoordsDict.Item(nodeB)(1)
        End If
    Next i
    
    If nodesDict.Count = 0 Then GoTo ExitWithError

    ' 1. Transferir las claves del diccionario a un array
    ReDim sortedNodeIDs(0 To nodesDict.Count - 1)
    i = 0
    Dim dictKey As Variant
    For Each dictKey In nodesDict.Keys
        sortedNodeIDs(i) = CLng(dictKey)
        i = i + 1
    Next dictKey

    ' 2. Ordenar el array usando el algoritmo de burbuja basado en la coordenada Y
    For i = LBound(sortedNodeIDs) To UBound(sortedNodeIDs) - 1
        For j = i + 1 To UBound(sortedNodeIDs)
            If nodesDict(sortedNodeIDs(i)) > nodesDict(sortedNodeIDs(j)) Then
                tempNode = sortedNodeIDs(i)
                sortedNodeIDs(i) = sortedNodeIDs(j)
                sortedNodeIDs(j) = tempNode
            End If
        Next j
    Next i
    
    GetSortedColumnNodes = sortedNodeIDs
    Exit Function

ErrorHandler_GetSortedNodes:
    Debug.Print "Error en GetSortedColumnNodes para PM " & physicalMemberID & ": " & Err.Description
ExitWithError:
    ReDim sortedNodeIDs(0 To -1): GetSortedColumnNodes = sortedNodeIDs
End Function

' Función: GetPMLengthFromSheet
' Propósito: Busca en la hoja "PM" la longitud total de un Miembro Físico específico.
'            Es una forma eficiente y segura de obtener este dato.
' Retorna: Double - La longitud del PM, o 0 si no se encuentra.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetPMLengthFromSheet(ByVal pmSheet As Object, ByVal pmID As Long) As Double
    Dim lastRow As Long
    Dim i As Long
    Dim dataRange As Variant
    
    GetPMLengthFromSheet = 0 ' Valor por defecto

    If pmSheet Is Nothing Then
        Exit Function ' Salir si el objeto de la hoja es inválido
    End If
    
    ' Obtener la última fila de la hoja "PM"
    lastRow = pmSheet.Cells(pmSheet.Rows.Count, "A").End(xlUp).Row
    
    ' Si no hay datos, salir
    If lastRow < 2 Then
        Exit Function
    End If
    
    ' Leer todos los datos de la hoja a un array para máxima velocidad
    dataRange = pmSheet.Range("A2:C" & lastRow).Value
    
    ' Buscar el PM ID en la primera columna del array
    For i = 1 To UBound(dataRange, 1)
        If CLng(dataRange(i, 1)) = pmID Then
            ' Si se encuentra, devolver la longitud de la tercera columna
            If IsNumeric(dataRange(i, 3)) Then
                GetPMLengthFromSheet = CDbl(dataRange(i, 3))
            End If
            Exit Function ' Salir de la función una vez encontrado
        End If
    Next i
End Function


' --- MS.TXT (Renombrada a MS_Process) ---
Sub MS_Process()
    ' Propósito: Extraer propiedades de materiales isótropos, soportes y reacciones
    ' del modelo STAAD.Pro abierto y escribirlos en las hojas "MC", "Soporte", "Reacciones"
    ' de "Límites de deflexión.xlsx".

    On Error GoTo MS_ProcessErrorHandler

    Debug.Print "MS_Process: Iniciando..."

    ' Se asume que g_objOpenSTAAD, g_objExcel, g_objWorkbook ya están inicializados en Main
    ' y que g_stdFile y g_excelFilePath también están definidos.

    ' 1. Llamar a la subrutina 'material'
    Debug.Print "MS_Process: Llamando a la subrutina 'material'..."
    Call material(g_objOpenSTAAD, g_objExcel, g_objWorkbook)
    Debug.Print "MS_Process: 'material' completada."

    ' 2. Llamar a la subrutina 'soporte'
    Debug.Print "MS_Process: Llamando a la subrutina 'soporte'..."
    Call soporte(g_objOpenSTAAD, g_objExcel, g_objWorkbook)
    Debug.Print "MS_Process: 'soporte' completada."

    ' 3. Llamar a la subrutina 'reacciones'
    Debug.Print "MS_Process: Llamando a la subrutina 'reacciones'..."
    Call reacciones(g_objOpenSTAAD, g_objExcel, g_objWorkbook)
    Debug.Print "MS_Process: 'reacciones' completada."

    Debug.Print "MS_Process: Completado."

MS_ProcessCleanup:
    Exit Sub

MS_ProcessErrorHandler:
    MsgBox "Ocurrió un error en la subrutina 'MS_Process':" & vbCrLf & _
           "Número de Error: " & Err.Number & vbCrLf & _
           "Descripción: " & Err.Description, vbCritical, "Error en M-S Process"
    Debug.Print "MS_Process: Error en MS_ProcessErrorHandler: " & Err.Description & " (" & Err.Number & ")"
    Resume MS_ProcessCleanup
End Sub


' --- RATIOS.TXT (Renombrada a Ratios_Process) ---
Sub Ratios_Process()
    ' Propósito: Extraer resultados de diseño de acero para todos los miembros
    '            del modelo STAAD.Pro y volcarlos en la hoja "Ratios" de un
    '            archivo de Excel existente o nuevo, con solo las columnas especificadas.

    On Error GoTo RatiosErrorHandler

    Debug.Print "Ratios_Process: Iniciando..."

    ' 1. Verificar si los resultados de análisis/diseño están disponibles
    If g_objOpenSTAAD.Output.AreResultsAvailable = 0 Then
        MsgBox "Error: Resultados de análisis/diseño no disponibles en STAAD.Pro. Asegúrese de que el modelo haya sido analizado y diseñado previamente.", vbCritical, "Resultados No Disponibles"
        GoTo RatiosCleanup
    End If

    ' 2. Obtener o crear la hoja "Ratios" y preparar encabezados
    Dim wsRatios As Object
    On Error Resume Next ' Manejar error si la hoja no existe
    Set wsRatios = g_objWorkbook.Sheets("Ratios")
    If wsRatios Is Nothing Then
        On Error GoTo RatiosErrorHandler ' Restaurar manejador antes de error
        Set wsRatios = g_objWorkbook.Sheets.Add(After:=g_objWorkbook.Sheets(g_objWorkbook.Sheets.Count))
        wsRatios.Name = "Ratios"
        Debug.Print "Hoja 'Ratios' creada."
    Else
        On Error GoTo RatiosErrorHandler
        wsRatios.Cells.ClearContents ' Limpiar contenido existente si la hoja ya existía
        Debug.Print "Hoja 'Ratios' encontrada y limpiada."
    End If
    Debug.Print "Hoja 'Ratios' preparada."

    ' Escribir encabezados en la hoja "Ratios" (solo las columnas solicitadas y en el orden especificado)
    With wsRatios
        .Cells(1, 1).Value = "ID del elemento"
        .Cells(1, 2).Value = "Perfil"
        .Cells(1, 3).Value = "Código de diseño"
        .Cells(1, 4).Value = "Caso de carga crítico"
        .Cells(1, 5).Value = "Sección crítica (m)"
        .Cells(1, 6).Value = "Ratio crítico"
        .Cells(1, 7).Value = "Estado de diseño"
        .Range("A1:G1").Font.Bold = True ' Ajustar el rango de negrita
    End With
    Debug.Print "Encabezados escritos en la hoja 'Ratios'."

    ' 3. Obtener el conteo de miembros y la lista de todos los IDs
    Dim membcount As Long
    Dim allMemberIDs() As Long ' Array para almacenar todos los IDs de miembros
    Dim currentMemberID As Long
    Dim currentRowRatios As Long ' Contador de fila para escribir en la hoja "Ratios"
    currentRowRatios = 2 ' Empezar a escribir datos desde la fila 2

    membcount = g_objOpenSTAAD.Geometry.GetMemberCount
    Debug.Print "Conteo de miembros obtenido: " & membcount

    If membcount = 0 Then
        MsgBox "No se encontraron miembros en el modelo STAAD.Pro para extraer resultados.", vbExclamation, "Sin Miembros"
        GoTo RatiosCleanup
    End If

    ReDim allMemberIDs(0 To membcount - 1) ' Redimensionar el array para todos los IDs
    g_objOpenSTAAD.Geometry.GetBeamList allMemberIDs ' Llenar el array con los IDs de los miembros

    Debug.Print "Se encontraron " & membcount & " miembros en el modelo STAAD.Pro."

    ' 4. Iterar sobre cada miembro y extraer sus resultados de diseño ---
    ' Variables de salida para GetMemberSteelDesignResults (todas se declaran, pero solo se usarán las necesarias)
    Dim designCode As String
    Dim designStatus As String
    Dim CriticalRatio As Double
    Dim allowableRatio As Double
    Dim criticalLoadCase As Long
    Dim criticalSection As Double
    Dim criticalClause As String
    Dim designSection As String        ' Esto será el "Perfil"
    Dim designForces(0 To 2) As Double ' Array fijo de 3 elementos para las fuerzas (Pz, Vy, Vx)
    Dim KLByR As Double

    Debug.Print "Iniciando extracción de resultados de diseño para cada miembro..."

    Dim i As Long

    For i = LBound(allMemberIDs) To UBound(allMemberIDs) ' Iterar a través de cada ID de miembro
        currentMemberID = allMemberIDs(i)

        ' Inicializar variables de salida para cada miembro antes de la llamada a la API
        designCode = "N/A"
        designStatus = "N/A"
        CriticalRatio = -1 ' Usar -1 para indicar que aún no se ha encontrado un ratio válido
        allowableRatio = 0
        criticalLoadCase = 0
        criticalSection = 0
        criticalClause = "N/A"
        designSection = "N/A"
        designForces(0) = 0: designForces(1) = 0: designForces(2) = 0 ' Reiniciar fuerzas
        KLByR = 0

        ' --- LLAMADA A LA FUNCIÓN GetMemberSteelDesignResults (reciclado de Design results.txt) ---
        On Error Resume Next ' Capturar errores de la API para este miembro
        Dim varReturnVal_API As Long ' Variable local para el retorno de la API
        varReturnVal_API = g_objOpenSTAAD.Output.GetMemberSteelDesignResults( _
            currentMemberID, _
            designCode, _
            designStatus, _
            CriticalRatio, _
            allowableRatio, _
            criticalLoadCase, _
            criticalSection, _
            criticalClause, _
            designSection, _
            designForces, _
            KLByR _
        )

        Dim apiErrorNumber As Long
        apiErrorNumber = Err.Number
        Dim apiErrorDescription As String
        apiErrorDescription = Err.Description
        Err.Clear ' Limpiar el objeto Err después de capturar la información
        On Error GoTo RatiosErrorHandler ' Reactivar el manejador de errores principal

        If apiErrorNumber = 0 Then
            If varReturnVal_API = 1 Then ' Si la función retornó éxito (1)
                ' Escribir SOLO las columnas solicitadas en la hoja "Ratios" y en el orden especificado
                With wsRatios
                    .Cells(currentRowRatios, 1).Value = currentMemberID           ' ID del elemento
                    .Cells(currentRowRatios, 2).Value = designSection             ' Perfil
                    .Cells(currentRowRatios, 3).Value = designCode                ' Código de diseño
                    .Cells(currentRowRatios, 4).Value = criticalLoadCase          ' Caso de carga crítico
                    .Cells(currentRowRatios, 5).Value = Format(criticalSection, "0.000") ' Sección crítica (m)
                    .Cells(currentRowRatios, 6).Value = Format(CriticalRatio, "0.000")   ' Ratio crítico
                    .Cells(currentRowRatios, 7).Value = designStatus              ' Estado de diseño
                End With
                Debug.Print "Datos de diseño extraídos para Miembro " & currentMemberID & ". Ratio: " & Format(CriticalRatio, "0.000")
            Else ' Si la función retornó 0 (falla al encontrar datos válidos para este miembro)
                Debug.Print "Advertencia: GetMemberSteelDesignResults retornó 0 para Miembro " & currentMemberID & ". Puede que no tenga resultados de diseño válidos."
                ' Escribir una fila indicando que no se encontraron resultados (solo las 7 columnas)
                With wsRatios
                    .Cells(currentRowRatios, 1).Value = currentMemberID
                    .Cells(currentRowRatios, 2).Value = "N/A"
                    .Cells(currentRowRatios, 3).Value = "N/A"
                    .Cells(currentRowRatios, 4).Value = "N/A"
                    .Cells(currentRowRatios, 5).Value = "N/A"
                    .Cells(currentRowRatios, 6).Value = "N/A"
                    .Cells(currentRowRatios, 7).Value = "No Diseñado"
                End With
            End If
        Else ' Si la llamada a la API falló con un error de VBA
            Debug.Print "ERROR API: Falló GetMemberSteelDesignResults para Miembro " & currentMemberID & ". Error: " & apiErrorNumber & " - " & apiErrorDescription
            MsgBox "Error al obtener resultados para Miembro " & currentMemberID & ": " & apiErrorDescription & " (Número: " & apiErrorNumber & ").", vbCritical, "Error de API"
            ' Escribir una fila indicando el error de la API (solo las 7 columnas)
            With wsRatios
                .Cells(currentRowRatios, 1).Value = currentMemberID
                .Cells(currentRowRatios, 2).Value = "ERROR_API"
                .Cells(currentRowRatios, 3).Value = "ERROR_API"
                .Cells(currentRowRatios, 4).Value = "ERROR_API"
                .Cells(currentRowRatios, 5).Value = "ERROR_API"
                .Cells(currentRowRatios, 6).Value = "ERROR_API"
                .Cells(currentRowRatios, 7).Value = "ERROR_API"
            End With
        End If
        currentRowRatios = currentRowRatios + 1
    Next i ' Siguiente miembro

    wsRatios.Columns.AutoFit ' Autoajustar columnas al finalizar
    Debug.Print "Extracción de resultados de diseño completada. Total de filas en 'Ratios': " & (currentRowRatios - 1)

    Debug.Print "Ratios_Process: Completado."

RatiosCleanup:
    On Error Resume Next ' Para evitar errores al cerrar objetos que ya podrían estar liberados
    If Not wsRatios Is Nothing Then Set wsRatios = Nothing
    Exit Sub

RatiosErrorHandler:
    MsgBox "Se ha producido un error inesperado durante la ejecución en la subrutina 'Ratios_Process': " & Err.Description & vbCrLf & _
           "Número de error: " & Err.Number, vbCritical, "Error en Extracción de Ratios"
    Resume RatiosCleanup ' Saltar a la sección de limpieza para cerrar los objetos
End Sub



' --- COMPUTOS.TXT (Renombrada a Computos_Process) ---
Sub Computos_Process()
 
    ' Declaración de variables LOCALES para esta subrutina
    Dim anlFilePath As String       ' Ruta completa del archivo .ANL
    Dim fs As Object                ' FileSystemObject para manejo de archivos
    Dim ts As Object                ' TextStream para leer el archivo ANL
    Dim line As String
    Dim inTakeOffSection As Boolean ' Indica si estamos dentro de una sección de cómputo activa
    Dim headerFound As Boolean      ' Indica si el encabezado de unidades de la sección actual ha sido encontrado
    Dim weightUnitANL As String
    Dim lengthUnitANL As String
    Dim currentSectionType As String ' Almacena el tipo de sección actual (e.g., "ALL", "NORMAL")

    ' Variables para el control de la selección de tablas en el ANL
    Dim sectionFoundAndProcessed As Boolean ' Indica si una sección de cómputo deseada ya fue procesada
    Dim foundPreferredSection As Boolean    ' Indica si la sección 'STEEL TAKE OFF' fue encontrada
    Dim foundFallbackSection As Boolean     ' Indica si la sección 'STEEL TAKE OFF ALL' fue encontrada
    Dim anyTakeOffSectionProcessed As Boolean ' Nueva bandera para verificar si alguna sección de cómputo se procesó

    ' Declaración de variables para los datos extraídos del ANL
    Dim profileRaw As String
    Dim lengthRaw As Double
    Dim weightRaw As Double
    Dim sProfileType As String      ' Tipo de perfil (ST, T, Perfiles Laminados, etc.)
    Dim sProfileName As String      ' Nombre específico del perfil (W14X808, IPE200, etc.)

    ' Variables para la interacción con las hojas de Excel (usando el libro global g_objWorkbook)
    Dim wsComputos As Object
    Dim wsElementos As Object ' Aunque no se usa directamente para leer en esta versión, se mantiene la referencia si es necesaria en otras partes.
    Dim currentOutputRow As Long

    ' Variables para agrupar y sumar los cómputos
    Dim dictComputos As Object      ' Requiere referencia a Microsoft Scripting Runtime (Tools -> References)
    Dim varKey As Variant           ' <-- DECLARACIÓN EXPLÍCITA PARA RESOLVER "Expecting an existing scalar var"
    Dim arrTotals As Variant        ' arrTotals(0) = Longitud Total (m), arrTotals(1) = Peso Total (kN)

    ' --- Inicio del Bloque de Código ---
    On Error GoTo ErrorHandler

    Debug.Print "--- INICIO DE LA SUBRUTINA GenerarComputosMetricosSTAAD (Cómputos) ---"

    ' --- 1. Obtener la ruta del archivo .ANL ---
    ' Asumimos que g_objOpenSTAAD ya está conectado desde Sub Main.
    If g_objOpenSTAAD Is Nothing Then
        MsgBox "Error interno: El objeto OpenSTAAD no está inicializado. No se pueden obtener cómputos. Asegúrese de que STAAD.Pro esté abierto y el modelo cargado.", vbCritical, "Error de Inicialización"
        GoTo CleanUp
    End If

    Dim staadFilePath As String ' Declarar staadFilePath localmente
    g_objOpenSTAAD.GetSTAADFile staadFilePath, "TRUE"

    If staadFilePath = "" Then
        MsgBox "Error: No se pudo obtener la ruta del archivo STAAD.Pro. Asegúrese de que un modelo esté abierto y guardado.", vbCritical, "Error de STAAD"
        Debug.Print "Error: staadFilePath es Empty."
        GoTo CleanUp
    End If

    ' Determinar la ruta del archivo .ANL de forma robusta
    Dim dotPos As Long
    dotPos = InStrRev(staadFilePath, ".")
    If dotPos > 0 Then
        anlFilePath = Left(staadFilePath, dotPos - 1) & ".ANL"
    Else
        ' Si no se encuentra un punto, simplemente añade .ANL
        anlFilePath = staadFilePath & ".ANL"
    End If

    Set fs = CreateObject("Scripting.FileSystemObject")
    If Not fs.FileExists(anlFilePath) Then
        MsgBox "Error: No se encontró el archivo .ANL en la ruta: " & anlFilePath & vbCrLf & _
               "Asegúrese de que el análisis se haya ejecutado en STAAD.Pro.", vbCritical, "Archivo ANL No Encontrado"
        Debug.Print "Error: Archivo ANL no encontrado en " & anlFilePath
        GoTo CleanUp
    End If
    Debug.Print "Archivo ANL encontrado en: " & anlFilePath

    ' --- 2. Preparación de hojas de Excel ---
    ' Asumimos que g_objExcel y g_objWorkbook ya están abiertos desde Sub Main.
    If g_objWorkbook Is Nothing Then
        MsgBox "Error interno: El libro de Excel no está inicializado. No se pueden escribir cómputos.", vbCritical, "Error de Inicialización"
        GoTo CleanUp
    End If

    ' Obtener la hoja "Cómputos" (crearla si no existe)
    On Error Resume Next ' Para manejar el error si la hoja no existe
    Set wsComputos = g_objWorkbook.Sheets("Cómputos")
    If Err.Number <> 0 Then
        Set wsComputos = g_objWorkbook.Sheets.Add(After:=g_objWorkbook.Sheets(g_objWorkbook.Sheets.Count))
        wsComputos.Name = "Cómputos"
        Err.Clear
        Debug.Print "DEBUG: Hoja 'Cómputos' creada."
    Else
        Debug.Print "DEBUG: Hoja 'Cómputos' encontrada."
    End If
    On Error GoTo ErrorHandler ' Restaurar manejo de errores

    ' Limpiar contenido previo en la hoja "Cómputos" (desde la fila 2 hacia abajo)
    g_objExcel.DisplayAlerts = False ' Desactivar alertas para la limpieza
    wsComputos.Range("A2:D" & wsComputos.Rows.Count).ClearContents
    g_objExcel.DisplayAlerts = True ' Reactivar alertas
    Debug.Print "DEBUG: Contenido previo de 'Cómputos' borrado."

    ' Escribir encabezados en la hoja "Cómputos"
    wsComputos.Cells(1, 1).Value = "Tipo de Perfil"
    wsComputos.Cells(1, 2).Value = "Perfil"
    wsComputos.Cells(1, 3).Value = "Longitud Total (m)"
    wsComputos.Cells(1, 4).Value = "Peso Total (kN)"
    wsComputos.Range("A1:D1").Font.Bold = True
    currentOutputRow = 2 ' Empezar a escribir datos desde la fila 2

    Set dictComputos = CreateObject("Scripting.Dictionary")
    Debug.Print "DEBUG: Diccionario dictComputos inicializado."

    ' --- 3. Leer y parsear el archivo .ANL ---
    Set ts = fs.OpenTextFile(anlFilePath, 1) ' ForReading
    inTakeOffSection = False
    headerFound = False
    sectionFoundAndProcessed = False
    foundPreferredSection = False
    foundFallbackSection = False
    anyTakeOffSectionProcessed = False

    Debug.Print "DEBUG: Abriendo archivo ANL para lectura. Iniciando lógica de selección de tabla."

    Do While Not ts.AtEndOfStream
        line = ts.ReadLine

        ' Si una sección deseada ya fue procesada Y ya no estamos dentro de una sección, salimos del bucle principal
        If sectionFoundAndProcessed And Not inTakeOffSection Then
            Debug.Print "DEBUG: Una sección deseada ya fue procesada y la sección actual terminó. Terminando lectura del ANL."
            Exit Do
        End If

        ' Lógica de detección de secciones basada en prioridad:
        ' Prioridad 1: "STEEL TAKE OFF" (pero no "STEEL TAKE OFF ALL")
        If Not inTakeOffSection And Not foundPreferredSection And InStr(1, UCase(line), "STEEL TAKE OFF") > 0 And InStr(1, UCase(line), "STEEL TAKE OFF ALL") = 0 Then
            inTakeOffSection = True
            foundPreferredSection = True
            headerFound = False ' Reset header flag for new section
            Debug.Print "DEBUG: Activando procesamiento de sección 'STEEL TAKE OFF' (Prioritaria)."
            GoTo NextLine
        End If

        ' Prioridad 2: "STEEL TAKE OFF ALL" (solo si la sección prioritaria no ha sido encontrada)
        If Not inTakeOffSection And Not foundPreferredSection And InStr(1, UCase(line), "STEEL TAKE OFF ALL") > 0 Then
            inTakeOffSection = True
            foundFallbackSection = True ' Marcamos que se encontró la sección de fallback
            headerFound = False ' Reset header flag for new section
            Debug.Print "DEBUG: Activando procesamiento de sección 'STEEL TAKE OFF ALL' (Fallback)."
            GoTo NextLine
        End If

        ' Ignorar explícitamente "STEEL MEMBER TAKE OFF ALL"
        If InStr(1, UCase(line), "STEEL MEMBER TAKE OFF ALL") > 0 Then
            Debug.Print "DEBUG: Ignorando línea: 'STEEL MEMBER TAKE OFF ALL'."
            GoTo NextLine
        End If

        ' Si estamos dentro de una sección de cómputo activa (STEEL TAKE OFF o STEEL TAKE OFF ALL)
        If inTakeOffSection Then
            ' Buscar línea de encabezado para unidades
            If Not headerFound Then
                If InStr(1, UCase(line), "WEIGHT") > 0 And InStr(1, UCase(line), "LENGTH") > 0 Then
                    If InStr(1, UCase(line), "WEIGHT(POUN") > 0 Or InStr(1, UCase(line), "WEIGHT(LBS") > 0 Then weightUnitANL = "LB"
                    If InStr(1, UCase(line), "WEIGHT(KIP") > 0 Then weightUnitANL = "KIP"
                    If InStr(1, UCase(line), "WEIGHT(KN") > 0 Then weightUnitANL = "KN"
                    If InStr(1, UCase(line), "WEIGHT(N") > 0 Then weightUnitANL = "N"
                    If InStr(1, UCase(line), "WEIGHT(KG") > 0 Then weightUnitANL = "KG"
                    
                    If InStr(1, UCase(line), "LENGTH(MMS") > 0 Then lengthUnitANL = "MM"
                    If InStr(1, UCase(line), "LENGTH(CM") > 0 Then lengthUnitANL = "CM"
                    If InStr(1, UCase(line), "LENGTH(METER") > 0 Or InStr(1, UCase(line), "LENGTH(METE)") > 0 Then lengthUnitANL = "M"
                    If InStr(1, UCase(line), "LENGTH(INCH") > 0 Then lengthUnitANL = "IN"
                    If InStr(1, UCase(line), "LENGTH(FEET") > 0 Or InStr(1, UCase(line), "LENGTH(FOOT)") > 0 Then lengthUnitANL = "FT"
                    
                    headerFound = True
                    Debug.Print "DEBUG: Unidades ANL detectadas: Peso=" & weightUnitANL & ", Longitud=" & lengthUnitANL
                    GoTo NextLine
                End If
            End If

            ' Buscar línea de "TOTAL =" para saber que la sección ha terminado
            If InStr(1, UCase(line), "TOTAL =") > 0 Then
                inTakeOffSection = False
                sectionFoundAndProcessed = True ' Marcar que la sección activa ha sido procesada
                anyTakeOffSectionProcessed = True ' Actualizar la bandera general
                Debug.Print "DEBUG: Fin de sección de cómputo detectado y marcado como procesado. Se finalizará la lectura del ANL si no hay más secciones prioritarias."
                GoTo NextLine
            End If

            ' Procesar líneas de datos de perfil si el encabezado ya se encontró
            If headerFound Then
                ' Limpiar la línea y dividirla en partes
                ' Reemplazar non-breaking space (Chr(160)) y luego reemplazar múltiples espacios por uno solo
                line = Replace(line, Chr(160), " ") 
                Do While InStr(line, "  ") > 0 ' Reemplazar dobles espacios por un solo espacio
                    line = Replace(line, "  ", " ")
                Loop
                line = Trim(line) ' Eliminar espacios al inicio/final

                ' Buscar líneas que comienzan con "ST " o "T " y tienen al menos 4 partes (ST/T, perfil, longitud, peso)
                If (Left(UCase(line), 3) = "ST " Or Left(UCase(line), 2) = "T ") And InStr(1, line, " ") > 0 Then
                    Dim parts() As String
                    parts = Split(line, " ")

                    ' DEBUG: Imprimir las partes parseadas para verificar
                    Debug.Print "DEBUG: Línea ANL original: """ & line & """"
                    Dim dimIdx As Long
                    For dimIdx = LBound(parts) To UBound(parts)
                        Debug.Print "  parts(" & dimIdx & ") = """ & parts(dimIdx) & """"
                    Next dimIdx


                    ' Asegurarse de que haya suficientes partes (ST/T, Perfil, Longitud, Peso -> al menos 4 partes, índice 0 a 3)
                    If UBound(parts) >= 3 Then 
                        profileRaw = parts(1) ' El nombre del perfil es la segunda parte (índice 1)
                        
                        ' Asegúrate de que las partes de longitud y peso sean numéricas antes de convertir
                        If IsNumeric(parts(2)) And IsNumeric(parts(3)) Then
                            lengthRaw = CDbl(parts(2)) ' Longitud (tercera parte, índice 2)
                            weightRaw = CDbl(parts(3)) ' Peso (cuarta parte, índice 3)
                        Else
                            Debug.Print "Advertencia: Longitud o peso no numérico encontrado en la línea (después de limpieza): " & line & ". Parts(2)='" & parts(2) & "', Parts(3)='" & parts(3) & "'"
                            GoTo NextLine ' Saltar al siguiente perfil si los datos no son válidos
                        End If
                        

                        ' Determinar Tipo de Perfil y Nombre de Perfil
                        ' Priorizar la sigla de la línea de ANL si es una conocida (ST, T, L)
                        sProfileName = UCase(profileRaw) ' Nombre del perfil en mayúsculas para la clasificación

                        If UCase(parts(0)) = "ST" Then
                            sProfileType = "ST" ' Acero
                        ElseIf UCase(parts(0)) = "T" Then
                            sProfileType = "T" ' Celosía (Truss)
                        ElseIf UCase(parts(0)) = "L" Then
                            sProfileType = "L" ' Ángulo
                        ElseIf UCase(parts(0)) = "LD" Then
                            sProfileType = "LD" ' Doble Ángulo
                        Else
                            ' Si parts(0) no es una sigla directa, entonces clasificar por el nombre del perfil (sProfileName)
                            If InStr(1, sProfileName, "W") > 0 Or InStr(1, sProfileName, "IPE") > 0 Or _
                               InStr(1, sProfileName, "HE") > 0 Or InStr(1, sProfileName, "UB") > 0 Or _
                               InStr(1, sProfileName, "UC") > 0 Then
                                sProfileType = "Perfiles Laminados"
                            ElseIf InStr(1, sProfileName, "CH") > 0 Or InStr(1, sProfileName, "C") > 0 Then
                                sProfileType = "Canal"
                            ElseIf InStr(1, sProfileName, "PIPE") > 0 Or InStr(1, sProfileName, "TUBE") > 0 Then
                                sProfileType = "Circular/Tubular"
                            ElseIf InStr(1, sProfileName, "RECT") > 0 Or InStr(1, sProfileName, "SQ") > 0 Then
                                sProfileType = "Rectangular/Cuadrado"
                            ElseIf InStr(1, sProfileName, "CIRC") > 0 Then
                                sProfileType = "Circular Sólido"
                            Else
                                sProfileType = "Otro Tipo de Perfil" ' Para perfiles no reconocidos
                            End If
                        End If
                        
                        ' Ajuste para perfiles de concreto si su nombre lo indica claramente
                        If InStr(1, sProfileName, "CONCRETE") > 0 Then sProfileType = "Concreto"
                        
                        ' --- Convertir unidades a m y kN ---
                        Dim lengthInM As Double
                        Dim weightInKN As Double

                        ' Convertir longitud a metros
                        Select Case UCase(lengthUnitANL)
                            Case "MM": lengthInM = lengthRaw / 1000#
                            Case "CM": lengthInM = lengthRaw / 100#
                            Case "M": lengthInM = lengthRaw
                            Case "IN": lengthInM = lengthRaw * 0.0254
                            Case "FT": lengthInM = lengthRaw * 0.3048
                            Case Else: lengthInM = lengthRaw ' Usar tal cual si la unidad es desconocida
                        End Select

                        ' Convertir peso a kilonewtons (kN)
                        Select Case UCase(weightUnitANL)
                            Case "LB": weightInKN = weightRaw * 0.00444822 ' 1 lb = 0.00444822 kN
                            Case "KIP": weightInKN = weightRaw * 4.44822 ' 1 kip = 4.44822 kN
                            Case "KN": weightInKN = weightRaw
                            Case "N": weightInKN = weightRaw / 1000#
                            Case "KG": weightInKN = weightRaw * 0.00980665 ' 1 kg = 0.00980665 kN (aprox, g=9.80665 m/s^2)
                            Case Else: weightInKN = weightRaw ' Usar tal cual si la unidad es desconocida
                        End Select

                        ' --- 5. Agrupar y sumar los cómputos ---
                        varKey = sProfileType & " | " & sProfileName ' Clave para el diccionario

                        If dictComputos.Exists(varKey) Then
                            ' Si ya existe, sumar a los totales existentes
                            arrTotals = dictComputos.Item(varKey)
                            arrTotals(0) = arrTotals(0) + lengthInM ' Sumar Longitud en metros
                            arrTotals(1) = arrTotals(1) + weightInKN ' Sumar Peso en kN
                            dictComputos.Item(varKey) = arrTotals
                        Else
                            ' Si no existe, crear una nueva entrada
                            ReDim arrTotals(1)
                            arrTotals(0) = lengthInM
                            arrTotals(1) = weightInKN
                            dictComputos.Add varKey, arrTotals
                        End If
                        Debug.Print "DEBUG: Perfil procesado y añadido/sumado: " & sProfileName & ", Longitud: " & Format(lengthInM, "0.000") & " m, Peso: " & Format(weightInKN, "0.000") & " kN"
                    End If ' End If UBound(parts) >= 3
                End If ' End If (Left(UCase(line), 3) = "ST " Or Left(UCase(line), 2) = "T ")
            End If ' End If headerFound
        End If ' End If inTakeOffSection
NextLine: ' Etiqueta para el salto GoTo
    Loop ' Continue reading file

    ts.Close ' Cerrar el archivo ANL
    Debug.Print "DEBUG: Archivo ANL cerrado."

    ' --- VERIFICACIÓN FINAL DE DATOS DE CÓMPUTOS ---
    ' Se verifica si se procesó alguna sección y si el diccionario de cómputos tiene elementos.
    If Not anyTakeOffSectionProcessed Or dictComputos.Count = 0 Then
        MsgBox "No se encontraron comandos de cómputos de acero ('STEEL TAKE OFF' o 'STEEL TAKE OFF ALL') cargados en el modelo o la sección encontrada no contenía datos válidos." & vbCrLf & _
               "Por favor, asegúrese de que el análisis se haya ejecutado correctamente en STAAD.Pro y que el archivo .ANL contenga las secciones de cómputo esperadas.", vbExclamation, "No Hay Datos de Cómputo"
        GoTo CleanUp ' Salir si no se encontró nada
    End If

    ' --- 6. Escribir los resultados agrupados en la hoja "Cómputos" ---
    currentOutputRow = 2 ' Empezar a escribir desde la fila 2
    Debug.Print "DEBUG: Iniciando escritura de resultados en 'Cómputos'."
    
    ' Esta verificación es redundante si la anterior ya pasó, pero no está de más
    If dictComputos.Count > 0 Then 
        For Each varKey In dictComputos.Keys
            arrTotals = dictComputos.Item(varKey)

            ' Separar el tipo de perfil y el nombre del perfil de la clave
            sProfileType = Split(varKey, " | ")(0)
            sProfileName = Split(varKey, " | ")(1)

            On Error Resume Next ' Manejar errores si las celdas están protegidas o inaccesibles
            wsComputos.Cells(currentOutputRow, 1).Value = sProfileType
            wsComputos.Cells(currentOutputRow, 2).Value = sProfileName
            wsComputos.Cells(currentOutputRow, 3).Value = Format(arrTotals(0), "0.000") ' Longitud Total (m)
            wsComputos.Cells(currentOutputRow, 4).Value = Format(arrTotals(1), "0.000") ' Peso Total (kN)
            
            If Err.Number <> 0 Then
                Debug.Print "ERROR: Fallo al escribir en la celda R" & currentOutputRow & "C" & 1 & " de la hoja 'Cómputos'. Error: " & Err.Description & " (" & Err.Number & ")"
                Err.Clear ' Limpiar el error para intentar con la siguiente fila
            Else
                Debug.Print "DEBUG: Escrito en fila " & currentOutputRow & ": " & sProfileType & " | " & sProfileName & " | " & Format(arrTotals(0), "0.000") & " | " & Format(arrTotals(1), "0.000")
            End If
            On Error GoTo ErrorHandler ' Restaurar manejo de errores

            currentOutputRow = currentOutputRow + 1
        Next varKey
        wsComputos.Columns.AutoFit
        Debug.Print "DEBUG: Escritura de resultados en 'Cómputos' completada. Filas escritas: " & (currentOutputRow - 2)
    Else
        Debug.Print "DEBUG: No se encontraron cómputos para escribir en Excel (diccionario vacío, esto no debería pasar si la alerta previa no se activó)."
    End If

    'MsgBox "Cómputos métricos generados exitosamente en la hoja 'Cómputos' desde el archivo ANL.", vbInformation, "Proceso Completado"

CleanUp:
    ' Liberar objetos LOCALES de esta subrutina
    If Not ts Is Nothing Then ts.Close
    Set fs = Nothing

    ' NO SE CIERRAN NI LIBERAN LOS OBJETOS GLOBALES (g_objExcel, g_objWorkbook, g_objOpenSTAAD)
    ' porque son gestionados por la subrutina Main de tu macro principal.
    Set wsComputos = Nothing
    Set wsElementos = Nothing ' También liberar esta referencia local
    Set dictComputos = Nothing
    Debug.Print "--- FIN DE LA SUBRUTINA GenerarComputosMetricosSTAAD (Cómputos) ---"
    Exit Sub

ErrorHandler:
    MsgBox "Ha ocurrido un error en la subrutina de Cómputos: " & Err.Description & " (Número: " & Err.Number & ").", vbCritical, "Error en Cómputos"
    Debug.Print "ERROR: Se ha producido un error general en GenerarComputosMetricosSTAAD: " & Err.Description & " (Número: " & Err.Number & ")."
    Resume CleanUp ' Saltar a la sección de limpieza para cerrar los objetos locales
End Sub


Sub material(ByRef in_objOpenSTAAD As Object, ByRef in_objExcel As Object, ByRef in_objWorkbook As Object)
    ' Propósito: Extraer las propiedades de los materiales isótropos en uso
    ' del modelo STAAD.Pro abierto y escribirlas en la hoja "MC"
    ' de "Límites de deflexión.xlsx".

    ' --- Variables ---
    Dim objSheetMC As Object        ' Objeto de la hoja "MC" de Excel

    Dim lMaterialCount As Long      ' Número total de materiales isótropos definidos en STAAD
    Dim i As Long                   ' Contador para bucle de materiales
    Dim sMaterialName As String     ' Nombre del material actual
    Dim lAssignedBeamCount As Long  ' Conteo de vigas asignadas al material
    Dim lAssignedPlateCount As Long ' Conteo de placas asignadas al material
    Dim lAssignedSolidCount As Long ' Conteo de sólidos asignados al material

    ' Variables para las propiedades del material (obtenidas de GetIsotropicMaterialPropertiesEx).
    Dim dblE As Double
    Dim dblPoisson As Double
    Dim dblG As Double
    Dim dblDensity As Double
    Dim dblAlpha As Double
    Dim dblCrDamp As Double
    Dim dblFy As Double
    Dim dblFu As Double
    Dim dblRy As Double
    Dim dblRt As Double
    Dim dblFcu As Double

    Dim materialColumnIndex As Long ' Índice de la columna actual para escribir propiedades (comienza en 3 para la columna C)

    ' --- Configurar el manejo de errores ---
    On Error GoTo MaterialErrorHandler

    Debug.Print "material: Iniciando procesamiento de materiales..."

    ' --- Obtener la hoja "MC" (usando el libro de trabajo ya abierto) ---
    Debug.Print "material: Intentando obtener la hoja 'MC'..."
    On Error Resume Next
    Set objSheetMC = in_objWorkbook.Sheets("MC")
    If objSheetMC Is Nothing Then
        On Error GoTo MaterialErrorHandler ' Restaurar manejador antes de error

        Debug.Print "material: Error: La hoja 'MC' no se encontró."
        GoTo MaterialCleanup
    End If
    On Error GoTo MaterialErrorHandler
    Debug.Print "material: Hoja 'MC' obtenida exitosamente."

    ' --- Limpiar contenido existente en las columnas de datos de materiales (Columnas C en adelante, desde la fila 2) ---
    Debug.Print "material: Limpiando contenido existente en la hoja 'MC' (Columnas C+)..."
    in_objExcel.DisplayAlerts = False ' Deshabilitar temporalmente las alertas para la limpieza
    objSheetMC.Range(objSheetMC.Cells(2, 3), objSheetMC.Cells(13, 26)).ClearContents
    in_objExcel.DisplayAlerts = True ' Volver a habilitar las alertas
    Debug.Print "material: Contenido de la hoja 'MC' (Columnas C+) limpiado."

    ' --- Escribir encabezados de propiedades en la Columna B (Filas 2 a 13) ---
    Debug.Print "material: Escribiendo encabezados de propiedades en la Columna B..."
    objSheetMC.Cells(2, 2).Value = "Título"
    objSheetMC.Cells(3, 2).Value = "Módulo de Young ""E"" (kN/m²)"
    objSheetMC.Cells(4, 2).Value = "Coeficiente de Poisson ""v"""
    objSheetMC.Cells(5, 2).Value = "Densidad ""Y"" (kN/m³)"
    objSheetMC.Cells(6, 2).Value = "Coeficiente Térmico ""a""(/°C)"
    objSheetMC.Cells(7, 2).Value = "Amortiguamiento Crítico"
    objSheetMC.Cells(8, 2).Value = "Módulo de Corte ""G"" (kN/m²)"
    objSheetMC.Cells(9, 2).Value = "Límite Elástico ""Fy"" (kN/m²)"
    objSheetMC.Cells(10, 2).Value = "Resistencia a la Tracción ""Fu"" (kN/m²)"
    objSheetMC.Cells(11, 2).Value = "Relación de Resistencia a la Cedencia ""Ry"""
    objSheetMC.Cells(12, 2).Value = "Relación de Resistencia a la Tracción ""Rt"""
    objSheetMC.Cells(13, 2).Value = "Resistencia a la Compresión Fcu (kN/m²)"
    Debug.Print "material: Encabezados de propiedades escritos."

    ' --- Extraer y escribir propiedades de materiales en uso en las Columnas C+ ---
    Debug.Print "material: Iniciando extracción y escritura de materiales en uso en las Columnas C+..."
    materialColumnIndex = 3

    lMaterialCount = in_objOpenSTAAD.Property.GetIsotropicMaterialCount()
    Debug.Print "material: Número total de materiales isótropos en STAAD: " & lMaterialCount

    If lMaterialCount > 0 Then
        For i = 0 To lMaterialCount - 1
            sMaterialName = in_objOpenSTAAD.Property.GetIsotropicMaterialPropertiesEx(i, dblE, dblPoisson, dblG, dblDensity, dblAlpha, dblCrDamp, dblFy, dblFu, dblRy, dblRt, dblFcu)

            lAssignedBeamCount = in_objOpenSTAAD.Property.GetIsotropicMaterialAssignedBeamCount(sMaterialName)
            lAssignedPlateCount = in_objOpenSTAAD.Property.GetIsotropicMaterialAssignedPlateCount(sMaterialName)
            lAssignedSolidCount = in_objOpenSTAAD.Property.GetIsotropicMaterialAssignedSolidCount(sMaterialName)

            If (lAssignedBeamCount > 0) Or (lAssignedPlateCount > 0) Or (lAssignedSolidCount > 0) Then
                Debug.Print "material: Material '" & sMaterialName & "' en uso. Escribiendo propiedades en la columna " & materialColumnIndex & "..."

                objSheetMC.Cells(2, materialColumnIndex).Value = sMaterialName
                objSheetMC.Cells(3, materialColumnIndex).Value = dblE
                objSheetMC.Cells(4, materialColumnIndex).Value = dblPoisson
                objSheetMC.Cells(5, materialColumnIndex).Value = dblDensity
                objSheetMC.Cells(6, materialColumnIndex).Value = dblAlpha
                objSheetMC.Cells(7, materialColumnIndex).Value = dblCrDamp
                objSheetMC.Cells(8, materialColumnIndex).Value = dblG
                objSheetMC.Cells(9, materialColumnIndex).Value = dblFy
                objSheetMC.Cells(10, materialColumnIndex).Value = dblFu
                objSheetMC.Cells(11, materialColumnIndex).Value = dblRy
                objSheetMC.Cells(12, materialColumnIndex).Value = dblRt
                objSheetMC.Cells(13, materialColumnIndex).Value = dblFcu

                materialColumnIndex = materialColumnIndex + 1
            Else
                Debug.Print "material: Material '" & sMaterialName & "' no asignado a ningún elemento. No se escribirá en Excel."
            End If
        Next i
        Debug.Print "material: Extracción y escritura de materiales completada."
    Else
        Debug.Print "material: No se encontraron materiales isótropos definidos o en uso."
    End If

MaterialCleanup:
    Debug.Print "material: Limpiando recursos específicos de 'material'..."
    Set objSheetMC = Nothing
    Debug.Print "material: Limpieza completada. Saliendo de 'material'."
    Exit Sub

MaterialErrorHandler:
    MsgBox "Ocurrió un error en la subrutina 'material':" & vbCrLf & _
           "Número de Error: " & Err.Number & vbCrLf & _
           "Descripción: " & Err.Description, vbCritical, "Error de Material"
    Debug.Print "material: Error en MaterialErrorHandler: " & Err.Description & " (" & Err.Number & ")"
    Resume MaterialCleanup
End Sub


Sub soporte(ByRef in_objOpenSTAAD As Object, ByRef in_objExcel As Object, ByRef in_objWorkbook As Object)
    ' Propósito: Extraer todos los soportes asignados en el modelo STAAD.Pro abierto,
    ' obtener el tipo de soporte, los nodos a los que está aplicado y su número de referencia (ej. S1, S2),
    ' exportar esta información para cada nodo a un archivo de texto temporal,
    ' luego leer ese archivo de texto, extraer la Referencia, el Tipo de Soporte (sin paréntesis) y el Nodo
    ' y escribirlos en las columnas A, B, C de la hoja "Soporte" del archivo "Límites de deflexión.xlsx",
    ' con encabezados en la primera fila.

    ' --- Variables para Rutas ---
    Dim tempTxtFilePath As String   ' Ruta completa del archivo de texto temporal

    ' --- Variables para Extracción de STAAD ---
    Dim lSupportCount As Long       ' Número total de nodos con soportes
    Dim lSupportedNodes() As Long   ' Array para almacenar los IDs de los nodos con soportes (unidimensional)
    Dim lCurrentNodeID As Long      ' ID del nodo actual en el bucle de extracción
    Dim lSupportReferenceNo As Long ' Número de referencia del soporte (ej. 1 para S1, 2 para S2)
    Dim lSupportTypeCodeEx As Long  ' Código del tipo de soporte (retornado por GetSupportInformationEx)
    Dim varReleaseSpec(0 To 5) As Long ' Array para especificaciones de liberación (no usado, pero requerido por la función)
    Dim varSpringSpec(0 To 5) As Double ' Array para rigideces de resorte (no usado, pero requerido por la función)
    Dim lSupportType As Long ' Variable necesaria para la llamada a la función, aunque el valor de retorno no se usa

    ' --- Variables para Escritura en Archivo de Texto ---
    Dim fileSystemWrite As Object   ' Objeto FileSystemObject para manejo de archivos (escritura)
    Dim textStreamWrite As Object   ' Objeto TextStream para escribir en el archivo
    Dim sSupportReferenceString As String ' La cadena "S#" para la referencia del soporte
    Dim sSupportTypeName As String ' El nombre legible del tipo de soporte
    Dim sOutputLine As String       ' Cadena para construir la línea de salida para cada nodo en el TXT

    ' --- Variables para Interacción con Excel ---
    Dim objSheetSoporte As Object   ' Objeto de la hoja "Soporte" de Excel

    ' --- Variables para Lectura de Archivo de Texto y Escritura en Excel ---
    Dim fileSystemRead As Object    ' Objeto FileSystemObject para manejo de archivos (lectura)
    Dim fileStreamRead As Object    ' Objeto TextStream para leer el archivo
    Dim line As String              ' Variable para leer cada línea del TXT
    Dim excelRow As Long            ' Contador de fila para escribir en Excel
    ' Variables para parsear la línea del TXT
    Dim nodeID_TXT As String
    Dim supportRef_TXT As String
    Dim supportType_TXT As String
    Dim colonPos As Long
    Dim tempString As String ' Variable temporal para parsear

    ' --- Contadores y Bucle ---
    Dim i As Long                   ' Contador genérico para bucles


    ' --- Configurar el manejo de errores ---
    On Error GoTo SoporteErrorHandler

    Debug.Print "soporte: Iniciando procesamiento de soportes..."

    ' Definir la ruta completa del archivo de texto temporal (en la misma carpeta que el modelo STAAD)
    Dim staadDir As String

    tempTxtFilePath = staadDir & "Soportes_STAAD_Exportados.txt"
    Debug.Print "soporte: Archivo de texto temporal: " & tempTxtFilePath

    ' --- 1. Obtener el número total de nodos con soportes ---
    Debug.Print "soporte: Intentando obtener el número de nodos con soportes..."
    lSupportCount = in_objOpenSTAAD.Support.GetSupportCount()
    Debug.Print "soporte: Número total de nodos con soportes encontrados: " & lSupportCount

    ' --- 2. Si hay soportes, obtener la lista de nodos y escribir en el archivo TXT ---
    If lSupportCount > 0 Then
        Debug.Print "soporte: Redimensionando array para " & lSupportCount & " nodos soportados."
        ReDim lSupportedNodes(lSupportCount - 1)

        Debug.Print "soporte: Intentando obtener la lista de nodos soportados..."
        in_objOpenSTAAD.Support.GetSupportNodes lSupportedNodes
        Debug.Print "soporte: Lista de nodos soportados obtenida con éxito."

        ' --- Abrir archivo de texto para escritura ---
        Debug.Print "soporte: Abriendo archivo de texto temporal para escritura..."
        Set fileSystemWrite = CreateObject("Scripting.FileSystemObject")
        Set textStreamWrite = fileSystemWrite.CreateTextFile(tempTxtFilePath, True)
        Debug.Print "soporte: Archivo de texto temporal abierto con éxito."

        ' Escribir un encabezado en el archivo
        textStreamWrite.WriteLine "--- Soportes Asignados (por Nodo) ---"
        textStreamWrite.WriteLine "Formato: NodoID: Referencia (Tipo de Soporte)"
        textStreamWrite.WriteLine "------------------------------------"

        Debug.Print "soporte: Procesando cada nodo soportado y escribiendo en archivo de texto..."
        For i = 0 To lSupportCount - 1
            lCurrentNodeID = lSupportedNodes(i)
            lSupportType = in_objOpenSTAAD.Support.GetSupportInformationEx(lCurrentNodeID, lSupportReferenceNo, lSupportTypeCodeEx, varReleaseSpec, varSpringSpec)
            sSupportTypeName = GetSupportTypeName(lSupportTypeCodeEx)

            If lSupportReferenceNo > 0 Then
                sSupportReferenceString = "S" & lSupportReferenceNo
            ElseIf lSupportReferenceNo = -1 Then
                 sSupportReferenceString = "Ref. Desconocida"
            Else
                 sSupportReferenceString = "Sin Soporte"
            End If

            sOutputLine = "Nodo " & lCurrentNodeID & ": " & sSupportReferenceString & " (" & sSupportTypeName & ")"
            textStreamWrite.WriteLine sOutputLine
        Next i

        ' --- Cerrar el archivo de texto ---
        textStreamWrite.Close
        Set textStreamWrite = Nothing
        Set fileSystemWrite = Nothing
        Debug.Print "soporte: Escritura en archivo de texto temporal completada."

    Else
        Debug.Print "soporte: No se encontraron soportes asignados en el modelo. Se creará un archivo de texto temporal vacío."
        Set fileSystemWrite = CreateObject("Scripting.FileSystemObject")
        Set textStreamWrite = fileSystemWrite.CreateTextFile(tempTxtFilePath, True)
        textStreamWrite.WriteLine "--- Soportes Asignados (por Nodo) ---"
        textStreamWrite.WriteLine "Formato: NodoID: Referencia (Tipo de Soporte)"
        textStreamWrite.WriteLine "------------------------------------"
        textStreamWrite.Close
        Set textStreamWrite = Nothing
        Set fileSystemWrite = Nothing
    End If

    ' --- 3. Obtener o crear la hoja "Soporte" (usando el libro de trabajo ya abierto) ---
    Debug.Print "soporte: Intentando obtener o crear hoja 'Soporte'..."
    On Error Resume Next ' Para manejar si la hoja no existe y crearla
    Set objSheetSoporte = in_objWorkbook.Sheets("Soporte")
    If objSheetSoporte Is Nothing Then
        On Error GoTo SoporteErrorHandler ' Restaurar manejador antes de error
        Debug.Print "soporte: Hoja 'Soporte' no encontrada. Creando nueva hoja..."
        Set objSheetSoporte = in_objWorkbook.Sheets.Add(After:=in_objWorkbook.Sheets(in_objWorkbook.Sheets.Count))
        objSheetSoporte.Name = "Soporte"
        Debug.Print "soporte: Hoja 'Soporte' creada con éxito."
    Else
        On Error GoTo SoporteErrorHandler
        Debug.Print "soporte: Hoja 'Soporte' encontrada. Limpiando contenido existente..."
        in_objExcel.DisplayAlerts = False ' Desactivar alertas temporalmente
        objSheetSoporte.Cells.ClearContents
        in_objExcel.DisplayAlerts = True ' Reactivar alertas
        Debug.Print "soporte: Preparación de hoja 'Soporte' completada."
    End If

    ' --- 4. Leer el archivo de texto y escribir en la hoja "Soporte" con la nueva estructura ---
    If Dir(tempTxtFilePath) <> "" Then
        Debug.Print "soporte: Iniciando lectura del archivo de texto y escritura en hoja 'Soporte'..."

        Set fileSystemRead = CreateObject("Scripting.FileSystemObject")
        Set fileStreamRead = fileSystemRead.OpenTextFile(tempTxtFilePath, 1)

        excelRow = 1

        ' Escribir encabezados en la primera fila
        objSheetSoporte.Cells(excelRow, 1).Value = "Referencia"
        objSheetSoporte.Cells(excelRow, 2).Value = "Tipo de Soporte"
        objSheetSoporte.Cells(excelRow, 3).Value = "Nodo"
        excelRow = 2

        ' Leer y descartar las líneas de encabezado del archivo de texto
        If Not fileStreamRead.AtEndOfStream Then fileStreamRead.ReadLine ' Línea de encabezado
        If Not fileStreamRead.AtEndOfStream Then fileStreamRead.ReadLine ' Línea de formato
        If Not fileStreamRead.AtEndOfStream Then fileStreamRead.ReadLine ' Línea de guiones

        Do While Not fileStreamRead.AtEndOfStream
            line = fileStreamRead.ReadLine

            If Trim(line) <> "" Then
                nodeID_TXT = ""
                supportRef_TXT = ""
                supportType_TXT = ""

                colonPos = InStr(line, ":")
                If colonPos > 0 Then
                    Dim nodoString As String
                    nodoString = Left(line, colonPos - 1)
                    Dim firstSpaceInNodo As Long
                    firstSpaceInNodo = InStr(nodoString, " ")
                    If firstSpaceInNodo > 0 Then
                         nodeID_TXT = Trim(Mid(nodoString, firstSpaceInNodo + 1))
                    End If

                    tempString = Trim(Mid(line, colonPos + 1))
                    Dim firstSpaceInTemp As Long
                    firstSpaceInTemp = InStr(tempString, " ")

                    If firstSpaceInTemp > 0 Then
                        supportRef_TXT = Trim(Left(tempString, firstSpaceInTemp - 1))
                        supportType_TXT = Trim(Mid(tempString, firstSpaceInTemp + 1))
                        If Left(supportType_TXT, 1) = "(" And Right(supportType_TXT, 1) = ")" Then
                            supportType_TXT = Mid(supportType_TXT, 2, Len(supportType_TXT) - 2)
                        End If
                    End If
                End If

                objSheetSoporte.Cells(excelRow, 1).Value = supportRef_TXT
                objSheetSoporte.Cells(excelRow, 2).Value = supportType_TXT
                objSheetSoporte.Cells(excelRow, 3).Value = nodeID_TXT
                excelRow = excelRow + 1
            End If
        Loop

        fileStreamRead.Close
        Set fileStreamRead = Nothing
        Set fileSystemRead = CreateObject("Scripting.FileSystemObject")
        Debug.Print "soporte: Lectura del archivo de texto y escritura en hoja 'Soporte' completada."

        ' --- Eliminar archivo de texto temporal ---
        Debug.Print "soporte: Eliminando archivo de texto temporal: " & tempTxtFilePath & "..."
        If fileSystemRead.FileExists(tempTxtFilePath) Then
            fileSystemRead.DeleteFile tempTxtFilePath, True
        End If
        Set fileSystemRead = Nothing
        Debug.Print "soporte: Archivo de texto temporal eliminado."

    Else
        Debug.Print "soporte: No se encontró el archivo de texto temporal (" & tempTxtFilePath & "). No se importará nada a la hoja 'Soporte'."
    End If

SoporteCleanup:
    Debug.Print "soporte: Limpiando recursos específicos de 'soporte'..."
    On Error Resume Next
    Dim tempTS As Object
    If Not textStreamWrite Is Nothing Then
        Set tempTS = textStreamWrite
        tempTS.Close
        Set textStreamWrite = Nothing
    End If
    If Not fileStreamRead Is Nothing Then
        Set tempTS = fileStreamRead
        tempTS.Close
        Set fileStreamRead = Nothing
    End If
    Set fileSystemWrite = Nothing
    Set fileSystemRead = Nothing
    Set objSheetSoporte = Nothing
    Debug.Print "soporte: Limpieza completada. Saliendo de 'soporte'."
    Exit Sub

SoporteErrorHandler:
    MsgBox "Ocurrió un error en la subrutina 'soporte':" & vbCrLf & _
           "Número de Error: " & Err.Number & vbCrLf & _
           "Descripción: " & Err.Description, vbCritical, "Error de Soporte"
    Debug.Print "soporte: Error en SoporteErrorHandler: " & Err.Description & " (" & Err.Number & ")"
    Resume SoporteCleanup
End Sub


Sub reacciones(ByRef in_objOpenSTAAD As Object, ByRef in_objExcel As Object, ByRef in_objWorkbook As Object)
    Dim wsReacciones As Object, wsSoporte As Object
    Dim i As Long, j As Long, k As Long
    Dim dReactionArray(0 To 5) As Double ' FX, FY, FZ, MX, MY, MZ
    Dim RetVal As Variant
    Dim nodeID As Long, loadCaseID As Long
    Dim maxAbsValueForCurrentCase As Double
    Dim criticalComponentForCurrentCase As String
    Dim rowIndex As Long
    Dim componentes() As String
    Dim nodosSoporte() As Long
    Dim lastRow As Long
    Dim lPrimaryLoadCaseCount As Long ' Número de casos de carga primarios
    Dim lPrimaryLoadCaseIDs() As Long ' Array para almacenar los IDs de los casos de carga primarios
    Dim hasNonZeroReaction As Boolean ' Nueva variable para verificar si hay reacciones no nulas

    componentes = Split("FX,FY,FZ,MX,MY,MZ", ",") ' Nombres de los componentes de reacción

    On Error GoTo ReaccionesErrorHandler

    Debug.Print "reacciones: Iniciando procesamiento de reacciones..."

    ' 1. Verificar si los resultados del análisis están disponibles
    If in_objOpenSTAAD.Output.AreResultsAvailable() = False Then
        MsgBox "Los resultados del análisis no están disponibles. Ejecute el análisis en STAAD antes de continuar.", vbCritical, "Resultados No Disponibles"
        Debug.Print "reacciones: Error: Resultados del análisis no disponibles."
        GoTo ReaccionesCleanup
    End If
    Debug.Print "reacciones: Resultados del análisis disponibles."

    ' 2. Obtener las hojas necesarias (usando el libro de trabajo ya abierto)
    Debug.Print "reacciones: Intentando obtener la hoja 'Soporte'..."
    On Error Resume Next
    Set wsSoporte = in_objWorkbook.Sheets("Soporte")
    If wsSoporte Is Nothing Then
        On Error GoTo ReaccionesErrorHandler ' Restaurar manejador antes de error
        MsgBox "Error: La hoja 'Soporte' no se encontró en el archivo Excel.", vbCritical, "Hoja No Encontrada"
        Debug.Print "reacciones: Error: Hoja 'Soporte' no encontrada."
        GoTo ReaccionesCleanup
    End If
    On Error GoTo ReaccionesErrorHandler
    Debug.Print "reacciones: 'Soporte' hoja obtenida exitosamente."

    ' 3. Leer los nodos desde la hoja "Soporte", columna C
    Debug.Print "reacciones: Leyendo nodos desde la hoja 'Soporte'..."
    lastRow = wsSoporte.Cells(wsSoporte.Rows.Count, 3).End(xlUp).Row ' xlUp es -4162
    If lastRow < 2 Then ' Verificar si hay filas de datos (el encabezado es la fila 1)
        MsgBox "No se encontraron nodos soportados en la hoja 'Soporte'. Asegúrese de que la macro 'soporte' se ejecutó correctamente.", vbExclamation, "No Hay Nodos Soportados"
        Debug.Print "reacciones: Advertencia: No se encontraron nodos soportados en la hoja 'Soporte'."
        GoTo ReaccionesCleanup
    End If
    ReDim nodosSoporte(1 To lastRow - 1)
    For i = 2 To lastRow
        nodosSoporte(i - 1) = wsSoporte.Cells(i, 3).Value
    Next i
    Debug.Print "reacciones: " & UBound(nodosSoporte) - LBound(nodosSoporte) + 1 & " nodos soportados leídos."

    ' 4. Preparar la hoja "Reacciones" ---
    Debug.Print "reacciones: Preparando la hoja 'Reacciones'..."
    On Error Resume Next ' Para manejar si la hoja no existe y crearla
    Set wsReacciones = in_objWorkbook.Sheets("Reacciones")
    If wsReacciones Is Nothing Then
        On Error GoTo ReaccionesErrorHandler
        Set wsReacciones = in_objWorkbook.Sheets.Add(After:=in_objWorkbook.Sheets(in_objWorkbook.Sheets.Count))
        wsReacciones.Name = "Reacciones"
        Debug.Print "reacciones: Hoja 'Reacciones' creada."
    Else
        On Error GoTo ReaccionesErrorHandler
        in_objExcel.DisplayAlerts = False ' Desactivar alertas temporalmente
        wsReacciones.Cells.ClearContents ' Limpiar contenido si ya existe
        in_objExcel.DisplayAlerts = True ' Reactivar alertas
        Debug.Print "reacciones: Hoja 'Reacciones' encontrada y limpiada."
    End If
    Debug.Print "reacciones: Hoja 'Reacciones' preparada."

    ' Escribir encabezados con unidades
    wsReacciones.Range("A1:I1").Value = Array("Nodo", "Caso", "FX (kN)", "FY (kN)", "FZ (kN)", "MX (kN-m)", "MY (kN-m)", "MZ (kN-m)", "Componente Crítico")
    wsReacciones.Range("A1:I1").Font.Bold = True
    rowIndex = 2

    ' 5. Obtener todos los casos de carga primarios
    Debug.Print "reacciones: Obteniendo todos los casos de carga primarios de STAAD.Pro..."
    lPrimaryLoadCaseCount = in_objOpenSTAAD.Load.GetPrimaryLoadCaseCount()

    If lPrimaryLoadCaseCount = 0 Then
        MsgBox "No se encontraron casos de carga primarios en el modelo STAAD.Pro.", vbExclamation, "No Hay Casos de Carga"
        Debug.Print "reacciones: Advertencia: No se encontraron casos de carga primarios en STAAD.Pro."
        GoTo ReaccionesCleanup
    End If

    ReDim lPrimaryLoadCaseIDs(0 To lPrimaryLoadCaseCount - 1)
    in_objOpenSTAAD.Load.GetPrimaryLoadCaseNumbers lPrimaryLoadCaseIDs

    ' Ordenar los casos de carga primarios
    If UBound(lPrimaryLoadCaseIDs) >= LBound(lPrimaryLoadCaseIDs) Then
        Call QuickSortLong(lPrimaryLoadCaseIDs, LBound(lPrimaryLoadCaseIDs), UBound(lPrimaryLoadCaseIDs))
    End If
    Debug.Print "reacciones: " & lPrimaryLoadCaseCount & " casos de carga primarios obtenidos y ordenados."

    ' 6. Iterar a través de cada nodo soportado y cada caso de carga primario
    Debug.Print "reacciones: Iniciando iteración para obtener reacciones..."
    For i = LBound(nodosSoporte) To UBound(nodosSoporte)
        nodeID = nodosSoporte(i)

        For j = LBound(lPrimaryLoadCaseIDs) To UBound(lPrimaryLoadCaseIDs)
            loadCaseID = lPrimaryLoadCaseIDs(j)

            ' Desactivar temporalmente el manejo de errores para esta llamada específica
            On Error Resume Next
            RetVal = in_objOpenSTAAD.Output.GetSupportReactions(nodeID, loadCaseID, dReactionArray)

            ' Verificar si ocurrió un error después de la llamada a la API de STAAD
            If Err.Number <> 0 Then
                Debug.Print "reacciones: !!! ADVERTENCIA DE ERROR !!! No se pudieron obtener reacciones para el Nodo " & nodeID & ", Caso de Carga " & loadCaseID & ". Error: " & Err.Description & " (" & Err.Number & ")"
                Err.Clear ' Limpiar el error para que no afecte la siguiente iteración
                RetVal = False ' Forzar RetVal a False para que no se intente escribir datos incorrectos
            End If
            ' Volver a habilitar el manejo general de errores
            On Error GoTo ReaccionesErrorHandler

            If RetVal = True Then
                ' Verificar si algún componente de reacción no es cero
                hasNonZeroReaction = False
                For k = 0 To 5
                    If Abs(dReactionArray(k)) > 0.000001 Then ' Usando un pequeño épsilon para comparación de punto flotante
                        hasNonZeroReaction = True
                        Exit For
                    End If
                Next k

                If hasNonZeroReaction Then ' Solo escribir si hay al menos una reacción no nula
                    maxAbsValueForCurrentCase = 0
                    criticalComponentForCurrentCase = ""

                    For k = 0 To 5 ' Iterar a través de los componentes de reacción
                        If Abs(dReactionArray(k)) > Abs(maxAbsValueForCurrentCase) Then
                            maxAbsValueForCurrentCase = dReactionArray(k)
                            criticalComponentForCurrentCase = componentes(k)
                        End If
                    Next k

                    With wsReacciones
                        .Cells(rowIndex, 1).Value = nodeID
                        .Cells(rowIndex, 2).Value = loadCaseID
                        .Cells(rowIndex, 3).Value = Format(dReactionArray(0), "0.00") ' FX
                        .Cells(rowIndex, 4).Value = Format(dReactionArray(1), "0.00") ' FY
                        .Cells(rowIndex, 5).Value = Format(dReactionArray(2), "0.00") ' FZ
                        .Cells(rowIndex, 6).Value = Format(dReactionArray(3), "0.00") ' MX
                        .Cells(rowIndex, 7).Value = Format(dReactionArray(4), "0.00") ' MY
                        .Cells(rowIndex, 8).Value = Format(dReactionArray(5), "0.00") ' MZ
                        .Cells(rowIndex, 9).Value = criticalComponentForCurrentCase
                    End With
                    rowIndex = rowIndex + 1
                Else
                    Debug.Print "reacciones: Nodo " & nodeID & ", Caso de Carga " & loadCaseID & ": Todas las reacciones son cero. Omitiendo la escritura en Excel."
                End If
            Else
                ' Este bloque se ejecutará si RetVal es Falso (ya sea por el error o por el manejo de errores explícito)
                ' No se necesita MsgBox aquí, ya que Debug.Print ya registra el problema.
            End If
        Next j
    Next i
    Debug.Print "reacciones: Extracción de reacciones completada."

    wsReacciones.Columns.AutoFit

ReaccionesCleanup:
    Debug.Print "reacciones: Limpiando recursos específicos de 'reacciones'..."
    Set wsReacciones = Nothing
    Set wsSoporte = Nothing
    Debug.Print "reacciones: Limpieza completada. Saliendo de 'reacciones'."
    Exit Sub

ReaccionesErrorHandler:
    MsgBox "Ocurrió un error en la subrutina 'reacciones':" & vbCrLf & _
           "Número de Error: " & Err.Number & vbCrLf & _
           "Descripción: " & Err.Description, vbCritical, "Error de Reacciones"
    Debug.Print "reacciones: Error en ReaccionesErrorHandler: " & Err.Description & " (" & Err.Number & ")"
    Resume ReaccionesCleanup
End Sub


'***********************************************************************************************************************************************************************************************************************************************************************************
'***********************************************************************************************************************************************************************************************************************************************************************************

' **************************************************************************************************
' *** FUNCIONES Y SUBRUTINAS AUXILIARES                                                          ***
' **************************************************************************************************

Private Function InitializeApplications() As Boolean
    On Error GoTo InitErrorHandler
    InitializeApplications = False ' Asumir fallo inicialmente

    ' --- 1. Conectar a OpenSTAAD ---
    Debug.Print "DEBUG: Intentando conectar a OpenSTAAD..."
    On Error Resume Next ' Para capturar errores en la conexión GetObject/CreateObject
    Set g_objOpenSTAAD = GetObject(, "StaadPro.OpenSTAAD")
    If Err.Number <> 0 Then ' Si GetObject falla (STAAD no abierto o no registrado)
        Debug.Print "DEBUG: GetObject falló (" & Err.Description & "). Intentando CreateObject..."
        Err.Clear
        Set g_objOpenSTAAD = CreateObject("StaadPro.OpenSTAAD")
    End If
    On Error GoTo InitErrorHandler ' Restaurar manejo de errores

    If g_objOpenSTAAD Is Nothing Then
        MsgBox "Error: No se pudo conectar con la instancia de OpenSTAAD. Asegúrese de que STAAD.Pro esté instalado y abierto.", vbCritical, "Error de Conexión STAAD"
        Exit Function
    End If
    Debug.Print "DEBUG: Conexión exitosa a OpenSTAAD."

    ' Verificar si hay un archivo STAAD abierto
    Dim stdFileLocal As String ' Usar una variable local para el retorno de GetSTAADFile
    On Error Resume Next ' Para manejar posibles errores si GetSTAADFile() falla
    g_objOpenSTAAD.GetSTAADFile stdFileLocal, "TRUE"
    If Err.Number <> 0 Then
        Debug.Print "ERROR: Falló GetSTAADFile: " & Err.Description & " (" & Err.Number & ")"
        Err.Clear
        stdFileLocal = ""
    End If
    On Error GoTo InitErrorHandler ' Restaurar el manejador de errores

    If stdFileLocal = "" Then
        MsgBox "Error: No se pudo obtener la ruta del archivo STAAD.Pro. Asegúrese de que un modelo esté abierto y guardado en STAAD.Pro.", vbCritical, "Error de Archivo STAAD"
        Exit Function
    End If



    Dim staadDir As String



    ' --- 2. Conectar a Excel ---
    Debug.Print "DEBUG: Intentando conectar a Excel..."
    On Error Resume Next ' Intentar GetObject primero
    Set g_objExcel = GetObject(, "Excel.Application")
    On Error GoTo InitErrorHandler ' Restaurar manejo de errores

    If g_objExcel Is Nothing Then
        ' Si no hay instancia de Excel abierta, crear una nueva
        Set g_objExcel = CreateObject("Excel.Application")
        If g_objExcel Is Nothing Then
            MsgBox "Error: No se pudo iniciar una nueva instancia de Excel.", vbCritical, "Error de Excel"
            Exit Function
        End If
    End If

    ' Configurar Excel para que se ejecute en segundo plano y sin alertas
    g_objExcel.Visible = False
    g_objExcel.DisplayAlerts = False ' Desactivar alertas para evitar interrupciones
    Debug.Print "DEBUG: Excel configurado para segundo plano (Visible=False, DisplayAlerts=False)."

    ' --- 3. Abrir o crear el libro de trabajo de Excel ---

    Dim fso As Object
    Set fso = CreateObject("Scripting.FileSystemObject")

    Dim foundWorkbook As Boolean
    foundWorkbook = False
    For Each g_objWorkbook In g_objExcel.Workbooks

    Next g_objWorkbook

    If Not foundWorkbook Then
       
    End If

    If g_objWorkbook Is Nothing Then
        MsgBox "ERROR CRÍTICO: No se pudo obtener el libro de trabajo de Excel. La macro no puede continuar.", vbCritical, "Error de Libro de Trabajo"
        Exit Function
    End If

    InitializeApplications = True ' Indicar éxito
    Exit Function

InitErrorHandler:
    MsgBox "Se produjo un error durante la inicialización de aplicaciones: " & Err.Description & " (Número: " & Err.Number & ").", vbCritical, "Error de Inicialización"
    InitializeApplications = False
End Function

Private Sub QuickSortLong(arr() As Long, L As Long, R As Long)
    Dim i As Long, j As Long, pivot As Long, temp As Long
    i = L: j = R
    pivot = arr((L + R) \ 2)

    Do While arr(i) < pivot
        i = i + 1
    Loop
    Do While arr(j) > pivot
        j = j - 1
    Loop

    If i <= j Then
        temp = arr(i)
        arr(i) = arr(j)
        arr(j) = temp
        i = i + 1
        j = j - 1
    End If

    If L < j Then QuickSortLong arr, L, j
    If i < R Then QuickSortLong arr, i, R
End Sub

Function GetSupportTypeName(ByVal SupportTypeCode As Long) As String
    Select Case SupportTypeCode
        Case 0
            GetSupportTypeName = "Sin soporte"
        Case 1
            GetSupportTypeName = "Soporte articulado"
        Case 2
            GetSupportTypeName = "Soporte fijo"
        Case 3
            GetSupportTypeName = "Soporte fijo con liberaciones"
        Case 4
            GetSupportTypeName = "Soporte impuesto"
        Case 5
            GetSupportTypeName = "Soporte impuesto con liberaciones"
        Case 6
            GetSupportTypeName = "Soporte inclinado"
        Case 7
            GetSupportTypeName = "Cimentación por zapatas"
        Case 8
            GetSupportTypeName = "Cimentación elástica de losa"
        Case 9
            GetSupportTypeName = "Cimentación de losa"
        Case 10
            GetSupportTypeName = "Soporte de resorte multi-lineal"
        Case 11
            GetSupportTypeName = "Soporte articulado generado"
        Case 12
            GetSupportTypeName = "Soporte fijo generado"
        Case 13
            GetSupportTypeName = "Soporte fijo generado con liberaciones"
        Case -1
            GetSupportTypeName = "Error general / Tipo desconocido"
        Case Else
            GetSupportTypeName = "Código de Tipo Desconocido (" & SupportTypeCode & ")"
    End Select
End Function
'***********************************************************************************************************************************************************************************************************************************************************************************
'***********************************************************************************************************************************************************************************************************************************************************************************

Sub Vistas() ' Nombre de la subrutina principal

    ' Declaración de variables
    Dim objOpenSTAAD As Object   ' Objeto principal de OpenSTAAD
    Dim stdFilePath As String    ' Ruta completa del archivo .STD
    Dim modelDirectory As String ' Directorio donde se encuentra el modelo (.STD)
    Dim modelBaseName As String  ' Nombre del modelo sin extensión (para el nombre de la carpeta)
    Dim imageFolderPath As String ' Ruta de la carpeta de destino para imágenes
    Dim fileName As String       ' Nombre del archivo de imagen (sin extensión)
    Dim fileExtension As String  ' Extensión de la imagen a guardar
    Dim fileFormat As Long       ' Formato de la imagen (1 para JPG)
    Dim overwrite As Boolean     ' Si se permite sobrescribir un archivo existente
    Dim exportResult As Long     ' Resultado de la exportación de la imagen
    Dim fso As Object            ' Objeto FileSystemObject para manipulación de carpetas
    Dim fullImagePath As String  ' Ruta completa del archivo de imagen (incluyendo nombre y extensión)

    ' --- Inicio del proceso ---
    Debug.Print "DEBUG: Iniciando la macro para generar múltiples vistas y exportar imágenes de STAAD.Pro (Optimización Agresiva)."

    ' Obtener el objeto OpenSTAAD
    On Error GoTo ErrorHandler
    Set objOpenSTAAD = GetObject(, "StaadPro.OpenSTAAD")
    Debug.Print "DEBUG: Objeto OpenSTAAD obtenido exitosamente."

    If objOpenSTAAD Is Nothing Then
        MsgBox "No se pudo conectar con STAAD.Pro. Asegúrese de que STAAD.Pro esté abierto y un modelo cargado.", vbCritical, "Error de Conexión"
        GoTo CleanUp
    End If

    ' Obtener la ruta completa del archivo STAAD.Pro abierto
    objOpenSTAAD.GetSTAADFile stdFilePath, "TRUE"
    Debug.Print "DEBUG: Ruta del archivo STAAD.Pro: " & stdFilePath

    If stdFilePath = "" Then
        MsgBox "No se pudo obtener la ruta del archivo STAAD.Pro. No se pueden exportar las imágenes.", vbExclamation, "Error de Exportación"
        GoTo CleanUp
    End If

    ' Crear objeto FileSystemObject
    Set fso = CreateObject("Scripting.FileSystemObject")

    ' Extraer el directorio donde se encuentra el archivo .STD
    modelDirectory = fso.GetParentFolderName(stdFilePath) & "\"

    ' Extraer el nombre del modelo sin extensión para la nueva carpeta
    modelBaseName = fso.GetBaseName(stdFilePath)
    Debug.Print "DEBUG: Nombre base del modelo: " & modelBaseName

    ' Definir la ruta de la nueva carpeta que se llama igual que el modelo
    imageFolderPath = modelDirectory & modelBaseName & "\"
    
    ' Verificar si la carpeta existe y crearla si no
    If Not fso.FolderExists(imageFolderPath) Then
        fso.CreateFolder imageFolderPath
        Debug.Print "DEBUG: Carpeta '" & modelBaseName & "' creada en: " & imageFolderPath
    Else
        Debug.Print "DEBUG: Carpeta '" & modelBaseName & "' ya existe en: " & imageFolderPath
    End If

    fileFormat = 1 ' 1 para JPG (JPEG)
    fileExtension = ".jpg" ' Definir la extensión para los mensajes y nombres de archivo
    overwrite = True ' Permitir sobrescribir los archivos existentes


    ' --- Subrutina para limpiar y configurar la vista ---
    ' Esta subrutina se llamará antes de cada exportación de imagen para asegurar un estado de vista base.
    Call ClearAndSetBaseView(objOpenSTAAD)


    ' ======================================================
    ' --- 1. Exportar Imagen: Isometría 3D (Secciones Completas y Soportes) ---
    ' ======================================================
    Debug.Print "DEBUG: --- Configurando vista para 'Isometría 3D' ---"
    objOpenSTAAD.View.ShowIsometric      ' Cambiar a vista isométrica (sin parámetros)
    objOpenSTAAD.View.SetDiagramMode 9, True, True ' Activar 'Secciones Completas' (3D Sections)
    objOpenSTAAD.View.SetLabel 4, True   ' Activar Soportes (ID 4)
    Debug.Print "DEBUG: Esperando 50ms para que la vista 'Isometría 3D' se actualice antes de exportar."
    Sleep 50 ' PAUSA OPTIMIZADA: Esperar a que la vista se actualice
    
    fileName = "Isometría 3D"
    fullImagePath = imageFolderPath & fileName & fileExtension
    Call ExportImage(objOpenSTAAD, fso, fullImagePath, imageFolderPath, fileName, fileFormat, overwrite)
    Debug.Print "DEBUG: Imagen 'Isometría 3D' procesada."
    Call ClearAndSetBaseView(objOpenSTAAD) ' Limpiar para la siguiente vista


    ' ======================================================
    ' --- 2. Exportar Imagen: Nodos (IDs de Nodos y Soportes) ---
    ' ======================================================
    Debug.Print "DEBUG: --- Configurando vista para 'Nodos' ---"
    objOpenSTAAD.View.SetLabel 0, True   ' Activar IDs de Nodos (ID 0)
    objOpenSTAAD.View.SetLabel 4, True   ' Activar Soportes (ID 4)
    Debug.Print "DEBUG: Esperando 50ms para que la vista 'Nodos' se actualice antes de exportar."
    Sleep 50 ' PAUSA OPTIMIZADA: Esperar a que la vista se actualice

    fileName = "Nodos"
    fullImagePath = imageFolderPath & fileName & fileExtension
    Call ExportImage(objOpenSTAAD, fso, fullImagePath, imageFolderPath, fileName, fileFormat, overwrite)
    Debug.Print "DEBUG: Imagen 'Nodos' procesada."
    Call ClearAndSetBaseView(objOpenSTAAD) ' Limpiar para la siguiente vista


    ' ======================================================
    ' --- 3. Exportar Imagen: Vigas (IDs de Vigas y Soportes) ---
    ' ======================================================
    Debug.Print "DEBUG: --- Configurando vista para 'Vigas' ---"
    objOpenSTAAD.View.SetLabel 1, True   ' Activar IDs de Vigas (ID 1)
    objOpenSTAAD.View.SetLabel 4, True   ' Activar Soportes (ID 4)
    Debug.Print "DEBUG: Esperando 50ms para que la vista 'Vigas' se actualice antes de exportar."
    Sleep 50 ' PAUSA OPTIMIZADA: Esperar a que la vista se actualice

    fileName = "Vigas"
    fullImagePath = imageFolderPath & fileName & fileExtension
    Call ExportImage(objOpenSTAAD, fso, fullImagePath, imageFolderPath, fileName, fileFormat, overwrite)
    Debug.Print "DEBUG: Imagen 'Vigas' procesada."
    Call ClearAndSetBaseView(objOpenSTAAD) ' Limpiar para la siguiente vista


    ' ======================================================
    ' --- 4. Exportar Imagen: Perfiles (Etiquetas de Sección de Miembros y Soportes) ---
    ' ======================================================
    Debug.Print "DEBUG: --- Configurando vista para 'Perfiles' ---"
    objOpenSTAAD.View.SetLabel 7, True   ' Activar Etiquetas de Sección de Miembros (Perfiles) (ID 7)
    objOpenSTAAD.View.SetLabel 4, True   ' Activar Soportes (ID 4)
    Debug.Print "DEBUG: Esperando 50ms para que la vista 'Perfiles' se actualice."
    Sleep 50 ' PAUSA OPTIMIZADA: Esperar a que la vista se actualice

    fileName = "Perfiles"
    fullImagePath = imageFolderPath & fileName & fileExtension
    Call ExportImage(objOpenSTAAD, fso, fullImagePath, imageFolderPath, fileName, fileFormat, overwrite)
    Debug.Print "DEBUG: Imagen 'Perfiles' procesada."
    Call ClearAndSetBaseView(objOpenSTAAD) ' Limpiar para la siguiente vista


    ' ======================================================
    ' --- 5. Exportar Imagen: Dimensiones (Dimensiones y Soportes) ---
    ' ======================================================
    Debug.Print "DEBUG: --- Configurando vista para 'Dimensiones' ---"
    objOpenSTAAD.View.SetLabel 16, True  ' Activar Dimensiones (ID 16)
    objOpenSTAAD.View.SetLabel 4, True   ' Activar Soportes (ID 4)
    Debug.Print "DEBUG: Esperando 50ms para que la vista 'Dimensiones' se actualice."
    Sleep 50 ' PAUSA OPTIMIZADA: Esperar a que la vista se actualice

    fileName = "Dimensiones"
    fullImagePath = imageFolderPath & fileName & fileExtension
    Call ExportImage(objOpenSTAAD, fso, fullImagePath, imageFolderPath, fileName, fileFormat, overwrite)
    Debug.Print "DEBUG: Imagen 'Dimensiones' procesada."
    ' No se necesita ClearAndSetBaseView aquí, ya que es la última imagen.

    'MsgBox "Todas las vistas y exportaciones de imágenes se han completado exitosamente en la carpeta: " & vbCrLf & imageFolderPath, _
           'vbInformation, "Proceso Completado del Reporte Gráfico"

CleanUp:
    ' Asegurarse de liberar objetos al finalizar
    Set objOpenSTAAD = Nothing
    If Not fso Is Nothing Then Set fso = Nothing
    Debug.Print "DEBUG: Objetos liberados. Fin de la macro principal."
    Exit Sub

ErrorHandler:
    MsgBox "Ha ocurrido un error en la macro principal: " & Err.Description & " (Número: " & Err.Number & ").", vbCritical, "Error en la Macro"
    GoTo CleanUp
End Sub


' --- Subrutina para limpiar las configuraciones de vista y establecer una base ---
Sub ClearAndSetBaseView(ByRef staadObj As Object)
    Debug.Print "DEBUG: Iniciando limpieza profunda de la vista."
    
    ' PRIMERO: ZoomAll y ShowAllMembers para establecer una vista base para el estado visual.
    Debug.Print "DEBUG: Ejecutando ZoomAll."
    staadObj.View.ZoomAll
    Sleep 30 ' Darle un momento a STAAD para aplicar el zoom

    Debug.Print "DEBUG: Ejecutando ShowAllMembers."
    staadObj.View.ShowAllMembers
    Sleep 30 ' Darle un momento a STAAD para aplicar mostrar todos los miembros

    On Error Resume Next ' Activar manejo de errores para depurar cada SetLabel/SetDiagramMode

    ' Desactivar todas las etiquetas y modos de diagrama conocidos que podríamos haber activado
    Debug.Print "DEBUG: Desactivando SetDiagramMode 9 (Secciones Completas)."
    staadObj.View.SetDiagramMode 9, False, True 
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetDiagramMode 9: " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 0 (IDs de Nodos)."
    staadObj.View.SetLabel 0, False             
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 0 (Nodos): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 1 (IDs de Miembros/Vigas)."
    staadObj.View.SetLabel 1, False             
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 1 (Vigas/Miembros): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 3 (IDs de Cargas)."
    staadObj.View.SetLabel 3, False             
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 3 (Cargas): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 4 (Soportes)."
    staadObj.View.SetLabel 4, False             
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 4 (Soportes): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 7 (Perfiles/Secciones de Miembros)."
    staadObj.View.SetLabel 7, False             
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 7 (Perfiles): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 16 (Dimensiones)."
    staadObj.View.SetLabel 16, False            
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 16 (Dimensiones): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    Debug.Print "DEBUG: Desactivando SetLabel 52 (IDs de Miembros Físicos)."
    staadObj.View.SetLabel 52, False            
    If Err.Number <> 0 Then Debug.Print "ERROR al desactivar SetLabel 52 (Miembros Físicos): " & Err.Description & " (" & Err.Number & ")": Err.Clear
    Sleep 30 ' Pausa después de cada desactivación

    On Error GoTo 0 ' Desactivar manejo de errores locales

    Debug.Print "DEBUG: Limpieza profunda de vista completada. Lista para la próxima configuración."
End Sub

' --- Subrutina para exportar una imagen ---
Sub ExportImage(ByRef staadObj As Object, ByRef fsoObj As Object, ByVal imagePath As String, ByVal folderPath As String, ByVal imgName As String, ByVal imgFormat As Long, ByVal overwriteFlag As Boolean)
    Debug.Print "DEBUG: Exportando imagen: " & imagePath

    ' Eliminar la imagen existente si ya existe
    If fsoObj.FileExists(imagePath) Then
        On Error Resume Next ' Permitir que la eliminación falle sin detener la macro
        fsoObj.DeleteFile imagePath, True ' True para forzar la eliminación
        If Err.Number <> 0 Then
            Debug.Print "ADVERTENCIA: No se pudo eliminar el archivo existente '" & imagePath & "'. Error: " & Err.Description
            Err.Clear
            MsgBox "Advertencia: No se pudo eliminar la imagen existente '" & imgName & "'. Intente cerrarla si está abierta y vuelva a ejecutar.", vbExclamation, "Problema al Eliminar Imagen"
        Else
            Debug.Print "DEBUG: Imagen existente eliminada: " & imagePath
        End If
        ' No necesitamos un GoTo aquí. Los errores subsiguientes serán manejados por el ErrorHandler general de Main.
    Else
        Debug.Print "DEBUG: No se encontró una imagen existente con el nombre '" & imgName & "'. Procediendo a guardar."
    End If

    ' Llamar a la función ExportView
    Dim exportResult As Long
    On Error GoTo ExportImageErrorHandler ' Manejador de errores local para esta subrutina
    exportResult = staadObj.View.ExportView(folderPath, imgName, imgFormat, overwriteFlag)

    If exportResult = 1 Then
        Debug.Print "DEBUG: Imagen exportada exitosamente a: " & imagePath
    Else
        ' Si exportResult no es 1, significa que la exportación falló sin un error VBA.
        Debug.Print "ERROR: Falló la exportación de la imagen '" & imgName & "'. Código de error de ExportView: " & exportResult
        MsgBox "Error: Falló la exportación de la imagen '" & imgName & "'. Código: " & exportResult & ". Verifique permisos.", vbCritical, "Error de Exportación"
    End If
    Exit Sub ' Salir de la subrutina de exportación

ExportImageErrorHandler: ' Manejador de errores específico para ExportImage
    Debug.Print "ERROR inesperado en ExportImage para '" & imgName & "': " & Err.Description & " (Número: " & Err.Number & ")"
    MsgBox "Error inesperado al exportar la imagen '" & imgName & "': " & Err.Description & " (Número: " & Err.Number & ")", vbCritical, "Error de Exportación"
    Resume Next ' Continúa después del error (saldrá de la subrutina).
End Sub
'===============================================================================================================================
' --- SECCIÓN DE FUNCIONES AUXILIARES (HELPERS) ---
' ... (Añadir estas dos nuevas funciones a esta sección) ...
'===============================================================================================================================

'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetNumericCellValue
' Propósito: Obtiene un valor numérico de una celda de forma segura. Si la celda está vacía,
'            contiene texto o un error, devuelve un valor por defecto.
' Parámetros:
'   wb (Object): El libro de trabajo.
'   sheetName (String): El nombre de la hoja.
'   cellAddress (String): La dirección de la celda.
'   defaultValue (Double): El valor a devolver si la celda no es numérica.
' Retorna: Double - El valor numérico de la celda o el valor por defecto.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetNumericCellValue(ByVal wb As Object, ByVal sheetName As String, ByVal cellAddress As String, ByVal defaultValue As Double) As Double
    Dim cellValue As Variant
    cellValue = GetCellValue(wb, sheetName, cellAddress)
    
    If IsNumeric(cellValue) And Not IsEmpty(cellValue) Then
        GetNumericCellValue = CDbl(cellValue)
    Else
        GetNumericCellValue = defaultValue
        Debug.Print "ADVERTENCIA: Valor no numérico en '" & sheetName & "'!" & cellAddress & ". Usando valor por defecto: " & defaultValue
    End If
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: PreloadDesignParameters (Versión 4 - Con Factores de Modificación Sísmica)
' Propósito: Lee TODOS los coeficientes y factores de diseño desde las hojas de configuración
'            de Excel y los carga en variables globales. Se ejecuta una sola vez.
'-------------------------------------------------------------------------------------------------------------------------------
Sub PreloadDesignParameters(ByVal wb As Object)
    Debug.Print "--- Iniciando precarga de parámetros de diseño ---"
    
    ' Hoja "Acero" - El valor por defecto 0 indica que si no se encuentra, no se aplicará verificación.
    g_VigasTechos_Tipo1 = GetNumericCellValue(wb, "Acero", "D6", 0)
    g_VigasTechos_Tipo2 = GetNumericCellValue(wb, "Acero", "E6", 0)
    g_VigasTechos_Tipo3 = GetNumericCellValue(wb, "Acero", "F6", 0)
    
    g_VigasCorreas_Tipo1 = GetNumericCellValue(wb, "Acero", "D7", 0)
    g_VigasCorreas_Tipo2 = GetNumericCellValue(wb, "Acero", "E7", 0)
    g_VigasCorreas_Tipo3 = GetNumericCellValue(wb, "Acero", "F7", 0)
    
    g_VigasPrin_Tipo1 = GetNumericCellValue(wb, "Acero", "D8", 0)
    g_VigasPrin_Tipo2 = GetNumericCellValue(wb, "Acero", "E8", 0)
    g_VigasPrin_Tipo3 = GetNumericCellValue(wb, "Acero", "F8", 0)
    
    g_VigasSec_Tipo1 = GetNumericCellValue(wb, "Acero", "D9", 0)
    g_VigasSec_Tipo2 = GetNumericCellValue(wb, "Acero", "E9", 0)
    g_VigasSec_Tipo3 = GetNumericCellValue(wb, "Acero", "F9", 0)
    
    g_VigasVoladizo_Tipo1 = GetNumericCellValue(wb, "Acero", "D10", 0)
    g_VigasVoladizo_Tipo2 = GetNumericCellValue(wb, "Acero", "E10", 0)
    g_VigasVoladizo_Tipo3 = GetNumericCellValue(wb, "Acero", "F10", 0)
    
    g_ArriostHoriz_Tipo1 = GetNumericCellValue(wb, "Acero", "D11", 0)
    g_ArriostHoriz_Tipo2 = GetNumericCellValue(wb, "Acero", "E11", 0)
    g_ArriostHoriz_Tipo3 = GetNumericCellValue(wb, "Acero", "F11", 0)
    
    ' Hoja "Otros"
    g_VigaCarrilTR_Tipo4 = GetNumericCellValue(wb, "Otros", "C5", 0)
    g_VigaCarrilUR_Tipo4 = GetNumericCellValue(wb, "Otros", "C6", 0)
    g_Monorriel_Tipo4 = GetNumericCellValue(wb, "Otros", "C7", 0)
    g_PuenteGrua_Tipo4 = GetNumericCellValue(wb, "Otros", "C8", 0)
    
    ' Hoja "Rangos" - El valor por defecto 1 es para evitar divisiones por cero si no se especifica.
    g_FactorVientoServicio = GetNumericCellValue(wb, "Rangos", "F6", 1)
    g_FactorVientoUltimas = GetNumericCellValue(wb, "Rangos", "F9", 1)
    g_FactorSismoServicio = GetNumericCellValue(wb, "Rangos", "G6", 1)
    g_FactorSismoUltimas = GetNumericCellValue(wb, "Rangos", "G9", 1)
    
    ' Nuevos factores de modificación de desplazamiento por Sismo. El valor por defecto es 1 (sin modificación).
    g_FactorSismoModServicioX = GetNumericCellValue(wb, "Rangos", "H6", 1)
    g_FactorSismoModServicioZ = GetNumericCellValue(wb, "Rangos", "I6", 1)
    g_FactorSismoModUltimasX = GetNumericCellValue(wb, "Rangos", "H9", 1)
    g_FactorSismoModUltimasZ = GetNumericCellValue(wb, "Rangos", "I9", 1)
    
    Debug.Print "--- Precarga de parámetros de diseño completada ---"
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: ConsolidateColumnDisplacementsFromArray (VERSIÓN OPTIMIZADA)
' Propósito: Genera el informe de derivas leyendo desde el array de resultados en memoria.
'-------------------------------------------------------------------------------------------------------------------------------
Sub ConsolidateColumnDisplacementsFromArray(ByRef dataArray As Variant, ByVal wsTarget As Object, ByVal group1 As String, ByVal group2 As String, ByVal envelopeTypeToProcess As String)
    On Error GoTo ConsolidateErrorHandler
    
    Dim consolidatedColumnDataDict As Object
    Set consolidatedColumnDataDict = CreateObject("Scripting.Dictionary")
    
    Dim i As Long, key As String
    Dim memberOutput As Variant
    
    ' Iterar sobre el array en memoria
    For i = 1 To UBound(dataArray, 1)
        If UCase(CStr(dataArray(i, 6))) = UCase(envelopeTypeToProcess) And (UCase(CStr(dataArray(i, 3))) = UCase(group1) Or UCase(CStr(dataArray(i, 3))) = UCase(group2)) Then
            If dataArray(i, 2) <> 0 Then key = "PM_" & dataArray(i, 2) Else key = "AM_" & dataArray(i, 1)
            
            If Not consolidatedColumnDataDict.Exists(key) Then
                ReDim memberOutput(0 To 17)
                memberOutput(0) = dataArray(i, 2): memberOutput(1) = dataArray(i, 1)
                memberOutput(2) = dataArray(i, 35): memberOutput(3) = dataArray(i, 32): memberOutput(4) = dataArray(i, 31): memberOutput(5) = dataArray(i, 34)
                memberOutput(6) = dataArray(i, 36): memberOutput(7) = dataArray(i, 37): memberOutput(8) = dataArray(i, 38): memberOutput(9) = dataArray(i, 39)
                memberOutput(10) = dataArray(i, 44): memberOutput(11) = dataArray(i, 41): memberOutput(12) = dataArray(i, 40): memberOutput(13) = dataArray(i, 43)
                memberOutput(14) = dataArray(i, 45): memberOutput(15) = dataArray(i, 46): memberOutput(16) = dataArray(i, 47): memberOutput(17) = dataArray(i, 48)
                consolidatedColumnDataDict.Add key, memberOutput
            Else
                memberOutput = consolidatedColumnDataDict.Item(key)
                If CDbl(dataArray(i, 39)) > CDbl(memberOutput(9)) Then ' Compara Ratio DX
                    memberOutput(2) = dataArray(i, 35): memberOutput(3) = dataArray(i, 32): memberOutput(4) = dataArray(i, 31): memberOutput(5) = dataArray(i, 34)
                    memberOutput(6) = dataArray(i, 36): memberOutput(7) = dataArray(i, 37): memberOutput(8) = dataArray(i, 38): memberOutput(9) = dataArray(i, 39)
                End If
                If CDbl(dataArray(i, 48)) > CDbl(memberOutput(17)) Then ' Compara Ratio DZ
                    memberOutput(10) = dataArray(i, 44): memberOutput(11) = dataArray(i, 41): memberOutput(12) = dataArray(i, 40): memberOutput(13) = dataArray(i, 43)
                    memberOutput(14) = dataArray(i, 45): memberOutput(15) = dataArray(i, 46): memberOutput(16) = dataArray(i, 47): memberOutput(17) = dataArray(i, 48)
                End If
                consolidatedColumnDataDict.Item(key) = memberOutput
            End If
        End If
    Next i
    
    ' Preparar hoja de destino
    Dim headersTarget As Variant
    headersTarget = Array("Physical Member ID", "Analytical Member ID", "Longitud DX (m)", "Caso de Carga Crit. DX", "Max DX (mm)", "Nodo Crit. DX", "Factor", "Deflexión Permisible DX", "Cumple Norma DX", "Ratio DX", "Longitud DZ (m)", "Caso de Carga Crit. DZ", "Max DZ (mm)", "Nodo Crit. DZ", "Factor", "Deflexión Permisible DZ", "Cumple Norma DZ", "Ratio DZ")
    wsTarget.Cells.ClearContents
    wsTarget.Range("A1").Resize(1, UBound(headersTarget) + 1).Value = headersTarget
    wsTarget.Range("A1").Resize(1, UBound(headersTarget) + 1).Font.Bold = True

    ' Escribir resultados consolidados en bloque
    If consolidatedColumnDataDict.Count > 0 Then
        Dim consolidatedArray() As Variant
        ReDim consolidatedArray(1 To consolidatedColumnDataDict.Count, 1 To 18)
        Dim count As Long
        count = 0
        For Each key In consolidatedColumnDataDict.Keys
            count = count + 1
            memberOutput = consolidatedColumnDataDict.Item(key)
            If Left(key, 3) = "PM_" Then consolidatedArray(count, 1) = Mid(key, 4) Else consolidatedArray(count, 2) = Mid(key, 4)
            consolidatedArray(count, 3) = memberOutput(2): consolidatedArray(count, 4) = memberOutput(3): consolidatedArray(count, 5) = memberOutput(4): consolidatedArray(count, 6) = memberOutput(5)
            consolidatedArray(count, 7) = memberOutput(6): consolidatedArray(count, 8) = memberOutput(7): consolidatedArray(count, 9) = memberOutput(8): consolidatedArray(count, 10) = memberOutput(9)
            consolidatedArray(count, 11) = memberOutput(10): consolidatedArray(count, 12) = memberOutput(11): consolidatedArray(count, 13) = memberOutput(12): consolidatedArray(count, 14) = memberOutput(13)
            consolidatedArray(count, 15) = memberOutput(14): consolidatedArray(count, 16) = memberOutput(15): consolidatedArray(count, 17) = memberOutput(16): consolidatedArray(count, 18) = memberOutput(17)
        Next key
        wsTarget.Range("A2").Resize(count, 18).Value = consolidatedArray
        wsTarget.Range("A2:R" & count + 1).Sort Key1:=wsTarget.Range("A2"), Order1:=xlAscending, Key2:=wsTarget.Range("B2"), Order2:=xlAscending, Header:=xlNo
        wsTarget.Columns.AutoFit
    End If
    
    Exit Sub
ConsolidateErrorHandler:
    MsgBox "Error en ConsolidateColumnDisplacementsFromArray: " & Err.Description, vbCritical
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: GetMaxLocalDeflectionFromPoints (VERSIÓN OPTIMIZADA V8.1)
' MEJORA 1: Usa GetMaxMemberDeflection (1 llamada vs 13)
' MEJORA 2: Calcula deflexión RELATIVA respecto a la cuerda
'-------------------------------------------------------------------------------------------------------------------------------
Sub GetMaxLocalDeflectionFromPoints(ByVal memberID As Long, _
                                     ByVal loadCaseID As Long, _
                                     ByVal memberLength As Double, _
                                     ByVal conversionFactorToMM As Double, _
                                     ByVal objOutput As Object, _
                                     ByVal componentIndex As Long, _
                                     ByRef maxLocalDeflection As Double)
    
    On Error GoTo GetMaxLocalDeflectionErrorHandler
    
    ' --- MÉTODO OPTIMIZADO: Usar función directa de OpenSTAAD ---
    Dim maxDY As Double, maxDZ As Double
    Dim apiSuccess As Boolean
    
    ' Intentar usar la función nativa GetMaxMemberDeflection (STAAD.Pro V8i+)
    On Error Resume Next
    apiSuccess = objOutput.GetMaxMemberDeflection(memberID, loadCaseID, maxDY, maxDZ)
    
    If Err.Number <> 0 Or Not apiSuccess Then
        ' Si falla, usar método de fallback
        Err.Clear
        On Error GoTo GetMaxLocalDeflectionErrorHandler
        Call GetMaxLocalDeflection_Fallback(memberID, loadCaseID, memberLength, conversionFactorToMM, objOutput, componentIndex, maxLocalDeflection)
        Exit Sub
    End If
    On Error GoTo GetMaxLocalDeflectionErrorHandler
    
    ' NOTA: GetMaxMemberDeflection YA retorna la deflexión relativa a la cuerda
    ' (STAAD calcula internamente: desplazamiento_real - interpolación_lineal)
    Select Case componentIndex
        Case 1 'DY Local (Vertical)
            maxLocalDeflection = Abs(maxDY) * conversionFactorToMM
        Case 2 'DZ Local (Horizontal)
            maxLocalDeflection = Abs(maxDZ) * conversionFactorToMM
    End Select
    
    Exit Sub
    
GetMaxLocalDeflectionErrorHandler:
    maxLocalDeflection = 0
    Err.Clear
End Sub




'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina AUXILIAR: Método de Fallback con cálculo RELATIVO (V8.1)
' Para versiones antiguas de STAAD o cuando GetMaxMemberDeflection no está disponible
'-------------------------------------------------------------------------------------------------------------------------------
Private Sub GetMaxLocalDeflection_Fallback(ByVal memberID As Long, _
                                           ByVal loadCaseID As Long, _
                                           ByVal memberLength As Double, _
                                           ByVal conversionFactorToMM As Double, _
                                           ByVal objOutput As Object, _
                                           ByVal componentIndex As Long, _
                                           ByRef maxLocalDeflection As Double)
    
    Dim i As Long
    Dim dDistance As Double, DYmodelunits As Double, DZmodelunits As Double
    Dim CurrentLocalDeflectionmm As Double
    
    ' --- OBTENER DESPLAZAMIENTOS EN LOS NODOS EXTREMOS (OPTIMIZADO) ---
    Dim memberNodeData As Variant
    memberNodeData = g_memberNodesDict.Item(memberID)
    Dim nodeA_ID As Long, nodeB_ID As Long
    nodeA_ID = memberNodeData(0)
    nodeB_ID = memberNodeData(1)
    
    Dim dispA() As Double, dispB() As Double
    Dim keyA As String, keyB As String
    
    keyA = nodeA_ID & "_" & loadCaseID
    keyB = nodeB_ID & "_" & loadCaseID
    
    ' Intentar obtener del caché global primero
    If Not g_nodalDisplacementsDict Is Nothing Then
        If g_nodalDisplacementsDict.Exists(keyA) Then
            dispA = g_nodalDisplacementsDict.Item(keyA)
        Else
            ReDim dispA(0 To 5)
            Call GetMemberEndDisplacementsWrapper(objOutput, nodeA_ID, loadCaseID, dispA)
        End If
        
        If g_nodalDisplacementsDict.Exists(keyB) Then
            dispB = g_nodalDisplacementsDict.Item(keyB)
        Else
            ReDim dispB(0 To 5)
            Call GetMemberEndDisplacementsWrapper(objOutput, nodeB_ID, loadCaseID, dispB)
        End If
    Else
        ReDim dispA(0 To 5)
        ReDim dispB(0 To 5)
        Call GetMemberEndDisplacementsWrapper(objOutput, nodeA_ID, loadCaseID, dispA)
        Call GetMemberEndDisplacementsWrapper(objOutput, nodeB_ID, loadCaseID, dispB)
    End If
    
    Dim dispA_component As Double, dispB_component As Double
    Select Case componentIndex
        Case 1 'DY Local (Vertical)
            dispA_component = dispA(1)
            dispB_component = dispB(1)
        Case 2 'DZ Local (Horizontal)
            dispA_component = dispA(2)
            dispB_component = dispB(2)
    End Select
    
    maxLocalDeflection = 0
    
    ' Muestrear 7 puntos a lo largo del miembro
    For i = 0 To 6
        dDistance = (memberLength / 6) * i
        
        On Error Resume Next
        If objOutput.GetIntermediateDeflectionAtDistance(memberID, dDistance, loadCaseID, DYmodelunits, DZmodelunits) Then
            
            ' --- CÁLCULO DE DEFLEXIÓN RELATIVA ---
            ' Interpolar linealmente el desplazamiento de la cuerda en este punto
            Dim chordDisp As Double
            Dim fraction As Double
            fraction = dDistance / memberLength
            chordDisp = dispA_component + (dispB_component - dispA_component) * fraction
            
            ' Deflexión relativa = Desplazamiento real - Cuerda
            Dim relativeDeflection As Double
            Select Case componentIndex
                Case 1 'DY Local
                    relativeDeflection = DYmodelunits - chordDisp
                    CurrentLocalDeflectionmm = Abs(relativeDeflection) * conversionFactorToMM
                Case 2 'DZ Local
                    relativeDeflection = DZmodelunits - chordDisp
                    CurrentLocalDeflectionmm = Abs(relativeDeflection) * conversionFactorToMM
            End Select
            
            If CurrentLocalDeflectionmm > maxLocalDeflection Then
                maxLocalDeflection = CurrentLocalDeflectionmm
            End If
        End If
        On Error GoTo 0
    Next i
End Sub



'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: CollectLoadCasesFromSheet
' Propósito: Centraliza la lógica para leer y validar los casos de carga desde una hoja de Excel.
'-------------------------------------------------------------------------------------------------------------------------------
Sub CollectLoadCasesFromSheet(ByVal wb As Object, ByVal sheetName As String, ByVal cols As Variant, ByVal envTypes As Variant, ByVal envNoRow As Long, ByVal rangeStartRow As Long, ByVal rangeEndRow As Long, ByVal listStartRow As Long, ByRef errorMessages As String)
    Dim i As Long, j As Long, currentCol As Long, listRowNum As Long
    Dim colLetter As String, currentColErrors As String, cellValueCheck As Variant
    Dim EnvNo As Variant, EnvType As String
    Dim StartLoadCase As Variant, EndLoadCase As Variant
    Dim LoadCaseList() As Long, numLoadCases As Long, currentCaseValue As Variant
    Dim startLoadCaseVal As Long, endLoadCaseVal As Long
    Dim rangeProvided As Boolean, listProvided As Boolean
    Dim finalNumLoadCases As Long, tempFinalLoadCaseList() As Long
    
    For i = LBound(cols) To UBound(cols)
        currentCol = cols(i)
        EnvType = envTypes(i)
        colLetter = Split(g_objExcel.Cells(1, currentCol).Address(True, False), "$")(0)
        currentColErrors = ""
        
        cellValueCheck = GetCellValue(wb, sheetName, colLetter & envNoRow)
        If IsEmpty(cellValueCheck) Then GoTo NextColumnLoop
        
        EnvNo = cellValueCheck
        If Not IsNumeric(EnvNo) Then currentColErrors = currentColErrors & "El número de envolvente debe ser numérico." & vbCrLf
        
        StartLoadCase = GetCellValue(wb, sheetName, colLetter & rangeStartRow)
        EndLoadCase = GetCellValue(wb, sheetName, colLetter & rangeEndRow)
        If Not IsEmpty(StartLoadCase) And Not IsNumeric(StartLoadCase) Then currentColErrors = currentColErrors & "El inicio del rango debe ser numérico." & vbCrLf
        If Not IsEmpty(EndLoadCase) And Not IsNumeric(EndLoadCase) Then currentColErrors = currentColErrors & "El final del rango debe ser numérico." & vbCrLf
        
        ReDim LoadCaseList(0 To -1)
        numLoadCases = 0
        listRowNum = listStartRow
        Do While Not IsEmpty(GetCellValue(wb, sheetName, colLetter & listRowNum))
            currentCaseValue = GetCellValue(wb, sheetName, colLetter & listRowNum)
            If IsNumeric(currentCaseValue) Then
                 numLoadCases = numLoadCases + 1
                 ReDim Preserve LoadCaseList(0 To numLoadCases - 1)
                 LoadCaseList(numLoadCases - 1) = CLng(currentCaseValue)
            End If
            listRowNum = listRowNum + 1
        Loop
        
        startLoadCaseVal = 0
        If IsNumeric(StartLoadCase) Then startLoadCaseVal = CLng(StartLoadCase)
        endLoadCaseVal = 0
        If IsNumeric(EndLoadCase) Then endLoadCaseVal = CLng(EndLoadCase)
        
        rangeProvided = (startLoadCaseVal > 0 And endLoadCaseVal > 0 And startLoadCaseVal <= endLoadCaseVal)
        listProvided = (numLoadCases > 0)
        
        If rangeProvided And listProvided Then currentColErrors = currentColErrors & "Rango Y lista proporcionados." & vbCrLf
        If Not rangeProvided And Not listProvided Then currentColErrors = currentColErrors & "Ni rango ni lista proporcionados." & vbCrLf
        If currentColErrors <> "" Then
            errorMessages = errorMessages & "Errores en " & sheetName & " - Col " & colLetter & ":" & vbCrLf & currentColErrors
            GoTo NextColumnLoop
        End If
        
        finalNumLoadCases = 0
        If rangeProvided Then
            finalNumLoadCases = endLoadCaseVal - startLoadCaseVal + 1
            ReDim tempFinalLoadCaseList(0 To finalNumLoadCases - 1)
            For j = 0 To finalNumLoadCases - 1
                tempFinalLoadCaseList(j) = startLoadCaseVal + j
            Next j
        ElseIf listProvided Then
            tempFinalLoadCaseList = LoadCaseList
            finalNumLoadCases = numLoadCases
        End If
        
        If finalNumLoadCases > 0 Then
            For j = 0 To finalNumLoadCases - 1
                g_overallLoadCaseIndex = g_overallLoadCaseIndex + 1
                ReDim Preserve g_finalLoadCasesArray(0 To g_overallLoadCaseIndex)
                ReDim Preserve g_finalLoadCaseTypesArray(0 To g_overallLoadCaseIndex)
                g_finalLoadCasesArray(g_overallLoadCaseIndex) = tempFinalLoadCaseList(j)
                g_finalLoadCaseTypesArray(g_overallLoadCaseIndex) = EnvType
            Next j
        End If
NextColumnLoop:
    Next i
End Sub
'-------------------------------------------------------------------------------------------------------------------------------
' Subrutinas: Write...Headers
' Propósito: Centralizan la escritura de encabezados para mantener Main más limpio.
'-------------------------------------------------------------------------------------------------------------------------------
Sub WriteDeflexionesCompHeaders(ByVal ws As Object)
    ws.Cells(1, 1).Value = "Member ID": ws.Cells(1, 2).Value = "Physical Member ID": ws.Cells(1, 3).Value = "Group Name": ws.Cells(1, 4).Value = "Longitud (m)": ws.Cells(1, 5).Value = "Load Case/Envelope ID": ws.Cells(1, 6).Value = "Envelope Type"
    ws.Cells(1, 11).Value = "Deflexión Crítica Vertical (mm)": ws.Cells(1, 13).Value = "Factor L/X Vertical": ws.Cells(1, 14).Value = "Deflexión Permisible Vertical (mm)": ws.Cells(1, 15).Value = "Cumple Norma Vertical": ws.Cells(1, 16).Value = "Relación Deflexión Vertical"
    ws.Cells(1, 25).Value = "Deflexión Crítica Horizontal (mm)": ws.Cells(1, 27).Value = "Factor L/X Horizontal": ws.Cells(1, 28).Value = "Deflexión Permisible Horizontal (mm)": ws.Cells(1, 29).Value = "Cumple Norma Horizontal": ws.Cells(1, 30).Value = "Relación Deflexión Horizontal"
    ws.Cells(1, 31).Value = "Max Rel DX (mm) Col": ws.Cells(1, 32).Value = "Caso Crítico DX Col": ws.Cells(1, 33).Value = "Y Coord Crítica DX Col (m)": ws.Cells(1, 34).Value = "Nodo Crítico DX Col": ws.Cells(1, 35).Value = "Longitud Tramo DX (m) Col": ws.Cells(1, 36).Value = "Factor L/X DX Col": ws.Cells(1, 37).Value = "Permisible DX (mm) Col": ws.Cells(1, 38).Value = "Cumple DX Col": ws.Cells(1, 39).Value = "Relación DX Col"
    ws.Cells(1, 40).Value = "Max Rel DZ (mm) Col": ws.Cells(1, 41).Value = "Caso Crítico DZ Col": ws.Cells(1, 42).Value = "Y Coord Crítica DZ Col (m)": ws.Cells(1, 43).Value = "Nodo Crítico DZ Col": ws.Cells(1, 44).Value = "Longitud Tramo DZ (m) Col": ws.Cells(1, 45).Value = "Factor L/X DZ Col": ws.Cells(1, 46).Value = "Permisible DZ (mm) Col": ws.Cells(1, 47).Value = "Cumple DZ Col": ws.Cells(1, 48).Value = "Relación DZ Col"
End Sub

Sub WriteVerificacionHeaders(ByVal ws As Object, ByVal maxDeflectionLabel As String)
    ws.Cells(1, 1).Value = "Physical Member ID": ws.Cells(1, 2).Value = "Analytical Member ID": ws.Cells(1, 3).Value = "Longitud de miembro (m)": ws.Cells(1, 4).Value = "Caso de carga crítico": ws.Cells(1, 5).Value = maxDeflectionLabel: ws.Cells(1, 6).Value = "Factor L/X": ws.Cells(1, 7).Value = "Deflexión Permisible (mm)": ws.Cells(1, 8).Value = "Cumple Norma": ws.Cells(1, 9).Value = "Relación Deflexión"
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetDeflectionCoefficient (Versión 2 - Grupos Independientes)
' Propósito: Devuelve el coeficiente L/X correcto basado en el grupo y tipo de carga.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetDeflectionCoefficient(ByVal memberGroup As String, ByVal envType As String) As Double
    GetDeflectionCoefficient = 0 ' Valor por defecto
    Select Case memberGroup
        ' *** INICIO DE LA MODIFICACIÓN ***
        Case "_VIGAS_PRIN"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_VigasPrin_Tipo1
                Case "2": GetDeflectionCoefficient = g_VigasPrin_Tipo2
                Case "3": GetDeflectionCoefficient = g_VigasPrin_Tipo3
            End Select
        Case "_VIGAS_SEC"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_VigasSec_Tipo1
                Case "2": GetDeflectionCoefficient = g_VigasSec_Tipo2
                Case "3": GetDeflectionCoefficient = g_VigasSec_Tipo3
            End Select
        ' *** FIN DE LA MODIFICACIÓN ***
        Case "_VIGAS_TECHOS"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_VigasTechos_Tipo1
                Case "2": GetDeflectionCoefficient = g_VigasTechos_Tipo2
                Case "3": GetDeflectionCoefficient = g_VigasTechos_Tipo3
            End Select
        ' *** INICIO DE LA MODIFICACIÓN ***
        Case "_VIGAS_CORREAS"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_VigasCorreas_Tipo1
                Case "2": GetDeflectionCoefficient = g_VigasCorreas_Tipo2
                Case "3": GetDeflectionCoefficient = g_VigasCorreas_Tipo3
            End Select
        Case "_ARRIOST_HORIZ"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_ArriostHoriz_Tipo1
                Case "2": GetDeflectionCoefficient = g_ArriostHoriz_Tipo2
                Case "3": GetDeflectionCoefficient = g_ArriostHoriz_Tipo3
            End Select
        ' *** FIN DE LA MODIFICACIÓN ***
        Case "_VIGAS_VOLADIZO"
            Select Case envType
                Case "1": GetDeflectionCoefficient = g_VigasVoladizo_Tipo1
                Case "2": GetDeflectionCoefficient = g_VigasVoladizo_Tipo2
                Case "3": GetDeflectionCoefficient = g_VigasVoladizo_Tipo3
            End Select
        Case "_VIGA_CARRIL_TR"
            If envType = "4" Then GetDeflectionCoefficient = g_VigaCarrilTR_Tipo4
        Case "_VIGA_CARRIL_UR"
            If envType = "4" Then GetDeflectionCoefficient = g_VigaCarrilUR_Tipo4
        Case "_MONORRIEL"
            If envType = "4" Then GetDeflectionCoefficient = g_Monorriel_Tipo4
        Case "_PUENTE_GRUA"
            If envType = "4" Then GetDeflectionCoefficient = g_PuenteGrua_Tipo4
    End Select
End Function
'-------------------------------------------------------------------------------------------------------------------------------
' Subrutinas: VerifyDeflection y VerifyDrift
' Propósito: Centralizan la lógica de cálculo de ratios y cumplimiento de normas.
'-------------------------------------------------------------------------------------------------------------------------------
Sub VerifyDeflection(ByVal actualDeflection As Double, ByVal permissibleDeflection As Double, ByRef complies As String, ByRef ratio As Double)
    If permissibleDeflection > 0.00001 Then
        ratio = Abs(actualDeflection) / permissibleDeflection
        If ratio <= 1 Then complies = "SI" Else complies = "NO"
    Else
        ratio = 0
        complies = "N/A"
    End If
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: VerifyDrift (Versión 2 - Factores Diferenciados)
' Propósito: Centraliza la lógica de cálculo de ratios y cumplimiento de normas para derivas,
'            seleccionando el factor correcto (Servicio vs. Últimas).
'-------------------------------------------------------------------------------------------------------------------------------
Sub VerifyDrift(ByVal actualDrift As Double, ByVal storeyHeight As Double, ByVal envType As String, ByRef factor As Double, ByRef permissible As Double, ByRef complies As String, ByRef ratio As Double)
    permissible = 0
    factor = 0
    
    ' Usar InStr para determinar el tipo de carga (Viento/Sismo) y la categoría (Servicio/Ultimas)
    If InStr(1, envType, "Viento-Servicio") > 0 Then
        factor = g_FactorVientoServicio
        If factor > 0 Then permissible = (storeyHeight * 1000) / factor
    ElseIf InStr(1, envType, "Viento-Ultimas") > 0 Then
        factor = g_FactorVientoUltimas
        If factor > 0 Then permissible = (storeyHeight * 1000) / factor
    ElseIf InStr(1, envType, "Sismo-Servicio") > 0 Then
        factor = g_FactorSismoServicio
        If factor > 0 Then permissible = (storeyHeight * 1000) * factor
    ElseIf InStr(1, envType, "Sismo-Ultimas") > 0 Then
        factor = g_FactorSismoUltimas
        If factor > 0 Then permissible = (storeyHeight * 1000) * factor
    End If
    
    If permissible > 0.00001 Then
        ratio = Abs(actualDrift) / permissible
        If ratio <= 1 Then complies = "SI" Else complies = "NO"
    Else
        ratio = 0
        complies = "N/A"
    End If
End Sub

'===============================================================================================================================
' Subrutina: ConsolidateBeamResultsFromArray (V8.1 - FORMATO V7 RESTAURADO COMPLETO)
' Propósito: Genera los informes de resumen para vigas en "Verificación Deflexiones" y "Verificación Deflexiones H"
'            MANTIENE EL FORMATO EXACTO DE V7: 9 columnas (ID, Tipo, Longitud, Caso, Max Deflexión, Factor, Permisible, Cumple, Ratio)
'===============================================================================================================================
Sub ConsolidateBeamResultsFromArray(ByRef dataArray As Variant, ByVal wsTarget As Object, ByVal direction As String)
    
    '--- PASO 1: Preparar hoja de destino con encabezados V7 (SIN CAMBIOS) ---
    wsTarget.Cells.ClearContents
    
    Dim headers As Variant
    Dim maxDeflectionLabel As String
    
    If direction = "Vertical" Then
        maxDeflectionLabel = "Max DY (mm)"
    Else
        maxDeflectionLabel = "Max DH (mm)"
    End If
    
    ' ✅ FORMATO V7: 9 columnas exactas
    headers = Split("ID,Tipo,Longitud de miembro (m),Caso de carga crítico," & maxDeflectionLabel & ",Factor L/X,Deflexión Permisible (mm),Cumple Norma,Relación Deflexión", ",")
    
    Dim i As Long
    For i = 0 To UBound(headers)
        wsTarget.Cells(1, i + 1).Value = headers(i)
        wsTarget.Cells(1, i + 1).Font.Bold = True
    Next i
    
    '--- PASO 2: Consolidar resultados críticos (LÓGICA V7 ADAPTADA A V8) ---
    Dim consolidatedDict As Object, key As String, criticalRowSource As Long
    Dim existingRatio As Double, currentRatio As Double
    Set consolidatedDict = CreateObject("Scripting.Dictionary")
    
    ' ✅ COLUMNAS CORRECTAS PARA V8 (resultsArray tiene 35 columnas)
    Dim ratioCol As Long, deflCol As Long, factorCol As Long, permCol As Long, compliesCol As Long
    
    If direction = "Vertical" Then
        deflCol = 21      ' Columna donde está "Max Deflexión Vertical (mm)" en V8
        factorCol = 23    ' Columna "Factor L/X Vertical"
        permCol = 24      ' Columna "Deflexión Permisible Vertical (mm)"
        compliesCol = 25  ' Columna "Cumple Norma Vertical"
        ratioCol = 26     ' Columna "Relación Deflexión Vertical"
    Else ' Horizontal
        deflCol = 27      ' Columna "Max Deflexión Horizontal (mm)" en V8
        factorCol = 28    ' Columna "Factor L/X Horizontal"
        permCol = 29      ' Columna "Deflexión Permisible Horizontal (mm)"
        compliesCol = 30  ' Columna "Cumple Norma Horizontal"
        ratioCol = 31     ' Columna "Relación Deflexión Horizontal"
    End If
    
    ' Iterar sobre el array de resultados y consolidar por PM o AM
    For i = 1 To UBound(dataArray, 1)
        ' Filtrar solo vigas, arriostramientos, carriles, monorrieles y puentes grúa
        If (dataArray(i, 3) Like "*VIGAS*" Or dataArray(i, 3) Like "*ARRIOST*" Or _
            dataArray(i, 3) Like "*CARRIL*" Or dataArray(i, 3) = "_MONORRIEL" Or _
            dataArray(i, 3) = "_PUENTE_GRUA") And dataArray(i, compliesCol) <> "N/A" Then
            
            ' Determinar la clave: PM o AM
            If dataArray(i, 2) <> 0 Then
                key = "PM_" & dataArray(i, 2)
            Else
                key = "AM_" & dataArray(i, 1)
            End If
            
            ' Si no existe, agregarlo
            If Not consolidatedDict.Exists(key) Then
                consolidatedDict.Add key, i
            Else
                ' Si existe, comparar ratios y quedarse con el peor
                criticalRowSource = consolidatedDict.Item(key)
                existingRatio = 0
                If IsNumeric(dataArray(criticalRowSource, ratioCol)) Then
                    existingRatio = CDbl(dataArray(criticalRowSource, ratioCol))
                End If
                
                currentRatio = 0
                If IsNumeric(dataArray(i, ratioCol)) Then
                    currentRatio = CDbl(dataArray(i, ratioCol))
                End If
                
                If currentRatio > existingRatio Then
                    consolidatedDict.Item(key) = i
                End If
            End If
        End If
    Next i
    
    '--- PASO 3: Escribir resultados en bloque (FORMATO V7 EXACTO: 9 COLUMNAS) ---
    If consolidatedDict.Count > 0 Then
        Dim sortedKeys() As String
        sortedKeys = SortDictionaryKeys(consolidatedDict)
        
        Dim consolidatedArray As Variant, consolidatedCount As Long
        ReDim consolidatedArray(1 To consolidatedDict.Count, 1 To 9)
        
        For consolidatedCount = 0 To UBound(sortedKeys)
            key = sortedKeys(consolidatedCount)
            criticalRowSource = consolidatedDict.Item(key)
            
            ' ✅ COLUMNA 1: ID (numérico, sin "PM_" o "AM_")
            If Left(key, 3) = "PM_" Then
                consolidatedArray(consolidatedCount + 1, 1) = CLng(Mid(key, 4))
            Else
                consolidatedArray(consolidatedCount + 1, 1) = CLng(Mid(key, 4))
            End If
            
            ' ✅ COLUMNA 2: Tipo ("PM" o "AM")
            If Left(key, 3) = "PM_" Then
                consolidatedArray(consolidatedCount + 1, 2) = "PM"
            Else
                consolidatedArray(consolidatedCount + 1, 2) = "AM"
            End If
            
            ' ✅ COLUMNAS 3-9: Datos del caso crítico (EXACTAMENTE COMO V7)
            consolidatedArray(consolidatedCount + 1, 3) = dataArray(criticalRowSource, 4)         ' Longitud
            consolidatedArray(consolidatedCount + 1, 4) = dataArray(criticalRowSource, 5)         ' Caso de carga
            consolidatedArray(consolidatedCount + 1, 5) = dataArray(criticalRowSource, deflCol)   ' Max Deflexión
            consolidatedArray(consolidatedCount + 1, 6) = dataArray(criticalRowSource, factorCol) ' Factor L/X
            consolidatedArray(consolidatedCount + 1, 7) = dataArray(criticalRowSource, permCol)   ' Deflexión Permisible
            consolidatedArray(consolidatedCount + 1, 8) = dataArray(criticalRowSource, compliesCol) ' Cumple Norma
            consolidatedArray(consolidatedCount + 1, 9) = dataArray(criticalRowSource, ratioCol)  ' Relación
        Next consolidatedCount
        
        ' Escribir todo de una sola vez
        wsTarget.Range("A2").Resize(consolidatedDict.Count, 9).Value = consolidatedArray
        
        ' Ajustar columnas
        wsTarget.Columns.AutoFit
    End If

End Sub

'===============================================================================================================================
' --- INICIO: NUEVAS FUNCIONES PARA CÁLCULO DE DEFLEXIÓN EN MIEMBROS FÍSICOS ---
'===============================================================================================================================
'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetOrderedNodesForPM (Versión 2 - 100% VBA Nativo)
' Propósito: Obtiene una lista ordenada de TODOS los nodos que componen un miembro físico.
'            Esta versión utiliza únicamente arrays dinámicos y diccionarios de VBA,
'            eliminando la dependencia de "System.Collections.ArrayList" para garantizar
'            la compatibilidad con el editor de macros de STAAD.Pro.
' Retorna: Un array de Longs con los IDs de los nodos ordenados.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetOrderedNodesForPM(ByVal pmID As Long, ByVal objSheetPM As Object) As Long()
    Dim emptyResult() As Long
    ReDim emptyResult(0 To -1)
    
    ' 1. Obtener nodos extremos desde la hoja PM
    Dim pmDataRange As Variant
    Dim lastRow As Long
    Dim startNode As Long
    Dim endNode As Long
    Dim i As Long
    
    lastRow = objSheetPM.Cells(objSheetPM.Rows.Count, "A").End(xlUp).Row
    If lastRow < 2 Then
        GetOrderedNodesForPM = emptyResult
        Exit Function
    End If
    pmDataRange = objSheetPM.Range("A2:E" & lastRow).Value
    
    For i = 1 To UBound(pmDataRange, 1)
        If CLng(pmDataRange(i, 1)) = pmID Then
            If IsNumeric(pmDataRange(i, 4)) And IsNumeric(pmDataRange(i, 5)) Then
                startNode = CLng(pmDataRange(i, 4))
                endNode = CLng(pmDataRange(i, 5))
                Exit For
            End If
        End If
    Next i
    
    If startNode = 0 Or endNode = 0 Then
        GetOrderedNodesForPM = emptyResult
        Exit Function
    End If
    
    ' 2. Construir la lista de miembros analíticos para este PM desde el diccionario global
    Dim analyticalMembersDict As Object
    Set analyticalMembersDict = CreateObject("Scripting.Dictionary")
    Dim dictKey As Variant
    Dim memberData As Variant
    For Each dictKey In g_memberNodesDict.Keys
        memberData = g_memberNodesDict.Item(dictKey)
        If CLng(memberData(3)) = pmID Then
            analyticalMembersDict.Add CLng(dictKey), Array(CLng(memberData(0)), CLng(memberData(1)))
        End If
    Next dictKey
    
    If analyticalMembersDict.Count = 0 Then
        GetOrderedNodesForPM = emptyResult
        Exit Function
    End If
    
    ' 3. Ordenar los nodos por conectividad usando un array dinámico
    Dim orderedNodesArray() As Long
    ReDim orderedNodesArray(0 To analyticalMembersDict.Count) ' Tamaño máximo posible
    Dim nodeCount As Long
    nodeCount = 0
    
    orderedNodesArray(nodeCount) = startNode
    nodeCount = nodeCount + 1
    
    Dim currentNode As Long
    Dim nextNode As Long
    Dim foundNext As Boolean
    
    currentNode = startNode
    
    Do While analyticalMembersDict.Count > 0 And currentNode <> endNode
        foundNext = False
        For Each dictKey In analyticalMembersDict.Keys
            Dim nodes As Variant
            nodes = analyticalMembersDict.Item(dictKey)
            If nodes(0) = currentNode Then
                nextNode = nodes(1)
                foundNext = True
            ElseIf nodes(1) = currentNode Then
                nextNode = nodes(0)
                foundNext = True
            End If
            
            If foundNext Then
                orderedNodesArray(nodeCount) = nextNode
                nodeCount = nodeCount + 1
                currentNode = nextNode
                analyticalMembersDict.Remove dictKey
                Exit For
            End If
        Next dictKey
        If Not foundNext Then Exit Do ' Romper bucle si no hay continuidad
    Loop
    
    ' Ajustar el tamaño final del array
    ReDim Preserve orderedNodesArray(0 To nodeCount - 1)
    GetOrderedNodesForPM = orderedNodesArray
End Function
'-------------------------------------------------------------------------------------------------------------------------------

'-------------------------------------------------------------------------------------------------------------------------------
' Función: CalculatePhysicalMemberMaxLocalDeflection (VERSIÓN SIMPLE Y RÁPIDA V8.2)
' Calcula deflexión relativa SIN el bucle adicional de segmentos (que lo hace más lento)
'-------------------------------------------------------------------------------------------------------------------------------
Function CalculatePhysicalMemberMaxLocalDeflection(ByVal pmID As Long, _
                                                    ByVal lcID As Long, _
                                                    ByVal objSheetPM As Object, _
                                                    ByVal conversionFactor As Double) As Double
    
    On Error GoTo CalcErrorHandler
    
    Dim maxDeflection As Double
    maxDeflection = 0
    
    ' --- Paso 1: Obtener nodos ordenados ---
    Dim orderedNodes() As Long
    orderedNodes = GetOrderedNodesForPM(pmID, objSheetPM)
    
    If UBound(orderedNodes) < 0 Then
        CalculatePhysicalMemberMaxLocalDeflection = 0
        Exit Function
    End If
    
    Dim nodeStartID As Long, nodeEndID As Long
    nodeStartID = orderedNodes(LBound(orderedNodes))
    nodeEndID = orderedNodes(UBound(orderedNodes))
    
    ' --- Paso 2: Coordenadas Y extremos ---
    Dim yStartGlobal As Double, yEndGlobal As Double
    Dim coordsStart As Variant, coordsEnd As Variant
    
    coordsStart = g_nodeCoordsDict.Item(nodeStartID)
    coordsEnd = g_nodeCoordsDict.Item(nodeEndID)
    yStartGlobal = coordsStart(1)
    yEndGlobal = coordsEnd(1)
    
    Dim pmTotalHeight As Double
    pmTotalHeight = Abs(yEndGlobal - yStartGlobal)
    
    If pmTotalHeight < 0.001 Then
        CalculatePhysicalMemberMaxLocalDeflection = 0
        Exit Function
    End If
    
    ' --- Paso 3: Desplazamientos extremos ---
    Dim dispStartY As Double, dispEndY As Double
    Dim dispArrayStart() As Double, dispArrayEnd() As Double
    Dim keyStart As String, keyEnd As String
    
    keyStart = nodeStartID & "_" & lcID
    keyEnd = nodeEndID & "_" & lcID
    
    dispArrayStart = g_nodalDisplacementsDict.Item(keyStart)
    dispArrayEnd = g_nodalDisplacementsDict.Item(keyEnd)
    dispStartY = dispArrayStart(1)
    dispEndY = dispArrayEnd(1)
    
    ' --- Paso 4: Calcular deflexión relativa SOLO en nodos intermedios ---
    Dim i As Long, currentNodeID As Long
    Dim yCurrentGlobal As Double, coordsCurrent As Variant
    Dim fraction As Double, chordDispY As Double
    Dim dispCurrentY As Double, dispArrayCurrent() As Double
    Dim relativeDeflection As Double
    Dim keyCurrent As String
    
    For i = 0 To UBound(orderedNodes)
        currentNodeID = orderedNodes(i)
        
        coordsCurrent = g_nodeCoordsDict.Item(currentNodeID)
        yCurrentGlobal = coordsCurrent(1)
        
        fraction = (yCurrentGlobal - yStartGlobal) / (yEndGlobal - yStartGlobal)
        chordDispY = dispStartY + (dispEndY - dispStartY) * fraction
        
        keyCurrent = currentNodeID & "_" & lcID
        dispArrayCurrent = g_nodalDisplacementsDict.Item(keyCurrent)
        dispCurrentY = dispArrayCurrent(1)
        
        relativeDeflection = Abs(dispCurrentY - chordDispY) * conversionFactor
        
        If relativeDeflection > maxDeflection Then
            maxDeflection = relativeDeflection
        End If
    Next i
    
    CalculatePhysicalMemberMaxLocalDeflection = maxDeflection
    Exit Function

CalcErrorHandler:
    CalculatePhysicalMemberMaxLocalDeflection = 0
End Function


'-------------------------------------------------------------------------------------------------------------------------------
' Función: FindRowInResultsArray
' Propósito: Busca la fila en el array de resultados que corresponde a un miembro analítico
'            y un caso de carga específicos. Esencial para obtener datos pre-cargados.
' Retorna: El índice de la fila (Long), o -1 si no se encuentra.
'-------------------------------------------------------------------------------------------------------------------------------
Function FindRowInResultsArray(ByVal memberID As Long, ByVal lcID As Long, ByRef dataArray As Variant) As Long
    Dim i As Long
    FindRowInResultsArray = -1 ' Valor por defecto si no se encuentra

    ' Búsqueda lineal. Para un rendimiento extremo en modelos gigantescos, se podría
    ' pre-procesar el array en un diccionario, pero para la mayoría de los casos esto es suficiente.
    For i = 1 To UBound(dataArray, 1)
        If CLng(dataArray(i, 1)) = memberID And CLng(dataArray(i, 5)) = lcID Then
            FindRowInResultsArray = i
            Exit Function
        End If
    Next i
End Function





' --- INICIO: FUNCIONES AUXILIARES DE MATEMÁTICAS VECTORIALES ---
'===============================================================================================================================

' Resta dos vectores (puntos) para obtener un vector director.
Function VectorSubtract(ByVal p2() As Double, ByVal p1() As Double) As Double()
    Dim result(0 To 2) As Double
    result(0) = p2(0) - p1(0)
    result(1) = p2(1) - p1(1)
    result(2) = p2(2) - p1(2)
    VectorSubtract = result
End Function

' Suma un punto y un vector de desplazamiento.
Function VectorAdd(ByVal p1() As Double, ByVal v() As Double) As Double()
    Dim result(0 To 2) As Double
    result(0) = p1(0) + v(0)
    result(1) = p1(1) + v(1)
    result(2) = p1(2) + v(2)
    VectorAdd = result
End Function

' Calcula la magnitud (longitud) de un vector.
Function VectorMagnitude(ByVal v() As Double) As Double
    VectorMagnitude = Sqr(v(0) * v(0) + v(1) * v(1) + v(2) * v(2))
End Function

' Calcula el producto punto de dos vectores.
Function VectorDotProduct(ByVal v1() As Double, ByVal v2() As Double) As Double
    VectorDotProduct = v1(0) * v2(0) + v1(1) * v2(1) + v1(2) * v2(2)
End Function

' Multiplica un vector por un escalar.
Function VectorScale(ByVal v() As Double, ByVal scalar As Double) As Double()
    Dim result(0 To 2) As Double
    result(0) = v(0) * scalar
    result(1) = v(1) * scalar
    result(2) = v(2) * scalar
    VectorScale = result
End Function
' Calcula el producto cruz de dos vectores.
Function VectorCrossProduct(ByVal v1() As Double, ByVal v2() As Double) As Double()
    Dim result(0 To 2) As Double
    result(0) = v1(1) * v2(2) - v1(2) * v2(1) ' (y1*z2 - z1*y2)
    result(1) = v1(2) * v2(0) - v1(0) * v2(2) ' (z1*x2 - x1*z2)
    result(2) = v1(0) * v2(1) - v1(1) * v2(0) ' (x1*y2 - y1*x2)
    VectorCrossProduct = result
End Function

' Normaliza un vector para hacerlo unitario (longitud = 1).
Function VectorNormalize(ByVal v() As Double) As Double()
    Dim result(0 To 2) As Double
    Dim mag As Double
    mag = VectorMagnitude(v)
    If mag > 0.000001 Then
        result(0) = v(0) / mag
        result(1) = v(1) / mag
        result(2) = v(2) / mag
    End If
    VectorNormalize = result
End Function


'-------------------------------------------------------------------------------------------------------------------------------
' FUNCIÓN AUXILIAR: FindAnalyticalMemberBetweenNodes
' Busca el ID del miembro analítico que conecta dos nodos dados, perteneciente a un PM específico
'-------------------------------------------------------------------------------------------------------------------------------
Private Function FindAnalyticalMemberBetweenNodes(ByVal nodeA As Long, _
                                                   ByVal nodeB As Long, _
                                                   ByVal pmID As Long) As Long
    
    Dim dictKey As Variant, memberData As Variant
    FindAnalyticalMemberBetweenNodes = 0 ' Default: no encontrado
    
    For Each dictKey In g_memberNodesDict.Keys
        memberData = g_memberNodesDict.Item(dictKey)
        ' memberData(0) = NodeA, memberData(1) = NodeB, memberData(3) = PhysicalMemberID
        
        If CLng(memberData(3)) = pmID Then ' Pertenece al PM correcto
            If (CLng(memberData(0)) = nodeA And CLng(memberData(1)) = nodeB) Or _
               (CLng(memberData(0)) = nodeB And CLng(memberData(1)) = nodeA) Then
                FindAnalyticalMemberBetweenNodes = CLng(dictKey)
                Exit Function
            End If
        End If
    Next dictKey
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' FUNCIÓN AUXILIAR: GetSegmentPanzaFromResults
' Obtiene la panza local (columna 19) de un segmento analítico desde el resultsArray
'-------------------------------------------------------------------------------------------------------------------------------
Private Function GetSegmentPanzaFromResults(ByVal memberID As Long, _
                                             ByVal lcID As Long) As Double
    
    Dim i As Long
    GetSegmentPanzaFromResults = 0 ' Default
    
    ' Búsqueda en el resultsArray global
    For i = 1 To resultCount
        If CLng(resultsArray(i, 1)) = memberID And CLng(resultsArray(i, 5)) = lcID Then
            GetSegmentPanzaFromResults = CDbl(resultsArray(i, 19)) ' Columna 19 = Panza DY
            Exit Function
        End If
    Next i
End Function



'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: CollectLoadCasesToList
' Propósito: Lee los casos de carga (rango o lista) desde una columna específica de una hoja
'            y los añade a un diccionario para una búsqueda rápida.
'-------------------------------------------------------------------------------------------------------------------------------
Sub CollectLoadCasesToList(ByVal wb As Object, ByVal sheetName As String, ByVal col As Long, ByVal rangeStartRow As Long, ByVal rangeEndRow As Long, ByVal listStartRow As Long, ByRef targetDict As Object, ByRef errorMessages As String)
    Dim j As Long
    Dim colLetter As String
    Dim currentColErrors As String
    Dim cellValueCheck As Variant
    Dim StartLoadCase As Variant, EndLoadCase As Variant
    Dim LoadCaseList() As Long, numLoadCases As Long, currentCaseValue As Variant
    Dim startLoadCaseVal As Long, endLoadCaseVal As Long
    Dim rangeProvided As Boolean, listProvided As Boolean
    Dim listRowNum As Long

    colLetter = Split(g_objExcel.Cells(1, col).Address(True, False), "$")(0)
    currentColErrors = ""

    ' Leer la definición por RANGO de casos de carga
    StartLoadCase = GetCellValue(wb, sheetName, colLetter & rangeStartRow)
    EndLoadCase = GetCellValue(wb, sheetName, colLetter & rangeEndRow)
    If Not IsEmpty(StartLoadCase) And Not IsNumeric(StartLoadCase) Then currentColErrors = currentColErrors & "El inicio del rango debe ser numérico." & vbCrLf
    If Not IsEmpty(EndLoadCase) And Not IsNumeric(EndLoadCase) Then currentColErrors = currentColErrors & "El final del rango debe ser numérico." & vbCrLf

    ' Leer la definición por LISTA de casos de carga
    ReDim LoadCaseList(0 To -1)
    numLoadCases = 0
    listRowNum = listStartRow
    Do While Not IsEmpty(GetCellValue(wb, sheetName, colLetter & listRowNum))
        currentCaseValue = GetCellValue(wb, sheetName, colLetter & listRowNum)
        If IsNumeric(currentCaseValue) Then
             numLoadCases = numLoadCases + 1
             ReDim Preserve LoadCaseList(0 To numLoadCases - 1)
             LoadCaseList(numLoadCases - 1) = CLng(currentCaseValue)
        End If
        listRowNum = listRowNum + 1
    Loop

    startLoadCaseVal = 0: If IsNumeric(StartLoadCase) Then startLoadCaseVal = CLng(StartLoadCase)
    endLoadCaseVal = 0: If IsNumeric(EndLoadCase) Then endLoadCaseVal = CLng(EndLoadCase)
    rangeProvided = (startLoadCaseVal > 0 And endLoadCaseVal > 0 And startLoadCaseVal <= endLoadCaseVal)
    listProvided = (numLoadCases > 0)

    If rangeProvided And listProvided Then currentColErrors = currentColErrors & "Rango Y lista proporcionados." & vbCrLf
    ' No es un error no proporcionar nada, simplemente la lista estará vacía.
    
    If currentColErrors <> "" Then
        errorMessages = errorMessages & "Errores en " & sheetName & " - Col " & colLetter & ":" & vbCrLf & currentColErrors
        Exit Sub
    End If

    ' Añadir los casos de carga encontrados al diccionario de destino
    If rangeProvided Then
        For j = startLoadCaseVal To endLoadCaseVal
            If Not targetDict.Exists(j) Then
                targetDict.Add j, True
            End If
        Next j
    ElseIf listProvided Then
        For j = 0 To numLoadCases - 1
            If Not targetDict.Exists(LoadCaseList(j)) Then
                targetDict.Add LoadCaseList(j), True
            End If
        Next j
    End If
End Sub
'===============================================================================================================================
' --- INICIO: SECCIÓN DE FUNCIONES PARA ANÁLISIS DE DERIVAS DE ENTREPISO ---
'===============================================================================================================================

' Estructura de datos personalizada para almacenar la información de un nivel de entrepiso.
Private Type StoryLevelInfo
    NodeID As Long
    LevelElevation As Double
End Type

'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetStoryLevelsForColumn (Versión 2 - Forzando Nodos Extremos)
' Propósito: Orquesta la detección de niveles, garantizando que el nodo base y el nodo tope
'            de la columna siempre se incluyan en el análisis de derivas.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetStoryLevelsForColumn(ByVal columnPM_ID As Long, ByVal columnAM_ID As Long) As Object
    Dim storyLevelsDict As Object
    Set storyLevelsDict = CreateObject("Scripting.Dictionary")
    
    Dim columnNodes() As Long
    Dim i As Long
    
    ' Obtener todos los nodos que componen la columna, ordenados por altura.
    columnNodes = GetColumnNodesSortedByHeight(columnPM_ID, columnAM_ID)
    
    If UBound(columnNodes) < 1 Then ' Se necesitan al menos 2 nodos (base y tope)
        Set GetStoryLevelsForColumn = storyLevelsDict ' Devuelve diccionario vacío
        Exit Function
    End If
    
    ' Arrays para almacenar las estructuras de nivel encontradas para cada dirección.
    Dim levelsX() As StoryLevelInfo
    Dim levelsZ() As StoryLevelInfo
    ReDim levelsX(0 To -1) ' Inicializar como array vacío
    ReDim levelsZ(0 To -1) ' Inicializar como array vacío
    
    Dim baseNodeID As Long, topNodeID As Long
    baseNodeID = columnNodes(LBound(columnNodes))
    topNodeID = columnNodes(UBound(columnNodes))
    
    ' --- LÓGICA CORREGIDA ---
    ' 1. Añadir siempre el nodo base (el más bajo) a ambas direcciones.
    Call AddLevelToArray(levelsX, baseNodeID)
    Call AddLevelToArray(levelsZ, baseNodeID)
    
    ' 2. Iterar por los nodos INTERMEDIOS para verificar si son niveles de entrepiso.
    ' El bucle ahora va desde el segundo nodo hasta el PENÚLTIMO.
    If UBound(columnNodes) > 1 Then ' Solo si hay nodos intermedios
        For i = LBound(columnNodes) + 1 To UBound(columnNodes) - 1
            Dim currentNodeID As Long
            currentNodeID = columnNodes(i)
            
            ' Verificar si el nodo está arriostrado en la dirección X.
            If IsNodeBracedInDirection(currentNodeID, columnPM_ID, columnAM_ID, "X") Then
                Call AddLevelToArray(levelsX, currentNodeID)
            End If
            
            ' Verificar si el nodo está arriostrado en la dirección Z.
            If IsNodeBracedInDirection(currentNodeID, columnPM_ID, columnAM_ID, "Z") Then
                Call AddLevelToArray(levelsZ, currentNodeID)
            End If
        Next i
    End If
    
    ' 3. Añadir siempre el nodo tope (el más alto) a ambas direcciones.
    ' Se usa un diccionario temporal para evitar añadir el nodo tope dos veces si ya fue
    ' detectado como un nivel arriostrado (lo cual es posible).
    Dim tempDictX As Object, tempDictZ As Object
    Set tempDictX = CreateObject("Scripting.Dictionary")
    Set tempDictZ = CreateObject("Scripting.Dictionary")
    
    For i = LBound(levelsX) To UBound(levelsX)
        tempDictX.Add levelsX(i).NodeID, True
    Next i
    If Not tempDictX.Exists(topNodeID) Then
        Call AddLevelToArray(levelsX, topNodeID)
    End If
    
    For i = LBound(levelsZ) To UBound(levelsZ)
        tempDictZ.Add levelsZ(i).NodeID, True
    Next i
    If Not tempDictZ.Exists(topNodeID) Then
        Call AddLevelToArray(levelsZ, topNodeID)
    End If
    
    ' --- FIN DE LA LÓGICA CORREGIDA ---
    
    ' Añadir los arrays de niveles al diccionario final.
    If UBound(levelsX) >= 0 Then storyLevelsDict.Add "X", levelsX
    If UBound(levelsZ) >= 0 Then storyLevelsDict.Add "Z", levelsZ
    
    Set GetStoryLevelsForColumn = storyLevelsDict
End Function
'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetColumnNodesSortedByHeight
' Propósito: Obtiene todos los nodos de una columna (sea PM o AM) y los devuelve en un array ordenado por cota Y.
'-------------------------------------------------------------------------------------------------------------------------------
Function GetColumnNodesSortedByHeight(ByVal pmID As Long, ByVal amID As Long) As Long()
    Dim nodesDict As Object
    Set nodesDict = CreateObject("Scripting.Dictionary")
    Dim dictKey As Variant, memberData As Variant
    Dim nodeA As Long, nodeB As Long
    
    ' Recopilar todos los nodos únicos de la columna.
    If pmID <> 0 Then ' Si es un Physical Member
        For Each dictKey In g_memberNodesDict.Keys
            memberData = g_memberNodesDict.Item(dictKey)
            If CLng(memberData(3)) = pmID Then
                nodeA = CLng(memberData(0))
                nodeB = CLng(memberData(1))
                If Not nodesDict.Exists(nodeA) Then nodesDict.Add nodeA, g_nodeCoordsDict.Item(nodeA)(1) ' Guarda ID y cota Y
                If Not nodesDict.Exists(nodeB) Then nodesDict.Add nodeB, g_nodeCoordsDict.Item(nodeB)(1)
            End If
        Next dictKey
    Else ' Si es un Analytical Member
        memberData = g_memberNodesDict.Item(amID)
        nodeA = CLng(memberData(0))
        nodeB = CLng(memberData(1))
        If Not nodesDict.Exists(nodeA) Then nodesDict.Add nodeA, g_nodeCoordsDict.Item(nodeA)(1)
        If Not nodesDict.Exists(nodeB) Then nodesDict.Add nodeB, g_nodeCoordsDict.Item(nodeB)(1)
    End If
    
    ' Ordenar los nodos por su cota Y (valor en el diccionario).
    Dim sortedNodes() As Long
    If nodesDict.Count > 0 Then
        Dim nodeKeys As Variant, nodeElevations As Variant
        nodeKeys = nodesDict.Keys
        nodeElevations = nodesDict.Items
        
        ' Algoritmo de ordenamiento (Burbuja)
        Dim i As Long, j As Long, tempKey As Long, tempElev As Double
        For i = LBound(nodeKeys) To UBound(nodeKeys) - 1
            For j = i + 1 To UBound(nodeKeys)
                If nodeElevations(j) < nodeElevations(i) Then
                    ' Intercambiar elevaciones
                    tempElev = nodeElevations(i)
                    nodeElevations(i) = nodeElevations(j)
                    nodeElevations(j) = tempElev
                    ' Intercambiar claves (IDs de nodo)
                    tempKey = nodeKeys(i)
                    nodeKeys(i) = nodeKeys(j)
                    nodeKeys(j) = tempKey
                End If
            Next j
        Next i
        ' ReDim y copiar las claves ordenadas al array de salida.
        ReDim sortedNodes(LBound(nodeKeys) To UBound(nodeKeys))
        For i = LBound(nodeKeys) To UBound(nodeKeys)
            sortedNodes(i) = nodeKeys(i)
        Next i
    Else
        ReDim sortedNodes(0 To -1) ' Array vacío
    End If
    
    GetColumnNodesSortedByHeight = sortedNodes
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: IsNodeBracedInDirection (Versión 12.1 - Lógica Direccional Estricta y Descarte Explícito)
' Propósito: Implementa la solución definitiva para la validación de nodos.
'            1. Descarta explícitamente los miembros del grupo "_ARRIOST_VERT".
'            2. Utiliza una verificación geométrica estricta (ratio de 10:1) para determinar la dirección
'               predominante de las vigas, eliminando la ambigüedad.
'-------------------------------------------------------------------------------------------------------------------------------
Function IsNodeBracedInDirection(ByVal nodeID As Long, ByVal sourcePmID As Long, ByVal sourceAmID As Long, ByVal direction As String) As Boolean
    ' Por defecto, un nodo no es un nivel de entrepiso hasta que se demuestre lo contrario.
    IsNodeBracedInDirection = False
    
    Dim dictKey As Variant
    Dim memberData As Variant
    Dim beamNodeA As Long
    Dim beamNodeB As Long
    Dim beamPmID As Long
    Dim beamGroup As String
    
    ' Iterar a través de todos los miembros del modelo para encontrar uno que califique este nodo.
    For Each dictKey In g_memberNodesDict.Keys
        memberData = g_memberNodesDict.Item(dictKey)
        beamNodeA = CLng(memberData(0))
        beamNodeB = CLng(memberData(1))
        
        ' Considerar solo miembros conectados al nodo de interés.
        If beamNodeA = nodeID Or beamNodeB = nodeID Then
            beamPmID = CLng(memberData(3))
            beamGroup = UCase(CStr(memberData(4))) ' Convertir a mayúsculas una sola vez
            
            ' --- INICIO DE LA LÓGICA DE FILTRADO Y DESCARTE ---
            
            ' Filtro 1: Descartar si es parte de la misma columna que estamos analizando.
            Dim isPartOfSourceColumn As Boolean
            isPartOfSourceColumn = False
            If sourcePmID <> 0 And beamPmID = sourcePmID Then
                isPartOfSourceColumn = True
            End If
            If sourcePmID = 0 And CLng(dictKey) = sourceAmID Then
                isPartOfSourceColumn = True
            End If
            
            ' Filtro 2: Descartar si es otra columna.
            Dim isAnotherColumn As Boolean
            isAnotherColumn = (InStr(1, beamGroup, "_COLUMNAS_") > 0)
            
            ' Filtro 3 (CRUCIAL): Descartar si es un arriostramiento vertical.
            Dim isVerticalBrace As Boolean
            isVerticalBrace = (beamGroup = "_ARRIOST_VERT")
            
            ' --- FIN DE LA LÓGICA DE FILTRADO Y DESCARTE ---
            
            ' Si el miembro pasa todos los filtros, procedemos con el análisis geométrico.
            If Not isPartOfSourceColumn And Not isAnotherColumn And Not isVerticalBrace Then
            
                ' Verificación de Horizontalidad
                Dim nodeACoords As Variant
                Dim nodeBCoords As Variant
                nodeACoords = g_nodeCoordsDict.Item(beamNodeA)
                nodeBCoords = g_nodeCoordsDict.Item(beamNodeB)
                
                If Abs(CDbl(nodeACoords(1)) - CDbl(nodeBCoords(1))) < 0.1 Then ' Filtro de Horizontalidad
                    
                    ' --- LÓGICA DIRECCIONAL ESTRICTA (NUEVA Y ROBUSTA) ---
                    Dim deltaX As Double
                    Dim deltaZ As Double
                    deltaX = Abs(CDbl(nodeACoords(0)) - CDbl(nodeBCoords(0)))
                    deltaZ = Abs(CDbl(nodeACoords(2)) - CDbl(nodeBCoords(2)))
                    
                    Dim beamIsInRequestedDirection As Boolean
                    beamIsInRequestedDirection = False
                    
                    ' Constante para definir qué tan "predominante" debe ser una dirección.
                    ' Un ratio de 10.0 significa que la proyección en un eje debe ser al menos 10 veces
                    ' mayor que en el otro para ser considerada en esa dirección.
                    Const DIRECTIONAL_TOLERANCE_RATIO As Double = 10.0
                    
                    If direction = "X" Then
                        ' Califica para X si es casi perfectamente ortogonal a Z...
                        If deltaZ < 0.001 Then
                            If deltaX > 0.001 Then
                                beamIsInRequestedDirection = True
                            End If
                        ' ...o si su proyección en X es significativamente mayor que en Z.
                        ElseIf (deltaX / deltaZ) > DIRECTIONAL_TOLERANCE_RATIO Then
                            beamIsInRequestedDirection = True
                        End If
                    ElseIf direction = "Z" Then
                        ' Califica para Z si es casi perfectamente ortogonal a X...
                        If deltaX < 0.001 Then
                            If deltaZ > 0.001 Then
                                beamIsInRequestedDirection = True
                            End If
                        ' ...o si su proyección en Z es significativamente mayor que en X.
                        ElseIf (deltaZ / deltaX) > DIRECTIONAL_TOLERANCE_RATIO Then
                            beamIsInRequestedDirection = True
                        End If
                    End If
                    ' --- FIN DE LA LÓGICA DIRECCIONAL ESTRICTA ---
                    
                    ' Si el miembro es efectivo en la dirección SOLICITADA, la última verificación es si conecta a otra columna.
                    If beamIsInRequestedDirection Then
                        Dim oppositeNodeID As Long
                        If beamNodeA = nodeID Then
                            oppositeNodeID = beamNodeB
                        Else
                            oppositeNodeID = beamNodeA
                        End If
                        
                        If ConnectsToDifferentColumn(oppositeNodeID, beamPmID, sourcePmID, sourceAmID) Then
                            ' ¡ÉXITO! Hemos encontrado un arriostramiento válido.
                            IsNodeBracedInDirection = True ' Calificamos el nodo.
                            Exit Function ' No necesitamos seguir buscando.
                        End If
                    End If
                End If ' Fin del filtro de horizontalidad
            End If ' Fin de la condición de filtrado
        End If ' Fin de la verificación de conexión al nodo
    Next dictKey
    
    ' Si el bucle termina, no se encontró ningún miembro calificante. La función devolverá False.
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: ConnectsToDifferentColumn (Versión 2 - Robusta)
' Propósito: Verifica si un nodo (o el extremo de un PM) se conecta a una columna diferente a la original.
'-------------------------------------------------------------------------------------------------------------------------------
Function ConnectsToDifferentColumn(ByVal startNodeID As Long, ByVal beamPmID As Long, ByVal sourcePmID As Long, ByVal sourceAmID As Long) As Boolean
    ConnectsToDifferentColumn = False
    
    If beamPmID <> 0 Then
        ' Si la viga es un PM, debemos encontrar su nodo extremo opuesto.
        Dim pmSheet As Object, lastRow As Long, i As Long, dataRange As Variant
        Set pmSheet = g_objWorkbook.Sheets("PM")
        lastRow = pmSheet.Cells(pmSheet.Rows.Count, "A").End(xlUp).Row
        If lastRow < 2 Then Exit Function
        dataRange = pmSheet.Range("A2:E" & lastRow).Value
        
        Dim pmStartNode As Long, pmEndNode As Long
        For i = 1 To UBound(dataRange, 1)
            If CLng(dataRange(i, 1)) = beamPmID Then
                pmStartNode = CLng(dataRange(i, 4))
                pmEndNode = CLng(dataRange(i, 5))
                Exit For
            End If
        Next i
        
        ' Determinar cuál es el nodo opuesto. El nodo opuesto es el que NO está en la columna de origen.
        ' Para saberlo, necesitamos la lista de nodos de la columna de origen.
        Dim sourceColumnNodes() As Long
        sourceColumnNodes = GetColumnNodesSortedByHeight(sourcePmID, sourceAmID)
        
        Dim isStartNodeOnSource As Boolean, isEndNodeOnSource As Boolean
        isStartNodeOnSource = False
        isEndNodeOnSource = False
        For i = LBound(sourceColumnNodes) To UBound(sourceColumnNodes)
            If sourceColumnNodes(i) = pmStartNode Then isStartNodeOnSource = True
            If sourceColumnNodes(i) = pmEndNode Then isEndNodeOnSource = True
        Next i
        
        ' Si el nodo inicial del PM de la viga está en nuestra columna, verificamos el nodo final.
        If isStartNodeOnSource And Not isEndNodeOnSource Then
            If IsNodeOnDifferentColumn(pmEndNode, sourcePmID, sourceAmID) Then ConnectsToDifferentColumn = True: Exit Function
        End If
        
        ' Si el nodo final del PM de la viga está en nuestra columna, verificamos el nodo inicial.
        If isEndNodeOnSource And Not isStartNodeOnSource Then
            If IsNodeOnDifferentColumn(pmStartNode, sourcePmID, sourceAmID) Then ConnectsToDifferentColumn = True: Exit Function
        End If
        
    Else
        ' Si la viga no es un PM, simplemente verificamos su nodo opuesto.
        If IsNodeOnDifferentColumn(startNodeID, sourcePmID, sourceAmID) Then
            ConnectsToDifferentColumn = True
        End If
    End If
End Function
'-------------------------------------------------------------------------------------------------------------------------------
' Función: IsNodeOnDifferentColumn
' Propósito: Función de bajo nivel que comprueba si un ID de nodo dado pertenece a CUALQUIER columna
'            que no sea la columna de origen que estamos analizando.
'-------------------------------------------------------------------------------------------------------------------------------
Function IsNodeOnDifferentColumn(ByVal nodeID As Long, ByVal sourcePmID As Long, ByVal sourceAmID As Long) As Boolean
    IsNodeOnDifferentColumn = False
    Dim dictKey As Variant, memberData As Variant
    Dim memberPmID As Long, memberGroup As String
    
    For Each dictKey In g_memberNodesDict.Keys
        memberData = g_memberNodesDict.Item(dictKey)
        
        ' Si el miembro actual contiene el nodo que estamos verificando...
        If CLng(memberData(0)) = nodeID Or CLng(memberData(1)) = nodeID Then
            memberGroup = CStr(memberData(4))
            memberPmID = CLng(memberData(3))
            
            ' Y si ese miembro es una columna...
            If memberGroup Like "*_COLUMNAS_*" Then
                ' Y si esa columna NO es la columna original desde la que empezamos...
                Dim isSourceColumn As Boolean
                isSourceColumn = False
                If sourcePmID <> 0 And memberPmID = sourcePmID Then
                    isSourceColumn = True
                ElseIf sourceAmID <> 0 And CLng(dictKey) = sourceAmID Then
                    isSourceColumn = True
                End If
                
                If Not isSourceColumn Then
                    IsNodeOnDifferentColumn = True
                    Exit Function ' Encontramos una conexión válida.
                End If
            End If
        End If
    Next dictKey
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: AddLevelToArray
' Propósito: Añade de forma segura una nueva estructura StoryLevelInfo a un array dinámico.
'-------------------------------------------------------------------------------------------------------------------------------
Private Sub AddLevelToArray(ByRef levelsArray() As StoryLevelInfo, ByVal nodeID As Long)
    Dim newIndex As Long
    newIndex = 0
    On Error Resume Next
    newIndex = UBound(levelsArray) + 1
    On Error GoTo 0
    
    ReDim Preserve levelsArray(0 To newIndex)
    levelsArray(newIndex).NodeID = nodeID
    levelsArray(newIndex).LevelElevation = g_nodeCoordsDict.Item(nodeID)(1) ' Cota Y
End Sub

'===============================================================================================================================
' --- FIN: SECCIÓN DE FUNCIONES PARA ANÁLISIS DE DERIVAS DE ENTREPISO ---
'===============================================================================================================================

'===============================================================================================================================
' --- INICIO: SECCIÓN DE REPORTE DE DERIVAS DE ENTREPISO ---
'===============================================================================================================================

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: GenerateStoryDriftReport
' Propósito: Orquesta la creación de las 4 tablas de reporte de derivas (X-Servicio, Z-Servicio, X-Ultimas, Z-Ultimas)
'            en la hoja de Excel especificada.
'-------------------------------------------------------------------------------------------------------------------------------
Sub GenerateStoryDriftReport(ByVal targetSheet As Object, ByVal reportType As String) ' reportType será "Viento" o "Sismo"
    Dim currentRow As Long
    currentRow = 1 ' Iniciar escritura en la fila 1

    Debug.Print "--- Generando reporte de derivas para: " & reportType & " ---"
    
    ' Limpiar la hoja de destino antes de empezar
    targetSheet.Cells.Clear
    targetSheet.Cells.Font.Name = "Calibri"
    targetSheet.Cells.Font.Size = 10

    ' --- Generar las 4 tablas secuencialmente ---
    ' Tabla 1: Dirección X, Servicio
    Call CreateSingleDriftTable(targetSheet, currentRow, reportType, "Servicio", "X")
    
    ' Tabla 2: Dirección Z, Servicio
    Call CreateSingleDriftTable(targetSheet, currentRow, reportType, "Servicio", "Z")
    
    ' Tabla 3: Dirección X, Últimas
    Call CreateSingleDriftTable(targetSheet, currentRow, reportType, "Ultimas", "X")
    
    ' Tabla 4: Dirección Z, Últimas
    Call CreateSingleDriftTable(targetSheet, currentRow, reportType, "Ultimas", "Z")
    
    targetSheet.Columns.AutoFit
    Debug.Print "--- Reporte de derivas para " & reportType & " completado. ---"
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: CreateSingleDriftTable (Versión Final 4.0 - Un Caso de Carga Crítico por Columna)
' Propósito: Procesa los datos, identifica el caso de carga más crítico por columna, y luego reporta
'            las derivas de todos los entrepisos bajo ese único caso de carga.
'-------------------------------------------------------------------------------------------------------------------------------

'-------------------------------------------------------------------------------------------------------------------------------
' Subrutina: CreateSingleDriftTable (Versión 8.0 - Cálculo de Distancia Corregido y Definitivo)
' Propósito: Restaura la lógica de ordenamiento de la V6 que funcionaba correctamente. Mueve el cálculo
'            de la altura de entrepiso (h) y el desplazamiento relativo al PASO 5, garantizando que la
'            distancia siempre se calcule entre nodos consecutivos en la tabla final.
'-------------------------------------------------------------------------------------------------------------------------------
Sub CreateSingleDriftTable(ByVal ws As Object, ByRef nextRow As Long, ByVal reportType As String, ByVal loadCategory As String, ByVal direction As String)
    
    ' --- BLOQUE ÚNICO DE DECLARACIÓN DE VARIABLES ---
    Dim title As String
    Dim headers() As String
    Dim i As Long
    Dim j As Long
    Dim k As Long
    Dim criticalLoadCasesDict As Object
    Dim finalResultsDict As Object
    Dim columnKey As String
    Dim memberID As Long
    Dim pmID As Long
    Dim memberGroup As String
    Dim currentEnvType As String
    Dim loadCaseID As Long
    Dim targetEnvType As String
    Dim storyLevelsByDirection As Object
    Dim levels() As StoryLevelInfo
    Dim topNodeID As Long
    Dim bottomNodeID As Long
    Dim topDisp() As Double
    Dim bottomDisp() As Double
    Dim dispRel As Double
    Dim storeyHeight As Double
    Dim dispAbs As Double
    Dim factor As Double
    Dim permissible As Double
    Dim complies As String
    Dim ratio As Double
    Dim sortedColumnKeys() As String
    Dim columnData As Object
    Dim dictKey As Variant
    Dim firstRowForColumn As Long
    Dim dispRelModificado As Double
    Dim modFactor As Double
    
    ' --- PASO 1: PRIMERA PASADA - Identificar el caso de carga crítico por columna (Lógica V6 sin cambios) ---
    Set criticalLoadCasesDict = CreateObject("Scripting.Dictionary")
    targetEnvType = reportType & "-" & loadCategory
    
    For j = 1 To UBound(resultsArray, 1)
        memberID = resultsArray(j, 1)
        pmID = resultsArray(j, 2)
        memberGroup = resultsArray(j, 3)
        currentEnvType = resultsArray(j, 6)
        loadCaseID = resultsArray(j, 5)
        
        If (memberGroup = "_COLUMNAS_PRIN" Or memberGroup = "_COLUMNAS_SEC") And currentEnvType = targetEnvType Then
            If pmID <> 0 Then
                columnKey = "PM_" & pmID
            Else
                columnKey = "AM_" & memberID
            End If
            
            Static storyLevelCache As Object
            If storyLevelCache Is Nothing Then
                Set storyLevelCache = CreateObject("Scripting.Dictionary")
            End If
            
            If Not storyLevelCache.Exists(columnKey) Then
                Set storyLevelsByDirection = GetStoryLevelsForColumn(pmID, memberID)
                storyLevelCache.Add columnKey, storyLevelsByDirection
            Else
                Set storyLevelsByDirection = storyLevelCache.Item(columnKey)
            End If
            
            If storyLevelsByDirection.Exists(direction) Then
                levels = storyLevelsByDirection.Item(direction)
                If UBound(levels) >= 1 Then
                    For k = 1 To UBound(levels)
                        topNodeID = levels(k).NodeID
                        bottomNodeID = levels(k - 1).NodeID
                        topDisp = g_nodalDisplacementsDict.Item(topNodeID & "_" & loadCaseID)
                        bottomDisp = g_nodalDisplacementsDict.Item(bottomNodeID & "_" & loadCaseID)
                        storeyHeight = Abs(levels(k).LevelElevation - levels(k - 1).LevelElevation)
                        
                        If storeyHeight > 0.1 Then
                            If direction = "X" Then
                                dispRel = Abs(topDisp(0) - bottomDisp(0)) * conversionFactorToMM
                            Else
                                dispRel = Abs(topDisp(2) - bottomDisp(2)) * conversionFactorToMM
                            End If
                            
                            If reportType = "Sismo" Then
                                modFactor = 1#
                                Select Case loadCategory
                                    Case "Servicio"
                                        If direction = "X" Then
                                            modFactor = g_FactorSismoModServicioX
                                        Else
                                            modFactor = g_FactorSismoModServicioZ
                                        End If
                                    Case "Ultimas"
                                        If direction = "X" Then
                                            modFactor = g_FactorSismoModUltimasX
                                        Else
                                            modFactor = g_FactorSismoModUltimasZ
                                        End If
                                End Select
                                dispRelModificado = dispRel * modFactor
                                Call VerifyDrift(dispRelModificado, storeyHeight, currentEnvType, factor, permissible, complies, ratio)
                            Else
                                Call VerifyDrift(dispRel, storeyHeight, currentEnvType, factor, permissible, complies, ratio)
                            End If
                            
                            If Not criticalLoadCasesDict.Exists(columnKey) Then
                                criticalLoadCasesDict.Add columnKey, Array(loadCaseID, ratio)
                            Else
                                Dim existingCritData As Variant
                                existingCritData = criticalLoadCasesDict.Item(columnKey)
                                If ratio > CDbl(existingCritData(1)) Then
                                    criticalLoadCasesDict.Item(columnKey) = Array(loadCaseID, ratio)
                                End If
                            End If
                        End If
                    Next k
                End If
            End If
        End If
    Next j
    
    ' --- PASO 2: SEGUNDA PASADA - Almacenar solo los datos ABSOLUTOS necesarios ---
    Set finalResultsDict = CreateObject("Scripting.Dictionary")
    
    For Each dictKey In criticalLoadCasesDict.Keys
        columnKey = CStr(dictKey)
        Dim criticalData As Variant
        criticalData = criticalLoadCasesDict.Item(dictKey)
        loadCaseID = CLng(criticalData(0))
        
        If InStr(columnKey, "PM_") > 0 Then
            pmID = CLng(Mid(columnKey, 4))
        Else
            pmID = 0
        End If
        If InStr(columnKey, "AM_") > 0 Then
            memberID = CLng(Mid(columnKey, 4))
        Else
            memberID = 0
        End If
        
        Set storyLevelsByDirection = storyLevelCache.Item(columnKey)
        levels = storyLevelsByDirection.Item(direction)
        
        Set columnData = CreateObject("Scripting.Dictionary")
        
        ' Almacenar solo el desplazamiento absoluto de cada nodo de nivel
        For k = 0 To UBound(levels)
            topNodeID = levels(k).NodeID
            topDisp = g_nodalDisplacementsDict.Item(topNodeID & "_" & loadCaseID)
            
            If direction = "X" Then
                dispAbs = topDisp(0) * conversionFactorToMM
            Else
                dispAbs = topDisp(2) * conversionFactorToMM
            End If
            
            columnData.Add topNodeID, Array(loadCaseID, dispAbs)
        Next k
        
        finalResultsDict.Add columnKey, columnData
    Next dictKey
    
    ' --- PASO 3: Si no se encontraron datos, no crear la tabla ---
    If finalResultsDict.Count = 0 Then
        ws.Cells(nextRow, 1).Value = "NO SE ENCONTRARON DATOS PARA: " & UCase(reportType) & " - DIRECCIÓN " & direction & " (" & UCase(loadCategory) & ")"
        ws.Cells(nextRow, 1).Font.Italic = True
        nextRow = nextRow + 3
        Exit Sub
    End If
    
    ' --- PASO 4: Escribir encabezados y título (Lógica V6 sin cambios) ---
    title = "VERIFICACIÓN DE DERIVAS POR " & UCase(reportType) & " - DIRECCIÓN " & direction & " (COMBINACIONES DE " & UCase(loadCategory) & ")"
    If reportType = "Sismo" Then
        headers = Split("ID,Tipo,Nodo,Caso de Carga,h (mm),Desplazamiento (mm),Desplazamiento Relativo (mm),Modificado (mm),Drift,Desplazamiento Permisible (mm),Verificación", ",")
    Else
        headers = Split("ID,Tipo,Nodo,Caso de Carga,h (mm),Desplazamiento (mm),Desplazamiento Relativo (mm),Drift,Desplazamiento Permisible (mm),Verificación", ",")
    End If
    
    ws.Cells(nextRow, 1).Value = title
    ws.Cells(nextRow, 1).Font.Bold = True
    ws.Cells(nextRow, 1).Font.Size = 12
    ws.Range(ws.Cells(nextRow, 1), ws.Cells(nextRow, UBound(headers) + 1)).Merge
    nextRow = nextRow + 1
    For i = 0 To UBound(headers)
        ws.Cells(nextRow, i + 1).Value = headers(i)
        ws.Cells(nextRow, i + 1).Font.Bold = True
    Next i
    nextRow = nextRow + 1
    
    ' --- PASO 5: Escribir los resultados con CÁLCULO DE DISTANCIA JUST-IN-TIME ---
    sortedColumnKeys = SortDictionaryKeys(finalResultsDict)
    
    For i = 0 To UBound(sortedColumnKeys)
        columnKey = sortedColumnKeys(i)
        Set columnData = finalResultsDict.Item(columnKey)
        
        If Left(columnKey, 3) = "PM_" Then
            ws.Cells(nextRow, 1).Value = CLng(Mid(columnKey, 4))
            ws.Cells(nextRow, 2).Value = "PM"
        Else
            ws.Cells(nextRow, 1).Value = CLng(Mid(columnKey, 4))
            ws.Cells(nextRow, 2).Value = "AM"
        End If
        
        ' Lógica de ordenamiento original de la V6 que funcionaba
        Dim nodeIDs() As Long
        Dim nodeElevations() As Double
        ReDim nodeIDs(0 To columnData.Count - 1)
        ReDim nodeElevations(0 To columnData.Count - 1)
        Dim idx As Long
        idx = 0
        
        For Each dictKey In columnData.Keys
            nodeIDs(idx) = CLng(dictKey)
            nodeElevations(idx) = g_nodeCoordsDict.Item(nodeIDs(idx))(1)
            idx = idx + 1
        Next dictKey
        
        Dim tempNodeID As Long
        Dim tempElev As Double
        For j = LBound(nodeIDs) To UBound(nodeIDs) - 1
            For k = j + 1 To UBound(nodeIDs)
                If nodeElevations(k) > nodeElevations(j) Then
                    tempElev = nodeElevations(j)
                    nodeElevations(j) = nodeElevations(k)
                    nodeElevations(k) = tempElev
                    tempNodeID = nodeIDs(j)
                    nodeIDs(j) = nodeIDs(k)
                    nodeIDs(k) = tempNodeID
                End If
            Next k
        Next j
        
        firstRowForColumn = nextRow
        
        ' Bucle de escritura con cálculo Just-in-Time
        For j = LBound(nodeIDs) To UBound(nodeIDs)
            topNodeID = nodeIDs(j)
            Dim resultData As Variant
            resultData = columnData.Item(topNodeID)
            loadCaseID = resultData(0)
            dispAbs = resultData(1)
            
            ws.Cells(nextRow, 3).Value = topNodeID
            ws.Cells(nextRow, 4).Value = loadCaseID
            ws.Cells(nextRow, 6).Value = Format(dispAbs, "0.00")
            
            ' Si no es el último nodo de la lista (la base), calcular y escribir los datos relativos
            If j < UBound(nodeIDs) Then
                bottomNodeID = nodeIDs(j + 1) ' El nodo consecutivo en la lista ordenada
                
                ' *** CÁLCULO PRECISO Y JUST-IN-TIME ***
                storeyHeight = Abs(g_nodeCoordsDict.Item(topNodeID)(1) - g_nodeCoordsDict.Item(bottomNodeID)(1))
                
                Dim bottomResultData As Variant
                bottomResultData = columnData.Item(bottomNodeID)
                Dim bottomDispAbs As Double
                bottomDispAbs = bottomResultData(1)
                
                dispRel = Abs(dispAbs - bottomDispAbs)
                
                ws.Cells(nextRow, 5).Value = Format(storeyHeight * 1000, "0.0")
                ws.Cells(nextRow, 7).Value = Format(dispRel, "0.00")
                
                If reportType = "Sismo" Then
                    modFactor = 1#
                    Select Case loadCategory
                        Case "Servicio"
                            If direction = "X" Then
                                modFactor = g_FactorSismoModServicioX
                            Else
                                modFactor = g_FactorSismoModServicioZ
                            End If
                        Case "Ultimas"
                            If direction = "X" Then
                                modFactor = g_FactorSismoModUltimasX
                            Else
                                modFactor = g_FactorSismoModUltimasZ
                            End If
                    End Select
                    dispRelModificado = dispRel * modFactor
                    Call VerifyDrift(dispRelModificado, storeyHeight, targetEnvType, factor, permissible, complies, ratio)
                    
                    ws.Cells(nextRow, 8).Value = Format(dispRelModificado, "0.00")
                    ws.Cells(nextRow, 9).Value = factor
                    ws.Cells(nextRow, 10).Value = Format(permissible, "0.00")
                    ws.Cells(nextRow, 11).Value = complies
                Else
                    Call VerifyDrift(dispRel, storeyHeight, targetEnvType, factor, permissible, complies, ratio)
                    ws.Cells(nextRow, 8).Value = factor
                    ws.Cells(nextRow, 9).Value = Format(permissible, "0.00")
                    ws.Cells(nextRow, 10).Value = complies
                End If
            End If
            nextRow = nextRow + 1
        Next j
        
        ws.Range(ws.Cells(firstRowForColumn, 1), ws.Cells(nextRow - 1, 1)).Merge
        ws.Range(ws.Cells(firstRowForColumn, 2), ws.Cells(nextRow - 1, 2)).Merge
        ws.Cells(firstRowForColumn, 1).VerticalAlignment = -4108
        ws.Cells(firstRowForColumn, 2).VerticalAlignment = -4108
    Next i
    
    nextRow = nextRow + 3
End Sub

'-------------------------------------------------------------------------------------------------------------------------------
' Función: SortDictionaryKeys (Versión Pura VBA)
' Propósito: Ordena las claves de un diccionario (PMs primero, luego AMs, ambos numéricamente).
'-------------------------------------------------------------------------------------------------------------------------------
Function SortDictionaryKeys(ByVal dict As Object) As String()
    Dim pmKeys() As Long, amKeys() As Long
    ReDim pmKeys(0 To -1)
    ReDim amKeys(0 To -1)
    
    Dim dictKey As Variant
    Dim pmCount As Long, amCount As Long
    pmCount = -1
    amCount = -1
    
    ' Separar las claves en dos arrays de Longs
    For Each dictKey In dict.Keys
        If Left(dictKey, 3) = "PM_" Then
            pmCount = pmCount + 1
            ReDim Preserve pmKeys(0 To pmCount)
            pmKeys(pmCount) = CLng(Mid(dictKey, 4))
        Else
            amCount = amCount + 1
            ReDim Preserve amKeys(0 To amCount)
            amKeys(amCount) = CLng(Mid(dictKey, 4))
        End If
    Next dictKey
    
    ' Ordenar cada array numéricamente (usando QuickSort si es necesario, o burbuja para simplicidad)
    If pmCount >= 0 Then Call QuickSortLong(pmKeys, 0, pmCount)
    If amCount >= 0 Then Call QuickSortLong(amKeys, 0, amCount)
    
    ' Reconstruir el array final de strings ordenado
    Dim sortedKeys() As String
    ReDim sortedKeys(0 To dict.Count - 1)
    
    Dim i As Long, idx As Long
    idx = 0
    If pmCount >= 0 Then
        For i = 0 To pmCount
            sortedKeys(idx) = "PM_" & pmKeys(i)
            idx = idx + 1
        Next i
    End If
    If amCount >= 0 Then
        For i = 0 To amCount
            sortedKeys(idx) = "AM_" & amKeys(i)
            idx = idx + 1
        Next i
    End If
    
    SortDictionaryKeys = sortedKeys
End Function


'===============================================================================================================================
' --- FIN: SECCIÓN DE REPORTE DE DERIVAS DE ENTREPISO ---
'===============================================================================================================================

'-------------------------------------------------------------------------------------------------------------------------------
' Función: GetMaxPanzaHorizontalForPM (VERSIÓN CORREGIDA V8.3)
' Propósito: Calcular la máxima deflexión horizontal leyendo desde resultsArray correctamente
'-------------------------------------------------------------------------------------------------------------------------------
Function GetMaxPanzaHorizontalForPM(ByVal pmID As Long, ByVal lcID As Long) As Double
    On Error Resume Next
    
    Dim analyticalMembers As Variant
    Dim i As Long
    Dim maxPanza As Double
    Dim currentPanza As Double
    Dim currentMemberID As Long
    Dim resultRowIndex As Long
    Dim indexKey As String
    
    maxPanza = 0
    
    ' Paso 1: Obtener lista de miembros analíticos del PM desde el caché
    If Not g_pmAnalyticalMembersDict Is Nothing Then
        If g_pmAnalyticalMembersDict.Exists(pmID) Then
            analyticalMembers = g_pmAnalyticalMembersDict.Item(pmID)
        Else
            GetMaxPanzaHorizontalForPM = 0
            Exit Function
        End If
    Else
        GetMaxPanzaHorizontalForPM = 0
        Exit Function
    End If
    
    ' Paso 2: Para cada miembro analítico, buscar su fila en resultsArray usando el índice
    If IsArray(analyticalMembers) Then
        For i = LBound(analyticalMembers) To UBound(analyticalMembers)
            currentMemberID = analyticalMembers(i)
            indexKey = currentMemberID & "_" & lcID
            
            If Not g_resultsIndexDict Is Nothing Then
                If g_resultsIndexDict.Exists(indexKey) Then
                    resultRowIndex = g_resultsIndexDict.Item(indexKey)
                    
                    ' Leer la panza horizontal de la columna 20
                    currentPanza = CDbl(resultsArray(resultRowIndex, 20))
                    
                    ' Comparar con el máximo actual
                    If Abs(currentPanza) > Abs(maxPanza) Then
                        maxPanza = currentPanza
                    End If
                End If
            End If
        Next i
    End If
    
    GetMaxPanzaHorizontalForPM = Abs(maxPanza)
    
    On Error GoTo 0
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' FUNCIÓN AUXILIAR: GetSegmentPanzaHorizontalFromResults
' Obtiene la panza horizontal (columna 20) de un segmento analítico desde el resultsArray
'-------------------------------------------------------------------------------------------------------------------------------
Private Function GetSegmentPanzaHorizontalFromResults(ByVal memberID As Long, _
                                                       ByVal lcID As Long) As Double
    
    Dim i As Long
    GetSegmentPanzaHorizontalFromResults = 0 ' Default
    
    ' Búsqueda en el resultsArray global
    For i = 1 To resultCount
        If CLng(resultsArray(i, 1)) = memberID And CLng(resultsArray(i, 5)) = lcID Then
            GetSegmentPanzaHorizontalFromResults = CDbl(resultsArray(i, 20)) ' Columna 20 = Panza DX (horizontal)
            Exit Function
        End If
    Next i
End Function

'-------------------------------------------------------------------------------------------------------------------------------
' Función: ForceCloseExcelFile (VERSIÓN CORREGIDA V8.3)
' Propósito: Cierra todas las instancias de Excel que tengan abierto un archivo específico.
'            Corrige el bug de comparación entre Name y FullName.
' Parámetros:
'   fileName (String): Nombre del archivo a cerrar (CON o SIN extensión)
' Retorna: Boolean - True si se cerró al menos una instancia, False si no se encontró el archivo abierto.
'-------------------------------------------------------------------------------------------------------------------------------
Function ForceCloseExcelFile(ByVal fileName As String) As Boolean
    On Error Resume Next
    
    Dim objExcelApp As Object
    Dim objWorkbook As Object
    Dim foundAndClosed As Boolean
    Dim attemptCount As Integer
    
    foundAndClosed = False
    
    Debug.Print "--- Verificando instancias de Excel con '" & fileName & "' abierto ---"
    
    ' Intentar obtener todas las instancias de Excel en ejecución
    Do
        Set objExcelApp = Nothing
        Set objExcelApp = GetObject(, "Excel.Application")
        
        If objExcelApp Is Nothing Then
            Debug.Print "✓ No se encontraron más instancias de Excel."
            Exit Do
        End If
        
        Debug.Print "  Instancia de Excel encontrada. Verificando libros abiertos..."
        
        ' Revisar todos los libros abiertos en esta instancia
        For Each objWorkbook In objExcelApp.Workbooks
            ' *** CORRECCIÓN CRÍTICA: Comparar con el nombre del archivo sin extensión ***
            Dim workbookNameWithoutExt As String
            Dim fileNameWithoutExt As String
            
            ' Obtener nombre del workbook sin extensión
            workbookNameWithoutExt = objWorkbook.Name
            If InStr(workbookNameWithoutExt, ".") > 0 Then
                workbookNameWithoutExt = Left(workbookNameWithoutExt, InStrRev(workbookNameWithoutExt, ".") - 1)
            End If
            
            ' Obtener fileName sin extensión
            fileNameWithoutExt = fileName
            If InStr(fileNameWithoutExt, ".") > 0 Then
                fileNameWithoutExt = Left(fileNameWithoutExt, InStrRev(fileNameWithoutExt, ".") - 1)
            End If

            ' Comparación corregida (sin distinguir mayúsculas/minúsculas)
            If StrComp(workbookNameWithoutExt, fileNameWithoutExt, vbTextCompare) = 0 Then
                Debug.Print "  ¡Archivo encontrado abierto: '" & objWorkbook.FullName & "'!"
                Debug.Print "  Intentando cerrar sin guardar..."
                
                objWorkbook.Saved = True ' Marcar como guardado para evitar prompt
                objWorkbook.Close SaveChanges:=False
                
                If Err.Number = 0 Then
                    Debug.Print "  ✓ Archivo cerrado exitosamente."
                    foundAndClosed = True
                Else
                    Debug.Print "  ✗ Error al cerrar: " & Err.Description
                    Err.Clear
                End If
            End If
        Next objWorkbook
        
        ' Si la instancia de Excel no tiene libros abiertos, cerrarla
        If objExcelApp.Workbooks.Count = 0 Then
            Debug.Print "  La instancia de Excel no tiene libros abiertos. Cerrándola..."
            objExcelApp.Quit
        End If
        
        ' Liberar objeto
        Set objExcelApp = Nothing
        
        ' Limitar intentos para evitar bucle infinito
        attemptCount = attemptCount + 1
        If attemptCount > 10 Then
            Debug.Print "⚠ Se alcanzó el límite de intentos. Saliendo del bucle."
            Exit Do
        End If
        
        ' Pequeña pausa para dar tiempo al sistema
        Sleep 100
    Loop
    
    ForceCloseExcelFile = foundAndClosed
    
    On Error GoTo 0
End Function
