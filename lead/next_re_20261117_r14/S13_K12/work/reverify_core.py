#!/usr/bin/env python3
# S13-K12 independent four-ring re-verification. READ-ONLY on gamemd.exe.
# Writes ONLY under lead/next_re_20261117_r14/S13_K12/. No venv, no pip.
import sys, csv, json, hashlib, random
from collections import defaultdict
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
import capstone.x86_const as XC

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE  = ROOT / 'ra2youli' / 'gamemd.exe'
COV  = ROOT / 'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL  = ROOT / 'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
CLS  = ROOT / 'lead/next_re_20261117_r14/SURVEY_D39/EVIDENCE/classification.tsv'
OUT  = ROOT / 'lead/next_re_20261117_r14/S13_K12'
(OUT/'work').mkdir(parents=True, exist_ok=True)
(OUT/'EVIDENCE').mkdir(parents=True, exist_ok=True)

def A(s):
    sys.stdout.write(str(s).encode('ascii','backslashreplace').decode()+"\n")

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest().upper()

raw=EXE.read_bytes(); exe_sha=sha256(EXE)
EXPECT='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
if exe_sha!=EXPECT: raise SystemExit('EXE SHA MISMATCH '+exe_sha)
pe=pefile.PE(data=raw,fast_load=True)
ib=int(pe.OPTIONAL_HEADER.ImageBase)
sections=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode('latin1')
    va=ib+int(s.VirtualAddress); vs=int(s.Misc_VirtualSize); rs=int(s.SizeOfRawData); ptr=int(s.PointerToRawData)
    sections.append({'name':nm,'va':va,'vs':vs,'rs':rs,'ptr':ptr,'end':va+max(vs,rs)})
byname={s['name']:s for s in sections}
tx=byname['.text']; text_va=tx['va']; text=raw[tx['ptr']:tx['ptr']+tx['rs']]

def va2off(va):
    va=int(va)&0xffffffff
    for s in sections:
        if s['va']<=va<s['end']:
            o=s['ptr']+va-s['va']
            if 0<=o<s['ptr']+s['rs'] and o<len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    if o is None or o+4>len(raw): return None
    return int.from_bytes(raw[o:o+4],'little')
def cstr(va,limit=160):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+limit]; z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except: return ''

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(text,text_va))
by_addr={i.address:(n,i) for n,i in enumerate(insns)}

sc=by_addr.get(0x4386AB,(None,None))[1]
sc_op=sc.operands[0] if sc and sc.operands else None
selfcheck019={
  'site':'0x4386AB','disasm':(sc.mnemonic+' '+sc.op_str) if sc else 'MISSING',
  'capstone':__import__('capstone').__version__,
  'op_type_MEM':bool(sc_op and sc_op.type==X86_OP_MEM),
  'mem_index':sc_op.mem.index if sc_op and sc_op.type==X86_OP_MEM else None,
  'mem_base':sc_op.mem.base if sc_op and sc_op.type==X86_OP_MEM else None,
  'mem_disp':hex(sc_op.mem.disp) if sc_op and sc_op.type==X86_OP_MEM else None,
  'never_tests_op_index_is_None':True,
}
if not(sc and sc.mnemonic=='call' and sc_op and sc_op.type==X86_OP_MEM and sc_op.mem.index==0 and sc_op.mem.disp==0x10):
    raise SystemExit('019 SELFCHECK FAILED '+json.dumps(selfcheck019))

cov_fields=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
cov=[]
for line in COV.read_text(encoding='utf-8-sig').splitlines()[1:]:
    if not line.strip(): continue
    q=line.split('\t'); q+=['']*(len(cov_fields)-len(q)); cov.append(dict(zip(cov_fields,q[:len(cov_fields)])))
atlas={}
for line in ATL.read_text(encoding='utf-8-sig').splitlines()[1:]:
    if not line.strip(): continue
    q=line.split('\t')
    atlas[q[0].strip().upper()]={'size':q[1] if len(q)>1 else '0','n_instr':q[2] if len(q)>2 else ''}
