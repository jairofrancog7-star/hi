# Entrena como las grandes · fútbol femenil sub-17

Guía de entrenamiento con 15 ejercicios dibujados, la dosis de cada uno y el video de cada uno. Pensada para una cancha compartida, botellas de refresco y una pared.

Esta edición didáctica está preparada para consultarse en el celular, imprimirse en
A4 y compartirse con el equipo.

## Descargas

| Formato | Archivo | Contenido | Uso sin internet |
|---|---|---|---|
| 📄 PDF A4 | **[Descargar la guía completa](https://github.com/jairofrancog7-star/hi/raw/main/guia-entrena-como-las-grandes.pdf)** | 20 páginas: portada, 15 fichas, apoyos de planificación y anexo. Incluye dibujos de cancha, pasos, dosis, enlaces y QR. | Sí, después de descargarla. Los videos enlazados requieren conexión. |
| 📱 PDF vertical | **[Descargar las láminas para el grupo](https://github.com/jairofrancog7-star/hi/raw/main/posters-para-el-grupo.pdf)** | 13 láminas verticales listas para mostrar o compartir por WhatsApp. | Sí, después de descargarlo. Los videos enlazados requieren conexión. |
| 🌐 Web | **[Abrir la guía en el celular](https://htmlpreview.github.io/?https://github.com/jairofrancog7-star/hi/blob/main/index.html)** | Versión web adaptable, con fichas en tarjetas y botones grandes para los videos. | La vista previa necesita conexión para abrir. |
| ⬇️ HTML | **[Descargar `index.html`](https://github.com/jairofrancog7-star/hi/raw/main/index.html)** | Un solo archivo con la guía web, sin JavaScript ni dependencias externas. | Sí, una vez guardado. Solo los videos necesitan conexión. |

En el visor de PDF del celular, usa el botón de descarga para guardar el archivo antes
de ir a la cancha. Así podrás consultar la guía aunque no tengas señal.

## Actualización Técnica

La versión actual incorpora soporte **100% Offline Optimizado** para que las 15 fichas
aparezcan de inmediato incluso en visores móviles sencillos:

- se eliminó el bloqueo de renderizado por JavaScript y ninguna tarjeta espera al
  evento de carga del DOM para mostrarse;
- la interfaz se construye con HTML semántico y CSS nativo, sin bibliotecas, fuentes
  ni hojas de estilo externas;
- las 15 imágenes SVG de los ejercicios y sus 15 QR están integrados como recursos
  compactos en el propio archivo y usan carga diferida nativa con `loading="lazy"` y
  decodificación asíncrona con `decoding="async"`;
- el contenido, los diagramas, las dosis y los QR funcionan sin conexión después de
  guardar `index.html`; únicamente abrir los videos enlazados requiere internet;
- las rutas relativas de descarga de `guia-entrena-como-las-grandes.pdf` y
  `posters-para-el-grupo.pdf` se conservan para que los tres archivos puedan guardarse
  juntos y usarse en el campo.

## Diseño y accesibilidad

La interfaz usa azul cielo como identidad principal y rosa como acento secundario. Los
tonos pastel se reservan para fondos, bordes y estados suaves; el texto y las acciones
usan colores más profundos para conservar buen contraste a plena luz del día.

Estos son los tokens aplicados en el HTML y en los PDF generados. GitHub no admite CSS
personalizado en este README, por lo que la tabla documenta la paleta, pero no intenta
estilizar esta página.

| Token | Color | Uso |
|---|---|---|
| Azul cielo | `#BFE9FF` | Fondos destacados y superficies de marca |
| Azul de acción | `#0B6FA4` | Botones, navegación y encabezados interactivos |
| Azul profundo | `#06496E` | Contraste, títulos y estados activos |
| Tinta | `#102A3A` | Texto principal |
| Texto secundario | `#486476` | Metadatos y explicaciones |
| Rosa | `#A52357` | Acentos, indicadores y bordes destacados |
| Rosa suave | `#FFE3ED` | Fondos de apoyo y estados hover |
| Papel | `#F7FCFF` | Fondo general claro |

La versión web incluye:

- diseño adaptable desde teléfonos pequeños hasta escritorio;
- tarjetas para agrupar cada ejercicio y sus videos;
- botones táctiles de al menos 48 px;
- navegación semántica, enlace para saltar al contenido y foco visible;
- tipografía de sistema, sin descargar fuentes externas;
- compatibilidad con la preferencia de movimiento reducido;
- funcionamiento sin JavaScript;
- 15 diagramas y 15 QR SVG compactos con carga diferida nativa.

## Las 15 fichas

| N.º | Ficha | N.º | Ficha |
|---:|---|---:|---|
| 01 | Calentar sin romperse (FIFA 11+) | 09 | Córner en contra |
| 02 | Rondo 4 contra 1 | 10 | Uno contra uno con cobertura |
| 03 | Cuatro contra dos con comodín | 11 | Basculación de la línea |
| 04 | Salir jugando desde la portera | 12 | Cabeceo progresivo |
| 05 | Tres toques y a la banda | 13 | Tiro al cuadro |
| 06 | Presión de seis segundos | 14 | Técnica con la pared |
| 07 | Centro al área y rechace | 15 | Con qué parte le pegas |
| 08 | Córner ensayado a favor |  |  |

La guía añade una portada con índice, instrucciones de uso y leyenda de los dibujos,
una semana tipo con partido el sábado, un menú según el número de jugadoras, una hoja
de control y un anexo de accesos QR.

## Videos, enlaces y QR

Los videos no se incrustan dentro del PDF ni del HTML: se abren en YouTube mediante
botones, enlaces o QR. La guía PDF contiene **62 enlaces clicables** y el PDF de láminas
contiene **13 enlaces clicables**. Los QR también sirven desde una hoja impresa.

El contenido didáctico queda disponible sin conexión al guardar los archivos. Para
abrir cualquier video se necesita internet.

## Orden sugerido para empezar

| Semana | Fichas |
|---:|---|
| 1 | 01 calentar · 14 pared · 02 rondo |
| 2 | Se suman 13 tiro y 15 zonas del pie |
| 3 | Se suman 10 y 11 defensa |
| 4 | Se suman 05, 07, 08 y 09 transición y balón parado |

**Regla práctica:** una ficha por sesión, no cinco.

## Generar y verificar los archivos

El generador utiliza únicamente la biblioteca estándar de Python. Desde la raíz del
repositorio:

```bash
python3 fuente/build.py
python3 fuente/src/verify.py
python3 -m unittest discover -s fuente/src -p 'test_*.py' -v
```

`build.py` vuelve a crear en la raíz `index.html`,
`guia-entrena-como-las-grandes.pdf` y `posters-para-el-grupo.pdf`.

`verify.py` comprueba la estructura de ambos PDF, el número de páginas, los enlaces,
los destinos QR fuente y la estructura del HTML. La suite independiente revisa el
motor PDF, la codificación QR y los 30 activos SVG offline.

## Estructura del repositorio

```text
.
├── index.html
├── guia-entrena-como-las-grandes.pdf
├── posters-para-el-grupo.pdf
├── README.md
├── LEEME.txt
└── fuente/
    ├── build.py
    └── src/
        ├── content.py
        ├── diagram.py
        ├── pdfkit.py
        ├── test_pdfkit.py
        ├── test_webassets.py
        ├── verify.py
        ├── webassets.py
        └── webstyle.py
```

## Sobre el contenido

Los ejercicios adaptan principios utilizados en el fútbol femenil de alto rendimiento:
rondos y juego de posición, transiciones, presión, balón parado y prevención de
lesiones. La activación toma como referencia el programa **FIFA 11+**
([material oficial de la FIFA](https://inside.fifa.com/es/health-and-medical/injury-prevention)).
Los videos enlazados son recursos públicos de YouTube en español.
