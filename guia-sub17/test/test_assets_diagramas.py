"""Pruebas de los assets de los Diagrama_Postura en el Orquestador_Build.

Feature `imagenes-reales-hero-interactivo`, bloque 13:

* **Property 14** (tarea 13.6): validador de recursos y excepcion de los creditos.
* **Property 15** (tarea 13.4): firma por extension de los assets copiados.
* **Property 16** (tarea 13.5): copia de assets, degradacion y reporte.
* **Property 53** (tarea 13.7): Validador_Rutas.

La Propiedad 53 no toca el disco: `ruta_aceptable` es una funcion pura sobre la
cadena de la ruta, asi que la propiedad solo genera rutas y lee veredictos.

Ninguna prueba de este modulo escribe en el repositorio: la fuente de los
Archivo_Diagrama se redirige a un `tempfile.TemporaryDirectory` sustituyendo
`diagramas_postura._raiz_proyecto`, igual que hace
`test_build.py::TestCopiaAssetsAtomica`, y el `Catalogo_Diagramas` se restaura en
`tearDown`. La Property 14 no toca el disco en absoluto: compone el documento en
memoria con `build_site.html_sitio(presentes=...)`.

_Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.8, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11,
5.12, 5.13, 5.14, 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7_
"""

from __future__ import annotations

import dataclasses
import os
import platform
import random
import sys
import tempfile
import unittest

# Bootstrap de rutas: cada modulo de prueba pone `src/` y `test/` en sys.path por
# su cuenta (convencion del proyecto).
_DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR_SRC = os.path.join(_DIR_RAIZ, "src")
_DIR_TEST = os.path.join(_DIR_RAIZ, "test")
for _ruta in (_DIR_SRC, _DIR_TEST):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import gen  # noqa: E402
from guia import build, build_html, build_site, secciones_guia  # noqa: E402
from guia import diagramas_postura as dp  # noqa: E402
from guia.errores import (  # noqa: E402
    E_ASSET_FALTANTE,
    E_ASSET_INVALIDO,
    ErrorAsset,
)

# El lector del marcado vive en `test/lector_recursos.py` desde la tarea 14.2:
# `test_build_site.py` amplia el Guardarrail_Recursos con el mismo ayudante, y
# duplicarlo habria dejado dos definiciones que podrian discrepar.
from lector_recursos import (  # noqa: E402
    ATRIBUTOS_RECURSO,
    CONTEXTOS_HTTP_PERMITIDOS,
    LectorRecursos,
)
from prop import ITERACIONES_POR_DEFECTO, for_all  # noqa: E402

#: Nombres de archivo que **no** estan declarados en el Catalogo_Diagramas. Se
#: siembran en el directorio fuente con contenido que no cumple ninguna firma,
#: para comprobar que la comprobacion los ignora por completo (criterio 5.14).
NO_DECLARADOS: tuple[str, ...] = (
    "sobrante-uno.png",
    "sobrante-dos.webp",
    "sobrante-tres.svg",
    "sobrante-cuatro.avif",
    "sobrante-cinco.txt",
)

#: Contenido de los archivos no declarados: no cumple la firma de ninguna de las
#: cuatro extensiones, asi que si la copia los mirara, abortaria.
BASURA: bytes = b"no-soy-una-imagen-ni-lo-pretendo"


# --------------------------------------------------------------------------- #
# Property 14
# --------------------------------------------------------------------------- #

ETQ_P14 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 14: Validador de recursos y excepcion de los creditos"
)

#: Extension ajena a `EXTENSIONES_PERMITIDAS`, para el "solo si" del validador.
EXTENSION_AJENA: str = ".jpg"

#: URL de prueba del campo `enlace` de un Credito. El dominio `.invalid` esta
#: reservado por la RFC 2606 y no resuelve: aunque alguien la pegara en un
#: navegador no habria peticion posible. Viaja como **texto visible** del
#: Bloque_Creditos, que es la unica excepcion del criterio 1.8.
URL_CREDITO: str = "https://ejemplo.invalid/licencia-de-la-imagen"


@dataclasses.dataclass(frozen=True, slots=True)
class Lectura:
    """Un Target_Web ya emitido y ya leido: se compone **una sola vez**."""

    documento: str
    bajo: str
    lector: LectorRecursos


#: Memoria de los documentos emitidos, por modo de render. El Target_Web cuesta
#: del orden de un decimo de segundo por emision y las 100 iteraciones no lo
#: cambian: lo que varia en cada caso es el subconjunto de presentes con el que
#: se rinde el Bloque_Creditos y los campos de credito ausentes. Aqui viven las
#: dos emisiones extremas: los ocho Archivo_Diagrama presentes (ocho `<img>` con
#: su ruta relativa) y ninguno presente (los ocho diagramas por SVG en linea).
_MEMORIA_DOC: dict[bool, Lectura] = {}


def _lectura(con_imagenes: bool) -> Lectura:
    """Devuelve la `Lectura` memoizada del Target_Web en el modo pedido."""
    if con_imagenes not in _MEMORIA_DOC:
        presentes: frozenset[str] = (
            frozenset(dp.ruta_relativa(d) for d in dp.CATALOGO)
            if con_imagenes
            else frozenset()
        )
        documento: str = build_site.html_sitio(presentes=presentes)
        lector = LectorRecursos()
        lector.feed(documento)
        lector.close()
        _MEMORIA_DOC[con_imagenes] = Lectura(
            documento=documento, bajo=documento.lower(), lector=lector
        )
    return _MEMORIA_DOC[con_imagenes]


