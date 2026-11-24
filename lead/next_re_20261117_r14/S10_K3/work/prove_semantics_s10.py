#!/usr/bin/env python3
"""S10-K3 strict semantic proof pass.

Allowed proof types only:
  1 WhatAmI: B8 imm32 C3 + enum(AbstractType) + RTTI class semantic + slot11/slot12 boundary via factory/ctor.
  2 GetSize: B8 imm32 C3 + factory push(size) -> operator new -> ctor writes canonical vtable.
  3 Mission_* behavior: exhaustively decoded default no-op mission handlers (body entry-to-ret + dispatch call/result store).
  4 RTTI class-name: placeholder rows with no RTTI anchor are fail-closed (0 rows).
No vtable-slot-only upgrades. No Ghidra.
"""
from pathlib import Path
import csv,json,struct,re,hashlib,collections
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
CARD=ROOT/'lead/next_re_20261117_r14/S10_K3'; WORK=CARD/'work'; EVID=CARD/'EVIDENCE'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append({'name':s.Name.rstrip(b'\0').decode('latin1'),'va':IB+s.VirtualAddress,'end':IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),'raw':s.PointerToRawData,'rsize':s.SizeOfRawData})
def off(va):
    for s in secs:
        if s['va']<=va<s['end']:
            d=va-s['va']
            if d<s['rsize']: return s['raw']+d
    return None
def read(va,n):
    o=off(va)
    return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
    b=read(va,4); return None if b is None else struct.unpack('<I',b)[0]
def hx(n): return format(n,'08X')
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,nbytes=512,count=100):
    b=read(va,nbytes)
    return list(md.disasm(b,va,count=count)) if b is not None else []
def shape(va):
    b=read(va,6)
    if b and len(b)==6 and b[0]==0xB8 and b[5]==0xC3:
        return {'kind':'B8_IMM32_C3','imm':struct.unpack_from('<I',b,1)[0],'bytes':b.hex()}
    b4=read(va,8)
    if b4 and b4[0]==0xB8 and b4[5]==0xC2:
        return {'kind':'B8_IMM32_C2_RET4','imm':struct.unpack_from('<I',b4,1)[0],'bytes':b4[:6].hex()}
    return {'kind':'OTHER','bytes':(b or b'').hex()}
def norm(x): return x.strip().lower()
with (WORK/'all_rtti.json').open(encoding='utf-8') as f: rj=json.load(f)
vtables=rj['vtables']; enum=rj['enum']; enum_by_val={e['value']:e for e in enum}
cov_all=list(csv.DictReader(COV.open('r',encoding='utf-8',newline=''),delimiter='\t'))
cov=[r for r in cov_all if r['subsystem'].strip().upper()=='S10']
atl={norm(r['entry']) for r in csv.DictReader(ATL.open('r',encoding='utf-8',newline=''),delimiter='\t')}
cov_by={norm(r['entry']):r for r in cov}
inter=[r for r in cov if norm(r['entry']) in atl]
anchor=collections.defaultdict(list)
for v in vtables:
    for i,s in enumerate(v['slots']):
        anchor[norm(s)].append({'vt':v['vt_hex'],'col':v['col_hex'],'class':v['class'],'offset':v['offset'],'slot':i,'nslots':v['nslots']})
class_vts=collections.defaultdict(dict)
for v in vtables:
    m=re.fullmatch(r'\.\?AV([A-Za-z0-9_]+)@@',v['class'])
    if m: class_vts[m.group(1)][v['offset']]=v
# operator new from all TClassFactory slot3 Create functions (atlas-independent)
factory_vts=[]
for v in vtables:
    m=re.search(r'TClassFactory@V([A-Za-z0-9_]+)@@',v['class'])
    if m and len(v['slots'])>3: factory_vts.append({'class':m.group(1),'vt':v,'ci':int(v['slots'][3],16)})
call_counter=collections.Counter()
for f in factory_vts:
    for it in dis(f['ci'],256,120):
        if it.mnemonic=='call' and it.op_str.startswith('0x'):
            call_counter[int(it.op_str,16)]+=1
operator_new=call_counter.most_common(1)[0][0] if call_counter else None

