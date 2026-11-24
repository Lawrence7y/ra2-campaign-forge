#!/usr/bin/env python3
"""S15-K4: static multi-channel evidence collector for the 21 currently unnamed S15 entries.
All capstone runs use skipdata=True. Outputs are deliberately untruncated."""
from __future__ import annotations
import csv, pathlib, struct, bisect, re, collections, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM, x86_const

ROOT = pathlib.Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT / 'ra2youli/gamemd.exe'
ATLAS = ROOT / 'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
COV = ROOT / 'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
OUT = pathlib.Path(__file__).resolve().parents[1] / 'EVIDENCE'
OUT.mkdir(exist_ok=True)
TARGETS = [
 '006D0F00','006D6070','006E1830','006E2A10','006E2AA0','006E4790','006E47C0','006E6310',
 '006EA3E0','006F1920','0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0',
 '0072DEF0','00751590','00752460','00763610','00763690'
]

def tsv(p):
    with p.open('r', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

pe = pefile.PE(str(EXE), fast_load=False)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b'\0').decode('latin1', 'replace')
    secs.append((name, IB+s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))

def va_rva(va): return va-IB
def sec_of(va):
    for n,a,vs,rs,pr in secs:
        if a <= va < a+max(vs,rs): return n
    return '?'
def read_va(va,n):
    try: return pe.get_data(va_rva(va), n)
    except Exception: return b''
def u32(va):
    b=read_va(va,4)
    return struct.unpack('<I',b)[0] if len(b)==4 else None

# imports: VA of IAT slot -> module!api
imports={}
for entry in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]):
    mod=entry.dll.decode('latin1','replace') if isinstance(entry.dll,bytes) else str(entry.dll)
    for imp in entry.imports:
        nm=imp.name.decode('latin1','replace') if imp.name else ('ordinal#%s'%imp.ordinal)
        if imp.address:
            imports[imp.address] = mod+'!'+nm