s13=[r for r in cov if r['subsystem'].strip().upper()=='S13' and r['entry'].strip().upper() in atlas]
n9={'n':len(s13),
    'named_L':sum(1 for r in s13 if r['name'].strip() and not r['name'].strip().upper().startswith('SUB_')),
    'proved':sum(1 for r in s13 if r['grade'].strip()=='[已证]')}
if (n9['n'],n9['named_L'],n9['proved'])!=(240,216,86):
    raise SystemExit('009 STOP '+json.dumps(n9))

tgt=[]
for line in CLS.read_text(encoding='utf-8-sig').splitlines()[1:]:
    q=line.split('\t')
    if len(q)>=3 and q[1].strip().upper()=='S13' and q[2].strip().upper()=='C1':
        tgt.append(q[0].strip().upper())
tgt=sorted(set(tgt))
if len(tgt)!=17: raise SystemExit('TARGET COUNT '+str(len(tgt))+' != 17')
if '00773030' in tgt: raise SystemExit('FORBIDDEN ENTRY 00773030 IN TARGETS')
tgt_int={int(e,16) for e in tgt}
cov_by={r['entry'].strip().upper():r for r in cov}

direct=defaultdict(list)
for i in insns:
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM:
        direct[int(i.operands[0].imm)&0xffffffff].append(i.address)

installs=defaultdict(list)
imm_refs=defaultdict(list)
for i in insns:
    if i.mnemonic in ('.byte','db',''): continue
    if i.mnemonic=='mov' and len(i.operands)>=2:
        d,s=i.operands
        if d.type==X86_OP_MEM and s.type==X86_OP_IMM and d.size==4:
            m=d.mem
            if m.base==0 and m.index==0 and m.disp:
                installs[int(m.disp)&0xffffffff].append((int(s.imm)&0xffffffff,i.address))
    for op in i.operands:
        if op.type==X86_OP_IMM:
            v=int(op.imm)&0xffffffff
            if ib<=v<ib+0x600000 and v%4==0: imm_refs[v].append(i.address)

def rtti_of_vt(vt):
    col=u32(vt-4)
    if col is None or col%4: return None
    td=u32(col+0xC)
    if td is None: return None
    nm=cstr(td+8)
    if not nm.startswith('.?A'): return None
    return {'col':col,'td':td,'name':nm}
def table_info(hit):
    for off in range(0,257):
        base=hit-4*off
        rr=rtti_of_vt(base)
        if rr: return {'base':base,'slot':off,'rtti':rr}
    return None
def install_witness(base):
    out=[]
    for g,lst in installs.items():
        for v,site in lst:
            if v==base: out.append({'kind':'install','site':site,'global':g})
    for site in imm_refs.get(base,[]): out.append({'kind':'imm','site':site,'global':0})
    return sorted(out,key=lambda x:x['site'])

ECX=XC.X86_REG_ECX
exact=defaultdict(list)
all_exact_hits=set()
for idx,i in enumerate(insns):
    if i.mnemonic!='call' or not i.operands or i.operands[0].type!=X86_OP_MEM: continue
    m=i.operands[0].mem
    if m.base==0 or m.index!=0 or m.disp<0 or (m.disp%4): continue
    basereg=m.base; g_mov=None; ecx_mov=None
    for j in range(idx-1,max(-1,idx-13),-1):
        p2=insns[j]
        if p2.mnemonic=='mov' and len(p2.operands)>=2:
            d,s=p2.operands
            if d.type==X86_OP_REG and d.reg==basereg and s.type==X86_OP_MEM and s.mem.base==0 and s.mem.index==0 and s.mem.disp and g_mov is None:
                g_mov=int(s.mem.disp)&0xffffffff
            if d.type==X86_OP_REG and d.reg==ECX and s.type==X86_OP_IMM and ecx_mov is None:
                ecx_mov=int(s.imm)&0xffffffff
        if g_mov is not None and ecx_mov is not None: break
    if g_mov is None or ecx_mov is None or g_mov!=ecx_mov: continue
    g=g_mov; slot=m.disp//4
    for vt,site in installs.get(g,[]):
        tv=u32(vt+m.disp)
        if tv is None: continue
        all_exact_hits.add(tv)
        if tv in tgt_int:
            exact[tv].append({'site':i.address,'global':g,'slot':slot,'vt':vt,
                              'install_site':site,'call':i.mnemonic+' '+i.op_str})

