# Copilot Workflow

Purpose: Provide a concise, repeatable workflow for Copilot to follow when implementing user stories from the backlog.

Principles
- Always start by reviewing `BACKLOG.md` and confirming the highest-priority User Story (US).
- For each US, produce exactly one completion summary file named `US-<n>-COMPLETION.md` in the repository root.
- Test the feature locally (build + manual browser verification) before marking the US done.
- Update `BACKLOG.md` with status and link to the completion doc when finished.

Step-by-step

1) Review the backlog
- Open `BACKLOG.md` and find the current highest-priority US.
- Identify acceptance criteria, dependencies, and files mentioned.

2) Implement the US tasks
- Follow the backlog's steps for the US. Make minimal, atomic changes.
- Keep commits focused (one logical change per commit).
- If you need to create files, follow the repo structure (src/, data/, dist/ etc.).

3) Create one summary doc per US
- Create a single file named `US-<n>-COMPLETION.md` (example: `US-1.2-COMPLETION.md`).
- Content template (minimum):
  - Title and US identifier
  - Status (Complete / Partial / Blocked)
  - What was implemented (brief)
  - Acceptance criteria checklist (mark each as ✅/❌)
  - Files changed (paths)
  - Tests performed and results (build output, browser verification)
  - Known limitations and next steps
  - Build status / webpack output (copy the last build summary)

4) Test the feature and build
- Run the build:

```powershell
npm run build
```

- Load the extension in Firefox (Developer Edition recommended):
  - Go to `about:debugging#/runtime/this-firefox`
  - Click "Load Temporary Add-on" and select `dist/manifest.json` or reload the existing temporary extension
- Manual verification checklist:
  - Popup opens on icon click
  - UI elements appear and respond (Approve/Reject/Feedback/Regenerate)
  - Keyboard navigation: Tab, Enter, Escape
  - No console errors in the extension or page (open Browser Console)
  - Verify storage changes via `about:debugging` or `browser.storage.local.get()` where appropriate
- Add test notes and any console output to the completion doc.

5) Update and check the backlog
- Edit `BACKLOG.md` to mark the US as `Done` or add status notes. Add a link to the `US-<n>-COMPLETION.md` file.
- If follow-ups are needed, add new backlog items with clear titles and descriptions.

6) Tell the user what they can test
- Explain what changes were made and instruct the user how to test them out.

Naming & Location Conventions
- Completion docs: `US-<n>-COMPLETION.md` in repo root.
- Branches for changes: `us/<n>-short-description` (example: `us/1-2-popup-ui`)
- Commit messages: `US-<n>: short description` (example: `US-1.2: add approval workflow to popup`)

Communication & Logs
- If blocked, add a short note in `BACKLOG.md` next to the US and create an issue if needed.
- Keep console logs brief and user-friendly; avoid leaking sensitive data.

Example completion doc checklist (to copy into each `US-<n>-COMPLETION.md`):

- [ ] Acceptance Criteria 1
- [ ] Acceptance Criteria 2
- [ ] Build successful
- [ ] Manual browser tests passed
- [ ] Backlog updated with link to this doc

Permissions & Safety
- Do not check in secrets, keys, or large binary blobs (icons can be placeholders; optimize before release).
- If a task requires external services (proxy, API keys), create a stub and add a TODO note in the completion doc.

If you want, I can now:
- Run the first step (review `BACKLOG.md`) and mark the todo as in-progress, or
- Immediately start work on the current highest-priority US listed in `BACKLOG.md`.

Auto-load helper

- A workspace skill file was added at `.copilot/WORKFLOW_SKILL.md`. Use the loader script to print and copy it:

```powershell
.\scripts\load_copilot_skill.ps1
```

Notes on "auto-load": this file provides a standardized prompt for assistants working on this repo. It cannot force GitHub Copilot (product) to automatically import a custom skill; use the loader or open the file in your editor when starting work.
