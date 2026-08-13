"""Pruebas del Diagrama_Botin: geometría Bézier, 7 zonas con trama y su render.

Cubre la tarea 3.5: las dos siluetas (planta y perfil) descritas con Bézier
cúbicas, las siete zonas de contacto (`pase`, `canonazo`, `tres_dedos`,
`efecto`, `planta`, `tacon`, `punta`) recortadas contra su contorno, cada una
con gris base + trama y su texto de acción de juego, el grafo `ADYACENTES` con
la regla de distinguibilidad en monocromo, y el hecho de que el `BotinSpec`
sea renderizable por `draw.py` (PDF) y `viz.py` (SVG).

Requisitos validados: 3.1, 3.2, 3.3, 3.7, 3.8, 3.9.
"""

from __future__ import annotations

import math
import os
import re
import sys
import unittest

# Bootstrap de rutas: mismo patron que el resto de modulos de prueba.
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, 'src')
if _DIR_SRC not in sys.path:
    sys.path.insert(0, _DIR_SRC)

from guia import draw, paleta, viz  # noqa: E402
from guia.diagram_spec import (  # noqa: E402
    ADYACENTES,
    BotinSpec,
    ClaseDiagrama,
    Trama,
    Vista,
    aplanar_bezier,
    botin_por_defecto,
    color_base_zona,
    contorno_a_poligono,
    offset_de_vista,
    pares_no_distinguibles,
    poligono_contorno,
    punto_en_poligono,
    son_distinguibles,
    validar_zonas_en_contorno,
    verificar_distinguibilidad,
    zonas_por_nombre,
)

# Los siete nombres de zona que exige el Requisito 3.2.
_ZONAS_ESPERADAS = frozenset(
    {'pase', 'canonazo', 'tres_dedos', 'efecto', 'planta', 'tacon', 'punta'}
)

# Colores hex de la paleta que puede emitir el botin (grises + rosa/negro/fondo).
_HEX_COLOR = re.compile(r'(?:fill|stroke)="(#[0-9A-Fa-f]{3,6})"')

# Operadores de color PDF (rg/RG) para verificar la paleta.
_RE_COLOR_PDF = re.compile(
    r'(-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (-?\d+(?:\.\d+)?) (rg|RG)'
)


def _paleta_rgb() -> frozenset:
    triplas = set()
    for color in paleta.COLORES_PALETA:
        r, g, b = paleta.rgb_pdf(color)
        triplas.add((round(r, 3), round(g, 3), round(b, 3)))
    return frozenset(triplas)


class TestGeometriaBezier(unittest.TestCase):
    def test_aplanar_bezier_incluye_extremos(self):
        controles = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0))
        puntos = aplanar_bezier(controles, 12)
        self.assertEqual(len(puntos), 13)
        self.assertEqual(puntos[0], (0.0, 0.0))
        self.assertEqual(puntos[-1], (10.0, 0.0))

    def test_contorno_a_poligono_cierra_y_no_repite_extremo(self):
        poligono = poligono_contorno(Vista.PLANTA, 12)
        self.assertGreaterEqual(len(poligono), 12)
        self.assertNotEqual(poligono[0], poligono[-1])
        for x, y in poligono:
            self.assertTrue(math.isfinite(x) and math.isfinite(y))

    def test_zonas_recortadas_dentro_de_su_contorno(self):
        # Req 3.1/3.2: cada zona cae dentro de la silueta de su vista.
        validar_zonas_en_contorno()  # no lanza
        spec = botin_por_defecto()
        for zona in spec.zonas:
            poligono = poligono_contorno(zona.vista, 12)
            for vertice in zona.poligono:
                with self.subTest(zona=zona.nombre, vertice=vertice):
                    self.assertTrue(punto_en_poligono(vertice, poligono))


