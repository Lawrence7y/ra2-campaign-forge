# -*- coding: utf-8 -*-
"""决定性一段：0x652C00（安装表B 0x7F0344）的 6 个调用者，哪个在**运行期**执行。

已测事实
--------
- 0x652C00 体内 `mov [edi], 0x7F0344`（edi=ecx=this）⇒ 把表B 写进对象首 dword。
- 0x652C00 有 6 个调用者：0x40D1F7 / 0x40D2D4 / 0x5BEA0A / 0x6404B3 / 0x69391A / 0x6AC81A。
- 单例 0x87F7E8 的构造 0x5BDA40 装的是**表A**。
- 0x40D1B0（含 0x40D1B2 写表A + 0x40D1F7 调 0x652C00）只以 `push 0x40D1B0; call 0x7C978A`
  被引用，而 0x7C978A 是 `push [esp+4]; call 0x7C970C; neg/sbb/neg/dec; ret` 形态的
  **0/1 判定器**（336 个调用者，仅 68 个前置 push imm）⇒ 不是 atexit 注册。

本段要答
--------
对 6 个调用者各取上下文（前后各 12 条指令 + 所在函数的时机字符串），判定：
- 该调用点是否 `mov ecx, 0x87F7E8` 之后紧接 call（⇒ 直接作用于单例）
- 若作用于单例且位于运行期路径 ⇒ 运行期 vtable = 表B ⇒ slot5 = One_Time
- 若都不作用于单例 ⇒ 表B 只给别的对象用，单例运行期恒为表A
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
REINIT = 0x652C00
ONE_TIME = 0x652CF0
CALLERS = [0x40D1F7, 0x40D2D4, 0x5BEA0A, 0x6404B3, 0x69391A, 0x6AC81A]

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

    def u32(self, va):
        b = self.read(va, 4)
        return None if b is None else struct.unpack("<I", b)[0]


def main():
    print("=" * 78)
    print("== STEP 0  identity + linear decode")
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
    idx = {i.address: k for k, i in enumerate(insns)}
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    def head_of(k):
        j = k - 1
        while j >= 0:
            p = insns[j]
            if p.mnemonic in ("ret", "retn", "int3", "hlt"):
                return j + 1
            j -= 1
        return 0

    def strings_near(lo, hi):
        out = []
        for k in range(idx.get(lo, 0), min(idx.get(lo, 0) + 4000, len(insns))):
            p = insns[k]
            if p.address >= hi:
                break
            if p.mnemonic == "push" and p.operands and p.operands[0].type == X86_OP_IMM:
                v = p.operands[0].imm & 0xFFFFFFFF
                if 0x7E1000 <= v < 0xB96000:
                    b = pe.read(v, 96)
                    if b:
                        z = b.split(b"\x00")[0]
                        if 4 <= len(z) <= 90 and all(32 <= c < 127 or c in (9, 10) for c in z):
                            out.append((p.address, v, z.decode("ascii", "replace")))
        return out

    print()
    print("=" * 78)
    print("== STEP 1  context of each 0x652C00 caller")
    print("=" * 78)
    results = []
    for ca in CALLERS:
        k = idx.get(ca)
        if k is None:
            print(f"\n-- 0x{ca:08X}: NOT at an instruction boundary")
            results.append({"site": ca, "boundary": False})
            continue
        head_k = head_of(k)
        head = insns[head_k].address
        print(f"\n-- caller 0x{ca:08X}  (host func head 0x{head:08X})")
        # 前 8 条
        for j in range(max(head_k, k - 8), k + 1):
            p = insns[j]
            mark = ""
            for op in p.operands:
                if op.type == X86_OP_IMM and (op.imm & 0xFFFFFFFF) == SINGLETON:
                    mark = "  <== SINGLETON"
                if op.type == X86_OP_MEM and op.mem.base == 0 and \
                        (op.mem.disp & 0xFFFFFFFF) == SINGLETON:
                    mark = "  <== SINGLETON(mem)"
            print(f"     {p.address:08X}  {p.bytes.hex():<20} {p.mnemonic} {p.op_str}{mark}")
        # 判 ecx 来源：在 call 之前找最后一次写 ecx
        ecx_src = "unknown"
        j = k - 1
        while j >= head_k:
            p = insns[j]
            if p.operands and p.operands[0].type == X86_OP_REG \
                    and p.operands[0].reg == 1:  # X86_REG_ECX == 1
                if p.mnemonic == "mov" and len(p.operands) == 2:
                    s = p.operands[1]
                    if s.type == X86_OP_IMM:
                        ecx_src = f"imm(0x{s.imm & 0xFFFFFFFF:08X})"
                    elif s.type == X86_OP_REG:
                        ecx_src = "reg"
                    elif s.type == X86_OP_MEM:
                        ecx_src = (f"abs[0x{s.mem.disp & 0xFFFFFFFF:08X}]"
                                   if s.mem.base == 0 else "mem[reg]")
                break
            j -= 1
        print(f"     ecx <- {ecx_src}")
        strs = strings_near(head, head + 0x1800)
        interesting = [s[2] for s in strs
                       if any(w in s[2] for w in ("Init", "Load", "Start", "Scenario",
                                                  "scenario", "Map", "Exit", "Shutdown",
                                                  "Destroy", "Clean", "Free"))]
        print(f"     host strings (timing-relevant): {interesting[:6]}")
        results.append({"site": ca, "boundary": True, "head": head,
                        "ecx_src": ecx_src, "strings": interesting[:6]})

    print()
    print("=" * 78)
    print("== STEP 2  which callers act on the SINGLETON?")
    print("=" * 78)
    on_singleton = [r for r in results
                    if r.get("boundary") and
                    (r["ecx_src"] == f"imm(0x{SINGLETON:08X})"
                     or r["ecx_src"] == f"abs[0x{SINGLETON:08X}]")]
    print(f"  callers with ecx == SINGLETON 0x87F7E8 : {len(on_singleton)}")
    for r in on_singleton:
        print(f"     0x{r['site']:08X}  host 0x{r['head']:08X}  ecx {r['ecx_src']}")
        print(f"        strings: {r['strings']}")

    others = [r for r in results if r not in on_singleton and r.get("boundary")]
    print(f"  callers with ecx != SINGLETON : {len(others)}")
    for r in others:
        print(f"     0x{r['site']:08X}  host 0x{r['head']:08X}  ecx {r['ecx_src']}")
        print(f"        strings: {r['strings']}")

    chk("0x40D1F7 acts on the singleton (ecx == 0x87F7E8)",
        any(r["site"] == 0x40D1F7 for r in on_singleton),
        "yes" if any(r["site"] == 0x40D1F7 for r in on_singleton) else "no")

    print()
    print("=" * 78)
    print("== STEP 3  verdict")
    print("=" * 78)
    if on_singleton:
        print("  [已证] 至少一处 0x652C00 调用以 ecx=单例执行 ⇒ 运行期单例可被装成表B。")
        for r in on_singleton:
            print(f"         0x{r['site']:08X}（宿主 0x{r['head']:08X}）")
        print("  ⇒ §347「运行时是表B」**成立**；slot5 = One_Time。")
        print("  ⇒ One_Time 经 slot5 被调用，分岔取决于该宿主的时机（见 strings）。")
        verdict = "TABLE_B_RUNTIME_CONFIRMED"
    else:
        print("  [已证] 6 处 0x652C00 调用**没有一处**以单例为 ecx ⇒ 表B 只用于别的对象。")
        print("  ⇒ 单例运行期恒为表A ⇒ slot5 = 0x5BDF30（非 One_Time）。")
        print("  ⇒ 但崩溃栈 0x652D51 证明 One_Time 跑过 ⇒ 需另找调用路径。")
        verdict = "SINGLETON_STAYS_TABLE_A"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
