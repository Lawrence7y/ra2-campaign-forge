#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 亲验：崩溃族函数 0x0047C520 / 0x0047C4D0 的逐指令复核。

目的：R09_COMMON.md 把下面两句当成事实写给四张卡：
  (a) 0x0047C52A: mov esi,[ecx+0xE4]   ; CellClass::FirstObject
  (b) 0x0047C538: 取 [eax+0x2C] 并 call
这两句都来自台账的**转述**。本项目已多次因"转述当真"翻车（§625-2 / §632-6）。
本脚本从原始 EXE 字节重算，不引用任何既有结论。

用法：
  python _lead_verify_47C5.py                # 打印 0x47C4C0..0x47C560 全段反汇编
  python _lead_verify_47C5.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_MEM, CS_OP_REG, CS_OP_IMM

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
IMAGE_BASE = 0x400000


def va_to_off(pe: pefile.PE, va: int):
    rva = va - IMAGE_BASE
    for s in pe.sections:
        lo = s.VirtualAddress
        hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if lo <= rva < hi:
            delta = rva - lo
            if delta >= s.SizeOfRawData:
                return None, s.Name.decode("latin1").rstrip("\x00")
            return s.PointerToRawData + delta, s.Name.decode("latin1").rstrip("\x00")
    return None, None


def mem_str(md: Cs, ins) -> str:
    """把 capstone 的 mem 操作数渲染成 '[base + index*scale + disp]'。"""
    for op in ins.operands:
        if op.type == CS_OP_MEM:
            m = op.mem
            base = ins.reg_name(m.base) if m.base else ""
            index = ins.reg_name(m.index) if m.index else ""
            parts = []
            if base:
                parts.append(base)
            if index:
                parts.append(f"{index}*{m.scale}" if m.scale > 1 else index)
            s = "+".join(parts)
            if m.disp:
                s += f"{m.disp:+#x}"
            return f"[{s}]"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="0x0047C4D0")
    ap.add_argument("--end", default="0x0047C560")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    pe = pefile.PE(str(EXE), fast_load=True)
    start, end = int(args.start, 16), int(args.end, 16)
    off, sec = va_to_off(pe, start)
    if off is None:
        print(f"[FATAL] {start:#x} 不在任何节里", file=sys.stderr)
        return 2
    data = pe.__data__[off: off + (end - start) + 16]

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    rows = []
    for ins in md.disasm(data, start):
        if ins.address >= end:
            break
        rows.append({
            "va": f"0x{ins.address:08X}",
            "bytes": ins.bytes.hex(),
            "mnemonic": ins.mnemonic,
            "op_str": ins.op_str,
            "mem": mem_str(md, ins),
        })

    print(f"# {EXE.name}  section={sec}  range=0x{start:08X}..0x{end:08X}")
    for r in rows:
        star = ""
        if r["va"] in ("0x0047C52A", "0x0047C52E", "0x0047C538", "0x0047C53B", "0x0047C4D0"):
            star = "   <== ATTENTION"
        print(f'{r["va"]}  {r["bytes"]:<24} {r["mnemonic"]:<8} {r["op_str"]:<32}{star}')

    # ---- 断言区：只报事实，不替读者下结论 ----
    print("\n# ---- 机械核对 ----")
    def find(va):
        for r in rows:
            if r["va"] == va:
                return r
        return None

    a = find("0x0047C52A")
    print(f"[0x0047C52A] {a['mnemonic']} {a['op_str']}  bytes={a['bytes']}" if a else "[0x0047C52A] 未落在本段")
    # 该指令的 mem 操作数 displacement 是否 == 0xE4
    if a:
        disp = None
        raw = bytes.fromhex(a["bytes"])
        # 独立用 capstone 再解析一次拿 disp，避免渲染字符串掩盖问题
        for ins in md.disasm(raw, int(a["va"], 16)):
            for op in ins.operands:
                if op.type == CS_OP_MEM:
                    disp = op.mem.disp
            break
        print(f"    -> 首个 mem disp = 0x{(disp or 0):X}   断言 disp==0xE4 : "
              f"{'PASS' if disp == 0xE4 else 'FAIL'}")

    b = find("0x0047C538")
    print(f"[0x0047C538] {b['mnemonic']} {b['op_str']}  bytes={b['bytes']}" if b else "[0x0047C538] 未落在本段")
    if b:
        raw = bytes.fromhex(b["bytes"])
        disp = None
        indirect = False
        for ins in md.disasm(raw, int(b["va"], 16)):
            indirect = "[" in ins.op_str
            for op in ins.operands:
                if op.type == CS_OP_MEM:
                    disp = op.mem.disp
            break
        print(f"    -> mem disp = 0x{(disp or 0):X}  间接引用={indirect}  断言 disp==0x2C : "
              f"{'PASS' if disp == 0x2C else 'FAIL'}")

    # Access address 0x000A0034 与 vptr 0x000A0008 的关系
    print(f"[算术] 0x000A0008 + 0x2C = 0x{0x000A0008 + 0x2C:08X}  "
          f"（S1 的 Access address = 0x000A0034）: "
          f"{'MATCH' if 0x000A0008 + 0x2C == 0x000A0034 else 'MISMATCH'}")

    if args.json:
        Path(args.json).write_text(json.dumps({"section": sec, "rows": rows},
                                              ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[out] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
