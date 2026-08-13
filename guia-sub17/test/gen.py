"""Generadores de datos de prueba para el motor `for_all` de `test/prop.py`.

Cada generador recibe un PRNG `random.Random` y devuelve un valor listo para
la propiedad. Los valores del dominio se construyen como **dataclasses reales**
(no diccionarios), de modo que el mismo valor sirve al validador de esquema
(`schema.py`) y al paginador (`layout.py`) sin conversión intermedia.

Convenciones del proyecto respetadas aquí:

* Python 3.11+, solo librería estándar. Sin `pip`, sin dependencias externas.
* Nada de `assert` en el código: los invariantes internos se expresan con
  `raise` (los `assert` desaparecen con `python -O`).
* Sin concatenación de strings en bucle: se acumula en `list[str]` y se
  colapsa con `''.join(...)`.
* Type hints y estilo idiomático de la stdlib.

Dependencia de orden (resuelta): las dataclasses del dominio viven en
`guia.schema` y los specs de diagrama en `guia.diagram_spec`, y los dos módulos
**ya existen** con la forma que este archivo importa. El módulo es por tanto
**importable por sí solo**: basta con `src/` y `test/` en `sys.path` (que es lo
que hace `_run_tests.py`) para que `import gen` termine sin excepción y para que
todos los nombres de `__all__` queden disponibles. Esa es la condición que la
tarea 5.1 de `imagenes-reales-hero-interactivo` fija, porque
`test/test_vistas_figura.py` importa de aquí sus generadores y no arrancaría si
la importación fallara.

El único nombre que todavía apunta a una forma inexistente es
`gen_figura_postura`, que necesita una `guia.diagram_spec.figura(...)` por
parámetros de postura: importa ese nombre **dentro** de la función, de modo que
solo falle quien lo llame y la utilería entera siga siendo importable.
"""

from __future__ import annotations

import dataclasses
import random
import re
from dataclasses import dataclass

# Dataclasses y enums del dominio (schema.py, tarea 1.6).
from guia.schema import (
    MATERIAL_PERMITIDO,
    ClaseDiagrama,
    Dosis,
    FichaEjercicio,
    Montaje,
    Posicion,
    Variante,
)

# Specs de diagrama (diagram_spec.py, tarea 3.1).
from guia.diagram_spec import (
    DiagramaSpec,
    Item,
    Mundo,
)

# `PanelFigura` y la `figura(...)` por parametros de postura (tarea 3.9) NO
# existen hoy en `guia.diagram_spec`: el catalogo de figuras acabo en
# `guia.figuras` con otra forma (`figura(fid)`). `gen_figura_postura` importa
# esos nombres **dentro** de la funcion, de modo que la utileria entera siga
# siendo importable y el resto de los generadores se pueda usar. Solo falla quien
# llame a `gen_figura_postura`, que es lo que ya ocurria antes con todo el
# modulo.

__all__ = [
    "MutacionFicha",
    "gen_catalogo",
    "gen_ficha",
    "gen_ficha_mutada",
    "gen_figura_postura",
    "gen_semilla",
    "gen_spec_diagrama",
    "gen_texto",
    "gen_texto_hostil",
    "gen_url",
    # Feature "imagenes-reales-hero-interactivo" (tarea 1.6).
    "BytesAsset",
    "CatalogoMutado",
    "MutacionLexica",
    "CAMPOS_CREDITO",
    "CONCEPTOS_CABECEO_EXIGIDOS",
    "EXTENSIONES_ASSET",
    "FUNDAMENTOS_CERRADOS",
    "IDS_DIAGRAMA",
    "RESERVADAS_ANCLAS",
    "gen_bytes_asset",
    "gen_campos_credito_ausentes",
    "gen_catalogo_fundamento_ajeno",
    "gen_conceptos_eliminados",
    "gen_cursor_relativo",
    "gen_presentes",
    "gen_progreso",
    "gen_punto_toque",
    "gen_reservadas_registradas",
    "gen_secuencia_progresos",
    "gen_texto_lexico",
    "gen_viewbox",
    # Ampliacion multi-vista del Proyector_Vistas (tarea 5.2).
    "AnguloFueraDeRango",
    "BytesVista",
    "PoseClave",
    "AZIMUTS_DECLARADOS_GEN",
    "AZIMUTS_MOVIL_GEN",
    "BYTES_MAX_VISTA_GEN",
    "CLAVES_VISTA_GEN",
    "ELEVACIONES_DECLARADAS_GEN",
    "IDS_POSE",
    "PASO_AZIMUT",
    "PUNTOS_MEDIOS_AZIMUT",
    "gen_angulo_fuera_de_rango",
    "gen_angulo_giro",
    "gen_azimut_declarado",
    "gen_bytes_vista",
    "gen_desplazamiento_dedo",
    "gen_elevacion_declarada",
    "gen_pose_clave",
    "gen_secuencia_angulos",
    # Validador_Rutas: rutas hostiles y aceptables (tarea 13.7).
    "RutaCandidata",
    "EXTENSIONES_AJENAS",
    "FAMILIAS_RUTA",
    "PREFIJOS_HOSTILES",
    "gen_ruta_hostil",
    # Guardarrail de codigo de los modulos nuevos (tarea 14.3).
    "ViolacionCodigo",
    "FAMILIAS_CODIGO",
    "FAMILIAS_HOSTILES",
    "FAMILIAS_MARCADO",
    "MODULOS_NUEVOS",
    "MODULOS_STDLIB_GEN",
    "PAQUETES_EXTERNOS",
    "gen_violacion_codigo",
    # Ayudantes de extraccion de CSS y de JavaScript (tarea 10.10).
    "Regla",
    "bloques_media",
    "cuerpo_de_funcion",
    "declaraciones",
    "escrituras_de_estilo",
    "reglas",
]

# --------------------------------------------------------------------------- #
# Vocabulario codificable en cp1252 (WinAnsi)
# --------------------------------------------------------------------------- #

# Núcleo de letras seguras en cp1252, con acentos y ñ del español.
_LETRAS: str = "abcdefghijklmnopqrstuvwxyzáéíóúüñ"
_LETRAS_MAY: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ"

# Palabras de muestra con acentos, ñ y signos de apertura del español.
_PALABRAS: tuple[str, ...] = (
    "balón",
    "posición",
    "presión",
    "compañera",
    "técnica",
    "prevención",
    "rodilla",
    "aterrizaje",
    "canonazo",
    "línea",
    "señalización",
    "coordinación",
    "¡vamos!",
    "¿lista?",
    "área",
    "portería",
)

# Caracteres claramente fuera de WinAnsi (cp1252) para textos hostiles. Se
# verifican en tiempo de importación: cualquiera que resulte codificable en
# cp1252 se descarta, para que `gen_texto_hostil` siempre incluya un carácter
# genuinamente no codificable (dispara `E_CARACTER_NO_CODIFICABLE`).
_HOSTILES_CANDIDATOS: str = "中你好日本語λμπΩ✓★→♥☃∑≠∞ก한"


def _no_codificable_cp1252(caracter: str) -> bool:
    """True si `caracter` NO se puede codificar en cp1252 (WinAnsi)."""
    try:
        caracter.encode("cp1252")
    except UnicodeEncodeError:
        return True
    return False


_HOSTILES: tuple[str, ...] = tuple(
    c for c in _HOSTILES_CANDIDATOS if _no_codificable_cp1252(c)
)

if not _HOSTILES:  # invariante de construcción; nunca debería ocurrir
    raise RuntimeError(
        "no hay caracteres hostiles no codificables en cp1252 disponibles"
    )


# --------------------------------------------------------------------------- #
# Generadores de texto
# --------------------------------------------------------------------------- #


def _palabra(rnd: random.Random, *, largo_min: int = 1, largo_max: int = 12) -> str:
    """Palabra sin espacios, codificable en cp1252, de longitud acotada."""
    if rnd.random() < 0.55:
        return rnd.choice(_PALABRAS)
    longitud: int = rnd.randint(largo_min, largo_max)
    letras: list[str] = [rnd.choice(_LETRAS)]
    for _ in range(longitud - 1):
        fuente: str = _LETRAS_MAY if rnd.random() < 0.1 else _LETRAS
        letras.append(rnd.choice(fuente))
    return "".join(letras)


def _palabra_larga(rnd: random.Random) -> str:
    """Token de hasta 40 caracteres sin ningún espacio (caso de envoltura)."""
    longitud: int = rnd.randint(20, 40)
    letras: list[str] = [rnd.choice(_LETRAS) for _ in range(longitud)]
    return "".join(letras)


def gen_texto(rnd: random.Random) -> str:
    """Texto con acentos, ñ, espacios múltiples y palabras largas.

    Todo el contenido es codificable en cp1252 (WinAnsi) por construcción.
    """
    n_palabras: int = rnd.randint(1, 8)
    partes: list[str] = []
    for indice in range(n_palabras):
        if indice > 0:
            # Espacios múltiples ocasionales para ejercitar la normalización.
            partes.append(" " * rnd.randint(1, 3))
        if rnd.random() < 0.15:
            partes.append(_palabra_larga(rnd))
        else:
            partes.append(_palabra(rnd))
    return "".join(partes)


