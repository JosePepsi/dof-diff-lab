# DOF Intelligence Lab architecture

## Scope

DOF Intelligence Lab is a small, traceable ingestion and search system for Mexico's Diario Oficial de la Federación. It does not determine legal effect. Official DOF/SIDOF publications remain the source of truth.

## Runtime flow

```text
SIDOF daily JSON (primary structured source)
        |
        | notes present
        v
normalize editions + provenance
        |
        +--> deterministic title tags
        +--> SHA-256 record hashes
        +--> versioned JSON / manifests / diffs
        +--> static inspection page
        |
        v
SQLite FTS5 corpus (generated artifact)

SIDOF unavailable or empty
        |
        v
DOF HTML index (independent official fallback/cross-check)
```

Tavily is outside the ingestion trust path. The optional `discover` command uses Tavily Search only to locate candidate URLs and restricts both requests and returned results to official DOF/SIDOF hosts. Discovery output is never treated as an authoritative publication without an official-source adapter.

## Modules

| Module | Responsibility |
|---|---|
| `sources.py` | Official source registry, SIDOF URLs, daily response normalization and public provenance fields. |
| `monitor.py` | Deterministic DOF HTML parser, fallback capture, tags, hashes, manifests, diffs and static rendering. |
| `site.py` | Página estática autocontenida (HTML+CSS+JS mínimo) con modo claro/oscuro; `render_site` se reexporta desde `monitor.py`. |
| `intelligence.py` | Orchestration CLI: `sync`, `build`, `search`, `discover`; SIDOF-first policy and fallback rules. |
| `corpus.py` | Rebuildable SQLite FTS5 index over normalized records. |
| `discovery.py` | Optional Tavily URL discovery with an official-host allowlist. |
| `__main__.py` | Thin package entrypoint forwarding to the intelligence CLI. |
| `web_watch.py` | Independent polling of verified official SNICE, ANAM, SAT and VUCEM pages/documents; writes separate snapshots and transition diffs. |

The project intentionally has no Python runtime dependencies outside the standard library. SQLite FTS5 is supplied by CPython's SQLite build. Tavily is called through `urllib`, so no SDK is required.

## Monitoreo complementario de portales

`.github/workflows/web-watch.yml` polls the sources below every six hours and can also be started manually. It uses only Python's standard library and commits evidence under `data/web-watch/`. Both publication workflows share a concurrency group so they do not race while pushing commits. The watcher fails the run on HTTP, MIME, decoding, parsing, redirect, or prior-state errors; it does not reinterpret an unavailable source as “no change.”

| Source | Watched evidence | Coverage boundary |
|---|---|---|
| SNICE home, DOF history, legal library, and notices/permits | Visible page text hash and official linked titles/URLs | A page change is a review lead, not proof of a new or legally effective instrument. |
| ANAM RSS feed | RSS item title, official link, date and summary | The official feed was empty when verified; no SAT classification-criteria feed was confirmed. |
| SAT annual RGCE index, 2026 RGCE and Anexo 22 PDFs | Relevant annual-index links filtered by RGCE (including its Anexo 22), NICO and classification terms, plus PDF SHA-256 and byte length | The official landing page is followed through its meta-refresh; fixed 2026 PDFs detect replacement at those locations, not every future document. |
| VUCEM home page | Visible text hash and official linked titles/URLs | No stable public Anexo 22 catalog was confirmed; the page monitor is not a catalog monitor. |

HTML is parsed without executing scripts. Non-official links are counted but excluded. Transient network errors and HTTP 408/425/429/5xx responses are retried up to three times with bounded exponential delay; permanent HTTP errors fail immediately. PDFs are downloaded only in memory to hash them; the repository stores no raw page or PDF bytes. Snapshots contain source metadata, hashes and extracted official link records. A baseline is recorded on first success; later changes create a transition JSON under `data/web-watch/diffs/<source-id>/`. An unchanged poll does not rewrite files, so it creates no commit.

Sources are polled independently within the run. A failed source makes the job fail, while successful sources still save their snapshots; an `always()` publication step commits only those evidence files and does not turn the failed run green. This avoids losing valid changes from other portals while keeping an outage visible in Actions.

This monitoring path is deliberately separate from `data/normalized/`, manifests and DOF publication diffs. It does not update legal catalogs, infer tariff effects, or replace DOF/SIDOF as the primary source. The scheduled job runs at 03:23, 09:23, 15:23 and 21:23 UTC.

## Source policy

`sidof.segob.gob.mx` and `dof.gob.mx` are primary official sources. SIDOF is preferred because its daily service exposes matutina, vespertina and extraordinaria groups. The DOF HTML index remains valuable as an independent fallback and for cross-checking no-publication states.

