# -*- coding: utf-8 -*-
"""R214-AUDIT(ds) a1: 独立复算 A/B/C/D 全部条目。只读 gamemd.exe，只写 _r214/a1_out.txt。"""
import sys, struct, collections, json, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

T0 = time.time()
RAW = P.RAW
SECS = [(s['lo'], s['hi_file'], s['name']) for s in P.SECS]
VIRT = [(s['lo'], s['hi_virt'], s['name']) for s in P.SECS]


def where(va):
    if va is None:
        return 'None'
    for lo, hi, nm in SECS:
        if lo <= va < hi:
            return nm
    for lo, hi, nm in VIRT:
        if lo <= va < hi:
            return 'virt-only'
    return 'other'


def dw(va):
    o = P.r2o(va)
    return None if o is None else struct.unpack_from('<I', RAW, o)[0]


def s32(v):
    return struct.unpack('<i', struct.pack('<I', v & 0xffffffff))[0]


def hx(v):
    return 'None' if v is None else '0x%08x' % v


# ---------------- COL / pred / views ----------------
COL = {}
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, RAW, s['rawptr'])
    for k in range(n - 4):
        if w[k] not in (0, 1, 2) or w[k + 2] != 0:
            continue
        if where(w[k + 3]) != '.data' or where(w[k + 4]) != '.rdata':
            continue
        nb = P.cstr(w[k + 3] + 8, 400)
        if not (nb and nb.startswith(b'.?A') and nb.endswith(b'@@')):
            continue
        raw = nb.decode('latin1')
        COL[base + 4 * k] = dict(addr=base + 4 * k, sig=w[k], mdisp=s32(w[k + 1]),
                                 pTD=w[k + 3], pCHD=w[k + 4], cls=raw[1:])

pred = collections.defaultdict(list)
for sn in ('.rdata', '.data'):
    s = P.B[sn]
    n = s['rawsize'] // 4
    base = s['lo']
    w = struct.unpack_from('<%dI' % n, RAW, s['rawptr'])
    for k in range(n - 1):
        if w[k] in COL and where(w[k + 1]) == '.text':
            pred[w[k]].append(base + 4 * k)

VSTART = sorted(v[0] + 4 for v in pred.values())
views = {}
for c, v in COL.items():
    if len(pred[c]) != 1:
        continue
    vt = pred[c][0] + 4
    # 口径1 (ex1/ex2): 连续 .text dword，遇非 .text 停
    s1 = []
    a = vt
    while len(s1) < 4096:
        d = dw(a)
        if d is None or where(d) != '.text':
            break
        s1.append(d)
        a += 4
    # 口径2 (m0/m1): 同时受下一个 vftable 起点约束
    nxt = None
    for x in VSTART:
        if x > vt:
            nxt = x
            break
    s2 = []
    a = vt
    lim = nxt or 0x10000000
    while a < lim and len(s2) < 2000:
        d = dw(a)
        if d is None or where(d) != '.text':
            break
        s2.append(d)
        a += 4
    views[c] = dict(C=c, base=vt, mdisp=v['mdisp'], cls=v['cls'], s1=s1, s2=s2)

print('=== SCALE ===')
print('COL=%d pred_sites=%d distinct_pred=%d views=%d' %
      (len(COL), sum(len(v) for v in pred.values()), len(pred), len(views)))
tot1 = sum(len(v['s1']) for v in views.values())
tot2 = sum(len(v['s2']) for v in views.values())
main = [v for v in views.values() if v['mdisp'] == 0]
sec = [v for v in views.values() if v['mdisp'] != 0]
print('views by mdisp==0: main=%d sec=%d' % (len(main), len(sec)))
print('slots 口径1(连续.text)=%d  口径2(下一起点约束)=%d  差异视图数=%d' %
      (tot1, tot2, sum(1 for v in views.values() if len(v['s1']) != len(v['s2']))))
# 两种口径不一致的视图
diff = [(hx(v['C']), v['cls'], v['mdisp'], len(v['s1']), len(v['s2']))
        for v in views.values() if len(v['s1']) != len(v['s2'])]