def gen_texto_hostil(rnd: random.Random) -> str:
    """Texto que incluye al menos un carácter fuera de WinAnsi (cp1252).

    Sirve para provocar `E_CARACTER_NO_CODIFICABLE` en la codificación.
    """
    base: str = gen_texto(rnd)
    hostil: str = rnd.choice(_HOSTILES)
    posicion: int = rnd.randint(0, len(base))
    partes: list[str] = [base[:posicion], hostil, base[posicion:]]
    return "".join(partes)


# --------------------------------------------------------------------------- #
# Generador de URLs
# --------------------------------------------------------------------------- #

_URL_ALFABETO: str = "abcdefghijklmnopqrstuvwxyz0123456789-"


def gen_url(rnd: random.Random) -> str:
    """URL http/https válida de 20 a 180 bytes (capacidad de QR v1–6 nivel L)."""
    objetivo: int = rnd.randint(20, 180)
    esquema: str = rnd.choice(("http://", "https://"))
    dominio: str = rnd.choice(("v.club", "sub17.mx", "video.ejemplo.org"))
    prefijo: str = f"{esquema}{dominio}/"
    # Longitud de relleno de la ruta para alcanzar el objetivo en bytes ASCII.
    restante: int = max(1, objetivo - len(prefijo))
    ruta: list[str] = [rnd.choice(_URL_ALFABETO) for _ in range(restante)]
    url: str = prefijo + "".join(ruta)
    if len(url.encode("ascii")) > 180:
        url = url[:180]
    return url


# --------------------------------------------------------------------------- #
# Componentes de la Ficha_Ejercicio
# --------------------------------------------------------------------------- #


def _gen_dosis(rnd: random.Random) -> Dosis:
    """Dosis con descanso y una combinación variable de series/reps/tiempos."""
    descanso: str = rnd.choice(("30 s", "1 min", "sin descanso", "2 min"))
    if rnd.random() < 0.6:
        return Dosis(
            descanso=descanso,
            series=rnd.randint(1, 5),
            repeticiones=rnd.randint(4, 20),
        )
    return Dosis(
        descanso=descanso,
        series=rnd.randint(1, 4),
        segundos=rnd.randint(10, 90),
    )


def _gen_montaje(rnd: random.Random) -> Montaje:
    """Montaje con medidas en metros estrictamente positivas."""
    return Montaje(
        ancho_m=round(rnd.uniform(4.0, 20.0), 1),
        largo_m=round(rnd.uniform(4.0, 30.0), 1),
        trazo=gen_texto(rnd),
        botellas=rnd.randint(0, 8),
    )


def _gen_variante_reducida(rnd: random.Random) -> Variante:
    """Variante de Espacio_Reducido: cabe en 10 m × 10 m o menos (Req 8.4)."""
    return Variante(
        ancho_m=round(rnd.uniform(3.0, 10.0), 1),
        largo_m=round(rnd.uniform(3.0, 10.0), 1),
        ajuste=gen_texto(rnd),
    )


def _gen_variante_completa(rnd: random.Random) -> Variante:
    """Variante de Espacio_Completo, típicamente mayor que la reducida."""
    return Variante(
        ancho_m=round(rnd.uniform(10.0, 40.0), 1),
        largo_m=round(rnd.uniform(10.0, 60.0), 1),
        ajuste=gen_texto(rnd),
    )


def _gen_material(rnd: random.Random) -> list[str]:
    """Subconjunto no vacío de MATERIAL_PERMITIDO (Req 8.5)."""
    disponibles: list[str] = sorted(MATERIAL_PERMITIDO)
    cantidad: int = rnd.randint(1, len(disponibles))
    # Selección determinista sin `random.sample`: barajado propio y corte.
    barajado: list[str] = list(disponibles)
    for i in range(len(barajado) - 1, 0, -1):
        j: int = rnd.randint(0, i)
        barajado[i], barajado[j] = barajado[j], barajado[i]
    return barajado[:cantidad]


def _gen_jugadoras(rnd: random.Random) -> tuple[int, int]:
    """Rango (min, max) con 1 <= min <= max <= 11 (Req 8.1)."""
    minimo: int = rnd.randint(1, 6)
    maximo: int = rnd.randint(minimo, 11)
    return (minimo, maximo)


_POSICIONES: tuple[Posicion, ...] = tuple(Posicion)
_ETIQUETAS: tuple[str, ...] = (
    "definicion",
    "remate_cabeza",
    "penal",
    "control",
    "pase",
    "blocaje",
    "salida",
)


def gen_ficha(rnd: random.Random, *, id_ficha: str | None = None) -> FichaEjercicio:
    """`FichaEjercicio` válida con longitudes variables de pasos y variantes."""
    identificador: str = id_ficha if id_ficha is not None else _slug(rnd)
    n_pasos: int = rnd.randint(2, 6)
    pasos: list[str] = [gen_texto(rnd) for _ in range(n_pasos)]
    posicion: Posicion = rnd.choice(_POSICIONES)
    tiene_video: bool = rnd.random() < 0.5
    return FichaEjercicio(
        id=identificador,
        titulo=gen_texto(rnd),
        objetivo=gen_texto(rnd),
        pasos=pasos,
        dosis=_gen_dosis(rnd),
        observacion=gen_texto(rnd),
        jugadoras=_gen_jugadoras(rnd),
        montaje=_gen_montaje(rnd),
        espacio_reducido=_gen_variante_reducida(rnd),
        espacio_completo=_gen_variante_completa(rnd),
        material=_gen_material(rnd),
        diagrama=gen_spec_diagrama(rnd),
        capitulo_id=rnd.choice(("cap10_fundamentos", "cap20_pos", "cap30_colectivo")),
        video_url=gen_url(rnd) if tiene_video else None,
        video_titulo=gen_texto(rnd) if tiene_video else None,
        errores_comunes=[gen_texto(rnd) for _ in range(rnd.randint(0, 3))],
        posiciones=[posicion.value],
        etiquetas=[rnd.choice(_ETIQUETAS)],
        heredada=rnd.random() < 0.1,
    )


def _slug(rnd: random.Random) -> str:
    """Slug corto y razonablemente único para el id de una ficha."""
    partes: list[str] = [
        rnd.choice(("tec", "pos", "col", "fis", "men")),
        "".join(rnd.choice(_LETRAS[:26]) for _ in range(6)),
        str(rnd.randrange(1000)),
    ]
    return "_".join(partes)


# --------------------------------------------------------------------------- #
# Ficha con una violación inyectada
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class MutacionFicha:
    """Resultado de `gen_ficha_mutada`: la ficha inválida y su localización.

    `ficha` es una `FichaEjercicio` real con exactamente una violación; `campo`
    nombra el campo alterado y `codigo_esperado` el código de error que el
    validador de esquema debería reportar (Property 2: la violación se detecta
    y se localiza).
    """

    ficha: FichaEjercicio
    campo: str
    codigo_esperado: str


# Mutaciones de un solo campo: (campo, valor inválido). Cada una viola el
# esquema de una forma localizable. El valor puede ser `None` (campo ausente)
# o de tipo/valor incorrecto.
_MUTACIONES: tuple[tuple[str, object], ...] = (
    ("titulo", None),
    ("objetivo", None),
    ("pasos", []),                       # se exigen >= 2 pasos
    ("pasos", ["único paso"]),           # solo 1 paso
    ("dosis", None),
    ("observacion", None),
    ("jugadoras", (0, 3)),               # min < 1
    ("jugadoras", (5, 2)),               # min > max
    ("material", ["laser"]),             # fuera de MATERIAL_PERMITIDO
    ("montaje", None),
    ("diagrama", None),
    ("id", ""),                          # id vacío
    ("titulo", 123),                     # tipo incorrecto
)

_E_FICHA_INCOMPLETA: str = "E_FICHA_INCOMPLETA"


def gen_ficha_mutada(rnd: random.Random) -> MutacionFicha:
    """`FichaEjercicio` con exactamente una violación inyectada.

    Usa `dataclasses.replace` para mutar un único campo de una ficha válida,
    dejando el resto intacto. Devuelve además el campo alterado y el código de
    error esperado para poder comprobar la localización del fallo.
    """
    base: FichaEjercicio = gen_ficha(rnd)
    campo, valor = rnd.choice(_MUTACIONES)
    mutada: FichaEjercicio = dataclasses.replace(base, **{campo: valor})
    return MutacionFicha(
        ficha=mutada,
        campo=campo,
        codigo_esperado=_E_FICHA_INCOMPLETA,
    )


# --------------------------------------------------------------------------- #
# Catálogo con conteos parametrizables
# --------------------------------------------------------------------------- #


def gen_catalogo(
    rnd: random.Random,
    *,
    n_fichas: int | None = None,
    por_posicion: int | None = None,
) -> tuple[FichaEjercicio, ...]:
    """Catálogo sintético de fichas con conteos parametrizables.

    Sin argumentos produce un catálogo de tamaño aleatorio (útil como `gen`
    para `for_all`). Con `n_fichas` fija el total; con `por_posicion` genera esa
    cantidad de fichas por cada `Posicion`, para ejercitar los umbrales de
    cobertura por posición y los caminos de error de conteo insuficiente.
    """
    fichas: list[FichaEjercicio] = []
    if por_posicion is not None:
        for posicion in _POSICIONES:
            for indice in range(por_posicion):
                identificador: str = f"{posicion.value}_{indice:03d}"
                ficha: FichaEjercicio = gen_ficha(rnd, id_ficha=identificador)
                ficha.posiciones = [posicion.value]
                fichas.append(ficha)
        return tuple(fichas)

    total: int = n_fichas if n_fichas is not None else rnd.randint(1, 30)
    for indice in range(total):
        fichas.append(gen_ficha(rnd, id_ficha=f"ficha_{indice:04d}"))
    return tuple(fichas)


