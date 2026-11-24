#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全进程只读扫描特定 dword/float 值（VirtualQueryEx + ReadProcessMemory）。
用于定位侧栏 credits 字段的存储位置（输入 = UI 显示的数值）。"""
import argparse
import ctypes
import struct
import sys
from ctypes import wintypes as wt

import w177_core as W

k32 = ctypes.windll.kernel32

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]

k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t]
k32.VirtualQueryEx.restype = ctypes.c_size_t
MEM_COMMIT = 0x1000
PAGE_READABLE = 0x02 | 0x04 | 0x08 | 0x10 | 0x20 | 0x40 | 0x80  # coarse


def readable_regions(h):
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION()
    while addr < 0x80000000:
        got = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not got:
            break
        base = mbi.BaseAddress or 0
        size = mbi.RegionSize
        if mbi.State == MEM_COMMIT and mbi.Protect & 0xFF not in (0x00, 0x01):
            yield base, size, mbi.Protect
        nxt = base + size
        if nxt <= addr:
            break
        addr = nxt


def scan(h, patterns):
    """patterns: list of (label, bytes); search aligned dword offsets."""
    hits = {lab: [] for lab, _ in patterns}
    for base, size, prot in readable_regions(h):
        if size > 0x4000000:  # skip huge
            continue
        buf = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(h, ctypes.c_void_p(base), buf, size, ctypes.byref(got)):
            continue
        data = buf.raw[:got.value]
        for lab, pat in patterns:
            start = 0
            while True:
                i = data.find(pat, start)
                if i < 0:
                    break
                if i % 4 == 0:
                    hits[lab].append(base + i)
                    if len(hits[lab]) >= 200:
                        break
                start = i + 1
            # cap
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vals", required=True, help="comma int values to scan (u32 and u32*100)")
    ap.add_argument("--max", type=int, default=200)
    a = ap.parse_args()
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    h = k32.OpenProcess(0x0010 | 0x0400, False, pid)  # VM_READ|QUERY_INFO
    if not h:
        print("open failed", ctypes.get_last_error()); return 2
    patterns = []
    for s in a.vals.split(","):
        v = int(s)
        patterns.append(("u32_%d" % v, struct.pack("<I", v & 0xFFFFFFFF)))
        patterns.append(("u32_%d_x100" % v, struct.pack("<I", (v * 100) & 0xFFFFFFFF)))
        patterns.append(("f32_%d" % v, struct.pack("<f", float(v))))
    hits = scan(h, patterns)
    for lab, addrs in hits.items():
        print("%s: %d hits" % (lab, len(addrs)))
        for va in addrs[:40]:
            print("  0x%08X" % va)
    k32.CloseHandle(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
