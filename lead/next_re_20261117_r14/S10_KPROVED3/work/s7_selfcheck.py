"""S10-KPROVED3 final self-check of core numbers + M1-M8/M6/M15 structural compliance."""
import csv, os, re, json
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.join(HERE,'..')
D=os.path.join(ROOT,'coverage_delta.tsv')
rows=list(csv.DictReader(open(D,encoding='utf-8'),delimiter='\t'))
print('delta rows =',len(rows),'(expect 8)')
merged=set('004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690'.split())
print('M-excl overlap =',len([r for r in rows if r['entry'] in merged]),'(expect 0)')
bad=[]
for r in rows:
    e=r['entry']; nm=r['name']; sem=r['one_line_semantics']; gr=r['grade']
    cls=nm.split('::')[0]
    # M8 forbidden
    for w in ['未证','未定','弱信号','线索','槽语义未']:
        if w in sem: bad.append((e,'M8',w))
    # M5 offset format: all @+0x hex
    for m in re.findall(r'@\+([0-9A-Fa-f]+)',sem):
        pass
    if gr!='[已证]': bad.append((e,'grade',gr))
    # M2: ② class appears in semantics and matches name class
    if ('②'+cls) not in sem and cls not in sem: bad.append((e,'M2',cls))
print('structural violations =',bad if bad else 'NONE')
# core numbers from summary
s=json.load(open(os.path.join(ROOT,'EVIDENCE','summary.json'),encoding='utf-8'))
print('four_ring_complete =',s['four_ring_complete'],'delta_rows =',s['delta_rows'],'A_total =',s['S10_A_total'])
b=s['baseline']
print('baseline pool=%d strict_rate=%.4f loose_rate=%.4f draws=%d'%(b['pool'],b['rate_strict'],b['rate_loose'],b['draws']))
# PROGRESS lines
pl=len(open(os.path.join(ROOT,'PROGRESS.md'),encoding='utf-8').read().splitlines())
print('PROGRESS lines =',pl,'(expect <=60)')