@dataclasses.dataclass(frozen=True, slots=True)
class CasoRecurso:
    """Caso de la Property 14: rutas, campos de credito ausentes y modo.

    `presentes` son rutas relativas de Archivo_Diagrama (incluidos el
    subconjunto vacio y el total) que alimentan al Validador_Rutas y el render del
    Bloque_Creditos; `ausentes` son los campos de credito que faltaran en la
    entrada, de modo que el `enlace` con `http` este a veces y a veces no; y
    `con_imagenes` elige cual de los dos documentos memoizados se revisa.
    """

    presentes: tuple[str, ...]
    ausentes: tuple[str, ...]
    con_imagenes: bool


def gen_caso_recurso(rnd: random.Random) -> CasoRecurso:
    """Rutas presentes, campos de credito ausentes y modo de render del sitio."""
    return CasoRecurso(
        presentes=gen.gen_presentes(rnd),
        ausentes=gen.gen_campos_credito_ausentes(rnd),
        con_imagenes=rnd.random() < 0.5,
    )


class TestProperty14ValidadorDeRecursos(unittest.TestCase):
    """Property 14: validador de recursos y excepcion de los creditos."""

    @classmethod
    def setUpClass(cls) -> None:
        # Las dos emisiones del Target_Web y la Hoja_Estilo, una sola vez.
        cls.css: str = build_html.estilo_css()
        _lectura(True)
        _lectura(False)

    def _creditos_del_caso(self, caso: CasoRecurso) -> str:
        """Bloque_Creditos con el `enlace` de prueba y los campos del caso.

        El catalogo se pasa por argumento, sin tocar `dp.CATALOGO`: la propiedad
        no deja estado global mutado ni depende del que dejen otras pruebas.
        """
        valores: dict[str, str | None] = {
            campo: (
                None
                if campo in caso.ausentes
                else (
                    URL_CREDITO
                    if campo == "enlace"
                    else dp.campo_de_credito(dp.CREDITO_PROPIO, campo)
                )
            )
            for campo in dp.CAMPOS_CREDITO
        }
        credito = dataclasses.replace(dp.CREDITO_PROPIO, **valores)
        catalogo = tuple(
            dataclasses.replace(d, credito=credito) for d in dp.CATALOGO
        )
        partes: list[str] = []
        secciones_guia.render_creditos_seccion(
            partes, presentes=frozenset(caso.presentes), catalogo=catalogo
        )
        return "".join(partes)

    def test_property_14_validador_de_recursos_y_excepcion_de_los_creditos(
        self,
    ) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 14: Validador de recursos y excepcion de los creditos.

        Para toda cadena de ruta, el validador del Guardarrail_Recursos la acepta
        si y solo si es una ruta relativa que empieza por `assets/` y termina en
        `.webp`, `.svg`, `.png` o `.avif`, y la rechaza nombrandola siempre que
        empiece por `http://`, por `https://`, por `//` o por `/`; y para todo
        documento emitido, todo atributo `src` lleva una ruta que ese validador
        acepta, el HTML no contiene ningun elemento `<link>` a hoja de estilo ni
        ningun `@import`, la Hoja_Estilo no contiene `url(` ni `http`, el
        Script_Unico es unico y no contiene `src=`, `http` ni la subcadena `//`,
        ninguna aparicion de la subcadena `http` cae en un atributo que provoque
        una peticion de red (solo en el `xmlns` de los `<svg>` en linea y en el
        `href` de los enlaces de video de las fichas, que son navegacion y no
        subrecursos), y dentro del Bloque_Creditos la subcadena `http` aparece
        unicamente como texto visible, nunca en un atributo y nunca dentro de un
        `<a href>`.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.8**
        """
        # El conjunto de extensiones aceptadas es exactamente el declarado, y la
        # extension ajena de la prueba no pertenece a el (criterio 1.11).
        self.assertNotIn(EXTENSION_AJENA, dp.EXTENSIONES_PERMITIDAS)
        # La Hoja_Estilo no carga ninguna imagen ni ningun recurso remoto
        # (criterios 1.2, 1.5 y 1.6): se mide una vez, no depende del caso.
        self.assertNotIn("url(", self.css)
        self.assertNotIn("http", self.css.lower())
        self.assertNotIn("@import", self.css.lower())

        def prop(caso: CasoRecurso) -> None:
            # ------------------------------------------------------------- #
            # 1. Validador_Rutas sobre las rutas del caso (criterios 1.1, 1.3)
            # ------------------------------------------------------------- #
            for ruta in caso.presentes:
                self.assertTrue(ruta.startswith("assets/"), msg=ruta)
                self.assertTrue(dp.ruta_aceptable(ruta), msg=ruta)

                # 2. Y los rechazos, nombrando la ruta (criterio 1.4).
                for prefijo in dp.PREFIJOS_RECHAZADOS:
                    mala: str = f"{prefijo}{ruta}"
                    with self.assertRaises(ErrorAsset) as ctx:
                        dp.ruta_aceptable(mala)
                    self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO)
                    self.assertIn(mala, str(ctx.exception))

                # 3. El "solo si" de la extension: fuera de las cuatro, no.
                ajena: str = f"{os.path.splitext(ruta)[0]}{EXTENSION_AJENA}"
                with self.assertRaises(ErrorAsset) as ctx:
                    dp.ruta_aceptable(ajena)
                self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO)
                self.assertIn(EXTENSION_AJENA, str(ctx.exception))

            # ------------------------------------------------------------- #
            # 4. El documento emitido (criterios 1.2, 1.3, 1.4, 1.5)
            # ------------------------------------------------------------- #
            lectura: Lectura = _lectura(caso.con_imagenes)
            lector: LectorRecursos = lectura.lector

            # Todo `src` es una ruta relativa que el Validador_Rutas acepta, y
            # ninguno empieza por un prefijo de red o absoluto.
            for etiqueta, valor in lector.srcs:
                for prefijo in dp.PREFIJOS_RECHAZADOS:
                    self.assertFalse(
                        valor.lower().startswith(prefijo),
                        msg=f"<{etiqueta} src={valor!r}> empieza por {prefijo!r}",
                    )
                self.assertTrue(dp.ruta_aceptable(valor), msg=valor)
            # Con los ocho presentes hay ocho `<img>`; sin ninguno, cero.
            self.assertEqual(
                len(lector.srcs), len(dp.CATALOGO) if caso.con_imagenes else 0
            )

            # Cero `<link>` (y por tanto cero hoja de estilo externa) y cero
            # `@import` en todo el documento (criterio 1.5).
            self.assertEqual(lector.etiquetas.get("link", 0), 0)
            self.assertNotIn("<link", lectura.bajo)
            self.assertNotIn("@import", lectura.bajo)
            for etiqueta, atributo, valor in lector.recursos:
                self.assertNotIn(
                    "http",
                    valor.lower(),
                    msg=f"<{etiqueta} {atributo}={valor!r}> pide red",
                )

            # Script_Unico: uno solo, propio, sin `src=`, sin `http` y sin `//`.
            self.assertEqual(lector.etiquetas.get("script", 0), 1)
            cuerpo_js: str = "".join(lector.scripts).lower()
            self.assertNotIn("src=", cuerpo_js)
            self.assertNotIn("http", cuerpo_js)
            self.assertNotIn("//", cuerpo_js)
            # Y el `<style>` embebido dice lo mismo que la Hoja_Estilo.
            for estilo in lector.estilos:
                self.assertNotIn("url(", estilo)
                self.assertNotIn("http", estilo.lower())

            # Toda aparicion de `http` en un atributo cae en un contexto que no
            # provoca peticion de red, y ninguna cae dentro del Bloque_Creditos
            # (criterios 1.2 y 1.8).
            for etiqueta, atributo, valor, en_creditos in lector.atributos_http:
                self.assertIn(
                    (etiqueta, atributo),
                    CONTEXTOS_HTTP_PERMITIDOS,
                    msg=f"<{etiqueta} {atributo}={valor[:60]!r}> trae http",
                )
                self.assertNotIn(atributo, ATRIBUTOS_RECURSO, msg=valor[:60])
                self.assertFalse(en_creditos, msg=f"{etiqueta}@{atributo}")
            self.assertEqual(lector.enlaces_en_creditos, 0)

            # ------------------------------------------------------------- #
            # 5. La excepcion: el enlace del credito como texto visible (1.8)
            # ------------------------------------------------------------- #
            fragmento: str = self._creditos_del_caso(caso)
            lector_creditos = LectorRecursos()
            lector_creditos.feed(fragmento)
            lector_creditos.close()

            # El bloque existe con sus ocho entradas con cualquier subconjunto de
            # presentes, y no trae ni un subrecurso ni un `<a href>`.
            self.assertEqual(len(lector_creditos.creditos), len(dp.CATALOGO))
            self.assertEqual(lector_creditos.recursos, [])
            self.assertEqual(lector_creditos.srcs, [])
            self.assertEqual(lector_creditos.enlaces_en_creditos, 0)
            self.assertEqual(lector_creditos.etiquetas.get("a", 0), 0)

            # Ningun atributo del bloque contiene `http`: la cadena solo vive en
            # los nodos de texto, y solo cuando el campo `enlace` esta presente.
            self.assertEqual(lector_creditos.atributos_http, [])
            textos_http = lector_creditos.texto_http
            enlace_presente: bool = "enlace" not in caso.ausentes
            self.assertEqual(bool(textos_http), enlace_presente)
            for texto, en_creditos in textos_http:
                self.assertTrue(en_creditos, msg=texto[:60])
                self.assertIn(URL_CREDITO, texto)

            # Y el campo `enlace` se lee como la URL cuando esta y como la marca
            # `dato pendiente` cuando falta (criterio 18.8).
            esperado: str = (
                URL_CREDITO if enlace_presente else dp.MARCA_PENDIENTE
            )
            enlaces = [t for campo, t in lector_creditos.campos if campo == "enlace"]
            self.assertEqual(len(enlaces), len(dp.CATALOGO))
            for texto in enlaces:
                self.assertEqual(texto, esperado)

        for_all(
            gen_caso_recurso,
            prop,
            iteraciones=ITERACIONES_POR_DEFECTO,
            etiqueta=ETQ_P14,
        )


# --------------------------------------------------------------------------- #
# Property 15
# --------------------------------------------------------------------------- #

ETQ_P15 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 15: Firma por extension de los assets copiados"
)


@dataclasses.dataclass(frozen=True, slots=True)
class CasoFirma:
    """Caso de la Property 15: un asset, su entrada del catalogo y el ruido.

    `asset` trae los bytes y la marca `firma_valida` que el generador construye y
    verifica por su cuenta; `indice` elige la entrada real del catalogo que se
    usara como unica declarada; `sobrantes` son los archivos no declarados que se
    siembran en el mismo directorio, y `estricto` alterna los dos modos de build,
    porque una firma que no corresponde aborta en los dos (criterio 5.13).
    """

    asset: gen.BytesAsset
    indice: int
    sobrantes: tuple[str, ...]
    estricto: bool


def gen_caso_firma(rnd) -> CasoFirma:
    """Caso de firma: bytes con o sin firma, entrada del catalogo y sobrantes."""
    return CasoFirma(
        asset=gen.gen_bytes_asset(rnd),
        indice=rnd.randrange(len(dp.CATALOGO)),
        sobrantes=tuple(n for n in NO_DECLARADOS if rnd.random() < 0.5),
        estricto=rnd.random() < 0.5,
    )


class TestProperty15FirmaPorExtension(unittest.TestCase):
    """Property 15: firma por extension de los assets copiados."""

    def setUp(self) -> None:
        self._raiz_original = dp._raiz_proyecto
        self._catalogo_original = dp.CATALOGO

    def tearDown(self) -> None:
        dp._raiz_proyecto = self._raiz_original
        dp.CATALOGO = self._catalogo_original

    def _redirigir_fuente(self, raiz: str) -> str:
        """Hace que `ruta_fuente` lea de `raiz` y devuelve el directorio fuente."""
        dp._raiz_proyecto = lambda: raiz
        fuente = os.path.join(raiz, *dp.DIR_ASSETS.split("/"))
        os.makedirs(fuente, exist_ok=True)
        return fuente

    def test_property_15_firma_por_extension_de_los_assets_copiados(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 15: Firma por extension de los assets copiados.

        Para toda secuencia de bytes y para toda extension declarada, la copia de
        assets publica el archivo si y solo si su contenido cumple la firma que
        corresponde a su extension (`RIFF` en 0 a 3 con `WEBP` en 8 a 11 para
        `.webp`, los bytes `89 50 4E 47` al inicio para `.png`, `ftyp` en 4 a 7
        para `.avif`, y la subcadena `<svg` dentro de los primeros 512 bytes para
        `.svg`); cuando la firma no coincide lanza `ErrorAsset` con el codigo
        `E_ASSET_INVALIDO` nombrando el archivo y no publica esa copia; y para
        todo conjunto de archivos no declarados en el Catalogo_Diagramas
        presentes en el directorio, la comprobacion los ignora por completo.

        **Validates: Requirements 5.12, 5.13, 5.14**
        """
        # Las cuatro Extensiones_Permitidas declaran firma y no hay firmas de
        # sobra: el dominio de la propiedad es exactamente el declarado.
        self.assertEqual(
            frozenset(build.FIRMAS), frozenset(dp.EXTENSIONES_PERMITIDAS)
        )

        def prop(caso: CasoFirma) -> None:
            asset = caso.asset
            extension = asset.extension

            # 1. La decision sobre los bytes es la firma del criterio 5.12, ni
            #    mas ni menos: el generador marca `firma_valida` comprobandola
            #    por su cuenta y `cumple_firma` tiene que coincidir.
            self.assertEqual(
                build.cumple_firma(asset.datos, extension),
                asset.firma_valida,
                msg=f"{extension}: firma decidida distinta de la construida",
            )

            declarado = dataclasses.replace(
                dp.CATALOGO[caso.indice],
                archivo=f"{dp.CATALOGO[caso.indice].id}{extension}",
            )
            dp.CATALOGO = (declarado,)
            relativa = dp.ruta_relativa(declarado)

            with tempfile.TemporaryDirectory(prefix="guia_p15_") as tmp:
                fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
                with open(os.path.join(fuente, declarado.archivo), "wb") as fh:
                    fh.write(asset.datos)
                # Ruido: archivos no declarados, todos con contenido invalido.
                for sobrante in caso.sobrantes:
                    with open(os.path.join(fuente, sobrante), "wb") as fh:
                        fh.write(BASURA)

                dir_dist = os.path.join(tmp, "dist")
                dir_tmp = os.path.join(dir_dist, ".tmp")
                os.makedirs(dir_tmp)
                destino_dir = build.dir_assets_dist(dir_dist)
                publicado = os.path.join(destino_dir, declarado.archivo)

                if asset.firma_valida:
                    copiados, faltantes = build._copiar_assets_atomico(
                        dir_dist, dir_tmp, estricto=caso.estricto
                    )
                    # 2. Firma correcta: se publica, con su mismo nombre y sus
                    #    mismos bytes, y nada queda a medias en dist/.tmp/.
                    self.assertEqual(copiados, (relativa,))
                    self.assertEqual(faltantes, ())
                    self.assertTrue(os.path.isfile(publicado), msg=relativa)
                    with open(publicado, "rb") as fh:
                        self.assertEqual(fh.read(), asset.datos)
                else:
                    # 3. Firma que no corresponde: aborta con E_ASSET_INVALIDO
                    #    nombrando el archivo, en Modo_Estricto y en Modo_Muestra.
                    with self.assertRaises(ErrorAsset) as ctx:
                        build._copiar_assets_atomico(
                            dir_dist, dir_tmp, estricto=caso.estricto
                        )
                    self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO)
                    self.assertIn(declarado.archivo, str(ctx.exception))
                    # 4. Y no publica esa copia.
                    self.assertFalse(os.path.exists(publicado), msg=relativa)

                # 5. En los dos caminos: dist/.tmp/ queda limpio y ningun archivo
                #    no declarado se mira ni se publica (criterio 5.14).
                self.assertEqual(os.listdir(dir_tmp), [])
                for sobrante in caso.sobrantes:
                    self.assertFalse(
                        os.path.exists(os.path.join(destino_dir, sobrante)),
                        msg=sobrante,
                    )

        for_all(
            gen_caso_firma,
            prop,
            iteraciones=ITERACIONES_POR_DEFECTO,
            etiqueta=ETQ_P15,
        )


