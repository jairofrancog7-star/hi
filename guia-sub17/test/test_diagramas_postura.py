"""Pruebas del Catalogo_Diagramas, del vocabulario, del lexico y del cabeceo.

Feature `imagenes-reales-hero-interactivo`, bloque 2:

* **Property 1** (tarea 2.6): forma del Catalogo_Diagramas.
* **Property 2** (tarea 2.7): vocabulario anatomico cerrado.
* **Property 3** (tarea 2.8): Guardarrail_Lexico.
* **Property 4** (tarea 2.9): Advertencia_Cabeceo obligatoria y completa.

Bloque 7, render de los bloques de diagrama:

* **Property 12** (tarea 7.6): render hibrido y dimensiones efectivas.
* **Property 13** (tarea 7.7): carga diferida de las imagenes.

_Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12,
3.4, 4.1, 4.2, 4.3, 4.4, 4.8, 5.1, 5.2, 5.3, 5.4, 5.5, 14.12, 14.13, 14.14,
14.16, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 20.1, 20.2, 20.3, 20.5_
"""

from __future__ import annotations

import os
import random
import sys
import unittest

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto; `unittest discover` no ejecuta
# `test/__init__.py`).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

from guia import diagramas_postura as dp  # noqa: E402
from guia import figuras  # noqa: E402
from guia.errores import E_ASSET_INVALIDO, ErrorAsset  # noqa: E402
from prop import for_all  # noqa: E402

# --------------------------------------------------------------------------- #
# Tablas congeladas de la tabla de Data Models del diseno
# --------------------------------------------------------------------------- #

#: Dimensiones declaradas por entrada: `(archivo, svg)`.
_DIMENSIONES: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "anatomia-base": ((1200, 1800), (360, 540)),
    "tiro-empeine": ((1200, 1600), (360, 480)),
    "pase-interior": ((1200, 1600), (360, 480)),
    "control-balon": ((1200, 1600), (360, 480)),
    "conduccion": ((1200, 1600), (360, 480)),
    "potencia-carrera": ((1200, 1600), (360, 480)),
    "cabeceo-frente": ((1200, 1600), (360, 480)),
    "pase-largo-empeine": ((1200, 1600), (360, 480)),
}

#: Marca que debe aparecer en cada paso segun su posicion en el orden fijo del
#: criterio 2.7: pie de apoyo, superficie de contacto, torso, brazos y mirada. La
#: posicion 2 se comprueba contra `SUPERFICIES_CONTACTO` y la 5 contra el verbo
#: inicial, que en todas las entradas es "mira".
_MARCA_POR_PASO: tuple[str, ...] = ("pie", "", "torso", "brazo", "")


def gen_indice(rnd: random.Random) -> int:
    """Indice de una entrada del Catalogo_Diagramas."""
    return rnd.randrange(len(dp.CATALOGO))


ETQ_P1 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 1: Forma del Catalogo_Diagramas"
)


