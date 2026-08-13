"""Pruebas del índice de dos pasadas con `Mapa_Paginas` (tarea 5.4).

Cubre:
* la plantilla `indice` como función pura: columna de folio de ancho fijo,
  placeholder `"000"` en la primera pasada, folios reales en la segunda, corte
  por conteo (`ENTRADAS_POR_PAGINA`) y título repetido en cada página;
* el paginador `paginar_con_indice`: reserva de páginas con `math.ceil`, punto
  fijo iterado que converge, y los fallos explícitos `E_PAGINACION_INESTABLE`
  (no converge) y `E_INDICE_DESALINEADO` (índice desalineado con las
  portadillas reales);
* que todo se reporta con `raise ErrorLayout(...)`, nunca con `assert`.

_Requirements: 1.2, 10.3_
"""

from __future__ import annotations

import math
import os
import sys
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import afm  # noqa: E402
from guia.errores import (  # noqa: E402
    E_INDICE_DESALINEADO,
    E_PAGINACION_INESTABLE,
    ErrorLayout,
)
from guia.indice import (  # noqa: E402
    IndiceCtx,
    extraer_mapa_paginas,
    paginar_con_indice,
    paginas_indice_para,
)
from guia.layout import (  # noqa: E402
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    PaginaRender,
    Plantilla,
    TipoElemento,
)
from guia.plantillas import (  # noqa: E402
    ENTRADAS_POR_PAGINA,
    FOLIO_PLACEHOLDER,
    DatosIndice,
    EntradaIndice,
    indice,
)

_TOL = 1e-3
_Y_TOPE = AREA_Y + AREA_H


def _todos_los_elementos(paginas):
    for pagina in paginas:
        for elem in pagina.elementos:
            yield elem


def _dentro_del_area(caso, paginas):
    for elem in _todos_los_elementos(paginas):
        caso.assertGreaterEqual(elem.x + _TOL, AREA_X)
        caso.assertLessEqual(elem.x + elem.w - _TOL, AREA_X + AREA_W)
        caso.assertGreaterEqual(elem.y + _TOL, AREA_Y)
        caso.assertLessEqual(elem.y + elem.h - _TOL, _Y_TOPE)


def _entradas(n: int) -> list[EntradaIndice]:
    return [
        EntradaIndice(titulo=f"Capítulo {i}", capitulo_id=f"cap{i:02d}", nivel=0)
        for i in range(n)
    ]


# --------------------------------------------------------------------------- #
# Renderizador sintético: portada + índice + capítulos con folios consecutivos
# --------------------------------------------------------------------------- #


def _hacer_renderizar(caps):
    """Devuelve (entradas_indice, renderizar).

    `caps` es una lista de tuplas ``(capitulo_id, titulo, n_paginas_contenido)``.
    El renderizador arma: 1 portada + N páginas de índice (con la plantilla real
    `indice`, cuyos `ElementoRender` se adjuntan a cada `PaginaRender`) + por
    cada capítulo una portadilla y su contenido, numerando los folios de forma
    consecutiva desde 1. El índice ocupa exactamente el mismo número de páginas
    en ambas pasadas, así que las portadillas no se mueven y el punto fijo
    converge en dos pasadas.
    """
    entradas_indice = [EntradaIndice(titulo=t, capitulo_id=cid) for cid, t, _ in caps]

    def renderizar(ctx: IndiceCtx) -> list[PaginaRender]:
        paginas: list[PaginaRender] = []
        folio = 0

        def nueva(cap_id, titulo, plantilla, elementos=None) -> None:
            nonlocal folio
            folio += 1
            paginas.append(
                PaginaRender(
                    folio=folio,
                    capitulo_id=cap_id,
                    capitulo_titulo=titulo,
                    plantilla=plantilla,
                    elementos=list(elementos) if elementos else [],
                )
            )

        nueva("_portada", "Portada", Plantilla.PORTADA)

        # Índice con la plantilla real; debe producir exactamente ctx.paginas.
        pgs_indice = indice(DatosIndice(entradas=entradas_indice, folios=ctx.folios))
        for pg in pgs_indice:
            nueva("_indice", "Índice", Plantilla.INDICE, elementos=pg.elementos)

        for cap_id, titulo, n_cont in caps:
            nueva(cap_id, titulo, Plantilla.PORTADILLA_CAPITULO)
            for _ in range(n_cont):
                nueva(cap_id, titulo, Plantilla.TEXTO)

        return paginas

    return entradas_indice, renderizar


# --------------------------------------------------------------------------- #
# La plantilla `indice`
# --------------------------------------------------------------------------- #


