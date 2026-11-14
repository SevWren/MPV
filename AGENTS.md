## Agent skills

### Issue tracker

Issues and specs live as GitHub issues on `SevWren/MPV`. Use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five default roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. Glossary at `GLOSSARY.md`, decisions in `docs/adr/`. See `docs/agents/domain.md`.

## Working in this repo

This is a personal mpv config directory: `mpv.conf`, `input.conf`, `scripts/`, and `script-opts/`. There is no build, package manager, or test runner. Check a change by loading it in mpv.

The repository is the source tree for the mpv scripts. During development, mpv loads the working copies from `%APPDATA%\mpv\scripts`, `%APPDATA%\mpv\script-opts`, and `%APPDATA%\mpv\script-modules`. Keep repository edits in the corresponding `scripts/`, `script-opts/`, and `script-modules/` directories; use the `%APPDATA%\mpv\...` paths when loading or manually testing the working copies.

Edit the live tree at the repo root. Treat `MPV Script Back/` as an archive of older copies.

When a script header and its `read_options` call disagree, follow the call. `playlist-view.lua` and `contact-sheet.lua` document `playlist_view.conf` and `contact_sheet.conf`, then call `read_options` with `mp.get_script_name()`, so mpv reads `script-opts/playlist-view.conf` and `script-opts/contact-sheet.conf`. `gallery-thumbgen.lua` passes `"gallery_worker"`, and `script-opts/gallery_worker.conf` matches. `webm.lua` passes no identifier, so it reads `script-opts/webm.conf`.

`playlist-view.lua` and `contact-sheet.lua` prepend `~~/script-modules/?.lua` and `require 'gallery'`. Their headers name `gallery-module.lua`. The copy in this repo is `MPV Script Back/script-modules/gallery.lua`. A checkout does not satisfy that require until `gallery.lua` is on mpv's `script-modules` path.

`screenshot-directory` in `mpv.conf` and `output_directory` in `script-opts/webm.conf` are absolute paths on this machine (`D:\ProgramData\asus`). Leave them unless the task is to change where files are written.

When `README.md` and a live file disagree, follow the live file. `input.conf` records that `collab_notebook_sub.lua` overrides bindings and is broken. That script is not in `scripts/`. `script-opts/collab_notebook_sub.conf` remains.

`autoload.lua` and `ytdl_hook.lua` are vendored upstream mpv scripts. Change them only for a local behavior this config needs.
