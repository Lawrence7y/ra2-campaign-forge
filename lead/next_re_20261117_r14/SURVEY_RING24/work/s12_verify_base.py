
import json,collections,random
from pathlib import Path
import pefile,capstone
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=open(ROOT/'ra2youli'/'gamemd.exe','rb').read()
pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=ib+s.VirtualAddress,vs=s.Misc_VirtualSize,rs=s.SizeOfRawData,ptr=s.PointerToRawData) for s in pe.sections]
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+8<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else None
def cstr(va,lim=120):
    o=va2off(va)
    if o is None: return ''
    b=raw[o:o+lim]; z=b.find(b'\0')
    if z>=0: b=b[:z]
    try: return b.decode('ascii')
    except: return ''
rows=json.load(open(OUT/'work'/'rows2.json'))
A=[r for r in rows if r['has2_rtti'] and r['has4']]
print('A total',len(A))
# hand verify 2 direct rows
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
for r in [x for x in A if x['n_direct_out']>0][:2]:
    e=r['e']; print('\n--- verify',r['entry'],r['sub'],r['name'][:40],'rtti',r['rtti_cls'],'slot',r['rtti_slot'],'vt',r['rtti_vt'])
    vt=int(r['rtti_vt'],16); slot=r['rtti_slot']
    print('   u32(vt+4*slot)=',hex(u32(vt+4*slot)),'expected',r['entry'])
    print('   COL=vt-4 ->',hex(u32(vt-4)),'TD=',hex(u32(u32(vt-4)+0xC)),'name=',cstr(u32(u32(vt-4)+0xC)+8))
    for s in r['direct_out'][:4]:
        o=va2off(s); b=raw[o:o+5]
        rel=int.from_bytes(b[1:5],'little',signed=True)
        print('   site',hex(s),b.hex(),'-> target',hex((s+5+rel)&0xffffffff),'match',(s+5+rel)&0xffffffff==e)
    # disasm around site
    s=r['direct_out'][0]; o=va2off(s-6)
    for i in md.disasm(raw[o:o+16], s-6):
        print('      ',hex(i.address),i.mnemonic,i.op_str)
        if i.address>=s: break
# baseline: within-subsystem random N rows
rng=random.Random(20261118)
print('\n=== random baseline: per subsystem draw 8 rows x 2000 trials ===')
for s in [f'S{i:02d}' for i in range(1,22)]:
    xs=[r for r in rows if r['sub']==s]
    if not xs: continue
    na=sum(1 for r in xs if r['has2_rtti'] and r['has4'])
    nC=sum(1 for r in xs if (not r['has2_rtti']) and r['has4'])
    nB=sum(1 for r in xs if r['has2_rtti'] and not r['has4'])
    pr=na/len(xs)
    trials=2000; tot=0
    for _ in range(trials):
        tot+=sum(1 for r in rng.sample(xs,min(8,len(xs))) if r['has2_rtti'] and r['has4'])
    print(f"  {s} n={len(xs):4d} A={na:3d} rate={pr*100:5.2f}%  E[A|8]={tot/trials:.2f}  B_rate={nB/len(xs)*100:5.2f}% C_rate={nC/len(xs)*100:5.2f}%")
