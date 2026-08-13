# Entrena como las grandes · sub-17 femenil

Guía de entrenamiento con **15 ejercicios dibujados**, la dosis de cada uno y el video
de cada uno. Pensada para una cancha compartida, botellas de refresco y una pared.

## Descargar

| | Archivo | Qué es |
|---|---|---|
| 📄 | **[Guía completa en PDF](https://github.com/jairofrancog7-star/hi/raw/main/guia-entrena-como-las-grandes.pdf)** | 20 hojas A4. Una ficha por hoja: dibujo de cancha, paso a paso, dosis, qué mira la compañera, enlaces y código QR. Para imprimir y llevar al campo. |
| 📱 | **[Láminas para el grupo](https://github.com/jairofrancog7-star/hi/raw/main/posters-para-el-grupo.pdf)** | 13 láminas verticales tamaño historia. Captura de pantalla y directo al WhatsApp. |
| 🌐 | **[Ver en el celular](https://htmlpreview.github.io/?https://github.com/jairofrancog7-star/hi/blob/main/index.html)** | La misma guía como página web, con todos los videos como botones. |

Desde el celular: toca el enlace, y arriba a la derecha de la vista del PDF está el
botón de descargar. Después ya lo puedes reenviar por WhatsApp.

## Cómo se ven los videos

Un PDF **no reproduce video adentro**: ningún lector de celular lo hace. Hay dos caminos
y los dos vienen puestos:

1. **Picar el nombre del video** en el PDF y se abre YouTube. Hay 62 enlaces.
2. **Escanear el cuadro QR** con la cámara. Esto también funciona desde la **hoja
   impresa**, que es donde un enlace no sirve de nada. Hay 24 códigos.

## Las 15 fichas

| | Ficha | | Ficha |
|---|---|---|---|
| 01 | Calentar sin romperse (FIFA 11+) | 09 | Córner en contra |
| 02 | Rondo 4 contra 1 | 10 | Uno contra uno con cobertura |
| 03 | Cuatro contra dos con comodín | 11 | Basculación de la línea |
| 04 | Salir jugando desde la portera | 12 | Cabeceo progresivo |
| 05 | Tres toques y a la banda | 13 | Tiro al cuadro |
| 06 | Presión de seis segundos | 14 | Técnica con la pared |
| 07 | Centro al área y rechace | 15 | Con qué parte le pegas |
| 08 | Córner ensayado a favor | | |

Más: portada con índice, hoja de cómo se usa con la leyenda de los dibujos, semana tipo
con partido el sábado, menú según cuántas jugadoras lleguen, hoja de control para la
libreta y un anexo con todos los QR juntos.

## Orden para empezar

| Semana | Fichas |
|---|---|
| 1 | 01 calentar · 14 pared · 02 rondo |
| 2 | se suman 13 tiro y 15 zonas del pie |
| 3 | 10 y 11 defensa |
| 4 | 05, 07, 08 y 09 transición y balón parado |

Regla: **una ficha por sesión, no cinco.**

## Cómo se generan los archivos

No hay dependencias: el PDF se escribe a mano (texto, vectores, enlaces clicables y los
códigos QR incluidos), con la librería estándar de Python.

```bash
python3 fuente/build.py     # genera los tres archivos
python3 fuente/src/verify.py # comprueba estructura, maquetación y lee los QR de vuelta
```

`verify.py` comprueba que la tabla de referencias del PDF apunte bien, que nada se salga
de la hoja y que los 30 códigos QR se decodifiquen al texto exacto.

## Sobre el contenido

Los principios de los ejercicios son los que están documentados en el fútbol de élite
femenil: el rondo y el juego de posición del Barcelona, las transiciones del Lyon, el
balón parado ensayado de Arsenal y Chelsea, y el programa **FIFA 11+** de prevención de
lesiones de rodilla que usan las selecciones nacionales
([material oficial de la FIFA](https://inside.fifa.com/es/health-and-medical/injury-prevention)).
Los videos enlazados son tutoriales públicos de YouTube en español.
