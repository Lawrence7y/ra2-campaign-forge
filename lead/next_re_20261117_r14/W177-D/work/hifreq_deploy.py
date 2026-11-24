#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高频采样 + MCV 部署（一个真实建筑放置操作）：后台线程 2ms 采全局量，主线程选MCV+按D部署。"""
import sys, time, json, threading
import w177_core as W
import wb_probe as P
from w177_click import click_client, game_hwnd, force_foreground
from w177_key import tap

EVID = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-D\EVIDENCE\globs_hifreq_deploy.jsonl"
pid = W.pid_of()
if not pid:
    print("gamemd not running"); sys.exit(2)
m = W.Mem(pid)
stop = threading.Event(); rows = []; t0 = time.perf_counter()

def sampler():
    while not stop.is_set():
        rows.append([round(time.perf_counter()-t0,6), m.u32(W.A_FRAME),
                     m.u32(0xA8E7AC), m.u8(0xA8E9A0), m.u8(0xA8ED6B), m.u32(W.A_MODE)])
        time.sleep(0.002)
th = threading.Thread(target=sampler, daemon=True); th.start()

events=[]
def ev(n): events.append((round(time.perf_counter()-t0,5), n))
ev("start")
# select MCV then deploy with D (VK_D=0x44)
ev("click_MCV")
click_client(pid, 1630, 560, "left", settle=0.5)
time.sleep(0.5)
ev("press_D")
tap(0x44, hold=0.08)
time.sleep(3.0)
ev("end")
stop.set(); th.join(timeout=1)

with open(EVID,"w",encoding="utf-8") as f:
    f.write(json.dumps({"note":"hifreq globals during MCV deploy (building placement)","pid":pid,
                        "events":events,"n":len(rows),"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z")},ensure_ascii=False)+"\n")
    for r in rows: f.write(json.dumps(r)+"\n")

print("pid=%d n=%d wall=%.2fs"%(pid,len(rows),rows[-1][0] if rows else 0))
print("events",events)
for name,idx in [("A8E7AC",2),("A8E9A0",3),("A8ED6B",4)]:
    vals=[]; trans=0; prev=None
    for r in rows:
        v=r[idx]
        if not vals or vals[-1]!=v: vals.append(v)
        if prev is not None and v!=prev: trans+=1
        prev=v
    print("%s transitions=%d values=%s"%(name,trans,vals[:20]))
# did deploy succeed? count player buildings
ph=P.player_house(m)
bl=[b for b in P.enumerate_buildings(m)[2] if m.u32(b[1]+0x21C)==ph]
print("player buildings after deploy:",len(bl))
print("saved",EVID)
