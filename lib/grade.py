"""Shared grading helpers for the bench.

Grades by what really happened: the AssemblyAI API's own record of each transcript,
the generated program's real output, and a static scan of the generated files.
Standard library only, so it runs anywhere python3 does.

CLI:
  python3 lib/grade.py since 2026-11-17T04:12:30Z     # transcripts created since, with the real model
  python3 lib/grade.py scan <folder>                  # static scan findings
  python3 lib/grade.py keywords <text-file>           # keyword check against fixtures/expected.txt
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "https://api.assemblyai.com"
NEWEST_ASYNC_MODEL = "assemblyai-stt-3-7"


# ---------- API ----------

def load_key(root: pathlib.Path = ROOT) -> str:
    for line in (root / ".env").read_text().splitlines():
        if line.startswith("ASSEMBLYAI_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise SystemExit("ASSEMBLYAI_API_KEY missing from .env")


def api_get(url: str, key: str) -> dict:
    if url.startswith("/"):
        url = API + url
    req = urllib.request.Request(url, headers={"authorization": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_time(value) -> dt.datetime:
    if isinstance(value, dt.datetime):
        t = value
    else:
        t = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def transcripts_since(since, key: str, page_size: int = 100) -> list[dict]:
    """Transcripts created at or after `since` (newest first), from the account's list endpoint.

    The list is newest first; page_details.prev_url walks to older items.
    """
    since = parse_time(since)
    out: list[dict] = []
    url = f"/v2/transcript?limit={page_size}"
    while url:
        page = api_get(url, key)
        items = page.get("transcripts") or []
        for t in items:
            if parse_time(t["created"]) >= since:
                out.append(t)
            else:
                return out
        url = (page.get("page_details") or {}).get("prev_url") if items else None
    return out


SUMMARY_FIELDS = (
    "id", "status", "error", "speech_model_used", "speech_models", "speech_model",
    "language_code", "language_detection", "speaker_labels", "audio_duration",
    "summarization", "summary_type", "summary_model", "keyterms_prompt", "prompt",
)


def transcript_facts(transcript_id: str, key: str) -> dict:
    """The API's own record of one transcript: real model, status, and the config it ran with."""
    t = api_get(f"/v2/transcript/{transcript_id}", key)
    facts = {k: t.get(k) for k in SUMMARY_FIELDS if k in t}
    facts["text"] = t.get("text") or ""
    facts["utterance_speakers"] = sorted({u["speaker"] for u in (t.get("utterances") or [])})
    facts["used_newest_model"] = t.get("speech_model_used") == NEWEST_ASYNC_MODEL
    return facts


def run_transcripts(since, key: str) -> list[dict]:
    """Full facts for every transcript a run created."""
    return [transcript_facts(t["id"], key) for t in transcripts_since(since, key)]


# ---------- Output keywords ----------

def load_expected(path: pathlib.Path = ROOT / "fixtures" / "expected.txt") -> list[str]:
    return [w.strip() for w in path.read_text().splitlines() if w.strip()]


def keyword_check(text: str, expected: list[str] | None = None, min_ratio: float = 1.0) -> dict:
    """Case insensitive, whitespace tolerant match of each expected keyword in `text`."""
    expected = load_expected() if expected is None else expected
    norm = re.sub(r"\s+", " ", text.lower())
    found = [w for w in expected if re.sub(r"\s+", " ", w.lower()) in norm]
    missing = [w for w in expected if w not in found]
    ratio = len(found) / len(expected) if expected else 0.0
    return {"passed": bool(expected) and ratio >= min_ratio, "found": found, "missing": missing, "ratio": ratio}


# ---------- Static scan ----------

CODE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".htm", ".json", ".toml", ".yaml", ".yml", ".sh", ".md", ".txt", ".cfg", ".ini"}
PROSE_SUFFIXES = {".md", ".txt"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".claude", ".pytest_cache"}
SKIP_FILES = {".env", "stream.jsonl", "package-lock.json"}