def push_before_new(ci):
    ins=dis(ci,256,120); idx=None
    for i,it in enumerate(ins):
        if it.mnemonic=='call' and it.op_str.startswith('0x') and int(it.op_str,16)==operator_new: idx=i; break
    if idx is None: return None
    for j in range(idx-1,-1,-1):
        it=ins[j]
        if it.mnemonic=='call': break
        if it.mnemonic=='push':
            try: sz=int(it.op_str,16)
            except ValueError: continue
            enc='6A imm8' if it.bytes[:1]==b'\x6a' else ('68 imm32' if it.bytes[:1]==b'\x68' else 'other')
            return {'size':sz,'encoding':enc,'addr':hx(it.address),'bytes':it.bytes.hex()}
    return None

def ctor_after_new(ci,canonical_vts):
    ins=dis(ci,256,120); indices=[i for i,it in enumerate(ins) if it.mnemonic=='call' and it.op_str.startswith('0x') and int(it.op_str,16)==operator_new]
    if not indices: return None
    i=indices[0]
    for jt in ins[i+1:]:
        if jt.mnemonic!='call' or not jt.op_str.startswith('0x'): continue
        ctor=int(jt.op_str,16)
        if ctor==0x7C8B3D: continue
        hits=[]
        for it in dis(ctor,1024,400):
            if it.mnemonic=='mov' and ', 0x' in it.op_str:
                m=re.search(r', 0x([0-9a-fA-F]+)$',it.op_str)
                if m and int(m.group(1),16) in canonical_vts:
                    hits.append({'addr':hx(it.address),'bytes':it.bytes.hex(),'vt':hx(int(m.group(1),16)),'insn':it.op_str})
            if it.mnemonic=='ret': break
        if hits: return {'ctor':hx(ctor),'vptr_writes':hits}
    return None
# GetSize closure for concrete classes that have a slot12 row in S10 coverage
getsize=[]; getsize_by_class={}
for f in factory_vts:
    cn=f['class']; v0=class_vts.get(cn,{}).get(0)
    if not v0 or len(v0['slots'])<=12: continue
    e12=norm(v0['slots'][12]); r=cov_by.get(e12)
    if not r or norm(e12) not in atl or r['grade'].strip()=='[已证]': continue
    sh=shape(int(e12,16))
    if sh['kind']!='B8_IMM32_C3': continue
    push=push_before_new(f['ci'])
    canonical=set(int(x['vt_hex'],16) for x in class_vts.get(cn,{}).values())
    ctor=ctor_after_new(f['ci'],canonical)
    closed=bool(push and ctor and push['size']==sh['imm'])
    row={'class':cn,'factory_vt':f['vt']['vt_hex'],'factory_entry':hx(f['ci']),'canonical_vt':v0['vt_hex'],
         'col':v0['col_hex'],'slot12_entry':r['entry'].strip().upper(),'bytes':sh['bytes'],'imm':sh['imm'],
         'push':push,'operator_new':hx(operator_new) if operator_new else None,'ctor':ctor,'closed':closed}
    getsize.append(row)
    if closed: getsize_by_class[cn]=row
# WhatAmI semantic match, only off0 slot11, with slot12 GetSize boundary closure
def enum_class_match(cname,ename):
    m=re.fullmatch(r'\.\?AV([A-Za-z0-9_]+)@@',cname)
    if not m: return False
    cls=m.group(1)
    if '$' in cls: return False
    base=cls[:-5] if cls.endswith('Class') else cls
    return ename==base
whatami=[]
for r in inter:
    if r['grade'].strip()=='[已证]': continue
    e=norm(r['entry']); sh=shape(int(r['entry'].strip(),16))
    if sh['kind']!='B8_IMM32_C3': continue
    ee=enum_by_val.get(sh['imm'])
    if not ee or ee['name']=='<none>': continue
    for a in anchor.get(e,[]):
        if a['offset']!=0 or a['slot']!=11: continue
        if not enum_class_match(a['class'],ee['name']): continue
        v0=next((v for v in vtables if v['vt_hex']==a['vt'] and v['offset']==0),None)
        s12=None
        if v0 and len(v0['slots'])>12: s12={'entry':v0['slots'][12],'shape':shape(int(v0['slots'][12],16))}
        cm=re.fullmatch(r'\.\?AV([A-Za-z0-9_]+)@@',a['class'])
        short_class=cm.group(1) if cm else ''
        boundary=bool(s12 and s12['shape']['kind']=='B8_IMM32_C3' and short_class in getsize_by_class)
        row={'entry':r['entry'].strip().upper(),'grade':r['grade'].strip(),'name':r['name'].strip(),
             'bytes':sh['bytes'],'imm':sh['imm'],'imm_hex':hx(sh['imm']),'class':a['class'],'vt':a['vt'],'col':a['col'],
             'slot':a['slot'],'enum_name':ee['name'],'enum_value':ee['value'],'slot12':s12,
             'getsize_boundary':boundary,'ctor_writes':getsize_by_class.get(short_class,{}).get('ctor',{}).get('vptr_writes',[])}
        if boundary: whatami.append(row)
