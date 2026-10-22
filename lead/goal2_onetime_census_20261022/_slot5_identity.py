# -*- coding: utf-8 -*-
"""待办 9 第三段（决定性）：表A slot5 = 0x5BDF30 的身份，与 One_Time 的关系。

为什么这是决定性的
------------------
`call [reg+0x14]` 是**跨类通用**槽位。273 处站点里，只有当对象的运行时虚表
恰为 0x7F0344（RadarClass 表B）时，slot5 才等于 One_Time(0x652CF0)；
若对象是表A(0x7E1964)，slot5 = 0x5BDF30（子代理已测）。

于是分岔 A/B 的判定变成：**0x5BDF30 是什么函数？**
- 若 0x5BDF30 也是「One_Time」语义（对象一次性初始化），则 slot5 是
  ObjectClass 体系的 One_Time 槽，调用者=对象初始化遍历 ⇒ 每次载图都会跑 ⇒ 分岔 B。
- 若 0x5BDF30 是别的东西（如 MouseClass 的每帧 AI），则 slot5 语义随类而变，
  不能靠通用槽反推 ⇒ 必须另找 RadarClass 专属调用点。

同时补：One_Time 与 0x5BDF30 是否共享基类实现（同父函数）。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"
TABLE_A_SLOT5 = 0x5BDF30
ONE_TIME = 0x652CF0
VT_A = 0x7E1964
VT_B = 0x7F0344

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


def dump_fn(pe, md, va, maxbytes=0x140, label=""):
    """从 va 起解码到第一个 ret，打印并返回 (insns, strings)。"""
    code = pe.read(va, maxbytes)
    if code is None:
        print(f"  !! cannot read at 0x{va:X}")
        return [], []
    out = []
    for i in md.disasm(code, va):
        out.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    strings = []
    for i in out:
        for op in i.operands:
            if i.mnemonic == "push" and op.type == X86_OP_IMM:
                v = op.imm & 0xFFFFFFFF
                if 0x7E1000 <= v < 0xB96000:
                    b = pe.read(v, 96)
                    if b:
                        z = b.split(b"\x00")[0]
                        if 4 <= len(z) <= 80 and all(32 <= c < 127 or c in (9, 10) for c in z):
                            strings.append((i.address, v, z.decode("ascii", "replace")))
    print(f"  --- {label} 0x{va:08X}: {len(out)} insns, {len(strings)} strings")
    for a, v, s in strings:
        print(f"      0x{a:08X} push 0x{v:08X}  {s!r}")
    return out, strings


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
    print("== STEP 1  table A slot5 = 0x5BDF30 identity")
    print("=" * 78)
    a_insns, a_str = dump_fn(pe, md, TABLE_A_SLOT5, 0x180, "TABLE_A slot5")

    a_is_onetime = any("One_Time" in s for _, _, s in a_str)
    chk("0x5BDF30 self-reports 'One_Time' in a debug string", a_is_onetime,
        a_str[0][2] if a_str else "no strings")

    print()
    print("=" * 78)
    print("== STEP 2  One_Time (0x652CF0) for comparison")
    print("=" * 78)
    b_insns, b_str = dump_fn(pe, md, ONE_TIME, 0x120, "TABLE_B slot5")

    print()
    print("=" * 78)
    print("== STEP 3  do they share a base implementation?")
    print("=" * 78)
    # 取各自 body 的 call 目标
    def calls(insns):
        r = []
        for i in insns:
            if i.mnemonic == "call" and i.operands and i.operands[0].type == X86_OP_IMM:
                r.append(i.operands[0].imm & 0xFFFFFFFF)
        return r

    a_calls = calls(a_insns)
    b_calls = calls(b_insns)
    print(f"  0x5BDF30 calls: {[f'0x{x:08X}' for x in a_calls]}")
    print(f"  0x652CF0 calls: {[f'0x{x:08X}' for x in b_calls]}")
    shared = set(a_calls) & set(b_calls)
    print(f"  shared call targets: {[f'0x{x:08X}' for x in sorted(shared)]}")

    # 前 8 条指令字节是否相同（同构但不同函数会不同）
    a_pref = bytes().join(i.bytes for i in a_insns[:6])
    b_pref = bytes().join(i.bytes for i in b_insns[:6])
    print(f"  0x5BDF30 first6 bytes: {a_pref.hex()}")
    print(f"  0x652CF0 first6 bytes: {b_pref.hex()}")
    chk("the two slot5 targets are distinct functions (prefixes differ)",
        a_pref != b_pref, "differ" if a_pref != b_pref else "IDENTICAL")

    print()
    print("=" * 78)
    print("== STEP 4  does 0x5BDF30 also call L3 (0x4A8850 / 0x4A8960)?")
    print("=" * 78)
    a_l3 = [x for x in a_calls if x in (0x4A8850, 0x4A8960)]
    b_l3 = [x for x in b_calls if x in (0x4A8850, 0x4A8960)]
    print(f"  0x5BDF30 L3 calls: {[f'0x{x:08X}' for x in a_l3]}")
    print(f"  0x652CF0 L3 calls: {[f'0x{x:08X}' for x in b_l3]}")
    chk("One_Time calls L3 sibling 0x4A8850", 0x4A8850 in b_calls,
        "yes" if 0x4A8850 in b_calls else "no")

    print()
    print("=" * 78)
    print("== STEP 5  verdict")
    print("=" * 78)
    if a_is_onetime:
        print("  [已证] 0x5BDF30 自报名为 One_Time 语义 ⇒ slot5 是 ObjectClass 体系的")
        print("         「对象一次性初始化」槽。调用者=对象初始化遍历 ⇒ 每次场景加载都跑")
        print("         ⇒ 分岔 B 成立（One_Time 会被重跑）。")
        verdict = "B_CONFIRMED"
    else:
        print("  [已证] 0x5BDF30 不是 One_Time 语义（自报名不同/无该串）。")
        print("         ⇒ slot5 语义随类而变，通用槽普查无法反推 RadarClass 的调用者。")
        print("         ⇒ One_Time 是否重跑**不能**由 273 处通用槽判定，仍属 [未定]。")
        print("         ⇒ 需要 RadarClass 专属路径（或真机断点 0x652CF0）才能定 A/B。")
        verdict = "UNDETERMINED_SLOT_IS_CLASS_SPECIFIC"

    print()
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print(f"verdict: {verdict}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
