"""Target_Laminas: laminas verticales para telefono/WhatsApp (`dist/laminas.pdf`).

Este modulo construye el Modelo_Paginas de `dist/laminas.pdf` (Addendum A,
Target_Laminas, Req 12.6): **una lamina por ficha** en formato **vertical de
telefono** (proporcion 9:16 en puntos, NO A4), reutilizando la plantilla
`lamina_vertical` de `plantillas.py` (tarea 5.2) y el `EscritorPDF` de
`build_pdf.py`.

Fuente de contenido (regla vigente del proyecto, MODO MUESTRA): se usan **solo**
las 15 Ficha_JSON reales del Catalogo_JSON, via `cap10_fundamentos.fichas_json()`.
No se inventan fichas ni se toca el esquema JSON, los enlaces ni los QR. Cada
lamina conserva el `id` de su ficha (en el titulo/observacion) y sus **enlaces**
(los Media_Item se rinden como items de texto con su URL, para copiarse o
escanearse desde el telefono).

Formato de pagina
-----------------

La pagina es vertical de telefono, `LAMINA_ANCHO x LAMINA_ALTO` puntos con
proporcion 9:16 (alto > ancho), **no** A4. `build_pdf.escribir_pdf` recibe ese
tamano y `con_banda=False` (la banda de encabezado/pie es geometria A4 y no
aplica a las laminas). El verificador estructural (`verify_pdf`) acepta el
`/MediaBox` real de cada pagina, asi que no asume A4.

Tema claro de alto contraste, como el resto del PDF (fondo `rosa` de la
plantilla = `#FFF8FB`); la estetica esta congelada y este modulo no la altera.

Solo libreria estandar; sin `assert` (todo invariante es `raise`); type hints y
`from __future__ import annotations`; sin concatenacion de strings en bucle.

_Requirements: 12.6, 9.4, 9.9_
"""

from __future__ import annotations

from typing import Any

from .contenido import cap10_fundamentos
from .layout import Anotacion, PaginaRender, Plantilla
from .plantillas import CtxPlantilla, DatosLamina
from .plantillas import lamina_vertical as _plantilla_lamina

__all__ = [
    "CAPITULO_ID",
    "TITULO",
    "LAMINA_ANCHO",
    "LAMINA_ALTO",
    "CTX_LAMINA",
    "datos_lamina",
    "modelo",
    "escribir",
]

#: Identificador del "capitulo" del Target_Laminas (una sola coleccion).
CAPITULO_ID: str = "laminas"

#: Titulo mostrado como capitulo de cada lamina.
TITULO: str = "Laminas para compartir"

#: Tamano de pagina vertical de telefono, en puntos, proporcion 9:16 (NO A4).
#: alto > ancho por construccion (formato retrato de celular).
LAMINA_ANCHO: float = 540.0
LAMINA_ALTO: float = 960.0

#: Margen uniforme de la lamina, en puntos.
_MARGEN: float = 30.0

#: Contexto de maquetacion con la geometria de la pagina vertical de telefono.
#: La plantilla `lamina_vertical` coloca todo dentro de `[x, x+ancho]` x
#: `[y_base, y_tope]`, que aqui cae dentro de `[0, LAMINA_ANCHO]` x
#: `[0, LAMINA_ALTO]`, de modo que el verificador estructural lo acepta.
CTX_LAMINA: CtxPlantilla = CtxPlantilla(
    x=_MARGEN,
    ancho=LAMINA_ANCHO - 2.0 * _MARGEN,
    y_tope=LAMINA_ALTO - _MARGEN,
    alto=LAMINA_ALTO - 2.0 * _MARGEN,
    fuente_cuerpo="Helvetica",
    fuente_titulo="Helvetica-Bold",
    tam_cuerpo=12.0,
    tam_titulo=24.0,
)

#: Maximo de claves de "que mira la companera" que entran en una lamina. Se
#: acota para que cada lamina quepa **en una sola pagina** (formato de telefono).
_MAX_CUES: int = 3