# --------------------------------------------------------------------------- #
# Specs de diagrama (coordenadas extremas)
# --------------------------------------------------------------------------- #

_TIPOS_ITEM: tuple[str, ...] = (
    "player",
    "rival",
    "gk",
    "ball",
    "cone",
    "run",
    "pass",
    "dribble",
    "shot",
    "txt",
    "zone",
    "poly",
    "mark",
    "seg",
    "boot",
    "target",
)


def gen_spec_diagrama(rnd: random.Random) -> DiagramaSpec:
    """Spec de cancha con items en los bordes del mundo y coordenadas extremas."""
    ancho_m: float = round(rnd.uniform(10.0, 40.0), 2)
    alto_m: float = round(rnd.uniform(10.0, 30.0), 2)
    mundo: Mundo = Mundo(ancho_m=ancho_m, alto_m=alto_m)

    # Coordenadas límite: esquinas, centro y valores en el borde exacto.
    candidatas_x: tuple[float, ...] = (0.0, ancho_m, ancho_m / 2, round(ancho_m, 3))
    candidatas_y: tuple[float, ...] = (0.0, alto_m, alto_m / 2, round(alto_m, 3))

    n_items: int = rnd.randint(1, 8)
    items: list[Item] = []
    for _ in range(n_items):
        items.append(
            Item(
                tipo=rnd.choice(_TIPOS_ITEM),
                x=rnd.choice(candidatas_x),
                y=rnd.choice(candidatas_y),
            )
        )

    return DiagramaSpec(
        clase=ClaseDiagrama.CANCHA,
        mundo=mundo,
        items=tuple(items),
        titulo=gen_texto(rnd) if rnd.random() < 0.5 else None,
    )


# --------------------------------------------------------------------------- #
# Figura de postura (ángulos extremos)
# --------------------------------------------------------------------------- #


def gen_figura_postura(rnd: random.Random):
    """Figura con flexión de rodilla 0–120°, valgo −30 a +30, inclinación variable.

    Importa `PanelFigura` y `figura` de forma local: esos nombres aún no existen
    con esta forma en el proyecto (ver la nota de los imports).
    """
    from guia.diagram_spec import figura  # noqa: PLC0415 - ver docstring

    return figura(
        flexion_rodilla=round(rnd.uniform(0.0, 120.0), 1),
        valgo=round(rnd.uniform(-30.0, 30.0), 1),
        inclinacion_tronco=round(rnd.uniform(0.0, 45.0), 1),
        apertura_pies=round(rnd.uniform(10.0, 60.0), 1),
        etiqueta=rnd.choice(("ASI SI", "ASI NO")),
    )


# --------------------------------------------------------------------------- #
# Semilla para el Plan_Rotacion
# --------------------------------------------------------------------------- #


def gen_semilla(rnd: random.Random) -> int:
    """Entero de 32 bits para sembrar el Plan_Rotacion de forma determinista."""
    return rnd.randrange(2**32)


# =========================================================================== #
# Feature "imagenes-reales-hero-interactivo" (tarea 1.6)
# =========================================================================== #
#
# Generadores de los Diagrama_Postura, del Mundo_Hero, del Guardarrail_Lexico,
# del Bloque_Creditos y de las Seccion_Reservada. Las tablas declarativas que
# siguen se escriben aqui **a proposito**: `gen.py` se importa antes de que
# existan `diagramas_postura.py`, `mundo_hero.py` y `secciones_guia.py`, asi que
# los generadores no pueden depender de esos modulos en tiempo de importacion.
# El unico que si los necesita (`gen_catalogo_fundamento_ajeno`) los importa
# dentro de la funcion.
#
# Convencion de forma: los subconjuntos se devuelven como **tuplas ordenadas**,
# no como `frozenset`, porque el shrinker de `prop.py` sabe reducir tuplas
# (quitando elementos y por mitades) y no sabe reducir conjuntos. El contraejemplo
# minimizado es entonces el subconjunto mas pequeno que sigue fallando.

#: Identificadores de los ocho Diagrama_Postura, en el orden del catalogo.
IDS_DIAGRAMA: tuple[str, ...] = (
    "anatomia-base",
    "tiro-empeine",
    "pase-interior",
    "control-balon",
    "conduccion",
    "potencia-carrera",
    "cabeceo-frente",
    "pase-largo-empeine",
)

#: Extensiones que acepta el Guardarrail_Recursos para un Archivo_Diagrama.
EXTENSIONES_ASSET: tuple[str, ...] = (".webp", ".svg", ".png", ".avif")

#: Directorio relativo de los Archivo_Diagrama (siempre con "/").
_DIR_ASSETS: str = "assets/img/tecnica"

#: Los cuatro Fundamento del conjunto cerrado (criterio 2.8).
FUNDAMENTOS_CERRADOS: tuple[str, ...] = (
    "golpeo",
    "pase",
    "control-conduccion",
    "cabeceo",
)

#: Anclas de Seccion_Reservada que esta spec emite (criterio 19.1).
RESERVADAS_ANCLAS: tuple[str, ...] = (
    "leyenda-simbolos",
    "rutina-semanal",
    *(f"ejercicios-{f}" for f in FUNDAMENTOS_CERRADOS),
)

#: Campos de una entrada del Bloque_Creditos (criterio 18.2).
CAMPOS_CREDITO: tuple[str, ...] = ("autor", "fuente", "licencia", "enlace")

#: Los siete conceptos que la Advertencia_Cabeceo debe contener (criterio 20.2).
CONCEPTOS_CABECEO_EXIGIDOS: tuple[str, ...] = (
    "frente",
    "coronilla",
    "cara",
    "cuello contraído",
    "ojos abiertos",
    "balón blando",
    "sin salto",
)

# Expresiones que el Guardarrail_Lexico rechaza (criterios 17.4, 17.5 y 17.6).
_MASCULINO_GENERICO: tuple[str, ...] = (
    "el jugador",
    "los jugadores",
    "el alumno",
    "los alumnos",
    "el niño",
    "los niños",
    "el chico",
    "los chicos",
)
_FORMAS_MASCULINAS: tuple[str, ...] = (
    "listo",
    "atento",
    "concentrado",
    "cansado",
    "preparado",
)
_CONDESCENDIENTES: tuple[str, ...] = (
    "es facilísimo",
    "es muy fácil",
    "no te compliques",
    "solo tienes que",
)

#: Todas las expresiones lexicas prohibidas, en una sola tabla plana.
_LEXICO_PROHIBIDO: tuple[str, ...] = (
    *_MASCULINO_GENERICO,
    *_FORMAS_MASCULINAS,
    *_CONDESCENDIENTES,
)


def _subconjunto(
    rnd: random.Random,
    elementos: tuple[str, ...],
    *,
    peso_vacio: float = 0.12,
    peso_total: float = 0.12,
) -> tuple[str, ...]:
    """Subconjunto ordenado de `elementos`, con el vacio y el total incluidos.

    Los dos extremos se sortean con probabilidad propia para que aparezcan de
    verdad en 100 iteraciones y no solo por casualidad: el vacio es el caso
    "ningun Archivo_Diagrama presente" y el total es "los ocho presentes".
    """
    sorteo: float = rnd.random()
    if sorteo < peso_vacio:
        return ()
    if sorteo < peso_vacio + peso_total:
        return tuple(elementos)
    elegidos: list[str] = [e for e in elementos if rnd.random() < 0.5]
    return tuple(elegidos)


# --------------------------------------------------------------------------- #
# Archivo_Diagrama presentes y firmas de bytes
# --------------------------------------------------------------------------- #


def gen_presentes(rnd: random.Random) -> tuple[str, ...]:
    """Subconjunto de rutas relativas de Archivo_Diagrama presentes.

    Cubre el subconjunto vacio (ningun archivo: los ocho diagramas se rinden con
    el Generador_SVG) y el total (los ocho presentes: todos con `<img>`), mas los
    subconjuntos intermedios que mezclan los dos modos de render. Cada ruta lleva
    una extension de `EXTENSIONES_ASSET` elegida al azar.
    """
    rutas: list[str] = []
    for identificador in IDS_DIAGRAMA:
        extension: str = rnd.choice(EXTENSIONES_ASSET)
        rutas.append(f"{_DIR_ASSETS}/{identificador}{extension}")
    return _subconjunto(rnd, tuple(rutas))


@dataclass(frozen=True, slots=True)
class BytesAsset:
    """Contenido de un asset copiado, con o sin la firma de su extension.

    `firma_valida` dice si `datos` empieza por la firma que el Orquestador_Build
    exige para `extension` (criterio 5.12), de modo que la propiedad sepa si
    debe esperar `ErrorAsset(E_ASSET_INVALIDO)` o una publicacion limpia.
    """

    extension: str
    datos: bytes
    firma_valida: bool


def _cuerpo_relleno(rnd: random.Random, largo: int) -> bytes:
    """Relleno de bytes arbitrarios, para que el asset no sea solo su firma."""
    return bytes(rnd.randrange(256) for _ in range(largo))


