# -*- coding: utf-8 -*-
"""Estilos inline de la guía web, separados del generador para poder mantenerlos."""

CSS = r"""
:root {
  color-scheme: light;
  --sky: #bfe9ff;
  --sky-strong: #72c9ef;
  --blue: #0b6fa4;
  --blue-deep: #06496e;
  --pink: #a52357;
  --pink-soft: #ffe3ed;
  --paper: #f7fcff;
  --surface: #ffffff;
  --surface-blue: #eef8fd;
  --text: #102a3a;
  --muted: #486476;
  --border: #b9dce9;
  --action: #0b6fa4;
  --action-text: #ffffff;
  --shadow: 0 18px 45px rgba(16, 42, 58, .10);
}

* { box-sizing: border-box; }

html {
  background-color: #bfe9ff !important;
  scroll-behavior: smooth;
  scroll-padding-top: 24px;
}

body {
  margin: 0;
  background: var(--paper);
  background-color: #bfe9ff !important;
  color: var(--text);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

a {
  color: var(--blue-deep);
  text-underline-offset: .18em;
}

.shell {
  width: min(1120px, calc(100% - 40px));
  margin-inline: auto;
}

.skip-link {
  position: fixed;
  z-index: 100;
  top: 12px;
  left: 16px;
  transform: translateY(-160%);
  padding: 11px 16px;
  border-radius: 10px;
  background: var(--text);
  color: var(--surface);
  font-weight: 800;
}

.skip-link:focus { transform: translateY(0); }

:focus-visible {
  outline: 3px solid var(--pink);
  outline-offset: 4px;
  border-radius: 6px;
}

.site-header {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--border);
  background:
    radial-gradient(circle at 88% 18%, var(--pink-soft) 0 12%, transparent 12.3%),
    linear-gradient(135deg, var(--sky) 0 70%, var(--pink-soft) 100%);
}

.site-header::after {
  content: "";
  position: absolute;
  right: -110px;
  bottom: -150px;
  width: 240px;
  height: 240px;
  border: 40px solid rgba(255, 255, 255, .42);
  border-radius: 50%;
  pointer-events: none;
}

.top-nav {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  gap: 20px;
  border-bottom: 1px solid rgba(6, 73, 110, .18);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  font-weight: 900;
  letter-spacing: -.02em;
  text-decoration: none;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--action);
  box-shadow: 0 6px 16px rgba(6, 73, 110, .18);
  color: var(--action-text);
  font-size: 18px;
}

.brand-ball {
  display: block;
  width: 22px;
  height: 22px;
}

.top-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.top-links a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 9px 14px;
  border-radius: 999px;
  color: var(--text);
  font-size: 14px;
  font-weight: 800;
  text-decoration: none;
}

.top-links a:hover {
  background: var(--pink-soft);
  color: var(--pink);
}

.hero {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, .65fr);
  align-items: end;
  gap: clamp(28px, 6vw, 72px);
  padding: clamp(48px, 8vw, 88px) 0 64px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  margin: 0 0 18px;
  padding: 4px 12px;
  border: 1px solid rgba(165, 35, 87, .28);
  border-radius: 999px;
  background: var(--pink-soft);
  color: var(--pink);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .13em;
  text-transform: uppercase;
}

h1 {
  max-width: 12ch;
  margin: 0;
  font-size: clamp(42px, 8vw, 78px);
  line-height: .98;
  letter-spacing: -.055em;
}

h1 em {
  color: var(--pink);
  font-style: normal;
}

.lede {
  max-width: 62ch;
  margin: 24px 0 0;
  color: var(--text);
  font-size: clamp(17px, 2vw, 20px);
  line-height: 1.55;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  padding: 11px 18px;
  border: 2px solid transparent;
  border-radius: 12px;
  background: var(--action);
  box-shadow: 0 8px 20px rgba(6, 73, 110, .15);
  color: var(--action-text);
  font-weight: 900;
  text-decoration: none;
  touch-action: manipulation;
}

.button:hover {
  background: var(--pink);
  color: #ffffff;
}

.button.secondary {
  border-color: var(--blue-deep);
  background: var(--surface);
  box-shadow: none;
  color: var(--blue-deep);
}

.button.secondary:hover {
  border-color: var(--pink);
  background: var(--pink-soft);
  color: var(--pink);
}

.hero-card {
  align-self: stretch;
  padding: 24px;
  border: 1px solid rgba(6, 73, 110, .18);
  border-radius: 22px;
  background: rgba(255, 255, 255, .72);
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
}

.hero-card h2 {
  margin: 0 0 14px;
  font-size: 17px;
}

.facts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 0;
}

.facts div {
  padding: 14px;
  border-radius: 14px;
  background: var(--surface);
}

.facts dt {
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.facts dd {
  margin: 2px 0 0;
  color: var(--blue-deep);
  font-size: 21px;
  font-weight: 900;
}

.offline-note {
  margin: 14px 0 0;
  padding: 12px 14px;
  border-left: 4px solid var(--pink);
  border-radius: 4px 12px 12px 4px;
  background: var(--pink-soft);
  color: var(--text);
  font-size: 14px;
}

main { padding: 56px 0 84px; }

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.section-heading h2 {
  margin: 0;
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.1;
  letter-spacing: -.035em;
}

.section-heading p {
  max-width: 48ch;
  margin: 0;
  color: var(--muted);
}

.downloads { margin-bottom: 48px; }

.download-table-wrap {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.download-table {
  width: 100%;
  border-collapse: collapse;
}

.download-table th,
.download-table td {
  padding: 16px 18px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: middle;
}

.download-table thead {
  background: var(--sky);
  color: var(--text);
}

.download-table th {
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
}

.download-table tbody tr:last-child td { border-bottom: 0; }
.download-table tbody tr:hover { background: var(--pink-soft); }
.download-table strong { display: block; color: var(--text); }
.download-table small { display: block; color: var(--muted); }

.download-table .button {
  width: 100%;
  min-width: 132px;
  font-size: 14px;
  box-shadow: none;
}

.contents {
  margin: 0 0 48px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.contents summary {
  display: flex;
  align-items: center;
  min-height: 56px;
  padding: 14px 18px;
  color: var(--blue-deep);
  font-weight: 900;
  cursor: pointer;
  touch-action: manipulation;
}

.contents summary::marker { color: var(--pink); }

.toc {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 0 14px 16px;
}

.toc-link {
  display: flex;
  align-items: center;
  min-height: 52px;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
}

.toc-link:hover {
  background: var(--pink-soft);
  color: var(--pink);
}

.toc-link span {
  flex: 0 0 34px;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--sky);
  color: var(--blue-deep);
  font-size: 12px;
  font-weight: 900;
}

.toc-link strong {
  font-size: 13px;
  line-height: 1.25;
}

.guide-heading { margin: 0 0 26px; }

.guide-heading h2 {
  margin: 0;
  font-size: clamp(30px, 5vw, 48px);
  letter-spacing: -.04em;
}

.guide-heading p {
  max-width: 62ch;
  margin: 8px 0 0;
  color: var(--muted);
}

.training-card {
  scroll-margin-top: 24px;
  margin: 0 0 28px;
  padding: clamp(22px, 4vw, 38px);
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.card-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.number {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 4px 10px;
  border-radius: 8px;
  background: var(--action);
  color: var(--action-text);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .1em;
}

.category {
  color: var(--pink);
  font-size: 12px;
  font-weight: 900;
  letter-spacing: .09em;
  text-transform: uppercase;
}

.team { color: var(--muted); font-size: 13px; }

.training-card > h2 {
  margin: 0;
  font-size: clamp(27px, 4vw, 38px);
  line-height: 1.15;
  letter-spacing: -.035em;
}

.subtitle {
  margin: 7px 0 14px;
  color: var(--pink);
  font-weight: 750;
  font-style: italic;
}

.idea {
  max-width: 74ch;
  margin: 0;
  color: var(--muted);
  font-size: 17px;
}

.diagram-card {
  margin: 26px 0 0;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface-blue);
}

.exercise-diagram {
  display: block;
  width: 100%;
  height: auto;
  max-height: 480px;
  border-radius: 12px;
  object-fit: contain;
  background: var(--sky);
  contain: layout paint;
}

.diagram-card figcaption {
  margin-top: 9px;
  color: var(--muted);
  font-size: 12px;
  text-align: center;
}

.lesson-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(260px, .75fr);
  gap: 24px;
  margin-top: 28px;
}

.training-card h3 {
  margin: 0 0 12px;
  color: var(--blue-deep);
  font-size: 13px;
  letter-spacing: .1em;
  text-transform: uppercase;
}

.steps {
  counter-reset: step;
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.steps li {
  counter-increment: step;
  display: grid;
  grid-template-columns: 36px 1fr;
  align-items: start;
  gap: 12px;
}

.steps li::before {
  content: counter(step);
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--sky);
  color: var(--blue-deep);
  font-size: 13px;
  font-weight: 900;
}

.coach-note {
  padding: 20px;
  border: 1px solid rgba(165, 35, 87, .22);
  border-radius: 16px;
  background: var(--pink-soft);
}

.coach-note h3 { color: var(--pink); }
.coach-note p { margin: 0 0 18px; }

.dose {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.dose-item {
  padding: 10px;
  border-radius: 10px;
  background: var(--surface);
}

.dose dt {
  color: var(--muted);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .09em;
  text-transform: uppercase;
}

.dose dd {
  margin: 2px 0 0;
  font-size: 14px;
  font-weight: 900;
}

.media-section {
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid var(--border);
}

.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.section-title span { color: var(--muted); font-size: 12px; }

.media-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px;
  align-items: stretch;
  gap: 12px;
}

.video-list { display: grid; gap: 10px; }

.video-card {
  display: flex;
  align-items: center;
  min-height: 64px;
  gap: 12px;
  padding: 11px 14px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface-blue);
  color: var(--text);
  text-decoration: none;
  touch-action: manipulation;
}

.video-card:hover {
  transform: translateY(-1px);
  border-color: var(--pink);
  background: var(--pink-soft);
}

.video-tag {
  flex: 0 0 auto;
  padding: 4px 7px;
  border-radius: 6px;
  background: var(--action);
  color: var(--action-text);
  font-size: 10px;
  font-weight: 900;
  letter-spacing: .08em;
}

.video-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  line-height: 1.35;
}

.video-copy strong { font-size: 14px; }
.video-copy small { color: var(--muted); font-size: 11px; }
.external { color: var(--pink); font-size: 20px; font-weight: 900; }

.qr-card {
  display: grid;
  grid-template-columns: 72px 1fr;
  align-items: center;
  min-height: 96px;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(165, 35, 87, .25);
  border-radius: 14px;
  background: var(--pink-soft);
  color: var(--text);
  text-decoration: none;
}

.qr-card:hover { border-color: var(--pink); }

.qr {
  display: block;
  width: 72px;
  height: 72px;
  padding: 4px;
  border-radius: 8px;
  background: #ffffff;
  contain: strict;
  object-fit: contain;
}

.qr-card span {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.qr-card strong { font-size: 13px; }
.qr-card small { margin-top: 4px; color: var(--muted); font-size: 10px; }

.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 48px;
  margin-top: 18px;
  color: var(--blue-deep);
  font-size: 13px;
  font-weight: 900;
}

.site-footer {
  padding: 42px 0 calc(42px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--border);
  background: var(--sky);
  text-align: center;
}

.site-footer strong {
  display: block;
  color: var(--pink);
  font-size: 22px;
}

.site-footer span { color: var(--text); font-size: 13px; }

.video-card,
.toc-link,
.button,
.qr-card,
.top-links a {
  transition: background-color .18s ease, border-color .18s ease, color .18s ease,
    transform .18s ease;
}

@media (max-width: 820px) {
  .hero { grid-template-columns: 1fr; }
  .hero-card { max-width: 560px; }
  .toc { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lesson-grid { grid-template-columns: 1fr; }
  .media-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  html, body { background-color: #bfe9ff !important; }
  .shell { width: min(100% - 28px, 1120px); }
  .top-nav { align-items: flex-start; flex-direction: column; padding: 14px 0; }
  .top-links { width: 100%; justify-content: flex-start; }
  .top-links a { flex: 1; }
  .hero { padding: 42px 0 48px; }
  .hero-actions .button { width: 100%; }
  .section-heading { align-items: flex-start; flex-direction: column; }
  .download-table-wrap { overflow: visible; border: 0; background: transparent; box-shadow: none; }
  .download-table,
  .download-table tbody,
  .download-table tr,
  .download-table td { display: block; width: 100%; }
  .download-table thead { display: none; }
  .download-table tr {
    margin-bottom: 12px;
    padding: 15px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: var(--surface);
    box-shadow: var(--shadow);
  }
  .download-table td {
    display: grid;
    grid-template-columns: 88px 1fr;
    gap: 10px;
    padding: 8px 0;
    border: 0;
  }
  .download-table td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 10px;
    font-weight: 900;
    letter-spacing: .08em;
    text-transform: uppercase;
  }
  .download-table .button { margin-top: 4px; }
  .toc { grid-template-columns: 1fr; }
  .training-card { padding: 22px 18px; border-radius: 18px; }
  .diagram-card { margin-inline: -4px; padding: 10px; }
  .exercise-diagram { max-height: 340px; }
  .section-title { align-items: flex-start; flex-direction: column; gap: 0; }
}

@media (max-width: 380px) {
  .dose { grid-template-columns: 1fr; }
  .qr-card { grid-template-columns: 64px 1fr; }
  .qr { width: 64px; height: 64px; }
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --sky: #183f53;
    --sky-strong: #24617d;
    --blue: #8bd8fa;
    --blue-deep: #bfe9ff;
    --pink: #ff9bc0;
    --pink-soft: #432238;
    --paper: #091f2b;
    --surface: #103344;
    --surface-blue: #123c50;
    --text: #edf8fc;
    --muted: #bdd7e3;
    --border: #2b5b70;
    --action: #bfe9ff;
    --action-text: #102a3a;
    --shadow: 0 18px 45px rgba(0, 0, 0, .28);
  }
  .site-header { background: linear-gradient(135deg, #183f53, #30253c); }
  .hero-card { background: rgba(16, 51, 68, .82); }
  .button:hover { color: #ffffff; }
  .site-footer { background: #12384b; }
}

@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after {
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
  }
}

@media print {
  @page { size: A4; margin: 14mm; }
  * { box-shadow: none !important; }
  body { background: #ffffff; color: #102a3a; font-size: 11pt; }
  .skip-link,
  .top-nav,
  .hero-actions,
  .downloads,
  .contents,
  .back-link,
  .site-footer { display: none !important; }
  .site-header { border: 0; background: #ffffff; }
  .hero { display: block; padding: 0 0 12mm; }
  .hero-card { margin-top: 8mm; border-color: #b9dce9; background: #eef8fd; }
  .eyebrow { background: #ffe3ed; }
  main { padding: 0; }
  .guide-heading { display: none; }
  .training-card {
    margin: 0;
    padding: 0;
    border: 0;
    border-radius: 0;
    break-before: page;
    box-shadow: none;
  }
  .diagram-card { break-inside: avoid; }
  .exercise-diagram { max-height: 86mm; }
  .lesson-grid { grid-template-columns: 1.35fr .65fr; gap: 8mm; }
  .coach-note { background: #ffe3ed; }
  .media-grid { grid-template-columns: 1fr 45mm; }
  .video-card,
  .qr-card { break-inside: avoid; background: #f7fcff; }
  .qr-card { grid-template-columns: 25mm 1fr; }
  .qr { width: 25mm; height: 25mm; }
}
"""
