"""Pruebas de `guia.plantillas`: las 8 plantillas de página y el registro.

Cubre la tarea 5.2:
* `portada`, `portadilla_capitulo`, `ficha`, `ficha_doble`, `tabla`,
  `lamina_vertical`, `apendice_qr`, `texto` como funciones puras
  `(datos, ctx) -> list[PaginaPlantilla]`,
* medición de toda altura vía `afm.py` (los elementos caben en el área),
* `tabla` corta por filas y **repite la cabecera** en cada página,
* el `Enum Plantilla` y `REGISTRO_PLANTILLAS` cubren las 8 plantillas.

_Requirements: 1.5, 1.7, 9.6, 10.4_
"""

from __future__ import annotations

import os
import sys
import types
import unittest

_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import plantillas  # noqa: E402
from guia.layout import (  # noqa: E402
    AREA_H,
    AREA_W,
    AREA_X,
    AREA_Y,
    Plantilla,
    TipoElemento,
)
from guia.plantillas import (  # noqa: E402
    CtxPlantilla,
    DatosApendiceQR,
    DatosLamina,
    DatosPortada,
    DatosPortadilla,
    DatosTabla,
    DatosTexto,
    EntradaQR,
    PaginaPlantilla,
    REGISTRO_PLANTILLAS,
    apendice_qr,
    ficha,
    ficha_doble,
    lamina_vertical,
    portada,
    portadilla_capitulo,
    tabla,
    texto,
)

_TOL = 1e-3
_Y_TOPE = AREA_Y + AREA_H


def _ficha_falsa(*, video_url: str | None = None, n_pasos: int = 3):
    """Objeto tipo `FichaEjercicio` con los atributos que leen las plantillas."""
    dosis = types.SimpleNamespace(
        series=3, repeticiones=10, segundos=None, minutos=None, descanso="60 s"
    )
    reducido = types.SimpleNamespace(ancho_m=8.0, largo_m=8.0, ajuste="menos conos")
    completo = types.SimpleNamespace(ancho_m=20.0, largo_m=30.0, ajuste="cancha media")
    return types.SimpleNamespace(
        id="del_definicion_1v1",
        titulo="Definición 1 contra 1",
        objetivo="Resolver el mano a mano ante la portera con calma.",
        pasos=[f"Paso número {i}" for i in range(1, n_pasos + 1)],
        dosis=dosis,
        observacion="mira si la portera achica o espera",
        diagrama=object(),
        espacio_reducido=reducido,
        espacio_completo=completo,
        errores_comunes=["Disparar sin mirar", "Frenar de más"],
        video_url=video_url,
        video_titulo="Video de ejemplo",
    )


def _elementos(paginas: list[PaginaPlantilla]):
    for pagina in paginas:
        for elem in pagina.elementos:
            yield elem


def _asegurar_dentro_del_area(caso: unittest.TestCase, paginas):
    """Todo elemento colocado cae dentro del área imprimible (Req 10.4)."""
    for elem in _elementos(paginas):
        caso.assertGreaterEqual(elem.x + _TOL, AREA_X)
        caso.assertLessEqual(elem.x - _TOL, AREA_X + AREA_W)
        caso.assertGreaterEqual(elem.y + _TOL, AREA_Y)
        caso.assertLessEqual(elem.y + elem.h - _TOL, _Y_TOPE)


class TestPortada(unittest.TestCase):
    def test_una_pagina_con_titulo(self):
        pgs = portada(DatosPortada(titulo="Guía Extensa", subtitulo="Sub-17", lede="Hola", pie="pie"))
        self.assertEqual(len(pgs), 1)
        textos = [e.datos.texto for e in pgs[0].elementos if e.tipo is TipoElemento.TEXTO]
        self.assertIn("Guía Extensa", textos)
        _asegurar_dentro_del_area(self, pgs)

    def test_es_pura(self):
        datos = DatosPortada(titulo="T")
        a = portada(datos)
        b = portada(datos)
        self.assertEqual(
            [e.datos.texto for e in _elementos(a) if hasattr(e.datos, "texto")],
            [e.datos.texto for e in _elementos(b) if hasattr(e.datos, "texto")],
        )


class TestPortadilla(unittest.TestCase):
    def test_una_pagina(self):
        pgs = portadilla_capitulo(DatosPortadilla(numero="10", titulo="Fundamentos", bajada="b"))
        self.assertEqual(len(pgs), 1)
        _asegurar_dentro_del_area(self, pgs)


class TestFicha(unittest.TestCase):
    def test_incluye_titulo_pasos_y_observacion(self):
        pgs = ficha(_ficha_falsa())
        self.assertGreaterEqual(len(pgs), 1)
        textos = " ".join(
            e.datos.texto for e in _elementos(pgs) if hasattr(e.datos, "texto")
        )
        self.assertIn("Definición 1 contra 1", textos)
        self.assertIn("Paso a paso", textos)
        self.assertIn("Qué mira la compañera", textos)
        # Hay un diagrama colocado.
        self.assertTrue(any(e.tipo is TipoElemento.DIAGRAMA for e in _elementos(pgs)))
        _asegurar_dentro_del_area(self, pgs)


