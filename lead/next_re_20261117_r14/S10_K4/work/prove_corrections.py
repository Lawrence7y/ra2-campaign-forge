#!/usr/bin/env python3
"""S10-K4: correct 19 mission-handler rows (semantics + true names), read-only against EXE."""
from pathlib import Path
import csv,struct,re,hashlib,collections
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'; COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
CARD=ROOT/'lead/next_re_20261117_r14/S10_K4'; EVID=CARD/'EVIDENCE'
data=EXE.read_bytes(); pe=pefile.PE(str(EXE),fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append({'va':IB+s.VirtualAddress,'end':IB+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData),'raw':s.PointerToRawData,'rsize':s.SizeOfRawData})
def off(va):
    for s in secs:
        if s['va']<=va<s['end']:
            d=va-s['va']
            if d<s['rsize']: return s['raw']+d
    return None
def rd(va,n):
    o=off(va)
    return None if o is None or o+n>len(data) else data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack('<I',b)[0] if b else None
def cstr(va):
    b=rd(va,200); return b.split(b'\0')[0].decode('latin1','replace') if b else '<null>'
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
def dis(va,n,count=100):
    b=rd(va,n); return list(md.disasm(b,va,count=count)) if b else []
def hx(n): return format(n,'08X')
# RTTI / vtable anchor
VT=0x007EDCC0
col=u32(VT-4); td=u32(col+0xC); td_name=cstr(td+8)
assert td_name=='.?AVMissionClass@@',td_name
vt_slots={}
for i in range(129,157): vt_slots[i]=u32(VT+4*i)
vt_by_entry={v:k for k,v in vt_slots.items()}
ctor_w=[(i.address,i.bytes.hex(),i.op_str) for i in dis(0x5B2DA0,0x80,80) if '0x7edcc0' in i.op_str.lower()]
assert any('[esi]' in op for _,_,op in ctor_w),ctor_w
# mission name table
name_table=[cstr(u32(0x816CAC+4*i)) for i in range(32)]
assert name_table[23]=='Harmless' and name_table[1]=='Attack' and name_table[30]=='Spyplane Approach'
# dispatch table + each dispatch case body
disp_table=[u32(0x5B34E8+4*i) for i in range(32)]
dispatch={}
for mid,stub in enumerate(disp_table):
    ins=dis(stub,80,60)
    call_addr=None; disp=None; stores={}
    for k,it in enumerate(ins):
        if it.mnemonic=='call' and 'dword ptr [' in it.op_str:
            m=re.search(r'\+ (0x[0-9a-fA-F]+)\]',it.op_str)
            if m:
                disp=int(m.group(1),16); call_addr=it.address
                for jt in ins[k+1:k+12]:
                    sm=re.fullmatch(r'dword ptr \[esi(?: \+ (0x[0-9a-fA-F]+|\d+))?\], (\w+)',jt.op_str)
                    if sm:
                        offv=int(sm.group(1),0) if sm.group(1) else 0
                        stores[offv]=(hx(jt.address),jt.bytes.hex(),sm.group(2))
                break
    dispatch[mid]={'mission_id':mid,'name':name_table[mid],'stub':hx(stub),'vslot':disp//4 if disp is not None else None,
                   'disp':disp,'call_addr':hx(call_addr) if call_addr else None,'stores':stores}
# verify shared Timer writes in every dispatch case used by the 19 rows
required_stores=[0,4,8]
frame_load_ok={}
for mid,d in dispatch.items():
    ins=dis(int(d['stub'],16),80,60)
    frame_load_ok[mid]=any(it.mnemonic=='mov' and it.op_str=='ecx, dword ptr [0xa8ed84]' for it in ins)
    d['frame_load']=frame_load_ok[mid]
