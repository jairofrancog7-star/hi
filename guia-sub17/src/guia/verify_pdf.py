"""Verificador_PDF: re-parseo estructural del PDF emitido (`verify_pdf.py`).

En este entorno **no hay lector de PDF** (Riesgo 1 del diseño). Para no publicar
un archivo que no abra, este módulo re-parsea el PDF ya escrito **desde los
bytes en disco**, sin usar ninguna estructura en memoria del `EscritorPDF`: es
un verificador *independiente* del escritor. Un archivo que pasa estas pruebas
satisface las condiciones estructurales mínimas que un lector exige para abrir.

Qué comprueba (ver design.md, Validación 12 y Riesgo 1):

* **Cabecera** `%PDF-` al inicio del archivo.
* **Recorrido de la xref** entrada por entrada: cada offset en uso apunta
  exactamente a ``N 0 obj`` con el número de objeto que le corresponde.
* **`/Root` → `/Catalog` → `/Pages`**: el trailer resuelve a un `/Catalog`, que
  referencia un árbol `/Pages` cuyo `/Count` coincide con el número real de
  páginas (`/Kids`) y con el `Modelo_Paginas` esperado, si se proporciona.
* **`zlib.decompress` de todo stream de contenido**: cada stream
  `/FlateDecode` debe descomprimir sin error.
* **Balance de operadores** `BT`/`ET` y `q`/`Q` en el contenido descomprimido,
  sin cierres huérfanos ni aperturas sin cerrar.
* **`math.isfinite`** sobre cada número del contenido y **rango
  ``[0, A4_W] × [0, A4_H]``** sobre las coordenadas de los operadores de
  construcción de trazos (`m`, `l`, `c`, `v`, `y`, `re`). Los operandos de
  posicionamiento relativo de texto (`Td`, `TD`, `Tm`) y de transformación
  (`cm`) admiten valores negativos por definición, así que sobre ellos solo se
  exige finitud, nunca rango.

Errores (subclase `ErrorPDF` de `ErrorBuild`, nunca `assert` que `python -O`
borraría):

* `E_PDF_CORRUPTO`: cabecera ausente, offset que no apunta a ``N 0 obj``,
  `/Root`/`/Catalog`/`/Pages` mal resueltos, `/Count` incorrecto, stream que no
  descomprime o coordenada no finita o fuera de página.
* `E_OPERADORES_DESBALANCEADOS`: `BT` sin `ET` o `q` sin `Q` (o al revés).

Además se expone un **PDF de control de 2 páginas** (`verificar_control`) que
cada build genera y verifica como caso testigo barato para detectar regresiones
del escritor.
"""

from __future__ import annotations

import math
import re
import zlib
from dataclasses import dataclass

from .errores import E_OPERADORES_DESBALANCEADOS, E_PDF_CORRUPTO, ErrorPDF
from .layout import A4_H, A4_W

__all__ = [
    "InformePDF",
    "verificar_pdf",
    "verificar_archivo",
    "construir_modelo_control",
    "verificar_control",
]

# Tolerancia para el rango de coordenadas (el formato numérico usa 3 decimales).
_EPS: float = 1e-3

# Bytes considerados espacio en blanco por la sintaxis PDF.
_WS: bytes = b"\x00\t\n\f\r "
# Delimitadores de la sintaxis PDF.
_DELIM: bytes = b"()<>[]{}/%"
# Caracteres que pueden formar un token numérico.
_NUM_CHARS: frozenset[int] = frozenset(b"0123456789+-.")

# Operadores de construcción de trazo cuyos operandos son coordenadas absolutas
# de página, y cuántos operandos de coordenada consumen.
_OPS_TRAZO: dict[bytes, int] = {
    b"m": 2,
    b"l": 2,
    b"c": 6,
    b"v": 4,
    b"y": 4,
    b"re": 4,
}


