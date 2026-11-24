"""S10-KPROVED2 own toolkit part 3: per-function disassembly + 3b feature extraction.
Uses classification ext_lo/ext_hi (self-written CFG extent from SURVEY) as body range,
but also computes own linear extent. Dumps full instruction listing with entry-relative offsets.
"""
import struct, sys
from capstone import *
from capstone.x86 import *
from re_core import PE
from call_sweep import full_text_sweep

def disasm_range(pe, start, end):
    code = pe.bytesva(start, end-start)
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    out=[]
    for ins in md.disasm(code, start):
        out.append(ins)
    return out

def load_a_rows():
    rows=[]
    with open(r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv', encoding='utf-8') as f:
        hdr=f.readline().rstrip('\n').split('\t'); ii={h:i for i,h in enumerate(hdr)}
        for line in f:
            c=line.rstrip('\n').split('\t')
            if c[ii['subsystem']]=='S10' and c[ii['has4_strict']]=='1' and c[ii['has2_rtti']]=='1':
                rows.append({h:c[ii[h]] for h in hdr})
    return rows

CAND = [0x004D5690,0x004D74E0,0x004D85D0,0x00706640,0x004D7D50,0x00702D40,0x004DBAD0,0x006F3AD0]

def summarize(pe, entry, ext_hi):
    insns = disasm_range(pe, entry, ext_hi)
    n=len(insns)
    jcc=[]; jmp=[]; calls=[]; ret=[]; indir_jmp=[]; indir_call=[]
    cmps=[]; memwrites=[]
    for ins in insns:
        off=ins.address-entry
        m=ins.mnemonic
        if m.startswith('j') and m not in ('jmp',):
            jcc.append((off,m,ins.op_str,ins.address))
        elif m=='jmp':
            jmp.append((off,'jmp',ins.op_str,ins.address))
        elif m=='call':
            calls.append((off,ins.op_str,ins.address))
        elif m.startswith('ret'):
            ret.append((off,m,ins.op_str,ins.address))
        # indirect jumps/calls: operand starts with '[' or is reg
        ops=ins.op_str
        if m=='jmp' and ('[' in ops or ops in ('eax','ebx','ecx','edx','esi','edi','ebp','esp')):
            indir_jmp.append((off,m,ops,ins.address))
        if m=='call' and ('[' in ops or ops in ('eax','ebx','ecx','edx','esi','edi','ebp','esp')):
            indir_call.append((off,m,ops,ins.address))
        if m in ('cmp','test'):
            cmps.append((off,m,ops,ins.address))
    backward=[j for j in jcc+jmp if _is_backward(j,insns,entry)]
    return {'n':n,'insns':insns,'jcc':jcc,'jmp':jmp,'calls':calls,'ret':ret,
            'indir_jmp':indir_jmp,'indir_call':indir_call,'cmps':cmps,'backward':backward}

def _is_backward(j, insns, entry):
    off,m,ops,va=j
    # parse immediate target from op_str like '0x4d5700' or '0x... <...>'
    import re
    mm=re.search(r'0x([0-9a-fA-F]+)',ops)
    if not mm: return False
    tgt=int(mm.group(1),16)
    return tgt<=va

if __name__=='__main__':
    pe=PE()
    rows={int(r['entry'],16):r for r in load_a_rows()}
    for e in CAND:
        r=rows[e]
        ext_hi=int(r['ext_hi'],16)
        s=summarize(pe,e,ext_hi)
        print(f'=== {e:08X} {r["name"]}  body[{e:08X},{ext_hi:08X}) n={s["n"]}')
        print(f'  jcc={len(s["jcc"])} jmp={len(s["jmp"])} calls={len(s["calls"])} ret={len(s["ret"])} indir_jmp={len(s["indir_jmp"])} indir_call={len(s["indir_call"])} backward={len(s["backward"])}')
        print('  indirect jmp:',[(hex(off),m,ops) for off,m,ops,_ in s['indir_jmp'][:20]])
        print('  indirect call:',[(hex(off),m,ops) for off,m,ops,_ in s['indir_call'][:20]])
        print('  ret:',[(hex(off),m,ops) for off,m,ops,_ in s['ret'][:10]])