def _con_firma(rnd: random.Random, extension: str) -> bytes:
    """Bytes que empiezan por la firma correcta de `extension` (criterio 5.12)."""
    relleno: bytes = _cuerpo_relleno(rnd, rnd.randint(16, 64))
    if extension == ".webp":
        # `RIFF` en 0..3, cuatro bytes de tamano y `WEBP` en 8..11.
        return b"RIFF" + _cuerpo_relleno(rnd, 4) + b"WEBP" + relleno
    if extension == ".png":
        return bytes((0x89, 0x50, 0x4E, 0x47)) + relleno
    if extension == ".avif":
        # `ftyp` en 4..7, tras los cuatro bytes de tamano de la caja.
        return _cuerpo_relleno(rnd, 4) + b"ftyp" + relleno
    # `.svg`: la subcadena `<svg` dentro de los primeros 512 bytes.
    hueco: bytes = b" " * rnd.randint(0, 40)
    return b"<?xml version='1.0'?>" + hueco + b"<svg viewBox='0 0 10 10'></svg>"


def _tiene_firma(extension: str, datos: bytes) -> bool:
    """Comprueba la firma del criterio 5.12 sobre `datos`.

    Se implementa aqui, en el generador, para que la marca `firma_valida` de
    `BytesAsset` sea cierta **por construccion** y no por confianza: `.svg` se
    valida por subcadena dentro de los primeros 512 bytes, asi que desplazar su
    firma no la invalida, y sin esta comprobacion el generador mentiria.
    """
    if extension == ".webp":
        return datos[0:4] == b"RIFF" and datos[8:12] == b"WEBP"
    if extension == ".png":
        return datos[0:4] == bytes((0x89, 0x50, 0x4E, 0x47))
    if extension == ".avif":
        return datos[4:8] == b"ftyp"
    return b"<svg" in datos[:512]


def _sin_firma(rnd: random.Random, extension: str) -> bytes:
    """Bytes que NO llevan la firma de `extension` (dispara E_ASSET_INVALIDO).

    Tres formas de fallar: contenido ajeno, firma de otra extension y firma
    correcta pero desplazada, que es el caso que un chequeo perezoso por offset
    dejaria pasar. La tercera forma no se usa con `.svg`, cuya firma se busca por
    subcadena y sobrevive al desplazamiento.
    """
    formas: int = 2 if extension == ".svg" else 3
    forma: int = rnd.randrange(formas)
    if forma == 0:
        return b"no-soy-una-imagen" + _cuerpo_relleno(rnd, rnd.randint(0, 32))
    if forma == 1:
        ajenas: tuple[str, ...] = tuple(
            e for e in EXTENSIONES_ASSET if e != extension
        )
        return _con_firma(rnd, rnd.choice(ajenas))
    return b"\x00" * rnd.randint(1, 8) + _con_firma(rnd, extension)


def gen_bytes_asset(rnd: random.Random) -> BytesAsset:
    """Asset con o sin la firma que corresponde a su extension (criterio 5.12).

    Reparte los casos entre las cuatro extensiones y entre firma valida e
    invalida, para ejercitar los dos caminos de `_copiar_assets_atomico`. La
    marca `firma_valida` se comprueba sobre los bytes ya construidos, de modo que
    ninguna colision fortuita del relleno pueda desmentirla.
    """
    extension: str = rnd.choice(EXTENSIONES_ASSET)
    valida: bool = rnd.random() < 0.5
    if valida:
        datos: bytes = _con_firma(rnd, extension)
        if not _tiene_firma(extension, datos):
            raise RuntimeError(f"firma valida mal construida para {extension}")
    else:
        datos = _sin_firma(rnd, extension)
        if _tiene_firma(extension, datos):
            # Colision fortuita del relleno: se cae al caso mas simple, que no
            # lleva ninguna firma de ninguna extension.
            datos = b"no-soy-una-imagen"
    return BytesAsset(extension=extension, datos=datos, firma_valida=valida)


# --------------------------------------------------------------------------- #
# Progreso_Scroll, cursor y toque del Mundo_Hero
# --------------------------------------------------------------------------- #


def gen_progreso(rnd: random.Random) -> float:
    """Progreso_Scroll dentro y fuera del intervalo `[0, 1]`.

    Incluye los bordes exactos (0.0 y 1.0), valores interiores y valores fuera de
    rango por los dos lados, que es donde se comprueba el acotado del criterio
    8.5 (opacidad 0 con progreso 1 o mas).
    """
    forma: int = rnd.randrange(5)
    if forma == 0:
        return 0.0
    if forma == 1:
        return 1.0
    if forma == 2:
        return rnd.uniform(0.0, 1.0)
    if forma == 3:
        return rnd.uniform(1.0, 4.0)
    return rnd.uniform(-3.0, 0.0)


def gen_secuencia_progresos(rnd: random.Random) -> tuple[float, ...]:
    """Secuencia monotona de Progreso_Scroll, creciente o decreciente.

    Sirve a la reversibilidad del criterio 8.6: se recorre la secuencia hacia
    delante y hacia atras y los valores de opacidad y escala deben coincidir en
    cada punto. La secuencia siempre tiene al menos dos elementos.
    """
    cantidad: int = rnd.randint(2, 12)
    valores: list[float] = sorted(gen_progreso(rnd) for _ in range(cantidad))
    if rnd.random() < 0.5:
        valores.reverse()
    return tuple(valores)


def gen_cursor_relativo(rnd: random.Random) -> tuple[float, float]:
    """Posicion relativa del cursor dentro del hero, en `[-1, 1]` por eje.

    Incluye el centro, las cuatro esquinas exactas y posiciones fuera del hero
    (modulo mayor que 1), para comprobar el tope de 20 px por eje del criterio
    9.4 y la vuelta a cero al salir (criterio 9.6).
    """
    def eje() -> float:
        forma: int = rnd.randrange(4)
        if forma == 0:
            return 0.0
        if forma == 1:
            return rnd.choice((-1.0, 1.0))
        if forma == 2:
            return rnd.uniform(-1.0, 1.0)
        return rnd.uniform(-3.0, 3.0)

    return (eje(), eje())


def gen_punto_toque(rnd: random.Random) -> tuple[float, float]:
    """Punto de toque en coordenadas porcentuales del hero, dentro y fuera.

    Dentro es `[0, 100]` en los dos ejes; fuera se sale por cualquiera de los
    cuatro lados. Con el punto fuera del hero, o sin balon dentro del radio
    declarado, `balon_mas_cercano` devuelve `None` (criterio 9.8).
    """
    if rnd.random() < 0.25:
        def eje_fuera() -> float:
            return rnd.choice((rnd.uniform(-80.0, -0.1), rnd.uniform(100.1, 180.0)))

        if rnd.random() < 0.5:
            return (eje_fuera(), rnd.uniform(0.0, 100.0))
        return (rnd.uniform(0.0, 100.0), eje_fuera())
    return (rnd.uniform(0.0, 100.0), rnd.uniform(0.0, 100.0))


# --------------------------------------------------------------------------- #
# Dimensiones del viewBox de los Diagrama_Postura
# --------------------------------------------------------------------------- #


def gen_viewbox(rnd: random.Random) -> tuple[int, int]:
    """Dimensiones declaradas `(ancho, alto)` de un Diagrama_Postura.

    El ancho vive en `(0, 1200]` y el alto es positivo (criterio 2.4), con los
    bordes exactos incluidos: 1 y 1200 de ancho, y los dos anchos reales del
    catalogo (360 en modo SVG y 1200 en modo archivo). El `viewBox` emitido es el
    doble de estas medidas (`FACTOR_VIEWBOX = 2.0`).
    """
    forma: int = rnd.randrange(4)
    if forma == 0:
        return (1, 1)
    if forma == 1:
        return (1200, rnd.randint(1, 1600))
    if forma == 2:
        return (360, 480)
    return (rnd.randint(1, 1200), rnd.randint(1, 2000))


# --------------------------------------------------------------------------- #
# Advertencia_Cabeceo, Guardarrail_Lexico, creditos y Seccion_Reservada
# --------------------------------------------------------------------------- #


def gen_conceptos_eliminados(rnd: random.Random) -> tuple[str, ...]:
    """Subconjunto de conceptos que se quitan de la Advertencia_Cabeceo.

    El subconjunto vacio es el texto declarado intacto (debe validar); cualquier
    subconjunto no vacio debe hacer que `validar_advertencia` lance
    `ErrorAsset(E_ASSET_INVALIDO)` nombrando un concepto ausente (criterio 20.5).
    """
    return _subconjunto(rnd, CONCEPTOS_CABECEO_EXIGIDOS, peso_total=0.08)


@dataclass(frozen=True, slots=True)
class MutacionLexica:
    """Texto con una expresion lexica prohibida insertada, y su localizacion.

    `texto` es el texto ya contaminado, `expresion` la expresion prohibida que se
    inserto y `posicion` el indice donde se inserto. El Guardarrail_Lexico debe
    devolver `expresion` entre sus violaciones, sea cual sea la posicion.
    """

    texto: str
    expresion: str
    posicion: int


