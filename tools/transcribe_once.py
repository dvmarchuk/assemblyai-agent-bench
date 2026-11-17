"""Transcribe one local file with AssemblyAI and print the model that actually ran.

Usage: python3 tools/transcribe_once.py fixtures/sample.mp3 [speech_model ...]
With no speech models given, the request omits speech_models so the account default runs.
Writes the full JSON response to runs/manual/<transcript_id>.json.
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://api.assemblyai.com"


def load_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("ASSEMBLYAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("ASSEMBLYAI_API_KEY missing from .env")


def call(method, path, key, body=None, raw=None):
    headers = {"authorization": key}
    data = None
    if raw is not None:
        data = raw
        headers["content-type"] = "application/octet-stream"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["content-type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def main():
    audio = pathlib.Path(sys.argv[1])
    models = sys.argv[2:]
    key = load_key()
    upload_url = call("POST", "/v2/upload", key, raw=audio.read_bytes())["upload_url"]
    body = {"audio_url": upload_url, "speaker_labels": True}
    if models:
        body["speech_models"] = models
    t = call("POST", "/v2/transcript", key, body=body)
    while t["status"] not in ("completed", "error"):
        time.sleep(3)  # about 20 polls per minute, under the 60 per minute limit
        t = call("GET", f"/v2/transcript/{t['id']}", key)
    out = ROOT / "runs" / "manual" / f"{t['id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(t, indent=2))
    print("id:", t["id"])
    print("status:", t["status"], t.get("error") or "")
    print("requested speech_models:", models or "(omitted, account default)")
    for k in ("speech_model_used", "speech_model", "speech_models", "language_code", "audio_duration"):
        print(f"{k}:", t.get(k))
    for u in t.get("utterances") or []:
        print(f"[{u['start'] / 1000:5.1f}s] {u['speaker']}: {u['text']}")


if __name__ == "__main__":
    main()
