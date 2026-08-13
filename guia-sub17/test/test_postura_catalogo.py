"""Cableado de la ilustracion de tecnica al catalogo real (tarea 33.2).

El motor de figuras puede estar perfecto y el build seguir reportando
`posturas: 0`: el contador del reporte cuenta **fichas con `postura` distinta de
None**, no ilustraciones registradas. Estas pruebas cubren justo esa costura, de
punta a punta:

* el adaptador `schema_json.ficha_json_a_ficha` cuelga la ilustracion de la
  Ficha_JSON, de modo que al adaptar `contenido/ejercicios.json` al menos una
  ficha queda con `postura`;
* lo que cuelga es un `DiagramaSpec` de clase POSTURA (lo que los dos
  renderizadores ya saben dibujar);
* una ficha que no es de golpeo queda con `postura is None`, que es un resultado
  legitimo y no un fallo del mapeo;
* el reporte del build publica `posturas > 0`.

_Requirements: 9.2, 10.6_
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

from guia import build, figuras, schema_json  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.diagram_spec import ClaseDiagrama, DiagramaSpec  # noqa: E402

#: Ficha del catalogo real que no es de golpeo: no le toca ilustracion.
_ID_SIN_POSTURA = "prevencion-fifa-11-plus"


def _fichas_adaptadas() -> tuple[object, ...]:
    """Adapta el Catalogo_JSON real a `FichaEjercicio` (sin cache del capitulo)."""
    crudas = schema_json.cargar_catalogo(cap10_fundamentos.ruta_catalogo())
    return tuple(
        schema_json.ficha_json_a_ficha(ficha, indice=indice)
        for indice, ficha in enumerate(crudas)
    )


#: Minimo de fichas con `postura` en el catalogo real. Cerrado el lote 3 (las
#: diez ilustraciones) el mapeo cablea 21 fichas; el umbral se deja en 20 para no
#: romperse por un ajuste menor de redaccion, pero nunca debe bajar.
_MINIMO_FICHAS_CON_POSTURA = 20


def _ids_de_figura_usados() -> set[str]:
    """Ids de ilustracion que el mapeo asigna a alguna ficha del catalogo real."""
    crudas = schema_json.cargar_catalogo(cap10_fundamentos.ruta_catalogo())
    usados = {figuras.id_figura_para(ficha) for ficha in crudas}
    usados.discard(None)
    return {str(fid) for fid in usados}


class TestPosturaEnCatalogoReal(unittest.TestCase):
    """El adaptador cuelga la ilustracion de las fichas que le toca."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fichas = _fichas_adaptadas()

    def test_al_menos_una_ficha_queda_con_postura(self) -> None:
        con_postura = [f for f in self.fichas if getattr(f, "postura", None) is not None]
        self.assertGreaterEqual(
            len(con_postura),
            _MINIMO_FICHAS_CON_POSTURA,
            "el catalogo real quedo con menos fichas ilustradas de las que el "
            "mapeo del lote 3 debe cablear",
        )

    def test_las_diez_ilustraciones_se_usan_al_menos_una_vez(self) -> None:
        # Una ilustracion que ninguna ficha usa es codigo muerto en el catalogo.
        self.assertEqual(_ids_de_figura_usados(), set(figuras.ids_figuras()))

    def test_la_postura_es_un_diagrama_spec_de_clase_postura(self) -> None:
        con_postura = [f for f in self.fichas if getattr(f, "postura", None) is not None]
        self.assertGreater(len(con_postura), 0)
        for ficha in con_postura:
            with self.subTest(ficha=ficha.id):
                self.assertIsInstance(ficha.postura, DiagramaSpec)
                self.assertIs(ficha.postura.clase, ClaseDiagrama.POSTURA)

    def test_ficha_que_no_es_de_golpeo_queda_sin_postura(self) -> None:
        # `None` es un resultado legitimo: no se le cuelga una ilustracion que no
        # le toca.
        por_id = {f.id: f for f in self.fichas}
        self.assertIn(_ID_SIN_POSTURA, por_id)
        self.assertIsNone(por_id[_ID_SIN_POSTURA].postura)

    def test_la_ficha_de_pase_corto_con_interior_lleva_su_ilustracion(self) -> None:
        por_id = {f.id: f for f in self.fichas}
        ficha = por_id.get("golpeo-interior-pase-corto")
        self.assertIsNotNone(ficha, "falta la ficha de golpeo con el interior")
        self.assertIsNotNone(ficha.postura)
        self.assertIn("pase corto", (ficha.postura.titulo or "").lower())


class TestContadorDelReporte(unittest.TestCase):
    """El reporte del build publica el conteo de fichas con postura."""

    def test_reporte_estricto_cuenta_posturas(self) -> None:
        with tempfile.TemporaryDirectory(prefix="guia_posturas_") as tmp:
            reporte = build.construir(
                modo=build.MODO_ESTRICTO,
                dir_dist=os.path.join(tmp, "dist"),
                con_preflight=False,
            )
        self.assertGreaterEqual(reporte.posturas, _MINIMO_FICHAS_CON_POSTURA)
        self.assertIn("posturas", reporte.texto())


if __name__ == "__main__":
    unittest.main()
