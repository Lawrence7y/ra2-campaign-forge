
import sys, os, importlib.util, json, pickle, collections
OUT=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('az',os.path.join(OUT,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows()
proved=[r for r in rows if r['grade']=='[已证]']
print('proved rows',len(proved))
atlas_set=set(az.atlas)
out=[]
for r in proved:
    c,d=az.classify_v2(r['entry'])
    reason=''
    if c=='D':
        if d.get('reason'): reason=d['reason']
        else:
            tabs=d.get('tables',[])
            if tabs and all(not(t['live'] or t['dtor'] or t['static_init']) for t in tabs):
                reason='tables present but no global-anchored install'
            else: reason='mixed/undetermined'
    out.append(dict(entry=r['entry'],sub=r['sub'],name=r['name'],cls=c,
                    c_kind=d.get('c_kind',''),reason=reason,
                    n_tables=len(d.get('tables',[])),
                    in_atlas=r['entry'] in atlas_set))
cnt=collections.Counter(x['cls'] for x in out)
print('COUNTS',dict(cnt))
per=collections.defaultdict(collections.Counter)
for x in out: per[x['sub']][x['cls']]+=1
print('%-5s %5s %5s %5s %5s %6s'%('sub','A','B','C','D','total'))
for k in sorted(per): 
    c=per[k]; print('%-5s %5d %5d %5d %5d %6d'%(k,c['A'],c['B'],c['C'],c['D'],sum(c.values())))
print()
dreason=collections.Counter(x['reason'] for x in out if x['cls']=='D')
print('D reasons',dict(dreason))
pickle.dump(out,open(os.path.join(OUT,'classes.pkl'),'wb'))
