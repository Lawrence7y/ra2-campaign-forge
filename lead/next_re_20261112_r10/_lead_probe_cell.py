#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 一次性探针（只读）：在活 gamemd 上验证 CellClass 两级访问路径。

目的：W109 的 UNKNOWNS 明确列了「0x87F924 表容量未证 / 真机 RPM 开销未测 /
真实空格与链长未知」。本探针只做最小验证，不写任何东西、不附加调试器：

  1. 读 [0x0087F924]  → 表基址
  2. 读 table[52*512+50] → NACNST 所在格的 cell 对象指针
  3. 读 cell+0xE4 / +0xE8 → 两条链头
  4. 读链头 [0] → vptr，判它是否 == 0x7E3EBC（BuildingClass 主虚表，RTTI 已证）
  5. 顺带读 static slot 0x0089C2E0 / 0x00ABDC50 的**值**（注意：值才是 cell 指针）

用法： python _lead_probe_cell.py <pid>
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

TABLE_GLOBAL = 0x0087F924
STATIC_SLOTS = [0x0089C2E0, 0x00ABDC50]
BUILDING_VT = 0x7E3EBC
CELL_FIRST_A = 0xE4
CELL_FIRST_B = 0xE8
NODE_NEXT = 0x30

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID, ctypes.c_size_t,
                                  ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype = wt.BOOL
k32.CloseHandle.argtypes = [wt.HANDLE]


def main():
    if len(sys.argv) < 2:
        print("usage: _lead_probe_cell.py <pid>")
        return 2
    pid = int(sys.argv[1], 0)
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        print("OpenProcess failed err=%d" % ctypes.get_last_error())
        return 3
    fails = [0]

    def rd(va, n):
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), buf, n, ctypes.byref(got))
        if not ok or got.value != n:
            fails[0] += 1
            return None
        return bytes(buf.raw[:n])

    def u32(va):
        b = rd(va, 4)
        return None if b is None else int.from_bytes(b, "little")

    try:
        print("=== probe pid=%d (read-only) ===" % pid)

        # 1) 表基址
        tbl = u32(TABLE_GLOBAL)
        print("1) [0x%08X] (table ptr) = %s" % (
            TABLE_GLOBAL, "READ FAIL" if tbl is None else "0x%08X" % tbl))
        if tbl is None:
            return 4

        # 2) NACNST 格 (row 52? 用 54,50 与 56,46 两个已知点)
        for (row, col, note) in [(54, 50, "NACNST?"), (56, 46, "NAPOWR#1"), (56, 48, "NAPOWR#2")]:
            idx = row * 512 + col
            cellp = u32(tbl + idx * 4)
            print("2) cell(%d,%d) idx=%-6d entry=0x%08X ptr=%s   [%s]" % (
                row, col, idx, tbl + idx * 4,
                "NULL" if cellp == 0 else ("READ FAIL" if cellp is None else "0x%08X" % cellp),
                note))
            if not cellp:
                continue
            # 3) 两条链头
            for off, name in ((CELL_FIRST_A, "+0xE4"), (CELL_FIRST_B, "+0xE8")):
                head = u32(cellp + off)
                if head is None:
                    print("     %s head = READ FAIL" % name)
                    continue
                if head == 0:
                    print("     %s head = NULL" % name)
                    continue
                vptr = u32(head)
                nxt = u32(head + NODE_NEXT)
                wa = u32(vptr + 0x2C) if vptr else None
                print("     %s head=0x%08X vptr=%s next=%s WhatAmI=%s  %s" % (
                    name, head,
                    "FAIL" if vptr is None else "0x%08X" % vptr,
                    "FAIL" if nxt is None else "0x%08X" % nxt,
                    "FAIL" if wa is None else hex(wa) if wa < 0x1000 else "0x%08X" % wa,
                    "** BuildingClass **" if vptr == BUILDING_VT else ""))

        # 4) 静态槽：值才是 cell 指针
        print("3) static slots (寄存器式：槽内存的是 cell 指针)")
        for s in STATIC_SLOTS:
            v = u32(s)
            print("   [0x%08X] = %s" % (s, "READ FAIL" if v is None else "0x%08X" % v))
            if v:
                for off, name in ((CELL_FIRST_A, "+0xE4"), (CELL_FIRST_B, "+0xE8")):
                    head = u32(v + off)
                    if head:
                        vptr = u32(head)
                        print("     %s head=0x%08X vptr=%s %s" % (
                            name, head, "FAIL" if vptr is None else "0x%08X" % vptr,
                            "** BuildingClass **" if vptr == BUILDING_VT else ""))

        print("\nRPM fail count = %d" % fails[0])
        return 0
    finally:
        k32.CloseHandle(h)


if __name__ == "__main__":
    raise SystemExit(main())
