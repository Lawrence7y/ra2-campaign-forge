
import os, importlib.util, json, pickle, collections, csv, random, hashlib
WORK=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.dirname(WORK); EVI=os.path.join(OUT,'EVIDENCE')
os.makedirs(EVI,exist_ok=True)
spec=importlib.util.spec_from_file_location('az',os.path.join(WORK,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows(); atlas_set=set(az.atlas)
proved=[r for r in rows if r['grade']=='[已证]']
HAND={0x5656D0:('A','hand-verified: global 0x87F7E8 live vptr 0x7E1964 written by ctor 0x5BDA40 (reg store @0x5BDA4A); atexit fn 0x40D1B0 is the DESTROY routine')}
res={}
for r in proved:
    c,d=az.classify_v2(r['entry'])
    note=''
    if r['entry'] in HAND: c,note=HAND[r['entry']]
    res[r['entry']]=(c,d,r,note)
cnt=collections.Counter(v[0] for v in res.values())
print('SNAPSHOT proved',len(proved),'TIER1',dict(cnt))
t2=collections.Counter()
for r in proved:
    c,d,_x,_n=res[r['entry']]
    if c=='D':
        for P in az.pos_index.get(r['entry'],[]):
            T=az.run_start_of_pos[P]
            for cc in az.run_cands.get(az.run_of_pos[P],[]):
                if cc<=P: T=cc
            if any(not x['dtor'] for x in az.by_vt_all2.get(T,[])): c='A'; break
    t2[c]+=1
print('TIER2 sensitivity',dict(t2))
sub_n=collections.Counter(); sub_p=collections.Counter()
for r in rows:
    if r['entry'] in atlas_set:
        sub_n[r['sub']]+=1
        if r['grade']=='[已证]': sub_p[r['sub']]+=1
sc=collections.defaultdict(collections.Counter)
for e,(c,d,r,n) in res.items(): sc[r['sub']][c]+=1
lines=[]
for k in sorted(sub_n):
    n_,p,c,thr=sub_n[k],sub_p[k],sc[k],(sub_n[k]+1)//2
    metb=p>=thr; meta=(p-c['B'])>=thr
    lines.append(dict(sub=k,n=n_,proved=p,thresh=thr,A=c['A'],B=c['B'],C=c['C'],D=c['D'],
                      proved_after=p-c['B'],met_before=metb,met_after=meta))
json.dump(dict(proved=len(proved),tier1=dict(cnt),tier2=dict(t2),sub=lines),
          open(os.path.join(OUT,'counts.json'),'w'),indent=1)
# ---- row_class.tsv ----
with open(os.path.join(EVI,'row_class.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','grade','class','basis','tables_and_slots','live_install_global<site','dtor_install_global<site'])
    for r in proved:
        c,d,_r,note=res[r['entry']]
        tabs=d.get('tables',[])
        tdesc=';'.join('%08X/%s/slot%d'%(t['table'],(t['col'] or '?'),t['slot']) for t in tabs[:3])
        live=';'.join('%08X<%08X'%(x['global_addr'] or 0,x['site']) for t in tabs for x in t['live'])
        dead=';'.join('%08X<%08X'%(x['global_addr'] or 0,x['site']) for t in tabs for x in t['dtor'])
        basis=note or d.get('reason') or d.get('c_kind') or tdesc
        w.writerow(['%08X'%r['entry'],r['sub'],r['name'],r['grade'],c,basis,tdesc,live,dead])
# ---- B list (incl. the hand-verified false positive) ----
with open(os.path.join(EVI,'B_class_list.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','grade','tableslot','global','live_vt','dtor_vt','detector','hand_verdict'])
    for r in proved:
        c,d,_r,note=res[r['entry']]
        if c!='B' and not note: continue
        if 0x5656D0!=r['entry'] and c!='B': continue
        tabs=d.get('tables',[])
        for t in tabs:
            w.writerow(['%08X'%r['entry'],r['sub'],r['name'],r['grade'],
                        '%08X/%s/slot%d'%(t['table'],(t['col'] or '?'),t['slot']),
                        ';'.join('%08X'%x['global_addr'] for x in t['dtor']),
                        ';'.join('%08X'%x['global_addr'] for x in t['live']) or '(none)',
                        ';'.join('%08X'%x['table'] for x in [] ) or '%08X'%t['table'],
                        'global-anchored','A (false positive of the B detector)' if note else 'B'])
# ---- A samples (>=5) ----
As=[(e,v) for e,v in res.items() if v[0]=='A']
random.seed(7); pick=random.sample(As,min(12,len(As)))
with open(os.path.join(EVI,'A_samples.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','live_vt(table)','slot','slot_value','global','ctor_write_site','ctor_fn','dtor_vt','dtor_write_site'])
    for e,(c,d,r,note) in pick:
        t=[x for x in d['tables'] if x['live'] or x['static_init']][0]
        lv=t['live'][0] if t['live'] else None
        w.writerow(['%08X'%e,r['sub'],r['name'],'%08X'%t['table'],t['slot'],
                    '%08X'%(az.dword(t['table']+4*t['slot']) or 0),
                    ('%08X'%lv['global_addr']) if (lv and lv['global_addr']) else '(reg/this)',
                    ('%08X'%lv['site']) if lv else '(static .data init)',
                    ('%08X'%lv['fn']) if lv else '', ';'.join('%08X'%x['table'] for x in t['dtor']) or '(none)',
                    ';'.join('%08X'%x['site'] for x in t['dtor'])])
# ---- baseline 50 ----
random.seed(20261118); samp=random.sample(proved,50)
bc=collections.Counter(res[r['entry']][0] for r in samp)
with open(os.path.join(EVI,'baseline50.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t'); w.writerow(['entry','subsystem','class'])
    for r in samp: w.writerow(['%08X'%r['entry'],r['sub'],res[r['entry']][0]])
print('BASELINE50 seed=20261118',dict(bc))
print('A',cnt['A'],'B',cnt['B'],'C',cnt['C'],'D',cnt['D'])
print('B-sub count (subsystems containing any B):', len({res[e][2]['sub'] for e,v in res.items() if v[0]=='B'}))
pickle.dump(dict(res={k:(v[0],v[3]) for k,v in res.items()},cnt=dict(cnt),t2=dict(t2),
                 sub=lines,baseline=dict(bc)),open(os.path.join(OUT,'final3.pkl'),'wb'))
