# RetrOS Copilot Skill

Purpose: A concise instruction set for Copilot-style agents to follow when starting work in this workspace.

Load order for agents
1. Read `COPILOT_WORKFLOW.md` in repository root.
2. Read `BACKLOG.md` to identify the highest-priority User Story (US).
3. Follow the `Step-by-step` section in `COPILOT_WORKFLOW.md`.
4. Create exactly one completion doc `US-<n>-COMPLETION.md` after finishing the US.
5. Update `BACKLOG.md` with status and a link to the completion doc.

Quick reminder for the agent
- Always make minimal, focused changes.
- Run `npm run build` after code changes and include the build output in the completion document.
- If blocked, update `BACKLOG.md` with a short note and create an issue if necessary.

Loader usage
- The repository includes `scripts/load_copilot_skill.ps1` which prints this file to console and copies the contents to clipboard for quick paste into assistant prompts.

Limitations
- This file is a workspace convenience. It cannot force third-party Copilot product features to "auto-load" content. Use the provided loader script or open this file in your editor.

--
Generated: February 8, 2026
