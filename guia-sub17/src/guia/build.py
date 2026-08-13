"""Orquestador_Build: ensambla la Guia_Extensa y sus validaciones (`build.py`).

Este modulo es el punto de union del pipeline: parte del `Catalogo_Contenido`
(paquete `guia.contenido`), lo pagina con el indice de dos pasadas y emite dos
artefactos con **escritura atomica** desde `dist/.tmp/`:

* ``dist/guia.pdf`` — el PDF A4 (tema claro de alto contraste, estetica
  congelada) escrito byte a byte por `build_pdf`.
* ``dist/web/`` — el sitio HTML estatico (un ``index.html`` mas un HTML por
  capitulo, estetica oscura congelada) escrito por `build_html`.

Dos modos de construccion
-------------------------

Regla vigente del proyecto: se usa **solo el contenido disponible** (portada +
15 fichas reales via `contenido.concatenar()`); no se inventan fichas ni se
detiene el pipeline por falta de contenido. Por eso hay dos modos:

* ``MODO_MUESTRA`` (por defecto): ejecuta el pipeline real y **todas** las
  validaciones estructurales, pero **omite** los umbrales de publicacion
  REVISADOS (>=100 paginas, entre 45 y 60 fichas, >=12 semanas/bloques). El
  reporte se marca como ``NO_PUBLICABLE`` / ``MUESTRA`` y enumera esos umbrales
  omitidos.
* ``MODO_ESTRICTO``: ademas de todo lo anterior, exige los umbrales de cobertura
  y el rango de paginas publicable. Es la ruta para cuando exista el catalogo
  completo; conserva intacta la logica estricta.

Validaciones que se ejecutan **siempre** (en ambos modos): preflight de entorno,
esquema del Catalogo_JSON, codificacion WinAnsi de todo texto, unicidad del
Plan_Rotacion (verificador independiente), round-trip de cada QR, operadores y
coordenadas del PDF (`verify_pdf`), coherencia del indice de dos pasadas y el
PDF de control, y el guardarrail de fuente unica de fichas (Req 15.4). En
MODO_MUESTRA se omiten **solo** los umbrales de publicacion revisados (>=100
paginas, 45-60 fichas, >=12 semanas); el reporte lo indica explicitamente.

Sin `assert` en produccion: todo fallo se expresa como `ErrorBuild` (o subclase)
con su codigo `E_*`. `main()` captura `ErrorBuild`, imprime **una** linea en
`stderr` y hace `sys.exit(1)`; en exito imprime el reporte y sale con 0.

Entrada: ``python -m guia.build`` (o ``python src/build.py``).

_Requirements: 1.8, 1.9, 2.1, 2.6, 2.8, 2.9, 5.10, 9.8, 10.1, 10.3, 10.4, 10.5,
10.6, 10.7_
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field

from . import (
    afm,
    build_guia_pdf,
    build_html,
    build_laminas,
    build_pdf,
    build_site,
    contenido,
    diagramas_postura,
    preflight,
    qr,
    qr_decode,
    rotacion,
    svg_postura,
    verify_pdf,
    verify_rotacion,
)
from .contenido import cap10_fundamentos
from .errores import (
    E_ASSET_FALTANTE,
    E_ASSET_INVALIDO,
    E_FICHA_EN_MODULO,
    ErrorAsset,
    ErrorBuild,
    ErrorFuenteFichas,
)
from .indice import IndiceCtx, paginar_con_indice
from .layout import PaginaRender, Plantilla, TipoElemento
from .plantillas import DatosIndice, EntradaIndice
from .plantillas import indice as _plantilla_indice
from .schema import exigir_minimo

__all__ = [
    "MODO_MUESTRA",
    "MODO_ESTRICTO",
    "N_BLOQUES_MUESTRA",
    "N_BLOQUES_ESTRICTO",
    "SEMILLA_ROTACION",
    "NOMBRE_PDF",
    "NOMBRE_LAMINAS",
    "NOMBRE_WEB",
    "NOMBRE_JSON",
    "NOMBRE_ASSETS",
    "FIRMAS",
    "BYTES_FIRMA",
    "firma_esperada",
    "cumple_firma",
    "dir_assets_dist",
    "PDF_HREF_WEB",
    "RANGO_PAGINAS_PUBLICABLE",
    "MIN_PAGINAS_PUBLICABLE",
    "MIN_FICHAS_PUBLICABLE",
    "MAX_FICHAS_PUBLICABLE",
    "MIN_BLOQUES_PUBLICABLE",
    "Reporte",
    "dir_dist_por_defecto",
    "construir",
    "verificar_sin_fichas_en_modulos",
    "main",
]


# --------------------------------------------------------------------------- #
# Constantes de modo, artefactos y rotacion
# --------------------------------------------------------------------------- #

#: Modo que ejecuta el pipeline y las validaciones estructurales pero omite los
#: umbrales de cobertura de publicacion. El reporte queda como NO_PUBLICABLE.
MODO_MUESTRA: str = "muestra"

#: Modo que ademas exige cobertura y rango de paginas publicable.
MODO_ESTRICTO: str = "estricto"

#: Bloques del Plan_Rotacion en modo muestra: con las 15 fichas reales solo hay
#: combinaciones unicas para unos pocos bloques (el umbral >=24 es cobertura y
#: se omite en muestra). Se genera un plan pequeno para ejercitar el generador y
#: su verificador de unicidad sin agotar las combinaciones.
N_BLOQUES_MUESTRA: int = 6

#: Bloques del Plan_Rotacion en modo estricto (Req 5.1: >= 24).
N_BLOQUES_ESTRICTO: int = 26

#: Semilla determinista del Plan_Rotacion (Riesgo 13).
SEMILLA_ROTACION: int = 20260101

#: Nombre del PDF emitido por esta feature (decision C6).
NOMBRE_PDF: str = "guia.pdf"

#: Nombre del PDF de laminas verticales para telefono/WhatsApp (Target_Laminas).
NOMBRE_LAMINAS: str = "laminas.pdf"

#: Nombre de la carpeta del sitio HTML estatico dentro de `dist/`.
NOMBRE_WEB: str = "web"

#: Nombre del Catalogo_JSON crudo copiado a `dist/` para su descarga (Req 13.1).
NOMBRE_JSON: str = "ejercicios.json"

#: Ruta relativa del PDF desde `dist/web/*.html` (un nivel arriba).
PDF_HREF_WEB: str = "../" + NOMBRE_PDF

#: Directorio de publicacion de los Archivo_Diagrama, relativo a `dist/` y con
#: separador "/" porque es tambien la ruta que viaja al HTML (criterio 5.6). Es
#: el mismo valor que `diagramas_postura.DIR_ASSETS`, no un segundo literal.
NOMBRE_ASSETS: str = diagramas_postura.DIR_ASSETS

#: Firma que debe cumplir la **copia** de un Asset_Local segun su extension,
#: antes de publicarla (criterios 5.12 y 30.10). Cada token es
#: `LITERAL@INICIO` (el literal aparece exactamente en ese desplazamiento) o
#: `LITERAL@INICIO:FIN` (el literal aparece en algun punto de esa ventana). Un
#: literal formado solo por digitos hexadecimales y de longitud par se lee como
#: bytes (`89504E47` son los cuatro bytes de cabecera del PNG); cualquier otro
#: literal se lee como ASCII (`RIFF`, `WEBP`, `ftyp`, `<svg`).
FIRMAS: dict[str, tuple[str, ...]] = {
    ".webp": ("RIFF@0", "WEBP@8"),
    ".png": ("89504E47@0",),
    ".avif": ("ftyp@4",),
    ".svg": ("<svg@0:512",),
}

#: Bytes que se leen de la copia para comprobar su firma. 512 es la ventana mas
#: ancha de `FIRMAS` (la del `.svg`), asi que basta una sola lectura corta para
#: las cuatro extensiones y nunca se carga el archivo entero en memoria.
BYTES_FIRMA: int = 512

#: Digitos hexadecimales, para decidir si el literal de un token de `FIRMAS` son
#: bytes en hexadecimal o texto ASCII.
_HEXDIGITOS: frozenset[str] = frozenset("0123456789abcdefABCDEF")

# --------------------------------------------------------------------------- #
# Umbrales de publicacion REVISADOS (aprobados por el usuario)
# --------------------------------------------------------------------------- #
#
# Estos valores sustituyen a los antiguos (>=120 fichas, >=12 por posicion,
# rango 200-300 paginas, etc.). Un build es PUBLICABLE (solo en MODO_ESTRICTO)
# cuando cumple los tres a la vez:
#
#   * paginas >= 100
#   * 45 <= fichas <= 60
#   * bloques (semanas) >= 12
#
# El "12 semanas" se interpreta como >= 12 Bloque_Semanal del Plan_Rotacion
# (una temporada de al menos 12 semanas): se usa `>=` por coherencia con el
# resto de umbrales de cobertura, que son minimos. En MODO_MUESTRA estos tres
# umbrales se OMITEN y el reporte los enumera como omitidos.

#: Paginas minimas para publicar (revisado: antes el rango era 200-300).
MIN_PAGINAS_PUBLICABLE: int = 100

#: Cota inferior de fichas para publicar (revisado: antes >= 120).
MIN_FICHAS_PUBLICABLE: int = 45

#: Cota superior de fichas para publicar (revisado).
MAX_FICHAS_PUBLICABLE: int = 60

#: Bloques (semanas) minimos del Plan_Rotacion para publicar (revisado: 12).
MIN_BLOQUES_PUBLICABLE: int = 12

#: Rango de paginas publicable como (min, max). El minimo revisado es 100; el
#: maximo se conserva como cota de sanidad. Se mantiene el nombre para no
#: romper importadores existentes.
RANGO_PAGINAS_PUBLICABLE: tuple[int, int] = (MIN_PAGINAS_PUBLICABLE, 300)

#: Titulo del documento (PDF e info del catalogo).
_TITULO_DOC: str = "Guia Extensa de Entrenamiento Femenil Sub-17"


# --------------------------------------------------------------------------- #
# Reporte del build
# --------------------------------------------------------------------------- #

#: Marca de una lista vacia en el reporte: el numero 0 y nada mas, para que la
#: linea exista siempre y el reporte sea comparable entre corridas.
_LISTA_VACIA: str = "0"


def _lista_reporte(valores: tuple[str, ...]) -> str:
    """Cuenta y enumera los valores de una lista del reporte, en su orden."""
    if not valores:
        return _LISTA_VACIA
    return f"{len(valores)}: " + ", ".join(valores)


def _fases_a_texto(pares: tuple[tuple[str, int], ...]) -> tuple[str, ...]:
    """`(id_diagrama, numero)` como `id#numero`, para la linea del reporte."""
    return tuple(f"{id_}#{numero}" for id_, numero in pares)


def _creditos_a_texto(pares: tuple[tuple[str, tuple[str, ...]], ...]) -> tuple[str, ...]:
    """`(id, campos_ausentes)` como `id[campo|campo]`, para el reporte (18.9)."""
    return tuple(f"{id_}[{'|'.join(campos)}]" for id_, campos in pares)


@dataclass(slots=True)
class Reporte:
    """Resumen de un build: conteos recalculados, tiempos, rutas y modo.

    `publicable` es `True` solo cuando el build corre en modo estricto y pasa
    los umbrales de cobertura y el rango de paginas. En modo muestra siempre es
    `False` y `umbrales_omitidos` enumera las validaciones de cobertura que no
    se aplicaron.
    """

    modo: str
    publicable: bool
    paginas_totales: int
    fichas: int
    bloques: int
    qr: int
    posturas: int
    diagramas: int
    capitulos: int
    version_python: str
    tiempos: dict[str, float] = field(default_factory=dict)
    umbrales_omitidos: tuple[str, ...] = ()
    validaciones: tuple[str, ...] = ()
    ruta_pdf: str = ""
    ruta_web_index: str = ""
    ruta_sitio: str = ""
    laminas: int = 0
    ruta_laminas: str = ""
    ruta_json: str = ""
    #: Paginas del Modelo_Paginas real (`_paginar()`), que es el conteo que
    #: evalua el umbral de publicacion. `paginas_totales` cuenta en cambio las
    #: hojas del PDF de fichas (una por ficha), asi que los dos numeros
    #: difieren; quien informe "paginas de la guia" debe usar este campo.
    paginas_modelo: int = 0
    #: Archivo_Diagrama publicados en `dist/assets/img/tecnica/` por la fase de
    #: copia atomica (criterio 5.11).
    assets_copiados: int = 0
    #: Rutas relativas de los Archivo_Diagrama declarados que no existen, en el
    #: orden del Catalogo_Diagramas (criterios 5.10 y 5.11).
    assets_faltantes: tuple[str, ...] = ()
    #: Diagrama_Postura rendidos por el Generador_SVG, es decir los que no tienen
    #: Archivo_Diagrama presente. Con `assets_copiados` suma las ocho entradas
    #: del catalogo (criterio 5.11).
    diagramas_svg: int = 0
    #: Pares `(id_diagrama, numero)` de las Fase_Numerada que el Generador_SVG no
    #: pudo emitir. La omision degrada, no aborta (criterio 14.17).
    fases_omitidas: tuple[tuple[str, int], ...] = ()
    #: Pares `(id_diagrama, campos_ausentes)` del Bloque_Creditos incompleto. El
    #: build termina; los campos solo quedan enumerados (criterio 18.9).
    creditos_pendientes: tuple[tuple[str, tuple[str, ...]], ...] = ()
    #: Fundamento declarados fuera del conjunto cerrado de cuatro: el Motor_Sitio
    #: no emite bloque para ellos y el reporte los enumera (criterio 3.9).
    fundamentos_omitidos: tuple[str, ...] = ()

    def texto(self) -> str:
        """Reporte legible en una sola cadena para imprimir en stdout."""
        estado = "PUBLICABLE" if self.publicable else "NO_PUBLICABLE / MUESTRA"
        lineas: list[str] = [
            f"Guia Extensa Sub-17 — build {self.modo.upper()} [{estado}]",
            f"  paginas totales : {self.paginas_totales}",
            f"  paginas modelo  : {self.paginas_modelo}",
            f"  fichas          : {self.fichas}",
            f"  bloques semana  : {self.bloques}",
            f"  codigos QR      : {self.qr}",
            f"  laminas         : {self.laminas}",
            f"  posturas        : {self.posturas}",
            f"  diagramas       : {self.diagramas}",
            f"  capitulos       : {self.capitulos}",
            f"  Python          : {self.version_python}",
        ]
        for fase, seg in self.tiempos.items():
            lineas.append(f"  t[{fase}]        : {seg:.3f} s")
        if self.umbrales_omitidos:
            lineas.append(
                "  umbrales OMITIDOS (muestra): " + ", ".join(self.umbrales_omitidos)
            )
        lineas.append(f"  assets copiados : {self.assets_copiados}")
        lineas.append(
            "  assets ausentes : " + _lista_reporte(self.assets_faltantes)
        )
        lineas.append(f"  diagramas SVG   : {self.diagramas_svg}")
        lineas.append(
            "  fases omitidas  : "
            + _lista_reporte(_fases_a_texto(self.fases_omitidas))
        )
        lineas.append(
            "  creditos pend.  : "
            + _lista_reporte(_creditos_a_texto(self.creditos_pendientes))
        )
        lineas.append(
            "  fundamentos om. : " + _lista_reporte(self.fundamentos_omitidos)
        )
        lineas.append("  validaciones    : " + ", ".join(self.validaciones))
        lineas.append(f"  PDF             : {self.ruta_pdf}")
        lineas.append(f"  LAMINAS         : {self.ruta_laminas}")
        lineas.append(f"  WEB             : {self.ruta_web_index}")
        lineas.append(f"  SITIO           : {self.ruta_sitio}")
        lineas.append(f"  JSON            : {self.ruta_json}")
        return "\n".join(lineas)


# --------------------------------------------------------------------------- #
# Localizacion de rutas del proyecto
# --------------------------------------------------------------------------- #


def _raiz_proyecto() -> str:
    """Ruta absoluta a `guia-sub17/` (dos niveles sobre `src/guia/build.py`)."""
    aqui = os.path.dirname(os.path.abspath(__file__))          # .../src/guia
    src = os.path.dirname(aqui)                                # .../src
    return os.path.dirname(src)                                # .../guia-sub17


def dir_dist_por_defecto() -> str:
    """Directorio `dist/` por defecto, relativo a la raiz del proyecto."""
    return os.path.join(_raiz_proyecto(), "dist")


# --------------------------------------------------------------------------- #
# Paginacion con indice de dos pasadas
# --------------------------------------------------------------------------- #


def _entradas_indice(paginas: list[PaginaRender]) -> list[EntradaIndice]:
    """Entradas del indice: una por capitulo que expone una portadilla.

    En modo muestra el contenido disponible (portada + fundamentos) no usa la
    plantilla `PORTADILLA_CAPITULO`, asi que la lista queda vacia y el paginador
    de dos pasadas no reserva paginas de indice; la coherencia del indice se
    verifica de todos modos (trivial sobre una lista vacia). Cuando exista el
    catalogo completo con portadillas, esta funcion las recoge en orden.
    """
    entradas: list[EntradaIndice] = []
    vistos: set[str] = set()
    for pagina in paginas:
        if (
            pagina.plantilla is Plantilla.PORTADILLA_CAPITULO
            and pagina.capitulo_id not in vistos
        ):
            vistos.add(pagina.capitulo_id)
            entradas.append(
                EntradaIndice(
                    titulo=pagina.capitulo_titulo or pagina.capitulo_id,
                    capitulo_id=pagina.capitulo_id,
                )
            )
    return entradas


def _renumerar(paginas: list[PaginaRender]) -> list[PaginaRender]:
    """Asigna folios consecutivos 1..N in situ y devuelve la misma lista."""
    for indice_pagina, pagina in enumerate(paginas, start=1):
        pagina.folio = indice_pagina
    return paginas


def _renderizar(ctx: IndiceCtx) -> list[PaginaRender]:
    """Produce el Modelo_Paginas completo para un contexto de indice dado.

    Concatena el catalogo (`contenido.concatenar`) y, si hay entradas de indice
    y el contexto reserva paginas para el, inserta el bloque del indice justo
    despues del primer capitulo (la portada) usando `ctx.folios`. Renumera los
    folios de forma consecutiva desde 1 para que el paginador de dos pasadas
    compare conteos y folios estables entre pasadas.
    """
    base = contenido.concatenar(folio_inicial=1)
    entradas = _entradas_indice(base)
    if not entradas or ctx.paginas <= 0:
        return _renumerar(base)

    paginas_indice = _plantilla_indice(
        DatosIndice(entradas=entradas, folios=ctx.folios)
    )
    render_indice = [
        PaginaRender(
            folio=0,
            capitulo_id="_indice",
            capitulo_titulo="Indice",
            plantilla=Plantilla.INDICE,
            elementos=pagina.elementos,
            anotaciones=pagina.anotaciones,
        )
        for pagina in paginas_indice
    ]

    # Inserta el indice tras las paginas del primer capitulo (la portada).
    primer_cap = base[0].capitulo_id if base else ""
    corte = 0
    while corte < len(base) and base[corte].capitulo_id == primer_cap:
        corte += 1
    ensamblado = base[:corte] + render_indice + base[corte:]
    return _renumerar(ensamblado)


def _paginar() -> list[PaginaRender]:
    """Pagina el documento con el indice de dos pasadas y devuelve el modelo."""
    base = contenido.concatenar(folio_inicial=1)
    entradas = _entradas_indice(base)
    paginacion = paginar_con_indice(entradas, _renderizar)
    return paginacion.paginas


# --------------------------------------------------------------------------- #
# Validaciones que se ejecutan siempre
# --------------------------------------------------------------------------- #


def _validar_esquema() -> int:
    """Valida el esquema del Catalogo_JSON y devuelve el numero de fichas.

    Las fichas provienen del `Catalogo_JSON` via el adaptador
    `schema_json.ficha_json_a_ficha`; su esquema de entrada se valida al cargar
    el catalogo (`cargar_catalogo` dentro de `cap10_fundamentos.fichas_json`),
    que lanza `E_JSON_NO_PARSEA` / `E_FICHA_JSON_INVALIDA` ante cualquier campo
    faltante o `tipo` de Media_Item fuera del conjunto permitido.
    """
    crudas = cap10_fundamentos.fichas_json()
    return len(crudas)


def _validar_codificacion(paginas: list[PaginaRender]) -> None:
    """Comprueba que todo el texto del modelo es codificable en WinAnsi.

    Recorre encabezados/pies y el payload de cada elemento de texto, tabla y QR,
    y los pasa por `afm.codificar_winansi`, que convierte un caracter fuera de
    WinAnsi en `E_CARACTER_NO_CODIFICABLE` con el caracter, su code point y su
    posicion (Req 2.3, 10.4). Los motores repiten esta codificacion al escribir;
    hacerla aqui detecta el problema antes de tocar el disco.
    """
    for pagina in paginas:
        for texto in (pagina.capitulo_titulo, pagina.titulo_ficha):
            if texto:
                afm.codificar_winansi(texto, ctx="encabezado de pagina")
        for elem in pagina.elementos:
            datos = elem.datos
            if elem.tipo in (TipoElemento.TEXTO, TipoElemento.PARRAFO):
                texto = getattr(datos, "texto", None)
                if texto:
                    afm.codificar_winansi(texto, ctx="texto de pagina")
            elif elem.tipo is TipoElemento.TABLA:
                for celda in getattr(datos, "celdas", ()):  # type: ignore[union-attr]
                    afm.codificar_winansi(str(celda), ctx="celda de tabla")
            elif elem.tipo is TipoElemento.QR:
                url = getattr(datos, "url", None)
                if url:
                    afm.codificar_winansi(url, ctx="uri de qr")
        for anot in pagina.anotaciones:
            afm.codificar_winansi(anot.uri, ctx="uri de anotacion")


def _validar_qr(fichas: tuple[object, ...]) -> int:
    """Genera y verifica (round-trip) el QR de cada ficha con video.

    Codifica la URL con `qr.codificar`, la re-decodifica con el decodificador
    independiente (`qr_decode`) y exige que reproduzca la URL de origen; si no,
    `verificar_qr` lanza `E_QR_NO_VERIFICA` con el id de la ficha (Req 9.7, 9.8).
    Devuelve cuantos QR se verificaron.
    """
    verificados = 0
    for ficha in fichas:
        url = getattr(ficha, "video_url", None)
        if not url:
            continue
        matriz = qr.codificar(url)
        qr_decode.verificar_qr(url, matriz, id_ficha=getattr(ficha, "id", "") or "")
        verificados += 1
    return verificados


def _validar_rotacion(fichas: tuple[object, ...], *, n_bloques: int) -> int:
    """Genera el Plan_Rotacion y verifica su unicidad de forma independiente.

    Usa `rotacion.generar_plan` (determinista, semilla fija) y luego
    `verify_rotacion.verificar_unicidad`, que **recalcula** las firmas desde los
    bloques emitidos (no desde la memoria del generador) y lanza
    `E_ROTACION_DUPLICADA` si dos bloques comparten combinacion (Req 5.10, 5.4).
    Devuelve el numero de bloques del plan.
    """
    plan = rotacion.generar_plan(
        list(fichas), n_bloques=n_bloques, semilla=SEMILLA_ROTACION
    )
    verify_rotacion.verificar_unicidad(plan.bloques)
    return len(plan.bloques)


def _contar_diagramas(paginas: list[PaginaRender]) -> int:
    """Cuenta los elementos de tipo DIAGRAMA colocados en el modelo."""
    return sum(
        1
        for pagina in paginas
        for elem in pagina.elementos
        if elem.tipo is TipoElemento.DIAGRAMA
    )


def _contar_diagramas_svg(presentes: frozenset[str]) -> int:
    """Diagrama_Postura que se rinden con el Generador_SVG (criterio 5.11).

    Delega la decision en `diagramas_postura.modo_render`, que es la unica
    funcion que elige entre Archivo_Diagrama y SVG, de modo que este conteo y el
    contenido grafico del sitio no puedan discrepar.
    """
    return sum(
        1
        for diagrama in diagramas_postura.CATALOGO
        if diagramas_postura.modo_render(diagrama, presentes)
        == diagramas_postura.MODO_SVG
    )


def _fases_omitidas() -> tuple[tuple[str, int], ...]:
    """Fase_Numerada no emitibles de todo el catalogo (criterio 14.17).

    Concatena `svg_postura.omisiones_de_fase` en el orden del catalogo. Nunca
    lanza: una fase que no cabe degrada y queda enumerada en el reporte.
    """
    omitidas: list[tuple[str, int]] = []
    for diagrama in diagramas_postura.CATALOGO:
        omitidas.extend(svg_postura.omisiones_de_fase(diagrama))
    return tuple(omitidas)


# --------------------------------------------------------------------------- #
# Escritura atomica de artefactos desde dist/.tmp/
# --------------------------------------------------------------------------- #


def _escribir_pdf_atomico(
    paginas: list[PaginaRender],
    dir_dist: str,
    dir_tmp: str,
    *,
    comprimir: bool,
) -> str:
    """Escribe el PDF en `dist/.tmp/` y lo mueve con `os.replace` a `dist/`.

    Verifica el PDF temporal (`verify_pdf`) y el PDF de control **antes** de
    publicarlo, de modo que un archivo corrupto nunca reemplaza al anterior.
    Devuelve la ruta final del PDF publicado.
    """
    tmp = os.path.join(dir_tmp, NOMBRE_PDF)
    build_pdf.escribir_pdf(paginas, tmp, comprimir=comprimir, titulo=_TITULO_DOC)
    verify_pdf.verificar_archivo(tmp, paginas_esperadas=len(paginas))
    verify_pdf.verificar_control()
    final = os.path.join(dir_dist, NOMBRE_PDF)
    os.replace(tmp, final)  # atomico y sobrescribe en Windows (a diferencia de rename)
    return final


def _escribir_laminas_atomico(
    dir_dist: str,
    dir_tmp: str,
    *,
    comprimir: bool,
) -> tuple[str, int]:
    """Escribe `laminas.pdf` (vertical de telefono) en `dist/.tmp/` y lo publica.

    Genera las laminas verticales desde el Catalogo_JSON (una por ficha),
    reutilizando la plantilla `lamina_vertical`, verifica el PDF temporal con
    `verify_pdf.verificar_archivo` (que acepta el `/MediaBox` real de cada
    pagina, no A4) y lo mueve con `os.replace` a `dist/`. Devuelve la ruta final
    y el numero de laminas emitidas.
    """
    tmp = os.path.join(dir_tmp, NOMBRE_LAMINAS)
    paginas = build_laminas.escribir(tmp, comprimir=comprimir)
    verify_pdf.verificar_archivo(tmp, paginas_esperadas=len(paginas))
    final = os.path.join(dir_dist, NOMBRE_LAMINAS)
    os.replace(tmp, final)
    return final, len(paginas)


def _copiar_json_atomico(dir_dist: str, dir_tmp: str) -> str:
    """Copia el Catalogo_JSON crudo a `dist/ejercicios.json` de forma atomica.

    El Target_Web enlaza al JSON crudo con una ruta relativa (`ejercicios.json`)
    para su descarga (Req 13.1). El archivo fuente vive en
    `contenido/ejercicios.json` (fuera de `dist/`), asi que se copia a `dist/`
    escribiendo primero en `dist/.tmp/` y moviendo con `os.replace` (atomico y
    sobrescribe en Windows). Devuelve la ruta final del JSON publicado.
    """
    origen = cap10_fundamentos.ruta_catalogo()
    tmp = os.path.join(dir_tmp, NOMBRE_JSON)
    shutil.copyfile(origen, tmp)
    final = os.path.join(dir_dist, NOMBRE_JSON)
    os.replace(tmp, final)
    return final


def _escribir_web_atomico(
    paginas: list[PaginaRender],
    dir_dist: str,
    dir_tmp: str,
    *,
    pdf_ruta: str,
) -> str:
    """Escribe el sitio HTML en `dist/.tmp/web/` y lo publica con `os.replace`.

    Genera el sitio completo (index + un HTML por capitulo + estilo.css) en el
    temporal, banda de descarga apuntando al PDF ya publicado, y luego reemplaza
    `dist/web/` de forma atomica. Devuelve la ruta del `index.html` publicado.
    """
    tmp_web = os.path.join(dir_tmp, NOMBRE_WEB)
    if os.path.isdir(tmp_web):
        shutil.rmtree(tmp_web)
    os.makedirs(tmp_web, exist_ok=True)
    build_html.escribir_html(
        paginas,
        tmp_web,
        titulo=_TITULO_DOC,
        pdf_href=PDF_HREF_WEB,
        pdf_ruta=pdf_ruta,
    )
    final = os.path.join(dir_dist, NOMBRE_WEB)
    if os.path.isdir(final):
        shutil.rmtree(final)
    os.replace(tmp_web, final)
    return os.path.join(final, "index.html")


# --------------------------------------------------------------------------- #
# Assets de los Diagrama_Postura: firma por extension y copia atomica
# --------------------------------------------------------------------------- #


def dir_assets_dist(dir_dist: str) -> str:
    """Directorio de publicacion de los assets dentro de `dir_dist`.

    No lo crea: el build estricto sin ningun Archivo_Diagrama presente no debe
    dejar `dist/assets/` creado y vacio, asi que el directorio se crea solo
    cuando hay una copia que publicar.
    """
    return os.path.join(dir_dist, *NOMBRE_ASSETS.split("/"))


def firma_esperada(extension: str) -> tuple[str, ...]:
    """Tokens de firma declarados para `extension` (criterio 5.12).

    La extension se compara en minusculas, igual que en el Validador_Rutas. Una
    extension sin firma declarada es un error de build, no un caso a ignorar:
    lanza `ErrorAsset(E_ASSET_INVALIDO)` nombrando la extension.
    """
    clave: str = extension.lower()
    firmas: tuple[str, ...] | None = FIRMAS.get(clave)
    if firmas is None:
        raise ErrorAsset(
            f"no hay firma declarada para la extension {clave!r}; las "
            f"declaradas son {tuple(FIRMAS)}",
            detalle={"extension": clave, "declaradas": tuple(FIRMAS)},
            codigo=E_ASSET_INVALIDO,
        )
    return firmas


def _literal_a_bytes(literal: str) -> bytes:
    """Bytes que representa el literal de un token de `FIRMAS`.

    Un literal de longitud par formado solo por digitos hexadecimales son bytes
    en hexadecimal (`89504E47` -> `b"\\x89PNG"`); cualquier otro literal es
    texto ASCII (`RIFF`, `WEBP`, `ftyp`, `<svg`). Ninguno de los literales ASCII
    declarados es ambiguo: todos llevan al menos un caracter que no es un digito
    hexadecimal.
    """
    if len(literal) >= 2 and len(literal) % 2 == 0:
        if all(caracter in _HEXDIGITOS for caracter in literal):
            return bytes.fromhex(literal)
    try:
        return literal.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ErrorAsset(
            f"el literal {literal!r} de un token de FIRMAS no es ASCII",
            detalle={"literal": literal},
            codigo=E_ASSET_INVALIDO,
        ) from exc


def _partes_token(token: str) -> tuple[bytes, int, int | None]:
    """Descompone un token de `FIRMAS` en `(bytes, inicio, fin)`.

    `fin` es `None` cuando el token exige coincidencia exacta en `inicio`, y el
    limite de la ventana cuando el token exige que el literal aparezca en algun
    punto de `datos[inicio:fin]`. Un token mal formado lanza
    `ErrorAsset(E_ASSET_INVALIDO)` nombrando el token.
    """
    literal, separador, posicion = token.partition("@")
    if not literal or not separador or not posicion:
        raise ErrorAsset(
            f"token de firma mal formado: {token!r}; se espera "
            "LITERAL@INICIO o LITERAL@INICIO:FIN",
            detalle={"token": token},
            codigo=E_ASSET_INVALIDO,
        )
    esperado: bytes = _literal_a_bytes(literal)
    if ":" in posicion:
        inicio_txt, _, fin_txt = posicion.partition(":")
        if not inicio_txt.isdigit() or not fin_txt.isdigit():
            raise ErrorAsset(
                f"token de firma con ventana no numerica: {token!r}",
                detalle={"token": token},
                codigo=E_ASSET_INVALIDO,
            )
        return esperado, int(inicio_txt), int(fin_txt)
    if not posicion.isdigit():
        raise ErrorAsset(
            f"token de firma con desplazamiento no numerico: {token!r}",
            detalle={"token": token},
            codigo=E_ASSET_INVALIDO,
        )
    return esperado, int(posicion), None


def _cumple_token(datos: bytes, token: str) -> bool:
    """`True` si `datos` satisface un token de firma."""
    esperado, inicio, fin = _partes_token(token)
    if fin is None:
        return datos[inicio : inicio + len(esperado)] == esperado
    return esperado in datos[inicio:fin]


def cumple_firma(datos: bytes, extension: str) -> bool:
    """`True` si los primeros bytes `datos` cumplen la firma de `extension`.

    Implementa el criterio 5.12 sobre los bytes ya leidos de la **copia**:
    `RIFF` en 0..3 con `WEBP` en 8..11 para `.webp`, los bytes `89 50 4E 47` al
    inicio para `.png`, `ftyp` en 4..7 para `.avif` y la subcadena `<svg` dentro
    de los primeros 512 bytes para `.svg`. Devuelve un booleano: quien decide
    abortar es `_copiar_assets_atomico`, que es el que sabe que archivo nombrar.
    """
    return all(_cumple_token(datos, token) for token in firma_esperada(extension))


def _borrar_copia(ruta: str) -> None:
    """Borra una copia temporal sin propagar el fallo de borrado.

    Se usa en el camino de error: lo que importa es que la copia invalida no se
    publique. Si el borrado falla, el `ErrorAsset` original sigue siendo el que
    aborta el build y no se pierde el diagnostico.
    """
    try:
        os.remove(ruta)
    except OSError:
        pass


def _leer_cabecera(ruta: str) -> bytes:
    """Primeros `BYTES_FIRMA` bytes de `ruta`, envolviendo el `OSError`."""
    try:
        with open(ruta, "rb") as fh:
            return fh.read(BYTES_FIRMA)
    except OSError as exc:
        raise ErrorAsset(
            f"no se pudo leer la copia del asset {ruta}: {exc}",
            detalle={"ruta": ruta, "error": str(exc)},
            codigo=E_ASSET_FALTANTE,
        ) from exc


def _copiar_assets_atomico(
    dir_dist: str,
    dir_tmp: str,
    *,
    estricto: bool,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Copia cada Archivo_Diagrama declarado a `dist/.tmp/`, lo valida y publica.

    Recorre **solo** las entradas del `Catalogo_Diagramas` (criterio 5.14): un
    archivo que este en `assets/img/tecnica/` sin estar declarado se ignora por
    completo. Para cada entrada:

    1. pasa su ruta relativa por `diagramas_postura.ruta_aceptable`, que es la
       unica funcion que decide si una ruta de asset es publicable (Requisito
       30), y por tanto la extension nunca se vuelve a mirar aqui;
    2. si el archivo fuente no existe, lo registra como faltante; en Modo_Estricto
       y con Requiere_Archivo en verdadero aborta con `E_ASSET_FALTANTE` y la
       ruta relativa en el mensaje (criterio 5.8). Con Requiere_Archivo en falso
       el build sigue en cualquier modo (criterios 5.9 y 5.10) y el diagrama se
       rinde con el Generador_SVG;
    3. lo copia a `dist/.tmp/` y comprueba la firma **sobre la copia** antes de
       publicarla (criterios 5.12 y 30.10). Una firma que no corresponde a la
       extension aborta en cualquier modo con `E_ASSET_INVALIDO` nombrando el
       archivo, y la copia temporal se borra sin publicarse (criterio 5.13);
    4. publica con `os.replace` en `dist/assets/img/tecnica/`, que es atomico y
       sobrescribe tambien en Windows (criterio 5.7).

    Devuelve `(copiados, faltantes)`, las dos como tuplas de rutas relativas en
    el orden del catalogo. Cualquier `OSError` de la copia, de la lectura o de la
    publicacion se envuelve en `ErrorAsset` con la ruta afectada en el detalle.
    El directorio de publicacion se crea solo cuando hay algo que publicar, para
    que un build sin ningun asset no deje `dist/assets/` creado y vacio.
    """
    copiados: list[str] = []
    faltantes: list[str] = []
    destino_dir: str = dir_assets_dist(dir_dist)

    for diagrama in diagramas_postura.CATALOGO:
        relativa: str = diagramas_postura.ruta_relativa(diagrama)
        # Unica autoridad sobre la ruta: aborta con ErrorAsset si no es aceptable.
        diagramas_postura.ruta_aceptable(relativa)

        origen: str = diagramas_postura.ruta_fuente(diagrama)
        if not os.path.isfile(origen):
            if estricto and diagrama.requiere_archivo:
                raise ErrorAsset(
                    f"falta el Archivo_Diagrama {relativa} de "
                    f"{diagrama.id}, que esta marcado Requiere_Archivo, y el "
                    "build corre en modo estricto",
                    detalle={
                        "id": diagrama.id,
                        "ruta": relativa,
                        "modo": MODO_ESTRICTO,
                    },
                    codigo=E_ASSET_FALTANTE,
                )
            faltantes.append(relativa)
            continue

        tmp_asset: str = os.path.join(dir_tmp, diagrama.archivo)
        try:
            os.makedirs(dir_tmp, exist_ok=True)
            shutil.copyfile(origen, tmp_asset)
        except OSError as exc:
            _borrar_copia(tmp_asset)
            raise ErrorAsset(
                f"no se pudo copiar el Archivo_Diagrama {relativa} a "
                f"{tmp_asset}: {exc}",
                detalle={
                    "id": diagrama.id,
                    "ruta": relativa,
                    "origen": origen,
                    "destino": tmp_asset,
                    "error": str(exc),
                },
                codigo=E_ASSET_FALTANTE,
            ) from exc

        extension: str = os.path.splitext(diagrama.archivo)[1].lower()
        cabecera: bytes = _leer_cabecera(tmp_asset)
        if not cumple_firma(cabecera, extension):
            _borrar_copia(tmp_asset)
            raise ErrorAsset(
                f"la copia de {diagrama.archivo} no cumple la firma de su "
                f"extension {extension!r}: se esperaba "
                f"{firma_esperada(extension)}",
                detalle={
                    "id": diagrama.id,
                    "archivo": diagrama.archivo,
                    "ruta": relativa,
                    "extension": extension,
                    "firma_esperada": firma_esperada(extension),
                },
                codigo=E_ASSET_INVALIDO,
            )

        final: str = os.path.join(destino_dir, diagrama.archivo)
        try:
            os.makedirs(destino_dir, exist_ok=True)
            os.replace(tmp_asset, final)
        except OSError as exc:
            _borrar_copia(tmp_asset)
            raise ErrorAsset(
                f"no se pudo publicar el Archivo_Diagrama {relativa} en "
                f"{final}: {exc}",
                detalle={
                    "id": diagrama.id,
                    "ruta": relativa,
                    "destino": final,
                    "error": str(exc),
                },
                codigo=E_ASSET_FALTANTE,
            ) from exc
        copiados.append(relativa)

    return tuple(copiados), tuple(faltantes)


