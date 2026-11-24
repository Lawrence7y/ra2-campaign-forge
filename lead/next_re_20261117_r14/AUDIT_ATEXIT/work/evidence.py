
import os, importlib.util, csv, json, collections
WORK=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(WORK); EVI=os.path.join(OUT,'EVIDENCE')
spec=importlib.util.spec_from_file_location('az',os.path.join(WORK,'analyze_lib.py'))
az=importlib.util.module_from_spec(spec); spec.loader.exec_module(az)
S13B=[0x0040B740,0x0040B820,0x0040F680,0x0040F760,0x0040FC50,0x0040FD30,0x0046B6A0,
      0x0046B780,0x0054E930,0x0054E9E0,0x0062B110,0x0062B1F0,0x0065BF90,0x0065C070]
S13W=[0x0040F870,0x0054E890,0x0054EA70]
S20D=[0x0040EF60,0x0040F040,0x0053C560,0x00551370,0x00551450,0x00556F50,0x00557030]
S20P=[0x0040F0A0,0x0040F150,0x0053C6A0,0x005514B0,0x00551560,0x00557090,0x00557140]
S20N=[0x00422BE0,0x00423930,0x004253B0,0x00425530,0x004A7C10]
with open(os.path.join(EVI,'detector_controls.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['source_verdict','entry','adjudicated','my_class','match','live_global','dtor_global','table','slot'])
    def row(src,e,adj):
        c,d=az.classify_v2(e); t=(d.get('tables') or [{}])[0]
        lv=';'.join('%08X'%x['global_addr'] for x in t.get('live',[])) or '-'
        dg=';'.join('%08X'%x['global_addr'] for x in t.get('dtor',[])) or '-'
        w.writerow([src,'%08X'%e,adj,c,'YES' if c==adj else 'NO',lv,dg,
                    '%08X'%t.get('table',0) if t else '',t.get('slot','') if t else ''])
    for e in S13B: row('a-S13-K12 blacklist',e,'B')
    for e in S13W: row('a-S13-K12 whitelist',e,'A')
    for e in S20D: row('a-S20-KPROVED demote(dtor)',e,'B')
    for e in S20P: row('a-S20-KPROVED exact PASS',e,'A')
    for e in S20N: row('a-S20-KPROVED demote(no-receiver)',e,'A')
print('wrote detector_controls.tsv')
cnt=json.load(open(os.path.join(OUT,'counts.json')))
with open(os.path.join(EVI,'subsystem_downgrade.tsv'),'w',newline='',encoding='utf8') as f:
    w=csv.writer(f,delimiter='\t')
    w.writerow(['subsystem','n_atlas','proved','threshold_ceil_half','A','B','C','D',
                'proved_after_B_demotion','met_before','met_after'])
    for r in cnt['sub']:
        w.writerow([r['sub'],r['n'],r['proved'],r['thresh'],r['A'],r['B'],r['C'],r['D'],
                    r['proved_after'],r['met_before'],r['met_after']])
print('wrote subsystem_downgrade.tsv')
print('tier1',cnt['tier1'],'tier2',cnt['tier2'])
print('subsystems with B:', [r['sub'] for r in cnt['sub'] if r['B']])
print('met_after:', [r['sub'] for r in cnt['sub'] if r['met_after']])
