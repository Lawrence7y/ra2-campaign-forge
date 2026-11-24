# -*- coding: utf-8 -*-
"""V2 §544 独立复算：从原始 measure_w*.json 重算 live_fps / 时刻 / units0 / map sha 等。

零真机、只读。所有数值自己从 frame_edges / samples 重算，不采信 §544 任何数字。
输出 JSON 到 stdout（调用方重定向到本目录文件）。
"""
import glob
import json
import os
import datetime
import collections

T = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
TZ8 = datetime.timezone(datetime.timedelta(hours=8))

fs = sorted(glob.glob(os.path.join(T, '**', 'measure_w*.json'), recursive=True))
rows = []
for p in fs:
    d = json.load(open(p, encoding='utf-8'))
    tripdir = os.path.relpath(os.path.dirname(p), T).replace('\\', '/')
    if tripdir == '.':
        tripdir = '(TRIP_ROOT)'
    edges = d.get('frame_edges') or []
    s = d.get('samples') or {}
    ts = s.get('t') or []
    fvals = s.get('f') or []
    gate = d.get('gate') or {}
    st = d.get('stats') or {}
    span = d.get('span_s')
    # 独立复算 live_fps = (末沿帧号-首沿帧号)/(末沿时刻-首沿时刻)
    live_fps = None
    f0 = f1 = t0 = t1 = df = dt = None
    if len(edges) >= 2:
        f0, t0 = edges[0][0], edges[0][1]
        f1, t1 = edges[-1][0], edges[-1][1]
        df, dt = f1 - f0, t1 - t0
        if dt > 0:
            live_fps = df / dt
    # 采样缺口
    gap_s = 0.0
    gap_n = 0
    for i in range(len(ts) - 1):
        dtt = ts[i + 1] - ts[i]
        if dtt > 0.010:
            gap_n += 1
            gap_s += dtt
    # 尾段停滞
    tail = (ts[-1] - edges[-1][1]) if (ts and edges) else None
    a = d.get('t_abs0')
    try:
        tstr = datetime.datetime.fromtimestamp(a, TZ8).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        tstr = None
    # 时刻字段（META ts, qc151_fields 里另有）
    rows.append(dict(
        path=p.replace('\\', '/'),
        rel=os.path.relpath(p, T).replace('\\', '/'),
        tripdir=tripdir,
        trip_id=d.get('trip_id'),
        window=d.get('window'),
        schema=d.get('schema'),
        t_abs0=a, time8=tstr,
        map_sha256=d.get('map_sha256'),
        gamemd_sha256=d.get('gamemd_sha256'),
        settle_s=d.get('settle_s'), span_s=span, hz=d.get('hz'),
        t_clock=d.get('t_clock'),
        units0=gate.get('units0'), pre_fps15=gate.get('pre_fps15'), gate_ok=gate.get('ok'),
        w1_units0=(d.get('w1') or {}).get('units0'),
        verdict=d.get('verdict'), error=d.get('error'),
        n_samples=len(ts), n_edges=len(edges),
        f_first=fvals[0] if fvals else None, f_last=fvals[-1] if fvals else None,
        f0=f0, f1=f1, df=df, dt=dt, live_fps=live_fps,
        fps_avg=st.get('fps_avg'), fps_p50=st.get('fps_p50'),
        frame_ms_p50=st.get('frame_ms_p50'), logic_frames=st.get('logic_frames'),
        max_stall_s=st.get('max_stall_s'), n_multi_advance=st.get('n_multi_advance'),
        tail_s=tail, tail_frac=(tail / span) if (tail is not None and span) else None,
        gap_s=gap_s, gap_n=gap_n,
        counters_n=len(d.get('counters') or []),
        h8=d.get('h8'),
        keys=sorted(d.keys()),
    ))

print(json.dumps(dict(total=len(rows), rows=rows), ensure_ascii=False, indent=1))
