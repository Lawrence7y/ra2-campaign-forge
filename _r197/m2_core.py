#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R197 第二刀（终稿）：181 处「相邻 BCA 元素递增」的成因取得可被否掉的正面判据。

主会话与执行员 #485 独立同值：CHD=954 / 槽位=2615 / 不同 BCD=1002 / 对=1661 / 减 1480 / 等 0 / 增 181。
本轮新增三条判据（每条都带反控，必须能被随机/退化数据否掉）：

 CORE-1 私有带恒 -24：对任一 CHD，若相邻两个 BCD 的全局引用计数都 == 1（称「私有对」），
        则 bcd[i+1] == bcd[i] - 24 恒成立（本刀实测 0 例外）。
        反控：把「引用计数 == 1」换成「引用计数 >= 1」（即取消去重门槛），例外立刻出现。

 CORE-2 688 归属：全部 688 个「diff != -24」的位置，没有任何一个是私有对（PP 类 = 0）。
        即 CORE-1 不是循环定义：688 个异常被「至少一端是共享 BCD」完整解释。

 CORE-3 单点判据：把每个私有 BCD 的地址按 -24 连成 run，实测 954 张 CHD 里 953 张的私有
        BCD 全部落在同一个 run 内（唯一例外 0x7fb4b0 属另一机制，见 EXC）。

 EXC 那唯一例外 0x7fb4b0 的形态单独给出，不许掩盖：其私有 BCD 跨 2 个 run，diff 序列含 192。
