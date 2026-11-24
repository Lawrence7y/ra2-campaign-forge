#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01-V1 启动脚本：只启动一个 gamemd.exe，把 pid 记到 work/launched_pid.txt。
本卡只关闭这个 pid。"""
import subprocess, time, os, sys
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD = r"D:\Project\ra2-campaign-forge\ra2youli"
PIDFILE = os.path.join(os.path.dirname(__file__), "launched_pid.txt")

# 先确认无残留
import subprocess as sp
out = sp.run(["powershell", "-NoProfile", "-Command",
              "(Get-Process gamemd -ErrorAction SilentlyContinue | Measure-Object).Count"],
             capture_output=True, text=True).stdout.strip()
if out != "0":
    print("ABORT: existing gamemd count=%s (not mine) - refusing to launch" % out)
    sys.exit(2)

p = subprocess.Popen([EXE], cwd=CWD, close_fds=True)
with open(PIDFILE, "w") as f:
    f.write(str(p.pid))
print("spawned pid=%d (recorded to launched_pid.txt)" % p.pid)
for i in range(12):
    time.sleep(1.5)
    if p.poll() is not None:
        print("EXITED rc=%s" % p.poll())
        break
    # 存活即持续打印
print("launch done; pid file:")
print(open(PIDFILE).read())
