"""Pruebas del Target_PDF_Guia: `dist/guia.pdf` una ficha por hoja (tarea 22.1/22.2).

Verifica que `build_guia_pdf`:

* produce **una hoja por ficha** (una `PaginaRender` por cada Ficha_JSON real);
* coloca en cada hoja su Diagrama_Cancha, la dosis/montaje y **un QR por cada
  Media_Item** de la ficha (misma cuenta de QR que de enlaces del catalogo);
* cada QR **decodifica offline a su URL de origen** (round-trip con
  `qr_decode.decodificar`);
* el `guia.pdf` emitido pasa el verificador estructural `verify_pdf.verificar_pdf`
  con el conteo de hojas del modelo.

Usa `tempfile` para el PDF en disco y limpia al terminar. Solo libreria
estandar y `unittest`.

_Requirements: 12.5, 9.6, 9.7, 9.9_
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import build_guia_pdf, build_pdf, qr_decode, verify_pdf  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.layout import PaginaRender, TipoElemento  # noqa: E402


def _qr_elems(pagina: PaginaRender) -> list:
    return [e for e in pagina.elementos if e.tipo is TipoElemento.QR]


class TestModeloGuiaPDF(unittest.TestCase):
    def setUp(self) -> None:
        self.crudas = cap10_fundamentos.fichas_json()
        self.paginas = build_guia_pdf.modelo()

    def test_una_hoja_por_ficha(self) -> None:
        self.assertEqual(len(self.paginas), len(self.crudas))
        self.assertEqual(len(self.paginas), 58)
        for pagina in self.paginas:
            self.assertIsInstance(pagina, PaginaRender)

    def test_folios_consecutivos_desde_uno(self) -> None:
        folios = [p.folio for p in self.paginas]
        self.assertEqual(folios, list(range(1, len(self.paginas) + 1)))

    def test_cada_hoja_tiene_su_diagrama_de_cancha(self) -> None:
        for cruda, pagina in zip(self.crudas, self.paginas):
            with self.subTest(id=cruda["id"]):
                diagramas = [
                    e for e in pagina.elementos if e.tipo is TipoElemento.DIAGRAMA
                ]
                if cruda.get("cancha"):
                    self.assertGreaterEqual(len(diagramas), 1)

    def test_un_qr_por_media_item(self) -> None:
        for cruda, pagina in zip(self.crudas, self.paginas):
            with self.subTest(id=cruda["id"]):
                self.assertEqual(len(_qr_elems(pagina)), len(cruda["media"]))

    def test_total_qr_igual_al_total_de_enlaces(self) -> None:
        total_media = sum(len(f["media"]) for f in self.crudas)
        total_qr = sum(len(_qr_elems(p)) for p in self.paginas)
        self.assertEqual(total_qr, total_media)

    def test_cada_qr_decodifica_a_su_url(self) -> None:
        for cruda, pagina in zip(self.crudas, self.paginas):
            qrs = _qr_elems(pagina)
            urls_ficha = [m["url"] for m in cruda["media"]]
            for elem, url in zip(qrs, urls_ficha):
                with self.subTest(id=cruda["id"], url=url):
                    matriz = elem.datos.matriz
                    self.assertIsNotNone(matriz)
                    self.assertEqual(qr_decode.decodificar(matriz), url)
                    # La anotacion /Link tambien apunta a la URL (Req 9.6).
            uris = [a.uri for a in pagina.anotaciones]
            for url in urls_ficha:
                self.assertIn(url, uris)


class TestPDFEstructural(unittest.TestCase):
    def test_guia_pdf_pasa_verificador_estructural(self) -> None:
        paginas = build_guia_pdf.modelo()
        datos = build_pdf.documento_a_bytes(paginas, comprimir=True, titulo="Guia")
        informe = verify_pdf.verificar_pdf(datos, paginas_esperadas=len(paginas))
        self.assertEqual(informe.paginas, len(paginas))

    def test_escribir_en_disco_y_verificar(self) -> None:
        fd, ruta = tempfile.mkstemp(suffix=".pdf", prefix="guia_target_")
        os.close(fd)
        try:
            paginas = build_guia_pdf.escribir(ruta, comprimir=True)
            self.assertTrue(os.path.isfile(ruta))
            informe = verify_pdf.verificar_archivo(ruta, paginas_esperadas=len(paginas))
            self.assertEqual(informe.paginas, len(paginas))
        finally:
            if os.path.exists(ruta):
                os.remove(ruta)


if __name__ == "__main__":
    unittest.main()