# --------------------------------------------------------------------------- #
# Property 16
# --------------------------------------------------------------------------- #

ETQ_P16 = (
    "Feature: imagenes-reales-hero-interactivo, "
    "Property 16: Copia de assets, degradacion y reporte"
)

#: Probabilidad de marcar una entrada con Requiere_Archivo en verdadero. Las ocho
#: entradas reales lo declaran en falso (criterio 5.2), asi que el caso exigente
#: solo existe mutando el catalogo; con 0.35 aparecen en 100 iteraciones tanto
#: catalogos sin ninguna exigente como catalogos con varias.
PESO_REQUIERE_ARCHIVO: float = 0.35

#: Tope de reintentos al pedirle al generador bytes con firma valida de una
#: extension concreta. `gen_bytes_asset` sortea extension y validez, asi que
#: acierta una de cada ocho veces; 200 intentos fallidos serian un generador roto.
MAX_INTENTOS_BYTES: int = 200


def _nombre_de(ruta: str) -> str:
    """Nombre de archivo de una ruta relativa del Catalogo_Diagramas."""
    return ruta.rsplit("/", 1)[-1]


def _id_de(ruta: str) -> str:
    """Identificador del Diagrama_Postura al que pertenece una ruta relativa."""
    return os.path.splitext(_nombre_de(ruta))[0]


