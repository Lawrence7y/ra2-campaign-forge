#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-KA 独立复算 j_flag_samples.jsonl —— 不 import W177-J/work 下任何脚本。
输出真实字段覆盖、取值集合、时间戳差分中位数、逐帧覆盖、悬停→点击窗数据。
"""
import json, os, statistics, collections

JL = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J\EVIDENCE\j_flag_samples.jsonl"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_flag_samples_stats.txt"
P = []
def p(s=''):
    P.append(str(s))
    print(s)

rows = []
bad = 0
with open(JL, encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            bad += 1
            if bad <= 5: p(f'BAD LINE {i}: {e}')
p(f'samples_parsed={len(rows)}  bad_lines={bad}')
keys = collections.Counter()
nulls = collections.Counter()
for r in rows:
    for k, v in r.items():
        keys[k] += 1
        if v is None: nulls[k] += 1
p('field_presence=' + json.dumps(dict(keys), sort_keys=True))
p('field_nulls=' + json.dumps(dict(nulls), sort_keys=True))
FIELDS = ['g_F16BF','g_F16BE','g_F16B7','g_DE58','A8E9A0','A8E7AC','A8ED6B','ghost_o1','frame','lenA','hover_cell','arg2_now','headA','credits']
for k in FIELDS:
    vals = [r.get(k) for r in rows if r.get(k) is not None]
    uniq = sorted(set(map(str, vals)))
    p(f'  {k}: present={len(vals)} distinct={len(uniq)} values={uniq[:12]}{" ..." if len(uniq)>12 else ""}')

# timestamp statistics
ts = [r['t'] for r in rows if isinstance(r.get('t'), (int,float))]
dts = [b-a for a,b in zip(ts, ts[1:]) if b > a]
p(f't_min={min(ts):.6f} t_max={max(ts):.6f} duration={max(ts)-min(ts):.6f}')
p(f'median_dt={statistics.median(dts):.9f}s  mean_dt={statistics.mean(dts):.9f}s  min_dt={min(dts):.9f} max_dt={max(dts):.9f}  median_rate={1/statistics.median(dts):.1f}/s  mean_rate={len(rows)/(max(ts)-min(ts)):.1f}/s')
frames = sorted(set(r['frame'] for r in rows if r.get('frame') is not None))
p(f'distinct_frames={len(frames)} frame_min={min(frames)} frame_max={max(frames)}')
fc = collections.Counter(r['frame'] for r in rows if r.get('frame') is not None)
p('frame_counts=' + json.dumps({str(k):fc[k] for k in frames}, sort_keys=True))

# click window (script clicked at t >= 0.25; actual click sample index 4710 in run json)
click_idx = 4710
p(f'click_idx_reported={click_idx}')
for i in range(max(0,click_idx-3), min(len(rows), click_idx+6)):
    r = rows[i]
    p(f'  [{i}] t={r["t"]:.6f} frame={r["frame"]} g_F16BF={r["g_F16BF"]} g_F16BE={r["g_F16BE"]} g_F16B7={r["g_F16B7"]} g_DE58={r["g_DE58"]} A8E9A0={r["A8E9A0"]} A8E7AC={r["A8E7AC"]} A8ED6B={r["A8ED6B"]} ghost_o1={r["ghost_o1"]} lenA={r["lenA"]} hover={r["hover_cell"]} credits={r["credits"]} click_fg_ok={r.get("click_fg_ok","-")}')

# hover->click window: all samples before click with cursor at anchor [113,62]
win = [r for r in rows if r['t'] <= 0.25]
p(f'pre_click_window_samples={len(win)}')
for k in ['g_F16BF','g_F16BE','g_F16B7','g_DE58','A8E9A0','A8E7AC','A8ED6B','ghost_o1','lenA','hover_cell','arg2_now','credits']:
    vals = sorted(set(str(r.get(k)) for r in win))
    p(f'  pre_click {k}: {vals[:10]}')
# per-frame first/last
p('per_frame_flag_changes=' + json.dumps({str(fr): {
    'g_F16BF': sorted(set(r['g_F16BF'] for r in rows if r['frame']==fr)),
    'g_F16BE': sorted(set(r['g_F16BE'] for r in rows if r['frame']==fr)),
    'g_F16B7': sorted(set(r['g_F16B7'] for r in rows if r['frame']==fr)),
    'g_DE58': sorted(set(r['g_DE58'] for r in rows if r['frame']==fr)),
    'A8E9A0': sorted(set(r['A8E9A0'] for r in rows if r['frame']==fr)),
    'ghost_o1': sorted(set(r['ghost_o1'] for r in rows if r['frame']==fr)),
    'lenA': sorted(set(r['lenA'] for r in rows if r['frame']==fr)),
} for fr in frames}, sort_keys=True))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write('\n'.join(P)+'\n')
print('saved', OUT)
