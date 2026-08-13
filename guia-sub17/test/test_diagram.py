"""Pruebas del Motor_Diagramas: puente `cancha` -> DiagramaSpec y render SVG.

Cubre la tarea 21 (Ola A): construcción del `DiagramaSpec` desde el campo
`cancha` de las Fichas_JSON, validación de coordenadas (sin `assert`) y la
salida SVG responsive/accesible de `viz.py`.
"""

from __future__ import annotations

import os
import sys
import unittest

# Bootstrap de rutas: `unittest discover -s test` importa este archivo como
# modulo de nivel superior, asi que `test/__init__.py` no corre. Cada modulo de
# prueba pone `src/` en sys.path por su cuenta (convencion del proyecto).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import diagram_spec, viz  # noqa: E402
from guia.diagram_spec import (  # noqa: E402
    ClaseDiagrama,
    DiagramaSpec,
    Item,
    Mundo,
    desde_cancha_json,
)
from guia.errores import E_COORDENADA_INVALIDA, ErrorLayout  # noqa: E402
from guia.schema_json import cargar_catalogo  # noqa: E402

_RUTA_CATALOGO = os.path.join(_DIR_RAIZ, 'contenido', 'ejercicios.json')


def _cancha_valida() -> dict:
    """Devuelve un campo `cancha` de ejemplo, dentro de un mundo 20x20."""
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


class TestDesdeCanchaJson(unittest.TestCase):
    def test_cancha_vacia_devuelve_none(self):
        self.assertIsNone(desde_cancha_json({}))

    def test_cancha_valida_produce_spec_hashable(self):
        spec = desde_cancha_json(_cancha_valida())
        self.assertIsInstance(spec, DiagramaSpec)
        self.assertEqual(spec.clase, ClaseDiagrama.CANCHA)
        self.assertEqual(spec.mundo, Mundo(20.0, 20.0))
        self.assertEqual(spec.titulo, 'Prueba')
        # Hashable: se puede meter en un set y usar como clave de dict.
        self.assertEqual(hash(spec), hash(spec))
        self.assertIn(spec, {spec})

    def test_items_esperados_y_tipos_correctos(self):
        spec = desde_cancha_json(_cancha_valida())
        tipos = sorted(item.tipo for item in spec.items)
        # 2 conos, 1 pass, 3 jugadoras (player/rival/gk), 1 balon, 1 zona.
        self.assertEqual(
            tipos,
            sorted(
                [
                    'cone', 'cone',
                    'pass',
                    'player', 'rival', 'gk',
                    'ball',
                    'zone',
                ]
            ),
        )
        # Los items son tuplas (no listas) y son hashables.
        self.assertIsInstance(spec.items, tuple)
        for item in spec.items:
            self.assertIsInstance(item, Item)
            self.assertIsInstance(hash(item), int)

    def test_mundo_por_defecto_cuando_falta(self):
        spec = desde_cancha_json({'jugadores': [{'x': 1, 'y': 1}]})
        self.assertEqual(spec.mundo, diagram_spec.MUNDO_POR_DEFECTO)

    def test_flecha_tipo_desconocido_cae_a_pass(self):
        spec = desde_cancha_json(
            {'flechas': [{'tipo': 'raro', 'x': 1, 'y': 1, 'x2': 2, 'y2': 2}]}
        )
        self.assertEqual(spec.items[0].tipo, 'pass')

    def test_coordenada_fuera_del_mundo_lanza_error(self):
        cancha = {
            'mundo': {'ancho_m': 10.0, 'alto_m': 10.0},
            'jugadores': [{'x': 20, 'y': 5}],
        }
        with self.assertRaises(ErrorLayout) as caja:
            desde_cancha_json(cancha)
        self.assertEqual(caja.exception.codigo, E_COORDENADA_INVALIDA)

    def test_coordenada_negativa_lanza_error(self):
        with self.assertRaises(ErrorLayout) as caja:
            desde_cancha_json({'conos': [{'x': -1, 'y': 5}]})
        self.assertEqual(caja.exception.codigo, E_COORDENADA_INVALIDA)

    def test_coordenada_no_finita_lanza_error(self):
        with self.assertRaises(ErrorLayout) as caja:
            desde_cancha_json({'balon': {'x': float('inf'), 'y': 5}})
        self.assertEqual(caja.exception.codigo, E_COORDENADA_INVALIDA)
        self.assertIn('coordenada invalida', caja.exception.mensaje)


class TestRenderSvg(unittest.TestCase):
    def test_svg_es_responsive_y_accesible(self):
        spec = desde_cancha_json(_cancha_valida())
        svg, view_box = viz.spec_a_svg(spec)
        self.assertIn('viewBox="', svg)
        self.assertIn(view_box, svg)
        self.assertIn('role="img"', svg)
        self.assertIn('<title>', svg)
        self.assertIn('<desc>', svg)
        self.assertIn('style="width:100%;height:auto"', svg)
        # Sin dimensiones absolutas en el elemento <svg>.
        self.assertNotIn('width="', svg.split('>', 1)[0])
        self.assertNotIn('height="', svg.split('>', 1)[0])

    def test_view_box_coincide_con_mundo_escalado(self):
        spec = desde_cancha_json(_cancha_valida())
        _, view_box = viz.spec_a_svg(spec)
        esperado_ancho = 20.0 * viz.ESCALA_PX_M
        esperado_alto = 20.0 * viz.ESCALA_PX_M
        self.assertEqual(view_box, f'0 0 {esperado_ancho:g} {esperado_alto:g}')

    def test_render_svg_es_determinista(self):
        spec = desde_cancha_json(_cancha_valida())
        self.assertEqual(viz.render_svg(spec), viz.render_svg(spec))

    def test_todas_las_fichas_del_catalogo_generan_svg(self):
        catalogo = cargar_catalogo(_RUTA_CATALOGO)
        self.assertGreaterEqual(len(catalogo), 45)
        con_diagrama = 0
        for ficha in catalogo:
            spec = desde_cancha_json(ficha['cancha'])
            if spec is None:
                continue
            con_diagrama += 1
            svg, _ = viz.spec_a_svg(spec)
            self.assertTrue(svg.startswith('<svg'))
            self.assertTrue(svg.endswith('</svg>'))
            self.assertIn('viewBox="', svg)
            self.assertIn('role="img"', svg)
        # Cada ficha con cancha poblada genera su SVG.
        self.assertEqual(con_diagrama, sum(1 for f in catalogo if f.get('cancha')))
        self.assertGreaterEqual(con_diagrama, 45)


if __name__ == '__main__':
    unittest.main()
