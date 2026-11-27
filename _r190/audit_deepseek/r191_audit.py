# -*- coding: utf-8 -*-
"""R191 跨家族审计（deepseek）：对 A1/A2/A3 与 R1..R4 的独立复核。
判据全部自写：不使用 _r190 的任何辅助函数，thunk 形态用纯字节匹配，
基类实现对照用 RTTI 自项链，不用被审脚本的分组口径。
只读 ra2bench/gamemd.exe，产物只落本目录。
"""
import sys, os, struct, collections, json, random, hashlib, math

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, ROOT + '/_r185')
import pe185 as P
RAW = P.RAW
T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
OUT = os.path.join(ROOT, '_r190/audit_deepseek')
os.makedirs(OUT, exist_ok=True)
R = {}
def pr(*a): print(*a)
def hdr(s): pr('\n==== ' + s + ' ====')

hdr('S0 独立重算底账（不引用 _r190 的任何中间量）')
SECV = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; n = s['rawsize'] // 4
    SECV[sec] = (s['lo'], struct.unpack_from('<%dI' % n, RAW, s['rawptr']), n)

name_ok = lambda nm: bool(nm) and nm.startswith(b'.?A') and nm.endswith(b'@@')
COL = {}          # colva -> dict
RELAX = []        # 放宽判据下的 COL 样元组
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(n - 4):
        d0, d1, d2, d3, d4 = v[i], v[i + 1], v[i + 2], v[i + 3], v[i + 4]
        if d0 not in (0, 1): continue
        if P.where(d3) != '.data': continue
        nm = P.cstr(d3 + 8, 200)
        if not name_ok(nm): continue
        b = base + 4 * i
        RELAX.append(dict(at=b, mdisp=d1, d2=d2, d4=d4, ok2=(d2 == 0),
                          ok4=(P.where(d4) == '.rdata'), name=nm.decode('latin1')))
        if d2 == 0 and P.where(d4) == '.rdata':
            COL[b] = dict(mdisp=d1, ptd=d3, pchd=d4, name=nm.decode('latin1'))
VT = {}
for sec in ('.rdata', '.data'):
    base, v, n = SECV[sec]
    for i in range(1, n):
        if not (LO <= v[i] < HI): continue
        b = base + 4 * i
        c = v[i - 1]
        if c in COL: VT[b] = COL[c]
def pre(vt):
    k = 0
    while True:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): return k
        k += 1
PRE = {vt: pre(vt) for vt in VT}
order = sorted(VT)
pr('COL(strict)=%d  COL(relaxed)=%d  VT=%d  slots=%d' %
   (len(COL), len(RELAX), len(VT), sum(PRE.values())))
pr('strict COL 地址集合 == VT 的 colptr 集合 :', set(COL) == set(P.dw(vt - 4) for vt in order))
R['base'] = dict(col=len(COL), col_relax=len(RELAX), vt=len(VT), slots=sum(PRE.values()))

def thunkof(va):
    o = P.r2o(va)
    if o is None: return None
    b = RAW[o:o + 16]
    if len(b) < 13: return None
    if b[0] == 0x81 and b[1] == 0x6C and b[2] == 0x24 and b[3] == 0x04:
        K = struct.unpack_from('<i', b, 4)[0]; p = 8
    elif b[0] == 0x83 and b[1] == 0x6C and b[2] == 0x24 and b[3] == 0x04:
        K = struct.unpack_from('<b', b, 4)[0]; p = 5
    else:
        return None
    if b[p] != 0xE9: return None
    rel = struct.unpack_from('<i', b, p + 1)[0]
    return K, (va + p + 5 + rel) & 0xFFFFFFFF

NP = [vt for vt in order if VT[vt]['mdisp'] != 0]
nz_slots = [(vt, k, P.dw(vt + 4 * k)) for vt in NP for k in range(PRE[vt])]
TH = {vt: [] for vt in NP}
DIR = []
for vt, k, val in nz_slots:
    th = thunkof(val)
    if th is None: DIR.append((vt, k, val))
    else: TH[vt].append((k, val, th[0], th[1]))
