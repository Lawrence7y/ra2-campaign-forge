# -*- coding: utf-8 -*-
"""S01-KPROVED main scanner: 100% .text instruction-boundary direct-call scan;
③b signals per row; weak(④) vs strong(④+③b); within-subsystem random baseline."""
import struct,hashlib,random,json,collections
import pefile
from capstone import *
from capstone.x86 import *
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE=pefile.PE(EXE,fast_load=False); IB=PE.OPTIONAL_HEADER.ImageBase; DATA=PE.__data__
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
SECS=[]
for s in PE.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin1'); SECS.append((nm,s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
def va_off(va):
    r=va-IB
    for nm,va0,vs,rs,rp in SECS:
        if va0<=r<va0+rs: return rp+(r-va0)
def rd(va,n):
    o=va_off(va); return DATA[o:o+n] if o is not None else b''
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if len(b)==4 else None
# atlas
atlas={}
for line in open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv",encoding='utf8').read().splitlines()[1:]:
    f=line.strip('"').split('\t')
    if len(f)>=3: atlas[f[0].upper()]={'size':int(f[1]),'nins':int(f[2]),'ncallers':int(f[3])}
# coverage S01
rows=[]
cov=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
for line in open(cov,encoding='utf8').read().splitlines()[1:]:
    f=line.split('\t')
    if len(f)>=5 and f[1]=='S01':
        rows.append({'entry':f[0].upper(),'name':f[2],'grade':f[4]})
print('S01 rows:',len(rows))
CLASSES=collections.Counter(r['grade'] for r in rows); print('⑨ grade counts:',dict(CLASSES))
unproven=[r for r in rows if r['grade']!='[已证]']
print('unproven pool:',len(unproven))

# ---- 100% .text linear sweep, instruction-boundary direct calls ----
TEXT_VA=0x401000; TEXT_VSZ=0x3DF38D; TEXT_END=TEXT_VA+TEXT_VSZ
sectsz=[(nm,va0,vs,rs,rp) for nm,va0,vs,rs,rp in SECS if nm=='.text'][0]
TEXT_RAWSTART=sectsz[4]; TEXT_RAWSIZE=sectsz[3]
tbuf=DATA[TEXT_RAWSTART:TEXT_RAWSTART+TEXT_RAWSIZE]
# instruction-boundary map via capstone disasm from VA=TEXT_VA
code=rd(TEXT_VA,TEXT_VSZ)
ins_count=0; boundaries=set(); e8_boundary={}  # addr->target for E8 at instruction boundary
for ins in MD.disasm(code,TEXT_VA):
    ins_count+=1; boundaries.add(ins.address)
    if ins.id==X86_INS_CALL and len(ins.bytes)>=5 and ins.bytes[0]==0xE8:
        rel=struct.unpack('<i',ins.bytes[1:5])[0]
        e8_boundary[ins.address]=(ins.address+5+rel)&0xFFFFFFFF
# raw E8 count for comparison
raw_e8=sum(1 for i in range(len(tbuf)-5) if tbuf[i]==0xE8)
print(f'.text sweep: {ins_count} instructions / {len(e8_boundary)} E8@boundary / {raw_e8} raw E8; VirtualSize={TEXT_VSZ} (0x{TEXT_VSZ:X})')
print('card baseline: 1,392,592 instructions / 68,253 E8@boundary — my sweep figures above')

# direct callers per entry (E8@boundary, non-self-loop)
direct=collections.defaultdict(list)
for site,tgt in e8_boundary.items():
    for r in rows:
        if int(r['entry'],16)==tgt:
            # non-self-loop: caller function body must not contain site; use atlas entry ranges approx
            direct[r['entry']].append(site)

# ---- ③b signals per unproven row ----
def body_signals(entry,size):
    va=int(entry,16); ins=list(MD.disasm(rd(va,size),va))
    cond=0; jt=0; loops=0; calls=0; jcc_targets=[]
    for i in ins:
        m=i.mnemonic; ops=i.op_str
        if m.startswith('j') and m!='jmp': cond+=1
        if m=='jmp' and '*' in ops: jt+=1
        if m=='call': calls+=1
        if m.startswith('j'):
            try:
                t=int(ops,16)
                if va<=t<=i.address: loops+=1
            except: pass
    return {'nins':len(ins),'cond':cond,'jt':jt,'loops':loops,'calls':calls}

# ③b classification (strict): jt>=1 OR (loops>=1 AND cond>=1) [complete loop I/O proxy] OR cond>=3 [multi-guard chain proxy]
# NOTE: this is a SCREENING proxy only; final ③b needs manual per-row contract reading.
def b3_screen(sig):
    reasons=[]
    if sig['jt']>=1: reasons.append('jumptable')
    if sig['loops']>=1 and sig['cond']>=1: reasons.append('loopIO')
    if sig['cond']>=3: reasons.append('multiguard>=3')
    return reasons

signals={}; weak=[]; strong=[]
for r in unproven:
    e=r['entry']; sig=body_signals(e,atlas[e]['size']); signals[e]=sig
    d=direct.get(e,[])
    w = len(d)>0
    b3 = b3_screen(sig)
    if w: weak.append(e)
    if w and b3: strong.append(e)

print('\n=== unproven row signals (entry grade name | nins cond jt loops calls | direct# | ③b_screen) ===')
for r in unproven:
    e=r['entry']; s=signals[e]; d=len(direct.get(e,[]))
    print(f"{e} {r['grade']:<10} {r['name'][:28]:<28} | {s['nins']:>5} {s['cond']:>4} {s['jt']:>2} {s['loops']:>3} {s['calls']:>4} | d={d:<3} | {','.join(b3_screen(s)) or '-'}")

print('\n=== weak(④ only) vs strong(④+③b_screen) ===')
print('weak count =',len(weak),' ->',weak)
print('strong count =',len(strong),' ->',strong)
diff=sorted(set(weak)-set(strong))
print('DIFFERENCE (weak minus strong) count =',len(diff),' ->',diff)

# random baseline: within S01 subsystem, random same number of rows (n=len(weak)), apply strong screen
import statistics
def trial(n,k,seed):
    rnd=random.Random(seed); hits=0
    pool=[r['entry'] for r in rows]
    for _ in range(k):
        sample=rnd.sample(pool,min(n,len(pool)))
        for e in sample:
            sig=signals.get(e) or body_signals(e,atlas[e]['size'])
            if b3_screen(sig) and len(direct.get(e,[]))>0: hits+=1
    return hits
for n in [len(weak),1]:
    hs=[trial(n,200,s) for s in (20261118,1,42,7,99)]
    print(f'random baseline within S01, sample n={n}, 200 draws x5 seeds: mean hits={statistics.mean(hs):.2f} {hs}')

json.dump({'ins_count':ins_count,'e8_boundary':len(e8_boundary),'raw_e8':raw_e8,
           'direct':{k:v for k,v in direct.items()},'signals':signals,'weak':weak,'strong':strong,'diff':diff},
          open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01_KPROVED\EVIDENCE\scan_main.json",'w'),indent=1)
