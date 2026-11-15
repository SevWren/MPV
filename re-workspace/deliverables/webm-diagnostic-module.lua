--[[
  webm_diag — Diagnostic export module for webm.lua
  ===================================================
  Deep module: one call from encode() captures everything.
  Callers never touch file paths, JSON serialization,
  Windows vs POSIX path logic, or fallback strategies.

  Interface (Design A — Single capture function):

    webm_diag.capture(context) -> path | nil

  context fields (all optional; nil handled gracefully):
    phase              "pre-encode" | "post-encode" | "error"
    command            array of strings (the assembled mpv command)
    format             format object (uses .displayName field)
    out_path           string (resolved output path)
    subprocess_result  {status, stdout, stderr} | nil
    options_snapshot   copy of the options table at encode time

  Returns: absolute path of written diagnostic file, or nil on failure.
  Invariant: never raises; always returns.

  Integration points (do NOT apply these edits here — comments only):
  ------------------------------------------------------------------
  -- In encode(), after command assembly (~L1853):
  --   local diag_ctx = {
  --     phase = "pre-encode",
  --     command = command,
  --     format = format,
  --     out_path = out_path,
  --     options_snapshot = shallow_copy(options),
  --   }
  --   webm_diag.capture(diag_ctx)
  --
  -- After subprocess completes (~L1858-1878):
  --   diag_ctx.phase = "post-encode"
  --   diag_ctx.subprocess_result = res   -- or {detached=true} if run_detached
  --   webm_diag.capture(diag_ctx)
  ------------------------------------------------------------------
]]

local mp    = mp       -- injected by mpv runtime
local utils = mp.utils -- mp.utils guaranteed in mpv >= 0.28

