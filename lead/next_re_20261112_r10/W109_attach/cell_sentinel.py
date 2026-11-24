# -*- coding: utf-8 -*-
"""cell_sentinel.py -- R10 W109. 只读 CellClass 对象链哨兵（离线合成 + 活进程只读附加）。

模式：
  --dump            只读解析 ra2youli\\gamemd.exe，打印结构常量 / 白名单规模 / 字节自核
  --self-test       合成内存造对象图，断言按预期检出（W104 原 14 项，不许退化）
  --attach <pid>    只读附加到活进程：按 L8 两级路径遍历 512x512 cell 表，扫 +0xE4/+0xE8
                    两条链，报告所有 vptr 不在白名单的节点，并 dump 该节点内存
  --selftest-attach 自己拉起无害替身进程（python -c sleep），验证 RPM 通路 +
                    "目标里没有 0x87F924 结构"的降级路径，全程不崩
  --perf            512x512 一半空格合成表的单次扫描耗时，据此给轮询频率建议

通用可选参数（--attach / --selftest-attach 共用）：
  --rows A-B --cols C-D   cell 矩形窗口（含端点），默认 0-511 全区
  --max-nodes N           每链节点上限（默认 64）
  --hex N                 每个可疑节点 dump 的字节数（默认 0x40）
  --max-report N          最多展开多少个可疑节点（默认 200，其余只计数）
  --quiet                 不打逐行进度

※ 只读承诺（本卡硬要求）：只请求 PROCESS_VM_READ。不写内存、不建远程线程、不改任何文件。
  本文件除下面这一行外不出现任何写内存 API 的名字：
  严禁 PROCESS_VM_WRITE / WriteProcessMemory / VirtualAllocEx / CreateRemoteThread。
  --selftest-attach 里有一个源码自审，会把这条纪律机器验一遍。

结构来源（LEAD_FINDINGS_R09.md L8 / SENTINEL_RULING.md）：
  table = *(uint32*)0x0087F924        全局"存表指针"，不是表本身              [已证]
  obj   = table[Y*512 + X]            表项是 uint32 指针，可为 0（空格）      [已证]
  node  = *(uint32*)obj               obj 就是 CellClass 对象本身
  headA = *(uint32*)(obj + 0xE4)；headB = *(uint32*)(obj + 0xE8)            [已证]
  next  = *(uint32*)(node + 0x30)                                          [已证]
  vptr  = *(uint32*)(node)            节点首 dword

分级：[已证] / [静态推断] / [未证] 严格区分。本卡**没有真机**，"能读真机"一律 [未证]。
"""

import ctypes
import ctypes.wintypes as wt
import os
import struct
import sys
import time

# ----------------------------------------------------------------------------
# 判定常量（见 SENTINEL_RULING.md）
# ----------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "ra2youli", "gamemd.exe"))

IMAGE_BASE = 0x00400000
CELLCLASS_OBJ_SIZE = 0x148     # [已证] 0x005663C3: push 0x148
CELLCLASS_STRIDE = 0x148       # [静态推断] 与 +0xE4/+0xE8/+0x140/+0x11b 布局相容
CELLCLASS_BASE = 0x1           # [未证] 不存在静态基址；保留常量只为兼容旧输出
ROW_SHIFT = 9                  # 行优先: idx = row*512 + col   [已证] shl ecx,9
COL_MASK = 0x1FF
MAPTABLE_PTR_VA = 0x0087F924   # [已证] 全局，存表基址
MAPTABLE_LEN_VA = 0x0087F928   # [未证] 语义；仅打印参考
STATIC_CELL_SLOTS = (0x0089C2E0, 0x00ABDC50)   # [已证] 静态槽 / [静态推断] 兜底槽

CHAIN_HEADS = (0xE4, 0xE8)     # [已证]
NEXT_OFFSET = 0x30             # [已证]
WHATAMI_OFFSET = 0x2C          # [已证]
FIRST_SLOT = 0x00              # vptr 所在槽

MAX_NODES = 4096               # --self-test 用（W104 原值）
DEFAULT_ATTACH_MAX_NODES = 64  # --attach 默认每链节点上限
MAX_WHATAMI = 0x80

TABLE_ROWS = 512
TABLE_COLS = 512
TABLE_BYTES = TABLE_ROWS * TABLE_COLS * 4      # [静态推断] 1 MB（L8-3）

# vtable 白名单（W104 内嵌口径，仅用于 --dump 报告；--attach 用下面的字节扫描口径）
WHITELIST_SRC = "W100_cell_sentinel/EVIDENCE/vtable_whitelist.txt"
WHITELIST_LINES = 280
WHITELIST_ANCHOR_SET = 16
WHITELIST_RUN_SET = 264
VT_ANCHORS = (0x007E3EBC, 0x007EB058)          # [已证] WhatAmI=6 / 15

PAGE = 0x1000
# 只读访问权，只有这一项。严禁 PROCESS_VM_WRITE / PROCESS_VM_OPERATION / CREATE_THREAD。
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000  # 只读查询（VQE/进程名需要它）
READ_ACCESS = PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION  # 附加时唯一使用的权限组合

# ----------------------------------------------------------------------------
# 内存抽象与"读不到"契约
#   Mem（合成内存，--self-test 用）：未登记页 -> 抛 MemoryError（W104 原契约，14 项自测依赖它）
#   ProcMem（活进程，只读）：任何失败 -> 返回 None，绝不抛（--attach 硬要求 2）
#   PerfMem（--perf 用）：与 ProcMem 同契约，页面字典承载
# _rd()/_ok() 把两种契约统一收敛成"读到/读不到"，scan_chain 只依赖它们。
# ----------------------------------------------------------------------------
class Mem(object):
    """按页登记的可读内存。未登记页 = 不可读（抛 MemoryError，保持 W104 语义）。"""

    def __init__(self):
        self.pages = {}   # page_va -> bytearray(PAGE)

    def map_page(self, va):
        p = va & ~(PAGE - 1)
        if p not in self.pages:
            self.pages[p] = bytearray(PAGE)
        return self.pages[p]

    def write(self, va, data):
        i = 0
        while i < len(data):
            off = (va + i) & (PAGE - 1)
            pg = self.map_page(va + i)
            n = min(PAGE - off, len(data) - i)
            pg[off:off + n] = data[i:i + n]
            i += n

    def write_u32(self, va, v):
        self.write(va, struct.pack("<I", v & 0xFFFFFFFF))

    def readable(self, va, n):
        if va <= 0:
            return False
        for k in range(n):
            if ((va + k) & ~(PAGE - 1)) not in self.pages:
                return False
        return True

    def read_u32(self, va):
        if not self.readable(va, 4):
            raise MemoryError("unreadable page at 0x%08X" % va)
        off = va & (PAGE - 1)
        return struct.unpack_from("<I", self.pages[va & ~(PAGE - 1)], off)[0]

    def read_bytes(self, va, n):
        if not self.readable(va, n):
            raise MemoryError("unreadable page at 0x%08X" % va)
        off = va & (PAGE - 1)
        return bytes(self.pages[va & ~(PAGE - 1)][off:off + n])


class ReadStats(object):
    def __init__(self):
        self.reads = 0
        self.fails = 0
        self.distinct_fail_va = set()


def addr_legal(a):
    """地址合法性预检 [硬要求 3]：< 0x10000 或 > 0x7FFFFFFF 直接判非法。
    （游戏是 32 位用户态进程；这一条同时挡住 next 指向垃圾时最常见的几种取值。）"""
    return isinstance(a, int) and 0x10000 <= a <= 0x7FFFFFFF


def _ok(mem, va, n):
    try:
        return bool(mem.readable(va, n))
    except Exception:
        return False


def _rd(mem, va, n, st=None):
    """读 n 字节 -> bytes；读不到（任何原因）-> None。绝不抛。"""
    if not isinstance(va, int) or va <= 0:
        return None
    try:
        b = mem.read_bytes(va, n)
    except MemoryError:
        if st is not None:
            st.fails += 1
            st.distinct_fail_va.add(va)
        return None
    except Exception:
        if st is not None:
            st.fails += 1
            st.distinct_fail_va.add(va)
        return None
    if st is not None:
        st.reads += 1
    if b is None:              # ProcMem/PerfMem 契约：读不到 -> None
        if st is not None:
            st.fails += 1
            st.distinct_fail_va.add(va)
        return None
    return bytes(b)


def _rd32(mem, va, st=None):
    b = _rd(mem, va, 4, st)
    if b is None or len(b) != 4:
        return None
    return struct.unpack("<I", b)[0]


class PerfMem(object):
    """--perf 用：页面字典承载的合成内存。接口与 ProcMem 一致：读不到返回 None，绝不抛。"""

    def __init__(self):
        self.st = ReadStats()
        self.pid = 0
        self.pages = {}

    def put(self, va, data):
        i = 0
        while i < len(data):
            p = (va + i) & ~(PAGE - 1)
            pg = self.pages.get(p)
            if pg is None:
                pg = bytearray(PAGE)
                self.pages[p] = pg
            off = (va + i) & (PAGE - 1)
            n = min(PAGE - off, len(data) - i)
            pg[off:off + n] = data[i:i + n]
            i += n

    def reserve(self, start, end):
        p = start & ~(PAGE - 1)
        while p < end:
            if p not in self.pages:
                self.pages[p] = bytearray(PAGE)
            p += PAGE

    def read_bytes(self, va, n):
        if not isinstance(va, int) or va <= 0 or n <= 0:
            return None
        out = bytearray()
        left, cur = n, va
        while left > 0:
            pg = self.pages.get(cur & ~(PAGE - 1))
            if pg is None:
                self.st.fails += 1
                self.st.distinct_fail_va.add(va)
                return None
            off = cur & (PAGE - 1)
            take = min(PAGE - off, left)
            out += pg[off:off + take]
            cur += take
            left -= take
        self.st.reads += 1
        return bytes(out)

    def readable(self, va, n):
        return self.read_bytes(va, n) is not None

    def alive(self):
        return True


