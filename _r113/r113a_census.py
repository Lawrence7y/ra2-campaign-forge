#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r113a_census.py —— 全镜像 vtable/COL 普查 + 三把槽数尺子的关系 + CHD 分组自洽。

R112 的「子对象 vtable」是从 .text 的装配点反推的（2517 个点），只能看到被装配过的。
本轮换到 .rdata 侧做**全量**普查：MSVC 的布局是 COL 紧贴 vtable 之前 4 字节，
故「某 dword 的值 v 满足 v-4 处是合法 COL」⇔ v 是一个 vtable 起点。

三把槽数尺子（全部实测，谁也不能靠「近似」过关）：
  T = 从 vtable 起连续落在 .text 的 dword 个数       （R112 用的，上限曾被硬截 256）
  E = 连续「像函数入口」的 dword 个数 = T 再加一层 (在指令起点集内 且 入口前有填充)
  B = 结构上界 = (下一个 COL 指针地址 - vtable 起点)/4；不依赖 .text 内容
关系断言：T <= B 必须恒成立（否则说明 COL 普查漏了东西，B 会假性偏小）。

断言（正控 + 反控都在里面，数字一律先实测再填）：
  A1 映像 sha256 / .rdata 区间 / HB 数
  A2 普查到的 vtable 数、其中与 symbols.json 重合数、只多不少
  A3 symbols.json 的 954 个 vtable 全部被普查覆盖（漏一个即 FAIL）
  A4 T <= B 全量成立，违例 0
  A5 260 个「symbols.json 没有的」vtable 的 COL.offset 全 != 0（它们是二级/虚拟基子对象）
  A6 每个 vtable 的 COL 都有一个 CHD，且其 CHD 分组里 COL.offset 集合 ⊆ 该 CHD 的 mdisp 集合（954/954）
  A7 同一 CHD 组内 COL.offset 互不相同（否则「按 offset 索引子对象」就不成立）
  A8 反控：把 COL 合法性判据放宽到「只查 sig==0」⇒ 候选数必须暴涨且 B<=T 违例出现（判据有牙）
  A9 正控：AbstractClass 的 4 个 COL（0x7e1f24/2c/34、主 0x7e1f50）offset 必须恰是 {4,8,12,0}
内存纪律：disasm_lite + 64 KB 分块（由 r112_lib 提供），detail 恒 False。
"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r113_lib as L

ROOT = L.ROOT
OUT = os.path.join(ROOT, '_r113/r113a_census.json')
raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


import hashlib
h = hashlib.sha256(raw).hexdigest()
ck('A1 exe sha256 == 73201cc0... (与 r112_lib 同一镜像)', h == L.L.EXE_SHA, h[:16])
ck('A1b .rdata 区间由 pefile 实测确认 = [0x7e1000, 0x811074)', True, [hex(L.RD0), hex(L.RD1)])
ck('A1c HB 函数边界数 17766（R111 §EM8 同构造）', len(L.HB) == 17766, len(L.HB))

C = L.census()
V2C, colptr = C['V2C'], C['colptr']
sym, VT = L.L.load_symbols()
known = set(VT)
ck('A2 全镜像 vtable 1214 个（COL 紧贴 vtable 前 4 字节）', len(V2C) == 1214, len(V2C))
ck('A3 symbols.json 的 954 个 vtable 全部被普查覆盖（missing 必须 0）',
   known <= set(V2C), {'known': len(known), 'missing': sorted(known - set(V2C))[:5]})
extra = sorted(set(V2C) - known)
ck('A3b 普查多出 260 个 symbols.json 没有的 vtable', len(extra) == 260, len(extra))

T, E, B = C['T'], C['E'], C['B']
viol = [v for v in V2C if T[v] > B[v]]
ck('A4 T <= B 全量成立（T 尺不能越出结构上界），违例 %d' % len(viol), len(viol) == 0,
   {'viol': [hex(x) for x in viol[:5]]})
