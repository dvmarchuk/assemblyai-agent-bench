# Notes

Working notes for the bench: model ids, findings, failure labels, decisions.

## Account

- AssemblyAI account created 2026-11-16, about 11 pm ET (already 2026-11-17 in UTC). STT-3.7 is the default for accounts created on or after 2026-11-17, so confirm the default model in 0.5 instead of assuming it.

## 0.6 Changelog and skill check (2026-11-16, 11 pm ET)

- Model id is `assemblyai-stt-3-7` (pre-recorded). The family also has `AssemblyAI-STT-3.7-Realtime` and `AssemblyAI-STT-3.7-Realtime-Agent` (launch blog dated Nov 17, 2026). Streaming ids still to confirm.
- Docs (Speech model versions and deprecations): accounts created on or after Nov 17, 2026 that omit `speech_models` get `assemblyai-stt-3-7`. Existing accounts on `universal-3-5-pro` / `universal-3-pro` switch on Dec 8, 2026. `universal-3-5-pro` and `universal-3-pro` are marked Deprecated as of Nov 17 (retirement date TBA).
- Migration guide: fallback behavior changed. With `speech_models: ["assemblyai-stt-3-7"]`, fallback to another model now depends on how language is set (with `language_detection: true` it never falls back). Worth a check in the grader.
- `assemblyai-skill` (github.com/AssemblyAI/assemblyai-skill) latest commit `f584ec5` (Nov 4, 2026): zero mentions of STT-3.7. It still says `universal-3-5-pro` is the async default and recommended model. Gap confirmed, Phase 5 stands.
- `assemblyai.com/llms/models.md` (last updated Nov 10) also has no STT-3.7 yet.
- Risk: our account was created Nov 16 ET (already Nov 17 UTC). If AssemblyAI counts it as pre Nov 17, omitting `speech_models` gives `universal-3-5-pro` until Dec 8. 0.5 settles this. Either way, grade on the model that actually ran, and the T1 prompt asks for the newest model explicitly.

Sources:
- https://www.assemblyai.com/docs/getting-started/model-versions-and-deprecations
- https://www.assemblyai.com/docs/pre-recorded-audio/assemblyai-stt-3-7-migration-guide
- https://www.assemblyai.com/blog/introducing-assemblyai-stt-3-7