def gen_texto_lexico(rnd: random.Random) -> MutacionLexica:
    """Texto con una expresion lexica prohibida en una posicion arbitraria.

    La insercion en cualquier punto (incluido el inicio y el final, y en mitad de
    una palabra) es lo que obliga al guardarrail a normalizar acentos y a usar
    limites de palabra en las formas masculinas, de modo que atrape "listo" pero
    no "listones" ni "cansancio".
    """
    base: str = gen_texto(rnd)
    expresion: str = rnd.choice(_LEXICO_PROHIBIDO)
    posicion: int = rnd.randint(0, len(base))
    partes: list[str] = [base[:posicion], " ", expresion, " ", base[posicion:]]
    return MutacionLexica(
        texto="".join(partes),
        expresion=expresion,
        posicion=posicion,
    )


def gen_campos_credito_ausentes(rnd: random.Random) -> tuple[str, ...]:
    """Subconjunto de campos de credito ausentes en una entrada del bloque.

    El vacio es el credito completo; el total es la entrada sin ningun dato, que
    aun asi se emite con la marca "dato pendiente" en los cuatro campos y queda
    registrada en `creditos_pendientes` (criterios 18.6 y 18.9).
    """
    return _subconjunto(rnd, CAMPOS_CREDITO, peso_vacio=0.2, peso_total=0.2)


def gen_reservadas_registradas(rnd: random.Random) -> tuple[str, ...]:
    """Subconjunto de anclas de Seccion_Reservada con cuerpo registrado.

    Con el registro vacio el documento es el de esta spec; con el registro
    completo es el de las dos specs juntas. En los dos extremos, y en todos los
    intermedios, cada Seccion_Reservada emite su ancla y su encabezado
    (criterio 19.7).
    """
    return _subconjunto(rnd, RESERVADAS_ANCLAS, peso_vacio=0.2, peso_total=0.2)


@dataclass(frozen=True, slots=True)
class CatalogoMutado:
    """Catalogo con uno o mas Fundamento fuera del conjunto cerrado de cuatro.

    `catalogo` es la tupla de `DiagramaPostura` ya mutada y `ajenos` los valores
    de Fundamento que quedaron fuera del conjunto cerrado, que es exactamente lo
    que el reporte del Orquestador_Build debe enumerar como omitidos
    (criterio 3.9).
    """

    catalogo: tuple[object, ...]
    ajenos: tuple[str, ...]


_FUNDAMENTOS_AJENOS: tuple[str, ...] = (
    "portería",
    "arbitraje",
    "saque-de-banda",
    "golpeo-avanzado",
    "",
)


def gen_catalogo_fundamento_ajeno(rnd: random.Random) -> CatalogoMutado:
    """Catalogo real con el Fundamento de una o mas entradas cambiado por otro.

    Importa `guia.diagramas_postura` **dentro** de la funcion: `gen.py` se carga
    antes de que ese modulo exista (tarea 2.1) y una importacion de nivel de
    modulo romperia toda la utileria de pruebas. Nunca muta `anatomia-base`, que
    es la unica entrada con Fundamento nulo.
    """
    from guia import diagramas_postura  # import local: ver docstring

    original: tuple[object, ...] = tuple(diagramas_postura.CATALOGO)
    mutables: list[int] = [
        indice
        for indice, entrada in enumerate(original)
        if getattr(entrada, "fundamento", None) is not None
    ]
    if not mutables:
        raise RuntimeError(
            "el catalogo no tiene ninguna entrada con Fundamento que mutar"
        )

    cuantas: int = rnd.randint(1, len(mutables))
    barajado: list[int] = list(mutables)
    for i in range(len(barajado) - 1, 0, -1):
        j: int = rnd.randint(0, i)
        barajado[i], barajado[j] = barajado[j], barajado[i]
    elegidos: list[int] = sorted(barajado[:cuantas])

    entradas: list[object] = list(original)
    ajenos: list[str] = []
    for indice in elegidos:
        ajeno: str = rnd.choice(_FUNDAMENTOS_AJENOS)
        entradas[indice] = dataclasses.replace(entradas[indice], fundamento=ajeno)
        if ajeno not in ajenos:
            ajenos.append(ajeno)

    return CatalogoMutado(catalogo=tuple(entradas), ajenos=tuple(ajenos))


# =========================================================================== #
# Ampliacion multi-vista: Proyector_Vistas y Figura_Girable (tarea 5.2)
# =========================================================================== #
#
# Las tablas que siguen se repiten aqui **a proposito**, igual que las de la
# tarea 1.6: `gen.py` no puede depender de `guia.vistas_figura` en tiempo de
# importacion, porque la utileria de pruebas tiene que seguir importandose
# aunque ese modulo falle. Las propiedades comparan las dos declaraciones, de
# modo que no puedan desincronizarse en silencio.

#: Los ocho azimuts declarados, en grados (criterio 22.1).
AZIMUTS_DECLARADOS_GEN: tuple[int, ...] = (0, 45, 90, 135, 180, 225, 270, 315)

#: Las dos elevaciones declaradas: picada y contrapicada (criterio 22.3).
ELEVACIONES_DECLARADAS_GEN: tuple[int, ...] = (60, -60)

#: Subconjunto_Azimuts_Movil: los seis que sobreviven bajo 768 px (criterio 12.7).
AZIMUTS_MOVIL_GEN: tuple[int, ...] = (0, 45, 90, 180, 270, 315)

#: Las diez Clave_Vista, en el orden exacto del criterio 22.1.
CLAVES_VISTA_GEN: tuple[str, ...] = (
    "az-000",
    "az-045",
    "az-090",
    "az-135",
    "az-180",
    "az-225",
    "az-270",
    "az-315",
    "el-p60",
    "el-m60",
)

#: Identificadores de las poses declaradas: los mismos ocho del catalogo.
IDS_POSE: tuple[str, ...] = IDS_DIAGRAMA

#: Techo de tamano de una Vista_Figura, en bytes (criterio 22.13).
BYTES_MAX_VISTA_GEN: int = 6144

#: Paso entre dos azimuts contiguos, en grados. Su mitad es el punto de empate
#: exacto del desempate del criterio 25.7.
PASO_AZIMUT: float = 45.0

#: Los ocho puntos medios entre azimuts contiguos: los casos limite del
#: desempate, donde `vista_mas_cercana` tiene que elegir el azimut **menor**.
PUNTOS_MEDIOS_AZIMUT: tuple[float, ...] = tuple(
    float(a) + PASO_AZIMUT / 2.0 for a in AZIMUTS_DECLARADOS_GEN
)


def gen_azimut_declarado(rnd: random.Random) -> int:
    """Azimut **dentro** de `AZIMUTS_DECLARADOS`, uno de los ocho.

    Es el dominio que `validar_vistas` acepta sin quejarse: la longitud de hueso
    en 3D tiene que dar la declarada con tolerancia 1e-6 en todos ellos
    (criterio 21.5).
    """
    return rnd.choice(AZIMUTS_DECLARADOS_GEN)


def gen_elevacion_declarada(rnd: random.Random) -> int:
    """Elevacion **dentro** de `ELEVACIONES_DECLARADAS`, o el 0 de las azimutales.

    Las ocho Vista_Azimut declaran elevacion 0 y las dos Vista_Elevacion +60 y
    -60 (criterios 22.2 y 22.3), asi que el dominio valido de la elevacion de una
    Clave_Vista es `{0, 60, -60}`.
    """
    return rnd.choice((0, *ELEVACIONES_DECLARADAS_GEN))


@dataclass(frozen=True, slots=True)
class AnguloFueraDeRango:
    """Azimut o elevacion que `validar_vistas` debe rechazar.

    `eje` dice cual de los dos se salio (`"azimut"` o `"elevacion"`) y `grados`
    el valor infractor. Los dos casos comparten generador porque comparten la
    fila de Error Handling: el mensaje nombra la figura, la clave y el valor.
    """

    eje: str
    grados: float


def gen_angulo_fuera_de_rango(rnd: random.Random) -> AnguloFueraDeRango:
    """Angulo que **no** pertenece a las tuplas declaradas (criterio 21.13).

    Para el azimut, cualquier grado que no sea multiplo de 45; para la
    elevacion, cualquiera distinto de 0, +60 y -60, incluidos los que saturan
    por encima de 90 grados y los negativos grandes.
    """
    if rnd.random() < 0.5:
        while True:
            grados: float = float(rnd.randrange(-720, 721))
            if grados % 45.0 != 0.0:
                return AnguloFueraDeRango(eje="azimut", grados=grados)
    candidatos: tuple[float, ...] = (
        -180.0,
        -90.0,
        -61.0,
        -59.0,
        -30.0,
        1.0,
        30.0,
        59.0,
        61.0,
        90.0,
        180.0,
        float(rnd.randrange(-360, 361)),
    )
    while True:
        grados = rnd.choice(candidatos)
        if grados not in (0.0, 60.0, -60.0):
            return AnguloFueraDeRango(eje="elevacion", grados=grados)


def gen_angulo_giro(rnd: random.Random) -> float:
    """Angulo de giro continuo en `[0, 360)`, con los casos limite forzados.

    Reparte los casos entre los ocho azimuts exactos (donde la Rotacion_Residual
    vale exactamente 0, criterio 25.11), los ocho puntos medios de 22.5 grados
    (donde el desempate del criterio 25.7 tiene que elegir el azimut declarado
    menor) y angulos uniformes del resto del circulo. Sin los dos primeros
    grupos, 100 iteraciones uniformes nunca tocarian los bordes.
    """
    forma: int = rnd.randrange(4)
    if forma == 0:
        return float(rnd.choice(AZIMUTS_DECLARADOS_GEN))
    if forma == 1:
        return rnd.choice(PUNTOS_MEDIOS_AZIMUT) % 360.0
    if forma == 2:
        # Justo al lado del punto medio, por los dos lados: el desempate no debe
        # depender de un `<=` mal puesto.
        medio: float = rnd.choice(PUNTOS_MEDIOS_AZIMUT)
        return (medio + rnd.choice((-0.001, 0.001))) % 360.0
    return rnd.uniform(0.0, 360.0) % 360.0