# Timer head in 005B3060
head=dis(0x5B3060,0x90,80)
head_text=['%08X %s %-8s %s'%(i.address,i.bytes.hex(),i.mnemonic,i.op_str) for i in head]
assert any(i.mnemonic=='lea' and 'esi, [edi + 0xc8]' in i.op_str for i in head)
assert any(i.mnemonic=='cmp' and i.op_str=='edx, -1' for i in head) and any(i.mnemonic=='sub' and i.op_str=='ecx, edx' for i in head)
assert any(i.mnemonic=='jmp' and '0x5b34e8' in i.op_str for i in head)
# entries and true names; primary mission from dispatch vslot (shared slots use first dispatch name, matching S10-K1 convention)
TRUE_NAMES={
 '005B2E20':'MissionClass::Mission_Harmless',
 '005B2E30':'MissionClass::Mission_Ambush',
 '005B2E40':'MissionClass::Mission_Attack',
 '005B2E50':'MissionClass::Mission_Capture',       # v133 also dispatched by Sabotage id17
 '005B2E70':'MissionClass::Mission_Guard',         # v135 also dispatched by Sticky id6
 '005B2E80':'MissionClass::Mission_AreaGuard',
 '005B2E90':'MissionClass::Mission_Harvest',
 '005B2ED0':'MissionClass::Mission_Return',
 '005B2EE0':'MissionClass::Mission_Stop',
 '005B2EF0':'MissionClass::Mission_Unload',
 '005B2F10':'MissionClass::Mission_Construction',
 '005B2F20':'MissionClass::Mission_Selling',
 '005B2F30':'MissionClass::Mission_Repair',
 '005B2F40':'MissionClass::Mission_Missile',
 '005B2F50':'MissionClass::Mission_Open',
 '005B2F80':'MissionClass::Mission_ParadropApproach',
 '005B2F90':'MissionClass::Mission_ParadropOverfly',
 '005B2FA0':'MissionClass::Mission_Wait',
 '005B2FB0':'MissionClass::Mission_SpyplaneApproach',
}
def nop_count(va):
    b=rd(va,512); n=0
    while n<len(b) and b[n]==0x90: n+=1
    return n
rows=[]; errors=[]
for entry in sorted(TRUE_NAMES):
    va=int(entry,16); slot=vt_by_entry.get(va)
    mids=[m for m,d in dispatch.items() if d['vslot']==slot]
    if slot is None or not mids: errors.append((entry,'no_slot_or_mid')); continue
    body=rd(va,512); ins=dis(va,32,4)
    if not body or body[:6]!=bytes.fromhex('b8c2010000c3'): errors.append((entry,'bad_body')); continue
    if len(ins)<2 or ins[0].mnemonic!='mov' or ins[1].mnemonic!='ret' or ins[1].address!=va+5: errors.append((entry,'not_2_insns')); continue
    const=struct.unpack_from('<I',body,1)[0]
    nops=nop_count(va+6)
    store_info={}
    ok=True
    for m in mids:
        d=dispatch[m]
        if not d['frame_load'] or any(o not in d['stores'] for o in required_stores) or d['stores'][8][2]!='eax': ok=False
        store_info[m]=d
    if not ok: errors.append((entry,'store_incomplete'))
    primary=min(mids)
    rows.append({'entry':entry,'slot':slot,'mids':mids,'names':[name_table[m] for m in mids],
                 'name':TRUE_NAMES[entry],'const':const,'nop':nops,'ret':hx(va+5),
                 'body':body[:6].hex(),'cap':['%s %s'%(i.mnemonic,i.op_str) for i in ins[:2]],
                 'stub':store_info[primary]['stub'],'store_abs':store_info[primary]['stores'][8][0],
                 'store_bytes':store_info[primary]['stores'][8][1],'disp':store_info[primary]['disp']})
if errors: raise SystemExit('ERRORS '+repr(errors))
# audit's NOP-length correction: gap from end of 6-byte body to next corrected row in this 19-row set
srt=sorted(int(e,16) for e in TRUE_NAMES)
for r in rows:
    va=int(r['entry'],16); nxt=next((x for x in srt if x>va),None)
    r['pad_to_next']=(nxt-va-6) if nxt else None
    r['next_entry']=('%08X'%nxt) if nxt else '-'
