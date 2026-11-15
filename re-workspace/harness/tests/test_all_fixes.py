import unittest
import re

WEBM_LUA = '/home/vercel-sandbox/MPV/scripts/webm.lua'
MPV_CONF  = '/home/vercel-sandbox/MPV/mpv.conf'

def read_webm():
    with open(WEBM_LUA) as f:
        return f.read()

def read_mpv_conf():
    with open(MPV_CONF) as f:
        return f.read()


# ---------------------------------------------------------------------------
# FIND-001: undefined 'bitrate' variable in strict filesize path
# ---------------------------------------------------------------------------
class TestFIND001_BitrateVariable(unittest.TestCase):
    """FIND-001: L1785-1786 must reference video_bitrate, not bare 'bitrate'"""

    def test_video_bitrate_used_in_minrate(self):
        """The minrate flag must be built with video_bitrate, not bare 'bitrate'.
        Actual source form: 'opts-add=minrate=" .. tostring(video_bitrate) .. "k'
        """
        src = read_webm()
        # Match the Lua concat form: opts-add=minrate=" .. tostring(<var>) .. "k
        m = re.search(r'opts-add=minrate="\s*\.\.\s*tostring\((\w+)\)\s*\.\.\s*"k', src)
        self.assertIsNotNone(m, "minrate flag (Lua concat form) not found in source")
        self.assertEqual(m.group(1), 'video_bitrate',
                         f"minrate uses wrong variable: {m.group(1)!r}, expected 'video_bitrate'")

    def test_video_bitrate_used_in_maxrate(self):
        """The maxrate flag must be built with video_bitrate, not bare 'bitrate'.
        Actual source form: 'opts-add=maxrate=" .. tostring(video_bitrate) .. "k'
        """
        src = read_webm()
        m = re.search(r'opts-add=maxrate="\s*\.\.\s*tostring\((\w+)\)\s*\.\.\s*"k', src)
        self.assertIsNotNone(m, "maxrate flag (Lua concat form) not found in source")
        self.assertEqual(m.group(1), 'video_bitrate',
                         f"maxrate uses wrong variable: {m.group(1)!r}, expected 'video_bitrate'")

    def test_bare_bitrate_variable_not_in_opts_concat(self):
        """No raw 'bitrate' variable should appear in an ovcopts/oacopts string concat."""
        src = read_webm()
        # Pattern: tostring(bitrate) inside a string that includes "opts-add="
        bad = re.findall(r'opts-add=(?:min|max)rate.*?tostring\(bitrate\)', src)
        self.assertEqual(bad, [],
                         f"Found bare 'bitrate' in minrate/maxrate flag: {bad}")


# ---------------------------------------------------------------------------
# FIND-003: default output_format must match registry key
# ---------------------------------------------------------------------------
class TestFIND003_OutputFormatDefault(unittest.TestCase):
    """FIND-003: options.output_format default must equal 'mp4' (a valid registry key)"""

    def test_default_output_format_is_mp4(self):
        src = read_webm()
        # First occurrence of output_format = "..." in the options table
        m = re.search(r'output_format\s*=\s*"([^"]+)"', src)
        self.assertIsNotNone(m, "output_format default not found")
        self.assertEqual(m.group(1), "mp4",
                         f"output_format default is '{m.group(1)}', expected 'mp4'")

    def test_mp4_key_exists_in_formats_registry(self):
        src = read_webm()
        self.assertIn('formats["mp4"]', src, "formats['mp4'] not registered")

    def test_no_human_readable_format_name_as_default(self):
        """Old value 'mp4 (h264/AAC)' must not be the default."""
        src = read_webm()
        m = re.search(r'output_format\s*=\s*"([^"]+)"', src)
        self.assertNotEqual(m.group(1), "mp4 (h264/AAC)",
                            "output_format still uses human-readable string as key")