class TestFichaDoble(unittest.TestCase):
    def test_dos_paginas_con_qr_y_anotacion(self):
        pgs = ficha_doble(_ficha_falsa(video_url="https://example.com/v"))
        self.assertGreaterEqual(len(pgs), 2)
        # Página de continuación lleva variantes de espacio.
        textos = " ".join(
            e.datos.texto for e in _elementos(pgs) if hasattr(e.datos, "texto")
        )
        self.assertIn("Espacio reducido", textos)
        self.assertIn("Errores comunes", textos)
        # El video produce un QR clicable (Req 9.6).
        self.assertTrue(any(e.tipo is TipoElemento.QR for e in _elementos(pgs)))
        anots = [a for pg in pgs for a in pg.anotaciones]
        self.assertTrue(any(a.uri == "https://example.com/v" for a in anots))
        _asegurar_dentro_del_area(self, pgs)

    def test_sin_video_no_hay_qr(self):
        pgs = ficha_doble(_ficha_falsa(video_url=None))
        self.assertFalse(any(e.tipo is TipoElemento.QR for e in _elementos(pgs)))


class TestTabla(unittest.TestCase):
    def test_corta_por_filas_y_repite_cabecera(self):
        cabecera = ["Jugadoras", "Sesión", "Duración"]
        filas = [[str(i), f"Sesión {i}", "60 min"] for i in range(1, 121)]
        pgs = tabla(DatosTabla(cabecera=cabecera, filas=filas, titulo="Decisión"))
        # Con 120 filas debe ocupar más de una página.
        self.assertGreater(len(pgs), 1)
        # Cada página que tenga filas de tabla arranca con una cabecera.
        for pagina in pgs:
            filas_tabla = [e for e in pagina.elementos if e.tipo is TipoElemento.TABLA]
            if filas_tabla:
                self.assertTrue(
                    filas_tabla[0].datos.es_cabecera,
                    "cada página de tabla debe empezar repitiendo la cabecera",
                )
        _asegurar_dentro_del_area(self, pgs)

    def test_una_pagina_una_sola_cabecera(self):
        pgs = tabla(DatosTabla(cabecera=["A", "B"], filas=[["1", "2"], ["3", "4"]]))
        self.assertEqual(len(pgs), 1)
        cabeceras = [
            e for e in pgs[0].elementos
            if e.tipo is TipoElemento.TABLA and e.datos.es_cabecera
        ]
        self.assertEqual(len(cabeceras), 1)


class TestLamina(unittest.TestCase):
    def test_una_pagina_con_fondo(self):
        pgs = lamina_vertical(
            DatosLamina(titulo="Calienta bien", bajada="antes de jugar", items=["a", "b"], fondo="negro")
        )
        self.assertEqual(len(pgs), 1)
        self.assertTrue(any(e.tipo is TipoElemento.RECT for e in pgs[0].elementos))
        _asegurar_dentro_del_area(self, pgs)


class TestApendiceQR(unittest.TestCase):
    def test_rejilla_con_qr_y_anotaciones(self):
        entradas = [
            EntradaQR(titulo=f"Video {i}", url=f"https://example.com/{i}")
            for i in range(1, 7)
        ]
        pgs = apendice_qr(DatosApendiceQR(entradas=entradas, titulo="Enlaces", columnas=3))
        self.assertGreaterEqual(len(pgs), 1)
        qrs = [e for e in _elementos(pgs) if e.tipo is TipoElemento.QR]
        self.assertEqual(len(qrs), len(entradas))
        anots = [a for pg in pgs for a in pg.anotaciones]
        self.assertEqual(len(anots), len(entradas))
        _asegurar_dentro_del_area(self, pgs)


class TestTexto(unittest.TestCase):
    def test_flujo_de_parrafos(self):
        parrafos = ["Este es un párrafo de prueba con acentos: ñ á é."] * 5
        pgs = texto(DatosTexto(parrafos=parrafos, titulo="Cómo usar la guía"))
        self.assertGreaterEqual(len(pgs), 1)
        textos = " ".join(
            e.datos.texto for e in _elementos(pgs) if hasattr(e.datos, "texto")
        )
        self.assertIn("Cómo usar la guía", textos)
        _asegurar_dentro_del_area(self, pgs)

    def test_corta_muchos_parrafos_en_varias_paginas(self):
        largo = "balón " * 120
        pgs = texto(DatosTexto(parrafos=[largo] * 20))
        self.assertGreater(len(pgs), 1)
        _asegurar_dentro_del_area(self, pgs)


class TestRegistro(unittest.TestCase):
    def test_registro_cubre_las_ocho_plantillas(self):
        esperadas = {
            Plantilla.PORTADA,
            Plantilla.PORTADILLA_CAPITULO,
            Plantilla.FICHA,
            Plantilla.FICHA_DOBLE,
            Plantilla.TABLA,
            Plantilla.LAMINA_VERTICAL,
            Plantilla.INDICE,
            Plantilla.APENDICE_QR,
            Plantilla.TEXTO,
        }
        self.assertEqual(set(REGISTRO_PLANTILLAS), esperadas)
        for fn in REGISTRO_PLANTILLAS.values():
            self.assertTrue(callable(fn))

    def test_plantilla_reexportada(self):
        self.assertIs(plantillas.Plantilla, Plantilla)


class TestDesborde(unittest.TestCase):
    def test_texto_mas_alto_que_area_es_error(self):
        from guia.errores import E_DESBORDE_TEXTO, ErrorLayout

        # Un ancho de caja diminuto obliga a partir el texto en tantísimas
        # líneas que un solo párrafo supera el área imprimible.
        ctx = CtxPlantilla(ancho=6.0)
        gigante = "palabra " * 4000
        with self.assertRaises(ErrorLayout) as caja:
            texto(DatosTexto(parrafos=[gigante]), ctx)
        self.assertEqual(caja.exception.codigo, E_DESBORDE_TEXTO)


if __name__ == "__main__":
    unittest.main()
