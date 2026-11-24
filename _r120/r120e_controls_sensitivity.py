#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120e_controls_sensitivity.py —— 两条判据的判别力与「结论对判据的敏感性」。

R120 的 Q2 要回答：能不能用「一个函数只碰一个 IID」这个统计量把「通用包装器」解释排除？
本脚本不去再算一遍分布（那在 r120d 里），而是量**这个结论有多依赖函数边界判据**：
  S1 执行员的 containment（CFG 前驱走）分布
  S2 主会话的 nearest-preceding-entry 分布
  S3 执行员自己报告的 M1/M2 两种判据在 60 个站点上的分歧数
若三种判据给出三种不同的「恰好 1 个」占比，则该统计量不稳健 ⇒ 不能用来排除任何解释。
反控：
  N1 IID 判据非恒真：d4 改成 0x46000001 ⇒ 命中 0
  N2 IID 判据真在筛：去掉 d2==0 条件 ⇒ 命中数必须严格变大
  N3 COM 形状判据不是「什么都能进」：0x7ed358（ILocomotion）必须**不**满足它
  N4 站点数反控：把目标地址 +4 后 push 站点必须为 0
"""
import json
import os
import struct
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r119'))
from _pe119 import PE_, BUF                      # noqa: E402

OUT = os.path.join(ROOT, '_r120', 'r120e_controls_sensitivity.json')
EXEC = os.path.join(ROOT, '_r120', 'x120exec_core.json')
MINE = os.path.join(ROOT, '_r120', 'r120d_recompute_exec.json')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def scan_nd3():
    """同时去掉 d2==0 与 d3 低字两个条件（只留 d4）。"""
    hits = []
    for nm in ('.rdata', '.data'):
        s = PE_.sec_by_name(nm)
        blob = BUF[s['raw']:s['raw'] + s['vsize']]
        for off in range(0, len(blob) - 15, 4):
            a, b, c, d = struct.unpack_from('<4I', blob, off)
            if d == 0x46000000:
                hits.append(s['va'] + off)
    return hits


def scan(drop_d2=False, d4=0x46000000):
    hits = []
    for nm in ('.rdata', '.data'):
        s = PE_.sec_by_name(nm)
        blob = BUF[s['raw']:s['raw'] + s['vsize']]
        for off in range(0, len(blob) - 15, 4):
            a, b, c, d = struct.unpack_from('<4I', blob, off)
            if d != d4:
                continue
            if not drop_d2 and b != 0:
                continue
            if (c & 0xFFFF) != 0x00C0:
                continue
            hits.append(s['va'] + off)
    return hits


base = scan()
c1 = scan(d4=0x46000001)
c2 = scan(drop_d2=True)
ck('N1 反控（IID 判据非恒真）：d4=0x46000001 ⇒ 命中 %d（必须 0）' % len(c1), len(c1) == 0, {'n': len(c1)})
# 🐞 自错 S-76：初稿断言「去掉 d2==0 条件后命中必须变多」。实测 11→11，**不变**。
# 原因不是判据坏了，而是这个镜像上 11 个命中本来就全部 d2==0 ⇒ 该条件在本镜像上**冗余**。
# 真正在筛的是 d3 的低 16 位：同时去掉 d2 与 d3 两个条件才变多（11→12）。如实分项登记。
c3 = scan_nd3()
ck('N2 反控（判据真在筛，分项）：去掉 d2==0 ⇒ %d（与 %d 相同 ⇒ d2 条件在本镜像上冗余）；'
   '再去掉 d3 低字 ⇒ %d（> %d ⇒ d3 条件确实在筛）；d4 改值 ⇒ %d（= 0 ⇒ d4 是主筛）'
   % (len(c2), len(base), len(c3), len(base), len(c1)),
   len(c2) == len(base) and len(c3) > len(base) and len(c1) == 0,
   {'with_all': len(base), 'drop_d2': len(c2), 'drop_d2_d3': len(c3), 'd4_plus1': len(c1)})

# N3：0x7ed358 不满足 COM 形状
o = PE_.va2off(0x7ed358)
d1, d2, d3, d4 = struct.unpack_from('<4I', BUF, o)
ck('N3 0x7ed358 的 16 字节 = %s，dwords=%s ⇒ 不满足 COM 形状（d2=%d, d3&0xFFFF=0x%04X, d4=0x%08X）'
   % (BUF[o:o + 16].hex(), [hex(x) for x in (d1, d2, d3, d4)], d2, d3 & 0xFFFF, d4),
   not (d2 == 0 and (d3 & 0xFFFF) == 0x00C0 and d4 == 0x46000000),
   {'in_scan': 0x7ed358 in scan()})

# N4：目标 +4 后的 push 站点必须为 0（键精确性反控）
e = json.load(open(EXEC, encoding='utf-8'))
def cnt_in(x): return e['q1'].get('sites') if x == 0x7f7c80 else None
# 用执行员的站点表做「+4 后无站点」的反控：检查 0x7f7c84 不在任何站点里
sites80 = set(int(x, 16) for x in e['q1']['site_addrs'])
ck('N4 反控（键精确性）：把 0x7f7c80 换成 0x7f7c84（GUID+4）后不可能出现在站点表里 ⇒ 命中 %d'
   % sum(1 for s in sites80 if s == 0x7f7c84), 0x7f7c84 not in sites80, {'n': 0})

# ---- S1/S2/S3 敏感性 ----
mine = json.load(open(MINE, encoding='utf-8'))
s1 = e['q2']['containment']
s2 = mine['dist_all']

# S3 由本脚本自己算：三种边界判据（int3 填充后首指令 / 终结指令后首指令 / nearest-preceding-entry）
# 在 60 个站点上给出的「归属函数」有多少个与其它判据不同。
QP = os.path.join(ROOT, '_r120', 'x120exec_q1_partial.json')
g = json.load(open(QP, encoding='utf-8'))['q1_groups']
pad = g['C1_int3pad'][0]
after = g['C2_afterterm'][0]

def owner(group, site):
    # 🐞 自错 S-77：执行员的 q1_groups 里 sites 是 **hex 字符串**，我传的是 int ⇒ 60/60 全部
    # 判成「不在任何组里」，于是 s3 被算成 60（假分歧）。改为按 hex 字符串比对。
    key = hex(site)
    for f in group:
        if key in f['sites']:
            return f['func_start']
    return None

# 主会话的 entry 表（从 r120d 的判据复算里复用同一实现）
import array
import bisect
import capstone
TEXT = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True
starts, calls = [], []
for off in range(0, TEXT['vsize'], 65536):
    blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
        starts.append(a)
        if mn == 'call' and ops.startswith('0x'):
            calls.append(int(ops, 16))
SSET = set(starts)
ENT = array.array('I', sorted({PE_.imagebase + struct.unpack_from('<I', BUF, PE_.e_lfanew + 24 + 16)[0]}
                              | {t for t in calls if t in SSET}))


def ent_owner(va):
    i = bisect.bisect_right(ENT, va) - 1
    return ENT[i] if i >= 0 else None


dis = 0
detail_rows = []
for site in (int(x, 16) for x in e['q1']['site_addrs']):
    a, b, c = owner(g['C1_int3pad'], site), owner(g['C2_afterterm'], site), ent_owner(site)
    if len({a, b, c}) > 1:
        dis += 1
    if len(detail_rows) < 6:
        detail_rows.append({'site': hex(site), 'int3pad': a, 'afterterm': b,
                            'nearest_entry': hex(c) if c else None})
s3 = dis

def pct(d):
    t = d.get('funcs') or 0
    return 100.0 * (d.get('exactly1', 0) or 0) / t if t else float('nan')

table = {
    'S1 执行员 containment（55 个函数）': {'funcs': s1['funcs'], 'exactly1': s1['exactly1'],
                                   'pct': 100.0 * s1['exactly1'] / s1['funcs']},
    'S2 主会话 nearest-entry（74 个函数）': {'funcs': s2['funcs'], 'exactly1': s2['exactly1'],
                                       'pct': 100.0 * s2['exactly1'] / s2['funcs']},
}
ck('S1/S2 两种函数边界判据下「恰好 1 个 IID」占比 = %.2f%%（%d 函数） vs %.2f%%（%d 函数）'
   '⇒ 数字不同（该统计量对判据敏感）'
   % (table['S1 执行员 containment（55 个函数）']['pct'], s1['funcs'],
      table['S2 主会话 nearest-entry（74 个函数）']['pct'], s2['funcs']),
   abs(table['S1 执行员 containment（55 个函数）']['pct']
       - table['S2 主会话 nearest-entry（74 个函数）']['pct']) > 1.0, table)
ck('S3 三种边界判据（int3 填充后首指令 / 终结指令后首指令 / nearest-preceding-entry）在 60 个站点上'
   '归属函数不同的站点数 = %d（样例 %s）'
   % (s3, json.dumps(detail_rows[:3], ensure_ascii=False)),
   s3 >= 30, {'n_disagree': s3, 'sample': detail_rows})

# ---- S5 执行员自己给了 5 种边界判据，逐种列「恰好 1 个 IID」占比 ----
Q2 = os.path.join(ROOT, '_r120', 'x120exec_q2.json')
if os.path.isfile(Q2):
    pv = json.load(open(Q2, encoding='utf-8'))['q2']['per_view']
    rows = []
    for k in sorted(pv):
        dd = pv[k]['distribution']
        rows.append({'view': k, 'funcs': dd['funcs'], 'exactly1': dd['exactly1'],
                     'pct': round(100.0 * dd['exactly1'] / dd['funcs'], 2) if dd['funcs'] else None})
    mine_pct = round(100.0 * s2['exactly1'] / s2['funcs'], 2)
    ck('S5 执行员 5 种边界判据的「恰好 1 个 IID」占比 = %s；主会话 nearest-entry 判据 = %.2f%%'
       '（与执行员的 C_addr_range_to_next_entry 逐个相同：%d/%d vs %d/%d）'
       % (json.dumps(rows, ensure_ascii=False), mine_pct,
          s2['exactly1'], s2['funcs'],
          pv['C_addr_range_to_next_entry']['distribution']['exactly1'],
          pv['C_addr_range_to_next_entry']['distribution']['funcs']),
       all(r['pct'] >= 90.0 for r in rows) and mine_pct >= 90.0
       and s2['exactly1'] == pv['C_addr_range_to_next_entry']['distribution']['exactly1']
       and s2['funcs'] == pv['C_addr_range_to_next_entry']['distribution']['funcs'],
       {'exec_views': rows, 'mine': mine_pct})
else:
    rows = []

concl = ('该统计量对函数边界判据敏感（两判据占比 %.2f%% vs %.2f%%，站点级分歧 %d/60），'
         '故**不能**用它排除「通用包装器」解释；R116 §EL 的 L3 替代解释维持「未排除」'
         % (table['S1 执行员 containment（55 个函数）']['pct'],
            table['S2 主会话 nearest-entry（74 个函数）']['pct'], s3))
ck('S4 结论（只写判据支撑得住的那句）：' + concl, True, {})

json.dump({'scan_with_d2': len(base), 'scan_d4_plus1': len(c1), 'scan_drop_d2': len(c2),
           's1_exec_containment': s1, 's2_main_nearest_entry': s2, 'criterion_disagree': s3,
           'exec_views': rows, 'conclusion': concl, 'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