# ---------------------------------------------------------------------------
# FIND-004: get_duration used wrong variable name (reversed vs big_endian)
# ---------------------------------------------------------------------------
class TestFIND004_GetDurationVariable(unittest.TestCase):
    """FIND-004: get_duration must pass big_endian_binary_duration to read_double"""

    def test_reversed_binary_duration_not_in_source(self):
        src = read_webm()
        self.assertNotIn('reversed_binary_duration', src,
                         "reversed_binary_duration still present in source")

    def test_big_endian_binary_duration_used_in_get_duration(self):
        src = read_webm()
        # get_duration block should contain read_double(big_endian_binary_duration)
        m = re.search(r'get_duration\s*=\s*function\(self\)(.*?)end,', src, re.DOTALL)
        self.assertIsNotNone(m, "get_duration function body not found")
        body = m.group(1)
        self.assertIn('big_endian_binary_duration', body,
                      "big_endian_binary_duration not in get_duration body")
        self.assertIn('read_double(big_endian_binary_duration)', body,
                      "read_double not called with big_endian_binary_duration")


# ---------------------------------------------------------------------------
# FIND-006: IPC handler must validate option keys against allowlist
# ---------------------------------------------------------------------------
class TestFIND006_IPCValidation(unittest.TestCase):
    """FIND-006: test_set_options must reject unknown keys and invalid JSON"""

    def _get_ipc_block(self, src):
        m = re.search(
            r'test_set_options\s*=\s*function.*?end\s*\nmp\.register_script_message',
            src, re.DOTALL)
        self.assertIsNotNone(m, "test_set_options block not found")
        return m.group()

    def test_allowlist_check_present(self):
        src = read_webm()
        block = self._get_ipc_block(src)
        self.assertIn('options[k] ~= nil', block,
                      "Key allowlist check missing from IPC handler")

    def test_unknown_key_logged_with_warn(self):
        src = read_webm()
        block = self._get_ipc_block(src)
        self.assertIn('msg.warn', block,
                      "Unknown key warning (msg.warn) missing from IPC handler")

    def test_json_type_check_present(self):
        src = read_webm()
        self.assertIn('type(new_options) ~= "table"', src,
                      "JSON type validation missing from IPC handler")

    def test_known_key_still_updated(self):
        """options[k] = v assignment must still be present for valid keys."""
        src = read_webm()
        block = self._get_ipc_block(src)
        self.assertIn('options[k] = v', block,
                      "options[k] = v assignment missing (valid keys won't be set)")


# ---------------------------------------------------------------------------
# FIND-007: temp file cleanup must happen BEFORE subprocess_detached
# ---------------------------------------------------------------------------
class TestFIND007_TempFileCleanup(unittest.TestCase):
    """FIND-007: os.remove and is_temporary check must precede subprocess_detached"""

    def _get_detached_block(self, src):
        m = re.search(
            r'if options\.run_detached then(.*?)return utils\.subprocess_detached',
            src, re.DOTALL)
        self.assertIsNotNone(m, "run_detached block not found")
        return m.group(1)

    def test_os_remove_before_detached(self):
        src = read_webm()
        block = self._get_detached_block(src)
        self.assertIn('os.remove', block,
                      "os.remove not called before subprocess_detached")

    def test_pass_logfile_cleanup_before_detached(self):
        src = read_webm()
        block = self._get_detached_block(src)
        self.assertIn('get_pass_logfile_path', block,
                      "get_pass_logfile_path cleanup missing before subprocess_detached")

    def test_is_temporary_check_before_detached(self):
        src = read_webm()
        block = self._get_detached_block(src)
        self.assertIn('is_temporary', block,
                      "is_temporary check missing before subprocess_detached")

    def test_out_path_defined_before_cleanup(self):
        """out_path must be defined before the run_detached block that calls get_pass_logfile_path(out_path)."""
        src = read_webm()
        out_path_def = src.find('local out_path = ')
        run_detached_block = src.find('if options.run_detached then')
        self.assertGreater(run_detached_block, out_path_def,
                           "out_path not defined before run_detached block")
        self.assertNotEqual(out_path_def, -1, "local out_path not found")


