"""Carga y validación del Catalogo_JSON, y adaptador a `FichaEjercicio`.

Este módulo implementa el Addendum A ("Entrena como las grandes"): el
`contenido/ejercicios.json` (Catalogo_JSON) es la **fuente única** de las
Ficha_Ejercicio. El JSON es el formato de **entrada**; la dataclass
`FichaEjercicio` de `guia.schema` es el **modelo interno** que consume el
paginador y el Motor_PDF. Un adaptador, `ficha_json_a_ficha`, mapea uno al
otro (decisión C5 de `requirements.md`).

Responsabilidades:

* **Carga (`cargar_catalogo`)**: abre el archivo con `encoding='utf-8'` y
  `json.load`. Si el texto no parsea, lanza `E_JSON_NO_PARSEA` con el mensaje,
  la línea, la columna y el offset que reporta `json.JSONDecodeError`.
* **Validación (`validar_catalogo`, `validar_ficha_json`)**: comprueba la
  presencia y el tipo de cada campo obligatorio de cada Ficha_JSON y de cada
  Media_Item, sin confiar en valores por defecto. Cualquier violación se
  reporta con `E_FICHA_JSON_INVALIDA` nombrando el `id` de la ficha y el campo
  afectado (o el índice del Media_Item y el valor inválido).
* **Adaptación (`ficha_json_a_ficha`)**: convierte una Ficha_JSON validada en
  una `FichaEjercicio`. El sitio web consume la Ficha_JSON directamente y **no
  necesita** este adaptador; por eso el import de `guia.schema` es diferido y
  tolerante: si `schema.py` todavía no existe (es la tarea 1.6), la función
  lanza un error claro y controlado en vez de romper el import de este módulo.
  Así, `import guia.schema_json` funciona hoy y la carga/validación es usable
  de inmediato por el sitio, aunque `schema.py` aún no esté escrito.

Solo librería estándar (`json`); sin `assert` (todo invariante es `raise`).

Requisitos: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 12.7, 15.5.
"""

from __future__ import annotations

import json
import os
from typing import Any

from .errores import ErrorCatalogoJSON, ErrorDependencia, E_JSON_NO_PARSEA

__all__ = [
    'TIPOS_MEDIA_PERMITIDOS',
    'CAMPOS_FICHA',
    'CLAVES_DOSIS',
    'CLAVES_MEDIA',
    'cargar_catalogo',
    'validar_catalogo',
    'validar_ficha_json',
    'validar_media_item',
    'ficha_json_a_ficha',
]

#: Conjunto cerrado de tipos de Media_Item admitidos (Req 11.5).
TIPOS_MEDIA_PERMITIDOS: frozenset[str] = frozenset(
    {'youtube', 'tiktok', 'instagram_reel', 'facebook_reel', 'web', 'busqueda'}
)

#: Campos obligatorios de cada Ficha_JSON, en orden de declaración (Req 11.2).
CAMPOS_FICHA: tuple[str, ...] = (
    'id',
    'numero',
    'titulo',
    'subtitulo',
    'categoria',
    'nivel',
    'contexto',
    'pasos',
    'que_mira_la_companera',
    'dosis',
    'cancha',
    'media',
)

#: Claves obligatorias dentro de `dosis` (Req 11.3).
CLAVES_DOSIS: tuple[str, ...] = ('cuando', 'duracion', 'jugadoras', 'material', 'meta')

#: Claves obligatorias dentro de cada Media_Item (Req 11.4).
CLAVES_MEDIA: tuple[str, ...] = ('tipo', 'url', 'titulo')

#: Campos de Ficha_JSON que son cadenas de texto simples y no vacías.
_CAMPOS_TEXTO: tuple[str, ...] = (
    'id',
    'titulo',
    'subtitulo',
    'categoria',
    'nivel',
    'contexto',
)


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #


