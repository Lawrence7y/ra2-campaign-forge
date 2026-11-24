#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115a_bound.py —— 链 I：接口方法表槽数的「独立结构上界」S 尺（R114 下轮待办④的正面回答）。

问题（R114 遗留）：
  R113 链 H 证明「槽数是接口属性」（10 个接口在全部承接类上恒定），但那个槽数只有
  **T 尺**一把尺子（= 从 vtable 起连续落在 .text 的 dword 个数，上限 256 截断、实测最大 344）。
  T 尺一旦越界到常量池就会把常量当方法槽；R112 报的 256 正是截断饱和值。
  缺的是一条**判据来源独立**的尺子。

本轮给的尺子 S（Structural end）：
  沿 .rdata 线从 v 往后扫，第一个「其值本身是一个合法 COL 起点」的 dword 下标 p。
  依据是 MSVC 固定布局：vtable 前紧贴 4 字节 COL 指针，同 CHD 组 vtable 首尾相接
  （R113 的全 .rdata 普查已给 1214 个 vtable，每个 v-4 都是合法 COL）。
  故 p 必然是「下一个 vtable 的 COL 指针」，槽数 = p，且这是**精确末端**不是下界。

断言（全部可机检）：
  A1 S 尺对全 1214 个 vtable 全部可定（无 None）
  A2 全镜像 S == B（B 尺 = 下一个 COL 指针间距）——证明 S 与 B 是同一结构事实的两种读法，
     不是巧合；且 S 从未小于 T（结构末端不可能是 .text 归属的下界之下）
  A3 【核心】259 个接口子对象 vtable 上 S == T == B 全等（三把独立尺子同值）
  A4 【精确性】这 259 个 vtable 的边界 dword **全部**是合法 COL（259/259），
     即端点正好卡在下一个 COL 指针上 ⇒ S 是精确值
  A5 【无关性】这些 vtable 的 CHD 组内，vtable 与 vtable 之间**没有间隙 dword**
  K1 反控：边界后移一格 ⇒ 那一格不是 method entry（不得落在 .text+STARTS）
  K2 反控：边界前移一格 ⇒ 那一格必须是 .text（否则说明槽数被高估）
  K3 随机基线：全镜像 T==S 比例；接口子对象上为 100%，全镜像应明显低于 100%
  K4 反控：把 S 的判据「值 ∈ COL 集合」放宽成「值 ∈ .rdata」⇒ 必须出现 S < T 的违例