# ---------------------------------------------------------------------------
# FIND-010: originalProperties must be captured in prepare(), not __init
# ---------------------------------------------------------------------------
class TestFIND010_PreviewPageTiming(unittest.TestCase):
    """FIND-010: live mpv properties captured at preview start, not at object construction"""

    def _get_prepare_block(self, src):
        # PreviewPage's prepare function (the override, not the base no-op)
        # Base class prepare returns nil; PreviewPage's sets originalProperties
        m = re.search(
            r'prepare\s*=\s*function\(self\)\s*\n\s*self\.originalProperties\s*=\s*\{',
            src, re.DOTALL)
        self.assertIsNotNone(m, "PreviewPage prepare() with originalProperties not found")
        return m.group()

    def test_original_properties_captured_in_prepare(self):
        src = read_webm()
        self._get_prepare_block(src)  # asserts it exists

    def test_vf_property_in_prepare_not_init(self):
        src = read_webm()
        # Find __init for PreviewPage specifically (after "PreviewPage" declaration)
        preview_section = src[src.index('local PreviewPage'):]
        init_m = re.search(
            r'__init\s*=\s*function\(self,\s*callback.*?end,\s*__base',
            preview_section, re.DOTALL)
        self.assertIsNotNone(init_m, "PreviewPage __init not found")
        init_body = init_m.group()
        self.assertNotIn('mp.get_property_native("vf")', init_body,
                         "vf property still captured in __init (should be in prepare)")

    def test_time_pos_not_in_init(self):
        src = read_webm()
        preview_section = src[src.index('local PreviewPage'):]
        init_m = re.search(
            r'__init\s*=\s*function\(self,\s*callback.*?end,\s*__base',
            preview_section, re.DOTALL)
        init_body = init_m.group()
        self.assertNotIn('mp.get_property_native("time-pos")', init_body,
                         "time-pos still captured in __init (should be in prepare)")

    def test_original_properties_initialized_empty_in_init(self):
        """__init must set self.originalProperties = {} as safe sentinel."""
        src = read_webm()
        preview_section = src[src.index('local PreviewPage'):]
        self.assertIn('self.originalProperties = {}', preview_section,
                      "self.originalProperties = {} sentinel missing from __init")

    def test_dispose_iterates_original_properties(self):
        """dispose() must still iterate originalProperties to restore state."""
        src = read_webm()
        preview_section = src[src.index('local PreviewPage'):]
        dispose_m = re.search(
            r'dispose\s*=\s*function\(self\)(.*?)end,', preview_section, re.DOTALL)
        self.assertIsNotNone(dispose_m, "PreviewPage dispose() not found")
        self.assertIn('self.originalProperties', dispose_m.group(1),
                      "dispose() does not iterate self.originalProperties")

    def test_show_calls_prepare_before_dispose_via_hide(self):
        """The base Page.show() must call prepare(); hide() calls dispose().
        This guarantees originalProperties is populated before dispose() runs."""
        src = read_webm()
        show_m = re.search(r'show\s*=\s*function\(self\)(.*?)end,', src, re.DOTALL)
        self.assertIsNotNone(show_m, "Page.show() not found")
        show_body = show_m.group(1)
        self.assertIn('self:prepare()', show_body,
                      "Page.show() does not call self:prepare()")


