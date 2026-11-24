#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 trials_final — current in-game session; validated ghost detection; no ESC cancel.
Runs A/B/C trials, selecting only buildable (green-footprint) empty anchors for A.
Paired pixel baseline is taken from l1_v2 (same card, green 1009 vs 15481 = 15.34x)."""
import os, sys, time, ctypes, json, struct, subprocess
import l1_helpers as H
from l1_helpers import W,P,C,D,u32,k32,FRAME,HOVER,CARD,EVID,shot,cols,napowr,cell_chain,closed_loop,scan_units,cell_ptr,save as _save
from w177_click import force_foreground, game_hwnd, click_client

RESULT=os.path.join(EVID,"l1_final_result.json"); TSV=os.path.join(EVID,"trials_final.tsv")
def save(r): json.dump(r,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
H.save=save
pid=W.pid_of()
H.pid=pid
res={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"card":"LIVE-L1-final","pid":pid,"stage":"start",
     "baseline_ref":{"source":"l1_v2_result.json","noghost_green":1009,"withghost_green":15481,"distinguish_x":15.34}}
save(res)
if not pid: res["abort"]="no gamemd"; save(res); sys.exit(2)
ph=P.player_house(W.Mem(pid))
m=W.Mem(pid); pts=C.all_player_building_types(m,ph); m.close()
res["start_types"]=pts; save(res)
if "NACNST" not in pts: res["abort"]="no yard"; save(res); sys.exit(3)
icon=(2336,472); res["icon"]=icon; save(res)

def ensure_ghost(tag):
    """Return True if footprint (green or red >=3000) present at PROBE_SCREEN; else order+pickup."""
    for attempt in range(5):
        force_foreground(game_hwnd(pid),0.4)
        u32.SetCursorPos(*H.PROBE_SCREEN); time.sleep(0.32)
        c=cols(*H.PROBE_SCREEN)
        if c["green"]>=3000 or c["red"]>=3000:
            return True
        m0=W.Mem(pid); pre=m0.u32(ph+0x30C); m0.close()
        force_foreground(game_hwnd(pid),0.4)
        ok,_=click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
        time.sleep(0.5)
        m1=W.Mem(pid); post=m1.u32(ph+0x30C); m1.close()
        ordered=post<pre-5
        if ordered:
            for i in range(100):
                time.sleep(0.4)
                m2=W.Mem(pid); cr=m2.u32(ph+0x30C); m2.close()
                if cr<=pre-580: break
            time.sleep(0.6)
            force_foreground(game_hwnd(pid),0.4)
            click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
            time.sleep(0.4)
        res.setdefault("orders",[]).append({"tag":tag,"attempt":attempt,"pre":pre,"post":post,"ordered":ordered}); save(res)
    u32.SetCursorPos(*H.PROBE_SCREEN); time.sleep(0.3)
    c=cols(*H.PROBE_SCREEN); res["ghost_fail"]={"tag":tag,"colors":c}; save(res)
    return False

# targets
m=W.Mem(pid); ph=P.player_house(m)
inf1,veh1=scan_units(m,ph); time.sleep(1.2); inf2,veh2=scan_units(m,ph)
inf_st=[k for k in inf1 if inf1.get(k)==inf2.get(k) and inf1.get(k,0)>=1]
veh_st=[k for k in veh1 if veh1.get(k)==veh2.get(k) and veh1.get(k,0)>=1]
occ=set(inf_st)|set(veh_st)
for i,o in P.enumerate_buildings(m)[2]:
    b=P.one_building(m,i,o)
    if b["cell"].get("valid"): occ.add((b["cell"]["cellX"],b["cell"]["cellY"]))
uc=list(inf_st)+list(veh_st)
cxm=sorted(c[0] for c in uc)[len(uc)//2] if uc else 31; cym=sorted(c[1] for c in uc)[len(uc)//2] if uc else 85
empty=[]
for cy in range(cym-10,cym+11):
    for cx in range(cxm-10,cxm+11):
        fc=[(x,y) for x in range(cx-1,cx+2) for y in range(cy,cy+2)]
        if any((x,y) in occ for x,y in fc): continue
        if any(not cell_ptr(m,x,y) for x,y in fc): continue
        empty.append((cx,cy))
empty.sort(key=lambda a: abs(a[0]-cxm)+abs(a[1]-cym))
m.close()
res["targets"]={"inf_stable":[list(k) for k in sorted(inf_st)],"veh_stable":[list(k) for k in sorted(veh_st)],
    "center":[cxm,cym],"empty":[list(a) for a in empty]}; save(res)
print("inf",sorted(inf_st),"veh",sorted(veh_st),"center",(cxm,cym),"nempty",len(empty),flush=True)

# ensure ghost
if not ensure_ghost("init"): res["abort"]="no ghost"; save(res); sys.exit(4)
print("ghost ready",flush=True)

# find buildable A anchors: closed-loop converges AND footprint is GREEN (with ghost in hand)
m=W.Mem(pid); good_A=[]; tried=0
for a in empty:
    if tried>=30 or len(good_A)>=5: break
    if any(max(abs(a[0]-g[0]),abs(a[1]-g[1]))<3 for g in good_A): continue
    tried+=1
    ok,cur,s,_=closed_loop(m,a)
    if not (ok and cur==a): continue
    force_foreground(game_hwnd(pid),0.3); u32.SetCursorPos(int(s[0]),int(s[1])); time.sleep(0.3)
    c=cols(s[0],s[1])
    if c["green"]>=3000 and c["red"]<2000:
        good_A.append(a); res.setdefault("buildable_A",[]).append({"anchor":list(a),"screen":list(s),"colors":c}); save(res)
m.close(); res["good_A"]=[list(a) for a in good_A]; save(res)
print("good_A",good_A,"tried",tried,flush=True)
if not good_A: res["abort"]="no buildable A"; save(res); sys.exit(5)

def run_trial(group,idx,anchor):
    tag="fin_%s_%02d"%(group,idx+1); rec={"group":group,"idx":idx+1,"anchor":list(anchor)}
    target=(anchor[0],anchor[1]+1) if group in ("B","C") else anchor
    rec["target_cell"]=list(target)
    m=W.Mem(pid); ph2=P.player_house(m)
    rec["hover_before"]=list(H.hcell(m)); pre_nap=napowr(m,ph2); rec["napowr_before"]=pre_nap
    rec["chain_before"]=cell_chain(m,*target)
    pre_placed=[x for x in pre_nap if x["o1"]==0 and x["valid"]]; m.close()
    if not ensure_ghost(tag): m.close(); rec["success"]=False; rec["note"]="no ghost"; return rec
    m=W.Mem(pid)
    ok,cur,screen,trace=closed_loop(m,anchor,tag)
    rec["loop_ok"]=ok; rec["cur"]=list(cur) if cur[0] is not None else None; rec["iters"]=len(trace)
    rec["screen"]=list(screen); rec["hover_after_cursor"]=list(H.hcell(m))
    rec["colors_with"]=cols(screen[0],screen[1]); shot(tag+"_withghost")
    fb=H.rd(m,FRAME); u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(0.6); fa=H.rd(m,FRAME)
    rec["hover_after_click"]=list(H.hcell(m)); time.sleep(0.4)
    post_nap=napowr(m,ph2); rec["napowr_after"]=post_nap; rec["chain_after"]=cell_chain(m,*target)
    rec["frame_before"]=fb; rec["frame_after"]=fa
    placed=[x for x in post_nap if x["o1"]==0 and x["valid"]]
    rec["success"]=len(placed)>len(pre_placed)
    rec["link_after"]=any(v and 'BuildingClass' in v for v in rec["chain_after"].get("rttiA",[])+rec["chain_after"].get("rttiB",[]))
    shot(tag+"_after"); m.close(); return rec

res["stage"]="trials"; save(res)
for i,a in enumerate(good_A[:5]):
    r=run_trial("A",i,a); res.setdefault("trials",[]).append(r); save(res)
    print("A",i+1,"success",r["success"],"loop",r["loop_ok"],"G",r["colors_with"]["green"],"R",r["colors_with"]["red"],flush=True)
Bc=sorted(inf_st); Cc=sorted(veh_st)
for i in range(5):
    if Bc:
        b=Bc[i%len(Bc)]; r=run_trial("B",i,(b[0],b[1]-1)); res.setdefault("trials",[]).append(r); save(res)
        print("B",i+1,"success",r["success"],"loop",r["loop_ok"],"G",r["colors_with"]["green"],"R",r["colors_with"]["red"],flush=True)
    if Cc:
        c=Cc[i%len(Cc)]; r=run_trial("C",i,(c[0],c[1]-1)); res.setdefault("trials",[]).append(r); save(res)
        print("C",i+1,"success",r["success"],"loop",r["loop_ok"],"G",r["colors_with"]["green"],"R",r["colors_with"]["red"],flush=True)
res["stage"]="done"; save(res)
with open(TSV,"w",encoding="utf-8") as f:
    f.write("group\ttrial\ttarget\tanchor\thover_before\thover_after_cursor\thover_after_click\tloop_ok\titers\tgreen\tred\tsuccess\tnapowr_placed\tlink_after\n")
    for r in res.get("trials",[]):
        f.write("\t".join([r["group"],str(r["idx"]),str(r.get("target_cell")),str(r.get("anchor")),
            str(r.get("hover_before")),str(r.get("hover_after_cursor")),str(r.get("hover_after_click")),
            str(r.get("loop_ok")),str(r.get("iters")),str(r.get("colors_with",{}).get("green")),
            str(r.get("colors_with",{}).get("red")),str(r.get("success")),
            str(len([x for x in r.get("napowr_after",[]) if x["o1"]==0 and x.get("valid")])),
            str(r.get("link_after"))])+"\n")
print("DONE",flush=True)
