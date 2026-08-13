"""Paleta cromática única del proyecto (compartida por PDF y HTML/SVG).

Un solo módulo declara los colores del sistema. Los dos renderizadores del
Motor_Diagramas consumen esta paleta:

* `viz.py` (SVG / Target_Web) usa las **cadenas hex** (`#E5197F`, `#111`, ...).
* `draw.py` (operadores PDF) usa las **triplas RGB normalizadas** en `[0, 1]`
  que produce `rgb_pdf(...)`.

La Property 12 del diseño (*todo color emitido pertenece a la paleta*) se apoya
en `COLORES_PALETA` y en `es_color_valido(...)`: cualquier color que un motor
emita debe normalizar a un valor de ese conjunto.

Convenciones del proyecto respetadas:

* Solo biblioteca estándar.
* Sin `assert` en producción: `rgb_pdf` lanza `ValueError` ante un color que no
  pertenece a la paleta (error de programación, no del build).
"""

from __future__ import annotations

__all__ = [
    "ROSA",
    "NEGRO",
    "FONDO",
    "ROJO",
    "BLANCO",
    "GRISES_TRAMA",
    "PALETA",
    # Tema WEB oscuro (glass / futurista minimalista).
    "WEB_FONDO",
    "WEB_FONDO_PROFUNDO",
    "WEB_SUPERFICIE",
    "WEB_BORDE",
    "WEB_MAGENTA",
    "WEB_CORAL",
    "WEB_CIAN",
    "WEB_VIOLETA",
    "WEB_VERDE",
    "WEB_AZUL_CLARO",
    "WEB_TEXTO",
    "WEB_TEXTO_ATENUADO",
    "PALETA_WEB",
    # Paleta_Guia (tema claro del Target_Web, Requisito 16).
    "WEB_HERO_CIELO",
    "WEB_HERO_MEDIO",
    "WEB_HERO_TINTA",
    "WEB_HERO_LINEA",
    "WEB_HERO_ROSA",
    "WEB_HERO_CORAL",
    "WEB_HERO_BLANCO",
    "PALETA_GUIA",
    "SOMBRA_GUIA",
    "OSCURO_FONDO",
    "OSCURO_TEXTO",
    "CLASES_TEXTO",
    "UMBRAL_CONTRASTE",
    "COLORES_PALETA",
    "normalizar_hex",
    "es_color_valido",
    "luminancia_relativa",
    "contraste",
    "pares_declarados",
    "rgb_pdf",
]

# --------------------------------------------------------------------------- #
# Colores declarados
# --------------------------------------------------------------------------- #

#: Rosa de acento del proyecto.
ROSA: str = "#E5197F"

#: Negro (tinta principal de líneas y texto). Forma corta de `#111111`.
NEGRO: str = "#111"

#: Fondo claro del PDF (rosa muy pálido).
FONDO: str = "#FFF8FB"

#: Rojo reservado **solo** a marcas de corrección (única excepción de paleta).
ROJO: str = "#D0021B"

#: Blanco para rellenos internos (portera, rival, balón).
BLANCO: str = "#FFFFFF"

#: Grises de trama usados en los rellenos de zonas (del más claro al más oscuro).
GRISES_TRAMA: tuple[str, ...] = (
    "#EDEDED",
    "#D9D9D9",
    "#BFBFBF",
    "#9A9A9A",
    "#5A5A5A",
)

#: Mapa por nombre lógico -> color hex. Es el punto de entrada más cómodo.
PALETA: dict[str, str] = {
    "rosa": ROSA,
    "negro": NEGRO,
    "fondo": FONDO,
    "rojo": ROJO,
    "blanco": BLANCO,
}


