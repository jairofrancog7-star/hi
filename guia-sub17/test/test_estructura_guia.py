"""Pruebas de la estructura de la guia en el Target_Web (bloque 7).

Feature `imagenes-reales-hero-interactivo`:

* **Property 17** (tarea 7.8): estructura, orden, anclas reservadas y navegacion.
* **Property 18** (tarea 7.9): composicion del bloque de Fundamento.
* **Property 19** (tarea 7.10): Fundamento fuera del conjunto cerrado.
* **Property 20** (tarea 7.11): Bloque_Creditos completo y sin peticiones de red.
* **Property 21** (tarea 7.12): degradacion sin JavaScript.

Nota de coste: las propiedades que necesitan el documento completo lo generan con
`build_site.html_sitio(fichas=..., presentes=...)`. Las 58 Ficha_JSON se cargan
**una sola vez** por clase y se inyectan, porque el que cuesta segundos es leer y
validar el `Catalogo_JSON`, no rendirlo. Las propiedades que solo miran el tramo
de la guia usan `secciones_guia`, que no toca las fichas.

_Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 3.8, 3.9, 13.7, 13.8, 18.1, 18.2,
18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 19.1, 19.3, 19.4, 19.5, 19.6, 19.7,
20.4, 20.6_
"""

from __future__ import annotations

import dataclasses
import os
import random
import re
import sys
import unittest
from html.parser import HTMLParser

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
import lector_recursos  # noqa: E402
from guia import build_html, build_site  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia import secciones_guia as sg  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402
from guia.schema_json import cargar_catalogo  # noqa: E402
from prop import for_all  # noqa: E402

_esc = build_html._esc

#: Subconjunto vacio de Archivo_Diagrama: es el estado real del repositorio hoy y
#: el que rinde los ocho diagramas con el Generador_SVG.
VACIO: frozenset[str] = frozenset()


# --------------------------------------------------------------------------- #
# Utileria de troceado del documento
# --------------------------------------------------------------------------- #


def _articulo(marcado: str, d: dp.DiagramaPostura) -> str:
    """El `<article>` del bloque de `d`, desde su `id` hasta su cierre."""
    marca: str = f'id="{_esc(dp.id_bloque(d))}"'
    inicio: int = marcado.index(marca)
    fin: int = marcado.index("</article>", inicio)
    return marcado[inicio:fin]


def _bloque_fundamento(marcado: str, fundamento: str) -> str:
    """El bloque de `fundamento`, desde su `id` hasta el del siguiente bloque.

    Se trocea por el `id` del bloque siguiente y no por `</section>` porque los
    bloques anidan secciones (el diagrama, su Visor_Ampliado y la
    Seccion_Reservada), y contar cierres seria fragil.
    """
    posicion: int = dp.FUNDAMENTOS.index(fundamento)
    inicio: int = marcado.index(f'id="{_esc(sg.ancla_fundamento(fundamento))}"')
    if posicion + 1 < len(dp.FUNDAMENTOS):
        siguiente: str = sg.ancla_fundamento(dp.FUNDAMENTOS[posicion + 1])
        return marcado[inicio : marcado.index(f'id="{_esc(siguiente)}"')]
    return marcado[inicio:]


def _navegacion(documento: str) -> str:
    """El `<nav class="sitio">` del documento, que es el ultimo hijo de `<main>`."""
    inicio: int = documento.rindex('<nav class="sitio">')
    return documento[inicio : documento.index("</nav>", inicio)]


def _indice_de_secciones(documento: str) -> str:
    """La `<ul class="indice-secciones">` del indice del plan (criterio 19.3)."""
    inicio: int = documento.index(f'<ul class="{sg.CLASE_INDICE}">')
    return documento[inicio : documento.index("</ul>", inicio)]


def _cuerpo_falso(ancla: str):
    """Cuerpo registrable de una Seccion_Reservada, marcado para reconocerlo."""

    def render(partes: list[str]) -> None:
        partes.append(f'<p data-cuerpo="{_esc(ancla)}">contenido de otra guía</p>')

    return render


# --------------------------------------------------------------------------- #
# Property 17: estructura, orden, anclas reservadas y navegacion
# --------------------------------------------------------------------------- #