# --------------------------------------------------------------------------- #
# Cobertura (solo modo estricto)
# --------------------------------------------------------------------------- #

#: Etiquetas de las validaciones de publicacion que el modo muestra omite.
#: Reflejan los umbrales REVISADOS (100 paginas, 45-60 fichas, 12 semanas), no
#: los antiguos (120 / 200-300 / etc.).
_UMBRALES_OMITIDOS_MUESTRA: tuple[str, ...] = (
    f"paginas>={MIN_PAGINAS_PUBLICABLE}",
    f"fichas en [{MIN_FICHAS_PUBLICABLE}, {MAX_FICHAS_PUBLICABLE}]",
    f"bloques (semanas)>={MIN_BLOQUES_PUBLICABLE}",
)


def _exigir_cobertura(
    *, fichas: int, bloques: int, paginas: int
) -> None:
    """Exige los umbrales de publicacion REVISADOS (solo en modo estricto).

    Un build es publicable cuando cumple los tres umbrales aprobados por el
    usuario: `paginas >= 100`, `45 <= fichas <= 60` y `bloques (semanas) >= 12`.
    Cualquier incumplimiento lanza `E_COBERTURA_MINIMA` nombrando la coleccion
    afectada (se reutiliza `exigir_minimo`, que ya emite ese codigo).

    El limite superior de fichas se expresa como `exigir_minimo("fichas_max",
    MAX, fichas)`: falla cuando `MAX < fichas`, es decir cuando hay mas fichas
    de las permitidas. Es el mismo patron que usaba el limite superior de
    paginas.
    """
    # Cota inferior y superior de fichas (45..60).
    exigir_minimo("fichas", fichas, MIN_FICHAS_PUBLICABLE)
    exigir_minimo("fichas_max", MAX_FICHAS_PUBLICABLE, fichas)
    # Bloques (semanas) >= 12.
    exigir_minimo("bloques", bloques, MIN_BLOQUES_PUBLICABLE)
    # Paginas >= 100 (minimo revisado), con la cota de sanidad superior.
    minimo, maximo = RANGO_PAGINAS_PUBLICABLE
    exigir_minimo("paginas", paginas, minimo)
    if paginas > maximo:
        # Reutiliza el codigo de cobertura para el limite superior de paginas.
        exigir_minimo("paginas_max", maximo, paginas)


