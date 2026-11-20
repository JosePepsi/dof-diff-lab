"""Presentación estática del monitor: una sola página HTML autocontenida y determinista.

Sin fuentes, scripts, imágenes ni rastreadores externos. Solo CSS y un JS mínimo
(opcional) para filtrar tarjetas; la página funciona completa sin JavaScript.
"""
from __future__ import annotations

from datetime import date
from html import escape
import unicodedata

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")

STATUS = {
    "changed": ("Con cambios", "Se detectaron altas, bajas o modificaciones frente a la captura previa."),
    "no_change": ("Sin cambios", "El catálogo coincide con la captura previa de esta edición."),
    "no_edition": ("Sin edición confirmada", "No se confirmó una edición publicada para esta fecha."),
}

TYPE_LABELS = {
    "acuerdo": "Acuerdo", "aviso": "Aviso", "circular": "Circular", "convenio": "Convenio", "convocatoria": "Convocatoria",
    "decreto": "Decreto", "norma": "Norma", "otro": "Otro", "resolucion": "Resolución", "sentencia": "Sentencia",
}
TOPIC_LABELS = {
    "data_protection": "Protección de datos", "energy": "Energía", "environment": "Medio ambiente", "financial": "Financiero",
    "fiscal": "Fiscal", "health": "Salud", "labor": "Laboral", "other": "Sin tema específico", "public_procurement": "Contrataciones públicas",
    "trade": "Comercio exterior",
}

