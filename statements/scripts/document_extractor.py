"""Fetch the official LeyChile XML export and extract its plain text.

The output text (header + articles/chapters + promulgation + textual annexes,
minus embedded binary attachments) is what tag_attribute.py delimits over.
Run this module directly to (re)generate outputs/document.txt.
"""

import urllib.request
import xml.etree.ElementTree as ET

from paths import DOC_TXT_PATH, RAW_XML_PATH, ensure_outputs_dir

NORMA_ID = 1111283
XML_URL = f"https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma={NORMA_ID}"
LC_NS = "{http://www.leychile.cl/esquemas}"


def download_xml():
    req = urllib.request.Request(XML_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    RAW_XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_XML_PATH.write_bytes(data)
    return data


def load_xml_bytes():
    if RAW_XML_PATH.exists():
        return RAW_XML_PATH.read_bytes()
    return download_xml()


def extract_mixed_text(texto_el):
    """Concatenate a <Texto> element's own text flow.

    LeyChile inlines embedded binary attachments (e.g. scanned charts) as
    child elements inside <Texto>. We skip each child's own subtree (which
    may hold base64 image data) but keep its `.tail`, i.e. the narrative
    text that follows it, so the surrounding prose stays intact.
    """
    parts = [texto_el.text or ""]
    for child in texto_el:
        parts.append(child.tail or "")
    return "".join(parts)


def collect_body_text(estructuras_funcionales_el, out):
    for el in estructuras_funcionales_el.findall(LC_NS + "EstructuraFuncional"):
        texto = el.find(LC_NS + "Texto")
        if texto is not None:
            out.append(extract_mixed_text(texto))
        children = el.find(LC_NS + "EstructurasFuncionales")
        if children is not None:
            collect_body_text(children, out)


def build_document_text(xml_bytes):
    root = ET.fromstring(xml_bytes)
    pieces = []

    encabezado = root.find(LC_NS + "Encabezado")
    if encabezado is not None:
        texto = encabezado.find(LC_NS + "Texto")
        if texto is not None:
            pieces.append(extract_mixed_text(texto))

    body = []
    ef_root = root.find(LC_NS + "EstructurasFuncionales")
    if ef_root is not None:
        collect_body_text(ef_root, body)
    pieces.extend(body)

    promulgacion = root.find(LC_NS + "Promulgacion")
    if promulgacion is not None:
        texto = promulgacion.find(LC_NS + "Texto")
        if texto is not None:
            pieces.append(extract_mixed_text(texto))

    anexos = root.find(LC_NS + "Anexos")
    if anexos is not None:
        for anexo in anexos.findall(LC_NS + "Anexo"):
            texto = anexo.find(LC_NS + "Texto")
            if texto is not None:
                pieces.append(extract_mixed_text(texto))

    return "".join(pieces)


def get_document_text():
    """Return the extracted plain text, writing/refreshing document.txt."""
    doc_text = build_document_text(load_xml_bytes())
    ensure_outputs_dir()
    with open(DOC_TXT_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(doc_text)
    return doc_text


def main():
    doc_text = get_document_text()
    print(f"Wrote {len(doc_text):,} chars -> {DOC_TXT_PATH}")


if __name__ == "__main__":
    main()
