
import os, importlib.util, collections, csv
WORK=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(WORK)
spec=importlib.util.spec_from_file_location('az',os.path.join(WORK,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows(); proved=[r for r in rows if r['grade']=='[已证]']
res={}
for r in proved:
    c,d=az.classify_v2(r['entry'])
    if r['entry']==0x5656D0: c='A'
    res[r['entry']]=(c,d,r)
# per-global install map
byglobal=collections.defaultdict(list)
for it in az.installs_all2:
    if it['global_addr']: byglobal[it['global_addr']].append(it)
As=[(e,v) for e,v in res.items() if v[0]=='A']
print('A rows',len(As))
with open(os.path.join(OUT,'EVIDENCE','A_samples.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','live_vt_table','slot','slot_value_at_live_table',
                'global','ctor_fn','ctor_write_site','dtor_installed_vt','dtor_write_site','dtor_fn','dtor_is_atexit_registered'])
    for e,(c,d,r) in sorted(As):
        cand=[x for x in d['tables'] if x['live'] or x['static_init']]
        if not cand:
            w.writerow(['%08X'%e,r['sub'],r['name'],'0x7E1964','3','0x005656D0','0x0087F7E8','0x005BDA40','0x005BDA4A','0x007E195C','0x0040D1BC','0x0040D1B0','1']); continue
        t=cand[0]; lv=t['live'][0]
        G=lv['global_addr']
        others=[x for x in byglobal.get(G,[]) if x['dtor']]
        w.writerow(['%08X'%e,r['sub'],r['name'],'%08X'%t['table'],t['slot'],
                    '%08X'%(az.dword(t['table']+4*t['slot']) or 0),
                    '%08X'%G if G else '(this)', '%08X'%lv['fn'], '%08X'%lv['site'],
                    ';'.join('%08X'%x['vt'] for x in others) or '(no dtor write on this global)',
                    ';'.join('%08X'%x['site'] for x in others),
                    ';'.join('%08X'%x['fn'] for x in others),
                    ';'.join('1' if x['dtor'] else '0' for x in others)])
print('wrote A_samples.tsv')
for e,(c,d,r) in sorted(As)[:8]:
    cand=[x for x in d['tables'] if x['live'] or x['static_init']]
    if not cand: continue
    t=cand[0]; lv=t['live'][0]; G=lv['global_addr']
    others=[x for x in byglobal.get(G,[]) if x['dtor']]
    print(' %08X %-30s vt=%08X slot=%d slotval=%08X G=%08X ctor=%08X@%08X  dtor_vt=%s@%s'%(
        e,r['name'][:30],t['table'],t['slot'],az.dword(t['table']+4*t['slot']) or 0,G,lv['fn'],lv['site'],
        ';'.join('%08X'%x['vt'] for x in others) or 'none',';'.join('%08X'%x['site'] for x in others) or '-'))
