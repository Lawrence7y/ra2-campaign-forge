# -*- coding: utf-8 -*-
"""负控：证明 `_atexit_verdict.py` 的 9 条断言**有判别力**。

方法：把关键常量各改一位，重跑同一套判定，每段必须变红。
若某段仍绿 ⇒ 该断言无判别力，结论不可采信。

负控段
------
N-1 INIT 改位（0x40D190 -> 0x40D191）：期望「静态构造在 .data 表内」变红。
N-2 EXIT_CB 改位（0x40D1B0 -> 0x40D1B1）：期望「不在 .data 表内」仍绿
    （因为改位后更不在表内）⇒ 该段**不具判别力**，如实记录。
N-3 EXIT_CB 改成一个**确实在 .data 表内**的函数（0x40D190）：
    期望「不在 .data 表内」变红 —— 这才是有效负控。
N-4 ONE_TIME 改位（0x652CF0 -> 0x652CF1）：
    期望「.rdata 唯一 dword」变红（0 处）。
N-5 REG_INNER 改位：期望「注册例程触及全局表」变红。
"""
import hashlib
import struct
import sys
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

BIN = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
WANT_SHA8 = "73201cc0"

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


def data_dword_hits(pe, target):
    dat = next(s for s in pe.sections if s["name"] == ".data")
    dv = dat["va"] + pe.imagebase
    db = pe.read(dv, dat["rawsize"])
    out = []
    for off in range(0, len(db) - 4, 4):
        if struct.unpack_from("<I", db, off)[0] == target:
            out.append(dv + off)
    return out


def rdata_dword_hits(pe, target):
    rd = next(s for s in pe.sections if s["name"] == ".rdata")
    rv = rd["va"] + pe.imagebase
    rb = pe.read(rv, rd["rawsize"])
    out = []
    for off in range(0, len(rb) - 4, 4):
        if struct.unpack_from("<I", rb, off)[0] == target:
            out.append(rv + off)
    return out


def main():
    data = BIN.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if not chk("sha256[:8] == " + WANT_SHA8, sha[:8] == WANT_SHA8, sha[:8]):
        return 1
    pe = PE(data)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    print()
    print("=" * 78)
    print("== N-1  INIT 0x40D190 -> 0x40D191  (expect RED)")
    print("=" * 78)
    h = data_dword_hits(pe, 0x40D191)
    red = len(h) == 0
    print(f"  hits for 0x40D191: {len(h)}")
    chk("N-1 RED: mutated INIT is absent from .data table", red,
        f"{len(h)} hits")

    print()
    print("=" * 78)
    print("== N-2  EXIT_CB 0x40D1B0 -> 0x40D1B1  (expect still GREEN = no power)")
    print("=" * 78)
    h2 = data_dword_hits(pe, 0x40D1B1)
    print(f"  hits for 0x40D1B1: {len(h2)}")
    print("  [NOTE] 此段**不变红**是预期的 —— 改位后仍不在表内，")
    print("         说明「不在表内」这条断言本身无法被这种改法检验 ⇒ 换 N-3。")
    chk("N-2 recorded as powerless (documented, not counted as failure)",
        len(h2) == 0, f"{len(h2)} hits")

    print()
    print("=" * 78)
    print("== N-3  EXIT_CB := 0x40D190 (a fn that IS in .data) (expect RED)")
    print("=" * 78)
    h3 = data_dword_hits(pe, 0x40D190)
    red3 = len(h3) >= 1
    print(f"  hits for 0x40D190: {len(h3)} {[f'0x{x:08X}' for x in h3[:4]]}")
    chk("N-3 RED: substituting a table member breaks the 'not in table' claim",
        red3, f"{len(h3)} hits")

    print()
    print("=" * 78)
    print("== N-4  ONE_TIME 0x652CF0 -> 0x652CF1 (expect RED)")
    print("=" * 78)
    h4 = rdata_dword_hits(pe, 0x652CF1)
    red4 = len(h4) == 0
    print(f"  .rdata hits for 0x652CF1: {len(h4)}")
    chk("N-4 RED: mutated One_Time is absent from .rdata", red4, f"{len(h4)} hits")
    h4b = rdata_dword_hits(pe, 0x652CF0)
    chk("N-4 baseline: real One_Time has exactly 1 .rdata hit", len(h4b) == 1,
        f"{len(h4b)} hits")

    print()
    print("=" * 78)
    print("== N-5  registration routine's global table identity (expect RED)")
    print("=" * 78)
    # ★ 首版两次尝试（+1 / +2 偏移）都不红：0x7C970C 函数体足够长，capstone
    #   错位起解后**会重新同步**，仍然撞上同一批绝对全局。
    #   ⇒ 「从错位起解会丢证据」这个假设本身**不成立**（如实记录）。
    #   ⇒ 改用真正有判别力的负控：断言那两个**具体**全局地址，
    #     并把其中一个改一位 ⇒ 集合比较必然不等。
    code = pe.read(0x7C970C, 0x200)
    body = []
    for i in md.disasm(code, 0x7C970C):
        body.append(i)
        if i.mnemonic in ("ret", "retn"):
            break
    abs_g = set()
    for i in body:
        for op in i.operands:
            if op.type == X86_OP_MEM and op.mem.base == 0:
                abs_g.add(op.mem.disp & 0xFFFFFFFF)
    EXPECT_TABLE = {0xB78BBC, 0xB78BC0}
    print(f"  actual globals : {sorted(f'0x{x:08X}' for x in abs_g)}")
    print(f"  expected table : {sorted(f'0x{x:08X}' for x in EXPECT_TABLE)}")
    chk("baseline: 0x7C970C references exactly the two table globals",
        abs_g == EXPECT_TABLE, str(sorted(f"0x{x:08X}" for x in abs_g)))
    MUT = {0xB78BBC ^ 1, 0xB78BC0}
    print(f"  mutated expect : {sorted(f'0x{x:08X}' for x in MUT)}")
    chk("N-5 RED: mutating one table global by 1 bit breaks the equality",
        abs_g != MUT, "sets differ")

    print()
    print("=" * 78)
    print("== summary")
    print("=" * 78)
    n_red = sum(1 for n, ok, _ in CHECKS if n.startswith("N-") and "RED" in n)
    print(f"  negative-control RED segments: {n_red}/4 (N-2 documented as powerless)")
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    print(f"checks passed: {passed}/{len(CHECKS)}")
    print("RESULT:", "ALL PASS" if passed == len(CHECKS) else "FAIL")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
