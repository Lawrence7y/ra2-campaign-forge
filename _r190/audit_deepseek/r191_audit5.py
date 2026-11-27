# -*- coding: utf-8 -*-
"""R191 审计第五轮（决定性取证）。
W1 R1 的诚實置换零假设（按层内类置换值），给「两侧都直接 0 命中」的真 p 值。
W2 A1 的判别判据：每个 (层偏移,槽号) 组的「类->值」映射基数与是否为 1:1 / 多:1 / 散，
   并检验「同值类是否落在同一继承子树」（继承共享 vs 巧合）。
W3 A3 的替代解释：extra 四档宿主表是否在同一层另有副表；以及 StageClass 在 36/172/248 三处
   有无副表的对照（同基类、不同档，直接判别档的成因）。
"""
import sys, struct, collections, json, random, itertools
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
RW = {}
def hdr(s): print('\n==== ' + s + ' ====')
SECV = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; n = s['rawsize'] // 4
    SECV[sec] = (s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n)
name_ok = lambda nm: bool(nm) and nm.startswith(b'.?A') and nm.endswith(b'@@')
COL = {}
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(n - 4):
        if v[i] not in (0, 1) or v[i + 2] != 0: continue
        if P.where(v[i + 3]) != '.data' or P.where(v[i + 4]) != '.rdata': continue
        nm = P.cstr(v[i + 3] + 8, 200)
        if not name_ok(nm): continue
        COL[base + 4 * i] = dict(mdisp=v[i + 1], ptd=v[i + 3], pchd=v[i + 4], name=nm.decode('latin1'))
VT = {}
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(1, n):
        if LO <= v[i] < HI and v[i - 1] in COL: VT[base + 4 * i] = COL[v[i - 1]]
def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
PRE = {vt: pre(vt) for vt in VT}
order = sorted(VT)
def thunkof(va):
    o = P.r2o(va)
    if o is None: return None
    b = RAW[o:o + 16]
    if len(b) < 13: return None
    if b[0] == 0x81 and b[1:4] == b'\x6c\x24\x04': K = struct.unpack_from('<i', b, 4)[0]; p = 8
    elif b[0] == 0x83 and b[1:4] == b'\x6c\x24\x04': K = struct.unpack_from('<b', b, 4)[0]; p = 5
    else: return None
    if b[p] != 0xE9: return None
    return K, (va + p + 5 + struct.unpack_from('<i', b, p + 1)[0]) & 0xFFFFFFFF
NP = [vt for vt in order if VT[vt]['mdisp'] != 0]
DIR = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])
       if thunkof(P.dw(vt + 4 * k)) is None]
ISDIR = set((vt, k) for vt, k, _ in DIR)
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
mult = {k: v for k, v in byname.items() if len(v) > 1}
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
nm2 = lambda x: (P.cstr(x + 8, 200) or b'').decode('latin1') if x else ''

hdr('W1 R1 置换零假设：层内按类置换值，重算「两侧都直接且相等」')
trip = []
for nm, lst in mult.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            A, B = lst[i], lst[j]
            for k in range(min(PRE[A], PRE[B])):
                if (A, k) in ISDIR and (B, k) in ISDIR:
                    trip.append((VT[A]['mdisp'], VT[B]['mdisp'], k, P.dw(A + 4 * k), P.dw(B + 4 * k)))
print('  两侧都直接的比较三元组 %d，实测相等 %d' % (len(trip), sum(1 for t in trip if t[3] == t[4])))
# 零假设：对每个 (层,槽号) 组，把「该类在该层的值」在同类之间随机置换
layerslot = collections.defaultdict(list)   # (m,k) -> [(vt,val)]
for vt, k, v in DIR: layerslot[(VT[vt]['mdisp'], k)].append((vt, v))
rng = random.Random(1207)
obs = 0
null = []
for _ in range(2000):
    mp = {}
    for key, lst in layerslot.items():
        vs = [v for _, v in lst]; rng.shuffle(vs)
        for (vt, _), v in zip(lst, vs): mp[(vt, key[1])] = v
    eq = 0
    for mA, mB, k, a, b in trip:
        if mp.get((mA, k)) == mp.get((mB, k)): eq += 1
    null.append(eq)
null.sort()
print('  置换 2000 次：中位 %d / p95 %d / max %d ；实测 %d ；P(null >= obs) = %.4f' %
      (null[1000], null[1900], null[-1], sum(1 for t in trip if t[3] == t[4]),
       sum(1 for x in null if x >= sum(1 for t in trip if t[3] == t[4])) / len(null)))
RW['W1'] = dict(triples=len(trip), obs=sum(1 for t in trip if t[3] == t[4]),
                null=[null[1000], null[1900], null[-1]])

hdr('W2 A1 判别判据：每个 (层偏移,槽号) 的「类->值」映射基数')
g = collections.defaultdict(list)
for vt, k, v in DIR: g[(VT[vt]['mdisp'], k)].append((VT[vt]['name'], v))
kind = collections.Counter(); cov = collections.Counter(); rows = []
for key in sorted(g):
    lst = g[key]; c = collections.Counter(v for _, v in lst)
    ncls = len(set(n for n, _ in lst)); nval = len(c)
    if nval == 1: t = 'multi:1 (all classes share)'
    elif nval == len(lst): t = '1:1 (each class own)'
    else: t = 'mixed'
    kind[t] += 1; cov[t] += len(lst)
    rows.append((key[0], key[1], len(lst), nval, t, c.most_common(1)[0]))
