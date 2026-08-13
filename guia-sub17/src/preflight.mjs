/**
 * preflight.mjs - Verificacion de entorno del pipeline de la Guia Extensa Sub-17.
 *
 * Comprueba, en este orden:
 *   1. Runtime: Node (>= 18) o Bun.
 *   2. Modulos nucleo importables y funcionales: node:fs, node:path, node:zlib.
 *   3. Carpetas del esqueleto del proyecto: src/content/, test/, dist/.tmp/.
 *   4. Presencia de cada modulo del pipeline declarado en MODULOS_PIPELINE.
 *
 * Politica de fallo (Req 2.8, 2.9):
 *   - Runtime ausente o por debajo del minimo  -> Error E_DEPENDENCIA (siempre).
 *   - Modulo nucleo ausente o no funcional     -> Error E_DEPENDENCIA (siempre).
 *   - Carpeta del esqueleto ausente            -> Error E_DEPENDENCIA (siempre).
 *   - Modulo del pipeline ausente              -> pendiente (permisivo) /
 *                                                 Error E_DEPENDENCIA (--estricto).
 *
 * Los modulos del pipeline se van completando en sus propias tareas, por eso en
 * modo permisivo su ausencia no es fatal: el preflight informa que faltan y con
 * que tarea se cierran. El Orquestador_Build (tarea 13.1) llama a preflight con
 * { estricto: true } porque sin el pipeline completo no hay build posible.
 *
 * Este modulo no tiene imports de nivel superior a proposito: si node:fs o
 * node:zlib no estuvieran disponibles, un import estatico abortaria la carga del
 * archivo antes de poder emitir E_DEPENDENCIA con un mensaje util.
 *
 * _Requirements: 2.2, 2.8, 2.9_
 */

/** Raiz del proyecto (guia-sub17/), un nivel arriba de src/. */
export const RAIZ = new URL('../', import.meta.url);

/** Version mayor minima de Node soportada por el pipeline. */
export const NODE_MINIMO = 18;

/** Codigo de error unico del preflight, segun la tabla de codigos del diseno. */
export const E_DEPENDENCIA = 'E_DEPENDENCIA';

/**
 * Modulos nucleo del runtime que el pipeline usa sin alternativa:
 * node:fs para leer y escribir artefactos, node:path para rutas de salida y
 * node:zlib para los streams FlateDecode del PDF.
 */
export const NUCLEOS_REQUERIDOS = [
  { especificador: 'node:fs', simbolos: ['existsSync', 'readFileSync', 'createWriteStream'] },
  { especificador: 'node:path', simbolos: ['join', 'resolve', 'dirname'] },
  { especificador: 'node:zlib', simbolos: ['deflateSync', 'inflateSync'] }
];

/** Carpetas del esqueleto del proyecto. */
export const CARPETAS_REQUERIDAS = ['src/', 'src/content/', 'test/', 'dist/.tmp/'];

/**
 * Modulos del pipeline, en el orden en que las tareas los van cerrando.
 * `tarea` es la sub-tarea del plan que completa el componente; se imprime en el
 * reporte para que un pendiente diga por si solo como resolverse.
 */
export const MODULOS_PIPELINE = [
  { ruta: 'test/runner.mjs', componente: 'Motor_Pruebas', tarea: '1.2' },
  { ruta: 'test/gen.mjs', componente: 'Generadores_Prueba', tarea: '1.3' },
  { ruta: 'src/afm.mjs', componente: 'Metricas', tarea: '1.4' },
  { ruta: 'src/schema.mjs', componente: 'Validador_Esquema', tarea: '1.6' },
  { ruta: 'src/qr.mjs', componente: 'Generador_QR', tarea: '2.1' },
  { ruta: 'src/qr-decode.mjs', componente: 'Decodificador_QR', tarea: '2.2' },
  { ruta: 'src/diagram-spec.mjs', componente: 'Motor_Diagramas (spec)', tarea: '3.1' },
  { ruta: 'src/draw.mjs', componente: 'Motor_Diagramas (PDF)', tarea: '3.2' },
  { ruta: 'src/viz.mjs', componente: 'Motor_Diagramas (SVG)', tarea: '3.2' },
  { ruta: 'src/layout.mjs', componente: 'Paginador', tarea: '5.1' },
  { ruta: 'src/rotacion.mjs', componente: 'Plan_Rotacion', tarea: '6.1' },
  { ruta: 'src/verify-rotacion.mjs', componente: 'Verificador_Rotacion', tarea: '6.2' },
  { ruta: 'src/build-pdf.mjs', componente: 'Motor_PDF', tarea: '7.1' },
  { ruta: 'src/verify-pdf.mjs', componente: 'Verificador_PDF', tarea: '7.4' },
  { ruta: 'src/build-html.mjs', componente: 'Motor_HTML', tarea: '7.5' },
  { ruta: 'src/content/index.mjs', componente: 'Catalogo_Contenido', tarea: '9.1' },
  { ruta: 'src/build.mjs', componente: 'Orquestador_Build', tarea: '13.1' }
];

