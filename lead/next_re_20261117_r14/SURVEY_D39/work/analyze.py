#!/usr/bin/env python3
"""SURVEY-D39 self-contained analyzer. Reads only; writes only SURVEY_D39."""
from __future__ import annotations
import csv, hashlib, json, math, random, re
from collections import Counter, defaultdict
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT / 'ra2youli' / 'gamemd.exe'
COV = ROOT / 'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATLAS = ROOT / 'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
OUT = ROOT / 'lead/next_re_20261117_r14/SURVEY_D39'
(OUT/'work').mkdir(parents=True, exist_ok=True)
(OUT/'EVIDENCE').mkdir(parents=True, exist_ok=True)
SUBS = ['S10','S11','S20','S13']
FIELDS = ['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest().upper()

def read_cov():
    out=[]
    lines=COV.read_text(encoding='utf-8-sig').splitlines()
    for line in lines[1:]:
        if not line.strip(): continue
        q=line.split('\t')
        q += ['']*(len(FIELDS)-len(q))
        out.append(dict(zip(FIELDS,q[:len(FIELDS)])))
    return out

def read_atlas():
    out=[]
    lines=ATLAS.read_text(encoding='utf-8-sig').splitlines()
    hdr=lines[0].split('\t')
    for line in lines[1:]:
        if not line.strip(): continue
        q=line.split('\t'); q += ['']*(len(hdr)-len(q))
        out.append(dict(zip(hdr,q[:len(hdr)])))
    return out

cov=read_cov(); atlas=read_atlas()
atlas_by={r['entry'].strip().upper():r for r in atlas}
atlas_entries=sorted(atlas_by)
# disk recomputation of Lead's gate numbers
pat_sub=re.compile(r'::SUB_[0-9A-F]{8}$', re.I)
pat_slot=re.compile(r'::(?:V?SLOT)[0-9]+$', re.I)
def named_flags(name):
    n=(name or '').strip(); u=n.upper()
    L=bool(n) and not u.startswith('SUB_')
    S=L and not bool(pat_sub.search(u))
    T=S and not bool(pat_slot.search(u))
    return L,S,T
metrics={}
for s in [f'S{i:02d}' for i in range(1,23)]:
    rs=[r for r in cov if r['subsystem'].strip().upper()==s and r['entry'].strip().upper() in atlas_by]
    proved=sum(r['grade'].strip()=='[已证]' for r in rs)
    namedS=sum(named_flags(r['name'])[1] for r in rs)
    thr=math.ceil(len(rs)/2)
    metrics[s]={'n':len(rs),'named_L':sum(named_flags(r['name'])[0] for r in rs),'named_S':namedS,
                'named_strict':sum(named_flags(r['name'])[2] for r in rs),'proved':proved,'threshold':thr,
                'gap':max(0,thr-proved)}
grades=Counter(r['grade'].strip() for r in cov)
static_in_atlas=sum(1 for r in cov if r['grade'].strip()=='[静态推断]' and r['entry'].strip().upper() in atlas_by)
static_in_atlas_nonS22=sum(1 for r in cov if r['grade'].strip()=='[静态推断]' and r['entry'].strip().upper() in atlas_by and r['subsystem'].strip().upper()!='S22')
proved_gap=sum(v['gap'] for v in metrics.values())
proved_gap_nonS22=sum(v['gap'] for k,v in metrics.items() if k!='S22')
if (static_in_atlas_nonS22,proved_gap_nonS22)!=(4416,2736):
    raise SystemExit(f'N9 STOP global mismatch: static={static_in_atlas_nonS22} gap={proved_gap_nonS22}')
lead_gate={s:{'n':metrics[s]['n'],'named':metrics[s]['named_S'],'proved':metrics[s]['proved'],'threshold':metrics[s]['threshold'],'gap':metrics[s]['gap']} for s in SUBS}
# fail closed if disk disagrees with Lead values stated in CARD
expected={'S10':(526,117,263,146),'S11':(368,29,184,155),'S20':(410,40,205,165),'S13':(240,86,120,34)}
mismatch={s:{'got':lead_gate[s],'want':expected[s]} for s in SUBS if (metrics[s]['n'],metrics[s]['proved'],metrics[s]['threshold'],metrics[s]['gap'])!=expected[s]}
if mismatch:
    (OUT/'work'/'STOP_N9.json').write_text(json.dumps(mismatch,ensure_ascii=False,indent=2),encoding='utf-8')
    raise SystemExit('N9 STOP: disk mismatch '+json.dumps(mismatch,ensure_ascii=False))

raw=EXE.read_bytes(); exe_sha=hashlib.sha256(raw).hexdigest().upper()
pe=pefile.PE(data=raw, fast_load=True)
ib=int(pe.OPTIONAL_HEADER.ImageBase)
sections=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode('latin1')
    va=ib+int(s.VirtualAddress); vs=int(s.Misc_VirtualSize); rs=int(s.SizeOfRawData); ptr=int(s.PointerToRawData)
    sections.append({'name':nm,'va':va,'vs':vs,'rs':rs,'ptr':ptr,'end':va+max(vs,rs)})
by_name={s['name']:s for s in sections}
text_sec=by_name['.text']; text_va=text_sec['va']
text=raw[text_sec['ptr']:text_sec['ptr']+text_sec['rs']]
def va2off(va):
    va=int(va)&0xffffffff
    for s in sections:
        if s['va'] <= va < s['end']:
            o=s['ptr']+va-s['va']
            if 0 <= o < s['ptr']+s['rs'] and o < len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    if o is None or o+4>len(raw): return None
    return int.from_bytes(raw[o:o+4],'little')
def cstr(va,limit=128):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+limit]
    z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except UnicodeDecodeError: return ''

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
insns=list(md.disasm(text,text_va))
by_addr={i.address:(n,i) for n,i in enumerate(insns)}
# selfcheck 019: known positive call [edx+0x10]
sc_ins=by_addr.get(0x4386AB,(None,None))[1]
sc_op=sc_ins.operands[0] if sc_ins else None
selfcheck={
 'known_site':'0x4386AB','disasm':(sc_ins.mnemonic+' '+sc_ins.op_str) if sc_ins else 'MISSING',
 'capstone_version':__import__('capstone').__version__,
 'mem_index':sc_op.mem.index if sc_op and sc_op.type==X86_OP_MEM else None,
 'op_index_attr':getattr(sc_op,'index','NO_ATTR') if sc_op else 'NO_OP',
 'note':'call [edx+0x10] is a known positive; mem.index==0 means no SIB index. Script never tests op.index is None.'
}
if not sc_ins or sc_op.type!=X86_OP_MEM or sc_op.mem.index!=0 or sc_op.mem.disp!=0x10:
    raise SystemExit('019 selfcheck failed')