@dataclass(frozen=True, slots=True)
class PoseClave:
    """Par de identificador de pose y Clave_Vista, uno de los ochenta posibles.

    `pose_id` es el identificador de una de las ocho poses declaradas y `clave`
    una de las diez Clave_Vista. Se devuelve el identificador y no la `Pose`
    porque `gen.py` no importa `guia.svg_postura` en tiempo de modulo; la
    propiedad resuelve la pose con `svg_postura.pose_de`.
    """

    pose_id: str
    clave: str


def gen_pose_clave(rnd: random.Random) -> PoseClave:
    """Par `(pose, Clave_Vista)` cubriendo las diez claves y las ocho poses."""
    return PoseClave(
        pose_id=rnd.choice(IDS_POSE),
        clave=rnd.choice(CLAVES_VISTA_GEN),
    )


def gen_desplazamiento_dedo(rnd: random.Random) -> tuple[float, float]:
    """Desplazamiento del dedo en el Arrastre_Rotacion, en pixeles por eje.

    Incluye el `(0, 0)` exacto (el toque sin arrastre, que no debe girar nada) y
    desplazamientos lo bastante grandes para **saturar** la elevacion en +-60
    grados con los 0.6 grados por pixel del criterio 28.9: 100 pixeles ya dan 60
    grados, asi que el generador llega hasta 400 por los dos lados.
    """
    if rnd.random() < 0.12:
        return (0.0, 0.0)

    def eje() -> float:
        forma: int = rnd.randrange(3)
        if forma == 0:
            return 0.0
        if forma == 1:
            return rnd.uniform(-40.0, 40.0)
        return rnd.choice((-1.0, 1.0)) * rnd.uniform(100.0, 400.0)

    return (eje(), eje())


def gen_secuencia_angulos(rnd: random.Random) -> tuple[float, ...]:
    """Secuencia monotona de angulos de giro, creciente o decreciente.

    Sirve a la reversibilidad de la conmutacion: recorrer la secuencia hacia
    delante y hacia atras debe elegir la misma Clave_Vista en cada punto, y el
    Modo_Inerte debe conservar el ultimo angulo. Siempre trae al menos dos
    elementos y siempre incluye algun azimut exacto o algun punto medio, que son
    los angulos donde la eleccion cambia.
    """
    cantidad: int = rnd.randint(2, 12)
    valores: list[float] = [gen_angulo_giro(rnd) for _ in range(cantidad)]
    valores.sort()
    if rnd.random() < 0.5:
        valores.reverse()
    return tuple(valores)


@dataclass(frozen=True, slots=True)
class BytesVista:
    """Carga de marcado de una Vista_Figura alrededor del techo de 6144 bytes.

    `marcado` es la carga y `cabe` dice si su tamano en bytes respeta
    `BYTES_MAX_VISTA` (criterio 22.13). La marca se calcula sobre los bytes ya
    construidos, no por confianza en el tamano pedido.
    """

    marcado: str
    tamano: int
    cabe: bool


def gen_bytes_vista(rnd: random.Random) -> BytesVista:
    """Carga de Vista_Figura por debajo, en el limite exacto y por encima.

    El limite exacto (6144 bytes justos) es el caso que un `<` mal puesto
    rechazaria y un `<=` aceptaria, asi que se fuerza con probabilidad propia.
    Todo el relleno es ASCII, de modo que un caracter sea un byte y el tamano
    pedido coincida con el medido.
    """
    forma: int = rnd.randrange(4)
    if forma == 0:
        objetivo: int = BYTES_MAX_VISTA_GEN
    elif forma == 1:
        objetivo = BYTES_MAX_VISTA_GEN + rnd.randint(1, 2048)
    elif forma == 2:
        objetivo = BYTES_MAX_VISTA_GEN - rnd.randint(1, 2048)
    else:
        objetivo = rnd.randint(1, 2 * BYTES_MAX_VISTA_GEN)

    apertura: str = '<g class="relleno">'
    cierre: str = "</g>"
    hueco: int = max(0, objetivo - len(apertura) - len(cierre))
    marcado: str = "".join((apertura, "x" * hueco, cierre))
    tamano: int = len(marcado.encode("utf-8"))
    return BytesVista(
        marcado=marcado,
        tamano=tamano,
        cabe=tamano <= BYTES_MAX_VISTA_GEN,
    )


# --------------------------------------------------------------------------- #
# Validador_Rutas: rutas hostiles y rutas aceptables (tarea 13.7)
# --------------------------------------------------------------------------- #
#
# El Requisito 30 es un "si y solo si": para probarlo hacen falta las dos
# orillas, asi que este generador produce rutas hostiles **y** rutas que el
# Validador_Rutas tiene que aceptar (las ocho del catalogo, la extension en
# mayusculas y el separador de Windows, que se normaliza antes de decidir).
#
# Como el resto de la utileria, las tablas se declaran aqui y no se importan de
# `guia.diagramas_postura`: la propiedad compara las dos declaraciones, de modo
# que no puedan desincronizarse en silencio.

#: Prefijos que convierten una ruta en peticion de red o en ruta absoluta
#: (criterio 30.3). Mismo contenido que `PREFIJOS_RECHAZADOS`, declarado aparte.
PREFIJOS_HOSTILES: tuple[str, ...] = ("http://", "https://", "//", "/")

#: Extensiones ajenas a Extensiones_Permitidas (criterio 30.5). La cadena vacia
#: es la ruta sin extension, y `.svgz` y `.JPG` son los dos casos que un
#: `endswith` perezoso o una comparacion sensible a la caja dejarian pasar.
EXTENSIONES_AJENAS: tuple[str, ...] = (
    ".jpg",
    ".JPG",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".svgz",
    ".js",
    ".html",
    "",
)

#: Directorios que **no** son `assets/`: uno por forma de fallar el prefijo
#: (subdirectorio suelto, `assets/` anidado dentro de otro, codigo fuente, la
#: caja cambiada y un nombre que solo empieza igual).
_DIRECTORIOS_AJENOS: tuple[str, ...] = (
    "img/tecnica",
    "dist/assets/img/tecnica",
    "src/guia",
    "Assets/img/tecnica",
    "assetsx/img/tecnica",
    "contenido",
)

#: Las ocho familias de ruta que el generador sabe construir. Viajan en el caso
#: para que el contraejemplo diga de que forma salio la ruta.
FAMILIAS_RUTA: tuple[str, ...] = (
    "catalogo",
    "prefijo_red",
    "ascendente",
    "separador_windows",
    "extension_ajena",
    "extension_mayuscula",
    "fuera_de_assets",
    "vacia",
)


@dataclass(frozen=True, slots=True)
class RutaCandidata:
    """Una ruta para el Validador_Rutas, con la familia de la que salio.

    `familia` **no** dice si la ruta es aceptable: eso lo decide la propiedad
    aplicando las tres condiciones del Requisito 30 sobre la ruta normalizada.
    Es solo el rotulo de diagnostico del contraejemplo.
    """

    ruta: str
    familia: str


def _ruta_de_catalogo(rnd: random.Random) -> str:
    """Ruta relativa aceptable: `assets/img/tecnica/<id><extension>`."""
    identificador: str = rnd.choice(IDS_DIAGRAMA)
    extension: str = rnd.choice(EXTENSIONES_ASSET)
    return f"{_DIR_ASSETS}/{identificador}{extension}"


def _cambiar_caja(rnd: random.Random, extension: str) -> str:
    """Extension con la caja alterada: toda en mayusculas o letra por letra."""
    if rnd.random() < 0.5:
        return extension.upper()
    letras: list[str] = [
        c.upper() if rnd.random() < 0.5 else c for c in extension
    ]
    return "".join(letras)


def _con_ascendente(rnd: random.Random, base: str) -> str:
    """Inserta el segmento `..` en `base`, o un casi-fallo que no lo es.

    El casi-fallo (`a..b` como nombre de archivo) es el caso que un `".." in
    ruta` a ciegas rechazaria: el criterio 30.4 habla del **segmento** `..`, no
    de la subcadena, asi que esa ruta tiene que seguir siendo aceptable.
    """
    segmentos: list[str] = base.split("/")
    forma: int = rnd.randrange(4)
    if forma == 0:
        return "/".join(("..", *segmentos))
    if forma == 1:
        corte: int = rnd.randint(1, len(segmentos) - 1)
        return "/".join((*segmentos[:corte], "..", *segmentos[corte:]))
    if forma == 2:
        return "\\".join(("..", *segmentos))
    nombre: str = segmentos[-1]
    return "/".join((*segmentos[:-1], f"a..b-{nombre}"))


