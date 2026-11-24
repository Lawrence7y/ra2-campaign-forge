#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B-group extension: add valid infantry-cell trials (verify InfantryClass present at click time)."""
import os,sys,time,json,ctypes
import w177_core as W, wb_probe as P, wc_probe as C
from w177_click import game_hwnd, force_foreground, click_client
from collections import Counter
import l2_probe_lib as L
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2"
EVID=os.path.join(CARD,"EVIDENCE"); RESULT=os.path.join(EVID,"l2_result3.json")
PID=41892; L.PID=PID; ICON=(2336,472); PROBE=(1400,560); u32=L.u32
def save(r): json.dump(r,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
def footprint_ok():
    cp=L.PNT(); u32.GetCursorPos(ctypes.byref(cp)); c=L.cols(cp.x,cp.y)
    return (c["green"]>=3000 or c["red"]>=3000),c
def cred(m,ph): return L.rd(m,ph+0x30C)
def wait_stable(ph,maxs=35):
    prev=None; stable=0
    for _ in range(int(maxs/0.5)):
        m=W.Mem(PID); cr=cred(m,ph); m.close()
        if cr==prev: stable+=1
        else: stable=0
        prev=cr
        if stable>=5: return prev
        time.sleep(0.5)
    return prev
def ensure_ghost(ph,tag):
    force_foreground(game_hwnd(PID),0.3); u32.SetCursorPos(*PROBE); time.sleep(0.3)
    ok,c=footprint_ok()
    if ok: return True
    for att in range(5):
        force_foreground(game_hwnd(PID),0.3)
        pm=W.Mem(PID); pre=cred(pm,ph); pm.close()
        click_client(PID,ICON[0],ICON[1],"left",settle=0.3,verify=True); time.sleep(0.7)
        u32.SetCursorPos(*PROBE); time.sleep(0.3); ok,c=footprint_ok()
        if ok: return True
        qm=W.Mem(PID); post=cred(qm,ph); qm.close()
        if post is not None and pre is not None and post<pre: wait_stable(ph)
        force_foreground(game_hwnd(PID),0.3)
        click_client(PID,ICON[0],ICON[1],"left",settle=0.3,verify=True); time.sleep(0.7)
        u32.SetCursorPos(*PROBE); time.sleep(0.3); ok,c=footprint_ok()
        if ok: return True
    return False
def scan_inf(ph):
    m=W.Mem(PID); ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); inf=Counter()
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=L.D.rtti_name(m,q)
        if not nm or 'InfantryClass' not in nm: continue
        lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
        if lx and ly: inf[(lx>>8,ly>>8)]+=1
    m.close(); return inf
res=json.load(open(RESULT,encoding="utf-8"))
m=W.Mem(PID); ph=P.player_house(m); m.close()
# count valid B trials (InfantryClass present at click)
def is_valid_b(t):
    r=(t.get("chain_before",{}).get("rttiA",[])+t.get("chain_before",{}).get("rttiB",[]))
    return any("Infantry" in x for x in r)
valid_b=sum(1 for t in res.get("trials",[]) if t["group"]=="B" and is_valid_b(t))
need=5-valid_b
print("valid B",valid_b,"need",need,flush=True)
res.setdefault("extensions",[]).append({"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"B_need":need}); save(res)
added=0; attempts=0
while added<need and attempts<12:
    attempts+=1
    inf=scan_inf(ph); cands=sorted(inf)
    print("attempt",attempts,"inf cells",cands,flush=True)
    progressed=False
    for cell in cands:
        ht=(cell[0]+1,cell[1])
        ok,cur,s,tr=L.aim(ht)
        if not ok: continue
        force_foreground(game_hwnd(PID),0.3)
        m=W.Mem(PID); cb=L.chain_at(m,*cell); rtti=(cb.get("rttiA",[])+cb.get("rttiB",[]))
        has_inf=any("InfantryClass" in r for r in rtti); m.close()
        if not has_inf: continue
        if not ensure_ghost(ph,"L2EXT_B_%02d"%(added+1)):
            print("no ghost ABORT",flush=True); save(res); sys.exit(2)
        ok,cur,s,tr=L.aim(ht); force_foreground(game_hwnd(PID),0.3)
        m=W.Mem(PID); cb=L.chain_at(m,*cell); rtti=(cb.get("rttiA",[])+cb.get("rttiB",[]))
        has_inf=any("InfantryClass" in r for r in rtti)
        if not has_inf: m.close(); continue
        pre_addrs={o["addr"] for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]}
        rec={"group":"B","idx":sum(1 for t in res.get("trials",[]) if t["group"]=="B")+1,"want_land":list(cell),
             "extension":True,"chain_before":cb,"hover_click":list(L.hcell(m)),
             "cols_click":L.cols(s[0],s[1]),"credit_before":cred(m,ph)}
        m.close()
        click_client(PID,int(s[0]),int(s[1]),"left",settle=0.3,verify=True); time.sleep(2.6)
        m=W.Mem(PID)
        post=[o for o in L.napowr(m,ph) if o["o1"]==0 and o["valid"]]
        new=[o for o in post if o["addr"] not in pre_addrs]
        rec["new_buildings"]=new; rec["napowr_after"]=L.napowr(m,ph); rec["credit_after"]=cred(m,ph)
        landing=new[0]["cell"] if new else None; rec["landing_cell"]=landing; rec["placed"]=bool(new)
        if landing:
            ch=L.chain_at(m,*landing); rec["chain_at_landing"]=ch; rttis=ch.get("rttiA",[])+ch.get("rttiB",[])
            rec["rtti_at_landing"]=rttis; rec["lenA_land"]=ch.get("lenA"); rec["lenB_land"]=ch.get("lenB")
            rec["has_buildingclass"]=any("BuildingClass" in r for r in rttis)
            rec["new_obj_in_chain"]=new[0]["obj"] in (ch.get("nodesA",[])+ch.get("nodesB",[]))
        else:
            rec["chain_at_landing"]=L.chain_at(m,*cell); rec["rtti_at_landing"]=[]
            rec["has_buildingclass"]=False; rec["new_obj_in_chain"]=False
        m.close()
        rec["occupies_want"]=(landing==list(cell))
        rec["success"]=bool(rec["placed"] and rec["has_buildingclass"] and rec["new_obj_in_chain"])
        rec["verdict"]=("B_overlap_allowed" if (rec["success"] and rec["occupies_want"]) else
                        ("B_rejected" if not rec["placed"] else "B_other"))
        res.setdefault("trials",[]).append(rec); added+=1; save(res)
        print("B ext",added,"want",cell,"verdict",rec["verdict"],"land",landing,flush=True)
        progressed=True; break
    if not progressed: time.sleep(1.0)
res["stage"]="done_ext2"; save(res)
with open(os.path.join(EVID,"trials3.tsv"),"w",encoding="utf-8") as f:
    f.write("group\tidx\twant\thover\tlanding\tplaced\toccupies\tlenA\tlenB\thasBuildingClass\tnewObjInChain\tverdict\taim_ok\n")
    for t in res.get("trials",[]):
        f.write("\t".join([t["group"],str(t["idx"]),str(t.get("want_land")),str(t.get("hover_click")),
            str(t.get("landing_cell")),str(t.get("placed")),str(t.get("occupies_want")),str(t.get("lenA_land")),
            str(t.get("lenB_land")),str(t.get("has_buildingclass")),str(t.get("new_obj_in_chain")),
            str(t.get("verdict")),str(t.get("aim_ok"))])+"\n")
print("B EXT DONE added",added,flush=True)
