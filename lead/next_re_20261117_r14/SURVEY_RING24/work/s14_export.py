
import json,collections,csv,math
from pathlib import Path
import pefile,capstone
ROOT=Path(r'D:\Project\ra2-campaign-forge')
OUT=ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'
rows=json.load(open(OUT/'work'/'rows2.json'))
step0=json.load(open(OUT/'work'/'step0.json')); M=step0['metrics']
SUBS=[f'S{i:02d}' for i in range(1,22)]

# ---------- (19) selfcheck
raw=open(ROOT/'ra2youli'/'gamemd.exe','rb').read()
pe=pefile.PE(data=raw,fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
s0=pe.sections[0]
code=raw[s0.PointerToRawData:s0.PointerToRawData+s0.Misc_VirtualSize]
cs2=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs2.detail=True
memops=0; noindex_attr=0; zeroindex=0; nonzero=0; n=0
for i in cs2.disasm(code[:2000000], ib+s0.VirtualAddress):
    n+=1
    for op in i.operands:
        if op.type==capstone.x86.X86_OP_MEM:
            memops+=1
            if not hasattr(op,'index'): noindex_attr+=1
            if op.mem.index==0: zeroindex+=1
            else: nonzero+=1
sc=dict(insns_scanned=n, memops=memops, no_op_index_attr=noindex_attr,
        mem_index_zero=zeroindex, mem_index_nonzero=nonzero,
        capstone=capstone.__version__, note='op.index does not exist; op.mem.index==0 means no SIB index (0 not None)')
# known positive selfcheck: instruction-boundary call, imm operand
known=None
cs3=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); cs3.detail=True
o=pe.get_offset_from_rva(0x4386AB-ib)
for i in cs3.disasm(raw[o-1:o+6], 0x4386AA):
    if i.address==0x4386AB: known=(i.mnemonic+' '+i.op_str)
sc['known_site_0x4386AB']=known
print('(19)',sc,flush=True)

# ---------- classification helper
def cls2(r, with_yrpp):
    h2 = r['has2_rtti'] or (with_yrpp and r['yrpp_conf'] and r['yrpp_conf']['ok'])
    h4 = r['has4']
    return 'A' if (h2 and h4) else ('B' if h2 else ('C' if h4 else 'D'))

# ---------- MATRIX.tsv
mat_rows=[]
for s in SUBS:
    xs=[r for r in rows if r['sub']==s]
    n=len(xs)
    c1=collections.Counter(cls2(r,False) for r in xs)
    c2=collections.Counter(cls2(r,True) for r in xs)
    A=sum(1 for r in xs if r['has2_rtti'] and r['has4'])
    ad=sum(1 for r in xs if r['has2_rtti'] and r['has4'] and r['n_direct_out']>0)
    al=sum(1 for r in xs if r['has2_rtti'] and r['has4'] and r['n_direct_out']==0)
    m=M[s]; up=m['proved']+c1['A']; up2=m['proved']+c2['A']
    p2=(c1['A']+c1['B'])/n if n else 0; p4=(c1['A']+c1['C'])/n if n else 0
    exp=n*p2*p4
    mat_rows.append(dict(subsystem=s,n_static=n,A=c1['A'],B=c1['B'],C=c1['C'],D=c1['D'],
        A_yrpp=c2['A'],C_yrpp=c2['C'],
        A_direct=ad,A_livevt=al,
        proved_now=m['proved'],threshold=m['threshold'],
        proved_ceil_rtti=up,proved_ceil_yrpp=up2,
        gap_now=m['gap'],gap_after=max(0,m['threshold']-up),
        reachable_rtti=('YES' if up>=m['threshold'] else 'no'),
        reachable_yrpp=('YES' if up2>=m['threshold'] else 'no'),
        p2=round(p2*100,2),p4=round(p4*100,2),exp_ind=round(exp,1),
        obs_over_exp=(round(c1['A']/exp,3) if exp>0 else '')))
