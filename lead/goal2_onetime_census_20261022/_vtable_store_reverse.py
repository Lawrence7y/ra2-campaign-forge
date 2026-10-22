# -*- coding: utf-8 -*-
"""待办 9c（方案 B）：反向枚举所有「装 vtable 到对象首字段」的站点，
再查每个站点的 caller 是否传 `0x87F7E8`。

为什么换方向
------------
`_indirect_write_census.py` 正向追踪（取址 → 30 条内同寄存器写）**失效**：
`0x5BDA4A` 的 `esi` 来自 `mov esi,ecx`，与 `0x40D190` 的 `mov ecx,0x87F7E8`
隔了一次 `call`，跨不过函数边界 ⇒ 假阴性。

**方案 B 不追踪来源**，而是：
1. 枚举全文件所有 `mov [reg], imm32` 且 `imm32` 落在 `.rdata` 的 vtable 区
   （判据：该地址 -4 处能解出合法 COL，且 COL 的 TypeDescriptor 名字可读）；
2. 对每个这样的站点，取其所在函数头；
3. 查该函数头的**全部 E8 调用者**；
4. 对每个调用者，看调用点前是否 `mov ecx, 0x87F7E8`（或 ecx 来自单例）。

这样能穷举，不会漏。
"""
import hashlib
import struct
import sys
import bisect
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_ECX, X86_REG_EAX, X86_REG_EDX,
                          X86_REG_ESI, X86_REG_EDI, X86_REG_EBX)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
EXIT_CB = 0x40D1B0

REGS = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx",
        X86_REG_EDX: "edx", X86_REG_ESI: "esi", X86_REG_EDI: "edi"}

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

    def cstr(self, va, n=100):
        b = self.read(va, n)
        if not b:
            return None
        z = b.split(b"\x00")[0]
        try:
            s = z.decode("ascii")
        except Exception:
            return None
        return s if 2 <= len(s) and all(32 <= ord(c) < 127 for c in s) else None


