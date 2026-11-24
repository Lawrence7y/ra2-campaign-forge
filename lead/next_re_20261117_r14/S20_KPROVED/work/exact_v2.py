import json,csv,os,struct
from collections import defaultdict
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_INS_MOV,X86_INS_LEA,X86_INS_CALL,X86_OP_REG,X86_OP_IMM,X86_OP_MEM,X86_REG_ECX
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
def nv(x): return format(x&0xffffffff,'08X')
s20=set()
with open(os.path.join(EV,'s20_scan.json'),encoding='utf-8') as f: scan=json.load(f)
for e,r in scan['rows'].items():
    if r['grade']=='[静态推断]': s20.add(e)
vtmap=defaultdict(set)
with open(os.path.join(EV,'vtable_rtti.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): vtmap[(r['vt'],int(r['slot']))].add(r['entry'])
# absolute C7 writes from raw scan
writes=defaultdict(set)
with open(os.path.join(EV,'raw_c7_s20vt.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['addr_mode']=='ABS': writes[r['global_or_disp']].add(r['vt'])
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
MAXD=14
exact_sites=[]; reg_writes=defaultdict(set)
atlas=[]
with open(ATLAS,encoding='utf-8') as f:
    next(f)
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)>=2: atlas.append((c[0].upper(),int(c[1])))
for entry,size in atlas:
    try: off=pe.get_offset_from_rva(int(entry,16)-base); code=raw[off:off+size]
    except Exception: continue
    if len(code)!=size: continue
    st={}; idx=0
    for ins in md.disasm(code,int(entry,16)):
        if ins.id==0: continue
        idx+=1; site=nv(ins.address); ops=ins.operands
        def setreg(r,s): st[r]=s
        def getreg(r):
            s=st.get(r)
            if s and idx-s['idx']<=MAXD: return s
            return None
        def clearreg(r): st.pop(r,None)
        if ins.id in (X86_INS_MOV,X86_INS_LEA) and len(ops)==2:
            d,s=ops[0],ops[1]
            if d.type==X86_OP_REG:
                r=d.reg
                if s.type==X86_OP_IMM:
                    setreg(r,{'kind':'addr','g':nv(s.imm),'idx':idx})
                elif s.type==X86_OP_REG:
                    q=getreg(s.reg)
                    if q: setreg(r,{**q,'idx':idx})
                    else: clearreg(r)
                elif s.type==X86_OP_MEM and s.mem.index==0:
                    if s.mem.base==0 and s.mem.disp:
                        setreg(r,{'kind':'obj','g':nv(s.mem.disp),'idx':idx})
                    elif s.mem.base is not None:
                        q=getreg(s.mem.base)
                        if q and q['kind'] in ('obj','addr'):
                            setreg(r,{'kind':'vt','g':q['g'],'idx':idx})
                        else: clearreg(r)
                    else: clearreg(r)
                else: clearreg(r)
            elif d.type==X86_OP_MEM and d.mem.index==0 and s.type==X86_OP_IMM:
                q=getreg(d.mem.base) if d.mem.base is not None else None
                if q and q['kind'] in ('obj','addr') and d.mem.disp==0:
                    writes[q['g']].add(nv(s.imm)); reg_writes[site].add((q['g'],nv(s.imm)))
        if ins.id==X86_INS_CALL and ops and ops[0].type==X86_OP_MEM:
            m=ops[0].mem
            if m.index==0 and m.base is not None and m.disp>=0:
                q=getreg(m.base)
                ecx=getreg(X86_REG_ECX)
                if q and q['kind'] in ('obj','addr','vt') and ecx and ecx['kind'] in ('obj','addr','vt') and ecx['g']==q['g']:
                    exact_sites.append({'site':site,'caller':entry,'global':q['g'],'slot':m.disp//4,
                                        'insn':f'{ins.mnemonic} {ins.op_str}','ecx_state':ecx['kind']})
# Resolve
resolved=defaultdict(list)
for s in exact_sites:
    for vt in sorted(writes.get(s['global'],[])):
        for e in sorted(vtmap.get((vt,s['slot']),[])):
            if e in s20:
                resolved[e].append({**s,'vt':vt})
with open(os.path.join(EV,'exact_v2_sites.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('site\tcaller\tglobal\tslot\tinsn\tecx_state\n')
    for s in exact_sites: f.write('\t'.join(str(s[k]) for k in ['site','caller','global','slot','insn','ecx_state'])+'\n')
with open(os.path.join(EV,'exact_v2_resolved.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('entry\tsite\tcaller\tglobal\tslot\tvt\tinsn\n')
    for e in sorted(resolved):
        for s in resolved[e]: f.write('\t'.join([e,s['site'],s['caller'],s['global'],str(s['slot']),s['vt'],s['insn']])+'\n')
print('EXACT_V2_SITES',len(exact_sites),'GLOBALS_WITH_WRITE',len(writes))
print('RESOLVED_ENTRIES',len(resolved),'SITES',sum(len(v) for v in resolved.values()))
for e in sorted(resolved): print(e,scan['rows'][e]['name'],len(resolved[e]))