CSS = """
:root{color-scheme:light dark;--bg:#f4f6f3;--surface:#ffffff;--surface-2:#eef2ee;--text:#1b211e;--muted:#56625b;--line:#d5dcd6;--accent:#006b48;--accent-fill:#00855a;--on-accent:#ffffff;--bar:#00855a;--bar-track:#e3e9e4;--focus:#0b5cad;
--b-changed-bg:#dff3e9;--b-changed-fg:#00573a;--b-same-bg:#e6eaee;--b-same-fg:#38434d;--b-none-bg:#fcefd0;--b-none-fg:#6b4600;--shadow:0 1px 2px rgba(20,30,25,.06),0 4px 16px rgba(20,30,25,.05)}
@media (prefers-color-scheme:dark){:root{--bg:#0e1210;--surface:#151a17;--surface-2:#1c231f;--text:#e9eeea;--muted:#a5b1aa;--line:#2b3430;--accent:#4fcf9d;--accent-fill:#4fcf9d;--on-accent:#06150f;--bar:#4fcf9d;--bar-track:#26302b;--focus:#7db8ff;
--b-changed-bg:#173a2c;--b-changed-fg:#8ee6c1;--b-same-bg:#262e34;--b-same-fg:#c3ccd3;--b-none-bg:#3a2e12;--b-none-fg:#f0cf85;--shadow:none}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--accent);text-underline-offset:.18em}
a:hover{text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
.skip{position:absolute;left:12px;top:-60px;background:var(--accent-fill);color:var(--on-accent);padding:.6rem 1rem;border-radius:8px;z-index:10;font-weight:600}
.skip:focus{top:12px}
.wrap{max-width:68rem;margin:0 auto;padding:0 16px}
header.top{background:var(--surface);border-bottom:1px solid var(--line)}
header.top .wrap{padding-top:28px;padding-bottom:26px}
.eyebrow{margin:0 0 6px;font-size:.8rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
h1{margin:0;font-size:clamp(1.65rem,4.5vw,2.4rem);line-height:1.15;letter-spacing:-.02em}
.meta{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin:16px 0 0;color:var(--muted)}
.meta time{color:var(--text);font-weight:600}
.badge{display:inline-flex;align-items:center;gap:7px;padding:4px 12px;border-radius:999px;font-weight:700;font-size:.88rem}
.badge::before{content:"";width:9px;height:9px;border-radius:50%;background:currentColor}
.badge.changed{background:var(--b-changed-bg);color:var(--b-changed-fg)}
.badge.no_change{background:var(--b-same-bg);color:var(--b-same-fg)}
.badge.no_edition{background:var(--b-none-bg);color:var(--b-none-fg)}
.lede{margin:14px 0 0;max-width:46rem;color:var(--muted)}
main.wrap{padding-top:28px;padding-bottom:8px}
section{margin:0 0 36px}
h2{font-size:1.2rem;margin:0 0 14px;letter-spacing:-.01em}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 36px;padding:0;list-style:none}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.stat b{display:block;font-size:2rem;line-height:1.1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{line-height:1.3;display:block;margin-top:4px;color:var(--muted);font-size:.9rem}
.charts{align-items:start;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:var(--shadow)}
.panel h3{margin:0 0 12px;font-size:1rem}
.bars{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.bars li{display:grid;grid-template-columns:minmax(0,9.5rem) 1fr 2.2rem;gap:10px;align-items:center;font-size:.9rem}
.bars .lbl{overflow-wrap:anywhere;line-height:1.25}
.bars .track{height:10px;background:var(--bar-track);border-radius:999px;overflow:hidden}
.bars .track i{display:block;height:100%;background:var(--bar);border-radius:999px}
.bars b{text-align:right;font-variant-numeric:tabular-nums}
.empty{background:var(--surface);border:1px dashed var(--line);border-radius:12px;padding:28px 24px}
.empty h2{margin-bottom:8px}
.empty p{margin:0 0 10px;max-width:46rem;color:var(--muted)}
.empty p:last-child{margin:0}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 14px}
.controls[hidden]{display:none}
.controls label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.controls input{flex:1 1 240px;min-width:0;font:inherit;color:var(--text);background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.6rem .85rem}
.controls input::placeholder{color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{font:inherit;font-size:.85rem;font-weight:600;color:var(--text);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:.35rem .8rem;cursor:pointer}
.chip:hover{border-color:var(--accent)}
.chip[aria-pressed=true]{background:var(--accent-fill);border-color:var(--accent-fill);color:var(--on-accent)}
.count{margin:0 0 12px;color:var(--muted);font-size:.9rem}
.notes-intro{margin:0 0 16px;color:var(--muted);max-width:46rem}
.cards{display:grid;gap:12px;margin:0;padding:0;list-style:none}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.card[hidden]{display:none}
.card h3{margin:6px 0 8px;font-size:1.02rem;line-height:1.4;font-weight:600}
.card .top{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.code{font:600 .88rem ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;padding:2px 8px;border-radius:6px;background:var(--surface-2);color:var(--accent)}
.pill{font-size:.78rem;font-weight:600;padding:2px 9px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.where{margin:0;color:var(--muted);font-size:.88rem}
details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
summary{cursor:pointer;font-size:.88rem;font-weight:600;color:var(--accent);padding:2px 0}
details ul{margin:10px 0 0;padding:0;list-style:none;display:grid;gap:8px}
details li{background:var(--surface-2);border-radius:8px;padding:9px 11px;font-size:.85rem;color:var(--muted)}
details li strong{color:var(--text)}
.notice{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--accent-fill);border-radius:12px;padding:20px 22px}
.notice h2{margin-bottom:10px}
.notice p{margin:0 0 10px;max-width:50rem}
.notice p:last-child{margin:0}
footer{margin-top:12px;padding:8px 0 40px;color:var(--muted);font-size:.85rem}
footer p{margin:0 0 6px}
@media (max-width:520px){.bars li{grid-template-columns:minmax(0,7.2rem) 1fr 2rem}.card{padding:14px}.stat b{font-size:1.7rem}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{:root{--bg:#fff;--surface:#fff;--surface-2:#fff;--text:#000;--muted:#333;--line:#999;--accent:#000;--shadow:none}
.skip,.controls,.count{display:none!important}body{font-size:11pt}.card,.panel,.stat{break-inside:avoid;box-shadow:none}.card[hidden]{display:block}
a[href^=http]::after{content:" (" attr(href) ")";font-size:.8em;font-weight:400;word-break:break-all}
.bars .track{border:1px solid #666}.bars .track i{background:#000}}
"""

JS = """
(function(){
var c=document.getElementById('controls');if(!c)return;
var cards=[].slice.call(document.querySelectorAll('.card')),q=document.getElementById('q'),chips=[].slice.call(c.querySelectorAll('.chip')),out=document.getElementById('count'),sel='';
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}
function run(){var t=norm(q.value.trim()),n=0;cards.forEach(function(k){var ok=(!sel||k.dataset.type===sel)&&(!t||k.dataset.q.indexOf(t)>-1);k.hidden=!ok;if(ok)n++});
out.textContent='Mostrando '+n+' de '+cards.length+' notas';}
q.addEventListener('input',run);
chips.forEach(function(b){b.addEventListener('click',function(){sel=b.dataset.type===sel?'':b.dataset.type;chips.forEach(function(x){x.setAttribute('aria-pressed',String(x.dataset.type===sel))});run()})});
window.addEventListener('beforeprint',function(){cards.forEach(function(k){k.hidden=false});[].forEach.call(document.querySelectorAll('details'),function(d){d.open=true})});
c.hidden=false;out.hidden=false;run();
})();
"""


def _label(mapping: dict[str, str], value: str) -> str:
    return mapping.get(value, value.replace("_", " ").capitalize())