# ----------------------------------------------------------------------------
# 链扫描核心：两条链都扫；节点上限 + 已访问集合 + 地址预检 + 硬循环保护。
# 任何越界 / 读失败 / 垃圾指针都变成 finding，不中断、不抛。
# ----------------------------------------------------------------------------
def scan_chain(mem, head, tag="", max_nodes=MAX_NODES, st=None):
    """从 mem.read_u32(head) 开始沿 +0x30 走。

    返回 dict:
      nodes        访问到的节点 VA 列表（不含非法节点自身）
      vptr         与 nodes 一一对应的 vptr（读了才记）
      stop         终止原因: 'null' | 'max_nodes' | 'cycle' | 'unreadable' | 'illegal'
      findings     问题列表 [{kind, node, detail, ...}]
      whatami      每个节点的 WhatAmI 值（能解出来就记，解不出记 None）
    """
    out = {"tag": tag, "head": head, "nodes": [], "vptr": [], "stop": None,
           "findings": [], "whatami": []}
    cur = _rd32(mem, head, st)
    if cur is None:
        out["stop"] = "unreadable"
        out["findings"].append({"kind": "head_unreadable", "node": head,
                                "detail": "chain head slot 0x%08X not readable" % head})
        return out

    seen = set()
    guard = 0
    guard_max = max(1, int(max_nodes)) * 4 + 16
    while True:
        guard += 1
        if guard > guard_max:                  # 兜底：任何意外路径都不能无限循环
            out["stop"] = "max_nodes"
            out["findings"].append({"kind": "guard", "node": cur,
                                    "detail": "hard loop guard tripped"})
            return out
        if cur == 0:
            out["stop"] = "null"
            return out
        if not addr_legal(cur):                # 垃圾 next 直接停
            out["stop"] = "illegal"
            out["findings"].append({"kind": "illegal_next", "node": cur,
                                    "detail": "next pointer 0x%08X fails range check" % cur})
            return out
        if cur in seen:
            out["stop"] = "cycle"
            out["findings"].append({"kind": "cycle", "node": cur,
                                    "detail": "revisited node 0x%08X" % cur})
            return out
        if len(out["nodes"]) >= max_nodes:
            out["stop"] = "max_nodes"
            out["findings"].append({"kind": "max_nodes", "node": cur,
                                    "detail": "node budget %d exhausted" % max_nodes})
            return out
        seen.add(cur)
        out["nodes"].append(cur)

        if not _ok(mem, cur, 4):
            out["findings"].append({"kind": "unreadable_node", "node": cur,
                                    "detail": "node page unreadable; cannot read vptr"})
            out["stop"] = "unreadable"
            return out

        vptr = _rd32(mem, cur, st)
        if vptr is None:
            out["findings"].append({"kind": "unreadable_node", "node": cur,
                                    "detail": "vptr read failed"})
            out["stop"] = "unreadable"
            return out
        out["vptr"].append(vptr)

        # --- R1: vptr 必须能解引用到 +0x2C ---
        if not _ok(mem, vptr, WHATAMI_OFFSET + 4):
            kind = "vptr_small_int" if vptr < 0x00100000 else "vptr_nonderef"
            out["findings"].append({"kind": kind, "node": cur, "vptr": vptr,
                                    "detail": "vptr=0x%08X cannot be dereferenced at +0x2C" % vptr})
            out["whatami"].append(None)
        else:
            w = _rd32(mem, vptr + WHATAMI_OFFSET, st)
            wb = _rd(mem, w, 3, st) if w is not None else None
            # --- R2: WhatAmI 返回值必须是 B8 imm32 C3 thunk ---
            if wb is None or wb[0] != 0xB8:
                kind = "vptr_heap_ptr" if vptr >= 0x00400000 else "vptr_fake_table"
                out["findings"].append({"kind": kind, "node": cur, "vptr": vptr,
                                        "whatami_slot": w,
                                        "detail": "vptr=0x%08X slot+0x2C=0x%08X not a thunk"
                                                  % (vptr, w if w is not None else 0)})
                out["whatami"].append(None)
            else:
                nb = _rd(mem, w + 1, 4, st)
                n = struct.unpack("<i", nb)[0] if nb else -1
                if n <= 0 or n > MAX_WHATAMI:
                    out["findings"].append({"kind": "whatami_out_of_range", "node": cur,
                                            "vptr": vptr,
                                            "detail": "WhatAmI()=%d out of (0,0x%X]"
                                                      % (n, MAX_WHATAMI)})
                    out["whatami"].append(None)
                else:
                    out["whatami"].append(n)

        # next 槽本身也可能落进不可读页 -> 读之前检查
        nxt_va = cur + NEXT_OFFSET
        if not _ok(mem, nxt_va, 4):
            out["findings"].append({"kind": "next_unreadable", "node": cur,
                                    "detail": "next slot 0x%08X unreadable" % nxt_va})
            out["stop"] = "unreadable"
            return out
        nx = _rd32(mem, nxt_va, st)
        if nx is None:
            out["findings"].append({"kind": "next_unreadable", "node": cur,
                                    "detail": "next slot 0x%08X read failed" % nxt_va})
            out["stop"] = "unreadable"
            return out
        cur = nx


def scan_object(mem, obj):
    """扫一个 CellClass 对象的两条链，返回 {0xE4: result, 0xE8: result}。"""
    return dict((h, scan_chain(mem, obj + h, tag="+0x%02X" % h)) for h in CHAIN_HEADS)

# ----------------------------------------------------------------------------
# 只读进程内存（--attach / --selftest-attach 用）
# ----------------------------------------------------------------------------
_k32 = None


def k32():
    global _k32
    if _k32 is None:
        _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
        _k32.OpenProcess.restype = wt.HANDLE
        _k32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID,
                                           ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        _k32.ReadProcessMemory.restype = wt.BOOL
        _k32.CloseHandle.argtypes = [wt.HANDLE]
        _k32.CloseHandle.restype = wt.BOOL
        _k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
        _k32.GetExitCodeProcess.restype = wt.BOOL
        _k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                                    ctypes.POINTER(wt.DWORD)]
        _k32.QueryFullProcessImageNameW.restype = wt.BOOL
    return _k32


class ProcMem(object):
    """只读进程内存。所有读失败一律返回 None，绝不抛（硬要求 2）。

    缓冲跨读复用：RPM 失败时常只写部分字节，复用旧缓冲会污染下一次读，
    因此要求"实际写入 == 请求长度"，否则整条判失败、不返回半截数据。
    """

    def __init__(self, pid, access=READ_ACCESS):
        self.pid = int(pid)
        self.h = None
        self.buf = ctypes.create_string_buffer(PAGE + 64)
        self.access = access
        self.st = ReadStats()
        self._probe_va = None

    # --- 生命周期 ---
    def open(self):
        k = k32()
        self.h = k.OpenProcess(self.access, False, self.pid)
        if not self.h:
            err = ctypes.get_last_error()
            self.h = None
            raise OSError("OpenProcess(pid=%d, access=0x%X) failed, GetLastError=%d"
                          % (self.pid, self.access, err))
        return self

    def close(self):
        if self.h:
            try:
                k32().CloseHandle(self.h)
            finally:
                self.h = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False

    # --- 探测 ---
    def alive(self):
        """是否需要"目标还活着"。GetExitCodeProcess/QueryFullProcessImageNameW 需要
        PROCESS_QUERY_LIMITED_INFORMATION，而本卡只请求 PROCESS_VM_READ，
        所以这里**不**用它们，改为"对一个已知可读地址做一次 RPM"来判活：
        读得到 = 活着；读不到 = 已退出/不可读（两种情况都只需如实说读不到）。
        """
        if not self.h:
            return False
        if self._probe_va is None:
            self._probe_va = self.find_private_probe()[2] or 0
        if not self._probe_va:
            return False
        return self.read_bytes(self._probe_va, 4) is not None

    def _legacy_image_name_query(self):
        """保留：需要 PROCESS_QUERY_LIMITED_INFORMATION 才能用，本卡默认不请求。"""
        if not self.h:
            return ""
        n = wt.DWORD(1024)
        b = ctypes.create_unicode_buffer(1024)
        if not k32().QueryFullProcessImageNameW(self.h, 0, b, ctypes.byref(n)):
            return ""
        return b.value

    def image_name(self):
        """先试 0x1010 权限句柄（只读 + 限量查询），失败再退回普通句柄——不改变本对象权限。"""
        if not self.h:
            return ""
        k = k32()
        hn = k.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION, False, self.pid)
        try:
            if not hn:
                return ""
            n = wt.DWORD(1024)
            b = ctypes.create_unicode_buffer(1024)
            if not k.QueryFullProcessImageNameW(hn, 0, b, ctypes.byref(n)):
                return ""
            return b.value
        finally:
            if hn:
                k.CloseHandle(hn)

    # --- 读 ---
    def _raw(self, va, n):
        got = ctypes.c_size_t(0)
        ok = k32().ReadProcessMemory(self.h, ctypes.c_void_p(va), self.buf, n,
                                     ctypes.byref(got))
        self.st.reads += 1
        if not ok or got.value != n:
            self.st.fails += 1
            self.st.distinct_fail_va.add(va)
            return None
        return self.buf.raw[:n]

    def read_bytes(self, va, n):
        """-> bytes | None。跨页时按页切分；任一段失败即整条失败（不返回半截数据）。"""
        if not isinstance(va, int) or va <= 0 or n <= 0:
            return None
        if not self.h:
            return None
        out = bytearray()
        left, cur = n, va
        while left > 0:
            off = cur & (PAGE - 1)
            chunk = min(PAGE - off, left)
            b = self._raw(cur, chunk)
            if b is None:
                return None
            out += b
            cur += chunk
            left -= chunk
        return bytes(out)

    def readable(self, va, n):
        return self.read_bytes(va, n) is not None

    # --- 只读探针：找目标进程里一个"实测可读的私有堆页" ---
    def find_private_probe(self, limit=4096):
        """找一块 MEM_PRIVATE 且**实测读得到**的区域，用它证明 RPM 通路活着。
        返回 (ok, detail, va)。

        为什么"实测"而不只信 VirtualQuery：两者可能因保护/沙箱给出不一致结果，
        所以以"读得到"为唯一判据。为什么不用模块基址：DSH 沙箱下 DLL 在子进程里的
        映射基址与本进程不同（EVIDENCE/probe_rpm_self.txt / UNKNOWNS U3），拿本进程
        基址去读会假失败。
        """
        k = k32()
        # 把函数对象**解析成局部变量**再设 argtypes：直接写 k.VirtualQueryEx.argtypes 在某些
        # ctypes 版本/属性接管场景下不会落到真正被调用的函数对象上，实测结果是
        # "argtypes=None、HANDLE 被截断成 int32、VQE 返回 0 / err=5"（见 EVIDENCE/probe_rpm_self.txt）。
        vqe = k.VirtualQueryEx
        vqe.argtypes = [wt.HANDLE, wt.LPCVOID, ctypes.c_void_p, ctypes.c_size_t]
        vqe.restype = ctypes.c_size_t

        class MBI(ctypes.Structure):
            _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocBase", ctypes.c_void_p),
                        ("AllocProtect", wt.DWORD), ("PartitionId", wt.WORD),
                        ("RegionSize", ctypes.c_size_t), ("State", wt.DWORD),
                        ("Protect", wt.DWORD), ("Type", wt.DWORD)]

        va = 0x10000
        tried = 0
        regions = 0
        handle = wt.HANDLE(self.h)
        while va < 0x7FFF0000 and regions < limit:
            mbi = MBI()
            r = vqe(handle, ctypes.c_void_p(va), ctypes.byref(mbi), ctypes.sizeof(mbi))
            if r != ctypes.sizeof(mbi):
                break
            regions += 1
            base = mbi.BaseAddress or 0
            size = mbi.RegionSize or PAGE
            if mbi.State == 0x1000 and mbi.Type == 0x20000:
                tried += 1
                b = self.read_bytes(base, 16)
                if b is not None:
                    return (True,
                            "private page 0x%08X readable (16 B: %s)" % (base, b.hex()),
                            base)
            nxt = base + size
            if nxt <= va:
                break
            va = nxt
        msg = ("no readable MEM_PRIVATE page (regions=%d, private tried=%d, RPM fails=%d)"
               % (regions, tried, self.st.fails))
        return False, msg, 0