class TestProperty1FormaDelCatalogo(unittest.TestCase):
    """Property 1: forma del Catalogo_Diagramas."""

    def test_property_1_forma_del_catalogo(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 1: Forma del Catalogo_Diagramas.

        Para toda entrada del Catalogo_Diagramas: su identificador y su posicion
        coinciden con el orden declarado; su Archivo_Diagrama es
        `assets/img/tecnica/<id>.<ext>` con extension aceptada; su ancho vive en
        (0, 1200] y su alto es positivo en los dos modos; su texto alternativo
        tiene 60 caracteres o mas y nombra la superficie de contacto con al menos
        dos elementos de postura (o seis Etiqueta_Anatomica en `anatomia-base`);
        tiene cinco pasos en el orden fijo, de 20 caracteres o mas y empezando
        por un verbo permitido; su Fundamento pertenece al conjunto cerrado o es
        nulo solo en `anatomia-base`; su postura equivalente existe en
        `figuras.FIGURAS` o es nula solo en `anatomia-base` y `cabeceo-frente`;
        su marca Requiere_Archivo es falsa; `pase-largo-empeine` declara el pase
        elevado a distancia en su titulo y en su texto alternativo y
        `potencia-carrera` declara sus tres Fase_Numerada en el orden fijo.

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9,
        2.10, 2.12, 5.1, 5.2, 14.12, 17.2**
        """

        def prop(indice: int) -> None:
            entrada = dp.CATALOGO[indice]

            # Criterios 2.1 y 2.2: identificador y posicion.
            self.assertEqual(entrada.id, dp.ORDEN_CATALOGO[indice])
            self.assertEqual(dp.IDS[indice], entrada.id)
            if indice == 0:
                self.assertEqual(entrada.id, dp.ANCLA_ANATOMIA)

            # Criterio 2.3: Archivo_Diagrama.
            extension = os.path.splitext(entrada.archivo)[1]
            self.assertIn(extension, dp.EXTENSIONES)
            self.assertEqual(entrada.archivo, f"{entrada.id}{extension}")
            self.assertEqual(
                dp.ruta_relativa(entrada),
                f"{dp.DIR_ASSETS}/{entrada.id}{extension}",
            )

            # Criterio 2.4: dimensiones de los dos modos.
            esperadas = _DIMENSIONES[entrada.id]
            self.assertEqual(dp.dimensiones(entrada, dp.MODO_ARCHIVO), esperadas[0])
            self.assertEqual(dp.dimensiones(entrada, dp.MODO_SVG), esperadas[1])
            for modo in (dp.MODO_ARCHIVO, dp.MODO_SVG):
                ancho, alto = dp.dimensiones(entrada, modo)
                self.assertGreater(ancho, 0)
                self.assertLessEqual(ancho, dp.ANCHO_MAXIMO)
                self.assertGreater(alto, 0)

            # Criterios 2.5 y 2.6: texto alternativo real.
            self.assertGreaterEqual(len(entrada.alt), dp.MINIMO_ALT)
            alt = dp.normalizar_lexico(entrada.alt)
            if entrada.id == dp.ANCLA_ANATOMIA:
                nombradas = [
                    e
                    for e in dp.ETIQUETAS_ANATOMIA
                    if dp.normalizar_lexico(e) in alt
                ]
                self.assertGreaterEqual(
                    len(nombradas), dp.MINIMO_ETIQUETAS_EN_ALT, nombradas
                )
            else:
                superficies = [
                    s
                    for s in dp.SUPERFICIES_CONTACTO
                    if dp.normalizar_lexico(s) in alt
                ]
                self.assertTrue(superficies, f"{entrada.id}: alt sin superficie")
                elementos = [
                    e
                    for e in dp.ELEMENTOS_POSTURA
                    if dp.normalizar_lexico(e) in alt
                ]
                self.assertGreaterEqual(len(elementos), 2, elementos)

            # Criterios 2.7 y 17.2: cinco pasos en el orden fijo.
            self.assertEqual(len(entrada.pasos), dp.PASOS_POR_ENTRADA)
            for posicion, paso in enumerate(entrada.pasos):
                self.assertGreaterEqual(
                    len(paso),
                    dp.MINIMO_PASO,
                    f"{entrada.id}: paso {posicion + 1} corto: {paso!r}",
                )
                self.assertTrue(
                    dp.empieza_con_verbo_permitido(paso),
                    f"{entrada.id}: paso {posicion + 1} empieza por "
                    f"{dp.verbo_inicial(paso)!r}",
                )
                marca = _MARCA_POR_PASO[posicion]
                if marca:
                    self.assertIn(
                        marca,
                        dp.normalizar_lexico(paso),
                        f"{entrada.id}: el paso {posicion + 1} debe hablar de "
                        f"{dp.ORDEN_PASOS[posicion]!r}",
                    )
            # Paso 2: superficie de contacto. Paso 5: mirada.
            paso_contacto = dp.normalizar_lexico(entrada.pasos[1])
            self.assertTrue(
                any(
                    dp.normalizar_lexico(s) in paso_contacto
                    for s in dp.SUPERFICIES_CONTACTO
                ),
                f"{entrada.id}: el paso 2 no nombra la superficie de contacto",
            )
            self.assertEqual(dp.verbo_inicial(entrada.pasos[4]), "mira")

            # Criterio 2.8: Fundamento del conjunto cerrado.
            if entrada.fundamento is None:
                self.assertEqual(entrada.id, dp.ANCLA_ANATOMIA)
            else:
                self.assertIn(entrada.fundamento, dp.FUNDAMENTOS)
            self.assertEqual(
                entrada.fundamento, dp.FUNDAMENTO_ESPERADO[entrada.id]
            )

            # Criterios 2.9 y 2.10: postura equivalente.
            if entrada.postura_id is None:
                self.assertIn(entrada.id, dp.SIN_POSTURA)
            else:
                self.assertNotIn(entrada.id, dp.SIN_POSTURA)
                self.assertIn(entrada.postura_id, figuras.FIGURAS)
            self.assertEqual(entrada.postura_id, dp.POSTURA_ESPERADA[entrada.id])

            # Criterios 5.1 y 5.2: Requiere_Archivo declarado y falso.
            self.assertIsInstance(entrada.requiere_archivo, bool)
            self.assertFalse(entrada.requiere_archivo)

            # Criterio 2.12: el pase elevado a distancia.
            if entrada.id == "pase-largo-empeine":
                for texto in (entrada.titulo, entrada.alt):
                    normalizado = dp.normalizar_lexico(texto)
                    self.assertIn("elevado", normalizado)
                    self.assertIn("distancia", normalizado)

            # Criterio 14.12: las tres Fase_Numerada de potencia-carrera.
            numeros = tuple(f.numero for f in entrada.fases)
            self.assertEqual(numeros, tuple(range(1, len(entrada.fases) + 1)))
            if entrada.id == "potencia-carrera":
                self.assertEqual(numeros, (1, 2, 3))
            else:
                self.assertEqual(entrada.fases, ())

        for_all(gen_indice, prop, iteraciones=100, etiqueta=ETQ_P1)

    def test_el_catalogo_tiene_ocho_entradas_en_orden(self) -> None:
        # Criterio 2.1: ni una mas, ni una menos, y sin identificadores repetidos.
        self.assertEqual(len(dp.CATALOGO), 8)
        self.assertEqual(dp.IDS, dp.ORDEN_CATALOGO)
        self.assertEqual(len(set(dp.IDS)), 8)

    def test_el_validador_acepta_el_catalogo_declarado(self) -> None:
        dp.validar_catalogo()

    def test_el_validador_nombra_la_entrada_rota(self) -> None:
        # Cordura del Validador_Catalogo: un paso corto se localiza por entrada.
        import dataclasses

        roto = dataclasses.replace(dp.CATALOGO[1], pasos=("Gira.",) * 5)
        with self.assertRaises(ErrorAsset) as capturado:
            dp._validar_pasos(roto)
        self.assertIn("tiro-empeine", str(capturado.exception))
        self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)


# --------------------------------------------------------------------------- #
# Property 2: vocabulario anatomico cerrado
# --------------------------------------------------------------------------- #

#: Los dieciseis terminos de la tabla del diseno (criterio 14.13), agrupados por
#: zona como los declara el documento.
_VOCABULARIO_ESPERADO: tuple[str, ...] = (
    # Cabeza y tronco
    "frente",
    "cuello",
    "hombro",
    "codo",
    "mano",
    "torso",
    # Ejes
    "línea media",
    "centro de gravedad",
    # Cadera y pierna
    "cadera",
    "rodilla",
    "espinilla",
    # Pie
    "pie",
    "empeine",
    "planta",
    "parte interna",
    "parte externa",
)


def gen_etiqueta_declarada(rnd: random.Random) -> tuple[int, int]:
    """Par `(indice de entrada, indice de etiqueta)` del Catalogo_Diagramas."""
    indice: int = rnd.randrange(len(dp.CATALOGO))
    etiquetas = dp.CATALOGO[indice].etiquetas
    return (indice, rnd.randrange(len(etiquetas)))


ETQ_P2 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 2: Vocabulario anatómico cerrado"
)


class TestProperty2Vocabulario(unittest.TestCase):
    """Property 2: vocabulario anatomico cerrado."""

    def test_property_2_vocabulario_cerrado(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 2: Vocabulario anatómico cerrado.

        Para todo Diagrama_Postura y para toda Etiqueta_Anatomica que declara, la
        etiqueta pertenece al vocabulario de dieciseis terminos que declara
        `anatomia-base`, y ese vocabulario contiene exactamente esos dieciseis
        terminos.

        **Validates: Requirements 14.13, 14.16**
        """
        vocabulario = frozenset(dp.ETIQUETAS_ANATOMIA)

        def prop(caso: tuple[int, int]) -> None:
            indice_entrada, indice_etiqueta = caso
            entrada = dp.CATALOGO[indice_entrada]
            etiqueta = entrada.etiquetas[indice_etiqueta % len(entrada.etiquetas)]

            # Criterio 14.16: la etiqueta pertenece al vocabulario cerrado.
            self.assertIn(
                etiqueta,
                vocabulario,
                f"{entrada.id}: etiqueta {etiqueta!r} fuera del vocabulario",
            )
            # Y el vocabulario es el que declara `anatomia-base` (criterio 14.13).
            self.assertIn(etiqueta, dp.CATALOGO[0].etiquetas)

            # El mapa etiqueta -> articulacion la ancla a una articulacion real.
            articulacion = dp.articulacion_de(etiqueta)
            self.assertIn(articulacion, dp.ARTICULACIONES)

            # Sin etiquetas repetidas dentro de una misma entrada.
            self.assertEqual(len(set(entrada.etiquetas)), len(entrada.etiquetas))

        for_all(gen_etiqueta_declarada, prop, iteraciones=100, etiqueta=ETQ_P2)

    def test_el_vocabulario_tiene_los_dieciseis_terminos(self) -> None:
        # Criterio 14.13: el conjunto es exactamente el de la tabla del diseno.
        self.assertEqual(dp.ETIQUETAS_ANATOMIA, _VOCABULARIO_ESPERADO)
        self.assertEqual(len(dp.ETIQUETAS_ANATOMIA), 16)
        self.assertEqual(dp.CATALOGO[0].etiquetas, _VOCABULARIO_ESPERADO)

    def test_el_mapa_cubre_el_vocabulario_y_marca_los_derivados(self) -> None:
        self.assertEqual(set(dp.ARTICULACION_POR_ETIQUETA), set(_VOCABULARIO_ESPERADO))
        self.assertEqual(len(dp.ARTICULACIONES), 17)
        self.assertEqual(
            dp.ETIQUETAS_DERIVADAS,
            frozenset(
                {
                    "espinilla",
                    "empeine",
                    "planta",
                    "parte interna",
                    "parte externa",
                    "línea media",
                    "centro de gravedad",
                }
            ),
        )
        for derivada in dp.ETIQUETAS_DERIVADAS:
            with self.subTest(etiqueta=derivada):
                self.assertIn(derivada, dp.ETIQUETAS_ANATOMIA)

    def test_una_etiqueta_ajena_se_rechaza_nombrandola(self) -> None:
        # El vocabulario es cerrado: una etiqueta inventada no pasa.
        with self.assertRaises(ErrorAsset) as capturado:
            dp.articulacion_de("clavícula")
        self.assertIn("clavícula", str(capturado.exception))
        self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)

    def test_el_validador_del_vocabulario_acepta_lo_declarado(self) -> None:
        dp.validar_vocabulario()


