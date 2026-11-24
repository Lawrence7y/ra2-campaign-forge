"""全 .text 单遍索引：直接调用、绝对内存写、结构体/寄存器 vtable 安装、push+call atexit 组合。
输出 index.json 供后续查询。
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C
import capstone

X86 = capstone.x86
TLO, THI = C.TLO, C.THI
buf = C.read(TLO, THI - TLO)

calls = []          # (site, target)  E8 rel32
jmp_raw = []        # (site, target)  E9 rel32 jmp
mov_abs_imm = []    # (site, imm, memdisp)
vinstall = []       # (site, imm, memop_str)  mov [reg+disp], imm32
push_imm = []       # (site, imm)
n = 0
for ins in C.md.disasm(buf, TLO):
    n += 1
    a = ins.address
    if ins.mnemonic == "call":
        if ins.operands and ins.operands[0].type == X86.X86_OP_IMM:
            calls.append((a, ins.operands[0].imm & 0xFFFFFFFF))
    elif ins.mnemonic in ("jmp",) and ins.operands and ins.operands[0].type == X86.X86_OP_IMM:
        jmp_raw.append((a, ins.operands[0].imm & 0xFFFFFFFF))
    elif ins.mnemonic == "push" and ins.operands and ins.operands[0].type == X86.X86_OP_IMM:
        push_imm.append((a, ins.operands[0].imm & 0xFFFFFFFF))
    elif ins.mnemonic == "mov" and len(ins.operands) == 2:
        d, s = ins.operands
        if d.type == X86.X86_OP_MEM and s.type == X86.X86_OP_IMM:
            imm = s.imm & 0xFFFFFFFF
            base = d.mem.base
            if base == 0:
                mov_abs_imm.append((a, imm, d.mem.disp & 0xFFFFFFFF))
            vinstall.append((a, imm, f"{ins.reg_name(d.mem.base)}+{d.mem.disp & 0xFFFFFFFF:#x}"))

idx = {
    "n_insn": n,
    "calls": calls,
    "jmp": jmp_raw,
    "mov_abs_imm": mov_abs_imm,
    "vinstall": vinstall,
    "push_imm": push_imm,
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.json")
json.dump(idx, open(out, "w"))
print("instructions:", n, "calls:", len(calls), "vinstall:", len(vinstall),
      "mov_abs_imm:", len(mov_abs_imm), "push_imm:", len(push_imm))
