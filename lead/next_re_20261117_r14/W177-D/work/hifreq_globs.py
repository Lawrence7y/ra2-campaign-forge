#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高频轮询 0xA8E7AC / 0xA8E9A0 / 0xA8ED6B（S12-K2 审计：帧内频繁变化）。只读内存。"""
import sys, time, json
import w177_core as W

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-D\EVIDENCE\globs_hifreq.jsonl"
pid = W.pid_of()
if not pid:
    print("gamemd not running"); sys.exit(2)
m = W.Mem(pid)
rows = []
t0 = time.perf_counter()
dur = 6.0
while time.perf_counter() - t0 < dur:
    t = time.perf_counter() - t0
    rows.append([round(t,6), m.u32(W.A_FRAME), m.u32(0xA8E7AC),
                 m.u8(0xA8E9A0), m.u8(0xA8ED6B), m.u32(W.A_MODE)])
    # no sleep: tight loop = max sampling rate
with open(EVID, "w", encoding="utf-8") as f:
    f.write(json.dumps({"note":"hifreq globals (tight loop, no clicks)","pid":pid,
                        "dur_target_s":dur,"n":len(rows),
                        "ts":time.strftime("%Y-%m-%dT%H:%M:%S%z")},ensure_ascii=False)+"\n")
    for r in rows:
        f.write(json.dumps(r)+"\n")

cols = {"A8E7AC":2,"A8E9A0":3,"A8ED6B":4,"frame":1,"mode":5}
print("pid=%d samples=%d wall=%.3fs rate=%.0f/s" % (pid,len(rows),rows[-1][0],len(rows)/rows[-1][0]))
for name,idx in cols.items():
    vals=[]; trans=0; prev=None
    for r in rows:
        v=r[idx]
        if not vals or vals[-1]!=v: vals.append(v)
        if prev is not None and v!=prev: trans+=1
        prev=v
    print("%-8s transitions=%d distinct=%d values(head)=%s" % (name,trans,len(set(r[idx] for r in rows)),vals[:12]))
print("saved",EVID)