@dataclass(frozen=True, slots=True)
class InformePDF:
    """Resumen de lo verificado: objetos, páginas y streams de contenido."""

    objetos: int
    paginas: int
    streams: int


# --------------------------------------------------------------------------- #
# Utilidades de bajo nivel para recorrer los bytes del PDF
# --------------------------------------------------------------------------- #


def _saltar_ws(datos: bytes, i: int) -> int:
    """Avanza `i` sobre espacios en blanco y comentarios `%...`."""
    n = len(datos)
    while i < n:
        c = datos[i]
        if c in _WS:
            i += 1
        elif c == 0x25:  # '%' comentario hasta fin de línea
            while i < n and datos[i] not in b"\r\n":
                i += 1
        else:
            break
    return i


def _fin_dict(datos: bytes, i: int) -> int:
    """Índice justo después del `>>` que cierra el diccionario que abre en `i`.

    Rastrea la profundidad de `<< >>` saltando literales `(...)` (con escapes) y
    cadenas hexadecimales `<...>`, para no confundir un `>>` que viva dentro de
    una cadena con el cierre del diccionario.
    """
    n = len(datos)
    if datos[i : i + 2] != b"<<":
        raise ErrorPDF(
            "se esperaba '<<' al inicio de un diccionario",
            codigo=E_PDF_CORRUPTO,
            detalle={"offset": i},
        )
    profundidad = 0
    while i < n:
        par = datos[i : i + 2]
        if par == b"<<":
            profundidad += 1
            i += 2
        elif par == b">>":
            profundidad -= 1
            i += 2
            if profundidad == 0:
                return i
        elif datos[i] == 0x28:  # '(' literal de cadena
            i = _fin_cadena(datos, i)
        elif datos[i] == 0x3C:  # '<' cadena hexadecimal (no era '<<')
            fin = datos.find(b">", i)
            i = n if fin < 0 else fin + 1
        else:
            i += 1
    raise ErrorPDF(
        "diccionario sin cierre '>>'",
        codigo=E_PDF_CORRUPTO,
        detalle={"offset": i},
    )


def _fin_cadena(datos: bytes, i: int) -> int:
    """Índice justo después del `)` que cierra el literal `(...)` que abre en `i`."""
    n = len(datos)
    i += 1  # consumir '('
    profundidad = 1
    while i < n:
        c = datos[i]
        if c == 0x5C:  # '\' escapa el siguiente byte
            i += 2
            continue
        if c == 0x28:  # '('
            profundidad += 1
        elif c == 0x29:  # ')'
            profundidad -= 1
            if profundidad == 0:
                return i + 1
        i += 1
    return n


# --------------------------------------------------------------------------- #
# Xref, objetos y referencias
# --------------------------------------------------------------------------- #

_RE_STARTXREF = re.compile(rb"startxref\s+(\d+)\s+%%EOF", re.DOTALL)
_RE_SUBSECCION = re.compile(rb"\s*(\d+)\s+(\d+)\s*\r?\n")
_RE_OBJ_CABECERA = re.compile(rb"\s*(\d+)\s+(\d+)\s+obj")
_RE_REF = re.compile(rb"(\d+)\s+(\d+)\s+R")


def _leer_startxref(datos: bytes) -> int:
    """Offset de la última tabla xref (último `startxref ... %%EOF`)."""
    ult = None
    for m in _RE_STARTXREF.finditer(datos):
        ult = m
    if ult is None:
        raise ErrorPDF(
            "no se encontró 'startxref ... %%EOF'",
            codigo=E_PDF_CORRUPTO,
        )
    return int(ult.group(1))


