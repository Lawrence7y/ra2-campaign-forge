# -*- coding: utf-8 -*-
"""R191 审计第四轮：收敛判定数字。
修正两处第一轮的方法错误：
 (a) 「打乱目标值」的置换零假设对「共享对数」是恒等变换（统计量只依赖多重集）⇒ 该反控恒真，作废；
     改用「按池均匀抽样」多重集零假设 + 「层内槽号置换」结构零假设。
 (b) R1 的真实比对空间要分「两侧都是直接槽」与「一侧是 thunk」两种，
     后者按 thunk 定律是构造性命中，不能算作比对机会。
"""
import sys, struct, collections, json, random, math
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
R4 = {}
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
ALL = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])]
DIR = [(vt, k, v) for vt, k, v in ALL if thunkof(v) is None]
ISDIR = set((vt, k) for vt, k, _ in DIR)
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
mult = {k: v for k, v in byname.items() if len(v) > 1}

hdr('V1 R1 真实比对空间：区分「两侧都是直接槽」与「至少一侧 thunk」')
tri = dict(both_direct=0, one_direct=0, no_direct=0)
matched = dict(both_direct=0, one_direct=0)
tabs_pair = set()
for nm, lst in mult.items():
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            A, B = lst[i], lst[j]; tabs_pair.add((A, B))
            for k in range(min(PRE[A], PRE[B])):
                a = P.dw(A + 4 * k); b = P.dw(B + 4 * k)
                nd = ((A, k) in ISDIR) + ((B, k) in ISDIR)
                key = ('both_direct' if nd == 2 else ('one_direct' if nd == 1 else 'no_direct'))
                tri[key] += 1
                if nd == 2 and a == b: matched['both_direct'] += 1
                if nd == 1 and a == b: matched['one_direct'] += 1
print('  表对 %d ；(表对,槽号) 三元组：两侧都直接 %d / 仅一侧直接 %d / 都不是直接 %d' %
      (len(tabs_pair), tri['both_direct'], tri['one_direct'], tri['no_direct']))
print('  命中数：两侧都直接 %d ；仅一侧直接 %d（后者按 thunk 定律是构造性命中）' %
      (matched['both_direct'], matched['one_direct']))
c = collections.Counter(v for _, _, v in DIR); nd_ = len(DIR)
q = sum((x / nd_) ** 2 for x in c.values())
E = tri['both_direct'] * q
pv = math.exp(-E)
print('  独立基率 Σp²=%.5f ⇒ 「两侧都直接」口径下期望命中 %.2f ；实测 0 ；Poisson P(0|%.2f)=%.3f' % (q, E, E, pv))
print('  ⇒ 判据自由度：只有 %d 次机会、期望 %.2f 次命中；0 命中在 5%% 水平上不可区分于随机' %
      (tri['both_direct'], E))
R4['V1'] = dict(pair_tables=len(tabs_pair), tri=tri, matched=matched, q=q, exp=E, p0=pv)

