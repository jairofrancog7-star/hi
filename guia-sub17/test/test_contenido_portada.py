"""Pruebas del capitulo de portada y del paquete `guia.contenido` (tarea 9.1).

Verifica que:
* `cap00_portada.paginas()` produce un `list[PaginaRender]` no vacio con folios
  consecutivos y con el capitulo propagado al encabezado/pie (Req 1.5, 1.6);
* el capitulo incluye el descargo informativo (Req 6.11) y el protocolo de
  seguridad en cancha compartida con ninos y beisbol (Req 8.7);
* todo el texto del capitulo es codificable en WinAnsi (cp1252) (Req 1.6);
* `contenido/__init__.py` expone el presupuesto de paginas y el orden de
  capitulos, y concatena capitulos sin contenido propio (Req 1.2).

_Requirements: 1.2, 1.6, 6.11, 8.7_
"""

from __future__ import annotations

import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import contenido  # noqa: E402
from guia.contenido import cap00_portada  # noqa: E402
from guia.layout import PaginaRender, Plantilla, TipoElemento  # noqa: E402


def _todos_los_textos(paginas: list[PaginaRender]) -> str:
    """Concatena el texto de todos los elementos de texto de las paginas."""
    trozos: list[str] = []
    for pagina in paginas:
        for elem in pagina.elementos:
            datos = elem.datos
            texto = getattr(datos, "texto", None)
            if isinstance(texto, str):
                trozos.append(texto)
    return "\n".join(trozos)


class TestCap00Portada(unittest.TestCase):
    def test_produce_lista_de_paginas_no_vacia(self) -> None:
        paginas = cap00_portada.paginas()
        self.assertIsInstance(paginas, list)
        self.assertGreater(len(paginas), 0)
        for pagina in paginas:
            self.assertIsInstance(pagina, PaginaRender)

    def test_primera_pagina_es_portada(self) -> None:
        paginas = cap00_portada.paginas()
        self.assertIs(paginas[0].plantilla, Plantilla.PORTADA)

    def test_folios_consecutivos_desde_folio_inicial(self) -> None:
        paginas = cap00_portada.paginas(folio_inicial=5)
        folios = [pagina.folio for pagina in paginas]
        self.assertEqual(folios, list(range(5, 5 + len(paginas))))

    def test_propaga_capitulo_en_cada_pagina(self) -> None:
        paginas = cap00_portada.paginas()
        for pagina in paginas:
            self.assertEqual(pagina.capitulo_id, cap00_portada.CAPITULO_ID)
            self.assertEqual(pagina.capitulo_titulo, cap00_portada.TITULO)

    def test_incluye_descargo_informativo(self) -> None:
        texto = _todos_los_textos(cap00_portada.paginas())
        self.assertIn(cap00_portada.MARCADOR_DESCARGO, texto)
        self.assertIn("profesional de la salud", texto)

    def test_incluye_protocolo_cancha_compartida(self) -> None:
        texto = _todos_los_textos(cap00_portada.paginas())
        self.assertIn(cap00_portada.MARCADOR_PROTOCOLO, texto)
        self.assertIn("ninos", texto)
        self.assertIn("beisbol", texto)

    def test_todo_el_texto_es_codificable_en_winansi(self) -> None:
        texto = _todos_los_textos(cap00_portada.paginas())
        # No debe lanzar UnicodeEncodeError (Req 1.6: acentos y n via cp1252).
        texto.encode("cp1252")

    def test_hay_elementos_de_texto(self) -> None:
        paginas = cap00_portada.paginas()
        tipos = {
            elem.tipo for pagina in paginas for elem in pagina.elementos
        }
        self.assertIn(TipoElemento.TEXTO, tipos)


class TestPaqueteContenido(unittest.TestCase):
    def test_expone_presupuesto_de_paginas(self) -> None:
        self.assertIsInstance(contenido.PRESUPUESTO_PAGINAS, dict)
        self.assertEqual(contenido.PRESUPUESTO_PAGINAS["cap00_portada"], 8)

    def test_expone_orden_de_capitulos(self) -> None:
        self.assertEqual(contenido.ORDEN_CAPITULOS[0], "cap00_portada")
        # El orden se deriva de CAPITULOS en el mismo orden explicito.
        esperado = tuple(cap.CAPITULO_ID for cap in contenido.CAPITULOS)
        self.assertEqual(contenido.ORDEN_CAPITULOS, esperado)

    def test_concatenar_une_los_capitulos_con_folios_consecutivos(self) -> None:
        paginas = contenido.concatenar()
        self.assertGreater(len(paginas), 0)
        folios = [pagina.folio for pagina in paginas]
        self.assertEqual(folios, list(range(1, len(paginas) + 1)))

    def test_desvios_presupuesto_reporta_por_capitulo(self) -> None:
        reporte = contenido.desvios_presupuesto()
        self.assertIn("cap00_portada", reporte)
        reales, objetivo, desvio = reporte["cap00_portada"]
        self.assertGreater(reales, 0)
        self.assertEqual(objetivo, 8)
        self.assertEqual(desvio, reales - 8)


if __name__ == "__main__":
    unittest.main()
