
import json,collections,csv,math
from pathlib import Path
import pefile
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
raw=open(ROOT/'ra2youli'/'gamemd.exe','rb').read()
pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[dict(name=s.Name.rstrip(b'\0').decode('latin1'),va=ib+s.VirtualAddress,vs=s.Misc_VirtualSize,rs=s.SizeOfRawData,ptr=s.PointerToRawData) for s in pe.sections]
def va2off(va):
    for s in secs:
        if s['va']<=va<s['va']+s['rs']:
            o=s['ptr']+va-s['va']
            if o+4<=len(raw): return o
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],'little') if o is not None else None
idx=json.load(open(OUT/'work'/'index.json'))
installs={int(k,16):v for k,v in idx['installs'].items()}
livevt={int(k,16):v for k,v in idx['livevt'].items()}
rows=json.load(open(OUT/'work'/'rows2.json'))
step0=json.load(open(OUT/'work'/'step0.json')); M=step0['metrics']
SUBS=[f'S{i:02d}' for i in range(1,22)]

# livevt validity: slot unanimous across all vtables ever installed at g
unamb=set()
for e,wl in livevt.items():
    for g,vt,slot,inst,disp in wl:
        vts={v for v,s in installs.get(g,[])}
        vals={u32(v2+4*slot) for v2 in vts}; vals.discard(None)
        if len(vals)==1 and e in vals: unamb.add(e)

def h4(r, strict):
    if r['n_direct_out']>0: return True
    if r['n_livevt']==0: return False
    return (int(r['entry'],16) in unamb) if strict else True
def h2(r, yrpp):
    return r['has2_rtti'] or (yrpp and r['yrpp_conf'] and r['yrpp_conf']['ok'])
def cls(r, strict, yrpp):
    a=h2(r,yrpp); b=h4(r,strict)
    return 'A' if a and b else ('B' if a else ('C' if b else 'D'))

combos=[('RTTI_strict4',True,False),('RTTI_loose4',False,False),('YRpp_strict4',True,True),('YRpp_loose4',False,True)]
out={}
for name,strict,yrpp in combos:
    mat={}
    for s in SUBS:
        xs=[r for r in rows if r['sub']==s]
        c=collections.Counter(cls(r,strict,yrpp) for r in xs)
        mat[s]=dict(n=len(xs),A=c['A'],B=c['B'],C=c['C'],D=c['D'])
    out[name]=mat
    tot={k:sum(mat[s][k] for s in SUBS) for k in 'ABCD'}
    print(name, tot)

# PRIMARY = RTTI x strict4
prim=out['RTTI_strict4']; loose=out['RTTI_loose4']
mrows=[]
for s in SUBS:
    v=prim[s]; l=loose[s]; m=M[s]
    n=v['n']
    p2=(l['A']+l['B'])/n if n else 0
    p4=(v['A']+v['C'])/n if n else 0
    # independence calc on primary
    exp=n*((v['A']+v['B'])/n)*(p4) if n else 0
    up=m['proved']+v['A']; up_loose=m['proved']+l['A']
    mrows.append(dict(subsystem=s,n_static=n,
        A=v['A'],B=v['B'],C=v['C'],D=v['D'],
        A_loose4=l['A'],B_loose4=l['B'],C_loose4=l['C'],D_loose4=l['D'],
        A_yrpp=out['YRpp_strict4'][s]['A'],
        A_direct=sum(1 for r in rows if r['sub']==s and r['has2_rtti'] and h4(r,True) and r['n_direct_out']>0),
        A_livevt=sum(1 for r in rows if r['sub']==s and r['has2_rtti'] and h4(r,True) and r['n_direct_out']==0),
        proved_now=m['proved'],threshold=m['threshold'],
        proved_ceil=up,gap_now=m['gap'],gap_after=max(0,m['threshold']-up),
        reachable=('YES' if up>=m['threshold'] else 'no'),
        reachable_loose4=('YES' if up_loose>=m['threshold'] else 'no'),
        p2=round((v['A']+v['B'])/n*100,2) if n else 0,
        p4=round(p4*100,2) if n else 0,
        exp_ind=round(exp,1),obs_over_exp=(round(v['A']/exp,3) if exp>0 else '')))
with (OUT/'MATRIX.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(mrows[0].keys()),delimiter='\t')
    w.writeheader(); [w.writerow(r) for r in mrows]
    # TOTAL
    H=list(mrows[0].keys())
    tot={}
    for k in H:
        if k=='subsystem': tot[k]='TOTAL'
        elif k=='reachable': tot[k]=str(sum(1 for r in mrows if r['reachable']=='YES'))
        elif k=='reachable_loose4': tot[k]=str(sum(1 for r in mrows if r['reachable_loose4']=='YES'))
        elif k in ('obs_over_exp',): tot[k]=''
        else: tot[k]=round(sum(float(r[k]) for r in mrows),2)
    A,B,C,D,n=tot['A'],tot['B'],tot['C'],tot['D'],tot['n_static']
    tot['p2']=round((A+B)/n*100,2); tot['p4']=round((A+C)/n*100,2)
    tot['exp_ind']=round(n*(A+B)/n*(A+C)/n,1); tot['obs_over_exp']=round(A/tot['exp_ind'],3)
    w.writerow(tot)
print('PRIMARY TOTAL', {k:tot[k] for k in ('n_static','A','B','C','D','A_loose4','A_yrpp','A_direct','A_livevt','proved_now','threshold','proved_ceil','gap_now','gap_after','reachable','reachable_loose4','p2','p4','exp_ind','obs_over_exp')})
print()
print('A=0 subsys (primary):',[r['subsystem'] for r in mrows if r['A']==0])
print('A=0 subsys (loose):',[r['subsystem'] for r in mrows if r['A_loose4']==0])
print('newly reachable primary:',[r['subsystem'] for r in mrows if r['reachable']=='YES' and r['gap_now']>0])
print('newly reachable loose:',[r['subsystem'] for r in mrows if r['reachable_loose4']=='YES' and r['gap_now']>0])
print('reachable both already-pass:',[r['subsystem'] for r in mrows if r['reachable']=='YES'])
json.dump(dict(prim=prim,loose=loose,yrpp=out['YRpp_strict4'],unamb=len(unamb)), open(OUT/'work'/'matrix_all.json','w'),indent=1)
