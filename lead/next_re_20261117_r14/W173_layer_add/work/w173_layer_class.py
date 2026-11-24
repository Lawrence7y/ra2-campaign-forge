# -*- coding: utf-8 -*-
"""W173 层号 0..4 <-> 对象类别：
 0x4A9720 SetLayer 的层号来自 call [vptr+0x78]。扫所有虚表的 slot+0x78 实现，
 反汇编每个实现看它返回哪个层号常量；用 RTTI (vftable[-1] -> COL -> type descriptor) 推类名。
 另：查 0x54B750 (mov [esi+0x94],0 所在函数) 的对象类别。
"""
from __future__ import annotations
import os
import sys
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import w173_common as C

E = C.EVID
SLOT = 0x78


def rtti_name(b, vft):
    try:
        col = b.u32(vft - 4)
        if not (0x400000 <= col < 0x900000):
            return None
        td = b.u32(col + 0xC)
        if not (0x400000 <= td < 0x900000):
            return None
        raw = b.read(td + 8, 60)
        s = raw.split(b"\x00")[0]
        txt = s.decode("ascii", errors="replace")
        if txt.startswith(".?AV"):
            return txt[4:].split("@@")[0]
        return txt
    except Exception:
        return None


def find_vftables(b):
    found = []
    seen = set()
    for sec in b.sections:
        if sec["name"] == ".text":
            continue
        buf = b.pe.__data__[sec["raw"]:sec["raw"] + sec["rawsize"]]
        n = len(buf) // 4
        run = 0
        text_end = C.stats()["text_end"]   # 0x7E4000 —— COL 指针(0x7Fxxxx)必须排除
        for k in range(n):
            v = struct.unpack_from("<I", buf, k * 4)[0]
            if 0x401000 <= v < text_end:
                run += 1
            else:
                if run >= 8:
                    base = sec["va"] + (k - run) * 4
                    if base not in seen:
                        found.append(base)
                        seen.add(base)
                run = 0
        if run >= 8:
            base = sec["va"] + (n - run) * 4
            if base not in seen:
                found.append(base)
                seen.add(base)
    return sorted(found)


def imm_return(va, maxins=14):
    b = C.B()
    m = C.md(True)
    try:
        data = b.read(va, 80)
    except Exception:
        return None, ""
    seq = []
    val = None
    for ins in m.disasm(data, va):
        if ins.id == 0:
            seq.append("%08X  .byte %s" % (ins.address, ins.bytes.hex()))
            continue
        seq.append("%08X  %-7s %s" % (ins.address, ins.mnemonic, ins.op_str))
        if ins.mnemonic == "mov" and len(ins.operands) >= 2:
            op0, op1 = ins.operands[0], ins.operands[1]
            if op0.type == C.X.X86_OP_REG and C._MD.reg_name(op0.reg) in ("eax", "ax", "al"):
                if op1.type == C.X.X86_OP_IMM:
                    val = op1.imm & 0xFFFFFFFF
                elif op1.type == C.X.X86_OP_REG and C._MD.reg_name(op1.reg) == "eax":
                    pass
        elif ins.mnemonic == "xor" and len(ins.operands) == 2:
            op0, op1 = ins.operands[0], ins.operands[1]
            if (op0.type == C.X.X86_OP_REG and op1.type == C.X.X86_OP_REG
                    and C._MD.reg_name(op0.reg) == C._MD.reg_name(op1.reg) == "eax"):
                val = 0
        if ins.mnemonic == "ret":
            break
        if len(seq) >= maxins:
            break
    return val, "\n".join(seq)


def main():
    b = C.B()
    L = ["=" * 95, "W173 层号来源：call [vptr+0x78] @ 0x4A973D（SetLayer 取层号）"]
    vfts = find_vftables(b)
    L.append("发现虚表数(>=8连续代码指针): %d" % len(vfts))
    rows = []
    for vft in vfts:
        try:
            fn = b.u32(vft + SLOT)
        except Exception:
            continue
        if not (0x401000 <= fn <= 0x900000):
            continue
        val, code = imm_return(fn)
        name = rtti_name(b, vft)
        rows.append((vft, fn, val, name, code))
    rows.sort(key=lambda r: (r[2] is None, r[2] if r[2] is not None else -1, r[0]))
    L.append("含 slot+0x78 的虚表数: %d" % len(rows))
    L.append("")
    L.append("层号 | vftable | slot+0x78实现 | RTTI类名 | 返回常量")
    bylayer = {}
    for vft, fn, val, name, code in rows:
        L.append("%s | %08X | %08X | %s | %s" % (
            ("L%d" % val) if val is not None and 0 <= val <= 4 else "?",
            vft, fn, name or "?", val))
        if val is not None and 0 <= val <= 4:
            bylayer.setdefault(val, []).append((vft, fn, name))
    L.append("")
    for lay in range(5):
        L.append("层 %d: %s" % (lay, ", ".join(
            "%08X(fn=%08X,%s)" % (v, f, n or "?") for v, f, n in bylayer.get(lay, [])) or "无"))
    L.append("")
    L.append("=" * 95)
    L.append("各 slot+0x78 实现的逐条反汇编（前14条，逐字符核对返回值）")
    for vft, fn, val, name, code in rows:
        L.append("-" * 90)
        L.append("vft=%08X fn=%08X ret=%s class=%s" % (vft, fn, val, name))
        L.append(code)
    C.write_text(os.path.join(E, "w173_layer_class.txt"), L)

    L2 = ["=" * 95, "fn 0x54B750 (mov [esi+0x94],0 @0x54B76C) 完整 + 调用者"]
    m = C.md(True)
    data = b.read(0x54B750, 0x180)
    for ins in m.disasm(data, 0x54B750):
        L2.append("%08X  %s %s%s" % (ins.address, ins.mnemonic, ins.op_str,
                                     "  ; .byte" if ins.id == 0 else ""))
    C.write_text(os.path.join(E, "w173_fn54B750.txt"), L2)
    print("layer_class: vftables=%d with slot78=%d" % (len(vfts), len(rows)))


if __name__ == "__main__":
    main()
