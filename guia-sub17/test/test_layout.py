"""Pruebas de `guia.layout`: Cursor, área imprimible, bandas y Modelo_Paginas.

Cubre la tarea 5.1:
* constantes A4, márgenes, bandas y área imprimible coherentes,
* `reservar`/`colocar` con medición vía `afm.py` y salto de página,
* propagación de `capitulo_id`, `capitulo_titulo` y `titulo_ficha` en cada salto,
* `mantener_juntos` como context manager con punto de guardado y un reintento,
* `ErrorLayout('E_DESBORDE_TEXTO')` con folio y bloque para bloques irreparables,
* emisión del Modelo_Paginas como lista de `PaginaRender`.

_Requirements: 1.4, 1.5, 1.7, 10.4, 10.5_
"""

from __future__ import annotations

import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import afm, layout  # noqa: E402
from guia.errores import E_DESBORDE_TEXTO, ErrorLayout  # noqa: E402
from guia.layout import (  # noqa: E402
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    Cursor,
    ElementoRender,
    Anotacion,
    PaginaRender,
    Plantilla,
    TextoDatos,
    TipoElemento,
    medir_elemento,
)


def _texto(texto: str, tamano: float = 10.0) -> ElementoRender:
    return ElementoRender(
        tipo=TipoElemento.PARRAFO,
        datos=TextoDatos(texto=texto, tamano=tamano),
    )


class TestGeometria(unittest.TestCase):
    """Las constantes de página son coherentes entre sí (Req 1.4)."""

    def test_area_dentro_de_la_pagina(self):
        self.assertEqual(layout.A4_W, 595.276)
        self.assertEqual(layout.A4_H, 841.890)
        self.assertGreater(AREA_W, 0.0)
        self.assertGreater(AREA_H, 0.0)
        # El área más márgenes y bandas reconstruye la altura total.
        total = (
            layout.MARGEN_SUP
            + layout.BANDA_SUP
            + AREA_H
            + layout.BANDA_INF
            + layout.MARGEN_INF
        )
        self.assertAlmostEqual(total, layout.A4_H, places=6)
        self.assertAlmostEqual(
            AREA_W + layout.MARGEN_IZQ + layout.MARGEN_DER, layout.A4_W, places=6
        )
        self.assertEqual(AREA_X, layout.MARGEN_IZQ)
        self.assertEqual(AREA_Y, layout.MARGEN_INF + layout.BANDA_INF)


class TestMedirElemento(unittest.TestCase):
    """La altura se deriva siempre de `afm.py`, nunca se estima (Req 10.4)."""

    def test_una_linea_corta(self):
        elem = _texto("Hola", tamano=10.0)
        # Cabe en una línea -> altura = 1 * tamano * interlineado.
        self.assertAlmostEqual(medir_elemento(elem, AREA_W), 10.0 * 1.2, places=6)

    def test_texto_largo_ocupa_varias_lineas(self):
        palabra = "balon "
        texto = palabra * 200
        elem = _texto(texto, tamano=10.0)
        lineas = afm.envolver(texto, AREA_W, "Helvetica", 10.0)
        esperado = len(lineas) * 10.0 * 1.2
        self.assertGreater(len(lineas), 1)
        self.assertAlmostEqual(medir_elemento(elem, AREA_W), esperado, places=6)

    def test_tipo_fijo_usa_altura_declarada(self):
        elem = ElementoRender(tipo=TipoElemento.DIAGRAMA, h=123.0)
        self.assertEqual(medir_elemento(elem, AREA_W), 123.0)

    def test_texto_sin_payload_es_error(self):
        elem = ElementoRender(tipo=TipoElemento.PARRAFO, datos=None)
        with self.assertRaises(ErrorLayout) as caja:
            medir_elemento(elem, AREA_W)
        self.assertEqual(caja.exception.codigo, E_DESBORDE_TEXTO)


class TestCursorColocar(unittest.TestCase):

    def test_cursor_arranca_con_una_pagina(self):
        cur = Cursor()
        modelo = cur.modelo_paginas()
        self.assertEqual(len(modelo), 1)
        self.assertIsInstance(modelo[0], PaginaRender)
        self.assertEqual(modelo[0].folio, 1)
        self.assertEqual(cur.y, AREA_Y + AREA_H)

    def test_colocar_ancla_y_baja_el_cursor(self):
        cur = Cursor()
        y0 = cur.y
        elem = cur.colocar(_texto("Una linea"))
        self.assertEqual(elem.x, AREA_X)
        self.assertEqual(elem.w, AREA_W)
        self.assertAlmostEqual(elem.h, 10.0 * 1.2, places=6)
        self.assertAlmostEqual(elem.y, y0 - elem.h, places=6)
        self.assertAlmostEqual(cur.y, y0 - elem.h, places=6)
        self.assertIn(elem, cur.pagina.elementos)

    def test_desborde_vertical_salta_de_pagina(self):
        cur = Cursor()
        # Bloque que ocupa casi toda la altura del área.
        alto = ElementoRender(tipo=TipoElemento.RECT, h=AREA_H - 5.0)
        cur.colocar(alto)
        self.assertEqual(len(cur.modelo_paginas()), 1)
        # Otro bloque similar ya no cabe: debe saltar a la página 2.
        cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=AREA_H - 5.0))
        self.assertEqual(len(cur.modelo_paginas()), 2)
        self.assertEqual(cur.pagina.folio, 2)