def gen_estructura(rnd: random.Random) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Un subconjunto de Archivo_Diagrama presentes y otro de cuerpos registrados.

    Los dos generadores traen su vacio y su total, asi que en 100 iteraciones se
    ven el documento de esta spec sola (registro vacio) y el de las dos specs
    juntas (registro lleno), y todo lo de en medio.
    """
    return (gen.gen_presentes(rnd), gen.gen_reservadas_registradas(rnd))


ETQ_P17 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 17: Estructura, orden, anclas reservadas y navegación"
)


class TestProperty17Estructura(unittest.TestCase):
    """Property 17: estructura, orden, anclas reservadas y navegacion."""

    def setUp(self) -> None:
        sg.limpiar_registro()

    def tearDown(self) -> None:
        sg.limpiar_registro()

    def test_property_17_estructura_y_orden(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 17: Estructura, orden, anclas reservadas y navegación.

        Para todo subconjunto de Archivo_Diagrama presentes y para todo
        subconjunto de cuerpos de Seccion_Reservada registrados, las posiciones de
        aparicion de las anclas en el documento siguen el orden hero, indice,
        `anatomia-base`, `leyenda-simbolos`, los cuatro bloques de Fundamento en
        el orden golpeo, pase, control y conduccion y cabeceo, `rutina-semanal` y
        `creditos`; toda Seccion_Reservada emite su ancla y su encabezado aunque
        su cuerpo no este registrado; y la navegacion en pagina contiene un enlace
        a `anatomia-base`, a `tecnica-en-imagenes` y a `creditos`, mientras el
        indice contiene una Zona_Tactil con enlace de ancla por cada seccion del
        plan.

        **Validates: Requirements 3.1, 3.2, 3.7, 18.1, 18.7, 19.1, 19.3, 19.5,
        19.6, 19.7**
        """

        def prop(caso: tuple[tuple[str, ...], tuple[str, ...]]) -> None:
            rutas, registradas = caso
            sg.limpiar_registro()
            try:
                for ancla in registradas:
                    sg.registrar(ancla, _cuerpo_falso(ancla))
                self.assertEqual(sg.registradas(), tuple(
                    r.ancla for r in sg.RESERVADAS if r.ancla in set(registradas)
                ))
                documento = build_site.html_sitio(
                    fichas=[], presentes=frozenset(rutas)
                )
            finally:
                sg.limpiar_registro()

            # Criterio 19.1: el orden de aparicion es el del plan.
            posiciones: list[int] = []
            for ancla in sg.PLAN:
                marca = f'id="{_esc(ancla)}"'
                self.assertIn(marca, documento, f"falta el ancla {ancla!r}")
                posiciones.append(documento.index(marca))
            self.assertEqual(
                posiciones,
                sorted(posiciones),
                f"el orden del plan no se respeta: {list(zip(sg.PLAN, posiciones))}",
            )

            # Criterios 19.6 y 19.7: ancla y encabezado de cada reservada, exista
            # o no su cuerpo; y el cuerpo solo aparece si esta registrado.
            for reservada in sg.RESERVADAS:
                self.assertIn(f'id="{_esc(reservada.ancla)}"', documento)
                etiqueta = f"h{reservada.nivel}"
                self.assertIn(
                    f"<{etiqueta}>{_esc(reservada.titulo)}</{etiqueta}>",
                    documento,
                    f"{reservada.ancla}: encabezado ausente",
                )
                marca_cuerpo = f'data-cuerpo="{_esc(reservada.ancla)}"'
                if reservada.ancla in registradas:
                    self.assertIn(marca_cuerpo, documento)
                else:
                    self.assertNotIn(marca_cuerpo, documento)

            # Criterios 3.7 y 18.7: la navegacion en pagina.
            navegacion = _navegacion(documento)
            for ancla in sg.ANCLAS_NAVEGACION:
                self.assertIn(f'href="#{_esc(ancla)}"', navegacion)

            # Criterio 19.3: una Zona_Tactil por seccion del plan en el indice.
            indice = _indice_de_secciones(documento)
            for ancla in sg.PLAN:
                self.assertIn(
                    f'<a class="{sg.CLASE_TACTIL}" href="#{_esc(ancla)}">',
                    indice,
                    f"el indice no enlaza la seccion {ancla!r}",
                )
            self.assertEqual(indice.count("<li "), len(sg.PLAN))

        for_all(gen_estructura, prop, iteraciones=100, etiqueta=ETQ_P17)

    def test_el_plan_es_el_del_criterio_19_1(self) -> None:
        sg.validar_plan()
        self.assertEqual(
            sg.PLAN,
            (
                "hero",
                "indice-guia",
                "anatomia-base",
                "leyenda-simbolos",
                "tecnica-en-imagenes",
                "fundamento-golpeo",
                "fundamento-pase",
                "fundamento-control-conduccion",
                "fundamento-cabeceo",
                "rutina-semanal",
                "creditos",
            ),
        )
        self.assertEqual(sg.anclas_esperadas(), sg.PLAN)

    def test_las_seis_reservadas_son_las_del_criterio_19_6(self) -> None:
        self.assertEqual(sg.anclas_reservadas(), gen.RESERVADAS_ANCLAS)
        self.assertEqual(len(sg.RESERVADAS), 6)

    def test_registrar_solo_acepta_anclas_reservadas(self) -> None:
        from guia.errores import E_ASSET_INVALIDO, ErrorAsset

        with self.assertRaises(ErrorAsset) as capturado:
            sg.registrar("apendice", _cuerpo_falso("apendice"))
        self.assertIn("apendice", str(capturado.exception))
        self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)

    def test_registrar_dos_veces_la_misma_ancla_es_error(self) -> None:
        from guia.errores import ErrorAsset

        sg.registrar(sg.ANCLA_LEYENDA, _cuerpo_falso(sg.ANCLA_LEYENDA))
        with self.assertRaises(ErrorAsset) as capturado:
            sg.registrar(sg.ANCLA_LEYENDA, _cuerpo_falso(sg.ANCLA_LEYENDA))
        self.assertIn(sg.ANCLA_LEYENDA, str(capturado.exception))

    def test_la_navegacion_es_el_ultimo_hijo_de_main(self) -> None:
        # Criterio 15.20: la navegacion cierra `<main>` para poder anclarse al
        # borde inferior con `position:sticky`.
        documento = build_site.html_sitio(fichas=[], presentes=VACIO)
        fin_main = documento.rindex("</main>")
        cierre_nav = documento.rindex("</nav>")
        self.assertLess(cierre_nav, fin_main)
        self.assertEqual(
            documento[cierre_nav : fin_main + len("</main>")],
            "</nav></main>",
        )


# --------------------------------------------------------------------------- #
# Property 18: composicion del bloque de Fundamento
# --------------------------------------------------------------------------- #


def gen_bloque(rnd: random.Random) -> tuple[tuple[str, ...], int]:
    """Un subconjunto de Archivo_Diagrama presentes y un Fundamento del cierre."""
    return (gen.gen_presentes(rnd), rnd.randrange(len(dp.FUNDAMENTOS)))


ETQ_P18 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 18: Composición del bloque de Fundamento"
)


