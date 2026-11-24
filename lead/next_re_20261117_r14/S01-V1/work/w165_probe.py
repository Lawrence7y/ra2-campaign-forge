#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W165 探针：每帧采 4 个量（frame / bullets / 总对象数 / **移动中对象数**）。

全部只读：OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + ReadProcessMemory。

地址与判据（台账 §905，全部静态钉死）：
  frame         0xA8ED84  dword
  mode          0xA8B238  dword
  bullets       0xA8ED50  dword
  总对象数       0xB0F730  dword   AbstractClass::Array.Count
  LogicClass    0x87F778  +4=Items  +0x10=Count   VectorClass<ObjectClass*>
  loco 偏移      obj+0x674  dword   LocomotionClass*
  无目标门        loco+0x54  dword   == -1  => 不寻路
  未移动门        loco+0x5F  byte    == 0   => 不寻路
"""
import argparse
import ctypes
import json
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

A_FRAME = 0x00A8ED84
A_MODE = 0x00A8B238
A_BULLETS = 0x00A8ED50
A_ABSTRACT = 0x00B0F730
A_LOGIC = 0x0087F778
OFF_LOCO = 0x674
OFF_LOCO_TARGET = 0x54
OFF_LOCO_MOVING = 0x5F


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(0x0010 | 0x0400, False, pid)  # VM_READ | QUERY_INFORMATION
        if not self.h:
            raise OSError("OpenProcess failed")
        self._b4 = ctypes.create_string_buffer(4)
        self._b1 = ctypes.create_string_buffer(1)
        self._got = ctypes.c_size_t(0)

    def u32(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self._b4, 4, ctypes.byref(self._got)) \
                and self._got.value == 4:
            return struct.unpack("<I", self._b4.raw)[0]
        return None

    def u8(self, va):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), self._b1, 1, ctypes.byref(self._got)) \
                and self._got.value == 1:
            return self._b1.raw[0]
        return None


def snapshot(m):
    """读一帧的 4 个标量 + 移动中对象数。"""
    rec = {
        "frame": m.u32(A_FRAME),
        "mode": m.u32(A_MODE),
        "bullets": m.u32(A_BULLETS),
        "objects": m.u32(A_ABSTRACT),
    }
    # LogicClass 的 VectorClass<ObjectClass*>
    items = m.u32(A_LOGIC + 4)
    count = m.u32(A_LOGIC + 0x10)
    rec["lc_items"] = items
    rec["lc_count"] = count

    moving = 0
    with_loco = 0
    has_target = 0
    scanned = 0
    if items and count and 0 < count < 5000:
        for i in range(count):
            obj = m.u32(items + 4 * i)
            scanned += 1
            if not obj:
                continue
            loco = m.u32(obj + OFF_LOCO)
            if not loco:
                continue
            with_loco += 1
            tgt = m.u32(loco + OFF_LOCO_TARGET)
            mv = m.u8(loco + OFF_LOCO_MOVING)
            if tgt is None or mv is None:
                continue
            if tgt != 0xFFFFFFFF:
                has_target += 1
                if mv != 0:
                    moving += 1
    rec["scanned"] = scanned
    rec["with_loco"] = with_loco
    rec["has_target"] = has_target
    rec["moving"] = moving
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=60.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--out", default="w165.ndjson")
    a = ap.parse_args()

    pid = pid_of()
    if not pid:
        print("gamemd not running")
        return 2
    m = Mem(pid)
    print("pid=%d  interval=%.3fs  secs=%.0f" % (pid, a.interval, a.secs))

    first = snapshot(m)
    print("first snapshot: %s" % json.dumps(first))
    print("  sanity: objects=%s  lc_count=%s  moving=%s" %
          (first["objects"], first["lc_count"], first["moving"]))

    t0 = time.perf_counter()
    n = 0
    with open(a.out, "w", encoding="utf-8") as f:
        while time.perf_counter() - t0 < a.secs:
            t = time.perf_counter() - t0
            rec = snapshot(m)
            rec["t"] = round(t, 4)
            f.write(json.dumps(rec) + "\n")
            n += 1
            time.sleep(a.interval)
    print("samples=%d -> %s" % (n, a.out))

    rows = [json.loads(l) for l in open(a.out, encoding="utf-8")]
    print()
    print("  frame   : %s -> %s" % (rows[0]["frame"], rows[-1]["frame"]))
    for k in ("mode", "bullets", "objects", "lc_count", "scanned", "with_loco", "has_target", "moving"):
        vals = [r[k] for r in rows if r[k] is not None]
        if vals:
            print("  %-10s: min %-5d med %-7.1f max %-5d" % (k, min(vals), sorted(vals)[len(vals) // 2], max(vals)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