print('mismatch sample=%s' % diff[:10])

# ================= A 组 =================
print('\n===== A 组 =====')
allslots = [(v['C'], v['cls'], v['mdisp'], i, d)
            for v in views.values() for i, d in enumerate(v['s2'])]
wherecnt = collections.Counter(where(x[4]) for x in allslots)
print('A1 total slots=%d  section dist=%s' % (len(allslots), dict(wherecnt)))
TGT = collections.Counter(x[4] for x in allslots)
print('A2 distinct target=%d' % len(TGT))
TM = collections.Counter(d for v in main for d in v['s2'])
TS = collections.Counter(d for v in sec for d in v['s2'])
both = set(TM) & set(TS)
print('A3 main_distinct=%d sec_distinct=%d both=%d onlymain=%d onlysec=%d  shared=%s' %
      (len(TM), len(TS), len(both), len(set(TM) - set(TS)), len(set(TS) - set(TM)),
       [hx(x) for x in both]))
# A4: 同索引主视图一致性
IDX = collections.defaultdict(collections.Counter)
for v in main:
    for i, d in enumerate(v['s2']):
        IDX[i][d] += 1
mono = [i for i in IDX if len(IDX[i]) == 1]
print('A4 idx_count=%d mono=%d  (max idx=%d)' % (len(IDX), len(mono), max(IDX)))
# 分母效应：只看 954 张主视图全部具备该槽的索引
full = [i for i in IDX if sum(IDX[i].values()) == len(main)]
monof = [i for i in full if len(IDX[i]) == 1]
print('A4b 分母=954 的索引数=%d 其中 mono=%d ; 分母<10 的索引数=%d 其中 mono=%d' %
      (len(full), len(monof), sum(1 for i in IDX if sum(IDX[i].values()) < 10),
       sum(1 for i in IDX if sum(IDX[i].values()) < 10 and len(IDX[i]) == 1)))
print('A4c mono 索引清单(前 30 个 idx,value)=%s' %
      [(i, hx(list(IDX[i])[0])) for i in mono[:30]])
# A5 反控：COL+4
m0vals = collections.Counter(dw(v['C'] + 4) for v in main)
print('A5 primary COL+4 取值分布=%s ; 其中落 .text 数=%d/%d' %
      (dict(list(m0vals.items())[:5]), sum(1 for v in main if where(dw(v['C'] + 4)) == '.text'), len(main)))
print('   注：COL+4 即 mdisp 字段本身；主视图 mdisp==0 恒成立 ⇒ 该反控恒为 0')

# ================= B 组 =================
print('\n===== B 组 =====')
gt = [v for v in views.values() if len(v['s2']) > 18]
print('B1 n>18 views=%d (main=%d sec=%d)' %
      (len(gt), sum(1 for v in gt if v['mdisp'] == 0), sum(1 for v in gt if v['mdisp'] != 0)))
s18 = [v['s2'][18] for v in gt]
c18 = collections.Counter(s18)
print('   slot18 distinct=%d section=%s' % (len(c18), dict(collections.Counter(where(x) for x in s18))))
print('B2 slot18 top3=%s' % [(hx(a), n) for a, n in c18.most_common(3)])
for cn in ('MouseClass', 'TabClass', 'ScrollClass', 'HouseClass'):
    want = '?AV%s@@' % cn
    hits = [v for v in views.values() if v['cls'] == want]
    pr = [v for v in hits if v['mdisp'] == 0]
    s21784 = [v for v in hits if v['mdisp'] == 21784]
    print('B3 %-12s cols=%d primary=%s' % (cn, len(hits),
          [(hx(v['base']), v['mdisp'], len(v['s2']), hx(v['s2'][0]),
            hx(v['s2'][18]) if len(v['s2']) > 18 else None) for v in pr]))
    print('   %-12s m21784=%s' % (cn, [(hx(v['base']), v['mdisp'], len(v['s2']),
                                        [hx(x) for x in v['s2']]) for v in s21784]))
