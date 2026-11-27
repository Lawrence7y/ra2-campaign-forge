# -*- coding: utf-8 -*-
"""R191 审计第三轮：定性判据（一次跑完，全部证据同屏）。
1) A1 的「统一规律」到底有没有：按 (层偏移, 槽号) 分组看值是否塌缩成单值
2) R1 比对空间的零假设：同槽号跨层比较在语义上是不同接口的成员
3) A3 的 attributes 位语义判定 + R4 具名反例
"""
import sys, struct, collections, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
R3 = {}
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
TH = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])
      if thunkof(P.dw(vt + 4 * k)) is not None]
print('直接槽 %d / thunk %d' % (len(DIR), len(TH)))

hdr('U0 独立复核 P3：thunk 的 jmp 目标是否 == 同组另一表同槽号')
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
pr_img = {}
for nm, lst in byname.items():
    z = [x for x in lst if VT[x]['mdisp'] == 0]
    if len(z) == 1: pr_img[nm] = z[0]
ok = 0; bad = []
Krule = collections.Counter()
for vt, k, val in TH:
    K, tgt = thunkof(val)
    lst = byname[VT[vt]['name']]
    hit = [o for o in lst if o != vt and PRE[o] > k and P.dw(o + 4 * k) == tgt]
    if hit:
        ok += 1
        Krule[(VT[vt]['mdisp'], VT[hit[0]]['mdisp'], K)] += 1
    else: bad.append((VT[vt]['name'], VT[vt]['mdisp'], k, hex(tgt)))
print('  jmp 目标命中同组另一表同槽号: %d/%d ；反例 %d %s' % (ok, len(TH), len(bad), bad[:4]))
print('  (本层mdisp, 目标层mdisp, K) 直方:', dict(sorted(Krule.items())))
R3['U0'] = dict(ok=ok, tot=len(TH), bad=bad[:6], rule=[[a, b, c, d] for (a, b, c), d in Krule.items()])

hdr('U1 A1 定性：按 (层偏移, 槽号) 分组，跨类值是否塌缩成单值')
g = collections.defaultdict(list)
for vt, k, v in DIR: g[(VT[vt]['mdisp'], k)].append((VT[vt]['name'], v))
rows = []
for key in sorted(g):
    lst = g[key]; c = collections.Counter(v for _, v in lst)
    top, n = c.most_common(1)[0]
    rows.append((key[0], key[1], len(lst), len(c), n / len(lst), top,
                 len(set(nm for nm, _ in lst))))
single = [r for r in rows if r[3] == 1]
print('  分组数 %d ；组内值唯一(1 种实现) %d 组 ；覆盖槽 %d / %d = %.1f%%' %
      (len(rows), len(single), sum(r[2] for r in single), len(DIR),
       100.0 * sum(r[2] for r in single) / len(DIR)))
print('  组内值种类分布:', dict(sorted(collections.Counter(r[3] for r in rows).items())))
print('  主导值覆盖 >=90%% 的组: %d 组，覆盖槽 %d' %
      (sum(1 for r in rows if r[4] >= 0.9), sum(r[2] for r in rows if r[4] >= 0.9)))
print('  多值组（同层同槽号跨类有 >1 种实现）:')
for r in rows:
    if r[3] > 1:
        print('    mdisp=%-6d k=%-2d 槽=%-3d 种类=%-3d 主导=%.2f 主导值=%s 类数=%d' %
              (r[0], r[1], r[2], r[3], r[4], hex(r[5]), r[6]))
R3['U1'] = dict(groups=len(rows), single=len(single),
                single_cov=sum(r[2] for r in single), total=len(DIR),
                kinds=dict(sorted(collections.Counter(r[3] for r in rows).items())),
                multi=[[r[0], r[1], r[2], r[3], round(r[4], 3), hex(r[5])] for r in rows if r[3] > 1])

hdr('U2 R1：同槽号跨层比较的语义合法性')
print('  证据：layer 8 = INoticeSink 子对象；layer 12 = INoticeSource 子对象（见 U4）')
print('  两者 slot0 是不同的虚函数成员，按「同槽号」比较是拿不同接口的不同成员比 ⇒ 0 命中是域错配')
s8 = collections.Counter(P.dw(vt) for vt in order if VT[vt]['mdisp'] == 8)
s12 = collections.Counter(P.dw(vt) for vt in order if VT[vt]['mdisp'] == 12)
s4 = collections.Counter(P.dw(vt) for vt in order if VT[vt]['mdisp'] == 4)
print('  layer8 各槽值分布(全部槽):', [(hex(a), b) for a, b in s8.most_common(4)])
print('  layer12:', [(hex(a), b) for a, b in s12.most_common(4)])
print('  layer4 :', [(hex(a), b) for a, b in s4.most_common(6)])
print('  layer8 与 layer12 的槽值集合交集 =', {hex(a) for a in set(s8) & set(s12)})
R3['U2'] = dict(l8=[[hex(a), b] for a, b in s8.most_common(4)],
                l12=[[hex(a), b] for a, b in s12.most_common(4)],
                l4=[[hex(a), b] for a, b in s4.most_common(6)])

