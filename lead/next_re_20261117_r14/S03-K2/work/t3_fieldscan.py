#!/usr/bin/env python3
"""T3: field writer/reader scan for the 3 new classes. this=ecx at entry, track ecx->esi/edi/ebx."""
import sys, os, struct, csv
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_INS_INVALID
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

def scan_func(fn, thisregs_init={'ecx'}):
    """Return list of (addr, mnem, disp, width, is_write, bytes) for [thisreg+disp] accesses.
    Track this-registers via mov dst,src where src is a thisreg."""
    acc=[]
    regs=set(thisregs_init)
    for ins in dis(fn, 0x600, 400):
        if ins.id==X86_INS_INVALID: continue
        m=ins.mnemonic; ops=ins.operands
        # detect mov reg,reg / lea reg,[thisreg+..] propagation
        if m=='mov' and len(ops)==2 and ops[0].type==X86_OP_REG and ops[1].type==X86_OP_REG:
            d=ins.reg_name(ops[0].reg); s=ins.reg_name(ops[1].reg)
            if s in regs: regs.add(d)
            elif d in regs and d!=s: regs.discard(d)
        # examine memory operands
        for idx,op in enumerate(ops):
            if op.type==X86_OP_MEM and op.mem.base!=0:
                base=ins.reg_name(op.mem.base)
                if base in regs and op.mem.disp not in (0,) :
                    disp=op.mem.disp
                    w=op.size if op.size else 4
                    iswr = (idx==0 and m in ('mov','movzx','movsx','add','sub','or','and','xor','inc','dec','shl','shr','test'))
                    if m in ('cmp','test') : iswr=False
                    acc.append((ins.address,m,disp,w,iswr,ins.bytes.hex()))
        if m=='ret': break
    return acc

classes={
 'CDFileClass':[0x401950,0x401940,0x47AE10,0x47AAB0,0x47AF10,0x431F10,0x431F30,0x431B80],
 'BufferIOFileClass':[0x432610,0x431B20,0x431B80,0x431E80,0x431F70,0x431F50],
 'RawFileClass':[0x65D3A0,0x65CAC0,0x65CBF0,0x65D420,0x65CB50,0x65CB30,0x65CCE0,0x65CF00,0x65D0D0,0x65CDD0,0x65CCA0,0x65CA00],
}
for cls,fns in classes.items():
    p(f"\n########## {cls} ##########")
    allacc=[]
    for fn in fns:
        acc=scan_func(fn)
        allacc+=acc
    # aggregate by disp
    from collections import defaultdict
    byd=defaultdict(lambda:{'w':[],'r':[]})
    for a,m,disp,w,iswr,raw in allacc:
        rec=(a,m,w,raw)
        (byd[disp]['w'] if iswr else byd[disp]['r']).append(rec)
    p(f"  {'off':>5} {'wid':>3} {'#W':>3} {'#R':>3}  writers / readers")
    for disp in sorted(byd):
        v=byd[disp]
        ws=v['w']; rs=v['r']
        widths=set(x[2] for x in ws+rs)
        p(f"  +0x{disp:03X} {max(widths) if widths else 0:>3} {len(ws):>3} {len(rs):>3}  "
          f"W={[hex(x[0]) for x in ws[:6]]} R={[hex(x[0]) for x in rs[:6]]}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T3_fieldscan.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T3_fieldscan.txt]")
