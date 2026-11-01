#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 亲验探针 v2：frame 计数器起点语义决定性检验。
方法：counters 行（1Hz，含 units、t_rel）内插到 frame 轴（用同窗 samples.t↔samples.f 线性内插），
      找 units 首 >0 行的内插 frame 值。frame≈0 ⇒ 计数器自 battle 起计（菜单/加载不累计）。
只读。
"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def interp_frame(f_list, t_list, t):
    if t <= t_list[0]:
        return f_list[0]
    if t >= t_list[-1]:
        return f_list[-1]
    for i in range(len(t_list) - 1):
        if t_list[i] <= t <= t_list[i + 1]:
            dt = t_list[i + 1] - t_list[i]
            if dt <= 0:
                return f_list[i]
            w = (t - t_list[i]) / dt
            return f_list[i] + w * (f_list[i + 1] - f_list[i])
    return None

for d in ["l1_20261023e1", "l1_20261023hb", "l1_20261023k", "l3_20261023q", "l3_20261023r", "l3_20261031ha", "l3_20261031hb"]:
    try:
        mw = jload(f"{ROOT}/{d}/measure_w0.json")
    except Exception as e:
        print(f"  {d}: 读取失败 {e!r}")
        continue
    s = mw.get("samples") or {}
    cnt = mw.get("counters") or []
    fl, tl_ = s.get("f"), s.get("t")
    if not fl or not tl_ or not cnt:
        print(f"  {d}: samples.f/t 或 counters 缺")
        continue
    units_seq = [c.get("units") for c in cnt]
    first = next((i for i, u in enumerate(units_seq) if isinstance(u, (int, float)) and u > 0), None)
    if first is None:
        print(f"  {d}: 窗内 units 恒 0  f=[{fl[0]}..{fl[-1]}]  units={units_seq}")
        continue
    c = cnt[first]
    fi = interp_frame(fl, tl_, c["t_rel"])
    print(f"  {d}: counters units 序列={units_seq[:8]}{'…' if len(units_seq)>8 else ''}")
    print(f"      units>0 首行 t_rel={c.get('t_rel')} units={c.get('units')}  ⇒ 内插 frame={fi and round(fi,2)}  "
          f"(窗 f 域=[{fl[0]}..{fl[-1]}], 窗时长≈{round(tl_[-1]-tl_[0],3)}s)")