# instruction-boundary direct calls
direct=defaultdict(list)
for i in insns:
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_IMM:
        direct[int(i.operands[0].imm)&0xffffffff].append(i.address)

# absolute vptr installs and imm references at instruction boundaries
installs=defaultdict(list)   # global -> [(vt, site)]
imm_refs=defaultdict(list)   # imm -> [site]
for i in insns:
    if i.mnemonic=='.byte': continue
    if i.mnemonic=='mov' and len(i.operands)>=2 and i.operands[0].type==X86_OP_MEM and i.operands[1].type==X86_OP_IMM:
        m=i.operands[0].mem
        if m.base==0 and m.index==0 and m.disp and i.operands[0].size==4:
            installs[int(m.disp)&0xffffffff].append((int(i.operands[1].imm)&0xffffffff,i.address))
    for op in i.operands:
        if op.type==X86_OP_IMM:
            v=int(op.imm)&0xffffffff
            if ib <= v <= ib+0x500000 and v%4==0:
                imm_refs[v].append(i.address)

# target static rows
target=[]
for r in cov:
    e=r['entry'].strip().upper()
    if r['subsystem'].strip().upper() in SUBS and r['grade'].strip()=='[静态推断]' and e in atlas_by:
        target.append(r)
target_entries={r['entry'].strip().upper() for r in target}
target_entries_int={int(e,16) for e in target_entries}

# baseline sample of 100 atlas entries, one deterministic seed
rng=random.Random(20261118)
baseline_entries=set(rng.sample(atlas_entries,100))

# scan aligned dwords in non-text sections for selected entries
scan_entries_str=target_entries|baseline_entries
scan_entries={int(e,16) for e in scan_entries_str}
raw_hits=defaultdict(list)
for s in sections:
    if s['name']=='.text': continue
    start=(s['va']+3)//4*4
    end=s['va']+s['rs']
    for va in range(start,end-3,4):
        v=u32(va)
        if v in scan_entries: raw_hits[v].append((va,s['name']))