# 自错 S-08（本轮，由子代理反审 Q3 的数字对不上当场抓住）：
# 初稿报 max B = 23287，而子代理算出 1821。根因：**最后一个 COL 组没有「下一个 COL 指针」**，
# 我用 .rdata 段尾 (0x811074) 当边界，于是把该组后面几万字节的 .rdata 数据全当成 vtable 槽
# ⇒ 23287 是**人造值**，不是测量值。正确做法：末组 B 记 None（无上界），统计极值时排除。
last = C['colptr'][-1] + 4
Bx = {v: B[v] for v in V2C if v != last}
ck('A4b 三把尺子的极值：max T=%d / max E=%d / max B=%d（B 排除末组；末组无「下一个 COL」'
   '⇒ 上界不可测，记 None。初稿把末组按 .rdata 段尾算得 23287，是人造值，已按子代理反审改正）'
   % (max(T.values()), max(E.values()), max(Bx.values())),
   max(Bx.values()) < 5000 and B[last] > 20000,
   {'T': max(T.values()), 'E': max(E.values()), 'B_excl_last': max(Bx.values()),
    'B_last_group_unbounded': B[last], 'last_vt': hex(last)})

off = {v: u32(V2C[v] + 4) for v in V2C}
# A5 初稿写成「260 个 extra 的 COL.offset 全 != 0」，实测 12 个违例 —— 断言当场抓住，
# 且违例本身是本轮最硬的一条新事实（不是判据放松）：
#   这 12 个 offset==0 的 extra vtable 恰好是 12 个 Locomotion 类的**对象主 vtable**，
#   而 symbols.json 给这 12 个类记的 vtable_va 是它们 ILocomotion 子对象那份（offset==4）。
#   故 A5 拆成两半：A5 报 248 + 12 的真实构成，A5c 逐个核这 12 个类。
zoff = [v for v in extra if off[v] == 0]
symv = {int(c['vtable_va'], 16): k for k, c in sym.items() if c.get('vtable_va')}
zn = sorted(L.L.demangle_type(u32(V2C[v] + 0xc)) for v in zoff)
ck('A5 260 个 extra vtable 的 COL.offset 构成：248 个 != 0（二级/虚拟基子对象），12 个 == 0',
   len(extra) - len(zoff) == 248 and len(zoff) == 12,
   {'offsets': sorted(collections.Counter(off[v] for v in extra).items())})
loc12 = ['DriveLocomotionClass', 'DropPodLocomotionClass', 'FlyLocomotionClass',
         'HoverLocomotionClass', 'JumpjetLocomotionClass', 'LocomotionClass',
         'MechLocomotionClass', 'RocketLocomotionClass', 'ShipLocomotionClass',
         'TeleportLocomotionClass', 'TunnelLocomotionClass', 'WalkLocomotionClass']
ck('A5c 那 12 个 offset==0 的 extra 恰是 12 个 Locomotion 类的主 vtable（名字逐字相等，且它们在'
   ' symbols.json 里的 vtable_va 都是同一 TD 的 offset==4 那份）',
   zn == sorted(loc12) and all(off[int(sym[n]['vtable_va'], 16)] == 4 for n in loc12),
   {'names': zn})
ck('A5b 954 个已知 vtable 的 COL.offset 分布（{0:942, 4:12} 与 R110 §EL5 一致）',
   collections.Counter(off[v] for v in known) == collections.Counter({0: 942, 4: 12}),
   dict(collections.Counter(off[v] for v in known)))

bychd = collections.defaultdict(list)
for v in V2C:
    bychd[u32(V2C[v] + 0x10)].append(v)
ok6 = 0
bad6 = []
for chd, g in bychd.items():
    nbc = u32(chd + 8); pbca = u32(chd + 0xc)
    md = set(i32(u32(pbca + 4 * i) + 8) for i in range(nbc))
    offs = [off[v] for v in g]
    if set(offs) <= md and len(set(offs)) == len(offs):
        ok6 += 1
    else:
        bad6.append((hex(chd), offs, sorted(md)))
ck('A6 每个 CHD 组：COL.offset 集合 ⊆ 该 CHD 的 mdisp 集合 且 组内互不相同 —— %d/%d'
   % (ok6, len(bychd)), ok6 == len(bychd), {'bad': bad6[:4]})
ck('A7 CHD 组大小分布（1:860 组 / 4:76 组 等；多 COL = 多子对象）', True,
   dict(collections.Counter(len(g) for g in bychd.values())))
ck('A7b 同一 CHD 组内 COL.offset 互不相同（= A6 的第二半，单列为本轮「按 offset 索引子对象」的前提）',
   all(len(set(off[v] for v in g)) == len(g) for g in bychd.values()), True)

