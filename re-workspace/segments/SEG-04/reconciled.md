# SEG-04 Reconciled Analysis
**Lines**: L563-744
**Description**: IEEE-754 double encode/decode, FirstpassStats class, VP8 2-pass logfile I/O

## Purpose
Implements manual IEEE-754 double-precision float serialization for patching VP8 first-pass statistics logfiles. The logfile format stores per-frame statistics as fixed-size binary records; the duration field is a little-endian IEEE-754 double. The script patches these durations after the first pass to correct the average frame duration.

## Line Walkthrough
- **L563-578**: `read_double(bytes)` — deserializes IEEE-754 from 8-byte array (big-endian order). Extracts sign (bit 7 of byte 1), exponent (bits 6-0 of byte 1 + bits 7-4 of byte 2), mantissa (bits 3-0 of byte 2 + bytes 3-8). Returns 0 if exponent==0.
- **L580-617**: `write_double(num)` — serializes a number to 8-byte IEEE-754 big-endian. Handles zero, Inf/NaN (not explicitly), negative numbers. Uses `math.frexp` to extract mantissa+exponent, then encodes.
- **L618-653**: `FirstpassStats` class — represents one binary record from the VP8 firstpass logfile.
  - Fields: `binary_data_before_duration`, `binary_duration`, `binary_data_after_duration`.
  - Class constants: `duration_multiplier = 10000000.0`, `fields_before_duration = 16`, `fields_after_duration = 1`.
  - Record size: `(16 + 1 + 1) * 8 = 144 bytes`.
- **L618-634**: Methods: `get_duration`, `set_duration`, `_bytes_to_string`, `as_binary_string`.
  - `get_duration`: reverses binary_duration, reads as big-endian double, divides by multiplier. NOTE: Bug — uses undefined `reversed_binary_duration` instead of local.
  - `set_duration`: multiplies by multiplier, writes double, reverses to little-endian.
- **L708-724**: `read_logfile_into_stats_array(logfile_path)` — reads binary logfile, chunks into 144-byte records, constructs FirstpassStats array.
- **L725-735**: `write_stats_array_to_logfile(stats_array, logfile_path)` — writes stats array back to binary file.
- **L736-749**: `vp8_patch_logfile(logfile_path, encode_total_duration)` — reads logfile, computes average frame duration, sets all frame durations, sets last frame to total duration, writes back.

## Inputs / Outputs
- **read_double**: 8-element byte array → float64.
- **write_double**: float64 → 8-element byte array.
- **vp8_patch_logfile**: logfile path + total duration → modified file on disk.

## Side Effects
- `vp8_patch_logfile` reads and overwrites a file on disk.
- `write_stats_array_to_logfile` opens file for writing.

## Invariants
- `read_double` and `write_double` are approximate inverses (within IEEE-754 precision).
- FirstpassStats record is always 144 bytes.
- `duration_multiplier = 1e7` (VP8 timestamps in 10ns units).

## Edge Cases
- **Bug at L620**: `get_duration` references `reversed_binary_duration` (undefined local); should be `big_endian_binary_duration`. This would cause a runtime error if `get_duration` is called. However, `vp8_patch_logfile` only calls `set_duration`, never `get_duration`, so this bug is never triggered in normal operation.
- `write_double` handling of Inf/NaN: not explicitly handled; `math.frexp(math.huge)` behavior is implementation-defined.
- If logfile has non-144-byte-multiple size (corrupt file), remaining bytes are silently discarded.
- `read_double` returns 0 when exponent is 0 (denormals and true zero both return 0).

## mpv Interactions
None in this segment. Pure Lua file I/O.

## Security Notes
- `read_logfile_into_stats_array` opens files with `io.open` — path is derived from `out_path` which comes from user-controlled `output_directory` and `output_template`. Path traversal possible if output directory is attacker-controlled.
