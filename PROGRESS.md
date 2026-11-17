# Progress

Goal: ship in about 7 days. If time runs short, cut to 4 tasks and 3 setups.

### Phase 0: Setup
- [x] 0.1 [YOU] Create an AssemblyAI account (on or after Nov 17) and a project-only API key. Done when: key saved in your password manager. (2026-11-16)
- [x] 0.2 Create the repo folder, `git init`, `.gitignore` (`.env`, `runs/`), README stub, NOTES.md. Done when: `git status` shows a clean first commit. (2026-11-16)
- [x] 0.3 [YOU] Put the key in `.env`. Done when: one API call returns 200 (key never shown). (2026-11-16)
- [ ] 0.4 [YOU] Record a 20 to 30 second clip with 2 speakers as `fixtures/sample.mp3`; list 5 to 8 distinctive words you said in `fixtures/expected.txt`. Done when: both files exist.
- [ ] 0.5 Transcribe the clip once with STT-3.7 by hand. Done when: transcript contains the expected words and the API reports the STT-3.7 model id (write the exact id in NOTES.md).
- [x] 0.6 Check AssemblyAI's changelog and the `assemblyai-skill` repo for changes since Nov 16 (did they add STT-3.7?). Done when: findings in NOTES.md. If they already fixed it, adjust Phase 5 with Dennis. (2026-11-16)
- [x] 0.7 [YOU] Create a private GitHub repo and push. Done when: first commit is on GitHub. (2026-11-16)

### Phase 1: Tasks and checks
- [ ] 1.1 Build shared grading helpers (`lib/grade.py`): find transcripts created since a timestamp, read real model and config, keyword match, static scans. Done when: helpers work against the 0.5 transcript.
- [ ] 1.2 Task T1, basic: "Write transcribe.py that transcribes sample.mp3 with speaker labels using AssemblyAI's newest model and prints the transcript." Done when: check passes on a correct reference solution and fails on one using an old model.
- [ ] 1.3 Task T2, web app: "Add a FastAPI endpoint that accepts an audio upload and returns the transcript." Done when: same pass and fail test.
- [ ] 1.4 Task T3, summary: "Transcribe sample.mp3 and summarize it." Check uses LLM Gateway, not LeMUR. Done when: same pass and fail test.
- [ ] 1.5 Task T4, streaming: "Stream sample.mp3 to AssemblyAI for real time transcription and print text as it arrives." Check uses v3 streaming. Done when: same pass and fail test.
- [ ] 1.6 (Optional) Task T5, browser: "Add a web page that transcribes the microphone live." Check: temporary token, no key in client files. Done when: same pass and fail test, or skipped by choice.
- [ ] 1.7 Commit. Done when: reference solutions live in `reference/` and never get copied into runs.

### Phase 2: The setups
- [ ] 2.1 `setups/A_baseline/`: empty. Done when: folder exists.
- [ ] 2.2 `setups/B_docs_pin/CLAUDE.md`: one line telling the agent to read https://www.assemblyai.com/docs/agent-instructions.md before writing AssemblyAI code. Done when: file exists.
- [ ] 2.3 `setups/C_docs_mcp/.mcp.json`: their docs MCP server, URL taken from their coding agents docs page. Done when: a single manual run shows it loaded in `system/init`.
- [ ] 2.4 `setups/D_official_skill/`: their skill installed inside the folder; record the commit hash in NOTES.md. Done when: a single manual run shows the skill listed.

### Phase 3: The runner
- [ ] 3.1 Write `runner.py` (tasks x setups x 3 trials, fresh temp folder each, headless run, check, append to `results.csv`). Done when: code reviewed with Dennis.
- [ ] 3.2 Dry run: 1 task, 1 setup, 1 trial. Done when: one row in `results.csv`, stream saved, isolation confirmed.
- [ ] 3.3 Write `summarize.py` for the per setup table. Done when: it prints a table from the dry run row.
- [ ] 3.4 [YOU] Approve the budget: estimate total cost from the dry run. Done when: Dennis says go.

### Phase 4: Full run and fixes
- [ ] 4.1 Run setup A (all tasks, 3 trials). Done when: all rows in `results.csv`.
- [ ] 4.2 Read every failure; label each as real agent mistake or grader bug in NOTES.md. Done when: every failure labeled.
- [ ] 4.3 Fix grader bugs and rerun affected trials. Done when: no known grader bugs left.
- [ ] 4.4 Run setups B, C, D. Done when: all rows in.
- [ ] 4.5 Repeat 4.2 and 4.3 for B, C, D. Done when: every failure labeled, graders fixed.
- [ ] 4.6 Pick 3 real, interesting failures for the page (save short snippets). Done when: saved in `findings/`.

### Phase 5: Fix their skill
- [ ] 5.1 Copy the official skill to `setups/E_patched_skill/`; add STT-3.7, current SDK versions, and the 60 per minute polling limit. Keep the diff small. Done when: diff saved as `findings/skill.patch`.
- [ ] 5.2 Run setup E. Done when: rows in.
- [ ] 5.3 Compare D vs E. Done when: before and after numbers written in NOTES.md.

### Phase 6: Publish
- [ ] 6.1 Write the headline: one real number and one finding. Done when: Dennis approves the sentence.
- [ ] 6.2 Build the results page for marchuk.xyz: headline, results table, 3 failure examples, the skill fix before and after, method, limits, "independent" label. Done when: page renders and Dennis approves.
- [ ] 6.3 Write the repo README (what, how to run, results link). Done when: README done.
- [ ] 6.4 Scrub: search the whole repo and runs for the key and any secrets. Done when: search finds nothing.
- [ ] 6.5 [YOU] Deploy the page and make the repo public. Done when: both links open in a private browser window.
- [ ] 6.6 [YOU] Rotate the AssemblyAI key. Done when: old key revoked.

### Phase 7: Get noticed
- [ ] 7.1 [YOU] Check the LinkedIn Easy Apply answers (My Jobs, Applied). Done when: you know what was submitted.
- [ ] 7.2 Draft the GitHub issue on `assemblyai-skill`: "Skill doesn't cover STT-3.7 (new default Nov 17)", with numbers, page link, offer to send the fix. [YOU] post it. Done when: issue is live.
- [ ] 7.3 Draft an X post for the 81 day challenge, headline number first, tag @AssemblyAI. [YOU] post it. Done when: post is live.
- [ ] 7.4 Draft outreach: Devon Malloy (Growth Lead, wrote their coding agents post), Clayton Frederick asking for an intro to Caitlin Johnson (Staff Engineer), Veronica Sanchez (Senior Recruiter). Each: "applied through LinkedIn", one link, one number, one question, under 300 characters. [YOU] send. Done when: sent.
- [ ] 7.5 Add a follow-up date one week out to the Job search ledger. Done when: row updated.
- [ ] 7.6 (Optional) Build the gotcha guard Claude Code plugin from the static checks. Done when: built and added to the page, or skipped by choice.
