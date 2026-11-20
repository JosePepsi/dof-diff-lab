from datetime import date
from pathlib import Path
import json
from urllib.error import HTTPError
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dof_diff_lab.intelligence import sync_date
from dof_diff_lab.monitor import ParseError, SourceResponse

HTML = b"""
<html><body>
<p>Fecha: 18/08/2026 - Edicion Matutina</p>
<p>PRIMERA</p><p>PODER EJECUTIVO</p><p>SECRETARIA DE ECONOMIA</p>
<a href='https://dof.gob.mx/nota_detalle.php?codigo=5796484&fecha=18/08/2026'>Acuerdo de comercio exterior.</a>
</body></html>
"""

GENERIC_SHELL = b"<html><body><p>Diario Oficial de la Federacion</p></body></html>"


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = sync_date(
            date(2026, 8, 18),
            root,
            sidof_fetch=lambda _date: [{
                "code": "5796484",
                "title": "Acuerdo de comercio exterior.",
                "canonical_url": "https://sidof.segob.gob.mx/notas/5796484",
                "source_api_url": "https://sidof.segob.gob.mx/dof/sidof/notas/nota/5796484",
                "publication_date": "2026-08-18",
                "edition": "matutina",
                "section": "PRIMERA",
                "issuer_primary": "PODER EJECUTIVO",
                "issuer_secondary": "SECRETARIA DE ECONOMIA",
                "source_id": "sidof",
                "title_available": True,
                "has_html": True,
                "has_document": True,
                "has_image": True,
                "page_start": 2,
                "page_end": 5,
                "journal_code": "300001",
            }],
        )
        assert result["source_id"] == "sidof"
        path = root / "data" / "normalized" / "2026-08-18" / "matutina.json"
        assert path.is_file()
        payload = json.loads(path.read_text(encoding="utf-8"))
        note = payload["notes"][0]
        assert note["code"] == "5796484"
        assert note["tags"]
        assert note["canonical_url"] == "https://sidof.segob.gob.mx/notas/5796484"
        assert note["source_api_url"].endswith("/notas/nota/5796484")
        assert note["title_available"] is True
        assert note["has_html"] is True
        assert note["has_document"] is True
        assert note["has_image"] is True
        assert note["page_start"] == 2
        assert note["page_end"] == 5
        assert note["journal_code"] == "300001"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = sync_date(
            date(2026, 8, 18),
            root,
            sidof_fetch=lambda _date: [],
            dof_fetch=lambda _url: SourceResponse(200, "text/html", HTML),
        )
        assert result["source_id"] == "dof_index"
        assert result["status"] == "changed"

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = sync_date(
            date(2026, 8, 18),
            root,
            sidof_fetch=lambda _date: (_ for _ in ()).throw(OSError("temporary outage")),
            dof_fetch=lambda _url: SourceResponse(200, "text/html", HTML),
        )
        assert result["source_id"] == "dof_index"
        assert "temporary outage" in str(result["sidof_error"])

    dof_called = False

    def unexpected_dof(_url: str) -> SourceResponse:
        nonlocal dof_called
        dof_called = True
        return SourceResponse(200, "text/html", HTML)

    try:
        sync_date(
            date(2026, 8, 18),
            Path("."),
            sidof_fetch=lambda _date: (_ for _ in ()).throw(RuntimeError("programming bug")),
            dof_fetch=unexpected_dof,
        )
    except RuntimeError as error:
        assert str(error) == "programming bug"
    else:
        raise AssertionError("Programming errors from SIDOF normalization must propagate")
    assert dof_called is False

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        result = sync_date(
            date(2026, 8, 29),
            root,
            sidof_fetch=lambda _date: [],
            dof_fetch=lambda _url: SourceResponse(200, "text/html", GENERIC_SHELL),
        )
        assert result["status"] == "no_edition"
        assert result["source_id"] == "sidof+dof_index"
        assert (root / "data" / "normalized" / "2026-08-29" / "matutina.json").is_file()

    with tempfile.TemporaryDirectory() as directory:
        try:
            sync_date(
                date(2026, 8, 31),
                Path(directory),
                sidof_fetch=lambda _date: [],
                dof_fetch=lambda _url: SourceResponse(200, "text/html", GENERIC_SHELL),
            )
        except ParseError:
            pass
        else:
            raise AssertionError("An empty SIDOF response must not hide a malformed weekday DOF response")

    # Issue #3: no_edition evidence-based and fail-closed.
    def confirmed(day: date, sidof) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = sync_date(day, root, sidof_fetch=sidof, dof_fetch=lambda _u: SourceResponse(200, "text/html", GENERIC_SHELL))
            manifest = json.loads((root / "data" / "manifests" / day.isoformat() / "matutina.json").read_text(encoding="utf-8"))
            assert manifest["source"]["dof_raw_sha256"]
            assert result["status"] == "no_edition"
            return manifest["source"]

    assert confirmed(date(2026, 11, 15), lambda _d: [])["no_edition_basis"] == "weekend"
    assert confirmed(date(2026, 11, 16), lambda _d: [])["no_edition_basis"] == "holiday:Día de la Revolución"

    def must_fail(day: date, sidof, dof=lambda _u: SourceResponse(200, "text/html", GENERIC_SHELL)) -> None:
        with tempfile.TemporaryDirectory() as directory:
            try:
                sync_date(day, Path(directory), sidof_fetch=sidof, dof_fetch=dof)
            except ParseError:
                assert not (Path(directory) / "data").exists()
            else:
                raise AssertionError(f"{day} must fail closed")

    must_fail(date(2026, 11, 17), lambda _d: [])  # dia habil con indice malformado

    # SIDOF contesta 406 a un dia sin edicion (observado 2026-11-15 y 2026-11-16).
    def sidof_status(code: int):
        def fetch(_d):
            raise OSError(f"No se pudo consultar SIDOF: HTTP Error {code}") from HTTPError("https://sidof.example", code, "x", {}, None)
        return fetch

    source = confirmed(date(2026, 11, 15), sidof_status(406))
    assert source["no_edition_basis"] == "weekend" and source["sidof_http_status"] == 406 and source["sidof_empty"] is False
    assert confirmed(date(2026, 11, 16), sidof_status(406))["no_edition_basis"] == "holiday:Día de la Revolución"
    must_fail(date(2026, 11, 17), sidof_status(406))  # 406 en dia habil ordinario no confirma nada
    must_fail(date(2026, 11, 16), sidof_status(500))  # otro estado HTTP en feriado
    must_fail(date(2026, 11, 16), sidof_status(403))
    must_fail(date(2026, 11, 15), sidof_status(404))
    must_fail(date(2026, 11, 15), lambda _d: (_ for _ in ()).throw(OSError("network down")))  # SIDOF caido en fin de semana
    must_fail(date(2026, 11, 16), lambda _d: (_ for _ in ()).throw(OSError("network down")))  # SIDOF caido en feriado
    # Otro ParseError (nota duplicada) en feriado tampoco se acepta como no_edition.
    dup = b"<html><body><p>Fecha: 16/11/2026 - Edicion Matutina</p><a href='https://dof.gob.mx/nota_detalle.php?codigo=1&fecha=16/11/2026'>A.</a><a href='https://dof.gob.mx/nota_detalle.php?codigo=1&fecha=16/11/2026'>A.</a></body></html>"
    must_fail(date(2026, 11, 16), lambda _d: [], dof=lambda _u: SourceResponse(200, "text/html", dup))


if __name__ == "__main__":
    main()