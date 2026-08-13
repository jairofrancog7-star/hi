"""Ayudante compartido del Guardarrail_Recursos: lectura del marcado emitido.

Feature `imagenes-reales-hero-interactivo`, tarea 14.2.

El Requisito 1 no se puede comprobar con busquedas de subcadena: la pregunta es
**de contexto**. La cadena `http` en un atributo `src` es una peticion de red y
la misma cadena en el `xmlns` de un `<svg>` en linea es una declaracion de
espacio de nombres que no descarga nada; un `<img src="assets/...">` es un
Asset_Local legitimo y un `<img src="https://...">` es un Recurso_Externo. Por
eso el guardarrail lee el marcado con `html.parser.HTMLParser` y clasifica cada
aparicion por la etiqueta y el atributo en que vive.

Este modulo nacio dentro de `test_assets_diagramas.py` (Property 14, tarea 13.6)
y se extrajo aqui cuando la tarea 14.2 amplio el Guardarrail_Recursos de
`test_build_site.py`: las dos pruebas miden lo mismo sobre el mismo documento, y
duplicar el lector habria dejado dos definiciones que podrian discrepar.

No es un modulo de prueba: `_run_tests.py` descubre con el patron `test*.py`, asi
que este archivo solo se importa. Solo libreria estandar.

_Requirements: 1.1, 1.2, 1.3, 1.4, 1.8, 1.9, 1.10, 30.8, 30.9_
"""

from __future__ import annotations

from html.parser import HTMLParser

#: Etiquetas que descargan un subrecurso en cuanto el navegador las encuentra.
#: Un `http` en uno de sus atributos de URL si es una peticion de red, y por eso
#: el Guardarrail_Recursos las mira una por una (criterios 1.2 y 1.10).
ETIQUETAS_CARGADORAS: tuple[str, ...] = (
    "img",
    "image",
    "script",
    "link",
    "iframe",
    "embed",
    "object",
    "source",
    "video",
    "audio",
    "track",
    "use",
)

#: Atributos por los que una etiqueta cargadora trae su subrecurso.
ATRIBUTOS_RECURSO: tuple[str, ...] = ("src", "srcset", "data", "poster")

#: Contextos donde la cadena `http` **no** provoca ninguna peticion de red y el
#: Guardarrail_Recursos la acepta: el `xmlns` de los `<svg>` en linea heredados
#: (`viz.py`, el QR de `build_html.py` y `escena3d.py`), que es una declaracion de
#: espacio de nombres, y el `href` de los enlaces de video de las 58 fichas, que
#: es navegacion que la usuaria decide, no un subrecurso que el documento cargue.
#: Cualquier otro par etiqueta-atributo con `http` es un fallo del guardarrail.
CONTEXTOS_HTTP_PERMITIDOS: tuple[tuple[str, str], ...] = (
    ("svg", "xmlns"),
    ("a", "href"),
)

#: Clases de los elementos que rotulan **con su propia URL** un enlace de
#: navegacion. El Target_Web imprime la direccion del video junto al enlace y al
#: codigo QR para que se pueda teclear a mano, asi que ahi la cadena `http` vive
#: en un nodo de texto sin ser un subrecurso (criterio 30.9).
CLASES_URL_VISIBLE: tuple[str, ...] = ("enlace-visible",)

#: Etiquetas sin cierre: no entran en la pila de anidamiento.
ETIQUETAS_VACIAS: frozenset[str] = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