# Mission default no-op handlers: exact entry-to-ret + dispatch stub result store
MISSION_NAMES=['Sleep','Attack','Move','QMove','Retreat','Guard','Sticky','Enter','Capture','Eaten','Harvest','Area Guard','Return','Stop','Ambush','Hunt','Unload','Sabotage','Construction','Selling','Repair','Rescue','Missile','Harmless','Open','Patrol','Paradrop Approach','Paradrop Overfly','Wait','Attack Move','Spyplane Approach','Spyplane Overfly']
stub_bytes=bytes.fromhex('b8c2010000c3')
def exact_noop(va):
    b=read(va,16)
    if not b or b[:6]!=stub_bytes: return None
    ins=dis(va,16,2)
    if len(ins)<2 or ins[0].mnemonic!='mov' or ins[1].mnemonic!='ret' or ins[1].address!=va+5: return None
    if any(x!=0x90 for x in b[6:16]): return None
    return {'bytes':b[:16].hex(),'ret_addr':hx(ins[1].address),'padding_nops':10}
# dispatch table parse
disp_table_base=0x5B34E8
table=[u32(disp_table_base+4*i) for i in range(32)]
dispatch=[]; dispatch_by_slot=collections.defaultdict(list)
for mid,stub in enumerate(table):
    info={'mission_id':mid,'mission':MISSION_NAMES[mid],'stub':hx(stub),'disp':None,'slot':None,'result_store':None}
    ins=dis(stub,192,80)
    for i,it in enumerate(ins):
        if it.mnemonic=='call' and it.op_str.startswith('dword ptr ['):
            nums=re.findall(r'0x([0-9a-fA-F]+)',it.op_str)
            if nums:
                info['disp']=int(nums[-1],16); info['slot']=info['disp']//4
            for jt in ins[i+1:i+9]:
                if jt.mnemonic=='mov' and re.fullmatch(r'dword ptr \[esi \+ 8\], eax',jt.op_str):
                    info['result_store']={'addr':hx(jt.address),'bytes':jt.bytes.hex(),'insn':jt.op_str}
            break
    info['insns']=[{'addr':hx(it.address),'bytes':it.bytes.hex(),'mnemonic':it.mnemonic,'op_str':it.op_str} for it in ins[:24]]
    dispatch.append(info)
    if info['slot'] is not None and info['result_store']: dispatch_by_slot[info['slot']].append(info)
noop=[]; noop_rejected=[]
for r in inter:
    if r['grade'].strip()=='[已证]': continue
    va=int(r['entry'].strip(),16); ex=exact_noop(va)
    if not ex: continue
    a=anchor.get(norm(r['entry']),[])
    slots=sorted(set(x['slot'] for x in a))
    callers=[]
    for s in slots: callers.extend(dispatch_by_slot.get(s,[]))
    # require every anchored mission slot to have a decoded dispatch caller and result store
    ok=bool(slots) and all(dispatch_by_slot.get(s) for s in slots)
    rec={'entry':r['entry'].strip().upper(),'grade':r['grade'].strip(),'name':r['name'].strip(),
         'body':ex,'anchors':a,'slots':slots,'callers':callers,'accepted':ok}
    (noop if ok else noop_rejected).append(rec)
# placeholder RTTI class-name channel (type 4): fail-closed when no RTTI anchor
placeholder=[]
for r in inter:
    n=r['name'].strip()
    if not n or n.startswith('sub_') or '::sub_' in n:
        a=anchor.get(norm(r['entry']),[])
        placeholder.append({'entry':r['entry'].strip().upper(),'grade':r['grade'].strip(),'name':n,'anchors':len(a)})
