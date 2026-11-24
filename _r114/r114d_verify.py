#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114d_verify.py —— 给「回收的 29 个站点读得对不对」找一个**真有鉴别力**的校验。

背景（r114c 的 C2b FAIL 教给我的）：
  我原来的验证思路是「用 R112 已然定值的 313 个站点算出的逐 IID N 去卡新回收的 29 个」。
  实测一致 1 / 冲突 28 —— 但**冲突项全部是 n112.get(iid) is None**，
  即那 7 个 IID（0x7f7c90 / 0x7ea6e8 / 0x7e9b40 / 0x7e36c0 / 0x7f7cc0 / 0x7e9b20 / 0x7f7c20）
  在 R112 的 313 个定值站点里**一个都没有**（它们以前全被 ppv 检测失败挡住）。
  所以这条校验**结构上不可能成立**：基准集里没有这些 IID 的对照值。
  这是我这轮的判据设计错误，不是数据问题。但它揭示了一条真事实：
  **这 30 个 NA 站点是那 7 个 IID 的唯一（或几乎唯一）证据来源**，
  所以它们的正确性只能靠**另一条独立数据面**来验，不能靠"与旧值比"。

本轮采用的独立校验（三条，都不共用被检验的 .text 立即数）：
  D1 **精确 mdisp 等式（不是"落在集合里"）**：对每个站点 (类 C, IID i, N)，查 C 的 RTTI 里
     「mdisp 恰好 == N」的接口名集合，要求它包含链 A/B 独立判给 i 的名字。
     这比 r114a 的 A6（"N ∈ 所有 mdisp 的并集"）强得多：A6 的并集对每个类有几十个值，
     N 落进去近乎必然；D1 要求**名字对上**。
  D2 **共用体的跨类一致性**：9 个类共用 0x4f4240 这个 QI 体（18 个站点）。
     同一个函数体对同一个 IID 只能给一个 N —— 若我们读错，不同类会给出不同 N。
     这是**同一段字节被互斥的类同时检验**，不依赖任何外部值。
  D3 **A6 无鉴别力这件事的量化**：给出「N ∈ 该类 mdisp 并集」的随机基线，
     证明它为什么不能当验证（与执行员的意见②对账）。
