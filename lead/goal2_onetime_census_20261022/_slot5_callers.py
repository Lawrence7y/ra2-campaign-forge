# -*- coding: utf-8 -*-
"""待办 9 第二段：谁调用 slot5（= RadarClass::One_Time 0x652CF0），在什么时机。

为什么需要这一段
----------------
`_onetime_census.py` 证了 One_Time 是表 B 的 slot5，但**没有**回答"谁调 slot5"。
它只扫了 `call [reg+0x14]` 的字面量宿主，得出 "hosts that also touch [0x87F7E8] : 0"
就收尾了。这个结论**不足**：对象指针常由**参数/成员**传入，宿主函数不会字面量
引用单例地址。要判分岔 A（启动一次）/ B（每次载图）/ A'（加载未完成 + WM_CLOSE），
必须看**调用 slot5 的宿主的性质**。

判定思路
--------
1. 取全部 `call [reg+0x14]`（disp8）站点，共 273 处（已由前脚本确认编码）。
2. 对每站，回溯 reg 的来源：
   - 若 reg 来自 `mov reg,[X]` 且 X 是**对象指针成员** ⇒ 记为 "obj-member"
   - 若 reg 来自函数**参数**（到函数头未定义）⇒ 记为 "param"
   - 若 reg 来自**循环变量**（在循环体内，且 reg 随数组步进）⇒ 记为 "array-iter"
3. 找宿主函数的**时机特征字符串**：场景加载 / 开局 / 每帧 相关。
4. 关键判据：YR 引擎里 `One_Time` 是 ObjectClass 体系虚函数，通常在场景启动时
   由遍历全部对象的 `LogicClass::One_Time()` 调一次。若找到"遍历对象数组 + 调 slot5"
   的循环宿主 ⇒ 分岔 B（每次载图重跑）。若只在静态构造期 ⇒ 分岔 A。

纪律
----
- 只读；从真实指令边界解码；段表 VA 是 RVA 需加 imagebase。
- 结论必须区分 [已证] / [强推断] / [未定]。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_EAX, X86_REG_EBX, X86_REG_ECX, X86_REG_EDX,
                          X86_REG_ESI, X86_REG_EDI, X86_REG_EBP, X86_REG_ESP)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
ONE_TIME = 0x652CF0
SLOT5_DISP = 0x14

REGS = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx",
        X86_REG_EDX: "edx", X86_REG_ESI: "esi", X86_REG_EDI: "edi",
        X86_REG_EBP: "ebp", X86_REG_ESP: "esp"}

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

    def sec_of(self, va):
        rva = va - self.imagebase
        for s in self.sections:
            if s["va"] <= rva < s["va"] + max(s["vsize"], s["rawsize"]):
                return s["name"]
        return None


def main():
    print("=" * 78)
    print("== STEP 0  identity + full .text linear decode")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1

    pe = PE(data)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    code = data[text["rawptr"]:text["rawptr"] + text["rawsize"]]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    insns = []
    # ★ 线性解码会在不可解码字节处停（本件实测 66 处）。必须**续解**：
    #   停在 X ⇒ 从 X+1 重新起解，直到段尾。断点地址全部记录，供边界审计。
    stops = []
    cur = text_va
    end = text_va + text["rawsize"]
    while cur < end:
        off = pe.va2off(cur)
        if off is None:
            break
        chunk = data[off:off + (end - cur)]
        got = 0
        last_end = cur
        for i in md.disasm(chunk, cur):
            insns.append(i)
            got += 1
            last_end = i.address + i.size
        if got == 0:
            stops.append(cur)
            cur += 1
        else:
            cur = last_end
    print(f"decoded {len(insns)} instructions in .text")
    print(f"undecodable stops: {len(stops)}")
    if stops:
        print("  first 12 stop bytes: " + ", ".join(f"0x{x:X}" for x in stops[:12]))
    if not chk("decoded > 500000", len(insns) > 500000, str(len(insns))):
        return 1

    addr2idx = {i.address: k for k, i in enumerate(insns)}

    print()
    print("=" * 78)
    print("== STEP 1  all call [reg+0x14] sites (disp8)")
    print("=" * 78)
    sites = []
    for k, i in enumerate(insns):
        if i.mnemonic != "call" or len(i.operands) != 1:
            continue
        op = i.operands[0]
        if op.type != X86_OP_MEM:
            continue
        if op.mem.base == 0 or op.mem.index != 0:
            continue
        if op.mem.disp != SLOT5_DISP:
            continue
        sites.append((k, i, REGS.get(op.mem.base, "?")))
    print(f"total call [reg+0x14] sites: {len(sites)}")
    chk("site count in 250..300 (matches prior 273)", 250 <= len(sites) <= 300,
        str(len(sites)))

    print()
    print("=" * 78)
    print("== STEP 2  classify reg provenance for each site")
    print("=" * 78)

    def find_func_head(idx):
        """从 idx 向前找函数头：前一条是 ret/int3/nop 填充，或跨段。"""
        k = idx - 1
        while k >= 0:
            p = insns[k]
            if p.mnemonic in ("ret", "retn", "int3", "hlt"):
                return k + 1
            if p.mnemonic == "nop":
                # nop 填充：继续往前，但连续 nop 后面才是头
                k -= 1
                continue
            k -= 1
        return 0

    def reg_source(k, reg, depth=0):
        """在 k 之前回溯 reg 的最后一次写。返回描述。"""
        if depth > 3:
            return "deep"
        j = k - 1
        while j >= 0:
            p = insns[j]
            # 目标写 reg？
            wrote = False
            if len(p.operands) >= 1 and p.operands[0].type == X86_OP_REG \
                    and p.operands[0].reg == reg:
                wrote = True
            if wrote:
                if p.mnemonic == "mov" and len(p.operands) == 2:
                    s = p.operands[1]
                    if s.type == X86_OP_MEM:
                        if s.mem.base != 0:
                            return f"mem[{REGS.get(s.mem.base,'?')}+0x{s.mem.disp:X}]"
                        return f"abs[0x{s.mem.disp:X}]"
                    if s.type == X86_OP_REG:
                        return f"reg({REGS.get(s.reg,'?')})"
                    if s.type == X86_OP_IMM:
                        return f"imm(0x{s.imm:X})"
                if p.mnemonic in ("call",):
                    return "call-retval"
                if p.mnemonic in ("xor", "sub") and len(p.operands) == 2 \
                        and p.operands[1].type == X86_OP_REG \
                        and p.operands[1].reg == reg:
                    return "zeroed"
                return f"{p.mnemonic}"
            # 遇到 call 且 reg 是易失寄存器 ⇒ 值来自返回值
            if p.mnemonic == "call" and reg in (X86_REG_EAX, X86_REG_ECX,
                                                X86_REG_EDX):
                return "call-clobbered"
            j -= 1
            if j < 0:
                break
        return "func-head(undef)"

    classified = []
    for k, i, rbase in sites:
        reg = None
        for rr, nm in REGS.items():
            if nm == rbase:
                reg = rr
                break
        head = find_func_head(k)
        head_va = insns[head].address
        src = reg_source(k, reg)
        # 循环特征：从 head 到 k 之间有无向后跳转
        loop = False
        for j in range(head, k):
            p = insns[j]
            if p.mnemonic.startswith("j") and p.operands:
                t = p.operands[0]
                if t.type == X86_OP_IMM and t.imm <= p.address and t.imm >= head_va:
                    loop = True
                    break
        classified.append({"site": i.address, "reg": rbase, "head": head_va,
                           "src": src, "loop": loop, "idx": k})

    # 汇总
    from collections import Counter
    src_kind = Counter()
    for c in classified:
        s = c["src"]
        if s.startswith("abs[0x87F7E8]"):
            src_kind["abs-singleton(read)"] += 1
        elif s == f"imm(0x{SINGLETON:X})":
            src_kind["imm-singleton(addr-of)"] += 1
        elif s.startswith("mem[") and "0x0]" in s:
            src_kind["mem[vtable]"] += 1
        elif s.startswith("mem["):
            src_kind["mem[member]"] += 1
        elif s.startswith("func-head"):
            src_kind["param/undef"] += 1
        elif s == "call-clobbered":
            src_kind["call-clobbered"] += 1
        elif s.startswith("reg("):
            src_kind["reg-chain"] += 1
        else:
            src_kind["other:" + s] += 1
    for k2, v in src_kind.most_common():
        print(f"  {k2:<28} {v}")

    # ★ 关键两类：字面量取单例（读 [abs] 或取地址 imm）后再调 slot5
    lit_single = [c for c in classified
                  if c["src"].startswith("abs[0x87F7E8]")
                  or c["src"] == f"imm(0x{SINGLETON:X})"]
    loop_vt = [c for c in classified
               if c["loop"] and c["src"].startswith("mem[") and "0x0]" in c["src"]]
    print()
    print(f"  sites reaching slot5 from the SINGLETON literally : {len(lit_single)}")
    for c in lit_single:
        print(f"     site 0x{c['site']:08X}  host 0x{c['head']:08X}  src {c['src']}")
    print(f"  loop hosts calling slot5 via [obj+0] vtable : {len(loop_vt)}")
    for c in loop_vt[:20]:
        print(f"     site 0x{c['site']:08X}  host 0x{c['head']:08X}  src {c['src']}")

    print()
    print("=" * 78)
    print("== STEP 3  timing strings in slot5-calling hosts")
    print("=" * 78)

    def strings_in_range(lo, hi, limit=400):
        """扫 .rdata 找 push imm32 指向的可读串（限定在宿主函数范围内）。"""
        out = []
        j = addr2idx.get(lo)
        if j is None:
            return out
        while j < len(insns) and insns[j].address < hi and len(out) < limit:
            p = insns[j]
            if p.mnemonic == "push" and len(p.operands) == 1 \
                    and p.operands[0].type == X86_OP_IMM:
                v = p.operands[0].imm & 0xFFFFFFFF
                if 0x7E1000 <= v < 0xB96000:
                    b = pe.read(v, 96)
                    if b:
                        z = b.split(b"\x00")[0]
                        if 4 <= len(z) <= 80 and all(32 <= ch < 127 or ch in (9, 10) for ch in z):
                            try:
                                s = z.decode("ascii")
                            except Exception:
                                s = None
                            if s:
                                out.append((p.address, v, s))
            j += 1
        return out

    # 收集所有 slot5 宿主（去重），找时机串
    heads = {}
    for c in classified:
        heads.setdefault(c["head"], []).append(c["site"])

    KEYWORDS = ("Scenario", "scenario", "Map", "Load", "load", "Start",
                "Init", "New Game", "game", "Tiberium", "frame", "Frame")
    hits = []
    for h, ss in sorted(heads.items()):
        # 宿主范围：到下一个函数头
        nxt = None
        for k2 in range(addr2idx.get(h, 0) + 1, len(insns)):
            if insns[k2].address in heads:
                nxt = insns[k2].address
                break
        hi = nxt if nxt else h + 0x2000
        strs = strings_in_range(h, min(hi, h + 0x3000))
        interesting = [s for s in strs if any(kw in s[2] for kw in KEYWORDS)]
        if interesting:
            hits.append((h, ss, interesting))

    print(f"slot5 hosts with timing-relevant strings: {len(hits)}")
    for h, ss, strs in hits[:15]:
        print(f"  host 0x{h:08X}  sites {[f'0x{x:08X}' for x in ss]}")
        for a, v, s in strs[:6]:
            print(f"     0x{a:08X} 0x{v:08X}  {s!r}")

    print()
    print("=" * 78)
    print("== STEP 4  is One_Time reachable from a scene-load entry?")
    print("=" * 78)
    # One_Time 只在表 B slot5。若某宿主的 slot5 调用其对象 vtable 可能是表 B，
    # 则该宿主可能是 One_Time 的调用者。这里给出「loop + vtable」宿主的函数体特征。
    print(f"loop+vtable hosts: {len(set(c['head'] for c in loop_vt))}")
    for h in sorted(set(c["head"] for c in loop_vt))[:10]:
        strs = strings_in_range(h, h + 0x1200)
        print(f"  host 0x{h:08X}  strings: {[s[2][:40] for s in strs[:5]]}")

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    # 判定逻辑
    has_scene_host = any(any("cenario" in s[2] or "Load" in s[2] or "Map" in s[2]
                             for s in strs) for _, _, strs in hits)
    print(f"  [已证] One_Time = 表B slot5（前脚本 13/13）")
    print(f"  [已证] One_Time 体内无一次性闩锁（前脚本断言）")
    print(f"  [统计] call [reg+0x14] 站点 {len(sites)} 处；")
    print(f"         其中字面量取单例 {len(lit_single)} 处；")
    print(f"         循环宿主经 [obj+0] 虚表调 slot5 {len(loop_vt)} 处")
    if has_scene_host:
        print("  [强推断] 存在带场景加载语义串的 slot5 宿主 ⇒ 支持分岔 B（每次载图重跑）")
        verdict = "B_SUPPORTED"
    elif loop_vt:
        print("  [强推断] 存在循环遍历对象并调 slot5 的宿主 ⇒ 支持分岔 B（场景内遍历）")
        verdict = "B_LOOP_ITER"
    else:
        print("  [未定] 未找到场景加载或循环遍历证据 ⇒ 不能排除分岔 A")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