内存纪律：只读 census.pkl + 分块；不整段 detail=True；脚本带 timeout 由外层控制。
"""
import collections, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r115_lib as K

ROOT = K.ROOT
OUT = os.path.join(ROOT, '_r115/r115a_bound.json')
checks = []
C = K.census()
V2C, T, B, E, colptr = C['V2C'], C['T'], C['B'], C['E'], C['colptr']
checks_log = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---- S 尺全量 ----
S = {}
Sstop = {}
for v in sorted(V2C):
    n, stop = K.slot_scale_S(v)
    S[v] = n
    Sstop[v] = stop

# ---- A3 核心：接口子对象上 S==T==B ----
IF = {}
_FULLP = os.path.join(ROOT, '_r115/iface_subobj_full.json')
if os.path.exists(_FULLP):
    # 本轮重建的**未截断**全集（R113 落盘时 detail 被 v[:80] 静默截断，
    # INoticeSink 81 类只剩 80 行 ⇒ 260 收缩成 259。见 A0 断言）
    _J = json.load(open(_FULLP))
    IF = {nm: sorted(set(int(r[2], 16) for r in rows)) for nm, rows in _J.items()}
else:
    IF = K.iface_subobj_vts()

# ---- A0 R113 落盘截断缺陷复现与修复（写入纪律发现，必须如实报告）----
_TR = K.iface_subobj_vts()          # R113 落盘版（detail 被截断）
_trv = sorted(set(v for vs in _TR.values() for v in vs))
_fv = sorted(set(v for vs in IF.values() for v in vs))
ck('A0 R113 落盘 detail 被 v[:80] 静默截断：per_interface 记 INoticeSink=81 而 detail 只有 80 '
   '⇒ 总行数 %d 而真实 %d，distinct vtable %d 而真实 %d'
   % (sum(len(v) for v in _TR.values()), sum(len(v) for v in IF.values()), len(_trv), len(_fv)),
   len(_trv) == 259 and len(_fv) == 260,
   {'r113_truncated': {'rows': sum(len(v) for v in _TR.values()), 'vt': len(_trv)},
    'rebuilt_full': {'rows': sum(len(v) for v in IF.values()), 'vt': len(_fv)}})

none_s = sorted(hex(v) for v in V2C if S[v] is None)
# A1 的边界是**判据的真实范围**，不是缺陷：S 尺要求「下一个 vtable 的 COL 指针存在」。
# .rdata 里最后一个 vtable 之后没有任何 COL ⇒ S 无定义，必须显式钉住，不许悄悄放宽。
_DEG = ['0x7fa498']
ck('A1 S 尺有定义域边界：全 %d 个 vtable 中恰好 %d 个无定义，且正是 .rdata 里最后一个 vtable %s'
   '（.?AV_com_error@@，其后是 UTF-16 字面量 C\0I\0N\0O\0 无下一个 COL）−− 显式钉住、不默认值'
   % (len(V2C), len(none_s), none_s), none_s == _DEG,
   {'undefined': none_s, 'pinned': _DEG})

# ---- A2 S==B 与 S>=T ----
_DEF = [v for v in V2C if S[v] is not None]
ne_sb = [(hex(v), S[v], B[v]) for v in V2C if S[v] is not None and S[v] != B[v]]
ck('A2a 全镜像 S 尺与 B 尺逐点相等（%d/%d 个有定义者，违例 %d）' % (len(_DEF), len(V2C), len(ne_sb)),
   not ne_sb, ne_sb[:5] or 'equal')
lt_st = [(hex(v), S[v], T[v]) for v in V2C if S[v] is not None and S[v] < T[v]]
ck('A2b 全镜像 S 尺从不小于 T 尺（违例 %d）' % len(lt_st), not lt_st, lt_st[:5] or 'S>=T')

ifv = sorted(set(v for vs in IF.values() for v in vs))
bad3 = [(nm, hex(v), S[v], T[v], B[v]) for nm, vs in IF.items() for v in vs
        if not (S[v] == T[v] == B[v])]
ck('A3 【核心】%d 个接口子对象 vtable 上 S == T == B 全等（违例 %d）' % (len(ifv), len(bad3)),
   not bad3, bad3[:5] or 'all three scales agree')

# A3b 措辞消歧 + E 尺不可靠的实测（执行员 #1 独立复算报 257/260，让我发现「三者」有歧义）
# 执行员把 B 换成 E 得 257/260；复算确认差异**不是数据分歧，是尺子选择**。
badE = [(hex(v), S[v], T[v], E[v]) for v in ifv if not (S[v] == T[v] == E[v])]
ck('A3b 措辞消歧：A3 的三源是 S/T/B（口径上界），**不是** S/T/E。若换成 E 则 %d/%d 不成立'
   '（%s）—— 执行员 #1 正是按 S/T/E 算得 257/260，差异源于尺子选择不是数据分歧'
   % (len(badE), len(ifv), badE), len(badE) == 3,
   {'E_violations': badE})
# A3d 执行员 #1（deepseek）第二版提出的核心质疑，主会话复算成立（r115e 的 E-A14）：
# 260 个接口子对象 vtable 的集合 == 「CHD 组内非组尾」vtable 的集合（差集 0/0）。
# ⇒ A3 与 K3 的「100%」无法区分「因为是接口所以槽数固定」与
#   「因为位于组内非尾位置、排布紧邻所以三把尺子对齐」。**这是真实混淆，必须登记降级。**
_bychd_l = collections.defaultdict(list)
for _v in V2C:
    _bychd_l[K.u32(V2C[_v] + 0x10)].append(_v)
_last_s = set()
_notlast_s = set()
for _chd, _vs in _bychd_l.items():
    _vs = sorted(_vs)
    _last_s.add(_vs[-1])
    _notlast_s.update(_vs[:-1])
ck('A3d 【执行员 #1 的混淆成立，A3/K3 强度降级】接口子对象 vtable %d 个 与 「CHD 组内非组尾」'
   'vtable %d 个 **是同一个集合**（差集 %d/%d）⇒ A3 的 100%% 无法区分'
   '「接口属性」与「组内非尾位置的排布紧邻」这两种解释；K3 的 100%% vs 80.71%% 同理'
   '只能说明「非组尾位置」这个更弱的性质'
   % (len(ifv), len(_notlast_s), len(set(ifv) - _notlast_s), len(_notlast_s - set(ifv))),
   set(ifv) == _notlast_s,
   {'iface_n': len(ifv), 'notlast_n': len(_notlast_s)})

ck('A3c E 尺在 ILocomotion 上不可靠（这是本轮新增的反面结论）：12 个 ILocomotion 子对象'
   'vtable 的 T/S/B 全为 50，而 E 只有 {3,14,17,50} ⇒ 「连续像函数入口」这把尺子会把'
   'thunk/跳板序列判成非入口，故 E 不能当槽数尺，只能当「下界存在性」检查',
   set(E[v] for nm, vs in IF.items() if nm == 'ILocomotion' for v in vs) == {3, 14, 17, 50},
   {'loco12_E': sorted(set(E[v] for v in IF['ILocomotion']))})
per = {}
for nm, vs in IF.items():
    per[nm] = {'n_vt': len(vs), 'slots': sorted(set(S[v] for v in vs)),
               'T': sorted(set(T[v] for v in vs)), 'B': sorted(set(B[v] for v in vs)),
               'E': sorted(set(E[v] for v in vs))}
print('per-interface S/T/B/E:', json.dumps(per, ensure_ascii=False, sort_keys=True))

# ---- A4 精确性：边界 dword 全是 COL ----
bkind = collections.Counter()
noncol = []
for v in ifv:
    d = K.u32(v + 4 * S[v])
    k = K.boundary_kind(d)
    bkind[k] += 1
    if k != 'COL':
        noncol.append([hex(v), S[v], hex(d), k])
ck('A4 这 %d 个边界 dword 全部是合法 COL（%s），端点精确卡在下一个 COL 指针上'
   % (len(ifv), dict(bkind)), not noncol, noncol[:5] or ('COL %d/%d' % (bkind['COL'], len(ifv))))

# 对照：全镜像 1214 个的边界种类（含非 COL 者，说明 COL 100% 不是平凡结论）
ball = collections.Counter(K.boundary_kind(K.u32(v + 4 * S[v])) for v in V2C if S[v] is not None)
# 自错 S-15：初稿把「边界是 COL」当成 A4 的独立证据。复算发现全镜像 1213/1213 也是 COL ——
# 因为 S 尺的**定义本身**就是「扫到第一个 COL 值」，故该性质恒真、零鉴别力。
# 如实降级：A4 只登记「端点位置的构成」，不作独立性证据；独立性由 A3（三把独立尺子同值）承担。
ck('A4b 自错 S-15 登记：全镜像 %d 个有定义 vtable 的边界种类 %s —— 恒为 COL 是 S 尺定义所致，'
   '零鉴别力，故 A4 不作为独立证据，只登记端点构成；独立性由 A3（T/S/B 三源同值）承担'
   % (sum(ball.values()), dict(ball)), ball['COL'] == sum(ball.values()), dict(ball))

# ---- A5 CHD 组内无间隙 ----
bychd = collections.defaultdict(list)
for v in V2C:
    bychd[K.u32(V2C[v] + 0x10)].append(v)
gaps = 0
for chd, vs in bychd.items():
    vs = sorted(vs)
    for a, b in zip(vs, vs[1:]):
        if a + 4 * S[a] != b - 4:      # a 末端之后应紧接 b 的 COL 指针
            gaps += 1
ck('A5 同 CHD 组内相邻 vtable 首尾相接（末端+COL 指针 == 下一个 vtable 起点），间隙 %d 个'
   % gaps, gaps == 0, {'groups': len(bychd), 'gaps': gaps})

# ---- K1 边界后移一格不是 method entry ----
k1 = [hex(v) for v in ifv if K.entry_at(K.u32(v + 4 * S[v]))]
ck('K1 反控：边界后移一格（当作多一槽）⇒ %d/%d 个落在「.text 且是指令起点」'
   % (len(k1), len(ifv)),
   len(k1) == 0, k1[:5] or 'none')

# ---- K2 边界前移一格必须是 .text ----
k2bad = [hex(v) for v in ifv if not (K.TS <= K.u32(v + 4 * (S[v] - 1)) < K.TE)]
ck('K2 反控：边界前移一格（当作少一槽）⇒ %d 个不再是 .text（应为 0，否则槽数被高估）'
   % len(k2bad), not k2bad, k2bad[:5] or 'all still .text')

# ---- K3 随机基线 ----
eq_all = sum(1 for v in V2C if S[v] is not None and S[v] == T[v])
ck('K3 随机基线：全镜像 T==S %d/%d = %.2f%%；接口子对象 %d/%d = 100.00%% ⇒ 三尺同值不是平凡性质'
   % (eq_all, len(_DEF), 100.0 * eq_all / len(_DEF),
      sum(1 for v in ifv if S[v] == T[v]), len(ifv)),
   len(ifv) == sum(1 for v in ifv if S[v] == T[v]) and eq_all < len(_DEF),
   {'all_eq': eq_all, 'all_n': len(_DEF)})

# ---- K4 放宽判据必须出现 S<T 违例 ----
# 反控的正确形态（自错 S-16）：初稿把「放宽成 ∈ .rdata」作用在**接口子对象**上，
# 实测 0/260 违例 —— 因为接口子对象的边界前 dword 全是方法入口，落在 .text 而非 .rdata，
# 放宽判据够不到。**反控打在不下手的地方 = 没反控**。改打在**真会出差异的全镜像域**上。
def s_loose(v):
    n = 0
    while v + 4 * n + 4 <= K.RD1 and n < 4000:
        d = K.u32(v + 4 * n)
        if K.RD0 <= d < K.RD1:           # 放宽：只要值落在 .rdata
            return n
        n += 1
    return None


loose_diff = [(hex(v), S[v], s_loose(v), T[v]) for v in V2C
              if S[v] is not None and s_loose(v) is not None and s_loose(v) != S[v]]
ck('K4 反控（打在全镜像域）：把 S 判据从「值 ∈ 合法 COL」放宽成「值 ∈ .rdata」⇒ %d 个 vtable '
   '的槽数被改判（宽判据撞上 vtable 中间的常量池 dword）⇒「合法 COL」这一步收紧有牙'
   % len(loose_diff), len(loose_diff) >= 1, loose_diff[:5])

# ---- K5 反向：T 尺单独用会低估，故 S 尺不是 T 尺的复述 ----
t_lt_s = [(hex(v), T[v], S[v]) for v in V2C if S[v] is not None and T[v] < S[v]]
ck('K5 【链 H 的补强】T 尺单独用会在 %d 个 vtable 上**低估**槽数（T<S，如 %s）'
   '⇒ S 尺不是 T 尺的复述；而在 260 个接口子对象上 T==S 全等 ⇒ 接口方法表恰好无常量池穿插'
   % (len(t_lt_s), t_lt_s[:3]), len(t_lt_s) >= 1, {'n': len(t_lt_s), 'sample': t_lt_s[:3]})

out = {'scale_S': {hex(v): S[v] for v in V2C if S[v] is not None},
       'per_interface': per,
       'iface_vt_count': len(ifv),
       'boundary_kinds_iface': dict(bkind),
       'boundary_kinds_all': dict(ball),
       'T_eq_S_all': eq_all, 'T_eq_S_all_n': len(_DEF),
       'S_undefined': none_s,
       'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, %d FAIL' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
