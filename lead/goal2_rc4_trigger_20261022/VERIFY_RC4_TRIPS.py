#!/usr/bin/env python
"""RC-4 三趟一致性核验：多份 minidump 的帧链是否逐环相同。

★ 目的
  单份 dump 通过验证 ≠ 结论稳定。必须证明**多次独立复现**得到同一条链，
  且时间量（关窗→崩溃）落在同一区间，才能把「必然触发」与「偶发」分开。

★ 判据
  T1  至少 3 趟独立复现（不同 pid、不同 dump 文件）
  T2  每趟 `Eip == 0x00724737` 且 `Access == 0x00000250`
  T3  每趟 dump 五环帧链全过（真实栈偏移，见 VERIFY_RC4_MINIDUMP.py 头注）
  T4  每趟 `singleton_at_hit == 0`（崩溃时全局已被清零）
  T5  「关窗 → 崩溃」时延的极差 < 1.0 s（同区间 ⇒ 确定性，非随机）
  T6  每趟的 dump 互不相同（sha256 去重后份数 == 趟数）

★ 用法
  python VERIFY_RC4_TRIPS.py
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead/goal2_rc4_trigger_20261022"
DUMP_DIR = Path(r"D:\ra2dumps")

RC4_EIP = 0x00724737
RC4_ACCESS = 0x00000250

# ★ 真实栈偏移（由全量搜索五环返回地址定谳，见 VERIFY_RC4_MINIDUMP.py 头注）
FRAMES = [
    (0x00920358, 0x00654418, "0x724730 ← 0x654413"),
    (0x00920388, 0x006403A8, "0x654320 ← 0x6403A3"),
    (0x009203AC, 0x006ABD3E, "0x6403A0 ← 0x6ABD39"),
    (0x009203E4, 0x004A8B18, "0x6ABD30 ← 0x4A8B13"),
    (0x0092043C, 0x00652D51, "0x4A8850 ← 0x652D4C"),
]
REAL_STACK = 0x00920300

CHECKS = []


def chk(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("  [%s] %-52s %s" % ("PASS" if ok else "FAIL", name, detail))


def load_dump(path: Path):
    """返回 (ranges, base_rva, reader)。reader(va, n) -> bytes|None。"""
    f = open(path, "rb")
    hdr = f.read(32)
    sig, ver, ns, dir_rva, ck, ts, flags = struct.unpack("<IIIIIIQ", hdr)
    if sig != 0x504D444D:
        f.close()
        raise ValueError("bad MDMP signature: %08X" % sig)
    f.seek(dir_rva)
    dirs = {}
    for _ in range(ns):
        t, sz, r = struct.unpack("<III", f.read(12))
        if t:
            dirs[t] = (sz, r)
    msz, mrva = dirs[9]
    f.seek(mrva)
    nr = struct.unpack("<Q", f.read(8))[0]
    base_rva = struct.unpack("<Q", f.read(8))[0]
    ranges = [struct.unpack("<QQ", f.read(16)) for _ in range(nr)]

    def reader(va, n):
        for start, rsize in ranges:
            if start <= va and va + n <= start + rsize:
                f.seek(base_rva + (va - ranges[0][0]))
                return f.read(n)
        return None

    return ranges, base_rva, reader, f


def main() -> int:
    print("=" * 78)
    print("RC-4 三趟一致性核验")
    print("=" * 78)

    # ---- 汇总所有 debugger 版趟记录 ----
    trips = []
    for jf in sorted(CARD.glob("PROBE_DBG_*.json")):
        d = json.loads(jf.read_text(encoding="utf-8"))
        for r in d.get("trips", []):
            if r.get("rc4_hit"):
                trips.append((jf.name, r))
    print("发现 %d 条 debugger 版命中记录" % len(trips))
    if not trips:
        print("!! 无记录，无法核验")
        return 2

    # ---- T1 ----
    pids = [r.get("pid") for _, r in trips]
    chk("T1 至少 3 趟独立复现（不同 pid）",
        len(trips) >= 3 and len(set(pids)) == len(pids),
        "%d 趟, pids=%s" % (len(trips), pids))

    # ---- T2 ----
    ok2 = True
    for jf, r in trips:
        h = r["rc4_hit"]
        acc = h["info"][1] if len(h.get("info", [])) > 1 else None
        good = (h["address"] == RC4_EIP and acc == RC4_ACCESS)
        ok2 &= good
        print("      %-28s Eip=%08X Access=%s %s"
              % (jf, h["address"],
                 ("%08X" % acc) if acc is not None else "None",
                 "OK" if good else "MISMATCH"))
    chk("T2 每趟 Eip==0x724737 且 Access==0x250", ok2)

    # ---- T3 ----
    ok3 = True
    for jf, r in trips:
        md = r.get("minidump") or {}
        if not md.get("ok"):
            chk("T3 %s dump 可读" % jf, False, "no dump")
            ok3 = False
            continue
        dp = Path(md["path"])
        try:
            ranges, base_rva, reader, fh = load_dump(dp)
        except Exception as e:      # noqa: BLE001
            chk("T3 %s dump 可读" % jf, False, repr(e))
            ok3 = False
            continue
        try:
            got = []
            allok = True
            for va, want, lbl in FRAMES:
                raw = reader(va, 4)
                v = struct.unpack("<I", raw)[0] if raw else None
                got.append(v)
                allok &= (v == want)
            ok3 &= allok
            print("      %-28s chain=%s %s"
                  % (jf, ["%08X" % g if g is not None else "NONE"
                          for g in got],
                     "OK" if allok else "MISMATCH"))
        finally:
            fh.close()
    chk("T3 每趟 dump 五环帧链全过", ok3)

    # ---- T4 ----
    ok4 = all(r["rc4_hit"].get("singleton_at_hit") == 0 for _, r in trips)
    chk("T4 每趟崩溃时 singleton == 0", ok4,
        "values=%s" % [r["rc4_hit"].get("singleton_at_hit")
                       for _, r in trips])

    # ---- T5 ----
    delays = [r["rc4_hit"].get("since_close_s") for _, r in trips
              if r["rc4_hit"].get("since_close_s") is not None]
    if len(delays) >= 2:
        spread = max(delays) - min(delays)
        chk("T5 关窗→崩溃时延极差 < 1.0 s", spread < 1.0,
            "delays=%s spread=%.3f"
            % ([round(x, 3) for x in delays], spread))
    else:
        chk("T5 关窗→崩溃时延极差 < 1.0 s", False, "样本不足")

    # ---- T6 ----
    shas = [((r.get("minidump") or {}).get("sha256")) for _, r in trips]
    chk("T6 dump 去重后份数 == 趟数（每趟不同进程）",
        len(set(s for s in shas if s)) == len([s for s in shas if s]),
        "%d 份, %d 唯一" % (len(shas), len(set(s for s in shas if s))))

    print()
    n = len(CHECKS)
    ok = sum(1 for _, v, _ in CHECKS if v)
    print("-" * 78)
    print("结果：%d/%d PASS" % (ok, n))
    if ok != n:
        for name, v, d in CHECKS:
            if not v:
                print("  FAIL:", name, d)
        return 1
    print("判定：CONFIRMED —— RC-4 是关窗后的确定性事件，非概率事件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