# B4: calls to 0x723ea0/0x723eb0
md = Cs(CS_ARCH_X86, CS_MODE_32)
T4 = {0x723ea0, 0x723eb0}
t = P.B['.text']
blob = RAW[t['rawptr']:t['rawptr'] + t['rawsize']]
cand = []
for op in (0xe8, 0xe9):
    ob = bytes([op])
    pos = 0
    while True:
        i = blob.find(ob, pos)
        if i < 0 or i + 5 > len(blob):
            break
        pos = i + 1
        rel = struct.unpack_from('<i', blob, i + 1)[0]
        a = t['lo'] + i
        tg = a + 5 + rel
        if tg in T4:
            cand.append((a, op, rel, tg))
ver = []
dec_fail = []
for a, op, rel, tg in cand:
    o = P.r2o(a)
    ins = next(md.disasm(RAW[o:o + 16], a, count=1), None)
    if ins is not None and ins.size == 5 and ins.mnemonic in ('call', 'jmp') \
            and ins.op_str.strip() == hex(tg):
        ver.append((a, ins.mnemonic, tg, rel))
    else:
        dec_fail.append((hx(a), hx(op), ins.mnemonic + ' ' + ins.op_str if ins else None))
print('B4 prefilter(e8/e9)=%d verified=%d decode_fail=%d' % (len(cand), len(ver), len(dec_fail)))
print('   call/jmp 分布=%s ; 按目标=%s' %
      (dict(collections.Counter(m for _, m, _, _ in ver)),
       dict(collections.Counter(hx(tg) for _, _, tg, _ in ver))))
print('   sites=%s' % [hx(a) for a, _, _, _ in sorted(ver)])
print('   slot 值命中=%d/14044' % sum(1 for x in allslots if x[4] in T4))
for tg in (0x723ea0, 0x723eb0):
    o = P.r2o(tg)
    print('   目标 %s 前 8 字节=%s where=%s' % (hx(tg), RAW[o:o + 8].hex(), where(tg)))
print('B5 slot17: views=%d distinct=%d top3=%s' %
      (sum(1 for v in views.values() if len(v['s2']) > 17),
       len(set(v['s2'][17] for v in views.values() if len(v['s2']) > 17)),
       [(hx(a), n) for a, n in collections.Counter(
           v['s2'][17] for v in views.values() if len(v['s2']) > 17).most_common(3)]))
print('   slot19: views=%d distinct=%d top3=%s' %
      (sum(1 for v in views.values() if len(v['s2']) > 19),
       len(set(v['s2'][19] for v in views.values() if len(v['s2']) > 19)),
       [(hx(a), n) for a, n in collections.Counter(
           v['s2'][19] for v in views.values() if len(v['s2']) > 19).most_common(3)]))
print('   三者(17/18/19 distinct)=%d/%d/%d' %
      (len(set(v['s2'][17] for v in views.values() if len(v['s2']) > 17)), len(c18),
       len(set(v['s2'][19] for v in views.values() if len(v['s2']) > 19))))


# ================= C 组 =================
def adj(a):
    o = P.r2o(a)
    if o is None:
        return None
    q = []
    for i in md.disasm(RAW[o:o + 16], a):
        q.append(i)
        if len(q) >= 2:
            break
    if len(q) < 2:
        return None
    i1, i2 = q[0], q[1]
    if i1.mnemonic != 'sub' or 'esp + 4' not in i1.op_str:
        return None
    if i2.mnemonic != 'jmp' or '[' in i2.op_str or not i2.op_str.strip().startswith('0x'):
        return None
    try:
        imm = int(i1.op_str.split(',')[-1].strip(), 16)
        jt = int(i2.op_str.strip().split()[0], 16)
    except Exception:
        return None
    return dict(imm=imm, jmp=jt, l1=i1.size, l2=i2.size,
                s=i1.mnemonic + ' ' + i1.op_str, j=i2.mnemonic + ' ' + i2.op_str)


