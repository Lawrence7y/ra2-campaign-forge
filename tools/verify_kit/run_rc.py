#!/usr/bin/env python3
"""run_rc.py -- run a command and capture its exit code independently.

Files produced (parent dirs must exist):
  <out>           stdout + stderr of the child, merged, raw bytes
  <out>.exitcode  the child's exit code, decimal integer + newline
  <out>.cmdline   the exact command line that was spawned

The exit code is NEVER embedded inside <out>; the output file and the exit
code file are written separately so no single process can quietly narrate
its own success.

Usage:
  python -B run_rc.py --out <path> [--cwd DIR] [--timeout SEC] -- CMD [ARGS...]

run_rc.py exits with the child's exit code (pass-through).
127 = spawn failure, 124 = timeout, 2 = usage error.
"""
import os
import subprocess
import sys
from subprocess import list2cmdline

import _vk_io

USAGE = ("usage: run_rc.py --out PATH [--cwd DIR] [--timeout SEC] "
         "-- CMD [ARGS...]")


def main(argv):
    if "--" not in argv:
        print(USAGE, file=sys.stderr)
        return 2
    sep = argv.index("--")
    head, cmd = argv[:sep], argv[sep + 1:]
    out_path = None
    cwd = None
    timeout = None
    i = 0
    while i < len(head):
        a = head[i]
        if a == "--out" and i + 1 < len(head):
            out_path = head[i + 1]
            i += 2
        elif a == "--cwd" and i + 1 < len(head):
            cwd = head[i + 1]
            i += 2
        elif a == "--timeout" and i + 1 < len(head):
            timeout = float(head[i + 1])
            i += 2
        else:
            print("ERROR: unknown/Incomplete option: %s" % a, file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2
    if not out_path:
        print("ERROR: --out is required", file=sys.stderr)
        return 2
    if not cmd:
        print("ERROR: empty command after --", file=sys.stderr)
        return 2

    try:
        proc = subprocess.run(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout)
        rc = proc.returncode
        out_bytes = proc.stdout or b""
    except FileNotFoundError as e:
        rc = 127
        out_bytes = ("run_rc: spawn failed: %s\n" % e).encode("utf-8", "replace")
    except OSError as e:
        rc = 126
        out_bytes = ("run_rc: cannot execute: %s\n" % e).encode("utf-8", "replace")
    except subprocess.TimeoutExpired as e:
        rc = 124
        partial = e.stdout if isinstance(e.stdout, bytes) else b""
        out_bytes = partial + ("run_rc: timeout after %ss, child killed, "
                               "exit code recorded as 124\n" % timeout).encode("ascii")

    try:
        _vk_io.write_bytes(out_path, out_bytes)
        _vk_io.write_text(out_path + ".exitcode", "%d\n" % rc)
        _vk_io.write_text(out_path + ".cmdline", list2cmdline(cmd) + "\n")
    except (OSError, ValueError) as e:
        print("ERROR: cannot write capture files: %s" % e, file=sys.stderr)
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