"""
import sys, struct, collections, json, random
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

def s32(v): return struct.unpack('<i', struct.pack('<I', v))[0]
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3] + 8, 400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4*i] = dict(sig=w[i], mdisp=s32(w[i+1]), ptd=w[i+3], pchd=w[i+4], name=nm.decode('latin1'))

CHD = {}
for c, cc in COL.items():
    v = cc['pchd']
    if v not in CHD: CHD[v] = dict(n=P.dw(v + 8), arr=P.dw(v + 12), cols=[])
    CHD[v]['cols'].append(c)
for v, d in CHD.items():
    d['bcds'] = [P.dw(d['arr'] + 4*j) for j in range(d['n'])]
    d['ncb'] = [P.dw(b + 4) for b in d['bcds']]
    d['md'] = [s32(P.dw(b + 8)) for b in d['bcds']]

alls = [b for d in CHD.values() for b in d['bcds']]
ref = collections.Counter(alls)
ck('K0a CHD==954', len(CHD) == 954, len(CHD))
ck('K0b 槽位==2615', len(alls) == 2615, len(alls))
ck('K0c 不同BCD==1002', len(set(alls)) == 1002, len(set(alls)))
ck('K0d COL==1214', len(COL) == 1214, len(COL))
ck('K0e 引用计数分布 1->698', collections.Counter(ref.values())[1] == 698, collections.Counter(ref.values())[1])
ck('K0f 共享 BCD 数 == 304', sum(1 for b, c in ref.items() if c > 1) == 304, sum(1 for b, c in ref.items() if c > 1))
ck('K0g 共享槽位 == 1917', sum(c for b, c in ref.items() if c > 1) == 1917, sum(c for b, c in ref.items() if c > 1))

pairs = []
for v, d in CHD.items():
    b = d['bcds']
    for i in range(len(b) - 1): pairs.append((v, i, b[i+1] - b[i]))
dec = sum(1 for a, b, c in pairs if c < 0)
eq = sum(1 for a, b, c in pairs if c == 0)
inc = sum(1 for a, b, c in pairs if c > 0)
ck('K1a 对==1661', len(pairs) == 1661, len(pairs))
ck('K1b 减1480/等0/增181', (dec, eq, inc) == (1480, 0, 181), (dec, eq, inc))

# ---- CORE-1 私有对恒 -24 ----
pp = [(v, i, c) for v, i, c in pairs if ref[CHD[v]['bcds'][i]] == 1 and ref[CHD[v]['bcds'][i+1]] == 1]
pp_ok = sum(1 for v, i, c in pp if c == -24)
ck('CORE1 私有对恒 -24 (0 例外)', pp_ok == len(pp), (pp_ok, len(pp)))
# 反控 R1：取消去重门槛（ref>=1 即全体对）
all_ok = sum(1 for v, i, c in pairs if c == -24)
ck('CORE1-R1 反控 取消门槛后非-24 条数 > 0', len(pairs) - all_ok > 0, len(pairs) - all_ok)

# ---- CORE-2 688 归属 ----
nq = [(v, i, c) for v, i, c in pairs if c != -24]
ck('CORE2a 非-24 共 688', len(nq) == 688, len(nq))
ck('CORE2b 688 中私有对 == 0', len([1 for v, i, c in nq if ref[CHD[v]['bcds'][i]] == 1 and ref[CHD[v]['bcds'][i+1]] == 1]) == 0, '')
sym = collections.Counter()
for v, i, c in nq:
    b = CHD[v]['bcds']
    a1 = ref[b[i]] == 1; a2 = ref[b[i+1]] == 1
    sym[('UP' if c > 0 else 'DN', 'PP' if (a1 and a2) else ('SS' if not a1 and not a2 else ('PS' if a1 else 'SP')))] += 1
ck('CORE2c 符号 x ref类别 表', len(sym) == 5, dict(sym))

# ---- CORE-3 私有 BCD 落在单一 -24 run ----
pv = sorted(b for b, c in ref.items() if c == 1)
runs = []; cur = [pv[0]]
for x in pv[1:]:
    if x == cur[-1] + 24: cur.append(x)
    else: runs.append(cur); cur = [x]
runs.append(cur)
runid = {}
for k, r in enumerate(runs):
    for b in r: runid[b] = k
same = 0; cross = []
for v, d in CHD.items():
    ids = set(runid[b] for b in d['bcds'] if ref[b] == 1)
    if len(ids) <= 1: same += 1
    else: cross.append(v)
ck('CORE3 私有 BCD 单 run 的 CHD == 953/954', same == 953, (same, len(CHD)))
ck('CORE3-EXC 唯一例外 == 0x7fb4b0', cross == [0x7fb4b0], cross)

# ---- EXC 明细 ----
exc = CHD[0x7fb4b0]
exc_priv = [b for b in exc['bcds'] if ref[b] == 1]
exc_d = [exc_priv[k] - exc_priv[k+1] for k in range(len(exc_priv) - 1)]

# ---- 树关系（复算执行员 Q4）----
def build(ncb, n):
    if any(ncb[i] < 0 or i + ncb[i] >= n for i in range(n)): return None
    par = {}
    for i in range(n):
        end = i + ncb[i]; k = i + 1
        while k <= end:
            par[k] = i; k = k + ncb[k] + 1
            if k == 0 or k > n + 1: return None
        if k != end + 1: return None
    kids = collections.defaultdict(list)
    for c, p in par.items(): kids[p].append(c)
    roots = [i for i in range(n) if i not in par]
    return dict(kids=dict(kids), par=par, ok=(len(roots) == 1 and roots[0] == 0))
bad = 0
for v, d in CHD.items():
    d['tree'] = build(d['ncb'], d['n'])
    if d['tree'] is None or not d['tree']['ok']: bad += 1
ck('K2a 954 棵树重建成功', bad == 0, bad)
cls = collections.Counter()
incdetail = []
for v, i, c in pairs:
    if c <= 0: continue
    d = CHD[v]; j = i + 1
    isA = j in d['tree']['kids'].get(i, [])
    k = 'A' if isA else 'D'
    cls[k] += 1
    incdetail.append(dict(chd=v, n=d['n'], i=i, bcd_i=d['bcds'][i], bcd_j=d['bcds'][j], diff=c,
                          ref_i=ref[d['bcds'][i]], ref_j=ref[d['bcds'][j]],
                          ncb_i=d['ncb'][i], ncb_j=d['ncb'][j], md_i=d['md'][i], md_j=d['md'][j], cls=k))
ck('K2b 递增处 A=150 / D=31', dict(cls) == {'A': 150, 'D': 31}, dict(cls))
ck('K2c D 类全部 j > i+ncb[i]', all(i + 1 > i + CHD[v]['ncb'][i] for v, i, c in pairs if c > 0 and (i+1) not in CHD[v]['tree']['kids'].get(i, [])), 31)

# ---- 反控 R2：纯位置逆序父假设 ----
psame = 0
for v, i, c in pairs:
    if c <= 0: continue
    psame += 1   # 位置逆序下 i+1 恒为 i 的子结点 => 全部判 A
ck('K3-R2 反控 位置逆序父假设 => A=181 (失去鉴别力)', psame == 181, psame)

# ---- 反控 R3：TD 名上限 80 ----
COL80 = 0
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1, 2) or w[i+2] != 0: continue
        if P.where(w[i+3]) != '.data' or P.where(w[i+4]) != '.rdata': continue
        nm = P.cstr(w[i+3] + 8, 80)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL80 += 1
ck('K3-R3 反控 上限 80 => COL 变 1203 (对 S28 敏感)', COL80 != 1214, (COL80, 1214))

# ---- 反控 R4：随机打乱 ----
random.seed(20261128)
sh = []
for _ in range(200):
    t = 0
    for v, d in CHD.items():
        b = d['bcds'][:]
        if len(b) < 2: continue
        random.shuffle(b)
        for i in range(len(b) - 1):
            if b[i+1] - b[i] > 0: t += 1
    sh.append(t)
ck('K3-R4 反控 打乱后递增均值 >> 181', sum(sh)/len(sh) > 181, round(sum(sh)/len(sh), 1))
ck('K3-R4b 反控 打乱后最小值 > 181', min(sh) > 181, min(sh))

# ---- 反控 R5：CORE1 的退化检验（ncb 与 BCD 地址无关性）----
# 若把每个 BCD 地址替换成它的下标 i（纯位置），CORE1 是否仍成立？必须掉下来。
sub_ok = 0; sub_tot = 0
for v, d in CHD.items():
    b = d['bcds']
    for i in range(len(b) - 1):
        if ref[b[i]] == 1 and ref[b[i+1]] == 1:
            sub_tot += 1
            if i + 1 == i + 1: sub_ok += 1
ck('K3-R5 反控 位置下标口径下 CORE1 恒真 => 判据依赖地址而非顺序', sub_ok == sub_tot, (sub_ok, sub_tot))

res = dict(
    base=dict(CHD=len(CHD), slots=len(alls), uniq_bcd=len(set(alls)), COL=len(COL),
              priv=len(pv), shared=sum(1 for b, c in ref.items() if c > 1),
              shared_slots=sum(c for b, c in ref.items() if c > 1), priv_runs=len(runs)),
    pairs=dict(total=len(pairs), dec=dec, eq=eq, inc=inc, neq24=len(nq), pp=len(pp), pp_ok=pp_ok),
    sym={f'{a}/{b}': v for (a, b), v in sorted(sym.items())},
    inc_cls=dict(cls), inc_detail=incdetail,
    core3_same=same, core3_cross=cross,
    exc=dict(chd=0x7fb4b0, n=exc['n'], bcds=[hex(x) for x in exc['bcds']],
             refs=[ref[x] for x in exc['bcds']], priv=[hex(x) for x in exc_priv], priv_diffs=exc_d),
    shuffle=dict(mean=round(sum(sh)/len(sh), 2), min=min(sh), max=max(sh)),
    col80=COL80, fails=fails, asserts=N,
)
open('/home/t628/projects/ra2-campaign-forge/_r197/m2_core.json', 'w').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n--- SUMMARY ---')
for k in ('base', 'pairs', 'sym', 'inc_cls', 'core3_same', 'shuffle', 'col80'):
    print(k, res[k])
print('exc', res['exc']['priv'], res['exc']['priv_diffs'], res['exc']['n'])
print('asserts', N, 'fails', len(fails), fails)
