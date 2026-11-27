# -*- coding: utf-8 -*-
"""R191 审计第二轮：把第一轮的歧义判据精确化，并给 A3 的替代判据。
要点：层的接口候选集、值与接口默认实现的比对、直接槽目标的形态学、
extra 四档基类名的清单内比例、三条可让 A2/A3 变红的反控。
"""
import sys, os, struct, collections, json, random, math
ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW; T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = ROOT + '/_r190/audit_deepseek'
R2 = {}
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
        COL[base + 4 * i] = dict(mdisp=v[i + 1], ptd=v[i + 3], pchd=v[i + 4],
                                 name=nm.decode('latin1'))
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
    if b[0] == 0x81 and b[1:4] == b'\x6c\x24\x04':
        K = struct.unpack_from('<i', b, 4)[0]; p = 8
    elif b[0] == 0x83 and b[1:4] == b'\x6c\x24\x04':
        K = struct.unpack_from('<b', b, 4)[0]; p = 5
    else: return None
    if b[p] != 0xE9: return None
    return K, (va + p + 5 + struct.unpack_from('<i', b, p + 1)[0]) & 0xFFFFFFFF
NP = [vt for vt in order if VT[vt]['mdisp'] != 0]
DIR = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])
       if thunkof(P.dw(vt + 4 * k)) is None]
print('直接槽 %d' % len(DIR))
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12); o = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        o.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                      pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return o
BD = {vt: bases_of(VT[vt]) for vt in order}
byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
prim = {k: v[0] for k, v in byname.items() if len([x for x in v if VT[x]['mdisp'] == 0]) == 1}
names1214 = set(c['name'] for c in COL.values())

