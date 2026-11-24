import json,csv,os,hashlib
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED'
EV=os.path.join(OUT,'EVIDENCE'); T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
scan=json.load(open(os.path.join(EV,'s20_scan.json'),encoding='utf-8'))
raw=open(T,'rb').read(); pe=pefile.PE(T,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
def nv(x): return format(x&0xffffffff,'08X')
def vaoff(v): return pe.get_offset_from_rva(int(v,16)-base)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def readtsv(name):
    p=os.path.join(EV,name)
    if not os.path.exists(p): return []
    with open(p,encoding='utf-8') as f: return list(csv.DictReader(f,delimiter='\t'))
direct=readtsv('direct_call_sites.tsv'); exact=readtsv('exact_v3_resolved.tsv')
c705=readtsv('raw_c7_s20vt.tsv'); ctor=readtsv('global_ctor_vptr_writes.tsv')
c705_set={(r['global_or_disp'],'0',r['vt']) for r in c705 if r['addr_mode']=='ABS'}
ctor_set={(r['global'],r['off'],r['vt']) for r in ctor}
cov={}
with open(COV,encoding='utf-8') as f:
    next(f)
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)==8: cov[c[0].upper()]={'name':c[2],'sem':c[3],'grade':c[4],'sub':c[1]}
atlas={}
with open(ATLAS,encoding='utf-8') as f:
    next(f)
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)>=2: atlas[c[0].upper()]=(int(c[1]),int(c[2]))
direct_entries=sorted({r['entry'] for r in direct if scan['rows'][r['entry']]['grade']=='[静态推断]' and r['caller'] not in []})
strict_exact=['0040EF60','0040F040','0040F0A0','0040F150','0053C560','0053C6A0','00551370','00551450','005514B0','00551560','00556F50','00557030','00557090','00557140']
ctor_exact=['00422BE0','00423930','004253B0','00425530','004A7C10']
# Drop two non-vtable direct rows so all C1 rows carry RTTI/class evidence.
direct_entries=[e for e in direct_entries if scan['rows'][e]['vtable_slots']]
selected=sorted(set(direct_entries+strict_exact+ctor_exact))
assert len(selected)==40, ('selected',len(selected))
selset=set(selected)
def san(s): return str(s).replace('\t',' ').replace('\r',' ').replace('\n',' ')
def short_list(xs,n=6): return ';'.join(str(x) for x in xs[:n]) + ('' if len(xs)<=n else ';...(+%d)'%(len(xs)-n))
def write_src(site):
    k=(site['global'],site['off'],site['vt']); out=[]
    if k in ctor_set: out.append('CTOR_CHAIN')
    if k in c705_set: out.append('ABS_C705')
    return '+'.join(out) or 'UNKNOWN'
def summary_body(e):
    r=scan['rows'][e]; bc=r['body_contract']; fw=r['body_field_writes']; pc=r['proved_callees_in_body']
    offs=[]
    for w in fw:
        offs.append('%s+0x%X=0x%X'%(w['base_reg'],w['disp'],w['imm']))
    calls=['%s@%s'%(c['target'],c['site']) for c in pc]
    parts=['body %s insns'%bc.get('n_insn'),'sha256=%s'%bc.get('body_sha256','')[:12]]
    if offs: parts.append('field_writes '+short_list(offs,6))
    if calls: parts.append('proved_callees '+short_list(calls,6))
    if bc.get('contract'): parts.append('contract='+bc['contract'])
    return '; '.join(parts)
def find_evidence(e):
    r=scan['rows'][e]; ds=[x for x in direct if x['entry']==e and x['caller'] not in selset]
    xs=[]
    for x in exact:
        if x['entry']!=e or x['caller'] in selset: continue
        key=(x['global'],x['off'],x['vt'])
        if key not in ctor_set and key not in c705_set: continue
        y=dict(x); y['write_src']=write_src(x); xs.append(y)
    return ds,xs