# --------------------------------------------------------------------------- #
# Guardarrail de fuente unica de fichas (Req 15.2, 15.4)
# --------------------------------------------------------------------------- #

#: Un modulo de contenido es de capitulo si su nombre empieza por `cap` seguido
#: de digitos (p.ej. `cap00_portada.py`, `cap10_fundamentos.py`).
_PATRON_MODULO_CAP: re.Pattern[str] = re.compile(r"^cap\d+.*\.py$")

#: Nombre de la clase de ficha que los modulos de capitulo NO pueden construir.
_NOMBRE_FICHA: str = "FichaEjercicio"


def _dir_contenido() -> str:
    """Directorio del paquete `guia.contenido` (donde viven los `capNN_*.py`)."""
    return os.path.dirname(os.path.abspath(contenido.__file__))


def _modulos_capitulo(dir_contenido: str) -> list[str]:
    """Rutas de los modulos `capNN_*.py` de un directorio, en orden estable."""
    nombres = [
        nombre
        for nombre in os.listdir(dir_contenido)
        if _PATRON_MODULO_CAP.match(nombre)
    ]
    nombres.sort()
    return [os.path.join(dir_contenido, nombre) for nombre in nombres]


def _construye_ficha(arbol: ast.AST) -> bool:
    """`True` si el AST contiene una llamada que construye una `FichaEjercicio`.

    Reconoce tanto `FichaEjercicio(...)` (nombre directo) como
    `algo.FichaEjercicio(...)` (acceso por atributo). Cargar fichas desde el
    Catalogo_JSON con `ficha_json_a_ficha(...)` NO cuenta: ese adaptador vive en
    `schema_json`, no en el modulo de capitulo, y aqui solo se ve su llamada por
    nombre (`ficha_json_a_ficha`), no una construccion literal de la dataclass.
    """
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        func = nodo.func
        if isinstance(func, ast.Name) and func.id == _NOMBRE_FICHA:
            return True
        if isinstance(func, ast.Attribute) and func.attr == _NOMBRE_FICHA:
            return True
    return False