raw_hits=defaultdict(list)
for s in sections:
    if s['name']=='.text': continue
    start=(s['va']+3)//4*4; end=s['va']+s['rs']
    for va in range(start,end-3,4):
        v=u32(va)
        if v in tgt_int: raw_hits[v].append((va,s['name']))
vt_tables=defaultdict(list)
for e,hits in raw_hits.items():
    for hit,sec in hits:
        ti=table_info(hit)
        if ti: vt_tables[e].append({'base':ti['base'],'slot':ti['slot'],'rtti':ti['rtti'],'section':sec,'hit':hit})

def ring1(entry):
    va=int(entry,16); off=va2off(va)
    b=raw[off:off+16]
    aligned=(va%16==0)
    first=b[0]
    no_e8e9eb=first not in (0xE8,0xE9,0xEB)
    pre=raw[max(0,off-16):off]
    q=len(pre)
    while q>0 and pre[q-1] in (0x90,0xCC): q-=1
    term_ok=False; term_desc=''
    if q>=1 and pre[q-1]==0xC3: term_ok=True; term_desc='ret (C3)'
    elif q>=3 and pre[q-3]==0xC2: term_ok=True; term_desc='ret imm16 (C2 '+pre[q-2:q].hex()+')'
    elif q>=1 and pre[q-1] in (0xEB,0xE9): term_ok=True; term_desc='jmp rel'
    pred=term_desc; falls=not term_ok
    nop_pad=len(pre)-q
    dis=list(md.disasm(raw[off:off+min(48,len(raw)-off)],va))
    pro=' | '.join(x.mnemonic+' '+x.op_str for x in dis[:6])
    return {'aligned16':aligned,'first_byte':hex(first),'not_E8_E9_EB':no_e8e9eb,
            'pred_insn':pred,'pred_fallthrough':falls,'nop_pad':nop_pad,'prologue':pro,'bytes16':b.hex(),
            'atlas_size':atlas.get(entry,{}).get('size','0')}

FREE=0x7C8B3D
def body_dis(entry,limit=0x400):
    va=int(entry,16); off=va2off(va)
    if off is None: return []
    return list(md.disasm(raw[off:off+min(limit,len(raw)-off)],va))
def ring3(entry,vts):
    dis=body_dis(entry)
    names=[v['rtti']['name'] for v in vts]
    fam='DynamicVectorClass' if any('DynamicVectorClass' in n for n in names) else ('VectorClass' if any('VectorClass' in n for n in names) else '')
    slots={v['slot'] for v in vts}
    key=[]; calls=[]
    for x in dis:
        h=x.bytes.hex(); rel='0x%X'%(x.address-int(entry,16))
        tag=None
        if x.mnemonic=='ret' and x.op_str.strip()=='8': tag='ret8'
        elif x.mnemonic=='ret' and x.op_str.strip()=='4': tag='ret4'
        elif x.mnemonic=='ret' and x.op_str.strip()=='': tag='ret_near'
        elif h.startswith('83c8ff'): tag='or_eax_neg1'
        elif h.startswith('c7410404000000'): tag='mov_dword_[ecx+4]_4'
        elif h.startswith('c7410804000000'): tag='mov_dword_[ecx+8]_4'
        elif h.startswith('8b410c'): tag='mov_eax_[ecx+0xC]'
        elif h.startswith('8b4104'): tag='mov_eax_[ecx+4]'
        elif x.mnemonic=='call' and x.operands and x.operands[0].type==X86_OP_IMM:
            t=int(x.operands[0].imm)&0xffffffff; calls.append(hex(t))
            if t==FREE: tag='call_free_0x7C8B3D'
        if tag: key.append({'off':rel,'insn':x.mnemonic+' '+x.op_str,'bytes':h,'tag':tag})
    contract=''
    if 3 in slots and any(k['tag']=='call_free_0x7C8B3D' for k in key):
        contract='Clear'
    elif 4 in slots and any(k['tag']=='or_eax_neg1' for k in key) and any(k['tag'] in ('ret4','ret_near') for k in key):
        contract='FindItemIndex'
    elif 5 in slots and any(k['tag']=='mov_eax_[ecx+0xC]' for k in key):
        contract='GetItemIndex'
    elif 6 in slots and any(k['tag']=='mov_eax_[ecx+4]' for k in key):
        contract='GetItem'
    elif 1 in slots and any(k['tag'] in ('ret4','ret_near') for k in key):
        contract='operator=='
    elif 2 in slots and any(k['tag']=='ret8' for k in key):
        contract='SetCapacity'
    return {'family':fam,'slots_seen':sorted(slots),'contract':contract,'key_insns':key,
            'direct_calls_in_body':calls,'n_instr':len(dis)}