rtti_named=[p for p in placeholder if p['anchors']>0]
# delta rows
delta=[]
for w in whatami:
    e=w['entry']; name=f"AbstractClass::WhatAmI_{w['enum_name']}_{e}"
    sem=(f"WhatAmI: {w['class']} off0 v[{w['slot']}] returns AbstractType {w['enum_name']}=0x{w['imm_hex']}; "
         f"bytes {w['bytes']}; slot12 {w['slot12']['entry']} is GetSize-closed by ctor vptr write; enum entry {enum_by_val[w['imm']]['entry_va']} name_ptr {enum_by_val[w['imm']]['name_ptr']}")
    delta.append((e,'S10',name,sem,'[已证]','EVIDENCE/whatami_s10.txt'))
for g in getsize:
    if not g['closed']: continue
    e=g['slot12_entry']; name=f"{g['class'][3:-2] if g['class'].startswith('.?AV') and g['class'].endswith('@@') else g['class']}::GetSize"
    p=g['push']; c=g['ctor']
    sem=(f"GetSize double-point closure: {g['class']} off0 vtable {g['canonical_vt']} col {g['col']} slot12 entry {e} bytes {g['bytes']} => imm 0x{g['imm']:X}; "
         f"factory {g['factory_entry']} {p['encoding']} size 0x{p['size']:X} at {p['addr']} -> call operator new {g['operator_new']} -> ctor {c['ctor']} writes vptr {c['vptr_writes'][0]['vt']} at {c['vptr_writes'][0]['addr']}")
    delta.append((e,'S10',name,sem,'[已证]','EVIDENCE/getsize_s10.txt'))
for n in noop:
    e=n['entry']; name=f"MissionClass::Mission_DefaultHandler_{e}"
    slots=','.join('v%d'%s for s in n['slots'])
    mids=','.join(str(c['mission_id']) for c in sorted({c['stub']:c for c in n['callers']}.values(),key=lambda x:x['mission_id']))
    c0=n['callers'][0]
    sem=(f"Mission default no-op handler: {slots} dispatch stub {c0['stub']} for mission ids {{{mids}}}; "
         f"body {n['body']['bytes']} (mov eax,0x1C2; ret at {n['body']['ret_addr']}, 10 NOPs to next stub); "
         f"caller result store {c0['result_store']['insn']} @ {c0['result_store']['addr']}")
    delta.append((e,'S10',name,sem,'[已证]','EVIDENCE/mission_noop_s10.txt'))
# uniqueness guard: fail closed on duplicate entry/name
ents=[d[0] for d in delta]; nms=[d[2] for d in delta]
if len(ents)!=len(set(ents)) or len(nms)!=len(set(nms)):
    raise SystemExit('duplicate entry/name in delta')
delta=sorted(delta,key=lambda x:x[0])
with (CARD/'coverage_delta.tsv').open('w',encoding='utf-8',newline='') as f:
    for d in delta: f.write('\t'.join(d)+'\n')
# evidence files
sha=hashlib.sha256(data).hexdigest().upper(); head=['S10-K3 STRICT SEMANTIC PROOFS','SHA256='+sha,
 'TD=%d COL=%d VT=%d SLOTS=%d ENUM=%d OK=%s'%(len(rj['tds']),len(rj['cols']),len(vtables),sum(v['nslots'] for v in vtables),len(enum),rj['enum_ok']),
 'S10_ROWS=%d ATLAS_INTER=%d'%(len(cov),len(inter)),'OPERATOR_NEW=%s'%hx(operator_new),'FACTORY_CALL_TARGETS_TOP='+repr(call_counter.most_common(8)),
 'NO_VTABLE_SLOT_ONLY_UPGRADES']