def verificar_sin_fichas_en_modulos(
    dir_contenido: str | None = None,
) -> tuple[str, ...]:
    """Verifica que ningun modulo `capNN_*.py` construya una `FichaEjercicio`.

    Guardarrail de fuente unica (Req 15.2, 15.4): las Ficha_Ejercicio viven solo
    en el Catalogo_JSON (`contenido/ejercicios.json`), no incrustadas en modulos
    de contenido. Se inspecciona cada modulo de capitulo por **AST estatico**
    (sin importarlo ni ejecutarlo) buscando una construccion literal de
    `FichaEjercicio`. Si la halla, lanza `E_FICHA_EN_MODULO` nombrando el modulo
    infractor; en caso contrario devuelve la tupla de modulos revisados.

    `cap10_fundamentos` carga desde JSON via `ficha_json_a_ficha(...)` (permitido)
    y por tanto pasa el guardarrail; solo se rechaza construir `FichaEjercicio`
    literalmente dentro del modulo de capitulo.
    """
    raiz = _dir_contenido() if dir_contenido is None else dir_contenido
    revisados: list[str] = []
    for ruta in _modulos_capitulo(raiz):
        nombre = os.path.basename(ruta)
        with open(ruta, encoding="utf-8") as fh:
            fuente = fh.read()
        arbol = ast.parse(fuente, filename=nombre)
        if _construye_ficha(arbol):
            raise ErrorFuenteFichas(
                f"el modulo de contenido {nombre} construye una "
                f"{_NOMBRE_FICHA}; las fichas viven solo en el Catalogo_JSON "
                "(Req 15.2, 15.4)",
                detalle={"modulo": nombre, "codigo": E_FICHA_EN_MODULO},
            )
        revisados.append(nombre)
    return tuple(revisados)


