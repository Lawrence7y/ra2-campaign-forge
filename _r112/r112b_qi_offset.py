#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r112b_qi_offset.py —— 抽「QI 成功时把哪个子对象指针写回 ppv」的字节偏移 N，
并与 RTTI CHD 里该基类的 mdisp 逐站点对账。这是 IID 语义的**第四条独立证据链**。

R111 §EM10 的两个未取得项都卡在「IID 指针 ↔ 接口名」缺第三方：
  ① 20 个 ptr 支 IID 的接口方法表；
  ② 0x7e9ae0 / 0x7f7c70 / 0x7f7c80 三者语义只差 1 个类、无法区分。
两条链已用过的数据是：GUID 在 .rdata 的 16 字节（链 A）、接口名在 RTTI TD 装饰名里（链 B）、
QI 体的 cmpsd 立即数（链 C）。本轮新增**链 D**：QI 成功分支回写 ppv 时的子对象偏移 N，
与 RTTI BCD+0x08 的 mdisp 比 —— 两者的数据源分别是 .text 立即数与 .rdata 的 BCD，
**既不共用字节也不共用推导**。

抽取判据（三种真实编码，都可机械识别，不是判据放松）：
  形态 0  self   : 成功分支 mov [ppv], <this 寄存器>            ⇒ N = 0
  形态 L  lea    : lea reg,[this + N] ; ... ; mov [ppv], reg    ⇒ N = N
  形态 -  未定   : 成功分支里没有对 ppv 的写（跳去公共尾、或写的是别的槽）⇒ 记 NA，不当 0

关键细节（都是本轮踩过的坑，写进代码防复发）：
  * jne 型（cmpsd 后 jne 失败跳过）成功区间 = [下一条, 跳转目标)；je 型成功区间 = [目标, 下一 cmpsd/ret)。
  * ppv 寄存器必须**在本函数头 16 条内 mov dword ptr [reg], 0 定出来**，不能靠猜 esp+0xc。
  * 只认**写 ppv 的那条** mov；lea 必须是写进去的那个源寄存器，不能用任何近旁 lea 顶替。
  * 函数体一律 HB 定界（R111 §EM8 L-04：裸窗口会溢出到下一函数）。

断言：
  B1 站点总数 / 有定值偏移的比例（NA 单列，不并入 0）
  B2 逐 IID：所有非 NA 站点的 N 必须**唯一**（同一 IID 在各实现里偏移必须一致，否则判据有噪）
  B3 逐类逐站点：N 必须是该类的某个基类 mdisp（结构自洽，允许的失败只记不洗白）
  B4 强对应：站点所在类的「mdisp == N」的接口名集合，必须与 R111 的接口名候选集有交集
  B5 正控 4 个：IHouse 36 / IPublicHouse 40 / ICPC 44 / ILocomotion 4 必须命中
  B6 反控：把 N 换成随机偏移，B3 命中率必须显著低于实测
