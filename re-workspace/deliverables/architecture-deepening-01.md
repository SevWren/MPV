# Architecture Deepening 01 — Format Registry Seam

**Candidate:** Explicit format registry seam
**Strength:** Strong
**Dependency category:** In-process (pure computation, no I/O)
**Lines affected:** L745–L1216 (format class definitions), L863, L1698 (call sites)
**Date:** 2026-11-15

---

## Context

The `formats` table is a bare Lua table populated by seven class definitions:

```lua
formats["raw"]      = RawVideo()
formats["webm-vp8"] = WebmVP8()
formats["webm-vp9"] = WebmVP9()
formats["mp4"]      = MP4H264()
formats["mp4-nvenc"]= MP4NVENC()
formats["mp3"]      = MP3()
formats["gif"]      = GIF()
```

Callers reach in with a bare key:

```lua
-- L1698
local format = formats[options.output_format]
```

There is no lookup contract. If the key is wrong (FIND-002: `"raw"` in EncodeOptionsPage's formatIds list; FIND-003: `"mp4 (h264/AAC)"` as the default) the caller gets `nil` and crashes several calls later when it tries to invoke a method on that nil.

The interface is entirely implicit (duck typing). Every method on a Format — `getCodecFlags()`, `getFlags()`, `getPreFilters()`, `getPostFilters()`, `postCommandModifier()` — is called by callers without any validation that the retrieved object actually has those methods.

---

## Design-A — Minimize the interface (1 entry point, maximum leverage)

### Interface

```lua
-- Single entry point. Errors early, never returns nil.
-- Invariant: returned value satisfies the Format protocol (all five methods present).
-- Error mode: msg.error + returns nil if key unknown (caller must check).
local format, err = format_registry.lookup(key)
```

**Entry points:** 1
**Types:**
- `key`: string — one of the registered format identifiers
- `format`: Format instance (table with methods), or `nil` on error
- `err`: string error message, or `nil` on success

**Invariants:**
- If `format` is non-nil, it is guaranteed to have `getCodecFlags`, `getFlags`, `getPreFilters`, `getPostFilters`, `postCommandModifier`.
- The registry is read-only after boot (all entries registered at module load time).
- `lookup` never mutates the registry.

**Ordering constraints:** None. Registry is fully populated before any call to `lookup` because all `formats[x] = Foo()` lines execute at module load, before `encode()` can be called.

**Error modes:** Returns `nil, "unknown format: <key>"` for unregistered keys. Does not crash. Caller is responsible for the nil check (consistent with Lua convention).

### Implementation hidden behind seam

```lua
local format_registry = {}
local _formats = {}  -- private; replaces the global formats table

-- Registration (called at boot, not part of the public interface)
local function register(key, instance)
  assert(type(instance.getCodecFlags) == "function", "Format missing getCodecFlags")
  assert(type(instance.getFlags) == "function", "Format missing getFlags")
  assert(type(instance.getPreFilters) == "function", "Format missing getPreFilters")
  assert(type(instance.getPostFilters) == "function", "Format missing getPostFilters")
  assert(type(instance.postCommandModifier) == "function", "Format missing postCommandModifier")
  _formats[key] = instance
end

function format_registry.lookup(key)
  local f = _formats[key]
  if f == nil then
    local known = {}
    for k in pairs(_formats) do known[#known+1] = k end
    return nil, "unknown format: " .. tostring(key) .. " (known: " .. table.concat(known, ", ") .. ")"
  end
  return f, nil
end

-- Boot-time registrations:
register("webm-vp8", WebmVP8())
register("webm-vp9", WebmVP9())
register("mp4",      MP4H264())
register("mp4-nvenc",MP4NVENC())
register("mp3",      MP3())
register("gif",      GIF())
-- Note: "raw" deliberately not registered; EncodeOptionsPage formatIds updated accordingly.
```

### Usage example (Design-A)

```lua
-- In encode():
local format, err = format_registry.lookup(options.output_format)
if not format then
  message("Unknown output format: " .. tostring(options.output_format))
  return
end
-- format is now guaranteed non-nil and protocol-complete.
append(command, format:getCodecFlags())
```

```lua
-- In EncodeOptionsPage.__init():
-- Remove "raw" from formatIds; lookup validates remaining keys at page open time.
local formatIds = { "webm-vp8", "webm-vp9", "mp4", "mp4-nvenc", "mp3", "gif" }
for _, id in ipairs(formatIds) do
  local f, err = format_registry.lookup(id)
  assert(f, err)  -- boot-time assertion: fail fast if list diverges from registry
end
```

### What implementation hides

- The private `_formats` table (callers never index it directly)
- Protocol validation at registration time
- Error message construction including the list of known keys
- The fact that `"raw"` exists as a class (RawVideo) but is not in the lookup table

---

## Design-B — Optimize for the most common caller (default case trivial)

### Interface

```lua
-- Primary entry point: returns format or raises error (no nil return).
-- Optimized for encode() which always expects a valid format.
local format = format_registry.get(key)   -- errors loudly on bad key

-- Secondary entry point: for UI code that needs to enumerate display choices.
local ids = format_registry.list_ids()    -- returns array of registered keys, sorted
local display = format_registry.display_name(key)  -- returns displayName string
```

**Entry points:** 3
**Types:**
- `get(key)` → Format instance; calls `error()` on unknown key (Lua error, not nil return)
- `list_ids()` → array of strings, sorted alphabetically
- `display_name(key)` → string; calls `error()` on unknown key

**Invariants:**
- `get` never returns nil. Callers need no nil check.
- `list_ids` reflects exactly the registered set (EncodeOptionsPage derives its list from here, so FIND-002 becomes structurally impossible).
- Display names come from the Format instance's `displayName` field.

**Ordering constraints:** None.

**Error modes:** `error("unknown format: " .. key)` — Lua error propagates to mpv error handler. This is intentional: a bad format key is a programming error (misconfigured default or bad IPC set), not a recoverable runtime condition.

### Implementation hidden behind seam

```lua
local format_registry = {}
local _formats = {}
local _ids = {}  -- sorted list, maintained on registration

local function register(key, instance)
  _formats[key] = instance
  _ids[#_ids + 1] = key
  table.sort(_ids)
end

function format_registry.get(key)
  local f = _formats[key]
  if not f then error("unknown format: " .. tostring(key), 2) end
  return f
end

function format_registry.list_ids()
  local copy = {}
  for i, id in ipairs(_ids) do copy[i] = id end
  return copy
end

function format_registry.display_name(key)
  return format_registry.get(key).displayName
end

-- Boot registrations same as Design-A (no "raw")
```

### Usage example (Design-B)

```lua
-- In encode(): no nil check needed, errors propagate to mpv.
local format = format_registry.get(options.output_format)
append(command, format:getCodecFlags())

-- In EncodeOptionsPage.__init(): list_ids() drives the UI automatically.
local formatIds = format_registry.list_ids()
-- formatIds is now ["gif","mp3","mp4","mp4-nvenc","webm-vp8","webm-vp9"]
-- Adding a new format to the registry automatically appears in the UI.
```

### What implementation hides

- Same as Design-A, plus:
- Sorted order maintenance
- Display name indirection
- The fact that EncodeOptionsPage no longer has a hardcoded list (FIND-002 becomes structurally impossible)

---

## Dependency strategy

**Category:** In-process — no process boundary is crossed. The registry is pure data + pure computation.

**Adapters:** None required. The seam is a Lua module boundary (a local table with functions), not a process boundary. No test adapters are needed because the registry is deterministic and can be tested by calling `register` + `lookup/get` directly.

**Migration:** The global `formats` table is not removed — it is renamed to `_formats` (private) and all direct indexing (`formats[key]`) is replaced with `format_registry.lookup(key)` or `format_registry.get(key)`. The existing Format class hierarchy is unchanged.

---

## Trade-offs comparison

| Dimension | Design-A (minimize interface) | Design-B (optimize common caller) |
|-----------|-------------------------------|-----------------------------------|
| Entry points | 1 | 3 |
| Nil handling | Returns nil + err string (Lua convention) | Errors on bad key; nil impossible |
| encode() call site | Must check nil | No check needed |
| EncodeOptionsPage | Still hardcodes list | Derives list from registry (structural fix for FIND-002) |
| Testability | Identical | Identical |
| New format registration | Not surfaced | list_ids() auto-includes |
| Error message quality | Rich (includes known keys) | Same (error() message) |
| Caller learning curve | Familiar Lua pattern | Slightly unusual (error on bad key) |

---

## Recommendation

**Design-B is stronger.**

The primary caller of the registry is `encode()`, which runs in a user-triggered hot path where a bad format key is always a programming error (wrong default string, or malformed IPC). Returning nil from `format_registry.get()` and requiring every call site to check it trades a one-time registration-time catch for N ongoing runtime nil checks. Design-B's `error()` on bad key is consistent with how the rest of the Lua standard library handles programming errors (table access, string.format with wrong types, etc.).

More importantly, Design-B's `list_ids()` makes FIND-002 structurally impossible: EncodeOptionsPage can no longer have a hardcoded formatIds list that diverges from the registry. This is worth the extra two entry points.

The only reason to prefer Design-A is if the caller needs to handle a user-supplied format key gracefully (e.g., from options.output_format set via IPC with an unknown value). That case is better handled at the IPC boundary (Candidate 7 in the review) rather than by making every encode() call site defensive.
