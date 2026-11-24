#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W111 只读 vptr 哨兵（Lead 亲执真机用）。

与 W109 版本的差别（都是修 W110 暴露出来的错）：
  1. **等进图门**：先轮询 `[0x87F924]` 直到非 0，再等窗口内出现"首 dword 是合法虚表"的链头，
     才开始计时。W110 首轮全程 `global unreadable` 就是因为表还是 0（地图未加载）。
  2. **白名单 = RTTI 反查出的 1,305 个虚表起点**（`_lead_rtti_map.json` 的 vt2name 键），
     不再用"游程候选 + 逐字节同构"启发式。
  3. **不扫静态槽**：`0x0089C2E0` / `0x00ABDC50` 已证是**静态 CellClass 对象**（`0xABDC50`
     首 dword = `0x7E4EEC` = CellClass 虚表），不是"存 cell 指针的槽"。
  4. **自动发现监控集**：不依赖设计文件坐标（W110 发现设计里的 56/46 不是引擎格坐标）。

只读纪律：OpenProcess 只要 VM_READ | QUERY_LIMITED_INFORMATION；无任何写 API。

用法：
  python w111_vptr_watch.py <pid> --discover            # 一次性盘点 + 计时
  python w111_vptr_watch.py <pid> --watch --secs 180    # 等进图后持续监控
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import json
import struct
import sys
import time
from pathlib import Path

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TABLE_GLOBAL = 0x0087F924
ROWS = COLS = 512
CELL_A, CELL_B, NODE_NEXT, WHATAMI = 0xE4, 0xE8, 0x30, 0x2C
RDATA_LO, RDATA_HI = 0x7E1000, 0x812000
MAX_NODES = 64     # §647-10 单链上限，防死循环/自环

RTTI_JSON = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, wt.LPCVOID, wt.LPVOID,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype = wt.BOOL
k32.CloseHandle.argtypes = [wt.HANDLE]


class Mem:
    def __init__(self, pid):
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not self.h:
            raise OSError("OpenProcess failed err=%d" % ctypes.get_last_error())
        self.fails = 0

    def rd(self, va, n):
        b = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        ok = k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), b, n, ctypes.byref(got))
        if not ok or got.value != n:
            self.fails += 1
            return None
        return b.raw[:n]

    def u32(self, va):
        b = self.rd(va, 4)
        return None if b is None else int.from_bytes(b, "little")

    def close(self):
        k32.CloseHandle(self.h)


def load_whitelist():
    d = json.loads(RTTI_JSON.read_text(encoding="utf-8"))
    vt = {int(k, 16) for k in d["vt2name"]}
    return vt


def table_base(mem):
    return mem.u32(TABLE_GLOBAL)


def discover(mem, vt_ok):
    tbl = table_base(mem)
    t0 = time.perf_counter()
    blob = mem.rd(tbl, ROWS * COLS * 4) if tbl else None
    t_read = time.perf_counter() - t0
    if not blob:
        return None, "table ptr unreadable (mission not loaded?)"
    entries = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
    nonnull = [(i, v) for i, v in enumerate(entries) if v]
    t1 = time.perf_counter()
    heads = []      # (idx, cell, off, head, vptr)
    invalid = []    # (idx, cell, off, head, vptr)
    for i, cell in nonnull:
        for off in (CELL_A, CELL_B):
            h = mem.u32(cell + off)
            if not h or h < 0x10000:
                continue
            v = mem.u32(h)
            rec = (i, cell, off, h, v)
            (heads if (v and v in vt_ok) else invalid).append(rec)
    t_walk = time.perf_counter() - t1
    return dict(tbl=tbl, t_read=t_read, t_walk=t_walk, nonnull=len(nonnull),
                heads=heads, invalid=invalid), None