def _bytes_validos_de(rnd: random.Random, extension: str) -> bytes:
    """Bytes con la firma valida de `extension`, pedidos a `gen.gen_bytes_asset`.

    La Property 16 no habla de firmas (eso es la 15): necesita assets que la
    copia acepte, para poder mirar la publicacion, la degradacion y el reporte.
    Se reutiliza el mismo generador en vez de escribir aqui una segunda fuente de
    bytes de firma, que podria discrepar de la declarada.
    """
    for _ in range(MAX_INTENTOS_BYTES):
        asset = gen.gen_bytes_asset(rnd)
        if asset.firma_valida and asset.extension == extension:
            return asset.datos
    raise RuntimeError(
        f"gen_bytes_asset no produjo bytes validos de {extension!r} "
        f"en {MAX_INTENTOS_BYTES} intentos"
    )


@dataclasses.dataclass(frozen=True, slots=True)
class CasoCopia:
    """Caso de la Property 16: que assets estan, cuales se exigen y en que modo.

    `presentes` son las rutas relativas de los Archivo_Diagrama que existiran de
    verdad en el directorio fuente, en el orden del catalogo (incluidos el
    subconjunto vacio y el total); `datos` trae los bytes de cada una, con firma
    valida; `requeridos` son los identificadores que el catalogo mutado marcara
    con Requiere_Archivo en verdadero, y `estricto` alterna Modo_Estricto y
    Modo_Muestra.
    """

    presentes: tuple[str, ...]
    datos: tuple[tuple[str, bytes], ...]
    requeridos: tuple[str, ...]
    estricto: bool


