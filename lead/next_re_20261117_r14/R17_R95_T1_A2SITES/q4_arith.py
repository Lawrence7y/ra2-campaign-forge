"""Q4 arithmetic under both readings, plus the byte split by which member survives."""
import json
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
P0 = BASE + r'\D41_SUBST\_audit\EVIDENCE\a2_sites.json'
LOG = []
def P(*a):
    line=' '.join(str(x) for x in a); LOG.append(line); print(line, flush=True)

raw = open(P0, 'rb').read()
s = raw.decode('utf-8')
CUT = s.index('}, "bounds": ["')
CALLS_BYTES = CUT
BOUNDS_BYTES = len(raw) - CUT
FILE_BYTES = len(raw)

TF_N, TF_B = 4413, 744172839
P('current tier_final: %d 件 / %d B' % (TF_N, TF_B))
P('a2_sites.json     : 1 件 / %d B (%.2f%% of tier_final)' % (FILE_BYTES, 100*FILE_BYTES/TF_B))
P('')
P('members:')
P('  calls  section : %d B  (keys 6728 + site rows 68253)' % CALLS_BYTES)
P('  bounds section : %d B  (rows %d)' % (BOUNDS_BYTES, 1392592))
P('')
P('--- reading 2 (R14_COMMON §2.49 verbatim: reverifiable-at-address ⇔ object) ---')
P('  keep the whole file: 件 4413 / %d B ; 剔除 0 件 / 0 B' % TF_B)
P('--- reading 1 (card §2.49 wording: address-HOLDS-what-bytes) ---')
P('  A. drop whole file    : 件 %d / %d B ; 剔除 1 件 / %d B' % (TF_N-1, TF_B-FILE_BYTES, FILE_BYTES))
P('  B. keep calls only    : 件 %d / %d B ; 剔除 1 件 / %d B' % (TF_N, TF_B-FILE_BYTES+CALLS_BYTES, FILE_BYTES-CALLS_BYTES))
P('      (= drop 1 件, re-add 1 件 的 calls 部分 %d B)' % CALLS_BYTES)
P('  C. keep calls+bounds  : unchanged, %d 件 / %d B' % (TF_N, TF_B))
P('')
P('--- sanity: does the reading-1/B number line up with the -19,692,980 delta chain? ---')
P('  tier_final(旧) 724,479,859 + 19,692,980 = %d ( == %d ? %s )'
  % (724479859+19692980, TF_B, 724479859+19692980 == TF_B))
P('  if a2_sites drops entirely, new tier_final = %d + %d - %d = %d'
  % (714228639, 29944200, FILE_BYTES, 714228639+29944200-FILE_BYTES))
P('  if only its calls section counts,        = %d + %d - %d + %d = %d'
  % (714228639, 29944200, FILE_BYTES, CALLS_BYTES, 714228639+29944200-FILE_BYTES+CALLS_BYTES))
open(BASE + r'\R17_R95_T1_A2SITES\q4_arith.out','w',encoding='utf-8').write('\n'.join(LOG))