# --------------------------------------------------------------------------- #
# Orquestacion programatica
# --------------------------------------------------------------------------- #


def construir(
    *,
    modo: str = MODO_MUESTRA,
    dir_dist: str | None = None,
    comprimir: bool = True,
    con_preflight: bool = True,
) -> Reporte:
    """Ejecuta el pipeline completo y devuelve un `Reporte`.

    Fases: preflight -> esquema del catalogo -> paginacion con indice de dos
    pasadas -> codificacion WinAnsi -> Plan_Rotacion + unicidad -> QR round-trip
    -> PDF + verificacion estructural + PDF de control -> HTML -> copia de los
    Archivo_Diagrama con firma por extension -> sitio autocontenido -> escritura
    atomica con `os.replace` desde `dist/.tmp/`. En modo estricto ademas exige
    los umbrales de cobertura y el rango de paginas publicable.

    Lanza `ErrorBuild` (o subclase) ante cualquier fallo; no captura nada (eso
    lo hace `main`).
    """
    if modo not in (MODO_MUESTRA, MODO_ESTRICTO):
        # Precondicion de API: un modo desconocido es un error de programacion.
        raise ValueError(f"modo desconocido: {modo!r}")

    dir_dist = dir_dist_por_defecto() if dir_dist is None else dir_dist
    dir_tmp = os.path.join(dir_dist, ".tmp")
    os.makedirs(dir_dist, exist_ok=True)
    os.makedirs(dir_tmp, exist_ok=True)

    tiempos: dict[str, float] = {}
    reloj_total = time.perf_counter()

    # Fase 1: preflight de entorno (Req 2.2, 2.8, 2.9).
    version_python = ".".join(str(n) for n in sys.version_info[:3])
    if con_preflight:
        t0 = time.perf_counter()
        reporte_pre = preflight.ejecutar(silencioso=True)
        version_python = reporte_pre.version_python
        tiempos["preflight"] = time.perf_counter() - t0

    # Fase 2: esquema del Catalogo_JSON (siempre).
    t0 = time.perf_counter()
    n_fichas = _validar_esquema()
    fichas = cap10_fundamentos.fichas()
    tiempos["esquema"] = time.perf_counter() - t0

    # Fase 2c: en modo estricto, el gate de fichas (45..60) se comprueba ANTES
    # de la rotacion estricta (>=26 bloques), que con pocas fichas fallaria con
    # E_ROTACION_SIN_COMBINACION antes de llegar al gate de cobertura. Asi un
    # catalogo insuficiente (15 fichas) se rechaza con E_COBERTURA_MINIMA
    # nombrando la coleccion 'fichas', que es el fallo semanticamente correcto.
    if modo == MODO_ESTRICTO:
        exigir_minimo("fichas", n_fichas, MIN_FICHAS_PUBLICABLE)
        exigir_minimo("fichas_max", MAX_FICHAS_PUBLICABLE, n_fichas)

    # Fase 2b: guardarrail de fuente unica (Req 15.2, 15.4). Ningun modulo
    # `capNN_*.py` puede construir una FichaEjercicio; las fichas viven solo en
    # el Catalogo_JSON. Falla con E_FICHA_EN_MODULO ante un modulo infractor.
    t0 = time.perf_counter()
    verificar_sin_fichas_en_modulos()
    tiempos["guardarrail_fichas"] = time.perf_counter() - t0

    # Fase 3: paginacion con indice de dos pasadas (Req 1.2, 10.3).
    t0 = time.perf_counter()
    paginas = _paginar()
    tiempos["paginacion"] = time.perf_counter() - t0

    # Fase 4: codificacion WinAnsi de todo el texto (Req 2.3, 10.4).
    t0 = time.perf_counter()
    _validar_codificacion(paginas)
    tiempos["codificacion"] = time.perf_counter() - t0

    # Fase 5: Plan_Rotacion + unicidad independiente (Req 5.4, 5.10).
    t0 = time.perf_counter()
    n_bloques_objetivo = (
        N_BLOQUES_ESTRICTO if modo == MODO_ESTRICTO else N_BLOQUES_MUESTRA
    )
    n_bloques = _validar_rotacion(fichas, n_bloques=n_bloques_objetivo)
    tiempos["rotacion"] = time.perf_counter() - t0

    # Fase 6: QR round-trip (Req 9.7, 9.8).
    t0 = time.perf_counter()
    n_qr = _validar_qr(fichas)
    tiempos["qr"] = time.perf_counter() - t0

    # Fase 7: PDF del Target_PDF_Guia (una ficha por hoja) + verificacion
    # estructural + PDF de control (Req 2.1, 10.4/5, 12.5). `dist/guia.pdf` usa
    # el formato "una ficha por hoja" (Diagrama_Cancha + dosis + rejilla de QR
    # por Media_Item, verificados offline), no el modelo de la guia extensa.
    t0 = time.perf_counter()
    guia_paginas = build_guia_pdf.modelo()
    ruta_pdf = _escribir_pdf_atomico(guia_paginas, dir_dist, dir_tmp, comprimir=comprimir)
    tiempos["pdf"] = time.perf_counter() - t0

    # Fase 7b: laminas verticales para telefono/WhatsApp (Target_Laminas,
    # Req 12.6) -> dist/laminas.pdf. Una lamina por ficha, formato retrato de
    # telefono (9:16, NO A4), reutilizando la plantilla `lamina_vertical`. Se
    # verifica estructuralmente con verify_pdf (que acepta el MediaBox real) y
    # se publica con escritura atomica desde dist/.tmp/.
    t0 = time.perf_counter()
    ruta_laminas, n_laminas = _escribir_laminas_atomico(
        dir_dist, dir_tmp, comprimir=comprimir
    )
    tiempos["laminas"] = time.perf_counter() - t0

    # Fase 8: HTML estatico (Req 2.1, 2.4, 2.5, 2.7).
    t0 = time.perf_counter()
    ruta_web_index = _escribir_web_atomico(
        paginas, dir_dist, dir_tmp, pdf_ruta=ruta_pdf
    )
    tiempos["html"] = time.perf_counter() - t0

    # Fase 8b: Archivo_Diagrama a `dist/assets/img/tecnica/` (Req 5.6 a 5.14).
    # Va ANTES de emitir el sitio: el Target_Web referencia estas rutas
    # relativas, asi que los assets estan publicados cuando el HTML aparece. En
    # Modo_Estricto un faltante marcado Requiere_Archivo aborta; con
    # `requiere_archivo=False` en las ocho entradas el build sigue y el diagrama
    # se rinde con el Generador_SVG. La firma se valida sobre la copia temporal.
    t0 = time.perf_counter()
    copiados, assets_faltantes = _copiar_assets_atomico(
        dir_dist, dir_tmp, estricto=(modo == MODO_ESTRICTO)
    )
    tiempos["assets"] = time.perf_counter() - t0

    # Fase 9: sitio de un solo archivo autocontenido (Addendum A, Target_Web).
    # Emite `dist/index.html` (las 15 fichas reales del Catalogo_JSON con la
    # estetica oscura congelada) ADEMAS del `dist/web/` multi-archivo anterior.
    t0 = time.perf_counter()
    ruta_sitio = build_site.escribir_sitio(dir_dist=dir_dist)
    tiempos["sitio"] = time.perf_counter() - t0

    # Fase 9b: copia del Catalogo_JSON crudo a `dist/ejercicios.json` para que
    # el boton de descarga del Target_Web (Req 13.1) tenga un destino relativo.
    t0 = time.perf_counter()
    ruta_json = _copiar_json_atomico(dir_dist, dir_tmp)
    tiempos["json"] = time.perf_counter() - t0

    diagramas = _contar_diagramas(paginas)
    posturas = sum(1 for f in fichas if getattr(f, "postura", None) is not None)
    capitulos = len({p.capitulo_id for p in paginas})

    # Degradaciones registradas del Catalogo_Diagramas: cada una alimenta una
    # linea del reporte y ninguna aborta el build (criterios 3.9, 5.11, 14.17,
    # 18.9).
    diagramas_svg = _contar_diagramas_svg(diagramas_postura.presentes())
    fases_omitidas = _fases_omitidas()
    creditos_pendientes = diagramas_postura.campos_pendientes()
    fundamentos_omitidos = build_site.fundamentos_omitidos()

    publicable = False
    umbrales_omitidos: tuple[str, ...] = _UMBRALES_OMITIDOS_MUESTRA
    if modo == MODO_ESTRICTO:
        _exigir_cobertura(
            fichas=n_fichas, bloques=n_bloques, paginas=len(paginas)
        )
        publicable = True
        umbrales_omitidos = ()

    tiempos["total"] = time.perf_counter() - reloj_total

    validaciones = (
        "preflight" if con_preflight else "preflight(omitido)",
        "esquema_json",
        "sin_fichas_en_modulos",
        "codificacion_winansi",
        "unicidad_rotacion",
        "qr_round_trip",
        "verify_pdf",
        "pdf_control",
        "indice_coherente",
        "sitio_un_archivo",
        "guia_una_ficha_por_hoja",
        "laminas_vertical",
        "json_crudo_dist",
        "firma_assets",
    )

    return Reporte(
        modo=modo,
        publicable=publicable,
        paginas_totales=len(guia_paginas),
        fichas=n_fichas,
        bloques=n_bloques,
        qr=n_qr,
        posturas=posturas,
        diagramas=diagramas,
        capitulos=capitulos,
        version_python=version_python,
        tiempos=tiempos,
        umbrales_omitidos=umbrales_omitidos,
        validaciones=validaciones,
        ruta_pdf=ruta_pdf,
        ruta_web_index=ruta_web_index,
        ruta_sitio=ruta_sitio,
        laminas=n_laminas,
        ruta_laminas=ruta_laminas,
        ruta_json=ruta_json,
        paginas_modelo=len(paginas),
        assets_copiados=len(copiados),
        assets_faltantes=assets_faltantes,
        diagramas_svg=diagramas_svg,
        fases_omitidas=fases_omitidas,
        creditos_pendientes=creditos_pendientes,
        fundamentos_omitidos=fundamentos_omitidos,
    )


