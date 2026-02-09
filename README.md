# RetrOS-Web

**Web browser for RetrOS that automatically stylizes websites for the selected web era.**

RetrOS-Web is a Firefox-based hybrid extension + local proxy system that brings the nostalgic aesthetics of classic web eras and Windows OS versions to modern browsing. The system leverages local AI for full-page style generation, with a human-in-the-loop approval process, offline-first operation, and flexible era customization.

---

## Table of Contents

1. [Overview](#overview)  
2. [Architecture](#architecture)  
3. [Browser & Extension](#browser--extension)  
4. [Backend / Proxy](#backend--proxy)  
5. [Era System](#era-system)  
6. [AI Styling & Feedback](#ai-styling--feedback)  
7. [Style Storage & Hybrid Cache](#style-storage--hybrid-cache)  
8. [User Workflow](#user-workflow)  
9. [Offline-First AI](#offline-first-ai)  
10. [Planned Future Enhancements](#planned-future-enhancements)

---

## Overview

Retro Web Styler brings the nostalgic aesthetics of the 1990s and early 2000s web to modern browsing. Key features include:

- Full AI-generated styles for each site, based on user-selected era.
- Human-in-the-loop approval system for safety.
- Hybrid cache to detect site redesigns and reuse approved styles.
- Era-specific styling inspired by Windows 95 → Windows 7, plus classic 90s web.
- Local-first architecture for privacy and offline capability.
- Optional remote curated style packs pulled from GitHub at startup.

---

## Architecture

+----------------+ +-----------------+ +----------------+
| | | | | |
| Firefox |<----->| Local Proxy |<----->| AI Styling |
| Extension | | Python Backend | | Engine |
| (JS / WebExt) | | | | (Python Local) |
+----------------+ +-----------------+ +----------------+
| |
v v
Local Styles Cache Remote Curated Packs
(~/.retroweb/styles/) (GitHub)

---

## Browser & Extension

- **Browser:** Firefox Desktop / ESR
- **Extension:** JavaScript WebExtension
- **Responsibilities:**
  - Inject AI-generated CSS into visited pages.
  - Trigger approval popup on first visit for unapproved styles.
  - Manage user era selection (global only).
  - Maintain hybrid cache reference for site styles.
  - Pull curated style packs from GitHub on startup.

---

## Backend / Proxy

- **Architecture:** Local proxy + extension hybrid
- **Language:** Python (initial) → Go (future optimization)
- **Responsibilities:**
  - Fetch pages for style analysis.
  - Extract DOM and layout structure.
  - Run local AI for style generation.
  - Provide deterministic CSS output to the extension.
  - Ensure hybrid cache and fallback logic operate correctly.

---

## Era System

- **User Era Selection:** Global only, selected once per user/distro installation.
- **Supported Eras:**
  - Classic 90s web (1994–1997)
  - Windows 95
  - Windows 98
  - Windows ME
  - Windows 2000
  - Windows XP
  - Windows Vista
  - Windows 7
- **Accuracy Model:** Hybrid
  - Strict visual cues (colors, fonts, borders, UI metaphors)
  - Flexible technical layout constraints to maintain usability
  - Users can regenerate AI styles if output is unsatisfactory.

---

## AI Styling & Feedback

- **Full AI Generation**:
  - AI reads the page DOM and generates a full CSS style for the selected era.
  - Styles are only applied after user approval.
- **Approval Workflow**:
  - Popup banner / toolbar button triggered on first visit.
  - Options:
    - ✅ Approve style
    - ❌ Reject / regenerate
    - ✏️ Feedback (preset + optional free-text)
- **Hybrid Feedback System**:
  - Preset buttons: "Too modern", "Too simple", "Simplify layout", "Make it more usable"
  - Optional free-text input for nuanced guidance

---

## Style Storage & Hybrid Cache

- **Storage Location:** Local filesystem (`~/.retroweb/styles/`)  
- **Remote Curated Packs:** Pulled from GitHub on startup for each era  
- **Hybrid Cache Strategy:**
  1. Layout fingerprint + era
  2. Domain + page type + era
  3. Domain + era
- **Behavior:**  
  - If a style exists in the cache for a given site + era, the AI is skipped.
  - Only unapproved or missing styles are regenerated.

---

## User Workflow

1. **Install & Select Era**
   - Global era chosen during distro/extension setup.
2. **Visit Site**
   - Proxy fetches page, hybrid cache checked.
3. **Style Generation**
   - AI generates style if missing.
4. **Approval Popup**
   - User approves, rejects, or provides feedback.
5. **Hybrid Cache Update**
   - Approved style stored locally.
6. **Future Visits**
   - Cached style applied automatically.

---

## Offline-First AI

- AI runs **entirely locally** in the Python backend.
- No internet connection required for style generation.
- Cloud access optional only for future enhancements.

---

## Planned Future Enhancements

- Go implementation of proxy for higher performance.
- Optional per-site era overrides for advanced users.
- Expand curated style packs with user contributions.
- Improve AI model to better emulate era-specific layout patterns.
- Integration with Linux distro settings for “system-wide retro web mode”.

---

## License & Contributions

- Open-source, MIT License recommended.
- Contributions welcome for:
  - New era templates
  - Feedback improvements
  - Performance enhancements

---