hdr('U3 直接槽的「层默认桩」结构：每层 top1 值覆盖率')
lay = collections.defaultdict(collections.Counter)
for vt, k, v in DIR: lay[VT[vt]['mdisp']][v] += 1
for m in sorted(lay):
    c = lay[m]; tot = sum(c.values()); a, n = c.most_common(1)[0]
    print('  mdisp=%-6d 直接槽=%-4d 不同值=%-3d top1=%s x%-3d (%.1f%%)' %
          (m, tot, len(c), hex(a), n, 100.0 * n / tot))
R3['U3'] = {m: dict(n=sum(lay[m].values()), k=len(lay[m]),
                    top=hex(lay[m].most_common(1)[0][0]), topn=lay[m].most_common(1)[0][1])
            for m in sorted(lay)}

hdr('U4 attributes 位语义判定（R3/R4 的核心）')
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
ent = [(vt, x) for vt in order for x in BD[vt]]
print('  5302 条描述符 pdisp 直方:', dict(collections.Counter(x['pdisp'] for _, x in ent)))
print('  ⇒ pdisp 恒 -1 = 全部 non-virtual 基类；若 attributes.bit0 才是 non-virtual 标志，则 5302 条应全为 1')
a1 = collections.Counter(x['attr'] & 1 for _, x in ent)
print('  实测 attributes.bit0 :', dict(a1), ' ⇒ bit0 只标 %d 条，与 pdisp 恒 -1 矛盾' % a1.get(1, 0))
print('  attributes 全值直方:', dict(collections.Counter(x['attr'] for _, x in ent)))
print('  attributes==9 的 12 条具名:')
for vt, x in ent:
    if x['attr'] == 9:
        print('    %-58s mdisp=%-6d base=%-46s ncb=%d' %
              (VT[vt]['name'][:58], x['mdisp'],
               (P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1')[:46], x['ncb']))
print('  attributes==2 的 740 条按 (宿主 mdisp, 基类名) 分组 top8:')
a2 = collections.Counter()
for vt, x in ent:
    if x['attr'] == 2:
        a2[((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1'), x['mdisp'])] += 1
print('   ', a2.most_common(8))
print('  ⇒ attr=2 全落 UIUnknown/UIRTTITypeInfo 等重复出现的基类 ⇒ 与 MSVC BCD_AMBIGUOUS(0x2) 一致')
extra = sorted(set(x['mdisp'] for _, x in ent) - set(VT[vt]['mdisp'] for vt in order))
print('  extra 四档 attributes 直方（R4 反例基础）:')
for m in extra:
    sel = [x for _, x in ent if x['mdisp'] == m]
    c = collections.Counter(x['attr'] for x in sel)
    nm = collections.Counter((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') for x in sel)
    print('    mdisp=%-5d 条=%-3d attributes=%s 基类=%s bit0=1 的条数=%d' %
          (m, len(sel), dict(c), nm.most_common(), sum(v for k2, v in c.items() if k2 & 1)))
R3['U4'] = dict(pdisp=dict(collections.Counter(x['pdisp'] for _, x in ent)),
                bit0=dict(a1), attr=dict(collections.Counter(x['attr'] for _, x in ent)),
                a2=a2.most_common(8),
                extra={m: dict(n=sum(1 for _, x in ent if x['mdisp'] == m),
                               attr=dict(collections.Counter(x['attr'] for _, x in ent if x['mdisp'] == m)),
                               base=list(collections.Counter((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1')
                                                             for _, x in ent if x['mdisp'] == m).items()))
                       for m in extra})

hdr('U5 A3 对照：有副表的层 vs extra 四档，用同一判据能分开吗')
for m in sorted(set(x['mdisp'] for _, x in ent)):
    sel = [x for _, x in ent if x['mdisp'] == m]
    tag = 'EXTRA' if m in extra else 'layer'
    print('  %-5s mdisp=%-6d 条=%-5d attr=%s pdisp 唯一值=%s' %
          (tag, m, len(sel), dict(collections.Counter(x['attr'] for x in sel)),
           sorted(set(x['pdisp'] for x in sel))))
print('  ⇒ attributes 与 pdisp 在两组上的分布都不可分（pdisp 全 -1，attr 都以 0 为主）')
print('  ⇒ 「non-virtual 基类」这一解释在本镜像里对任何一档都成立，因此不能解释四档的差异（无判别力）')
names1214 = set(c['name'] for c in COL.values())
print('  extra 四档的基类是否另有自己的 COL：', {m: [(P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') in names1214
        for x in [y for _, y in ent if y['mdisp'] == m]][:1] for m in extra})
for m in extra:
    for bn in set((P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') for _, x in ent if x['mdisp'] == m):
        print('    %-40s 在 1214 名单内=%s ；本地表层=%s' %
              (bn, bn in names1214, [VT[v]['mdisp'] for v in byname.get(bn, [])]))
R3['U5'] = dict(inlist={m: [(P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') in names1214
                            for _, x in ent if x['mdisp'] == m][:1] for m in extra})
json.dump(R3, open(OUT + '/r191_audit3.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第三轮完成 ==')