def cargar_catalogo(ruta: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """Carga y valida el Catalogo_JSON en `ruta`.

    Abre el archivo como UTF-8 y lo parsea con `json.load`. Si el JSON no
    parsea, lanza `ErrorCatalogoJSON` con código `E_JSON_NO_PARSEA` incluyendo
    el mensaje, la línea, la columna y el offset del `json.JSONDecodeError`.
    Luego valida cada Ficha_JSON con `validar_catalogo`.

    Devuelve la lista de Ficha_JSON (dicts) ya validada.
    """
    ruta_texto = os.fspath(ruta)
    with open(ruta_texto, encoding='utf-8') as manejador:
        crudo = manejador.read()

    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError as exc:
        raise ErrorCatalogoJSON(
            f'{ruta_texto} no es JSON válido: {exc.msg} '
            f'(línea {exc.lineno}, columna {exc.colno}, offset {exc.pos})',
            codigo=E_JSON_NO_PARSEA,
            detalle={
                'ruta': ruta_texto,
                'mensaje': exc.msg,
                'linea': exc.lineno,
                'columna': exc.colno,
                'offset': exc.pos,
            },
        ) from exc

    return validar_catalogo(datos, ruta=ruta_texto)


# --------------------------------------------------------------------------- #
# Validación
# --------------------------------------------------------------------------- #


def validar_catalogo(
    datos: object,
    *,
    ruta: str | None = None,
) -> list[dict[str, Any]]:
    """Valida un Catalogo_JSON ya parseado y devuelve su lista de Ficha_JSON.

    El catálogo debe ser una lista de objetos. Cada objeto se valida con
    `validar_ficha_json`.
    """
    origen = ruta if ruta is not None else 'catálogo'
    if not isinstance(datos, list):
        raise ErrorCatalogoJSON(
            f'{origen} debe ser una lista de fichas, no {_nombre_tipo(datos)}',
            detalle={'origen': origen, 'tipo': _nombre_tipo(datos)},
        )

    fichas: list[dict[str, Any]] = []
    for indice, ficha in enumerate(datos):
        if not isinstance(ficha, dict):
            raise ErrorCatalogoJSON(
                f'la ficha en la posición {indice} debe ser un objeto, '
                f'no {_nombre_tipo(ficha)}',
                detalle={'indice': indice, 'tipo': _nombre_tipo(ficha)},
            )
        validar_ficha_json(ficha, indice=indice)
        fichas.append(ficha)

    return fichas


def validar_ficha_json(ficha: dict[str, Any], *, indice: int | None = None) -> None:
    """Valida una única Ficha_JSON.

    Comprueba presencia y tipo de cada campo obligatorio. Cualquier violación
    lanza `ErrorCatalogoJSON` (código `E_FICHA_JSON_INVALIDA`) nombrando el
    `id` de la ficha y el campo afectado.
    """
    fid = _id_para_error(ficha, indice)

    for campo in CAMPOS_FICHA:
        if campo not in ficha:
            _invalida(fid, f'falta el campo obligatorio {campo!r}', campo=campo)

    # Campos de texto simple, no vacíos.
    for campo in _CAMPOS_TEXTO:
        valor = ficha[campo]
        if not isinstance(valor, str):
            _invalida(
                fid,
                f'el campo {campo!r} debe ser texto, no {_nombre_tipo(valor)}',
                campo=campo,
            )
        if not valor.strip():
            _invalida(fid, f'el campo {campo!r} no puede estar vacío', campo=campo)

    # `numero`: entero (los booleanos no cuentan como enteros aquí).
    numero = ficha['numero']
    if isinstance(numero, bool) or not isinstance(numero, int):
        _invalida(
            fid,
            f'el campo \'numero\' debe ser un entero, no {_nombre_tipo(numero)}',
            campo='numero',
        )

    # `pasos`: lista no vacía de texto.
    _validar_lista_texto(fid, ficha['pasos'], 'pasos', permitir_vacia=False)

    # `que_mira_la_companera`: lista de texto (puede ir vacía).
    _validar_lista_texto(
        fid, ficha['que_mira_la_companera'], 'que_mira_la_companera',
        permitir_vacia=True,
    )

    # `dosis`: objeto con las cinco claves obligatorias, cada una de texto.
    dosis = ficha['dosis']
    if not isinstance(dosis, dict):
        _invalida(
            fid,
            f'el campo \'dosis\' debe ser un objeto, no {_nombre_tipo(dosis)}',
            campo='dosis',
        )
    for clave in CLAVES_DOSIS:
        if clave not in dosis:
            _invalida(
                fid, f'a \'dosis\' le falta la clave {clave!r}', campo=f'dosis.{clave}'
            )
        if not isinstance(dosis[clave], str):
            _invalida(
                fid,
                f'\'dosis.{clave}\' debe ser texto, no {_nombre_tipo(dosis[clave])}',
                campo=f'dosis.{clave}',
            )

    # `cancha`: objeto (estructura del diagrama; el Motor_Diagramas la detalla).
    cancha = ficha['cancha']
    if not isinstance(cancha, dict):
        _invalida(
            fid,
            f'el campo \'cancha\' debe ser un objeto, no {_nombre_tipo(cancha)}',
            campo='cancha',
        )

    # `media`: lista de Media_Item.
    media = ficha['media']
    if not isinstance(media, list):
        _invalida(
            fid,
            f'el campo \'media\' debe ser una lista, no {_nombre_tipo(media)}',
            campo='media',
        )
    for indice_media, item in enumerate(media):
        validar_media_item(item, ficha_id=fid, indice=indice_media)


def validar_media_item(
    item: object,
    *,
    ficha_id: str,
    indice: int,
) -> None:
    """Valida un Media_Item: `tipo` en el conjunto cerrado, más `url` y `titulo`."""
    if not isinstance(item, dict):
        _invalida(
            ficha_id,
            f'el media #{indice} debe ser un objeto, no {_nombre_tipo(item)}',
            campo=f'media[{indice}]',
        )

    for clave in CLAVES_MEDIA:
        if clave not in item:
            _invalida(
                ficha_id,
                f'al media #{indice} le falta la clave {clave!r}',
                campo=f'media[{indice}].{clave}',
            )
        if not isinstance(item[clave], str) or not item[clave].strip():
            _invalida(
                ficha_id,
                f'\'media[{indice}].{clave}\' debe ser texto no vacío',
                campo=f'media[{indice}].{clave}',
            )

    tipo = item['tipo']
    if tipo not in TIPOS_MEDIA_PERMITIDOS:
        permitidos = ', '.join(sorted(TIPOS_MEDIA_PERMITIDOS))
        _invalida(
            ficha_id,
            f'el media #{indice} tiene tipo {tipo!r} fuera del conjunto '
            f'permitido ({permitidos})',
            campo=f'media[{indice}].tipo',
            valor=tipo,
        )


# --------------------------------------------------------------------------- #
# Ayudantes de validación (privados)
# --------------------------------------------------------------------------- #


def _validar_lista_texto(
    ficha_id: str,
    valor: object,
    campo: str,
    *,
    permitir_vacia: bool,
) -> None:
    """Comprueba que `valor` es una lista de cadenas (no vacía si se exige)."""
    if not isinstance(valor, list):
        _invalida(
            ficha_id,
            f'el campo {campo!r} debe ser una lista, no {_nombre_tipo(valor)}',
            campo=campo,
        )
    if not permitir_vacia and not valor:
        _invalida(ficha_id, f'el campo {campo!r} no puede estar vacío', campo=campo)
    for posicion, elemento in enumerate(valor):
        if not isinstance(elemento, str) or not elemento.strip():
            _invalida(
                ficha_id,
                f'{campo}[{posicion}] debe ser texto no vacío',
                campo=f'{campo}[{posicion}]',
            )


def _invalida(
    ficha_id: str,
    motivo: str,
    *,
    campo: str,
    valor: object | None = None,
) -> None:
    """Lanza `E_FICHA_JSON_INVALIDA` localizando ficha, campo y (opcional) valor."""
    detalle: dict[str, object] = {'id': ficha_id, 'campo': campo}
    if valor is not None:
        detalle['valor'] = valor
    raise ErrorCatalogoJSON(
        f'ficha {ficha_id!r}: {motivo}',
        detalle=detalle,
    )


def _id_para_error(ficha: dict[str, Any], indice: int | None) -> str:
    """Mejor identificador disponible para los mensajes de error."""
    valor = ficha.get('id')
    if isinstance(valor, str) and valor.strip():
        return valor
    if indice is not None:
        return f'<sin id en posición {indice}>'
    return '<sin id>'


def _nombre_tipo(valor: object) -> str:
    """Nombre legible del tipo JSON de `valor`, para los mensajes."""
    if valor is None:
        return 'null'
    if isinstance(valor, bool):
        return 'bool'
    if isinstance(valor, str):
        return 'texto'
    if isinstance(valor, list):
        return 'lista'
    if isinstance(valor, dict):
        return 'objeto'
    return type(valor).__name__


# --------------------------------------------------------------------------- #
# Adaptador Ficha_JSON -> FichaEjercicio (tarea 17.2)
# --------------------------------------------------------------------------- #
#
# El sitio web (siguiente ola) consume la Ficha_JSON directamente y NO usa este
# adaptador. Solo el pipeline del PDF necesita el modelo interno `FichaEjercicio`
# de `guia.schema`. Por eso los imports de `guia.schema` y `guia.diagram_spec`
# son **diferidos** (dentro de la función) y **tolerantes**: si esos módulos aún
# no existen (son las tareas 1.6 y 3.1), la función lanza un error claro y
# controlado en vez de romper `import guia.schema_json`. Objetivo: que la carga
# y validación (17.1) sea usable HOY por el sitio aunque `schema.py` no exista.


def _importar_diferido(nombre: str, tarea: str) -> Any:
    """Importa `guia.<nombre>` de forma diferida y tolerante.

    Si el módulo todavía no existe, lanza `ErrorDependencia` con un mensaje
    claro que apunta a la tarea pendiente, en vez de propagar `ImportError`.
    """
    try:
        modulo = __import__(f'guia.{nombre}', fromlist=[nombre])
    except ImportError as exc:
        raise ErrorDependencia(
            f'{nombre}.py pendiente ({tarea}): el adaptador '
            f'ficha_json_a_ficha requiere guia.{nombre}, que aún no existe',
            detalle={'modulo': f'guia.{nombre}', 'tarea': tarea},
        ) from exc
    return modulo


def ficha_json_a_ficha(ficha: dict[str, Any], *, indice: int | None = None) -> Any:
    """Convierte una Ficha_JSON en una `FichaEjercicio` (modelo interno).

    Valida primero la Ficha_JSON (reutiliza `validar_ficha_json`) y luego mapea
    sus campos al modelo interno según la decisión C5 del diseño:

    * `contexto` + `dosis.meta` -> `objetivo`
    * `que_mira_la_companera`   -> `observacion`
    * `dosis`                   -> `montaje` (cuándo, duración, jugadoras, material)
    * `dosis.jugadoras`         -> `espacio_*` / rango de jugadoras
    * `cancha`                  -> `diagrama` (`DiagramaSpec`, vía `diagram_spec`)
    * primer `media`            -> `video_url` / `video_titulo`
    * técnica de la ficha       -> `postura` (`Diagrama_Postura`, vía `figuras`)

    TOLERANCIA: importa `guia.schema` (y `guia.diagram_spec`) de forma diferida.
    Si `schema.py` todavía no existe (tarea 1.6), lanza `ErrorDependencia` con
    el mensaje "schema.py pendiente (tarea 1.6)" en vez de romper el import del
    módulo. Así `import guia.schema_json` funciona hoy y la validación/carga es
    usable de inmediato por el sitio.
    """
    validar_ficha_json(ficha, indice=indice)

    schema = _importar_diferido('schema', 'tarea 1.6')

    dosis: dict[str, Any] = ficha['dosis']

    # contexto + meta -> objetivo (una sola frase de propósito).
    partes_objetivo: list[str] = [ficha['contexto'].strip()]
    meta = dosis['meta'].strip()
    if meta:
        partes_objetivo.append(meta)
    objetivo = ' '.join(parte for parte in partes_objetivo if parte)

    # que_mira_la_companera -> observacion (líneas unidas sin concatenar en bucle).
    observacion = '\n'.join(
        linea.strip() for linea in ficha['que_mira_la_companera']
    )

    # cancha -> DiagramaSpec (reutiliza el Motor_Diagramas).
    diagrama = _cancha_a_diagrama_spec(ficha['cancha'], ficha_id=ficha['id'])

    # media -> video_url / video_titulo (primer enlace, si lo hay).
    video_url: str | None = None
    video_titulo: str | None = None
    media: list[dict[str, Any]] = ficha['media']
    if media:
        video_url = media[0]['url']
        video_titulo = media[0]['titulo']

    montaje = {
        'cuando': dosis['cuando'],
        'duracion': dosis['duracion'],
        'jugadoras': dosis['jugadoras'],
        'material': dosis['material'],
    }

    campos: dict[str, Any] = {
        'id': ficha['id'],
        'numero': ficha['numero'],
        'titulo': ficha['titulo'],
        'subtitulo': ficha['subtitulo'],
        'categoria': ficha['categoria'],
        'nivel': ficha['nivel'],
        'objetivo': objetivo,
        'pasos': tuple(ficha['pasos']),
        'observacion': observacion,
        'montaje': montaje,
        'jugadoras': dosis['jugadoras'],
        'diagrama': diagrama,
        'video_url': video_url,
        'video_titulo': video_titulo,
        # Ilustración de técnica (Diagrama_Postura) que le toca a esta ficha
        # según `guia.figuras`; `None` si no le toca ninguna (Req 9.2, 10.6).
        'postura': _postura_de_ficha_json(ficha),
    }

    fabrica = getattr(schema, 'FichaEjercicio', None)
    if fabrica is None:
        raise ErrorDependencia(
            'schema.py pendiente (tarea 1.6): guia.schema no expone '
            'FichaEjercicio todavía',
            detalle={'modulo': 'guia.schema', 'simbolo': 'FichaEjercicio'},
        )

    if not _acepta_postura(fabrica):
        del campos['postura']

    return fabrica(**campos)


def _postura_de_ficha_json(ficha: dict[str, Any]) -> Any:
    """Resuelve el `Diagrama_Postura` de una Ficha_JSON, o `None`.

    Delega en `guia.figuras.para_ficha`, que mapea la técnica de la ficha (por
    palabras clave de su `id`, `titulo`, `subtitulo` y `categoria`) al id de una
    ilustración registrada.

    Por qué es tolerante (a diferencia de `_importar_diferido`, que lanza
    `ErrorDependencia`): la ilustración de técnica es **opcional**. Que una
    ficha no la lleve es un resultado legítimo, no un error: no toda ficha es de
    golpeo. Si `guia.figuras` no estuviera disponible, el catálogo sigue siendo
    adaptable y las fichas simplemente quedan sin `postura`; el reporte del
    build lo refleja en su contador `posturas`, que es el lugar donde se ve.
    """
    try:
        figuras = __import__('guia.figuras', fromlist=['figuras'])
    except ImportError:
        return None

    resolver = getattr(figuras, 'para_ficha', None)
    if resolver is None:
        return None

    return resolver(ficha)


def _acepta_postura(fabrica: Any) -> bool:
    """¿Acepta `fabrica` el kwarg `postura`?

    `schema.FichaEjercicio` lo declara como campo opcional (default `None`), así
    que hoy la respuesta es siempre sí. Se comprueba de todas formas porque la
    fábrica se resuelve con `getattr` sobre un módulo importado de forma
    diferida: ante una versión de `schema.py` sin ese campo, el adaptador omite
    la clave en vez de reventar con `TypeError`.
    """
    declarados = getattr(fabrica, '__dataclass_fields__', None)
    if declarados is None:
        return True
    return 'postura' in declarados


def _cancha_a_diagrama_spec(cancha: dict[str, Any], *, ficha_id: str) -> Any:
    """Construye un `DiagramaSpec` a partir del campo `cancha` de la Ficha_JSON.

    Import diferido y tolerante de `guia.diagram_spec` (tarea 3.1). Devuelve
    `None` si la cancha viene vacía (sin diagrama para esta ficha).
    """
    if not cancha:
        return None

    diagram_spec = _importar_diferido('diagram_spec', 'tarea 3.1')

    constructor = getattr(diagram_spec, 'desde_cancha_json', None)
    if constructor is None:
        constructor = getattr(diagram_spec, 'DiagramaSpec', None)
    if constructor is None:
        raise ErrorDependencia(
            'diagram_spec.py pendiente (tarea 3.1): guia.diagram_spec no '
            'expone un constructor de DiagramaSpec todavía',
            detalle={'modulo': 'guia.diagram_spec', 'ficha_id': ficha_id},
        )

    return constructor(cancha)
