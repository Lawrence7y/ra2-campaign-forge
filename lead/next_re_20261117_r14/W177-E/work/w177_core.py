#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177 只读探针核心库：ReadProcessMemory / Wow64GetThreadContext / 窗口几何 / 合成输入。
全部只读目标进程内存；不写内存、不注入、不 Hook。
"""
import ctypes
import struct
import subprocess
from ctypes import wintypes as wt

k32 = ctypes.windll.kernel32
u32 = ctypes.windll.user32

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

# 全局探针地址（R13 §5 / R14 §5）
A_FRAME = 0x00A8ED84
A_MODE = 0x00A8B238
A_BULLETS = 0x00A8ED50
A_ABSTRACT = 0x00B0F730          # AbstractClass::Array.Count
A_BUILDING_ARRAY = 0x00A8EB50    # BuildingClass::Array (DynamicVectorClass<BuildingClass*>)
A_BYPASS = 0x00A8ED6B            # G3 校验/绘制旁路开关

OFF_NEXT = 0x30                  # 格链 next (O5)
OFF_O1 = 0x81                    # Limbo bool
OFF_O2 = 0x74                    # 已进入格子锁存
OFF_O3 = 0x80                    # 精灵脏标记
OFF_OWNER = 0x21C                # HouseClass* owner (O4)
OFF_MAP = 0x520                  # 指向 MapClass (O6)
CELL_E4 = 0xE4                   # 格链头 A (C1)
CELL_E8 = 0xE8                   # 格链头 B (C2)


def pid_of(name="gamemd"):
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process %s -ErrorAction SilentlyContinue).Id" % name],
                         capture_output=True, text=True).stdout.split()
    return int(out[0]) if out else None


class Mem:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed err=%d" % ctypes.get_last_error())
        self._b1 = ctypes.create_string_buffer(1)
        self._b2 = ctypes.create_string_buffer(2)
        self._b4 = ctypes.create_string_buffer(4)
        self.got = ctypes.c_size_t(0)

    def _rd(self, va, buf, n):
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n, ctypes.byref(self.got)) \
                and self.got.value == n:
            return buf.raw[:n]
        return None

    def u8(self, va):
        b = self._rd(va, self._b1, 1)
        return b[0] if b else None

    def u16(self, va):
        b = self._rd(va, self._b2, 2)
        return struct.unpack("<H", b)[0] if b else None

    def u32(self, va):
        b = self._rd(va, self._b4, 4)
        return struct.unpack("<I", b)[0] if b else None

    def close(self):
        k32.CloseHandle(self.h)


def globals_snapshot(m):
    return {
        "frame": m.u32(A_FRAME),
        "mode": m.u32(A_MODE),
        "bullets": m.u32(A_BULLETS),
        "objects": m.u32(A_ABSTRACT),
        "bypass": m.u8(A_BYPASS),
    }


def building_array(m):
    """读 BuildingClass::Array 的 Items(+4)/Count(+0x10)，返回 (items, count)。"""
    items = m.u32(A_BUILDING_ARRAY + 4)
    count = m.u32(A_BUILDING_ARRAY + 0x10)
    return items, count


def list_buildings(m, maxn=4000):
    items, count = building_array(m)
    out = []
    if items and count and 0 < count < maxn:
        for i in range(count):
            p = m.u32(items + 4 * i)
            if p:
                out.append((i, p))
    return items, count, out


def chain_from(m, head):
    """沿 obj+0x30 遍历格链，返回 (nodes, length, hit_cycle)。
    限制最大 64 节点防死循环；同时返回每节点的 O1/O2/O3 供 R1 判据。"""
    nodes = []
    seen = set()
    p = head
    while p and len(nodes) < 64:
        if p in seen:
            return nodes, len(nodes), True
        seen.add(p)
        nodes.append({
            "addr": p,
            "o1_81": m.u8(p + OFF_O1),
            "o2_74": m.u8(p + OFF_O2),
            "o3_80": m.u8(p + OFF_O3),
            "next_30": m.u32(p + OFF_NEXT),
        })
        p = m.u32(p + OFF_NEXT)
    return nodes, len(nodes), p is not None and len(nodes) >= 64


# ---------- 线程 EIP / 上下文采样（只读） ----------
class WOW64_CONTEXT(ctypes.Structure):
    _fields_ = [("ContextFlags", wt.DWORD),
                ("Dr0", wt.DWORD), ("Dr1", wt.DWORD), ("Dr2", wt.DWORD), ("Dr3", wt.DWORD),
                ("Dr6", wt.DWORD), ("Dr7", wt.DWORD),
                ("FloatSave", wt.BYTE * 112),
                ("SegGs", wt.DWORD), ("SegFs", wt.DWORD), ("SegEs", wt.DWORD), ("SegDs", wt.DWORD),
                ("Edi", wt.DWORD), ("Esi", wt.DWORD), ("Ebx", wt.DWORD), ("Edx", wt.DWORD),
                ("Ecx", wt.DWORD), ("Eax", wt.DWORD), ("Ebp", wt.DWORD), ("Eip", wt.DWORD),
                ("SegCs", wt.DWORD), ("EFlags", wt.DWORD), ("Esp", wt.DWORD), ("SegSs", wt.DWORD),
                ("ExtendedRegisters", wt.BYTE * 512)]


CONTEXT_i386 = 0x00010000
CONTEXT_FULL = CONTEXT_i386 | 0x00000007
CONTEXT_CONTROL = CONTEXT_i386 | 0x00000001
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040


def list_threads(pid):
    TH32CS_SNAPTHREAD = 0x00000004

    class THREADENTRY32(ctypes.Structure):
        _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ThreadID", wt.DWORD),
                    ("th32OwnerProcessID", wt.DWORD), ("tpBasePri", wt.LONG),
                    ("tpDeltaPri", wt.LONG), ("dwFlags", wt.DWORD)]

    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap == wt.HANDLE(-1).value:
        return []
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(te)
    out = []
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def thread_context(tid, flags=CONTEXT_CONTROL):
    h = k32.OpenThread(THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, False, tid)
    if not h:
        return None
    ctx = WOW64_CONTEXT()
    ctx.ContextFlags = flags
    try:
        if k32.Wow64GetThreadContext(h, ctypes.byref(ctx)):
            return ctx
        return None
    finally:
        k32.CloseHandle(h)
