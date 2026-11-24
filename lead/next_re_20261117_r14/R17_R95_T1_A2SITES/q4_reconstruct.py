import csv, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P1 = BASE + r'\R17_R88_T1_SEMDEF\tier_final.tsv'
P2 = BASE + r'\R17_R92_T1_REJUDGE\rejudge1242.tsv'
LOG=[]
def L(*a):
    s=' '.join(str(x) for x in a); LOG.append(s); print(s, flush=True)

rows = [r for r in csv.reader(io.StringIO(open(P1,'rb').read().decode('utf-8')), delimiter='\t') if len(r)==5][1:]
p1a = {(r[0], int(r[1])) for r in rows}
L('old tier_final.tsv: 4,518 rows, %d B' % sum(b for _, b in p1a))
L('rows whose why_content mentions P1a:', sum(1 for r in rows if 'P1a' in r[2]), ' other:', sum(1 for r in rows if 'P1a' not in r[2]))

t2 = open(P2,'rb').read().decode('utf-8')
rr = [r for r in csv.reader(io.StringIO(t2), delimiter='\t')]
h = rr[0]; data = [dict(zip(h, r)) for r in rr[1:] if len(r)==len(h)]
oldobj = [r for r in data if r['old_verdict']=='对象抄本']
L('rejudge1242 old=对象抄本: %d rows, %d B' % (len(oldobj), sum(int(r['bytes']) for r in oldobj)))
oldobj_set = {(r['rel'], int(r['bytes'])) for r in oldobj}
L('   of those, present in old tier_final.tsv by (rel,bytes): %d' % len(oldobj_set & p1a))
L('   rel-only match: %d' % len({a for a,_ in oldobj_set} & {a for a,_ in p1a}))
L('')
L('== Q4 reconstruction ==')
nonobj = p1a - oldobj_set
L('P1a (non-object part) = old tier_final minus the 732 = %d 件 / %d B' % (len(nonobj), sum(b for _,b in nonobj)))
newobj_set = {(r['rel'], int(r['bytes'])) for r in data if r['new_verdict']=='对象抄本'}
L('projected tier_final = %d + %d = %d 件 / %d B' % (len(nonobj), len(newobj_set), len(nonobj)+len(newobj_set), sum(b for _,b in nonobj)+sum(b for _,b in newobj_set)))
L('   -> matches 4,413 / 744,172,839 ?', len(nonobj)+len(newobj_set)==4413 and sum(b for _,b in nonobj)+sum(b for _,b in newobj_set)==744172839)
open(BASE + r'\R17_R95_T1_A2SITES\q4_reconstruct.out','w',encoding='utf-8').write('\n'.join(LOG))
