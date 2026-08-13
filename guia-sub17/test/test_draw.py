"""Pruebas del renderizador a operadores PDF del Motor_Diagramas (`draw.py`).

Complementa `test_diagram.py` (que cubre `viz.py`, el renderizador SVG) con la
otra mitad del contrato de la tarea 3.2: `spec -> (operadores_pdf, bbox)`.

Verifica el contrato de `draw.py`:

* punto de entrada único `spec_a_operadores(spec) -> (str, bbox)`;
* bbox = ``(0, 0, ancho_m*ESCALA, alto_m*ESCALA)`` sin flip de Y;
* operadores `q`/`Q` y `BT`/`ET` balanceados (base de la Property 8);
* todo color emitido (`rg`/`RG`) pertenece a la paleta (base de la Property 12);
* números formateados de forma estable (determinismo);
* caché en memoria por el spec y `clave_spec` estable entre corridas.
"""

from __future__ import annotations

import os
import re
import sys
import unittest

# Bootstrap de rutas: mismo patron que el resto de modulos de prueba.
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import draw, paleta  # noqa: E402
from guia.diagram_spec import (  # noqa: E402
    ClaseDiagrama,
    DiagramaSpec,
    Item,
    Mundo,
    desde_cancha_json,
)
from guia.schema_json import cargar_catalogo  # noqa: E402

_RUTA_CATALOGO = os.path.join(_DIR_RAIZ, 'contenido', 'ejercicios.json')

# Captura las triplas de color de relleno (rg) y de trazo (RG).
_RE_COLOR = re.compile(
    r'(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (rg|RG)'
)


def _cancha_valida() -> dict:
    """Campo `cancha` de ejemplo con un item de cada familia, mundo 20x20."""
    return {
        'mundo': {'ancho_m': 20.0, 'alto_m': 20.0},
        'titulo': 'Prueba',
        'conos': [{'x': 2, 'y': 2}, {'x': 18, 'y': 2}],
        'jugadores': [
            {'x': 5, 'y': 5, 'equipo': 'propio', 'numero': 7},
            {'x': 15, 'y': 15, 'equipo': 'rival', 'numero': 4},
            {'x': 10, 'y': 1, 'equipo': 'gk', 'numero': 1},
        ],
        'flechas': [{'tipo': 'pass', 'x': 5, 'y': 5, 'x2': 15, 'y2': 15}],
        'balon': {'x': 5.5, 'y': 5.0},
        'zonas': [{'puntos': [[1, 1], [8, 1], [8, 8], [1, 8]], 'etiqueta': 'Z'}],
    }


def _paleta_normalizada() -> frozenset[tuple[float, float, float]]:
    """Todas las triplas RGB (redondeadas) que admite la paleta."""
    triplas = set()
    for color in paleta.COLORES_PALETA:
        r, g, b = paleta.rgb_pdf(color)
        triplas.add((round(r, 3), round(g, 3), round(b, 3)))
    return frozenset(triplas)


class TestContratoOperadores(unittest.TestCase):
    def test_punto_de_entrada_devuelve_operadores_y_bbox(self):
        spec = desde_cancha_json(_cancha_valida())
        ops, bbox = draw.spec_a_operadores(spec)
        self.assertIsInstance(ops, str)
        self.assertTrue(ops)
        self.assertEqual(len(bbox), 4)

    def test_bbox_es_mundo_escalado_sin_flip(self):
        spec = desde_cancha_json(_cancha_valida())
        bbox = draw.bbox_de(spec)
        self.assertEqual(
            bbox,
            (0.0, 0.0, 20.0 * draw.ESCALA_PT_M, 20.0 * draw.ESCALA_PT_M),
        )

    def test_operadores_de_es_atajo_de_la_cadena(self):
        spec = desde_cancha_json(_cancha_valida())
        ops, _ = draw.spec_a_operadores(spec)
        self.assertEqual(draw.operadores_de(spec), ops)

    def test_qQ_y_BTET_balanceados(self):
        spec = desde_cancha_json(_cancha_valida())
        ops = draw.operadores_de(spec)
        self.assertEqual(ops.count('q\n'), ops.count('Q\n'))
        self.assertEqual(ops.count('BT\n'), ops.count('ET\n'))

    def test_render_es_determinista(self):
        spec = desde_cancha_json(_cancha_valida())
        self.assertEqual(draw.operadores_de(spec), draw.operadores_de(spec))


