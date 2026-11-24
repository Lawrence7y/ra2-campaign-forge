#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 phase2 — resume from in-game with construction yard already deployed.
Locate icon -> no-ghost/with-ghost paired baseline -> A/B/C trials (B/C interleaved).
Read-only RPM + synthesized input. Does NOT launch/close the game."""
import os, sys, time, ctypes, json, struct, subprocess
from l1_helpers import *   # rd,hcell,shot,key_tap,click_raw,cols,save,cell_ptr,cell_chain,napowr,closed_loop,scan_units,find_empty,ghost_ready,W,P,C,D,u32,k32,icon not set
from l1_helpers import W, P, C, D, u32, k32, HOVER, FRAME, PROBE_SCREEN, CARD, EVID, WDIR

RESULT=os.path.join(EVID,"l1_phase2_result.json"); TSV=os.path.join(EVID,"trials_phase2.tsv")
# override save to phase2 file
def save2(res): json.dump(res,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
import l1_helpers as H
H.save=save2
save=save2

pid=W.pid_of()
H.pid=pid  # helpers' ghost_ready/closed_loop use module-global pid
res={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"card":"LIVE-L1-phase2","pid":pid,"stage":"start"}
save(res)
if not pid: res["abort"]="no gamemd"; save(res); sys.exit(2)
ph=P.player_house(W.Mem(pid))
m=W.Mem(pid); pts=C.all_player_building_types(m,ph); cr=m.u32(W.A_FRAME); m.close()
res["start"]={"types":pts,"frame":cr}; save(res)
print("start",pts,"frame",cr,flush=True)
if "NACNST" not in pts: res["abort"]="no construction yard"; save(res); sys.exit(3)

# locate icon
force_foreground(game_hwnd(pid),0.5)
shot("p2_sidebar")
subprocess.run([sys.executable,os.path.join(WDIR,"sidebar_locate.py"),os.path.join(EVID,"p2_sidebar.png")],cwd=WDIR,capture_output=True,text=True)
grid=json.load(open(os.path.join(EVID,"sidebar_grid.json"),encoding="utf-8"))
if grid.get("chosen"):
    icon=tuple(grid["chosen"]["center"])
else:
    # fallback: (2336,472) is the NAPOWR tile (磁能反應爐) programmatically found by W177-I
    # and re-confirmed in this card's l1_full/l1_v2 runs (top-left build tile).
    icon=(2336,472)
res["icon"]=icon; res["icon_source"]="sidebar_locate" if grid.get("chosen") else "verified_fallback"; save(res); print("icon",icon,res["icon_source"],flush=True)

# ---- targets first ----
m=W.Mem(pid); ph=P.player_house(m)
inf1,veh1=scan_units(m,ph); time.sleep(1.5); inf2,veh2=scan_units(m,ph)
inf_st=[k for k in inf1 if inf1.get(k)==inf2.get(k) and inf1.get(k,0)>=1]
veh_st=[k for k in veh1 if veh1.get(k)==veh2.get(k) and veh1.get(k,0)>=1]
# dynamic empty-cell scan around occupied cells (units+buildings), since camera/map region varies
occ=set(inf_st)|set(veh_st)
for i,o in P.enumerate_buildings(m)[2]:
    b=P.one_building(m,i,o)
    if b["cell"].get("valid"): occ.add((b["cell"]["cellX"],b["cell"]["cellY"]))
xs=[c[0] for c in occ] or [110]; ys=[c[1] for c in occ] or [60]
x0,x1=max(1,min(xs)-8), min(510,max(xs)+8); y0,y1=max(1,min(ys)-8), min(510,max(ys)+8)
empty=[]
for cy in range(y0,y1+1):
    for cx in range(x0,x1+1):
        fc=[(x,y) for x in range(cx-1,cx+2) for y in range(cy,cy+2)]
        if any((x,y) in occ for x,y in fc): continue
        if any(not cell_ptr(m,x,y) for x,y in fc): continue
        empty.append((cx,cy))
# restrict empty cells to a compact box around the UNIT cluster (those are in/near the viewport)
unitcells=list(inf_st)+list(veh_st)
cx_med=sorted(c[0] for c in unitcells)[len(unitcells)//2] if unitcells else 110
cy_med=sorted(c[1] for c in unitcells)[len(unitcells)//2] if unitcells else 60
empty_sorted=sorted(empty, key=lambda a: abs(a[0]-cx_med)+abs(a[1]-cy_med))
empty=empty_sorted
frame=m.u32(FRAME); m.close()
res["targets"]={"inf":{str(k):inf1[k] for k in inf1},"veh":{str(k):veh1[k] for k in veh1},
    "inf_stable":[list(k) for k in sorted(inf_st)],"veh_stable":[list(k) for k in sorted(veh_st)],
    "unit_center":[cx_med,cy_med],"scan_box":[x0,y0,x1,y1],"n_empty":len(empty),"empty":[list(a) for a in empty[:40]],"frame":frame}; save(res)
print("inf",sorted(inf_st),"veh",sorted(veh_st),"center",(cx_med,cy_med),"n_empty",len(empty),flush=True)

# good_A spread anchors reachable
m=W.Mem(pid); good_A=[]; tried=0
for a in empty:
    if tried>=40 or len(good_A)>=5: break
    if any(max(abs(a[0]-g[0]),abs(a[1]-g[1]))<3 for g in good_A): continue
    tried+=1
    ok,cur,s,_=closed_loop(m,a)
    if ok and cur==a: good_A.append(a)
m.close(); res["good_A"]=[list(a) for a in good_A]; save(res); print("good_A",good_A,"tried",tried,flush=True)
if len(good_A)<5: res["note"]="only %d reachable A anchors"%len(good_A)

# ---- need a ghost: check current NAPOWR limbo/placed, order if none limbo ----
m=W.Mem(pid); ph=P.player_house(m); cur_nap=napowr(m,ph); m.close()
res["cur_nap_start"]=cur_nap; save(res)
# We must ensure a ghost is IN HAND. Use footprint probe (green or red >=3000).
# H.ghost_ready probes PROBE_SCREEN; if no footprint, it orders+pickups.
force_foreground(game_hwnd(pid),0.5)
u32.SetCursorPos(*PROBE_SCREEN); time.sleep(0.3)
pc=cols(*PROBE_SCREEN); res["probe_initial"]=pc; save(res)
print("probe initial",pc,flush=True)
if not H.ghost_ready(W.Mem(pid),ph,icon,res,"init"):
    res["abort"]="cannot get ghost"; save(res); sys.exit(5)
print("ghost in hand",flush=True)

# ---- paired pixel baseline: NOGHOST (no ghost) then WITHGHOST at same empty cell ----
# NOTE: to get a true no-ghost screenshot we must cancel ghost. Use ESC (not right-click), verify footprint gone, then re-pickup.
base_anchor=good_A[0]
m=W.Mem(pid); okb,curb,sb,_=closed_loop(m,base_anchor); m.close()
force_foreground(game_hwnd(pid),0.4); u32.SetCursorPos(int(sb[0]),int(sb[1])); time.sleep(0.35)
cw=cols(sb[0],sb[1]); shot("p2_baseline_withghost")   # ghost currently in hand
# cancel via ESC
force_foreground(game_hwnd(pid),0.4)
H.key_tap(0x1B); time.sleep(0.4)
u32.SetCursorPos(int(sb[0]),int(sb[1])); time.sleep(0.35)
cn=cols(sb[0],sb[1]); shot("p2_baseline_noghost")
res["baseline"]={"anchor":list(base_anchor),"screen":list(sb),
    "withghost":cw,"noghost_esc":cn,
    "green_ratio_with":round(cw["green"]/cw["total"],6),
    "green_ratio_no":round(cn["green"]/cn["total"],6),
    "distinguish_x":round(cw["green"]/cn["green"],2) if cn["green"]>0 else None}
save(res); print("BASELINE with G",cw["green"],"no G",cn["green"],"ratio",res["baseline"]["distinguish_x"],flush=True)
# re-pickup ghost after ESC
if not H.ghost_ready(W.Mem(pid),ph,icon,res,"repickup_after_esc"):
    res["abort"]="cannot repickup after ESC"; save(res); sys.exit(6)
print("repickup ok",flush=True)

def target_of(group,anchor):
    return (anchor[0],anchor[1]+1) if group in ("B","C") else anchor
def run_trial(group,idx,anchor):
    tag="p2_%s_%02d"%(group,idx+1); rec={"group":group,"idx":idx+1,"anchor":list(anchor)}
    target=target_of(group,anchor); rec["target_cell"]=list(target)
    m=W.Mem(pid); ph2=P.player_house(m)
    rec["hover_before"]=list(hcell(m)); pre_nap=napowr(m,ph2); rec["napowr_before"]=pre_nap
    rec["chain_before"]=cell_chain(m,*target)
    pre_placed=[x for x in pre_nap if x["o1"]==0 and x["valid"]]; m.close()
    # ensure ghost in hand
    m=W.Mem(pid)
    if not H.ghost_ready(m,ph2,icon,res,tag):
        m.close(); rec["success"]=False; rec["note"]="no ghost"; return rec
    ok,cur,screen,trace=closed_loop(m,anchor,tag)
    rec["loop_ok"]=ok; rec["cur"]=list(cur) if cur[0] is not None else None
    rec["iters"]=len(trace); rec["screen"]=list(screen); rec["hover_after_cursor"]=list(hcell(m))
    rec["colors_with"]=cols(screen[0],screen[1]); shot(tag+"_withghost")
    fb=rd(m,FRAME); u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(0.6); fa=rd(m,FRAME)
    rec["hover_after_click"]=list(hcell(m)); time.sleep(0.4)
    post_nap=napowr(m,ph2); rec["napowr_after"]=post_nap
    rec["chain_after"]=cell_chain(m,*target); rec["frame_before"]=fb; rec["frame_after"]=fa
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
