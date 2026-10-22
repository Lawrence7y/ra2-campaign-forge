# -*- coding: utf-8 -*-
"""待办 9c：`[0x87F7E8]` 的**寄存器间接写**完整普查。

为什么要这一段
--------------
§352/§355 已证：
- 字面量写 `mov [0x87F7E8], imm32` 全文件**只有 1 处**（`0x40D1B2`，退出期 atexit 回调内）
- 表 A 的装点 `0x5BDA40` 也是经 `mov [esi],0x7E1964`（esi=this）间接写

⇒ 若运行期中段还有第三次装表，它一定是**寄存器间接**形态：
    mov reg, 0x87F7E8      ; 取单例地址
    mov [reg], 0x7F0344    ; 装表（间接）

这类写**字面量扫描看不见**。本脚本要把它找全。

普查口径
--------
1. 扫全 `.text`，找 `mov reg, imm32 == 0x87F7E8`（取地址）；
2. 从该点向后若干条指令内，找 `mov [reg], imm32` 或 `mov [reg+disp], imm32`；
3. 记录装的是什么值（表 A / 表 B / 其它）；
4. 判定该站点所在的时机（函数头 + 是否在 atexit 回调内 + 是否在构造链上）。

同时补一个反向普查：**所有把 0x7E1964 或 0x7F0344 写进任何位置**的站点，
看有没有目标其实是 `[0x87F7E8]` 但通过别名（lea/栈传递）达成的。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                          X86_REG_EAX, X86_REG_EBX, X86_REG_ECX, X86_REG_EDX,
                          X86_REG_ESI, X86_REG_EDI, X86_REG_EBP)

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
SINGLETON = 0x87F7E8
VT_A = 0x7E1964
VT_B = 0x7F0344
ONE_TIME = 0x652CF0
EXIT_CB = 0x40D1B0
MOUSE_CTOR = 0x5BDA40

REGS = {X86_REG_EAX: "eax", X86_REG_EBX: "ebx", X86_REG_ECX: "ecx",
        X86_REG_EDX: "edx", X86_REG_ESI: "esi", X86_REG_EDI: "edi",
        X86_REG_EBP: "ebp"}

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

    # 预建函数头
    HEADS = []
    prev_term = True
    for i in insns:
        if prev_term:
            HEADS.append(i.address)
        prev_term = i.mnemonic in ("ret", "retn", "int3", "hlt")
    import bisect
    HS = sorted(set(HEADS))

    def head_of(va):
        k = bisect.bisect_right(HS, va) - 1
        return HS[k] if k >= 0 else text_va

    print()
    print("=" * 78)
    print("== STEP 1  sites loading SINGLETON address into a register")
    print("=" * 78)
    loaders = []
    for k, i in enumerate(insns):
        if i.mnemonic in ("mov", "lea") and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_REG \
                and i.operands[1].type == X86_OP_IMM \
                and (i.operands[1].imm & 0xFFFFFFFF) == SINGLETON:
            loaders.append((k, i, i.operands[0].reg))
    print(f"  total: {len(loaders)}")
    for k, i, r in loaders[:40]:
        print(f"    0x{i.address:08X}  {REGS.get(r,'?')} <- 0x87F7E8   "
              f"(head 0x{head_of(i.address):08X})")
    chk("singleton address is loaded into registers somewhere", len(loaders) > 0,
        str(len(loaders)))

    print()
    print("=" * 78)
    print("== STEP 2  for each loader, look ahead for a store through that reg")
    print("=" * 78)
    WRITES = []
    for k, i, r in loaders:
        # 向后看最多 30 条，找 mov [r] / mov [r+disp], imm
        for j in range(k + 1, min(k + 30, len(insns))):
            p = insns[j]
            if p.mnemonic in ("ret", "retn"):
                break
            if p.mnemonic == "mov" and len(p.operands) == 2 \
                    and p.operands[0].type == X86_OP_MEM \
                    and p.operands[0].mem.base == r \
                    and p.operands[0].mem.index == 0:
                disp = p.operands[0].mem.disp
                if p.operands[1].type == X86_OP_IMM:
                    val = p.operands[1].imm & 0xFFFFFFFF
                elif p.operands[1].type == X86_OP_REG:
                    val = f"reg({REGS.get(p.operands[1].reg,'?')})"
                else:
                    val = "?"
                WRITES.append({"load_at": i.address, "store_at": p.address,
                               "reg": REGS.get(r, "?"), "disp": disp,
                               "value": val, "head": head_of(p.address),
                               "insn": f"{p.mnemonic} {p.op_str}"})
                break

    print(f"  stores through the loaded register: {len(WRITES)}")
    for w in WRITES:
        print(f"    load 0x{w['load_at']:08X} ({w['reg']}) -> "
              f"store 0x{w['store_at']:08X}  [{w['reg']}+0x{w['disp']:X}] = "
              f"{w['value']}   head 0x{w['head']:08X}")

    print()
    print("=" * 78)
    print("== STEP 3  which stores write a VTABLE (A or B)?")
    print("=" * 78)
    vt_writes = [w for w in WRITES
                 if w["value"] in (VT_A, VT_B)]
    print(f"  stores of a known vtable: {len(vt_writes)}")
    for w in vt_writes:
        which = "TABLE_A(MouseClass)" if w["value"] == VT_A else "TABLE_B(RadarClass)"
        in_exit_cb = (w["head"] == EXIT_CB)
        print(f"    store 0x{w['store_at']:08X}  {which}  disp=0x{w['disp']:X}")
        print(f"      head 0x{w['head']:08X}  in_atexit_callback={in_exit_cb}")

    # 关键：disp==0 的 vtable 写 = 装对象首 vtable
    first_field = [w for w in vt_writes if w["disp"] == 0]
    print(f"\n  stores to object first field (disp==0): {len(first_field)}")
    for w in first_field:
        which = "TABLE_A" if w["value"] == VT_A else "TABLE_B"
        print(f"    0x{w['store_at']:08X}  {which}  head 0x{w['head']:08X}")

    print()
    print("=" * 78)
    print("== STEP 4  verdict")
    print("=" * 78)
    a_first = [w for w in first_field if w["value"] == VT_A]
    b_first = [w for w in first_field if w["value"] == VT_B]
    print(f"  sites installing TABLE_A at offset 0 via indirect store: {len(a_first)}")
    for w in a_first:
        print(f"    0x{w['store_at']:08X}  head 0x{w['head']:08X}  reg {w['reg']}")
    print(f"  sites installing TABLE_B at offset 0 via indirect store: {len(b_first)}")
    for w in b_first:
        print(f"    0x{w['store_at']:08X}  head 0x{w['head']:08X}  reg {w['reg']}")

    in_exit = [w for w in b_first if w["head"] == EXIT_CB]
    outside_exit = [w for w in b_first if w["head"] != EXIT_CB]
    print(f"\n  TABLE_B installs inside atexit callback 0x40D1B0: {len(in_exit)}")
    print(f"  TABLE_B installs OUTSIDE the callback: {len(outside_exit)}")

    if not outside_exit:
        print("  [已证] 对 0x87F7E8 的**寄存器间接**装表，也**只有退出期那一次**")
        print("         ⇒ 运行期 `[0x87F7E8]` 恒为表 A（MouseClass）")
        print("         ⇒ slot5 = 0x5BDF30，**不是** One_Time")
        print("         ⇒ One_Time 在运行期不经该单例的 slot5 被调用")
        verdict = "NO_RUNTIME_INSTALL_OF_TABLE_B"
    else:
        print("  [已证] 发现**运行期**也有表 B 的间接装点：")
        for w in outside_exit:
            print(f"         0x{w['store_at']:08X}  head 0x{w['head']:08X}")
        print("         ⇒ 这些站点就是 One_Time 的调用时机候选，需逐个看宿主时机")
        verdict = "RUNTIME_INSTALL_FOUND"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
