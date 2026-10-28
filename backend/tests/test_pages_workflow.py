"""Phase 8a: the GitHub Pages workflow is valid for the rules of docs/DEPLOY.md (stdlib parser, scripts/check_workflow.py)."""
import sys

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import check_workflow as W  # noqa: E402

TEXT = (REPO / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")


def test_the_workflow_follows_the_deployment_rules():
    assert W.check(W.parse(TEXT)) == []


def test_the_checker_rejects_secrets_extra_permissions_unpinned_actions_and_the_backend():
    for bad in (TEXT.replace("id-token: write", "id-token: write\n  contents: write"), TEXT.replace("actions/checkout@v4", "actions/checkout@main"),
                TEXT.replace("npm test", "npm test\n        env:\n          K: ${{ secrets.X }}"), TEXT.replace("npm test", "npx playwright test"),
                TEXT.replace("branches: [master]", "branches: [master, dev]")):
        assert W.check(W.parse(bad)), bad[:0]


def test_the_checker_reports_unreadable_yaml():
    import pytest
    with pytest.raises(ValueError):
        W.parse("a:\n\tb: 1\n")