def rtti_of_vt(vt):
    col=u32(vt-4)
    if col is None: return None
    td=u32(col+0xC)
    if td is None: return None
    name=cstr(td+8)
    if not name.startswith('.?A'): return None
    return {'col':col,'td':td,'name':name}

def table_info(hit):
    # a dword hit may be any slot; walk back to the RTTI-tagged table base
    for off in range(0,257):
        base=hit-4*off
        rr=rtti_of_vt(base)
        if rr: return {'base':base,'slot':off,'rtti':rr}
    return None

vt_tables=defaultdict(list)
for e,hits in raw_hits.items():
    for hit,sec in hits:
        ti=table_info(hit)
        if ti: vt_tables[e].append({'base':ti['base'],'slot':ti['slot'],'rtti':ti['rtti'],'section':sec})

def witness_sites(base):
    sites=[]
    for g,lst in installs.items():
        for v,site in lst:
            if v==base: sites.append(('install',site,g))
    for site in imm_refs.get(base,[]): sites.append(('imm',site,0))
    return sorted(sites,key=lambda x:x[1])

# exact virtual dispatch: mov reg,[global] + mov ecx,global + call [reg+slot]
import capstone.x86_const as XC
ECX=XC.X86_REG_ECX
exact=defaultdict(list)
for idx,i in enumerate(insns):
    if i.mnemonic!='call' or not i.operands or i.operands[0].type!=X86_OP_MEM: continue
    m=i.operands[0].mem
    if m.base==0 or m.index!=0 or m.disp<0 or m.disp%4: continue
    base=m.base; g_mov=None; ecx_mov=None
    for j in range(idx-1,max(-1,idx-13),-1):
        p=insns[j]
        if p.mnemonic=='mov' and len(p.operands)>=2:
            d,s=p.operands
            if d.type==1 and d.reg==base and s.type==X86_OP_MEM and s.mem.base==0 and s.mem.index==0 and s.mem.disp and g_mov is None:
                g_mov=int(s.mem.disp)&0xffffffff
            if d.type==1 and d.reg==ECX and s.type==X86_OP_IMM and ecx_mov is None:
                ecx_mov=int(s.imm)&0xffffffff
        if g_mov is not None and ecx_mov is not None: break
    if g_mov is None or ecx_mov is None or g_mov!=ecx_mov: continue
    g=g_mov; slot=m.disp//4
    for vt,site in installs.get(g,[]):
        tv=u32(vt+m.disp)
        if tv in target_entries_int:
            exact[tv].append({'site':i.address,'global':g,'slot':slot,'vt':vt,'install_site':site})

# semantic named flag: placeholders Class::slotN / vslotN / sub_* do not count
pat_bad_sem=re.compile(r'(缺语义|占位|member \(callgraph\)|member \(rtti-vftable\)|slot/vslot/sub)',re.I)
def semantic_named(r):
    n=(r['name'] or '').strip(); sem=(r['one_line_semantics'] or '').strip(); u=n.upper()
    if not n or u.startswith('SUB_'): return False, 'sub_name'
    if re.search(r'::(?:V?SLOT)[0-9]+$',u): return False, 'slot_placeholder'
    if re.search(r'::SUB_[0-9A-F]{8}$',u): return False, 'sub_placeholder'
    if pat_bad_sem.search(sem): return False, 'generic_semantics'
    return True, 'named_contract'

# body contracts strong enough to name a vector-family slot without relying on the placeholder name
def body_bytes(entry,limit=512):
    va=int(entry,16); off=va-text_va
    if off<0 or off>=len(text): return b''
    size=int(str(atlas_by.get(entry,{}).get('size','0')).strip() or 0)
    return text[off:off+min(max(limit,size),512)]

def has_call_to(b,entry,target):
    for k in range(len(b)-4):
        if b[k]==0xE8:
            rel=int.from_bytes(b[k+1:k+5],'little',signed=True)
            if (int(entry,16)+k+5+rel)&0xffffffff == target: return True
    return False

def contract_from_body(entry,vts):
    b=body_bytes(entry)
    if not b: return ''
    names=';'.join(v['rtti']['name'] for v in vts)
    if 'VectorClass' not in names: return ''
    slots={v['slot'] for v in vts}
    ret4=b'\xc2\x04\x00' in b; ret8=b'\xc2\x08\x00' in b
    if 3 in slots and has_call_to(b,entry,0x7C8B3D) and b'\xc7\x41\x04\x04\x00\x00\x00' in b: return 'Clear'
    if 4 in slots and b'\x83\xc8\xff' in b and ret4: return 'FindItemIndex'
    if 5 in slots and b'\x8b\x41\x0c' in b and ret4: return 'GetItemIndex'
    if 6 in slots and b'\x8b\x41\x04\x8b\x4c\x24\x04\x8b\x04\x88\xc2\x04\x00' in b: return 'GetItem'
    if 1 in slots and ret4 and (b'\x39' in b or b'\x8b\x41\x08' in b): return 'operator=='
    if 2 in slots and ret8: return 'SetCapacity'
    return ''

