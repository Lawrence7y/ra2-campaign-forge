"""Q4 under the strict reading: the projected tier_final membership is reconstructible
(verified in q4_reconstruct.py). Now compute the two candidate corrected values."""
import csv, io
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P1 = BASE + r'\R17_R88_T1_SEMDEF\tier_final.tsv'
P2 = BASE + r'\R17_R92_T1_REJUDGE\rejudge1242.tsv'
LOG=[]
def L(*a):
    s=' '.join(str(x) for x in a); LOG.append(s); print(s, flush=True)

rows = [r for r in csv.reader(io.StringIO(open(P1,'rb').read().decode('utf-8')), delimiter='\t') if len(r)==5][1:]
p1a_all = {(r[0], int(r[1])) for r in rows}
t2 = open(P2,'rb').read().decode('utf-8')
rr = [r for r in csv.reader(io.StringIO(t2), delimiter='\t')]
h = rr[0]; data = [dict(zip(h, r)) for r in rr[1:] if len(r)==len(h)]
oldobj = {(r['rel'], int(r['bytes'])) for r in data if r['old_verdict']=='对象抄本'}
P1a = p1a_all - oldobj
newobj = {(r['rel'], int(r['bytes'])) for r in data if r['new_verdict']=='对象抄本'}

TF_N, TF_B = len(P1a)+len(newobj), sum(b for _,b in P1a)+sum(b for _,b in newobj)
L('projected tier_final  : %d 件 / %d B   (== 4,413 / 744,172,839: %s)'
  % (TF_N, TF_B, TF_N==4413 and TF_B==744172839))

A2_REL = 'next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
A2_B = 17624355
CALLS_B = 913237
BOUNDS_B = A2_B - CALLS_B
assert (A2_REL, A2_B) in newobj, 'a2_sites not an object member?'

def report(label, keep_b):
    n = TF_N
    b = TF_B - (A2_B - keep_b)
    L('%-28s : 应计入 %d B ; 应剔除 %d B ; 修正后 = %d 件 / %d B'
      % (label, keep_b, A2_B - keep_b, n, b))

L('')
L('--- Q4 candidates ---')
report('reading2 keep whole file', A2_B)
report('reading1/B calls only', CALLS_B)
report('reading1/A drop whole', 0)
L('')
L('bytes: calls %d (%.2f%% of the file) / bounds %d (%.2f%%)' %
  (CALLS_B, 100*CALLS_B/A2_B, BOUNDS_B, 100*BOUNDS_B/A2_B))
L('delta vs current tier_final bytes:')
for k in (A2_B, CALLS_B, 0):
    L('   keep %8d -> %d B  (delta %+d)' % (k, TF_B-(A2_B-k), -(A2_B-k)))
open(BASE + r'\R17_R95_T1_A2SITES\q4_final.out','w',encoding='utf-8').write('\n'.join(LOG))