print('\n===== C 组 =====')
ADJ = []
for v in views.values():
    for i, d in enumerate(v['s2']):
        r = adj(d)
        if r:
            r.update(view=v['C'], cls=v['cls'], mdisp=v['mdisp'], idx=i, slotaddr=v['base'] + 4 * i)
            ADJ.append(r)
print('C1 adjustor 槽总数=%d' % len(ADJ))
print('   in main views=%d in sec views=%d' %
      (sum(1 for a in ADJ if a['mdisp'] == 0), sum(1 for a in ADJ if a['mdisp'] != 0)))
okc = [a for a in ADJ if a['imm'] == a['mdisp']]
bad = [a for a in ADJ if a['imm'] != a['mdisp']]
print('   imm==mdisp 通过=%d 例外=%d' % (len(okc), len(bad)))
for a in bad:
    print('   例外 %s cls=%s mdisp=%d idx=%d imm=%d jmp=%s slotaddr=%s' %
          (hx(a['slotaddr']), a['cls'], a['mdisp'], a['idx'], a['imm'], hx(a['jmp']), hx(a['slotaddr'])))
# 目标归属映射
owner = collections.defaultdict(list)
for v in views.values():
    for i, d in enumerate(v['s2']):
        owner[d].append((v['C'], v['mdisp'], v['cls'], i))
print('C1b 一般律核验 imm == mdisp_self - mdisp_target :')
gen_ok = 0
gen_bad = []
for a in ADJ:
    ow = [x for x in owner.get(a['jmp'], [])]
    if not ow:
        gen_bad.append((hx(a['slotaddr']), 'target 不在任何视图槽'))
        continue
    mds = set(x[1] for x in ow)
    if len(mds) == 1 and a['imm'] == a['mdisp'] - list(mds)[0]:
        gen_ok += 1
    else:
        gen_bad.append((hx(a['slotaddr']), a['mdisp'], a['imm'], sorted(mds),
                        [(hx(x[0]), x[1], x[3]) for x in ow][:4]))
print('   满足 %d/%d ; 不满足=%d %s' % (gen_ok, len(ADJ), len(gen_bad), gen_bad[:6]))
# C2 HouseClass 细节
HC = [v for v in views.values() if v['cls'] == '?AVHouseClass@@']
print('C2 HouseClass COL 数=%d' % len(HC))
for v in sorted(HC, key=lambda x: -x['mdisp']):
    print('   col=%s mdisp=%-5d VT=%s slots=%2d idx0..2=%s  adj_idx=%s' %
          (hx(v['C']), v['mdisp'], hx(v['base']), len(v['s2']),
           [hx(x) for x in v['s2'][:3]],
           [a['idx'] for a in ADJ if a['view'] == v['C']]))
for a in bad:
    inmain = a['jmp'] in [d for v in HC if v['mdisp'] == 0 for d in v['s2']]
    print('   例外 %s idx=%d imm=%d jmp=%s 在本类主视图槽内=%s owner=%s' %
          (hx(a['slotaddr']), a['idx'], a['imm'], hx(a['jmp']), inmain,
           [(hx(x[0]), x[1], x[3]) for x in owner[a['jmp']]]))
# C3 mdisp 元组
bym = collections.defaultdict(set)
for c, v in COL.items():
    if v['mdisp'] != 0:
        bym[v['cls']].add(v['mdisp'])
tup = collections.Counter(tuple(sorted(s)) for s in bym.values())
print('C3 有非零 mdisp 的类数=%d 元组种类=%d' % (len(bym), len(tup)))
for k, n in tup.most_common():
    print('   %-40s x%d' % (str(k), n))
print('   HouseClass=%s  AircraftClass=%s' %
      (sorted(bym.get('?AVHouseClass@@', [])), sorted(bym.get('?AVAircraftClass@@', []))))
# C4 指令模板
tmpl = collections.Counter((a['l1'], a['l2'], a['s'].split(',')[0]) for a in ADJ)
print('C4 指令模板(l1,l2,前缀)=(x%d)' % len(tmpl))
for k, n in tmpl.most_common():
    print('   %s x%d' % (str(k), n))