Each SIDOF record preserves a human-facing canonical URL plus its machine-facing API URL when available. Availability flags (`has_html`, `has_document`, `has_image`), page range and journal code are retained when supplied by SIDOF. Missing titles are represented explicitly with `title_available=false`; synthetic fallback labels are not passed through title-classification rules.

## Editions and schedule

GitHub Actions checks the publication day in three windows: 16:17, 22:17 and 03:17 UTC. The publication date is resolved in `America/Mexico_City`, so the after-midnight UTC check still targets the intended Mexican publication date.

Repeated runs are idempotent. Existing normalized data for an edition is loaded before writing and compared by stable note identity plus record hash. A legitimate absence is `no_edition`; malformed weekday responses and source failures remain errors.

The Pages deployment runs only when the generated `site/` content changes, avoiding unnecessary deployment requests on repeated same-day captures. It uses a pinned `actions/deploy-pages` commit and makes at most three attempts, with bounded 15- and 30-second waits after failures. This helps recover from transient artifact-metadata API errors like those observed on 2026-11-25 and 2026-11-26; it cannot repair a persistent GitHub outage. If the last attempt fails, the job remains failed and deployment errors are never hidden as success.

### Ausencia confirmada (`no_edition`)

`no_edition` es un estado basado en evidencia y falla cerrado. Se confirma solo si se cumplen las tres condiciones:

1. La consulta a SIDOF tuvo éxito (sin error) y devolvió cero notas.
2. El índice del DOF falló únicamente con `NoRecognizableEditionError` (sin fecha ni edición reconocibles); cualquier otro `ParseError`, HTTP o MIME inesperado sigue siendo error.
3. La fecha es fin de semana o feriado obligatorio según `dof_diff_lab/calendar_mx.py`.

El manifiesto registra `source.no_edition_basis` (`weekend` o `holiday:<nombre>`), las URL consultadas y el SHA-256 de la respuesta del DOF. **«SIDOF sin contenido».** Para un día sin edición SIDOF no devuelve una lista vacía: contesta `HTTP 406 Not Acceptable` al listado de notas (observado el domingo 2026-11-15 y el lunes feriado 2026-11-16, con el índice del DOF respondiendo 200 sin edición reconocible). Por eso la primera condición se cumple también cuando SIDOF responde exactamente 406; el manifiesto lo registra en `source.sidof_http_status`. Cualquier otro error de SIDOF (tiempo agotado, 5xx, 403, 404) sigue sin confirmar nada.

Un día hábil no feriado con índice malformado, o un error de SIDOF distinto de ese 406 (incluso en fin de semana o feriado), termina en error. Si SIDOF o el índice traen notas en sábado, domingo o feriado (edición extraordinaria), se procesan normalmente.

Feriados (Ley Federal del Trabajo, art. 74): 1 de enero; primer lunes de febrero; tercer lunes de marzo; 1 de mayo; 16 de septiembre; 1 de octubre cada seis años desde 2024 (transmisión del Poder Ejecutivo Federal); tercer lunes de noviembre; 25 de diciembre. Origen: el monitor falló del 14 al 17 de noviembre de 2026 (el 16 fue feriado); ver issue #3.

## Stored artifacts

- `data/normalized/YYYY-MM-DD/<edition>.json`: canonical note records.
- `data/manifests/YYYY-MM-DD/<edition>.json`: provenance and parser/schema metadata.
- `data/diffs/YYYY-MM-DD[-edition].md`: deterministic changes for human review.
- `data/state/latest.json`: latest successful operational state.
- `site/index.html`: generated static inspection view.
- `.tmp/dof-corpus.sqlite3`: local FTS database. GitHub Actions writes it to `tmp/dof-corpus.sqlite3` to include it in the run artifact. Both directories are ignored by Git.

Raw DOF/SIDOF responses are not committed. Hashes and source metadata are retained where the capture path exposes them.

## Deliberate non-features

There is no vector database, autonomous legal agent, LLM classification, Selenium/browser scraper, OCR pipeline, or Tavily crawler in the production path. Those would add cost and failure modes without being necessary for the current corpus size and retrieval needs. Semantic/vector retrieval can be added later behind the existing normalized corpus only if evaluation shows a measurable benefit over FTS5.

## Verification contract

The CI suite is network-free and covers package entrypoint behavior, DOF parsing and retry semantics, no-publication handling, SIDOF edition normalization, provenance retention, corpus search, Tavily host restrictions, workflow permissions/scheduling, and public-readiness safeguards. GitHub Actions are pinned by commit SHA.