class TestPlantillaIndice(unittest.TestCase):
    def test_placeholder_en_primera_pasada(self):
        pgs = indice(DatosIndice(entradas=_entradas(3), folios=None))
        folios = [
            e.datos.texto
            for e in _todos_los_elementos(pgs)
            if e.tipo is TipoElemento.TEXTO and e.datos.texto == FOLIO_PLACEHOLDER
        ]
        self.assertEqual(len(folios), 3)
        _dentro_del_area(self, pgs)

    def test_folios_reales_en_segunda_pasada(self):
        entradas = _entradas(3)
        mapa = {"cap00": 12, "cap01": 40, "cap02": 133}
        pgs = indice(DatosIndice(entradas=entradas, folios=mapa))
        textos = [
            e.datos.texto
            for e in _todos_los_elementos(pgs)
            if e.tipo is TipoElemento.TEXTO
        ]
        for folio in ("12", "40", "133"):
            self.assertIn(folio, textos)
        self.assertNotIn(FOLIO_PLACEHOLDER, textos)

    def test_altura_de_fila_no_depende_del_folio(self):
        # La estabilidad del punto fijo descansa en esto: mismas cajas de texto
        # (posición y alto) con placeholder y con folios reales.
        entradas = _entradas(5)
        mapa = {e.capitulo_id: (i + 1) * 7 for i, e in enumerate(entradas)}
        p1 = indice(DatosIndice(entradas=entradas, folios=None))
        p2 = indice(DatosIndice(entradas=entradas, folios=mapa))
        self.assertEqual(len(p1), len(p2))
        # Mismo número de elementos por página (mismas filas).
        self.assertEqual(
            [len(pg.elementos) for pg in p1],
            [len(pg.elementos) for pg in p2],
        )
        # Cada fila ocupa la misma posición vertical y altura en ambas pasadas:
        # eso es lo que hace estable la paginación. El folio va alineado a la
        # derecha (su borde derecho es fijo en area_der), así que su `x`/`w`
        # cambian con el número de dígitos, pero la fila no se mueve.
        area_der = AREA_X + AREA_W
        for e1, e2 in zip(_todos_los_elementos(p1), _todos_los_elementos(p2)):
            self.assertAlmostEqual(e1.y, e2.y, places=3)
            self.assertAlmostEqual(e1.h, e2.h, places=3)
        # Todos los folios (placeholder o reales) comparten borde derecho fijo.
        for pgs in (p1, p2):
            for elem in _todos_los_elementos(pgs):
                txt = elem.datos.texto
                if txt == FOLIO_PLACEHOLDER or txt.isdigit():
                    self.assertAlmostEqual(elem.x + elem.w, area_der, places=3)

    def test_columna_de_folio_de_ancho_fijo(self):
        # El placeholder de 3 dígitos es el más ancho posible; ningún folio real
        # del rango publicable lo supera.
        ancho_col = afm.medir_texto(FOLIO_PLACEHOLDER)
        for folio in (1, 9, 10, 99, 100, 300):
            self.assertLessEqual(afm.medir_texto(str(folio)), ancho_col + 1e-6)

    def test_corta_por_conteo_y_repite_titulo(self):
        n = ENTRADAS_POR_PAGINA * 2 + 3
        pgs = indice(DatosIndice(entradas=_entradas(n), folios=None, titulo="Índice"))
        self.assertEqual(len(pgs), math.ceil(n / ENTRADAS_POR_PAGINA))
        # Cada página repite el título del índice.
        for pagina in pgs:
            titulos = [
                e.datos.texto
                for e in pagina.elementos
                if e.tipo is TipoElemento.TEXTO and e.datos.texto == "Índice"
            ]
            self.assertGreaterEqual(len(titulos), 1)
        _dentro_del_area(self, pgs)

    def test_titulo_largo_se_recorta_a_una_linea(self):
        larga = "Palabra " * 60
        entradas = [EntradaIndice(titulo=larga, capitulo_id="capX")]
        pgs = indice(DatosIndice(entradas=entradas, folios=None))
        self.assertEqual(len(pgs), 1)
        _dentro_del_area(self, pgs)


# --------------------------------------------------------------------------- #
# Reserva de páginas
# --------------------------------------------------------------------------- #


class TestReserva(unittest.TestCase):
    def test_ceil_de_entradas_por_pagina(self):
        self.assertEqual(paginas_indice_para(_entradas(0)), 0)
        self.assertEqual(paginas_indice_para(_entradas(1)), 1)
        self.assertEqual(
            paginas_indice_para(_entradas(ENTRADAS_POR_PAGINA)), 1
        )
        self.assertEqual(
            paginas_indice_para(_entradas(ENTRADAS_POR_PAGINA + 1)), 2
        )


# --------------------------------------------------------------------------- #
# El paginador de dos pasadas
# --------------------------------------------------------------------------- #


