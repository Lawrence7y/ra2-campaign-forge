#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r114b_audit_a3.py —— 亲自复算审计员 #202 对 R113 链 H（接口方法表槽数是接口属性）的 FAIL 判定。

审计员判 A3 = FAIL，理由两条：
  (1) 我的反控①（按 CHD 组内序号错位一档 ⇒ 3 接口不再恒定）**没有牙**：
      他构造了「同类内 k 个接口的 vtable 按固定轮换 r 重排，遍历全部 r」，10 个接口
      仍然全恒定（bad=0）⇒ 我的反控只否掉了一种特定错位方式，不构成对判据的否证。
  (2) C2 的「恒定」判据本身**没有区分力**：它只能说明槽数多重集稳定，
      不能指出「哪张 vtable 属于哪个接口」，因此也就不构成「槽数是接口属性」的证据。

本轮任务（全部由主会话亲自复算，不采信审计员结论）：
  B1 复现审计员的轮换反控：同类内固定轮换 r（遍历全部 r），10 接口是否仍全恒定
  B2 更强的零模型（这才是我该写的反控）：**每个类内部独立随机置换 vtable→接口的分配**，
     N 次试验，统计「逐接口槽数不恒定的接口数」的分布。若随机置换也常给出 0 违例，
     C2 的恒定就没有区分力 —— 必须如实认下来
  B3 判据到底证成了什么：给出一个**有区分力**的替代判据并实测
     （COL.offset 索引 vs 随机的「同组任意偏移」：真索引的 T 多重集必须显著更"整齐"）
  B4 结论裁定：R113 链 H 的哪一句必须撤回、哪一句仍站得住
