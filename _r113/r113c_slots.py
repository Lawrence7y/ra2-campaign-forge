#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113c_slots.py —— 链 H：接口方法表的槽数（R111 §EM10① 与 R112 下轮待办③ 的正面回答），
并**纠正 R112 一处量错了表**。

R112 的做法（r112c）：对每个 IID 取其认领类的「子对象 vtable」，槽数 = 从 vtable 起连续落在
.text 的 dword 个数（上限 256）。问题在于：**N==0 的 IID，其子对象就是对象本身**，
所以那个 vtable 是**类的 vtable**，不是该接口的方法表。R112 对 0x7f7c70/0x7f7c80 报出
「15 种槽数含 256」正是因为这个 —— 它把 77 个不同类的完整 vtable 当成了 IPersistStream 的方法表。
**这不是数据脏，是判据量错了对象。** 本轮把两类分开：
  N != 0 的 IID：子对象 vtable 真的是该接口的方法表 ⇒ 可读槽数
  N == 0 的 IID：子对象就是对象 ⇒ 只能从「该类 vtable 的头部」推断，不能直接读出接口槽数

本轮新增的独立判据（这是链 H 的核心，不依赖任何外部头文件）：
  **同一个接口嵌进不同类时，它的方法表槽数必须完全相同。**
  这条是自洽性约束，不是定义：不同类的自身方法数不同（AircraftClass 341、UnitClass 344、
  AbstractClass 24…），若「槽数」量的是类而不是接口，那么同一个接口在不同的类上必然给出
  不同数字。反之，若在所有嵌入类上恒定，则该数字只能是接口自身的属性。

断言：
  C1 普查与 R112 一致的部分：0x7f7ca0 的 77–78 个 IClassFactory 子对象槽数全为 5
  C2 N!=0 的接口逐个统计「槽数 × 出现类数」，每个接口必须**只有一个槽数取值**
  C3 反控：把「按 COL.offset 索引子对象」换成「按 CHD 组内顺序索引」⇒ 同接口槽数不再恒定
  C4 反控：把槽数尺子从 T 换成「CHD 组上界 B」⇒ 部分接口出现多个取值（B 含数据块）
  C5 R112 的 0x7f7c70/0x7f7c80「15 种槽数含 256」被复现，并给出归因（N==0 ⇒ 量到类 vtable）
  C6 12 个 Locomotion 类的 symbols.tab 缺陷单列：symbols 记的 vtable 是 offset==4 的子对象，
     其真实类 vtable 在 offset==0，两者槽数分别为 50 与 10
内存纪律：disasm_lite；只读已落盘的 census.pkl，不重扫。
"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r113_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r113/r113c_slots.json')
raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


C = L.census()
V2C, T, E, B = C['V2C'], C['T'], C['E'], C['B']
off = {v: u32(V2C[v] + 4) for v in V2C}
sym, VT = L.L.load_symbols()
RT = L.RTTI
B112 = json.load(open(os.path.join(ROOT, '_r112/r112b_qi_offset.json')))
C112 = json.load(open(os.path.join(ROOT, '_r112/r112c_subobj.json')))

n_all = sorted(C112['subobj']['0x7f7ca0']['vts'])
ck('C1 0x7f7ca0（IClassFactory）的 %d 个装配点 vtable 槽数全为 5（T 尺），与 R112 一致'
   % len(n_all), set(T[v] for v in n_all) == {5}, sorted(set(T[v] for v in n_all)))

# ---- 按 CHD 组 + COL.offset 索引子对象 ----
bychd = collections.defaultdict(dict)
for v in V2C:
    bychd[u32(V2C[v] + 0x10)][off[v]] = v


def iface_at(cls):
    """返回 {接口名: (该接口子对象在对象内的 offset, 子对象 vtable)}，只收非 IUnknown、
    且该 offset 上**恰好只有一个**接口名（有歧义就不猜）。"""
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        return {}
    vt = int(e['vtable_va'], 16)
    r = RT.get(vt)
    if not r:
        return {}
    grp = bychd.get(r['chd'], {})
    nbc = u32(r['chd'] + 8); pbca = u32(r['chd'] + 0xc)
    at = collections.defaultdict(set)
    for i in range(nbc):
        bcd = u32(pbca + 4 * i)
        at[i32(bcd + 8)].add(L.L.demangle_type(u32(bcd)))
    out = {}
    for o, sv in grp.items():
        if o == 0 or o not in at:
            continue
        nm = [x for x in at[o] if len(x) > 1 and x[0] == 'I' and x[1].isupper() and x != 'IUnknown']
        if len(nm) == 1:
            out[nm[0]] = (o, sv)
    return out