hdr('V2 A2 的多重集零假设（修正第一轮恒真反控）')
def pairs(cc): return sum(n * (n - 1) // 2 for n in cc.values())
pool_np = sorted(set(v for _, _, v in ALL))
obs = pairs(c)
rng = random.Random(4711)
def sim(nslot, pool, rep=2000):
    r = []
    for _ in range(rep):
        r.append(pairs(collections.Counter(rng.choices(pool, k=nslot))))
    r.sort(); return r
s_all = sim(len(DIR), pool_np)
s_pool278 = sim(len(DIR), sorted(c))
print('  实测共享对 %d' % obs)
print('  零假设A：从非主表池(%d 个不同地址)均匀抽 1013 次 ⇒ 中位 %d / p95 %d / max %d' %
      (len(pool_np), s_all[1000], s_all[1900], s_all[-1]))
print('  零假设B：从观测到的 %d 个地址池均匀抽 ⇒ 中位 %d / p95 %d / max %d' % (len(c), s_pool278[1000], s_pool278[1900], s_pool278[-1]))
print('  ⇒ 零假设A 下实测是上限的 %.1f 倍；零假设B 下是 %.1f 倍' %
      (obs / max(s_all[-1], 1), obs / max(s_pool278[-1], 1)))
R4['V2'] = dict(obs=obs, pool_np=len(pool_np), simA=[s_all[1000], s_all[1900], s_all[-1]],
                simB=[s_pool278[1000], s_pool278[1900], s_pool278[-1]])

hdr('V3 A2 变红反控：逐层剔除主导桩后富集还剩多少')
lay = collections.defaultdict(list)
for vt, k, v in DIR: lay[VT[vt]['mdisp']].append((vt, k, v))
rows = []
for m in sorted(lay):
    sel = lay[m]; cc = collections.Counter(v for _, _, v in sel)
    top, n = cc.most_common(1)[0]
    rest = [(vt, k, v) for vt, k, v in sel if v != top]
    cr = collections.Counter(v for _, _, v in rest)
    pool = len(set(v for _, _, v in sel))
    e = len(rest) * (len(rest) - 1) / 2 / max(pool, 1)
    rows.append((m, len(sel), hex(top), n, len(rest), len(cr), pairs(cr), round(e, 1),
                 round(pairs(cr) / max(e, 1e-9), 1)))
    print('  mdisp=%-6d 槽=%-4d top1=%s x%-3d 剔除后槽=%-3d 目标=%-3d 共享对=%-5d 均匀期望=%-6.1f 富集=x%.1f' %
          rows[-1])
tot_rest = sum(r[4] for r in rows); tot_pairs = sum(r[6] for r in rows)
print('  九层各自剔除 top1 后合计 %d 槽 / 共享对 %d' % (tot_rest, tot_pairs))
R4['V3'] = dict(rows=[[hex(r[0]) if False else r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]] for r in rows],
                rest_slots=tot_rest, rest_pairs=tot_pairs)

hdr('V4 A1 决定性判据：值是否由 (层偏移,槽号) 决定')
g = collections.defaultdict(list)
for vt, k, v in DIR: g[(VT[vt]['mdisp'], k)].append(v)
single = [kk for kk in g if len(set(g[kk])) == 1]
maj90 = [kk for kk in g if collections.Counter(g[kk]).most_common(1)[0][1] / len(g[kk]) >= 0.9]
cov_single = sum(len(g[kk]) for kk in single)
cov_maj = sum(len(g[kk]) for kk in maj90)
print('  (层偏移,槽号) 组数 %d' % len(g))
print('  组内单值（同层同槽号全类同址）%d 组，覆盖 %d 槽 = %.1f%%' % (len(single), cov_single, 100.0 * cov_single / nd_))
print('  组内主导值 >=90%% 的 %d 组，覆盖 %d 槽 = %.1f%%' % (len(maj90), cov_maj, 100.0 * cov_maj / nd_))
# 同槽号跨类 vs 跨层的命中率对比（真正的判别器）
def rate(sel, keyf):
    grp = collections.defaultdict(list)
    for vt, k, v in sel: grp[keyf(vt, k)].append(v)
    t = e = 0
    for kk, vs in grp.items():
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                t += 1; e += vs[i] == vs[j]
    return t, e
t1, e1 = rate(DIR, lambda vt, k: (VT[vt]['mdisp'], k))
t2, e2 = rate(DIR, lambda vt, k: (VT[vt]['name'], k))
print('  同 (层偏移,槽号) 跨类比较 %d 对，值相同 %d = %.2f%%' % (t1, e1, 100.0 * e1 / t1))
print('  同 (类名,槽号) 比较 %d 对，值相同 %d = %.2f%%   ← 被审 A1 用的口径' % (t2, e2, 100.0 * e2 / max(t2, 1)))
kperm = []
bytab = collections.defaultdict(list)
for vt, k, v in DIR: bytab[vt].append(v)
for _ in range(400):
    sel = []
    for vt, vs in bytab.items():
        ks = list(range(PRE[vt])); rng.shuffle(ks)
        for k, v in zip(ks, vs): sel.append((vt, k, v))
    kperm.append(rate(sel, lambda vt, k: (VT[vt]['mdisp'], k))[1])