def _lineas_dosis(dosis: dict[str, Any]) -> str | None:
    """Linea compacta de dosis para la bajada de la lamina (cuando + jugadoras)."""
    duracion = str(dosis.get("duracion", "")).strip()
    jugadoras = str(dosis.get("jugadoras", "")).strip()
    partes: list[str] = []
    if duracion:
        partes.append(f"Duracion: {duracion}")
    if jugadoras:
        partes.append(f"Jugadoras: {jugadoras}")
    return "  ".join(partes) if partes else None


def datos_lamina(ficha: dict[str, Any]) -> DatosLamina:
    """Convierte una Ficha_JSON real en el payload `DatosLamina` de la plantilla.

    Conserva el `id` de la ficha (en la bajada) y sus **enlaces** (cada
    Media_Item se rinde como un item de texto con su URL). El contenido se acota
    (dosis compacta + hasta `_MAX_CUES` claves + enlaces) para que la lamina
    quepa en una sola pagina vertical de telefono.
    """
    fid = str(ficha.get("id", "")).strip()
    titulo = str(ficha.get("titulo", "")).strip() or fid
    subtitulo = str(ficha.get("subtitulo", "")).strip()
    bajada_partes: list[str] = []
    if subtitulo:
        bajada_partes.append(subtitulo)
    if fid:
        bajada_partes.append(f"Ficha: {fid}")
    bajada = " - ".join(bajada_partes)

    items: list[str] = []
    dosis = ficha.get("dosis")
    if isinstance(dosis, dict):
        linea = _lineas_dosis(dosis)
        if linea is not None:
            items.append(linea)

    cues = ficha.get("que_mira_la_companera") or []
    for cue in cues[:_MAX_CUES]:
        texto = str(cue).strip()
        if texto:
            items.append(texto)

    for medio in ficha.get("media") or []:
        if not isinstance(medio, dict):
            continue
        url = str(medio.get("url", "")).strip()
        if not url:
            continue
        titulo_medio = str(medio.get("titulo", "")).strip()
        items.append(f"{titulo_medio}: {url}" if titulo_medio else url)

    return DatosLamina(titulo=titulo, bajada=bajada, items=items, fondo="rosa")


def modelo(fichas_json: list[dict[str, Any]] | None = None) -> list[PaginaRender]:
    """Modelo_Paginas del Target_Laminas: una `PaginaRender` vertical por ficha.

    Usa por defecto las 15 Ficha_JSON reales del Catalogo_JSON (via
    `cap10_fundamentos.fichas_json()`). Reutiliza la plantilla `lamina_vertical`
    con el contexto de pagina de telefono. Los folios se asignan consecutivos
    desde 1. La plantilla es de pagina fija (una por lamina), por lo que el
    modelo tiene tantas paginas como fichas.
    """
    crudas = cap10_fundamentos.fichas_json() if fichas_json is None else fichas_json
    render: list[PaginaRender] = []
    folio = 1
    for ficha in crudas:
        datos = datos_lamina(ficha)
        for pagina in _plantilla_lamina(datos, CTX_LAMINA):
            anotaciones: list[Anotacion] = list(pagina.anotaciones)
            render.append(
                PaginaRender(
                    folio=folio,
                    capitulo_id=CAPITULO_ID,
                    capitulo_titulo=TITULO,
                    plantilla=Plantilla.LAMINA_VERTICAL,
                    titulo_ficha=datos.titulo,
                    elementos=pagina.elementos,
                    anotaciones=anotaciones,
                )
            )
            folio += 1
    return render


def escribir(
    ruta: str,
    *,
    comprimir: bool = True,
    fichas_json: list[dict[str, Any]] | None = None,
    titulo: str = "Laminas Sub-17",
) -> list[PaginaRender]:
    """Genera el modelo del Target_Laminas y lo escribe como PDF vertical en `ruta`.

    Escribe con el tamano de pagina vertical de telefono y sin la banda A4
    (`con_banda=False`). Devuelve el Modelo_Paginas emitido (util para verificar
    el conteo de laminas y para las pruebas). Import diferido de `build_pdf`.
    """
    from . import build_pdf

    paginas = modelo(fichas_json)
    build_pdf.escribir_pdf(
        paginas,
        ruta,
        comprimir=comprimir,
        titulo=titulo,
        ancho=LAMINA_ANCHO,
        alto=LAMINA_ALTO,
        con_banda=False,
    )
    return paginas