per = collections.defaultdict(collections.Counter)   # 接口 -> Counter(槽数 -> 类数)
detail = collections.defaultdict(list)
for cls in sorted(sym):
    for nm, (o, sv) in iface_at(cls).items():
        per[nm][T[sv]] += 1
        detail[nm].append([cls, o, hex(sv), T[sv], E[sv], B[sv]])

rows = {nm: dict(c) for nm, c in per.items()}
multi = {nm: c for nm, c in rows.items() if len(c) > 1}
ck('C2 N!=0 的 %d 个接口，逐个的「槽数 × 类数」都只有**一个**取值 —— 违例 %d 个 %s'
   % (len(rows), len(multi), multi),
   len(rows) >= 9 and not multi, rows)
# 承接类的自身 vtable 长度跨度（实测 1..344），而同一个接口在所有承接类上槽数恒定 ⇒
# 「槽数」是接口的属性而非类的属性。这是链 H 的鉴别力来源，故把跨度一起报出来。
span = {'min': min(T.values()), 'max': max(T.values())}
ck('C2b 定死的最硬几项：INoticeSink=1（%d 类）/ IRTTITypeInfo=6（%d 类）/ ILocomotion=50（%d 类）/'
   ' IPiggyback=8（%d 类）；而全镜像类 vtable 长度跨度 %d..%d ⇒ 槽数恒定不可能是类属性'
   % (rows['INoticeSink'][1], rows['IRTTITypeInfo'][6], rows['ILocomotion'][50],
      rows['IPiggyback'][8], span['min'], span['max']),
   rows['INoticeSink'] == {1: 81} and rows['IRTTITypeInfo'] == {6: 78}
   and rows['ILocomotion'] == {50: 12} and rows['IPiggyback'] == {8: 6}, rows)


# ---- C3 反控：按 CHD 组内顺序索引而不是按 COL.offset ----
def alt_index(cls):
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        return {}
    r = RT.get(int(e['vtable_va'], 16))
    if not r:
        return {}
    grp = sorted(bychd.get(r['chd'], {}).items())          # 按 offset 排序后的 (offset, vt)
    named = sorted(iface_at(cls).items(), key=lambda kv: kv[1][0])
    out = {}
    for (nm, (o, sv)), (o2, sv2) in zip(named, grp):        # 人为错位：按序号对齐
        out[nm] = sv2
    return out


alt = collections.defaultdict(set)
for cls in sorted(sym):
    for nm, sv in alt_index(cls).items():
        alt[nm].add(T[sv])
alt_bad = {nm: sorted(s) for nm, s in alt.items() if len(s) > 1}
ck('C3 反控：改按「CHD 组内序号」索引子对象（错位一档）⇒ %d 个接口的槽数不再恒定，'
   '证明 C2 的恒定来自 COL.offset 这个真实索引，不是凑巧' % len(alt_bad),
   len(alt_bad) >= 3, {k: v[:4] for k, v in list(alt_bad.items())[:4]})

# ---- C4 反控：用「类自身 vtable」（COL.offset==0）冒充接口方法表 = R112 犯的那个错 ----
# 初稿的反控是「把尺子换成 B」，实测 0 个接口出现多值 —— 因为这些子对象 vtable 的 B 恰好都等于 T，
# B 对它们没有区分力（B 只对「组内含数据块」的 vtable 才是真上界）。**换错反控 = 没反控**。
# 改用一个真正会失败的错法：拿 offset==0 的那份（类 vtable）当接口方法表。
perW = collections.defaultdict(set)
for cls in sorted(sym):
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        continue
    r = RT.get(int(e['vtable_va'], 16))
    if not r:
        continue
    prim = bychd.get(r['chd'], {}).get(0)
    if prim is None or T[prim] == 0:
        continue
    for nm in iface_at(cls):
        perW[nm].add(T[prim])