"""
import collections, json, os, random, sys

sys.path.insert(0, os.path.join('/home/t628/projects/ra2-campaign-forge', '_r113'))
import r113_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r114/r114b_a3.json')
u32, i32 = L.u32, L.i32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


C = L.census()
V2C, T = C['V2C'], C['T']
off = {v: u32(V2C[v] + 4) for v in V2C}
sym, VT = L.L.load_symbols()
RT = L.RTTI

# CHD 组：chd -> {COL.offset: vtable}
bychd = collections.defaultdict(dict)
for v in V2C:
    bychd[u32(V2C[v] + 0x10)][off[v]] = v


def iface_at(cls):
    """{接口名: (offset, vtable)}，只收 offset!=0 且该 offset 上恰好一个接口名。"""
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        return {}
    r = RT.get(int(e['vtable_va'], 16))
    if not r:
        return {}
    grp = bychd.get(r['chd'], {})
    nbc = u32(r['chd'] + 8)
    pbca = u32(r['chd'] + 0xc)
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


# 真实测量：逐接口槽数
per = collections.defaultdict(collections.Counter)
for cls in sorted(sym):
    for nm, (o, sv) in iface_at(cls).items():
        per[nm][T[sv]] += 1
real_viol = {nm: dict(c) for nm, c in per.items() if len(c) > 1}
ck('B0 基线复算：%d 个接口，逐接口槽数不恒定的 %d 个（R113 C2 报 0）'
   % (len(per), len(real_viol)),
   len(real_viol) == 0 and len(per) >= 9,
   {nm: dict(per[nm]) for nm in list(per)[:12]})

# ---------------- B1 复现审计员的轮换反控 ----------------
byk = collections.defaultdict(list)
for cls in sorted(sym):
    ia = iface_at(cls)
    if ia:
        byk[len(ia)].append((cls, ia))

rot_rows = []
for k in sorted(byk):
    if k < 2:
        continue
    for r in range(1, k):
        alt = collections.defaultdict(set)
        for cls, ia in byk[k]:
            named = sorted(ia.items(), key=lambda kv: kv[1][0])
            vals = [ia[nm][1] for nm, _ in named]
            for j, (nm, _) in enumerate(named):
                alt[nm].add(T[vals[(j + r) % k]])
        bad = sum(1 for s in alt.values() if len(s) > 1)
        rot_rows.append({'k': k, 'r': r, 'bad': bad})
ck('B1 复现审计员的反控：同类内固定轮换 r（遍历全部 r）后，逐接口槽数不恒定的个数 —— '
   '实测 %s。若全为 0，则 R113 的 C3 反控**没有牙**，审计员的 FAIL 成立'
   % ([(x['k'], x['r'], x['bad']) for x in rot_rows],),
   all(x['bad'] == 0 for x in rot_rows), rot_rows)

# ---------------- B2 更强的零模型：同类内独立随机置换 ----------------
# 这才是 C2 该配的反控。零假设：vtable→接口的对应关系是任意的（只要在同一类内）。
# 若随机置换下「逐接口恒定」也常成立，则 C2 的恒定不能证明映射正确。
random.seed(1141)
trials = 2000
dist = collections.Counter()
for _ in range(trials):
    alt = collections.defaultdict(set)
    for cls in sorted(sym):
        ia = iface_at(cls)
        if not ia:
            continue
        items = list(ia.items())
        vals = [v[1] for nm, v in items]
        random.shuffle(vals)
        for (nm, _), sv in zip(items, vals):
            alt[nm].add(T[sv])
    bad = sum(1 for s in alt.values() if len(s) > 1)
    dist[bad] += 1
zero_share = 100.0 * dist[0] / trials
ck('B2 强零模型（同类内独立随机置换 vtable→接口，%d 次）：得到「0 个接口不恒定」的次数占 %.1f%%，'
   '违例数分布 %s ⇒ %s'
   % (trials, zero_share, dict(sorted(dist.items())[:8]),
      '随机置换也常给出 0 违例，C2 的「恒定」**没有区分力**' if zero_share > 5
      else '随机置换很少给出 0 违例，C2 有区分力'),
   True, {'zero_share_pct': round(zero_share, 2), 'dist': dict(sorted(dist.items())[:10])})

# ---------------- B3 有区分力的替代判据 ----------------
# 真正的鉴别问题是：**COL.offset 这个索引是不是真的把「同一个接口」的 vtable 聚到一起了？**
# 若接口的槽数是接口属性，那么「同一接口名」的 vtable 槽数应当**只有一个值**（已测）。
# 但 B2 说明这只要求多重集稳定。有区分力的对照：拿同一个类里**别的 offset** 的 vtable
# 去冒充该接口 ⇒ 跨类槽数必然散开（因为被冒充的是不同接口/不同类的表）。
# 关键改进：随机置换**跨类共享同一个置换**（保持"同一接口在所有类里都换成同一张表"），
# 这才是真正会破坏恒定的零模型；若无牙，说明这些接口的槽数恰好都相同。
alt2 = collections.defaultdict(set)
for cls in sorted(sym):
    ia = iface_at(cls)
    if not ia:
        continue
    named = sorted(ia.items(), key=lambda kv: kv[0])            # 按接口名排序（跨类一致）
    vals = [v[1] for nm, v in sorted(ia.items(), key=lambda kv: kv[0])]
    for j, (nm, _) in enumerate(named):
        alt2[nm].add(T[vals[(j + 1) % len(named)]])             # 全局一致的错位
bad2 = {nm: sorted(s) for nm, s in alt2.items() if len(s) > 1}
ck('B3 有区分力的对照（跨类一致错位一档，按接口名排序）：%d 个接口槽数散开 %s ⇒ '
   '「同一接口在所有类上槽数唯一」对**全局一致**的错位是敏感的'
   % (len(bad2), list(bad2.items())[:4]),
   len(bad2) >= 3, {'bad': {k: v[:4] for k, v in list(bad2.items())[:6]}})

# ---------------- B4 另一条独立判据：同一接口跨类时「逐槽实现指针集合」必须小 ----------------
# 初稿这条写成「子对象 vtable 的 slot0 体内 cmpsd 含该接口 IID」——**前提错了**：
# 只有 COM 子对象（IRTTITypeInfo/IPiggyback 等）的 slot0 才是 QI；非 COM 的子对象
# （如 INoticeSink 的 slot0）根本不是虚函数入口，实测 slot0 = 0x4246c83（不在 .text，body 为空）。
# 断言当场 FAIL 抓出（0/82）。改成一个不依赖"是不是 COM"的判据：
#   若 COL.offset 索引正确，则「同一接口在不同类里的第 j 个槽」应当指向**少数几个实现**
#   （同一份代码被多类复用，或每个类各一份）；而如果索引是错的（把不同接口的表混在一起），
#   逐槽指针集合会显著变大。
def slot_ptrs(sv, t, cap=64):
    out = []
    for j in range(min(t, cap)):
        v = u32(sv + 4 * j)
        out.append(v)
    return out


per_slot = collections.defaultdict(lambda: collections.defaultdict(set))
for cls in sorted(sym):
    for nm, (o, sv) in iface_at(cls).items():
        t = T[sv]
        for j, pv in enumerate(slot_ptrs(sv, t)):
            per_slot[nm][j].add(pv)

rows4 = {}
for nm in sorted(per_slot):
    sets = per_slot[nm]
    rows4[nm] = {'t': T[iface_at([c for c in sym if nm in iface_at(c)][0])[nm][1]],
                 'slots': len(sets),
                 'max_distinct': max(len(s) for s in sets.values()),
                 'total_distinct': sum(len(s) for s in sets.values())}
# 反控：把每个接口的 vtable 换成同组里**另一个 offset** 的 vtable 再量同样指标
per_slot_ctl = collections.defaultdict(lambda: collections.defaultdict(set))
for cls in sorted(sym):
    e = sym.get(cls)
    if not e or not e.get('vtable_va'):
        continue
    r = RT.get(int(e['vtable_va'], 16))
    if not r:
        continue
    grp = sorted(bychd.get(r['chd'], {}).items())
    ia = iface_at(cls)
    if not ia:
        continue
    named = sorted(ia.items(), key=lambda kv: kv[0])
    vals = [v[1] for nm, v in sorted(ia.items(), key=lambda kv: kv[0])]
    for j, (nm, _) in enumerate(named):
        sv2 = vals[(j + 1) % len(vals)]
        for s, pv in enumerate(slot_ptrs(sv2, T[sv2])):
            per_slot_ctl[nm][s].add(pv)
rows4_ctl = {}
for nm in sorted(per_slot_ctl):
    sets = per_slot_ctl[nm]
    rows4_ctl[nm] = {'max_distinct': max(len(s) for s in sets.values()),
                     'total_distinct': sum(len(s) for s in sets.values())}
ck('B4 独立判据（不依赖"是不是 COM"）：同一接口跨类时逐槽实现指针的 distinct 数 —— '
   '真索引 %s；全局一致错位后 %s ⇒ 真索引的逐槽指针集合明显更小，说明 COL.offset 确实'
   '把同一接口的方法表聚在一起'
   % ({k: v['total_distinct'] for k, v in rows4.items()},
      {k: v['total_distinct'] for k, v in rows4_ctl.items()}),
   sum(v['total_distinct'] for v in rows4.values())
   < sum(v['total_distinct'] for v in rows4_ctl.values()),
   {'real': rows4, 'control': rows4_ctl})

json.dump({'real_viol': real_viol, 'rot': rot_rows,
           'rand_dist': dict(sorted(dist.items())[:10]), 'zero_share_pct': round(zero_share, 2),
           'global_shift_bad': {k: v[:6] for k, v in list(bad2.items())[:8]},
           'slot_ptr_real': {k: v for k, v in rows4.items()},
           'slot_ptr_control': {k: v for k, v in rows4_ctl.items()},
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r114b] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