# --------------------------------------------------------------------------- #
# Tema WEB oscuro (estética futurista minimalista tipo "glass")
# --------------------------------------------------------------------------- #
#
# Estos colores AMPLÍAN la paleta para el sitio HTML (fondo casi negro, tarjetas
# de vidrio, degradados magenta/coral). El PDF sigue usando el tema CLARO de
# alto contraste (ROSA/NEGRO/FONDO/...). Se añaden a `COLORES_PALETA` para que
# `es_color_valido`/`rgb_pdf` también los acepten, sin quitar ni cambiar los
# colores del tema claro.

#: Fondo casi negro del sitio web.
WEB_FONDO: str = "#0A0A0F"

#: Superficie base (referencia sólida de las tarjetas de vidrio translúcidas).
WEB_SUPERFICIE: str = "#14141C"

#: Borde fino (1px) de las tarjetas y separadores del tema oscuro.
WEB_BORDE: str = "#2A2A38"

#: Magenta de acento para degradados y títulos.
WEB_MAGENTA: str = "#FF2E88"

#: Coral de acento, extremo cálido del degradado magenta->coral.
WEB_CORAL: str = "#FF7A59"

# --- Neones de la dirección de arte futurista (tarea 33.4) ----------------- #
#
# Se AÑADEN al tema oscuro; no sustituyen ni retiran `WEB_MAGENTA`, `WEB_CORAL`,
# `WEB_TEXTO` ni `WEB_FONDO` (hay pruebas que afirman esas cadenas exactas). Son
# los acentos de las líneas finas tipo interfaz deportiva y de las etiquetas de
# zona; el fondo sigue siendo oscuro profundo, nunca negro absoluto.

#: Cian de interfaz: líneas finas, ejes y etiquetas de la zona visual.
WEB_CIAN: str = "#3BE8F0"

#: Violeta de profundidad: capas y sombras de color de las tarjetas.
WEB_VIOLETA: str = "#8B5CF6"

#: Verde energético: métrica, progresión y estados de "logrado".
WEB_VERDE: str = "#2EF2A0"

# --- Visor 3D del hero (tarea 34.2) --------------------------------------- #
#
# También se AÑADEN, sin quitar ni cambiar nada. `WEB_AZUL_CLARO` es el color
# protagonista del visor: todas las aristas de la malla, sus acentos y su halo
# salen de este token, para que el color siga viniendo de la paleta y no quede
# escrito a mano en el JavaScript. `WEB_FONDO_PROFUNDO` es el tono más hondo que
# pidió el usuario para el fondo del hero: se añade en vez de tocar `WEB_FONDO`,
# porque hay pruebas que afirman la cadena exacta `#0A0A0F`.

#: Azul claro protagonista del visor 3D (aristas, acentos y halo del canvas).
WEB_AZUL_CLARO: str = "#7EC8FF"

#: Fondo del hero y del canvas: oscuro más hondo que `WEB_FONDO`, nunca negro.
WEB_FONDO_PROFUNDO: str = "#050508"

#: Texto claro principal sobre el fondo oscuro.
WEB_TEXTO: str = "#F4F4FA"

#: Texto atenuado (secundario) sobre el fondo oscuro.
WEB_TEXTO_ATENUADO: str = "#A0A0B8"

# --- Paleta_Guia: tema claro del Target_Web (Requisito 16) ---------------- #
#
# SIETE tokens cerrados y UNA sola constante de Python por color (criterio
# 16.2): `WEB_HERO_CIELO` es el nombre canonico de `--azul-cielo` y
# `WEB_HERO_TINTA` el de `--azul-profundo`. Ningun valor de esta seccion se
# repite como literal en otra constante; `OSCURO_TEXTO` reusa la constante
# `WEB_HERO_CIELO` en vez de volver a escribir su hex.
#
# Los tokens del tema oscuro (`WEB_FONDO`, `WEB_FONDO_PROFUNDO`,
# `WEB_AZUL_CLARO`) NO cambian (criterio 16.17): siguen declarados arriba con su
# valor exacto y hay pruebas vigentes que lo afirman. `WEB_AZUL_CLARO`
# (`#7EC8FF`) queda restringido a las aristas, los acentos y el halo del visor
# 3D del hero (criterio 16.18).