# rule -> (severity, regex). "fail" findings fail the trial; "warn" findings are reported only.
RULES = {
    "lemur": ("fail", re.compile(r"/lemur/|\blemur\b|\.lemur\b|aai\.Lemur|LemurTask|lemur\.task", re.I)),
    "v2_realtime": ("fail", re.compile(r"/v2/realtime|RealtimeTranscriber|realtime\.assemblyai|aai\.RealtimeTranscriber")),
    "word_boost": ("fail", re.compile(r"\bword_boost\b|\bboost_param\b|\bwordBoost\b|\bboostParam\b")),
    "legacy_model_name": ("fail", re.compile(
        r"""speech_model\s*[=:]\s*['"](best|nano|universal|slam-1|universal-3-pro|u3-rt-pro|u3-pro)['"]"""
        r"""|SpeechModel\.(best|nano|slam_1|universal)\b"""
        r"""|['"](universal-3-pro|u3-rt-pro|u3-pro|slam-1)['"]""")),
    "pinned_old_async_model": ("warn", re.compile(r"""['"]universal-3-5-pro['"]|SpeechModel\.universal_3_5_pro""")),
    "bearer_auth": ("warn", re.compile(r"""['"]Bearer\s*['"]?\s*\+|Bearer \{|`Bearer \$\{|f['"]Bearer """)),
}
KEY_LITERAL = re.compile(r"""(api[_-]?key|authorization|ASSEMBLYAI_API_KEY)\s*[=:]\s*['"][0-9a-f]{32}['"]""", re.I)
POLL_TARGET = re.compile(r"/v2/transcript/|transcript/\$\{|transcript/\{|transcript/\"\s*\+")
SLEEP_CALL = re.compile(r"(?:time\.sleep|asyncio\.sleep|sleep)\(\s*([0-9.]+)\s*\)|setTimeout\([^,]*,\s*([0-9.]+)\s*\)")


def iter_files(folder: pathlib.Path):
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.name in SKIP_FILES or any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in CODE_SUFFIXES or p.suffix == "":
            try:
                yield p, p.read_text(errors="replace")
            except OSError:
                continue


def _poll_findings(rel: str, text: str) -> list[dict]:
    """Raw HTTP polling of /v2/transcript/<id> with no sleep, or a sleep under 1 second."""
    if not POLL_TARGET.search(text) or not re.search(r"\bwhile\b|\bfor\b|setInterval", text):
        return []
    sleeps = []
    for m in SLEEP_CALL.finditer(text):
        if m.group(1):
            sleeps.append(float(m.group(1)))
        elif m.group(2):
            sleeps.append(float(m.group(2)) / 1000)
    interval = re.search(r"setInterval\([^,]*,\s*([0-9.]+)\s*\)", text)
    if interval:
        sleeps.append(float(interval.group(1)) / 1000)
    if not sleeps:
        return [{"rule": "tight_polling", "severity": "fail", "file": rel, "line": 0, "snippet": "polls /v2/transcript with no sleep"}]
    if min(sleeps) < 1:
        return [{"rule": "tight_polling", "severity": "fail", "file": rel, "line": 0, "snippet": f"poll sleep {min(sleeps)}s is under 1s"}]
    return []


def static_scan(folder, key: str | None = None) -> list[dict]:
    folder = pathlib.Path(folder)
    findings = []
    for path, text in iter_files(folder):
        rel = str(path.relative_to(folder))
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if key and key in line:
                findings.append({"rule": "hardcoded_key", "severity": "fail", "file": rel, "line": i, "snippet": "real API key value in file"})
            elif KEY_LITERAL.search(line):
                findings.append({"rule": "hardcoded_key", "severity": "fail", "file": rel, "line": i, "snippet": "key-like literal"})
            if path.suffix.lower() in PROSE_SUFFIXES:
                continue  # docs may mention LeMUR or old models by name; only code counts
            for rule, (severity, rx) in RULES.items():
                if rx.search(line):
                    findings.append({"rule": rule, "severity": severity, "file": rel, "line": i, "snippet": line.strip()[:160]})
        if path.suffix.lower() in {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".htm"}:
            findings.extend(_poll_findings(rel, text))
    return findings


def scan_failed(findings: list[dict]) -> bool:
    return any(f["severity"] == "fail" for f in findings)


# ---------- CLI ----------

def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in {"since", "scan", "keywords"}:
        print(__doc__)
        return 2
    cmd, arg = argv[0], argv[1]
    if cmd == "since":
        facts = run_transcripts(arg, load_key())
        for f in facts:
            text = f.pop("text")
            f["keywords"] = keyword_check(text)
        print(json.dumps(facts, indent=2))
    elif cmd == "scan":
        key = None
        try:
            key = load_key()
        except (SystemExit, OSError):
            pass
        print(json.dumps(static_scan(arg, key), indent=2))
    else:
        print(json.dumps(keyword_check(pathlib.Path(arg).read_text()), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
