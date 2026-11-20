# DOF Intelligence Lab

Monitor trazable y corpus consultable del **Diario Oficial de la Federación (DOF)** de México. Prefiere los datos abiertos estructurados de SIDOF, usa el índice HTML oficial del DOF como respaldo y contraste, conserva procedencia determinista (hashes, manifiestos, diffs) y publica una página estática de inspección.

> **No afiliación y uso responsable.** Este proyecto no está afiliado, patrocinado ni respaldado por el DOF ni por una autoridad pública. La fuente primaria siempre es la publicación oficial enlazada en `dof.gob.mx` o `sidof.segob.gob.mx`. Los catálogos, etiquetas, hashes y diffs son derivados técnicos: no determinan vigencia ni efectos jurídicos y no sustituyen la consulta oficial ni la asesoría profesional.

## Qué hace y por qué

| Pregunta | Respuesta |
|---|---|
| ¿Qué se publicó hoy? | Un catálogo normalizado por fecha y edición (matutina, vespertina, extraordinaria). |
| ¿Qué cambió respecto de la captura anterior? | Un diff determinista de altas, bajas y modificaciones. |
| ¿Puedo verificarlo? | Cada nota enlaza a la publicación oficial y lleva un hash SHA-256 de su registro. |
| ¿Puedo buscar? | Sí: índice local SQLite FTS5 reconstruible desde los catálogos. |
| ¿Dice qué ley está vigente? | No. Las etiquetas son coincidencias de reglas sobre títulos y metadatos. |

El entorno de ejecución usa solo la biblioteca estándar de Python: sin automatización de navegador, OCR, base vectorial ni SDK externo obligatorio.

## Cómo funciona

```text
SIDOF (JSON diario)  ──notas──▶  normalizar ediciones + procedencia
        │                              │
        │ no disponible o vacío        ├─▶ etiquetas por reglas, hashes SHA-256
        ▼                              ├─▶ data/normalized · manifests · diffs · state
Índice HTML del DOF                    ├─▶ site/index.html (página estática)
(respaldo y contraste)                 └─▶ corpus SQLite FTS5 (artefacto generado)
```

1. Consulta el JSON diario de SIDOF y normaliza las notas por edición.
2. Conserva metadatos oficiales, URL humanas, procedencia de la API, banderas de disponibilidad y hash por registro.
3. Si SIDOF falla o viene vacío, contrasta con el índice HTML oficial del DOF. Un día sin publicación confirmado por ambas fuentes queda como `no_edition`.
4. Escribe JSON normalizado, manifiestos, diffs y la página estática.
5. Reconstruye un corpus SQLite FTS5 para búsqueda léxica.
6. Opcionalmente usa Tavily solo para descubrir URL oficiales; nunca es fuente de verdad de la publicación.

## Inicio rápido

```bash
python3 -m dof_diff_lab sync --date 2026-08-29 --root .
python3 -m dof_diff_lab build --root . --database .tmp/dof-corpus.sqlite3
python3 -m dof_diff_lab search "comercio exterior" --database .tmp/dof-corpus.sqlite3
```

Descubrimiento opcional (requiere `TAVILY_API_KEY`):

```bash
export TAVILY_API_KEY="..."
python3 -m dof_diff_lab discover "DOF comercio exterior cambios recientes"
```

Analizador de respaldo, para diagnóstico:

```bash
python3 -m dof_diff_lab.monitor --date 2026-08-29 --root .
```

## Sitio publicado

`site/index.html` es **un solo archivo HTML autocontenido** generado de forma determinista (mismos datos, mismos bytes) por `dof_diff_lab/site.py`:

- Estado del día (`changed`, `no_change`, `no_edition`), fecha, tarjetas de resumen y gráficas de barras en CSS por tipo documental, tema y emisor.
- Una tarjeta por nota con enlace al DOF oficial; la evidencia de cada regla va en un `<details>`.
- Filtro de texto y por tipo con JavaScript mínimo opcional: sin JS la página sigue completa.
- Modo claro y oscuro (`prefers-color-scheme`), adaptable desde 360 px, enlace de salto, foco visible y hoja de estilos de impresión.
- Sin fuentes, scripts, imágenes ni rastreadores externos; `noindex,nofollow`.
- Los avisos de no afiliación y fuente primaria permanecen visibles.

