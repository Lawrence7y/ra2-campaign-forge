#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W154 probe: first in-game telemetry of this session (read-only).

Samples the engine counters every 50 ms for N seconds and writes NDJSON, then
prints a summary.  No input injection, no writes to the game.

Fields sampled:
  frame   [0xA8ED84]  logical frame counter (advances 1 per 32 ms tick)
  bullets [0xA8ED50]  DynamicVectorClass<BulletClass*>::Count
  mode    [0xA8B238]  mode selector
plus per-type instance counts to test the "FootClass = Unit+Infantry+Aircraft"
claim from the ledger (R11_COMMON §3.3).
"""
import argparse
import ctypes
import json
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

G = {
    "frame": 0x00A8ED84, "bullets": 0x00A8ED50, "mode": 0x00A8B238,
    "abstract": 0xB0F730, "foot": 0x008B3DD0, "units": 0x008B4118,
    "infantry": 0x00A83DF8, "aircraft": 0x00A8E3A0, "building": 0x00A8EB50,
    "techno": 0x00A8EC88, "anims": 0x00A8E9B8,
}
k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]


def pid_of():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process gamemd -ErrorAction SilentlyContinue).Id"],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--out", default="ingame_run1.ndjson")
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    h = k32.OpenProcess(0x1000 | 0x10, False, pid)
    buf = ctypes.create_string_buffer(4)
    got = ctypes.c_size_t(0)

    def rd(va):
        if k32.ReadProcessMemory(h, ctypes.c_void_p(va), buf, 4, ctypes.byref(got)) and got.value == 4:
            return struct.unpack("<I", buf.raw)[0]
        return None

    counts0 = {k: rd(v) for k, v in G.items()}
    print("counts at start: %s" % counts0)
    print("check FootClass == units+infantry+aircraft : %s+%s+%s = %s  (foot=%s)"
          % (counts0["units"], counts0["infantry"], counts0["aircraft"],
             (counts0["units"] or 0) + (counts0["infantry"] or 0) + (counts0["aircraft"] or 0),
             counts0["foot"]))

    t0 = time.perf_counter()
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        while time.perf_counter() - t0 < a.secs:
            t = time.perf_counter() - t0
            rec = {"t": round(t, 4), "frame": rd(G["frame"]), "bullets": rd(G["bullets"]),
                   "mode": rd(G["mode"])}
            f.write(json.dumps(rec) + "\n")
            n += 1
            time.sleep(a.interval)
    counts1 = {k: rd(v) for k, v in G.items()}
    print("samples=%d  counts at end: %s" % (n, counts1))

    # ---- summary ----
    rows = [json.loads(l) for l in open(a.out, encoding="utf-8")]
    print("mode set: %s" % sorted({r["mode"] for r in rows}))
    print("bullets: min=%s max=%s mean=%.2f"
          % (min(r["bullets"] for r in rows), max(r["bullets"] for r in rows),
             sum(r["bullets"] for r in rows) / len(rows)))
    df = [r["frame"] - rows[0]["frame"] for r in rows]
    st = [r for r in rows if r["frame"] != rows[0]["frame"]]
    if st:
        span = st[-1]["t"] - st[0]["t"]
        d = st[-1]["frame"] - st[0]["frame"]
        print("frame %s -> %s  over %.3f s  => %.2f frames/s, %.2f ms/frame"
              % (rows[0]["frame"], st[-1]["frame"], span, d / span, 1000.0 * span / d))
        # per-sample delta distribution
        dts, dfs = [], []
        for i in range(1, len(rows)):
            dts.append(rows[i]["t"] - rows[i - 1]["t"])
            dfs.append(rows[i]["frame"] - rows[i - 1]["frame"])
        print("delta frame per 50ms sample: %s" % sorted(set(dfs)))
        print("max gap between frame changes (s): %.3f"
              % max(r2["t"] - r1["t"] for r1, r2 in zip(st, st[1:])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
