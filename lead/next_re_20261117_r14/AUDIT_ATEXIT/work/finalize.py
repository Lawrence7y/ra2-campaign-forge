
import os, importlib.util, json, pickle, collections, csv
OUT=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('az',os.path.join(OUT,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows()
atlas_set=set(az.atlas)
proved=[r for r in rows if r['grade']=='[已证]']
res={}
for r in proved:
    c,d=az.classify_v2(r['entry'])
    res[r['entry']]=(c,d,r)
cnt=collections.Counter(v[0] for v in res.values())
print('PRIMARY (global-anchored) COUNTS',dict(cnt),'total',len(res))

# per-subsystem, atlas∩coverage denominators
sub_n=collections.Counter(); sub_p=collections.Counter()
for r in rows:
    if r['entry'] in atlas_set:
        sub_n[r['sub']]+=1
        if r['grade']=='[已证]': sub_p[r['sub']]+=1
sub_cls=collections.defaultdict(collections.Counter)
for e,(c,d,r) in res.items(): sub_cls[r['sub']][c]+=1

print('\n%-5s %5s %6s %6s %5s %5s %5s %5s   %s'%('sub','n','proved','thresh','A','B','C','D','B->demote proved / ok?'))
lines=[]
for k in sorted(sub_n):
    n=sub_n[k]; p=sub_p[k]; c=sub_cls[k]
    thr=-( -n // 2)   # ceil(0.5n)
    p2=p-c['B']
    ok='OK' if p2>=thr else 'NO'
    print('%-5s %5d %6d %6d %5d %5d %5d %5d   %d/%d %s %s'%(k,n,p,thr,c['A'],c['B'],c['C'],c['D'],p2,n,'met' if ok=='OK' else 'NOT-MET',('(was %d/%d %s)'%(p,n,'met' if p>=thr else 'NOT-MET'))))
    lines.append(dict(sub=k,n=n,proved=p,thresh=thr,A=c['A'],B=c['B'],C=c['C'],D=c['D'],
                      proved_after=p-c['B'],met_after=(p-c['B'])>=thr,
                      met_before=p>=thr))
json.dump(lines,open(os.path.join(OUT,'subsystem_table.json'),'w'),indent=1)

# ---- B list ----
Brows=[(e,)+v for e,v in res.items() if v[0]=='B']
print('\n=== B rows:',len(Brows),'===')
for e,c,d,r in Brows:
    for t in d['tables']:
        if t['dtor']:
            print('B %08X %s %s tbl=%08X(%s) slot=%d  global_install=%s'%(
                e,r['sub'],r['name'],t['table'],t['col'],t['slot'],
                [(('%08X'%x['global_addr']),('%08X'%x['site']),('%08X'%x['fn'])) for x in t['dtor']]))

# ---- A samples ----
Arows=[(e,)+v for e,v in res.items() if v[0]=='A']
print('\n=== A count:',len(Arows),'===')
for e,c,d,r in Arows:
    t=[x for x in d['tables'] if x['live'] or x['static_init']][0]
    print('A %08X %s %-28s tbl=%08X(%s) slot=%d live=%s dtor=%s'%(
        e,r['sub'],r['name'][:28],t['table'],t['col'],t['slot'],
        [(('%08X'%x['global_addr']),('%08X'%x['site']),('%08X'%x['fn'])) for x in t['live']],
        [(('%08X'%x['global_addr']),('%08X'%x['site'])) for x in t['dtor']]))

# ---- D sub-split ----
Drows=[(e,)+v for e,v in res.items() if v[0]=='D']
d1=[x for x in Drows if x[2].get('reason')]
d2=[x for x in Drows if not x[2].get('reason')]
print('\n=== D:',len(Drows),' D-1 no ref:',len(d1),' D-2 table-no-global:',len(d2))
basecls=[x for x in d2 if (x[2]['tables'][0]['col'] or '').find('?$VectorClass@')>=0]
print('    D-2 whose table is a VectorClass<> base table:',len(basecls))
pickle.dump(dict(res=res,B=Brows,A=Arows,D1=d1,D2=d2,basecls=basecls,
                 sub=lines,cnt=dict(cnt)),open(os.path.join(OUT,'final.pkl'),'wb'))
