# -*- coding: utf-8 -*-
"""R171 F：算出 V551 重钉所需的全部常量（实测，不手填），并先验证旧常量确实命中旧值。"""
import hashlib, io, os, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TIER = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14'))
V550 = os.path.join(TIER, 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')
V551 = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def parse(p):
    raw = io.open(p, 'rb').read()
    lines = [x for x in raw.decode('utf-8').split('\n') if x]
    rows = [l.split('\t') for l in lines[1:]]
    return raw, rows

r550, rows550 = parse(V550)
r551, rows551 = parse(V551)

# ---- 旧常量自证同法（反控：先证明我的算法能复现旧值）----
OLD_SHA = 'd85034b0b2e42fd34e8140e37e1d27be22cefbc2198d455b0295ef662c58a386'
OLD_BYTES = 120495
OLD_MASTER = '90ff6911e98087ca422264ef72c3bd5dc65d68f60a372f49f3d5a6800dd12aa2'
ck('N1 用同一算法在 V550 上复现旧 CUR_SHA256', hashlib.sha256(r550).hexdigest() == OLD_SHA)
ck('N2 用同一算法在 V550 上复现旧 TOTAL_BYTES', len(r550) == OLD_BYTES, len(r550))

# ---- 新值 ----
NEW_SHA = hashlib.sha256(r551).hexdigest()
NEW_BYTES = len(r551)
F24_STMT_B = len(rows551[[i for i,row in enumerate(rows551) if row[0]=='F24'][0]][1].encode())
F24_LIM_B  = len(rows551[[i for i,row in enumerate(rows551) if row[0]=='F24'][0]][4].encode())
ck('P1 F24.stmt 字节由 10520 增至 %d（D6 是禁缩，增长合法）' % F24_STMT_B, F24_STMT_B > 10520, F24_STMT_B)
ck('P1b F24.lim 字节未变 31158（本轮未动 limitations）', F24_LIM_B == 31158, F24_LIM_B)
ck('P1c F24 bytes == (stmt,lim) == (%d,%d)' % (F24_STMT_B, F24_LIM_B),
   (F24_STMT_B, F24_LIM_B) == (10565, 31158), (F24_STMT_B, F24_LIM_B))

print('\n  V551 sha256      = %s' % NEW_SHA)
print('  V551 bytes       = %d' % NEW_BYTES)
print('  F24 FLOORS       = (%d, %d)' % (F24_STMT_B, F24_LIM_B))

out = {'sha': NEW_SHA, 'bytes': NEW_BYTES, 'f24_floors': [F24_STMT_B, F24_LIM_B],
       'v550_sha': OLD_SHA, 'v550_bytes': OLD_BYTES, 'v550_master': OLD_MASTER}
io.open(os.path.join(HERE, 'r171f_pins.json'), 'w', encoding='utf-8').write(json.dumps(out, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