# --------------------------------------------------------------------------- #
# Interfaz de linea de comandos
# --------------------------------------------------------------------------- #


def _parsear_argv(argv: list[str]) -> argparse.Namespace:
    """Parsea los argumentos del orquestador."""
    parser = argparse.ArgumentParser(
        prog="guia.build",
        description=(
            "Construye la Guia Extensa Sub-17 (PDF + sitio HTML). Por defecto "
            "corre en MODO MUESTRA: pipeline y validaciones estructurales, sin "
            "los umbrales de cobertura de publicacion."
        ),
    )
    parser.add_argument(
        "--estricto",
        action="store_true",
        help="exige los umbrales de cobertura y el rango de paginas publicable",
    )
    parser.add_argument(
        "--sin-comprimir",
        action="store_true",
        help="omite zlib en los streams del PDF (marca el build NO_PUBLICABLE)",
    )
    parser.add_argument(
        "--dir",
        dest="dir_dist",
        default=None,
        help="directorio de salida (por defecto guia-sub17/dist)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entrada de linea de comandos del Orquestador_Build.

    Captura `ErrorBuild`, imprime **una** linea en `stderr` y devuelve 1; en
    exito imprime el reporte (paginas, fichas, bloques, QR, tiempos y modo) y
    devuelve 0.
    """
    if argv is None:
        argv = sys.argv[1:]
    args = _parsear_argv(argv)

    modo = MODO_ESTRICTO if args.estricto else MODO_MUESTRA
    try:
        reporte = construir(
            modo=modo,
            dir_dist=args.dir_dist,
            comprimir=not args.sin_comprimir,
        )
    except ErrorBuild as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(reporte.texto())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