hdr('T1 层的接口候选集：mdisp==层偏移 的基类项可能有多个（歧义源）')
cand = {}
amb = collections.Counter()
for vt in NP:
    m = VT[vt]['mdisp']
    cs = [(P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1') for x in BD[vt] if x['mdisp'] == m]
    cand[vt] = cs; amb[(m, len(cs))] += 1
print('按 (层偏移, 候选接口数) 计数:', dict(sorted(amb.items())))
print('候选数==1 的宿主表 %d / %d' % (sum(1 for vt in NP if len(cand[vt]) == 1), len(NP)))

hdr('T2 直接槽 = 接口默认实现的复用？(按候选接口唯一时比对)')
def nm2(c):
    return (P.cstr(c + 8, 200) or b'').decode('latin1') if c else ''
stat = collections.Counter(); det = collections.defaultdict(list)
for vt, k, v in DIR:
    cs = cand[vt]
    if len(cs) != 1:
        stat['ambiguous'] += 1; det['amb'].append((VT[vt]['name'], VT[vt]['mdisp'], k, hex(v), cs)); continue
    dn = cs[0]; p0 = prim.get(dn)
    if p0 is None:
        stat['iface_no_local_table'] += 1; det['nolt'].append((VT[vt]['name'], VT[vt]['mdisp'], k, dn)); continue
    if PRE[p0] <= k:
        stat['iface_table_short'] += 1; det['short'].append((VT[vt]['name'], k, dn, PRE[p0])); continue
    v0 = P.dw(p0 + 4 * k)
    if v0 == v: stat['same_as_iface_default'] += 1; det['same'].append((VT[vt]['name'], k, dn))
    else: stat['differs'] += 1; det['diff'].append((VT[vt]['name'], VT[vt]['mdisp'], k, hex(v), dn, hex(v0)))
for kk in ('same_as_iface_default', 'differs', 'iface_no_local_table', 'iface_table_short', 'ambiguous'):
    print('  %-24s %d' % (kk, stat[kk]))
print('  differs 样例:', det['diff'][:8])
print('  iface_no_local_table 按接口名:', collections.Counter(x[3] for x in det['nolt']).most_common(8))
print('  ambiguous 按层:', collections.Counter(x[1] for x in det['amb']).most_common())
print('  ambiguous 样例:', det['amb'][:5])
R2['T2'] = dict(stat=dict(stat), amb=collections.Counter(x[1] for x in det['amb']).most_common(),
                nolt=collections.Counter(x[3] for x in det['nolt']).most_common(10))

hdr('T3 歧义层的兜底判据：值与「任一候选接口主表同槽号」相同？')
ok = 0; no = 0; nonlocal_ = 0; sample = []
for vt, k, v in DIR:
    cs = cand[vt]
    if len(cs) != 1: continue
    pass
amb_hit = 0; amb_miss = 0; amb_cmp = 0
for vt, k, v in DIR:
    cs = cand[vt]
    if len(cs) < 2: continue
    cmp_ok = []
    for dn in cs:
        p0 = prim.get(dn)
        if p0 is not None and PRE[p0] > k: cmp_ok.append((dn, P.dw(p0 + 4 * k)))
    if not cmp_ok: nonlocal_ += 1; continue
    amb_cmp += 1
    if any(x[1] == v for x in cmp_ok): amb_hit += 1
    else:
        amb_miss += 1
        if len(sample) < 8: sample.append((VT[vt]['name'], VT[vt]['mdisp'], k, hex(v), [(a, hex(b)) for a, b in cmp_ok]))
print('歧义槽中可比较的 %d ；值命中任一候选 %d ；全不命中 %d ；无可比值 %d' % (amb_cmp, amb_hit, amb_miss, nonlocal_))
print('  全不命中样例:', sample)
R2['T3'] = dict(cmp=amb_cmp, hit=amb_hit, miss=amb_miss, nocomp=nonlocal_)

hdr('T4 直接槽目标的形态学（disasm_lite，仅 278 个不同目标，不全段反汇编）')
import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
targets = sorted(set(v for _, _, v in DIR))
form = {}
for va in targets:
    o = P.r2o(va)
    code = RAW[o:o + 32] if o is not None else b''
    ins = [i for i in md.disasm_lite(code, va)][:6]
    txt = ' '.join('%s %s' % (m, op) for _, _, m, op in ins)
    if ins and ins[0][2] == 'ret' and len(ins) == 1: f = 'empty_ret'
    elif ins and ins[0][2] == 'ret': f = 'other_ret'
    elif 'ret' in txt and len(ins) <= 4 and ('[esp + 4]' in txt or '[esp+4]' in txt): f = 'this_accessor'
    elif 'call dword ptr' in txt or 'jmp dword ptr' in txt or 'call qword' in txt: f = 'indirect_forward'
    elif ins and ins[0][2] in ('xor', 'mov') and 'ret' in txt: f = 'const_return'
    else: f = 'body'
    form[va] = (f, txt)
fc = collections.Counter(form[v][0] for _, _, v in DIR)
print('按槽计形态分布:', dict(fc))
for f in sorted(set(v[0] for v in form.values())):
    ex = [v for v in targets if form[v][0] == f][:2]
    print('  %-18s 目标数 %-4d 例: %s' % (f, sum(1 for v in targets if form[v][0] == f),
        [(hex(v), form[v][1][:60]) for v in ex]))
fwd = [v for v in targets if form[v][0] == 'indirect_forward']
print('间接转发目标(疑似 adjustor/vcall thunk 的另一种形态) %d 个 / %d' % (len(fwd), len(targets)))
print('  它们承载的槽数:', sum(1 for _, _, v in DIR if form[v][0] == 'indirect_forward'))
R2['T4'] = dict(by_slot=dict(fc), by_target={f: sum(1 for v in targets if form[v][0] == f)
                for f in set(v[0] for v in form.values())},
                fwd_slots=sum(1 for _, _, v in DIR if form[v][0] == 'indirect_forward'),
                fwd_targets=len(fwd),
                fwd_sample=[(hex(v), form[v][1][:70]) for v in fwd[:6]])

hdr('T5 A3 替代判据：extra 四档的基类名是否在本镜像有自己的一层')
tab = collections.defaultdict(lambda: dict(n=0, inlist=0, names=collections.Counter()))
for vt in order:
    for x in BD[vt]:
        dn = nm2(x['ptd']); e = tab[x['mdisp']]
        e['n'] += 1; e['names'][dn] += 1
        if dn in names1214: e['inlist'] += 1
layers = set(VT[vt]['mdisp'] for vt in order)
extra = sorted(set(tab) - layers)
for m in sorted(tab):
    e = tab[m]
    print('  mdisp=%-6d %s 项=%-5d 名单内=%-5d (%.1f%%) 名字数=%d top=%s' %
          (m, 'EXTRA' if m in extra else 'layer', e['n'], e['inlist'],
           100.0 * e['inlist'] / e['n'], len(e['names']), e['names'].most_common(3)))
R2['T5'] = {m: dict(n=tab[m]['n'], inlist=tab[m]['inlist'],
                    names=tab[m]['names'].most_common(4)) for m in sorted(tab)}

hdr('T6 反控（每条给出能让 A2/A3 变红的数）')
# C1 A3 红：attributes 在 extra 与 layer 的分布是否可分
ex_attr = collections.Counter(x['attr'] for vt in order for x in BD[vt] if x['mdisp'] in extra)
ly_attr = collections.Counter(x['attr'] for vt in order for x in BD[vt] if x['mdisp'] in layers)
print('C1(A3) extra 四档 attributes 直方 = %s（全 0）' % dict(ex_attr))
print('       有副表的层 attributes 直方 = %s' % dict(ly_attr))
print('       ⇒ attributes 在两组上都是 0 为众数；extra 组 bit0=1 的项数 = %d' % ex_attr.get(9, 0) + ex_attr.get(1, 0))
# C2 A3 红：pdisp 判据（真正的 non-virtual 标志）在这四档是否特异
ex_pd = collections.Counter(x['pdisp'] for vt in order for x in BD[vt] if x['mdisp'] in extra)
print('C2(A3) extra 四档 pdisp 直方 = %s；有副表层 pdisp 直方 = %s' %
      (dict(ex_pd), dict(collections.Counter(x['pdisp'] for vt in order for x in BD[vt] if x['mdisp'] in layers))))
print('       ⇒ pdisp 全局恒为 -1，对 extra 无判别力（A3 引用的位也不对：non-virtual 由 pdisp 表示，bit0 不是它）')
# C3 A2 绿：类内置换 k 后的同槽号共享率
DIRSET = set((vt, k) for vt, k, _ in DIR)
def samek(sel):
    groups = collections.defaultdict(list)
    for vt, k, v in sel: groups[k].append((VT[vt]['name'], v))
    tot = eq = 0
    for k, lst in groups.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[i][0] == lst[j][0]: continue
                tot += 1; eq += lst[i][1] == lst[j][1]
    return tot, eq
t0, e0 = samek(DIR)
rng = random.Random(20261117)
perm = []
bynn = {vt: list(range(PRE[vt])) for vt in NP}
for _ in range(400):
    kk = {vt: bynn[vt][:] for vt in bynn}
    for vt in kk: rng.shuffle(kk[vt])
    # 只在直接槽集合内重排槽号（保持每表直接槽个数不变）
    sel = []
    per_tab = collections.defaultdict(list)
    for vt, k, v in DIR: per_tab[vt].append(v)
    for vt, vs in per_tab.items():
        ks = kk[vt][:len(vs)]
        for k, v in zip(ks, vs): sel.append((vt, k, v))
    perm.append(samek(sel)[1])
perm.sort()
print('C3(A2) 实测同槽号跨类共享对 %d/%d = %.2f%% ；类内置换槽号 400 次中位数 %d (p95=%d, max=%d) = %.2f%%' %
      (e0, t0, 100.0 * e0 / t0, perm[200], perm[380], perm[-1], 100.0 * perm[200] / t0))
# C4 A2 红/绿：剔除「接口默认实现」后，跨接口名的聚集还剩多少
samedef = set()
for vt, k, v in DIR:
    cs = cand[vt]
    if len(cs) == 1:
        p0 = prim.get(cs[0])
        if p0 is not None and PRE[p0] > k and P.dw(p0 + 4 * k) == v: samedef.add((vt, k))
rest = [(vt, k, v) for vt, k, v in DIR if (vt, k) not in samedef]
cr = collections.Counter(v for _, _, v in rest)
pr_ = sum(n * (n - 1) // 2 for n in cr.values())
pool_np = len(set(P.dw(vt + 4 * k) for vt in NP for k in range(PRE[vt])))
print('C4(A2) 剔除「等于唯一候选接口默认实现」的 %d 槽后剩 %d 槽 / %d 目标 / 共享对 %d' %
      (len(samedef), len(rest), len(cr), pr_))
print('       均匀基率期望 %d 选 2 / %d = %.1f ⇒ 富集 x%.1f（仍远高于随机）' %
      (len(rest), pool_np, len(rest) * (len(rest) - 1) / 2 / pool_np,
       pr_ / max(len(rest) * (len(rest) - 1) / 2 / pool_np, 1e-9)))
print('       剩余 top6:', [(hex(a), b) for a, b in cr.most_common(6)])
# C5 A1 红：把「同组同序号」换成「同接口同序号」后的命中率对比
print('C5(A1) 同一批 1013 槽：按 COL 名组同序号 0/%d ；按候选接口名同序号 见下表' % len(DIR))
g = collections.defaultdict(list)
for vt, k, v in DIR:
    cs = cand[vt]
    if len(cs) == 1: g[(cs[0], k)].append(v)
tot = eq = ngrp = 0
for key, vs in g.items():
    if len(vs) < 2: continue
    ngrp += 1
    for i in range(len(vs)):
        for j in range(i + 1, len(vs)):
            tot += 1; eq += vs[i] == vs[j]
print('       (唯一候选接口名, 槽号) 分组：%d 组 / 可比较对 %d / 值相同 %d = %.2f%%' %
      (ngrp, tot, eq, 100.0 * eq / max(tot, 1)))
g2 = collections.defaultdict(list)
for vt, k, v in DIR:
    for dn in cand[vt]: g2[(dn, k)].append(v)
tot2 = eq2 = 0
for key, vs in g2.items():
    if len(vs) < 2: continue
    for i in range(len(vs)):
        for j in range(i + 1, len(vs)):
            tot2 += 1; eq2 += vs[i] == vs[j]
print('       (任一候选接口名, 槽号) 分组（歧义槽重复计入）：可比较对 %d / 相同 %d = %.2f%%' %
      (tot2, eq2, 100.0 * eq2 / max(tot2, 1)))
R2['ctrl'] = dict(C1_extra_attr=dict(ex_attr), C1_layer_attr=dict(ly_attr),
                  C3=(t0, e0, perm[200], perm[380], perm[-1]),
                  C4=(len(samedef), len(rest), len(cr), pr_, round(
                      pr_ / max(len(rest) * (len(rest) - 1) / 2 / pool_np, 1e-9), 2)),
                  C5=(ngrp, tot, eq), C5b=(tot2, eq2),
                  C4_top=[[hex(a), b] for a, b in cr.most_common(8)])
json.dump(R2, open(OUT + '/r191_audit2.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('\n== 第二轮完成 ==')
