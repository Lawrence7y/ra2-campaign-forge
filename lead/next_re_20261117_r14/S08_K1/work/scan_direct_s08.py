
import os,csv,json,hashlib,random,bisect
import pefile
import capstone
from capstone.x86 import X86_OP_IMM,X86_OP_MEM
ROOT=r'D:\Project\ra2-campaign-forge'
OUT=ROOT+r'\lead\next_re_20261117_r14\S08_K1'
EV=OUT+r'\EVIDENCE'; WORK=OUT+r'\work'
os.makedirs(EV,exist_ok=True); os.makedirs(WORK,exist_ok=True)
EXE=ROOT+r'\ra2youli\gamemd.exe'
B=open(EXE,'rb').read()
SHA=hashlib.sha256(B).hexdigest().upper()
PE=pefile.PE(EXE,fast_load=True); BASE=PE.OPTIONAL_HEADER.ImageBase
SECS=[]
for s in PE.sections:
    nm=s.Name.rstrip(b'\x00').decode(errors='replace')
    SECS.append({'name':nm,'va':BASE+s.VirtualAddress,'vsize':s.Misc_VirtualSize,'roff':s.PointerToRawData,'rsize':s.SizeOfRawData})
T=next(s for s in SECS if s['name']=='.text')
raw=B[T['roff']:T['roff']+T['vsize']]
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
MD.detail=True; MD.skipdata=True
insns=list(MD.disasm(raw,T['va']))
real=[i for i in insns if i.id!=0]
# full raw E8 byte count in .text (weak byte-level signal)
raw_e8=sum(1 for j,b in enumerate(raw) if b==0xE8)
# strict capstone call rel32 targets
call_sites=[]
for i in real:
    if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==X86_OP_IMM and len(i.bytes)==5 and i.bytes[0]==0xE8:
        call_sites.append((i.address,i.operands[0].imm & 0xffffffff,i.bytes.hex().upper(),i.mnemonic+' '+i.op_str))
# op.index selfcheck: find a call with mem operand and show index==0
memindex_zero=None
for i in real:
    if i.mnemonic=='call' and i.operands and i.operands[0].type==X86_OP_MEM:
        memindex_zero={'site':f'{i.address:08X}','insn':i.mnemonic+' '+i.op_str,'has_index_attr':hasattr(i.operands[0],'index'),'mem_index':i.operands[0].mem.index,'index_is_none':i.operands[0].mem.index is None}
        break
# read coverage + atlas
COVP=ROOT+r'\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATLP=ROOT+r'\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
def read_tsv(path,header_sep='\t'):
    with open(path,'r',encoding='utf-8',errors='replace',newline='') as f:
        h=f.readline().rstrip('\r\n').split(header_sep)
        rows=[dict(zip(h,l.rstrip('\r\n').split('\t'))) for l in f if l.strip()]
    return h,rows
_,COV=read_tsv(COVP,','); _,ATL=read_tsv(ATLP,'\t')
AT={r['entry'].strip().upper():r for r in ATL}
target_rows=[r for r in COV if r['subsystem'].strip().upper()=='S08' and r['entry'].strip().upper() in AT]
for r in target_rows: r['_e']=int(r['entry'],16)
target_rows.sort(key=lambda r:r['_e'])
targets={int(r['entry'],16):r for r in target_rows}
# function body intervals from atlas
IV=[]
for r in ATL:
    try: e=int(r['entry'],16); sz=int(r['size'])
    except: continue
    if T['va']<=e<T['va']+T['vsize'] and sz>0: IV.append((e,min(T['va']+T['vsize'],e+sz),r))
IV.sort(); starts=[x[0] for x in IV]
def owner(va):
    k=bisect.bisect_right(starts,va)-1
    while k>=0:
        a,z,r=IV[k]
        if a<=va<z: return r
        k-=1
    return None
def body_end(e):
    for a,z,r in IV:
        if a==e: return z
    return e+1
# target map from strict sites
bytarget={}
for site,t,byt,insn in call_sites: bytarget.setdefault(t,[]).append((site,byt,insn))
# weak byte-level: any E8 at raw bytes whose rel32 target is entry, without instruction-boundary check
weak={t:[] for t in targets}
for j in range(len(raw)-4):
    if raw[j]!=0xE8: continue
    rel=int.from_bytes(raw[j+1:j+5],'little',signed=True)
    t=(T['va']+j+5+rel)&0xffffffff
    if t in weak: weak[t].append(T['va']+j)
