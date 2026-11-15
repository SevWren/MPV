# FIND-006 Security Diagnosis: IPC Handler `test_set_options` Has No Input Validation

**ID**: FIND-006
**Severity**: High (Security)
**Type**: Security — Insufficient Input Validation / CWE-20
**Location**: `scripts/webm.lua` L68-74
**Status**: Confirmed — bug present in `canonical/webm.lf.lua`

---

## Phase 1: Feedback Loop

**Script**: `re-workspace/harness/tests/test_find_006.py`

The loop:
1. Extracts the `test_set_options` function body
2. Checks for absence of: allowlist, type() calls, rejection logging, range checks
3. Checks for presence of: bare pairs() merge (all keys accepted unconditionally)
4. Reports high-risk injectable options

**Baseline run result**: RED (exit 1) — 5/5 validation indicators absent, bare merge confirmed.

---

## Phase 2: Reproduce and Minimise

**Handler code** (L68-74):
```lua
test_set_options = function(new_options_json)
  local new_options = utils.parse_json(new_options_json)
  for k, v in pairs(new_options) do
    options[k] = v
  end
end
mp.register_script_message("mpv-webm-set-options", test_set_options)
```

**Minimal attack** (another Lua script loaded in the same mpv session):
```lua
mp.commandv("script-message", "mpv-webm-set-options",
  '{"additional_flags": "--vf lavfi=[drawtext=text=INJECTED] -f null -"}')
```

This sets `options.additional_flags` to an attacker-controlled string, which is later split
by `gmatch` at L1790 and appended verbatim to the ffmpeg command line.

---

## Phase 3: Hypotheses

Ranked by likelihood:

1. **Function is a debug/testing helper never hardened for production** (probability: 0.80)
   The function name `test_set_options` strongly suggests it was added for development testing
   and was never intended to remain enabled in production builds. The `mp.register_script_message`
   call makes it permanently active in all mpv sessions.

2. **Author assumed only trusted scripts run in mpv** (probability: 0.15)
   mpv has no script sandboxing. Any `.lua` file in the scripts directory, or any script
   loaded by a third-party config, can send arbitrary script-messages.

3. **Intentional feature with implicit trust model** (probability: 0.05)
   Unlikely — a legitimate "set options" API would use a structured, typed interface.

---

## Phase 4: Instrument — STRIDE Threat Modeling

**Threat model target**: Windows 10, mpv-x86_64-20261114, standard user account.

### Who can send script-messages?

| Attacker Surface | Mechanism | Requires |
|---|---|---|
| Co-loaded Lua script | `mp.commandv("script-message", ...)` | Script in `scripts/` dir |
| mpv IPC socket client | JSON IPC `{ "command": ["script-message", ...] }` | `--input-ipc-server` active |
| External process via IPC | Named pipe on Windows (`\\.\pipe\mpv-...`) | Access to named pipe |
| Malicious media file | mpv script filter or hook exploitation | Unusual but possible |

On Windows 10, the IPC server uses a named pipe. Any process running as the same user
can connect. This includes browser-based local file attacks, downloaded scripts, and
other applications in the user session.

### STRIDE Analysis

| Threat | Category | Vector | Impact |
|---|---|---|---|
| Inject `additional_flags` | Tampering | Any script-message sender | Arbitrary ffmpeg CLI flags; `-f` to change output format; `-vf`/`-af` to add processing |
| Inject `output_directory` | Tampering + EoP | IPC or co-loaded script | Write encoded files to arbitrary filesystem paths; Windows: `C:\Users\victim\AppData\Roaming\` |
| Inject `output_template` | Tampering | Same | Overwrite files via template expansion |
| Inject `run_detached=false` | DoS | Same | Force blocking encode, freeze mpv UI |
| Inject unknown keys | Information disclosure (future) | Same | Pollutes options table; could affect future key-sensitive code paths |
| Inject `crf=-1` or extreme values | Denial of service | Same | Trigger ffmpeg errors, produce corrupt output |

### High-Impact Windows 10 Scenarios

**Scenario A — additional_flags path traversal via ffmpeg output redirection**:
```json
{"additional_flags": "-f rawvideo -pix_fmt bgr24 pipe:1 > C:\\Users\\Public\\dump.raw"}
```
On Windows, shell injection is not possible through mpv's argument array (it uses `CreateProcess`
directly), but `-f` can redirect output format. Combined with output_directory manipulation,
an attacker can write to unexpected locations.

**Scenario B — output_directory traversal**:
```json
{"output_directory": "..\\..\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"}
```
If a user encodes a file, the output goes to the Startup folder. The file extension is
determined by the format codec, so `.mp4` or `.webm` files would appear there (harmless
as executables but could cause confusion or be used in social engineering).

**Scenario C — output_directory + output_template for targeted overwrite**:
```json
{
  "output_directory": "C:\\Users\\victim\\Documents",
  "output_template": "important-document"
}
```
Encodes would silently overwrite `important-document.mp4`.

**Scenario D — Disabling twopass and corrupting quality settings**:
```json
{"twopass": false, "crf": 0, "target_filesize": 999999999}
```
Forces maximum quality / maximum file size, consuming disk space.

---

## Phase 5: Fix and Regression Test

**Regression test** (`test_find_006.py`):
```python
def check_fix_applied(handler_body):
    has_allowlist = bool(re.search(r'allowed|whitelist|valid_keys', handler_body, re.IGNORECASE))
    has_type_check = bool(re.search(r'\btype\s*\(', handler_body))
    has_rejection_log = bool(re.search(r'msg\.(warn|error|info)', handler_body))
    return all([has_allowlist, has_type_check, has_rejection_log])
```

**Patch**: `re-workspace/deliverables/patches/FIND-006-fix-ipc-validation.patch`

The patch adds:
1. `_valid_options` table — allowlist mapping each option key to its expected Lua type
2. Unknown key rejection with `msg.warn` logging
3. Type checking for each value before assignment
4. Coercion for string "true"/"false" → boolean and string numbers → number (convenience)
5. Type mismatch rejection with detailed logging

**Allowlist covers all 24 options** defined in the options table at L6-31.

---

## Phase 6: Cleanup and Verification

After applying the patch, re-run:
```
python3 re-workspace/harness/tests/test_find_006.py
```
Expected: GREEN (exit 0) — allowlist, type(), and msg.warn detected in handler.

**Additional hardening recommendations** (beyond this patch):

1. **Remove or conditionally compile the handler**: The function name `test_set_options`
   implies it was a test/debug utility. Consider removing it entirely from production builds,
   or guarding it with `mp.get_property("debug")`.

2. **Add origin checking** (mpv does not expose sender identity, so this is not currently
   feasible without mpv API changes).

3. **Validate `additional_flags` content**: Even with allowlist protection, `additional_flags`
   is inherently dangerous. Consider deprecating it in favor of a structured flags API.

4. **Windows IPC exposure**: Document that `--input-ipc-server` should not be enabled in
   untrusted environments on Windows, as the named pipe is accessible to same-user processes.
