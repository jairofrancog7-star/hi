"""Modelo de dominio (dataclasses + Enum) y validación de esquema/cobertura.

Este módulo define el **modelo interno** que consume todo el pipeline del PDF
(paginador, motores de diagrama y QR, orquestador). Las Ficha_Ejercicio nacen
del `Catalogo_JSON` (`contenido/ejercicios.json`) vía el adaptador
`guia.schema_json.ficha_json_a_ficha`; aquí viven las dataclasses destino y los
validadores que garantizan que cada objeto cumple su esquema antes de
renderizar.

Principios (según `design.md` y las convenciones del proyecto):

* Python 3.11+, solo librería estándar. Nada de dependencias externas.
* `@dataclass` con type hints y `Enum` para conjuntos cerrados. Los campos sin
  valor por defecto son los **obligatorios** (Req 10.1); los que llevan
  `| None = None` o `default_factory` son opcionales.
* Los validadores **no confían en los defaults**: comprueban presencia y buen
  formato de cada campo obligatorio y reportan el `id` del objeto y el nombre
  del campo afectado.
* Nada de `assert` (desaparecen con `python -O`): todo fallo se expresa como
  `raise` de una subclase de `ErrorBuild`. Aquí se usan `ErrorEsquema`
  (`E_FICHA_INCOMPLETA`) y `ErrorCobertura` (`E_COBERTURA_MINIMA`).
* La tabla de umbrales mínimos de cobertura vive en un solo lugar
  (`UMBRALES_COBERTURA`).

Requisitos: 10.1, 10.2, 8.1, 8.4, 8.5, 8.9, 9.1.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from .errores import (
    E_COBERTURA_MINIMA,
    E_FICHA_INCOMPLETA,
    ErrorCobertura,
    ErrorEsquema,
)

__all__ = [
    'MATERIAL_PERMITIDO',
    'UMBRALES_COBERTURA',
    'LADO_ESPACIO_REDUCIDO_M',
    'Dia',
    'Posicion',
    'GrupoMuscular',
    'ClaseDiagrama',
    'Dosis',
    'Montaje',
    'Variante',
    'FichaEjercicio',
    'BloqueSesion',
    'Sesion',
    'Sabado',
    'BloqueSemanal',
    'Indicador',
    'ModuloPosicion',
    'EjercicioFuerza',
    'ModuloPrevencion',
    'ModuloMental',
    'LaminaVertical',
    'exigir_minimo',
    'exigir_umbral',
    'validar_ficha',
    'validar_catalogo',
    'validar_cobertura_fichas',
]

# --------------------------------------------------------------------------- #
# Conjuntos cerrados y constantes de dominio
# --------------------------------------------------------------------------- #

#: Material admitido en cualquier Ficha_Ejercicio (Req 8.5). Un conjunto
#: cerrado e inmutable: balón, botellas de refresco, una pared y gis.
MATERIAL_PERMITIDO: frozenset[str] = frozenset({'balon', 'botellas', 'pared', 'gis'})

#: Lado máximo (en metros) de la variante de Espacio_Reducido (Req 8.4): la
#: variante reducida debe caber en una franja de 10 m × 10 m o menor.
LADO_ESPACIO_REDUCIDO_M: float = 10.0


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class Dia(str, Enum):
    """Días de entrenamiento entre semana del Bloque_Semanal."""

    MARTES = 'martes'
    MIERCOLES = 'miercoles'
    JUEVES = 'jueves'


class Posicion(str, Enum):
    """Las siete posiciones cubiertas por un Modulo_Posicion (Req 4.1)."""

    PORTERA = 'portera'
    LATERAL = 'lateral'
    CENTRAL = 'central'
    CONTENCION = 'contencion'
    MEDIA = 'media'
    EXTREMO = 'extremo'
    DELANTERA = 'delantera'


class GrupoMuscular(str, Enum):
    """Grupos musculares de los ejercicios de fuerza del Modulo_Prevencion."""

    GLUTEO = 'gluteo'
    ISQUIOS = 'isquios'
    ADUCTORES = 'aductores'
    CORE = 'core'


class ClaseDiagrama(str, Enum):
    """Clases de diagrama que dibuja el Motor_Diagramas."""

    CANCHA = 'cancha'
    BOTIN = 'botin'
    POSTURA = 'postura'


# --------------------------------------------------------------------------- #
# Ficha_Ejercicio y sus componentes
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Dosis:
    """Dosificación de un ejercicio: descanso obligatorio y volumen opcional."""

    descanso: str
    series: int | None = None
    repeticiones: int | None = None
    segundos: int | None = None
    minutos: int | None = None


@dataclass(slots=True)
class Montaje:
    """Trazado del espacio con gis y botellas, con medidas en metros (Req 8.9)."""

    ancho_m: float                       # > 0
    largo_m: float                       # > 0
    trazo: str                           # cómo marcar con gis
    botellas: int


@dataclass(slots=True)
class Variante:
    """Variante de espacio (reducido o completo) con sus medidas y su ajuste."""

    ancho_m: float
    largo_m: float
    ajuste: str


@dataclass(slots=True)
class FichaEjercicio:
    """Una Ficha_Ejercicio del Catalogo_Contenido (modelo interno).

    Este modelo interno tiene **dos orígenes** y debe aceptar los campos de
    ambos sin romperse (el validador, no los defaults, decide qué es válido):

    * **Contenido de dominio autorado en Python** (catálogo sintético de los
      tests y capítulos narrativos): trae `dosis`, `espacio_reducido`,
      `espacio_completo`, `material` y `capitulo_id` con sus tipos de dominio
      (`Dosis`, `Variante`, `list[str]`), `jugadoras` como `tuple[int, int]` y
      `montaje` como `Montaje`.
    * **Addendum A / Catalogo_JSON** vía `guia.schema_json.ficha_json_a_ficha`
      (decisión C5): trae además `numero`, `subtitulo`, `categoria` y
      `nivel`, entrega `montaje` como `dict`, `jugadoras`
      como texto y `pasos` como `tuple`, y **omite** los campos de dominio
      anteriores.

    Por eso los únicos campos sin valor por defecto son los que **ambos**
    orígenes proporcionan siempre (`id`, `titulo`, `objetivo`, `pasos`,
    `observacion`, `jugadoras`, `montaje`, `diagrama`); el resto lleva un
    default para que ninguna de las dos construcciones falle. La obligatoriedad
    real (Req 10.1) la comprueba `validar_ficha`, que no confía en los defaults.
    """

    # --- siempre presentes en ambos orígenes (Req 10.1) ---
    id: str                              # slug único, p.ej. "del_definicion_1v1"
    titulo: str
    objetivo: str                        # una frase
    pasos: 'list[str] | tuple[str, ...]'  # >= 2, se numeran al renderizar
    observacion: str                     # "qué mira la compañera"
    jugadoras: 'tuple[int, int] | str'   # (min, max) 1<=min<=max (Req 8.1) o texto JSON
    montaje: 'Montaje | dict[str, object]'  # medidas en metros con gis/botellas (Req 8.9)
    diagrama: 'DiagramaSpec | None'      # Diagrama_Cancha (Req 9.1)
    # --- de dominio: los provee el catálogo Python; el adaptador JSON los omite ---
    dosis: 'Dosis | None' = None
    espacio_reducido: 'Variante | None' = None   # cabe en <= 10 x 10 m (Req 8.4)
    espacio_completo: 'Variante | None' = None
    material: list[str] = field(default_factory=list)  # subconjunto de MATERIAL_PERMITIDO (Req 8.5)
    capitulo_id: str = ''
    # --- de Addendum A / Catalogo_JSON: los provee el adaptador ficha_json_a_ficha ---
    numero: int | None = None
    subtitulo: str | None = None
    categoria: str | None = None
    nivel: str | None = None
    # --- opcionales comunes ---
    video_url: str | None = None         # si existe => /Link + QR (Req 9.6)
    video_titulo: str | None = None
    errores_comunes: list[str] = field(default_factory=list)
    postura: 'DiagramaPosturaSpec | None' = None
    posiciones: list[str] = field(default_factory=list)
    etiquetas: list[str] = field(default_factory=list)
    heredada: bool = False               # True en las 15 fichas originales (Req 9.5)
    nota_seguridad: str | None = None


# --------------------------------------------------------------------------- #
# Bloque_Semanal y Plan_Rotacion
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class BloqueSesion:
    """Un bloque de una sesión (nombre y minutos que consume)."""

    nombre: str
    minutos: int


@dataclass(slots=True)
class Sesion:
    """Una sesión de entrenamiento de un día del Bloque_Semanal."""

    dia: Dia
    foco: str
    bloques: list[BloqueSesion]          # sum(b.minutos) == total_min (Req 5.6)
    total_min: int                       # <= 90 (Req 5.7)
    ficha_ids: list[str]
    jugadoras: tuple[int, int]           # rango derivado de las fichas
    version_corta: 'Sesion | None' = None  # total_min <= 30 (Req 5.9)
    sustituta_id: str | None = None      # sesión alterna con menos jugadoras (Req 8.8)


@dataclass(slots=True)
class Sabado:
    """Sesión de sábado: calentamiento y enfoque del fin de semana."""

    calentamiento: list[str]
    enfoque: str


@dataclass(slots=True)
class BloqueSemanal:
    """Un Bloque_Semanal del Plan_Rotacion (Req 5.1, 5.2, 5.5)."""

    id: str                              # "S01".."S26"
    semana: int
    objetivo: str                        # una sola frase (Req 5.5)
    sesiones: dict[Dia, Sesion]          # las tres claves presentes (Req 5.2)
    sabado: Sabado
    firma: str                           # combinación canónica de ficha_ids


# --------------------------------------------------------------------------- #
# Modulo_Posicion, Modulo_Prevencion, Modulo_Mental
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class Indicador:
    """Indicador de progreso medible de un Modulo_Posicion (Req 4.7)."""

    nombre: str
    objetivo: float
    unidad: str
    como_medir: str


@dataclass(slots=True)
class ModuloPosicion:
    """Módulo específico de una posición (Req 4.1-4.7)."""

    posicion: Posicion
    titulo: str
    rol_defensivo: list[str]             # no vacío (Req 4.3)
    rol_ofensivo: list[str]              # no vacío
    indicadores: list[Indicador]         # no vacía (Req 4.7)
    ficha_ids: list[str]                 # >= 12, con >= 3 de min 1 jugadora
    frases_cancha: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EjercicioFuerza:
    """Ejercicio de fuerza sin gimnasio, con su Diagrama_Postura (Req 6.4, 6.5)."""

    id: str
    nombre: str
    grupo: GrupoMuscular
    dosis: Dosis
    material: list[str]
    postura: 'DiagramaPosturaSpec'       # dos paneles + >= 1 marca


@dataclass(slots=True)
class ModuloPrevencion:
    """Módulo de prevención de lesiones y cuidado del cuerpo (Req 6.*)."""

    secciones: list['SeccionTexto']      # incluye lca_cadera, lca_rodilla, lca_isquios
    fifa11: 'ProgramaFifa'               # 3 partes, cada ejercicio con 3 niveles (Req 6.3)
    fuerza: list[EjercicioFuerza]        # >= 20, cada uno con postura (Req 6.4, 6.5)
    aterrizaje: FichaEjercicio           # marcas de alineación rodilla-punta (Req 6.6)
    ciclo: list['FaseCiclo']             # cada fase con ajuste de carga (Req 6.7)
    hierro: list['TablaAlimento']
    calcio: list['TablaAlimento']
    movilidad: list['PasoMovilidad']     # sum(minutos) == 10 (Req 6.9)
    banderas_rojas: list[str]            # Req 6.10
    descargo: str                        # Req 6.11


@dataclass(slots=True)
class ModuloMental:
    """Módulo de preparación mental y visual (Req 7.*)."""

    pre_partido: list['PasoRutina']      # t en minutos negativos, monótono (Req 7.2)
    tras_error: list['PasoProtocolo']    # sum(segundos) < 10 (Req 7.3)
    visualizaciones: list['Visualizacion']        # >= 8, con guion y duración
    comunicacion: list['EjercicioComunicacion']   # >= 10, frases por posición
    escaneo: list[FichaEjercicio]        # >= 10, material balón + pared
    registro: 'EscalaRegistro'           # escala 1..5 en 3 dimensiones
    liderazgo: list['SeccionTexto']


# --------------------------------------------------------------------------- #
# Lamina_Vertical
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class LaminaVertical:
    """Lámina vertical infografía rosa/negro para WhatsApp (Req 9.4)."""

    id: str                              # los 13 ids originales se conservan (Req 9.4)
    titulo: str
    bajada: str
    items: list['LaminaItem']            # viñetas, números grandes, mini-diagramas
    fondo: str                           # 'rosa' | 'negro'
    video_url: str | None = None


# --------------------------------------------------------------------------- #
# Tabla de umbrales mínimos de cobertura (un solo lugar)
# --------------------------------------------------------------------------- #

#: Umbrales mínimos de cobertura del catálogo completo. Toda comprobación de
#: cantidad los lee de aquí, de modo que ajustar un umbral es un cambio de una
#: sola línea (Req 10.6, Property 23). Los valores provienen de `design.md`.
UMBRALES_COBERTURA: dict[str, int] = {
    'fichas': 120,
    'fichas_por_posicion': 12,
    'individuales_por_posicion': 3,
    'individuales': 30,
    'bloques': 24,
    'fuerza': 20,
    'visualizaciones': 8,
    'comunicacion': 10,
    'escaneo': 10,
    'posturas': 40,
    'laminas': 13,
    'heredadas': 15,
}


# --------------------------------------------------------------------------- #
# Validadores de cobertura (E_COBERTURA_MINIMA)
# --------------------------------------------------------------------------- #


def exigir_minimo(coleccion: str, cantidad: int, minimo: int) -> None:
    """Exige `cantidad >= minimo`; si no, lanza `E_COBERTURA_MINIMA`.

    El mensaje sigue el formato de `design.md`: ``<coleccion>: hay <n>, se
    requieren <min>``. El detalle transporta la colección afectada y los
    conteos para diagnóstico programático.
    """
    if cantidad < minimo:
        raise ErrorCobertura(
            f'{coleccion}: hay {cantidad}, se requieren {minimo}',
            detalle={'coleccion': coleccion, 'cantidad': cantidad, 'minimo': minimo},
        )


def exigir_umbral(clave: str, cantidad: int) -> None:
    """Como `exigir_minimo`, pero tomando el mínimo de `UMBRALES_COBERTURA`."""
    if clave not in UMBRALES_COBERTURA:
        raise ErrorCobertura(
            f'umbral desconocido: {clave!r}',
            detalle={'coleccion': clave, 'cantidad': cantidad, 'minimo': -1},
        )
    exigir_minimo(clave, cantidad, UMBRALES_COBERTURA[clave])


def validar_cobertura_fichas(fichas: Iterable[FichaEjercicio]) -> None:
    """Comprueba los umbrales de cobertura que dependen solo de las fichas.

    Verifica el total de fichas (>= 120), las fichas ejecutables por una sola
    jugadora (>= 30), las fichas heredadas presentes (>= 15) y, por cada
    posición declarada, el mínimo de fichas y de fichas individuales. Cada
    incumplimiento lanza `E_COBERTURA_MINIMA` nombrando la colección afectada.
    """
    lista: list[FichaEjercicio] = list(fichas)

    exigir_umbral('fichas', len(lista))

    individuales = sum(1 for f in lista if _min_jugadoras(f) == 1)
    exigir_umbral('individuales', individuales)

    heredadas = sum(1 for f in lista if f.heredada)
    exigir_umbral('heredadas', heredadas)

    por_posicion: dict[str, int] = {}
    individuales_por_posicion: dict[str, int] = {}
    for ficha in lista:
        es_individual = _min_jugadoras(ficha) == 1
        for pos in ficha.posiciones:
            por_posicion[pos] = por_posicion.get(pos, 0) + 1
            if es_individual:
                individuales_por_posicion[pos] = (
                    individuales_por_posicion.get(pos, 0) + 1
                )

    for posicion in Posicion:
        clave = posicion.value
        exigir_minimo(
            f'fichas_posicion_{clave}',
            por_posicion.get(clave, 0),
            UMBRALES_COBERTURA['fichas_por_posicion'],
        )
        exigir_minimo(
            f'individuales_posicion_{clave}',
            individuales_por_posicion.get(clave, 0),
            UMBRALES_COBERTURA['individuales_por_posicion'],
        )


def _min_jugadoras(ficha: FichaEjercicio) -> int:
    """Mínimo de jugadoras de la ficha, tolerante a formas inválidas."""
    jugadoras = ficha.jugadoras
    if isinstance(jugadoras, tuple) and len(jugadoras) == 2:
        minimo = jugadoras[0]
        if isinstance(minimo, int) and not isinstance(minimo, bool):
            return minimo
    return -1


# --------------------------------------------------------------------------- #
# Validador de esquema de Ficha_Ejercicio (E_FICHA_INCOMPLETA)
# --------------------------------------------------------------------------- #


def validar_catalogo(fichas: Iterable[FichaEjercicio]) -> None:
    """Valida el esquema de cada Ficha_Ejercicio del catálogo.

    Recorre las fichas y aplica `validar_ficha` a cada una. La primera
    violación detiene la validación con `E_FICHA_INCOMPLETA`.
    """
    for ficha in fichas:
        validar_ficha(ficha)


def validar_ficha(ficha: FichaEjercicio) -> None:
    """Comprueba que una Ficha_Ejercicio cumple su esquema (Property 7).

    Verifica presencia y buen formato de cada campo obligatorio sin confiar en
    los valores por defecto de la dataclass. Cualquier violación lanza
    `ErrorEsquema` con código `E_FICHA_INCOMPLETA`, nombrando el `id` de la
    ficha y el campo afectado (Req 10.1, 10.2).
    """
    fid = ficha.id if isinstance(ficha.id, str) and ficha.id.strip() else '<sin id>'

    _texto_no_vacio(fid, ficha.id, 'id')
    _texto_no_vacio(fid, ficha.titulo, 'titulo')
    _texto_no_vacio(fid, ficha.objetivo, 'objetivo')
    _texto_no_vacio(fid, ficha.observacion, 'observacion')
    _texto_no_vacio(fid, ficha.capitulo_id, 'capitulo_id')

    # pasos: secuencia de >= 2 elementos, cada uno texto no vacío (Req 10.1). Se
    # acepta list (catálogo Python) o tuple (adaptador JSON), nunca str.
    if isinstance(ficha.pasos, str) or not isinstance(ficha.pasos, (list, tuple)):
        _falla(fid, 'pasos', f'debe ser una lista de pasos, no {_tipo(ficha.pasos)}')
    if len(ficha.pasos) < 2:
        _falla(fid, 'pasos', f'se requieren al menos 2 pasos, hay {len(ficha.pasos)}')
    for indice, paso in enumerate(ficha.pasos):
        if not isinstance(paso, str) or not paso.strip():
            _falla(fid, f'pasos[{indice}]', 'debe ser texto no vacío')

    # dosis: objeto Dosis con descanso presente (Req 10.1).
    if not isinstance(ficha.dosis, Dosis):
        _falla(fid, 'dosis', f'debe ser una Dosis, no {_tipo(ficha.dosis)}')
    if not isinstance(ficha.dosis.descanso, str) or not ficha.dosis.descanso.strip():
        _falla(fid, 'dosis.descanso', 'debe ser texto no vacío')

    # jugadoras: (min, max) con 1 <= min <= max (Req 8.1).
    _rango_jugadoras(fid, ficha.jugadoras)

    # montaje: medidas en metros mayores que cero (Req 8.9).
    if not isinstance(ficha.montaje, Montaje):
        _falla(fid, 'montaje', f'debe ser un Montaje, no {_tipo(ficha.montaje)}')
    _medida_positiva(fid, ficha.montaje.ancho_m, 'montaje.ancho_m')
    _medida_positiva(fid, ficha.montaje.largo_m, 'montaje.largo_m')

    # espacio_reducido: Variante que cabe en 10 m x 10 m (Req 8.4).
    _variante_positiva(fid, ficha.espacio_reducido, 'espacio_reducido')
    if isinstance(ficha.espacio_reducido, Variante):
        _cabe_en_reducido(fid, ficha.espacio_reducido.ancho_m, 'espacio_reducido.ancho_m')
        _cabe_en_reducido(fid, ficha.espacio_reducido.largo_m, 'espacio_reducido.largo_m')

    # espacio_completo: Variante con medidas positivas.
    _variante_positiva(fid, ficha.espacio_completo, 'espacio_completo')

    # material: subconjunto de MATERIAL_PERMITIDO (Req 8.5).
    if not isinstance(ficha.material, list):
        _falla(fid, 'material', f'debe ser una lista, no {_tipo(ficha.material)}')
    for indice, elemento in enumerate(ficha.material):
        if elemento not in MATERIAL_PERMITIDO:
            permitidos = ', '.join(sorted(MATERIAL_PERMITIDO))
            _falla(
                fid,
                f'material[{indice}]',
                f'{elemento!r} no está en el material permitido ({permitidos})',
            )

    # diagrama: un Diagrama_Cancha presente y renderizable (Req 9.1).
    if ficha.diagrama is None:
        _falla(fid, 'diagrama', 'falta el Diagrama_Cancha')


# --------------------------------------------------------------------------- #
# Ayudantes de validación de ficha (privados)
# --------------------------------------------------------------------------- #


def _texto_no_vacio(fid: str, valor: object, campo: str) -> None:
    """Exige que `valor` sea una cadena no vacía."""
    if not isinstance(valor, str):
        _falla(fid, campo, f'debe ser texto, no {_tipo(valor)}')
    if not valor.strip():
        _falla(fid, campo, 'no puede estar vacío')


def _rango_jugadoras(fid: str, jugadoras: object) -> None:
    """Exige un par (min, max) de enteros con 1 <= min <= max (Req 8.1)."""
    if not isinstance(jugadoras, tuple) or len(jugadoras) != 2:
        _falla(fid, 'jugadoras', 'debe ser una tupla (min, max)')
    minimo, maximo = jugadoras
    if isinstance(minimo, bool) or not isinstance(minimo, int):
        _falla(fid, 'jugadoras', f'el mínimo debe ser entero, no {_tipo(minimo)}')
    if isinstance(maximo, bool) or not isinstance(maximo, int):
        _falla(fid, 'jugadoras', f'el máximo debe ser entero, no {_tipo(maximo)}')
    if minimo < 1:
        _falla(fid, 'jugadoras', f'el mínimo debe ser >= 1, es {minimo}')
    if minimo > maximo:
        _falla(fid, 'jugadoras', f'el mínimo ({minimo}) supera al máximo ({maximo})')


def _variante_positiva(fid: str, variante: object, campo: str) -> None:
    """Exige que `variante` sea una Variante con medidas positivas."""
    if not isinstance(variante, Variante):
        _falla(fid, campo, f'debe ser una Variante, no {_tipo(variante)}')
    _medida_positiva(fid, variante.ancho_m, f'{campo}.ancho_m')
    _medida_positiva(fid, variante.largo_m, f'{campo}.largo_m')


def _medida_positiva(fid: str, valor: object, campo: str) -> None:
    """Exige una medida numérica en metros estrictamente positiva."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        _falla(fid, campo, f'debe ser un número en metros, no {_tipo(valor)}')
    if not valor > 0:
        _falla(fid, campo, f'debe ser mayor que cero, es {float(valor):.3f}')


def _cabe_en_reducido(fid: str, valor: object, campo: str) -> None:
    """Exige que una medida no supere el lado del Espacio_Reducido (Req 8.4)."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if valor > LADO_ESPACIO_REDUCIDO_M:
            _falla(
                fid,
                campo,
                f'debe caber en {LADO_ESPACIO_REDUCIDO_M:.3f} m, es {float(valor):.3f}',
            )


def _falla(fid: str, campo: str, motivo: str) -> None:
    """Lanza `E_FICHA_INCOMPLETA` localizando ficha y campo."""
    raise ErrorEsquema(
        f'ficha {fid!r}: campo {campo!r} {motivo}',
        detalle={'id': fid, 'campo': campo},
        codigo=E_FICHA_INCOMPLETA,
    )


def _tipo(valor: object) -> str:
    """Nombre legible del tipo de `valor`, para los mensajes de error."""
    if valor is None:
        return 'None'
    return type(valor).__name__