## Triaje de cambios comerciales

El comando `triage` es **sin conexión y de solo lectura**: busca términos arancelarios o de regulación comercial en los **títulos publicados** de los catálogos ya normalizados. Sirve a investigadores y a proyectos como `arancel-mx` y `wiki-comercio-exterior-mx`; no es una fuente de leyes ni de aranceles automáticos.

```bash
python3 -m dof_diff_lab triage --root . --start 2026-11-01 --end 2026-11-10 --limit 100
```

La respuesta incluye reglas coincidentes, evidencia textual exacta, enlace oficial, hash de la nota y diagnóstico de cobertura. Cero coincidencias locales **no** prueba que no haya cambios relevantes; `priority_review` significa coincidencia de palabra clave en el título, **no** importancia jurídica, vigencia ni cambio arancelario confirmado. Detalles y límites en [Contrato de trade watch](docs/trade-watch-contract.md).

## Estructura de datos

| Ruta | Contenido |
|---|---|
| `data/normalized/AAAA-MM-DD/<edición>.json` | registros canónicos para comparar e ingerir al corpus |
| `data/manifests/AAAA-MM-DD/<edición>.json` | procedencia, versiones de analizador/esquema y hashes |
| `data/diffs/AAAA-MM-DD[-edición].md` | cambios legibles y deterministas |
| `data/state/latest.json` | último estado operativo |
| `site/index.html` | vista estática de inspección con enlaces a la fuente |
| `.tmp/dof-corpus.sqlite3` | base de búsqueda local generada; Actions la publica como `tmp/dof-corpus.sqlite3` dentro del artefacto de la corrida |

## Automatización

GitHub Actions consulta la fecha de publicación mexicana a las **16:17, 22:17 y 03:17 UTC**. La corrida de las 03:17 UTC resuelve la fecha en `America/Mexico_City` para evitar consultar el día siguiente por error y dar otra ventana a ediciones vespertinas o extraordinarias.

El flujo sincroniza las fuentes oficiales, construye el corpus, sube derivados verificados, confirma solo los cambios en `data/` y `site/`, y despliega el sitio estático. Las acciones están fijadas por SHA de commit y los trabajos usan permisos mínimos.

## Límites de confianza

- La publicación oficial en `dof.gob.mx` / `sidof.segob.gob.mx` es la única fuente de verdad.
- Tavily queda fuera de la ruta de ingesta: solo localiza URL candidatas y se restringe a hosts oficiales.
- Las etiquetas son coincidencias deterministas de reglas, no probabilidades ni conclusiones jurídicas.
- No se conserva el HTML crudo (`raw_retained: false`); solo su hash.
- Un día sin notas confirmado es `no_edition`; respuestas HTTP/MIME inesperadas son errores, para no confundir una falla de fuente con ausencia de publicación.

## Verificaciones

```bash
for t in entrypoint monitor monitor_workflow public_readiness sources corpus discovery intelligence trade_watch repository_integrity site; do
  python3 tests/check_$t.py
done
```

No requieren red ni secretos. Consulte [`docs/monitor-architecture.md`](docs/monitor-architecture.md) para el diseño y [`SECURITY.md`](SECURITY.md) para reportes responsables.

## Límites de diseño

El sistema se mantiene deliberadamente determinista. SQLite FTS5 basta para el corpus actual y la terminología jurídica exacta; una capa vectorial o LLM solo se justificaría con evaluación que demuestre valor de recuperación. Las conclusiones jurídicas generadas por IA quedan fuera del límite de confianza de este repositorio.

## Licencia

El código es Apache-2.0. El contenido del DOF sigue sujeto a sus términos oficiales; este repositorio no pretende relicenciar publicaciones oficiales ni sustituir el diario.
