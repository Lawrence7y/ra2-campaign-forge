#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 亲验：三处同族函数的调用点普查 + 共同守卫 0x00A8E9A0 的读写普查。

为什么要做：
  S1/S2 崩在 0x0047C538（`0x47C520` 内）。要知道"崩溃时引擎正在干什么"，
  必须先知道**谁在调它**。而三个同族函数（0x47C4D0 / 0x47C520 / 0x47C550）
  入口都有同一个守卫 `mov al,[0x00A8E9A0]`，那个 bool 决定这一族是否执行。

方法（全部从原始字节重算）：
  1. 扫 `.text` 找 `E8 rel32`（call rel32），算目标，命中三处之一即记录。
  2. 扫 `.rdata` 找三处地址作为数据项出现的位置（可能是 vtable 槽，也可能是别的表）。
  3. 对 0x00A8E9A0：
     - 找所有含该 imm32 的指令（读/写都算），逐条反汇编判定 mem 操作数是读还是写。
     - 统计读点数 / 写点数；列出全部写点地址。

用法：
  python _lead_caller_census.py
  python _lead_caller_census.py --json out.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
IMAGE_BASE = 0x400000
TARGETS = {0x0047C4D0: "0x47C4D0", 0x0047C520: "0x47C520", 0x0047C550: "0x47C550"}
GUARD_VA = 0x00A8E9A0


def secs_of(pe):
    out = []
    for s in pe.sections:
        out.append({
            "name": s.Name.decode("latin1").rstrip("\x00"),
            "va": IMAGE_BASE + s.VirtualAddress,
            "vsize": s.Misc_VirtualSize,
            "raw": s.PointerToRawData,
            "rsize": s.SizeOfRawData,
            "exec": bool(s.Characteristics & 0x20000000),
        })
    return out


def find_sec(secs, name):
    return next(s for s in secs if s["name"] == name)


def off_in(secs, va):
    for s in secs:
        size = max(s["vsize"], s["rsize"])
        if s["va"] <= va < s["va"] + size:
            d = va - s["va"]
            if d >= s["rsize"]:
                return None
            return s["raw"] + d
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    pe = pefile.PE(str(EXE), fast_load=True)
    buf = pe.__data__
    secs = secs_of(pe)
    text = find_sec(secs, ".text")
    rdata = find_sec(secs, ".rdata")

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    # ---------- 1) call rel32 -> 三个目标 ----------
    t0 = text["va"]
    tdata = bytes(buf[text["raw"]: text["raw"] + text["rsize"]])
    calls = []
    for i in range(len(tdata) - 5):
        if tdata[i] != 0xE8:
            continue
        rel = int.from_bytes(tdata[i + 1:i + 5], "little", signed=True)
        va = t0 + i
        tgt = va + 5 + rel
        if tgt in TARGETS:
            calls.append({"from": va, "to": tgt, "name": TARGETS[tgt]})

    # ---------- 2) 三处地址在 .rdata 里作为数据项 ----------
    refs = []
    r0, rs = rdata["va"], rdata["rsize"]
    rbuf = bytes(buf[rdata["raw"]: rdata["raw"] + rs])
    for tgt in TARGETS:
        pat = tgt.to_bytes(4, "little")
        start = 0
        while True:
            k = rbuf.find(pat, start)
            if k < 0:
                break
            refs.append({"where": r0 + k, "to": tgt, "name": TARGETS[tgt]})
            start = k + 1

    # ---------- 3) 守卫 0x00A8E9A0 的读写普查 ----------
    gpat = GUARD_VA.to_bytes(4, "little")
    guard = {"read": [], "write": [], "other": []}
    start = 0
    while True:
        k = tdata.find(gpat, start)
        if k < 0:
            break
        start = k + 1
        va = t0 + k
        # 指令起点未必等于 imm 位置：从 k-15 起试每条长度，找能覆盖到 k 的起点
        found = False
        for back in range(1, 16):
            if k - back < 0:
                break
            cand = k - back
            for ins in md.disasm(tdata[cand:cand + 16], t0 + cand):
                if ins.address > va:
                    break
                span = (ins.address, ins.address + ins.size)
                if span[0] <= va < span[1]:
                    kind = "other"
                    has_mem_guard = False
                    for op in ins.operands:
                        if op.type == CS_OP_IMM and op.imm == GUARD_VA:
                            kind_mem = None
                            # 判断这条指令是否把结果写回 [guard]
                            for op2 in ins.operands:
                                if op2.type == CS_OP_MEM and op2.mem.disp == GUARD_VA:
                                    if ins.address + ins.size and ins.mnemonic.startswith(("mov", "and", "or", "xor", "add", "sub", "inc", "dec", "set")):
                                        # 目的操作数是第一个 op
                                        pass
                            # 简单判定：目的（第一个操作数）是否为 [0xA8E9A0]
                            dst = ins.operands[0]
                            if dst.type == CS_OP_MEM and dst.mem.disp == GUARD_VA:
                                kind = "write"
                            else:
                                kind = "read"
                    guard[kind].append({"va": ins.address, "asm": f"{ins.mnemonic} {ins.op_str}",
                                        "bytes": ins.bytes.hex()})
                    found = True
                    break
            if found:
                break
        if not found:
            guard["other"].append({"va": va, "asm": "<未定位到指令起点>", "bytes": ""})

    # ---------- 输出 ----------
    print(f"# {EXE.name}   三处同族函数调用点普查")
    print(f"\n## 1) call rel32 命中（共 {len(calls)} 处）")
    for c in calls:
        print(f"  0x{c['from']:08X}  call 0x{c['to']:08X}   ({c['name']})")

    print(f"\n## 2) 在 .rdata 里作为数据项出现（共 {len(refs)} 处，可能是 vtable 槽/函数表）")
    for r in refs:
        print(f"  0x{r['where']:08X}  -> 0x{r['to']:08X}   ({r['name']})")

    print(f"\n## 3) 守卫 0x{GUARD_VA:08X}：读 {len(guard['read'])} 处 / 写 {len(guard['write'])} 处 / 未定位 {len(guard['other'])} 处")
    print("  --- 写点（这些决定该 bool 何时为真）---")
    for r in guard["write"]:
        print(f"    0x{r['va']:08X}  {r['bytes']:<22} {r['asm']}")
    if not guard["write"]:
        print("    （没有直接写点：说明它由别处间接写，或由结构体/块写入）")
    print("  --- 读点（前 20 条）---")
    for r in guard["read"][:20]:
        print(f"    0x{r['va']:08X}  {r['bytes']:<22} {r['asm']}")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "calls": calls, "rdata_refs": refs, "guard": guard,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[out] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
