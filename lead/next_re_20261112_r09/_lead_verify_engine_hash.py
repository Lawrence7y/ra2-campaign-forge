#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 亲验：引擎哈希 0x4A1DE0 的尾块处理方式，能否复现五个零售 id。

背景：W101 声称 `engine_hash("ARTMD.INI") = 0x5B47D8D5` 等五个 id 全中，
并据此断言「名字从未被改，此前是哈希算法用错」。
这条如果成立，就推翻 Lead 自己记的「引擎按 0xAF902833 取不到 ARTMD.INI」。
本项目已多次因"转述当真"翻车，故 Lead 亲算。

方法：CRC-32（zlib 表）。引擎的每 4 字节块做 `not → 4 表步 → not`，
等价于把寄存器保持在取反态连续推进 ⇒ 前 n//4*4 字节的等价形态就是 zlib crc32(prefix)。
真正未知的是**尾块（len%4 个残留字节）怎么处理**。本脚本枚举 6 种体面候选。
"""
from __future__ import annotations

import zlib

MODES = ["stream", "stage_only", "pad_nul", "pad_first", "pad_count", "pad_count_then_b"]

TARGETS = {
    "ARTMD.INI": 0x5B47D8D5,
    "RULESMD.INI": 0x8218F9F4,
    "LOCALMD.MIX": 0xFBE0D09D,
    "LOCAL.MIX": 0xA8548FD9,
    "ART.INI": 0xF91B2C8B,
}


def h(b: bytes) -> int:
    return zlib.crc32(b) & 0xFFFFFFFF


def modes(name: str) -> dict:
    b = name.encode("ascii")
    n = len(b)
    full = (n // 4) * 4
    pre, left = b[:full], b[full:]
    out = {"stream": h(b), "stage_only": h(pre)}
    if not left:
        for k in MODES[2:]:
            out[k] = h(pre)
        return out
    k = len(left)
    out["pad_nul"] = h(pre + left + b"\x00" * (4 - k))
    out["pad_first"] = h(pre + left + left[0:1] * (4 - k))
    out["pad_count"] = h(pre + left + bytes([k]) * (4 - k))
    out["pad_count_then_b"] = h(pre + left + bytes([k]) + b[: 3 - k])
    return out


def main():
    print(f"{'name':<14}{'len':>4}  " + "  ".join(f"{m:>18}" for m in MODES) + "     TARGET")
    hits = {}
    for nm, tg in TARGETS.items():
        m = modes(nm)
        print(f"{nm:<14}{len(nm):>4}  " + "  ".join(f"{m[k]:>18X}" for k in MODES) + f"   {tg:08X}")
        for k, v in m.items():
            if v == tg:
                hits.setdefault(k, []).append(nm)
    print()
    print("== 每种模式命中数 ==")
    for k in MODES:
        got = hits.get(k, [])
        print(f"  {k:<18} {len(got)}/5  {got if got else ''}")
    best = max(MODES, key=lambda k: len(hits.get(k, [])))
    print(f"\n最佳模式 = {best}  命中 {len(hits.get(best, []))}/5")

    print("\n== 对照：ra2forge mixlib 用的 crc32(UPPER(name)) ==")
    for nm in TARGETS:
        print(f"  {nm:<14} mixlib={zlib.crc32(nm.upper().encode('ascii')) & 0xFFFFFFFF:08X}"
              f"   引擎({best})={modes(nm)[best]:08X}   目标={TARGETS[nm]:08X}")

    print("\n== 补充：若干常见名字在最佳模式下的值 ==")
    for nm in ["ARTMD.INI", "RULESMD.INI", "ART.INI", "RULES.INI", "RA2MD.INI",
               "BATTLEMD.INI", "ISOTEMMD.MIX", "TEMPERAT.MIX", "GENERIC.MIX",
               "RA2.MIX", "RA2MD.MIX", "EXPANDMD98.MIX", "LANGMD.MIX", "MULTIMD.MIX"]:
        print(f"  {nm:<16} {modes(nm)[best]:08X}")


if __name__ == "__main__":
    main()