SMALL = {"de", "del", "la", "las", "los", "y", "e", "el", "para", "en"}


def _name(value: str) -> str:
    words = value.lower().split()
    return " ".join(w if (w in SMALL and i) else w.capitalize() for i, w in enumerate(words))


def _long_date(value: str) -> str:
    try:
        d = date.fromisoformat(value)
    except ValueError:
        return value
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def _index_url(value: str) -> str | None:
    try:
        d = date.fromisoformat(value)
    except ValueError:
        return None
    return f"https://dof.gob.mx/index_113.php?year={d.year}&month={d.month:02d}&day={d.day:02d}"


def _bars(items: dict[str, int], labels: dict[str, str] | None = None, limit: int | None = None) -> str:
    rows = sorted(items.items(), key=lambda kv: (-kv[1], kv[0]))
    if limit:
        rows = rows[:limit]
    if not rows:
        return "<p class=\"where\">Sin datos.</p>"
    top = max(count for _, count in rows) or 1
    lis = "".join(
        f"<li><span class=\"lbl\">{escape(_label(labels, name) if labels else _name(name))}</span>"
        f"<span class=\"track\" aria-hidden=\"true\"><i style=\"width:{count / top * 100:.1f}%\"></i></span><b>{count}</b></li>"
        for name, count in rows
    )
    return f"<ul class=\"bars\">{lis}</ul>"


def _tag_value(note: dict[str, object], name: str) -> str:
    for item in note["tags"]:
        if item["name"] == name:
            return str(item["value"])
    return ""


def _card(note: dict[str, object]) -> str:
    doc_type = _tag_value(note, "document_type") or "otro"
    topic = _tag_value(note, "topic")
    code = str(note["code"] or "sin código")
    title = str(note["title"])
    issuer = str(note.get("issuer_secondary") or note.get("issuer_primary") or "")
    section = str(note.get("section") or "")
    where = " · ".join(part for part in (_name(section) if section else "", _name(issuer)) if part)
    search = " ".join((code, title, issuer, section, _label(TYPE_LABELS, doc_type), _label(TOPIC_LABELS, topic) if topic else ""))
    tags = "".join(
        "<li>" + f"<strong>{escape(str(item['name']))}: {escape(str(item['value']))}.</strong> Regla: {escape(str(item['rule_id']))} ({escape(str(item['rule_version']))}). Evidencia: {escape(str(item['evidence']))}. Coincidencia de regla; no probabilidad ni conclusión jurídica.</li>"
        for item in note["tags"]
    )
    topic_pill = f"<span class=\"pill\">{escape(_label(TOPIC_LABELS, topic))}</span>" if topic and topic != "other" else ""
    where_html = f"<p class=\"where\">{escape(where)}</p>" if where else ""
    details = f"<details><summary>Coincidencias de reglas ({len(note['tags'])})</summary><ul>{tags}</ul></details>" if tags else ""
    return (
        f"<li class=\"card\" data-type=\"{escape(doc_type)}\" data-q=\"{escape(_fold(search))}\">"
        f"<div class=\"top\"><a class=\"code\" href=\"{escape(str(note['canonical_url']))}\">{escape(code)}</a>"
        f"<span class=\"pill\">{escape(_label(TYPE_LABELS, doc_type))}</span>{topic_pill}</div>"
        f"<h3>{escape(title)}</h3>{where_html}{details}</li>"
    )


def _fold(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text.lower()) if not unicodedata.combining(ch))


