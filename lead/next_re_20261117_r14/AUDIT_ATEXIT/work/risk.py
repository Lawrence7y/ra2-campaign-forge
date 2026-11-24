
import os, importlib.util, collections, csv, json
WORK=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(WORK)
spec=importlib.util.spec_from_file_location('az',os.path.join(WORK,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
rows=az.load_rows(); proved=[r for r in rows if r['grade']=='[已证]']
HAND={0x5656D0:'A'}
res={}
for r in proved:
    c,d=az.classify_v2(r['entry'])
    if r['entry'] in HAND: c='A'
    res[r['entry']]=(c,d,r)
D=[(e,v) for e,v in res.items() if v[0]=='D']
d1=[x for x in D if x[1][1].get('reason')]; d2=[x for x in D if not x[1][1].get('reason')]
# D-2 residual risk: table has a *register* install inside an atexit-registered fn
risk=[]
for e,(c,d,r) in d2:
    hit=False
    for t in d['tables']:
        for x in az.by_vt_all2.get(t['table'],[]):
            if x['fn'] in az.registered: hit=True
    if hit: risk.append((e,r))
print('D total',len(D),'D-1',len(d1),'D-2',len(d2),'D-2 with an atexit-fn register install (residual B-risk)',len(risk))
print('D-1 rows (no reference at all):')
for e,(c,d,r) in d1[:30]:
    print('   %08X %s %-32s in_atlas=%s'%(e,r['sub'],r['name'][:32],e in az.atlas))
# A rows full detail
As=[(e,v) for e,v in res.items() if v[0]=='A']
print('\nA rows:',len(As))
with open(os.path.join(OUT,'EVIDENCE','A_detail.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['entry','subsystem','name','live_vt','slot','slot_value','global','ctor_fn','ctor_write_site','dtor_vt_table','dtor_write_site','dtor_fn'])
    for e,(c,d,r) in sorted(As):
        cand=[x for x in d['tables'] if x['live'] or x['static_init']]
        if not cand:
            w.writerow(['%08X'%e,r['sub'],r['name'],'(hand-verified)','','','0087F7E8','005BDA40','005BDA4A','','','']); continue
        t=cand[0]
        lv=t['live'][0] if t['live'] else {}
        w.writerow(['%08X'%e,r['sub'],r['name'],'%08X'%t['table'],t['slot'],
                    '%08X'%(az.dword(t['table']+4*t['slot']) or 0),
                    ('%08X'%lv['global_addr']) if lv.get('global_addr') else '(this)',
                    ('%08X'%lv['fn']) if lv else '',('%08X'%lv['site']) if lv else '',
                    ';'.join('%08X'%x['vt'] for x in t['dtor']) or '(none)',
                    ';'.join('%08X'%x['site'] for x in t['dtor']) or '',
                    ';'.join('%08X'%x['fn'] for x in t['dtor']) or ''])
# print 6 A rows for hand check
for e,(c,d,r) in sorted(As)[:6]:
    cand=[x for x in d['tables'] if x['live'] or x['static_init']]
    if not cand: continue
    t=cand[0]
    print('  %08X %s %-34s vt=%08X slot=%d val=%08X global=%s ctor_fn=%08X site=%08X dtor=%s'%(
      e,r['sub'],r['name'][:34],t['table'],t['slot'],az.dword(t['table']+4*t['slot']) or 0,
      ('%08X'%t['live'][0]['global_addr']) if t['live'] else '(static)',t['live'][0]['fn'],t['live'][0]['site'],
      ';'.join('%08X'%x['vt'] for x in t['dtor']) or 'none'))
