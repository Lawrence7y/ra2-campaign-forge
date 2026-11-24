# -*- coding: utf-8 -*-
"""全面重扫安装点：按 atlas 函数边界反汇编，找所有 mov [mem],imm 且 imm==目标 vt。
覆盖 C7 05(abs)/C7 4x(disp8)/C7 8x(disp32)/C7 0x(modrm no disp) 全形式。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

WORK = os.path.dirname(os.path.abspath(__file__))
REFS = json.load(open(os.path.join(WORK,"refs.json"),encoding="utf-8"))

# 收集所有目标 vt
vts = {}
for e,v in REFS.items():
    for s in v.get("slots",[]):
        if s.get("vtable_base"):
            vts[int(s["vtable_base"],16)] = e
# 00468670 手动补（k=124 超窗）
vts[0x007E46E4] = "004684E0"

targets = set(vts)
# 按函数边界反汇编整个 .text，收集 mov [mem],imm 命中
hits = {vt:[] for vt in targets}
FUNCS = sorted((int(k,16), int(info["size"])) for k,info in R.ATLAS.items())
for fva, fsz in FUNCS:
    if fsz<=0: continue
    for ins in R.disasm_body(fva, fsz):
        if ins.mnemonic!="mov" or len(ins.operands)!=2: continue
        a,b = ins.operands
        if a.type!=X86_OP_MEM or b.type!=X86_OP_IMM: continue
        imm = b.imm & 0xFFFFFFFF
        if imm in targets:
            hits[imm].append((ins.address, fva, fsz, ins.op_str, ins.bytes.hex()))

for vt in sorted(targets):
    print("\n### vt=%08X (row %s) install sites = %d" % (vt, vts[vt], len(hits[vt])))
    for a,fva,fsz,op,by in hits[vt]:
        print("  @%08X host=%08X sz=%d atexit=%s in_func_self=%s  %s  [%s]" % (
            a,fva,fsz, C2.is_atexit_registered(fva), (fva<=vt<fva), op, by))