atlas=tsv(ATLAS)
atlas_by={r['entry'].lower():r for r in atlas}
atlas_sorted=sorted(((int(r['entry'],16), int(r['size'],0) if r['size'] else 0, r) for r in atlas), key=lambda x:x[0])
starts=[x[0] for x in atlas_sorted]
def owner(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and va < atlas_sorted[i][0]+atlas_sorted[i][1]: return atlas_sorted[i]
    return None

cov=tsv(COV)
cov_by={r['entry'].upper():r for r in cov}
def fname(va):
    r=cov_by.get('%08X'%(va & 0xffffffff))
    return (r['subsystem']+'|'+r['name']+'|'+r['grade']) if r else ''

md=Cs(CS_ARCH_X86, CS_MODE_32); md.detail=True; md.skipdata=True
# full .text linear sweep with skipdata; independent of atlas boundaries
text=[s for s in secs if s[0]=='.text'][0]
tname,tbase,tvs,trs,tpr=text
tbytes=pe.get_data(tbase-IB, max(tvs,trs))
insns=list(md.disasm(tbytes,tbase))
inset={i.address for i in insns}
by_addr={i.address:i for i in insns}
callx=collections.defaultdict(list)
for i in insns:
    if i.mnemonic in ('call','jmp') and len(i.operands)==1 and i.operands[0].type==CS_OP_IMM:
        callx[i.operands[0].imm & 0xffffffff].append((i.address,i.mnemonic,i.size))

# helper: printable string at VA
def cstr(va,maxn=180):
    b=read_va(va,maxn)
    out=bytearray()
    for c in b:
        if c==0: break
        if 32 <= c < 127: out.append(c)
        else: break
        if len(out)>=maxn: break
    return out.decode('ascii','replace') if len(out)>=3 else ''

def fmt_ins(i,mark_addrs=()):
    op=i.op_str
    # annotate direct call/jmp targets
    ann=[]
    if len(i.operands) and i.operands[0].type==CS_OP_IMM:
        t=i.operands[0].imm & 0xffffffff
        lab=fname(t) or imports.get(t,'')
        if lab: ann.append(' ; '+lab)
    return '%08X  %-20s %-8s %s%s' % (i.address, i.bytes.hex(), i.mnemonic, op, ''.join(ann))

def disasm_range(va,size):
    b=read_va(va,size)
    return list(md.disasm(b,va))

# VTABLE scan: exact dword slot values; parse vtable[-1] -> COL -> TD via COL+0xC -> TD+8 per R14_COMMON §8.1 ⑧
vlines=['S15-K4 channel 1: vtable slot scan + RTTI chain (COL+0xC -> TD+8; fail-closed)']
vhits=collections.defaultdict(list)
for sname,sa,svs,srs,spr in secs:
    if not sname.startswith('.rdata'): continue
    data=pe.get_data(sa-IB, max(svs,srs))
    for off in range(0,len(data)-3,4):
        val=struct.unpack_from('<I',data,off)[0]
        if val in {int(x,16) for x in TARGETS}:
            vhits[val].append(sa+off)
for t in TARGETS:
    va=int(t,16); hits=vhits.get(va,[])
    vlines.append('%s: vtable-slot dword hits=%d %s' % (t,len(hits),' '.join('%08X'%h for h in hits)))
    for h in hits:
        col=u32(h-4)
        vlines.append('  slot@%08X  vtable[-1]=%08X %s' % (h,col or 0,sec_of(col) if col else '?'))
        if col is None: continue
        td=u32(col+0xC)
        vlines.append('  COL+0xC -> TD=%08X %s' % (td or 0,sec_of(td) if td else '?'))
        if td is None: continue
        nmva=u32(td+8)
        nm=cstr(nmva) if nmva else ''
        vlines.append('  TD+8 -> name@%08X = %s' % (nmva or 0,nm or '<FAIL-CLOSED>'))
(OUT/'vtable_scan_k4.txt').write_text('\n'.join(vlines)+'\n',encoding='utf-8')

# Main dumps
ov=['S15-K4 static collector overview','exe=%s bytes=%d IB=%08X'%(EXE,EXE.stat().st_size,IB)]
ov.append('sections: '+'; '.join('%s[%08X,+%X]'%(n,a,max(vs,rs)) for n,a,vs,rs,pr in secs))
ov.append('.text linear sweep skipdata=True: %d instructions, %d bytes'%(len(insns),len(tbytes)))
ov.append('atlas functions=%d; coverage rows=%d; direct call targets indexed=%d'%(len(atlas),len(cov),len(callx)))
(OUT/'analysis_overview.txt').write_text('\n'.join(ov)+'\n',encoding='utf-8')

all_d=[]; all_x=[]; all_s=[]
for t in TARGETS:
    va=int(t,16); ar=atlas_by.get(t.lower(),{})
    size=int(ar.get('size','0'),0) if ar else 0
    ii=disasm_range(va,size)
    first=by_addr.get(va)
    all_d.append('\n'+'='*90)
    all_d.append('TARGET %s  atlas_size=%d  n_instr=%d  sweep_boundary=%s  prev_bytes=%s'%(
        t,size,len(ii), 'YES' if va in inset else 'NO', tbytes[va-tbase-8:va-tbase].hex() if va-tbase>=8 else '?'))
    all_d.append('atlas row: '+(repr(ar) if ar else '<none>'))
    all_d.append('coverage row: '+(repr(cov_by.get(t)) if cov_by.get(t) else '<none>'))
    for i in ii: all_d.append(fmt_ins(i))
    # resolved calls / imports / strings / globals
    all_s.append('\n'+'='*90+'\nTARGET '+t)
    calls=[]
    for i in ii:
        if i.mnemonic in ('call','jmp') and len(i.operands) and i.operands[0].type==CS_OP_IMM:
            dest=i.operands[0].imm & 0xffffffff
            lab=fname(dest) or imports.get(dest,'')
            calls.append((i.address,i.mnemonic,dest,lab))
        if i.mnemonic=='call' and len(i.operands) and i.operands[0].type==CS_OP_MEM:
            m=i.operands[0].mem
            all_s.append('  indirect@%08X %s %s'%(i.address,i.mnemonic,i.op_str))
    all_s.append('  direct calls/jmps (%d):'%len(calls))
    for a,m,d,l in calls: all_s.append('    %08X %-4s -> %08X %s'%(a,m,d,l))
    strs=[]; globs=[]
    for i in ii:
        for op in i.operands:
            cand=None; kind=''
            if op.type==CS_OP_IMM: cand=op.imm & 0xffffffff; kind='imm'
            elif op.type==CS_OP_MEM and op.mem.base==0 and op.mem.index==0 and op.mem.disp:
                cand=op.mem.disp & 0xffffffff; kind='mem'
            if cand is None or not (IB <= cand < IB+0x800000): continue
            s=cstr(cand)
            if s: strs.append((i.address,kind,cand,s))
            if sec_of(cand) in ('.data','.bss','.idata'): globs.append((i.address,kind,cand,sec_of(cand)))
    all_s.append('  string-like refs (%d):'%len(strs))
    for a,k,c,s in strs: all_s.append('    %08X %-3s %08X %-8s %r'%(a,k,c,sec_of(c),s))
    all_s.append('  data-global refs (%d):'%len(globs))
    seen=set()
    for a,k,c,sec in globs:
        key=(k,c)
        if key in seen: continue
        seen.add(key); all_s.append('    %08X %-3s %08X %s'%(a,k,c,sec))
    # callers from full sweep
    xs=callx.get(va,[])
    all_x.append('\n'+'='*90+'\nTARGET '+t+'  direct call/jmp xrefs=%d'%len(xs))
    for site,m,ln in xs:
        ow=owner(site)
        if ow:
            os_,sz,orow=ow
            olab='%08X(size %d) %s'%(os_,sz,fname(os_))
        else: olab='<atlas hole / no containing interval>'
        all_x.append('  site %08X %-4s len=%d  owner=%s'%(site,m,ln,olab))
        # context: 10 preceding and 6 following instructions from linear sweep
        idx=next((k for k,i2 in enumerate(insns) if i2.address==site),None)
        if idx is not None:
            for i2 in insns[max(0,idx-10):min(len(insns),idx+7)]:
                all_x.append(('    > ' if i2.address==site else '      ')+fmt_ins(i2))
(OUT/'targets_disasm.txt').write_text('\n'.join(all_d)+'\n',encoding='utf-8')
(OUT/'targets_xrefs.txt').write_text('\n'.join(all_x)+'\n',encoding='utf-8')
(OUT/'strings_imports_globals.txt').write_text('\n'.join(all_s)+'\n',encoding='utf-8')
print('WROTE', *(str(OUT/f) for f in ['analysis_overview.txt','targets_disasm.txt','targets_xrefs.txt','strings_imports_globals.txt','vtable_scan_k4.txt']))
print('instructions',len(insns),'vtable hits total',sum(len(v) for v in vhits.values()))