def render_site(manifest: dict[str, object], notes: list[dict[str, object]]) -> str:
    insights = manifest["insights"]
    status = str(manifest["status"])
    status_label, status_help = STATUS.get(status, (status, ""))
    pub = str(manifest["publication_date"])
    count = int(manifest["note_count"])
    types = insights["by_document_type"]
    topics = insights["by_topic"]
    issuers = insights.get("by_issuer", {})
    real_topics = {k: v for k, v in topics.items() if k != "other"}

    stats = (
        f"<li class=\"stat\"><b>{count}</b><span>Notas publicadas</span></li>"
        f"<li class=\"stat\"><b>{len(types)}</b><span>Tipos documentales</span></li>"
        f"<li class=\"stat\"><b>{len(real_topics)}</b><span>Temas detectados</span></li>"
        f"<li class=\"stat\"><b>{len(issuers)}</b><span>Emisores</span></li>"
    )
    index_url = _index_url(pub)
    if status == "no_edition" or not notes:
        link = f" Puede consultar el índice oficial de esa fecha en <a href=\"{escape(index_url)}\">dof.gob.mx</a>." if index_url else ""
        body = (
            "<section class=\"empty\" aria-labelledby=\"vacio\"><h2 id=\"vacio\">Sin edición confirmada</h2>"
            "<p>Para esta fecha no se encontraron notas en las fuentes oficiales consultadas (SIDOF y el índice HTML del DOF), por lo que no hay catálogo que mostrar.</p>"
            "<p>Es un resultado esperable en días sin publicación, como fines de semana o festivos. No es un error del monitor y tampoco prueba por sí mismo que no exista publicación: la fuente primaria es la publicación oficial." + link + "</p>"
            "<p>El monitor volverá a consultar en su siguiente corrida programada.</p></section>"
        )
    else:
        chips = "".join(
            f"<button type=\"button\" class=\"chip\" data-type=\"{escape(k)}\" aria-pressed=\"false\">{escape(_label(TYPE_LABELS, k))} ({v})</button>"
            for k, v in sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))
        )
        body = (
            "<section aria-labelledby=\"graficas\"><h2 id=\"graficas\">Panorama</h2><div class=\"charts\">"
            f"<div class=\"panel\"><h3>Tipos documentales</h3>{_bars(types, TYPE_LABELS)}</div>"
            f"<div class=\"panel\"><h3>Temas detectados por reglas</h3>{_bars(topics, TOPIC_LABELS)}</div>"
            f"<div class=\"panel\"><h3>Principales emisores</h3>{_bars(issuers, None, 6)}</div></div></section>"
            "<section aria-labelledby=\"notas\"><h2 id=\"notas\">Coincidencias de reglas y evidencia</h2>"
            "<p class=\"notes-intro\">Las etiquetas describen coincidencias deterministas en títulos y metadatos; no determinan vigencia, alcance ni efecto jurídico. Cada código enlaza a la publicación oficial.</p>"
            "<div class=\"controls\" id=\"controls\" hidden><label for=\"q\">Buscar en las notas</label>"
            "<input id=\"q\" type=\"search\" placeholder=\"Buscar por código, título o emisor\" autocomplete=\"off\">"
            f"<div class=\"chips\" role=\"group\" aria-label=\"Filtrar por tipo documental\">{chips}</div></div>"
            "<p class=\"count\" id=\"count\" role=\"status\" aria-live=\"polite\" hidden></p>"
            f"<ul class=\"cards\">{''.join(_card(n) for n in notes)}</ul></section>"
        )
    edition = manifest.get("edition")
    edition_html = f"<span>Edición {escape(str(edition))}</span>" if edition else ""
    return "".join((
        "<!doctype html>\n<html lang=\"es\"><head><meta charset=\"utf-8\">",
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
        "<meta name=\"robots\" content=\"noindex,nofollow\"><meta name=\"color-scheme\" content=\"light dark\">",
        f"<title>Monitor diario del DOF · {escape(pub)}</title><style>{CSS}</style></head><body>",
        "<a class=\"skip\" href=\"#contenido\">Saltar al contenido</a>",
        "<header class=\"top\"><div class=\"wrap\"><p class=\"eyebrow\">Diario Oficial de la Federación</p><h1>Monitor diario del DOF</h1>",
        f"<p class=\"meta\"><span>Publicación del <time datetime=\"{escape(pub)}\">{escape(_long_date(pub))}</time></span>{edition_html}",
        f"<span class=\"badge {escape(status)}\">{escape(status_label)}</span></p>",
        f"<p class=\"lede\">{escape(status_help)} Catálogo derivado y verificable; la fuente primaria es la publicación oficial.</p>",
        "</div></header>",
        f"<main id=\"contenido\" class=\"wrap\"><ul class=\"stats\" aria-label=\"Resumen\">{stats}</ul>{body}",
        "<section class=\"notice\" aria-labelledby=\"aviso\"><h2 id=\"aviso\">Aviso importante</h2>",
        "<p><strong>No afiliación:</strong> este proyecto no está afiliado, patrocinado ni respaldado por el Diario Oficial de la Federación.</p>",
        "<p><strong>Fuente primaria:</strong> prevalece la publicación oficial enlazada. Este catálogo derivado no sustituye la fuente oficial ni constituye asesoría jurídica.</p>",
        "</section></main>",
        "<footer><div class=\"wrap\"><p>Página estática generada de forma determinista a partir de los catálogos normalizados del repositorio. Sin cookies, rastreadores ni recursos externos.</p>",
        f"<p>Estado técnico: <code>{escape(status)}</code> · Fecha: <code>{escape(pub)}</code></p></div></footer>",
        f"<script>{JS}</script></body></html>\n",
    ))
