# MEMORY.md — AI Job Finder Core Intelligence & Repository Memory

> Pointer & Fast Reference to [AGENT_MEMORY.md](file:///d:/Ai%20job%20finder/AGENT_MEMORY.md) (the canonical living project memory).

## Key Architecture & Verified Tech Stack
- **Autonomous Browser Engine**: Camoufox Gecko (`src/stealth_browser.py`) with per-worker PID profile isolation (`data/profiles/worker_{pid}`) + `src/browser_agent.py` async multi-step form filler.
- **Computer-Use Fallback**: `src/desktop_agent.py` (`pyautogui` + `mss` coordinate-bounded vision agent).
- **Hybrid Matching Engine**: `sentence-transformers` (`BAAI/bge-small-en-v1.5`, $d=384$) + stdlib SQLite FTS5 BM25 search (`src/matcher.py`) + ChromaDB with WAL mode.
- **ATS Resume Compiler**: In-process `typst.compile()` in `src/cv_builder.py` (zero external `typst.exe` PATH dependency).
- **Agent Orchestrator**: `src/career_agent.py` with Google AX-style SQLite task state checkpointing (`agent_checkpoints`).

## Adversarial Red-Team Repository Audits (Audited 2026-09-24)
| Repository / Tool | Claimed Capability | Verification Reality | Decision |
|---|---|---|---|
| `doofzoff/SIMURG` | Autonomous ATS stream agent & real-time scraper | Stream AUROC = 0.55 (coin toss); single test stream; thin HTTP wrapper over `tinyfish.ai` (hardcoded key, 30 req/min). | **BUSTED & REJECTED** |
| `kajisho5/ffmpeg-skill` | LLM agent skill for multimedia video generation | Pure markdown prompt guide; hard-requires system `ffmpeg` (5.0+) with `libass`, `drawtext`, `loudnorm` on Windows PATH. | **REJECTED AS BUNDLE** (Retain minimal stdlib subprocess) |
| `supertone-oss-archive/supertonic` | Ultra-fast on-device neural TTS | Archived & abandoned by HYBE/Supertone; OpenRAIL-M license restrictions; robotic prosody; 1.2GB weight overhead. | **BUSTED & REJECTED** |
| `h4ckf0r0day/obscura` | Stealth browser for bot-bypassing job application | Custom Rust DOM/JS engine (not Chromium/Gecko); active DOM divergence issues (#1141, #1142) break Workday/Greenhouse SPAs. | **REJECTED** (Retain Camoufox C++ Gecko) |
| `@kalypsodesigns` | AI job application & automated career workflow | Instagram UI influencer selling Figma/Canva templates; zero software or scraping code exists. | **BUSTED & REJECTED** |
| `google/ax` | Autonomous agent execution substrate | Experimental `v1alpha1` Kubernetes-native cluster orchestrator in Go requiring Agent Substrate and container registries. | **ADOPTED PATTERN ONLY** (SQLite task state checkpointing in `career_agent.py`) |

## Execution Policy: Intervention-by-Exception
- **Autopilot (`mode="full_auto"`)**: Handles 100% of routine workflows without human prompts (discovery, ghost job audit, System-1 matching, Typst resume compilation, stealth navigation, form filling, and submission).
- **Human Escalation Only**: The agent halts and alerts the human **strictly** upon hard external blockers:
  1. `CAPTCHA_DETECTED`: Cloudflare Turnstile or enterprise visual/behavioral CAPTCHAs.
  2. `LOGIN_REQUIRED`: Account creation, password setups, or email 2FA/OTP verification.
- **UI Exception Center**: When an exception occurs, [`ApexWarfareCenter.tsx`](file:///d:/Ai%20job%20finder/frontend/src/components/ApexWarfareCenter.tsx) highlights the target requisition with an amber action badge and provides a 1-click `Open Portal →` link.

For the complete audit logs, session history, and architectural invariants, see [AGENT_MEMORY.md](file:///d:/Ai%20job%20finder/AGENT_MEMORY.md).
