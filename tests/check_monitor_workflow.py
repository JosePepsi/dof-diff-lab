from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "dof-monitor.yml"
CHECK_WORKFLOW = ROOT / ".github" / "workflows" / "check.yml"


def main() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = (
        "name: Monitor diario del DOF",
        "workflow_dispatch:",
        "schedule:",
        'cron: "17 16 * * *"',
        'cron: "17 22 * * *"',
        'cron: "17 3 * * *"',
        "TZ=America/Mexico_City date +%F",
        "concurrency:",
        "cancel-in-progress: false",
        "contents: read",
        "contents: write",
        "pages: write",
        "id-token: write",
        "PUBLICATION_DATE:",
        "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
        'date -u -d "$publication_date"',
        '[[ "$(date -u -d "$publication_date" +%F 2>/dev/null)" != "$publication_date" ]]',
        "python3 -m dof_diff_lab.intelligence sync",
        "python3 -m dof_diff_lab.intelligence build",
        "--database tmp/dof-corpus.sqlite3",
        "test -s tmp/dof-corpus.sqlite3",
        "            tmp/dof-corpus.sqlite3",
        "git add -- data site",
        "git diff --cached --quiet -- data site",
        "git commit -m",
        "git pull --rebase origin main",
        "if-no-files-found: error",
        "needs: [capture, publish]",
        "site_changed: ${{ steps.publication.outputs.site_changed }}",
        "if: needs.publish.outputs.site_changed == 'true'",
        "echo \"site_changed=false\" >> \"$GITHUB_OUTPUT\"",
        "echo \"site_changed=true\" >> \"$GITHUB_OUTPUT\"",
    )
    for fragment in required_fragments:
        assert fragment in text, fragment
    assert "pull_request:" not in text
    assert 'publication_date="${{ inputs.publication_date }}"' not in text
    assert "data/raw" not in text
    # New daily publication files start untracked; the no-op guard must inspect the index.
    assert text.index("git add -- data site") < text.index("git diff --cached --quiet -- data site") < text.index("git commit -m")
    assert "if git diff --quiet -- data site" not in text
    assert text.index("git commit -m") < text.index("git pull --rebase origin main") < text.index("git push")
    refs = re.findall(r"uses:\s*[^@\s]+@([^\s]+)", text)
    assert refs and all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs), refs

    check_text = CHECK_WORKFLOW.read_text(encoding="utf-8")
    for action_commit in (
        "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "5fda3b95a4ea91299a34e894583c3862153e4b97",
        "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
        "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
        "45bfe0192ca1faeb007ade9deae92b16b8254a0d",
        "fc324d3547104276b827a68afc52ff2a11cc49c9",
        "368f82528645a54fb793d4d04e342629a3f51346",
    ):
        assert action_commit in text or action_commit in check_text, action_commit
    assert "continue-on-error: true" in text
    assert "steps.deployment.outcome == 'failure'" in text
    assert "steps.deployment.outputs.page_url || steps.deployment_retry_action.outputs.page_url || steps.deployment_final_action.outputs.page_url" in text
    assert "steps.deployment_retry_action.outcome == 'failure'" in text
    assert "sleep 15" in text
    assert "sleep 30" in text
    assert text.count("actions/deploy-pages@368f82528645a54fb793d4d04e342629a3f51346") == 3
    for command in (
        "python3 tests/check_entrypoint.py",
        "python3 tests/check_monitor.py",
        "python3 tests/check_monitor_workflow.py",
        "python3 tests/check_public_readiness.py",
        "python3 tests/check_sources.py",
        "python3 tests/check_corpus.py",
        "python3 tests/check_discovery.py",
        "python3 tests/check_intelligence.py",
        "python3 tests/check_repository_integrity.py",
    ):
        assert command in check_text, command
    for legacy_dependency in ("apt-get", "ocrmypdf", "tesseract", "pdftotext", "pdfunite"):
        assert legacy_dependency not in check_text, legacy_dependency


if __name__ == "__main__":
    main()