# ---------------------------------------------------------------------------
# FIND-012: encode subprocess must have isolation flags before input file
# ---------------------------------------------------------------------------
class TestFIND012_SubprocessIsolation(unittest.TestCase):
    """FIND-012: subprocess isolation flags must be present and ordered before path"""

    def _get_command_block(self, src):
        # The encode() function's local command = { ... } array
        m = re.search(
            r'local command\s*=\s*\{([^}]*"mpv"[^}]*)\}',
            src, re.DOTALL)
        self.assertIsNotNone(m, "local command = { ... } array not found in encode()")
        return m.group(1)

    def test_no_config_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--no-config"', block)

    def test_load_scripts_no_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--load-scripts=no"', block)

    def test_keep_open_no_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--keep-open=no"', block)

    def test_loop_playlist_no_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--loop-playlist=no"', block)

    def test_hwdec_no_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--hwdec=no"', block)

    def test_save_position_on_quit_no_in_command(self):
        src = read_webm()
        block = self._get_command_block(src)
        self.assertIn('"--save-position-on-quit=no"', block)

    def test_isolation_flags_before_path(self):
        """All isolation flags must appear BEFORE the path variable in the command array."""
        src = read_webm()
        block = self._get_command_block(src)
        no_config_pos = block.find('"--no-config"')
        path_pos = block.find('\n    path,')
        # If path, is not found try alternate spacing
        if path_pos == -1:
            path_pos = block.find('path,')
        self.assertNotEqual(no_config_pos, -1, '"--no-config" not in command block')
        self.assertNotEqual(path_pos, -1, 'path, not found in command block')
        self.assertGreater(path_pos, no_config_pos,
                           "Isolation flags must appear before 'path' in command array")


# ---------------------------------------------------------------------------
# FIND-011/FIND-012 (additional_flags token validation)
# ---------------------------------------------------------------------------
class TestAdditionalFlagsValidation(unittest.TestCase):
    """additional_flags and non_strict_additional_flags tokens must require -- prefix"""

    def test_additional_flags_prefix_check(self):
        src = read_webm()
        flags_block = re.search(
            r'for token in string\.gmatch\(options\.additional_flags(.*?)end\s*end',
            src, re.DOTALL)
        self.assertIsNotNone(flags_block, "additional_flags loop not found")
        block = flags_block.group()
        self.assertIn('token:sub(1, 2) == "--"', block,
                      "-- prefix validation missing from additional_flags loop")

    def test_non_strict_additional_flags_prefix_check(self):
        src = read_webm()
        flags_block = re.search(
            r'for token in string\.gmatch\(options\.non_strict_additional_flags(.*?)end\s*end',
            src, re.DOTALL)
        self.assertIsNotNone(flags_block, "non_strict_additional_flags loop not found")
        block = flags_block.group()
        self.assertIn('token:sub(1, 2) == "--"', block,
                      "-- prefix validation missing from non_strict_additional_flags loop")

    def test_invalid_token_logged(self):
        src = read_webm()
        self.assertIn('msg.warn("Skipping invalid additional_flag', src,
                      "Invalid token warning missing from additional_flags processing")


# ---------------------------------------------------------------------------
# mpv.conf sanity checks
# ---------------------------------------------------------------------------
class TestMpvConf(unittest.TestCase):
    """mpv.conf must not contain invalid or harmful settings"""

    def test_verbose_msg_level_not_active(self):
        """msg-level=webm=verbose would prevent mpv from starting."""
        content = read_mpv_conf()
        # Must not appear as an active (non-commented) line
        active_lines = [l for l in content.splitlines()
                        if not l.strip().startswith('#') and 'msg-level=webm=verbose' in l]
        self.assertEqual(active_lines, [],
                         f"Active msg-level=webm=verbose found: {active_lines}")

    def test_log_file_not_active(self):
        """Active log-file= would write sensitive paths to disk."""
        content = read_mpv_conf()
        active_log = [l for l in content.splitlines()
                      if not l.strip().startswith('#') and 'log-file=' in l]
        self.assertEqual(active_log, [],
                         f"Active log-file= found in mpv.conf: {active_log}")

    def test_msg_level_v_not_webm_verbose(self):
        """The commented hint should reference 'v' not 'verbose'."""
        content = read_mpv_conf()
        # 'verbose' is not a valid mpv log level; ensure no line sets it actively
        bad = [l for l in content.splitlines()
               if not l.strip().startswith('#') and 'webm=verbose' in l]
        self.assertEqual(bad, [],
                         f"Active webm=verbose log level found: {bad}")


if __name__ == '__main__':
    import sys
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(__import__('__main__'))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
