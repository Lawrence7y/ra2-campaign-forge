
import os, importlib.util, json, pickle, collections, csv, random
WORK=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.dirname(WORK)
spec=importlib.util.spec_from_file_location('az',os.path.join(WORK,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows(); atlas_set=set(az.atlas)
proved=[r for r in rows if r['grade']=='[已证]']
HAND={0x5656D0:'A'}   # hand-verified: global 0x87F7E8 live vptr 0x7E1964 installed by ctor 0x5BDA40
res={}
for r in proved:
    c,d=az.classify_v2(r['entry'])
    if r['entry'] in HAND: c=HAND[r['entry']]
    res[r['entry']]=(c,d,r)
cnt=collections.Counter(v[0] for v in res.values())
print('TIER1 (global-anchored, hand-corrected):',dict(cnt),'sum',sum(cnt.values()))

# tier2 sensitivity: register-ctor installs also count as live
def classify_t2(E):
    c,d=az.classify_v2(E)
    if c!='D': return c,d
    # look for register installs whose fn is not a dtor-identified function
    for P in az.pos_index.get(E,[]):
        T=az.run_start_of_pos[P]
        for cc in az.run_cands.get(az.run_of_pos[P],[]):
            if cc<=P: T=cc
        ins=az.by_vt_all2.get(T,[])
        if any(not x['dtor'] for x in ins): return 'A',d
    return c,d
t2=collections.Counter(classify_t2(r['entry'])[0] for r in proved)
print('TIER2 sensitivity (register installs by unknown-role fns count live):',dict(t2))

sub_n=collections.Counter(); sub_p=collections.Counter()
for r in rows:
    if r['entry'] in atlas_set:
        sub_n[r['sub']]+=1
        if r['grade']=='[已证]': sub_p[r['sub']]+=1
sub_cls=collections.defaultdict(collections.Counter)
for e,(c,d,r) in res.items(): sub_cls[r['sub']][c]+=1
lines=[]
print('\n%-4s %5s %6s %6s | %4s %4s %4s %4s | %s'%('sub','n','proved','thresh','A','B','C','D','B-demoted proved / met?'))
for k in sorted(sub_n):
    n=sub_n[k]; p=sub_p[k]; c=sub_cls[k]; thr=(n+1)//2
    p2=p-c['B']
    met_b=p>=thr; met_a=p2>=thr
    print('%-4s %5d %6d %6d | %4d %4d %4d %4d | %d/%d %s (was %s)'%(k,n,p,thr,c['A'],c['B'],c['C'],c['D'],
          p2,n,'met' if met_a else 'NOT-MET','met' if met_b else 'NOT-MET'))
    lines.append(dict(sub=k,n=n,proved=p,thresh=thr,A=c['A'],B=c['B'],C=c['C'],D=c['D'],
                      proved_after=p2,met_before=met_b,met_after=met_a))
json.dump(dict(tier1=dict(cnt),tier2=dict(t2),sub=lines),open(os.path.join(OUT,'counts.json'),'w'),indent=1)

# baseline: 50 random proved rows, single seed
random.seed(20261118)
samp=random.sample(proved,50)
b=collections.Counter(res[r['entry']][0] for r in samp)
print('\nBASELINE 50 random proved rows (seed 20261118):',dict(b))
# row-level tsv
with open(os.path.join(OUT,'EVIDENCE','row_class.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','grade','class','reason_or_table','live_install','dtor_install'])
    for r in proved:
        c,d,r2=res[r['entry']]
        tabs=d.get('tables',[])
        tbl=';'.join('%08X/%s/slot%d'%(t['table'],(t['col'] or '?'),t['slot']) for t in tabs[:3])
        live=';'.join('%08X<%08X'%(x['global_addr'] or 0,x['site']) for t in tabs for x in t['live'])
        dead=';'.join('%08X<%08X'%(x['global_addr'] or 0,x['site']) for t in tabs for x in t['dtor'])
        w.writerow(['%08X'%r['entry'],r['sub'],r['name'],r['grade'],c,
                    d.get('reason','') or d.get('c_kind','') or tbl,live,dead])
print('wrote EVIDENCE/row_class.tsv')
# D sub-split
D=[(e,v) for e,v in res.items() if v[0]=='D']
d1=[x for x in D if x[1][1].get('reason')]; d2=[x for x in D if not x[1][1].get('reason')]
risk=[x for x in d2 if all(all(y['dtor'] for y in t['dtor']) for t in x[1][1]['tables'] if t['dtor'])
      and any(t['dtor'] for t in x[1][1]['tables'])]
print('D:',len(D),' D-1 no ref:',len(d1),' D-2 table w/o global install:',len(d2))
pickle.dump(dict(res=res,cnt=dict(cnt),t2=dict(t2),sub=lines,baseline=dict(b),
                 d1=d1,d2=d2,D=D),open(os.path.join(OUT,'final2.pkl'),'wb'))