#: `--azul-cielo`: fondo de seccion y tarjeta, relleno de silueta, inicio del
#: degradado del hero. Nombre canonico del token (criterio 16.2).
WEB_HERO_CIELO: str = "#DCEEFF"

#: `--azul-medio`: fondo de seccion y tarjeta, final del degradado del hero.
WEB_HERO_MEDIO: str = "#B8DCFA"

#: `--azul-profundo`: todo el texto de cuerpo, contorno de los diagramas y
#: texto del hero. Nombre canonico del token (criterio 16.2).
WEB_HERO_TINTA: str = "#0B2C4D"

#: `--azul-linea`: lineas guia de las Etiqueta_Anatomica y trazos secundarios.
WEB_HERO_LINEA: str = "#1E6FA8"

#: `--rosa-acento`: numeracion de pasos, subrayado del titulo, pestana activa e
#: iconos de logro. Nunca fondo de seccion ni de tarjeta (criterio 16.11).
WEB_HERO_ROSA: str = "#E85D9B"

#: `--coral-alerta`: flechas de movimiento de los diagramas y texto de error
#: (solo sobre `--blanco-suave`, criterio 16.13).
WEB_HERO_CORAL: str = "#D92D20"

#: `--blanco-suave`: fondo de seccion y tarjeta, fondo del texto de error.
WEB_HERO_BLANCO: str = "#F7FBFF"

#: Mapa token CSS -> color de la Paleta_Guia. Son exactamente los siete tokens
#: del criterio 16.1, en el orden de la tabla del diseno.
PALETA_GUIA: dict[str, str] = {
    "--azul-cielo": WEB_HERO_CIELO,
    "--azul-medio": WEB_HERO_MEDIO,
    "--azul-profundo": WEB_HERO_TINTA,
    "--azul-linea": WEB_HERO_LINEA,
    "--rosa-acento": WEB_HERO_ROSA,
    "--coral-alerta": WEB_HERO_CORAL,
    "--blanco-suave": WEB_HERO_BLANCO,
}

#: Color unico de toda sombra de la Hoja_Estilo (criterio 16.14). No es un hex:
#: lleva canal alfa, asi que vive fuera de `COLORES_PALETA`.
SOMBRA_GUIA: str = "rgba(11,44,77,0.12)"

#: Fondo del bloque `prefers-color-scheme: dark` (criterio 16.15).
OSCURO_FONDO: str = "#0B1F33"

#: Texto del bloque `prefers-color-scheme: dark` (criterio 16.15). Es el mismo
#: color que `--azul-cielo`: se declara como **alias explicito** de la
#: constante, nunca como un segundo literal (criterio 16.2).
OSCURO_TEXTO: str = WEB_HERO_CIELO

#: Mapa por nombre lógico -> color hex del tema WEB oscuro.
PALETA_WEB: dict[str, str] = {
    "web_fondo": WEB_FONDO,
    "web_fondo_profundo": WEB_FONDO_PROFUNDO,
    "web_superficie": WEB_SUPERFICIE,
    "web_borde": WEB_BORDE,
    "web_magenta": WEB_MAGENTA,
    "web_coral": WEB_CORAL,
    "web_cian": WEB_CIAN,
    "web_violeta": WEB_VIOLETA,
    "web_verde": WEB_VERDE,
    "web_azul_claro": WEB_AZUL_CLARO,
    "web_texto": WEB_TEXTO,
    "web_texto_atenuado": WEB_TEXTO_ATENUADO,
}


# --------------------------------------------------------------------------- #
# Normalización y validación
# --------------------------------------------------------------------------- #


