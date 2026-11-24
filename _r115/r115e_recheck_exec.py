#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115e_recheck_exec.py —— 主会话对执行员 #1（deepseek）第二版 16 条断言的亲自复算（§2.12 规则 D）。

执行员第二版提出四条**针对主会话结论的实质反驳**，必须逐条独立验证：

  E-A13 「三条等式中只有 T==S 有内容」：
         E<=T 恒真（定义内含）、S>=T 恒真（COL 全在 .rdata）、S==B 恒真（同一集合）。
  E-A14 「混淆已定量」：260 个接口子对象 vtable 的集合 == 「非组尾 vtable」集合，
         故全部实测都无法区分「因为是接口所以槽数固定」与「因为排布紧邻所以三把尺子对齐」。
  E-A15 「260 个接口子对象的 1318 个槽里 1317 个是指令起点」，
         唯一例外 ILocomotion@0x7f5a24 槽 14 → 0x729e50。
  E-A16 「84 个类同时承 2..3 个接口，且各接口槽数互不相同 ⇒ 槽数不由类决定」。

若 E-A13/E-A14 成立，则主会话的 A3（三源同值）与 K3（随机基线）就**没有**它们声称的强度。
本脚本给出一条**新的、不被该混淆污染的对照**：按 CHD 组内位置分层，
比较「组尾」与「非组尾」的 T==S 比例；若接口子对象集合与「非组尾」集合完全相同，
则该分层**无法**区分二者 —— 必须另找对照。
"""
import json, os, sys, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r115')
import r115_lib as K

ROOT = K.ROOT
OUT = os.path.join(ROOT, '_r115/r115e_recheck_exec.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


C = K.census()
V2C, T, E, B, colptr = C['V2C'], C['T'], C['E'], C['B'], C['colptr']
IF = json.load(open(os.path.join(ROOT, '_r115/iface_subobj_full.json')))
IF = {nm: sorted(set(int(r[2], 16) for r in rows)) for nm, rows in IF.items()}
ifv = sorted(set(v for vs in IF.values() for v in vs))

S = {}
for v in V2C:
    n, _ = K.slot_scale_S(v)
    S[v] = n
_DEF = [v for v in V2C if S[v] is not None]

# ---- E-A13 三条等式是否恒真 ----
# S >= T：S 的定义是「扫到第一个合法 COL 值」，而 COL 全在 .rdata；T 数的是连续落在 .text 的 dword。
# 只要 vtable 的槽区里不含「值恰好是合法 COL」的 dword，S 就 >= T。这不是恒真，是可证伪的：
# 要找 S < T 的实例。若有 ⇒ 不恒真。
s_lt_t = [(hex(v), S[v], T[v]) for v in _DEF if S[v] < T[v]]
ck('E-A13a 执行员说「S>=T 恒真（COL 全在 .rdata）」—— 复算：S<T 的实例 %d 个；'
   'S==T 的 %d 个、S>T 的 %d 个 ⇒ 「恒真」说法需看判据：S>=T 成立但**不是定义内含**，'
   '而是「槽区不含合法 COL 值」这一实测事实'
   % (len(s_lt_t), sum(1 for v in _DEF if S[v] == T[v]), sum(1 for v in _DEF if S[v] > T[v])),
   len(s_lt_t) == 0,
   {'S_lt_T': s_lt_t[:5], 'eq': sum(1 for v in _DEF if S[v] == T[v]),
    'gt': sum(1 for v in _DEF if S[v] > T[v])})

# S == B：执行员说「同一集合」。复算是否逐点相等
ne = [(hex(v), S[v], B[v]) for v in _DEF if S[v] != B[v]]
ck('E-A13b 执行员说「S==B 恒真（同一集合）」—— 复算：逐点不等的 %d 个 ⇒ 确实逐点全等，'
   '但这是**两条独立实现的同值**（S 沿途扫值、B 用 colptr 排序后取下一个），'
   '不是「同一集合」的平凡推论：B 需要 colptr 索引，S 不需要' % len(ne),
   not ne, {'mismatch': ne[:5]})

# E <= T：执行员说「定义内含」。复算 E>T 的实例
e_gt_t = [(hex(v), E[v], T[v]) for v in _DEF if E[v] > T[v]]
ck('E-A13c 执行员说「E<=T 定义内含」。复算：E>T 的实例 %d 个 ⇒ 需注意 E 的判据是'
   '「在 STARTS 内且有填充」，T 是「落在 .text」，前者更严，理论上 E<=T；但这是**判据包含关系**'
   '（E 的条件是 T 的子集），确实恒真 —— 这点执行员说对了'
   % len(e_gt_t), len(e_gt_t) == 0, {'E_gt_T': e_gt_t[:5]})

# ---- E-A14：接口子对象集合 == 非组尾集合？----
bychd = collections.defaultdict(list)
for v in V2C:
    bychd[K.u32(V2C[v] + 0x10)].append(v)
last_in_group = set()
not_last = set()
for chd, vs in bychd.items():
    vs = sorted(vs)
    last_in_group.add(vs[-1])
    not_last.update(vs[:-1])
ifv_set = set(ifv)
ck('E-A14 【执行员的核心质疑】复算：接口子对象 vtable %d 个，「非组尾」vtable %d 个，'
   '两集合完全相同=%s（差集 %d / %d）⇒ 执行员说的混淆**成立**：'
   '本轮所有在接口子对象上做的「三源同值」实测，都无法区分'
   '「因为是接口所以槽数固定」与「因为排布紧邻所以三把尺子对齐」'
   % (len(ifv_set), len(not_last), ifv_set == not_last,
      len(ifv_set - not_last), len(not_last - ifv_set)),
   ifv_set == not_last,
   {'iface': len(ifv_set), 'not_last': len(not_last),
    'iface_minus_notlast': sorted(hex(x) for x in list(ifv_set - not_last))[:5],
    'notlast_minus_iface': sorted(hex(x) for x in list(not_last - ifv_set))[:5]})

# ---- 该混淆的实际影响：分层对照是否还有区分力 ----
strat = {'last': {'n': 0, 'eq': 0}, 'not_last': {'n': 0, 'eq': 0}}
for v in _DEF:
    k = 'last' if v in last_in_group else 'not_last'
    strat[k]['n'] += 1
    if S[v] == T[v]:
        strat[k]['eq'] += 1
r_last = strat['last']['eq'] / strat['last']['n'] if strat['last']['n'] else 0
r_not = strat['not_last']['eq'] / strat['not_last']['n'] if strat['not_last']['n'] else 0
ck('E-A14b 分层对照复算：组尾 T==S %d/%d=%.2f%%；非组尾 %d/%d=%.2f%% ⇒ '
   '分层「有差」但**非组尾层与接口子对象层完全重合**，故这个差**不能**证明'
   '「接口属性」——只能证明「非组尾位置」这个更弱的性质'
   % (strat['last']['eq'], strat['last']['n'], 100 * r_last,
      strat['not_last']['eq'], strat['not_last']['n'], 100 * r_not),
   strat['not_last']['eq'] == strat['not_last']['n'],
   {'last': r_last, 'not_last': r_not, 'n': strat})

# ---- 需要一条不被该混淆污染的新对照 ----
# 找「同类多接口」对照：同一个类里不同接口的槽数是否不同（执行员的 A16）。
sym = K.L.L.load_symbols()[0]
RT = K.L.RTTI
off = {v: K.u32(V2C[v] + 4) for v in V2C}
bychd_off = collections.defaultdict(dict)
for v in V2C:
    bychd_off[K.u32(V2C[v] + 0x10)][K.u32(V2C[v] + 4)] = v


def iface_at(cls):
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        return {}
    r = RT.get(int(e['vtable_va'], 16))
    if not r:
        return {}
    grp = bychd_off.get(r['chd'], {})
    nbc = K.u32(r['chd'] + 8)
    pbca = K.u32(r['chd'] + 0xc)
    at = collections.defaultdict(set)
    for i in range(nbc):
        bcd = K.u32(pbca + 4 * i)
        at[K.i32(bcd + 8)].add(K.L.L.demangle_type(K.u32(bcd)))
    out = {}
    for o, sv in grp.items():
        if o == 0 or o not in at:
            continue
        nm = [x for x in at[o] if len(x) > 1 and x[0] == 'I' and x[1].isupper() and x != 'IUnknown']
        if len(nm) == 1:
            out[nm[0]] = (o, sv)
    return out


multi = {}
for cls in sorted(sym):
    d = iface_at(cls)
    if len(d) >= 2:
        multi[cls] = {nm: S[sv] for nm, (o, sv) in d.items()}
differ = {c: d for c, d in multi.items() if len(set(d.values())) > 1}
ck('E-A16 【执行员最有分量的对照，复算】同时承 2 个及以上接口的类 %d 个；'
   '其中「各接口槽数互不相同」的 %d 个 ⇒ 同一类内部槽数就不同，'
   '故「槽数由承接类决定」被直接排除（例：%s）'
   % (len(multi), len(differ), list(differ.items())[:1]),
   len(multi) >= 80 and len(differ) == len(multi),
   {'n_multi': len(multi), 'n_differ': len(differ), 'sample': list(differ.items())[:2]})

# ---- E-A15 槽内容：1318 个槽里有几个不是指令起点 ----
_st = set(K.L.STARTS)
tot = 0
notstart = []
for nm, vs in IF.items():
    for v in vs:
        for k in range(S[v]):
            tot += 1
            d = K.u32(v + 4 * k)
            if d not in _st:
                notstart.append([nm, hex(v), k, hex(d), bool(K.TS <= d < K.TE)])
ck('E-A15 复算：260 个接口子对象的 %d 个槽里，不是已知指令起点的 %d 个（全在 .text 内）'
   '⇒ 执行员说对了；这也反向证明 T 尺（「落在 .text」）比 E 尺（「是指令起点」）更适合当槽数尺'
   % (tot, len(notstart)), tot == 1318 and len(notstart) == 1, {'total': tot, 'notstart': notstart})

# ---- E-A17 样本偏斜：5 个接口只有 1 个承接类 ⇒ 其「恒定」是单样本 ----
cnt = {nm: len(vs) for nm, vs in IF.items()}
single = sorted(nm for nm, n in cnt.items() if n == 1)
multi_n = sorted(nm for nm, n in cnt.items() if n > 1)
ck('E-A17 复算执行员的「样本偏斜」质疑：10 个接口里 %d 个只有 **1 个**承接类（%s），'
   '它们的「槽数恒定」是单样本、恒真且零信息量；真正多样本的只有 %d 个（%s）'
   '⇒ 「10 个接口全部恒定」这句话的**有效样本是 5 个**，不是 10 个'
   % (len(single), single, len(multi_n), [(nm, cnt[nm]) for nm in multi_n]),
   len(single) == 5 and len(multi_n) == 5, {'single': single,
                                            'multi': {nm: cnt[nm] for nm in multi_n}})

# ---- E-A18 三条 INoticeSink 记录的 COL.offset=21784 是虚基类偏移 ----
_offc = collections.Counter()
for nm, vs in IF.items():
    for v in vs:
        _offc[(nm, K.u32(V2C[v] + 4))] += 1
_big = [(k, c) for k, c in _offc.items() if k[1] > 0x2000]
ck('E-A18 复算：COL.offset > 0x2000 的接口子对象记录共 %d 条，全部是 INoticeSink 且 offset=21784(0x5518) '
   '（%s）⇒ 这是**虚基类子对象偏移**，与其他 257 条的小偏移不是同一形态；'
   '它把 INoticeSink 的样本从 78 抬到 81，但不改变 T 值（=1），'
   '「81 个类」不应被读成 81 个普通二级子对象'
   % (sum(c for _, c in _big), _big),
   len(_big) == 1 and _big[0][0][1] == 21784 and _big[0][1] == 3,
   {'large_offsets': [[list(k), c] for k, c in _big]})

# ---- E-A16b A16 的对照能否经受样本偏斜（执行员 A16 是唯一承重对照，必须加固）----
_pairs = collections.Counter(tuple(sorted(set(d.values()))) for d in multi.values())
_dep_on_single = sum(v for k, v in _pairs.items() if set(k) <= {1})
ck('E-A16b 【加固】A16 的 %d 个多接口类里，按「槽数取值组合」分布 %s —— '
   '**没有一个组合是 {1}**（即不依赖单样本接口），76 个是 (1,6)、6 个是 (8,50)、'
   '各 1 个是 (1,6,9) 与 (1,5,6,9,15)。(8,50) 这 6 个尤其干净：IPiggyback 与 ILocomotion '
   '都是多样本接口（6 类 / 12 类）⇒ A16 的对照**经受得住样本偏斜的批评**'
   % (len(multi), dict(_pairs)), _dep_on_single == 0,
   {'pairs': {str(k): v for k, v in _pairs.items()}})

out = {'E_A13': {'s_lt_t': s_lt_t, 's_eq_t': sum(1 for v in _DEF if S[v] == T[v]),
                 's_gt_t': sum(1 for v in _DEF if S[v] > T[v]), 'e_gt_t': e_gt_t},
       'E_A14': {'iface_n': len(ifv_set), 'not_last_n': len(not_last),
                 'identical': ifv_set == not_last},
       'stratified': {k: {'n': v['n'], 'eq': v['eq']} for k, v in strat.items()},
       'E_A16': {'n_multi': len(multi), 'n_differ': len(differ)},
       'E_A16b_pairs': {str(k): v for k, v in _pairs.items()},
       'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, %d FAIL' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
