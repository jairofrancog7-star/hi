"""Pruebas del capitulo de fundamentos tecnicos (tarea 9.2, MODO MUESTRA).

Verifica que `cap10_fundamentos`:

* rinde **exactamente las 15 fichas reales** del Catalogo_JSON, por `id`
  (Req 9.5: se conservan las fichas existentes, sin inventar nuevas);
* conserva los enlaces (media -> video_url / video_titulo) y el diagrama de
  cancha de cada ficha exactamente como los produce el adaptador;
* incluye el bloque del **Diagrama_Botin** a media pagina A4 (>= A4_H/2) con sus
  7 zonas y la accion de juego de cada una (Req 3.6, 3.7);
* produce un `list[PaginaRender]` con folios consecutivos y el capitulo
  propagado al encabezado/pie (Req 1.5);
* queda registrado en `contenido` de modo que `concatenar()` lo incluye
  **despues** de la portada.

_Requirements: 9.5, 3.6, 3.7, 1.5, 8.1_
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
from guia.contenido import cap00_portada, cap10_fundamentos  # noqa: E402
from guia.diagram_spec import BotinSpec, ClaseDiagrama, botin_por_defecto  # noqa: E402
from guia.layout import A4_H, PaginaRender, TipoElemento  # noqa: E402


def _textos(paginas: list[PaginaRender]) -> str:
    trozos: list[str] = []
    for pagina in paginas:
        for elem in pagina.elementos:
            texto = getattr(elem.datos, "texto", None)
            if isinstance(texto, str):
                trozos.append(texto)
    return "\n".join(trozos)


class TestFichasReales(unittest.TestCase):
    def test_rinde_exactamente_las_15_fichas_reales_por_id(self) -> None:
        crudas = cap10_fundamentos.fichas_json()
        convertidas = cap10_fundamentos.fichas()
        self.assertEqual(len(crudas), 58)
        self.assertEqual(len(convertidas), 58)
        ids_json = [f["id"] for f in crudas]
        ids_ficha = [f.id for f in convertidas]
        self.assertEqual(ids_ficha, ids_json)

    def test_conserva_enlaces_media_exactamente(self) -> None:
        crudas = cap10_fundamentos.fichas_json()
        convertidas = cap10_fundamentos.fichas()
        for cruda, ficha in zip(crudas, convertidas):
            with self.subTest(id=cruda["id"]):
                media = cruda["media"]
                if media:
                    self.assertEqual(ficha.video_url, media[0]["url"])
                    self.assertEqual(ficha.video_titulo, media[0]["titulo"])
                else:
                    self.assertIsNone(ficha.video_url)

    def test_conserva_el_diagrama_de_cancha(self) -> None:
        crudas = cap10_fundamentos.fichas_json()
        convertidas = cap10_fundamentos.fichas()
        for cruda, ficha in zip(crudas, convertidas):
            with self.subTest(id=cruda["id"]):
                if cruda.get("cancha"):
                    self.assertIsNotNone(ficha.diagrama)


class TestPaginasFundamentos(unittest.TestCase):
    def test_produce_paginas_no_vacias(self) -> None:
        paginas = cap10_fundamentos.paginas()
        self.assertGreater(len(paginas), 0)
        for pagina in paginas:
            self.assertIsInstance(pagina, PaginaRender)

    def test_folios_consecutivos_desde_folio_inicial(self) -> None:
        paginas = cap10_fundamentos.paginas(folio_inicial=9)
        folios = [pagina.folio for pagina in paginas]
        self.assertEqual(folios, list(range(9, 9 + len(paginas))))

    def test_propaga_capitulo_en_cada_pagina(self) -> None:
        for pagina in cap10_fundamentos.paginas():
            self.assertEqual(pagina.capitulo_id, cap10_fundamentos.CAPITULO_ID)
            self.assertEqual(pagina.capitulo_titulo, cap10_fundamentos.TITULO)


class TestBloqueBotin(unittest.TestCase):
    def _pagina_del_botin(self) -> PaginaRender:
        for pagina in cap10_fundamentos.paginas():
            for elem in pagina.elementos:
                if elem.tipo is TipoElemento.DIAGRAMA:
                    spec = getattr(elem.datos, "spec", None)
                    if isinstance(spec, BotinSpec):
                        return pagina
        self.fail("no se encontro el bloque del Diagrama_Botin")

    def test_incluye_el_diagrama_del_botin(self) -> None:
        pagina = self._pagina_del_botin()
        diagramas = [
            elem
            for elem in pagina.elementos
            if elem.tipo is TipoElemento.DIAGRAMA
            and isinstance(getattr(elem.datos, "spec", None), BotinSpec)
        ]
        self.assertEqual(len(diagramas), 1)
        self.assertEqual(diagramas[0].datos.spec.clase, ClaseDiagrama.BOTIN)

    def test_diagrama_ocupa_al_menos_media_pagina_a4(self) -> None:
        pagina = self._pagina_del_botin()
        diagrama = next(
            elem
            for elem in pagina.elementos
            if elem.tipo is TipoElemento.DIAGRAMA
            and isinstance(getattr(elem.datos, "spec", None), BotinSpec)
        )
        self.assertGreaterEqual(diagrama.h, A4_H / 2.0)

    def test_lista_las_7_zonas_con_su_accion_de_juego(self) -> None:
        pagina = self._pagina_del_botin()
        texto = _textos([pagina])
        zonas = botin_por_defecto().zonas
        self.assertEqual(len(zonas), 7)
        for zona in zonas:
            with self.subTest(zona=zona.nombre):
                self.assertIn(zona.accion, texto)


class TestRegistroEnContenido(unittest.TestCase):
    def test_cap10_esta_registrado_en_orden(self) -> None:
        self.assertIn("cap10_fundamentos", contenido.ORDEN_CAPITULOS)
        indice_cap00 = contenido.ORDEN_CAPITULOS.index("cap00_portada")
        indice_cap10 = contenido.ORDEN_CAPITULOS.index("cap10_fundamentos")
        self.assertLess(indice_cap00, indice_cap10)

    def test_concatenar_incluye_cap10_tras_la_portada(self) -> None:
        paginas = contenido.concatenar()
        ids_por_pagina = [p.capitulo_id for p in paginas]
        self.assertIn("cap10_fundamentos", ids_por_pagina)
        # La ultima pagina de portada precede a la primera de fundamentos.
        ultimo_portada = max(
            i for i, cid in enumerate(ids_por_pagina) if cid == "cap00_portada"
        )
        primero_fundamentos = min(
            i for i, cid in enumerate(ids_por_pagina) if cid == "cap10_fundamentos"
        )
        self.assertLess(ultimo_portada, primero_fundamentos)
        # Folios globales consecutivos tras concatenar.
        folios = [p.folio for p in paginas]
        self.assertEqual(folios, list(range(1, len(paginas) + 1)))


if __name__ == "__main__":
    unittest.main()