def _parsear_xref(datos: bytes, inicio: int) -> tuple[dict[int, int], bytes]:
    """Recorre la xref clásica y devuelve `(offsets_en_uso, trailer_dict)`."""
    if datos[inicio : inicio + 4] != b"xref":
        raise ErrorPDF(
            "startxref no apunta a la palabra 'xref'",
            codigo=E_PDF_CORRUPTO,
            detalle={"inicio": inicio},
        )
    i = inicio + 4
    offsets: dict[int, int] = {}
    n = len(datos)
    while True:
        j = _saltar_ws(datos, i)
        if datos[j : j + 7] == b"trailer":
            i = j + 7
            break
        m = _RE_SUBSECCION.match(datos, i)
        if m is None:
            raise ErrorPDF(
                "cabecera de subsección xref inválida",
                codigo=E_PDF_CORRUPTO,
                detalle={"offset": i},
            )
        primero = int(m.group(1))
        cuenta = int(m.group(2))
        p = m.end()
        for k in range(cuenta):
            entrada = datos[p : p + 20]
            if len(entrada) < 18:
                raise ErrorPDF(
                    "entrada xref truncada",
                    codigo=E_PDF_CORRUPTO,
                    detalle={"objeto": primero + k},
                )
            tipo = entrada[17:18]
            if tipo == b"n":
                offsets[primero + k] = int(entrada[0:10])
            p += 20
        i = p
        if i >= n:
            raise ErrorPDF(
                "xref sin 'trailer'", codigo=E_PDF_CORRUPTO
            )
    fin_ws = _saltar_ws(datos, i)
    trailer = datos[fin_ws : _fin_dict(datos, fin_ws)]
    return offsets, trailer


def _leer_objeto(datos: bytes, offset: int, num: int) -> tuple[bytes, bytes | None]:
    """Lee el objeto `num` en `offset`. Devuelve `(dict_o_valor, stream|None)`.

    Confirma que el offset apunta exactamente a ``N 0 obj`` con el número
    esperado (recorrido de la xref). Para objetos de stream, devuelve además los
    bytes crudos del stream (aún comprimidos si llevan `/FlateDecode`).
    """
    m = _RE_OBJ_CABECERA.match(datos, offset)
    if m is None or int(m.group(1)) != num:
        halo = datos[offset : offset + 24]
        raise ErrorPDF(
            f"el offset del objeto {num} no apunta a '{num} 0 obj'",
            codigo=E_PDF_CORRUPTO,
            detalle={"objeto": num, "offset": offset, "bytes": repr(halo)},
        )
    j = _saltar_ws(datos, m.end())
    if datos[j : j + 2] == b"<<":
        fin = _fin_dict(datos, j)
        dic = datos[j:fin]
        k = _saltar_ws(datos, fin)
        if datos[k : k + 6] == b"stream":
            k += 6
            if datos[k : k + 2] == b"\r\n":
                k += 2
            elif datos[k : k + 1] in (b"\n", b"\r"):
                k += 1
            mlen = re.search(rb"/Length\s+(\d+)", dic)
            if mlen is not None:
                largo = int(mlen.group(1))
                cuerpo = datos[k : k + largo]
                if datos[_saltar_ws(datos, k + largo) : _saltar_ws(datos, k + largo) + 9] != b"endstream":
                    raise ErrorPDF(
                        f"stream del objeto {num} sin 'endstream' tras /Length",
                        codigo=E_PDF_CORRUPTO,
                        detalle={"objeto": num},
                    )
            else:
                fin_s = datos.find(b"endstream", k)
                if fin_s < 0:
                    raise ErrorPDF(
                        f"stream del objeto {num} sin 'endstream'",
                        codigo=E_PDF_CORRUPTO,
                        detalle={"objeto": num},
                    )
                cuerpo = datos[k:fin_s]
            return dic, cuerpo
        return dic, None
    fin_v = datos.find(b"endobj", j)
    if fin_v < 0:
        raise ErrorPDF(
            f"objeto {num} sin 'endobj'",
            codigo=E_PDF_CORRUPTO,
            detalle={"objeto": num},
        )
    return datos[j:fin_v], None


