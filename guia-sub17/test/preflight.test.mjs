/**
 * Pruebas unitarias del preflight de dependencias.
 *
 * Autonomas a proposito: el motor de pruebas propio (test/runner.mjs) llega en la
 * tarea 1.2, asi que este archivo usa node:assert y se ejecuta con
 * `node test/preflight.test.mjs`. Cuando exista el runner, estas pruebas se
 * migran a su formato describe/it.
 *
 * _Requirements: 2.8, 2.9_
 */
import assert from 'node:assert/strict';
import {
  preflight,
  detectarRuntime,
  formatearReporte,
  ErrorDependencia,
  MODULOS_PIPELINE,
  CARPETAS_REQUERIDAS,
  NODE_MINIMO,
  E_DEPENDENCIA
} from '../src/preflight.mjs';

let fallos = 0;
async function prueba(nombre, fn) {
  try {
    await fn();
    console.log(`  ok    ${nombre}`);
  } catch (err) {
    fallos++;
    console.error(`  FALLA ${nombre}\n        ${err.message}`);
  }
}

console.log('preflight.test.mjs');

await prueba('detecta el runtime actual con version', () => {
  const rt = detectarRuntime();
  assert.ok(rt.nombre === 'node' || rt.nombre === 'bun', `runtime inesperado: ${rt.nombre}`);
  assert.ok(typeof rt.version === 'string' && rt.version.length > 0);
  assert.ok(Number.isFinite(rt.mayor));
});

await prueba('rechaza un runtime sin Node ni Bun', () => {
  const rt = detectarRuntime({ process: { versions: {} } });
  assert.equal(rt.nombre, 'desconocido');
  assert.equal(rt.mayor, null);
});

await prueba('reconoce Bun por globalThis.Bun', () => {
  const rt = detectarRuntime({ Bun: { version: '1.1.30' } });
  assert.equal(rt.nombre, 'bun');
  assert.equal(rt.mayor, 1);
});

await prueba(`el modo permisivo pasa con el pipeline incompleto (Node >= ${NODE_MINIMO})`, async () => {
  const rep = await preflight({ estricto: false });
  assert.equal(rep.ok, true);
  assert.equal(rep.runtime.ok, true);
  assert.equal(rep.carpetas.length, CARPETAS_REQUERIDAS.length);
  assert.ok(rep.carpetas.every((c) => c.presente), 'falta una carpeta del esqueleto');
  assert.ok(rep.nucleos.every((n) => n.ok), 'falta un modulo nucleo');
  assert.equal(rep.modulos.length, MODULOS_PIPELINE.length);
});

await prueba('el modo estricto falla con E_DEPENDENCIA nombrando el componente pendiente', async () => {
  const rep = await preflight({ estricto: false });
  if (rep.pendientes.length === 0) {
    console.log('        (pipeline completo: nada pendiente, prueba no aplicable)');
    return;
  }
  await assert.rejects(
    () => preflight({ estricto: true }),
    (err) => {
      assert.ok(err instanceof ErrorDependencia);
      assert.equal(err.code, E_DEPENDENCIA);
      assert.ok(err.message.startsWith('falta el componente: '), err.message);
      assert.ok(err.message.includes(rep.pendientes[0].ruta), err.message);
      assert.equal(err.message.includes('\n'), false, 'el mensaje debe ser de una linea');
      return true;
    }
  );
});

await prueba('el reporte se puede imprimir', async () => {
  const texto = formatearReporte(await preflight({}));
  assert.ok(texto.includes('Preflight - Guia Extensa Sub-17'));
  assert.ok(texto.includes('runtime'));
});

console.log(fallos === 0 ? 'preflight.test.mjs: todo en verde' : `preflight.test.mjs: ${fallos} fallo(s)`);
process.exitCode = fallos === 0 ? 0 : 1;
