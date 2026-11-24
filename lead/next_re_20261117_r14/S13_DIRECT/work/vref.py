import sys,io,struct,pefile,json,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
raw=open(EXE,'rb').read()
pe=pefile.PE(EXE)
# sections
secs={}
for s in pe.sections:
    n=s.Name.rstrip(b'\x00').decode(errors='replace')
    secs[n]=(pe.OPTIONAL_HEADER.ImageBase+s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
print('sections',list(secs.keys()))
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\direct_analysis.json',encoding='utf-8'))
static=[x['entry'] for x in d['results']]
static_int={int(e,16):e for e in static}
# scan all sections' raw data for dword == static entry (aligned and unaligned)
refs=collections.defaultdict(lambda: collections.Counter())
for name,(va,vs,pr,rs) in secs.items():
    data=raw[pr:pr+rs]
    for i in range(0,len(data)-3):
        v=struct.unpack_from('<I',data,i)[0]
        if v in static_int:
            refs[static_int[v]][name]+=1
# categorize
n_vref=0; n_noref=0
for e in static:
    c=refs[e]
    rdata=c.get('.rdata',0); data=c.get('.data',0); text=c.get('.text',0)
    if rdata>0: n_vref+=1
    if sum(c.values())==0: n_noref+=1
print('static rows with >=1 dword ref in .rdata (vtable-compatible):',n_vref)
print('static rows with ZERO dword ref anywhere:',n_noref)
# show breakdown for a sample
for e in static[:15]:
    print(e,dict(refs[e]))
# save
out=[]
for x in d['results']:
    e=x['entry']; c=refs[e]
    out.append({**x,'dword_refs':dict(c),'virtual_reachable':(c.get('.rdata',0)>0 or c.get('.data',0)>0)})
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\vref_analysis.json','w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
print('saved vref_analysis.json')