/** Error de dependencia con el codigo que el Orquestador_Build traduce a salida != 0. */
export class ErrorDependencia extends Error {
  /** @param {string} componente Nombre del componente faltante. @param {string} [detalle] */
  constructor(componente, detalle) {
    super(`falta el componente: ${componente}${detalle ? ` (${detalle})` : ''}`);
    this.name = 'ErrorDependencia';
    this.code = E_DEPENDENCIA;
    this.componente = componente;
  }
}

/** @returns {{nombre: 'node'|'bun'|'desconocido', version: string|null, mayor: number|null}} */
export function detectarRuntime(entorno = globalThis) {
  const bun = entorno.Bun;
  if (bun && typeof bun.version === 'string') {
    return { nombre: 'bun', version: bun.version, mayor: mayorDe(bun.version) };
  }
  const version = entorno.process?.versions?.node;
  if (typeof version === 'string') {
    return { nombre: 'node', version, mayor: mayorDe(version) };
  }
  return { nombre: 'desconocido', version: null, mayor: null };
}

function mayorDe(version) {
  const n = Number.parseInt(String(version).replace(/^v/, '').split('.')[0], 10);
  return Number.isFinite(n) ? n : null;
}

/**
 * Verificacion de entorno completa.
 * @param {{estricto?: boolean}} [opciones]
 * @returns {Promise<Reporte>} Reporte con ok, runtime, nucleos, carpetas y modulos.
 * @throws {ErrorDependencia} con code = 'E_DEPENDENCIA' y mensaje de una linea.
 */
export async function preflight({ estricto = false } = {}) {
  /** @type {Reporte} */
  const reporte = {
    ok: false,
    estricto,
    runtime: null,
    nucleos: [],
    carpetas: [],
    modulos: [],
    pendientes: [],
    faltante: null
  };

  // --- 1. Runtime ---------------------------------------------------------
  const runtime = detectarRuntime();
  if (runtime.nombre === 'desconocido') {
    reporte.runtime = { ...runtime, ok: false, detalle: 'runtime no reconocido' };
    reporte.faltante = 'Node >= 18 o Bun';
    throw new ErrorDependencia('Node >= 18 o Bun', 'runtime no reconocido');
  }
  if (runtime.nombre === 'node' && (runtime.mayor === null || runtime.mayor < NODE_MINIMO)) {
    reporte.runtime = { ...runtime, ok: false, detalle: `Node ${runtime.version} < ${NODE_MINIMO}` };
    reporte.faltante = `Node >= ${NODE_MINIMO}`;
    throw new ErrorDependencia(`Node >= ${NODE_MINIMO}`, `se encontro Node ${runtime.version}`);
  }
  reporte.runtime = {
    ...runtime,
    ok: true,
    detalle: `${runtime.nombre} ${runtime.version}`
  };

  // --- 2. Modulos nucleo --------------------------------------------------
  /** @type {Record<string, any>} */
  const nucleo = {};
  for (const { especificador, simbolos } of NUCLEOS_REQUERIDOS) {
    let modulo;
    try {
      modulo = await import(especificador);
    } catch (err) {
      reporte.nucleos.push({ especificador, ok: false, detalle: `no se puede importar: ${err.message}` });
      reporte.faltante = especificador;
      throw new ErrorDependencia(especificador, 'no se puede importar');
    }
    const ausentes = simbolos.filter((s) => typeof modulo[s] !== 'function');
    if (ausentes.length > 0) {
      reporte.nucleos.push({ especificador, ok: false, detalle: `sin ${ausentes.join(', ')}` });
      reporte.faltante = `${especificador}.${ausentes[0]}`;
      throw new ErrorDependencia(`${especificador}.${ausentes[0]}`, 'la funcion no existe en este runtime');
    }
    nucleo[especificador] = modulo;
    reporte.nucleos.push({ especificador, ok: true, detalle: `${simbolos.join(', ')} disponibles` });
  }

  // zlib debe funcionar, no solo existir: los streams del PDF van con FlateDecode.
  const { deflateSync, inflateSync } = nucleo['node:zlib'];
  try {
    const muestra = new TextEncoder().encode('guia-sub17 preflight: ñ á é í ó ú');
    const ida = new TextDecoder().decode(inflateSync(deflateSync(muestra)));
    if (ida !== 'guia-sub17 preflight: ñ á é í ó ú') throw new Error('round-trip distinto');
    reporte.nucleos.push({ especificador: 'node:zlib (round-trip)', ok: true, detalle: 'deflateSync/inflateSync verificados' });
  } catch (err) {
    reporte.nucleos.push({ especificador: 'node:zlib (round-trip)', ok: false, detalle: err.message });
    reporte.faltante = 'node:zlib (deflateSync/inflateSync)';
    throw new ErrorDependencia('node:zlib (deflateSync/inflateSync)', `round-trip fallido: ${err.message}`);
  }

  // --- 3. Carpetas del esqueleto -----------------------------------------
  const { existsSync } = nucleo['node:fs'];
  for (const carpeta of CARPETAS_REQUERIDAS) {
    const presente = existsSync(new URL(carpeta, RAIZ));
    reporte.carpetas.push({ carpeta, presente });
    if (!presente) {
      reporte.faltante = carpeta;
      throw new ErrorDependencia(carpeta, 'carpeta del proyecto ausente');
    }
  }

  // --- 4. Modulos del pipeline -------------------------------------------
  for (const modulo of MODULOS_PIPELINE) {
    const presente = existsSync(new URL(modulo.ruta, RAIZ));
    const fila = { ...modulo, presente };
    reporte.modulos.push(fila);
    if (!presente) reporte.pendientes.push(fila);
  }

  if (estricto && reporte.pendientes.length > 0) {
    const [primero] = reporte.pendientes;
    const otros = reporte.pendientes.length - 1;
    reporte.faltante = primero.ruta;
    throw new ErrorDependencia(
      primero.ruta,
      `${primero.componente}, tarea ${primero.tarea}${otros > 0 ? ` y ${otros} mas` : ''}`
    );
  }

  reporte.ok = true;
  return reporte;
}

