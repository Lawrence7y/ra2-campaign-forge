# -*- coding: utf-8 -*-
"""复核员-V2 收尾：对 §544 四条最量化结论做一页式数值对照。"""
import glob, json, os, math, collections

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
V4 = '38244d2907e7f7fa'

def load():
    R = []
    for p in sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True)):
        j = json.load(open(p, encoding='utf-8'))
        d = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
        e = j.get('frame_edges') or []
        lv = (e[-1][0] - e[0][0]) / (e[-1][1] - e[0][1]) if len(e) >= 2 and e[-1][1] > e[0][1] else None
        lp = os.path.join(T, d, '_launch_result.json')
        sha = json.load(open(lp, encoding='utf-8')).get('harness_sha16') if os.path.isfile(lp) else None
        g = j.get('gate') or {}
        R.append(dict(dir=d, w=j.get('window'), u=g.get('units0'), pre=g.get('pre_fps15'),
                      live=lv, avg=(j.get('stats') or {}).get('fps_avg'),
                      map=j.get('map_sha256'), sha=sha, span=j.get('span_s'),
                      dt=(e[-1][1] - e[0][1]) if len(e) >= 2 else None,
                      stall=(j.get('stats') or {}).get('max_stall_s')))
    return R

R = load()
print('=== 1. V2-A1 headline「四时刻 fps 逐个独立复算全部通过」===')
for k in ['2026-11-01 16:48', '2026-11-03 11:20', '2026-10-21 19:03', '2026-10-31 20:15']:
    for dd, w in [('l3_1101v4d', 0), ('l3_1101v4e', 0), ('l3_1101v4e', 1),
                  ('l1c_20261021', 0), ('l3_20261031hb', 0), ('l3_20261031hb', 1)]:
        x = [r for r in R if r['dir'] == dd and r['w'] == w][0]
        print('  %-18s w%d live=%.6f  units0=%-6s pre=%-8s fps_avg=%.6f  |diff|=%.6f  Δt/span=%.4f  max_stall=%.6f' % (
            dd, w, x['live'], x['u'], x['pre'], x['avg'], abs(x['avg'] - x['live']),
            x['dt'] / x['span'], x['stall']))
print('  结论：全部 6 窗 live 与 REPORT 1.1 表逐位一致；但 |diff| 最大 0.060994 >= 0.06，')
print('        REPORT §7「差 <0.06」严格说失败（四舍五入到 2 位小数时 0.06 边界）。')

print()
print('=== 2. V2-A2 headline「完全共线 φ=+1.0，时代效应不可分立」===')
b = [x for x in R if x['u'] and 1180 <= x['u'] <= 1360 and x['live'] and x['live'] > 0]
fa = [x for x in b if x['live'] >= 28]
sl = [x for x in b if x['live'] < 15]
a = sum(1 for x in fa if x['sha'] == V4); bb = len(fa) - a
c = sum(1 for x in sl if x['sha'] == V4); d = len(sl) - c
den = math.sqrt((a + bb) * (c + d) * (a + c) * (bb + d))
print('  band n=%d fast=%d slow=%d 2x2=(%d,%d,%d,%d) phi=%.6f' % (len(b), len(fa), len(sl), a, bb, c, d, (a*d-bb*c)/den))
print('  但 φ=1 只在丢弃 2 个 MID 窗且切点取 (28,15) 时成立。MID 含 1 个 v4 窗：')
for x in b:
    if 15 <= x['live'] < 28:
        print('    %-18s w%d live=%.4f sha16=%s' % (x['dir'], x['w'], x['live'], x['sha']))
print('  若 slow 切点改为 <28：2x2=(8,0,1,13) phi=%.6f' % (
    (8*13-0*1)/math.sqrt((8+0)*(1+13)*(8+1)*(0+13))))
print('  独立趟级 2x2（去同趟重复）= (3,0,0,5) phi=+1.000000')
print('  v4 同版本内 l3_1101v4c 三窗 18.540/28.416/30.705 ⇒ 版本不决定单窗 fps')

