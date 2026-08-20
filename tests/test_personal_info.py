"""Personal info must never live in tracked files — it comes from .env
(gitignored) or the local SQLite DB (gitignored)."""
import subprocess
from pathlib import Path

from config import settings
from core.profile import apply_env_identity

REPO = Path(__file__).resolve().parent.parent

# Original author's info that was scrubbed, plus generic leak canaries.
FORBIDDEN = ["parmanand", "prajapati", "doctustech"]

TEXT_SUFFIXES = {".py", ".yaml", ".yml", ".md", ".js", ".html", ".css",
                 ".json", ".txt", ".example", ".gitignore"}


def tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [REPO / f for f in out
            if ((REPO / f).suffix.lower() in TEXT_SUFFIXES
                or (REPO / f).name in (".env.example", ".gitignore"))
            and (REPO / f) != Path(__file__).resolve()]


def test_no_personal_info_in_tracked_files():
    hits = []
    for f in tracked_files():
        try:
            text = f.read_text(errors="ignore").lower()
        except OSError:
            continue
        for word in FORBIDDEN:
            if word in text:
                hits.append(f"{f.relative_to(REPO)}: contains '{word}'")
    assert not hits, "Personal info found in tracked files:\n" + "\n".join(hits)


def test_env_and_db_are_gitignored():
    gitignore = (REPO / ".gitignore").read_text()
    assert ".env" in gitignore
    assert "*.db" in gitignore


def test_env_identity_fills_placeholder_name(monkeypatch):
    monkeypatch.setattr(settings, "CANDIDATE_NAME", "TestName")
    cfg = apply_env_identity({"outreach": {"candidate_name": "[Your Name]"}})
    assert cfg["outreach"]["candidate_name"] == "TestName"
    cfg = apply_env_identity({"outreach": {"candidate_name": ""}})
    assert cfg["outreach"]["candidate_name"] == "TestName"


def test_env_identity_respects_profile_name(monkeypatch):
    monkeypatch.setattr(settings, "CANDIDATE_NAME", "TestName")
    cfg = apply_env_identity({"outreach": {"candidate_name": "ProfileName"}})
    assert cfg["outreach"]["candidate_name"] == "ProfileName"


def test_env_identity_no_env_set(monkeypatch):
    monkeypatch.setattr(settings, "CANDIDATE_NAME", "")
    cfg = apply_env_identity({"outreach": {"candidate_name": "[Your Name]"}})
    assert cfg["outreach"]["candidate_name"] == "[Your Name]"


def test_env_identity_does_not_mutate_input_outreach():
    original = {"candidate_name": "[Your Name]"}
    apply_env_identity({"outreach": original})
    assert original == {"candidate_name": "[Your Name]"}
