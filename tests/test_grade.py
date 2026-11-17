"""Offline tests for lib/grade.py: python3 -m unittest discover -s tests"""
import pathlib
import sys
import tempfile
import textwrap
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import grade  # noqa: E402

FAKE_KEY = "0123456789abcdef0123456789abcdef"

GOOD_PY = textwrap.dedent('''
    import os, time, requests
    import assemblyai as aai
    aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
    config = aai.TranscriptionConfig(speech_models=["assemblyai-stt-3-7"], speaker_labels=True)
    t = aai.Transcriber(config=config).transcribe("sample.mp3")
    # raw polling example
    while True:
        r = requests.get(f"https://api.assemblyai.com/v2/transcript/{tid}", headers=h).json()
        if r["status"] in ("completed", "error"):
            break
        time.sleep(3)
    gw = "https://llm-gateway.assemblyai.com/v1/chat/completions"
    ws = "wss://streaming.assemblyai.com/v3/ws"
''')

BAD_PY = textwrap.dedent(f'''
    import requests
    API_KEY = "{FAKE_KEY}"
    r = transcript.lemur.task("summarize")
    t = aai.RealtimeTranscriber(sample_rate=16000)
    cfg = aai.TranscriptionConfig(word_boost=["IFTA"], speech_model="best")
    while True:
        r = requests.get("https://api.assemblyai.com/v2/transcript/" + tid)
        if r.json()["status"] == "completed":
            break
''')


class StaticScan(unittest.TestCase):
    def scan(self, files, key=None):
        with tempfile.TemporaryDirectory() as d:
            for name, body in files.items():
                p = pathlib.Path(d) / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body)
            return grade.static_scan(d, key)

    def test_good_code_is_clean(self):
        findings = self.scan({"transcribe.py": GOOD_PY})
        self.assertEqual(findings, [])

    def test_bad_code_hits_every_rule(self):
        rules = {f["rule"] for f in self.scan({"bad.py": BAD_PY})}
        for rule in ("hardcoded_key", "lemur", "v2_realtime", "word_boost", "legacy_model_name", "tight_polling"):
            self.assertIn(rule, rules)

    def test_real_key_value_found_anywhere(self):
        findings = self.scan({"app.js": f"const k = process.env.X || '{FAKE_KEY}x';"}, key=FAKE_KEY)
        self.assertIn("hardcoded_key", {f["rule"] for f in findings})

    def test_env_file_ignored(self):
        self.assertEqual(self.scan({".env": f"ASSEMBLYAI_API_KEY={FAKE_KEY}"}, key=FAKE_KEY), [])

    def test_docs_may_mention_lemur(self):
        self.assertEqual(self.scan({"README.md": "Uses LLM Gateway instead of LeMUR."}), [])

    def test_fast_js_polling(self):
        js = "while (true) { const r = await fetch(`https://api.assemblyai.com/v2/transcript/${id}`); await new Promise(r => setTimeout(r, 200)); }"
        self.assertIn("tight_polling", {f["rule"] for f in self.scan({"poll.js": js})})

    def test_old_async_model_is_warning_only(self):
        findings = self.scan({"t.py": 'cfg = {"speech_models": ["universal-3-5-pro"]}'})
        self.assertEqual([(f["rule"], f["severity"]) for f in findings], [("pinned_old_async_model", "warn")])
        self.assertFalse(grade.scan_failed(findings))


class Keywords(unittest.TestCase):
    def test_case_and_whitespace(self):
        r = grade.keyword_check("Your  IFTA tax and the eld, fuel\ncard here", ["IFTA", "ELD", "fuel card"])
        self.assertTrue(r["passed"])

    def test_missing(self):
        r = grade.keyword_check("only IFTA here", ["IFTA", "Gemini"])
        self.assertFalse(r["passed"])
        self.assertEqual(r["missing"], ["Gemini"])


if __name__ == "__main__":
    unittest.main()
