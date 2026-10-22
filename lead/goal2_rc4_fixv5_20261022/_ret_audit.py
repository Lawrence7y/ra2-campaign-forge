# -*- coding: utf-8 -*-
"""v4 缺陷复核：cave 零值路径的 ret 尺寸 vs 函数真实 ret 尺寸，以及调用者返回值读取。

只读 gamemd.exe，不写任何二进制。
"""
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_REG
from capstone.x86_const import X86_REG_EAX, X86_REG_AX, X86_REG_AL, X86_REG_AH

DATA = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe").read_bytes()

pe = struct.unpack_from("<I", DATA, 0x3C)[0]
nsec = struct.unpack_from("<H", DATA, pe + 6)[0]
opt = pe + 24
base = struct.unpack_from("<I", DATA, opt + 28)[0]
sect = opt + struct.unpack_from("<H", DATA, pe + 20)[0]
SECS = {}
for i in range(nsec):
    o = sect + 40 * i
    name = DATA[o:o + 8].rstrip(b"\0").decode()
    vs, va, rs, ro = struct.unpack_from("<IIII", DATA, o + 8)
    SECS[name] = (base + va, rs, ro)
TVA, TRS, TRO = SECS[".text"]

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
EAXSET = {X86_REG_EAX, X86_REG_AX, X86_REG_AL, X86_REG_AH}


def read(va, n):
    for name, (sva, rs, ro) in SECS.items():
        if sva <= va < sva + rs:
            off = ro + (va - sva)
            return DATA[off:off + n]
    return b""


def e8_callers(target):
    hits = []
    for o in range(TRO, TRO + TRS - 4):
        if DATA[o] != 0xE8:
            continue
        rel = struct.unpack_from("<i", DATA, o + 1)[0]
        if ((o - TRO + TVA + 5 + rel) & 0xFFFFFFFF) == target:
            hits.append(o - TRO + TVA)
    return hits


def real_ret_size(fn_va):
    for i in MD.disasm(read(fn_va, 0x800), fn_va):
        if i.mnemonic in ("ret", "retf"):
            return int(i.op_str) if i.op_str else 0
    return None


CAVES = {
    "0x7241A0": "85c9740a8a44240456e9974172f031c0c20400",
    "0x724200": "85c9740a5355568bf1e9b74172f031c0c20400",
    "0x724520": "85c9740f8b442404898128020000e9974472f031c0c20400",
    "0x724530": "85c9740b8b8128020000e9674472f031c0c20400",
    "0x724540": "85c9740b8b812c020000e9374472f031c0c20400",
    "0x724580": "85c9740d535556578b7c2414e9374472f031c0c20400",
    "0x724730": "85c9740c83ec0c558be956e9a74572f031c0c20400",
    "0x724C00": "85c9740a8b510433c0e9374a72f031c0c20400",
}
VA = {k: int(k, 16) for k in CAVES}

print("=" * 78)
print("== A  cave 零值路径 ret 尺寸 vs 函数真实 ret 尺寸")
print("=" * 78)
bad = []
for k, h in CAVES.items():
    ins = list(MD.disasm(bytes.fromhex(h), 0x10000000))
    last = ins[-1]
    cave_ret = 0 if not last.op_str else int(last.op_str)
    fn_ret = real_ret_size(VA[k])
    ok = cave_ret == fn_ret
    print("  %-10s cave末条=%-9s ret=%-2d | 真实 ret=%-2d | %s"
          % (k, last.mnemonic, cave_ret, fn_ret, "OK" if ok else "*** MISMATCH ***"))
    if not ok:
        bad.append((k, cave_ret, fn_ret))
print()
print("  MISMATCH = %d  %s" % (len(bad), bad))

print()
print("=" * 78)
print("== B  调用者是否真读返回值（严格：任何把 eax 族当源的操作）")
print("=" * 78)
total_reads = 0
for k in CAVES:
    cs = e8_callers(VA[k])
    reads = []
    for c in cs:
        nxt = list(MD.disasm(read(c + 5, 16), c + 5))
        if not nxt:
            continue
        i0 = nxt[0]
        rd = False
        for idx, op in enumerate(i0.operands):
            if op.type != X86_OP_REG or op.reg not in EAXSET:
                continue
            if i0.mnemonic in ("mov", "lea", "pop") and idx == 0:
                continue
            if (i0.mnemonic == "xor" and len(i0.operands) == 2
                    and i0.operands[1].type == X86_OP_REG
                    and i0.operands[1].reg == i0.operands[0].reg):
                continue
            rd = True
        if rd:
            reads.append((hex(c), i0.mnemonic, i0.op_str))
    total_reads += len(reads)
    print("  %-10s callers=%-2d  真读eax=%-2d  %s" % (k, len(cs), len(reads), reads[:3]))
print()
print("  ★ 真读返回值站点合计 = %d" % total_reads)