"""
import collections, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r114_lib as R

ROOT = R.ROOT
OUT = os.path.join(ROOT, '_r114/r114d_verify.json')
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


sites = R.extract('new', 'fixed3')[0]
# IID -> 接口名：只用链 A/B 的独立结论（R112 落盘的 full_sets 里唯一的那一批）
d112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
NAME_OF = {}
for iid, info in d112['full_sets'].items():
    if isinstance(info, dict) and len(info.get('full', [])) == 1:
        NAME_OF[iid] = info['full'][0]
ck('D0 可用的「IID→接口名」唯一映射 %d 条（来自 R112 链 A/B，不来自本轮任何数据）'
   % len(NAME_OF), len(NAME_OF) >= 7, NAME_OF)

# ---------------- D1 精确 mdisp 等式 ----------------
def exact_mdisp_names(cls, N):
    """该类 RTTI 里 mdisp 恰好 == N 的基类名集合。"""
    r = R.RTTI[int(R.sym[cls]['vtable_va'], 16)]
    out = set()
    for nm, mds in r['bases'].items():
        if N in mds:
            out.add(nm)
    return out


rows = []
for k, iid, s0, i, N in sites:
    if N == 'NA':
        continue
    nm = NAME_OF.get(iid)
    if nm is None:
        continue
    got = exact_mdisp_names(k, int(N))
    rows.append({'class': k, 'iid': iid, 'name': nm, 'N': int(N),
                 'hit': nm in got, 'got_sample': sorted(got)[:6], 'n_got': len(got)})
ok1 = sum(1 for r in rows if r['hit'])
ck('D1 精确 mdisp 等式（不是"落在并集里"）：%d 个可判站点，该类的 RTTI 里'
   '"mdisp 恰好 == N" 的接口名集合**包含**链 A/B 判给该 IID 的名字 ⇒ %d/%d = %.1f%%'
   % (len(rows), ok1, len(rows), 100.0 * ok1 / len(rows)),
   ok1 == len(rows), {'miss': [r for r in rows if not r['hit']][:6]})

# 反控：把 N 随机换成别的值，D1 的命中率必须掉下来
random.seed(1143)
pool = sorted(set(int(x[4]) for x in sites if x[4] != 'NA'))
trial = 300
hitc = 0
for _ in range(trial):
    h = 0
    for r in rows:
        N2 = random.choice(pool)
        if r['name'] in exact_mdisp_names(r['class'], N2):
            h += 1
    hitc += h / len(rows)
base = 100.0 * hitc / trial
ck('D1b 反控：把 N 随机置换成池里任一值（%d 个候选值）后 D1 命中率 %.2f%%，实测 %.1f%% ⇒ '
   '富集 %.1f 倍。若随机也能接近 100%%，则 D1 无鉴别力'
   % (len(pool), base, 100.0 * ok1 / len(rows), (100.0 * ok1 / len(rows)) / base if base else 999),
   base < 60, {'rand_pct': round(base, 2), 'pool': pool})

# ---------------- D2 共用体的跨类一致性 ----------------
byentry = collections.defaultdict(list)
for k, iid, s0, i, N in sites:
    if N != 'NA':
        byentry[s0].append((k, iid, N))
shared = {hex(e): v for e, v in byentry.items() if len(set(x[0] for x in v)) >= 2}
inconsist = []
for e, v in byentry.items():
    per = collections.defaultdict(set)
    for k, iid, N in v:
        per[iid].add(N)
    for iid, ns in per.items():
        if len(ns) > 1:
            inconsist.append((hex(e), iid, sorted(ns)))
ck('D2 共用体跨类一致性：%d 个函数体被 ≥2 个类共用，逐体内逐 IID 的 N 必须唯一 —— '
   '违例 %d 个%s。这是**同一段字节被多个互斥的类同时检验**，不依赖任何外部值'
   % (len(shared), len(inconsist), inconsist[:4]),
   len(shared) >= 2 and not inconsist,
   {'shared_entries': list(shared.keys())[:6], 'inconsist': inconsist})

# ---------------- D3 A6 为什么无鉴别力（与执行员意见②对账） ----------------
def in_union(cls, N):
    r = R.RTTI[int(R.sym[cls]['vtable_va'], 16)]
    u = set()
    for v in r['bases'].values():
        u |= set(v)
    return N in u


real_union = sum(1 for k, iid, s0, i, N in sites if N != 'NA' and in_union(k, int(N)))
tot = sum(1 for k, iid, s0, i, N in sites if N != 'NA')
hitc2 = 0
for _ in range(trial):
    h = 0
    for k, iid, s0, i, N in sites:
        if N == 'NA':
            continue
        if in_union(k, random.choice(pool)):
            h += 1
    hitc2 += h / tot
base2 = 100.0 * hitc2 / trial
ck('D3 对账执行员意见②：A6 口径（N 属于该类全部基类 mdisp 的并集）实测 {:.1f}pct，'
   '随机 N 的基线 {:.1f}pct ⇒ 鉴别力仅 {:.1f} 倍。这就是它为什么在修前修后都满值、'
   '不能当验证的原因（并集对每个类有几十个值，落进去近乎必然）'.format(
       100.0 * real_union / tot, base2,
       (100.0 * real_union / tot) / base2 if base2 else 999)
   , base2 > 25 and (100.0 * real_union / tot) / base2 < 5, {'real_pct': round(100.0 * real_union / tot, 2), 'rand_pct': round(base2, 2)})

# ---------------- D4 N 值分布与 STATIC 单列 ----------------
dist = collections.Counter(str(N) for k, iid, s0, i, N in sites if N != 'NA')
na_cnt = sum(1 for k, iid, s0, i, N in sites if N == 'NA')
static_like = [(k, iid, hex(s0)) for k, iid, s0, i, N in sites if N == 'NA']
ck('D4 修完三处缺陷后的 N 分布 %s；残留 NA %d 个 %s 单列，**不并入 0**'
   % (dict(dist), na_cnt, static_like),
   na_cnt == 1 and static_like[0][0] == 'ApplicationClass',
   {'n_dist': dict(dist), 'na': static_like})

json.dump({'d1': {'ok': ok1, 'tot': len(rows), 'rand_pct': round(base, 2)},
           'd2': {'shared': len(shared), 'inconsist': inconsist},
           'd3': {'real_pct': round(100.0 * real_union / tot, 2), 'rand_pct': round(base2, 2)},
           'n_dist': dict(dist), 'rows': rows[:60], 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r114d] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