class TestProperty18BloqueDeFundamento(unittest.TestCase):
    """Property 18: composicion del bloque de Fundamento."""

    def setUp(self) -> None:
        sg.limpiar_registro()

    def test_property_18_composicion_del_bloque(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 18: Composición del bloque de Fundamento.

        Para todo subconjunto de Archivo_Diagrama presentes y para todo bloque de
        Fundamento, el bloque contiene los Diagrama_Postura que el catalogo le
        asigna en el orden del catalogo, y dentro del bloque de cada diagrama
        aparecen, en este orden de posicion: el titulo como encabezado de nivel 3,
        el elemento `<figure>` con su contenido grafico, la lista ordenada con
        exactamente un elemento por paso declarado y con el mismo texto, y el
        error frecuente, seguido del ancla `ejercicios-<fundamento>`; y en el
        bloque de cabeceo la Advertencia_Cabeceo aparece despues del `<figure>` y
        antes de la lista de pasos.

        **Validates: Requirements 3.3, 3.5, 3.6, 19.4, 20.4**
        """

        def prop(caso: tuple[tuple[str, ...], int]) -> None:
            rutas, indice = caso
            presentes = frozenset(rutas)
            fundamento = dp.FUNDAMENTOS[indice % len(dp.FUNDAMENTOS)]

            partes: list[str] = []
            sg.render_tecnica(partes, presentes=presentes)
            bloque = _bloque_fundamento("".join(partes), fundamento)

            entradas = dp.por_fundamento(fundamento)
            self.assertTrue(entradas, f"{fundamento}: sin diagramas asignados")

            # Criterio 3.3: los diagramas del catalogo, en el orden del catalogo.
            posiciones = [
                bloque.index(f'data-diagrama="{_esc(d.id)}"') for d in entradas
            ]
            self.assertEqual(posiciones, sorted(posiciones))

            for entrada in entradas:
                articulo = _articulo(bloque, entrada)
                # Criterio 3.6: el titulo como encabezado de nivel 3.
                titulo = f"<h3>{_esc(entrada.titulo)}</h3>"
                self.assertIn(titulo, articulo)
                pos_titulo = articulo.index(titulo)
                pos_figura = articulo.index("<figure")
                pos_cierre_figura = articulo.index("</figure>")
                pos_pasos = articulo.index(f'<ol class="{dp.CLASE_PASOS}">')
                pos_error = articulo.index(f'<p class="{dp.CLASE_ERROR}">')
                self.assertLess(pos_titulo, pos_figura)
                self.assertLess(pos_cierre_figura, pos_pasos)
                self.assertLess(pos_pasos, pos_error)

                # Criterio 3.4: exactamente un contenido grafico en el `<figure>`.
                figura = articulo[pos_figura:pos_cierre_figura]
                self.assertEqual(figura.count("<img") + figura.count("<svg"), 1)

                # Criterio 3.5: un `<li>` por paso declarado, con el mismo texto.
                lista = articulo[pos_pasos : articulo.index("</ol>", pos_pasos)]
                self.assertEqual(lista.count("<li>"), len(entrada.pasos))
                for paso in entrada.pasos:
                    self.assertIn(f"<li>{_esc(paso)}</li>", lista)

                # El error frecuente, con su rotulo de texto.
                self.assertIn(_esc(entrada.error_frecuente), articulo)
                self.assertIn(_esc(dp.ETIQUETA_ERROR), articulo)

                # Criterio 20.4: la advertencia va tras el `<figure>` y antes de
                # los pasos, y solo `cabeceo-frente` la declara.
                if entrada.advertencia is not None:
                    pos_aviso = articulo.index(f'<p class="{dp.CLASE_AVISO}">')
                    self.assertLess(pos_cierre_figura, pos_aviso)
                    self.assertLess(pos_aviso, pos_pasos)
                    self.assertIn(_esc(entrada.advertencia), articulo)
                else:
                    self.assertNotIn(f'<p class="{dp.CLASE_AVISO}">', articulo)

            # Criterio 19.4: la Seccion_Reservada del Fundamento cierra el bloque,
            # despues del error frecuente del ultimo diagrama.
            ancla = sg.ancla_ejercicios(fundamento)
            self.assertIn(f'id="{_esc(ancla)}"', bloque)
            ultimo = _articulo(bloque, entradas[-1])
            self.assertLess(
                bloque.index(ultimo) + len(ultimo),
                bloque.index(f'id="{_esc(ancla)}"'),
            )

        for_all(gen_bloque, prop, iteraciones=100, etiqueta=ETQ_P18)

    def test_los_cuatro_bloques_van_en_el_orden_del_criterio_19_5(self) -> None:
        partes: list[str] = []
        sg.render_tecnica(partes, presentes=VACIO)
        marcado = "".join(partes)
        posiciones = [
            marcado.index(f'id="{sg.ancla_fundamento(f)}"') for f in dp.FUNDAMENTOS
        ]
        self.assertEqual(posiciones, sorted(posiciones))
        self.assertEqual(dp.FUNDAMENTOS, ("golpeo", "pase", "control-conduccion", "cabeceo"))

    def test_la_seccion_de_tecnica_lleva_su_ancla(self) -> None:
        partes: list[str] = []
        sg.render_tecnica(partes, presentes=VACIO)
        self.assertIn(f'id="{dp.ANCLA_TECNICA}"', "".join(partes))


# --------------------------------------------------------------------------- #
# Property 19: Fundamento fuera del conjunto cerrado
# --------------------------------------------------------------------------- #

ETQ_P19 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 19: Fundamento fuera del conjunto cerrado"
)


class TestProperty19FundamentoAjeno(unittest.TestCase):
    """Property 19: Fundamento fuera del conjunto cerrado."""

    def setUp(self) -> None:
        sg.limpiar_registro()

    def test_property_19_fundamento_ajeno(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 19: Fundamento fuera del conjunto cerrado.

        Para todo catalogo que declara uno o mas Fundamento fuera del conjunto
        cerrado de cuatro, el Motor_Sitio emite exactamente los cuatro bloques
        declarados, ningun bloque para los fundamentos ajenos, y el reporte del
        Orquestador_Build enumera exactamente los fundamentos omitidos.

        **Validates: Requirements 3.9**
        """

        def prop(mutado: gen.CatalogoMutado) -> None:
            catalogo = mutado.catalogo
            partes: list[str] = []
            omitidos = sg.render_tecnica(
                partes, presentes=VACIO, catalogo=catalogo
            )
            marcado = "".join(partes)

            # Exactamente los cuatro bloques del conjunto cerrado.
            self.assertEqual(
                marcado.count(f'class="{sg.CLASE_FUNDAMENTO}"'),
                len(dp.FUNDAMENTOS),
            )
            for fundamento in dp.FUNDAMENTOS:
                self.assertIn(f'data-fundamento="{_esc(fundamento)}"', marcado)

            # Ningun bloque para los fundamentos ajenos, y ningun diagrama suyo.
            for ajeno in mutado.ajenos:
                self.assertNotIn(f'data-fundamento="{_esc(ajeno)}"', marcado)
            for entrada in catalogo:
                if entrada.fundamento in mutado.ajenos:
                    self.assertNotIn(
                        f'data-diagrama="{_esc(entrada.id)}"', marcado
                    )
                elif entrada.fundamento is not None:
                    self.assertIn(f'data-diagrama="{_esc(entrada.id)}"', marcado)

            # El reporte enumera exactamente los fundamentos omitidos.
            self.assertEqual(set(omitidos), set(mutado.ajenos))
            self.assertEqual(
                set(dp.fundamentos_omitidos(catalogo)), set(mutado.ajenos)
            )
            self.assertEqual(len(set(omitidos)), len(omitidos))

        for_all(
            gen.gen_catalogo_fundamento_ajeno,
            prop,
            iteraciones=100,
            etiqueta=ETQ_P19,
        )

    def test_el_catalogo_declarado_no_omite_ningun_fundamento(self) -> None:
        self.assertEqual(dp.fundamentos_omitidos(), ())
        partes: list[str] = []
        self.assertEqual(sg.render_tecnica(partes, presentes=VACIO), ())


# --------------------------------------------------------------------------- #
# Property 20: Bloque_Creditos completo y sin peticiones de red
# --------------------------------------------------------------------------- #


def _catalogo_sin_campos(campos: tuple[str, ...]) -> tuple[dp.DiagramaPostura, ...]:
    """El catalogo real con `campos` del credito puestos a `None` en las ocho."""
    cambios = {campo: None for campo in campos}
    return tuple(
        dataclasses.replace(
            d, credito=dataclasses.replace(d.credito, **cambios)
        )
        for d in dp.CATALOGO
    )


def gen_creditos(rnd: random.Random) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Un subconjunto de presentes y un subconjunto de campos de credito ausentes."""
    return (gen.gen_presentes(rnd), gen.gen_campos_credito_ausentes(rnd))


ETQ_P20 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 20: Bloque_Creditos completo y sin peticiones de red"
)


class TestProperty20BloqueCreditos(unittest.TestCase):
    """Property 20: Bloque_Creditos completo y sin peticiones de red."""

    def test_property_20_bloque_creditos(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 20: Bloque_Creditos completo y sin peticiones de red.

        Para todo subconjunto de Archivo_Diagrama presentes y para todo
        subconjunto de campos de credito ausentes, el Bloque_Creditos contiene
        exactamente una entrada por Diagrama_Postura del catalogo; cada entrada
        contiene autor, fuente, licencia y enlace, con la marca "dato pendiente"
        en cada campo ausente; las entradas de los diagramas rendidos por el
        Generador_SVG declaran la autoria y la licencia propias del proyecto;
        ningun enlace se emite como elemento `<a href>` ni con ningun atributo que
        provoque una peticion de red; el reporte enumera el identificador de cada
        entrada incompleta junto al nombre de cada campo ausente y el build
        termina.

        **Validates: Requirements 18.2, 18.3, 18.4, 18.5, 18.6, 18.8, 18.9**
        """

        def prop(caso: tuple[tuple[str, ...], tuple[str, ...]]) -> None:
            rutas, ausentes = caso
            presentes = frozenset(rutas)
            catalogo = _catalogo_sin_campos(ausentes)

            partes: list[str] = []
            dp.render_creditos(partes, presentes=presentes, catalogo=catalogo)
            marcado = "".join(partes)

            # Criterios 18.1 y 18.6: el bloque existe siempre, con su ancla.
            self.assertIn(f'id="{_esc(dp.ANCLA_CREDITOS)}"', marcado)

            # Criterio 18.2: una entrada por Diagrama_Postura, ni una mas.
            self.assertEqual(
                marcado.count(f'class="{dp.CLASE_CREDITO}"'), len(catalogo)
            )

            for entrada in catalogo:
                self.assertIn(f'data-credito="{_esc(entrada.id)}"', marcado)

            # Criterio 18.5: ni un `<a href>` ni ningun atributo de red.
            for prohibido in ("<a ", "href=", "src=", "http", "url("):
                self.assertNotIn(prohibido, marcado, prohibido)

            for entrada in catalogo:
                inicio = marcado.index(f'data-credito="{_esc(entrada.id)}"')
                fin = marcado.index("</li>", inicio)
                celda = marcado[inicio:fin]
                # Criterio 18.3: los cuatro campos, con su rotulo visible.
                for campo, rotulo in dp.ROTULOS_CREDITO:
                    self.assertIn(f'data-campo="{campo}"', celda)
                    self.assertIn(f"<dt>{_esc(rotulo)}</dt>", celda)
                    valor = dp.campo_de_credito(entrada.credito, campo)
                    esperado = (
                        dp.MARCA_PENDIENTE if valor is None else valor
                    )
                    self.assertIn(
                        f'<dd data-campo="{campo}">{_esc(esperado)}</dd>', celda
                    )
                    # Criterio 18.8: la marca solo en los campos ausentes.
                    if campo in ausentes:
                        self.assertIsNone(valor)

                # Criterio 18.4: los rendidos por el Generador_SVG declaran la
                # autoria y la licencia propias del proyecto, cuando las tienen.
                if dp.modo_render(entrada, presentes) == dp.MODO_SVG:
                    if "autor" not in ausentes:
                        self.assertIn(_esc(dp.CREDITO_PROPIO.autor), celda)
                    if "licencia" not in ausentes:
                        self.assertIn(_esc(dp.CREDITO_PROPIO.licencia), celda)

            # Criterio 18.9: el reporte enumera id y campos ausentes, y el build
            # termina (esta llamada no lanza nada).
            esperados = tuple(
                campo
                for campo in dp.CAMPOS_CREDITO
                if dp.campo_de_credito(dp.CREDITO_PROPIO, campo) is None
                or campo in ausentes
            )
            pendientes = dp.campos_pendientes(catalogo)
            self.assertEqual(
                pendientes,
                tuple((d.id, esperados) for d in catalogo),
            )

        for_all(gen_creditos, prop, iteraciones=100, etiqueta=ETQ_P20)

    def test_el_bloque_existe_con_los_ocho_en_svg(self) -> None:
        # Criterio 18.6: sin ningun Archivo_Diagrama el bloque sigue completo.
        partes: list[str] = []
        dp.render_creditos(partes, presentes=VACIO)
        marcado = "".join(partes)
        self.assertEqual(
            marcado.count(f'class="{dp.CLASE_CREDITO}"'), len(dp.CATALOGO)
        )
        self.assertEqual(marcado.count('data-modo="svg"'), len(dp.CATALOGO))
        self.assertIn(_esc(dp.CREDITO_PROPIO.autor), marcado)
        self.assertIn(_esc(dp.CREDITO_PROPIO.licencia), marcado)

    def test_el_enlace_ausente_se_marca_como_pendiente(self) -> None:
        # Las ocho entradas declaran `enlace=None`, asi que las ocho lo marcan.
        partes: list[str] = []
        dp.render_creditos(partes, presentes=VACIO)
        marcado = "".join(partes)
        self.assertEqual(
            marcado.count(
                f'<dd data-campo="enlace">{_esc(dp.MARCA_PENDIENTE)}</dd>'
            ),
            len(dp.CATALOGO),
        )
        self.assertEqual(
            dp.campos_pendientes(),
            tuple((d.id, ("enlace",)) for d in dp.CATALOGO),
        )


# --------------------------------------------------------------------------- #
# Property 21: degradacion sin JavaScript
# --------------------------------------------------------------------------- #

#: Ancla y enlace de indice de una ficha, para leer las 58 en una sola pasada.
_RE_ANCLA_FICHA = re.compile(r'id="ficha-([^"]+)"')
_RE_ENLACE_FICHA = re.compile(r'href="#ficha-([^"]+)"')

ETQ_P21 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 21: Degradación sin JavaScript"
)