# --------------------------------------------------------------------------- #
# Property 3: Guardarrail_Lexico
# --------------------------------------------------------------------------- #

import json  # noqa: E402

import gen  # noqa: E402
import test_guardarrail_clubes as clubes  # noqa: E402
from guia.contenido import cap10_fundamentos  # noqa: E402


def _cadenas(dato: object) -> tuple[str, ...]:
    """Todas las cadenas de una estructura JSON, en orden de recorrido."""
    encontradas: list[str] = []
    pendientes: list[object] = [dato]
    while pendientes:
        actual = pendientes.pop()
        if isinstance(actual, str):
            encontradas.append(actual)
        elif isinstance(actual, dict):
            pendientes.extend(actual.values())
        elif isinstance(actual, list):
            pendientes.extend(actual)
    return tuple(encontradas)


def _textos_de_fichas() -> tuple[str, ...]:
    """Textos visibles del Catalogo_JSON (`contenido/ejercicios.json`)."""
    with open(cap10_fundamentos.ruta_catalogo(), encoding="utf-8") as manejador:
        datos = json.load(manejador)
    return _cadenas(datos)


#: Textos del catalogo de fichas y del Catalogo_Diagramas, con su identificador.
_TEXTOS_FICHAS: tuple[str, ...] = _textos_de_fichas()
_TEXTOS_CATALOGO: tuple[tuple[str, str], ...] = tuple(
    (d.id, texto) for d in dp.CATALOGO for texto in dp.textos_de(d)
)


