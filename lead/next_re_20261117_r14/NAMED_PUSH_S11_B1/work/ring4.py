import os,sys,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from core import *
rows=json.load(open('b1_rows.json',encoding='utf-8'))
print('entry     vtable      install   func      call55A6C0 call55A6F0 free  kind')
for r in rows:
    ea=int(r['entry'],16)
    refs=[x for x in dword_refs(ea) if not in_text(x)]
    vt=resolve_slot(refs[0])['vtable'] if refs else None
    if not vt: continue
    insts=[i for i in install_sites(vt) if is_vptr_store(i,vt)]
    best=None
    for ins in insts:
        at=atlas_func_of(ins.address)
        fs=at[0] if at else None
        if not fs: continue
        body=[i for i in dis(fs, read_va(fs, at[1])) if i.id!=0]
        c=[i.operands[0].imm & 0xFFFFFFFF for i in body if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM]
        kind = 'CTOR' if 0x55A6C0 in c else ('DTOR' if 0x55A6F0 in c else '?')
        free = 0x7C8B3D in c
        if kind=='CTOR' and not free:
            best=(ins,fs,kind,free); break
        if best is None: best=(ins,fs,kind,free)
    ins,fs,kind,free=best
    print('%s  %s  %s  %s  %-9s %-9s %-5s %s' % (r['entry'], hx(vt), hx(ins.address), hx(fs), kind, '', free, ins.op_str))
