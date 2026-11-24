#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-D launch gamemd.exe (cwd=ra2youli); record own pid under W177-D/work/. Only launches own process."""
import os
import subprocess
import sys
import time

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD = r"D:\Project\ra2-campaign-forge\ra2youli"
HERE = os.path.dirname(os.path.abspath(__file__))
PIDF = os.path.join(HERE, "game.pid")
MY_PIDS = os.path.join(HERE, "my_pids.txt")


def main():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],
                         capture_output=True, text=True).stdout.strip()
    if out != "0":
        print("ABORT: residual gamemd count=%s" % out)
        return 2
    p = subprocess.Popen([GAME], cwd=CWD, close_fds=True)
    with open(PIDF, "w") as f:
        f.write(str(p.pid))
    with open(MY_PIDS, "a") as f:
        f.write(str(p.pid) + "\n")
    print("spawned pid=%d pidfile=%s" % (p.pid, PIDF))
    for i in range(12):
        time.sleep(1.0)
        if p.poll() is not None:
            print("EXITED early rc=%s" % p.poll())
            return 3
        print("  t+%ds alive" % (i + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