(EVID/'whatami_s10.txt').write_text('\n'.join(head+[
 'WHATAMI_CANDIDATES=%d NONPROVED=%d'%(len(whatami),len(whatami)),
 *['WHATAMI '+json.dumps(x,ensure_ascii=False) for x in whatami],
 'WHATAMI_REJECT_REASON = only off0 slot11 with enum/class semantic match AND slot12 GetSize closure accepted; wrong slot/abstract/enum mismatch rejected'
])+'\n',encoding='utf-8')
(EVID/'getsize_s10.txt').write_text('\n'.join(head+[
 'GETSIZE_SLOT12_ROWS_SCANNED=%d CLOSED=%d'%(len(getsize),sum(g['closed'] for g in getsize)),
 *['GETSIZE '+json.dumps(x,ensure_ascii=False) for x in getsize],
 'ENCODING_NOPUSH='+str(sum(1 for g in getsize if g['closed'] and g['push'] and g['push']['encoding'].startswith('6A'))),
 'ENCODING_PUSH32='+str(sum(1 for g in getsize if g['closed'] and g['push'] and g['push']['encoding'].startswith('68')))
])+'\n',encoding='utf-8')
(EVID/'mission_noop_s10.txt').write_text('\n'.join(head+[
 'DISPATCH_TABLE_BASE=%08X COUNT=%d'%(disp_table_base,len(table)),
 'DISPATCH_TABLE='+','.join(hx(x) for x in table),
 *['DISPATCH '+json.dumps(x,ensure_ascii=False) for x in dispatch],
 'NOOP_ACCEPTED=%d REJECTED=%d'%(len(noop),len(noop_rejected)),
 *['NOOP '+json.dumps(x,ensure_ascii=False) for x in noop],
 *['NOOP_REJECTED '+json.dumps(x,ensure_ascii=False) for x in noop_rejected]
])+'\n',encoding='utf-8')
# exhaustive census / exclusions
cov_b8=[]
for r in inter:
    sh=shape(int(r['entry'].strip(),16))
    if sh['kind'].startswith('B8_IMM32'):
        cov_b8.append({'entry':r['entry'].strip().upper(),'grade':r['grade'].strip(),'name':r['name'].strip(),'kind':sh['kind'],'imm':sh.get('imm'),'bytes':sh['bytes']})
(EVID/'semantic_census_s10.txt').write_text('\n'.join(head+[
 'CHANNEL_A_COVERAGE_ENTRY_BYTES: B8_IMM32_C3=%d B8_IMM32_C2_RET4=%d'%(
   sum(x['kind']=='B8_IMM32_C3' for x in cov_b8),sum(x['kind']=='B8_IMM32_C2_RET4' for x in cov_b8)),
 'CHANNEL_B_RTTI_ANCHORED: nonproved_anchored=%d'%sum(1 for r in inter if r['grade'].strip()!='[已证]' and anchor.get(norm(r['entry']))),
 'WHATAMI_UPGRADES=%d GETSIZE_UPGRADES=%d MISSION_NOOP_UPGRADES=%d RTTI_NAME_UPGRADES=%d'%(len(whatami),sum(g['closed'] for g in getsize),len(noop),len(rtti_named)),
 'PLACEHOLDER_ROWS=%d PLACEHOLDER_WITH_RTTI_ANCHOR=%d'%(len(placeholder),len(rtti_named)),
 'B8_IMM32_C3_ROWS='+str(sum(x['kind']=='B8_IMM32_C3' for x in cov_b8)),
 *['COV_B8 '+json.dumps(x,ensure_ascii=False) for x in cov_b8],
 *['PLACEHOLDER '+json.dumps(x,ensure_ascii=False) for x in placeholder],
 'EXCLUSION: 0x1C2 stubs accepted only when entry-to-ret exact body + dispatch call/result-store decoded; vtable membership alone never used',
 'EXCLUSION: 004D27C0/00417FE0/004D27C0-class constant returns already [已证] or not in nonproved strict set',
 'EXCLUSION: 0070DD90 AircraftClass slot250 imm=1 is neither AbstractType semantic match nor off0 slot11/12 GetSize; remains unchanged',
 'EXCLUSION: 005B3970 MissionClass::slot13 serializer/destructor-like rows not upgraded because no listed proof type binds the chosen method name without vtable-slot inference'
])+'\n',encoding='utf-8')
(WORK/'semantic_candidates_s10.json').write_text(json.dumps({'whatami':whatami,'getsize':getsize,'noop':noop,'noop_rejected':noop_rejected,'placeholder':placeholder,'cov_b8':cov_b8,'delta':delta},ensure_ascii=False,indent=2),encoding='utf-8')
print('whatami=%d getsize=%d noop=%d rtti_name=%d delta=%d'%(len(whatami),sum(g['closed'] for g in getsize),len(noop),len(rtti_named),len(delta)))