badW = {nm: sorted(s) for nm, s in perW.items() if len(s) > 1}
ck('C4 反控：拿「类自身 vtable」（COL.offset==0）冒充接口方法表 ⇒ %d 个接口的「槽数」不再恒定'
   '（这正是 R112 对 N==0 的 IID 做的事）—— 证明 C2 的恒定是真信号' % len(badW),
   len(badW) >= 5, {k: v[:5] for k, v in list(badW.items())[:4]})

# ---- C5 R112 的 0x7f7c70/0x7f7c80「15 种槽数含 256」复现与归因 ----
sc = C112['subobj']['0x7f7c80']['slot_counts']
ck('C5 R112 对 0x7f7c70/0x7f7c80 报的槽数分布（15 种、含 256）可复现：%s' % (sc,),
   len(sc) == 15 and 256 in sc, sc)
n0 = [v for v in C112['subobj']['0x7f7c80']['vts']]
ck('C5b 归因：这 77 个子对象的 COL.offset 全为 0 ⇒ 它们就是 77 个**类**的 vtable，'
   '其槽数（24/27/40/48/122…/256）是类方法数，不是 IPersistStream 的方法表长度',
   set(off[v] for v in n0) == {0} and set(T[v] for v in n0) != {8},
   {'offsets': sorted(set(off[v] for v in n0)), 'T_sample': sorted(set(T[v] for v in n0))[:6]})
ck('C5c 且 T 尺的 256 上限是人为截断（实测 max T=344，有 %d 个 vtable 超过 256）⇒ '
   'R112 报的 256 是饱和值不是测量值' % sum(1 for v in T if T[v] > 256),
   sum(1 for v in T if T[v] > 256) > 0, [(hex(v), T[v]) for v in sorted(T) if T[v] > 256])

# ---- C6 12 个 Locomotion 类的 symbols 记录缺陷 ----
loc12 = ['DriveLocomotionClass', 'DropPodLocomotionClass', 'FlyLocomotionClass',
         'HoverLocomotionClass', 'JumpjetLocomotionClass', 'LocomotionClass',
         'MechLocomotionClass', 'RocketLocomotionClass', 'ShipLocomotionClass',
         'TeleportLocomotionClass', 'TunnelLocomotionClass', 'WalkLocomotionClass']
bad6 = []
for n in loc12:
    sv = int(sym[n]['vtable_va'], 16)
    o = off[sv]
    prim = bychd[RT[sv]['chd']].get(0)
    if not (o == 4 and prim is not None and T[sv] == 50 and 10 <= T[prim] <= 12):
        bad6.append([n, o, T[sv], hex(prim) if prim else None, T[prim] if prim else None])
ck('C6 12 个 Locomotion 类：symbols.json 记的 vtable 都是 COL.offset==4 的 **ILocomotion 子对象**'
   '（槽数全为 50），而它们的**类 vtable** 在 offset==0（槽数 10，Teleport 为 12：它多两个自有方法）'
   '—— 12/12 一致，违例 %d' % len(bad6), not bad6,
   bad6 or {'sym_T': sorted(set(out_T for out_T in
                                 [C['T'][int(sym[n]['vtable_va'], 16)] for n in loc12])),
            'primary_T': sorted(set(C['T'][bychd[RT[int(sym[n]['vtable_va'], 16)]['chd']][0]]
                                    for n in loc12))})

out = {'per_interface': rows, 'detail': {k: v[:80] for k, v in detail.items()},
       'r112_slot_counts_7f7c80': sc, 'loc12_primary_vs_sym': {
           n: {'sym_vt': sym[n]['vtable_va'], 'sym_off': off[int(sym[n]['vtable_va'], 16)],
               'sym_T': T[int(sym[n]['vtable_va'], 16)],
               'primary_vt': hex(bychd[RT[int(sym[n]['vtable_va'], 16)]['chd']][0]),
               'primary_T': T[bychd[RT[int(sym[n]['vtable_va'], 16)]['chd']][0]]}
           for n in loc12}, 'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113c] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
