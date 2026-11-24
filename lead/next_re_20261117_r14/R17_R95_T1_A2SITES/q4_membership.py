import csv, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P1 = BASE + r'\R17_R88_T1_SEMDEF\tier_final.tsv'
P2 = BASE + r'\R17_R92_T1_REJUDGE\rejudge1242.tsv'
LOG=[]
def L(*a):
    s=' '.join(str(x) for x in a); LOG.append(s); print(s, flush=True)

t = open(P1, 'rb').read().decode('utf-8')
rows = [r for r in csv.reader(io.StringIO(t), delimiter='\t') if len(r) == 5][1:]
L('tier_final.tsv (old, 4,518 rows) sum(bytes) =', sum(int(r[1]) for r in rows), '-> 724,479,859 ?', sum(int(r[1]) for r in rows) == 724479859)

t2 = open(P2, 'rb').read().decode('utf-8')
rows2 = [r for r in csv.reader(io.StringIO(t2), delimiter='\t')]
hdr = rows2[0]; data = [r for r in rows2[1:] if len(r) == len(hdr)]
L('rejudge1242 cols:', hdr)
newobj = [r for r in data if r[2] == '对象抄本']
L('new-object rows:', len(newobj), 'bytes', sum(int(r[1]) for r in newobj), '-> 29,944,200 ?', sum(int(r[1]) for r in newobj) == 29944200)
a2 = [r for r in data if 'a2_sites.json' in r[0]]
for r in a2:
    L('a2_sites row:', dict(zip(hdr, r)))

# arithmetic closure of the two expressions given in §2.53
L('')
L('x = 4,513 + 3,786 =', 4513+3786, ' (= current 4,413 ?', 4513+3786 == 4413, ')')
L('y = 724,479,859 - 17,624,355 + 29,944,200 =', 724479859-17624355+29944200, ' (= 744,172,839 ?', 724479859-17624355+29944200 == 744172839, ')')
L('old: 4,518 + 3,786 =', 4518+3786, ' ; 724,479,859 + 10,251,220 =', 724479859+10251220)
L('612 = 505 + 89 + 18? ->', 505+89+18)
open(BASE + r'\R17_R95_T1_A2SITES\q4_membership.out','w',encoding='utf-8').write('\n'.join(LOG))