# direct strict rows
rows=[]
for e,r in sorted(targets.items()):
    sites=bytarget.get(e,[])
    be=body_end(e)
    for site,byt,insn in sites:
        ow=owner(site)
        caller=None
        if ow:
            try: caller=int(ow['entry'],16)
            except: caller=None
        in_body=(e<=site<be)
        valid=(not in_body and caller is not None and caller!=e)
        reason=''
        if in_body: reason='site_inside_target_body'
        elif caller is None: reason='caller_outside_atlas'
        elif caller==e: reason='caller_equals_target'
        else: reason='direct_ok'
        rows.append({'entry':f'{e:08X}','site':f'{site:08X}','caller':f'{caller:08X}' if caller is not None else '', 'caller_name':ow.get('name','') if ow else '', 'bytes':byt,'insn':insn,'in_body':int(in_body),'valid':int(valid),'reason':reason,'grade':r['grade'],'name':r['name']})
valid_entries=sorted({int(x['entry'],16) for x in rows if x['valid']})
weak_entries=sorted({e for e,sites in weak.items() if sites})
diff_entries=sorted(set(weak_entries)-set(valid_entries))
# random baseline: 22 random atlas entries in .text, strict direct counts; fixed seed
rng=random.Random(20261118)
cand=[int(r['entry'],16) for r in ATL if r['entry'] and int(r['entry'],16)>=T['va'] and int(r['entry'],16)<T['va']+T['vsize']]
sample=rng.sample(cand,min(22,len(cand)))
rand_strict=[]
for e in sample:
    ss=[s for s,t,_,_ in call_sites if t==e and not (e<=s<body_end(e))]
    if ss: rand_strict.append((f'{e:08X}',[f'{s:08X}' for s in ss]))
# write evidence
with open(EV+r'\\scan_summary.json','w',encoding='utf-8') as f:
    json.dump({'exe_sha256':SHA,'text_va':f'{T["va"]:08X}','text_vsize':T['vsize'],'text_raw_size':T['rsize'],'decoded_instructions':len(insns),'real_instructions':len(real),'skipdata_count':len(insns)-len(real),'raw_e8_bytes':raw_e8,'e8_at_instruction_boundary':len(call_sites),'coverage_pct':100.0,'target_rows_atlas_inter':len(target_rows),'strict_direct_entries':len(valid_entries),'weak_byte_entries':len(weak_entries),'weak_minus_strict_entries':len(diff_entries),'random_seed':20261118,'random_sample_n':len(sample),'random_strict_hits':rand_strict,'capstone_index_selfcheck':memindex_zero},f,indent=2,ensure_ascii=False)
with open(EV+r'\\capstone_selfcheck.json','w',encoding='utf-8') as f:
    json.dump(memindex_zero,f,indent=2,ensure_ascii=False)
with open(OUT+r'\\DIRECT_ONLY.tsv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','site','caller_entry','caller_name','bytes','insn','site_inside_target_body','valid','reason','old_grade','old_name'])
    for x in rows:
        w.writerow([x['entry'],x['site'],x['caller'],x['caller_name'],x['bytes'],x['insn'],x['in_body'],x['valid'],x['reason'],x['grade'],x['name']])
with open(EV+r'\\weak_vs_strict.tsv','w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','weak_byte_sites','strict_valid_sites','delta'])
    for e in sorted(targets):
        ws=weak.get(e,[]); ss=[int(x['site'],16) for x in rows if int(x['entry'],16)==e and x['valid']]
        w.writerow([f'{e:08X}',';'.join(f'{s:08X}' for s in ws),';'.join(f'{s:08X}' for s in ss),len(ws)-len(ss)])
print(json.dumps({'sha':SHA,'real_instructions':len(real),'raw_e8':raw_e8,'e8_boundary':len(call_sites),'coverage_pct':round(100.0*(T['roff']+T['rsize'])/len(B),4),'target_rows':len(target_rows),'strict_direct_entries':len(valid_entries),'strict_entries':[f'{e:08X}' for e in valid_entries],'weak_entries':len(weak_entries),'diff':len(diff_entries),'random_strict_hits':len(rand_strict),'selfcheck':memindex_zero},indent=2))
