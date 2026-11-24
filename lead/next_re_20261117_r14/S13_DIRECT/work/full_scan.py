import sys,io,pefile,hashlib,struct,json,time,bisect
from capstone import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')

EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE'

raw=open(EXE,'rb').read()
print('EXE SHA256',hashlib.sha256(raw).hexdigest().upper())
pe=pefile.PE(EXE)
sec=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
base=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
vsize=sec.Misc_VirtualSize
code=raw[sec.PointerToRawData:sec.PointerToRawData+vsize]
text_end=base+vsize
print('TEXT base',hex(base),'end',hex(text_end),'vsize',vsize)

# ---- FULL SCAN (100% of .text VirtualSize), skipdata=True ----
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
boundaries=set()
call_sites=[]   # (site, target, caller_fn_entry_or_0)
nins=0; ne8=0; nskip=0
t0=time.time()
for ins in md.disasm(code,base):
    nins+=1
    boundaries.add(ins.address)
    if ins.mnemonic.startswith('.'): nskip+=1
    b=ins.bytes
    if b and b[0]==0xE8 and len(b)>=5:
        ne8+=1
        rel=struct.unpack('<i',b[1:5])[0]
        target=ins.address+5+rel
        call_sites.append((ins.address,target))
print('SCAN nins',nins,'skipdata',nskip,'real',nins-nskip,'E8-at-boundary',ne8,'coverage_pct',100.0,'sec=%.1f'%(time.time()-t0))
print('boundaries',len(boundaries))
assert nins==1392592, nins
assert ne8==68253, ne8

# ---- ⑲ self-check ----
# find a mem operand without index
md2=Cs(CS_ARCH_X86,CS_MODE_32); md2.detail=True
sample=bytes.fromhex('ff5010')  # call dword ptr [eax+0x10]
ins=next(md2.disasm(sample,0x4386ab))
op=ins.operands[0]
print('XIX check: ins=',ins.mnemonic,ins.op_str,'hasattr(op,"index")=',hasattr(op,'index'),'op.mem.index=',op.mem.index,'op.mem.index is None=',op.mem.index is None)

# ---- build atlas intervals ----
# atlas: entry size n_instr ...
atls=[]  # (entry, size)
with open(ATL,'r',encoding='utf-8',errors='replace') as f:
    lines=f.read().split('\n')
for ln in lines[1:]:
    if not ln.strip(): continue
    p=ln.split('\t')
    try: e=int(p[0],16); sz=int(p[1])
    except: continue
    atls.append((e,sz))
atls.sort()
atl_starts=[e for e,s in atls]
def find_caller(site):
    i=bisect.bisect_right(atl_starts,site)-1
    if i>=0:
        e,sz=atls[i]
        if e<=site<e+sz: return e,sz
    return (0,0)

# caller resolution for all call sites
call_index={}  # target -> list of dicts
for site,target in call_sites:
    ce,csz=find_caller(site)
    d={'site':site,'caller_entry':ce,'caller_size':csz}
    call_index.setdefault(target,[]).append(d)
print('distinct call targets',len(call_index))

# ---- coverage rows ----
with open(COV,'r',encoding='utf-8',errors='replace') as f: covlines=f.read().split('\n')
covrows=[]
for ln in covlines[1:]:
    if not ln.strip(): continue
    p=ln.split('\t')
    if len(p)<8: continue
    covrows.append(p)
atlentry=set(e for e,s in atls)
# grade lookup by entry
grade_by_entry={}
sub_by_entry={}
for r in covrows:
    grade_by_entry[r[0].upper()]=r[4]
    sub_by_entry[r[0].upper()]=r[1]

# S13 static rows
s13static=[]
for r in covrows:
    if r[1].strip().upper()=='S13' and r[4].strip()=='[静态推断]' and int(r[0],16) in atlentry:
        s13static.append(r)
print('S13 static rows',len(s13static))

# ---- Evaluate direct call criterion for each S13 static row ----
results=[]
for r in s13static:
    entry=int(r[0],16)
    sites=call_index.get(entry,[])
    quals=[]; skipped_self=[]; nonboundary=[]
    for d in sites:
        site=d['site']; ce=d['caller_entry']; csz=d['caller_size']
        # criterion 3: caller != this row's body (caller interval must NOT contain entry)
        if ce and ce<=entry<ce+csz:
            skipped_self.append((site,ce,csz))
            continue
        # criterion 1 & 2 already guaranteed by scan (site is boundary, target==entry byte-exact)
        caller_grade=grade_by_entry.get('%08X'%ce,'') if ce else ''
        quals.append({'site':hex(site),'caller':('%08X'%ce if ce else 'NONE'),'caller_size':csz,'caller_grade':caller_grade})
    results.append({'entry':r[0],'name':r[2],'semantics':r[3],'grade':r[4],
                    'evidence':r[5],'n_sources':r[6],'conflict':r[7],
                    'n_sites':len(sites),'qual_sites':quals,'self_skipped':skipped_self})

n_qual=sum(1 for x in results if x['qual_sites'])
print('S13 static rows with >=1 qualifying direct call',n_qual)
for x in results:
    if x['qual_sites']:
        print('QUAL',x['entry'],x['name'],'sites',x['qual_sites'][:3],'selfskip',x['self_skipped'][:2])

# save full results
with open(OUT+'\\direct_analysis.json','w',encoding='utf-8') as f:
    json.dump({'scan':{'nins':nins,'ne8':ne8,'skipdata':nskip,'nins_real':nins-nskip,'vsize':vsize,'base':hex(base),'coverage_pct':100.0},
               'xix':{'hasattr_index':hasattr(op,'index'),'mem_index':op.mem.index,'mem_index_is_None':op.mem.index is None},
               'n_s13_static':len(s13static),'n_qual':n_qual,'results':results},f,ensure_ascii=False,indent=1)

# save all direct call sites (target -> site) for audit
with open(OUT+'\\all_direct_call_sites.tsv','w',encoding='utf-8') as f:
    f.write('site\ttarget\tcaller_entry\tcaller_size\n')
    for site,target in sorted(call_sites):
        ce,csz=find_caller(site)
        f.write('%08X\t%08X\t%08X\t%d\n'%(site,target,ce,csz))
print('EVIDENCE written')
