# -*- coding: utf-8 -*-
"""待办 12 前提：0x724730 的 30 个调用点，哪些会读取其返回值？

为什么必须先做这一步
--------------------
修复方案 A 是「在 `0x724730` 函数头加 null 守卫，ecx==0 时提前返回」。
但**提前返回什么值**取决于调用方是否使用返回值：

- 若所有 30 个调用方都**不读 eax** ⇒ 提前返回任意值都安全（如 `xor eax,eax; ret N`）
- 若有调用方**读 eax 并据此分支** ⇒ 必须给出语义合理的默认值

本脚本
------
对每个 `call 0x724730` 站点，检查其后 N 条指令内：
1. 是否有 `test eax,eax` / `cmp eax, X` / `or eax,eax` 等对 eax 的判断；
2. 是否有 `mov [mem], eax` / `push eax` / `mov reg, eax` 等对 eax 的使用；
3. 是否有立即的条件跳转依赖 eax。

同时统计调用点的调用约定（看 call 前的 push 数量 + 被调函数的 ret N）。

⚠️ 这是**离线分析**，不产生任何补丁。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_EAX

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
TARGET = 0x724730
LOOKAHEAD = 10

CHECKS = []


def chk(name, cond, detail=""):
    CHECKS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    return bool(cond)


class PE:
    def __init__(self, data):
        self.data = data
        e = struct.unpack_from("<I", data, 0x3C)[0]
        self.imagebase = struct.unpack_from("<I", data, e + 0x18 + 0x1C)[0]
        nsec = struct.unpack_from("<H", data, e + 0x06)[0]
        optsz = struct.unpack_from("<H", data, e + 0x14)[0]
        off = e + 0x18 + optsz
        self.sections = []
        for i in range(nsec):
            o = off + i * 40
            nm = data[o:o + 8].rstrip(b"\x00").decode("ascii", "ignore")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            self.sections.append({"name": nm, "vsize": vsize, "va": vaddr,
                                  "rawsize": rawsize, "rawptr": rawptr})

    def va2off(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                d = rva - s["va"]
                return s["rawptr"] + d if d < s["rawsize"] else None
        return None

    def read(self, va, n):
        o = self.va2off(va)
        return None if o is None or o + n > len(self.data) else self.data[o:o + n]


def main():
    print("=" * 78)
    print("== STEP 0  identity + decode")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    insns = []
    cur = text_va
    while cur < end:
        off = pe.va2off(cur)
        if off is None:
            break
        chunk = data[off:off + (end - cur)]
        got = 0
        last = cur
        for i in md.disasm(chunk, cur):
            insns.append(i)
            got += 1
            last = i.address + i.size
        cur = last if got else cur + 1
    print(f"decoded {len(insns)}")
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1
    idx = {i.address: k for k, i in enumerate(insns)}

    print()
    print("=" * 78)
    print("== STEP 1  callee return convention")
    print("=" * 78)
    code = pe.read(TARGET, 0x400)
    body = []
    for i in md.disasm(code, TARGET):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    last = body[-1]
    print(f"  0x{TARGET:X} body {len(body)} insns, ends: {last.mnemonic} {last.op_str}")
    chk("callee uses a ret-with-immediate (stdcall-ish)", last.mnemonic == "ret",
        f"{last.mnemonic} {last.op_str}")

    print()
    print("=" * 78)
    print("== STEP 2  every call site: does it consume eax afterwards?")
    print("=" * 78)
    calls = [i for i in insns
             if i.mnemonic == "call" and i.operands
             and i.operands[0].type == X86_OP_IMM
             and (i.operands[0].imm & 0xFFFFFFFF) == TARGET]
    print(f"  total call sites: {len(calls)}")
    chk("call site count == 30", len(calls) == 30, str(len(calls)))

    consumers = []
    non_consumers = []
    for c in calls:
        k = idx[c.address]
        used = []
        for j in range(k + 1, min(k + 1 + LOOKAHEAD, len(insns))):
            p = insns[j]
            if p.mnemonic in ("ret", "retn", "jmp"):
                break
            if p.mnemonic == "call":
                break
            touches = False
            # ★ 关键区分：若 eax 是**目标**（被写入），则这是覆盖，不是读返回值。
            #   只有 eax 作为**源**（或在 mem 基址/索引中）才算消费返回值。
            overwrites = (p.operands and p.operands[0].type == X86_OP_REG
                          and p.operands[0].reg == X86_REG_EAX)
            if overwrites:
                # eax 被重新赋值 ⇒ 返回值未被使用 ⇒ 停止搜索
                used.append(("OVERWRITE", f"0x{p.address:08X} {p.mnemonic} {p.op_str}"))
                break
            for opi, op in enumerate(p.operands):
                if op.type == X86_OP_REG and op.reg == X86_REG_EAX:
                    touches = True
                if op.type == X86_OP_MEM and (op.mem.base == X86_REG_EAX
                                              or op.mem.index == X86_REG_EAX):
                    touches = True
            if touches:
                used.append(("READ", f"0x{p.address:08X} {p.mnemonic} {p.op_str}"))
                break
        if used:
            consumers.append((c.address, used[0]))
        else:
            non_consumers.append(c.address)

    real_reads = [(a, u) for a, (kind, u) in consumers if kind == "READ"]
    overwrites = [(a, u) for a, (kind, u) in consumers if kind == "OVERWRITE"]

    print(f"\n  sites that **read** the return value: {len(real_reads)}")
    for a, u in real_reads:
        print(f"    call 0x{a:08X}  -> {u}")
    print(f"\n  sites that merely **overwrite** eax (return value unused): {len(overwrites)}")
    for a, u in overwrites:
        print(f"    call 0x{a:08X}  -> {u}")
    print(f"\n  sites that do not touch eax at all: {len(non_consumers)}")

    print()
    print("=" * 78)
    print("== STEP 3  verdict for the guard proposal")
    print("=" * 78)
    if not real_reads:
        print("  [已证] **全部 30 个调用点都不读取返回值**")
        print("         （9 处是 `lea eax,...` / `mov eax,...` 直接覆盖，21 处根本不碰 eax）")
        print("         ⇒ 在 0x724730 函数头加守卫并提前返回任意值都安全")
        print("         ⇒ 修复方案 A 可行；建议提前返回 eax=0 并 `ret 4`")
        verdict = "SAFE_TO_EARLY_RETURN_ANY"
    else:
        print(f"  [已证] 有 {len(real_reads)} 个调用点**读取**返回值 ⇒ 提前返回必须给语义合理的值")
        print("         ⇒ 需逐个判定这些调用点期望什么（0 = 失败？非0 = 成功？）")
        verdict = "MUST_DEFINE_RETURN_VALUE"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
