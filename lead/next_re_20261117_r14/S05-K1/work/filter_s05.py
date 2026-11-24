import csv, collections, re, os
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
COV=os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
OUT=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','work','s05_filter.txt')

with open(COV,encoding='utf-8',errors='replace') as f:
    rows=list(csv.DictReader(f,delimiter='\t'))
s05=[r for r in rows if r['subsystem']=='S05']
g=collections.Counter(r['grade'] for r in s05)
with open(OUT,'w',encoding='utf-8') as o:
    o.write('S05 total=%d\n'%len(s05))
    o.write('grades: '+repr(dict(g))+'\n\n')
    # field-offset entries
    pat=re.compile(r'\+\s*0x[0-9A-Fa-f]+')
    field=[r for r in s05 if pat.search(r['one_line_semantics'])]
    o.write('=== entries whose one_line mentions +0xNN: %d ===\n'%len(field))
    fgc=collections.Counter(r['grade'] for r in field)
    o.write('field grades: '+repr(dict(fgc))+'\n')
    for r in field:
        o.write('%s\t%s\t%s\t%s\n'%(r['entry'],r['name'],r['grade'],r['one_line_semantics']))
    o.write('\n=== [未证] count=%d ; unnamed sub_ count=%d ; union=%d ===\n'%(
        sum(1 for r in s05 if r['grade']=='[未证]'),
        sum(1 for r in s05 if r['name'].startswith('sub_')),
        sum(1 for r in s05 if r['grade']=='[未证]' or r['name'].startswith('sub_'))))
    # distinct offsets mentioned across ALL S05
    offs=collections.Counter()
    for r in s05:
        for m in pat.findall(r['one_line_semantics']):
            offs[m.lower()]+=1
    o.write('\n=== distinct offsets in S05 one_line (top 60) ===\n')
    for off,c in offs.most_common(60):
        o.write('%s %d\n'%(off,c))
print('wrote',OUT)
