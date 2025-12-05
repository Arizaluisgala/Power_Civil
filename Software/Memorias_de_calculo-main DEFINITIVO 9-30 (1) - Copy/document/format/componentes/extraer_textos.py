def extraer_textos_header(header):
    textos = []
    for t in header._element.xpath('.//w:t'):
        txt = t.text.strip() if t.text else ""
        if txt and txt not in textos:
            textos.append(txt)
    return textos