class TestZonas(unittest.TestCase):
    def test_hay_exactamente_las_siete_zonas(self):
        spec = botin_por_defecto()
        self.assertEqual(len(spec.zonas), 7)
        self.assertEqual(
            frozenset(z.nombre for z in spec.zonas), _ZONAS_ESPERADAS
        )

    def test_cada_zona_tiene_accion_de_juego(self):
        # Req 3.7: junto a cada zona, para que accion de juego se usa.
        for zona in botin_por_defecto().zonas:
            with self.subTest(zona=zona.nombre):
                self.assertTrue(zona.accion.strip())

    def test_gris_base_pertenece_a_la_paleta(self):
        # Req 3.8: la paleta se conserva; el gris base es un gris de la paleta.
        for zona in botin_por_defecto().zonas:
            with self.subTest(zona=zona.nombre):
                self.assertIn(color_base_zona(zona.gris), paleta.GRISES_TRAMA)

    def test_dos_vistas_planta_y_perfil(self):
        # Req 3.1: una vista de planta y una de perfil.
        vistas = {z.vista for z in botin_por_defecto().zonas}
        self.assertEqual(vistas, {Vista.PLANTA, Vista.PERFIL})

    def test_offset_separa_las_vistas(self):
        self.assertEqual(offset_de_vista(Vista.PLANTA), (0.0, 0.0))
        self.assertGreater(offset_de_vista(Vista.PERFIL)[0], 0.0)


class TestDistinguibilidad(unittest.TestCase):
    def test_regla_de_distinguibilidad_en_pares_adyacentes(self):
        # Req 3.3 / 3.9: distinta trama o gris que difiere >= 0.18.
        self.assertEqual(pares_no_distinguibles(), [])
        verificar_distinguibilidad()  # no lanza

    def test_regla_explicita_por_par(self):
        indice = zonas_por_nombre()
        for a, b in ADYACENTES:
            with self.subTest(par=(a, b)):
                za, zb = indice[a], indice[b]
                distinta_trama = za.trama != zb.trama
                gris_lejano = abs(za.gris - zb.gris) >= 0.18 - 1e-9
                self.assertTrue(distinta_trama or gris_lejano)
                self.assertTrue(son_distinguibles(za, zb))

    def test_adyacencias_referencian_zonas_existentes(self):
        nombres = {z.nombre for z in botin_por_defecto().zonas}
        for a, b in ADYACENTES:
            self.assertIn(a, nombres)
            self.assertIn(b, nombres)


class TestRenderPDF(unittest.TestCase):
    def setUp(self):
        self.spec = botin_por_defecto('Zonas del botin')

    def test_punto_de_entrada_unico_despacha_al_botin(self):
        ops, bbox = draw.spec_a_operadores(self.spec)
        self.assertEqual(ops, draw.botin_a_operadores(self.spec)[0])
        self.assertEqual(bbox, draw.bbox_botin(self.spec))
        self.assertEqual(bbox[0], 0.0)
        self.assertEqual(bbox[1], 0.0)
        self.assertGreater(bbox[2], 0.0)
        self.assertGreater(bbox[3], 0.0)

    def test_operadores_balanceados(self):
        ops, _ = draw.spec_a_operadores(self.spec)
        self.assertEqual(ops.count('q\n'), ops.count('Q\n'))
        self.assertEqual(ops.count('BT\n'), ops.count('ET\n'))

    def test_todo_color_pdf_pertenece_a_la_paleta(self):
        # Req 3.8 (base de la Property 12).
        ops, _ = draw.spec_a_operadores(self.spec)
        validas = _paleta_rgb()
        encontrados = _RE_COLOR_PDF.findall(ops)
        self.assertTrue(encontrados)
        for r, g, b, _op in encontrados:
            tripla = (round(float(r), 3), round(float(g), 3), round(float(b), 3))
            self.assertIn(tripla, validas)

    def test_coordenadas_de_camino_dentro_del_bbox(self):
        # Base de la Property 8 para la salida PDF del botin.
        ops, bbox = draw.spec_a_operadores(self.spec)
        max_x, max_y = bbox[2], bbox[3]
        tol = 1e-6
        # Coordenadas de operadores de construccion de camino: m, l, c.
        patron = re.compile(
            r'((?:-?\d+(?:\.\d+)? )+)(m|l|c)\n'
        )
        vistos = 0
        for grupo, _op in patron.findall(ops):
            numeros = [float(n) for n in grupo.split()]
            pares = list(zip(numeros[0::2], numeros[1::2]))
            for x, y in pares:
                self.assertTrue(math.isfinite(x) and math.isfinite(y))
                self.assertGreaterEqual(x, -tol)
                self.assertLessEqual(x, max_x + tol)
                self.assertGreaterEqual(y, -tol)
                self.assertLessEqual(y, max_y + tol)
                vistos += 1
        self.assertGreater(vistos, 0)

    def test_accion_de_cada_zona_aparece_en_el_pdf(self):
        ops, _ = draw.spec_a_operadores(self.spec)
        for zona in self.spec.zonas:
            with self.subTest(zona=zona.nombre):
                self.assertIn(f'({zona.accion}) Tj', ops)

    def test_render_pdf_determinista(self):
        self.assertEqual(
            draw.operadores_de(self.spec), draw.operadores_de(self.spec)
        )

    def test_clave_spec_estable_para_botin(self):
        clave = draw.clave_spec(self.spec)
        self.assertEqual(clave, draw.clave_spec(self.spec))
        self.assertEqual(len(clave), 32)
        int(clave, 16)


