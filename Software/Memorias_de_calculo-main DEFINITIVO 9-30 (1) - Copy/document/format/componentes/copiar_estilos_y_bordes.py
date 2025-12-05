from docx.oxml import parse_xml
from docx.oxml.ns import qn
from lxml import etree

def copiar_estilos_y_bordes(base_doc, nuevo_doc):
    nuevo_doc.styles.element.clear()
    for elm in base_doc.styles.element:
        nuevo_doc.styles.element.append(elm)
    src_sec = base_doc.sections[0]
    dst_sec = nuevo_doc.sections[0]
    bordes = src_sec._sectPr.find(qn('w:pgBorders'))
    if bordes is not None:
        dst_sec._sectPr.append(parse_xml(etree.tostring(bordes)))