class LectorRecursos(HTMLParser):
    """Extrae del marcado los atributos de recurso, el `<script>` y el `<style>`.

    Se lee con `html.parser.HTMLParser` y no con busquedas de subcadena porque la
    pregunta del Requisito 1 es **de contexto**: un `http` en un `src` es una
    peticion de red y el mismo `http` en un nodo de texto del Bloque_Creditos es
    el enlace del credito. Buscar `"http"` a ciegas no distingue los dos casos.

    `en_creditos` sigue la `<section class="... seccion-creditos">` contando la
    profundidad de secciones anidadas, de modo que el texto y los atributos
    quedan marcados con el bloque al que pertenecen.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        #: Conteo por nombre de etiqueta.
        self.etiquetas: dict[str, int] = {}
        #: Pares `(etiqueta, valor)` de todo atributo `src` del documento.
        self.srcs: list[tuple[str, str]] = []
        #: Ternas `(etiqueta, atributo, valor)` de los subrecursos declarados.
        self.recursos: list[tuple[str, str, str]] = []
        #: Cuadruples `(etiqueta, atributo, valor, en_creditos)` con `http`.
        self.atributos_http: list[tuple[str, str, str, bool]] = []
        #: Pares `(texto, en_creditos)` de los nodos de texto con `http`.
        self.texto_http: list[tuple[str, bool]] = []
        #: Ternas `(texto, en_creditos, es_rotulo)` de los mismos nodos. El
        #: tercer dato distingue el rotulo visible de un enlace de navegacion
        #: (los enlaces de video de las 58 fichas se rotulan con su propia URL,
        #: dentro del `<a>` o en el `<span class="enlace-visible">` que la imprime
        #: para teclearla a mano) del `http` suelto en la prosa, que si seria un
        #: fallo del guardarrail.
        self.texto_http_ctx: list[tuple[str, bool, bool]] = []
        #: Cuerpo de cada `<script>` y de cada `<style>`.
        self.scripts: list[str] = []
        self.estilos: list[str] = []
        #: Identificadores de las entradas del Bloque_Creditos y sus campos.
        self.creditos: list[str] = []
        self.campos: list[tuple[str, str]] = []
        #: Elementos `<a>` dentro del Bloque_Creditos (criterios 1.8 y 18.5).
        self.enlaces_en_creditos: int = 0
        self.en_creditos: bool = False
        self._prof_seccion: int = 0
        self._en_script: bool = False
        self._en_estilo: bool = False
        self._campo: str | None = None
        #: Pila de elementos abiertos con la marca de "rotulo de enlace": el
        #: propio `<a>` y los elementos de `CLASES_URL_VISIBLE`.
        self._pila: list[tuple[str, bool]] = []

    @property
    def en_rotulo_de_enlace(self) -> bool:
        """True mientras la lectura va dentro del rotulo de un enlace."""
        return any(marca for _, marca in self._pila)

    def handle_starttag(self, tag: str, attrs: list) -> None:  # noqa: D102
        self.etiquetas[tag] = self.etiquetas.get(tag, 0) + 1
        mapa: dict[str, str] = {n: (v or "") for n, v in attrs}
        clases: str = mapa.get("class", "")
        if tag not in ETIQUETAS_VACIAS:
            rotulo: bool = tag == "a" or any(
                c in clases for c in CLASES_URL_VISIBLE
            )
            self._pila.append((tag, rotulo))
        if tag == "section":
            if self.en_creditos:
                self._prof_seccion += 1
            elif "seccion-creditos" in mapa.get("class", ""):
                self.en_creditos = True
                self._prof_seccion = 1
        if tag == "script":
            self._en_script = True
        if tag == "style":
            self._en_estilo = True
        if tag == "a" and self.en_creditos:
            self.enlaces_en_creditos += 1
        if "data-credito" in mapa:
            self.creditos.append(mapa["data-credito"])
        if tag == "dd" and "data-campo" in mapa:
            self._campo = mapa["data-campo"]
        for nombre, valor in mapa.items():
            if nombre == "src":
                self.srcs.append((tag, valor))
            if tag in ETIQUETAS_CARGADORAS and (
                nombre in ATRIBUTOS_RECURSO or (tag == "link" and nombre == "href")
            ):
                self.recursos.append((tag, nombre, valor))
            if "http" in valor.lower():
                self.atributos_http.append((tag, nombre, valor, self.en_creditos))

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        # Se cierra hasta la etiqueta que corresponde: asi una etiqueta sin
        # cierre explicito no desalinea la pila para el resto del documento.
        for indice in range(len(self._pila) - 1, -1, -1):
            if self._pila[indice][0] == tag:
                del self._pila[indice:]
                break
        if tag == "script":
            self._en_script = False
        if tag == "style":
            self._en_estilo = False
        if tag == "dd":
            self._campo = None
        if tag == "section" and self.en_creditos:
            self._prof_seccion -= 1
            if self._prof_seccion <= 0:
                self.en_creditos = False

    def handle_data(self, data: str) -> None:  # noqa: D102
        if self._en_script:
            self.scripts.append(data)
        if self._en_estilo:
            self.estilos.append(data)
        if self._campo is not None:
            self.campos.append((self._campo, data))
        if "http" in data.lower():
            self.texto_http.append((data, self.en_creditos))
            self.texto_http_ctx.append(
                (data, self.en_creditos, self.en_rotulo_de_enlace)
            )


def leer(documento: str) -> LectorRecursos:
    """Devuelve el `LectorRecursos` ya alimentado y cerrado con `documento`."""
    lector = LectorRecursos()
    lector.feed(documento)
    lector.close()
    return lector
