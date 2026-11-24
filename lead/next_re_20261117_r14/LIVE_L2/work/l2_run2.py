#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L2 corrected experiment — attaches to live game (pid from arg or file).

PRIMARY VERDICT (non-pixel): after click, read placed object's Location cell and that
cell's +0xE4/+0xE8 chain; a new BuildingClass node => placed & occupies cell.

Ghost-in-hand / build-complete are APPARATUS signals only (footprint pixel>=3000,
credit stabilization, NAPOWR o1 state) — never used for the scientific verdict.
"""
import os, sys, time, json, ctypes, struct
import w177_core as W, wb_probe as P, wc_probe as C
from w177_click import game_hwnd, force_foreground, click_client
from collections import Counter
import l2_probe_lib as L

CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2"
EVID=os.path.join(CARD,"EVIDENCE")
RESULT=os.path.join(EVID,"l2_result2.json")
TSV=os.path.join(EVID,"trials2.tsv")
PID=int(sys.argv[1]) if len(sys.argv)>1 else 41892
L.PID=PID
ICON=(2336,472)
PROBE=(1400,560)
u32=L.u32
OFFSET_GUESS=(2,-4)   # empirical from diag_click: hover(114,62)->landing(112,66)

def save(res): json.dump(res,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def footprint_ok():
    cp=L.PNT(); u32.GetCursorPos(ctypes.byref(cp))
    c=L.cols(cp.x,cp.y)
    return (c["green"]>=3000 or c["red"]>=3000), c

def credit(m,ph): return L.rd(m,ph+0x30C)

def wait_credit_stable(ph,maxs=35,stable_need=5):
    prev=None; stable=0
    for i in range(int(maxs/0.5)):
        m=W.Mem(PID); cr=credit(m,ph); m.close()
        if prev is not None and cr==prev: stable+=1
        else: stable=0
        prev=cr
        if stable>=stable_need: return prev
        time.sleep(0.5)
    return prev

def ensure_ghost(ph,res,tag):
    force_foreground(game_hwnd(PID),0.3)
    u32.SetCursorPos(*PROBE); time.sleep(0.3)
    ok,c=footprint_ok()
    if ok:
        res.setdefault("ghost",[]).append({"tag":tag,"note":"already_in_hand","cols":c}); save(res); return True
    for attempt in range(5):
        force_foreground(game_hwnd(PID),0.3)
        pre_m=W.Mem(PID); pre=credit(pre_m,ph); pre_m.close()
        okc,_=click_client(PID,ICON[0],ICON[1],"left",settle=0.3,verify=True)
        time.sleep(0.7)
        u32.SetCursorPos(*PROBE); time.sleep(0.3)
        ok,c=footprint_ok()
        if ok:
            res.setdefault("ghost",[]).append({"tag":tag,"attempt":attempt,"note":"pickup_direct","cols":c}); save(res); return True
        post_m=W.Mem(PID); post=credit(post_m,ph); post_m.close()
        # wait for construction complete if an order started
        if post is not None and pre is not None and post < pre:
            wait_credit_stable(ph)
        force_foreground(game_hwnd(PID),0.3)
        click_client(PID,ICON[0],ICON[1],"left",settle=0.3,verify=True)
        time.sleep(0.7)
        u32.SetCursorPos(*PROBE); time.sleep(0.3)
        ok,c=footprint_ok()
        res.setdefault("ghost",[]).append({"tag":tag,"attempt":attempt,"note":"order_build_pickup",
                                           "pre":pre,"post":post,"cols":c,"ok":ok}); save(res)
        if ok: return True
    res["ghost_fail"]={"tag":tag}; save(res); return False

def scan_units(ph):
    m=W.Mem(PID); ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT)
    inf=Counter(); veh=Counter()
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=L.D.rtti_name(m,q)
        if not nm: continue
        lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
        if lx is None or ly is None: continue
        c=(lx>>8,ly>>8)
        if 'InfantryClass' in nm: inf[c]+=1
        elif 'UnitClass' in nm: veh[c]+=1
    m.close(); return inf,veh

def occupied_cells(ph):
    occ=set(); m=W.Mem(PID)
    for i,o in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,o)
        if b["cell"].get("valid"): occ.add((b["cell"]["cellX"],b["cell"]["cellY"]))
    inf,veh=scan_units(ph); occ|=set(inf)|set(veh); m.close(); return occ

res={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"card":"LIVE-L2-corrected","pid":PID,
     "criterion":"post-click read placed object Location cell +0xE4/+0xE8 chain; new BuildingClass=>placed",
     "apparatus_note":"footprint/credit used ONLY to confirm ghost-in-hand; verdict is memory chain only",
     "stage":"start"}
save(res)

m=W.Mem(PID); ph=P.player_house(m)
if not ph: res["abort"]="no player house"; save(res); sys.exit(2)
res["ingame"]={"frame":m.u32(W.A_FRAME),"ph":hex(ph),"credit":credit(m,ph),
               "build_types":C.all_player_building_types(m,ph)}; save(res)
m.close()

# discover reachable empty cells near center
def reachable(cells,want):
    good=[]
    for c in cells:
        ok,cur,s,tr=L.aim(c)
        if ok and cur==c: good.append((c,s))
        if len(good)>=want: break
    return good

m=W.Mem(PID); u32.SetCursorPos(1400,700); time.sleep(0.3); center=L.hcell(m); m.close()
res["center"]=list(center) if center[0] is not None else None; save(res)
occ=occupied_cells(ph)
c0=center if center[0] is not None else (113,62)
cands=[]
for cy in range(c0[1]-10,c0[1]+10):
    for cx in range(c0[0]-12,c0[0]+12):
        if (cx,cy) in occ: continue
        m=W.Mem(PID); okc=bool(L.cell_ptr(m,cx,cy)); m.close()
        if okc: cands.append((cx,cy))
cands.sort(key=lambda c:abs(c[0]-c0[0])+abs(c[1]-c0[1]))
empty_good=reachable(cands[:70],12)
res["targets"]={"center":list(c0),"empty_good":[[list(c),[round(z,1) for z in s]] for c,s in empty_good]}
save(res)
print("center",c0,"empty_good",len(empty_good),"occ",len(occ),flush=True)

offset=[list(OFFSET_GUESS)]
def run_trial(group,idx,want_land):
    tag="L2_%s_%02d"%(group,idx+1)
    rec={"group":group,"idx":idx+1,"want_land":list(want_land)}
    m=W.Mem(PID)
    pre_placed=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
    pre_addrs={o["addr"] for o in pre_placed}
    rec["chain_before"]=L.chain_at(m,*want_land)
    rec["credit_before"]=credit(m,ph)
    m.close()
    if not ensure_ghost(ph,res,tag):
        rec.update(placed=False,success=False,verdict="no_ghost"); save(res); return rec
    hover_target=(want_land[0]+offset[0][0],want_land[1]+offset[0][1])
    rec["hover_target"]=list(hover_target)
    ok,cur,s,tr=L.aim(hover_target)
    rec["aim_ok"]=ok; rec["aim_cur"]=list(cur) if cur[0] is not None else None
    rec["aim_iters"]=len(tr); rec["screen"]=[round(z,1) for z in s]
    force_foreground(game_hwnd(PID),0.3)
    m=W.Mem(PID); rec["hover_click"]=list(L.hcell(m)); rec["cols_click"]=L.cols(s[0],s[1])
    rec["credit_click"]=credit(m,ph); m.close()
    okc,info=click_client(PID,int(s[0]),int(s[1]),"left",settle=0.3,verify=True)
    rec["click_ok"]=okc
    time.sleep(2.6)  # platform placement state settles with delay
    m=W.Mem(PID)
    post_placed=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
    new=[o for o in post_placed if o["addr"] not in pre_addrs]
    rec["new_buildings"]=new
    rec["napowr_after"]=L.napowr(m,ph)
    rec["credit_after"]=credit(m,ph)
    rec["hover_after"]=list(L.hcell(m))
    rec["frame_after"]=m.u32(W.A_FRAME)
    placed_ok=bool(new)
    landing=new[0]["cell"] if new else None
    rec["landing_cell"]=landing
    if landing:
        ch=L.chain_at(m,*landing)
        rec["chain_at_landing"]=ch
        rttis=ch.get("rttiA",[])+ch.get("rttiB",[])
        rec["lenA_land"]=ch.get("lenA"); rec["lenB_land"]=ch.get("lenB")
        rec["has_buildingclass"]=any("BuildingClass" in r for r in rttis)
        rec["new_obj_in_chain"]=any(new[0]["obj"] in (ch.get("nodesA",[])+ch.get("nodesB",[])) for _ in [0])
    else:
        rec["chain_at_landing"]=L.chain_at(m,*want_land)
        rec["lenA_land"]=rec["chain_at_landing"].get("lenA"); rec["lenB_land"]=rec["chain_at_landing"].get("lenB")
        rec["has_buildingclass"]=False; rec["new_obj_in_chain"]=False
    m.close()
    rec["placed"]=placed_ok
    rec["occupies_want"]=(landing==list(want_land))
    rec["success"]=bool(placed_ok and rec["has_buildingclass"] and rec["new_obj_in_chain"])
    if group=="A":
        if rec["success"] and landing and rec["hover_click"][0] is not None:
            off=(rec["hover_click"][0]-landing[0],rec["hover_click"][1]-landing[1])
            rec["calibrated_offset"]=list(off); offset[0]=off
        rec["verdict"]="A_success" if rec["success"] else "A_fail"
    elif group=="B":
        rec["verdict"]=("B_overlap_allowed" if (rec["success"] and rec["occupies_want"]) else
                        ("B_rejected" if not placed_ok else "B_other"))
    else:
        rec["verdict"]=("C_overlap_allowed" if (rec["success"] and rec["occupies_want"]) else
                        ("C_rejected" if not placed_ok else "C_other"))
    save(res); return rec

# ---- A gate ----
res["stage"]="A"; save(res)
A=[]
for i,(c,s) in enumerate(empty_good[:6]):
    r=run_trial("A",i,c); A.append(r); res.setdefault("trials",[]).append(r); save(res)
    print("A",i+1,"ok",r.get("success"),"land",r.get("landing_cell"),"offset",offset[0],flush=True)
Aok=sum(1 for r in A if r.get("success"))
res["A_gate"]={"n":len(A),"success":Aok,"fail":len(A)-Aok,"offset":list(offset[0]),
               "pass":Aok>len(A)/2 if A else False}
save(res); print("A_GATE",res["A_gate"],flush=True)
if res["A_gate"]["pass"]:
    res["stage"]="BC"; save(res)
    inf,veh=scan_units(ph)
    # on-screen check via aim
    def on_screen(cell):
        ht=(cell[0]+offset[0][0],cell[1]+offset[0][1])
        ok,cur,s,tr=L.aim(ht); return ok
    Bc=[c for c in sorted(inf) if on_screen(c)][:5]
    Cc=[c for c in sorted(veh) if on_screen(c)][:5]
    res["BC_targets"]={"B":[list(c) for c in Bc],"C":[list(c) for c in Cc],
                       "inf_all":{str(k):v for k,v in inf.items()},"veh_all":{str(k):v for k,v in veh.items()}}
    save(res); print("BC",Bc,Cc,flush=True)
    for i in range(5):
        if i<len(Bc):
            r=run_trial("B",i,Bc[i]); res.setdefault("trials",[]).append(r); save(res)
            print("B",i+1,r["verdict"],"want",Bc[i],"land",r.get("landing_cell"),flush=True)
        if i<len(Cc):
            r=run_trial("C",i,Cc[i]); res.setdefault("trials",[]).append(r); save(res)
            print("C",i+1,r["verdict"],"want",Cc[i],"land",r.get("landing_cell"),flush=True)
res["stage"]="done"; save(res)
# TSV
with open(TSV,"w",encoding="utf-8") as f:
    f.write("group\tidx\twant_land\thover_click\tlanding\tplaced\toccupies_want\tlenA\tlenB\thas_buildingclass\tnew_obj_in_chain\tverdict\taim_ok\n")
    for r in res.get("trials",[]):
        f.write("\t".join([r["group"],str(r["idx"]),str(r.get("want_land")),str(r.get("hover_click")),
            str(r.get("landing_cell")),str(r.get("placed")),str(r.get("occupies_want")),str(r.get("lenA_land")),
            str(r.get("lenB_land")),str(r.get("has_buildingclass")),str(r.get("new_obj_in_chain")),
            str(r.get("verdict")),str(r.get("aim_ok"))])+"\n")
print("DONE",flush=True)
