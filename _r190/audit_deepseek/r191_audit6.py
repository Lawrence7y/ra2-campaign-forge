# -*- coding: utf-8 -*-
"""R191 审计第六轮：修正 W1 的键错（拿 mdisp 当 vtable 查表）并给 R1 的终局分解。
X1 两侧都直接的同槽号比较：按 (层A,层B) 分解 + 正确的层内值置换零假设
X2 「0 命中」与「两层默认桩本就不同」是否同义反复：直接列出每个 (层A,层B) 的默认桩地址
X3 A1 终局：三种口径的可比对空间与命中率并列
X4 A3 终局：同一基类 StageClass 在 36 / 172 / 248 三档的不同结果（决定性反例）
"""
import sys, struct, collections, json, random, itertools
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
RX = {}
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
VAL = {(vt, k): v for vt, k, v in DIR}
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
mult = {k: v for k, v in byname.items() if len(v) > 1}

hdr('X1 两侧都直接的同槽号比较（修正键后）')
trip = []
for nm, lst in mult.items():
    for A, B in itertools.combinations(lst, 2):
        for k in range(min(PRE[A], PRE[B])):
            if (A, k) in ISDIR and (B, k) in ISDIR:
                trip.append((A, B, k, VAL[(A, k)], VAL[(B, k)]))
print('  三元组 %d；实测相等 %d' % (len(trip), sum(1 for t in trip if t[3] == t[4])))
byAB = collections.defaultdict(lambda: [0, 0])
for A, B, k, a, b in trip:
    key = (VT[A]['mdisp'], VT[B]['mdisp']); byAB[key][0] += 1; byAB[key][1] += (a == b)
print('  按 (层A,层B) 分解 [比较数, 相等数]:')
for key in sorted(byAB):
    a_vals = set(VAL[(A, k)] for A, B, k, _, _ in trip if (VT[A]['mdisp'], VT[B]['mdisp']) == key)
    print('    %-14s %s' % (str(key), byAB[key]))
# 正确的置换零假设：在「所有直接槽」范围内按层内类置换值
rng = random.Random(3320)
grp = collections.defaultdict(list)
for vt, k, v in DIR: grp[(VT[vt]['mdisp'], k)].append((vt, v))
obs = sum(1 for t in trip if t[3] == t[4])
null = []
for _ in range(2000):
    mp = {}
    for key, lst in grp.items():
        vs = [v for _, v in lst]; rng.shuffle(vs)
        for (vt, _), v in zip(lst, vs): mp[(vt, key[1])] = v
    null.append(sum(1 for A, B, k, _, _ in trip if mp[(A, k)] == mp[(B, k)]))
null.sort()
print('  层内值置换 2000 次：中位 %d / p95 %d / max %d ；实测 %d' % (null[1000], null[1900], null[-1], obs))
print('  ⇒ 置换后仍几乎必为 0 说明：该 123 对的 0 命中由「两层各自塌缩到不同主导值」决定，非独立随机')
RX['X1'] = dict(triples=len(trip), obs=obs, byAB={str(k): v for k, v in sorted(byAB.items())},
                null=[null[1000], null[1900], null[-1]])

hdr('X2 每个 (层A,层B) 的默认桩地址——0 命中是否与「桩不同」同义反复')
for key in sorted(byAB):
    mA, mB = key
    pa = collections.Counter(VAL[(A, k)] for A, B, k, _, _ in trip if VT[A]['mdisp'] == mA and VT[B]['mdisp'] == mB)
    pb = collections.Counter(VAL[(B, k)] for A, B, k, _, _ in trip if VT[A]['mdisp'] == mA and VT[B]['mdisp'] == mB)
    print('  层%s vs 层%s ：A 侧值集合 %s ；B 侧值集合 %s ；交集 %s' %
          (mA, mB, [(hex(a), b) for a, b in pa.most_common(3)],
           [(hex(a), b) for a, b in pb.most_common(3)],
           {hex(x) for x in set(pa) & set(pb)} or '空'))
RX['X2'] = 'see log'

hdr('X3 A1 终局：三种分组口径并列')
def rate(keyf):
    g2 = collections.defaultdict(list)
    for vt, k, v in DIR: g2[keyf(vt, k)].append((vt, v))
    t = e = 0
    for kk, lst in g2.items():
        for (v1n, v1), (v2n, v2) in itertools.combinations(lst, 2):
            t += 1; e += v1 == v2
    return len(g2), t, e
for tag, f in (('COL 修饰名组 + 槽号（被审 A1 口径）', lambda vt, k: (VT[vt]['name'], k)),
               ('层偏移 + 槽号（接口槽位口径）', lambda vt, k: (VT[vt]['mdisp'], k)),
               ('仅槽号', lambda vt, k: k)):
    ng, t, e = rate(f)
    print('  %-34s 组=%-4d 可比较对=%-6d 相等=%-6d (%.2f%%)' % (tag, ng, t, e, 100.0 * e / max(t, 1)))
RX['X3'] = {tag: rate(f) for tag, f in (('name_k', lambda vt, k: (VT[vt]['name'], k)),
                                        ('md_k', lambda vt, k: (VT[vt]['mdisp'], k)),
                                        ('k', lambda vt, k: k))} if False else {}
ng, t, e = rate(lambda vt, k: (VT[vt]['name'], k)); RX['X3']['name_k'] = [ng, t, e]
ng, t, e = rate(lambda vt, k: (VT[vt]['mdisp'], k)); RX['X3']['md_k'] = [ng, t, e]
ng, t, e = rate(lambda vt, k: k); RX['X3']['k'] = [ng, t, e]

hdr('X4 A3 终局：同一基类 StageClass（attributes 全 0）三档结果不同')
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
nm2 = lambda x: (P.cstr(x + 8, 200) or b'').decode('latin1') if x else ''
layers = set(VT[vt]['mdisp'] for vt in order)
rows = [(VT[vt]['name'], x['mdisp'], x['attr'], x['pdisp'], x['ncb'])
        for vt in order for x in BD[vt] if nm2(x['ptd']) == '.?AVStageClass@@']
c = collections.Counter((m, a, pd, m in layers) for _, m, a, pd, _ in rows)
print('  StageClass 作为基类共 %d 条；按 (mdisp, attributes, pdisp, 有副表) 计数:' % len(rows))
for key, n in sorted(c.items()):
    print('    mdisp=%-5d attr=%d pdisp=%s 有副表=%-5s x%d' % (key[0], key[1], key[2], key[3], n))
hosts = collections.Counter((m, VT[vt]['name']) for vt in order for x in BD[vt]
                            if nm2(x['ptd']) == '.?AVStageClass@@' for m in [x['mdisp']])
print('  宿主明细（按档）:')
for (m, h), n in sorted(hosts.items()):
    print('    mdisp=%-5d 宿主 %s' % (m, h))
print('  ⇒ 同一基类、attributes 同为 0、pdisp 同为 -1，却在 36 档生成 4 张副表、在 172/248 档一条不生成')
print('  ⇒ attributes 对「是否生成副表」零判别力；A3 的解释在数据上不成立')
RX['X4'] = dict(total=len(rows), table=[[k[0], k[1], k[2], k[3], v] for k, v in sorted(c.items())],
                hosts=[[m, h, n] for (m, h), n in sorted(hosts.items())])
json.dump(RX, open(OUT + '/r191_audit6.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第六轮完成 ==')