def gen_caso_copia(rnd: random.Random) -> CasoCopia:
    """Subconjunto de presentes con sus bytes, marcas Requiere_Archivo y modo."""
    presentes: tuple[str, ...] = gen.gen_presentes(rnd)
    datos: tuple[tuple[str, bytes], ...] = tuple(
        (ruta, _bytes_validos_de(rnd, os.path.splitext(ruta)[1]))
        for ruta in presentes
    )
    # Los identificadores salen de `gen.IDS_DIAGRAMA`, no de `dp.CATALOGO`: la
    # propiedad muta el catalogo dentro de cada iteracion y el generador no debe
    # depender de ese estado.
    requeridos: tuple[str, ...] = tuple(
        identificador
        for identificador in gen.IDS_DIAGRAMA
        if rnd.random() < PESO_REQUIERE_ARCHIVO
    )
    return CasoCopia(
        presentes=presentes,
        datos=datos,
        requeridos=requeridos,
        estricto=rnd.random() < 0.5,
    )


class TestProperty16CopiaDegradacionYReporte(unittest.TestCase):
    """Property 16: copia de assets, degradacion y reporte."""

    def setUp(self) -> None:
        self._raiz_original = dp._raiz_proyecto
        self._catalogo_original = dp.CATALOGO
        # `construir()` alimenta esta linea del reporte con el mismo ayudante.
        # Se calcula una vez, con el catalogo real: la mutacion de cada iteracion
        # solo toca `archivo` y `requiere_archivo`, que no cambian las fases.
        self._fases_omitidas = build._fases_omitidas()

    def tearDown(self) -> None:
        dp._raiz_proyecto = self._raiz_original
        dp.CATALOGO = self._catalogo_original

    def _redirigir_fuente(self, raiz: str) -> str:
        """Hace que `ruta_fuente` lea de `raiz` y devuelve el directorio fuente."""
        dp._raiz_proyecto = lambda: raiz
        fuente = os.path.join(raiz, *dp.DIR_ASSETS.split("/"))
        os.makedirs(fuente, exist_ok=True)
        return fuente

    def _catalogo_mutado(self, caso: CasoCopia) -> tuple[dp.DiagramaPostura, ...]:
        """Las ocho entradas reales con la extension sorteada y las marcas."""
        archivos: dict[str, str] = {
            _id_de(ruta): _nombre_de(ruta) for ruta in caso.presentes
        }
        return tuple(
            dataclasses.replace(
                diagrama,
                archivo=archivos.get(diagrama.id, diagrama.archivo),
                requiere_archivo=diagrama.id in caso.requeridos,
            )
            for diagrama in self._catalogo_original
        )

    def _reporte(
        self,
        *,
        estricto: bool,
        copiados: tuple[str, ...],
        faltantes: tuple[str, ...],
    ) -> build.Reporte:
        """Arma el `Reporte` con los mismos ayudantes que usa `construir()`.

        No se llama a `construir()`: la propiedad corre 100 veces y el build
        completo tarda minutos. Los seis campos de los diagramas se alimentan de
        las mismas consultas de la Fase 8b, de modo que lo que aqui se comprueba
        es lo que el build real declara.
        """
        return build.Reporte(
            modo=build.MODO_ESTRICTO if estricto else build.MODO_MUESTRA,
            publicable=False,
            paginas_totales=0,
            fichas=0,
            bloques=0,
            qr=0,
            posturas=0,
            diagramas=len(dp.CATALOGO),
            capitulos=0,
            version_python=platform.python_version(),
            assets_copiados=len(copiados),
            assets_faltantes=faltantes,
            diagramas_svg=build._contar_diagramas_svg(dp.presentes()),
            fases_omitidas=self._fases_omitidas,
            creditos_pendientes=dp.campos_pendientes(),
            fundamentos_omitidos=build_site.fundamentos_omitidos(),
        )

    def test_property_16_copia_de_assets_degradacion_y_reporte(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 16: Copia de assets, degradacion y reporte.

        Para todo subconjunto de Archivo_Diagrama presentes: la copia publica en
        `dist/assets/img/tecnica/` exactamente los presentes, con su mismo
        nombre, y no deja ningun resto en `dist/.tmp/`; el reporte declara el
        numero de copiados, la lista de ausentes y el numero de diagramas
        rendidos desde el Generador_SVG, y esos dos conteos de diagramas suman
        ocho; en Modo_Muestra el build termina siempre; en Modo_Estricto el build
        termina cuando todo ausente esta marcado con Requiere_Archivo en falso, y
        lanza `ErrorAsset` con el codigo `E_ASSET_FALTANTE` y con la ruta
        relativa de un archivo ausente en el mensaje cuando alguno marcado
        Requiere_Archivo falta.

        **Validates: Requirements 5.6, 5.7, 5.8, 5.9, 5.10, 5.11**
        """
        # El catalogo declara las ocho entradas: el "suman ocho" del criterio
        # 5.11 se mide contra el catalogo, no contra un numero suelto.
        self.assertEqual(len(self._catalogo_original), len(gen.IDS_DIAGRAMA))

        def prop(caso: CasoCopia) -> None:
            catalogo = self._catalogo_mutado(caso)
            presentes = frozenset(caso.presentes)
            copiados_esp = tuple(
                dp.ruta_relativa(d)
                for d in catalogo
                if dp.ruta_relativa(d) in presentes
            )
            faltantes_esp = tuple(
                dp.ruta_relativa(d)
                for d in catalogo
                if dp.ruta_relativa(d) not in presentes
            )
            exigente_ausente = next(
                (
                    dp.ruta_relativa(d)
                    for d in catalogo
                    if d.requiere_archivo and dp.ruta_relativa(d) not in presentes
                ),
                None,
            )

            dp.CATALOGO = catalogo
            try:
                with tempfile.TemporaryDirectory(prefix="guia_p16_") as tmp:
                    fuente = self._redirigir_fuente(os.path.join(tmp, "repo"))
                    for ruta, datos in caso.datos:
                        with open(os.path.join(fuente, _nombre_de(ruta)), "wb") as fh:
                            fh.write(datos)

                    dir_dist = os.path.join(tmp, "dist")
                    dir_tmp = os.path.join(dir_dist, ".tmp")
                    os.makedirs(dir_tmp)
                    destino_dir = build.dir_assets_dist(dir_dist)

                    def verificar_completo(estricto: bool) -> None:
                        """Contrato de una copia que termina, en el modo dado."""
                        copiados, faltantes = build._copiar_assets_atomico(
                            dir_dist, dir_tmp, estricto=estricto
                        )
                        # 1. Publica exactamente los presentes, con su mismo
                        #    nombre, y enumera los ausentes (criterios 5.6, 5.10).
                        self.assertEqual(copiados, copiados_esp)
                        self.assertEqual(faltantes, faltantes_esp)
                        if copiados_esp:
                            self.assertEqual(
                                sorted(os.listdir(destino_dir)),
                                sorted(_nombre_de(r) for r in copiados_esp),
                            )
                            for ruta, datos in caso.datos:
                                publicado = os.path.join(
                                    destino_dir, _nombre_de(ruta)
                                )
                                with open(publicado, "rb") as fh:
                                    self.assertEqual(fh.read(), datos, msg=ruta)
                        else:
                            # Sin nada que publicar no se crea `dist/assets/`.
                            self.assertFalse(os.path.exists(destino_dir))
                        # 2. La publicacion es atomica desde `dist/.tmp/` y no
                        #    deja ningun resto (criterio 5.7).
                        self.assertEqual(os.listdir(dir_tmp), [])

                        # 3. El reporte declara los tres numeros y los dos
                        #    conteos de diagramas suman ocho (criterio 5.11).
                        reporte = self._reporte(
                            estricto=estricto,
                            copiados=copiados,
                            faltantes=faltantes,
                        )
                        self.assertEqual(
                            reporte.assets_copiados + reporte.diagramas_svg,
                            len(catalogo),
                        )
                        self.assertEqual(reporte.assets_copiados, len(copiados_esp))
                        self.assertEqual(reporte.diagramas_svg, len(faltantes_esp))
                        texto = reporte.texto()
                        self.assertIn(f"assets copiados : {len(copiados_esp)}", texto)
                        self.assertIn(f"diagramas SVG   : {len(faltantes_esp)}", texto)
                        if faltantes_esp:
                            self.assertIn(
                                f"assets ausentes : {len(faltantes_esp)}: ", texto
                            )
                            for ruta in faltantes_esp:
                                self.assertIn(ruta, texto)
                        else:
                            self.assertIn("assets ausentes : 0", texto)

                    aborta = caso.estricto and exigente_ausente is not None
                    if aborta:
                        # 4. Modo_Estricto con un ausente marcado Requiere_Archivo:
                        #    `E_ASSET_FALTANTE` con su ruta relativa (criterio 5.8).
                        with self.assertRaises(ErrorAsset) as ctx:
                            build._copiar_assets_atomico(
                                dir_dist, dir_tmp, estricto=True
                            )
                        self.assertEqual(ctx.exception.codigo, E_ASSET_FALTANTE)
                        self.assertIn(exigente_ausente, str(ctx.exception))
                        self.assertEqual(os.listdir(dir_tmp), [])
                        # Ni un solo nombre fuera de los presentes se publico.
                        if os.path.isdir(destino_dir):
                            nombres = frozenset(
                                _nombre_de(r) for r in copiados_esp
                            )
                            for nombre in os.listdir(destino_dir):
                                self.assertIn(nombre, nombres)
                        # 5. En Modo_Muestra el build termina siempre, con el
                        #    mismo catalogo exigente (criterio 5.10).
                        verificar_completo(False)
                    else:
                        # 6. Sin ausentes exigentes, Modo_Estricto tambien termina
                        #    (criterio 5.9), igual que Modo_Muestra.
                        verificar_completo(caso.estricto)
            finally:
                # El catalogo vuelve a su sitio en cada iteracion: el generador y
                # las demas pruebas leen siempre el declarado.
                dp.CATALOGO = self._catalogo_original

        for_all(
            gen_caso_copia,
            prop,
            iteraciones=ITERACIONES_POR_DEFECTO,
            etiqueta=ETQ_P16,
        )


# --------------------------------------------------------------------------- #
# Property 53
# --------------------------------------------------------------------------- #

ETQ_P53 = (
    "Feature: imagenes-reales-hero-interactivo, Property 53: Validador_Rutas"
)

#: Extensiones_Permitidas tal como el criterio 30.1 la declara: las cuatro y en
#: ese orden. Se escribe aqui literalmente para que la prueba compare el orden
#: contra el requisito, y no contra si misma.
ORDEN_EXTENSIONES: tuple[str, ...] = (".webp", ".svg", ".png", ".avif")

#: Numero de entradas del Catalogo_Diagramas (criterio 30.7).
ENTRADAS_CATALOGO: int = 8


def _condiciones(ruta: str) -> tuple[bool, bool, bool, str]:
    """Las tres condiciones del Requisito 30 sobre `ruta`, mas su extension.

    Devuelve `(bajo_assets, sin_ascendente, extension_permitida, extension)`.
    Se miden sobre la ruta **normalizada** (el `\\` de Windows convertido en
    `/`), que es la forma en la que el criterio 30.2 pregunta por el prefijo:
    normalizar antes de decidir solo puede endurecer el veredicto, porque es lo
    que hace que `..\\` cuente como segmento `..` y que `\\assets\\...` cuente
    como ruta absoluta.

    Esta funcion es el enunciado de la propiedad, no una copia del validador: no
    ordena los rechazos ni compone ningun mensaje, solo dice cuales de las tres
    condiciones se cumplen.
    """
    normalizada: str = ruta.replace("\\", "/")
    bajo_assets: bool = normalizada.startswith(dp.PREFIJO_ASSETS)
    sin_ascendente: bool = dp.SEGMENTO_ASCENDENTE not in normalizada.split("/")
    extension: str = os.path.splitext(normalizada)[1].lower()
    return bajo_assets, sin_ascendente, extension in ORDEN_EXTENSIONES, extension


def _nombra(mensaje: str, valor: str) -> bool:
    """True si `mensaje` nombra `valor`, tal cual o en su forma `repr`.

    El validador interpola con `!r`, asi que una ruta con `\\` aparece con la
    barra doblada. Se admiten las dos formas para no atar la propiedad al estilo
    de interpolacion, que no es lo que el requisito pide.
    """
    return valor in mensaje or repr(valor) in mensaje


class TestProperty53ValidadorRutas(unittest.TestCase):
    """Property 53: Validador_Rutas."""

    def test_property_53_validador_rutas(self) -> None:
        """Feature: imagenes-reales-hero-interactivo, Property 53: Validador_Rutas.

        Para toda cadena de ruta, el Validador_Rutas la acepta si y solo si
        empieza por `assets/`, no contiene el segmento `..` y su extension,
        comparada en minusculas, pertenece a Extensiones_Permitidas; cuando la
        rechaza por prefijo de red o por segmento `..` su mensaje nombra la ruta,
        y cuando la rechaza por extension su mensaje nombra la extension;
        Extensiones_Permitidas contiene exactamente `.webp`, `.svg`, `.png` y
        `.avif`, en ese orden; y las ocho rutas relativas del Catalogo_Diagramas
        son aceptadas.

        **Validates: Requirements 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7**
        """
        # Criterio 30.1: las cuatro extensiones y su orden exacto, comparados
        # contra la tupla del requisito. `EXTENSIONES` sigue siendo la misma
        # tupla, de modo que no haya un segundo literal que se desincronice.
        self.assertEqual(dp.EXTENSIONES_PERMITIDAS, ORDEN_EXTENSIONES)
        self.assertEqual(dp.EXTENSIONES, ORDEN_EXTENSIONES)
        self.assertEqual(gen.EXTENSIONES_ASSET, ORDEN_EXTENSIONES)
        self.assertEqual(dp.PREFIJOS_RECHAZADOS, gen.PREFIJOS_HOSTILES)

        # Criterio 30.7: las ocho rutas relativas del catalogo son aceptadas.
        self.assertEqual(len(dp.CATALOGO), ENTRADAS_CATALOGO)
        for entrada in dp.CATALOGO:
            relativa: str = dp.ruta_relativa(entrada)
            self.assertTrue(dp.ruta_aceptable(relativa), msg=relativa)

        def prop(caso: gen.RutaCandidata) -> None:
            ruta: str = caso.ruta
            bajo_assets, sin_ascendente, ext_ok, extension = _condiciones(ruta)
            aceptable: bool = bajo_assets and sin_ascendente and ext_ok
            contexto: str = f"{caso.familia}: {ruta!r}"

            if aceptable:
                # 1. El "si": las tres condiciones bastan, con la extension en
                #    mayusculas (criterio 30.6) y con el separador de Windows.
                self.assertTrue(dp.ruta_aceptable(ruta), msg=contexto)
                return

            # 2. El "solo si": si falla cualquiera de las tres, rechazo con
            #    `ErrorAsset(E_ASSET_INVALIDO)`. Nunca un `False` silencioso ni
            #    una excepcion de otra clase.
            with self.assertRaises(ErrorAsset, msg=contexto) as ctx:
                dp.ruta_aceptable(ruta)
            self.assertEqual(ctx.exception.codigo, E_ASSET_INVALIDO, msg=contexto)
            mensaje: str = ctx.exception.mensaje

            # 3. Prefijo de red o de raiz, segmento `..` o ruta que no vive bajo
            #    `assets/`: el mensaje nombra la ruta (criterios 30.3 y 30.4).
            if not bajo_assets or not sin_ascendente:
                self.assertTrue(_nombra(mensaje, ruta), msg=f"{contexto} -> {mensaje}")
            else:
                # 4. La ruta esta bien y lo unico ajeno es el formato: el mensaje
                #    nombra la extension, ya en minusculas (criterios 30.5, 30.6).
                self.assertFalse(ext_ok, msg=contexto)
                self.assertTrue(
                    _nombra(mensaje, extension), msg=f"{contexto} -> {mensaje}"
                )
                self.assertEqual(
                    ctx.exception.detalle.get("extension"), extension, msg=contexto
                )

        for_all(
            gen.gen_ruta_hostil,
            prop,
            iteraciones=ITERACIONES_POR_DEFECTO,
            etiqueta=ETQ_P53,
        )


if __name__ == "__main__":
    unittest.main()