def gen_caso_lexico(rnd: random.Random) -> tuple[int, int, gen.MutacionLexica]:
    """Un texto declarado del catalogo, uno de las fichas y un texto contaminado.

    Los tres viajan juntos en cada iteracion: los dos primeros ejercitan el lado
    "todo texto declarado pasa el guardarrail" y el tercero el lado "toda
    expresion prohibida se detecta donde sea que se inserte".
    """
    return (
        rnd.randrange(len(_TEXTOS_CATALOGO)),
        rnd.randrange(len(_TEXTOS_FICHAS)),
        gen.gen_texto_lexico(rnd),
    )


ETQ_P3 = (
    "Feature: imagenes-reales-hero-interactivo, Property 3: Guardarrail_Lexico"
)


class TestProperty3GuardarrailLexico(unittest.TestCase):
    """Property 3: Guardarrail_Lexico."""

    def test_property_3_guardarrail_lexico(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 3: Guardarrail_Lexico.

        Para todo texto del Catalogo_Diagramas y de las fichas, el detector
        lexico no halla ninguna expresion de masculino generico, forma masculina,
        expresion condescendiente ni nombre de club, y todo paso empieza por un
        verbo de la lista de verbos permitidos en segunda persona del singular; y
        para todo texto limpio y toda expresion de esas listas, insertar la
        expresion en cualquier posicion del texto hace que el detector la halle y
        que el mensaje de fallo contenga el identificador de la entrada y la
        expresion rechazada.

        **Validates: Requirements 2.11, 17.1, 17.3, 17.4, 17.5, 17.6, 17.7**
        """

        def prop(caso: tuple[int, int, gen.MutacionLexica]) -> None:
            indice_catalogo, indice_ficha, mutacion = caso

            # Lado limpio: el texto declarado del Catalogo_Diagramas.
            id_, texto = _TEXTOS_CATALOGO[indice_catalogo % len(_TEXTOS_CATALOGO)]
            self.assertEqual(
                dp.violaciones_lexicas(id_, texto),
                (),
                f"{id_}: texto declarado con expresion prohibida: {texto!r}",
            )

            # Lado limpio: el texto declarado de las fichas (criterios 17.1, 2.11).
            ficha = _TEXTOS_FICHAS[indice_ficha % len(_TEXTOS_FICHAS)]
            self.assertEqual(
                dp.violaciones_lexicas("ficha", ficha),
                (),
                f"ficha: texto con expresion prohibida: {ficha!r}",
            )

            # Lado contaminado: la expresion insertada se detecta y se nombra.
            halladas = dp.violaciones_lexicas(mutacion.expresion, mutacion.texto)
            self.assertIn(
                mutacion.expresion,
                halladas,
                f"no se detecto {mutacion.expresion!r} en la posicion "
                f"{mutacion.posicion}",
            )
            with self.assertRaises(ErrorAsset) as capturado:
                dp.validar_lexico("tiro-empeine", mutacion.texto)
            mensaje = str(capturado.exception)
            self.assertIn("tiro-empeine", mensaje)
            self.assertIn(mutacion.expresion, mensaje)
            self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)

        for_all(gen_caso_lexico, prop, iteraciones=100, etiqueta=ETQ_P3)

    def test_las_cuatro_listas_son_las_del_diseno(self) -> None:
        # Criterios 17.2, 17.4, 17.5 y 17.6: contenido exacto de las listas.
        self.assertEqual(
            dp.VERBOS_PERMITIDOS,
            (
                "coloca",
                "apoya",
                "gira",
                "lleva",
                "mira",
                "golpea",
                "contacta",
                "acompaña",
                "flexiona",
                "alinea",
                "mantén",
                "empuja",
                "recibe",
                "amortigua",
                "controla",
                "conduce",
                "protege",
                "salta",
                "impulsa",
                "respira",
            ),
        )
        self.assertEqual(
            dp.MASCULINO_GENERICO,
            (
                "el jugador",
                "los jugadores",
                "el alumno",
                "los alumnos",
                "el niño",
                "los niños",
                "el chico",
                "los chicos",
            ),
        )
        self.assertEqual(
            dp.FORMAS_MASCULINAS,
            ("listo", "atento", "concentrado", "cansado", "preparado"),
        )
        self.assertEqual(
            dp.CONDESCENDIENTES,
            ("es facilísimo", "es muy fácil", "no te compliques", "solo tienes que"),
        )

    def test_reutiliza_la_lista_de_clubes_del_guardarrail_vigente(self) -> None:
        # Criterio 2.11: la misma lista, sin copias que se desincronicen.
        self.assertEqual(dp.CLUBES_VETADOS, clubes.CLUBES_VETADOS)

    def test_los_limites_de_palabra_evitan_los_falsos_positivos(self) -> None:
        # "listones" y "cansancio" no son formas masculinas, y "parte interna" no
        # es el club "Inter".
        for limpio in (
            "Coloca los listones del cajon a la altura de tu rodilla.",
            "El cansancio aparece al final de la serie, respira y sigue.",
            "Contacta el balón con la parte interna del pie.",
            "Trabajas el interior del pie en cada repetición.",
        ):
            with self.subTest(texto=limpio):
                self.assertEqual(dp.violaciones_lexicas("prueba", limpio), ())

    def test_detecta_una_expresion_de_cada_lista(self) -> None:
        casos = (
            ("Cuando el jugador recibe, gira el cuerpo.", "el jugador"),
            ("Quedas listo para el siguiente toque.", "listo"),
            ("Es muy fácil, no te preocupes.", "es muy fácil"),
            ("Entrena como el Olympique.", "Olympique"),
        )
        for texto, esperada in casos:
            with self.subTest(texto=texto):
                self.assertIn(esperada, dp.violaciones_lexicas("x", texto))

    def test_todos_los_pasos_del_catalogo_empiezan_por_verbo_permitido(self) -> None:
        # Criterio 17.3, sobre las cuarenta lineas de paso del catalogo.
        for entrada in dp.CATALOGO:
            for posicion, paso in enumerate(entrada.pasos):
                with self.subTest(id=entrada.id, paso=posicion + 1):
                    self.assertTrue(
                        dp.empieza_con_verbo_permitido(paso),
                        f"{entrada.id}: paso {posicion + 1} empieza por "
                        f"{dp.verbo_inicial(paso)!r}",
                    )


# --------------------------------------------------------------------------- #
# Property 4: Advertencia_Cabeceo obligatoria y completa
# --------------------------------------------------------------------------- #

import dataclasses  # noqa: E402

#: Entrada que declara la Advertencia_Cabeceo (criterio 20.1).
_CABECEO = dp.por_id("cabeceo-frente")

#: Marca del generador -> nombre del concepto y sinonimos que hay que borrar para
#: que el concepto quede realmente ausente del texto.
_CONCEPTO_POR_MARCA: dict[str, tuple[str, tuple[str, ...]]] = {}
for _marca in gen.CONCEPTOS_CABECEO_EXIGIDOS:
    for _nombre, _sinonimos in dp.CONCEPTOS_CABECEO:
        if dp.normalizar_lexico(_marca) in tuple(
            dp.normalizar_lexico(s) for s in _sinonimos
        ):
            _CONCEPTO_POR_MARCA[_marca] = (_nombre, _sinonimos)
            break

if set(_CONCEPTO_POR_MARCA) != set(gen.CONCEPTOS_CABECEO_EXIGIDOS):
    raise RuntimeError(
        "las marcas del generador no cubren los conceptos de la Advertencia_Cabeceo"
    )


def _sin_conceptos(texto: str, marcas: tuple[str, ...]) -> str:
    """Quita del texto todos los sinonimos de los conceptos de `marcas`."""
    resultado: str = texto
    for marca in marcas:
        _, sinonimos = _CONCEPTO_POR_MARCA[marca]
        for sinonimo in sinonimos:
            resultado = resultado.replace(sinonimo, "")
    return resultado


ETQ_P4 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 4: Advertencia_Cabeceo obligatoria y completa"
)


class TestProperty4AdvertenciaCabeceo(unittest.TestCase):
    """Property 4: Advertencia_Cabeceo obligatoria y completa."""

    def test_property_4_advertencia_completa(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 4: Advertencia_Cabeceo obligatoria y completa.

        Para toda variante del texto de la Advertencia_Cabeceo obtenida quitando
        uno o mas de los conceptos exigidos, el Validador_Catalogo lanza
        `ErrorAsset` con el codigo `E_ASSET_INVALIDO` y su mensaje nombra un
        concepto ausente; y el texto declarado en el catalogo pasa la validacion
        conteniendo la frente como unica superficie de contacto, la coronilla y
        la cara como superficies a evitar, el cuello contraido y firme, los ojos
        abiertos, el balon blando y la progresion sin salto.

        **Validates: Requirements 14.14, 20.1, 20.2, 20.3, 20.5**
        """

        def prop(marcas: tuple[str, ...]) -> None:
            texto = _sin_conceptos(dp.ADVERTENCIA_CABECEO, marcas)
            variante = dataclasses.replace(_CABECEO, advertencia=texto)

            if not marcas:
                # Subconjunto vacio: el texto declarado pasa la validacion.
                self.assertGreaterEqual(len(texto), dp.MINIMO_ADVERTENCIA)
                self.assertEqual(dp.conceptos_ausentes(texto), ())
                dp.validar_advertencia(variante)
                return

            esperados = tuple(_CONCEPTO_POR_MARCA[m][0] for m in marcas)
            ausentes = dp.conceptos_ausentes(texto)
            for nombre in esperados:
                self.assertIn(nombre, ausentes, f"{nombre} deberia faltar")

            with self.assertRaises(ErrorAsset) as capturado:
                dp.validar_advertencia(variante)
            mensaje = str(capturado.exception)
            self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)
            self.assertIn("cabeceo-frente", mensaje)
            self.assertTrue(
                any(nombre in mensaje for nombre in esperados),
                f"el mensaje no nombra ningun concepto ausente: {mensaje}",
            )

        for_all(
            gen.gen_conceptos_eliminados, prop, iteraciones=100, etiqueta=ETQ_P4
        )

    def test_el_texto_declarado_cubre_los_siete_conceptos(self) -> None:
        # Criterios 20.2 y 20.3.
        self.assertIsNotNone(_CABECEO.advertencia)
        self.assertGreaterEqual(len(dp.ADVERTENCIA_CABECEO), 120)
        self.assertEqual(len(dp.CONCEPTOS_CABECEO), 7)
        self.assertEqual(dp.conceptos_ausentes(dp.ADVERTENCIA_CABECEO), ())
        normalizado = dp.normalizar_lexico(dp.ADVERTENCIA_CABECEO)
        for fragmento in (
            "frente",
            "coronilla",
            "cara",
            "cuello contraido",
            "ojos abiertos",
            "balon blando",
            "sin salto",
        ):
            with self.subTest(concepto=fragmento):
                self.assertIn(fragmento, normalizado)

    def test_solo_cabeceo_frente_declara_advertencia(self) -> None:
        # Criterio 20.1: la advertencia es obligatoria ahi y solo ahi.
        for entrada in dp.CATALOGO:
            with self.subTest(id=entrada.id):
                if entrada.id == "cabeceo-frente":
                    self.assertIsNotNone(entrada.advertencia)
                else:
                    self.assertIsNone(entrada.advertencia)
                dp.validar_advertencia(entrada)

    def test_un_texto_recortado_por_debajo_del_minimo_se_rechaza(self) -> None:
        # Criterio 20.3: menos de 120 caracteres es invalido, y el mensaje nombra
        # los conceptos que quedaron fuera del recorte.
        corto = dataclasses.replace(
            _CABECEO, advertencia=dp.ADVERTENCIA_CABECEO[:80]
        )
        with self.assertRaises(ErrorAsset) as capturado:
            dp.validar_advertencia(corto)
        self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)
        self.assertIn("cabeceo-frente", str(capturado.exception))

    def test_una_advertencia_ausente_se_rechaza(self) -> None:
        vacia = dataclasses.replace(_CABECEO, advertencia=None)
        with self.assertRaises(ErrorAsset) as capturado:
            dp.validar_advertencia(vacia)
        self.assertEqual(capturado.exception.codigo, E_ASSET_INVALIDO)