_RE_MEDIABOX = re.compile(rb"/MediaBox\s*\[([^\]]*)\]")
_RE_NUMERO = re.compile(rb"[-+]?(?:\d+\.\d*|\.\d+|\d+)")


def _leer_mediabox(
    dic: bytes, *, respaldo: tuple[float, float] = (A4_W, A4_H)
) -> tuple[float, float]:
    """Ancho y alto en puntos leídos del `/MediaBox` de un diccionario.

    El `/MediaBox` es `[x0 y0 x1 y1]`; el ancho es `x1 - x0` y el alto `y1 - y0`.
    Si el diccionario no declara `/MediaBox` (o viene mal formado), devuelve el
    `respaldo` (por defecto A4, o el `/MediaBox` heredado del árbol `/Pages`).
    Nunca lanza: es una lectura de respaldo, y el rango se comprueba después.
    """
    m = _RE_MEDIABOX.search(dic)
    if m is None:
        return respaldo
    nums = [float(x) for x in _RE_NUMERO.findall(m.group(1))]
    if len(nums) < 4:
        return respaldo
    ancho = abs(nums[2] - nums[0])
    alto = abs(nums[3] - nums[1])
    if ancho <= 0.0 or alto <= 0.0:
        return respaldo
    return ancho, alto


def _ref(dic: bytes, clave: bytes) -> int:
    """Número de objeto referido por `clave` (`/Clave N 0 R`) dentro de `dic`."""
    m = re.search(re.escape(clave) + rb"\s+(\d+)\s+(\d+)\s+R", dic)
    if m is None:
        raise ErrorPDF(
            f"falta la referencia {clave.decode('ascii')} en el diccionario",
            codigo=E_PDF_CORRUPTO,
            detalle={"clave": clave.decode("ascii")},
        )
    return int(m.group(1))


# --------------------------------------------------------------------------- #
# Balance de operadores y validez de coordenadas en un stream de contenido
# --------------------------------------------------------------------------- #


def _detalle_stream(folio: int | None, recurso: str) -> dict[str, object]:
    detalle: dict[str, object] = {"recurso": recurso}
    if folio is not None:
        detalle["folio"] = folio
    return detalle