class TestRenderSVG(unittest.TestCase):
    def setUp(self):
        self.spec = botin_por_defecto('Zonas del botin')

    def test_punto_de_entrada_unico_despacha_al_botin(self):
        svg, view_box = viz.spec_a_svg(self.spec)
        self.assertEqual(svg, viz.botin_a_svg(self.spec)[0])
        self.assertTrue(svg.startswith('<svg'))
        self.assertTrue(svg.endswith('</svg>'))
        self.assertIn(f'viewBox="{view_box}"', svg)

    def test_svg_responsive_y_accesible(self):
        svg, _ = viz.spec_a_svg(self.spec)
        self.assertIn('role="img"', svg)
        self.assertIn('<title>', svg)
        self.assertIn('<desc>', svg)
        self.assertIn('style="width:100%;height:auto"', svg)
        self.assertNotIn('width="', svg.split('>', 1)[0])
        self.assertNotIn('height="', svg.split('>', 1)[0])

    def test_hay_un_clippath_por_zona(self):
        svg, _ = viz.spec_a_svg(self.spec)
        for zona in self.spec.zonas:
            with self.subTest(zona=zona.nombre):
                self.assertIn(f'<clipPath id="zona-{zona.nombre}">', svg)

    def test_accion_de_cada_zona_aparece_en_el_svg(self):
        # Req 3.7 en la salida web.
        svg, _ = viz.spec_a_svg(self.spec)
        for zona in self.spec.zonas:
            with self.subTest(zona=zona.nombre):
                self.assertIn(zona.accion, svg)

    def test_todo_color_svg_pertenece_a_la_paleta(self):
        # Req 3.8 / 3.9 en la salida web.
        svg, _ = viz.spec_a_svg(self.spec)
        colores = _HEX_COLOR.findall(svg)
        self.assertTrue(colores)
        for color in colores:
            with self.subTest(color=color):
                self.assertTrue(paleta.es_color_valido(color))

    def test_render_svg_determinista(self):
        self.assertEqual(viz.render_svg(self.spec), viz.render_svg(self.spec))


class TestSpec(unittest.TestCase):
    def test_botin_spec_es_hashable_y_de_clase_botin(self):
        spec = botin_por_defecto()
        self.assertIsInstance(spec, BotinSpec)
        self.assertEqual(spec.clase, ClaseDiagrama.BOTIN)
        self.assertEqual(hash(spec), hash(spec))
        self.assertIn(spec, {spec})

    def test_dos_vistas_lado_a_lado_en_el_mundo(self):
        # El mundo del botin aloja las dos vistas (planta + perfil) una al lado
        # de la otra; el tamano final en pagina lo fija la plantilla (Req 3.6).
        spec = botin_por_defecto()
        _, bbox = draw.spec_a_operadores(spec)
        self.assertGreater(bbox[2], bbox[3])  # mas ancho que alto (dos vistas)
        # El ancho cubre las dos vistas mas su separacion.
        ancho_min = (
            offset_de_vista(Vista.PERFIL)[0] * draw.ESCALA_BOTIN_PT
        )
        self.assertGreaterEqual(bbox[2], ancho_min)


if __name__ == '__main__':
    unittest.main()