# K8 18 + K10 43 addresses that C2 sample must avoid
K8='0075E510 0065BED0 0040BBC0 0040BC10 0040F8A0 0040F8F0 0040FE70 0040FEC0 0046B8C0 0046B910 0048AFD0 0048B020 0054EB50 0054EBA0 0062B330 0062B380 0065C1B0 0065C200'.split()
K10='0040B640 0040B670 0040B860 0040F610 0040F7A0 0040F870 0040FBB0 0040FBE0 0040FD70 0046B5E0 0046B610 0046B7C0 0054E890 0054E8C0 0054EA50 0054EB20 0062B070 0062B0A0 0062B230 0065BEF0 0065BF20 0065C0B0 0048AD10 0048AD40 0048AE60 0048AED0 0048AFA0 0040B700 0040F640 0040FC10 0046B660 0054E8F0 0062B0D0 0065BF50 0040F630 0040FC00 0040B7F0 0040F730 0040FD00 0046B750 0054E9E0 0062B1C0 0065C040'.split()
avoid=set(K8)|set(K10)

features=[]
for r in target:
    e=r['entry'].strip().upper(); eint=int(e,16)
    vtl=[]
    for t in vt_tables.get(eint,[]):
        vtl.append({'vt':t['base'],'slot':t['slot'],'section':t['section'],'rtti':t['rtti'],'witness':witness_sites(t['base'])})
    rtti=[v for v in vtl if v['rtti']]
    witnesses=[w for v in rtti for w in v['witness']]
    contract=contract_from_body(e,rtti)
    named,why=semantic_named(r)
    if not named and contract:
        named=True; why='body_contract:'+contract
    dcs=direct.get(eint,[]); ex=exact.get(eint,[])
    if dcs or ex:
        cls='C1'; reason='direct_call' if dcs else 'exact_dispatch'
    elif not rtti or not witnesses:
        cls='C3'; reason='rtti_missing_or_no_live_witness'
    elif not named:
        cls='C4'; reason=why
    else:
        cls='C2'; reason='rtti_plus_live_witness_no_ring4'
    features.append({'entry':e,'subsystem':r['subsystem'],'name':r['name'],'semantics':r['one_line_semantics'],
                     'class':cls,'reason':reason,'semantic_named':named,'contract':contract,'direct_calls':dcs,'exact':ex,
                     'vts':vtl,'rtti':rtti,'witnesses':witnesses})

# global baseline: exact predicate from CARD = active vptr install AND direct call count 0
base_hits=[]
for e in baseline_entries:
    eint=int(e,16)
    vtlist=vt_tables.get(eint,[])
    has_install=any(any(w[0]=='install' for w in witness_sites(v['base'])) for v in vtlist)
    if has_install and not direct.get(eint,[]): base_hits.append(e)
baseline={'seed':20261118,'sample_n':100,'hits':len(base_hits),'rate':len(base_hits)/100.0,'hit_entries':sorted(base_hits)}

# outputs
with (OUT/'EVIDENCE'/'classification.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','class','reason','name','semantics','direct_calls','exact_sites','rtti_classes','install_or_imm_sites','body_contract'])
    for x in features:
        classes=';'.join(sorted({v['rtti']['name'] for v in x['rtti']}))
        sites=[]
        for ww in x['witnesses'][:10]: sites.append(f'{ww[0]}@{ww[1]:08X}'+(('/g'+hex(ww[2])) if ww[0]=='install' else ''))
        w.writerow([x['entry'],x['subsystem'],x['class'],x['reason'],x['name'],x['semantics'],
                    len(x['direct_calls']),len(x['exact']),classes,';'.join(sites),x.get('contract','')])
with (OUT/'EVIDENCE'/'ring4_sites.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','kind','site','global','slot','vt','install_site'])
    for x in features:
        for s in x['direct_calls']: w.writerow([x['entry'],'direct',f'{s:08X}','','','',''])
        for q in x['exact']: w.writerow([x['entry'],'exact',f"{q['site']:08X}",f"{q['global']:08X}",q['slot'],f"{q['vt']:08X}",f"{q['install_site']:08X}"])
