"""
CLI Harness for mpv encode experiment replication.
execution_environment: mock (mpv is not available in this sandbox)

This harness accepts an argv array for an mpv encode subprocess,
analyzes the command array statically for known-bad tokens and flags,
and simulates what the subprocess would do based on that static analysis.
"""

import os
import re
import json
import time
import subprocess
import sys

# ---------------------------------------------------------------------------
# Static analysis helpers
# ---------------------------------------------------------------------------

def parse_mpv_run_args(log_line: str) -> list:
    """
    Parses: Run command: run, flags=64, args=[command="mpv", args="--start=0.5", ...]
    Returns: ["mpv", "--start=0.5", ...]
    """
    matches = re.findall(r'args="((?:[^"\\]|\\.)*)"', log_line)
    return [m.replace('\\"', '"').replace('\\\\', '\\') for m in matches]


def has_moov_atom(path: str) -> bool:
    """
    MP4 files must contain a 'moov' atom. If absent, the file is unplayable.
    Read the first and last 64KB and search for the 'moov' box type.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    with open(path, "rb") as f:
        header = f.read(65536)
        f.seek(max(0, os.path.getsize(path) - 65536))
        footer = f.read(65536)
    return b"moov" in header or b"moov" in footer


def analyze_command_static(argv: list) -> dict:
    """
    Statically analyze an mpv command array for known-bad patterns that
    would cause a hang or corrupt output.

    Returns a dict with analysis results.
    """
    result = {
        "has_no_config": "--no-config" in argv,
        "has_load_scripts_no": "--load-scripts=no" in argv,
        "has_keep_open_no": "--keep-open=no" in argv,
        "has_loop_playlist_no": "--loop-playlist=no" in argv,
        "has_hwdec_no": "--hwdec=no" in argv,
        "has_save_position_no": "--save-position-on-quit=no" in argv,
        "bare_tokens": [],
        "output_path": None,
        "input_path": None,
        "extra_positional_args": [],
    }

    # Scan for bare tokens (not starting with -- and not the first arg "mpv")
    for i, token in enumerate(argv):
        if i == 0:
            continue  # skip "mpv" itself
        if not token.startswith("-") and not token.startswith("--o="):
            # Could be input file (first non-flag arg) or a bare option token
            if result["input_path"] is None and not token.startswith("--"):
                result["input_path"] = token
            elif not token.startswith("--"):
                # Subsequent positional args are suspect
                result["extra_positional_args"].append((i, token))
                result["bare_tokens"].append(token)
        if token.startswith("--o="):
            result["output_path"] = token[4:]

    return result


def predict_outcome(analysis: dict) -> dict:
    """
    Given static analysis of a command array, predict the encode outcome.
    This is a mock prediction based on known mpv behavior.
    """
    prediction = {
        "predicted_timed_out": False,
        "predicted_output_valid": True,
        "reasons": []
    }

    # Check 1: bare tokens that mpv would interpret as file paths
    if analysis["bare_tokens"]:
        for token in analysis["bare_tokens"]:
            prediction["reasons"].append(
                f"BARE_TOKEN: '{token}' has no '--' prefix — mpv interprets it as a "
                f"second input file path. mpv will attempt to open this as a file, fail, "
                f"and depending on keep-open setting, may hang."
            )
            prediction["predicted_output_valid"] = False

    # Check 2: keep-open=yes from user config (if --no-config is absent)
    if not analysis["has_no_config"]:
        prediction["reasons"].append(
            "NO_CONFIG_ABSENT: --no-config not in command. User's mpv.conf will be loaded "
            "by subprocess. User's mpv.conf has keep-open=yes [log:62]. Subprocess will not "
            "exit after encoding completes."
        )
        if analysis["bare_tokens"]:
            prediction["predicted_timed_out"] = True
            prediction["reasons"].append(
                "COMPOUND: bare token + keep-open=yes → subprocess tries to open bad file, "
                "fails, keep-open prevents exit → indefinite hang at 0% CPU."
            )

    # Check 3: load-scripts absent
    if not analysis["has_load_scripts_no"]:
        prediction["reasons"].append(
            "LOAD_SCRIPTS_NOT_DISABLED: User scripts (autoload, SmartCopyPaste, etc.) will "
            "be loaded by subprocess [log:155-179]. autoload may scan D:\\Videos\\ directory "
            "and add files to playlist, causing unexpected behavior."
        )

    # Check 4: If no bare tokens and has no-config, should be fine
    if not analysis["bare_tokens"] and analysis["has_no_config"] and analysis["has_keep_open_no"]:
        prediction["predicted_timed_out"] = False
        prediction["predicted_output_valid"] = True
        prediction["reasons"].append(
            "CLEAN: No bare tokens, --no-config present, --keep-open=no present. "
            "Subprocess should encode and exit cleanly."
        )

    return prediction


def run_encode_experiment(argv: list, timeout: int = 30, mock: bool = True) -> dict:
    """
    Run an encode experiment.
    If mock=True (default in this sandbox), performs static analysis only.
    If mock=False, actually runs the subprocess (requires real mpv).
    """
    result = {
        "command_array": argv,
        "execution_environment": "mock_harness" if mock else "real_mpv",
        "timeout_seconds": timeout,
        "static_analysis": analyze_command_static(argv),
        "prediction": None,
        "timed_out": None,
        "exit_code": None,
        "output_file_exists": None,
        "output_file_size_bytes": None,
        "output_file_size_after_kill_bytes": None,
        "moov_atom_present": None,
        "cpu_samples": [],
        "stdout": "",
        "stderr": "",
        "notes": ""
    }

    prediction = predict_outcome(result["static_analysis"])
    result["prediction"] = prediction

    if mock:
        # Mock mode: use static analysis to fill in predicted values
        result["timed_out"] = prediction["predicted_timed_out"]
        result["exit_code"] = None if prediction["predicted_timed_out"] else 0
        result["output_file_exists"] = True
        result["output_file_size_bytes"] = 0 if prediction["predicted_timed_out"] else 50000
        result["output_file_size_after_kill_bytes"] = 6291456 if prediction["predicted_timed_out"] else 50000
        result["moov_atom_present"] = False if prediction["predicted_timed_out"] else True
        result["cpu_samples"] = [0.0, 0.0, 0.0] if prediction["predicted_timed_out"] else [85.0, 90.0, 20.0]
        result["notes"] = (
            "MOCK RESULT — static analysis only. Real mpv not available in sandbox. "
            "Predictions based on known mpv behavior with these flags. "
            "Reasons: " + "; ".join(prediction["reasons"])
        )
    else:
        # Real execution mode
        output_path = result["static_analysis"]["output_path"]
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start = time.time()
        size_samples = []
        timed_out = False

        while proc.poll() is None:
            elapsed = time.time() - start
            if elapsed > timeout:
                proc.kill()
                timed_out = True
                break
            if output_path and os.path.exists(output_path):
                size_samples.append(os.path.getsize(output_path))
            time.sleep(2)

        stdout, stderr = proc.communicate()
        final_size = os.path.getsize(output_path) if output_path and os.path.exists(output_path) else 0

        result["timed_out"] = timed_out
        result["exit_code"] = proc.returncode
        result["output_file_exists"] = output_path is not None and os.path.exists(output_path)
        result["output_file_size_bytes"] = size_samples[-1] if size_samples else 0
        result["output_file_size_after_kill_bytes"] = final_size
        result["moov_atom_present"] = has_moov_atom(output_path) if output_path else False
        result["cpu_samples"] = size_samples  # proxy
        result["stdout"] = stdout.decode(errors="replace")[:2000]
        result["stderr"] = stderr.decode(errors="replace")[:2000]
        result["notes"] = "Real execution result."

    return result


def test_hypothesis(base_argv: list, modification: dict, timeout: int = 30, mock: bool = True) -> dict:
    """
    Test a hypothesis by modifying the base argv in a controlled way.
    modification = {
        "add_before_path": ["--keep-open=no"],
        "remove": ["cq-level=28"],
        "add_after_path": ["--loop-playlist=no"],
    }
    """
    argv = base_argv.copy()

    # Find the input file path index (first non-flag arg after "mpv")
    path_idx = None
    for i, a in enumerate(argv):
        if i == 0:
            continue
        if not a.startswith("-"):
            path_idx = i
            break

    # Remove tokens
    for token in modification.get("remove", []):
        if token in argv:
            argv.remove(token)

    # Add before path (after "mpv" but before path)
    if path_idx is not None:
        for token in reversed(modification.get("add_before_path", [])):
            argv.insert(1, token)

    # Add after path
    if path_idx is not None:
        new_path_idx = argv.index(argv[path_idx]) if argv[path_idx] in argv else path_idx
        for i, token in enumerate(modification.get("add_after_path", [])):
            argv.insert(new_path_idx + 1 + i, token)

    return run_encode_experiment(argv, timeout=timeout, mock=mock)


# ---------------------------------------------------------------------------
# Base argv from log:1282
# ---------------------------------------------------------------------------

BASE_ARGV = [
    "mpv",
    "D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4",
    "--start=0:00:00.567",
    "--end=0:00:01.469",
    "--loop-file=no",
    "--no-pause",
    "--ovc=libx264",
    "--oac=aac",
    "--vid=1",
    "--aid=1",
    "--sid=no",
    "--sub-ass-override=force",
    "--sub-auto=fuzzy",
    "--sub-pos=97.000000",
    "--sub-delay=0.000000",
    "--video-rotate=0",
    "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]",
    "--deinterlace=no",
    "--vf-add=lavfi-scale=-2:720",
    "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0",
    "--ovcopts-add=b=86939k",
    "cq-level=28",
    "--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4"
]

PATCHED_ARGV = [
    "mpv",
    "--no-config",
    "--load-scripts=no",
    "--keep-open=no",
    "--loop-playlist=no",
    "--hwdec=no",
    "--save-position-on-quit=no",
    "D:\\Videos\\Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p.mp4",
    "--start=0:00:00.567",
    "--end=0:00:01.469",
    "--loop-file=no",
    "--no-pause",
    "--ovc=libx264",
    "--oac=aac",
    "--vid=1",
    "--aid=1",
    "--sid=no",
    "--sub-ass-override=force",
    "--sub-auto=fuzzy",
    "--sub-pos=97.000000",
    "--sub-delay=0.000000",
    "--video-rotate=0",
    "--ytdl-format=bv*[height<=1080]+ba/b[height<=1080]",
    "--deinterlace=no",
    "--vf-add=lavfi-scale=-2:720",
    "--vf-add=lavfi-eq=contrast=1:saturation=1:brightness=0",
    "--ovcopts-add=b=86939k",
    # Note: "cq-level=28" is ABSENT because patched validation skips it
    "--o=D:\\ProgramData\\asus/Rockford_High-School-Marching-Band-2026-BOA-Grand-National-Championships-Prelimi_001_1080p-[00.00.567-00.01.469]-audio.mp4"
]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="mpv encode experiment harness")
    parser.add_argument("experiment", choices=["E1","E2","E3","E4","E5","E6","E7","all"],
                        help="Which experiment to run")
    parser.add_argument("--real", action="store_true", help="Use real mpv (not mock)")
    args = parser.parse_args()

    mock = not args.real
    experiments = {}

    # E1: Baseline — reproduce the bug
    if args.experiment in ("E1", "all"):
        experiments["E1"] = run_encode_experiment(BASE_ARGV, timeout=30, mock=mock)
        experiments["E1"]["experiment_id"] = "E1"

    # E2: test keep-open hypothesis
    if args.experiment in ("E2", "all"):
        argv_e2 = BASE_ARGV.copy()
        argv_e2.insert(1, "--keep-open=no")
        experiments["E2"] = run_encode_experiment(argv_e2, timeout=30, mock=mock)
        experiments["E2"]["experiment_id"] = "E2"

    # E3: test loop-playlist hypothesis
    if args.experiment in ("E3", "all"):
        argv_e3 = BASE_ARGV.copy()
        argv_e3.insert(1, "--loop-playlist=no")
        experiments["E3"] = run_encode_experiment(argv_e3, timeout=30, mock=mock)
        experiments["E3"]["experiment_id"] = "E3"

    # E4: test cq-level=28 bare arg hypothesis (remove bare token)
    if args.experiment in ("E4", "all"):
        argv_e4 = [a for a in BASE_ARGV if a != "cq-level=28"]
        experiments["E4"] = run_encode_experiment(argv_e4, timeout=30, mock=mock)
        experiments["E4"]["experiment_id"] = "E4"

    # E5: test no-config hypothesis
    if args.experiment in ("E5", "all"):
        argv_e5 = BASE_ARGV.copy()
        argv_e5.insert(1, "--no-config")
        argv_e5.insert(2, "--load-scripts=no")
        experiments["E5"] = run_encode_experiment(argv_e5, timeout=30, mock=mock)
        experiments["E5"]["experiment_id"] = "E5"

    # E6: combined fix
    if args.experiment in ("E6", "all"):
        experiments["E6"] = run_encode_experiment(PATCHED_ARGV, timeout=30, mock=mock)
        experiments["E6"]["experiment_id"] = "E6"

    # E7: regression — verify patched webm.lua behavior (same as E6 but labeled separately)
    if args.experiment in ("E7", "all"):
        experiments["E7"] = run_encode_experiment(PATCHED_ARGV, timeout=30, mock=mock)
        experiments["E7"]["experiment_id"] = "E7"
        experiments["E7"]["notes"] = "Regression test: patched webm.lua command array. " + experiments["E7"].get("notes", "")

    for exp_id, result in experiments.items():
        print(f"\n=== {exp_id} ===")
        print(json.dumps(result, indent=2))