def normalizar_hex(color: str) -> str:
    """Normaliza un color hex a la forma canónica `#rrggbb` en minúsculas.

    Acepta la forma corta de 3 dígitos (`#111` -> `#111111`) y la larga de 6.
    Lanza `ValueError` si `color` no es un hex reconocible.
    """
    if not isinstance(color, str) or not color.startswith("#"):
        raise ValueError(f"color hex invalido: {color!r}")
    cuerpo = color[1:]
    if len(cuerpo) == 3:
        cuerpo = "".join(ch * 2 for ch in cuerpo)
    if len(cuerpo) != 6:
        raise ValueError(f"color hex invalido: {color!r}")
    try:
        int(cuerpo, 16)
    except ValueError:
        raise ValueError(f"color hex invalido: {color!r}") from None
    return "#" + cuerpo.lower()


#: Conjunto normalizado de todos los colores admitidos por la paleta.
#: Incluye el tema claro del PDF (ROSA/NEGRO/FONDO/ROJO/BLANCO/GRISES_TRAMA),
#: el tema WEB oscuro (fondo casi negro, vidrio, borde, magenta/coral, textos) y
#: la Paleta_Guia con su fondo de Modo_Oscuro, que es lo que emiten el
#: Generador_SVG y el Mundo_Hero.
COLORES_PALETA: frozenset[str] = frozenset(
    normalizar_hex(c)
    for c in (
        ROSA,
        NEGRO,
        FONDO,
        ROJO,
        BLANCO,
        *GRISES_TRAMA,
        WEB_FONDO,
        WEB_FONDO_PROFUNDO,
        WEB_SUPERFICIE,
        WEB_BORDE,
        WEB_MAGENTA,
        WEB_CORAL,
        WEB_CIAN,
        WEB_VIOLETA,
        WEB_VERDE,
        WEB_AZUL_CLARO,
        WEB_TEXTO,
        WEB_TEXTO_ATENUADO,
        *PALETA_GUIA.values(),
        OSCURO_FONDO,
    )
)


def es_color_valido(color: str) -> bool:
    """Indica si `color` (hex, corto o largo) pertenece a la paleta."""
    try:
        return normalizar_hex(color) in COLORES_PALETA
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# Conversión a operadores de color PDF
# --------------------------------------------------------------------------- #


def _canal_lineal(componente: int) -> float:
    """Linealiza un componente sRGB de 0 a 255 segun WCAG 2.x."""
    normalizado: float = componente / 255.0
    if normalizado <= 0.03928:
        return normalizado / 12.92
    return ((normalizado + 0.055) / 1.055) ** 2.4


def luminancia_relativa(color: str) -> float:
    """Luminancia relativa de `color` en `[0, 1]`, segun WCAG 2.x.

    Acepta cualquier hex reconocible por `normalizar_hex` (forma corta o larga),
    pertenezca o no a la paleta: es una funcion de colorimetria, no un
    guardarrail de paleta. Un hex invalido se reporta con `ValueError`.
    """
    normal: str = normalizar_hex(color)
    rojo: float = _canal_lineal(int(normal[1:3], 16))
    verde: float = _canal_lineal(int(normal[3:5], 16))
    azul: float = _canal_lineal(int(normal[5:7], 16))
    return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul


def contraste(color_a: str, color_b: str) -> float:
    """Relacion de contraste WCAG 2.x entre dos colores, en `[1, 21]`.

    La formula es `(L_claro + 0.05) / (L_oscuro + 0.05)`: las luminancias se
    **ordenan** antes de dividir, de modo que el resultado es simetrico
    (`contraste(a, b) == contraste(b, a)`) y nunca menor que 1. El maximo, 21,
    lo alcanza el par negro/blanco puros.
    """
    luz_a: float = luminancia_relativa(color_a)
    luz_b: float = luminancia_relativa(color_b)
    clara: float = max(luz_a, luz_b)
    oscura: float = min(luz_a, luz_b)
    return (clara + 0.05) / (oscura + 0.05)


