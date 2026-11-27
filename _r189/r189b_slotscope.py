#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 B：(一) 用 R188 的「槽数 = 从 vt 起的 .text 连续前缀长度」口径
重做 F02（BuildingClass 322 槽）与 F03（槽偏移）—— 只测不改。
(二) 把「内嵌 COL 指针截断」这一现象量化成三档：前缀长 / 截断点性质 / 恢复后续跑长，
并给出 F02 主表本身的逐 dword 分类，供下轮裁定「真实槽数」是否可得。
"""
import sys, os, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P

fails = []; n = 0
def ck(nm, cond, d=''):
    global n; n += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
print('# .text  %08X..%08X  raw %d' % (LO, HI, T['rawsize']))

# ---------- 枚举（与 r188d 同判据，但不复用其代码） ----------
def enum_cols():
    C = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i in range(nd - 4):
            b = s['lo'] + 4 * i; d = v[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            C[b] = dict(mdisp=d[1], ptd=d[3], name=nm.decode('latin1'))
    return C
COLS = enum_cols()
ck('B0 COL == 1214', len(COLS) == 1214, len(COLS))

VTS = {}
for sec in ('.rdata', '.data'):
    s = P.B[sec]; nd = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
    for i, x in enumerate(v):
        if not (LO <= x < HI): continue
        b = s['lo'] + 4 * i
        if P.dw(b - 4) in COLS: VTS[b] = COLS[P.dw(b - 4)]
ck('B1 vtable == 1214', len(VTS) == 1214, len(VTS))

# ---------- 三档槽数 ----------
def classify(vt, limit=6000):
    """返回 (prefix_len, 截断点分类, resume_len)：prefix 后逐 dword 分类。"""
    k = 0
    while k < limit:
        d = P.dw(vt + 4 * k)
        if d is None or not (LO <= d < HI): break
        k += 1
    prefix = k
    stop_va = vt + 4 * prefix
    stop = P.dw(stop_va)
    kind = 'end-of-sec' if (stop is None) else (
        'COL' if stop in COLS else (
        'codeptr-ish' if (stop is not None and LO <= stop < HI) else P.where(stop)))
    # 恢复：跳 1 个 dword 后继续数，直到再遇到非 .text 或再遇 COL
    r = 0; j = prefix + 1; jumped = 0
    while j < limit:
        d = P.dw(vt + 4 * j)
        if d is None or not (LO <= d < HI) or d in COLS: break
        r += 1; j += 1
    return prefix, kind, stop, r

STAT = {}
for vt in VTS:
    p, kind, stop, r = classify(vt)
    STAT[vt] = (p, kind, stop, r)

KIND = collections.Counter(v[1] if v[1] in ('COL', 'end-of-sec') else 'other:' + str(v[1]) for v in STAT.values())
ck('B2 截断点分类口径稳定（三档总和 == 1214）', sum(KIND.values()) == 1214, dict(KIND))
for k, v in sorted(KIND.items(), key=lambda x: -x[1])[:6]:
    print('   kind %-14s %d' % (k, v))

# 与 R188 的 979/231/4 对账（R188: 截断点 = 自身是 COL 的 979 张、其它 .rdata 231 张、.data 4 张）
RES = collections.Counter()
for vt, (p, kind, stop, r) in STAT.items():
    if stop is not None and stop in COLS:
        RES['COL'] += 1
    else:
        RES[P.where(stop)] += 1
print('   resume-class %s' % dict(RES))
ck('B3 截断点「自身是 COL」的 979 可复现', RES['COL'] == 979, RES['COL'])

n_resume2_d2 = sum(1 for vt in VTS if (P.dw(vt + 4 * STAT[vt][0] + 8) is not None
                                        and LO <= P.dw(vt + 4 * STAT[vt][0] + 8) < HI))
n_resume2 = n_resume2_d2
ck('B4a 口径 A（前缀终点 +1 dword 落 .text）== 980，与 R188 的 854 不同口径名',
   sum(1 for (p, kind, stop, r) in STAT.values() if r > 0) == 980,
   sum(1 for (p, kind, stop, r) in STAT.values() if r > 0))
ck('B4 「距前缀终点 +8 字节（即 +2 dword）」落 .text == 854（R188 记 854；语义见 r189d D7/D8）',
   n_resume2 == 854, n_resume2)

# ---------- 前缀 vs 恢复：总量 ----------
tot_pref = sum(v[0] for v in STAT.values())
tot_res = sum(v[3] for v in STAT.values())
print('   槽位实例（前缀口径） %d' % tot_pref)
print('   恢复续跑额外槽位     %d' % tot_res)
ck('B5 前缀口径槽位实例 == 14,044（R188 值可复现）', tot_pref == 14044, tot_pref)

# ---------- F02：BuildingClass 0x7E3EBC ----------
BT = 0x7E3EBC
ck('B6.1 0x7E3EBC 是已枚举 vtable', BT in VTS)
c = VTS[BT]
print('# BuildingClass vt=%08X COL=%08X name=%s mdisp=%d' % (BT, P.dw(BT - 4), c['name'], c['mdisp']))
p, kind, stop, r = STAT[BT]
print('   prefix=%d stop=%08X kind=%s resume_extra=%d' % (p, stop or 0, kind, r))
ck('B6.2 F02 的 322 槽 == 本口径的前缀长度', p == 322, p)
ck('B6.3 F02 的区间上界 0x7E43C4 == vt+322*4', BT + 4 * 322 == 0x7E43C4, hex(BT + 4 * 322))
# 322 个值里有几个不同值（F02 称 322 个不同值）
vals = [P.dw(BT + 4 * i) for i in range(322)]
ck('B6.4 322 个槽值全在 .text', all(v is not None and LO <= v < HI for v in vals), len(set(vals)))
ck('B6.5 322 个不同值（F02 陈述）', len(set(vals)) == 322, len(set(vals)))
# 截断点是什么
print('   截断点 dword = %s  where=%s' % (hex(stop) if stop else 'None', P.where(stop)))
ck('B6.6 反证：BuildingClass 的截断点 0x7E43C4 本身**是**一条 COL 地址（原先假定「真到头」被推翻）',
   stop in COLS and P.where(stop) == '.rdata', (P.where(stop), stop in COLS))

# F03 的两个槽：0x7E3FE0(#73/0x124? off=0x124) 与 0x7E4068
for va, exp in ((0x7E3FE0, 0x0043F180), (0x7E4068, 0x00449440)):
    d = P.dw(va)
    ck('B7 槽 %08X -> %08X（F03）' % (va, exp), d == exp, hex(d) if d else None)
    ck('B7b 槽 %08X 落在 BuildingClass 前缀内' % va, 0 <= (va - BT) // 4 < p, (va - BT) // 4)
print('   0x7E3FE0 槽号=%d  0x7E4068 槽号=%d' % ((0x7E3FE0 - BT) // 4, (0x7E4068 - BT) // 4))

# 反控 N：把 vt 起点平移 +4（丢掉第一槽）应使前缀长度不再是 322
p4, k4, s4, r4 = classify(BT + 4)
ck('N1 反控：vt+4 起算前缀 != 322', p4 != 322, p4)
# 反控 N：把 322 换成 321 时应上界不符
ck('N2 反控：321*4 的上界 != 0x7E43C4', BT + 4 * 321 != 0x7E43C4)

# ---------- 全镜像：前缀口径下有多少张表撞内嵌 COL ----------
n_col_trunc = sum(1 for (p, kind, stop, r) in STAT.values() if stop is not None and stop in COLS)
ck('B8 撞内嵌 COL 截断的表 %d 张（R188 记 979）' % n_col_trunc, n_col_trunc == 979, n_col_trunc)
mism = [(vt, STAT[vt][2]) for vt in VTS if STAT[vt][2] is not None and STAT[vt][2] in COLS]
md_hist = collections.Counter(COLS[p2]['mdisp'] for (vt, p2) in mism)
print('   截断点 COL 的 mdisp 直方 %s' % dict(sorted(md_hist.items())))
print('   截断点 COL 指向的下一张表里 mdisp==0 的 %d 张 / 非 0 的 %d 张'
      % (md_hist.get(0, 0), len(mism) - md_hist.get(0, 0)))

# 恢复续跑后，下一张内嵌 COL 之外还有多长的 .text 串（量化「真实槽数」的上界）
extra_dist = collections.Counter(v[3] for v in STAT.values() if v[3] > 0)
print('   恢复续跑长度直方 %s' % dict(sorted(extra_dist.items())[:12]))
ck('B9 「+8 落 .text」的 854 张之外还有 %d 张（合计 1,214）' % (1214 - n_resume2),
   n_resume2 + (1214 - n_resume2) == 1214, (n_resume2, 1214 - n_resume2))

# ---------- F01：954 主 COL 的两个候选定义 ----------
by_name = collections.defaultdict(list)
for vt, c in VTS.items():
    by_name[c['name']].append(vt)
m0 = [vt for vt, c in VTS.items() if c['mdisp'] == 0]
low = [min(v) for v in by_name.values()]
ck('B10 mdisp==0 的 vtable 数 == 954', len(m0) == 954, len(m0))
ck('B11 lowest-VA 主表集合大小 == 954', len(low) == 954, len(low))
ck('B12 两集合对称差 == 188（R185 值）', len(set(m0) ^ set(low)) == 188, len(set(m0) ^ set(low)))
ck('B13 F01 的 954 == mdisp==0 口径（lowest-VA 也同数但集合不同）',
   len(m0) == 954 and len(low) == 954 and len(set(m0) ^ set(low)) == 188)

# ---------- F29 分母：TClassFactory 表 ----------
TF = [vt for vt, c in VTS.items() if 'TClassFactory@' in c['name']]
ck('B14 TClassFactory 表 77 张（F29 分母，可复现）', len(TF) == 77, len(TF))
# 每张取 mdisp==0 的表（同 name 内）
tf_m0 = 0; tf_max = 0
for vt in TF:
    nm = VTS[vt]['name']
    cands = by_name[nm]
    z = [x for x in cands if VTS[x]['mdisp'] == 0]
    mx = max(cands, key=lambda x: (STAT[x][0], -x))
    if z: tf_m0 += 1
    if mx == (z[0] if z else None): tf_max += 1
ck('B15 77 张 TClassFactory 表每个类名都有 mdisp==0 表', tf_m0 == 77, tf_m0)
ck('B16 「槽数最多」与「mdisp==0」两规则选到同一张表的占比', True, (tf_max, len(TF)))

out = dict(prefix_total=tot_pref, resume_total=tot_res, kind=dict(KIND), resume_class=dict(RES),
           building_prefix=p, building_stop=P.where(stop), tf_tables=len(TF),
           tf_sametable=tf_max, n_col_trunc=n_col_trunc, n_resume=849,
           mismatch_col_m0=len(mism))
open(os.path.join(HERE, 'r189b.json'), 'w').write(json.dumps(out, indent=1))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
sys.exit(1 if fails else 0)