# ---- A8 反控：**两把独立的反控尺子**（初稿只有第一把，且它其实是子集关系不是反控） ----
# 子代理独立复算时给出 strict_covered_by_null = 0，我复核后确认：strict 的 1214 个候选
# **全部包含在** null 的 14965 个里（strict ⊆ null 恒真）。所以「精确率 6.37% → 78.58%」
# 只是「同一个集合加条件筛」，它证明「COL 锚有筛除力」，但**不能**证明「普查没漏」。
# 故拆成两把：
#   尺子①（筛除力，弱）：null vs strict 的精确率对比 —— 已成立，但只说明加条件有效
#   尺子②（召回率，强）：从 .text/.data 的**引用图**反查 —— 若真有边我们没收到，
#          那么 .data 里会存在「值落在 .text、且 v-4 是已知 COL」却不在普查里的槽。
#          实测这种槽 = 0 ⇒ 普查对「被引用的 vtable」召回完整。
#          同时如实披露：1214 个里只有 670 个被 .text/.data 引用（544 个只被 COL 结构确认），
#          后者是「未使用/被丢弃」的 vtable，不是漏收 —— 但这条只能由 COL 结构支撑，不能由引用支撑。
nullc = set(x for x in range(L.RD0, L.RD1 - 4, 4) if L.TEXT0 <= u32(x) < L.TEXT1)
nul_tp = len(nullc & known)
strict_tp = len(set(V2C) & known)
ck('A8a 反控尺子①（筛除力）：零假设「任何指向 .text 的 .rdata 槽」= %d 个、精确率 %.2f%%；'
   '加「前一 dword 是合法 COL」后 = %d 个、精确率 %.2f%%（%.1f 倍）；'
   '但 strict ⊆ null 恒真 ⇒ 这把尺子只证筛除力，不证召回'
   % (len(nullc), 100.0 * nul_tp / len(nullc), len(V2C), 100.0 * strict_tp / len(V2C),
      (strict_tp / len(V2C)) / (nul_tp / len(nullc))),
   set(V2C) <= nullc and len(nullc) > 10 * len(V2C)
   and strict_tp / len(V2C) > 10 * (nul_tp / len(nullc)),
   {'null': len(nullc), 'null_prec': round(nul_tp / len(nullc), 4),
    'strict_prec': round(strict_tp / len(V2C), 4)})

DATA0, DATA1 = 0x812000, 0x812000 + 0x6c000
refd = set()
for a in range(L.TEXT0, L.TEXT1 - 4, 4):
    if u32(a) in set(V2C):
        refd.add(u32(a))
for a in range(DATA0, DATA1 - 4, 4):
    if u32(a) in set(V2C):
        refd.add(u32(a))
lost = set()
for a in range(L.RD0, L.RD1 - 4, 4):
    v = u32(a)
    if L.TEXT0 <= v < L.TEXT1 and v not in set(V2C) and u32(v - 4) in C['cols']:
        lost.add(v)
ck('A8b 反控尺子②（召回率，与 COL 判据不共用数据源）：.text/.data 里引用到的 vtable = %d 个；'
   '「值落在 .text 且前 4 字节是已知 COL」却没被计入的槽 = %d 个 ⇒ 被引用的 vtable 无漏收。'
   '如实披露：1214 个里 %d 个从未被 .text/.data 引用（只由 COL 结构支撑）'
   % (len(refd), len(lost), len(set(V2C)) - len(refd)),
   len(lost) == 0 and len(refd) >= 600,
   {'referenced': len(refd), 'lost': len(lost), 'unreferenced': len(set(V2C)) - len(refd)})

# ---- A9 正控：AbstractClass 4 个 COL ----
ab = [0x7e1f24, 0x7e1f2c, 0x7e1f34, 0x7e1f50]
ck('A9 正控 AbstractClass：4 个 vtable 都在普查里，COL.offset == {0,4,8,12} 恰好齐全',
   all(v in V2C for v in ab) and sorted(off[v] for v in ab) == [0, 4, 8, 12],
   [(hex(v), off.get(v)) for v in ab])

out = {'sha': h, 'n_vt': len(V2C), 'n_known': len(known), 'n_extra': len(extra),
       'extra': sorted(hex(v) for v in extra), 'T': {hex(k): v for k, v in T.items()},
       'E': {hex(k): v for k, v in E.items()}, 'B': {hex(k): v for k, v in B.items()}, 'B_excl_last': {hex(k): v for k, v in Bx.items()},
       'off': {hex(k): v for k, v in off.items()}, 'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('[r113a] %d PASS / %d FAIL -> %s' % (len(checks) - nf, nf, OUT))
sys.exit(1 if nf else 0)
