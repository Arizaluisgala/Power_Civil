from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

def poner_bordes_tabla(tabla):
    tbl = tabla._element
    
    # Correct way to get tblPr
    tblPr_list = tbl.xpath("w:tblPr")
    if not tblPr_list:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    else:
        tblPr = tblPr_list[0]

    # Ensure tblLook is present and configured to not interfere with borders
    tblLook = tblPr.first_child_found_in("w:tblLook")
    if tblLook is None:
        tblLook = OxmlElement("w:tblLook")
        tblPr.append(tblLook)
    tblLook.set(qn('w:val'), "04A0")
    tblLook.set(qn('w:firstRow'), "0")
    tblLook.set(qn('w:lastRow'), "0")
    tblLook.set(qn('w:firstColumn'), "0")
    tblLook.set(qn('w:lastColumn'), "0")
    tblLook.set(qn('w:noHBand'), "1")
    tblLook.set(qn('w:noVBand'), "1")

    # Define borders
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '8')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '000000')
        tblBorders.append(border)
    
    # Remove existing borders and add new ones
    for b in tblPr.xpath("w:tblBorders"):
        tblPr.remove(b)
    tblPr.append(tblBorders)

    for row in tabla.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(12)