#: Clases de texto del Requisito 16: `cuerpo` exige 4.5 de contraste (criterio
#: 16.7) y `grande` exige 3.0 (criterio 16.8: texto grande, icono o trazo).
CLASES_TEXTO: frozenset[str] = frozenset({"cuerpo", "grande"})

#: Umbral de contraste minimo por clase de texto.
UMBRAL_CONTRASTE: dict[str, float] = {"cuerpo": 4.5, "grande": 3.0}

# Pares (texto, fondo, clase) que la Hoja_Estilo declara de verdad. La tupla es
# **explicita** a proposito: es el contrato de color del producto, no el producto
# cartesiano de la paleta. Incluye los pares del bloque de Modo_Oscuro (criterio
# 16.16). Consecuencias que esta lista codifica:
#
# * `--rosa-acento` nunca aparece con la clase `cuerpo` (criterio 16.10): su
#   contraste con los fondos claros no llega a 4.5, asi que solo pinta texto
#   grande, iconos y trazos.
# * `--coral-alerta` como texto de cuerpo aparece unicamente sobre
#   `--blanco-suave` (criterio 16.13); sobre `--azul-cielo` solo pinta las
#   flechas de los diagramas, que son trazo.
_PARES_DECLARADOS: tuple[tuple[str, str, str], ...] = (
    # Tema claro: texto de cuerpo en `--azul-profundo` sobre los tres fondos
    # permitidos (criterios 16.3, 16.4 y 6.4).
    (WEB_HERO_TINTA, WEB_HERO_CIELO, "cuerpo"),
    (WEB_HERO_TINTA, WEB_HERO_MEDIO, "cuerpo"),
    (WEB_HERO_TINTA, WEB_HERO_BLANCO, "cuerpo"),
    # Lineas guia y trazos secundarios.
    (WEB_HERO_LINEA, WEB_HERO_CIELO, "cuerpo"),
    (WEB_HERO_LINEA, WEB_HERO_BLANCO, "cuerpo"),
    # Acento rosa: solo texto grande, iconos y trazos.
    (WEB_HERO_ROSA, WEB_HERO_BLANCO, "grande"),
    # Coral: flechas sobre el relleno de silueta y texto de error sobre blanco.
    (WEB_HERO_CORAL, WEB_HERO_CIELO, "grande"),
    (WEB_HERO_CORAL, WEB_HERO_BLANCO, "cuerpo"),
    # Modo_Oscuro (criterios 16.15 y 16.16).
    (OSCURO_TEXTO, OSCURO_FONDO, "cuerpo"),
    (WEB_HERO_ROSA, OSCURO_FONDO, "grande"),
    (WEB_HERO_CORAL, OSCURO_FONDO, "grande"),
)


def pares_declarados() -> tuple[tuple[str, str, str], ...]:
    """Pares `(texto, fondo, clase)` de color que declara la Hoja_Estilo.

    `clase` vale `"cuerpo"` (umbral 4.5) o `"grande"` (umbral 3.0, para texto
    grande, iconos y trazos). Incluye los pares del bloque de Modo_Oscuro. Es la
    lista que recorre la propiedad de contraste; devolver la tupla tal cual es
    seguro porque las tuplas son inmutables.
    """
    return _PARES_DECLARADOS


def rgb_pdf(color: str) -> tuple[float, float, float]:
    """Convierte un color de la paleta en su tripla RGB normalizada `[0, 1]`.

    Solo acepta colores que pertenezcan a la paleta; un color ajeno indica un
    error de programación en un renderizador y se reporta con `ValueError`
    (no con `assert`, que `python -O` borraría).
    """
    normal = normalizar_hex(color)
    if normal not in COLORES_PALETA:
        raise ValueError(f"color fuera de la paleta: {color!r}")
    r = int(normal[1:3], 16) / 255.0
    g = int(normal[3:5], 16) / 255.0
    b = int(normal[5:7], 16) / 255.0
    return (r, g, b)