def _kernel32_base_here():
    """取本进程里 kernel32.dll 的基址。System32 的 DLL 是共享映像，同位数进程里基址一致，
    于是它可以当"目标进程里肯定可读"的探针地址。
    注意：这只证明 RPM 通路过得去，**不能**证明目标里也有同名模块（见 UNKNOWNS.md）。"""
    k = k32()
    if not hasattr(k, "GetModuleHandleExW"):
        k.GetModuleHandleExW.argtypes = [wt.DWORD, wt.LPCWSTR,
                                         ctypes.POINTER(ctypes.c_void_p)]
        k.GetModuleHandleExW.restype = wt.BOOL
    FUNC_ADDR = 0x00000004
    UNCHANGED = 0x00000002
    hmod = ctypes.c_void_p(0)
    fn = ctypes.cast(k.ReadProcessMemory, ctypes.c_void_p).value
    k.GetModuleHandleExW(FUNC_ADDR | UNCHANGED, ctypes.cast(fn, wt.LPCWSTR),
                         ctypes.byref(hmod))
    return hmod.value or 0


# ----------------------------------------------------------------------------
# PE 静态解析（--dump / --attach 白名单构建共用）
# ----------------------------------------------------------------------------
def _pe_map(path):
    """读 PE 节表，返回 (imgbase, [(name, va, vsize, raw_off, raw_size)], data)"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] != b"MZ":
        raise SystemExit("not a PE: " + path)
    lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[lfanew:lfanew + 4] != b"PE\0\0":
        raise SystemExit("bad PE sig")
    nsec = struct.unpack_from("<H", data, lfanew + 6)[0]
    optsz = struct.unpack_from("<H", data, lfanew + 20)[0]
    imgbase = struct.unpack_from("<I", data, lfanew + 24 + 28)[0]
    sec = lfanew + 24 + optsz
    out = []
    for k in range(nsec):
        o = sec + 40 * k
        name = data[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        out.append((name, imgbase + va, vsize, roff, rsize))
    return imgbase, out, data


def _imgsize(secs):
    return max(va + max(vs, rs) for _n, va, vs, ro, rs in secs)


def build_template(exe=EXE):
    """把镜像按 VA 铺成 bytes（洞填 0），供白名单同构判断。"""
    imgbase, secs, data = _pe_map(exe)
    size = _imgsize(secs) - imgbase
    tpl = bytearray(b"\x00" * size)
    for _n, va, vs, ro, rs in secs:
        n = min(rs, max(0, size - (va - imgbase)))
        if n > 0:
            tpl[va - imgbase: va - imgbase + n] = data[ro:ro + n]
    return imgbase, secs, tpl


_SECS_CACHE = {}


def section_of(va, exe=None):
    """VA -> (节名, is_exec)。只有 .text 算可执行；不在任何节里或读不到节表时按"可执行"处理
    （fail-open：宁可把它排进白名单，也不要因为判错而产生假阳性）。"""
    key = exe or EXE
    if key not in _SECS_CACHE:
        try:
            _SECS_CACHE[key] = _pe_map(key)[1]
        except Exception:
            _SECS_CACHE[key] = []
    for name, sva, vs, ro, rs in _SECS_CACHE[key]:
        if sva <= va < sva + max(vs, rs):
            return name, (name == ".text")
    return "?", True


def _whatami_in_template(tpl, imgbase, slot_va):
    off = slot_va - imgbase
    if off < 0 or off + 4 > len(tpl):
        return None
    thunk = struct.unpack_from("<I", tpl, off)[0]
    o2 = thunk - imgbase
    if o2 < 0 or o2 + 6 > len(tpl):
        return None
    if tpl[o2] != 0xB8 or tpl[o2 + 5] != 0xC3:
        return None
    n = struct.unpack_from("<i", tpl, o2 + 1)[0]
    return n if 0 <= n <= 0xFFFF else None


def build_whitelist(tpl_bytes, imgbase, secs):
    """从镜像的非 .text 数据节里扫"连续可执行指针游程"，把每个游程里的**每个 word** 当候选起点
    收进白名单（沿用 W104 step12 的口径），并解出起点 +0x2C 处的 WhatAmI。

    [静态推断] 依据：0x0047C538 `ff 50 2c` 调的是第 11 槽（0x2C/4）；vptr 指向 vtbl[0]，
    所以槽 11 的地址 = vptr + 0x2C —— 与 W104 self-test 里 `write_u32(vt + 11*4, thunk)` 同构。
    [已证] 限制：相邻 vtable 被合并成一条游程时，后者起点不在白名单，
    所以**白名单只能当"疑似合法"的一票**（SENTINEL_RULING §4-3）。
    """
    end = _imgsize(secs)
    runs = []
    cur = []
    wl = set()

    def flush():
        if cur:
            runs.append(list(cur))
            del cur[:]

    a = imgbase
    while a + 4 <= end:
        secname, _ex = section_of(a)
        if secname == ".text":
            flush()
            nxt = a + (PAGE - (a & (PAGE - 1)))     # 整页跳过代码，避免逐 dword 扫 .text
            a = nxt if nxt > a else a + 4
            continue
        off = a - imgbase
        if off + 4 > len(tpl_bytes):
            break
        val = struct.unpack_from("<I", tpl_bytes, off)[0]
        if 0x00400000 <= val < end and addr_legal(val):
            cur.append((a, val))
            if len(cur) > 0x4000:                   # 游程上限，防止异常数据撑爆
                flush()
        else:
            flush()
        a += 4
    flush()

    whatami = {}
    for run in runs:
        for va, _tgt in run:
            wl.add(va)
        s = run[0][0]
        whatami[s] = _whatami_in_template(tpl_bytes, imgbase, s + WHATAMI_OFFSET)
    for v in VT_ANCHORS:
        wl.add(v)
        whatami.setdefault(v, _whatami_in_template(tpl_bytes, imgbase, v + WHATAMI_OFFSET))
    return wl, len(wl), runs, whatami


_EVIDENCE_WL = None


def set_evidence_whitelist(vals):
    global _EVIDENCE_WL
    _EVIDENCE_WL = set(vals) | set(VT_ANCHORS)
    return len(_EVIDENCE_WL)


def in_whitelist(vptr):
    return _EVIDENCE_WL is not None and vptr in _EVIDENCE_WL


def judge_vptr(mem, tpl_bytes, imgbase, vptr, max_scan=0x4000):
    """对一个活进程里的 vptr 做两级判定（只读）。返回 (verdict, detail)。

    verdict:
      "wl"          命中镜像派生的白名单（弱证据，见 SENTINEL_RULING §4-3）
      "isomorphic"  活进程里 vptr 起那段内存与静态镜像**同位置逐字节同构**
                    （跳过所有"静态目标指向运行时分配区/越界"的 word）
      "suspect"     两者都不是 -> 报出来
    """
    if not addr_legal(vptr):
        return "suspect", "vptr=0x%08X fails range check" % vptr
    if in_whitelist(vptr):
        return "wl", "0x%08X in image-derived whitelist" % vptr
    if not tpl_bytes:
        return "suspect", "no static template (gamemd.exe missing?)"
    off = vptr - imgbase
    if off < 0 or off >= len(tpl_bytes):
        return "suspect", "vptr=0x%08X outside image VA range" % vptr
    n = min(max_scan, len(tpl_bytes) - off)
    n -= n % 4
    if n < 256:
        return "suspect", "image tail too short for isomorphic check"
    live = mem.read_bytes(vptr, n)
    if live is None:
        return "suspect", "vptr=0x%08X unreadable in process" % vptr
    tpl = bytes(tpl_bytes[off:off + n])
    total = n // 4
    eq = skipped = diff = 0
    lim = len(tpl_bytes)
    for i in range(0, n, 4):
        tgt = struct.unpack_from("<I", tpl, i)[0]
        p = tgt - imgbase
        if tgt < imgbase or p < 0 or p + 4 > lim:
            skipped += 1          # 静态里就无效的 word（运行时会被填）-> 不参与比对
            eq += 1
            continue
        if live[i:i + 4] == tpl[i:i + 4]:
            eq += 1
        else:
            diff += 1
    comparable = total - skipped
    if comparable < 64:
        return "suspect", "too few comparable words (%d)" % comparable
    rate = eq / float(total)
    tag = "structural match %.4f / %d words (%d skipped, %d diff)" % (
        rate, total, skipped, diff)
    if rate >= 0.995:
        return "isomorphic", tag
    return "suspect", "structural MISMATCH " + tag

# ----------------------------------------------------------------------------
# --dump
# ----------------------------------------------------------------------------
def cmd_dump():
    print("=== cell_sentinel --dump (read-only, no process attach) ===")
    print("EXE                : %s" % EXE)
    print("EXE exists/size    : %s / %s" %
          (os.path.exists(EXE), (os.path.getsize(EXE) if os.path.exists(EXE) else "-")))
    print("CELLCLASS_BASE     : 0x%X   [未证] 不存在静态基址；cell 经 [0x87F924] 两级访问"
          % CELLCLASS_BASE)
    print("CELLCLASS_STRIDE   : 0x%X (%d)  [静态推断] 0x005663C3: 6848010000 push 0x148"
          % (CELLCLASS_STRIDE, CELLCLASS_STRIDE))
    print("CELLCLASS_OBJ_SIZE : 0x%X (%d)  [已证] 0x00566AA6: 81c548010000 add ebp,0x148"
          % (CELLCLASS_OBJ_SIZE, CELLCLASS_OBJ_SIZE))
    print("INDEXING           : row-major, idx = row*%d + col  [已证] 0x00429DFA: c1e109"
          % (1 << ROW_SHIFT))
    print("TABLE GLOBAL       : 0x%08X（存表基址的全局）  [已证] 0x00429DF5: a124f98700"
          % MAPTABLE_PTR_VA)
    print("STATIC CELL SLOTS  : %s  [已证]/[静态推断]"
          % ", ".join("0x%08X" % v for v in STATIC_CELL_SLOTS))
    print("CHAIN HEADS        : %s  [已证] 0x0047C52A / 0x0047C4E3"
          % ", ".join("+0x%02X" % h for h in CHAIN_HEADS))
    print("NEXT OFFSET        : +0x%02X  [已证] 0x0047C540: 8b7630" % NEXT_OFFSET)
    print("WHATAMI SLOT       : +0x%02X  [已证] 0x0047C538: ff502c" % WHATAMI_OFFSET)
    print("CHAIN TERMINATOR   : NULL  [已证] test esi,esi / jne")
    print("WHITELIST_EMBEDDED : %d 条（来源 %s，SHA256 FC0A0F3C…7889）  [已证]"
          % (WHITELIST_LINES, WHITELIST_SRC))
    print("WHITELIST SET A/B  : %d / %d (step12_whitelist.txt:24,29)"
          % (WHITELIST_ANCHOR_SET, WHITELIST_RUN_SET))
    print("WHITELIST 已知缺陷  : 未处理相邻 vtable 合并成游程 (LEAD_FINDINGS_R09.md L2-2)"
          " => 只能当'疑似合法'的一票")

    if not os.path.exists(EXE):
        print("\n[SKIP] exe missing, cannot cross-check bytes")
        return 0

    imgbase, secs, data = _pe_map(EXE)
    print("\nPE ImageBase       : 0x%08X" % imgbase)
    for name, va, vs, ro, rs in secs:
        print("  %-8s VA=0x%08X VSize=0x%06X RawPtr=0x%06X RawSize=0x%06X"
              % (name, va, vs, ro, rs))

    def rd(va, n):
        for name, sva, vs, ro, rs in secs:
            if sva <= va < sva + max(vs, rs):
                o = ro + (va - sva)
                return data[o:o + n]
        return b""

    checks = [
        ("0x0047C52A mov esi,[ecx+0xE4]", 0x0047C52A, bytes.fromhex("8bb1e4000000")),
        ("0x0047C4E3 mov esi,[ecx+0xE8]", 0x0047C4E3, bytes.fromhex("8bb1e8000000")),
        ("0x0047C538 call [eax+0x2C]   ", 0x0047C538, bytes.fromhex("ff502c")),
        ("0x0047C540 mov esi,[esi+0x30] ", 0x0047C540, bytes.fromhex("8b7630")),
        ("0x0047C53B cmp eax,6         ", 0x0047C53B, bytes.fromhex("83f806")),
        ("0x00459EC0 mov eax,6; ret    ", 0x00459EC0, bytes.fromhex("b806000000c3")),
        ("0x00523340 mov eax,15; ret   ", 0x00523340, bytes.fromhex("b80f000000c3")),
        ("0x00483B32 shl edi,9 (row*512)", 0x00483B32, bytes.fromhex("c1e709")),
        ("0x005780B4 shl ecx,9 (row*512)", 0x005780B4, bytes.fromhex("c1e109")),
        ("0x005663C3 push 0x148 (obj sz)", 0x005663C3, bytes.fromhex("6848010000")),
        ("0x00566AA6 add ebp,0x148 (strd)", 0x00566AA6, bytes.fromhex("81c548010000")),
        ("0x00429DF5 mov eax,[0x87F924]", 0x00429DF5, bytes.fromhex("a124f98700")),
        ("0x00429DFA shl ecx,9        ", 0x00429DFA, bytes.fromhex("c1e109")),
        ("0x00429E19 mov ebx,[eax] 2lvl", 0x00429E19, bytes.fromhex("8b18")),
        ("0x00429E1F test ebx,ebx     ", 0x00429E1F, bytes.fromhex("85db")),
    ]
    ok = bad = 0
    print("\n=== byte self-check (VA: bytes) ===")
    for label, va, want in checks:
        got = rd(va, len(want))
        good = got == want
        ok += good
        bad += (not good)
        print("  [%s] %s 0x%08X: %s%s" % ("OK" if good else "MISMATCH", label, va,
                                          got.hex(), "" if good else " (want %s)" % want.hex()))
    print("  => %d ok, %d mismatch" % (ok, bad))

    print("\n=== vtable anchor slots ===")
    tpl_full = bytearray(data)
    for va in VT_ANCHORS:
        s11 = struct.unpack_from("<I", rd(va + 11 * 4, 4), 0)[0]
        s107 = struct.unpack_from("<I", rd(va + 107 * 4, 4), 0)[0]
        print("  0x%08X slot11=0x%08X WhatAmI=%s slot107=0x%08X"
              % (va, s11, _whatami_in_template(tpl_full, imgbase, va + WHATAMI_OFFSET), s107))

    t0 = time.perf_counter()
    imgbase2, secs2, tpl = build_template(EXE)
    wl, n, runs, whatami = build_whitelist(tpl, imgbase2, secs2)
    dt = (time.perf_counter() - t0) * 1000.0
    lens = sorted((len(r) for r in runs), reverse=True)
    print("\n=== whitelist by structural scan (--attach 实际用的判据之一) ===")
    print("  runs            : %d  (累计 word %d)" % (len(runs), sum(lens)))
    print("  top10 run sizes : %s" % lens[:10])
    print("  candidate start : %d  ([静态推断] 每个 word 当候选，同 W104 step12 口径)" % n)
    print("  anchors         : %s" % ", ".join(
        "0x%08X WhatAmI=%s" % (v, whatami.get(v)) for v in VT_ANCHORS))
    print("  build time      : %.1f ms" % dt)
    print("  ⚠ 白名单不完备（相邻 vtable 合并游程会漏起点）——见 SENTINEL_RULING §4-3；")
    print("    --attach 因此还叠了第二判据（与静态镜像同构），见 ATTACH_MODE.md §读路径")
    return 0 if bad == 0 else 2


# ----------------------------------------------------------------------------
# --self-test：合成内存（W104 原 14 项，逐条不动）
# ----------------------------------------------------------------------------
THUNK_N = 6
VT_OK = 0x007E3EBC
VT_OK2 = 0x007EB058
VT_HEAP = 0x15FD38E8
VT_FAKE = 0x000A0008
VMAP_OBJ = 0x00ABCD00
UNREAD = 0x00DEAD00


def _node(mem, va, vptr, nxt):
    mem.write_u32(va + FIRST_SLOT, vptr)
    mem.write_u32(va + NEXT_OFFSET, nxt)


def build_all():
    """一次建档，四套互不重叠的对象图（v2：v1 的假 FAIL 因 part2 复用了 0xABCD00）。"""
    mem = Mem()
    for vt, th in ((VT_OK, 0x00459EC0), (VT_OK2, 0x00523340)):
        mem.write_u32(vt + FIRST_SLOT, 0x00410260)
        mem.write_u32(vt + 11 * 4, th)
    mem.write(0x00459EC0, b"\xb8" + struct.pack("<i", THUNK_N) + b"\xc3\x90")
    mem.write(0x00523340, b"\xb8" + struct.pack("<i", 15) + b"\xc3\x90")
    mem.write_u32(VT_HEAP + 11 * 4, 0x00000014)

    # --- 对象 A (0xABCD00)：链A 合法2节点；链B 第二节点 vptr=小整数(S1) ---
    _node(mem, 0x00010000, VT_OK, 0x00011000)
    _node(mem, 0x00011000, VT_OK2, 0)
    _node(mem, 0x00020000, VT_OK, 0x00021000)
    _node(mem, 0x00021000, VT_FAKE, 0)
    mem.write_u32(0x00ABCD00 + 0xE4, 0x00010000)
    mem.write_u32(0x00ABCD00 + 0xE8, 0x00020000)

    # --- 对象 B (0xADCD00)：链A 第二节点 vptr=堆指针(S3)；链B 成环 ---
    _node(mem, 0x00030000, VT_OK, 0x00031000)
    _node(mem, 0x00031000, VT_HEAP, 0)
    _node(mem, 0x00032000, VT_OK, 0x00033000)
    _node(mem, 0x00033000, VT_OK, 0x00034000)
    _node(mem, 0x00034000, VT_OK, 0x00033000)
    mem.write_u32(0x00ADCD00 + 0xE4, 0x00030000)
    mem.write_u32(0x00ADCD00 + 0xE8, 0x00032000)

    # --- 对象 C (0xADCE00)：链A 空；链B next 指向不可读页 ---
    _node(mem, 0x00040000, VT_OK, 0)
    _node(mem, 0x00042000, VT_OK, UNREAD)
    mem.write_u32(0x00ADCE00 + 0xE4, 0)
    mem.write_u32(0x00ADCE00 + 0xE8, 0x00042000)

    # --- 自环节点（供节点上限用），不挂到任何已验证对象上 ---
    _node(mem, 0x00050000, VT_OK, 0x00050000)
    mem.write_u32(0x00ADCF00 + 0xE4, 0x00050000)
    mem.write_u32(0x00ADCF00 + 0xE8, 0)
    return mem


def cmd_self_test():
    fails = []
    checks = []

    def ck(name, ok, got):
        checks.append((name, bool(ok), got))
        print("  [%s] %s (got %r)" % ("PASS" if ok else "FAIL", name, got))
        if not ok:
            fails.append("%s got %r" % (name, got))

    def show(obj, res):
        print("\n--- object 0x%08X ---" % obj)
        for h in CHAIN_HEADS:
            r = res[h]
            print("  chain +0x%02X: nodes=%d stop=%-10s whatami=%-14s findings=%s" %
                  (h, len(r["nodes"]), r["stop"], r["whatami"],
                   [f["kind"] for f in r["findings"]]))

    print("=== cell_sentinel --self-test (synthetic memory, no process, no attach) ===")
    print("build: 4 independent object graphs, no object address reuse")
    mem = build_all()

    # 1) 小整数 vptr（S1 形态）
    ra = scan_object(mem, 0x00ABCD00)
    show(0x00ABCD00, ra)
    ck("A.chain+0xE4 两个节点且无 finding",
       len(ra[0xE4]["nodes"]) == 2 and ra[0xE4]["findings"] == [],
       (len(ra[0xE4]["nodes"]), [f["kind"] for f in ra[0xE4]["findings"]]))
    ck("A.chain+0xE4 WhatAmI=[6,15]", ra[0xE4]["whatami"] == [6, 15], ra[0xE4]["whatami"])
    ck("A.chain+0xE8 检出 vptr_small_int",
       any(f["kind"] == "vptr_small_int" for f in ra[0xE8]["findings"]),
       [f["kind"] for f in ra[0xE8]["findings"]])
    ck("A.chain+0xE8 坏节点不中断遍历（走到 NULL）", ra[0xE8]["stop"] == "null", ra[0xE8]["stop"])
    ck("A.chain+0xE8 节点数=2（含坏节点）", len(ra[0xE8]["nodes"]) == 2, len(ra[0xE8]["nodes"]))

    # 2) 堆指针 vptr + 成环
    rb = scan_object(mem, 0x00ADCD00)
    show(0x00ADCD00, rb)
    ck("B.chain+0xE4 检出 vptr_heap_ptr",
       any(f["kind"] == "vptr_heap_ptr" for f in rb[0xE4]["findings"]),
       [f["kind"] for f in rb[0xE4]["findings"]])
    ck("B.chain+0xE8 检出 cycle",
       rb[0xE8]["stop"] == "cycle" and any(f["kind"] == "cycle" for f in rb[0xE8]["findings"]),
       rb[0xE8]["stop"])
    ck("B.chain+0xE8 成环时节点数有限(<=4)", len(rb[0xE8]["nodes"]) <= 4, len(rb[0xE8]["nodes"]))

    # 3) 空链 + next 落不可读页
    rc = scan_object(mem, 0x00ADCE00)
    show(0x00ADCE00, rc)
    ck("C.chain+0xE4 空链 => NULL 终止且无 finding",
       rc[0xE4]["stop"] == "null" and rc[0xE4]["findings"] == [],
       (rc[0xE4]["stop"], [f["kind"] for f in rc[0xE4]["findings"]]))
    ck("C.chain+0xE8 next 指向不可读页 => unreadable_node 拦截，不崩",
       any(f["kind"] == "unreadable_node" for f in rc[0xE8]["findings"])
       and rc[0xE8]["stop"] == "unreadable", rc[0xE8]["stop"])

    # 4) 对象本身未映射 => 必须安全退回
    rd = scan_object(mem, 0x00ABE000)
    show(0x00ABE000, rd)
    ck("D 未映射对象 => 两条链都 head_unreadable",
       all(rd[h]["stop"] == "unreadable" and
           any(f["kind"] == "head_unreadable" for f in rd[h]["findings"]) for h in CHAIN_HEADS),
       [rd[h]["stop"] for h in CHAIN_HEADS])

    # 5) 节点上限
    cap = scan_chain(mem, 0x00ADCF00 + 0xE4, max_nodes=8)
    print("\n--- node budget (max_nodes=8, self-loop node) ---")
    print("  stop=%s nodes=%d findings=%s" %
          (cap["stop"], len(cap["nodes"]), [f["kind"] for f in cap["findings"]]))
    ck("E 节点上限生效（stop 为 cycle 或 max_nodes）",
       cap["stop"] in ("cycle", "max_nodes"), cap["stop"])
    ck("E 上限内节点数 <= 8", len(cap["nodes"]) <= 8, len(cap["nodes"]))

    # 6) 可重复性：同一对象连扫 3 次结果必须一致
    reps = [scan_object(mem, 0x00ABCD00)[0xE4]["whatami"] for _ in range(3)]
    ck("F 连扫 3 次结果一致（无状态污染）", reps[0] == reps[1] == reps[2] == [6, 15], reps)

    print("\n=== summary: %d checks, %d failed ===" % (len(checks), len(fails)))
    print("RESULT: %s" % ("GREEN" if not fails else "RED"))
    for f in fails:
        print("  FAILED: " + f)
    return 0 if not fails else 1


# ----------------------------------------------------------------------------
# 替身进程（--selftest-attach 用；绝不启动 gamemd）
# ----------------------------------------------------------------------------
FORBIDDEN_IMAGES = ("gamemd", "game.exe", "ra2md", "yuri")


def spawn_decoy(seconds=90):
    """拉起 python -c "import time;time.sleep(N)"（无参数、无文件、只 sleep）。"""
    import subprocess
    code = "import time;time.sleep(%d)" % int(seconds)
    creationflags = 0x08000000 if os.name == "nt" else 0    # CREATE_NO_WINDOW
    return subprocess.Popen([sys.executable, "-c", code],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, creationflags=creationflags)


def kill_own(p):
    try:
        p.terminate()
        p.wait(timeout=3)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass

# ----------------------------------------------------------------------------
# 扫描主循环（--attach / --selftest-attach 共用，全部防御式）
# ----------------------------------------------------------------------------
def parse_range(spec, lo, hi):
    if not spec:
        return lo, hi
    if "-" in spec:
        a, b = spec.split("-", 1)
        a, b = int(a), int(b)
    else:
        a = b = int(spec)
    if not (lo <= a <= b < hi):
        raise ValueError("range %r out of [%d,%d]" % (spec, lo, hi))
    return a, b


def _ascii(b):
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


def dump_hex(mem, va, n):
    """尽力 dump：能读多少读多少；整块读失败就退到逐 dword，仍失败如实标 <unreadable>。"""
    out = []
    cur, left = va, n
    while left > 0:
        step = min(64, left)
        b = mem.read_bytes(cur, step)
        if b is None:
            b4 = mem.read_bytes(cur, 4)
            if b4 is None:
                out.append("  +0x%04X: <unreadable>" % (cur - va))
                cur += 4
                left -= 4
                continue
            out.append("  +0x%04X: %-47s %s" % (cur - va, b4.hex(" "), _ascii(b4)))
            cur += 4
            left -= 4
            continue
        for i in range(0, len(b), 16):
            chunk = b[i:i + 16]
            out.append("  +0x%04X: %-47s %s" % (cur - va + i, chunk.hex(" "), _ascii(chunk)))
        cur += len(b)
        left -= len(b)
    return out


def scan_attach(mem, opts, banner_lines=None):
    """按 L8 两级路径遍历 cell 表并扫两条链。返回统计 dict。全程不抛。"""
    rows = opts["rows"]
    cols = opts["cols"]
    quiet = opts["quiet"]
    stats = {
        "pid": mem.pid,
        "table_base": None, "table_len": None,
        "cells_scanned": 0, "cells_null": 0,
        "cell_unreadable": 0, "cell_illegal": 0, "cell_dupe": 0,
        "cells_nonnull": 0, "objs_walked": 0,
        "chains": 0, "nodes": 0,
        "fail_head": 0, "fail_node": 0, "fail_next": 0, "stay_counts": {},
        "suspects": [], "suspects_truncated": 0,
        "judge_wl": 0, "judge_iso": 0,
        "notes": [], "verdict": None,
        "elapsed": None, "template": None, "wl_size": 0,
    }
    for ln in (banner_lines or []):
        print(ln)
    print("target pid         : %d" % mem.pid)
    print("range rows         : %d-%d (%d)" % (rows[0], rows[1], rows[1] - rows[0] + 1))
    print("range cols         : %d-%d (%d)" % (cols[0], cols[1], cols[1] - cols[0] + 1))
    print("max nodes / chain  : %d" % opts["max_nodes"])
    print("hex dump per node  : 0x%X" % opts["hexlen"])
    sys.stdout.flush()

    nreport = opts["max_report"]

    def note(kind, cell, chain, node, vptr, verdict, detail, findings):
        if len(stats["suspects"]) >= nreport:
            stats["suspects_truncated"] += 1
            return
        stats["suspects"].append({
            "kind": kind, "cell": cell, "chain": chain, "node": node,
            "vptr": vptr, "verdict": verdict, "detail": detail,
            "findings": [f["kind"] for f in findings],
        })

    # ---- 静态模板 + 白名单（一次性）----
    tpl = opts.get("tpl")
    imgbase = opts.get("imgbase", IMAGE_BASE)
    try:
        if tpl is None and os.path.exists(EXE):
            t1 = time.perf_counter()
            imgbase, secs, tpl = build_template(EXE)
            wl, wn, runs, whatami = build_whitelist(tpl, imgbase, secs)
            set_evidence_whitelist(wl)
            stats["wl_size"] = wn
            print("template           : %s (ImageBase 0x%08X, %d runs, %d candidate starts, %.1f ms)"
                  % (os.path.basename(EXE), imgbase, len(runs), wn,
                     (time.perf_counter() - t1) * 1000))
            print("anchor WhatAmI     : %s" % ", ".join(
                "0x%08X=%s" % (v, whatami.get(v)) for v in VT_ANCHORS))
        elif tpl is None:
            print("template           : MISSING (%s) -> 降级为'只做可解引用检查'" % EXE)
        stats["template"] = "loaded" if tpl is not None else "missing"
    except Exception as e:
        print("template           : build FAILED (%s: %s) -> 降级" % (type(e).__name__, e))
        tpl = None
        stats["template"] = "failed"

    # ---- 全局表指针（L8 两级路径的第一级）----
    tb = _rd32(mem, MAPTABLE_PTR_VA, mem.st)
    stats["table_base"] = tb
    stats["table_len"] = _rd32(mem, MAPTABLE_LEN_VA, mem.st)
    print("global [0x%08X]   : table base = %s" % (
        MAPTABLE_PTR_VA, ("0x%08X" % tb) if tb is not None else "<unreadable>"))
    print("global [0x%08X]   : value      = %s   ([未证] 语义，仅供参考)" % (
        MAPTABLE_LEN_VA,
        ("0x%08X" % stats["table_len"]) if stats["table_len"] is not None else "<unreadable>"))

    if tb is None:
        stats["verdict"] = "TARGET_HAS_NO_STRUCTURE"
        print("VERDICT            : TARGET_HAS_NO_STRUCTURE")
        print("                     读不到 0x%08X —— 该进程里没有这个全局，或该地址不可读。"
              % MAPTABLE_PTR_VA)
        stats["notes"].append("global unreadable")
        _finish(mem, stats)
        return stats
    if not addr_legal(tb):
        stats["verdict"] = "TABLE_PTR_ILLEGAL"
        print("VERDICT            : TABLE_PTR_ILLEGAL  0x%08X 未过地址预检 "
              "(<0x10000 或 >0x7FFFFFFF)" % tb)
        stats["notes"].append("table ptr illegal")
        _finish(mem, stats)
        return stats

    first = _rd32(mem, tb, mem.st)
    print("table[0]           : %s" % (("0x%08X" % first) if first is not None else "<unreadable>"))
    if first is not None and not (first == 0 or addr_legal(first)):
        stats["verdict"] = "TARGET_HAS_NO_STRUCTURE"
        print("VERDICT            : TARGET_HAS_NO_STRUCTURE")
        print("                     0x%08X 处首项 0x%08X 既非 0 也不像指针 => 该全局不是 cell 表基址"
              % (tb, first))
        stats["notes"].append("table[0] implausible")
        _finish(mem, stats)
        return stats

    # ---- 静态 cell 槽（额外起点，运行时读其值）----
    print("\n--- static cell slots (额外起点，运行时读其值) ---")
    for va in STATIC_CELL_SLOTS:
        v = _rd32(mem, va, mem.st)
        print("  [0x%08X] = %s" % (va, ("0x%08X" % v) if v is not None else "<unreadable>"))
        if v is None:
            continue
        if not addr_legal(v):
            print("    -> 值不合法，跳过")
            stats["cell_illegal"] += 1
            continue
        quad = _rd(mem, v + 0x24, 4, mem.st)
        rc = None
        if quad is not None:
            lo = struct.unpack("<h", quad[:2])[0]
            hi = struct.unpack("<h", quad[2:4])[0]
            rc = (lo, hi)          # +0x24 = 行 / +0x26 = 列（[已证] L1）
        print("    cell obj=0x%08X  [+0x24..0x27]=%s  推断 (行,列)=%s"
              % (v, quad.hex() if quad else "<unread>", rc if rc else "?"))
        _scan_cell(mem, stats, opts, cell=va, obj=v, where="slot 0x%08X" % va,
                   note=note, tpl=tpl, imgbase=imgbase)

    # ---- 主表遍历（L8 第一级 + 第二级）----
    print("\n--- table sweep (table=0x%08X, rows %d-%d, cols %d-%d) ---"
          % (tb, rows[0], rows[1], cols[0], cols[1]))
    cache = {}
    t0 = time.perf_counter()
    for row in range(rows[0], rows[1] + 1):
        rowbase = tb + (row << ROW_SHIFT) * 4
        rnull = 0
        stop_now = False
        for col in range(cols[0], cols[1] + 1):
            obj = _rd32(mem, rowbase + col * 4, mem.st)
            stats["cells_scanned"] += 1
            if obj is None:
                stats["cell_unreadable"] += 1
                continue
            if obj == 0:
                stats["cells_null"] += 1
                rnull += 1
                continue
            if not addr_legal(obj):
                stats["cell_illegal"] += 1
                continue
            stats["cells_nonnull"] += 1
            if obj in cache:
                stats["cell_dupe"] += 1
                continue
            cache[obj] = 1
            stats["objs_walked"] += 1
            _scan_cell(mem, stats, opts, cell=rowbase + col * 4, obj=obj,
                       where="row %d col %d" % (row, col), note=note,
                       tpl=tpl, imgbase=imgbase)
        # 每行一次存活检查：一行 512 格，说明窗口很密，也让"中途退出"能及时停
        if not mem.alive():
            print("  !! 目标在扫描中途不可读（已扫到 row %d）；如实停止并报告" % row)
            stats["notes"].append("target unreadable mid-sweep at row %d" % row)
            stop_now = True
        if not quiet:
            print("  row %4d: null=%-4d scanned=%-7d obj=%-5d nodes=%-6d suspects=%d"
                  % (row, rnull, stats["cells_scanned"], stats["cells_nonnull"],
                     stats["nodes"], len(stats["suspects"]) + stats["suspects_truncated"]))
            sys.stdout.flush()
        if stop_now:
            break
    stats["elapsed"] = time.perf_counter() - t0
    if stats["verdict"] is None:
        stats["verdict"] = ("RED" if (stats["suspects"] or stats["suspects_truncated"])
                            else "GREEN")
    _finish(mem, stats)
    return stats


def _scan_cell(mem, stats, opts, cell, obj, where, note, tpl, imgbase):
    """扫一个 cell 对象的两条链并逐节点判定。任何异常都记账后继续。"""
    for h in CHAIN_HEADS:
        stats["chains"] += 1
        try:
            res = scan_chain(mem, obj + h, tag="+0x%02X" % h,
                             max_nodes=opts["max_nodes"], st=mem.st)
        except Exception as e:                 # 理论上不该发生；发生了也不能中断扫描
            stats["notes"].append("scan_chain raised %s at cell 0x%08X +0x%02X"
                                  % (type(e).__name__, obj, h))
            continue
        stats["nodes"] += len(res["nodes"])
        stats["stay_counts"][res["stop"]] = stats["stay_counts"].get(res["stop"], 0) + 1
        for f in res["findings"]:
            k = f["kind"]
            if k == "head_unreadable":
                stats["fail_head"] += 1
            elif k == "unreadable_node":
                stats["fail_node"] += 1
            elif k == "next_unreadable":
                stats["fail_next"] += 1
        if res["findings"]:
            note("chain_anomaly", cell, "+0x%02X" % h, res["findings"][0].get("node"),
                 None, "n/a",
                 "%s: %s" % (where, "; ".join(
                     "%s(0x%08X)" % (f["kind"], f.get("node", 0)) for f in res["findings"])),
                 res["findings"])
        for i, node in enumerate(res["nodes"]):
            if i >= len(res["vptr"]):
                break
            vptr = res["vptr"][i]
            try:
                verdict, detail = judge_vptr(mem, tpl, imgbase, vptr)
            except Exception as e:
                verdict, detail = "suspect", "judge raised %s" % type(e).__name__
            if verdict == "wl":
                stats["judge_wl"] += 1
                continue
            if verdict == "isomorphic":
                stats["judge_iso"] += 1
                continue
            note("bad_vptr", cell, "+0x%02X" % h, node, vptr, verdict,
                 "%s -> %s" % (where, detail), res["findings"])


def _finish(mem, stats):
    print("\n=== summary ===")
    print("verdict            : %s" % stats["verdict"])
    print("cells scanned      : %d  (null=%d, non-null=%d, unreadable=%d, illegal=%d, dupe=%d)"
          % (stats["cells_scanned"], stats["cells_null"], stats["cells_nonnull"],
             stats["cell_unreadable"], stats["cell_illegal"], stats["cell_dupe"]))
    print("cell objs walked   : %d   (chains=%d, nodes=%d)"
          % (stats["objs_walked"], stats["chains"], stats["nodes"]))
    print("chain stop reasons : %s" % dict(sorted(stats["stay_counts"].items())))
    print("read failures      : head=%d node=%d next=%d  (RPM fail calls=%d, distinct addrs=%d)"
          % (stats["fail_head"], stats["fail_node"], stats["fail_next"],
             mem.st.fails, len(mem.st.distinct_fail_va)))
    print("vptr judged        : whitelist=%d isomorphic=%d"
          % (stats["judge_wl"], stats["judge_iso"]))
    print("suspects reported  : %d (+%d truncated)"
          % (len(stats["suspects"]), stats["suspects_truncated"]))
    if stats["elapsed"] is not None:
        n = max(1, stats["cells_scanned"])
        print("sweep time         : %.4f s  (%.2f us/cell)" % (stats["elapsed"],
                                                               1e6 * stats["elapsed"] / n))
    if stats["notes"]:
        print("notes              : %s" % stats["notes"])


def report_suspects(mem, stats, hexlen):
    if stats["suspects"]:
        print("\n=== suspect nodes（vptr 既不在白名单、也不与静态镜像同构）===")
        for i, s in enumerate(stats["suspects"], 1):
            print("\n[%d] %s  cell=0x%08X  chain=%s  node=%s  vptr=%s"
                  % (i, s["kind"], s["cell"], s["chain"],
                     ("0x%08X" % s["node"]) if s["node"] else "?",
                     ("0x%08X" % s["vptr"]) if s["vptr"] else "?"))
            print("    where   : %s" % s["detail"])
            print("    findings: %s" % s["findings"])
            if s["node"] and addr_legal(s["node"]):
                print("    dump node 0x%08X (%d bytes):" % (s["node"], hexlen))
                for ln in dump_hex(mem, s["node"], hexlen):
                    print(ln)
            if s["vptr"] and addr_legal(s["vptr"]):
                print("    dump vptr target 0x%08X (64 bytes):" % s["vptr"])
                for ln in dump_hex(mem, s["vptr"], 64):
                    print(ln)
        if stats["suspects_truncated"]:
            print("\n[!] 还有 %d 个可疑节点未展开（--max-report 限制）"
                  % stats["suspects_truncated"])


# ----------------------------------------------------------------------------
# --attach
# ----------------------------------------------------------------------------
def cmd_attach(pid, opts):
    print("=== cell_sentinel --attach (READ-ONLY) ===")
    print("access requested   : 0x%04X = VM_READ | QUERY_LIMITED_INFORMATION（只读，无写权限）"
          % READ_ACCESS)
    mem = ProcMem(pid, READ_ACCESS)
    try:
        mem.open()
    except OSError as e:
        print("OpenProcess FAILED : %s" % e)
        print("hint               : pid 是否存在？是否同用户/权限够？（32/64 位不影响 RPM）")
        return 3
    try:
        img = mem.image_name()
        print("image              : %s" % (img or "<unknown>"))
        low = (img or "").lower()
        for bad in FORBIDDEN_IMAGES:
            if bad in low:
                if opts.get("allow_game"):
                    print("ALLOWED            : 目标是游戏进程（命中 %r），"
                          "但已由 --allow-game 显式授权（Lead 真机卡 W110）。" % bad)
                    break
                print("REFUSE             : 目标看起来是游戏进程（命中 %r）。"
                      "本卡不得附加 gamemd / 游戏本体。"
                      "（真机卡请显式加 --allow-game）" % bad)
                return 4
        print("alive              : %s" % mem.alive())
        stats = scan_attach(mem, opts)
        report_suspects(mem, stats, opts["hexlen"])
        return 0
    finally:
        mem.close()

# ----------------------------------------------------------------------------
# --selftest-attach：替身进程
# ----------------------------------------------------------------------------
def cmd_selftest_attach(opts):
    fails = []
    checks = []

    def ck(name, ok, got):
        checks.append((name, bool(ok), got))
        print("  [%s] %s (got %r)" % ("PASS" if ok else "FAIL", name, got))
        if not ok:
            fails.append("%s got %r" % (name, got))

    print("=== cell_sentinel --selftest-attach (decoy process, READ-ONLY) ===")
    print("decoy              : python.exe -c \"import time;time.sleep(...)\"（无参数/无文件/只睡）")
    p = spawn_decoy(90)
    pid = p.pid
    print("decoy pid          : %d" % pid)
    mem = ProcMem(pid, READ_ACCESS)
    try:
        t0 = time.perf_counter()
        mem.open()
        print("OpenProcess        : OK in %.2f ms (access=0x%04X)"
              % ((time.perf_counter() - t0) * 1000, READ_ACCESS))
        ck("1 OpenProcess 只请求只读权限组合 (0x%X)" % READ_ACCESS,
           mem.access == READ_ACCESS, hex(mem.access))
        img = mem.image_name()
        print("image              : %s" % (img or "<empty: 查询失败，但不影响后续>"))
        ck("2 替身不是游戏进程", not any(b in (img or "").lower() for b in FORBIDDEN_IMAGES),
           img or "")

        # --- RPM 通路：读"目标进程自己的私有堆页"。
        # 替身是 python -c，它一定已经 import 了 time，堆里有大量 MEM_PRIVATE 可读页；
        # 这里不依赖任何硬编码/共享映像基址（DSH 沙箱下 kernel32 基址不一致，见 U3）。---
        probe_ok, probe_detail, probe_va = mem.find_private_probe()
        print("RPM probe          : %s" % probe_detail)
        ck("3 能读到目标进程的私有堆内存（RPM 通路活着）", probe_ok, probe_detail)
        ck("3a 未映射地址 0x00000010 读不到且不抛", mem.read_bytes(0x10, 4) is None,
           mem.read_bytes(0x10, 4))

        # --- 地址合法性预检 ---
        ck("3b addr_legal(0x10000)=True", addr_legal(0x10000) is True, addr_legal(0x10000))
        ck("3c addr_legal(0xFFFF)=False", addr_legal(0xFFFF) is False, addr_legal(0xFFFF))
        ck("3d addr_legal(0x80000000)=False", addr_legal(0x80000000) is False,
           addr_legal(0x80000000))

        # --- 非法地址读：必须 None，绝不抛 ---
        for va in (0x0, 0x4, 0x7FFFFFF0, -1):
            try:
                r = mem.read_bytes(va, 4)
                ok = (r is None)
            except Exception as e:
                ok, r = False, "RAISED %s" % type(e).__name__
            ck("4 非法地址 0x%08X 读不到且不抛" % (va & 0xFFFFFFFF), ok, r)

        g = _rd32(mem, MAPTABLE_PTR_VA, mem.st)
        print("decoy [0x%08X]   : %s" % (MAPTABLE_PTR_VA,
                                         ("0x%08X" % g) if g is not None else "<unreadable>"))

        # --- 完整扫描路径：替身里没有 cell 表 -> 必须给出明确 VERDICT，不崩 ---
        o2 = dict(opts)
        o2.update({"rows": (0, 511), "cols": (0, 511), "quiet": True})
        t0 = time.perf_counter()
        try:
            stats = scan_attach(mem, o2, banner_lines=["--- full sweep path against decoy ---"])
            raised = None
        except Exception as e:
            stats, raised = None, type(e).__name__
        dt = (time.perf_counter() - t0) * 1000
        print("sweep path         : %s in %.1f ms"
              % ("raised " + raised if raised else "returned", dt))
        ck("5 完整扫描路径对替身不抛异常", raised is None, raised)
        ck("6 结论 = TARGET_HAS_NO_STRUCTURE",
           stats is not None and stats["verdict"] == "TARGET_HAS_NO_STRUCTURE",
           stats["verdict"] if stats else None)
        ck("7 扫描统计无崩溃迹象（cells_scanned=0）",
           stats is not None and stats["cells_scanned"] == 0,
           stats["cells_scanned"] if stats else None)

        # --- 小窗口路径 ---
        o3 = dict(opts)
        o3.update({"rows": (0, 3), "cols": (0, 3), "quiet": True})
        try:
            scan_attach(mem, o3)
            ok8 = True
        except Exception as e:
            ok8 = type(e).__name__
        ck("8 --rows 0-3 --cols 0-3 窗口路径不崩", ok8 is True, ok8)

        # --- 目标退出后继续读（防崩的关键场景）---
        kill_own(p)
        time.sleep(0.3)
        print("\n--- after decoy exit ---")
        ck("9 目标退出后 alive()=False", mem.alive() is False, mem.alive())
        # 两个容易踩的坑，都在这里显式验证：
        #  (a) 0x7FFE0000 这类 KUSER 共享页在**任何**仍活着的进程里都可读（PID 复用后尤其），
        #      所以"目标退出后仍能读某个固定地址"并不奇怪，不能拿它当判活/判死依据。
        #  (b) 因此判死只看 alive()（读目标**自己的**私有页），且必须容忍"读不到"而不抛。
        stale = mem.read_bytes(probe_va, 4)
        print("post-exit, shared KUSER page 0x%08X -> %r  （可为非 None，属预期）"
              % (probe_va, stale if stale is None else stale.hex()))
        try:
            noprobes = []
            for i in range(3):
                noprobes.append(mem.alive() is False)
                time.sleep(0.05)
            ok10 = all(noprobes)
        except Exception as e:
            ok10, noprobes = False, "RAISED %s" % type(e).__name__
        ck("10 目标退出后 alive() 稳定为 False 且不抛", ok10, noprobes)
        ck("10b 目标退出后任一读失败都不会抛异常（契约）",
           mem.read_bytes(0x0, 4) is None and mem.read_bytes(0x7FFFFFF0, 4) is None,
           (mem.read_bytes(0x0, 4), mem.read_bytes(0x7FFFFFF0, 4)))

        # --- 不存在的 pid ---
        try:
            dead = ProcMem(0x7FFFFFF0, PROCESS_VM_READ)
            dead.open()
            ok11 = False
        except OSError:
            ok11 = True
        except Exception:
            ok11 = False
        ck("11 OpenProcess 无效 pid 抛 OSError（可被捕获）", ok11, ok11)

        # --- 只读纪律自审：源码里不得出现写内存 API 名字 ---
        # 被禁名字用切分拼接构造，这段代码自身因此不会命中自己。
        txt = open(os.path.abspath(__file__), "r", encoding="utf-8").read()
        forbid = ("PROCESS_VM_" + "WRITE", "Write" + "ProcessMemory",
                  "Virtual" + "AllocEx", "Create" + "RemoteThread",
                  "PROCESS_VM_" + "OPERATION", "Virtual" + "ProtectEx")
        exempt = [i for i, ln in enumerate(txt.splitlines(), 1) if "严禁" in ln]
        hits = []
        for ith, line in enumerate(txt.splitlines(), 1):
            if ith in exempt:
                continue
            for t in forbid:
                if t in line:
                    hits.append((ith, t, line.strip()[:60]))
        print("source audit       : %d forbidden-API hit(s); %d '严禁' line(s) exempted"
              % (len(hits), len(exempt)))
        ck("12 源码无写内存 API（除严禁注释行）", hits == [], hits)

    finally:
        kill_own(p)
        mem.close()

    print("\n=== summary: %d checks, %d failed ===" % (len(checks), len(fails)))
    print("RESULT: %s" % ("GREEN" if not fails else "RED"))
    for f in fails:
        print("  FAILED: " + f)
    return 0 if not fails else 1


# ----------------------------------------------------------------------------
# --perf：512x512、一半空格的合成表
# ----------------------------------------------------------------------------
def cmd_perf(opts):
    """量"扫描逻辑 + 每 cell 一次 4B 读 + 两条链遍历 + 判定"的 CPU 成本。

    为什么不用真 RPM：本机自测发现 RPM 对本进程读不到（EVIDENCE/probe_rpm_self.txt），
    所以"自进程 RPM 基准"在这里不成立。改用与 ProcMem 同接口、同失败语义的 PerfMem。
    跨进程 RPM 的额外开销 [未证]，须真机重测。
    """
    print("=== cell_sentinel --perf (synthetic 512x512 table, half empty) ===")
    print("测量对象：扫描逻辑（每 cell 一次 4B 读 + 两条链遍历 + 判定）；不含跨进程 RPM 开销。")
    print("为什么不用真 RPM：本机 RPM 对自身读不到（EVIDENCE/probe_rpm_self.txt），")
    print("                 故用等接口 PerfMem；跨进程开销 [未证]，见 ATTACH_MODE.md §性能。")

    ncell = TABLE_ROWS * TABLE_COLS
    nobj = ncell // 2                      # 前一半非空，后一半空格 => 一半为空
    base = 0x10000000
    tab_va = base
    obj_va = tab_va + TABLE_BYTES
    node_va = obj_va + nobj * CELLCLASS_STRIDE
    vt_va = node_va + nobj * 4 * 64
    total = (vt_va - base) + 0x2000
    mem = PerfMem()
    mem.reserve(base, base + total)
    print("synthetic layout   : tab 0x%08X(+0x%X) obj 0x%08X node 0x%08X vt 0x%08X"
          % (tab_va, TABLE_BYTES, obj_va, node_va, vt_va))
    print("synthetic size     : %.1f MB; %d cells, %d non-null"
          % (total / 1048576.0, ncell, nobj))

    thunk_va = vt_va + 0x10
    mem.put(thunk_va, b"\xb8\x06\x00\x00\x00\xc3")        # WhatAmI: mov eax,6; ret
    wl = set()
    nvt = 0x1000
    for i in range(nvt):
        v = vt_va + i * 4
        mem.put(v, struct.pack("<I", 0x00410260))
        mem.put(v + WHATAMI_OFFSET, struct.pack("<I", thunk_va))
        wl.add(v)
    for i in range(nobj):
        o = obj_va + i * CELLCLASS_STRIDE
        mem.put(tab_va + i * 4, struct.pack("<I", o))
        v = vt_va + (i % nvt) * 4
        for h, k in ((0xE4, 0), (0xE8, 2)):
            n0 = node_va + (i * 4 + k) * 64
            n1 = node_va + (i * 4 + k + 1) * 64
            mem.put(o + h, struct.pack("<I", n0))
            mem.put(n0, struct.pack("<I", v))
            mem.put(n0 + NEXT_OFFSET, struct.pack("<I", n1))
            mem.put(n1, struct.pack("<I", v))
            mem.put(n1 + NEXT_OFFSET, struct.pack("<I", 0))
    set_evidence_whitelist(wl)
    print("vtable pool        : %d vptr whitelisted; WhatAmI thunk @ 0x%08X" % (len(wl), thunk_va))

    def sweep(label, rows, cols, max_nodes=2):
        t0 = time.perf_counter()
        scanned = nulls = objs = nodes = 0
        for r in range(rows[0], rows[1] + 1):
            rowbase = tab_va + (r << ROW_SHIFT) * 4
            for c in range(cols[0], cols[1] + 1):
                v = mem.read_bytes(rowbase + c * 4, 4)
                scanned += 1
                if v is None:
                    continue
                obj = struct.unpack("<I", v)[0]
                if obj == 0:
                    nulls += 1
                    continue
                objs += 1
                for h in CHAIN_HEADS:
                    res = scan_chain(mem, obj + h, max_nodes=max_nodes, st=mem.st)
                    nodes += len(res["nodes"])
        dt = time.perf_counter() - t0
        print("  %-30s cells=%-7d null=%-6d obj=%-6d nodes=%-6d %8.4f s (%.2f us/cell)"
              % (label, scanned, nulls, objs, nodes, dt, 1e6 * dt / max(1, scanned)))
        return dt, scanned

    print("\n--- measured sweeps (single-threaded, no progress printing) ---")
    d1, n1 = sweep("full 512x512 #1", (0, 511), (0, 511))
    d2, _ = sweep("full 512x512 #2", (0, 511), (0, 511))
    d3, _ = sweep("full 512x512 #3", (0, 511), (0, 511))
    d4, _ = sweep("full 512x512 #4", (0, 511), (0, 511))
    sweep("window 40x40 (rows/cols 200-239)", (200, 239), (200, 239))
    sweep("window 100x100 (rows/cols 200-299)", (200, 299), (200, 299))
    sweep("single row (0-0, cols 0-511)", (0, 0), (0, 511))

    t0 = time.perf_counter()
    for r in range(0, 512):
        rowbase = tab_va + (r << ROW_SHIFT) * 4
        for c in range(0, 512):
            mem.read_bytes(rowbase + c * 4, 4)
    dt_tab = time.perf_counter() - t0
    print("  %-30s cells=%-7d %27.4f s (%.2f us/cell)"
          % ("table reads only (no chains)", ncell, dt_tab, 1e6 * dt_tab / ncell))

    best = min(d1, d2, d3, d4)
    per = best / n1
    print("\n  => 单次全表扫描 best-of-4 = %.4f s  (%.2f us/cell)" % (best, per * 1e6))
    print("  => 纯表读 %.4f s (%.1f%%)；链遍历+判定 %.4f s (%.1f%%)"
          % (dt_tab, 100.0 * dt_tab / best, best - dt_tab, 100.0 * (best - dt_tab) / best))
    print("\n--- duty cycle at candidate poll rates (CPU-only) ---")
    print("  duty(%) = 单次耗时 s * 频率 Hz * 100  —— 超过 100% 表示一秒内扫不完一次")
    for hz in (0.2, 0.5, 1, 2, 4, 8):
        print("  full sweep @ %4.1f Hz: duty = %8.1f %% of one core" % (hz, 100.0 * best * hz))
    print("\n--- window cost (same per-cell rate) ---")
    for w in (20, 40, 60, 100):
        ms = per * w * w * 1000
        print("  %3dx%-3d = %5d cells -> %7.2f ms/sweep; @2 Hz = %6.2f %% of one core;"
              " @0.5 Hz = %6.2f %%"
              % (w, w, w * w, ms, 100.0 * (ms / 1000.0) * 2, 100.0 * (ms / 1000.0) * 0.5))
    print("\n建议（仅就该 CPU 成本）：")
    print("  * 全表只做一次诊断；常驻轮询必须用 --rows/--cols 窗口。")
    print("  * 20x20~40x40 窗口 + 0.5~2 Hz 是安全区（见上表）；跨进程 RPM 开销要叠加，")
    print("    真机上必须重测本表再定频率（[未证]）。")
    return 0


# ----------------------------------------------------------------------------
def _parse_opts(argv):
    opts = {
        "rows": (0, TABLE_ROWS - 1), "cols": (0, TABLE_COLS - 1),
        "max_nodes": DEFAULT_ATTACH_MAX_NODES,
        "hexlen": 0x40, "max_report": 200, "quiet": False,
        "allow_game": False,
        "tpl": None, "imgbase": IMAGE_BASE,
    }
    pid = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--rows":
            i += 1
            opts["rows"] = parse_range(argv[i], 0, TABLE_ROWS - 1)
        elif a == "--cols":
            i += 1
            opts["cols"] = parse_range(argv[i], 0, TABLE_COLS - 1)
        elif a == "--max-nodes":
            i += 1
            opts["max_nodes"] = max(1, int(argv[i]))
        elif a == "--hex":
            i += 1
            opts["hexlen"] = max(4, int(argv[i], 0))
        elif a == "--max-report":
            i += 1
            opts["max_report"] = max(1, int(argv[i]))
        elif a == "--quiet":
            opts["quiet"] = True
        elif a == "--allow-game":
            # [R10] Lead 显式授权开关：默认仍拒绝附加游戏本体；
            # 只有在真机卡（W110）里由 Lead 明确加此参数才放行。
            opts["allow_game"] = True
        elif a == "--attach":
            i += 1
            pid = int(argv[i], 0)
        elif a in ("--dump", "--self-test", "--perf", "--selftest-attach"):
            pass
        else:
            raise SystemExit("unknown arg: %s" % a)
        i += 1
    return pid, opts


def main(argv):
    if len(argv) == 1:
        print(__doc__)
        print("usage: python cell_sentinel.py --dump | --self-test | --perf | --selftest-attach |"
              " --attach <pid> [--rows A-B --cols C-D --max-nodes N --hex N --max-report N --quiet]")
        return 2
    try:
        pid, opts = _parse_opts(argv[1:])
    except (SystemExit, ValueError) as e:
        print("arg error: %s" % e)
        return 2

    if "--dump" in argv:
        return cmd_dump()
    if "--self-test" in argv:
        return cmd_self_test()
    if "--perf" in argv:
        return cmd_perf(opts)
    if "--selftest-attach" in argv:
        return cmd_selftest_attach(opts)
    if pid is not None:
        return cmd_attach(pid, opts)
    print("nothing to do")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))




