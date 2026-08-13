# -*- coding: utf-8 -*-
"""Auditoría reproducible de los PDF, los QR fuente y la guía web."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote
import zlib


SRC_DIR = Path(__file__).resolve().parent
FUENTE_DIR = SRC_DIR.parent
REPO_ROOT = FUENTE_DIR.parent
for import_dir in (SRC_DIR, FUENTE_DIR):
    location = str(import_dir)
    if location not in sys.path:
        sys.path.insert(0, location)

import pdfkit as pk  # noqa: E402  (módulo local, después de ajustar sys.path)
import content as C  # noqa: E402
from test_pdfkit import decode  # noqa: E402


fails = []


def fail(message):
    fails.append(message)


def contrast_ratio(color_a, color_b):
    """Calcula contraste WCAG entre dos colores #rrggbb."""
    def luminance(color):
        channels = [int(color[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                  for v in channels]
        return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]

    light, dark = sorted((luminance(color_a), luminance(color_b)), reverse=True)
    return (light + .05) / (dark + .05)


class HTMLAudit(HTMLParser):
    """Recolecta estructura y atributos relevantes sin depender de paquetes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.starts = Counter()
        self.ends = Counter()
        self.nav_labels = []
        self.main_ids = set()
        self.skip_links = []
        self.pdf_links = set()
        self.diagram_images = []
        self.qr_images = []
        self.remote_resources = []
        self.javascript = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self.starts[tag] += 1
        values = {str(k).lower(): (v or '') for k, v in attrs}

        if tag == 'script':
            self.javascript.append('<script>')
        for name, value in values.items():
            if name.startswith('on'):
                self.javascript.append('%s=' % name)
            if value.strip().lower().startswith('javascript:'):
                self.javascript.append(value)

        if tag == 'main' and values.get('id'):
            self.main_ids.add(values['id'])
        if tag == 'nav':
            self.nav_labels.append(values.get('aria-label', '').strip())
        if tag == 'a':
            href = values.get('href', '').strip()
            classes = values.get('class', '').lower().split()
            if (href.startswith('#') and
                    any('skip' in name or 'saltar' in name for name in classes)):
                self.skip_links.append(href[1:])
            clean_href = href.lower().split('?', 1)[0].split('#', 1)[0]
            if clean_href.endswith('.pdf'):
                self.pdf_links.add(Path(clean_href).name)
        if tag == 'img':
            classes = values.get('class', '').lower().split()
            src = values.get('src', '').strip()
            if 'exercise-diagram' in classes:
                self.diagram_images.append(values)
            if 'qr' in classes:
                self.qr_images.append(values)
            if src.startswith(('http://', 'https://', '//')):
                self.remote_resources.append(src)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.ends[tag.lower()] += 1

    def handle_endtag(self, tag):
        self.ends[tag.lower()] += 1


# ---------------------------------------------------------------------- PDF
for name in ('guia-entrena-como-las-grandes.pdf', 'posters-para-el-grupo.pdf'):
    path = REPO_ROOT / name
    if not path.is_file():
        fail('%s: archivo ausente en %s' % (name, REPO_ROOT))
        continue
    raw = path.read_bytes()
    if not raw.startswith(b'%PDF-1.4'):
        fail(name + ': cabecera')
    if not raw.rstrip().endswith(b'%%EOF'):
        fail(name + ': sin %%EOF')

    start_match = re.search(rb'startxref\s+(\d+)', raw)
    if not start_match:
        fail(name + ': sin startxref')
        continue
    sx = int(start_match.group(1))
    if raw[sx:sx + 4] != b'xref':
        fail(name + ': startxref')
    offs = [int(m.group(1)) for m in
            re.finditer(rb'^(\d{10}) 00000 n $', raw[sx:], re.M)]
    for i, off in enumerate(offs, 1):
        if not raw[off:off + 30].startswith(b'%d 0 obj' % i):
            fail('%s: offset del objeto %d' % (name, i))

    count_match = re.search(rb'/Type /Pages /Count (\d+)', raw)
    if not count_match:
        fail(name + ': sin contador de páginas')
        continue
    npages = int(count_match.group(1))
    nreal = len(re.findall(rb'/Type /Page /Parent', raw))
    if npages != nreal:
        fail('%s: Count %d != %d páginas' % (name, npages, nreal))
    nlinks = len(re.findall(rb'/Subtype /Link', raw))

    # Descomprimir streams y revisar el equilibrio de operadores de texto.
    bt = et = 0
    nbad = 0
    for match in re.finditer(
            rb'<< /Length \d+ /Filter /FlateDecode >>\nstream\n(.*?)\nendstream',
            raw, re.S):
        try:
            txt = zlib.decompress(match.group(1)).decode('latin-1')
        except Exception as exc:
            fail('%s: stream ilegible (%s)' % (name, exc))
            continue
        bt += txt.count('BT ')
        et += txt.count(' ET')
        nbad += len(re.findall(r'(?<![\w./])(nan|inf|-inf)(?![\w.])', txt))
    if bt != et:
        fail('%s: BT/ET descompensados (%d/%d)' % (name, bt, et))
    if nbad:
        fail('%s: %d números inválidos' % (name, nbad))
    print('%-38s %2d páginas · %3d KB · %3d enlaces · BT=ET=%d'
          % (name, npages, len(raw) // 1024, nlinks, bt))


# ------------------------------------------------------------- QR de fuente
urls = set()
for drill in C.DRILLS:
    urls.add(drill['qr'])
    for _, _, url in drill['links']:
        urls.add(url)
for poster in C.POSTERS:
    urls.add(poster['qr'])

ok = 0
for url in sorted(urls):
    try:
        size, matrix = pk.qr_matrix(url)
        decoded = decode(size, matrix)
    except Exception as exc:
        fail('QR fuente %s: %s' % (url, exc))
        continue
    if decoded == url:
        ok += 1
    else:
        fail('QR fuente incorrecto: %r != %r' % (decoded, url))
print('\nDestinos QR fuente verificados: %d/%d '
      '(matrices fuente; no es un escaneo del PDF renderizado)'
      % (ok, len(urls)))


# --------------------------------------------------------------------- HTML
html_path = REPO_ROOT / 'index.html'
if not html_path.is_file():
    fail('html: falta index.html en %s' % REPO_ROOT)
    html = ''
else:
    html = html_path.read_text(encoding='utf-8')

audit = HTMLAudit()
try:
    audit.feed(html)
    audit.close()
except Exception as exc:
    fail('html: no se pudo analizar (%s)' % exc)

expected_articles = len(C.DRILLS)
if audit.starts['article'] != expected_articles:
    fail('html: %d fichas <article>; se esperaban %d'
         % (audit.starts['article'], expected_articles))
if audit.javascript:
    fail('html: contiene JavaScript (%s)' % ', '.join(audit.javascript[:3]))
if audit.starts['main'] != 1:
    fail('html: debe contener exactamente un <main>')
if not audit.nav_labels or any(not label for label in audit.nav_labels):
    fail('html: cada <nav> necesita aria-label no vacío')
if not audit.skip_links:
    fail('html: falta enlace de salto accesible')
elif not any(target in audit.main_ids for target in audit.skip_links):
    fail('html: el enlace de salto no apunta al id de <main>')

for pdf_name in ('guia-entrena-como-las-grandes.pdf', 'posters-para-el-grupo.pdf'):
    if pdf_name not in audit.pdf_links:
        fail('html: falta enlace a %s' % pdf_name)

for tag in ('div', 'article', 'ol', 'dl', 'nav', 'main', 'section', 'svg'):
    opened, closed = audit.starts[tag], audit.ends[tag]
    if opened != closed:
        fail('html: <%s> %d abiertas / %d cerradas' % (tag, opened, closed))

if len(audit.diagram_images) != expected_articles:
    fail('html: %d diagramas <img>; se esperaban %d'
         % (len(audit.diagram_images), expected_articles))
if len(audit.qr_images) != expected_articles:
    fail('html: %d QR <img>; se esperaban %d'
         % (len(audit.qr_images), expected_articles))
embedded_bytes = 0
for kind, images in (('diagrama', audit.diagram_images), ('QR', audit.qr_images)):
    for i, attrs in enumerate(images, 1):
        if attrs.get('loading', '').lower() != 'lazy':
            fail('html: %s %d necesita loading="lazy"' % (kind, i))
        if attrs.get('decoding', '').lower() != 'async':
            fail('html: %s %d necesita decoding="async"' % (kind, i))
        if not attrs.get('width', '').isdigit() or not attrs.get('height', '').isdigit():
            fail('html: %s %d necesita width y height numéricos' % (kind, i))
        if not attrs.get('alt', '').strip():
            fail('html: %s %d necesita texto alternativo' % (kind, i))
        src = attrs.get('src', '')
        if not src.lower().startswith('data:image/svg+xml,'):
            fail('html: %s %d no está integrado como SVG data:image offline' % (kind, i))
            continue
        if len(src) > 64 * 1024:
            fail('html: %s %d supera 64 KB' % (kind, i))
        embedded_bytes += len(src)
        try:
            svg = unquote(src.split(',', 1)[1])
        except Exception as exc:
            fail('html: %s %d tiene URI ilegible (%s)' % (kind, i, exc))
            continue
        if not (svg.startswith('<svg') and svg.endswith('</svg>')):
            fail('html: %s %d no contiene un SVG completo' % (kind, i))
        if '<script' in svg.lower() or '<image' in svg.lower():
            fail('html: %s %d contiene recursos o script no permitidos' % (kind, i))
if embedded_bytes > 1024 * 1024:
    fail('html: las imágenes integradas superan 1 MB')
if audit.remote_resources:
    fail('html: contiene recursos visuales remotos (%s)' % audit.remote_resources[0])

for forbidden in ('<link', '<iframe', '@import', 'url(http://', 'url(https://'):
    if forbidden in html.lower():
        fail('html: recurso bloqueante o remoto no permitido (%s)' % forbidden)

lower_html = html.lower()
if '#bfe9ff' not in lower_html:
    fail('html: falta el token azul cielo #bfe9ff')
if not re.search(r'html\s*\{[^}]*background-color\s*:\s*#bfe9ff', lower_html, re.S):
    fail('html: el fondo raíz no fuerza #bfe9ff')

css_vars = {name.lower(): value.lower() for name, value in re.findall(
    r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\b', html)}
pink_vars = {name: value for name, value in css_vars.items()
             if 'pink' in name or 'rosa' in name}
if not pink_vars:
    fail('html: falta un token CSS rosa (--pink… o --rosa…)')
if ':focus-visible' not in lower_html:
    fail('html: falta estilo :focus-visible')
if not re.search(r'@media\s+print\b', lower_html):
    fail('html: falta @media print')
if 'prefers-color-scheme' not in lower_html:
    fail('html: falta integración con prefers-color-scheme')
if 'prefers-reduced-motion' not in lower_html:
    fail('html: falta ajuste para prefers-reduced-motion')

touch_sizes = [float(value) for value in re.findall(
    r'min-(?:height|block-size)\s*:\s*([0-9]+(?:\.[0-9]+)?)px', lower_html)]
if not any(value >= 48 for value in touch_sizes):
    fail('html: falta un objetivo táctil con min-height de al menos 48px')

# Comprobaciones WCAG sobre los pares clave de los temas claro y oscuro.
def variables_from(block):
    if not block:
        return {}
    return {name: value for name, value in re.findall(
        r'(--[\w-]+)\s*:\s*(#[0-9a-f]{6})\b', block.group(1))}


light_block = re.search(r':root\s*\{([^}]*)\}', lower_html, re.S)
dark_block = re.search(
    r'@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{\s*:root\s*\{([^}]*)\}',
    lower_html, re.S)
themes = (('claro', variables_from(light_block)), ('oscuro', variables_from(dark_block)))
text_pairs = (
    ('texto/azul cielo', '--text', '--sky', 4.5),
    ('texto/rosa suave', '--text', '--pink-soft', 4.5),
    ('acción', '--action-text', '--action', 4.5),
    ('texto secundario/papel', '--muted', '--paper', 4.5),
    ('rosa/rosa suave', '--pink', '--pink-soft', 4.5),
    ('foco/superficie', '--pink', '--surface', 3.0),
)
contrast_results = []
for theme_name, variables in themes:
    ratios = []
    if not variables:
        fail('html: no se pudieron leer las variables del tema %s' % theme_name)
        continue
    for label, foreground_name, background_name, minimum in text_pairs:
        foreground = variables.get(foreground_name)
        background = variables.get(background_name)
        if not foreground or not background:
            fail('html: tema %s sin colores para %s' % (theme_name, label))
            continue
        ratio = contrast_ratio(foreground, background)
        ratios.append(ratio)
        if ratio < minimum:
            fail('html: contraste %s en tema %s insuficiente (%.2f:1; mínimo %.1f:1)'
                 % (label, theme_name, ratio, minimum))
    if ratios:
        contrast_results.append('%s mínimo %.2f:1' % (theme_name, min(ratios)))

print('index.html: %d fichas · sin JavaScript · %d diagramas lazy · %d QR lazy'
      % (audit.starts['article'], len(audit.diagram_images), len(audit.qr_images)))
print('Imágenes SVG offline integradas: %d KB' % (embedded_bytes // 1024))
if contrast_results:
    print('Contraste CSS: ' + ' · '.join(contrast_results))

print()
if fails:
    print('%d FALLAS:' % len(fails))
    for item in fails[:40]:
        print(' -', item)
    sys.exit(1)
print('TODO VERIFICADO')