def _revisar_contenido(
    contenido: bytes,
    *,
    folio: int | None,
    recurso: str,
    limite_w: float = A4_W,
    limite_h: float = A4_H,
) -> None:
    """Verifica balance `BT/ET` y `q/Q`, finitud y rango de coordenadas.

    `limite_w`/`limite_h` son el ancho y alto reales de la página (leídos de su
    `/MediaBox`), no un A4 fijo: así el verificador acepta páginas verticales de
    teléfono además del A4 por defecto.

    Recorre el stream token a token saltando literales de cadena y nombres para
    no interpretar su interior como números u operadores. Acumula los operandos
    numéricos previos a cada operador y, cuando el operador construye trazo,
    valida que sus coordenadas sean finitas y caigan en la página.
    """
    n = len(contenido)
    i = 0
    prof_bt = 0
    prof_q = 0
    operandos: list[float] = []
    while i < n:
        c = contenido[i]
        if c in _WS:
            i += 1
            continue
        if c == 0x28:  # '(' literal de cadena de texto
            i = _fin_cadena(contenido, i)
            operandos.clear()
            continue
        if c == 0x2F:  # '/' nombre
            i += 1
            while i < n and contenido[i] not in _WS and contenido[i] not in _DELIM:
                i += 1
            continue
        if c == 0x25:  # '%' comentario
            while i < n and contenido[i] not in b"\r\n":
                i += 1
            continue
        if c == 0x3C:  # '<' cadena hex o '<<'
            if contenido[i : i + 2] == b"<<":
                i += 2
            else:
                fin = contenido.find(b">", i)
                i = n if fin < 0 else fin + 1
            operandos.clear()
            continue
        if c in b">[]{}":
            i += 1
            continue
        if c in _NUM_CHARS:
            ini = i
            i += 1
            while i < n and contenido[i] in _NUM_CHARS:
                i += 1
            token = contenido[ini:i]
            try:
                valor = float(token)
            except ValueError:
                operandos.clear()
                continue
            if not math.isfinite(valor):
                raise ErrorPDF(
                    f"coordenada no finita en el contenido: {token!r}",
                    codigo=E_PDF_CORRUPTO,
                    detalle=_detalle_stream(folio, recurso),
                )
            operandos.append(valor)
            continue
        # Operador: run de caracteres regulares.
        ini = i
        i += 1
        while i < n and contenido[i] not in _WS and contenido[i] not in _DELIM:
            i += 1
        op = contenido[ini:i]
        if op == b"BT":
            prof_bt += 1
        elif op == b"ET":
            prof_bt -= 1
            if prof_bt < 0:
                raise ErrorPDF(
                    "operador 'ET' sin 'BT' previo",
                    codigo=E_OPERADORES_DESBALANCEADOS,
                    detalle=_detalle_stream(folio, recurso),
                )
        elif op == b"q":
            prof_q += 1
        elif op == b"Q":
            prof_q -= 1
            if prof_q < 0:
                raise ErrorPDF(
                    "operador 'Q' sin 'q' previo",
                    codigo=E_OPERADORES_DESBALANCEADOS,
                    detalle=_detalle_stream(folio, recurso),
                )
        elif op in _OPS_TRAZO:
            _validar_coordenadas(
                op, operandos, folio=folio, recurso=recurso,
                limite_w=limite_w, limite_h=limite_h,
            )
        operandos.clear()

    if prof_bt != 0:
        raise ErrorPDF(
            f"bloques de texto sin cerrar: faltan {prof_bt} 'ET'",
            codigo=E_OPERADORES_DESBALANCEADOS,
            detalle=_detalle_stream(folio, recurso),
        )
    if prof_q != 0:
        raise ErrorPDF(
            f"estados gráficos sin cerrar: faltan {prof_q} 'Q'",
            codigo=E_OPERADORES_DESBALANCEADOS,
            detalle=_detalle_stream(folio, recurso),
        )


def _validar_coordenadas(
    op: bytes,
    operandos: list[float],
    *,
    folio: int | None,
    recurso: str,
    limite_w: float = A4_W,
    limite_h: float = A4_H,
) -> None:
    """Comprueba que las coordenadas de un operador de trazo caen en la página.

    Para `m`/`l`/`c`/`v`/`y` las coordenadas alternan x, y, x, y…; para `re` son
    `x y w h`. Se valida el bloque final de operandos que consume el operador
    (los anteriores pertenecen a operadores ya cerrados de la misma línea).
    `limite_w`/`limite_h` son el tamaño real de la página (su `/MediaBox`).
    """
    consume = _OPS_TRAZO[op]
    if len(operandos) < consume:
        return  # operandos insuficientes: la finitud ya quedó comprobada
    coords = operandos[-consume:]
    if op == b"re":
        pares = (
            (coords[0], limite_w),
            (coords[1], limite_h),
            (coords[2], limite_w),
            (coords[3], limite_h),
        )
        for valor, limite in pares:
            _rango(valor, limite, op, folio=folio, recurso=recurso)
        return
    for idx, valor in enumerate(coords):
        limite = limite_w if idx % 2 == 0 else limite_h
        _rango(valor, limite, op, folio=folio, recurso=recurso)


def _rango(
    valor: float, limite: float, op: bytes, *, folio: int | None, recurso: str
) -> None:
    if valor < -_EPS or valor > limite + _EPS:
        raise ErrorPDF(
            f"coordenada {valor:.3f} del operador '{op.decode('ascii')}' "
            f"fuera de la página [0, {limite:.3f}]",
            codigo=E_PDF_CORRUPTO,
            detalle=_detalle_stream(folio, recurso),
        )