def _con_separador_windows(rnd: random.Random, base: str) -> str:
    """Ruta con separador `\\` de Windows, entera, a medias o desde la raiz."""
    forma: int = rnd.randrange(3)
    if forma == 0:
        return base.replace("/", "\\")
    if forma == 1:
        segmentos: list[str] = base.split("/")
        corte: int = rnd.randint(1, len(segmentos) - 1)
        primero: str = "/".join(segmentos[:corte])
        resto: str = "\\".join(segmentos[corte:])
        return f"{primero}\\{resto}"
    return f"\\{base.replace('/', chr(92))}"


def gen_ruta_hostil(rnd: random.Random) -> RutaCandidata:
    """Ruta de Asset_Local hostil o aceptable, para el Validador_Rutas.

    Reparte los casos entre las ocho `FAMILIAS_RUTA`: prefijos `http://`,
    `https://`, `//` y `/`; el segmento `..` en cualquier posicion (y su
    casi-fallo `a..b`); el separador `\\` de Windows, entero, a medias y desde
    la raiz; extensiones ajenas y extensiones declaradas con la caja cambiada;
    rutas fuera de `assets/`; la cadena vacia; y las rutas reales del catalogo.
    """
    familia: str = rnd.choice(FAMILIAS_RUTA)
    base: str = _ruta_de_catalogo(rnd)

    if familia == "prefijo_red":
        prefijo: str = rnd.choice(PREFIJOS_HOSTILES)
        if rnd.random() < 0.25:
            prefijo = prefijo.upper()
        ruta: str = f"{prefijo}{base}"
    elif familia == "ascendente":
        ruta = _con_ascendente(rnd, base)
    elif familia == "separador_windows":
        ruta = _con_separador_windows(rnd, base)
    elif familia == "extension_ajena":
        raiz: str = base.rsplit(".", 1)[0]
        ruta = f"{raiz}{rnd.choice(EXTENSIONES_AJENAS)}"
    elif familia == "extension_mayuscula":
        raiz = base.rsplit(".", 1)[0]
        extension: str = rnd.choice(EXTENSIONES_ASSET)
        ruta = f"{raiz}{_cambiar_caja(rnd, extension)}"
    elif familia == "fuera_de_assets":
        nombre: str = base.rsplit("/", 1)[-1]
        directorio: str = rnd.choice(_DIRECTORIOS_AJENOS)
        ruta = nombre if rnd.random() < 0.2 else f"{directorio}/{nombre}"
    elif familia == "vacia":
        ruta = ""
    else:
        ruta = base

    return RutaCandidata(ruta=ruta, familia=familia)


# --------------------------------------------------------------------------- #
# Guardarrail de codigo de los modulos nuevos (tarea 14.3)
# --------------------------------------------------------------------------- #
#
# Los criterios 13.3 y 13.4 son prohibiciones ("solo stdlib y `guia`", "ningun
# `assert`") y el 13.2 tambien ("ni `<script>`, ni `<canvas>`, ni `<img>`, ni
# atributo de evento en linea"). Una prohibicion se prueba de las dos orillas:
# hace falta inyectar la violacion para ver que el detector la encuentra, y hace
# falta inyectar el CASI-FALLO para ver que no la inventa.
#
# Este generador produce el **plan** de la inyeccion, no la inyeccion: dice que
# modulo o que documento tocar, de que familia es el injerto, si el detector
# debe encontrarlo y con que marca. Quien aplica el plan es la propiedad, sobre
# una copia en memoria del arbol de sintaxis o del marcado; en `src/guia/` no se
# escribe nunca.

#: Los cinco modulos nuevos de la feature (criterios 13.3 y 13.4).
MODULOS_NUEVOS: tuple[str, ...] = (
    "diagramas_postura",
    "svg_postura",
    "vistas_figura",
    "secciones_guia",
    "mundo_hero",
)

#: Paquetes de terceros que este proyecto no puede instalar. Ninguno pertenece a
#: `sys.stdlib_module_names`, que es lo que el detector consulta.
PAQUETES_EXTERNOS: tuple[str, ...] = (
    "reportlab",
    "PIL",
    "numpy",
    "hypothesis",
    "qrcode",
    "requests",
    "lxml",
    "cairosvg",
    "pytest",
    "yaml",
)

#: Modulos de la libreria estandar para los injertos aceptables. `xml.etree` es
#: el caso con punto, que obliga a mirar la raiz del nombre y no el nombre entero.
MODULOS_STDLIB_GEN: tuple[str, ...] = (
    "math",
    "json",
    "re",
    "textwrap",
    "itertools",
    "collections",
    "xml.etree.ElementTree",
    "unicodedata",
)

#: Familias de injerto sobre el arbol de sintaxis. Las seis primeras son
#: violaciones; las cuatro ultimas son casi-fallos que deben pasar.
FAMILIAS_CODIGO: tuple[str, ...] = (
    "assert_modulo",
    "assert_en_funcion",
    "assert_anidado",
    "import_externo",
    "from_externo",
    "import_externo_en_funcion",
    "import_stdlib",
    "from_paquete_propio",
    "from_relativo",
    "parecido_a_assert",
)

#: Familias de injerto sobre un documento de capitulo. Las cuatro primeras son
#: violaciones del criterio 13.2; las tres ultimas son casi-fallos.
FAMILIAS_MARCADO: tuple[str, ...] = (
    "script",
    "canvas",
    "img",
    "evento_en_linea",
    "texto_menciona_script",
    "atributo_data_on",
    "svg_con_rol_img",
)

#: Familias que el detector **tiene** que encontrar.
FAMILIAS_HOSTILES: frozenset[str] = frozenset(
    {
        "assert_modulo",
        "assert_en_funcion",
        "assert_anidado",
        "import_externo",
        "from_externo",
        "import_externo_en_funcion",
        "script",
        "canvas",
        "img",
        "evento_en_linea",
    }
)

#: Atributos de evento en linea con los que se construye el injerto hostil.
_EVENTOS_EN_LINEA: tuple[str, ...] = (
    "onclick",
    "onload",
    "onmouseover",
    "ontouchstart",
    "onerror",
)


@dataclass(frozen=True, slots=True)
class ViolacionCodigo:
    """Plan de una inyeccion sobre un modulo nuevo o sobre un capitulo.

    `dominio` vale `"modulo"` (injerto de sentencias Python sobre el arbol de
    sintaxis) o `"documento"` (injerto de marcado sobre el HTML del capitulo).
    `hostil` dice si el detector debe encontrar la violacion, y `marca` es la
    cadena que su mensaje tiene que nombrar. `posicion`, en `[0, 1]`, elige el
    lugar del injerto: el indice dentro del cuerpo del modulo o de la funcion, y
    la linea del documento. `objetivo` es el modulo nuevo, o la cadena vacia
    cuando el documento lo resuelve la propiedad por `posicion`.
    """

    dominio: str
    objetivo: str
    familia: str
    hostil: bool
    fragmento: str
    marca: str
    posicion: float


def _injerto_codigo(rnd: random.Random, familia: str) -> tuple[str, str]:
    """Sentencia Python del injerto y marca que el detector debe nombrar."""
    if familia in ("assert_modulo", "assert_en_funcion"):
        forma: int = rnd.randrange(3)
        if forma == 0:
            return "assert 1 == 1", "assert"
        if forma == 1:
            return 'assert bool(1), "invariante inyectado"', "assert"
        return "assert len(()) == 0", "assert"
    if familia == "assert_anidado":
        if rnd.random() < 0.5:
            return "if bool(1):\n    assert 1 == 1", "assert"
        return "try:\n    assert 1 == 1\nexcept Exception:\n    pass", "assert"
    if familia in ("import_externo", "import_externo_en_funcion"):
        paquete: str = rnd.choice(PAQUETES_EXTERNOS)
        if rnd.random() < 0.5:
            return f"import {paquete}", paquete
        return f"import {paquete}.submodulo as alias", paquete
    if familia == "from_externo":
        paquete = rnd.choice(PAQUETES_EXTERNOS)
        if rnd.random() < 0.5:
            return f"from {paquete} import algo", paquete
        return f"from {paquete}.interno import algo", paquete
    if familia == "import_stdlib":
        modulo: str = rnd.choice(MODULOS_STDLIB_GEN)
        if rnd.random() < 0.5:
            return f"import {modulo}", modulo
        return f"from {modulo} import algo", modulo
    if familia == "from_paquete_propio":
        if rnd.random() < 0.5:
            return "from guia import errores", "guia"
        return "import guia.paleta", "guia"
    if familia == "from_relativo":
        if rnd.random() < 0.5:
            return "from . import errores", "guia"
        return "from .errores import ErrorAsset", "guia"
    # parecido_a_assert: cadenas y nombres que dicen "assert" sin serlo.
    forma = rnd.randrange(3)
    if forma == 0:
        return '_TEXTO_INYECTADO = "assert 1 == 1"', "assert"
    if forma == 1:
        return "def assertar_invariante():\n    return None", "assert"
    return "_ = ('assert', 'import reportlab')", "assert"