class TestPaletaYFormato(unittest.TestCase):
    def test_todo_color_emitido_pertenece_a_la_paleta(self):
        # Base de la Property 12 para la salida PDF.
        spec = desde_cancha_json(_cancha_valida())
        ops = draw.operadores_de(spec)
        validas = _paleta_normalizada()
        encontrados = _RE_COLOR.findall(ops)
        self.assertTrue(encontrados, 'el diagrama deberia emitir colores')
        for r, g, b, _op in encontrados:
            tripla = (round(float(r), 3), round(float(g), 3), round(float(b), 3))
            self.assertIn(
                tripla, validas, f'color {tripla} fuera de la paleta'
            )

    def test_num_recorta_ceros_para_bytes_estables(self):
        self.assertEqual(draw._num(1.0), '1')
        self.assertEqual(draw._num(1.5), '1.5')
        self.assertEqual(draw._num(0.0), '0')
        self.assertEqual(draw._num(2.500), '2.5')
        # Sin notacion cientifica ni ceros colgantes.
        self.assertNotIn('e', draw._num(1234.0))


class TestCacheYClave(unittest.TestCase):
    def test_cache_en_memoria_reusa_el_resultado(self):
        spec = desde_cancha_json(_cancha_valida())
        primero = draw.spec_a_operadores(spec)
        segundo = draw.spec_a_operadores(spec)
        # `lru_cache` devuelve el mismo objeto para el mismo spec hashable.
        self.assertIs(primero, segundo)

    def test_clave_spec_es_estable_y_hex_de_16_bytes(self):
        spec = desde_cancha_json(_cancha_valida())
        clave = draw.clave_spec(spec)
        self.assertEqual(clave, draw.clave_spec(spec))
        self.assertEqual(len(clave), 32)  # 16 bytes en hex
        int(clave, 16)  # es hex valido

    def test_clave_spec_distingue_specs_distintos(self):
        a = desde_cancha_json(_cancha_valida())
        b = DiagramaSpec(
            clase=ClaseDiagrama.CANCHA,
            mundo=Mundo(20.0, 20.0),
            items=(Item(tipo='ball', x=1.0, y=1.0),),
        )
        self.assertNotEqual(draw.clave_spec(a), draw.clave_spec(b))


class TestFichasHeredadas(unittest.TestCase):
    def test_las_15_fichas_producen_operadores_validos(self):
        catalogo = cargar_catalogo(_RUTA_CATALOGO)
        self.assertGreaterEqual(len(catalogo), 45)
        validas = _paleta_normalizada()
        con_diagrama = 0
        for ficha in catalogo:
            spec = desde_cancha_json(ficha['cancha'])
            if spec is None:
                continue
            con_diagrama += 1
            with self.subTest(ficha=ficha['id']):
                ops, bbox = draw.spec_a_operadores(spec)
                self.assertTrue(ops)
                # Operadores balanceados (Property 8, parte PDF).
                self.assertEqual(ops.count('q\n'), ops.count('Q\n'))
                self.assertEqual(ops.count('BT\n'), ops.count('ET\n'))
                # bbox no degenerado y de area positiva.
                self.assertEqual(bbox[0], 0.0)
                self.assertEqual(bbox[1], 0.0)
                self.assertGreater(bbox[2], 0.0)
                self.assertGreater(bbox[3], 0.0)
                # Todo color de la ficha pertenece a la paleta (Property 12).
                for r, g, b, _op in _RE_COLOR.findall(ops):
                    tripla = (
                        round(float(r), 3),
                        round(float(g), 3),
                        round(float(b), 3),
                    )
                    self.assertIn(tripla, validas)
        self.assertEqual(con_diagrama, sum(1 for f in catalogo if f.get('cancha')))
        self.assertGreaterEqual(con_diagrama, 45)


if __name__ == '__main__':
    unittest.main()