# evidence
sha=hashlib.sha256(data).hexdigest().upper()
out=['S10-K4 CORRECTED 19 MISSION HANDLER ROWS',
     'SHA256='+sha,
     'VTABLE=%08X COL=%08X TD=%08X TD_NAME=%s'%(VT,col,td,td_name),
     'CTOR_VPTR_WRITE='+repr(ctor_w),
     'NAME_TABLE=0x816CAC indexed by mission id; read by 005B3740/005B3760/005B3910/005B3950',
     'DISPATCH_TABLE=0x5B34E8 indexed by [this+0xAC] at 005B30B2; switch 005B30C1',
     'TIMER_GATE=005B307A-005B30A1; ESI_LEA=005B3086 lea esi,[edi+0xC8]',
     'TIMER_STORE=[esi]=StartTime=CurrentFrame(0xA8ED84); [esi+4]=parsed second field; [esi+8]=TimeLeft=eax(return)',
     'CHANNEL_1=dispatch id->stub->vslot; CHANNEL_2=in-binary mission name table 0x816CAC; CHANNEL_3=RTTI COL+0xC->TD+8 and ctor vptr write',
     'NOP_COUNT=contiguous 0x90 bytes immediately after 6-byte body; PAD_TO_NEXT=gap from body end to next corrected row (audit correction; includes skipped sibling stubs); atlas size=6 means padding is not function body',
     '']
for r in rows:
    out.append('ENTRY=%s NAME=%s VSLOT=%d MIDS=%s MISSION_NAMES=%s'%(r['entry'],r['name'],r['slot'],r['mids'],r['names']))
    out.append('  BODY=%s RET=%s DISASM=%s CONST=%d(0x%X) CONTIGUOUS_NOP90=%d PAD_TO_NEXT_CORRECTED_ROW=%s NEXT=%s'%(r['body'],r['ret'],r['cap'],r['const'],r['const'],r['nop'],r['pad_to_next'],r['next_entry']))
    out.append('  DISPATCH_STUB=%s CALL_DISP=0x%X RESULT_STORE=%s BYTES=%s (dword ptr [esi+8],eax => [edi+0xD0]=TimeLeft)'%(r['stub'],r['disp'],r['store_abs'],r['store_bytes']))
    out.append('  SEMANTICS=returns %d-frame polling interval (MissionClass::UpdateTimer TimeLeft), approx %.3fs@60fps'%(r['const'],r['const']/60.0))
(EVID/'mission_rows_corrected.txt').write_text('\n'.join(out)+'\n',encoding='utf-8')
# delta: 19 semantic/name corrections, grade stays proved as audited K3
FN=['entry','subsystem','name','one_line_semantics','grade','evidence_path']
with COV.open('r',encoding='utf-8',newline='') as f: cov=list(csv.DictReader(f,delimiter='\t'))
cov_by={r['entry'].strip().lower():r for r in cov}
delta=[]
for r in rows:
    mids=','.join(str(m) for m in r['mids'])
    alias=('; same vslot also mission %s'%','.join(r['names'][1:])) if len(r['mids'])>1 else ''
    pad_disp=(str(r['pad_to_next'])+'B') if r['pad_to_next'] is not None else 'n/a(last)'
    sem=(f"{r['name']}: v{r['slot']} default mission timer handler for mission {r['names'][0]}(id {mids}{alias}): "
         f"body {r['body']} = mov eax,0x{r['const']:X}; ret (2 insns, 10 contiguous 0x90, pad_to_next_corrected_row={pad_disp}); "
         f"dispatch stub {r['stub']} call [vptr+0x{r['disp']:X}] -> 005B3086 esi=edi+0xC8, {r['store_abs']} [esi+8]=eax -> [edi+0xD0]=TimeLeft={r['const']} frames, StartTime [edi+0xC8]=CurrentFrame; "
         f"=> returns {r['const']}-frame polling interval (MissionClass::UpdateTimer), approx {r['const']/60.0:.3f}s@60fps; entry-to-ret verified")
    delta.append([r['entry'],'S10',r['name'],sem,'[已证]','EVIDENCE/mission_rows_corrected.txt'])
ents=[d[0] for d in delta]; nms=[d[2] for d in delta]
assert len(ents)==len(set(ents)) and len(nms)==len(set(nms))
with (CARD/'coverage_delta.tsv').open('w',encoding='utf-8',newline='') as f:
    for d in delta: f.write('\t'.join(d)+'\n')
print('rows=%d contiguous_nop=%s pad_to_next=%s'%(len(rows),collections.Counter(r['nop'] for r in rows),collections.Counter(r['pad_to_next'] for r in rows)))
for r in rows: print(r['entry'],r['name'],r['slot'],r['mids'],'contig90=',r['nop'],'pad_next=',r['pad_to_next'])
