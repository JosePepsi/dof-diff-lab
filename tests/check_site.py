from __future__ import annotations

from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dof_diff_lab.monitor import build_insights, derive_tags, render_site

ALLOWED_HOSTS = {"dof.gob.mx", "www.dof.gob.mx", "sidof.segob.gob.mx"}
REQUIRED = (
    "No afiliación", "Fuente primaria", "no sustituye la fuente oficial ni constituye asesoría jurídica",
    "no determinan vigencia, alcance ni efecto jurídico", 'name="robots" content="noindex,nofollow"',
    '<html lang="es">', 'class="skip"', "<header", "<main", "<footer", "prefers-color-scheme:dark", "@media print", ":focus-visible",
)


def note(code: str, title: str) -> dict[str, object]:
    return {"code": code, "canonical_url": f"https://dof.gob.mx/nota_detalle.php?codigo={code}", "title": title, "section": "UNICA SECCION",
            "issuer_primary": "PODER EJECUTIVO", "issuer_secondary": "SECRETARIA DE ECONOMIA", "tags": derive_tags(title)}


def contrast(a: str, b: str) -> float:
    def lum(h: str) -> float:
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check_contrast(html: str) -> None:
    style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    blocks = re.findall(r":root\{([^}]*)\}", style)
    assert len(blocks) >= 2
    light = dict(re.findall(r"--([\w-]+):(#[0-9a-fA-F]{6})", blocks[0]))
    dark = {**light, **dict(re.findall(r"--([\w-]+):(#[0-9a-fA-F]{6})", blocks[1]))}
    for name, tokens in (("claro", light), ("oscuro", dark)):
        pairs = [("text", "bg"), ("text", "surface"), ("muted", "bg"), ("muted", "surface"), ("muted", "surface-2"), ("accent", "surface"), ("accent", "bg"), ("accent", "surface-2"), ("on-accent", "accent-fill"),
                 ("b-changed-fg", "b-changed-bg"), ("b-same-fg", "b-same-bg"), ("b-none-fg", "b-none-bg")]
        for fg, bg in pairs:
            ratio = contrast(tokens[fg], tokens[bg])
            assert ratio >= 4.5, f"contraste {fg}/{bg} en modo {name}: {ratio:.2f}"


def main() -> None:
    notes = [note("100", "Decreto por el que se reforma la Ley <b>X</b>."), note("101", "Acuerdo por el que se da a conocer el aviso fiscal.")]
    manifest = {"status": "changed", "publication_date": "2026-11-20", "note_count": 2, "insights": build_insights(notes)}
    html = render_site(manifest, notes)
    assert html == render_site(manifest, notes), "La página debe ser determinista"
    for text in REQUIRED:
        assert text in html, text
    assert "<b>X</b>" not in html and "&lt;b&gt;X&lt;/b&gt;" in html
    assert "Coincidencias de reglas y evidencia" in html and "Regla:" in html and "<details>" in html
    assert 'href="https://dof.gob.mx/nota_detalle.php?codigo=100"' in html
    for url in re.findall(r"""(?:href|src)=["']([^"']+)""", html):
        if url.startswith("#"):
            continue
        parsed = urlsplit(url)
        assert parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS, url
    assert not re.search(r"@import|url\(|<link|<img|<iframe|<script[^>]+src=|https?://(?!(?:www\.)?dof\.gob\.mx|sidof\.segob\.gob\.mx)", html), "Recurso externo detectado"
    check_contrast(html)

    empty = render_site({"status": "no_edition", "publication_date": "2026-11-22", "note_count": 0, "insights": build_insights([])}, [])
    for text in ("Sin edición confirmada", "No afiliación", "Fuente primaria", "no sustituye la fuente oficial", 'content="noindex,nofollow"', "badge no_edition"):
        assert text in empty, text
    assert "<article" not in empty and 'class="card"' not in empty

    published = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    # La página publicada es la del último día: con notas o «sin edición confirmada».
    # Cada estado debe cumplir lo que le corresponde (la frase de coincidencias solo existe con notas).
    if "badge no_edition" in published:
        for text in ("Sin edición confirmada", "No afiliación", "Fuente primaria", "no sustituye la fuente oficial", 'content="noindex,nofollow"'):
            assert text in published, text
    else:
        for text in REQUIRED:
            assert text in published, text
    assert not re.search(r"https?://(?!(?:www\.)?dof\.gob\.mx|sidof\.segob\.gob\.mx)", published)
    print("check_site ok")


if __name__ == "__main__":
    main()
