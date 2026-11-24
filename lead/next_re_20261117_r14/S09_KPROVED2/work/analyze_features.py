import re, struct, sys, os
from capstone import *
from capstone.x86 import *

# parse disassembly text files
def analyze(fn):
    lines = open(fn, encoding='utf-8').read().splitlines()
    insns = []
    for ln in lines[1:]:
        m = re.match(r'^([0-9A-F]{8}):\s+([0-9a-f]+)\s+(\S+)\s*(.*)$', ln)
        if m:
            insns.append((int(m.group(1),16), m.group(2), m.group(3), m.group(4).strip()))
    return insns

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True

for fn in sorted(f for f in os.listdir('.') if f.startswith('dis_') and f.endswith('.txt')):
    insns = analyze(fn)
    addrs = [i[0] for i in insns]
    jcc=[]; jmp_ind=[]; jmp_dir=[]; calls_dir=[]; calls_ind=[]; rets=[]
    loops=[]
    for idx,(a,b,mn,op) in enumerate(insns):
        if mn.startswith('j') and mn not in ('jmp',) and not mn.startswith('jecxz'):
            # conditional jump
            tgt=None
            mm=re.match(r'0x([0-9A-Fa-f]+)',op)
            if mm: tgt=int(mm.group(1),16)
            jcc.append((a,mn,op,tgt))
        if mn=='jmp':
            if '[' in op or op.strip() in ('eax','ebx','ecx','edx','esi','edi','ebp','esp'):
                jmp_ind.append((a,mn,op))
            else:
                mm=re.match(r'0x([0-9A-Fa-f]+)',op)
                jmp_dir.append((a,mn,int(mm.group(1),16) if mm else None,op))
        if mn=='call':
            if '[' in op:
                calls_ind.append((a,mn,op))
            else:
                mm=re.match(r'0x([0-9A-Fa-f]+)',op)
                calls_dir.append((a,mn,int(mm.group(1),16) if mm else None,op))
        if mn.startswith('ret'):
            rets.append((a,mn,op))
        # backward jcc/jmp = loop
        mm=re.match(r'0x([0-9A-Fa-f]+)',op)
        if mm and (mn.startswith('j')):
            tgt=int(mm.group(1),16)
            if tgt<=a: loops.append((a,mn,tgt))
    # distinct jcc targets
    distinct_tgts=set(t for _,_,_,t in jcc if t is not None)
    print("=== %s (%d insns) ===" % (fn,len(insns)))
    print(" jcc=%d distinct_jcc_targets=%d jmp_ind=%d jmp_dir=%d call_dir=%d call_ind=%d ret=%d backward=%d" % (
        len(jcc),len(distinct_tgts),len(jmp_ind),len(jmp_dir),len(calls_dir),len(calls_ind),len(rets),len(loops)))
    if jmp_ind:
        print("  IND JMP:", [(hex(a),op) for a,_,op in jmp_ind])
    print("  jcc targets:", [hex(t) for t in sorted(distinct_tgts)][:20])
    print("  call_dir:", [hex(t) for _,_,t,_ in calls_dir if t][:20])
    print()
