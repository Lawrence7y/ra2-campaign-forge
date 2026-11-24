"""Operationalize M7: for each backedge, extract loop body [target, source] and
report explicit writes (non-esp destination), pointer advance, boundary cmp,
and calls. Card S05-KPROVED3."""
import json
CFG=json.load(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S05_KPROVED3\work\cfg_features.json"))

def is_write(m,op):
    # destination is memory at start of op_str
    dst=op.split(',')[0].strip()
    if not dst.lower().startswith(('dword ptr','byte ptr','word ptr','qword ptr')): return False
    if m not in ('mov','or','and','add','sub','xor','inc','dec','adc','sbb'): return False
    return True
def is_stack(dst): return 'esp' in dst or 'ebp' in dst

CAND=['006F3330','006F8DF0','006FFEC0','00704350','0070BF50','00712170','00716150','005F9720']
for k in CAND:
    x=CFG[k]; body=x['body']; idx={int(o.replace('+0x',''),16):i for i,(o,m,op,hx) in enumerate(body)}
    offs=sorted(idx)
    print("="*95); print(f"{k} {x['name']}")
    for (bo,m,bt) in x['features']['backedges'][:12]:
        # bo/source is 'at' offset; bt is target offset
        si=idx.get(bo); ti=idx.get(bt)
        if si is None or ti is None:
            print(f"  backedge +0x{bo:04X} {m} -> +0x{bt:04X} (idx miss)"); continue
        loop=body[ti:si+1]
        writes=[(o,op) for o,mm,op,hx in loop if is_write(mm,op)]
        objw=[(o,op) for o,op in writes if not is_stack(op.split(',')[0].strip())]
        stw=[(o,op) for o,op in writes if is_stack(op.split(',')[0].strip())]
        cmps=[(o,op) for o,mm,op,hx in loop if mm=='cmp']
        adv=[(o,mm,op) for o,mm,op,hx in loop if mm in ('inc','add','sub') and any(r in op for r in ('esi','edi','ebx','eax','ecx','edx','ebp'))]
        calls=[(o,op) for o,mm,op,hx in loop if mm.startswith('call')]
        print(f"  backedge +0x{bo:04X} {m} -> +0x{bt:04X} | len={len(loop)} objW={len(objw)} stackW={len(stw)} cmp={len(cmps)} calls={len(calls)}")
        if objw: print(f"     objW: {objw[:5]}")
        if stw:  print(f"     stkW: {stw[:4]}")
        if cmps: print(f"     cmp : {cmps[:6]}")
        if adv:  print(f"     adv : {adv[:6]}")
    print()
