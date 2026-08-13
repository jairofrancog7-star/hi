# BLOQUEO DE CONTENIDO — RESUELTO

Fecha de desbloqueo: 2026-08-08
Última actualización de este documento: **2026-08-08**

> Este archivo nació como registro de un bloqueo (faltaban los HTML de origen y
> no se quiso inventar contenido). El bloqueo está **cerrado** desde 2026-08-08.
> Lo que sigue son los números vigentes, no los de aquella fecha.

## Resumen ejecutivo

- **Desbloqueado por Vía B**, con autorización explícita del usuario para
  redactar contenido práctico propio para Sub-17.
- La guía es **PUBLICABLE** en `MODO_ESTRICTO`: cumple los tres umbrales.
- Suite completa en verde: **292 tests, 0 fallos, 0 errores, ok=True** (corrida
  limpia tras borrar los tres `__pycache__`).
- Build completo en **10.6 s**, muy por debajo del límite de 120 s del Req 10.7.
  Desglose: QR 6.8 s, PDF 2.8 s, y todo lo demás por debajo de 0.4 s. Por eso la
  caché en disco de la tarea 13.5 se descartó: no hay nada que optimizar.
- **13 validaciones** ejecutadas en cada corrida: preflight, esquema_json,
  sin_fichas_en_modulos, codificacion_winansi, unicidad_rotacion, qr_round_trip,
  verify_pdf, pdf_control, indice_coherente, sitio_un_archivo,
  guia_una_ficha_por_hoja, laminas_vertical y json_crudo_dist.

## Umbrales de publicación (REVISADOS) — TODOS CUMPLIDOS

PUBLICABLE solo si se cumplen **los tres a la vez**:

| Umbral                            | Requerido         | Actual | ¿Cumple? |
|-----------------------------------|-------------------|--------|----------|
| Páginas del modelo (`_paginar()`) | **>= 100**        | 169    | Sí       |
| Fichas únicas                     | **entre 45 y 60** | 58     | Sí       |
| Semanas (bloques de rotación)     | **>= 12**         | 26     | Sí       |

`python src/build.py --estricto` reporta **[PUBLICABLE]**.

Ojo con dos campos del reporte que se confunden fácil:

- `paginas modelo : 169` es **el valor que evalúa el umbral**.
- `paginas totales : 58` cuenta las hojas del PDF de fichas, una por ficha. No
  es el gate.

## Catálogo de fichas

- `contenido/ejercicios.json`: **58 fichas** (15 heredadas + 43 propias), con
  **58 ids únicos y 58 numeros únicos**.
- Las **58 de 58** están completas en los cinco campos obligatorios: `dosis`,
  progresión, métrica de mejora, diagrama de `cancha` y variante para 1-8
  jugadoras. **0 incompletas**.
- Lo blinda `test/test_guardarrail_completitud_fichas.py`, que falla nombrando
  `numero`, `id` y el campo faltante. Acepta las dos grafías que conviven en el
  catálogo (`Progresion:` y `Progresión:`) normalizando los diacríticos.

## Capítulos de prosa

Cableados en `contenido/__init__.py`, con las páginas que ocupan hoy:

| Módulo                 | Páginas |
|------------------------|---------|
| `cap00_portada`        | 8       |
| `cap10_fundamentos`    | fichas  |
| `cap20_posiciones`     | 9       |
| `cap30_colectivo`      | 8       |
| `cap40_prevencion`     | 9       |
| `cap50_mental`         | 7       |
| `cap60_periodizacion`  | 8       |
| `cap80_apendices`      | 6       |

Varios quedan por debajo del presupuesto original del plan (por ejemplo
prevención, presupuestada en ~30 páginas). La razón está escrita en cada tarea
de `tasks.md`: ese presupuesto suponía un Diagrama_Postura por ejercicio de
fuerza, y ese renderizador (tarea 3.9) **no está implementado**. La corrección
postural se entrega como texto en las fichas.

## Regla de contenido — respetada

- **Cero** nombres de fuentes de metodología, bibliografía, referencias, autores
  o sus URLs. **Cero** nombres de club y de futbolistas. **Cero** jerga interna
  de desarrollo (`MODO_MUESTRA`, `NO_PUBLICABLE`, `Catalogo_JSON`, `Target_*`,
  `pipeline`, nombres de módulo `.py`).
- Grep final sobre los **87 archivos** de `dist/` y `publicacion/`, con los
  streams de los PDF descomprimidos con `zlib`: **0 violaciones**.
- Guardarraíles que lo mantienen así: `test/test_guardarrail_clubes.py` y
  `test/test_guardarrail_jerga_interna.py`, cada uno con su prueba de cordura
  que inyecta una violación y exige que el detector la cace.
- Los únicos enlaces visibles son **videos de ejemplo** con su QR. Los 8
  enlaces de TikTok viven solo dentro de `media[]`, con `tipo: "tiktok"`,
  `titulo: "Video de ejemplo"` y el ancla fija "Ver demostración". Nunca se
  presentan como fuente, bibliografía ni referencia metodológica, y **no se
  analizó ningún video**: el entorno es offline y no hay acceso a video.

## Artefactos (regenerados y verificados en disco, 2026-08-08)

`dist/`:

| Archivo           | Tamaño      |
|-------------------|-------------|
| `index.html`      | 3,050,939 B |
| `guia.pdf`        | 257,656 B   |
| `laminas.pdf`     | 41,837 B    |
| `ejercicios.json` | 198,570 B   |