# --------------------------------------------------------------------------- #
# Property 12: render hibrido y dimensiones efectivas
# --------------------------------------------------------------------------- #

import re  # noqa: E402

from guia import build_html, build_site  # noqa: E402

_esc = build_html._esc


def _figura_de(marcado: str) -> str:
    """El `<figure>` de un bloque, que es donde vive el contenido grafico."""
    inicio: int = marcado.index("<figure")
    fin: int = marcado.index("</figure>")
    return marcado[inicio:fin]


def gen_render_hibrido(rnd: random.Random) -> tuple[tuple[str, ...], int]:
    """Un subconjunto de Archivo_Diagrama presentes y una entrada del catalogo.

    El subconjunto viene de `gen.gen_presentes`, que incluye el vacio (los ocho
    con el Generador_SVG) y el total (los ocho con `<img>`), asi que los dos
    caminos de `modo_render` se ejercitan de verdad en 100 iteraciones.
    """
    return (gen.gen_presentes(rnd), rnd.randrange(len(dp.CATALOGO)))


ETQ_P12 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 12: Render híbrido y dimensiones efectivas"
)


class TestProperty12RenderHibrido(unittest.TestCase):
    """Property 12: render hibrido y dimensiones efectivas."""

    def test_property_12_render_hibrido(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 12: Render híbrido y dimensiones efectivas.

        Para todo subconjunto de Archivo_Diagrama presentes en el repositorio y
        para toda entrada del catalogo, el bloque emitido contiene exactamente un
        contenido grafico: un elemento `<img>` con `src` igual a la ruta relativa
        declarada y con `decoding="async"` cuando su archivo esta presente, o el
        `<svg>` en linea del Generador_SVG cuando falta; ese contenido lleva el
        texto alternativo declarado y los atributos `width` y `height` con los
        valores que el catalogo declara para el modo de render efectivo, incluso
        cuando los dos modos declaran dimensiones distintas.

        **Validates: Requirements 3.4, 4.3, 4.4, 4.8, 5.3, 5.4, 5.5**
        """

        def prop(caso: tuple[tuple[str, ...], int]) -> None:
            rutas, indice = caso
            presentes = frozenset(rutas)
            entrada = dp.CATALOGO[indice % len(dp.CATALOGO)]
            modo = dp.modo_render(entrada, presentes)
            ancho, alto = dp.dimensiones(entrada, modo)

            # Los dos modos declaran dimensiones distintas en las ocho entradas:
            # el criterio 4.8 solo tiene sentido si eso se cumple de verdad.
            self.assertNotEqual(
                dp.dimensiones(entrada, dp.MODO_ARCHIVO),
                dp.dimensiones(entrada, dp.MODO_SVG),
            )

            partes: list[str] = []
            dp.render_bloque(
                entrada, partes, presentes=presentes, primero=True
            )
            figura = _figura_de("".join(partes))

            # Criterio 5.5: exactamente un contenido grafico, siempre.
            self.assertEqual(
                figura.count("<img") + figura.count("<svg"),
                1,
                f"{entrada.id}/{modo}: contenido grafico ausente o duplicado",
            )

            if modo == dp.MODO_ARCHIVO:
                # Criterios 5.3, 3.4 y 4.4.
                self.assertEqual(figura.count("<img"), 1)
                self.assertIn(f'src="{_esc(dp.ruta_relativa(entrada))}"', figura)
                self.assertIn('decoding="async"', figura)
                self.assertIn(f'alt="{_esc(entrada.alt)}"', figura)
            else:
                # Criterios 5.4 y 3.4: el SVG en linea lleva el mismo texto
                # alternativo, como `aria-label` de su `role="img"`.
                self.assertEqual(figura.count("<svg"), 1)
                self.assertIn('role="img"', figura)
                self.assertIn(f'aria-label="{_esc(entrada.alt)}"', figura)

            # Criterios 4.3 y 4.8: dimensiones del modo de render efectivo.
            self.assertIn(f'width="{ancho}"', figura)
            self.assertIn(f'height="{alto}"', figura)

        for_all(gen_render_hibrido, prop, iteraciones=100, etiqueta=ETQ_P12)

    def test_el_modo_efectivo_decide_las_dimensiones(self) -> None:
        # Cordura de los dos extremos: ningun archivo y los ocho archivos.
        vacio: frozenset[str] = frozenset()
        todos = frozenset(dp.ruta_relativa(d) for d in dp.CATALOGO)
        for entrada in dp.CATALOGO:
            with self.subTest(id=entrada.id):
                self.assertEqual(dp.modo_render(entrada, vacio), dp.MODO_SVG)
                self.assertEqual(
                    dp.modo_render(entrada, todos), dp.MODO_ARCHIVO
                )

    def test_el_orden_del_bloque_es_el_declarado(self) -> None:
        # Criterios 3.5, 3.6 y 20.4 sobre la entrada con advertencia y fases.
        vacio: frozenset[str] = frozenset()
        for identificador in ("cabeceo-frente", "potencia-carrera"):
            entrada = dp.por_id(identificador)
            partes: list[str] = []
            dp.render_bloque(
                entrada, partes, presentes=vacio, primero=False
            )
            marcado = "".join(partes)
            with self.subTest(id=identificador):
                self.assertLess(
                    marcado.index(f"<h3>{_esc(entrada.titulo)}</h3>"),
                    marcado.index("<figure"),
                )
                self.assertLess(
                    marcado.index("</figure>"),
                    marcado.index(f'<ol class="{dp.CLASE_PASOS}">'),
                )
                self.assertLess(
                    marcado.index(f'<ol class="{dp.CLASE_PASOS}">'),
                    marcado.index(f'<p class="{dp.CLASE_ERROR}">'),
                )
                self.assertEqual(
                    marcado.count("<li>"), dp.PASOS_POR_ENTRADA + 0
                )
                if entrada.advertencia is not None:
                    self.assertLess(
                        marcado.index("</figure>"),
                        marcado.index(f'<p class="{dp.CLASE_AVISO}">'),
                    )
                    self.assertLess(
                        marcado.index(f'<p class="{dp.CLASE_AVISO}">'),
                        marcado.index(f'<ol class="{dp.CLASE_PASOS}">'),
                    )
                if entrada.fases:
                    self.assertIn(f'<ol class="{dp.CLASE_FASES}">', marcado)
                    for fase in entrada.fases:
                        self.assertIn(f'<li value="{fase.numero}">', marcado)


# --------------------------------------------------------------------------- #
# Property 13: carga diferida de las imagenes
# --------------------------------------------------------------------------- #

#: Un elemento `<img ...>` completo, para leer sus atributos uno por uno.
_RE_IMG = re.compile(r"<img\b[^>]*>")

ETQ_P13 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 13: Carga diferida de las imágenes"
)


class TestProperty13CargaDiferida(unittest.TestCase):
    """Property 13: carga diferida de las imagenes."""

    def test_property_13_carga_diferida(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 13: Carga diferida de las imágenes.

        Para todo subconjunto de Archivo_Diagrama presentes, el documento
        contiene a lo sumo un elemento `<img>` con `loading="eager"`, ese elemento
        es el primer `<img>` del documento, y todos los demas elementos `<img>`
        llevan `loading="lazy"`.

        **Validates: Requirements 4.1, 4.2**
        """

        def prop(rutas: tuple[str, ...]) -> None:
            presentes = frozenset(rutas)
            documento = build_site.html_sitio(fichas=[], presentes=presentes)
            etiquetas = _RE_IMG.findall(documento)

            # Un `<img>` por Archivo_Diagrama presente, ni uno mas.
            declaradas = frozenset(dp.ruta_relativa(d) for d in dp.CATALOGO)
            self.assertEqual(len(etiquetas), len(presentes & declaradas))

            inmediatas = [
                e for e in etiquetas if f'loading="{dp.CARGA_INMEDIATA}"' in e
            ]
            self.assertLessEqual(len(inmediatas), 1, inmediatas)

            for posicion, etiqueta in enumerate(etiquetas):
                if posicion == 0:
                    self.assertIn(
                        f'loading="{dp.CARGA_INMEDIATA}"',
                        etiqueta,
                        "el primer <img> del documento no es el inmediato",
                    )
                else:
                    self.assertIn(
                        f'loading="{dp.CARGA_DIFERIDA}"',
                        etiqueta,
                        f"el <img> numero {posicion + 1} no es diferido",
                    )

        for_all(gen.gen_presentes, prop, iteraciones=100, etiqueta=ETQ_P13)

    def test_sin_archivos_no_hay_ninguna_imagen(self) -> None:
        # Con el subconjunto vacio los ocho se rinden con el Generador_SVG, asi
        # que el documento no lleva ni un `<img>`: por eso el guardarrail vigente
        # `test_build_site::assertNotIn("<img", ...)` sigue en verde.
        documento = build_site.html_sitio(fichas=[], presentes=frozenset())
        self.assertEqual(_RE_IMG.findall(documento), [])
        self.assertEqual(dp.presentes(), frozenset())

    def test_con_los_ocho_archivos_solo_el_primero_es_inmediato(self) -> None:
        todos = frozenset(dp.ruta_relativa(d) for d in dp.CATALOGO)
        documento = build_site.html_sitio(fichas=[], presentes=todos)
        etiquetas = _RE_IMG.findall(documento)
        self.assertEqual(len(etiquetas), 8)
        self.assertEqual(
            sum(f'loading="{dp.CARGA_INMEDIATA}"' in e for e in etiquetas), 1
        )
        self.assertIn(f'loading="{dp.CARGA_INMEDIATA}"', etiquetas[0])
        # El primer `<img>` del documento es el de `anatomia-base`, que va en su
        # propia seccion antes de la de tecnica (criterio 3.2).
        self.assertIn(
            _esc(dp.ruta_relativa(dp.por_id(dp.ANCLA_ANATOMIA))), etiquetas[0]
        )


# --------------------------------------------------------------------------- #
# Ejemplos declarados del contenido del catalogo (tarea 14.4)
# --------------------------------------------------------------------------- #


class TestEjemplosDelCatalogo(unittest.TestCase):
    """Dos ejemplos concretos que la Property 1 cubre en general.

    La propiedad recorre las ocho entradas y afirma la *forma* de cada campo. Un
    ejemplo fija ademas el *contenido* que el requisito nombra por su nombre, de
    modo que renumerar las fases de `potencia-carrera` o suavizar el titulo de
    `pase-largo-empeine` rompa una prueba que dice exactamente que se perdio.

    _Requirements: 2.12, 14.12_
    """

    def test_potencia_carrera_declara_tres_fases_en_orden(self) -> None:
        # Criterio 14.12: tres Fase_Numerada, en su orden fijo y sin huecos.
        diagrama = dp.por_id("potencia-carrera")
        numeros = tuple(fase.numero for fase in diagrama.fases)
        self.assertEqual(numeros, (1, 2, 3))
        # Cada fase trae su propio texto: ninguna vacia y ninguna repetida.
        textos = tuple(fase.texto for fase in diagrama.fases)
        for numero, texto in zip(numeros, textos):
            with self.subTest(fase=numero):
                self.assertTrue(texto.strip(), msg=f"fase {numero} sin texto")
        self.assertEqual(len(frozenset(textos)), len(textos))

    def test_solo_potencia_carrera_declara_fases(self) -> None:
        # El resto del catalogo no lleva Fase_Numerada, asi que las tres de
        # `potencia-carrera` son las unicas del documento (criterio 14.12).
        con_fases = tuple(d.id for d in dp.CATALOGO if d.fases)
        self.assertEqual(con_fases, ("potencia-carrera",))

    def test_pase_largo_declara_pase_elevado_a_distancia(self) -> None:
        # Criterio 2.12: la entrada se anuncia como pase elevado a distancia en
        # su titulo **y** en su texto alternativo, no solo en uno de los dos.
        diagrama = dp.por_id("pase-largo-empeine")
        for campo, texto in (
            ("titulo", diagrama.titulo),
            ("alt", diagrama.alt),
        ):
            with self.subTest(campo=campo):
                self.assertIn("pase elevado a distancia", texto)
        self.assertIn("empeine", diagrama.titulo)


if __name__ == "__main__":
    unittest.main()