nth = sum(len(v) for v in TH.values())
pr('非主表槽 %d = thunk %d + 直接 %d' % (len(nz_slots), nth, len(DIR)))
Khist = collections.Counter((VT[vt]['mdisp'], t[2]) for vt in TH for t in TH[vt])
pr('thunk (本层mdisp,K) 直方:', dict(sorted(Khist.items())))
R['thunks'] = dict(nz=len(nz_slots), thunk=nth, direct=len(DIR))

byname = collections.defaultdict(list)
for vt in order: byname[VT[vt]['name']].append(vt)
mult = {k: sorted(v) for k, v in byname.items() if len(v) > 1}
prim = {}
for k, lst in byname.items():
    z = [vt for vt in lst if VT[vt]['mdisp'] == 0]
    if len(z) == 1: prim[k] = z[0]
pr('名字组 %d / 多表组 %d / 有唯一 mdisp=0 主表的组 %d' % (len(byname), len(mult), len(prim)))

# ---------------- R1: 比对空间 ----------------
hdr('S1 R1 比对空间：被审口径的 0 究竟有多少可比对机会')
DIRSET = set((vt, k) for vt, k, _ in DIR)
pair_all = 0; opp_direct = 0; opp_same_n = collections.Counter()
parity = []
for nm, lst in mult.items():
    for a in range(len(lst)):
        for b in range(a + 1, len(lst)):
            A, B = lst[a], lst[b]
            n = min(PRE[A], PRE[B]); pair_all += n
            for k in range(n):
                hit = ((A, k) in DIRSET) + ((B, k) in DIRSET)
                opp_direct += hit
                opp_same_n[hit] += 1
                parity.append((A, B, k, VT[VT[A]['pchd']]['name'] if 0 else ''))
# 复算被审口径的匹配数（同组另一层同序号）
m_same = 0; m_any = 0
byvtgrp = {}
for nm, lst in mult.items():
    for vt in lst: byvtgrp[vt] = lst
for vt, k, val in DIR:
    lst = byvtgrp.get(vt, [])
    if any(PRE[o] > k and P.dw(o + 4 * k) == val for o in lst if o != vt): m_any += 1
pr('多表组内表对数覆盖的 (表对,槽号) 三元组总可比对数 = %d' % pair_all)
pr('  其中至少一侧是直接槽的机会数 = %d  (两侧都是直接槽 %d / 仅一侧 %d)' %
   (opp_direct, opp_same_n[2], opp_same_n[1]))
pr('复算：直接槽值 == 同组另一层同序号槽 的命中数 = %d / %d' % (m_any, len(DIR)))
# 期望匹配（独立性基率）：值分布的多重集自乘
cnt = collections.Counter(v for _, _, v in DIR)
N_d = len(DIR)
q = sum((c / N_d) ** 2 for c in cnt.values())
E_same = opp_direct * q
pr('  值多样性: 不同目标 %d / 1013, Σp^2 = %.6g' % (len(cnt), q))
pr('  独立基率下期望命中 = %.4f  ⇒ 实测 %d 的信息量 ≈ 0（0 本就是零假设期望值）' % (E_same, m_any))
R['R1'] = dict(pair_triples=pair_all, opp_direct=opp_direct, opp_both=opp_same_n[2],
               opp_one=opp_same_n[1], obs=m_any, distinct_val=len(cnt), sum_p2=q,
               exp=E_same)