with (OUT/'MATRIX.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(mat_rows[0].keys()),delimiter='\t')
    w.writeheader(); [w.writerow(r) for r in mat_rows]

# ---------- EVIDENCE/classification.tsv (per row)
with (OUT/'EVIDENCE'/'classification.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','class_rtti','class_yrpp','has2_rtti','has2_yrpp','has4',
                'n_direct_all','n_direct_out','n_livevt','rtti_classes','rtti_vt','rtti_slot',
                'ring4_direct_sites','ring4_livevt','yrpp_binding','ext_lo','ext_hi','atlas_size','name'])
    for r in rows:
        yc=r['yrpp_conf']
        w.writerow([r['entry'],r['sub'],cls2(r,False),cls2(r,True),
            int(r['has2_rtti']), int(bool(yc and yc['ok'])), int(r['has4']),
            r['n_direct_all'],r['n_direct_out'],r['n_livevt'],
            ';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],
            ';'.join('%08X'%x for x in r['direct_out']),
            ';'.join('g%08X/vt%08X/s%d/inst%08X/disp%08X'%tuple(x) for x in r['livevt']),
            ('%s:%d %s %s'%(r['yrpp'][0],r['yrpp'][1],r['yrpp'][2],r['yrpp'][3])) if r['yrpp'] else '',
            '%08X'%r['ext_lo'],'%08X'%r['ext_hi'],r['size'],r['name']])

# ---------- A samples with evidence
A=[r for r in rows if r['has2_rtti'] and r['has4']]
with (OUT/'EVIDENCE'/'A_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','channel','rtti_class','vt','slot','ring4_site','name'])
    for r in [x for x in A if x['n_direct_out']>0][:15]:
        w.writerow([r['entry'],r['sub'],'direct',';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],
                    '%08X'%r['direct_out'][0],r['name']])
    for r in [x for x in A if x['n_direct_out']==0][:15]:
        lv=r['livevt'][0]
        w.writerow([r['entry'],r['sub'],'livevt',';'.join(r['rtti_cls']),r['rtti_vt'],r['rtti_slot'],
                    'install@%08X/dispatch@%08X/g%08X'%(lv[3],lv[4],lv[0]),r['name']])
# ---------- C samples (ring4 without ring2)
C=[r for r in rows if (not r['has2_rtti']) and r['has4']]
with (OUT/'EVIDENCE'/'C_samples.tsv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','n_direct_out','n_livevt','yrpp','name'])
    for r in C[:20]: w.writerow([r['entry'],r['sub'],r['n_direct_out'],r['n_livevt'],'y' if r['yrpp'] else '',r['name']])

summary=dict(selfcheck_019=sc,
  totals=dict(n=len(rows),A=len(A),B=sum(1 for r in rows if r['has2_rtti'] and not r['has4']),
              C=len(C),D=sum(1 for r in rows if not r['has2_rtti'] and not r['has4'])),
  A_yrpp=sum(1 for r in rows if cls2(r,True)=='A'),
  A_by_channel=dict(direct=sum(1 for r in A if r['n_direct_out']>0 and r['n_livevt']==0),
                    livevt=sum(1 for r in A if r['n_direct_out']==0),
                    both=sum(1 for r in A if r['n_direct_out']>0 and r['n_livevt']>0)),
  extent_vs_atlas=dict(match=sum(1 for r in rows if r['ext_size']==r['size']),total=len(rows)),
  reachable=[r['subsystem'] for r in mat_rows if r['reachable_rtti']=='YES'],
  newly_reachable=[r['subsystem'] for r in mat_rows if r['reachable_rtti']=='YES' and r['gap_now']>0],
  A_zero_subsystems=[r['subsystem'] for r in mat_rows if r['A']==0])
json.dump(summary, open(OUT/'work'/'summary.json','w'), ensure_ascii=False, indent=1)
print(json.dumps(summary,ensure_ascii=False,indent=1))
