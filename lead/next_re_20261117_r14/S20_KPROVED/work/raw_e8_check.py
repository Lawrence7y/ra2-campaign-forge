import json,struct,bisect,os
import pefile
TARGET=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\EVIDENCE'
raw=open(TARGET,'rb').read(); pe=pefile.PE(TARGET,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
sec=next(s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')=='.text')
start=sec.PointerToRawData; end=start+sec.SizeOfRawData; text_va=base+sec.VirtualAddress
def nv(x): return format(x&0xffffffff,'08X')
scan=json.load(open(os.path.join(EV,'s20_scan.json'),encoding='utf-8'))
s20_static={e for e,r in scan['rows'].items() if r['grade']=='[静态推断]'}
direct_sites=set()
for e,r in scan['rows'].items():
    for s in r['direct_calls_into']:
        direct_sites.add((s['site'],e))
iv=[]
with open(ATLAS,encoding='utf-8') as f:
    next(f)
    for line in f:
        c=line.rstrip('\r\n').split('\t')
        if len(c)>=2:
            e=int(c[0],16); iv.append((e,e+int(c[1]),nv(e)))
iv.sort(); starts=[x[0] for x in iv]
def owner(va):
    i=bisect.bisect_right(starts,va)-1
    if i>=0 and iv[i][0]<=va<iv[i][1]: return iv[i][2]
    return ''
rows=[]
for off in range(start,end-4):
    if raw[off]!=0xE8: continue
    site=nv(text_va+(off-start)); rel=struct.unpack_from('<i',raw,off+1)[0]; tgt=nv(text_va+(off-start)+5+rel)
    if tgt in s20_static:
        own=owner(int(site,16)); boundary=(site,tgt) in direct_sites
        rows.append((tgt,site,own,'Y' if boundary else 'N',raw[off:off+5].hex().upper()))
with open(os.path.join(EV,'raw_e8_targets.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('entry\tsite\tatlas_owner\tboundary_verified\tbytes\n')
    for r in rows: f.write('\t'.join(r)+'\n')
print('RAW_E8_TO_S20_STATIC_SITES',len(rows),'ENTRIES',len(set(r[0] for r in rows)))
print('BOUNDARY_VERIFIED_SITES',sum(1 for r in rows if r[3]=='Y'),'ENTRIES',len(set(r[0] for r in rows if r[3]=='Y')))
print('NEW_NONBOUNDARY_SITES',sum(1 for r in rows if r[3]=='N'),'ENTRIES',len(set(r[0] for r in rows if r[3]=='N')))
for e in sorted(set(r[0] for r in rows if r[3]=='N')):
    print('NONBOUNDARY',e,sum(1 for r in rows if r[0]==e and r[3]=='N'))