# --------------------------------------------------------------------------- #
# Verificación de alto nivel
# --------------------------------------------------------------------------- #


def verificar_pdf(datos: bytes, *, paginas_esperadas: int | None = None) -> InformePDF:
    """Re-parsea y verifica el PDF `datos`. Lanza `ErrorPDF` si algo falla.

    `paginas_esperadas`, si se da, es el número de páginas del `Modelo_Paginas`;
    debe coincidir con el `/Count` del árbol `/Pages` y con la cantidad real de
    hojas en `/Kids`.
    """
    if not datos.startswith(b"%PDF-"):
        raise ErrorPDF(
            "el archivo no empieza con la cabecera '%PDF-'",
            codigo=E_PDF_CORRUPTO,
            detalle={"cabecera": repr(datos[:8])},
        )

    inicio_xref = _leer_startxref(datos)
    offsets, trailer = _parsear_xref(datos, inicio_xref)

    # Recorrido de la xref: cada offset en uso apunta a 'N 0 obj'.
    dicts: dict[int, bytes] = {}
    streams: dict[int, bytes] = {}
    for num, offset in offsets.items():
        dic, cuerpo = _leer_objeto(datos, offset, num)
        dicts[num] = dic
        if cuerpo is not None:
            streams[num] = cuerpo

    # /Root -> /Catalog -> /Pages
    raiz_num = _ref(trailer, b"/Root")
    catalogo = dicts.get(raiz_num)
    if catalogo is None or not re.search(rb"/Type\s*/Catalog", catalogo):
        raise ErrorPDF(
            "el /Root no resuelve a un objeto /Catalog",
            codigo=E_PDF_CORRUPTO,
            detalle={"root": raiz_num},
        )
    pages_num = _ref(catalogo, b"/Pages")
    pages = dicts.get(pages_num)
    if pages is None or not re.search(rb"/Type\s*/Pages", pages):
        raise ErrorPDF(
            "el /Pages del catálogo no resuelve a un árbol /Pages",
            codigo=E_PDF_CORRUPTO,
            detalle={"pages": pages_num},
        )

    m_count = re.search(rb"/Count\s+(\d+)", pages)
    if m_count is None:
        raise ErrorPDF(
            "el árbol /Pages no declara /Count",
            codigo=E_PDF_CORRUPTO,
            detalle={"pages": pages_num},
        )
    count = int(m_count.group(1))

    m_kids = re.search(rb"/Kids\s*\[([^\]]*)\]", pages, re.DOTALL)
    if m_kids is None:
        raise ErrorPDF(
            "el árbol /Pages no declara /Kids",
            codigo=E_PDF_CORRUPTO,
            detalle={"pages": pages_num},
        )
    kids = [int(x) for x, _ in _RE_REF.findall(m_kids.group(1))]

    if count != len(kids):
        raise ErrorPDF(
            f"/Count ({count}) distinto del número de páginas en /Kids ({len(kids)})",
            codigo=E_PDF_CORRUPTO,
            detalle={"count": count, "kids": len(kids)},
        )
    if paginas_esperadas is not None and count != paginas_esperadas:
        raise ErrorPDF(
            f"/Count ({count}) distinto del Modelo_Paginas esperado "
            f"({paginas_esperadas})",
            codigo=E_PDF_CORRUPTO,
            detalle={"count": count, "esperado": paginas_esperadas},
        )

    # /MediaBox heredado del árbol /Pages (si lo declara), usado como respaldo.
    media_arbol = _leer_mediabox(pages)

    # Mapa de stream de contenido de página -> folio (orden de /Kids) y ->
    # tamaño real de la página (su /MediaBox), para acotar las coordenadas por
    # página en lugar de asumir A4 (soporta láminas verticales de teléfono).
    folio_de_stream: dict[int, int] = {}
    limites_de_stream: dict[int, tuple[float, float]] = {}
    for indice, pagina_num in enumerate(kids):
        pagina = dicts.get(pagina_num)
        if pagina is None or not re.search(rb"/Type\s*/Page\b", pagina):
            raise ErrorPDF(
                f"la hoja {pagina_num} de /Kids no resuelve a un /Page",
                codigo=E_PDF_CORRUPTO,
                detalle={"pagina": pagina_num, "folio": indice + 1},
            )
        contenido_num = _ref(pagina, b"/Contents")
        folio_de_stream[contenido_num] = indice + 1
        limites_de_stream[contenido_num] = _leer_mediabox(pagina, respaldo=media_arbol)

    # zlib.decompress de todo stream de contenido + balance/rango de operadores.
    for num, crudo in streams.items():
        dic = dicts[num]
        if b"/FlateDecode" in dic:
            try:
                contenido = zlib.decompress(crudo)
            except zlib.error as exc:
                raise ErrorPDF(
                    f"el stream del objeto {num} no descomprime: {exc}",
                    codigo=E_PDF_CORRUPTO,
                    detalle=_detalle_stream(folio_de_stream.get(num), f"obj {num}"),
                ) from exc
        else:
            contenido = crudo
        folio = folio_de_stream.get(num)
        recurso = f"pagina {folio}" if folio is not None else f"obj {num}"
        limite_w, limite_h = limites_de_stream.get(num, (A4_W, A4_H))
        _revisar_contenido(
            contenido, folio=folio, recurso=recurso,
            limite_w=limite_w, limite_h=limite_h,
        )

    return InformePDF(objetos=len(offsets), paginas=count, streams=len(streams))