# ---------------- A1: 语义对齐口径 ----------------
hdr('S2 A1 换口径：直接槽是不是「基类自带实现」的拷贝')
def bases_of(c):
    ch = c['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12)
    if num is None or pba is None: return []
    out = []
    for j in range(num):
        e = P.dw(pba + 4 * j)
        if e is None: continue
        out.append(dict(ptd=P.dw(e), ncb=P.dw(e + 4), mdisp=P.dw(e + 8),
                        pdisp=P.dw(e + 12), vdisp=P.dw(e + 16), attr=P.dw(e + 20)))
    return out
BD = {vt: bases_of(VT[vt]) for vt in order}
cls = collections.Counter(); samples = collections.defaultdict(list)
inherit = override = unresolved = 0
for vt, k, val in DIR:
    m = VT[vt]['mdisp']; e = [x for x in BD[vt] if x['mdisp'] == m]
    if len(e) != 1:
        unresolved += 1; samples['dup_mdisp'].append((VT[vt]['name'], m, len(e))); continue
    dn = P.cstr(e[0]['ptd'] + 8, 200)
    dn = dn.decode('latin1') if dn else ''
    p0 = prim.get(dn)
    if p0 is None or PRE[p0] <= k:
        unresolved += 1
        cls['base_not_local_or_short'] += 1
        samples['unres'].append((VT[vt]['name'], m, k, dn, 'noP0' if p0 is None else PRE[p0]))
        continue
    v0 = P.dw(p0 + 4 * k)
    if v0 == val: inherit += 1
    else:
        override += 1
        cls['override'] += 1
        if len(samples['ovr']) < 25:
            samples['ovr'].append((VT[vt]['name'], m, k, hex(val), dn, hex(v0)))
pr('1013 直接槽按「基类子对象自带实现 vs 派生覆盖」分档：')
pr('  与基类自身主表同序号实现相同（继承/未覆盖）= %d' % inherit)
pr('  不同（派生覆盖或基类表不可比）= %d' % override)
pr('  无法判定（基类无本地表或表更短）= %d' % unresolved)
pr('  无法判定的原因分布:', dict(cls))
R['A1'] = dict(inherit=inherit, override=override, unresolved=unresolved,
               why=dict(cls), override_samples=samples['ovr'])
# 覆盖档里到底是哪些基类子对象？按 (基类名,k) 聚类
ov_by = collections.Counter()
for vt, k, val in DIR:
    m = VT[vt]['mdisp']; e = [x for x in BD[vt] if x['mdisp'] == m]
    if len(e) != 1: continue
    dn = (P.cstr(e[0]['ptd'] + 8, 200) or b'').decode('latin1')
    p0 = prim.get(dn)
    if p0 is None or PRE[p0] <= k: continue
    if P.dw(p0 + 4 * k) != val: ov_by[(dn, k)] += 1
pr('覆盖档按 (基类名,槽号) 聚类 top12:', ov_by.most_common(12))
R['A1']['ov_by'] = [[a, b, c] for (a, b), c in ov_by.most_common(20)]
# 同表内重复目标（同一函数被同表两个槽引用）
intra = 0; intra_tabs = set()
for vt in NP:
    vs = [v for _, v in sorted(TH[vt] and [] or [])] if False else None
for vt in set(vt for vt, k, v in DIR):
    vs = [v for t, k, v in DIR if t == vt]
    c2 = collections.Counter(vs)
    d = sum(c - 1 for c in c2.values() if c > 1)
    if d: intra += d; intra_tabs.add(vt)
pr('直接槽中「同表内不同槽号 → 同一地址」的多余计数 = %d（涉及 %d 张表）' % (intra, len(intra_tabs)))

# ---------------- A2: 基率 ----------------
hdr('S3 A2 基率：聚集是否超出随机')
allvals = [P.dw(vt + 4 * k) for vt in order for k in range(PRE[vt])]
POOL_ALL = len(set(allvals))
POOL_NP = len(set(P.dw(vt + 4 * k) for vt in NP for k in range(PRE[vt])))
def pairs(c):
    return sum(n * (n - 1) // 2 for n in c.values())
c_dir = collections.Counter(v for _, _, v in DIR)
obs_pairs = pairs(c_dir)
E_unif_all = len(DIR) * (len(DIR) - 1) / 2 / POOL_ALL
E_unif_np = len(DIR) * (len(DIR) - 1) / 2 / POOL_NP
pr('池大小：全 14044 槽的不同目标 %d；非主表 1318 槽的不同目标 %d' % (POOL_ALL, POOL_NP))
pr('1013 直接槽内共享同一目标的对数(实测) = %d' % obs_pairs)
pr('均匀抽自全池期望对数 = %.1f ；抽自非主表池期望 = %.1f ；放大倍数 %s' %
   (E_unif_all, E_unif_np, 'x%.0f' % (obs_pairs / max(E_unif_all, 1e-9))))
pr('目标多重度 top12:', [(hex(k), v) for k, v in c_dir.most_common(12)])
# 同槽号跨类 vs 异槽号 的共享率
def share_stats(sel):
    tot = 0; eq = 0
    byk = collections.defaultdict(list)
    for vt, k, v in sel: byk[k].append((VT[vt]['name'], v))
    for k, lst in byk.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                if lst[i][0] == lst[j][0]: continue
                tot += 1; eq += (lst[i][1] == lst[j][1])
    return tot, eq
t_all, e_all = share_stats(DIR)
# 异槽号：把 k 打乱后重算
rng = random.Random(1911)
perm_eq = []
for _ in range(200):
    shuffled = [(vt, rng.randrange(0, 10 ** 6), v) for vt, k, v in DIR]
    perm_eq.append(share_stats(shuffled)[1])
base_p = q  # 两个随机槽目标相同的独立基率
pr('同槽号跨类比较对数 = %d，其中目标相同 = %d（命中率 %.4f）' % (t_all, e_all, e_all / max(t_all, 1)))
pr('  k 打乱(200 次) 后同「位置组」共享对中位数 = %.0f（命中率 %.4f）' %
   (sorted(perm_eq)[100], sorted(perm_eq)[100] / max(t_all, 1)))
pr('  独立基率期望命中 = %.1f（命中率 %.4f）⇒ 富集比 = x%.1f' %
   (t_all * base_p, base_p, (e_all / max(t_all, 1)) / base_p))
# 打乱 target 的置换零假设（保持 k 结构、打乱目标）
tv = [v for _, _, v in DIR]
tp = []
for _ in range(200):
    rng.shuffle(tv)
    tp.append(pairs(collections.Counter(tv)))
tp.sort()
pr('置换零假设(打乱 1013 个目标值 200 次) 共享对数 中位数=%d 上界=%d ；实测=%d' %
   (tp[100], tp[-1], obs_pairs))
# 桩函数占比
def cls_bytes(va, n=8):
    o = P.r2o(va)
    return None if o is None else RAW[o:o + n]
def trivial(va):
    b = cls_bytes(va, 8)
    if b is None or len(b) < 3: return None
    if b[0] == 0xC2: return 'retK'
    if b[0] == 0x32 and b[1] == 0xC0 and b[2] == 0xC2: return 'xorret'
    if b[0] == 0xB8 and b[5] == 0xC2: return 'mov0ret'
    if b[0] == 0x33 and b[1] == 0xC0: return 'xoreax'
    return None
tk = collections.Counter()
for _, _, v in DIR: tk[trivial(v)] += 1
pr('直接槽目标首字节形态:', dict(tk))
top5 = c_dir.most_common(5)
covered = sum(v for _, v in top5)
pr('top5 地址覆盖槽数 %d / 1013 = %.1f%%；其形态 %s' %
   (covered, 100.0 * covered / 1013, [trivial(a) for a, _ in top5]))
pr('top5 目标首 16 字节:', [(hex(a), cls_bytes(a, 16).hex()) for a, _ in top5])
rest = collections.Counter({v: c for v, c in c_dir.items() if v not in dict(top5)})
pr('剔除 top5 后剩余槽 %d / 目标 %d / 共享对数 %d' %
   (1013 - covered, len(rest), pairs(rest)))
R['A2'] = dict(pool_all=POOL_ALL, pool_np=POOL_NP, obs_pairs=obs_pairs,
               exp_unif=round(E_unif_all, 2), exp_unif_np=round(E_unif_np, 2),
               same_k_pairs=t_all, same_k_eq=e_all, perm_med=sorted(perm_eq)[100],
               indep_exp=round(t_all * base_p, 2), enrich=round((e_all / max(t_all, 1)) / base_p, 2),
               perm_pairs_med=tp[100], perm_pairs_max=tp[-1],
               top5=[[hex(a), v] for a, v in top5], top5_covered=covered,
               rest_pairs=pairs(rest), rest_targets=len(rest), trivial=dict(tk))

# ---------------- R2: 两个口径 ----------------
hdr('S4 R2 去重口径：地址去重 vs (表,槽) 去重')
d_addr = len(c_dir)
d_tab_slot = len(DIR)
d_name_k = len(set((VT[vt]['name'], k) for vt, k, _ in DIR))
d_col_k = len(set((P.dw(vt - 4), k) for vt, k, _ in DIR))
d_md_k = len(set((VT[vt]['mdisp'], k) for vt, k, _ in DIR))
d_k = len(set(k for _, k, _ in DIR))
pr('地址去重 = %d ；(表,槽) 去重 = %d ；(COL,k) 去重 = %d ；(类名,k) 去重 = %d ；(层mdisp,k) 去重 = %d ；槽号去重 = %d' %
   (d_addr, d_tab_slot, d_col_k, d_name_k, d_md_k, d_k))
per = collections.defaultdict(lambda: dict(n=0, tabs=set(), ks=set(), names=set()))
for vt, k, v in DIR:
    e = per[v]; e['n'] += 1; e['tabs'].add(vt); e['ks'].add(k); e['names'].add(VT[vt]['name'])
one = sum(1 for v, e in per.items() if e['n'] == 1)
same_k_only = sum(1 for v, e in per.items() if e['n'] > 1 and len(e['ks']) == 1)
diff_k = sum(1 for v, e in per.items() if len(e['ks']) > 1)
pr('单一引用（无共享）的目标 %d ；被多处引用且槽号全同 %d ；槽号不同(跨虚函数复用) %d' % (one, same_k_only, diff_k))
multi = sorted(((e['n'], len(e['tabs']), len(e['ks']), len(e['names']), hex(v))
                for v, e in per.items() if e['n'] > 1), reverse=True)[:12]
pr('共享目标 top12 (槽数,表数,槽号数,类名数,地址):', multi)
R['R2'] = dict(distinct_addr=d_addr, distinct_table_slot=d_tab_slot, distinct_col_k=d_col_k,
               distinct_name_k=d_name_k, distinct_md_k=d_md_k, distinct_k=d_k,
               single_ref=one, shared_same_k=same_k_only, shared_diff_k=diff_k, top=multi)

# ---------------- R3: BCD 布局验证 ----------------
hdr('S5 R3 BCD 布局是否真的是 {pTD,ncb,PMD{mdisp,pdisp,vdisp},attributes}')
ent = []
for vt in order:
    ent += [(vt, x) for x in BD[vt]]
n_ent = len(ent)
tdok = sum(1 for vt, x in ent if P.dw(x['ptd']) == 0x7F9594 and name_ok(P.cstr(x['ptd'] + 8, 200)))
pd = collections.Counter(x['pdisp'] for vt, x in ent)
vd16 = collections.Counter(x['vdisp'] for vt, x in ent)
at20 = collections.Counter(x['attr'] for vt, x in ent)
pr('描述符项 %d ；dword@0 是合法 TD 的 %d' % (n_ent, tdok))
pr('dword@12 (pdisp) 直方:', dict(pd))
pr('dword@16 直方:', dict(vd16), ' ；dword@20 直方:', dict(at20))
selfn = 0; selfncb = 0; selfmd = 0
for vt in order:
    c = VT[vt]; b0 = BD[vt][0]
    if P.cstr(b0['ptd'] + 8, 200) == c['name'].encode(): selfn += 1
    if b0['ncb'] == P.dw(c['pchd'] + 8) - 1: selfncb += 1
    if b0['mdisp'] == 0: selfmd += 1
pr('自项校验：名相同 %d/1214 ；ncb==numBaseClasses-1 %d/1214 ；mdisp==0 %d/1214' % (selfn, selfncb, selfmd))
# 反控 1：若 attributes 在 +16，则 vdisp 取 {0,9,2} 与 pdisp==-1 矛盾
contra = sum(1 for vt, x in ent if x['pdisp'] == 0xFFFFFFFF and x['vdisp'] != 0)
pr('反控1：pdisp==-1 但 +16 非 0 的项 = %d（若 >0 则 +16 不是纯 vdisp 或存在虚基类）' % contra)
# 反控 2：若基类数组是 20 字节内联记录而非指针数组
bad20 = 0; base20 = None
for vt in order[:200]:
    ch = VT[vt]['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12)
    for j in range(min(num, 4)):
        e = pba + 20 * j
        if P.dw(e) is None or P.dw(P.dw(e)) != 0x7F9594: bad20 += 1
pr('反控2：按「20 字节内联记录」解释前 200 张表基类数组，第 j 项的 dword 不是合法 TD 的项数 = %d（>0 即 20 字节内联假设不成立；数组存的是指针）' % bad20)
# 反控 3：指针数组假设下 5 项全验证
ok5 = 0; tot5 = 0
for vt in order:
    ch = VT[vt]['pchd']; num = P.dw(ch + 8); pba = P.dw(ch + 12)
    for j in range(num):
        e = P.dw(pba + 4 * j); tot5 += 1
        if e is not None and P.dw(e) is not None and P.dw(P.dw(e)) == 0x7F9594: ok5 += 1
pr('反控3：指针数组假设 %d/%d 项二次间接命中 type_info' % (ok5, tot5))
R['R3'] = dict(entries=n_ent, tdok=tdok, pdisp=dict(pd), dw16=dict(vd16), dw20=dict(at20),
               self_name=selfn, self_ncb=selfncb, self_md=selfmd, contra16=contra,
               bad20=bad20, ok5=ok5, tot5=tot5)

# ---------------- A3 / R4 ----------------
hdr('S6 A3/R4 attributes 分布能否支撑「non-virtual 基类」解释')
layers = set(VT[vt]['mdisp'] for vt in order)
extra = sorted(set(x['mdisp'] for vt, x in ent) - layers)
pr('COL 层偏移集合(%d):' % len(layers), sorted(layers), ' 只在 BCD 里出现的:', extra)
buck = collections.defaultdict(collections.Counter)
for vt, x in ent: buck[x['mdisp']][x['attr']] += 1
for m in sorted(buck, key=lambda z: (z not in extra, z)):
    tag = 'EXTRA' if m in extra else 'layer'
    pr('  mdisp=%-6d %s 项数=%-5d attributes 直方 %s' %
       (m, tag, sum(buck[m].values()), dict(buck[m])))
names1214 = set(c['name'] for c in COL.values())
ext_detail = collections.defaultdict(collections.Counter)
for vt in order:
    for x in BD[vt]:
        if x['mdisp'] in extra:
            dn = (P.cstr(x['ptd'] + 8, 200) or b'').decode('latin1')
            ext_detail[x['mdisp']][dn] += 1
for m in extra:
    pr('  mdisp=%d 基类名 %s' % (m, ext_detail[m].most_common()))
# 这些基类是否在本镜像里另有自己的 COL（⇒ 多态）
for m in extra:
    for dn, c in ext_detail[m].most_common():
        has = dn in names1214
        mir = [hex(VT[vt]['mdisp']) for vt in byname.get(dn, [])]
        pr('    %s 在 1214 名单内=%s ；其本地表层 %s' % (dn[:60], has, mir))
# 放宽扫描：是否存在 mdisp ∈ extra 的 COL 样元组被 strict 判据滤掉
pr('放宽 COL 扫描 %d 条；其中 mdisp ∈ extra 的 %d 条：' %
   (len(RELAX), sum(1 for r in RELAX if r['mdisp'] in extra)))
badm = [r for r in RELAX if r['mdisp'] in extra]
pr('  严格判据通过数 %d ；被 d2!=0 拒 %d ；被 d4∉.rdata 拒 %d' %
   (sum(1 for r in badm if r['ok2'] and r['ok4']),
    sum(1 for r in badm if not r['ok2']), sum(1 for r in badm if not r['ok4'])))
pr('  样例行:', [(hex(r['at']), r['mdisp'], r['name'][:44], r['d2'], hex(r['d4'])) for r in badm[:10]])
# 反控：把所有 descriptors 的 mdisp 全取出来做同一判据——bit0 是否恒为 0
bit0 = collections.Counter()
for vt, x in ent: bit0[(x['mdisp'] in extra, x['attr'] & 1)] += 1
pr('bit0 与「是否落在 extra 四档」的交叉表 { (is_extra, bit0): 计数 }:', dict(bit0))
bit1 = collections.Counter()
for vt, x in ent: bit1[(x['mdisp'] in extra, (x['attr'] >> 1) & 1)] += 1
pr('bit1 与 extra 的交叉表:', dict(bit1))
# 有副表的层（4/8/12/24/36/40/44/1728/21784）里的 attributes 分布，做同口径对照
anylayer = collections.Counter()
for vt, x in ent: anylayer[(x['mdisp'] in layers and x['mdisp'] != 0, x['attr'])] += 1
pr('「有独立副表的非零层」vs attributes 交叉表:', dict(anylayer))
R['A3'] = dict(layers=sorted(layers), extra=extra,
               buck={m: dict(buck[m]) for m in buck},
               ext_detail={m: ext_detail[m].most_common() for m in extra},
               relax_extra=[[hex(r['at']), r['mdisp'], r['name']] for r in badm],
               bit0=[[a, b, c] for (a, b), c in bit0.items()],
               bit1=[[a, b, c] for (a, b), c in bit1.items()],
               layer_attr=[[a, b, c] for (a, b), c in anylayer.items()])

# ---------------- 反控汇总 ----------------
hdr('S7 反控（含可让 A2/A3 变红者）')
# C1: A2 —— 剔除 top5 桩后聚集还剩多少
pr('C1(A2) 剔除 top5 目标后：剩余 %d 槽 / %d 目标 / 共享对数 %d；若不剔除为 %d' %
   (1013 - covered, len(rest), pairs(rest), obs_pairs))
# C2: A2 —— 只保留「非桩」函数（排除 retK/xorret/mov0ret）再算共享
nonstub = [(vt, k, v) for vt, k, v in DIR if trivial(v) is None]
cn = collections.Counter(v for _, _, v in nonstub)
pr('C2(A2) 只留非桩函数：槽 %d / 目标 %d / 共享对数 %d / 最大多重度 %d' %
   (len(nonstub), len(cn), pairs(cn), max(cn.values())))
# C3: A3 —— attributes 判据换成常量（全体同值）是否同样"通过"
allattr = set(x['attr'] for vt, x in ent)
pr('C3(A3) 全体 attributes 取值集合 = %s ⇒ 若拿 bit 判读写进解释，必须证明它在 extra 与 layer 之间不同' % sorted(allattr))
# C4: A1 —— 把"同组同序号 0 命中"换成"同基类子对象同序号"，命中数
bybase = collections.defaultdict(list)
for vt, k, v in DIR:
    m = VT[vt]['mdisp']; e = [x for x in BD[vt] if x['mdisp'] == m]
    dn = (P.cstr(e[0]['ptd'] + 8, 200) or b'').decode('latin1') if len(e) == 1 else '?'
    bybase[(dn, k)].append(v)
tot = 0; eq = 0; ngrp = 0
for key, vs in bybase.items():
    if len(vs) < 2: continue
    ngrp += 1
    for i in range(len(vs)):
        for j in range(i + 1, len(vs)):
            tot += 1; eq += (vs[i] == vs[j])
pr('C4(A1) 按 (基类子对象名, 槽号) 对齐：可比较对 %d（%d 组），其中值相同 %d（%.2f%%）' %
   (tot, ngrp, eq, 100.0 * eq / max(tot, 1)))
R['ctrl'] = dict(C1=dict(rest_slots=1013 - covered, rest_targets=len(rest), rest_pairs=pairs(rest),
                         all_pairs=obs_pairs),
                 C2=dict(slots=len(nonstub), targets=len(cn), pairs=pairs(cn),
                         maxmult=max(cn.values()) if cn else 0),
                 C3=sorted(allattr), C4=dict(pairs=tot, groups=ngrp, eq=eq,
                                             rate=round(100.0 * eq / max(tot, 1), 3)))

json.dump(R, open(os.path.join(OUT, 'r191_audit.json'), 'w'), indent=1, ensure_ascii=False, default=str)
pr('\n== 完成，产物 %s ==' % os.path.join(OUT, 'r191_audit.json'))