-- ---------------------------------------------------------------------------
-- Internal: minimal safe JSON serializer
-- mp.utils.format_json is available but cannot handle tables with cycles or
-- mixed-key tables reliably across all mpv versions.  This serializer is
-- cycle-safe (tracks visited tables), always returns a string, and produces
-- human-readable indented output.
-- ---------------------------------------------------------------------------
local function _json_serialize(val, indent, visited)
  indent   = indent   or 0
  visited  = visited  or {}
  local t  = type(val)
  local pad = string.rep("  ", indent)
  local pad1 = string.rep("  ", indent + 1)

  if val == nil then
    return "null"
  elseif t == "boolean" then
    return val and "true" or "false"
  elseif t == "number" then
    -- Emit integers without decimal point for readability
    if val == math.floor(val) and math.abs(val) < 1e15 then
      return string.format("%d", val)
    else
      return string.format("%g", val)
    end
  elseif t == "string" then
    -- Escape special characters
    local escaped = val
      :gsub("\\", "\\\\")
      :gsub('"',  '\\"')
      :gsub("\n", "\\n")
      :gsub("\r", "\\r")
      :gsub("\t", "\\t")
    return '"' .. escaped .. '"'
  elseif t == "table" then
    if visited[val] then
      return '"<cycle>"'
    end
    visited[val] = true

    -- Decide: array or object?
    -- An array has only consecutive integer keys starting at 1.
    local is_array = true
    local max_n = 0
    for k, _ in pairs(val) do
      if type(k) ~= "number" or k ~= math.floor(k) or k < 1 then
        is_array = false
        break
      end
      if k > max_n then max_n = k end
    end
    -- Also check for gaps
    if is_array then
      for i = 1, max_n do
        if val[i] == nil then
          is_array = false
          break
        end
      end
    end

    local parts = {}
    if is_array and max_n > 0 then
      for i = 1, max_n do
        parts[#parts + 1] = pad1 .. _json_serialize(val[i], indent + 1, visited)
      end
      visited[val] = nil
      if #parts == 0 then return "[]" end
      return "[\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "]"
    else
      -- Object: sort keys for deterministic output
      local keys = {}
      for k in pairs(val) do
        keys[#keys + 1] = tostring(k)
      end
      table.sort(keys)
      for _, k in ipairs(keys) do
        local v = val[k]
        -- Skip function values; they cannot be serialized
        if type(v) ~= "function" then
          parts[#parts + 1] = pad1 .. '"' .. k:gsub('"', '\\"') .. '": '
            .. _json_serialize(v, indent + 1, visited)
        end
      end
      visited[val] = nil
      if #parts == 0 then return "{}" end
      return "{\n" .. table.concat(parts, ",\n") .. "\n" .. pad .. "}"
    end
  else
    -- function, userdata, thread — not serializable
    return '"<' .. t .. '>"'
  end
end

-- ---------------------------------------------------------------------------
-- Internal: safe shallow copy of a table (for options snapshot)
-- ---------------------------------------------------------------------------
local function _shallow_copy(tbl)
  if type(tbl) ~= "table" then return tbl end
  local copy = {}
  for k, v in pairs(tbl) do
    -- Only copy primitive-valued fields; skip functions and userdata
    local vt = type(v)
    if vt ~= "function" and vt ~= "userdata" and vt ~= "thread" then
      copy[k] = v
    end
  end
  return copy
end

-- ---------------------------------------------------------------------------
-- Internal: determine output directory for the diagnostic file
-- Priority: out_path directory > ~/ home directory > os.tmpname() parent
-- ---------------------------------------------------------------------------
local function _resolve_diag_dir(out_path)
  if out_path and out_path ~= "" then
    local dir, _ = utils.split_path(out_path)
    if dir and dir ~= "" then
      local info = utils.file_info(dir)
      if info and info.is_dir then
        return dir
      end
    end
  end
  -- Fallback: mpv home directory (~/)
  local home_dir = mp.command_native({"expand-path", "~/"})
  if type(home_dir) == "string" and home_dir ~= "" then
    return home_dir
  end
  -- Last resort: system temp
  local tmp = os.tmpname()
  if tmp then
    local dir, _ = utils.split_path(tmp)
    return dir or "/tmp"
  end
  return "/tmp"
end

-- ---------------------------------------------------------------------------
-- Internal: build the filename  webm-debug-YYYYMMDD-HHMMSS.json
-- ---------------------------------------------------------------------------
local function _make_filename()
  local stamp = os.date("%Y%m%d-%H%M%S")
  return "webm-debug-" .. stamp .. ".json"
end

-- ---------------------------------------------------------------------------
-- Internal: attempt to write data to path using io.open (primary) then
-- mp.utils.write_file (secondary).  Returns true on success, false+msg on
-- failure.  Both methods are wrapped in pcall.
-- ---------------------------------------------------------------------------
local function _write_file(path, data)
  -- Primary: io.open
  local ok, err = pcall(function()
    local f, ferr = io.open(path, "w")
    if not f then
      error(ferr or "io.open returned nil")
    end
    f:write(data)
    f:close()
  end)
  if ok then return true end

  -- Secondary: mp.utils.write_file (mpv >= 0.37, requires "file://" prefix)
  local ok2, err2 = pcall(function()
    utils.write_file("file://" .. path, data)
  end)
  if ok2 then return true end

  return false, "io.open: " .. tostring(err) .. " | write_file: " .. tostring(err2)
end

-- ---------------------------------------------------------------------------
-- Internal: collect all 12 diagnostic fields into one flat table
-- ---------------------------------------------------------------------------
local function _collect(context)
  context = context or {}

  -- 1. timestamp
  local timestamp = os.date("%Y-%m-%dT%H:%M:%S")

  -- 2. mpv_version
  local mpv_version = mp.get_property("mpv-version") or "unknown"

  -- 3. platform
  local platform_str = mp.get_property("platform") or "unknown"
  local is_windows   = (platform_str == "windows")
  local platform = {
    name       = platform_str,
    is_windows = is_windows,
  }

  -- 4. script_version  (matches the constant in webm.lua)
  local script_version = "2.0"   -- update when webm.lua bumps its version

  -- 5. options (snapshot passed by caller, or empty)
  local options_snapshot
  if type(context.options_snapshot) == "table" then
    options_snapshot = _shallow_copy(context.options_snapshot)
  else
    options_snapshot = {}
  end

  -- 6. input_path
  local input_path = mp.get_property("path") or "unknown"

  -- 7. input_exists
  local input_exists = nil
  if input_path ~= "unknown" then
    local fi = utils.file_info(input_path)
    if fi then
      input_exists = {
        size    = fi.size,
        is_file = fi.is_file,
        is_dir  = fi.is_dir,
      }
    else
      input_exists = false
    end
  end

  -- 8. output_path
  local output_path = context.out_path or "unknown"

  -- 9. output_format
  local output_format = {
    name        = (options_snapshot.output_format or "unknown"),
    displayName = (context.format and context.format.displayName) or "unknown",
  }

  -- 10. command (the assembled subprocess argv)
  local command_copy = {}
  if type(context.command) == "table" then
    for i, v in ipairs(context.command) do
      command_copy[i] = tostring(v)
    end
  end

  -- 11. subprocess_result
  local subprocess_result
  if type(context.subprocess_result) == "table" then
    local sr = context.subprocess_result
    if sr.detached then
      subprocess_result = { detached = true }
    else
      subprocess_result = {
        status = sr.status,
        stdout = sr.stdout or "",
        stderr = sr.stderr or "",
      }
    end
  else
    -- run_detached=yes path: no result available
    subprocess_result = { detached = true }
  end

  -- 12. output_file_size
  local output_file_size = nil
  if output_path ~= "unknown" then
    local fi = utils.file_info(output_path)
    if fi then
      output_file_size = fi.size
    else
      output_file_size = false   -- file does not exist (yet or at all)
    end
  end

  return {
    timestamp         = timestamp,
    mpv_version       = mpv_version,
    platform          = platform,
    script_version    = script_version,
    options           = options_snapshot,
    input_path        = input_path,
    input_exists      = input_exists,
    output_path       = output_path,
    output_format     = output_format,
    command           = command_copy,
    subprocess_result = subprocess_result,
    output_file_size  = output_file_size,
    -- Bonus metadata
    phase             = context.phase or "unknown",
    encode_session_ts = os.time(),
  }
end

-- ---------------------------------------------------------------------------
-- Public module table
-- ---------------------------------------------------------------------------
local webm_diag = {}

--[[
  webm_diag.capture(context) -> path | nil

  Collects all 12 diagnostic fields, serializes to JSON, and writes to
  {output_directory}/webm-debug-YYYYMMDD-HHMMSS.json.

  On write failure: falls back to mp.msg.warn for each top-level field so
  the data appears in mpv's log if --log-file is configured.

  Never raises. Always returns (path string or nil).
]]
function webm_diag.capture(context)
  -- Guard: entire function is pcall-wrapped so encode() is never interrupted
  local ok, result = pcall(function()
    local diag    = _collect(context)
    local json    = _json_serialize(diag, 0, {})
    local dir     = _resolve_diag_dir(context and context.out_path)
    local fname   = _make_filename()
    local path    = utils.join_path(dir, fname)

    local wrote, write_err = _write_file(path, json)
    if wrote then
      mp.msg.info("[webm_diag] Diagnostic written to: " .. path)
      return path
    else
      -- Fallback: emit to mpv log line by line (visible with --log-file)
      mp.msg.warn("[webm_diag] File write failed (" .. tostring(write_err)
        .. "); emitting to log instead.")
      mp.msg.warn("[webm_diag] ---- BEGIN DIAGNOSTIC ----")
      mp.msg.warn("[webm_diag] timestamp: "         .. tostring(diag.timestamp))
      mp.msg.warn("[webm_diag] mpv_version: "       .. tostring(diag.mpv_version))
      mp.msg.warn("[webm_diag] platform: "          .. tostring(diag.platform.name))
      mp.msg.warn("[webm_diag] script_version: "    .. tostring(diag.script_version))
      mp.msg.warn("[webm_diag] input_path: "        .. tostring(diag.input_path))
      mp.msg.warn("[webm_diag] output_path: "       .. tostring(diag.output_path))
      mp.msg.warn("[webm_diag] output_format: "
        .. tostring(diag.output_format.name) .. " / "
        .. tostring(diag.output_format.displayName))
      mp.msg.warn("[webm_diag] subprocess_result: " .. _json_serialize(diag.subprocess_result))
      mp.msg.warn("[webm_diag] command: "           .. _json_serialize(diag.command))
      mp.msg.warn("[webm_diag] ---- END DIAGNOSTIC ----")
      return nil
    end
  end)

  if ok then
    return result
  else
    -- pcall itself caught an error — this should never happen, but be safe
    mp.msg.error("[webm_diag] Internal error in capture(): " .. tostring(result))
    return nil
  end
end

--[[
  webm_diag.capture_on_failure(context, subprocess_result)

  Convenience wrapper: only writes the diagnostic file when the subprocess
  indicates failure (non-zero status or nil result).  Used when debug_mode
  is false (default) so files are written only on actual encode failures.

  When debug_mode=true, call webm_diag.capture() directly on every encode.
]]
function webm_diag.capture_on_failure(context, subprocess_result)
  local failed = true   -- default: assume failure (e.g. detached, unknown)
  if type(subprocess_result) == "table" then
    if subprocess_result.detached then
      -- run_detached=yes: we cannot know if it failed; write defensively
      failed = true
    else
      failed = (subprocess_result.status == nil or subprocess_result.status ~= 0)
    end
  elseif subprocess_result == false or subprocess_result == nil then
    failed = true
  end

  if failed then
    if context then
      context.subprocess_result = subprocess_result
    end
    return webm_diag.capture(context)
  end
  return nil
end

return webm_diag