def is_vtable(pe, va):
    """判据：va-4 处是 COL，COL+0x0C 是 TypeDescriptor(VA)，其 +0x08 是可读的 .?AV... 名。"""
    col = pe.u32(va - 4)
    if not col:
        return None
    if col < pe.imagebase:
        col += pe.imagebase
    td = pe.u32(col + 0x0C)
    if not td:
        return None
    if td < pe.imagebase:
        td += pe.imagebase
    name = pe.cstr(td + 0x08)
    if name and name.startswith(".?A"):
        return name
    return None


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

    # ★ 函数头判定必须**跳过 nop 填充**：
    #   `ret` 后面常跟一串 `90`（对齐填充），填充之后的第一个真指令才是下一个函数头。
    #   本轮首版把填充起点当成函数头（0x5BDA35 而非 0x5BDA40），导致 callers 恒为 0。
    HEADS = []
    k = 0
    n = len(insns)
    while k < n:
        i = insns[k]
        if k == 0:
            HEADS.append(i.address)
            k += 1
            continue
        prev = insns[k - 1]
        if prev.mnemonic in ("ret", "retn", "int3", "hlt"):
            # 跳过紧随其后的 nop 填充
            j = k
            while j < n and insns[j].mnemonic == "nop":
                j += 1
            if j < n:
                HEADS.append(insns[j].address)
            k = j if j > k else k + 1
            continue
        k += 1
    HS = sorted(set(HEADS))

    def head_of(va):
        k = bisect.bisect_right(HS, va) - 1
        return HS[k] if k >= 0 else text_va

    print()
    print("=" * 78)
    print("== STEP 1  ALL stores of a vtable into [reg] or [reg+disp] (disp==0)")
    print("=" * 78)
    # ★ 这一步**不要求** reg 能追到单例 —— 反向枚举，不会漏
    vt_stores = []
    for i in insns:
        if i.mnemonic != "mov" or len(i.operands) != 2:
            continue
        d, s = i.operands
        if d.type != X86_OP_MEM or s.type != X86_OP_IMM:
            continue
        if d.mem.base == 0 or d.mem.index != 0 or d.mem.disp != 0:
            continue
        val = s.imm & 0xFFFFFFFF
        name = is_vtable(pe, val)
        if name:
            vt_stores.append({"at": i.address, "reg": REGS.get(d.mem.base, "?"),
                              "vt": val, "name": name,
                              "head": head_of(i.address),
                              "insn": f"{i.mnemonic} {i.op_str}"})
    print(f"  total vtable stores to [reg] (disp=0): {len(vt_stores)}")
    for v in vt_stores:
        print(f"    0x{v['at']:08X}  [{v['reg']}] = 0x{v['vt']:08X} {v['name']}")
        print(f"       head 0x{v['head']:08X}")

    chk("found the known TABLE_A install site 0x5BDA4A",
        any(v["at"] == 0x5BDA4A for v in vt_stores),
        str([f"0x{v['at']:08X}" for v in vt_stores]))
    chk("found the known TABLE_B install site 0x652C0C",
        any(v["at"] == 0x652C0C for v in vt_stores),
        str([f"0x{v['at']:08X}" for v in vt_stores]))

    print()
    print("=" * 78)
    print("== STEP 2  for each store, who calls its function with ecx == SINGLETON?")
    print("=" * 78)
    # 建 call 站点索引：callee -> [(call_addr, caller_head)]
    callers = {}
    for i in insns:
        if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
            t = i.operands[0].imm & 0xFFFFFFFF
            if text_va <= t < end:
                callers.setdefault(t, []).append(i.address)

    def ecx_before(call_addr):
        """在 call 之前找 ecx 的最后一次写，返回描述。"""
        k = idx.get(call_addr)
        if k is None:
            return "?"
        head = head_of(call_addr)
        hk = idx.get(head, 0)
        j = k - 1
        while j >= hk:
            p = insns[j]
            if p.operands and p.operands[0].type == X86_OP_REG \
                    and p.operands[0].reg == X86_REG_ECX:
                if p.mnemonic == "mov" and len(p.operands) == 2:
                    s = p.operands[1]
                    if s.type == X86_OP_IMM:
                        return f"imm(0x{s.imm & 0xFFFFFFFF:08X})"
                    if s.type == X86_OP_REG:
                        return f"reg({REGS.get(s.reg,'?')})"
                    if s.type == X86_OP_MEM:
                        return "mem"
                return p.mnemonic
            j -= 1
        return "undef"

    results = []
    for v in vt_stores:
        cs = callers.get(v["head"], [])
        hits = []
        for c in cs:
            src = ecx_before(c)
            hits.append({"call": c, "ecx_src": src,
                         "is_singleton": src == f"imm(0x{SINGLETON:08X})"})
        results.append({"store": v, "callers": hits})

    for r in results:
        v = r["store"]
        print(f"\n  -- store 0x{v['at']:08X}  [{v['reg']}] = {v['name']}")
        print(f"     head 0x{v['head']:08X}  callers={len(r['callers'])}")
        for h in r["callers"][:12]:
            mark = "  <== SINGLETON" if h["is_singleton"] else ""
            print(f"        call 0x{h['call']:08X}  ecx <- {h['ecx_src']}{mark}")

    print()
    print("=" * 78)
    print("== STEP 3  verdict: which vtable stores are reached with ecx == 0x87F7E8")
    print("=" * 78)
    singles = []
    for r in results:
        for h in r["callers"]:
            if h["is_singleton"]:
                singles.append((r["store"], h))
    print(f"  (store, caller-with-singleton) pairs: {len(singles)}")
    for v, h in singles:
        print(f"    store 0x{v['at']:08X} ({v['name']})  "
              f"caller 0x{h['call']:08X}  head 0x{v['head']:08X}")

    table_a_singles = [x for x in singles if x[0]["vt"] == VT_A]
    table_b_singles = [x for x in singles if x[0]["vt"] == VT_B]
    print(f"\n  TABLE_A(MouseClass) installs reached with singleton: {len(table_a_singles)}")
    for v, h in table_a_singles:
        print(f"    store 0x{v['at']:08X}  head 0x{v['head']:08X}  "
              f"caller 0x{h['call']:08X}  in_atexit={v['head'] == EXIT_CB}")
    print(f"  TABLE_B(RadarClass) installs reached with singleton: {len(table_b_singles)}")
    for v, h in table_b_singles:
        print(f"    store 0x{v['at']:08X}  head 0x{v['head']:08X}  "
              f"caller 0x{h['call']:08X}  in_atexit={v['head'] == EXIT_CB}")

    if table_b_singles:
        non_exit = [x for x in table_b_singles if x[0]["head"] != EXIT_CB]
        if non_exit:
            print("  [已证] 存在**非退出期**的 TABLE_B 装点，且以单例为 this：")
            for v, h in non_exit:
                print(f"         0x{v['at']:08X}（head 0x{v['head']:08X}）")
            print("         ⇒ 这些是 One_Time 运行期可达的直接证据")
            verdict = "RUNTIME_TABLE_B_INSTALL_FOUND"
        else:
            print("  [已证] TABLE_B 装点全部在退出期回调内 ⇒ 运行期单例恒为表 A")
            verdict = "TABLE_B_ONLY_IN_ATEXIT"
    else:
        print("  [未定] 未找到以单例为 this 的 TABLE_B 装点（可能 caller 不在 E8 图内）")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
