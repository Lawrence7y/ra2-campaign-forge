#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S22-CENSUS exploratory channel counts. Read-only inputs; writes only under S22_CENSUS/work."""
import sys, os, re, struct, json, hashlib, bisect, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86_const import X86_INS_MOV, X86_INS_LEA, X86_INS_PUSH, X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_INVALID

ROOT = r'D:/Project/ra2-campaign-forge'
EXE = os.path.join(ROOT,'ra2youli','gamemd.exe')
COV = os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
ATL = os.path.join(ROOT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
WORK = os.path.join(ROOT,'lead','next_re_20261117_r14','S22_CENSUS','work')
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = pe.__data__
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode('latin1')
    secs.append(dict(nm=nm, va=IB+s.VirtualAddress, rva=s.VirtualAddress, vsize=s.Misc_VirtualSize, raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
by={s['nm']:s for s in secs}

def u32(va):
    rva=va-IB
    for s in secs:
        if s['rva'] <= rva < s['rva']+max(s['vsize'],s['rawsize']):
            off=s['raw']+(rva-s['rva'])
            if off+4 <= len(DATA) and off+4 <= s['raw']+s['rawsize']:
                return struct.unpack_from('<I',DATA,off)[0]
            break
    raise KeyError(hex(va))

def cstr(va, maxb=200):
    rva=va-IB
    for s in secs:
        if s['rva'] <= rva < s['rva']+max(s['vsize'],s['rawsize']):
            off=s['raw']+(rva-s['rva'])
            chunk=DATA[off:off+maxb]
            z=chunk.find(b'\0')
            return chunk[:z] if z>=0 else None
    return None

def demangle(nm):
    if not nm: return nm
    s=nm
    for p in ('.?AV','.?AU'):
        if s.startswith(p): s=s[4:]; break
    if s.endswith('@@'): s=s[:-2]
    return s

# TD: inline name at TD+8; fail closed on malformed
tds={}
for s in secs:
    if s['nm'] not in ('.rdata','.data'): continue
    buf=DATA[s['raw']:s['raw']+s['rawsize']]
    for off in range(0,len(buf)-16,4):
        va=s['va']+off
        if struct.unpack_from('<I',buf,off)[0] != 0x7F9594: continue
        if struct.unpack_from('<I',buf,off+4)[0] != 0: continue
        raw=cstr(va+8)
        if not raw or not raw.startswith((b'.?AV',b'.?AU')) or not raw.endswith(b'@@'): continue
        nm=raw.decode('latin1')
        cls=demangle(nm)
        if not cls: continue
        tds[va]=dict(td=va, raw=nm, cls=cls, section=s['nm'])
print('TDs',len(tds))
# COL: +0xC -> TD; sig 0, CHD pointer sanity
cols={}
for s in secs:
    if s['nm'] not in ('.rdata','.data'): continue
    buf=DATA[s['raw']:s['raw']+s['rawsize']]
    for off in range(0,len(buf)-20,4):
        va=s['va']+off
        sig, offv, cdoff = struct.unpack_from('<III',buf,off)
        ptd=struct.unpack_from('<I',buf,off+12)[0]
        chd=struct.unpack_from('<I',buf,off+16)[0]
        if sig != 0 or ptd not in tds: continue
        if not (0x400000 <= chd < 0x900000): continue
        cols[va]=dict(col=va, sig=sig, off=offv, cdoff=cdoff, td=ptd, chd=chd, raw=tds[ptd]['raw'], cls=tds[ptd]['cls'])
print('COLs',len(cols))
# vtable scan in .rdata only
r=by['.rdata']; buf=DATA[r['raw']:r['raw']+r['rawsize']]
text=by['.text']; tlo=text['va']; thi=text['va']+text['rawsize']
colset=set(cols)
vpos=[]
for off in range(0,len(buf)-4,4):
    v=struct.unpack_from('<I',buf,off)[0]
    if v in colset: vpos.append((r['va']+off,v))
vpos.sort()
vts=[]; slot_to_members=collections.defaultdict(list); vt_by_addr={}
for k,(pos,col) in enumerate(vpos):
    vt=pos+4
    hard=vpos[k+1][0] if k+1<len(vpos) else r['va']+len(buf)
    slots=[]
    va=vt
    while va < hard:
        try: fv=u32(va)
        except KeyError: break
        if not (tlo <= fv < thi): break
        slots.append((va,fv)); va+=4
    rec=dict(vt=vt, col=col, td=cols[col]['td'], cls=cols[col]['cls'], slots=slots, end=va)
    vts.append(rec); vt_by_addr[vt]=rec
    for i,(sva,fv) in enumerate(slots):
        slot_to_members[fv].append(dict(vt=vt,col=col,td=cols[col]['td'],cls=cols[col]['cls'],slot=i,sva=sva))
print('vtable tables',len(vts),'slots',sum(len(v['slots']) for v in vts))
# scope
with open(ATL,'r',encoding='utf-8',errors='replace') as f:
    ah=f.readline().rstrip('\n'); al=[ln.rstrip('\n').split('\t') for ln in f if ln.strip()]
asize={int(r[0],16): int(r[1]) for r in al}
aset=set(asize)
with open(COV,'r',encoding='utf-8',errors='replace') as f:
    ch=f.readline().rstrip('\n'); cr=[ln.rstrip('\n').split('\t') for ln in f if ln.strip()]
targets=[r for r in cr if r[1].strip().upper()=='S22' and int(r[0],16) in aset]
print('S22∩atlas',len(targets))

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
coltd=set(cols)|set(tds)
TAB=chr(9)
def hx(x): return '%08X' % (x & 0xffffffff)
def tl(vals): return TAB.join('' if v is None else str(v).replace(TAB,' ').replace('\n',' ') for v in vals)+'\n'
def suggest(cls):
    c=cls or ''
    if c.startswith('?$VectorClass@') or c.startswith('?$DynamicVectorClass@') or c.startswith('T_VectorClass_') or c.startswith('T_DynamicVectorClass_') or c.startswith('T_TClassFactory_') or c.startswith('T_DiscreteDistributionClass_'):
        return 'S22(保留)'
    rules=[
      (('LocomotionClass','WalkLocomotionClass','DriveLocomotionClass','FlyLocomotionClass','JumpjetLocomotionClass','ShipLocomotionClass','TeleportLocomotionClass'),'S11'),
      (('TeamClass','TeamTypeClass','HouseClass','HouseTypeClass','ScriptClass','ScriptTypeClass','TaskForceClass','AITriggerTypeClass','AITriggerClass'),'S14'),
      (('WeaponTypeClass','WarheadTypeClass','BulletClass','WeaponClass','TargetingClass'),'S13'),
      (('CommandClass','TacticalClass','SidebarClass','SelectClass','GadgetClass','ControlClass'),'S09'),
      (('SpawnManagerClass','InfantryClass','UnitClass','VehicleClass','AircraftClass','BuildingClass','FootClass','TechnoClass','MissionClass'),'S10'),
      (('ObjectClass','AbstractClass','TechnoTypeClass','InfantryTypeClass','UnitTypeClass','BuildingTypeClass','AircraftTypeClass'),'S05'),
      (('CellClass','MapClass','TerrainClass','OverlayClass','SmudgeClass','TerrainTypeClass','OverlayTypeClass','SmudgeTypeClass'),'S06'),
      (('TagClass','TriggerClass','TriggerTypeClass','TEventClass','TActionClass'),'S15'),
      (('SuperClass','SuperWeaponTypeClass'),'S16'),
      (('SwizzleClass','SaveGameClass','LoadGameClass'),'S17'),
      (('WinsockInterfaceClass','NetworkClass','EventClass'),'S18'),
      (('VocClass','VoxClass','MovieHandle','AudioClass','SoundClass'),'S19'),
      (('ParticleClass','ParticleSystemClass','AnimClass','VoxelAnimClass','EMPulseClass'),'S20'),
      (('CampaignClass','SideClass','WorldDominationTour'),'S21'),
      (('FileEntryClass','CCFileClass','CDFileClass'),'S03'),
      (('WinsockBufferType','IConnectionPoint'),'S18'),
      (('ToolTipClass','CheckListClass','ButtonFadeEffect'),'S09'),
    ]
    for keys,sub in rules:
        if any(k in c for k in keys): return sub
    return '-'
# coverage hint (advice only)
hint_counts=collections.Counter()
for row in cr:
    if len(row)<5: continue
    sub=row[1].strip().upper()
    if sub=='S22': continue
    m=re.match(r'([A-Za-z_][A-Za-z0-9_$?@]*)::',row[2])
    if m: hint_counts[(m.group(1),sub)]+=1
class_hint={}
for (cls,sub),n in hint_counts.items():
    tot=sum(v for (c2,_),v in hint_counts.items() if c2==cls)
    if tot and n/tot>=0.6: class_hint[cls]=(sub,n,tot)
# classify
results=[]; kinds=collections.Counter(); cc=collections.Counter(); ckind=collections.defaultdict(collections.Counter)
hesitant=collections.Counter()
for row in targets:
    es=row[0].upper(); e=int(es,16); a1=slot_to_members.get(e,[]); a2=[]; a3=[]
    a3d=[]; a3r=[]; sem=[]
    regvt=collections.defaultdict(set)
    try:
        sec=next(s for s in secs if s['rva']<=e-IB<s['rva']+max(s['vsize'],s['rawsize']))
        off=sec['raw']+(e-IB); body=DATA[off:off+asize[e]]
    except Exception:
        body=b''
    for insn in md.disasm(body,e):
        if insn.id==0: continue
        txt=(insn.mnemonic+' '+insn.op_str).strip()
        for op in insn.operands:
            if op.type==X86_OP_IMM:
                v=op.imm&0xffffffff
                if v in coltd:
                    a3.append(dict(addr=insn.address,insn=txt,val=v,ref='COL' if v in colset else 'TD',raw=(tds[cols[v]['td']].get('raw','') if v in colset else tds[v].get('raw',''))))
            elif op.type==X86_OP_MEM and op.mem.disp:
                v=op.mem.disp&0xffffffff
                if v in coltd: a3d.append((insn.address,txt,v))
        if insn.id==X86_INS_MOV and len(insn.operands)>=2:
            dst,src=insn.operands[0],insn.operands[1]
            if dst.type==X86_OP_MEM and (dst.mem.base!=X86_REG_INVALID or dst.mem.index!=X86_REG_INVALID) and src.type==X86_OP_IMM:
                v=src.imm&0xffffffff
                if v in vt_by_addr:
                    rec=vt_by_addr[v]; col,td,cls=rec['col'],rec['td'],rec.get('cls', rec.get('class', '')); a2.append(dict(addr=insn.address,insn=txt,vt=v,col=col,td=td,cls=cls))
            if dst.type==X86_OP_MEM and src.type==X86_OP_REG:
                for v in sorted(regvt.get(src.reg,set())): sem.append((insn.address,txt,v))
            if dst.type==X86_OP_REG:
                if src.type==X86_OP_IMM and (src.imm&0xffffffff) in vt_by_addr: regvt[dst.reg]={src.imm&0xffffffff}
                elif src.type==X86_OP_MEM and (src.mem.disp&0xffffffff) in vt_by_addr: regvt[dst.reg]={src.mem.disp&0xffffffff}
                elif src.type==X86_OP_REG: regvt[dst.reg]=set(regvt.get(src.reg,set()))
                else: regvt.pop(dst.reg,None)
        for reg in insn.regs_write:
            if insn.id==X86_INS_MOV and len(insn.operands)>=2 and insn.operands[0].type==X86_OP_REG and insn.operands[0].reg==reg: continue
            regvt.pop(reg,None)
    for i in range(0,max(0,len(body)-3),4):
        v=struct.unpack_from('<I',body,i)[0]
        if v in coltd: a3r.append((e+i,v))
    if a1:
        k='A1'; m0=a1[0]; vt,col,td,cls=m0['vt'],m0['col'],m0['td'],m0.get('cls', m0.get('class',''))
        voc='VT=%s+0x%X;COL=%s'%(hx(vt),m0['slot']*4,hx(col))
        ev='A1 .rdata vtable slot %d@%s=%s; COL=%s[+0xC]->TD=%s; TD+8 inline %s'%(m0['slot'],hx(m0['sva']),es,hx(col),hx(td),tds[td].get('raw',''))
    elif a2:
        k='A2'; m0=a2[0]; vt,col,td,cls=m0['vt'],m0['col'],m0['td'],m0.get('cls', m0.get('class',''))
        voc='VT=%s;COL=%s'%(hx(vt),hx(col))
        ev='A2 %s: %s; VT %s -> COL %s -> TD %s; TD+8 inline %s'%(hx(m0['addr']),m0['insn'],hx(vt),hx(col),hx(td),tds[td].get('raw',''))
    elif a3:
        k='A3'; m0=a3[0]
        if m0['ref']=='COL': rec=cols[m0['val']]; col=m0['val']; td=rec['td']; cls=rec.get('cls', rec.get('class', '')); voc='COL=%s'%hx(col)
        else: col='-'; td=m0['val']; cls=tds[td]['cls']; voc='TD=%s'%hx(td)
        ev='A3 %s: %s; immediate %s=%s; TD+8 inline %s'%(hx(m0['addr']),m0['insn'],m0['ref'],hx(m0['val']),tds[td].get('raw','') if td in tds else '?')
    else:
        k='A4'; vt=col=td=cls='-'; voc='-'; ev='placeholder'
    sg=suggest(cls) if k!='A4' else '-'
    if k!='A4' and sg=='-' and cls in class_hint: sg=class_hint[cls][0]+'(hint)'
    results.append(dict(entry=es,kind=k,voc=voc,td=hx(td) if td!='-' else '-',cls=cls,ev=ev,sg=sg,a1=a1,a2=a2,a3=a3,a3d=a3d,a3r=a3r,sem=sem,size=asize[e],cname=row[2],grade=row[4]))
    kinds[k]+=1
    if k!='A4': cc[cls]+=1; ckind[cls][k]+=1
TOTAL_SLOTS=sum(len(s['slots']) for s in vts)
for rec in results:
    if rec['kind']=='A4':
        rec['ev']=('A4: A1 entry absent from %d fresh .rdata slot values; A2 no mov[reg],VT; A3 no immediate COL/TD; also checked reg-mediated VT stores=%d, disp COL/TD=%d, raw COL/TD dwords=%d'%(TOTAL_SLOTS,len(rec['sem']),len(rec['a3d']),len(rec['a3r'])))
# write CENSUS
OUT=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS'
EVD=os.path.join(OUT,'EVIDENCE'); os.makedirs(EVD,exist_ok=True)
with open(os.path.join(OUT,'CENSUS.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['entry','anchor_kind','vt_or_col','td','class_name','evidence','suggested_subsystem']))
    for x in results: f.write(tl([x['entry'],x['kind'],x['voc'],x['td'],x['cls'],x['ev'],x['sg']]))
# evidence files
with open(os.path.join(EVD,'rtti_tds.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['td','section','raw_rtti_name','class_name']))
    for va in sorted(tds): f.write(tl([hx(va),tds[va]['section'],tds[va]['raw'],tds[va].get('cls', tds[va].get('class',''))]))
with open(os.path.join(EVD,'rtti_cols.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['col','sig','offset','cd_offset','td','chd','raw_rtti_name','class_name']))
    for va in sorted(cols):
        c=cols[va]; f.write(tl([hx(va),c['sig'],c.get('offset', c.get('offv',0)),c['cdoff'],hx(c['td']),hx(c['chd']),c['raw'],c.get('cls', c.get('class', ''))]))
with open(os.path.join(EVD,'vtable_slots.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['vtable','col','td','class_name','slot','slot_va','func_va']))
    flat=[]
    for vtrec in vts:
        for idx,(sva,func) in enumerate(vtrec.get('slots',[])):
            flat.append((vtrec['vt'],vtrec['col'],vtrec['td'],vtrec.get('cls',vtrec.get('class','')),idx,sva,func))
    for row in sorted(flat,key=lambda x:(x[0],x[4])): f.write(tl([hx(row[0]),hx(row[1]),hx(row[2]),row[3],row[4],hx(row[5]),hx(row[6])]))
with open(os.path.join(EVD,'channel_hits.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['entry','selected_kind','all_a1','all_a2','all_a3_strict','a3_mem_disp','a3_raw_dword','reg_mediated_vt_store']))
    for x in results:
        f.write(tl([x['entry'],x['kind'],';'.join('VT=%s/COL=%s/TD=%s/slot=%d/%s'%(hx(m['vt']),hx(m['col']),hx(m['td']),m['slot'],m.get('cls', m.get('class',''))) for m in x['a1']),
          ';'.join('@%s:%s->VT=%s/COL=%s/TD=%s/%s'%(hx(m['addr']),m['insn'],hx(m['vt']),hx(m['col']),hx(m['td']),m.get('cls', m.get('class',''))) for m in x['a2']),
          ';'.join('@%s:%s/%s=%s/%s'%(hx(m['addr']),m['insn'],m['ref'],hx(m['val']),m['raw']) for m in x['a3']),
          ';'.join('@%s:%s=%s'%(hx(a),t,hx(v)) for a,t,v in x['a3d']),
          ';'.join('%s=%s'%(hx(a),hx(v)) for a,v in x['a3r']),
          ';'.join('@%s:%s->VT=%s'%(hx(a),t,hx(v)) for a,t,v in x['sem'])]))
with open(os.path.join(EVD,'class_agg_full.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['class_name','rows','A1','A2','A3','suggested_subsystem']))
    for cls,n in cc.most_common():
        k=ckind[cls]; f.write(tl([cls,n,k['A1'],k['A2'],k['A3'],suggest(cls)]))
unanch=[x for x in results if x['kind']=='A4']; step=max(1,len(unanch)//40); samples=unanch[::step][:40]
with open(os.path.join(EVD,'A4_samples.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['entry','coverage_name','why_A1_missed','why_A2_missed','why_A3_missed','equivalent_forms_checked']))
    for x in samples:
        f.write(tl([x['entry'],x['cname'],'not among %d slot values in fresh .rdata scan'%TOTAL_SLOTS,
          'no mov [base/index],imm where imm is one of %d vtable starts; size=%d bytes disassembled with skipdata=True'%(len(vt_by_addr),x['size']),
          'no immediate operand equal to any of %d COL or %d TD addresses'%(len(cols),len(tds)),
          'reg-mediated VT stores=%d; memory-disp COL/TD=%d; raw COL/TD dwords=%d'%(len(x['sem']),len(x['a3d']),len(x['a3r']))]))
with open(os.path.join(EVD,'coverage_class_hints.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write(tl(['class_name','dominant_non_S22_subsystem','rows','total_named_rows']))
    for cls,(sub,n,tot) in sorted(class_hint.items()): f.write(tl([cls,sub,n,tot]))
with open(os.path.join(EVD,'scan_manifest.txt'),'w',encoding='utf-8',newline='') as f:
    f.write('S22-CENSUS scan manifest\n')
    f.write('exe=%s\n'%EXE.replace('\\','/')); f.write('exe_size=%d\n'%len(DATA)); f.write('exe_sha256=%s\n'%hashlib.sha256(DATA).hexdigest().upper())
    f.write('coverage=%s\n'%COV.replace('\\','/')); f.write('atlas=%s\n'%ATL.replace('\\','/'))
    f.write('image_base=0x%X\n'%IB)
    f.write('sections='+';'.join('%s:VA=%08X,VSIZE=%08X,RAWSIZE=%08X'%(s['nm'],s['va'],s['vsize'],s['rawsize']) for s in secs)+'\n')
    f.write('TD_count=%d COL_count=%d vtable_count=%d vtable_slots=%d\n'%(len(tds),len(cols),len(vpos),TOTAL_SLOTS))
    f.write('TD_rule=pVFTable@TD+0=0x7F9594, spare@TD+4=0, name INLINE at TD+8 (.?AV/.?AU ... @@)\n')
    f.write('COL_rule=sig@COL+0=0, CHD@COL+0x10 in image, TD@COL+0x0C (NOT COL+8)\n')
    f.write('vtable_rule=.rdata aligned dword==COL at vt-4; slots walked until non-.text or next .rdata COL boundary; no atlas boundary used\n')
    f.write('A1=entry is vtable slot; A2=mov[reg],immVT in atlas body; A3=immediate COL/TD ref; A4=all missed\n')
    f.write('capstone=5.0.7 skipdata=True detail=True; grade read-only col5\n')
# summary/progress generated by separate script
print('S22_TOTAL',len(results),'TD',len(tds),'COL',len(cols),'VTABLES',len(vpos),'SLOTS',TOTAL_SLOTS)
print('A1',kinds['A1'],'A2',kinds['A2'],'A3',kinds['A3'],'A4',kinds['A4'])
print('ANCHORED',kinds['A1']+kinds['A2']+kinds['A3'],'CLASSES',len(cc))