class TestPropagacionContexto(unittest.TestCase):
    """Todo salto de página propaga capítulo y título de ficha (Req 1.5, 1.7)."""

    def test_contexto_fijado_al_construir_alcanza_la_primera_pagina(self):
        cur = Cursor(
            {
                "capitulo_id": "cap10",
                "capitulo_titulo": "Fundamentos tecnicos",
                "titulo_ficha": "Conduccion en zigzag",
                "plantilla": Plantilla.FICHA,
            }
        )
        primera = cur.modelo_paginas()[0]
        self.assertEqual(primera.capitulo_id, "cap10")
        self.assertEqual(primera.capitulo_titulo, "Fundamentos tecnicos")
        self.assertEqual(primera.titulo_ficha, "Conduccion en zigzag")
        self.assertEqual(primera.plantilla, Plantilla.FICHA)

    def test_salto_hereda_capitulo_y_ficha(self):
        cur = Cursor()
        cur.fijar_capitulo("cap10", "Fundamentos tecnicos")
        cur.fijar_ficha("Conduccion en zigzag")
        cur.fijar_plantilla(Plantilla.FICHA)
        # Forzar varios saltos con bloques altos. Las páginas abiertas después
        # de fijar el contexto (todas menos la inicial) deben heredarlo.
        for _ in range(3):
            cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=AREA_H - 5.0))
        modelo = cur.modelo_paginas()
        self.assertGreaterEqual(len(modelo), 3)
        for pagina in modelo[1:]:
            self.assertEqual(pagina.capitulo_id, "cap10")
            self.assertEqual(pagina.capitulo_titulo, "Fundamentos tecnicos")
            self.assertEqual(pagina.titulo_ficha, "Conduccion en zigzag")
            self.assertEqual(pagina.plantilla, Plantilla.FICHA)

    def test_folios_consecutivos_desde_uno(self):
        cur = Cursor()
        for _ in range(4):
            cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=AREA_H - 5.0))
        folios = [p.folio for p in cur.modelo_paginas()]
        self.assertEqual(folios, list(range(1, len(folios) + 1)))


class TestMantenerJuntos(unittest.TestCase):

    def test_grupo_que_cabe_no_salta(self):
        cur = Cursor()
        with cur.mantener_juntos(50.0):
            cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=20.0))
            cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=20.0))
        self.assertEqual(len(cur.modelo_paginas()), 1)

    def test_grupo_que_no_cabe_salta_antes_de_colocar(self):
        cur = Cursor()
        # Consumir casi toda la página, dejando poco espacio.
        cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=AREA_H - 30.0))
        self.assertEqual(len(cur.modelo_paginas()), 1)
        # Un grupo de 100 pt no cabe en lo que queda: debe empezar en pág. 2
        # y quedar entero en ella (sin viudas).
        with cur.mantener_juntos(100.0):
            a = cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=50.0))
            b = cur.colocar(ElementoRender(tipo=TipoElemento.RECT, h=50.0))
        self.assertEqual(len(cur.modelo_paginas()), 2)
        pagina2 = cur.modelo_paginas()[1]
        self.assertIn(a, pagina2.elementos)
        self.assertIn(b, pagina2.elementos)
        # La página 1 no quedó con parte del grupo.
        self.assertEqual(len(cur.modelo_paginas()[0].elementos), 1)

    def test_grupo_mas_alto_que_pagina_es_error(self):
        cur = Cursor()
        with self.assertRaises(ErrorLayout) as caja:
            with cur.mantener_juntos(AREA_H + 1.0, bloque="tabla_gigante"):
                pass
        self.assertEqual(caja.exception.codigo, E_DESBORDE_TEXTO)
        self.assertIn("bloque", caja.exception.detalle)
        self.assertIn("folio", caja.exception.detalle)


class TestDesbordeIrreparable(unittest.TestCase):
    """Bloque más alto que el área -> E_DESBORDE_TEXTO con folio (Req 10.4/10.5)."""

    def test_reservar_bloque_mas_alto_que_area(self):
        cur = Cursor()
        with self.assertRaises(ErrorLayout) as caja:
            cur.reservar(AREA_H + 10.0, bloque="parrafo_44")
        err = caja.exception
        self.assertEqual(err.codigo, E_DESBORDE_TEXTO)
        self.assertEqual(err.detalle["folio"], 1)
        self.assertEqual(err.detalle["bloque"], "parrafo_44")

    def test_colocar_texto_mas_alto_que_pagina(self):
        cur = Cursor()
        # Texto imposiblemente largo para una sola página.
        gigante = ("palabra " * 5000)
        with self.assertRaises(ErrorLayout) as caja:
            cur.colocar(_texto(gigante))
        self.assertEqual(caja.exception.codigo, E_DESBORDE_TEXTO)


class TestAnotaciones(unittest.TestCase):

    def test_anotar_agrega_a_la_pagina_actual(self):
        cur = Cursor()
        an = Anotacion(
            uri="https://example.com/v",
            rect=(10.0, 10.0, 100.0, 30.0),
            ficha_id="del_1v1",
        )
        cur.anotar(an)
        self.assertIn(an, cur.pagina.anotaciones)


if __name__ == "__main__":
    unittest.main()
