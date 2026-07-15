#!/usr/bin/env python3
"""Run the project test gate and persist its structured summary."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.test_results import parse_test_summary  # noqa: E402

_CLEANUP_TIMEOUT_SECONDS = 2.0
_DIAGNOSTIC_TAIL_CHARACTERS = 2000


def _stream_text(stream: str | bytes | None) -> str:
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode("utf-8", errors="replace")
    return stream


def _bounded_tail(stream: str | bytes | None) -> str:
    text = _stream_text(stream).strip()
    if len(text) <= _DIAGNOSTIC_TAIL_CHARACTERS:
        return text
    omitted = len(text) - _DIAGNOSTIC_TAIL_CHARACTERS
    return f"[truncated {omitted} characters] {text[-_DIAGNOSTIC_TAIL_CHARACTERS:]}"


def _failure_summary(
    reason: str,
    *,
    stdout: str | bytes | None = None,
    stderr: str | bytes | None = None,
    cleanup_detail: str | None = None,
) -> dict[str, object]:
    details = [reason]
    if cleanup_detail:
        details.append(cleanup_detail)
    stderr_tail = _bounded_tail(stderr)
    stdout_tail = _bounded_tail(stdout)
    if stderr_tail:
        details.append(f"stderr tail: {stderr_tail}")
    if stdout_tail:
        details.append(f"stdout tail: {stdout_tail}")
    return {
        "all_passed": False,
        "project_coverage": None,
        "collected": 0,
        "source": "pytest",
        "detail": "; ".join(details),
    }


def _signal_process_tree(
    process: subprocess.Popen[str], *, force: bool
) -> str:
    """Signal pytest and its descendants, returning an audit-friendly action detail."""
    if os.name == "posix":
        signal_to_send = signal.SIGKILL if force else signal.SIGTERM
        action = signal_to_send.name
        try:
            os.killpg(process.pid, signal_to_send)
        except ProcessLookupError:
            return f"pytest process group already exited before {action}"
        except OSError as exc:
            return f"failed to send {action} to pytest process group: {exc}"
        return f"sent {action} to pytest process group"

    if os.name == "nt":
        taskkill_command = ["taskkill", "/PID", str(process.pid), "/T"]
        if force:
            taskkill_command.append("/F")
        try:
            result = subprocess.run(
                taskkill_command,
                capture_output=True,
                text=True,
                timeout=_CLEANUP_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            taskkill_detail = f"taskkill failed: {exc}"
        else:
            if result.returncode == 0:
                action = "force-terminated" if force else "terminated"
                return f"{action} pytest process tree with taskkill"
            taskkill_detail = (
                f"taskkill returned {result.returncode}: "
                f"{_bounded_tail(result.stderr or result.stdout)}"
            )
        try:
            if force:
                process.kill()
            else:
                process.terminate()
        except OSError as exc:
            action = "kill" if force else "termination"
            return f"{taskkill_detail}; direct pytest {action} failed: {exc}"
        action = "killed" if force else "terminated"
        return f"{taskkill_detail}; {action} pytest process directly"

    try:
        process.terminate()
    except OSError as exc:
        return f"failed to terminate pytest process: {exc}"
    return "terminated pytest process"


def _posix_process_group_exists(process: subprocess.Popen[str]) -> bool:
    if os.name != "posix":
        return False
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _close_process_pipes(process: subprocess.Popen[str]) -> list[str]:
    errors: list[str] = []
    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        if stream is None:
            continue
        try:
            stream.close()
        except OSError as exc:
            errors.append(f"failed to close pytest {name}: {exc}")
    return errors


def _terminate_and_reap(
    process: subprocess.Popen[str],
) -> tuple[str | bytes | None, str | bytes | None, str]:
    """Bound termination, escalation, pipe draining, and leader reaping."""
    details = [_signal_process_tree(process, force=False)]
    try:
        stdout, stderr = process.communicate(timeout=_CLEANUP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as terminate_timeout:
        stdout = terminate_timeout.stdout
        stderr = terminate_timeout.stderr
        details.append(
            f"pytest process group did not exit within {_CLEANUP_TIMEOUT_SECONDS:g} seconds"
        )
    else:
        if _posix_process_group_exists(process):
            details.append(_signal_process_tree(process, force=True))
        return stdout, stderr, "; ".join(details)

    details.append(_signal_process_tree(process, force=True))
    try:
        stdout, stderr = process.communicate(timeout=_CLEANUP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as kill_timeout:
        stdout = kill_timeout.stdout or stdout
        stderr = kill_timeout.stderr or stderr
        details.append(
            f"pytest pipes remained open {_CLEANUP_TIMEOUT_SECONDS:g} seconds after forced cleanup"
        )
        details.extend(_close_process_pipes(process))
        if process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=_CLEANUP_TIMEOUT_SECONDS)
            except (OSError, subprocess.SubprocessError) as exc:
                details.append(f"failed to reap pytest process: {exc}")
    return stdout, stderr, "; ".join(details)


def _terminate_after_interrupt(
    process: subprocess.Popen[str],
) -> tuple[str | bytes | None, str | bytes | None, str]:
    """Prevent repeated Ctrl-C from interrupting the bounded cleanup sequence."""
    previous_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        return _terminate_and_reap(process)
    finally:
        signal.signal(signal.SIGINT, previous_handler)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run entofile tests with coverage")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--coverage-floor",
        type=float,
        default=90.0,
        help="Minimum project coverage percentage (default: 90)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=600.0,
        help="Pytest timeout in seconds (default: 600)",
    )
    args = parser.parse_args()
    if not 0.0 <= args.coverage_floor <= 100.0:
        parser.error("--coverage-floor must be between 0 and 100")
    if args.timeout <= 0.0:
        parser.error("--timeout must be positive")

    root = args.project_root.resolve()
    report_path = root / "output" / "reports" / "test_results.json"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        junit_path = temp / "junit.xml"
        coverage_path = temp / "coverage.json"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--cache-clear",
            f"--junitxml={junit_path}",
            "--cov=src",
            f"--cov-fail-under={args.coverage_floor:g}",
            f"--cov-report=json:{coverage_path}",
            "-q",
        ]
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
                start_new_session=os.name == "posix",
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
            )
            process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            assert process is not None
            stdout, stderr, cleanup_detail = _terminate_and_reap(process)
            summary = _failure_summary(
                f"pytest timed out after {args.timeout:g} seconds",
                stdout=stdout or exc.stdout,
                stderr=stderr or exc.stderr,
                cleanup_detail=cleanup_detail,
            )
            returncode = 124
        except KeyboardInterrupt:
            if process is None:
                summary = _failure_summary("pytest interrupted by SIGINT before launch")
            else:
                stdout, stderr, cleanup_detail = _terminate_after_interrupt(process)
                summary = _failure_summary(
                    "pytest interrupted by SIGINT",
                    stdout=stdout,
                    stderr=stderr,
                    cleanup_detail=cleanup_detail,
                )
            returncode = 130
        except (OSError, subprocess.SubprocessError) as exc:
            if process is not None:
                stdout, stderr, cleanup_detail = _terminate_and_reap(process)
                summary = _failure_summary(
                    f"pytest subprocess failed: {type(exc).__name__}: {exc}",
                    stdout=stdout,
                    stderr=stderr,
                    cleanup_detail=cleanup_detail,
                )
            else:
                summary = _failure_summary(
                    f"pytest subprocess failed to start: {type(exc).__name__}: {exc}"
                )
            returncode = 124
        else:
            if process.returncode is None:
                summary = _failure_summary("pytest exited without a return code")
                returncode = 124
            else:
                summary = parse_test_summary(
                    junit_path,
                    coverage_path,
                    process.returncode,
                    source="pytest",
                )
                returncode = process.returncode

    report = {
        "summary": summary,
        "coverage_floor": args.coverage_floor,
        "command": command,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