print('   8 字节版明细=%s' %
      [(hx(a['slotaddr']), a['cls'], a['mdisp'], a['idx'], a['imm'], a['s'])
       for a in ADJ if a['l1'] == 8])
print('   纯助记符序列 distinct=%d' % len(set((a['s'].split()[0], a['j'].split()[0]) for a in ADJ)))
# C5 每张次视图 adjustor 数
cntv = collections.Counter()
for v in views.values():
    if v['mdisp'] != 0:
        cntv[sum(1 for a in ADJ if a['view'] == v['C'])] += 1
print('C5 次视图 adjustor 数分布=%s (次视图总数=%d)' %
      (dict(sorted(cntv.items())), sum(1 for v in views.values() if v['mdisp'] != 0)))
z = [v for v in views.values() if v['mdisp'] != 0 and len(v['s2']) > 0
     and sum(1 for a in ADJ if a['view'] == v['C']) == 0]
print('   adjustor==0 的次视图槽数分布=%s' %
      dict(sorted(collections.Counter(len(v['s2']) for v in z).items())))

# ================= D 组 =================
print('\n===== D 组 =====')
MAIN = {}
for v in main:
    MAIN[v['C']] = v
byL = collections.defaultdict(list)
for c, v in MAIN.items():
    byL[len(v['s2'])].append(c)
pref = collections.defaultdict(list)
for c, v in MAIN.items():
    sl = v['s2']
    for L in (len(sl), len(sl) // 2, 1):
        pref[(L, tuple(sl[:L]))].append(c)
PARENT = {}
AMB = []
for c, v in MAIN.items():
    sl = v['s2']
    best = None
    for L in range(1, len(sl) + 1):
        if L == len(sl):
            continue
        cands = [x for x in pref.get((L, tuple(sl[:L])), []) if x != c and len(MAIN[x]['s2']) > L]
        if cands:
            best = (L, cands)
    PARENT[c] = best[1] if best else []
    if best and len(best[1]) > 1:
        AMB.append((MAIN[c]['cls'], best[0], [MAIN[x]['cls'] for x in best[1]][:5]))
roots = [c for c in MAIN if not PARENT[c]]
DEP = {}


def dep(c, seen=()):
    if c in DEP:
        return DEP[c]
    if c in seen:
        return 0
    p = PARENT[c]
    d = 1 + max([dep(x, seen + (c,)) for x in p]) if p else 0
    DEP[c] = d
    return d


for c in MAIN:
    dep(c)
print('D1 复算 m1 口径: 主视图=%d 歧义类=%d 根=%d 最大深度=%d 深度直方(非0)=%s' %
      (len(MAIN), len(AMB), len(roots), max(DEP.values()),
       dict(sorted((k, v) for k, v in collections.Counter(DEP.values()).items() if k))))
mutual = [c for c in MAIN if PARENT[c] and any(c in PARENT[x] for x in PARENT[c])]
print('   互为父子的类数=%d 例=%s' %
      (len(mutual), [(MAIN[c]['cls'], [MAIN[x]['cls'] for x in PARENT[c]][:2]) for c in mutual[:5]]))
# 全长前缀口径（m1 只索引 3 个长度）
FULL = 0
FULLEX = []
items = list(MAIN.items())
for i in range(len(items)):
    a = items[i][1]['s2']
    for j in range(len(items)):
        if i == j:
            continue
        b = items[j][1]['s2']
        if len(a) < len(b) and b[:len(a)] == a:
            FULL += 1
            if len(FULLEX) < 5:
                FULLEX.append((items[i][1]['cls'], items[j][1]['cls']))
print('   全长前缀口径的合法前缀对数=%d 例=%s' % (FULL, FULLEX))
dup = collections.defaultdict(list)
for c, v in MAIN.items():
    dup[tuple(v['s2'])].append(c)
dups = [g for g in dup.values() if len(g) > 1]
print('   完全同槽序列组=%s' % [[MAIN[c]['cls'] for c in g] for g in dups])
print('\nelapsed=%.2fs' % (time.time() - T0))
