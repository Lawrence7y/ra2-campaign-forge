import json,csv,os
from collections import defaultdict
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_INS_MOV,X86_INS_LEA,X86_INS_CALL,X86_OP_REG,X86_OP_IMM,X86_OP_MEM,X86_REG_ECX
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
def nv(x): return format(x&0xffffffff,'08X')
scan=json.load(open(os.path.join(EV,'s20_scan.json'),encoding='utf-8'))
s20={e for e,r in scan['rows'].items() if r['grade']=='[静态推断]'}
vtmap=defaultdict(set)
with open(os.path.join(EV,'vtable_rtti.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): vtmap[(r['vt'],int(r['slot']))].add(r['entry'])
s20vt={vt for vt,slot in vtmap}

writes=defaultdict(set)
with open(os.path.join(EV,'raw_c7_s20vt.tsv'),encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'):
        if r['addr_mode']=='ABS': writes[(r['global_or_disp'],0)].add(r['vt'])
gct=os.path.join(EV,'global_ctor_vptr_writes.tsv')
if os.path.exists(gct):
    with open(gct,encoding='utf-8') as f:
        for r in csv.DictReader(f,delimiter='\t'): writes[(r['global'],int(r['off']))].add(r['vt'])

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
MAXD=64
exact=[]; write_sites=[]
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
        def get(r):
            s=st.get(r)
            return s if s and idx-s['idx']<=MAXD else None
        def put(r,s): st[r]={**s,'idx':idx}
        def drop(r): st.pop(r,None)
        if ins.id in (X86_INS_MOV,X86_INS_LEA) and len(ops)==2:
            d,s=ops[0],ops[1]
            if d.type==X86_OP_REG:
                r=d.reg
                if s.type==X86_OP_IMM:
                    if nv(s.imm) in s20vt:
                        put(r,{'kind':'constvt','g':nv(s.imm),'off':0,'vt':nv(s.imm)})
                    else:
                        put(r,{'kind':'addr','g':nv(s.imm),'off':0})
                elif s.type==X86_OP_REG:
                    q=get(s.reg)
                    if q: put(r,q)
                    else: drop(r)
                elif s.type==X86_OP_MEM and s.mem.index==0:
                    if s.mem.base==0 and s.mem.disp:
                        put(r,{'kind':'obj','g':nv(s.mem.disp),'off':0})
                    elif s.mem.base is not None:
                        q=get(s.mem.base)
                        if q and q['kind'] in ('addr','obj','vt'):
                            put(r,{'kind':'vt','g':q['g'],'off':q['off']+s.mem.disp})
                        else: drop(r)
                    else: drop(r)
                else: drop(r)
            elif d.type==X86_OP_MEM and d.mem.index==0 and s.type==X86_OP_REG:
                q=get(d.mem.base) if d.mem.base is not None else None
                vq=get(s.reg)
                if q and q['kind'] in ('addr','obj') and vq and vq['kind']=='constvt':
                    writes[(q['g'],q['off']+d.mem.disp)].add(vq['vt'])
                    write_sites.append((site,q['g'],q['off']+d.mem.disp,vq['vt'],entry,f'{ins.mnemonic} {ins.op_str}'))
            elif d.type==X86_OP_MEM and d.mem.index==0 and s.type==X86_OP_IMM:
                q=get(d.mem.base) if d.mem.base is not None else None
                if q and q['kind'] in ('addr','obj'):
                    writes[(q['g'],q['off']+d.mem.disp)].add(nv(s.imm))
                    write_sites.append((site,q['g'],q['off']+d.mem.disp,nv(s.imm),entry,f'{ins.mnemonic} {ins.op_str}'))
        if ins.id==X86_INS_CALL and ops and ops[0].type==X86_OP_MEM:
            m=ops[0].mem
            if m.index==0 and m.base is not None and m.disp>=0:
                q=get(m.base); ecx=get(X86_REG_ECX)
                if q and q['kind'] in ('addr','obj','vt') and ecx and ecx['g']==q['g'] and q['off']>=ecx['off']:
                    exact.append({'site':site,'caller':entry,'g':q['g'],'off':q['off'],'slot':m.disp//4,
                                  'insn':f'{ins.mnemonic} {ins.op_str}','ecx_kind':ecx['kind']})
resolved=defaultdict(list)
for s in exact:
    for vt in sorted(writes.get((s['g'],s['off']),[])):
        for e in sorted(vtmap.get((vt,s['slot']),[])):
            if e in s20: resolved[e].append({**s,'vt':vt})
with open(os.path.join(EV,'exact_v3_write_sites.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('site\tglobal\toff\tvt\tcaller\tinsn\n')
    for r in write_sites: f.write('\t'.join(map(str,r))+'\n')
with open(os.path.join(EV,'exact_v3_sites.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('site\tcaller\tglobal\toff\tslot\tinsn\tecx_kind\n')
    for s in exact: f.write('\t'.join(str(s[k]) for k in ['site','caller','g','off','slot','insn','ecx_kind'])+'\n')
with open(os.path.join(EV,'exact_v3_resolved.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('entry\tsite\tcaller\tglobal\toff\tslot\tvt\tinsn\n')
    for e in sorted(resolved):
        for s in resolved[e]: f.write('\t'.join([e,s['site'],s['caller'],s['g'],str(s['off']),str(s['slot']),s['vt'],s['insn']])+'\n')
print('EXACT_V3_SITES',len(exact),'WRITE_KEYS',len(writes),'RESOLVED_ENTRIES',len(resolved),'RESOLVED_SITES',sum(len(v) for v in resolved.values()))
for e in sorted(resolved): print(e,scan['rows'][e]['name'],len(resolved[e]))