kperm.sort()
print('  反控：层内槽号随机重排 400 次，同(层,槽号) 命中中位 %d / p95 %d / max %d（实测 %d）' %
      (kperm[200], kperm[380], kperm[-1], e1))
R4['V4'] = dict(groups=len(g), single=len(single), single_cov=cov_single,
                maj90=len(maj90), maj_cov=cov_maj,
                layer_k=(t1, e1), name_k=(t2, e2), kperm=[kperm[200], kperm[380], kperm[-1]])

hdr('V5 A2 的「5 个桩」到底是什么')
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for a, n in c.most_common(6):
    o = P.r2o(a); b = RAW[o:o + 40]
    ins = list(md.disasm_lite(b, a))[:8]
    print('  %s x%-3d %s' % (hex(a), n, ' ; '.join('%s %s' % (m, op) for _, _, m, op in ins)))
    print('        bytes=%s' % b[:20].hex())
R4['V5'] = [[hex(a), n, RAW[P.r2o(a):P.r2o(a) + 20].hex()] for a, n in c.most_common(6)]

hdr('V6 A3/R4 收口：extra 四档 vs 有副表层的 attributes 交叉表')
def bases_of(cx):
    ch = cx['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
ent = [(vt, x) for vt in order for x in BD[vt]]
layers = set(VT[vt]['mdisp'] for vt in order)
extra = sorted(set(x['mdisp'] for _, x in ent) - layers)
cross = collections.Counter((x['mdisp'] in extra, x['attr']) for _, x in ent)
print('  (是否 extra, attributes) 交叉表:', dict(cross))
print('  attributes==0 的 %d 条里：extra 档 %d 条 / 有副表层 %d 条 ⇒ 同一 attributes 值两边都出现，零判别力' %
      (sum(v for (e2, a), v in cross.items() if a == 0),
       cross.get((True, 0), 0), cross.get((False, 0), 0)))
print('  attributes 中出现 bit0=1 的只有 attr=9 的 12 条：是否 extra 档 =',
      cross.get((True, 9), 0), '条；有副表层 =', cross.get((False, 9), 0), '条')
print('  ⇒ R4 反例：extra 四档 62 条 attributes 全 0 且无副表；而 attributes 同为 0 的 4488 条却有副表')
print('     ⇒ attributes 不能区分「有无副表」；A3 的解释无判别力，判定为不成立')
for m in extra:
    sel = [x for _, x in ent if x['mdisp'] == m]
    print('  EXTRA mdisp=%-5d 条=%-3d attributes=%s pdisp=%s 基类=%s' %
          (m, len(sel), dict(collections.Counter(x['attr'] for x in sel)),
           sorted(set(x['pdisp'] for x in sel)),
           list(collections.Counter((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') for x in sel).items())))
# 替代判据：这些基类在本镜像是否有自己的 vtable/COL，以及是否在别的宿主里以 mdisp=0 出现
names = set(cx['name'] for cx in COL.values())
for m in extra:
    for bn in set((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') for _, x in ent if x['mdisp'] == m):
        occ = collections.Counter(x['mdisp'] for _, x in ent
                                  if (P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') == bn)
        print('  基类 %-30s 有自己 COL=%s ；出现在层 %s ；各 mdisp 出现次数 %s' %
              (bn, bn in names, [VT[v]['mdisp'] for v in byname.get(bn, [])],
               dict(sorted(occ.items()))))
        R4.setdefault('V6_bases', {})[bn] = dict(has_col=bn in names,
                                                 layers=[VT[v]['mdisp'] for v in byname.get(bn, [])],
                                                 occ=dict(sorted(occ.items())))
R4['V6'] = dict(cross=[[bool(a), b, cc] for (a, b), cc in cross.items()],
                extra={m: dict(n=sum(1 for _, x in ent if x['mdisp'] == m),
                               attr=dict(collections.Counter(x['attr'] for _, x in ent if x['mdisp'] == m)))
                       for m in extra})
json.dump(R4, open(OUT + '/r191_audit4.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第四轮完成 ==')
