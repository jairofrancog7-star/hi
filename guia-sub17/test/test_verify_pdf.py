"""Pruebas del Verificador_PDF (`verify_pdf.py`, tarea 7.4).

Comprueban que:

* el PDF que emite `build_pdf` **pasa** el verificador estructural, tanto
  comprimido como sin comprimir;
* el PDF de control de 2 páginas se genera y verifica en cada build;
* un PDF **corrupto** se detecta con el código correcto:
  - un offset de la xref roto            -> `E_PDF_CORRUPTO`
  - un `/Count` que no coincide          -> `E_PDF_CORRUPTO`
  - un stream que no descomprime          -> `E_PDF_CORRUPTO`
  - una coordenada fuera de la página     -> `E_PDF_CORRUPTO`
  - un `BT` sin `ET` (u operador huérfano) -> `E_OPERADORES_DESBALANCEADOS`

Sin `assert` de producción: aquí se usan las aserciones de `unittest`.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_DIR_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"
)
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_pdf, verify_pdf  # noqa: E402
from guia.diagram_spec import ClaseDiagrama, DiagramaSpec, Item, Mundo  # noqa: E402
from guia.errores import (  # noqa: E402
    E_OPERADORES_DESBALANCEADOS,
    E_PDF_CORRUPTO,
    ErrorPDF,
)
from guia.layout import (  # noqa: E402
    Anotacion,
    ElementoRender,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
)
from guia.plantillas import DiagramaDatos, QRDatos, RectDatos  # noqa: E402


def _modelo_rico() -> list[PaginaRender]:
    """Modelo_Paginas de 2 páginas con texto, rect, diagrama, QR y anotación."""
    url = "https://youtube.com/watch?v=cafe1"
    spec = DiagramaSpec(
        clase=ClaseDiagrama.CANCHA,
        mundo=Mundo(ancho_m=10.0, alto_m=10.0),
        items=(
            Item(tipo="player", x=2.0, y=2.0, numero=9),
            Item(tipo="ball", x=5.0, y=5.0),
            Item(tipo="pass", x=2.0, y=2.0, x2=5.0, y2=5.0),
        ),
    )
    p1 = PaginaRender(
        folio=1,
        capitulo_id="cap10",
        capitulo_titulo="Fundamentos técnicos",
        plantilla=Plantilla.FICHA,
        titulo_ficha="Definición ante portera",
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.TEXTO, x=60.0, y=700.0, w=400.0, h=40.0,
            datos=TextoDatos(texto="Café con niña y peña.", fuente="Helvetica-Bold",
                             tamano=12.0),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.RECT, x=60.0, y=650.0, w=200.0, h=20.0,
            datos=RectDatos(relleno="#E5197F", borde="#111"),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.DIAGRAMA, x=60.0, y=380.0, w=240.0, h=240.0,
            datos=DiagramaDatos(spec=spec, titulo="cancha"),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.QR, x=60.0, y=260.0, w=96.0, h=96.0,
            datos=QRDatos(url=url),
        )
    )
    p1.anotaciones.append(
        Anotacion(uri=url, rect=(60.0, 260.0, 156.0, 356.0), ficha_id="def_1v1")
    )
    p2 = PaginaRender(
        folio=2, capitulo_id="cap10", capitulo_titulo="Fundamentos técnicos",
        plantilla=Plantilla.TEXTO,
    )
    p2.elementos.append(
        ElementoRender(
            tipo=TipoElemento.PARRAFO, x=60.0, y=600.0, w=460.0, h=120.0,
            datos=TextoDatos(
                texto=("Este parrafo se envuelve en varias lineas para ejercitar "
                       "el operador Td de salto de linea del motor, que emite "
                       "desplazamientos verticales negativos."),
                tamano=10.0,
            ),
        )
    )
    return [p1, p2]


def _pdf_una_pagina(contenido: bytes) -> bytes:
    """Ensambla a mano un PDF de 1 página con `contenido` como stream literal.

    Usa `EscritorPDF` (sin comprimir) para que la xref, los offsets y el
    `/Length` sean correctos por construcción; así el único posible defecto es
    el que inyecta el propio `contenido` (operadores desbalanceados, coordenada
    fuera de rango…), y no un desajuste de longitudes por editar bytes a mano.
    """
    fd, ruta = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        with build_pdf.EscritorPDF(ruta, comprimir=False) as esc:
            raiz = esc.reservar_id()
            pages = esc.reservar_id()
            cont_id = esc.stream("", contenido)
            page_id = esc.obj(
                (
                    f"<< /Type /Page /Parent {pages} 0 R "
                    f"/MediaBox [0 0 595 842] /Contents {cont_id} 0 R "
                    f"/Resources << >> >>"
                ).encode("ascii")
            )
            esc.obj(
                f"<< /Type /Pages /Kids [ {page_id} 0 R ] /Count 1 >>".encode("ascii"),
                oid=pages,
            )
            esc.obj(
                f"<< /Type /Catalog /Pages {pages} 0 R >>".encode("ascii"),
                oid=raiz,
            )
            info = esc.obj(b"<< /Title (control) >>")
            esc.cerrar(raiz, info)
        with open(ruta, "rb") as fh:
            return fh.read()
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass


class TestPdfValidoPasa(unittest.TestCase):
    def test_pdf_de_build_pdf_pasa_comprimido(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_rico(), comprimir=True)
        informe = verify_pdf.verificar_pdf(datos, paginas_esperadas=2)
        self.assertEqual(informe.paginas, 2)
        self.assertGreaterEqual(informe.streams, 3)

    def test_pdf_de_build_pdf_pasa_sin_comprimir(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_rico(), comprimir=False)
        informe = verify_pdf.verificar_pdf(datos, paginas_esperadas=2)
        self.assertEqual(informe.paginas, 2)

    def test_control_dos_paginas(self) -> None:
        informe = verify_pdf.verificar_control()
        self.assertEqual(informe.paginas, 2)


class TestPdfCorruptoSeDetecta(unittest.TestCase):
    def test_offset_xref_roto(self) -> None:
        import re as _re

        # PDF pequeño y determinista (sin diagramas ni QR, ajeno a la caché).
        datos = bytearray(_pdf_una_pagina(b"BT\n/F1 10 Tf\n(x) Tj\nET\n"))
        # Localizar la tabla xref real por el valor de 'startxref' (no por rfind,
        # que caería dentro de la palabra 'startxref').
        inicio = int(_re.search(rb"startxref\s+(\d+)\s+%%EOF", bytes(datos)).group(1))
        m_cab = _re.match(rb"xref\r?\n\d+\s+\d+\r?\n", bytes(datos)[inicio:])
        entradas = inicio + m_cab.end()
        # obj 0 es la entrada libre (20 bytes). Apuntar el offset del obj 1 más
        # allá del fin del archivo garantiza que no exista allí un 'N 0 obj'.
        obj1 = entradas + 20
        datos[obj1 : obj1 + 10] = b"9999999999"
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(bytes(datos))
        self.assertEqual(caja.exception.codigo, E_PDF_CORRUPTO)

    def test_count_incorrecto(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_rico(), comprimir=True)
        # El Modelo tiene 2 páginas; exigir 3 debe fallar.
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(datos, paginas_esperadas=3)
        self.assertEqual(caja.exception.codigo, E_PDF_CORRUPTO)

    def test_count_del_arbol_alterado(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_rico(), comprimir=True)
        # Cambiar "/Count 2" por "/Count 5" en el árbol de páginas.
        corrupto = datos.replace(b"/Count 2", b"/Count 5", 1)
        self.assertNotEqual(corrupto, datos)
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(corrupto, paginas_esperadas=2)
        self.assertEqual(caja.exception.codigo, E_PDF_CORRUPTO)

    def test_stream_no_descomprimible(self) -> None:
        datos = bytearray(build_pdf.documento_a_bytes(_modelo_rico(), comprimir=True))
        # Corromper los bytes justo después del primer 'stream\n' (datos zlib).
        marca = datos.index(b"stream\n") + len(b"stream\n")
        datos[marca : marca + 4] = b"\x00\x00\x00\x00"
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(bytes(datos))
        self.assertEqual(caja.exception.codigo, E_PDF_CORRUPTO)

    def test_coordenada_fuera_de_pagina(self) -> None:
        # Un 're' cuya x (9000) excede A4_W debe detectarse.
        contenido = b"q\n1 1 1 rg\n9000 20 100 100 re\nf\nQ\n"
        pdf = _pdf_una_pagina(contenido)
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(pdf, paginas_esperadas=1)
        self.assertEqual(caja.exception.codigo, E_PDF_CORRUPTO)

    def test_bt_sin_et(self) -> None:
        # 'BT' abierto y nunca cerrado: operadores desbalanceados.
        contenido = b"BT\n/F1 10 Tf\n50 700 Td\n(hola) Tj\n"
        pdf = _pdf_una_pagina(contenido)
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(pdf, paginas_esperadas=1)
        self.assertEqual(caja.exception.codigo, E_OPERADORES_DESBALANCEADOS)

    def test_q_sin_cerrar(self) -> None:
        # 'q' sin su 'Q' correspondiente.
        contenido = b"q\n1 0 0 1 0 0 cm\n0 0 100 100 re\nf\n"
        pdf = _pdf_una_pagina(contenido)
        with self.assertRaises(ErrorPDF) as caja:
            verify_pdf.verificar_pdf(pdf, paginas_esperadas=1)
        self.assertEqual(caja.exception.codigo, E_OPERADORES_DESBALANCEADOS)

    def test_pagina_una_manual_valida_pasa(self) -> None:
        # Caso positivo con el ensamblador manual: contenido balanceado y en rango.
        contenido = b"q\nBT\n/F1 10 Tf\n50 700 Td\n(ok) Tj\nET\n0 0 100 100 re\nf\nQ\n"
        pdf = _pdf_una_pagina(contenido)
        informe = verify_pdf.verificar_pdf(pdf, paginas_esperadas=1)
        self.assertEqual(informe.paginas, 1)


if __name__ == "__main__":
    unittest.main()