/** Reporte legible de una sola pantalla. */
export function formatearReporte(reporte) {
  const lineas = [];
  const marca = (ok) => (ok ? 'ok  ' : 'FALTA');
  lineas.push('Preflight - Guia Extensa Sub-17');
  lineas.push(`  runtime   ${marca(reporte.runtime?.ok)} ${reporte.runtime?.detalle ?? 'sin detectar'}` +
    (reporte.runtime?.nombre === 'node' ? ` (minimo v${NODE_MINIMO})` : ''));
  for (const n of reporte.nucleos) lineas.push(`  nucleo    ${marca(n.ok)} ${n.especificador}: ${n.detalle}`);
  for (const c of reporte.carpetas) lineas.push(`  carpeta   ${marca(c.presente)} ${c.carpeta}`);

  const presentes = reporte.modulos.filter((m) => m.presente).length;
  lineas.push(`  pipeline  ${presentes}/${reporte.modulos.length} modulos presentes, ${reporte.pendientes.length} pendientes`);
  for (const m of reporte.pendientes) {
    lineas.push(`    pendiente  ${m.ruta.padEnd(24)} ${m.componente.padEnd(24)} tarea ${m.tarea}`);
  }
  lineas.push(`  modo      ${reporte.estricto ? 'estricto (el pipeline debe estar completo)' : 'permisivo (usa --estricto para exigir el pipeline completo)'}`);
  lineas.push(reporte.ok ? '  resultado ENTORNO LISTO' : '  resultado ENTORNO INCOMPLETO');
  return lineas.join('\n');
}

// --- Ejecucion directa: `node src/preflight.mjs [--estricto] [--json]` ------
const proceso = globalThis.process;
let directa = false;
if (proceso?.argv?.[1]) {
  try {
    const { pathToFileURL } = await import('node:url');
    directa = pathToFileURL(proceso.argv[1]).href === import.meta.url;
  } catch {
    directa = false;
  }
}

if (directa) {
  const argv = proceso.argv.slice(2);
  const estricto = argv.includes('--estricto');
  const json = argv.includes('--json');
  try {
    const reporte = await preflight({ estricto });
    console.log(json ? JSON.stringify(reporte, null, 2) : formatearReporte(reporte));
    proceso.exitCode = 0;
  } catch (err) {
    console.error(`${err.code ?? 'E_DESCONOCIDO'}: ${err.message}`);
    proceso.exitCode = 1;
  }
}

/**
 * @typedef {Object} Reporte
 * @property {boolean} ok
 * @property {boolean} estricto
 * @property {{nombre: string, version: string|null, mayor: number|null, ok: boolean, detalle: string}|null} runtime
 * @property {{especificador: string, ok: boolean, detalle: string}[]} nucleos
 * @property {{carpeta: string, presente: boolean}[]} carpetas
 * @property {{ruta: string, componente: string, tarea: string, presente: boolean}[]} modulos
 * @property {{ruta: string, componente: string, tarea: string, presente: boolean}[]} pendientes
 * @property {string|null} faltante
 */