def _injerto_marcado(rnd: random.Random, familia: str) -> tuple[str, str]:
    """Fragmento de marcado del injerto y marca que el detector debe nombrar."""
    if familia == "script":
        if rnd.random() < 0.5:
            return "<script>var x = 1;</script>", "<script"
        return '<SCRIPT type="text/javascript"></SCRIPT>', "<script"
    if familia == "canvas":
        if rnd.random() < 0.5:
            return '<canvas width="360" height="640"></canvas>', "<canvas"
        return "<CANVAS hidden></CANVAS>", "<canvas"
    if familia == "img":
        if rnd.random() < 0.5:
            return '<img src="assets/img/tecnica/x.webp" alt="x">', "<img"
        return '<IMG src="x.png" alt="y">', "<img"
    if familia == "evento_en_linea":
        evento: str = rnd.choice(_EVENTOS_EN_LINEA)
        # El separador alterna espacio y salto de linea: un atributo de evento
        # partido en dos lineas sigue siendo un atributo de evento.
        separacion: str = " " if rnd.random() < 0.5 else "\n  "
        return f'<p{separacion}{evento}="f()">texto</p>', evento
    if familia == "texto_menciona_script":
        return (
            "<p>Esta pagina no trae script, canvas ni onclick: "
            "es marcado estatico.</p>",
            "",
        )
    if familia == "atributo_data_on":
        return '<p data-onda="1" data-imagen="no">texto</p>', ""
    # svg_con_rol_img: el `role="img"` que un detector perezoso confundiria.
    return '<svg viewBox="0 0 10 10" role="img" focusable="false"></svg>', ""


def gen_violacion_codigo(rnd: random.Random) -> ViolacionCodigo:
    """Plan de inyeccion sobre un modulo nuevo o sobre un capitulo.

    Sortea el dominio (arbol de sintaxis de uno de los cinco `MODULOS_NUEVOS` o
    marcado de un documento de capitulo), la familia del injerto entre las diez
    de `FAMILIAS_CODIGO` o las siete de `FAMILIAS_MARCADO`, la forma concreta del
    injerto dentro de su familia y la posicion relativa donde clavarlo. Las dos
    orillas estan representadas: familias hostiles que el detector debe hallar y
    casi-fallos que no debe inventar.
    """
    if rnd.random() < 0.7:
        familia: str = rnd.choice(FAMILIAS_CODIGO)
        fragmento, marca = _injerto_codigo(rnd, familia)
        return ViolacionCodigo(
            dominio="modulo",
            objetivo=rnd.choice(MODULOS_NUEVOS),
            familia=familia,
            hostil=familia in FAMILIAS_HOSTILES,
            fragmento=fragmento,
            marca=marca,
            posicion=rnd.random(),
        )

    familia = rnd.choice(FAMILIAS_MARCADO)
    fragmento, marca = _injerto_marcado(rnd, familia)
    return ViolacionCodigo(
        dominio="documento",
        objetivo="",
        familia=familia,
        hostil=familia in FAMILIAS_HOSTILES,
        fragmento=fragmento,
        marca=marca,
        posicion=rnd.random(),
    )


# --------------------------------------------------------------------------- #
# Ayudantes de extraccion de CSS y de JavaScript (tarea 10.10)
# --------------------------------------------------------------------------- #
#
# Las propiedades sobre la Hoja_Estilo y sobre el Script_Unico NO comparan
# cadenas enteras: extraen la pieza que les toca y la afirman. Asi el
# contraejemplo que reporta el shrinker es la declaracion infractora --una linea
# de veinte caracteres-- y no veinte mil bytes de CSS.
#
# Son analizadores deliberadamente simples, escritos para el CSS que este
# proyecto emite: sin comentarios, sin cadenas con llaves dentro y con todas las
# declaraciones separadas por punto y coma. No pretenden ser un parser de CSS.


@dataclass(frozen=True, slots=True)
class Regla:
    """Una regla CSS ya troceada: su selector, su cuerpo y su consulta de medios.

    `media` es la condicion de la `@media` que la envuelve (por ejemplo
    `"(hover: hover)"`) o la cadena vacia cuando la regla vive en el nivel
    superior de la hoja. Eso es lo que deja preguntar "esta regla `:hover` esta
    dentro de `@media (hover: hover)`" sin volver a recorrer el CSS.
    """

    selector: str
    cuerpo: str
    media: str


def _trocear(css: str) -> list[Regla]:
    """Trocea `css` en reglas, anotando la consulta de medios de cada una.

    Recorre el texto una sola vez con una pila de contextos `@media`. Un bloque
    `@` sin declaraciones propias (`@media`, `@supports`) abre contexto; cualquier
    otro bloque (`@keyframes`, una regla normal) se devuelve como `Regla`.
    """
    encontradas: list[Regla] = []
    pila: list[str] = []
    inicio: int = 0
    profundidad_regla: int = 0
    cabeza: str = ""

    posicion: int = 0
    while posicion < len(css):
        caracter = css[posicion]
        if caracter == "{":
            cabeza = css[inicio:posicion].strip()
            if profundidad_regla == 0 and cabeza.startswith(("@media", "@supports")):
                pila.append(cabeza)
                inicio = posicion + 1
            else:
                # Cuerpo de la regla: se busca su llave de cierre contando
                # anidamientos (los `@keyframes` llevan bloques dentro).
                nivel = 1
                fin = posicion + 1
                while fin < len(css) and nivel > 0:
                    if css[fin] == "{":
                        nivel += 1
                    elif css[fin] == "}":
                        nivel -= 1
                    fin += 1
                cuerpo = css[posicion + 1 : fin - 1]
                media = pila[-1][len("@media") :].strip() if pila else ""
                encontradas.append(Regla(selector=cabeza, cuerpo=cuerpo, media=media))
                posicion = fin
                inicio = fin
                continue
        elif caracter == "}":
            if pila:
                pila.pop()
            inicio = posicion + 1
        posicion += 1

    return encontradas


def reglas(css: str) -> tuple[Regla, ...]:
    """Todas las reglas de `css`, cada una con la consulta de medios que la envuelve."""
    return tuple(_trocear(css))


def bloques_media(css: str) -> tuple[tuple[str, str], ...]:
    """Pares `(condicion, cuerpo)` de cada `@media` de `css`, en orden de aparicion.

    `condicion` viene sin el `@media` y sin espacios de sobra
    (`"(prefers-reduced-motion: reduce)"`), y `cuerpo` es el texto entre las
    llaves de la consulta. El orden de la tupla **es** el orden del CSS, que es lo
    que necesita la propiedad de cascada del criterio 11.7.
    """
    hallados: list[tuple[str, str]] = []
    posicion: int = css.find("@media")
    while posicion >= 0:
        abre = css.find("{", posicion)
        if abre < 0:
            break
        condicion = css[posicion + len("@media") : abre].strip()
        nivel = 1
        fin = abre + 1
        while fin < len(css) and nivel > 0:
            if css[fin] == "{":
                nivel += 1
            elif css[fin] == "}":
                nivel -= 1
            fin += 1
        hallados.append((condicion, css[abre + 1 : fin - 1]))
        posicion = css.find("@media", fin)
    return tuple(hallados)


def declaraciones(css: str, propiedad: str) -> tuple[tuple[str, str], ...]:
    """Pares `(selector, valor)` de cada declaracion de `propiedad` en `css`.

    Coincide con la propiedad exacta, no con sus parientes: pedir `"width"` no
    devuelve `min-width` ni `max-width`, y pedir `"background"` no devuelve
    `background-image`. El valor viene sin el punto y coma y sin espacios de
    sobra.
    """
    hallados: list[tuple[str, str]] = []
    for regla in _trocear(css):
        for trozo in regla.cuerpo.split(";"):
            if ":" not in trozo:
                continue
            nombre, _, valor = trozo.partition(":")
            if nombre.strip() == propiedad:
                hallados.append((regla.selector, valor.strip()))
    return tuple(hallados)


def cuerpo_de_funcion(js: str, nombre: str) -> str:
    """Cuerpo de la funcion `nombre` dentro de `js`, sin sus llaves exteriores.

    Busca `function <nombre>(` y devuelve lo que hay entre la llave que abre su
    cuerpo y la que lo cierra, contando anidamientos. Devuelve la cadena vacia
    cuando la funcion no existe, para que la propiedad pueda afirmar su ausencia
    sin reventar con una excepcion de indice.
    """
    marca: str = f"function {nombre}("
    inicio: int = js.find(marca)
    if inicio < 0:
        return ""
    abre: int = js.find("{", inicio)
    if abre < 0:
        return ""
    nivel: int = 1
    fin: int = abre + 1
    while fin < len(js) and nivel > 0:
        if js[fin] == "{":
            nivel += 1
        elif js[fin] == "}":
            nivel -= 1
        fin += 1
    return js[abre + 1 : fin - 1]


def escrituras_de_estilo(js: str) -> tuple[tuple[str, str], ...]:
    """Pares `(propiedad, expresion)` de cada escritura `style.<prop> = ...` en `js`.

    Cubre las dos formas que el proyecto usa: `elemento.style.transform=...` y
    `elemento.style.setProperty('--x',...)`. Devuelve la propiedad escrita y la
    expresion asignada, para que la propiedad de presupuesto de escrituras cuente
    por propiedad y para que el contraejemplo sea la escritura infractora.
    """
    hallados: list[tuple[str, str]] = []
    for coincidencia in re.finditer(
        r"\.style\.([A-Za-z]+)\s*=\s*([^;]+)", js
    ):
        hallados.append((coincidencia.group(1), coincidencia.group(2).strip()))
    for coincidencia in re.finditer(
        r"\.style\.setProperty\(\s*['\"]([^'\"]+)['\"]\s*,([^)]*)\)", js
    ):
        hallados.append((coincidencia.group(1), coincidencia.group(2).strip()))
    return tuple(hallados)