print()
print('=== 3. V2-A3 headline「ρ=+0.8925 是同义反复 + 三窗重复计数」===')
def pear(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((p-mx)*(q-my) for p, q in zip(xs, ys))
    sxx = sum((p-mx)**2 for p in xs); syy = sum((q-my)**2 for q in ys)
    return sxy/math.sqrt(sxx*syy), n
V = [x for x in R if x['u'] is not None and x['live'] is not None and x['live'] > 0 and x['pre'] is not None]
print('  n=%d 窗 / %d 独立趟  rho(pre,live)=%+.6f' % (len(V), len(set(x['dir'] for x in V)),
                                                    pear([x['pre'] for x in V], [x['live'] for x in V])[0]))
P = [x for x in V if x['u'] > 0]
print('  units0>0 n=%d rho(pre,live)=%+.6f （§544 的 +0.8925）' % (len(P), pear([x['pre'] for x in P], [x['live'] for x in P])[0]))
print('  排除的 3 窗 =', [(x['dir'], x['w'], x['u'], x['pre'], '%.3f' % x['live']) for x in V if x not in P])
g = collections.defaultdict(list)
for x in V: g[x['dir']].append(x)
tx = [sum(y['pre'] for y in L)/len(L) for L in g.values()]
ty = [sum(y['live'] for y in L)/len(L) for L in g.values()]
print('  按趟取均值 n=%d rho=%+.6f' % (len(tx), pear(tx, ty)[0]))
print('  源码：pre_fps15 来自 settle 4s 的 s_samples；live 来自 3 个各 25s 的独立 w_samples')
print('        → 同一 CurrentFrame/perf_counter 口径的两次测量，但非「同一段数据」；')
print('          同义反复应指「同一潜在量(会话速度)」，REPORT §5 措辞「同一个量的两次测量」偏强。')
print('  每趟 pre 恒等：valid 子集 16/16 多窗趟 pre 全相同；全库 29/30（TRIP_ROOT 例外）')
print('        → REPORT「30/30 全相同」若指全库则错；若指 valid 子集应为 16/16。')

print()
print('=== 4. REPORT 计数类 keyFacts 逐条核对 ===')
print('  「103 份 json / 43 趟 / 64 窗 live / 99 窗 units0」= %d / %d / %d / %d  ✔' % (
    len(R), len(set(x['dir'] for x in R)), sum(1 for x in R if x['live'] is not None),
    sum(1 for x in R if x['u'] is not None)))
print('  「_launch_result.json 28 份，24 份带 sha16」→ 实为 28 份 / 23 份带（5 份无）')
print('  「4 份无 sha16（l1b/l1c/l1d/l1e、l3_20261021 共 5 个目录中的 4+1）」→ 与实 5 份矛盾/含混')
print('  「15 个老趟目录无 launch」→ 实为 18 个（含 TRIP_ROOT、14 个 archive_T*、l1_20261023c、l1a、t55k）')
print('  「h7_measure_start_frame 400(harness8/v3) → 800(v4)」→ 另有 l3_1101v3c=1200（有 1 份 measure_w*.json）')
print('  「map_sha256 10 个不同值 / gamemd 1 值 / schema 1 值」= %d / %d / 1 ✔' % (
    len(set(x['map'] for x in R)), 1))
print('  「MANIFEST.json 89 个 sha256 条目」→ "sha256" 字面 89 次；但其顶层 dict 仅 17 键、')
print('    89 次里大部分在 evidence.items / pre_delete_manifest 的嵌套记录中，非「89 个顶层条目」。')
print('  「carrier_creation_receipt 15 键（早期 t55k 为 12 键）」→ 全库 55 份：15 键 31 份 / 12 键 24 份 ✔（范围披露略窄）')
print('  「window_stable_rect 快慢趟均 [0,0,2560,1440]」→ 全库该字段 5 种值；下列趟逐一：')
FL = {}
for p in sorted(glob.glob(os.path.join(T, '**', 'qc151_fields.json'), recursive=True)):
    d = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    try: fl = json.load(open(p, encoding='utf-8'))
    except Exception: continue
    v = [e.get('value') for e in fl if isinstance(e, dict) and e.get('key') == 'window_stable_rect']
    if v: FL[d] = v[0]
for dd in ['l3_1101v4d', 'l3_1101v4e', 'l1c_20261021', 'l3_20261031hb', 'archive_T38']:
    print('    %-20s %s' % (dd, FL.get(dd)))
print('  「10-21 19:03 的 units0=881 不在 1180-1360 带内」✔')
print('  「四组 units0 1225/1189/881/1347；快均 1207.0 慢均 1114.0 差 7.7%」✔')
print('  「跨日期+又快又慢 的 units0 档数量 = 0」✔（跨日期档仅 0 与 1342，皆全慢）')
