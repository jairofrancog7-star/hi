"""Pruebas del Motor_PDF (`build_pdf.py`, tarea 7.1).

Generan un PDF mínimo en un archivo temporal (que se limpia siempre) y
comprueban:

* la cabecera `%PDF-` y el `%%EOF` final;
* que el archivo **abre**: `startxref` apunta a la palabra `xref`, la tabla
  tiene una entrada por objeto y cada offset apunta a `N 0 obj`;
* que el `/Count` del árbol de páginas coincide con el Modelo_Paginas y que hay
  `/Root` con `/Catalog`;
* que **todos** los streams `/FlateDecode` se descomprimen con `zlib`;
* que un carácter fuera de WinAnsiEncoding aborta con
  `E_CARACTER_NO_CODIFICABLE`;
* que la anotación `/Link` lleva `/URI` y un rectángulo dentro de la página.

Sin `assert` de producción aquí: en pruebas sí se usa `assert*` de
`unittest.TestCase`.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
import zlib

_DIR_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"
)
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_pdf  # noqa: E402
from guia.diagram_spec import ClaseDiagrama, DiagramaSpec, Item, Mundo  # noqa: E402
from guia.errores import ErrorBuild  # noqa: E402
from guia.layout import (  # noqa: E402
    A4_H,
    A4_W,
    Anotacion,
    ElementoRender,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
)
from guia.plantillas import DiagramaDatos, QRDatos, RectDatos  # noqa: E402


def _diagrama_min() -> DiagramaSpec:
    """Un Diagrama_Cancha mínimo pero válido para ejercitar el render."""
    return DiagramaSpec(
        clase=ClaseDiagrama.CANCHA,
        mundo=Mundo(ancho_m=10.0, alto_m=10.0),
        items=(
            Item(tipo="player", x=2.0, y=2.0, numero=9),
            Item(tipo="ball", x=5.0, y=5.0),
            Item(tipo="pass", x=2.0, y=2.0, x2=5.0, y2=5.0),
        ),
    )


def _modelo_min() -> list[PaginaRender]:
    """Modelo_Paginas de dos páginas con texto, diagrama, QR y anotación."""
    url = "https://youtube.com/watch?v=cafe1"

    p1 = PaginaRender(
        folio=1,
        capitulo_id="cap10",
        capitulo_titulo="Fundamentos técnicos",
        plantilla=Plantilla.FICHA,
        titulo_ficha="Definición ante portera",
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.TEXTO,
            x=60.0,
            y=700.0,
            w=400.0,
            h=40.0,
            datos=TextoDatos(
                texto="Café con niña y peña: acentos y ñ del español.",
                fuente="Helvetica-Bold",
                tamano=12.0,
            ),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.RECT,
            x=60.0,
            y=650.0,
            w=200.0,
            h=20.0,
            datos=RectDatos(relleno="#E5197F", borde="#111"),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.DIAGRAMA,
            x=60.0,
            y=380.0,
            w=240.0,
            h=240.0,
            datos=DiagramaDatos(spec=_diagrama_min(), titulo="cancha"),
        )
    )
    p1.elementos.append(
        ElementoRender(
            tipo=TipoElemento.QR,
            x=60.0,
            y=260.0,
            w=96.0,
            h=96.0,
            datos=QRDatos(url=url),
        )
    )
    p1.anotaciones.append(
        Anotacion(uri=url, rect=(60.0, 260.0, 156.0, 356.0), ficha_id="def_1v1")
    )

    p2 = PaginaRender(
        folio=2,
        capitulo_id="cap10",
        capitulo_titulo="Fundamentos técnicos",
        plantilla=Plantilla.TEXTO,
    )
    p2.elementos.append(
        ElementoRender(
            tipo=TipoElemento.PARRAFO,
            x=60.0,
            y=600.0,
            w=460.0,
            h=120.0,
            datos=TextoDatos(
                texto=(
                    "Este parrafo es largo para forzar la envoltura del texto "
                    "en varias lineas dentro de la caja del elemento, y asi "
                    "ejercitar el operador Td de salto de linea del motor."
                ),
                tamano=10.0,
            ),
        )
    )
    return [p1, p2]


class _PdfParseado:
    """Parser mínimo de la xref para las aserciones (no es verify_pdf)."""

    def __init__(self, datos: bytes) -> None:
        self.datos = datos
        m = re.search(rb"startxref\s+(\d+)\s+%%EOF", datos)
        if m is None:
            raise ValueError("sin startxref/%%EOF")
        self.inicio_xref = int(m.group(1))

    def offsets(self) -> list[int]:
        d = self.datos
        pos = self.inicio_xref
        if not d[pos:].startswith(b"xref"):
            raise ValueError("startxref no apunta a 'xref'")
        # Cabecera de subsección: "0 N".
        m = re.match(rb"xref\r?\n(\d+)\s+(\d+)\r?\n", d[pos:])
        if m is None:
            raise ValueError("cabecera xref invalida")
        n = int(m.group(2))
        cuerpo = d[pos + m.end():]
        offs: list[int] = []
        for i in range(n):
            entrada = cuerpo[i * 20:(i + 1) * 20]
            offs.append(int(entrada[:10]))
        return offs


class TestEstructuraPDF(unittest.TestCase):
    def test_pdf_minimo_abre_y_descomprime(self) -> None:
        paginas = _modelo_min()
        datos = build_pdf.documento_a_bytes(paginas, comprimir=True)

        self.assertTrue(datos.startswith(b"%PDF-"), "falta la cabecera %PDF-")
        self.assertIn(b"%%EOF", datos[-16:], "falta %%EOF al final")

        pdf = _PdfParseado(datos)
        offs = pdf.offsets()
        # Debe haber al menos: catalog, pages, 2 fuentes, banda, 2 contenidos,
        # 1 anotacion, 2 paginas, info => 11 objetos + el libre (0).
        self.assertGreaterEqual(len(offs), 12)
        # Cada offset (salvo el 0 libre) apunta a "N 0 obj".
        for i in range(1, len(offs)):
            trozo = datos[offs[i]:offs[i] + 24]
            self.assertRegex(
                trozo,
                rb"^%d 0 obj" % i,
                f"offset del objeto {i} no apunta a 'N 0 obj'",
            )

        # /Root -> /Catalog con /Pages, y /Count == numero de paginas.
        self.assertIn(b"/Type /Catalog", datos)
        m = re.search(rb"/Count (\d+)", datos)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(1)), len(paginas))

    def test_streams_flate_se_descomprimen(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_min(), comprimir=True)
        # Todo stream FlateDecode debe descomprimir sin error.
        n = 0
        for m in re.finditer(
            rb"/Filter /FlateDecode /Length (\d+) >>\s*stream\r?\n", datos
        ):
            longitud = int(m.group(1))
            inicio = m.end()
            crudo = datos[inicio:inicio + longitud]
            zlib.decompress(crudo)  # lanza si está corrupto
            n += 1
        self.assertGreaterEqual(n, 3)  # banda + 2 contenidos como mínimo

    def test_sin_comprimir_tambien_abre(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_min(), comprimir=False)
        self.assertTrue(datos.startswith(b"%PDF-"))
        self.assertNotIn(b"/FlateDecode", datos)
        pdf = _PdfParseado(datos)
        offs = pdf.offsets()
        for i in range(1, len(offs)):
            self.assertRegex(datos[offs[i]:offs[i] + 24], rb"^%d 0 obj" % i)

    def test_anotacion_link_uri_dentro_de_pagina(self) -> None:
        datos = build_pdf.documento_a_bytes(_modelo_min(), comprimir=True)
        self.assertIn(b"/Subtype /Link", datos)
        self.assertIn(b"/S /URI /URI (https://youtube.com/watch?v=cafe1)", datos)
        m = re.search(
            rb"/Rect \[([-\d. ]+)\]", datos
        )
        self.assertIsNotNone(m)
        valores = [float(v) for v in m.group(1).split()]
        self.assertEqual(len(valores), 4)
        x0, y0, x1, y1 = valores
        for v, alto in ((x0, False), (x1, False), (y0, True), (y1, True)):
            limite = A4_H if alto else A4_W
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, limite + 1e-6)

    def test_anotacion_fuera_de_pagina_se_recorta(self) -> None:
        url = "https://ej.mx/v"
        pagina = PaginaRender(
            folio=1,
            capitulo_id="c",
            capitulo_titulo="C",
            plantilla=Plantilla.FICHA,
        )
        pagina.elementos.append(
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                x=60.0,
                y=700.0,
                w=200.0,
                h=20.0,
                datos=TextoDatos(texto="hola"),
            )
        )
        # Rectángulo que se sale de la página por los cuatro lados.
        pagina.anotaciones.append(
            Anotacion(uri=url, rect=(-50.0, -20.0, A4_W + 80.0, A4_H + 40.0),
                      ficha_id="x")
        )
        datos = build_pdf.documento_a_bytes([pagina], comprimir=True)
        m = re.search(rb"/Rect \[([-\d. ]+)\]", datos)
        self.assertIsNotNone(m)
        x0, y0, x1, y1 = (float(v) for v in m.group(1).split())
        self.assertGreaterEqual(x0, 0.0)
        self.assertGreaterEqual(y0, 0.0)
        self.assertLessEqual(x1, A4_W + 1e-6)
        self.assertLessEqual(y1, A4_H + 1e-6)


class TestCodificacionTexto(unittest.TestCase):
    def test_acentos_y_enie_se_codifican(self) -> None:
        # No debe lanzar: todos los caracteres están en WinAnsi/cp1252.
        datos = build_pdf.documento_a_bytes(_modelo_min(), comprimir=True)
        self.assertTrue(datos.startswith(b"%PDF-"))

    def test_caracter_no_codificable_aborta(self) -> None:
        pagina = PaginaRender(
            folio=1,
            capitulo_id="c",
            capitulo_titulo="C",
            plantilla=Plantilla.TEXTO,
        )
        pagina.elementos.append(
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                x=60.0,
                y=700.0,
                w=200.0,
                h=20.0,
                datos=TextoDatos(texto="emoji fuera de WinAnsi: \U0001F600"),
            )
        )
        with self.assertRaises(ErrorBuild) as caja:
            build_pdf.documento_a_bytes([pagina], comprimir=True)
        self.assertEqual(caja.exception.codigo, "E_CARACTER_NO_CODIFICABLE")


class TestEscritorPDF(unittest.TestCase):
    def test_id_reservado_no_escrito_falla_al_cerrar(self) -> None:
        fd, ruta = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            with self.assertRaises(ErrorBuild) as caja:
                esc = build_pdf.EscritorPDF(ruta, comprimir=True)
                raiz = esc.reservar_id()
                esc.reservar_id()  # nunca se escribe -> debe fallar
                info = esc.obj(b"<< /Title (x) >>")
                esc.obj(b"<< /Type /Catalog >>", oid=raiz)
                esc.cerrar(raiz, info)
            self.assertEqual(caja.exception.codigo, "E_PDF_CORRUPTO")
        finally:
            try:
                os.remove(ruta)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
