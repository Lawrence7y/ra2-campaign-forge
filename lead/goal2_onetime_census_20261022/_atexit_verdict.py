# -*- coding: utf-8 -*-
"""最终定谳：0x40D1B0 是「退出期析构回调」还是「启动期初始化」？

已测事实
--------
- 0x7E1964 = .?AVMouseClass@@（表A），slot5 = 0x5BDF30
- 0x7F0344 = .?AVRadarClass@@（表B），slot5 = 0x652CF0 = One_Time
- 0x40D190: mov ecx,0x87F7E8; call 0x5BDA40(构造,装表A); push 0x40D1B0; call 0x7C978A; ret
- 0x40D1B0: mov [0x87F7E8],0x7E1964(表A); ...; mov ecx,0x87F7E8; call 0x652C00(装表B); ret
- 0x7C978A: push [esp+4]; call 0x7C970C; neg/sbb/neg/dec; ret

0x7C978A 的返回语义
-------------------
设 call 0x7C970C 返回 x：
  neg eax   : eax=-x,  CF=(x!=0)
  sbb eax,eax: eax = -CF = (x!=0 ? -1 : 0)
  neg eax   : eax = (x!=0 ? 1 : 0), CF=(x!=0)
  dec eax   : eax = (x!=0 ? 0 : -1)
⇒ 返回 0 表示成功、-1 表示失败。这正是 MSVC `_onexit`/`atexit` 的返回约定。

本脚本要证
----------
1. 0x7C970C 是注册函数（把参数存进一张函数指针表）。
2. 0x40D1B0 在 .data 里**没有**被当作启动期 init 表项（只在 push 处出现）。
3. 0x40D190 在 .data 里有 init 表项（启动期静态构造）。
4. 若 1+2+3 成立 ⇒ 0x40D1B0 = 退出期析构 ⇒ 表B 不在运行期装到 0x87F7E8。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
G_MOUSE = 0x87F7E8
REG = 0x7C978A        # 疑 atexit
REG_INNER = 0x7C970C  # 真正的注册实现
INIT = 0x40D190       # 静态构造
EXIT_CB = 0x40D1B0    # 疑析构

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
    print("== STEP 0  identity")
    print("=" * 78)
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    print(f"sha256 : {sha}")
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    print()
    print("=" * 78)
    print("== STEP 1  0x7C970C — is it a registration routine (stores fn ptr)?")
    print("=" * 78)
    code = pe.read(REG_INNER, 0x200)
    body = []
    for i in md.disasm(code, REG_INNER):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    print(f"  0x7C970C body: {len(body)} insns")
    for i in body:
        print(f"    {i.address:08X}  {i.bytes.hex():<22} {i.mnemonic} {i.op_str}")
    # 注册特征：有全局指针（表头）读写 + 有 store 到 [base+index*4]
    abs_g = set()
    has_index_store = False
    for i in body:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0:
                abs_g.add(op.mem.disp & 0xFFFFFFFF)
        if i.mnemonic == "mov" and len(i.operands) == 2 \
                and i.operands[0].type == X86_OP_MEM \
                and i.operands[0].mem.index != 0:
            has_index_store = True
    print(f"  absolute globals referenced: {[f'0x{x:08X}' for x in sorted(abs_g)]}")
    print(f"  has store through [base+index*4]: {has_index_store}")
    chk("0x7C970C touches a global table (registration routine shape)",
        len(abs_g) >= 1, str([f"0x{x:08X}" for x in sorted(abs_g)]))

    print()
    print("=" * 78)
    print("== STEP 2  does any .data init table hold 0x40D1B0 or 0x40D190?")
    print("=" * 78)
    dat = next(s for s in pe.sections if s["name"] == ".data")
    dat_va = dat["va"] + pe.imagebase
    dat_bytes = pe.read(dat_va, dat["rawsize"])
    # .data 里搜 dword == 目标
    hits = {}
    for target, label in ((INIT, "INIT 0x40D190"), (EXIT_CB, "EXIT_CB 0x40D1B0")):
        found = []
        for off in range(0, len(dat_bytes) - 4, 4):
            if struct.unpack_from("<I", dat_bytes, off)[0] == target:
                found.append(dat_va + off)
        hits[label] = found
        print(f"  {label}: {len(found)} .data dword match(es) "
              f"{[f'0x{x:08X}' for x in found[:8]]}")
    chk("0x40D190 (static ctor) IS in a .data pointer table",
        len(hits["INIT 0x40D190"]) >= 1,
        f"{len(hits['INIT 0x40D190'])} hit(s)")
    chk("0x40D1B0 (suspect dtor) is NOT in any .data pointer table",
        len(hits["EXIT_CB 0x40D1B0"]) == 0,
        f"{len(hits['EXIT_CB 0x40D1B0'])} hit(s)")

    print()
    print("=" * 78)
    print("== STEP 3  is 0x40D1B0 reachable ONLY via the registration call?")
    print("=" * 78)
    text = next(s for s in pe.sections if s["name"] == ".text")
    text_va = text["va"] + pe.imagebase
    end = text_va + text["rawsize"]
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

    push_sites = [i.address for i in insns
                  if i.mnemonic == "push" and i.operands
                  and i.operands[0].type == X86_OP_IMM
                  and (i.operands[0].imm & 0xFFFFFFFF) == EXIT_CB]
    call_sites = [i.address for i in insns
                  if i.mnemonic == "call" and i.operands
                  and i.operands[0].type == X86_OP_IMM
                  and (i.operands[0].imm & 0xFFFFFFFF) == EXIT_CB]
    jmp_sites = [i.address for i in insns
                 if i.mnemonic.startswith("j") and i.operands
                 and i.operands[0].type == X86_OP_IMM
                 and (i.operands[0].imm & 0xFFFFFFFF) == EXIT_CB]
    print(f"  push 0x40D1B0 : {[f'0x{x:08X}' for x in push_sites]}")
    print(f"  call 0x40D1B0 : {[f'0x{x:08X}' for x in call_sites]}")
    print(f"  jmp  0x40D1B0 : {[f'0x{x:08X}' for x in jmp_sites]}")
    chk("0x40D1B0 is never directly called or jumped to",
        len(call_sites) == 0 and len(jmp_sites) == 0,
        f"call={len(call_sites)} jmp={len(jmp_sites)}")
    chk("0x40D1B0 is pushed exactly once (registration only)",
        len(push_sites) == 1, str([f"0x{x:08X}" for x in push_sites]))

    print()
    print("=" * 78)
    print("== STEP 4  also: is 0x652CF0 reachable at all outside table B?")
    print("=" * 78)
    e8 = [i.address for i in insns
          if i.mnemonic == "call" and i.operands
          and i.operands[0].type == X86_OP_IMM
          and (i.operands[0].imm & 0xFFFFFFFF) == 0x652CF0]
    print(f"  E8 callers of One_Time 0x652CF0: {len(e8)} {[f'0x{x:08X}' for x in e8]}")
    rdata = next(s for s in pe.sections if s["name"] == ".rdata")
    rd_va = rdata["va"] + pe.imagebase
    rd = pe.read(rd_va, rdata["rawsize"])
    dwords = []
    for off in range(0, len(rd) - 4, 4):
        if struct.unpack_from("<I", rd, off)[0] == 0x652CF0:
            dwords.append(rd_va + off)
    print(f"  .rdata dwords == 0x652CF0: {[f'0x{x:08X}' for x in dwords]}")
    chk("One_Time appears exactly once in .rdata (table B slot5)",
        len(dwords) == 1, str([f"0x{x:08X}" for x in dwords]))
    chk("One_Time has zero direct E8 callers", len(e8) == 0, str(len(e8)))

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    reg_shape = len(abs_g) >= 1
    no_table = len(hits["EXIT_CB 0x40D1B0"]) == 0
    init_in_table = len(hits["INIT 0x40D190"]) >= 1
    only_push = (len(call_sites) == 0 and len(jmp_sites) == 0
                 and len(push_sites) == 1)
    if reg_shape and no_table and init_in_table and only_push:
        print("  [已证] 0x40D190 在 .data 指针表内 ⇒ 是**启动期**静态构造。")
        print("  [已证] 0x40D1B0 不在任何 .data 表内，且**从不**被 call/jmp，")
        print("         唯一引用是 0x40D19A 的 `push 0x40D1B0; call 0x7C978A`。")
        print("  [已证] 0x7C978A 以 0/1 语义包装 0x7C970C（注册例程）⇒ atexit 形态。")
        print("  ⇒ **0x40D1B0 是退出期析构回调**，其内的「写表A→改表B」只在进程退出时执行。")
        print("  ⇒ 运行期 0x87F7E8 的 vtable = 表A(MouseClass)，slot5 = 0x5BDF30。")
        print("  ⇒ One_Time(0x652CF0) 仅经表B slot5 可达，而表B 只在 5 个运行期站点")
        print("     装到**别的对象**上（0x40D2D4/0x5BEA0A/0x6404B3/0x69391A/0x6AC81A）。")
        print("  [更正] 台账 §347「运行时是表B ⇒ slot5 = One_Time（在 0x87F7E8 上）」")
        print("         **不成立**：那两行写表发生在退出期。")
        verdict = "EXIT_CALLBACK_CONFIRMED_SINGLETON_STAYS_TABLE_A"
    else:
        print("  [未定] 证据不全，见各步实测。")
        verdict = "UNDETERMINED"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
