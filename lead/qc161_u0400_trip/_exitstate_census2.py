#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""exitstate [0xA8EDD8] 写/读点普查 v2 —— 字节先决（capstone 补形），D-09-A 设计输入。

v1 用「op_str 含 0xa8edd8」的过滤器跑全 .text ⇒ 0 命中。0 命中对 2.7 MB 代码段
本身就是异常信号（[[census-zero-hits-positive-control]]）⇒ 改字节先决：
  1. 在 .text 原始字节里找 `D8 EE A8 00`（小端 VA）全部出现位置；
  2. **阳性对照**：同一装置在 singleton `68 73 88 00` 上必须有大量命中；
  3. 每个命中点回退 -12..+2 解码，判定「这条指令是不是引用该 VA 的」并分写/读；
  4. 输出指令级清单。
只读母本 gamemd.exe（sha 先验）。
"""
from __future__ import annotations

import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

GAME_SRC = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020")
GAMEMD = GAME_SRC / "gamemd.exe"
ADDR = 0x00A8EDD8
CTL_SINGLETON = 0x00887368
EXPECT_SHA16 = "73201cc021497c95"

WR_MNEMS = {"mov", "and", "or", "xor", "add", "sub", "inc", "dec", "xchg", "cmpxchg",
            "movaps", "movdqa", "bt", "bts", "btr", "btc"}
RD_ONLY_MNEMS = {"cmp", "test", "movzx", "movsx", "lea", "push"}


def parse_sections(path: Path):
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    sec = pe + 24 + opt
    image_base = struct.unpack_from("<I", data, pe + 52)[0]
    out = []
    for i in range(nsec):
        o = sec + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, va = struct.unpack_from("<II", data, o + 8)
        rawsize, rawoff = struct.unpack_from("<II", data, o + 16)
        out.append((name, data[rawoff:rawoff + rawsize], image_base + va, rawsize))
    return out


def classify(md, blob, hit_off, file_off):
    """命中点前后窗口解码，找**完整**指令 whose 编码字节含该 VA 字面。"""
    va_target = None
    # 从命中位置回退扫描各对齐起点，找一条结束于/跨过命中点的指令
    results = []
    for back in range(1, 16):
        start = hit_off - back
        if start < 0:
            continue
        for ins in md.disasm(blob[start:start + 32], 0):
            enc = ins.bytes
            j = blob.find(bytes(enc), start)
            if j != start:
                continue
            # 该指令字节里是否嵌 VA 小端
            le = struct.pack("<I", ADDR)
            if le in enc:
                m = ins.mnemonic
                ops = ins.op_str
                is_write = m in WR_MNEMS and ops.strip().startswith("dword ptr [")
                kind = "WRITE" if is_write else ("READ" if m in RD_ONLY_MNEMS else "AMBIG")
                results.append((back, m, ops, kind))
            break
    return results


def main() -> int:
    import hashlib
    if hashlib.sha256(GAMEMD.read_bytes()).hexdigest()[:16] != EXPECT_SHA16:
        raise SystemExit("母本 sha 不符，停")
    secs = parse_sections(GAMEMD)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    total = {}
    for name, blob, vaddr, size in secs:
        needle = struct.pack("<I", ADDR)
        ctl = struct.pack("<I", CTL_SINGLETON)
        n_hit = blob.count(needle)
        n_ctl = blob.count(ctl)
        if n_hit or n_ctl:
            total[name] = (n_hit, n_ctl)
    print("== 字面命中（阳性对照=singleton 计数）==")
    for k, (h, c) in total.items():
        print("  %-8s exitstate=%-4d singleton(对照)=%d" % (k, h, c))
    if not any(h for h, _ in total.values()):
        print("!! exitstate 零命中 ⇒ 该 VA 可能只被代码以非常规形式引用（rip 相对?不可能 32 位;或 EBP 基址）")
    # 详查 .text 每个命中点
    for name, blob, vaddr, size in secs:
        if name != ".text":
            continue
        needle = struct.pack("<I", ADDR)
        pos, hits = 0, []
        while True:
            i = blob.find(needle, pos)
            if i < 0:
                break
            hits.append(i)
            pos = i + 1
        print("== .text 命中 %d 点：逐点指令归因 ==" % len(hits))
        seen = set()
        for i in hits:
            for back, m, ops, kind in classify(md, blob, i, i):
                key = (vaddr + i - back, m)
                if key in seen:
                    continue
                seen.add(key)
                print("  %08X  %-6s %-38s [%s]" % (vaddr + i - back, m, ops, kind))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