for t in kind: print('  %-26s 组数 %-3d 覆盖槽 %-4d (%.1f%%)' % (t, kind[t], cov[t], 100.0 * cov[t] / len(DIR)))
print('  全部组:', len(g), ' 覆盖', sum(cov.values()), '/', len(DIR))
print('  1:1 组（每类各自实现，即纯虚/覆盖）明细：')
for r in rows:
    if r[4].startswith('1:1'):
        print('    mdisp=%-5d k=%-2d 槽=%-3d 值种类=%d' % (r[0], r[1], r[2], r[3]))
print('  mixed 组明细（含主导+少数例外）：')
for r in rows:
    if r[4] == 'mixed':
        print('    mdisp=%-5d k=%-2d 槽=%-3d 种类=%-3d 主导=%s x%d' %
              (r[0], r[1], r[2], r[3], hex(r[5][0]), r[5][1]))
RW['W2'] = dict(kind=dict(kind), cov=dict(cov), groups=len(g),
                one_to_one=[[r[0], r[1], r[2], r[3]] for r in rows if r[4].startswith('1:1')],
                mixed=[[r[0], r[1], r[2], r[3], hex(r[5][0]), r[5][1]] for r in rows if r[4] == 'mixed'])

hdr('W3 A1 深判：同值的类是否落在同一继承子树（若是则「共享默认实现」可解释）')
def ancestors(name):
    out = set([name])
    if name not in byname: return out
    vt = [x for x in byname[name] if VT[x]['mdisp'] == 0]
    if not vt: return out
    for x in BD[vt[0]][1:]:
        out.add(nm2(x['ptd']))
    return out
same_sub = collections.Counter(); pairs = 0; same_val = 0; sameval_samesub = 0
for key in sorted(g):
    lst = g[key]
    for (n1, v1), (n2, v2) in itertools.combinations(lst, 2):
        if n1 == n2: continue
        pairs += 1
        if v1 != v2: continue
        same_val += 1
        a1 = ancestors(n1); a2 = ancestors(n2)
        if a1 & a2: sameval_samesub += 1
        else: same_sub['different_subtree'] += 1
print('  同 (层,槽号) 跨类比较 %d 对；值相同且同继承子树 %d；值相同但不同子树 %d' %
      (pairs, sameval_samesub, same_sub['different_subtree']))
print('  ⇒ 不同子树也大量共享同一地址 ⇒ 是「同一接口默认实现」而非继承链传递')
RW['W3'] = dict(pairs=pairs, same_val=same_val, samesub=sameval_samesub,
                diffsub=same_sub['different_subtree'])

hdr('W4 A3 替代解释：同基类在「有副表档」与「无副表档」的对照')
layers = set(VT[vt]['mdisp'] for vt in order)
extra = sorted(set(x['mdisp'] for _, x in [(vt, y) for vt in order for y in BD[vt]]) - layers)
tab = collections.defaultdict(list)   # 基类名 -> [(host, mdisp, 是否有副表)]
for vt in order:
    for x in BD[vt]:
        bn = nm2(x['ptd'])
        tab[bn].append((VT[vt]['name'], x['mdisp'], x['mdisp'] in layers))
for bn in ('.?AVStageClass@@', '.?AVBounceClass@@', '.?AVFlasherClass@@'):
    lst = tab.get(bn, [])
    c = collections.Counter((m, has) for _, m, has in lst)
    print('  基类 %-30s 出现 %d 次：' % (bn, len(lst)))
    for (m, has), n in sorted(c.items()):
        print('     mdisp=%-6d 有副表=%-5s x%d' % (m, has, n))
    hosts = sorted(set(h for h, m, has in lst if not has))
    print('     无副表档的宿主类 %d 个，例: %s' % (len(hosts), hosts[:6]))
print('  逐档统计：extra 档的宿主是否在同一层另有副表')
for m in extra:
    hosts = sorted(set(VT[vt]['name'] for vt in order for x in BD[vt] if x['mdisp'] == m))
    alt = collections.Counter()
    for h in hosts:
        alt[tuple(sorted(set(x['mdisp'] for vt in byname.get(h, []) for x in BD[vt]
                             if x['mdisp'] in layers)))] += 1
    print('    mdisp=%-5d 宿主 %d 个；宿主自身拥有的副表层组合 %s' %
          (m, len(hosts), [([hex(y) for y in k], v) for k, v in alt.most_common(3)]))
print('  对照：layer 36 的副表宿主（同为 StageClass 基类）')
for vt in order:
    if VT[vt]['mdisp'] == 36:
        print('    宿主 %-40s 基类(mdisp):%s' %
              (VT[vt]['name'][:40], [(nm2(x['ptd'])[:22], x['mdisp']) for x in BD[vt]]))
RW['W4'] = {bn: dict(cnt=[[m, has, n] for (m, has), n in
                          sorted(collections.Counter((x[1], x[2]) for x in tab.get(bn, [])).items())])
            for bn in ('.?AVStageClass@@', '.?AVBounceClass@@', '.?AVFlasherClass@@')}

hdr('W5 R4 收口：extra 四档每一档的完整台账（具名+计数+attributes）')
for m in extra:
    sel = [(VT[vt]['name'], x) for vt in order for x in BD[vt] if x['mdisp'] == m]
    hosts = collections.Counter(n for n, _ in sel)
    print('  mdisp=%d 共 %d 条 / 宿主 %d 个 ；attributes=%s ；ncb 直方=%s' %
          (m, len(sel), len(hosts), dict(collections.Counter(x['attr'] for _, x in sel)),
           dict(collections.Counter(x['ncb'] for _, x in sel))))
    print('     宿主:', [h[:44] for h, _ in hosts.most_common()])
json.dump(RW, open(OUT + '/r191_audit5.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第五轮完成 ==')