# samples
c1=[x for x in features if x['class']=='C1']
c2=[x for x in features if x['class']=='C2' and x['entry'] not in avoid]
with (OUT/'EVIDENCE'/'C1_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','evidence','name'])
    for x in c1[:10]:
        ev=('direct:'+','.join(f'{s:08X}' for s in x['direct_calls'][:3])) if x['direct_calls'] else ('exact:'+','.join(f"{q['site']:08X}/g{q['global']:08X}/s{q['slot']}" for q in x['exact'][:3]))
        w.writerow([x['entry'],x['subsystem'],ev,x['name']])
with (OUT/'EVIDENCE'/'C2_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','rtti','witness','name'])
    for x in c2[:12]:
        cls=';'.join(sorted({v['rtti']['name'] for v in x['rtti']}))
        ww=x['witnesses'][0] if x['witnesses'] else None
        ev='' if ww is None else (f"{ww[0]}@{ww[1]:08X}"+(f"/g{ww[2]:08X}" if ww[0]=='install' else ''))
        w.writerow([x['entry'],x['subsystem'],cls,ev,x['name']])
# counts and gate outcomes
matrix={}; per_sub={}
for s in SUBS:
    xs=[x for x in features if x['subsystem']==s]
    cnt=Counter(x['class'] for x in xs)
    matrix[s]={k:cnt.get(k,0) for k in ['C1','C2','C3','C4']}
    m=metrics[s]; cur=m['proved']; thr=m['threshold']
    strict=min(cur+cnt.get('C1',0),m['n']); three=min(cur+cnt.get('C1',0)+cnt.get('C2',0),m['n'])
    per_sub[s]={'n':m['n'],'named_S':m['named_S'],'current_proved':cur,'threshold':thr,
                'strict_proved':strict,'strict_pass':strict>=thr,'strict_gap':max(0,thr-strict),
                'three_proved':three,'three_pass':three>=thr,'three_gap':max(0,thr-three)}
# alternative requiring semantic_named for C1
alt_counts={}
for s in SUBS:
    xs=[x for x in features if x['subsystem']==s]
    alt_counts[s]=Counter('C1' if (x['direct_calls'] or x['exact']) and x['semantic_named'] else ('C4' if (x['direct_calls'] or x['exact']) else x['class']) for x in xs)

result={
 'exe_sha256':exe_sha,'expected_sha256':'73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476',
 'inputs':{'coverage_rows':len(cov),'atlas_rows':len(atlas),'coverage_grades':dict(grades),'static_in_atlas':static_in_atlas,'static_in_atlas_nonS22':static_in_atlas_nonS22,'proved_gap_all_subsystems_including_S22':proved_gap,'proved_gap_nonS22':proved_gap_nonS22},
 'disk_gate':lead_gate,'n9_mismatch':mismatch,
 'selfcheck019':selfcheck,
 'capstone':{'text_instructions':len(insns),'direct_call_sites':sum(len(v) for v in direct.values()),'aligned_dword_vt_scan_entries':len(scan_entries),'aligned_dword_hits':sum(len(v) for v in raw_hits.values()),'install_records':sum(len(v) for v in installs.values()),'rtti_table_hits':sum(len(v) for v in vt_tables.values()),'exact_call_sites':sum(len(v) for v in exact.values())},
 'baseline':baseline,
 'matrix':matrix,'subsystem_outcomes':per_sub,
 'totals':{
   'static_rows':len(features),
   'C1':sum(v['C1'] for v in matrix.values()),'C2':sum(v['C2'] for v in matrix.values()),
   'C3':sum(v['C3'] for v in matrix.values()),'C4':sum(v['C4'] for v in matrix.values()),
   'strict_up':sum(v['C1'] for v in matrix.values()),
   'three_up':sum(v['C1']+v['C2'] for v in matrix.values()),
   'strict_pass_count':sum(v['strict_pass'] for v in per_sub.values()),
   'three_pass_count':sum(v['three_pass'] for v in per_sub.values())},
 'c1_sample_count':len(c1),'c2_sample_count_non61':len(c2),'avoid61_count':len(avoid),
 'alternative_c1_requires_named':{s:dict(alt_counts[s]) for s in SUBS}
}
(OUT/'work'/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'work'/'baseline_hits.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
