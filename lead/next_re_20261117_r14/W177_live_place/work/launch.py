#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动 gamemd.exe（cwd=ra2youli），把 pid 写入 work/game.pid。只启动我自己的进程。"""
import os
import subprocess
import sys
import time

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD = r"D:\Project\ra2-campaign-forge\ra2youli"
HERE = os.path.dirname(os.path.abspath(__file__))
PIDF = os.path.join(HERE, "game.pid")


def main():
    # 前置：确认无残留
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],
                         capture_output=True, text=True).stdout.strip()
    if out != "0":
        print("ABORT: residual gamemd count=%s" % out)
        return 2
    p = subprocess.Popen([GAME], cwd=CWD, close_fds=True)
    with open(PIDF, "w") as f:
        f.write(str(p.pid))
    print("spawned pid=%d  pidfile=%s" % (p.pid, PIDF))
    for i in range(8):
        time.sleep(1.0)
        if p.poll() is not None:
            print("EXITED early rc=%s" % p.poll())
            return 3
        print("  t+%ds alive" % (i + 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