rows=[]
for e in tgt:
    vts=vt_tables.get(int(e,16),[])
    r2={'vt_tables':[{'vt':hex(v['base']),'slot':v['slot'],'col':hex(v['rtti']['col']),
                      'td':hex(v['rtti']['td']),'name':v['rtti']['name'],'section':v['section'],
                      'hit':hex(v['hit']),'witness':install_witness(v['base'])} for v in vts],
        'classes':sorted({v['rtti']['name'] for v in vts})}
    ex=[s for s in exact.get(int(e,16),[]) if s['site']!=int(e,16)]
    rows.append({'entry':e,'cov_name':cov_by[e]['name'],'cov_sem':cov_by[e]['one_line_semantics'],
                 'old_grade':cov_by[e]['grade'],
                 'ring1':ring1(e),'ring2':r2,'ring3':ring3(e,vts),
                 'ring4':{'kind':'exact','n_sites':len(ex),'sites':ex}})

pool=sorted({r['entry'].strip().upper() for r in s13 if r['grade'].strip()=='[静态推断]'} - set(tgt))
rng=random.Random(20261118)
sample=rng.sample(pool,17)
def pred_exact(entry):
    return bool([s for s in exact.get(int(entry,16),[]) if s['site']!=int(entry,16)])
fp_hits=[e for e in sample if pred_exact(e)]
all_s13_entries=[r['entry'].strip().upper() for r in s13]
hit_all=[e for e in all_s13_entries if pred_exact(e)]
baseline={'seed':20261118,'pool_size':len(pool),'sample_n':17,'sample':sample,
          'false_positive_hits':len(fp_hits),'false_positive_entries':fp_hits,
          'S13_rows_total':len(all_s13_entries),'S13_predicate_hits':len(hit_all),
          'S13_predicate_hit_entries':hit_all,
          'S13_hits_outside_target':sorted(set(hit_all)-set(tgt)),
          'S13_target_missed':sorted(set(tgt)-set(hit_all))}

summary={'exe_sha256':exe_sha,'selfcheck019':selfcheck019,'n9':n9,'target_count':len(tgt),
         'direct_call_sites_total':sum(len(v) for v in direct.values()),
         'install_records':sum(len(v) for v in installs.values()),
         'text_instructions':len(insns),'exact_dispatch_targets_hit':len(exact),
         'baseline':baseline}
(OUT/'work'/'reverify_core.json').write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=2),encoding='utf-8')
A(json.dumps(summary,ensure_ascii=False,indent=2))
A('--- ROWS ---')
for r in rows:
    sites=[(hex(s['site']),hex(s['global']),s['slot'],hex(s['install_site'])) for s in r['ring4']['sites']]
    A('%s R1(align=%s,first=%s,notbranch=%s,pf=%s) R2=%s R3=%s R4n=%d sites=%s'%(
        r['entry'],r['ring1']['aligned16'],r['ring1']['first_byte'],r['ring1']['not_E8_E9_EB'],
        r['ring1']['pred_fallthrough'],r['ring2']['classes'],r['ring3']['contract'],r['ring4']['n_sites'],sites))