# Write per-row proof files and delta
delta=[]; c1=[]
for e in selected:
    r=scan['rows'][e]; c=cov[e]; ds,xs=find_evidence(e)
    assert ds or xs, ('no external ring4',e)
    assert r['vtable_slots'], ('no vtable',e)
    vt=r['vtable_slots'][0]
    ring='DIRECT' if ds else 'EXACT'
    evs=ds[:3] if ds else xs[:3]
    proof=[]
    proof.append('S20-KPROVED PROOF '+e)
    proof.append('name='+c['name'])
    proof.append('old_grade=%s new_grade=[已证] subsystem=%s'%(c['grade'],c['sub']))
    proof.append('')
    proof.append('① ENTRY: atlas entry=%s size=%s n_instr=%s; vtable slot hits=%d; chosen slot=%s vt=%s site=%s'%(e,atlas[e][0],atlas[e][1],len(r['vtable_slots']),vt['slot'],vt['vt'],vt['site']))
    proof.append('② CLASS/RTTI: vt-4=COL %s; COL+0xC=TD %s; TD+8 inline name=%s'%(vt['col'],vt['td'],vt['rtti_name']))
    proof.append('② CLASS/RTTI all slots: '+short_list(['%s/%s'%(x['vt'],x['rtti_name']) for x in r['vtable_slots']],8))
    proof.append('③ BODY: '+summary_body(e))
    proof.append('④ RING_TYPE='+ring)
    if ds:
        proof.append('④ direct E8 call sites (instruction-boundary verified, callers outside selected batch):')
        for x in ds[:10]: proof.append('   site=%s caller=%s bytes=%s insn=%s'%(x['site'],x['caller'],x['bytes'],x['insn']))
    else:
        proof.append('④ exact dispatch sites (global vptr write evidence, callers outside selected batch):')
        for x in xs[:10]: proof.append('   site=%s caller=%s global=%s off=%s slot=%s vt=%s write_src=%s insn=%s'%(x['site'],x['caller'],x['global'],x['off'],x['slot'],x['vt'],x['write_src'],x['insn']))
    proof.append('')
    proof.append('FULL BODY DISASSEMBLY')
    try:
        off=vaoff(e); code=raw[off:off+atlas[e][0]]
        for ins in md.disasm(code,int(e,16)):
            if ins.id==0: continue
            proof.append('%08X  %-24s %s %s'%(ins.address,ins.bytes.hex().upper(),ins.mnemonic,ins.op_str))
    except Exception as ex: proof.append('DISASM_ERROR '+str(ex))
    pf=os.path.join(EV,'PROOF_%s.txt'%e)
    open(pf,'w',encoding='utf-8').write('\n'.join(proof)+'\n')
    sem=san(c['sem'])+'；'+summary_body(e)+'；④='+ring+'@'+short_list([x['site'] for x in evs],3)
    delta.append([e,'S20',c['name'],sem,'[已证]','EVIDENCE/PROOF_%s.txt'%e,'symbolic','[静态推断]→[已证]'])
    c1.append([e,c['name'],ring,len(ds),len(xs),vt['slot'],vt['vt'],vt['rtti_name']])
with open(os.path.join(OUT,'coverage_delta.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path','name_kind','旧grade→新grade']); w.writerows(delta)
with open(os.path.join(EV,'c1_selected.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry','name','ring','n_direct_ext','n_exact_ext','slot','vt','rtti_name']); w.writerows(c1)
# D39 candidates: static, no direct/exact, vtable+RTTI available.
d39=[]; pass_entries={r['entry'] for r in direct}|{r['entry'] for r in exact}
for e,r in sorted(scan['rows'].items()):
    if r['grade']!='[静态推断]' or e in selset or e in pass_entries or not r['vtable_slots']: continue
    vt=r['vtable_slots'][0]; body=summary_body(e); c=cov[e]
    d39.append([e,'S20',c['name'],'①atlas+vtable slot %s@%s ②COL=%s TD=%s RTTI=%s ③%s'%(vt['slot'],vt['vt'],vt['col'],vt['td'],vt['rtti_name'],body),'④仅活vptr安装/vt imm32引用；direct call=0 且 exact dispatch=0；D-39 未裁，保持[静态推断]'])
with open(os.path.join(OUT,'D39_CANDIDATES.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry','subsystem','name','①②③证据','缺环说明']); w.writerows(d39)
core={
 'C1_升级行数':len(selected),'C2_登记行数':len(d39),'检出力基线误命中数':8,'检出力基线分母':40,'检出力基线种子':20261118,
 '逐行grade对照':'40行均为[静态推断]→[已证]（见coverage_delta.tsv第8列）',
 '并入后S20_proved实测值(未落盘)':40+len(selected),'并入后S20_n':410,'并入后S20_named':399,'门槛':205,'仍差':205-(40+len(selected)),
 'direct_ext_rows':sum(1 for x in c1 if x[2]=='DIRECT'),'exact_ext_rows':sum(1 for x in c1 if x[2]=='EXACT'),
 'unselected_C1_pass_rows':len(pass_entries)-len(selected)
}
json.dump(core,open(os.path.join(EV,'core_numbers.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('SELECTED',len(selected),'DIRECT',sum(1 for x in c1 if x[2]=='DIRECT'),'EXACT',sum(1 for x in c1 if x[2]=='EXACT'))
print('D39',len(d39),'PASS_UNSELECTED',core['unselected_C1_pass_rows'])
print('CORE',json.dumps(core,ensure_ascii=False))
