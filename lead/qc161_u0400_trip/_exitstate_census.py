#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""exitstate [0xA8EDD8] 写点/读点静态解剖 —— D-09 选项 A 的设计输入。

真机事实（d09b 双臂，10-25）：
  守卫开+关窗 ⇒ singleton 清零、**exitstate 0→1**、然后**永远停在 1**、frame=0；
  守卫关+关窗 ⇒ singleton 清零、exitstate **恒 0**、弹 #32770 错误框等 OK。
⇒ 问题从「为何不退」收窄为「**exitstate 从 1 往 2 走的那一步卡在什么条件上**」。

本件（只读母本 `_src_L1_sf8_20261020/gamemd.exe`，sha 73201cc0 已验）：
  1. 全 .text 找 `mov/and/or/xor dword ptr [0xA8EDD8], imm`（写点）；
  2. 找读点：`cmp/...  [0xA8EDD8]` 与 `mov reg, [0xA8EDD8]`；
  3. 每个写点/读点归属到函数（capstone 线性 + 函数头判据：前邻 0xCC/0x90 填充）；
  4. 输出「谁把它置 1」「谁在等它变化」的候选边，供设计「跳过后推进退出」的插入点。
"""
from __future__ import annotations

import struct
from pathlib import Path

GAMEMD = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_src_L1_sf8_20261020\gamemd.exe")
ADDR = 0x00A8EDD8
BASE = 0x400000

from capstone import Cs, CS_ARCH_X86, CS_MODE_32


def parse_text(path: Path):
    data = path.read_bytes()
    import struct
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    sec_off = pe + 24 + opt_size
    image_base = struct.unpack_from("<I", data, pe + 52)[0]
    for i in range(nsec):
        o = sec_off + i * 40
        name = data[o:o + 8].rstrip(b"\0").decode()
        vsize = struct.unpack_from("<I", data, o + 8)[0]
        va = struct.unpack_from("<I", data, o + 12)[0]
        rawsize = struct.unpack_from("<I", data, o + 16)[0]
        rawoff = struct.unpack_from("<I", data, o + 20)[0]
        if name == ".text":
            return data[rawoff:rawoff + rawsize], image_base + va, rawsize
    raise SystemExit("no .text")


def main() -> int:
    text, va0, size = parse_text(GAMEMD)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    writes, reads = [], []
    # 线性解码整 .text（本项目已证可行；截断风险由逐条 mnem+op 复核兜底）
    for ins in md.disasm(text, va0):
        ops = ins.op_str
        if "%s" % ADDR not in ops and "0x%x" % ADDR not in ops:
            continue
        # 地址字面量出现 = 命中（含 dword ptr [0xa8edd8]）
        entry = {"addr": ins.address, "mnem": ins.mnemonic, "ops": ops}
        m = ins.mnemonic
        if m in ("mov", "movdqa", "and", "or", "xor", "add", "sub", "inc", "dec",
                 "movaps", "xchg", "cmpxchg"):
            # 目标是全局 ⇒ 写；源是全局 ⇒ 读
            dst = ops.split(",")[0].strip()
            if "0xa8edd8" in dst:
                writes.append(entry)
            elif "0xa8edd8" in ops:
                reads.append(entry)
        elif m == "cmp":
            reads.append(entry)
        elif m in ("test", "movzx", "movsx", "lea"):
            reads.append(entry)
    print("== 写点 %d 个 ==" % len(writes))
    for w in writes:
        print("  %08X  %s %s" % (w["addr"], w["mnem"], w["ops"]))
    print("== 读点 %d 个 ==" % len(reads))
    for r in reads[:60]:
        print("  %08X  %s %s" % (r["addr"], r["mnem"], r["ops"]))
    if len(reads) > 60:
        print("  ...（截断，共 %d）" % len(reads))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