class TestProperty21SinJavaScript(unittest.TestCase):
    """Property 21: degradacion sin JavaScript."""

    @classmethod
    def setUpClass(cls) -> None:
        # Las 58 Ficha_JSON se cargan y validan una sola vez: lo caro es leer el
        # catalogo, no rendirlo, y esta propiedad necesita las fichas reales.
        cls.fichas = cargar_catalogo(cap10_fundamentos.ruta_catalogo())
        cls.css = build_html.estilo_css()

    def setUp(self) -> None:
        sg.limpiar_registro()

    @staticmethod
    def _sin_script(documento: str) -> str:
        bajo = documento.lower()
        inicio = bajo.index("<script")
        fin = bajo.index("</script>") + len("</script>")
        return documento[:inicio] + documento[fin:]

    def test_property_21_degradacion_sin_javascript(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 21: Degradación sin JavaScript.

        Para todo subconjunto de Archivo_Diagrama presentes, retirar el elemento
        `<script>` del documento conserva integros los ocho bloques de
        Diagrama_Postura con su contenido grafico, sus listas de pasos, sus fases y
        la Advertencia_Cabeceo, mas las anclas de todas las secciones del plan, el
        Bloque_Creditos, las 58 fichas con sus anclas, el buscador y sus filtros,
        el indice y los tres enlaces de descarga relativos.

        **Validates: Requirements 3.8, 13.7, 13.8, 20.6**
        """

        def prop(rutas: tuple[str, ...]) -> None:
            presentes = frozenset(rutas)
            documento = build_site.html_sitio(
                fichas=self.fichas, presentes=presentes
            )
            sin_js = self._sin_script(documento)
            self.assertNotIn("<script", sin_js.lower())

            # Los ocho bloques, con su contenido grafico y sus pasos.
            for entrada in dp.CATALOGO:
                articulo = _articulo(sin_js, entrada)
                self.assertEqual(
                    articulo.count("<img") + articulo.count("<svg"),
                    1,
                    f"{entrada.id}: contenido grafico ausente sin JavaScript",
                )
                for paso in entrada.pasos:
                    self.assertIn(f"<li>{_esc(paso)}</li>", articulo)
                for fase in entrada.fases:
                    self.assertIn(
                        f'<li value="{fase.numero}">{_esc(fase.texto)}</li>',
                        articulo,
                    )
                self.assertIn(_esc(entrada.error_frecuente), articulo)

            # Criterio 20.6: la Advertencia_Cabeceo es texto del HTML.
            self.assertIn(_esc(dp.ADVERTENCIA_CABECEO), sin_js)

            # Las anclas de todas las secciones del plan y de las reservadas.
            for ancla in (*sg.PLAN, *sg.anclas_reservadas()):
                self.assertIn(f'id="{_esc(ancla)}"', sin_js)

            # El Bloque_Creditos completo.
            self.assertEqual(
                sin_js.count(f'class="{dp.CLASE_CREDITO}"'), len(dp.CATALOGO)
            )

            # Las 58 fichas con su ancla y su entrada de indice. Se leen en una
            # sola pasada con expresion regular: `assertIn` una vez por ficha
            # recorreria el documento de 3 MB ciento dieciseis veces por
            # iteracion, y la propiedad tardaria minutos en vez de segundos.
            self.assertEqual(len(self.fichas), 58)
            esperadas = {ficha["id"] for ficha in self.fichas}
            self.assertEqual(set(_RE_ANCLA_FICHA.findall(sin_js)), esperadas)
            self.assertEqual(set(_RE_ENLACE_FICHA.findall(sin_js)), esperadas)

            # El buscador con sus filtros, y el indice.
            bajo = sin_js.lower()
            for marca in (
                'type="search"',
                'id="gb-q"',
                'id="gb-cat"',
                'id="gb-niv"',
                'class="indice-capitulos"',
                f'class="{sg.CLASE_INDICE}"',
            ):
                self.assertIn(marca, bajo)

            # Los tres enlaces de descarga relativos.
            for descarga in (
                'href="guia.pdf" download',
                'href="laminas.pdf" download',
                'href="ejercicios.json" download',
            ):
                self.assertIn(descarga, bajo)

            # Y las Vista_Figura del Visor_Ampliado siguen todas en el DOM.
            self.assertEqual(sin_js.count('class="visor-ampliado"'), 8)
            # Sin JavaScript el overlay sigue siendo alcanzable y con salida: la
            # regla `:target` lo destapa y su cierre es un `<a>` de ancla.
            self.assertIn(f".{sg.CLASE_VISOR}:target{{display:flex;}}", self.css)
            # La clase que le da el mando al JavaScript la pone el Script_Unico
            # sobre `<html>`; el marcado emitido no la trae, asi que sin script
            # manda `:target` y el overlay sigue abriendose y cerrandose.
            self.assertNotIn(f'class="{sg.CLASE_CON_JS}"', sin_js)

        for_all(gen.gen_presentes, prop, iteraciones=100, etiqueta=ETQ_P21)


# --------------------------------------------------------------------------- #
# El Visor_Ampliado como overlay modal, leido sobre el documento emitido
# --------------------------------------------------------------------------- #


def _cuerpo_de_regla(css: str, selector: str) -> str:
    """Cuerpo de la regla cuyo selector es EXACTAMENTE `selector`.

    Hace falta buscar por selector exacto y no por subcadena: `.visor-cerrar`
    aparece tambien al final de la regla agrupada de todas las Zona_Tactil, y
    `css.index(".visor-cerrar{")` caeria ahi.
    """
    for regla in gen.reglas(css):
        if regla.selector == selector:
            return regla.cuerpo
    return ""


class LectorOverlays(HTMLParser):
    """Recoge cada `<section class="visor-ampliado">` del documento emitido.

    Se lee con `html.parser.HTMLParser` y no con busquedas de subcadena porque las
    preguntas son de **estructura**: cuantos `<h2>` hay DENTRO de cada overlay, si
    su `aria-labelledby` apunta a un `id` que existe de verdad y si el `<svg>` del
    icono vive dentro de la Zona_Tactil de cierre. Contar `"<h2"` sobre el
    documento entero no responde ninguna de las tres.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        #: Todos los `id` del documento, para resolver `aria-labelledby`.
        self.ids: list[str] = []
        #: Un registro por overlay, en orden de documento.
        self.overlays: list[dict[str, object]] = []
        self._actual: dict[str, object] | None = None
        self._prof: int = 0
        self._en_cierre: bool = False

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: D102
        mapa: dict[str, str] = {n: (v or "") for n, v in attrs}
        if "id" in mapa:
            self.ids.append(mapa["id"])
        clases: list[str] = mapa.get("class", "").split()
        if tag == "section" and sg.CLASE_VISOR in clases:
            self._actual = {
                "id": mapa.get("id", ""),
                "role": mapa.get("role", ""),
                "aria-modal": mapa.get("aria-modal", ""),
                "aria-labelledby": mapa.get("aria-labelledby", ""),
                "hidden": "hidden" in mapa,
                "h2": [],
                "cierres": 0,
                "aria-cerrar": "",
                "svg_cierre": 0,
                "barras": 0,
                "cuerpos": 0,
                "lienzos": 0,
            }
            self.overlays.append(self._actual)
            self._prof = 1
            return
        if self._actual is None:
            return
        if tag not in lector_recursos.ETIQUETAS_VACIAS:
            self._prof += 1
        if tag == "h2":
            self._actual["h2"].append(mapa.get("id", ""))
        if sg.CLASE_BARRA in clases:
            self._actual["barras"] += 1
        if sg.CLASE_CUERPO_VISOR in clases:
            self._actual["cuerpos"] += 1
        if sg.CLASE_LIENZO in clases:
            self._actual["lienzos"] += 1
        if sg.CLASE_CERRAR in clases:
            self._actual["cierres"] += 1
            self._actual["aria-cerrar"] = mapa.get("aria-label", "")
            self._en_cierre = True
        if tag == "svg" and self._en_cierre:
            self._actual["svg_cierre"] += 1

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        if self._actual is None:
            return
        if tag == "a":
            self._en_cierre = False
        self._prof -= 1
        if self._prof <= 0:
            self._actual = None


class TestVisorAmpliadoComoOverlayModal(unittest.TestCase):
    """El Visor_Ampliado es un overlay modal de verdad, no una seccion que crece.

    Antes de este rediseño el "modal" era una `<section>` del flujo del documento
    que `:target` estiraba a `100dvh`. De ahi salian los cuatro sintomas que la
    usuaria veia: el titulo del bloque y el del visor pintados encimados, ningun
    velo ni barra superior, un "Cerrar" con pinta de enlace roto y la ilustracion
    desbordada. Estas pruebas fijan el contrato nuevo sobre el documento emitido.

    _Requirements: 28.5, 28.13, 28.16, 28.21, 28.22, 28.23, 28.24_
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.documento: str = build_site.html_sitio()
        cls.css: str = build_html.estilo_css()
        lector = LectorOverlays()
        lector.feed(cls.documento)
        lector.close()
        cls.lector = lector

    def test_un_overlay_por_diagrama(self) -> None:
        self.assertEqual(len(self.lector.overlays), len(dp.CATALOGO))

    def test_exactamente_un_h2_por_overlay(self) -> None:
        # El sintoma de los titulos encimados: antes el visor repetia el titulo del
        # bloque dentro del mismo flujo. Ahora hay UN encabezado y es el del
        # overlay, con el `id` que su `aria-labelledby` nombra.
        for overlay in self.lector.overlays:
            with self.subTest(overlay=overlay["id"]):
                self.assertEqual(
                    len(overlay["h2"]),
                    1,
                    f"{overlay['id']}: {len(overlay['h2'])} encabezados <h2>",
                )
                self.assertTrue(overlay["h2"][0].startswith(sg.PREFIJO_TITULO_MODAL))

    def test_semantica_de_dialogo(self) -> None:
        ids = set(self.lector.ids)
        for overlay in self.lector.overlays:
            with self.subTest(overlay=overlay["id"]):
                self.assertEqual(overlay["role"], "dialog")
                self.assertEqual(overlay["aria-modal"], "true")
                etiqueta = overlay["aria-labelledby"]
                self.assertIn(etiqueta, ids, "aria-labelledby apunta a la nada")
                self.assertEqual([etiqueta], overlay["h2"])

    def test_cierre_con_icono_en_svg_y_etiqueta_accesible(self) -> None:
        for overlay in self.lector.overlays:
            with self.subTest(overlay=overlay["id"]):
                self.assertEqual(overlay["cierres"], 1)
                self.assertEqual(overlay["aria-cerrar"], sg.TEXTO_CERRAR)
                # La ✕ es un `<svg>` en linea, no un caracter suelto.
                self.assertEqual(overlay["svg_cierre"], 1)
        # Y el cierre mide 44 px de lado en los dos ejes, con forma circular.
        regla = _cuerpo_de_regla(self.css, f".{sg.CLASE_CERRAR}")
        self.assertIn(f"min-height:{build_html.LADO_TOQUE_PX}px", regla)
        self.assertIn(f"min-width:{build_html.LADO_TOQUE_PX}px", regla)
        self.assertIn("border-radius:999px", regla)

    def test_barra_cuerpo_y_lienzo_una_vez_cada_uno(self) -> None:
        for overlay in self.lector.overlays:
            with self.subTest(overlay=overlay["id"]):
                self.assertEqual(overlay["barras"], 1)
                self.assertEqual(overlay["cuerpos"], 1)
                self.assertEqual(overlay["lienzos"], 1)

    def test_layout_de_overlay_y_una_sola_position_fixed(self) -> None:
        # La UNICA `position:fixed` de la hoja, y es la del overlay (criterio 28.5).
        self.assertEqual(self.css.count("position:fixed"), 1)
        posiciones = dict(gen.declaraciones(self.css, "position"))
        self.assertEqual(posiciones.get(f".{sg.CLASE_VISOR}"), "fixed")
        regla = _cuerpo_de_regla(self.css, f".{sg.CLASE_VISOR}")
        for pieza in (
            "touch-action:none",
            "position:fixed",
            "inset:0",
            f"z-index:{build_html.CAPA_MODAL}",
            "display:flex",
            "flex-direction:column",
            "color-mix(in srgb, var(--fondo-modal) 85%, transparent)",
            f"backdrop-filter:blur({build_html.DESENFOQUE_MODAL})",
        ):
            with self.subTest(pieza=pieza):
                self.assertIn(pieza, regla)

    def test_barra_superior_fija_con_titulo_truncado(self) -> None:
        barra = _cuerpo_de_regla(self.css, f".{sg.CLASE_BARRA}")
        self.assertIn(f"height:{build_html.ALTO_BARRA_MODAL}px", barra)
        self.assertIn("display:flex", barra)
        self.assertIn("justify-content:space-between", barra)
        self.assertIn("align-items:center", barra)
        titulo = _cuerpo_de_regla(self.css, f".{sg.CLASE_TITULO_VISOR}")
        for pieza in (
            "text-overflow:ellipsis",
            "white-space:nowrap",
            "overflow:hidden",
        ):
            with self.subTest(pieza=pieza):
                self.assertIn(pieza, titulo)

    def test_cuerpo_desplazable_y_gesto_contenido(self) -> None:
        cuerpo = _cuerpo_de_regla(self.css, f".{sg.CLASE_CUERPO_VISOR}")
        self.assertIn("overflow-y:auto", cuerpo)
        self.assertIn("overscroll-behavior:contain", cuerpo)

    def test_ilustracion_contenida_en_su_recuadro(self) -> None:
        lienzo = _cuerpo_de_regla(self.css, f".{sg.CLASE_LIENZO}")
        self.assertIn(f"aspect-ratio:var({dp.VARIABLE_RELACION}", lienzo)
        self.assertIn(f"max-height:{build_html.ALTO_MAX_LIENZO}", lienzo)
        self.assertIn("display:flex", lienzo)
        ajustes = dict(gen.declaraciones(self.css, "object-fit"))
        clave = f".{sg.CLASE_LIENZO} img,.{sg.CLASE_LIENZO} svg"
        self.assertEqual(ajustes.get(clave), "contain")
        anchos = dict(gen.declaraciones(self.css, "width"))
        self.assertEqual(anchos.get(clave), "100%")
        # Y cada lienzo declara la relacion de aspecto de SU diagrama.
        for entrada in dp.CATALOGO:
            ancho, alto = dp.dimensiones(entrada, dp.MODO_SVG)
            with self.subTest(diagrama=entrada.id):
                self.assertIn(
                    f'class="{sg.CLASE_LIENZO}" '
                    f'style="{dp.VARIABLE_RELACION}:{ancho}/{alto}"',
                    self.documento,
                )

    def test_bloqueo_de_scroll_por_clase_y_no_en_linea(self) -> None:
        # El bloqueo cuelga de una CLASE en `<body>`, porque el Script_Unico solo
        # tiene permitido escribir `transform`, `opacity`, `visibility` y
        # `will-change` en linea (criterio 10.3).
        self.assertIn(
            f"body.{sg.CLASE_CUERPO_FIJO}{{overflow:hidden;}}", self.css
        )
        js = build_site._js_hero()
        self.assertIn("classList.add(CL_FIJO)", js)
        self.assertIn("classList.remove(CL_FIJO)", js)
        # Y guarda y restaura la posicion exacta de desplazamiento.
        abrir = gen.cuerpo_de_funcion(js, "abrirModal")
        cerrar = gen.cuerpo_de_funcion(js, "cerrarModal")
        self.assertIn("modalScroll=window.scrollY||0;", abrir)
        self.assertIn("window.scrollTo(0,modalScroll);", cerrar)
        self.assertNotIn(".style.", abrir)
        self.assertNotIn(".style.", cerrar)

    def test_las_tres_maneras_de_cerrar_y_la_trampa_de_foco(self) -> None:
        js = build_site._js_hero()
        # Clic o toque en la Zona_Tactil de cierre.
        self.assertIn("nodoCer.addEventListener('click',alCerrarVisor);", js)
        # Escape.
        trampa = gen.cuerpo_de_funcion(js, "atraparFoco")
        self.assertIn("if(tecla==='Escape'){cerrarModal();return;}", trampa)
        self.assertIn("document.addEventListener('keydown',atraparFoco);", js)
        # Toque en el fondo, comprobando el blanco contra el propio overlay.
        fondo = gen.cuerpo_de_funcion(js, "alTocarFondo")
        self.assertIn("blanco===overlay", fondo)
        self.assertIn("cerrarModal();", fondo)
        # Tab atrapado dentro del overlay.
        self.assertIn("ev.preventDefault();", trampa)
        # Foco al cierre al abrir y de vuelta al origen al cerrar.
        abrir = gen.cuerpo_de_funcion(js, "abrirModal")
        cerrar = gen.cuerpo_de_funcion(js, "cerrarModal")
        self.assertIn("enfocar(cierreDe(ov));", abrir)
        self.assertIn("enfocar(origen);", cerrar)

    def test_mejora_progresiva_en_tres_reglas_y_en_ese_orden(self) -> None:
        # Sin JavaScript manda `:target`; con el Script_Unico vivo manda `hidden`.
        oculta = f".{sg.CLASE_VISOR}[hidden]{{display:none;}}"
        objetivo = f".{sg.CLASE_VISOR}:target{{display:flex;}}"
        con_js = f".{sg.CLASE_CON_JS} .{sg.CLASE_VISOR}[hidden]{{display:none;}}"
        for regla in (oculta, objetivo, con_js):
            with self.subTest(regla=regla):
                self.assertIn(regla, self.css)
        self.assertLess(self.css.index(oculta), self.css.index(objetivo))
        self.assertLess(self.css.index(objetivo), self.css.index(con_js))
        # Y el overlay se emite con `hidden`, que es su estado de reposo.
        for overlay in self.lector.overlays:
            with self.subTest(overlay=overlay["id"]):
                self.assertTrue(overlay["hidden"])
        # La clase que enciende el control por JavaScript la pone el script, nunca
        # el HTML emitido.
        self.assertIn("classList.add(CL_CON_JS)", build_site._js_hero())

    def test_el_script_sigue_siendo_uno_y_con_un_solo_bucle(self) -> None:
        bajo = self.documento.lower()
        self.assertEqual(bajo.count("<script"), 1)
        cuerpo = self.documento[bajo.index("<script") : bajo.index("</script>")]
        self.assertEqual(cuerpo.count("requestAnimationFrame("), 1)
        for prohibida in ("//", "import", "require(", "src=", "http"):
            with self.subTest(prohibida=prohibida):
                self.assertNotIn(prohibida, cuerpo.lower())


if __name__ == "__main__":
    unittest.main()
