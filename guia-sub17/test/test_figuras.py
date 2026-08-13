"""Pruebas del motor de ilustraciones didacticas (`figuras.py`, tarea 3.9).

No basta con que la ilustracion renderice: estas pruebas exigen que **ensene**.
Para la ficha de golpeo se comprueba que la figura declare explicitamente:

* el pie de apoyo,
* la superficie de contacto del balon,
* la orientacion del cuerpo (lineas de cadera y de hombros),
* la trayectoria del balon,
* y el error frecuente contrastado en un segundo panel.

Ademas se verifica lo de siempre en este proyecto: spec hashable, coordenadas
dentro del mundo, todo color de la paleta, SVG accesible con `viewBox`,
`role="img"` y `<title>`, operadores PDF balanceados, texto codificable en
WinAnsi y render determinista.

_Requirements: 9.2, 9.3, 6.5, 6.6, 9.10, 10.4_
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

from guia import draw, figuras, paleta, viz  # noqa: E402
from guia.diagram_spec import ClaseDiagrama  # noqa: E402


def _todas_las_etiquetas(spec) -> str:
    """Concatena en minusculas las etiquetas de items y leyenda del spec."""
    partes = [it.etiqueta for it in spec.items if it.etiqueta]
    partes.extend(le.texto for le in spec.leyenda)
    partes.extend(le.simbolo for le in spec.leyenda)
    if spec.titulo:
        partes.append(spec.titulo)
    return " | ".join(partes).lower()


class TestRegistro(unittest.TestCase):
    """El registro expone ilustraciones y falla limpio ante un id ajeno."""

    def test_hay_al_menos_una_ilustracion(self) -> None:
        self.assertGreaterEqual(len(figuras.ids_figuras()), 1)

    def test_contador_de_posturas_es_positivo(self) -> None:
        # Es el valor que el reporte del build publica como `posturas`.
        self.assertGreater(figuras.contar_posturas(), 0)

    def test_todas_son_de_clase_postura(self) -> None:
        for spec in figuras.todas_las_figuras():
            with self.subTest(titulo=spec.titulo):
                self.assertIs(spec.clase, ClaseDiagrama.POSTURA)

    def test_id_desconocido_falla_con_value_error(self) -> None:
        with self.assertRaises(ValueError):
            figuras.figura("no-existe")

    def test_ids_en_orden_estable(self) -> None:
        self.assertEqual(figuras.ids_figuras(), tuple(sorted(figuras.ids_figuras())))


class TestInvariantesDeSpec(unittest.TestCase):
    """Invariantes que valen para toda ilustracion registrada."""

    def setUp(self) -> None:
        self.specs = figuras.todas_las_figuras()

    def test_spec_es_hashable(self) -> None:
        for spec in self.specs:
            with self.subTest(titulo=spec.titulo):
                self.assertIsInstance(hash(spec), int)
                self.assertIn(spec, {spec})

    def test_toda_coordenada_es_finita_y_cae_en_el_mundo(self) -> None:
        for spec in self.specs:
            ancho, alto = spec.mundo.ancho_m, spec.mundo.alto_m
            for indice, item in enumerate(spec.items):
                pares = [(item.x, item.y)]
                if item.x2 is not None and item.y2 is not None:
                    pares.append((item.x2, item.y2))
                pares.extend(item.puntos)
                for x, y in pares:
                    with self.subTest(item=indice, tipo=item.tipo, x=x, y=y):
                        self.assertTrue(math.isfinite(x))
                        self.assertTrue(math.isfinite(y))
                        self.assertGreaterEqual(x, 0.0)
                        self.assertLessEqual(x, ancho)
                        self.assertGreaterEqual(y, 0.0)
                        self.assertLessEqual(y, alto)

    def test_todo_color_declarado_pertenece_a_la_paleta(self) -> None:
        for spec in self.specs:
            for item in spec.items:
                if item.color:
                    with self.subTest(tipo=item.tipo, color=item.color):
                        self.assertTrue(paleta.es_color_valido(item.color))

    def test_todo_texto_es_codificable_en_winansi(self) -> None:
        # Req 1.6: el PDF escribe literales en cp1252. Un guion largo romperia.
        for spec in self.specs:
            _todas_las_etiquetas(spec).encode("cp1252")

    def test_tiene_leyenda_no_vacia(self) -> None:
        for spec in self.specs:
            with self.subTest(titulo=spec.titulo):
                self.assertGreaterEqual(len(spec.leyenda), 1)
                for entrada in spec.leyenda:
                    self.assertTrue(entrada.texto.strip())
                    self.assertTrue(entrada.simbolo.strip())


class TestValorDidactico(unittest.TestCase):
    """La ilustracion de golpeo debe ensenar, no solo dibujar."""

    def setUp(self) -> None:
        self.spec = figuras.pase_corto_interior()
        self.etiquetas = _todas_las_etiquetas(self.spec)
        self.tipos = [it.tipo for it in self.spec.items]

    def test_declara_el_pie_de_apoyo(self) -> None:
        self.assertIn("pie de apoyo", self.etiquetas)

    def test_declara_la_superficie_de_contacto(self) -> None:
        self.assertIn("contacto", self.etiquetas)

    def test_declara_la_orientacion_del_cuerpo(self) -> None:
        self.assertIn("linea de cadera", self.etiquetas)
        self.assertIn("linea de hombros", self.etiquetas)

    def test_declara_la_trayectoria_del_balon(self) -> None:
        self.assertIn("balon raso", self.etiquetas)
        # La trayectoria se dibuja con una flecha, no solo con texto.
        self.assertIn("pass", self.tipos)

    def test_hay_balon_y_zonas_resaltadas(self) -> None:
        self.assertIn("ball", self.tipos)
        self.assertGreaterEqual(self.tipos.count("zone"), 2)

    def test_contrasta_correcto_y_error_en_dos_paneles(self) -> None:
        textos = [it.etiqueta for it in self.spec.items if it.tipo == "txt"]
        self.assertIn(figuras.ROTULO_CORRECTO, textos)
        self.assertIn(figuras.ROTULO_ERROR, textos)

    def test_el_error_se_marca_en_rojo_y_ademas_con_texto(self) -> None:
        # Req de accesibilidad: no comunicar solo por color.
        rojos = [
            it
            for it in self.spec.items
            if it.color and paleta.normalizar_hex(it.color) == paleta.normalizar_hex(paleta.ROJO)
        ]
        self.assertGreaterEqual(len(rojos), 1)
        for item in rojos:
            with self.subTest(etiqueta=item.etiqueta):
                self.assertTrue(item.etiqueta.strip())
        self.assertIn("punta", self.etiquetas)

    def test_los_dos_paneles_tienen_figura_propia(self) -> None:
        # Cada panel lleva su cabeza: dos figuras, no una duplicada por error.
        cabezas = [it for it in self.spec.items if it.etiqueta == "cabeza"]
        self.assertEqual(len(cabezas), 2)
        mitad = self.spec.mundo.ancho_m / 2.0
        self.assertTrue(any(c.x < mitad for c in cabezas))
        self.assertTrue(any(c.x >= mitad for c in cabezas))


class TestRenderSvg(unittest.TestCase):
    """El SVG es responsive, accesible y determinista."""

    def setUp(self) -> None:
        self.spec = figuras.pase_corto_interior()

    def test_svg_accesible_y_responsive(self) -> None:
        svg, view_box = viz.spec_a_svg(self.spec)
        self.assertIn(f'viewBox="{view_box}"', svg)
        self.assertIn('role="img"', svg)
        self.assertIn("<title", svg)
        # Sin dimensiones absolutas en la etiqueta de apertura.
        apertura = svg.split(">", 1)[0]
        self.assertNotIn('width="', apertura)
        self.assertNotIn('height="', apertura)

    def test_view_box_cubre_el_mundo_completo(self) -> None:
        _, view_box = viz.spec_a_svg(self.spec)
        self.assertTrue(view_box.startswith("0 0 "))

    def test_render_determinista(self) -> None:
        self.assertEqual(viz.render_svg(self.spec), viz.render_svg(self.spec))

    def test_todo_color_del_svg_pertenece_a_la_paleta(self) -> None:
        svg, _ = viz.spec_a_svg(self.spec)
        for token in svg.replace('"', " ").replace("'", " ").split():
            if token.startswith("#"):
                with self.subTest(color=token):
                    self.assertTrue(paleta.es_color_valido(token))


class TestRenderPdf(unittest.TestCase):
    """Los operadores PDF salen balanceados y con colores de la paleta."""

    def setUp(self) -> None:
        self.spec = figuras.pase_corto_interior()

    def test_operadores_balanceados(self) -> None:
        ops, _ = draw.spec_a_operadores(self.spec)
        self.assertEqual(ops.count("q\n"), ops.count("Q\n"))
        self.assertEqual(ops.count("BT\n"), ops.count("ET\n"))

    def test_bbox_positivo(self) -> None:
        _, bbox = draw.spec_a_operadores(self.spec)
        self.assertEqual(len(bbox), 4)
        self.assertGreater(bbox[2], 0.0)
        self.assertGreater(bbox[3], 0.0)

    def test_render_pdf_determinista(self) -> None:
        self.assertEqual(draw.operadores_de(self.spec), draw.operadores_de(self.spec))


class TestFiguraParametrica(unittest.TestCase):
    """La figura responde a sus parametros y rechaza valores imposibles."""

    def test_el_valgo_desvia_la_rodilla_de_apoyo(self) -> None:
        alineada = figuras.figura_jugadora(0.0, valgo=0.0)
        colapsada = figuras.figura_jugadora(0.0, valgo=22.0)
        r_ok = next(i for i in alineada if i.etiqueta == "rodilla de apoyo")
        r_mal = next(i for i in colapsada if i.etiqueta == "rodilla de apoyo")
        self.assertNotAlmostEqual(r_ok.x, r_mal.x, places=3)

    def test_apertura_de_pies_invalida_falla(self) -> None:
        with self.assertRaises(ValueError):
            figuras.figura_jugadora(0.0, apertura_pies=0.0)

    def test_lado_ejecutor_espeja_la_figura(self) -> None:
        der = figuras.figura_jugadora(0.0, lado_ejecutor="der")
        izq = figuras.figura_jugadora(0.0, lado_ejecutor="izq")
        c_der = next(i for i in der if i.etiqueta == "cabeza")
        c_izq = next(i for i in izq if i.etiqueta == "cabeza")
        self.assertNotAlmostEqual(c_der.x, c_izq.x, places=3)

    def test_zona_circular_con_pocos_lados_falla(self) -> None:
        with self.assertRaises(ValueError):
            figuras._circulo_zona(1.0, 1.0, 0.5, lados=2)


# =========================================================================== #
# Lote 3 (tarea 33.3): las nueve ilustraciones restantes
# =========================================================================== #

#: Las diez ilustraciones que debe exponer el catalogo cerrado el lote 3.
_IDS_ESPERADOS: tuple[str, ...] = (
    "aterrizaje-seguro",
    "bajar-balon-aereo",
    "conduccion",
    "control-orientado",
    "golpeo-exterior",
    "pase-corto-interior",
    "pase-largo-empeine",
    "regate-cambio-direccion",
    "tiro-colocado-interior",
    "tiro-potencia-empeine",
)

#: Lenguaje que la ilustracion de aterrizaje NO debe usar: es tecnica de salto y
#: caida, no diagnostico ni rehabilitacion.
_LENGUAJE_NO_PERMITIDO: tuple[str, ...] = (
    "lesion",
    "diagnostic",
    "rehabilit",
    "ligamento",
    "terapia",
    "tratamiento",
    "dolor",
    "medic",
    "clinic",
    "sintoma",
    "fisioter",
)


def _tipos(spec) -> list[str]:
    """Tipos de item del spec, en orden."""
    return [it.tipo for it in spec.items]


def _textos(spec) -> list[str]:
    """Rotulos de texto (`txt`) del spec."""
    return [it.etiqueta for it in spec.items if it.tipo == "txt"]


class TestCatalogoDeDiez(unittest.TestCase):
    """Cerrado el lote 3, el catalogo tiene exactamente diez ilustraciones."""

    def test_los_ids_registrados_son_los_diez_esperados(self) -> None:
        self.assertEqual(figuras.ids_figuras(), _IDS_ESPERADOS)

    def test_el_contador_de_posturas_es_diez(self) -> None:
        self.assertEqual(figuras.contar_posturas(), 10)


class TestInvariantesDeLasDiezFiguras(unittest.TestCase):
    """Los invariantes del proyecto, corridos sobre las diez ilustraciones.

    Una sola prueba parametrizada con `subTest` por figura: si una falla, el
    reporte dice cual y las otras nueve se siguen evaluando.
    """

    def test_invariantes_por_figura(self) -> None:
        for fid in _IDS_ESPERADOS:
            with self.subTest(figura=fid):
                spec = figuras.figura(fid)

                # Clase y spec hashable (cacheable con lru_cache).
                self.assertIs(spec.clase, ClaseDiagrama.POSTURA)
                self.assertIsInstance(hash(spec), int)

                # Toda coordenada finita y dentro del mundo.
                ancho, alto = spec.mundo.ancho_m, spec.mundo.alto_m
                for item in spec.items:
                    pares = [(item.x, item.y)]
                    if item.x2 is not None and item.y2 is not None:
                        pares.append((item.x2, item.y2))
                    pares.extend(item.puntos)
                    for x, y in pares:
                        self.assertTrue(math.isfinite(x) and math.isfinite(y))
                        self.assertGreaterEqual(x, 0.0)
                        self.assertLessEqual(x, ancho)
                        self.assertGreaterEqual(y, 0.0)
                        self.assertLessEqual(y, alto)

                # Todo color declarado pertenece a la paleta.
                for item in spec.items:
                    if item.color:
                        self.assertTrue(paleta.es_color_valido(item.color))

                # Texto codificable en WinAnsi (cp1252) y leyenda no vacia.
                _todas_las_etiquetas(spec).encode("cp1252")
                self.assertGreaterEqual(len(spec.leyenda), 1)

                # Dos paneles contrastados: correcto y error frecuente.
                textos = _textos(spec)
                self.assertIn(figuras.ROTULO_CORRECTO, textos)
                self.assertIn(figuras.ROTULO_ERROR, textos)

                # SVG accesible y responsive.
                svg, view_box = viz.spec_a_svg(spec)
                self.assertIn(f'viewBox="{view_box}"', svg)
                self.assertIn('role="img"', svg)
                self.assertIn("<title", svg)
                apertura = svg.split(">", 1)[0]
                self.assertNotIn('width="', apertura)
                self.assertNotIn('height="', apertura)
                for token in svg.replace('"', " ").replace("'", " ").split():
                    if token.startswith("#"):
                        self.assertTrue(paleta.es_color_valido(token))

                # Operadores PDF balanceados y bbox positivo.
                ops, bbox = draw.spec_a_operadores(spec)
                self.assertEqual(ops.count("q\n"), ops.count("Q\n"))
                self.assertEqual(ops.count("BT\n"), ops.count("ET\n"))
                self.assertGreater(bbox[2], 0.0)
                self.assertGreater(bbox[3], 0.0)

                # Render determinista en los dos motores.
                self.assertEqual(viz.render_svg(spec), viz.render_svg(spec))
                self.assertEqual(draw.operadores_de(spec), draw.operadores_de(spec))

    def test_ningun_error_se_comunica_solo_con_color(self) -> None:
        # Req de accesibilidad: toda marca roja lleva texto que la nombra, y el
        # panel del error nombra el error y la correccion.
        rojo = paleta.normalizar_hex(paleta.ROJO)
        for fid in _IDS_ESPERADOS:
            with self.subTest(figura=fid):
                spec = figuras.figura(fid)
                rojos = [
                    it
                    for it in spec.items
                    if it.color and paleta.normalizar_hex(it.color) == rojo
                ]
                self.assertGreaterEqual(len(rojos), 1)
                for item in rojos:
                    self.assertTrue(item.etiqueta.strip())
                textos = " | ".join(_textos(spec)).lower()
                self.assertIn("corrige", textos)


class TestPaseLargoEmpeine(unittest.TestCase):
    """Pase largo: aproximacion, apoyo atras del balon, empeine y vuelo."""

    def setUp(self) -> None:
        self.spec = figuras.pase_largo_empeine()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_declara_la_carrera_de_aproximacion(self) -> None:
        self.assertIn("carrera de aproximacion", self.etiquetas)
        self.assertIn("run", _tipos(self.spec))

    def test_el_apoyo_va_al_lado_y_atras_del_balon(self) -> None:
        self.assertIn("pie de apoyo al lado y atras del balon", self.etiquetas)

    def test_declara_tronco_estable_y_contacto_con_empeine(self) -> None:
        self.assertIn("tronco estable", self.etiquetas)
        self.assertIn("contacto con el empeine", self.etiquetas)

    def test_la_trayectoria_es_aerea_y_de_distancia_amplia(self) -> None:
        self.assertIn("sube por el aire", self.etiquetas)
        self.assertIn("envio largo a la banda", self.etiquetas)
        # Dos tramos de pase: subida y caida del balon.
        self.assertGreaterEqual(_tipos(self.spec).count("pass"), 2)
        # Hay una companera lejana que recibe el envio.
        self.assertIn("player", _tipos(self.spec))

    def test_el_error_es_el_apoyo_encima_del_balon(self) -> None:
        self.assertIn("pie de apoyo encima del balon", self.etiquetas)
        self.assertIn("envio corto y sin altura", self.etiquetas)


class TestTiroPotenciaEmpeine(unittest.TestCase):
    """Tiro de potencia: preparacion, apoyo, empeine, tronco y terminacion."""

    def setUp(self) -> None:
        self.spec = figuras.tiro_potencia_empeine()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_declara_preparacion_y_apoyo_estable(self) -> None:
        self.assertIn("preparacion y ultimo paso", self.etiquetas)
        self.assertIn("pie de apoyo estable", self.etiquetas)

    def test_declara_contacto_con_empeine_e_inclinacion_del_tronco(self) -> None:
        self.assertIn("contacto con el empeine", self.etiquetas)
        self.assertIn("tronco inclinado sobre el balon", self.etiquetas)

    def test_declara_la_terminacion_de_la_pierna(self) -> None:
        self.assertIn("terminacion de la pierna", self.etiquetas)

    def test_hay_flecha_de_potencia_hacia_la_porteria(self) -> None:
        self.assertIn("potencia hacia la porteria", self.etiquetas)
        self.assertIn("porteria", self.etiquetas)
        self.assertIn("shot", _tipos(self.spec))

    def test_el_error_es_el_tronco_echado_hacia_atras(self) -> None:
        self.assertIn("tronco echado hacia atras", self.etiquetas)
        self.assertIn("por encima del travesano", self.etiquetas)


class TestTiroColocadoInterior(unittest.TestCase):
    """Tiro colocado: cuerpo abierto, contacto lateral y zona objetivo."""

    def setUp(self) -> None:
        self.spec = figuras.tiro_colocado_interior()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_declara_el_cuerpo_abierto(self) -> None:
        self.assertIn("cuerpo abierto al palo lejano", self.etiquetas)

    def test_declara_el_contacto_lateral_con_el_balon(self) -> None:
        self.assertIn("contacto lateral con el interior", self.etiquetas)

    def test_hay_trayectoria_curva_hacia_una_zona_objetivo(self) -> None:
        self.assertIn("trayectoria curva", self.etiquetas)
        self.assertIn("zona objetivo", self.etiquetas)
        self.assertIn("target", _tipos(self.spec))
        self.assertIn("zone", _tipos(self.spec))

    def test_el_error_es_la_cadera_cerrada(self) -> None:
        self.assertIn("cadera cerrada", self.etiquetas)
        self.assertIn("balon al centro", self.etiquetas)


class TestTirosSeDistinguen(unittest.TestCase):
    """El tiro colocado y el de potencia no pueden verse igual."""

    def setUp(self) -> None:
        self.potencia = figuras.tiro_potencia_empeine()
        self.colocado = figuras.tiro_colocado_interior()

    def test_son_specs_distintos(self) -> None:
        self.assertNotEqual(self.potencia, self.colocado)
        self.assertNotEqual(self.potencia.titulo, self.colocado.titulo)

    def test_solo_el_de_potencia_usa_flecha_gruesa_de_disparo(self) -> None:
        # La flecha `shot` es el trazo grueso: es el codigo visual de la fuerza.
        self.assertIn("shot", _tipos(self.potencia))
        self.assertNotIn("shot", _tipos(self.colocado))

    def test_solo_el_colocado_marca_zona_objetivo_y_punto_de_mira(self) -> None:
        self.assertIn("target", _tipos(self.colocado))
        self.assertNotIn("target", _tipos(self.potencia))
        self.assertIn("zona objetivo", _todas_las_etiquetas(self.colocado))
        self.assertNotIn("zona objetivo", _todas_las_etiquetas(self.potencia))

    def test_la_clave_de_ejecucion_es_distinta_en_el_texto(self) -> None:
        self.assertIn("disparo fuerte", " | ".join(_textos(self.potencia)).lower())
        self.assertIn("mas precision", " | ".join(_textos(self.colocado)).lower())


class TestGolpeoExterior(unittest.TestCase):
    """Golpeo con exterior: zona de contacto, cadera, tobillo y salida."""

    def setUp(self) -> None:
        self.spec = figuras.golpeo_exterior()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_marca_la_zona_de_contacto_del_exterior(self) -> None:
        self.assertIn("contacto con el exterior del pie", self.etiquetas)
        self.assertIn("zone", _tipos(self.spec))

    def test_declara_cadera_y_tobillo(self) -> None:
        self.assertIn("cadera cerrada hacia dentro", self.etiquetas)
        self.assertIn("tobillo firme y girado", self.etiquetas)

    def test_declara_la_direccion_de_salida_del_balon(self) -> None:
        self.assertIn("direccion de salida", self.etiquetas)

    def test_el_error_es_golpear_con_la_punta(self) -> None:
        self.assertIn("contacto con la punta", self.etiquetas)
        self.assertIn("tobillo suelto", self.etiquetas)


class TestControlOrientado(unittest.TestCase):
    """Control orientado: perfil, cabeza arriba, primer toque al espacio."""

    def setUp(self) -> None:
        self.spec = figuras.control_orientado()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_recibe_perfilada(self) -> None:
        self.assertIn("cuerpo perfilado", self.etiquetas)
        self.assertIn("pie de apoyo perfilado", self.etiquetas)

    def test_la_cabeza_se_levanta_antes_de_recibir(self) -> None:
        self.assertIn("cabeza levantada antes de recibir", self.etiquetas)
        self.assertIn("mira el espacio antes del control", self.etiquetas)

    def test_el_primer_toque_va_al_espacio_libre(self) -> None:
        self.assertIn("primer toque hacia el espacio libre", self.etiquetas)
        self.assertIn("espacio libre", self.etiquetas)

    def test_contrasta_controlar_detenido_con_controlar_orientado(self) -> None:
        self.assertIn("control detenido", self.etiquetas)
        self.assertIn("control orientado", self.etiquetas)
        self.assertIn("rival", _tipos(self.spec))


class TestBajarBalonAereo(unittest.TestCase):
    """Bajar balon aereo: tres superficies y amortiguacion."""

    def setUp(self) -> None:
        self.spec = figuras.bajar_balon_aereo()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_marca_las_tres_superficies_de_control(self) -> None:
        self.assertIn("control con la planta", self.etiquetas)
        self.assertIn("control con el muslo", self.etiquetas)
        self.assertIn("control con el pecho", self.etiquetas)
        self.assertGreaterEqual(_tipos(self.spec).count("zone"), 3)

    def test_declara_la_amortiguacion_retirando_la_superficie(self) -> None:
        self.assertIn("retira el pecho para amortiguar", self.etiquetas)
        self.assertIn("baja el muslo para amortiguar", self.etiquetas)

    def test_el_balon_llega_del_aire_y_queda_muerto_en_el_piso(self) -> None:
        self.assertIn("balon que cae del aire", self.etiquetas)
        self.assertIn("queda muerto en el piso", self.etiquetas)

    def test_el_error_es_que_el_balon_rebote_hacia_arriba(self) -> None:
        self.assertIn("superficie rigida", self.etiquetas)
        self.assertIn("rebota hacia arriba", self.etiquetas)


class TestConduccion(unittest.TestCase):
    """Conduccion: toques cortos, balon cerca y mirada alterna."""

    def setUp(self) -> None:
        self.spec = figuras.conduccion()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_declara_toques_cortos(self) -> None:
        self.assertIn("toques cortos y seguidos", self.etiquetas)
        self.assertGreaterEqual(_tipos(self.spec).count("dribble"), 2)

    def test_el_balon_va_cerca_del_cuerpo(self) -> None:
        self.assertIn("balon cerca del cuerpo", self.etiquetas)

    def test_declara_las_miradas_alternadas(self) -> None:
        self.assertIn("mirada al balon", self.etiquetas)
        self.assertIn("mirada al espacio", self.etiquetas)
        self.assertIn("miradas alternadas", self.etiquetas)

    def test_usa_interior_y_exterior(self) -> None:
        self.assertIn("toque con el interior", self.etiquetas)
        self.assertIn("toque con el exterior", self.etiquetas)

    def test_el_error_es_balon_lejos_y_cabeza_abajo(self) -> None:
        self.assertIn("balon lejos del cuerpo", self.etiquetas)
        self.assertIn("cabeza abajo", self.etiquetas)


class TestRegateCambioDireccion(unittest.TestCase):
    """Regate: frenado, engano, cambio de apoyo y salida explosiva."""

    def setUp(self) -> None:
        self.spec = figuras.regate_cambio_direccion()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_declara_el_frenado(self) -> None:
        self.assertIn("frena con la planta", self.etiquetas)

    def test_declara_el_engano_de_hombro_o_cadera(self) -> None:
        self.assertIn("engano de hombro", self.etiquetas)

    def test_declara_el_cambio_de_apoyo_y_la_salida_explosiva(self) -> None:
        self.assertIn("cambio de apoyo", self.etiquetas)
        self.assertIn("salida explosiva", self.etiquetas)
        self.assertIn("cambio de direccion con el exterior", self.etiquetas)

    def test_compara_el_cambio_lento_con_el_cambio_eficaz(self) -> None:
        self.assertIn("cambio lento y previsible", self.etiquetas)
        self.assertIn("centro de gravedad bajo", self.etiquetas)
        self.assertIn("centro de gravedad alto", self.etiquetas)

    def test_hay_una_rival_a_la_que_superar(self) -> None:
        self.assertIn("rival", _tipos(self.spec))


class TestAterrizajeSeguro(unittest.TestCase):
    """Aterrizaje seguro: alineacion, cadera flexionada y colapso contrastado."""

    def setUp(self) -> None:
        self.spec = figuras.aterrizaje_seguro()
        self.etiquetas = _todas_las_etiquetas(self.spec)

    def test_la_rodilla_va_alineada_con_pie_y_cadera(self) -> None:
        self.assertIn("rodilla alineada con el pie y la cadera", self.etiquetas)
        self.assertIn("linea de alineacion cadera-rodilla-pie", self.etiquetas)

    def test_declara_la_cadera_flexionada(self) -> None:
        self.assertIn("cadera flexionada", self.etiquetas)

    def test_contrasta_el_colapso_de_rodilla_hacia_adentro(self) -> None:
        self.assertIn("rodilla se va hacia adentro", self.etiquetas)
        self.assertIn("cadera casi sin flexionar", self.etiquetas)

    def test_la_rodilla_del_panel_de_error_se_desvia_de_verdad(self) -> None:
        # El contraste no es solo textual: la geometria cambia.
        ok = next(
            it
            for it in self.spec.items
            if it.etiqueta == "rodilla alineada con el pie y la cadera"
        )
        mal = next(
            it for it in self.spec.items if it.etiqueta == "rodilla se va hacia adentro"
        )
        mitad = self.spec.mundo.ancho_m / 2.0
        self.assertLess(ok.x, mitad)
        self.assertGreaterEqual(mal.x, mitad)
        # Medido desde el centro de su propio panel, la rodilla del error queda
        # mas hacia dentro que la alineada.
        self.assertGreater(mal.x - mitad, ok.x)

    def test_se_presenta_como_tecnica_no_como_diagnostico(self) -> None:
        textos = " | ".join(_textos(self.spec)).lower()
        self.assertIn("gesto tecnico de salto y caida", textos)

    def test_el_texto_no_usa_lenguaje_de_diagnostico(self) -> None:
        # Encuadre obligatorio: tecnica de salto y caida. Nada de diagnostico,
        # lesion ni rehabilitacion, ni en items ni en leyenda ni en el titulo.
        etiquetas = self.etiquetas
        for palabra in _LENGUAJE_NO_PERMITIDO:
            with self.subTest(palabra=palabra):
                self.assertNotIn(palabra, etiquetas)


if __name__ == "__main__":
    unittest.main()
