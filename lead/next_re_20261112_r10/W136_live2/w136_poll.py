#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W136: live read-only poll of the per-frame machinery (ledger §881-§883).

What this measures (all READ-ONLY, PROCESS_VM_READ only):
  - the logical frame counter            [0xA8ED84]
  - the event-ring counters              [0x8B41F8] count, [0x8B41FC] read idx,
                                         [0x8B4200] write idx
  - the mode selector                    [0xA8B238]   (switch in fn 0x647260)
  - the producer gate                    [0xA802C8]
  - the sync/debug flag word             [0xA8D5F8]   (expect 0 unless -MPDEBUG/-ATTRACT)
  - the per-type instance-array counts   (House/Foot/Unit/Infantry/Aircraft/Building/
                                         Techno/Abstract)

Why these: §881 established the chain 0x6BB9A0 -> 0x48CCC0 (Conquer.CPP loop) ->
0x55D360 (per-frame).  §883 showed the per-frame event pump writes 111-byte records
into a 16,384-entry ring and the consumer 0x64C380 scans that ring every frame.
So the ring occupancy is the quantity that predicts per-frame cost of the pump.

ALSO a structural prediction to falsify: I derived a stride of 111 bytes =
37 dwords * 3, with ring base 0x8B4204.  If records really are 111 bytes and the
count ever exceeds 0, then (0x8B4204 + 16384*111) = 0xA53204 must be readable
BSS.  This run reports whether the ring ever becomes non-empty.

Usage:
    python -X utf8 w136_poll.py --pid 1234 --secs 60
    python -X utf8 w136_poll.py --launch --secs 60
"""
import argparse
import ctypes
import io
import os
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

SANDBOX = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\sandbox_game"

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

FRAME = 0x00A8ED84
EV_COUNT = 0x008B41F8
EV_RD = 0x008B41FC
EV_WR = 0x008B4200
MODE = 0x00A8B238
PROD_GATE = 0x00A802C8
SYNC_FLAGS = 0x00A8D5F8

ARRAYS = [
    ("House", 0x00A80238), ("Foot", 0x008B3DD0), ("Unit", 0x008B4118),
    ("Infantry", 0x00A83DF8), ("Aircraft", 0x00A8E3A0), ("Building", 0x00A8EB50),
    ("Techno", 0x00A8EC88), ("Abstract", 0x00B0F730),
]

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


class Mem:
    def __init__(self, pid):
        self.dead = 0
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION,
                                 False, pid)
        if not self.h:
            raise OSError("OpenProcess failed: %d" % ctypes.get_last_error())

    def u32(self, va):
        b = ctypes.create_string_buffer(4)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, 4,
                                   ctypes.byref(got))
        if not ok or got.value != 4:
            self.dead += 1
            return None
        self.dead = 0
        return struct.unpack("<I", b.raw)[0]

    def u8(self, va):
        b = ctypes.create_string_buffer(1)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, 1,
                                   ctypes.byref(got))
        if not ok or got.value != 1:
            return None
        return b.raw[0]


def game_pids():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process gamemd -ErrorAction SilentlyContinue | "
                        "Select-Object -ExpandProperty Id"],
                       capture_output=True, text=True, timeout=60)
    return [int(x) for x in (r.stdout or "").split() if x.strip().isdigit()]


def launch(extra=""):
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\" %s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % (SANDBOX, extra))
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, text=True, timeout=120)
    t0 = time.time()
    while time.time() - t0 < 120:
        p = game_pids()
        if p:
            return p[0]
        time.sleep(1.0)
    raise RuntimeError("gamemd did not start")


def kill_all():
    for p in game_pids():
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p)],
                       capture_output=True, text=True, timeout=60)
    time.sleep(2.0)
    return game_pids()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int)
    ap.add_argument("--launch", action="store_true")
    ap.add_argument("--secs", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-kill", action="store_true")
    ap.add_argument("--game-args", default="")
    a = ap.parse_args()

    if not a.pid and not a.launch:
        ap.error("give --pid or --launch")

    launched = False
    if a.launch:
        pre = game_pids()
        if pre:
            print("killing leftover gamemd: %r" % pre)
            kill_all()
        pid = launch(a.game_args)
        launched = True
    else:
        pid = a.pid
    print("attached pid=%d  (READ-ONLY, PROCESS_VM_READ only)" % pid)

    mem = Mem(pid)
    out = io.open(a.out, "w", encoding="utf-8") if a.out else None
    if out:
        out.write("t\tframe\tev_count\tev_rd\tev_wr\tmode\tprod_gate\tsync_flags\t"
                  + "\t".join(n for n, _ in ARRAYS) + "\n")

    frames = []
    evmax = 0
    evnz = 0
    changes = []
    t0 = time.time()
    samples = 0
    last = None

    while time.time() - t0 < a.secs:
        if mem.dead > 30:
            print("PROCESS_GONE at t=%.1fs (30 consecutive read failures)" % (time.time() - t0))
            break
        fr = mem.u32(FRAME)
        ec = mem.u32(EV_COUNT)
        rd = mem.u32(EV_RD)
        wr = mem.u32(EV_WR)
        md = mem.u32(MODE)
        pg = mem.u32(PROD_GATE)
        sf = mem.u32(SYNC_FLAGS)
        arr = {n: mem.u32(va) for n, va in ARRAYS}
        t = time.time() - t0
        samples += 1
        if fr is not None:
            frames.append((t, fr))
        if ec is not None:
            if ec > evmax:
                evmax = ec
            if ec > 0:
                evnz += 1
        cur = (fr, ec, rd, wr, md, pg, sf, tuple(arr.values()))
        if cur != last:
            changes.append((t, cur))
            print("t=%7.3f frame=%-8s evcnt=%-6s rd=%-6s wr=%-6s mode=%-3s gate=%-3s sync=0x%X"
                  % (t, fr, ec, rd, wr, md, pg, sf or 0))
            if any(v for v in arr.values()):
                print("           arrays: " + " ".join("%s=%s" % (n, v) for n, v in arr.items()))
            last = cur
        if out:
            out.write("%.3f\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"
                      % (t, fr, ec, rd, wr, md, pg, sf,
                         "\t".join(str(arr[n]) for n, _ in ARRAYS)))
            out.flush()
        time.sleep(a.interval)

    print("\n=== SUMMARY over %.1fs, %d samples ===" % (time.time() - t0, samples))
    if len(frames) >= 2:
        f0, f1 = frames[0][1], frames[-1][1]
        dt = frames[-1][0] - frames[0][0]
        print("  frame counter: %d -> %d  (delta %d over %.1fs = %.2f fps-ish)"
              % (f0, f1, f1 - f0, dt, (f1 - f0) / dt if dt else 0))
        print("  => frame counter %s advancing" % ("IS" if f1 > f0 else "IS NOT"))
    else:
        print("  frame counter: not sampled enough")
    print("  event count: max=%d, samples>0 = %d/%d" % (evmax, evnz, samples))
    print("  distinct state changes: %d" % len(changes))

    if out:
        out.close()
        print("  wrote %s" % a.out)

    if launched and not a.no_kill:
        left = kill_all()
        print("  residual gamemd: %r" % left)
    return 0


if __name__ == "__main__":
    sys.exit(main())
