"""全 .text 单遍扫描：vtable 安装点 / 间接调用 / 跳表 / 直接调用。
skipdata=True。结果缓存 JSON。
"""
import json, os, struct
import core as C

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan.json")

installs = []   # {site, imm, dst, ins}
vcalls = []     # {site, reg, disp, ins}
jmptbl = []     # {site, table, scale, index, ins}
calls = []      # {site, target}
atexit = []     # {site, fn, after}

lo, hi = C.TEXT_LO, C.TEXT_HI
buf = C.read(lo, hi - lo)


def is_vt_candidate(v):
    if not (C.sec_of(v) and C.sec_of(v)[0] in (".rdata", ".data")):
        return False
    return C.rtti_of_vtable(v) is not None


n = 0
for ins in C.md.disasm(buf, lo):
    n += 1
    a = ins.address
    if ins.id == 0:  # skipdata 伪指令 (.byte)
        continue
    ops = ins.operands
    if ins.mnemonic == "mov" and len(ops) == 2 and ops[0].type == C.capstone.x86.X86_OP_MEM \
            and ops[1].type == C.capstone.x86.X86_OP_IMM:
        v = ops[1].imm & 0xFFFFFFFF
        if is_vt_candidate(v):
            m = ops[0].mem
            base = ins.reg_name(m.base) if m.base else ""
            idx = ins.reg_name(m.index) if m.index else ""
            dst = f"[{base}{'+' + hex(m.disp) if m.disp else ''}{'*' + idx if idx else ''}]" if (base or idx) else f"[{hex(m.disp & 0xFFFFFFFF)}]"
            installs.append({"site": a, "imm": v, "dst": dst,
                             "abs": (m.base == 0 and m.index == 0),
                             "disp": m.disp & 0xFFFFFFFF, "ins": C.fmt(ins)})
    elif ins.mnemonic == "call" and len(ops) == 1:
        if ops[0].type == C.capstone.x86.X86_OP_MEM:
            m = ops[0].mem
            vcalls.append({"site": a, "base": ins.reg_name(m.base) if m.base else "",
                           "index": ins.reg_name(m.index) if m.index else "",
                           "disp": m.disp, "ins": C.fmt(ins)})
        elif ops[0].type == C.capstone.x86.X86_OP_IMM:
            calls.append({"site": a, "target": ops[0].imm & 0xFFFFFFFF})
    elif ins.mnemonic == "jmp" and len(ops) == 1 and ops[0].type == C.capstone.x86.X86_OP_MEM:
        m = ops[0].mem
        jmptbl.append({"site": a, "base": ins.reg_name(m.base) if m.base else "",
                       "index": ins.reg_name(m.index) if m.index else "",
                       "scale": m.scale, "disp": m.disp & 0xFFFFFFFF, "ins": C.fmt(ins)})

print("instructions:", n)
print("installs:", len(installs), "vcalls:", len(vcalls), "jmptbl:", len(jmptbl), "calls:", len(calls))
json.dump({"installs": installs, "vcalls": vcalls, "jmptbl": jmptbl, "calls": calls},
          open(OUT, "w"), indent=0)
print("->", OUT)