class TestPaginarConIndice(unittest.TestCase):
    def test_converge_y_alinea_folios(self):
        caps = [(f"cap{i:02d}", f"Capítulo {i}", 5) for i in range(6)]
        entradas, renderizar = _hacer_renderizar(caps)
        resultado = paginar_con_indice(entradas, renderizar)

        # Converge en dos pasadas (índice estable por construcción).
        self.assertEqual(resultado.pasadas, 2)
        self.assertEqual(resultado.paginas_indice, paginas_indice_para(entradas))

        # El Mapa_Paginas apunta al folio real de cada portadilla.
        mapa_real = extraer_mapa_paginas(resultado.paginas)
        self.assertEqual(resultado.mapa, mapa_real)
        for entrada in entradas:
            self.assertIn(entrada.capitulo_id, resultado.mapa)

        # La pasada devuelta muestra folios reales en el índice (no placeholder).
        textos_indice = [
            e.datos.texto
            for pagina in resultado.paginas
            if pagina.plantilla is Plantilla.INDICE
            for e in pagina.elementos
            if e.tipo is TipoElemento.TEXTO
        ]
        for cap_id, folio in resultado.mapa.items():
            if cap_id.startswith("cap"):
                self.assertIn(str(folio), textos_indice)

    def test_folios_del_indice_coinciden_con_las_portadillas(self):
        # Property 5 en espíritu: lo que dice el índice es donde inicia el cap.
        caps = [(f"cap{i:02d}", f"Capítulo {i}", i % 4 + 1) for i in range(10)]
        entradas, renderizar = _hacer_renderizar(caps)
        resultado = paginar_con_indice(entradas, renderizar)
        for pagina in resultado.paginas:
            if pagina.plantilla is Plantilla.PORTADILLA_CAPITULO:
                self.assertEqual(resultado.mapa[pagina.capitulo_id], pagina.folio)

    def test_paginacion_inestable_falla_explicito(self):
        # Renderizador adversario: añade una página de relleno más en cada
        # pasada, así el conteo (y los folios de portadilla) nunca se estabilizan
        # y el punto fijo no converge.
        caps = [(f"cap{i:02d}", f"Capítulo {i}", 3) for i in range(5)]
        entradas_indice = [EntradaIndice(titulo=t, capitulo_id=cid) for cid, t, _ in caps]
        llamadas = {"n": 0}

        def renderizar(ctx: IndiceCtx) -> list[PaginaRender]:
            llamadas["n"] += 1
            paginas: list[PaginaRender] = []
            folio = 0

            def nueva(cap_id, titulo, plantilla) -> None:
                nonlocal folio
                folio += 1
                paginas.append(
                    PaginaRender(
                        folio=folio,
                        capitulo_id=cap_id,
                        capitulo_titulo=titulo,
                        plantilla=plantilla,
                    )
                )

            nueva("_portada", "Portada", Plantilla.PORTADA)
            for _ in indice(DatosIndice(entradas=entradas_indice, folios=ctx.folios)):
                nueva("_indice", "Índice", Plantilla.INDICE)
            # Relleno creciente: distinto en cada pasada -> nunca converge.
            for _ in range(llamadas["n"]):
                nueva("_relleno", "Relleno", Plantilla.TEXTO)
            for cap_id, titulo, n_cont in caps:
                nueva(cap_id, titulo, Plantilla.PORTADILLA_CAPITULO)
                for _ in range(n_cont):
                    nueva(cap_id, titulo, Plantilla.TEXTO)
            return paginas

        with self.assertRaises(ErrorLayout) as caja:
            paginar_con_indice(entradas_indice, renderizar)
        self.assertEqual(caja.exception.codigo, E_PAGINACION_INESTABLE)

    def test_indice_desalineado_falla_explicito(self):
        # Una entrada del índice apunta a un capítulo que no existe (sin
        # portadilla): debe detectarse como índice desalineado.
        caps = [(f"cap{i:02d}", f"Capítulo {i}", 3) for i in range(4)]
        entradas, renderizar = _hacer_renderizar(caps)
        entradas = list(entradas) + [
            EntradaIndice(titulo="Capítulo fantasma", capitulo_id="cap_fantasma")
        ]
        with self.assertRaises(ErrorLayout) as caja:
            paginar_con_indice(entradas, renderizar)
        self.assertEqual(caja.exception.codigo, E_INDICE_DESALINEADO)

    def test_max_pasadas_invalido(self):
        caps = [("cap00", "Uno", 1)]
        entradas, renderizar = _hacer_renderizar(caps)
        with self.assertRaises(ErrorLayout) as caja:
            paginar_con_indice(entradas, renderizar, max_pasadas=1)
        self.assertEqual(caja.exception.codigo, E_PAGINACION_INESTABLE)


if __name__ == "__main__":
    unittest.main()