def verificar_archivo(ruta: str, *, paginas_esperadas: int | None = None) -> InformePDF:
    """Lee el PDF en `ruta` y lo verifica con `verificar_pdf`."""
    with open(ruta, "rb") as fh:
        datos = fh.read()
    return verificar_pdf(datos, paginas_esperadas=paginas_esperadas)


# --------------------------------------------------------------------------- #
# PDF de control de 2 páginas (caso testigo de cada build)
# --------------------------------------------------------------------------- #


def construir_modelo_control() -> list:
    """Modelo_Paginas mínimo de 2 páginas para el caso de control del build.

    Usa solo texto (que ejercita `BT/ET`) sobre la banda compartida (que
    ejercita `q/Q`), de modo que el verificador recorra un PDF real y pequeño.
    """
    from .layout import (
        AREA_W,
        ElementoRender,
        PaginaRender,
        Plantilla,
        TextoDatos,
        TipoElemento,
    )

    def _pagina(folio: int, texto: str) -> "object":
        pagina = PaginaRender(
            folio=folio,
            capitulo_id="control",
            capitulo_titulo="PDF de control",
            plantilla=Plantilla.TEXTO,
        )
        pagina.elementos.append(
            ElementoRender(
                tipo=TipoElemento.TEXTO,
                x=46.0,
                y=700.0,
                w=AREA_W,
                h=40.0,
                datos=TextoDatos(texto=texto, fuente="Helvetica", tamano=11.0),
            )
        )
        return pagina

    return [
        _pagina(1, "Pagina de control uno: verificacion estructural del PDF."),
        _pagina(2, "Pagina de control dos: acentos y enie (Cafe, nino, pena)."),
    ]


def verificar_control() -> InformePDF:
    """Genera y verifica el PDF de control de 2 páginas.

    Punto de autochequeo barato del escritor en cada build: si el `EscritorPDF`
    regresiona, este control falla con `E_PDF_CORRUPTO` sin necesidad del
    catálogo completo.
    """
    from . import build_pdf

    modelo = construir_modelo_control()
    datos = build_pdf.documento_a_bytes(modelo, comprimir=True, titulo="Control")
    return verificar_pdf(datos, paginas_esperadas=2)