def cmd_discover(mem, vt_ok):
    d, err = discover(mem, vt_ok)
    if err:
        print("DISCOVER FAIL:", err)
        return 1
    print("table            : 0x%08X" % d["tbl"])
    print("bulk read 1MB    : %.1f ms" % (d["t_read"] * 1000))
    print("non-null cells   : %d" % d["nonnull"])
    print("walk (all cells) : %.1f ms   (RPM fails=%d)" % (d["t_walk"] * 1000, mem.fails))
    print("chain heads with RTTI-valid vptr : %d" % len(d["heads"]))
    print("chain heads with INVALID vptr    : %d" % len(d["invalid"]))
    if d["heads"]:
        rs = [i // COLS for i, *_ in d["heads"]]
        cs = [i % COLS for i, *_ in d["heads"]]
        print("  row range %d..%d   col range %d..%d" % (min(rs), max(rs), min(cs), max(cs)))
        import collections
        cnt = collections.Counter(v for *_, v in d["heads"])
        for v, c in cnt.most_common(8):
            print("    vptr=0x%08X  %4d cells" % (v, c))
    for rec in d["invalid"][:6]:
        i, cell, off, h, v = rec
        print("  INVALID idx=%d (r%d,c%d) cell=0x%08X off=+0x%02X head=0x%08X vptr=%s"
              % (i, i // COLS, i % COLS, cell, off, h, "FAIL" if v is None else "0x%08X" % v))
    return 0


def cmd_watch(mem, vt_ok, secs, quiet):
    print("=== 等进图（[0x87F924] != 0 且出现 RTTI 合法链头）===")
    t0 = time.time()
    d = None
    while time.time() - t0 < 120:
        d, err = discover(mem, vt_ok)
        if d and d["heads"]:
            print("进图确认 @ +%.1fs  table=0x%08X  heads=%d"
                  % (time.time() - t0, d["tbl"], len(d["heads"])))
            break
        d = None
        time.sleep(0.3)
    if not d:
        print("WAIT_FAIL: 120s 内未确认进图")
        return 2

    # 监控集 = 发现时所有非空链头（含 invalid，便于观察变化）
    watch = {}
    for i, cell, off, h, v in d["heads"] + d["invalid"]:
        watch[(cell, off)] = v
    print("监控集 %d 条链；开始计时 %ds" % (len(watch), secs))

    snap = {}          # node -> 上一次扫到的合法 vptr（用于"变化"判定）
    seen_bad = {}
    benign_total = [0]   # §648-6 benign events counted, not printed      # node -> 首次报出的理由（同一节点只报一次）
    tbl = d["tbl"]
    hits = 0
    n = 0
    nnodes_max = 0
    t_start = time.time()
    while time.time() - t_start < secs:
        n += 1
        scan_t0 = time.perf_counter()
        bad = []
        benign = []
        nnodes = 0
        # 先整表 bulk 读一次，拿 cell 指针是否被替换
        blob = mem.rd(tbl, ROWS * COLS * 4)
        if blob:
            entries = struct.unpack_from("<%dI" % (ROWS * COLS), blob, 0)
        for (cell, off), prev_v in list(watch.items()):
            h = mem.u32(cell + off)
            if h is None or h < 0x10000:
                benign.append((cell, off, prev_v, h, None, "head_gone/zero", 0, None))
                continue
            # §647-10：必须走完整条链。S9 崩溃点 0x47C4FD 遍历的是链上
            # **每一个** 节点，坏节点未必要是链头——只盯链头必然漏。
            seen, node, k, stop = set(), h, 0, False
            while node and node >= 0x10000 and k < MAX_NODES:
                if node in seen:
                    bad.append((cell, off, prev_v, h, None, "chain_cycle", k, None))
                    stop = True
                    break
                seen.add(node)
                k += 1
                nnodes += 1
                # 1 次 RPM 同时取 vptr(+0x00) 和 next(+0x30)，省一半系统调用
                nb = mem.rd(node, NODE_NEXT + 4)
                if not nb:
                    bad.append((cell, off, prev_v, h, None, "node_unreadable", k, None))
                    stop = True
                    break
                v = struct.unpack_from("<I", nb, 0)[0]
                nxt = struct.unpack_from("<I", nb, NODE_NEXT)[0]
                if v not in vt_ok:
                    old = snap[node] if node in snap else None
                    if node not in seen_bad:
                        # §647-4 的决定性验证：崩溃是 call [vptr+0x2C] 跳到 0。
                        # 在真机上直接读一次 [vptr+0x2C]，看它是不是 0。
                        probe = mem.u32(v + WHATAMI)
                        seen_bad[node] = "vptr_invalid"
                        bad.append((cell, off, prev_v, node, v, "vptr_invalid", k, old))
                    stop = True
                    break
                snap[node] = v
                if nxt and nxt < 0x10000:
                    # a null next is the normal chain terminator, not corruption
                    bad.append((cell, off, prev_v, node, v, "next_corrupt", k, nxt))
                    stop = True
                    break
                node = nxt
            if not stop and k >= MAX_NODES:
                bad.append((cell, off, prev_v, h, None, "chain_too_long", k, None))
        dt = (time.perf_counter() - scan_t0) * 1000
        # §648-6: head->0 is NORMAL gameplay (object left the cell). Logging every
        # occurrence wrote 14,748 junk lines in one run and buried the 2 real hits.
        # Count it, print only under W111_VERBOSE (and only the first sighting).
        benign_seen = globals().setdefault("_benign_seen", set())
        benign_total[0] += len(benign)
        if os.environ.get("W111_VERBOSE") == "1":
            for cell, off, pv, h, v, why, k, aux in benign[:2]:
                key = (cell, off)
                if key in benign_seen:
                    continue
                benign_seen.add(key)
                print("  [benign] %-15s cell=0x%08X +0x%02X node#%d" % (why, cell, off, k))
        if bad:
            hits += 1
            print("\n*** SCAN#%d  %d BAD @ %.3fs  (scan %.2f ms) ***"
                  % (n, len(bad), time.time() - t_start, dt))
            for cell, off, pv, h, v, why, k, aux in bad[:12]:
                if why in ("vptr_invalid",):
                    pr = mem.u32((v or 0) + WHATAMI)
                    print("   %-16s cell=0x%08X +0x%02X  node#%d=0x%08X  "
                          "vptr %s -> 0x%08X   [vptr+0x2C]=%s"
                          % (why, cell, off, k, h or 0,
                             "None(首扫未见)" if aux is None
                             else "0x%08X(合法)" % aux, v or 0,
                             "unreadable" if pr is None else "0x%08X" % pr))
                elif why == "next_corrupt":
                    print("   %-16s cell=0x%08X +0x%02X  node#%d=0x%08X  "
                          "vptr=0x%08X  next=0x%08X"
                          % (why, cell, off, k, h or 0, v or 0, aux or 0))
                else:
                    print("   %-16s cell=0x%08X +0x%02X  node#%d head=0x%08X vptr=%s"
                          % (why, cell, off, k, h or 0,
                             "FAIL" if v is None else "0x%08X" % v))
                nb = mem.rd(h, 0x40) if (h and h >= 0x10000) else None
                if nb:
                    print("      node dump: " + " ".join("%02x" % b for b in nb[:32]))
            sys.stdout.flush()
            if hits >= 3:
                print("已命中 3 次，停止")
                break
        elif not quiet and n % 25 == 0:
            print("  scan#%-5d %.1fs  chains=%d  nodes=%d  scan=%.2fms  benign=%d  rpm_fails=%d"
                  % (n, time.time() - t_start, len(watch), nnodes, dt, benign_total[0], mem.fails))
            sys.stdout.flush()
        # 若进程消失则退出
        if mem.u32(tbl) is None and mem.fails > 50:
            print("PROCESS_GONE 或表不可读 @ scan#%d" % n)
            break
        # §647-10: the old 20ms sleep was the real bottleneck behind 24 Hz
        # (a scan itself is only 11ms). The corruption window may be shorter
        # than tens of ms, so drop the sleep and gain an order of magnitude.
        time.sleep(0.0)
    print("\n=== 结束：%d 次扫描，%d 次命中 ===" % (n, hits))
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", type=int)
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--secs", type=float, default=180)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    vt_ok = load_whitelist()
    print("RTTI 白名单：%d 个虚表起点" % len(vt_ok))
    mem = Mem(a.pid)
    try:
        if a.discover:
            return cmd_discover(mem, vt_ok)
        if a.watch:
            return cmd_watch(mem, vt_ok, a.secs, a.quiet)
        print("需要 --discover 或 --watch")
        return 2
    finally:
        mem.close()


if __name__ == "__main__":
    raise SystemExit(main())
