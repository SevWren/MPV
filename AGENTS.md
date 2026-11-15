# AGENTS.md — MPV Configuration & webm.lua Scripts

This repo contains mpv configuration, user scripts, and an AI-assisted agentic setup for maintaining `scripts/webm.lua`.

## Active Development

**Primary file under development:** `scripts/webm.lua`
- 2856 lines of MoonScript-compiled Lua
- 10 MoonScript-generated classes (`_class_0`/`_base_0`/`_parent_0` scaffolding throughout)
- 7 output formats: RawVideo, WebmVP8, WebmVP9, MP4, MP4NVENC, MP3, GIF
- 24 configurable options (see `script-opts/webm.conf`)
- Developer environment: **Windows 10**, mpv build `mpv-x86_64-20261114-git-649001d4e2` (LuaJIT 2.1, clang)

**Confirmed bugs (fix priority order):**
1. FIND-003 (medium): `options.output_format` default `"mp4 (h264/AAC)"` doesn't match registry key `"mp4"` — crashes first encode for new users (L17)
2. FIND-001 (high): undefined `bitrate` at L1779-1780 — crashes strict filesize mode
3. FIND-006 (high/security): IPC handler has no validation at L68-74 — any same-user script can inject options
4. FIND-007 (medium): temp file leak when `run_detached=true` (default on Windows)
See full register: `re-workspace/deliverables/13-defect-and-quality-register.md`

## Skills

Available in `.agents/skills/`:

| Skill | Use when |
|---|---|
| `ask-matt` | Routing — determine which skill fits the situation |
| `diagnosing-bugs` | A bug resists a first glance; build a tight feedback loop first |
| `codebase-design` | Designing or deepening a module's interface |
| `domain-modeling` | Updating `GLOSSARY.md`, recording ADRs, sharpening terminology |
| `improve-codebase-architecture` | Surfacing deepening opportunities; runs HTML report |
| `implement` | Implementing a single ticket or small feature |
| `tdd` | Building a behavior test-first |
| `code-review` | Reviewing a diff against standards and spec |
| `research` | Delegating reading legwork to a background agent |

## Agent Roles

Role definitions in `.claude/agents/`:

| Role | Purpose |
|---|---|
| `re-team-lead` | Team lead for a swarm team (opus) |
| `re-segment-analyst` | Blind single-lens source segment analyst (sonnet) |
| `re-reconciler` | Reconciles A/B/C analyst outputs (sonnet) |
| `re-skeptic` | Adversarial challenger of reconciled models (sonnet) |
| `re-micro-analyst` | Per-function/option micro-analyst (haiku) |
| `re-toolsmith` | Builds deterministic analysis tools (sonnet) |
| `re-test-engineer` | Harness and test builder (sonnet) |
| `re-reconstructor` | Clean Lua reconstruction author (sonnet) |
| `re-security-analyst` | Blue-team security analyst (sonnet) |
| `re-red-team` | Red-team falsifier (sonnet) |
| `re-doc-author` | Deliverable document author (sonnet) |
| `re-doc-editor` | Document editor in P3 chain (sonnet) |
| `re-verifier` | Blind claim verifier (haiku) |
| `re-adjudicator` | Dispute adjudicator, K≥3 Delphi panels (opus) |
| `re-auditor` | Independent final auditor, fresh context (opus) |

## Analysis Package

Complete reverse-engineering package: `re-workspace/deliverables/`
- Swarm operations report: `22-swarm-operations-report.md` (Mode C degraded, 1.8% budget used)
- Architecture review HTML: `architecture-review.html`
- Bug diagnosis: `audit/bug-diagnosis/DIAGNOSIS-SUMMARY.md`
- Windows developer environment: `14b-windows-developer-environment.md`

## Working in this repo

This is a personal mpv config directory: `mpv.conf`, `input.conf`, `scripts/`, and `script-opts/`. There is no build, package manager, or test runner. Check a change by loading it in mpv.

The repository is the source tree for the mpv scripts. During development, mpv loads the working copies from `%APPDATA%\mpv\scripts`, `%APPDATA%\mpv\script-opts`, and `%APPDATA%\mpv\script-modules`. Keep repository edits in the corresponding `scripts/`, `script-opts/`, and `script-modules/` directories; use the `%APPDATA%\mpv\...` paths when loading or manually testing the working copies.

Edit the live tree at the repo root. Treat `MPV Script Back/` as an archive of older copies.

When a script header and its `read_options` call disagree, follow the call. `playlist-view.lua` and `contact-sheet.lua` document `playlist_view.conf` and `contact_sheet.conf`, then call `read_options` with `mp.get_script_name()`, so mpv reads `script-opts/playlist-view.conf` and `script-opts/contact-sheet.conf`. `gallery-thumbgen.lua` passes `"gallery_worker"`, and `script-opts/gallery_worker.conf` matches. `webm.lua` passes no identifier, so it reads `script-opts/webm.conf`.

`playlist-view.lua` and `contact-sheet.lua` prepend `~~/script-modules/?.lua` and `require 'gallery'`. Their headers name `gallery-module.lua`. The copy in this repo is `MPV Script Back/script-modules/gallery.lua`. A checkout does not satisfy that require until `gallery.lua` is on mpv's `script-modules` path.

`screenshot-directory` in `mpv.conf` and `output_directory` in `script-opts/webm.conf` are absolute paths on this machine (`D:\ProgramData\asus`). Leave them unless the task is to change where files are written.

When `README.md` and a live file disagree, follow the live file. `input.conf` records that `collab_notebook_sub.lua` overrides bindings and is broken. That script is not in `scripts/`. `script-opts/collab_notebook_sub.conf` remains.

`autoload.lua` and `ytdl_hook.lua` are vendored upstream mpv scripts. Change them only for a local behavior this config needs.

## Issue tracker

Issues and specs live as GitHub issues on `SevWren/MPV`. Use the `gh` CLI. See `docs/agents/issue-tracker.md`.

## Triage labels

Five default roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

## Domain docs

Single-context. Glossary at `GLOSSARY.md`, decisions in `docs/adr/`. See `docs/agents/domain.md`.

## Vocabulary

See `GLOSSARY.md` for domain terms. See `docs/adr/` for architectural decisions.
See `.agents/skills/codebase-design/SKILL.md` for architecture vocabulary (module, interface, depth, seam, adapter, leverage, locality).

## Key Context for Agents

- The script is **MoonScript-compiled** — `_class_0`/`_base_0` scaffolding is generated, not hand-written; do not "fix" it
- Primary runtime: **LuaJIT 2.1** (mpv's bundled Lua on Windows); `math.ldexp`, `bit.*` available
- Two process execution paths: `mp.utils.subprocess` (foreground/argv) and `io.popen(shell_escape(...))` (background/shell) — both are intentional
- IPC trust boundary: `mpv-webm-set-options` message is a deliberate extension point (see ADR-0005), not a bug to remove
- The `_class_0` inheritance pattern: `Child._base_0 = {}; Child._class_0 = {}; setmetatable(Child._base_0, {__index = Parent._base_0})`