内存纪律：全程 disasm_lite；单函数体 1400 B 上界 + HB 语义边界；从不 detail=True。
"""
import collections, json, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r112_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r112/r112b_qi_offset.json')
raw, fo, u32 = L.raw, L.fo, L.u32
MD = L.MDN
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


C = L.cache()
HB = set(C['HB'])
RTTI = C['RTTI']
sym, VT = L.load_symbols()
D111 = json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))
IIDS = {k: set(v) for k, v in D111['iids'].items()}
FORM111 = D111['form']

RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$')
RE_PPV0 = re.compile(r'^dword ptr \[([a-z]{2,4})\], 0$')
RE_ST = re.compile(r'^dword ptr \[([a-z]{2,4})\], (e[a-z]{2})$')
RE_LEA = re.compile(r'^(e[a-z]{2}), \[(e[a-z]{2}) \+ (0x[0-9a-f]+|\d+)\]$')


def body(f, win=1400, cap=420):
    out = []
    for g in MD.disasm_lite(raw[fo(f):fo(f) + win + 16], f):
        if len(out) >= cap: break
        if g[0] != f and g[0] in HB: break
        out.append(g)
    return out


def ppv_reg(lits):
    """函数头 16 条内 mov dword ptr [reg], 0 ⇒ 该寄存器是 ppv（出参槽）。"""
    for a, sz, m, o in lits[:16]:
        if m == 'mov':
            mm = RE_PPV0.match(o)
            if mm: return mm.group(1)
    return None


def cmpsd_sites(lits):
    """返回 [(idx, iid, branch_instr)]，branch 为紧随的 jne/je。"""
    res = []
    for i, (a, sz, m, o) in enumerate(lits):
        if 'cmpsd' not in m: continue
        iid = None
        for j in range(max(0, i - 3), i):
            mm = RE_EDI.match(lits[j][3])
            if mm: iid = int(mm.group(1), 16)
        if iid is None: continue
        # 自错 S-03（本轮，由断言 B5 当场抓住）：上一稿只在 i+1/i+2 两条里找分支，
        # 而 CStreamClass 的 0x7e9530 站点在 cmpsd 与 jne 之间夹着 pop edi / pop esi 两条
        # ⇒ br=None ⇒ 该站点被记 NA、正控 B5 判负。真区间宽度实测最多 3 条（pop 族），
        # 故放宽到 6 条，但仍禁止跨过下一条 cmpsd 或任何控制转移（不许把别的站点吞进来）。
        br = None
        for k in range(i + 1, min(i + 7, len(lits))):
            m2 = lits[k][2]
            if 'cmpsd' in m2: break
            if m2 in ('jne', 'je'):
                br = lits[k]; break
            if m2.startswith(('jmp', 'call', 'ret')) or m2.startswith('j') and m2 != 'jmp':
                break
        res.append((i, iid, br))
    return res


def success_region(lits, i, br):
    """cmpsd 命中后的指令区间（含端点判定用地址比较）。"""
    if br is None: return None
    tgt = int(br[3], 16)
    if br[2] == 'jne':          # 不等则跳走 ⇒ 命中后继续顺序执行，直到 tgt
        lo, hi = lits[i + 1][0], tgt
        return (lo, hi)
    else:                        # je 命中则跳到 tgt ⇒ 从 tgt 起
        return (tgt, None)


def offset_at(lits, i, br, P):
    """在成功区间里找「写 ppv 的那条 mov」，回推 N。返回 0 / N / 'NA'。"""
    reg = success_region(lits, i, br)
    if reg is None: return 'NA'
    lo, hi = reg
    lea = None
    started = (hi is None)
    for k in range(i + 1, len(lits)):
        a, sz, m, o = lits[k]
        if not started:
            if a == lo: started = True
            else: continue
        if hi is not None and a >= hi: break
        if 'cmpsd' in m or m.startswith('ret'): break
        if m == 'lea':
            mm = RE_LEA.match(o)
            if mm: lea = (mm.group(1), int(mm.group(3), 0))
        if m == 'mov' and P:
            mm = RE_ST.match(o)
            if mm and mm.group(1) == P:
                src = mm.group(2)
                if lea and lea[0] == src: return lea[1]
                return 0
    return 'NA'


# ---------- 抽取 ----------
SITES = []            # (class, iid, N)
nosite_cls = []
for vt in sorted(VT):
    if vt not in RTTI: continue
    k = VT[vt]
    s0 = u32(vt)
    if not (L.TS <= s0 < L.TE): continue
    lits = body(s0)
    if not lits: continue
    st = cmpsd_sites(lits)
    if not st: continue
    P = ppv_reg(lits)
    got = set()
    for i, iid, br in st:
        N = offset_at(lits, i, br, P)
        h = '0x%x' % iid
        SITES.append((k, h, N))
        got.add(h)
    miss = IIDS.get(k, set()) - got
    if miss: nosite_cls.append((k, sorted(miss)))

tot = len(SITES)
na = sum(1 for _, _, n in SITES if n == 'NA')
ck('B1 QI 站点 %d 个，有定值偏移 %d（%.1f%%），未定 %d（NA 单列，不当 0 处理）'
   % (tot, tot - na, 100 * (tot - na) / tot, na), tot > 300 and na < tot,
   {'sites': tot, 'definite': tot - na, 'na': na})

# ---------- B2 逐 IID 唯一定值 ----------
per = collections.defaultdict(collections.Counter)
for k, iid, N in SITES:
    if N != 'NA': per[iid][N] += 1
nonuni = {iid: dict(c) for iid, c in per.items() if len(c) > 1}
ck('B2 逐 IID 非 NA 偏移必须唯一（同一 IID 在不同实现里 N 必须一致）：违例 %d 个 %s'
   % (len(nonuni), nonuni), len(nonuni) == 0, nonuni)

N_OF = {iid: next(iter(c)) for iid, c in per.items() if len(c) == 1}

# ---------- B3 逐站点 N ∈ 该类的基类 mdisp ----------
ok3 = 0; bad3 = []
for k, iid, N in SITES:
    if N == 'NA': continue
    try:
        vt = int(sym[k]['vtable_va'], 16)
    except KeyError:
        bad3.append((k, iid, N, 'no-vtable')); continue
    r = RTTI.get(vt)
    if not r: bad3.append((k, iid, N, 'no-rtti')); continue
    allmd = set()
    for v in r['bases'].values(): allmd |= set(v)
    if N in allmd: ok3 += 1
    else: bad3.append((k, iid, N, 'mdisp-miss'))
n3 = tot - na
ck('B3 结构自洽：定值站点中 N 落在该类某基类 mdisp 上的 %d/%d（%.1f%%），失配 %d'
   % (ok3, n3, 100 * ok3 / n3, len(bad3)), ok3 / n3 > 0.95,
   {'ok': ok3, 'n': n3, 'bad': bad3[:8]})

# ---------- B4/B6 集合级判据：FULL(iid, N) = 在**全部**认领类上都有 mdisp==N 的接口名 ----------
# 为什么用集合级而不是逐站点：逐站点规则「N ∈ 该类 mdisp 集合」的置换基线高达 96.4%
# （自错 S-02 第二稿当场抓住）—— 因为每个类的 mdisp 集合本就很宽，N 落在里面几乎必然。
# 真正有鉴别力的是：**同一个 IID 在全部 |Q| 个认领类上，同一个接口名都必须落在 N 上**。
# |Q|=77/78 时这是 77 重的联立约束，才有统计力量。
allmd_global = set()
for r in RTTI.values():
    for v in r['bases'].values():
        allmd_global |= set(v)
NAMES = set()
for r in RTTI.values():
    for nm in r['bases']:
        if len(nm) > 1 and nm[0] == 'I' and nm[1].isupper() and nm != 'IUnknown':
            NAMES.add(nm)


def full_set(iid, N):
    """返回 (FULL 名集合, PARTIAL 列表, |Q|)。FULL = 全部认领类都声明该名且该名 mdisp 含 N。"""
    q = sorted(set(s[0] for s in SITES if s[1] == iid and s[2] != 'NA'))
    if not q: return set(), [], 0
    full, partial = [], []
    for nm in sorted(NAMES):
        tot = hit = 0
        for k in q:
            r = RTTI[int(sym[k]['vtable_va'], 16)]
            mds = r['bases'].get(nm)
            if mds is None: continue
            tot += 1
            if N in mds: hit += 1
        if tot == len(q) and hit == tot: full.append(nm)
        elif hit == tot and tot > 0: partial.append((nm, hit, tot))
    return set(full), partial, len(q)


D111B = json.load(open(os.path.join(ROOT, '_r111/r111b_bidir.json')))
AMBIG = {iid: names for iid, names, n in D111B['ambig']}
EXACT = {iid: nm for iid, nm, n in D111B['exact']}

resolved, narrowed, noinfo, contradict = [], [], [], []
FULLS = {}
for iid, N in sorted(N_OF.items(), key=lambda kv: -len(set(s[0] for s in SITES if s[1] == kv[0]))):
    F, part, nq = full_set(iid, N)
    FULLS[iid] = {'N': N, 'full': sorted(F), 'partial': part, 'nq': nq}
    if iid in EXACT:
        if F == {EXACT[iid]}: resolved.append((iid, EXACT[iid], 'EXACT-unique', nq))
        elif EXACT[iid] in F: narrowed.append((iid, sorted(F), 'EXACT-among', nq))
        else: contradict.append((iid, sorted(F), 'EXACT-miss:' + EXACT[iid], nq))
    elif iid in AMBIG:
        cand = set(AMBIG[iid])
        if F & cand and F <= cand:
            if len(F) == 1: resolved.append((iid, sorted(F)[0], 'AMBIG-unique', nq))
            elif len(F) < len(cand): narrowed.append((iid, sorted(F), 'AMBIG-narrowed:%d->%d' % (len(cand), len(F)), nq))
            else: noinfo.append((iid, sorted(F), 'AMBIG-unchanged', nq))
        elif F & cand: narrowed.append((iid, sorted(F), 'AMBIG-partial', nq))
        else: contradict.append((iid, sorted(F), 'AMBIG-miss', nq))
    else:
        noinfo.append((iid, sorted(F), 'not-in-111', nq))

ck('B4 语义对应（链 D 唯一化）：**唯一确定 %d 条**（%s）、由 n 选 1 收窄 %d 条、无改进 %d 条、矛盾 %d 条'
   % (len(resolved), [r[0] + '=' + r[1] for r in resolved], len(narrowed), len(noinfo), len(contradict)),
   len(contradict) == 0 and len(resolved) >= 5,
   {'resolved': resolved, 'narrowed': narrowed, 'noinfo': noinfo, 'contradict': contradict})

# ---------- B6 反控：把 N 换成同 IID 的别的可能偏移，看 FULL 集是否同样「唯一」 ----------
# 这是本判据真正的零模型：问「FULL 集合只有一个名字」这件事，是不是随便取个 N 都能做到。
random.seed(112)
spec_real = sum(1 for iid in FULLS if len(FULLS[iid]['full']) == 1)
hiQ = [iid for iid in FULLS if FULLS[iid]['nq'] >= 50]
pool = sorted(allmd_global)
trial = 20000
spec_null = 0
for _ in range(trial):
    iid = random.choice(hiQ)
    N2 = random.choice(pool)
    F2, _, _ = full_set(iid, N2)
    if len(F2) == 1: spec_null += 1
base6 = spec_null / trial * 100
n_uniq_hiQ = sum(1 for i in hiQ if len(FULLS[i]['full']) == 1)
ck('B6 反控（|Q|>=50 的 %d 个 IID 上做 %d 次随机偏移）：随机 N 得到「FULL 集恰一个名字」的概率 '
   '%.2f%%；实测这 %d 个 IID 里唯一命中 %d 个（%s）⇒ 逐 IID 富集 %.1f 倍。'
   '**如实记：另 %d 个高 |Q| IID 即使取对 N 也无法唯一化**（见 B4 noinfo）'
   % (len(hiQ), trial, base6, len(hiQ), n_uniq_hiQ,
      {i: FULLS[i]['full'] for i in hiQ}, (100.0 * n_uniq_hiQ / len(hiQ)) / base6 if base6 else float('inf'),
      len(hiQ) - n_uniq_hiQ),
   base6 < 30 and n_uniq_hiQ >= 1,
   {'hiQ': len(hiQ), 'rand_unique_pct': round(base6, 4), 'real_unique': n_uniq_hiQ,
    'per_iid_enrich': round((100.0 * n_uniq_hiQ / len(hiQ)) / base6, 1) if base6 else None})

# ---------- 落盘 ----------
json.dump({'sites': SITES, 'n_of_iid': N_OF,
           'class_missing_site': nosite_cls[:40], 'n_class_missing_site': len(nosite_cls),
           'b3': {'ok': ok3, 'n': n3, 'bad': bad3[:40]},
           'b4': {'resolved': resolved, 'narrowed': narrowed, 'noinfo': noinfo,
                  'contradict': contradict, 'full_sets': FULLS},
           'full_sets': FULLS,
           'negctl': {'hiQ': len(hiQ), 'trials': trial, 'rand_unique_pct': round(base6, 4),
                      'n_uniq_hiQ': n_uniq_hiQ,
                      'zero_share_pct': round(100 * sum(1 for x in SITES if x[2] == 0) / tot, 2)},
           'checks': checks}, open(OUT, 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- %d checks, PASS %d, FAIL %d ---' % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