`publicacion/`:

| Ruta                        | Conteo / tamaño        |
|-----------------------------|------------------------|
| `index.html`                | 8,704 B                |
| `README.md`                 | 664 B                  |
| `.nojekyll`                 | 0 B (presente y vacío) |
| `Guia_Extensa_Sub17.pdf`    | 257,656 B              |
| `laminas/lamina-NN.svg`     | **58** archivos        |
| `guia/*.html`               | **10**, los 10 reapuntados al PDF publicado |

`Guia_Extensa_Sub17.pdf` pesa exactamente lo mismo que `dist/guia.pdf`
(257,656 B): es copia del PDF fresco de esta corrida, no un resto viejo.
El `README.md` publica los conteos del último build: **Paginas 111, Fichas 58,
Laminas 58**.

## Lo que no está y por qué (resumen; el detalle vive en `tasks.md`)

| Tarea | Estado | Motivo |
|---|---|---|
| 3.6 `colocar_etiquetas_botin` | `[~]` | Un solo botín, 7 zonas de nombre corto y posición fija, cero solapes. El colocador automático resolvería un problema que este catálogo no tiene |
| 3.9 Diagrama_Postura | `[~]` | Requiere revisión de un profesional de la salud: dibujar posturas correctas e incorrectas para menores no se autora a ciegas. Por eso `posturas: 0` y prevención en 9 páginas |
| 13.5 caché en disco | `[~]` | El build tarda 10.6 s contra un límite de 120 s, y una caché en disco puede servir arte rancio tras cambiar el catálogo |
| 15.3 push a GitHub | `[~]` | Instrucción permanente del usuario: no se hace push |
| 10.1-10.7, 12.1, 12.2 | sin marcar | Esos archivos no existen y no se van a crear; el contenido se entrega consolidado (ver el mapeo de las tareas 10 y 12) |
| 9 sub-tareas `*` | sin marcar | Opcionales; cada una con su motivo escrito. Las otras 17 opcionales sí están cerradas |

## Auditoría física: los entregables abren (2026-08-08)

Verificado que abren, no solo que existen: los PDF re-parseados con `verify_pdf`
exigiendo el conteo de hojas del modelo, los HTML con `html.parser`, el JSON con
`json.load`, los SVG por `<svg>`, `</svg>` y `viewBox`.

**8 de 8 entregables presentes y abren**, todos con fecha 2026-08-08 17:08:
`dist/index.html` (49,716 etiquetas), `dist/web/index.html`, `dist/guia.pdf` (58
hojas, 189 objetos, 59 streams), `dist/laminas.pdf` (58 hojas),
`dist/ejercicios.json` (58 fichas), `publicacion/index.html`,
`publicacion/Guia_Extensa_Sub17.pdf` (58 hojas) y las 58 láminas SVG con **0 mal
formadas**.

**QR:** 67 en total (uno por Media_Item), los **67 decodifican a su URL de origen**
y cada URL está además como anotación `/Link`. Cero discrepancias.

### Paridad de las superficies web: CORREGIDA (2026-08-08)

Era el último hueco y está cerrado. `plantillas.py` gana `_texto_dosis` y
`_poner_media_ficha` (un QR clicable por Media_Item, encabezado "Videos y enlaces",
pie `<titulo> - Ver demostracion` y anotación `/Link`), y `cap10_fundamentos.paginas()`
pasa el `media` crudo del catálogo a la plantilla.

`dist/web/10-fundamentos.html` y su copia `publicacion/guia/10-fundamentos.html` pasan
de 0 a **58** líneas de dosis, **58** de progresión, **58** de métrica, **58** de
variante 1-8, de 59 a **126** SVG, y de 0 a **8** menciones de "Video de ejemplo" y
**67** bloques de QR.

Consecuencia esperada y verificada: **las páginas del modelo suben de 111 a 169** y el
capítulo de fundamentos de 58 a 117. El umbral sigue siendo >= 100 y **no se bajó
ningún umbral**; tampoco hubo que ajustar pruebas, porque ninguna fijaba el conteo
exacto. La suite sigue en 292 tests, 0 fallos. `t[paginacion]` sube a 7.95 s y `t[qr]`
baja a 0.21 s (las matrices se reutilizan): total 10.5 s de un límite de 120 s.

QR contra `media[]`: **67 QR, los 67 decodifican a su URL exacta**, con 67 anotaciones
`/Link`. Igual en el PDF de fichas. Cero discrepancias.

Matiz: `dist/index.html` no contiene la palabra "Dosis" porque el sitio de un archivo
rinde la dosis como una rejilla de 5 celdas con sus propias etiquetas. Es otra
plantilla, no una falta.

### Diagramas 3D: nunca estuvieron en el alcance

Cero coincidencias de `3D`, `tridimensional`, `three.js` y `webgl` en
`requirements.md`, `design.md` y `tasks.md`. El Diagrama_Cancha está especificado
como **2D** (mundo en metros, origen abajo-izquierda, un solo spec para PDF y SVG) y
los 59 diagramas emitidos son 2D y válidos. Un renderizador 3D sería **mejora
futura**: pediría una dependencia de gráficos o un motor propio de proyección, y este
proyecto es stdlib-only y offline.

## Publicación en GitHub (tarea 15.3)

**No realizada** por instrucción permanente del usuario: no se hace push. La
estructura de `publicacion/` está lista y completa para subirla a mano.
