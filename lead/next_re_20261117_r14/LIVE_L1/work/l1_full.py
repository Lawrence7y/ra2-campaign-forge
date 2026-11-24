#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 full experiment (single continuous session).
A group: empty-ground placements (negative baseline).
B group: infantry-cell placements.
C group: own-vehicle-cell placements. B/C interleaved.
All read-only RPM + synthesized mouse/keyboard. Only closes the pid it launches.
Writes EVIDENCE/l1_full_result.json + per-trial screenshots and a TSV."""
import os, sys, time, ctypes, json, struct, subprocess
from collections import Counter
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD  = r"D:\Project\ra2-campaign-forge\ra2youli"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")
WDIR = os.path.join(CARD, "work")
PIDF = os.path.join(WDIR, "game.pid")
MY_PIDS = os.path.join(WDIR, "my_pids.txt")
RESULT = os.path.join(EVID, "l1_full_result.json")
TSV = os.path.join(EVID, "trials.tsv")
HOVER=0x88095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
SAFE=(250,2050,250,1300)
JX0=(55.6,25.9); JY0=(-55.6,25.9)
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]; u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
    return None
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def shot(tag):
    p=os.path.join(EVID,tag+".png")
    ImageGrab.grab(all_screens=False).save(p); return p
def key_tap(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.08); u32.keybd_event(vk,0,2,0); time.sleep(0.15)
def click_raw(x,y,dwell=0.25):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.12)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(dwell)

def footprint_colors(sx,sy,rad=110):
    im=ImageGrab.grab(bbox=(int(sx-rad),int(sy-rad),int(sx+rad),int(sy+rad)),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size; green=red=0
    for yy in range(h):
        for xx in range(w):
            r,g,b=px[xx,yy]
            if g>180 and r<90 and b<90: green+=1
            elif r>180 and g<90 and b<90: red+=1
    return {"green":green,"red":red,"total":w*h}

def cell_ptr(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); idx=(cy<<9)+cx
    if not base or idx<0 or idx>=0x40000: return None
    c=m.u32(base+idx*4)
    return c if (c and c!=P.INVALID_CELL) else None

def cell_chain(m,cx,cy):
    c=cell_ptr(m,cx,cy)
    if not c: return {"valid":False,"lenA":0,"lenB":0,"rttiA":[],"rttiB":[]}
    out={"valid":True,"cell":hex(c)}
    for tag,off in (("A",0xE4),("B",0xE8)):
        head=m.u32(c+off); nodes=[]; seen=set(); p=head
        while p and len(nodes)<32 and p not in seen:
            seen.add(p); nodes.append(p); p=m.u32(p+0x30)
        out["head"+tag]=hex(head) if head else None
        out["len"+tag]=len(nodes)
        out["rtti"+tag]=[(D.rtti_name(m,x)[0] or "?") for x in nodes]
        out["nodes"+tag]=[hex(x) for x in nodes]
    return out

def list_napowr(m,ph):
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        cell=b["cell"]
        out.append({"obj":hex(obj),"o1_81":b["o1_81"],"o2_74":b["o2_74"],
                    "cell":[cell["cellX"],cell["cellY"]],"valid":cell["valid"],
                    "lenA":b["chains"]["lenA"]})
    return out

def player_types(m,ph):
    return C.all_player_building_types(m,ph)

def closed_loop(m,pid,anchor,trace_tag=None):
    def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=cp.x,cp.y
    if not (SAFE[0]<=sx<=SAFE[1] and SAFE[2]<=sy<=SAFE[3]): sx,sy=1400,600
    cam0=(rd(m,CAMX),rd(m,CAMY))
    jx=list(JX0); jy=list(JY0); trace=[]; ok=False
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.30)
    cur=hcell(m)
    for it in range(45):
        if cur[0] is None: time.sleep(0.2); cur=hcell(m); continue
        ex,ey=anchor[0]-cur[0],anchor[1]-cur[1]
        trace.append({"it":it,"screen":[int(sx),int(sy)],"cell":list(cur),"err":[ex,ey],
                      "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)})
        if (rd(m,CAMX),rd(m,CAMY))!=cam0: break
        if ex==0 and ey==0: ok=True; break
        dsx=0.75*(jx[0]*ex+jy[0]*ey); dsy=0.75*(jx[1]*ex+jy[1]*ey)
        ox,oy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (sx,sy)==(ox,oy): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.26)
        nxt=hcell(m)
        ddx,ddy=sx-ox,sy-oy; dcx,dcy=(nxt[0]-cur[0],nxt[1]-cur[1]) if nxt[0] is not None else (0,0)
        if abs(ddx)+abs(ddy)>=8:
            erx=dcx-(jx[0]*ddx+jy[0]*ddy); ery=dcy-(jx[1]*ddx+jy[1]*ddy)
            n2=ddx*ddx+ddy*ddy
            if n2>0:
                jx[0]+=0.5*erx*ddx/n2; jx[1]+=0.5*ery*ddx/n2
                jy[0]+=0.5*erx*ddy/n2; jy[1]+=0.5*ery*ddy/n2
        cur=nxt
    if trace_tag:
        json.dump({"anchor":list(anchor),"ok":ok,"cur":list(cur) if cur[0] is not None else None,
                   "iters":len(trace),"Jfinal":{"jx":jx,"jy":jy},"trace":trace},
                  open(os.path.join(EVID,trace_tag+".json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return ok,cur,(sx,sy),trace

def scan_units(m,ph):
    ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT)
    inf=Counter(); veh=Counter()
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if not nm: continue
        lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
        if lx is None or ly is None: continue
        c=(lx>>8,ly>>8)
        if 'InfantryClass' in nm: inf[c]+=1
        elif 'UnitClass' in nm: veh[c]+=1
    return inf,veh

def find_empty_anchors(m,occ_cells,n=6):
    # anchor A => footprint cells X[a-1..a+1], Y[a..a+1] all empty+valid
    out=[]
    for cy in range(52,67):
        for cx in range(101,120):
            fc=[(x,y) for x in range(cx-1,cx+2) for y in range(cy,cy+2)]
            if any((x,y) in occ_cells for x,y in fc): continue
            if any(not cell_ptr(m,x,y) for x,y in fc): continue
            out.append((cx,cy))
    return out[:n]

def save_checkpoint(res):
    json.dump(res, open(RESULT,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

def main():
    res={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"card":"LIVE-L1","stage":"start"}
    save_checkpoint(res)
    # residual check
    n=int(subprocess.run(["powershell","-NoProfile","-Command",
        "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True).stdout.strip() or 0)
    if n!=0:
        res["abort"]="residual gamemd=%d"%n; save_checkpoint(res); print("ABORT residual",n); return 2
    # launch (only pid we start)
    det=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    p=subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
    open(PIDF,"w").write(str(p.pid))
    with open(MY_PIDS,"a") as f: f.write(time.strftime("%Y-%m-%dT%H:%M:%S")+" pid="+str(p.pid)+"\n")
    res["pid"]=p.pid; res["stage"]="launched"; save_checkpoint(res)
    print("launched",p.pid,flush=True)
    time.sleep(18)  # intro splash + main menu
    hwnd=game_hwnd(p.pid)
    # set topmost so screenshots keep showing the game even if IDE steals focus
    try:
        u32.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
        u32.SetWindowPos(hwnd,ctypes.c_void_p(-1),0,0,0,0,0x0002|0x0001)
    except Exception as e:
        res["topmost_err"]=str(e)
    ff=force_foreground(hwnd,0.8)
    res["initial_foreground"]=ff; save_checkpoint(res)
    print("foreground",ff,"curfg",hex(u32.GetForegroundWindow()),flush=True)
    shot("f_menu")
    # nav
    for name,x,y,w in [("single",720,219,1.4),("skirmish",720,303,2.0)]:
        force_foreground(game_hwnd(p.pid),0.4)
        ok,info=click_client(p.pid,x,y,"left",settle=0.4,verify=True)
        res["nav_"+name]={"ok":ok,"info":info}; save_checkpoint(res)
        print("nav",name,ok,flush=True)
        if not ok: res["abort"]="nav "+name; save_checkpoint(res); return 3
        time.sleep(w)
    shot("f_sk_setup")
    force_foreground(game_hwnd(p.pid),0.4)
    ok,info=click_client(p.pid,730,263,"left",settle=0.4,verify=True)
    res["nav_start"]={"ok":ok,"info":info}; save_checkpoint(res)
    print("nav start",ok,flush=True)
    if not ok: res["abort"]="nav start"; save_checkpoint(res); return 4
    # wait in-game + player house
    fr=0; ph=None
    for i in range(30):
        time.sleep(0.8)
        m=W.Mem(p.pid); fr=m.u32(FRAME); ph=P.player_house(m); m.close()
        if fr>5 and ph: break
    res["ingame"]={"frame":fr,"playerHouse":hex(ph) if ph else None}; save_checkpoint(res)
    print("ingame frame",fr,"ph",hex(ph) if ph else None,flush=True)
    if not (fr>5 and ph): res["abort"]="no ingame"; save_checkpoint(res); return 5
    time.sleep(1.5)
    force_foreground(game_hwnd(p.pid),0.5)
    # deploy MCV if needed
    m=W.Mem(p.pid); pt=player_types(m,ph); m.close()
    res["pre_deploy_types"]=pt; save_checkpoint(res)
    if "NACNST" not in pt:
        m=W.Mem(p.pid)
        ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); mcv=None
        for i in range(ac):
            q=m.u32(ai+4*i)
            if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
            nm,_=D.rtti_name(m,q)
            if nm and 'UnitClass' in nm:
                lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
                if lx and ly: mcv=(lx>>8,ly>>8); break
        m.close()
        res["mcv_cell"]=mcv; save_checkpoint(res)
        if mcv:
            m=W.Mem(p.pid)
            ok,cur,screen,_=closed_loop(m,p.pid,mcv,"f_mcv_closedloop")
            m.close()
            sx,sy=screen
        else: sx,sy=1350,485
        force_foreground(game_hwnd(p.pid),0.5)
        click_raw(sx,sy,0.35); key_tap(0x44); time.sleep(2.5)
        m=W.Mem(p.pid); pt=player_types(m,ph); m.close()
        res["post_deploy_types"]=pt; save_checkpoint(res)
        print("post deploy",pt,flush=True)
        shot("f_after_deploy")
        if "NACNST" not in pt: res["abort"]="no construction yard"; save_checkpoint(res); return 6
    # locate sidebar icon
    shot("f_sidebar")
    subprocess.run([sys.executable,os.path.join(WDIR,"sidebar_locate.py"),
                    os.path.join(EVID,"f_sidebar.png")],cwd=WDIR,capture_output=True,text=True)
    grid=json.load(open(os.path.join(EVID,"sidebar_grid.json"),encoding="utf-8"))
    if not grid.get("chosen"):
        res["abort"]="no sidebar icon"; save_checkpoint(res); return 7
    icon=tuple(grid["chosen"]["center"]); res["icon"]=icon; save_checkpoint(res)
    print("icon",icon,flush=True)

    # ---- Order helper: create one limbo NAPOWR (already built) ----
    def order_build_pickup(with_baseline_anchor=None, baseline_tag=None):
        force_foreground(game_hwnd(p.pid),0.5)
        m=W.Mem(p.pid); pre=rd(m,ph+0x30C); m.close()
        ok,info=click_client(p.pid,icon[0],icon[1],"left",settle=0.35,verify=True)
        if not ok: return False,{"order_click":ok,"info":info}
        time.sleep(0.5)
        # wait for build (credit drop ~600) with timeout
        built=None
        for i in range(90):
            time.sleep(0.4)
            m=W.Mem(p.pid); cr=rd(m,ph+0x30C); m.close()
            if cr<=pre-580: built=cr; break
        # NO-GHOST BASELINE: cursor to anchor, no ghost following cursor yet
        if with_baseline_anchor is not None:
            m=W.Mem(p.pid)
            okb,cb,sb,_=closed_loop(m,p.pid,with_baseline_anchor,baseline_tag+"_closedloop")
            m.close()
            time.sleep(0.2)
            bg=footprint_colors(sb[0],sb[1])
            shot(baseline_tag+"_noghost")
            res.setdefault("baselines",{})[baseline_tag]={"anchor":list(with_baseline_anchor),
                "loop_ok":okb,"cur":list(cb) if cb[0] is not None else None,"screen":list(sb),"colors":bg}
            save_checkpoint(res)
        # pickup ghost
        force_foreground(game_hwnd(p.pid),0.5)
        ok2,info2=click_client(p.pid,icon[0],icon[1],"left",settle=0.35,verify=True)
        time.sleep(0.4)
        m=W.Mem(p.pid); nap=list_napowr(m,ph); m.close()
        limbo=[x for x in nap if x["o1_81"]==1]
        return (ok2 and bool(limbo)),{"pre_credits":pre,"built_credits":built,"pickup_ok":ok2,
                                      "limbo":limbo,"napowr":nap}

    # Is there already a limbo ghost? (from stray earlier). If not, order one.
    m=W.Mem(p.pid); nap=list_napowr(m,ph); m.close()
    if not any(x["o1_81"]==1 for x in nap):
        okd,det=order_build_pickup()
        res["initial_ghost"]={"ok":okd,"detail":det}; save_checkpoint(res)
        print("initial ghost",okd,flush=True)
        if not okd: res["abort"]="no ghost"; save_checkpoint(res); return 8
    else:
        res["initial_ghost"]={"ok":True,"detail":"existing limbo","napowr":nap}; save_checkpoint(res)

    # ---- Scan targets (infantry / vehicle / empty) ----
    m=W.Mem(p.pid); ph=P.player_house(m)
    inf,veh=scan_units(m,ph)
    inf1=dict(inf); veh1=dict(veh)
    time.sleep(1.5)
    inf2,veh2=scan_units(m,ph)
    inf_st=[k for k in inf1 if inf1.get(k)==inf2.get(k) and inf1.get(k,0)>=1]
    veh_st=[k for k in veh1 if veh1.get(k)==veh2.get(k) and veh1.get(k,0)>=1]
    occ=set(inf_st)|set(veh_st)
    # add building-occupied cells: yard (108,58) and placed napowr cells
    for obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,*obj)
        if b["cell"].get("valid"):
            occ.add((b["cell"]["cellX"],b["cell"]["cellY"]))
    empty_anchors=find_empty_anchors(m,occ,n=8)
    res["targets"]={"inf":{str(k):inf1[k] for k in inf1},"veh":{str(k):veh1[k] for k in veh1},
                    "inf_stable":[list(k) for k in sorted(inf_st)],
                    "veh_stable":[list(k) for k in sorted(veh_st)],
                    "empty_anchors":[list(a) for a in empty_anchors],
                    "frame":m.u32(FRAME)}
    m.close(); save_checkpoint(res)
    print("inf_stable",sorted(inf_st),"veh_stable",sorted(veh_st),"empty",empty_anchors[:8],flush=True)

    # trial definitions: A (empty), then B/C interleaved
    # anchor for covering target cell T is (T.x, T.y-1) so footprint Y[T.y-1..T.y] covers T
    A_targets=empty_anchors[:5]
    Bcells=sorted(inf_st); Ccells=sorted(veh_st)
    trials=[]
    for i,t in enumerate(A_targets): trials.append(("A",i,(t[0],t[1])))
    nbc=max(len(Bcells),len(Ccells),5)
    for i in range(5):
        bt=Bcells[i%len(Bcells)] if Bcells else None
        ct=Ccells[i%len(Ccells)] if Ccells else None
        if bt: trials.append(("B",i,(bt[0],bt[1]-1)))
        if ct: trials.append(("C",i,(ct[0],ct[1]-1)))

    # TSV header
    with open(TSV,"w",encoding="utf-8") as f:
        f.write("group\ttrial\ttarget_cell\tanchor\thover_before\thover_after_cursor\thover_after_click\t"
                "loop_ok\titers\tgreen_with\tred_with\tgreen_no\tred_no\tsuccess\tnapowr_count\t"
                "target_chain_before\tlink_after\tnotes\n")

    def run_trial(group,idx,anchor):
        tag="t_%s_%02d"%(group,idx+1)
        rec={"group":group,"idx":idx+1,"anchor":list(anchor)}
        # target cell whose occupancy we test: for B/C anchor=(tx,ty-1)->target=(tx,ty)
        target=(anchor[0],anchor[1]+1) if group in ("B","C") else (anchor[0],anchor[1])
        rec["target_cell"]=list(target)
        m=W.Mem(p.pid); ph2=P.player_house(m)
        rec["hover_before"]=list(hcell(m))
        pre_nap=list_napowr(m,ph2); rec["napowr_before"]=pre_nap
        chain_before=cell_chain(m,target[0],target[1]); rec["chain_before"]=chain_before
        # ensure ghost present
        limbo=[x for x in pre_nap if x["o1_81"]==1]
        if not limbo:
            m.close()
            okd,det=order_build_pickup()
            rec["reordered"]={"ok":okd,"detail":det}
            if not okd:
                rec["success"]=False; rec["notes"]="no ghost; reorder failed"
                return rec
            m=W.Mem(p.pid); ph2=P.player_house(m)
        # closed loop to anchor
        ok,cur,screen,trace=closed_loop(m,p.pid,anchor,tag+"_closedloop")
        rec["loop_ok"]=ok; rec["cur"]=list(cur) if cur[0] is not None else None
        rec["iters"]=len(trace); rec["screen"]=list(screen)
        rec["hover_after_cursor"]=list(hcell(m))
        time.sleep(0.2)
        # WITH-GHOST screenshot + colors
        colors_with=footprint_colors(screen[0],screen[1])
        rec["colors_with"]=colors_with
        shot(tag+"_withghost")
        # paired NO-GHOST baseline: right-click to cancel ghost, re-position, screenshot, then re-pickup
        colors_no={"green":None,"red":None,"total":colors_with["total"]}
        # (do paired baselines only once per group at first trial to save cycles; reuse after)
        bkey="G%s"%group
        if bkey not in res.get("baselines",{}):
            force_foreground(game_hwnd(p.pid),0.5)
            # right click on map to cancel placement
            u32.SetCursorPos(int(screen[0]),int(screen[1])); time.sleep(0.1)
            u32.mouse_event(8,0,0,0,0); time.sleep(0.07); u32.mouse_event(16,0,0,0,0); time.sleep(0.3)
            m2=W.Mem(p.pid); n2=list_napowr(m2,ph2); m2.close()
            still=[x for x in n2 if x["o1_81"]==1]
            if not still:
                # no ghost now -> move to same screen pos, capture baseline
                u32.SetCursorPos(int(screen[0]),int(screen[1])); time.sleep(0.3)
                colors_no=footprint_colors(screen[0],screen[1])
                shot(tag+"_noghost")
                res.setdefault("baselines",{})[bkey]={"anchor":list(anchor),"screen":list(screen),
                    "colors_noghost":colors_no,"colors_with_ghost":colors_with,
                    "green_ratio_with":round(colors_with["green"]/colors_with["total"],6),
                    "green_ratio_no":round(colors_no["green"]/colors_no["total"],6) if colors_no["green"] is not None else None,
                    "distinguish_x":None}
                if colors_no["green"] and colors_no["green"]>0:
                    res["baselines"][bkey]["distinguish_x"]=round(colors_with["green"]/colors_no["green"],2)
                save_checkpoint(res)
                # re-pickup ghost for the actual click
                force_foreground(game_hwnd(p.pid),0.5)
                okr,det=order_build_pickup()
                rec["repickup"]={"ok":okr,"detail":det}
                m=W.Mem(p.pid); ph2=P.player_house(m)
            else:
                rec["noghost_cancel_failed"]=still
        else:
            b=res["baselines"][bkey]
            colors_no={"green":b["colors_noghost"]["green"],"red":b["colors_noghost"]["red"],
                       "total":colors_with["total"]}
        # click to place
        fb=rd(m,FRAME)
        u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(0.6)
        fa=rd(m,FRAME)
        rec["hover_after_click"]=list(hcell(m))
        time.sleep(0.5)
        post_nap=list_napowr(m,ph2)
        rec["napowr_after"]=post_nap
        chain_after=cell_chain(m,target[0],target[1]); rec["chain_after"]=chain_after
        rec["frame_before"]=fb; rec["frame_after"]=fa
        # success criterion: a player NAPOWR with o1=0 and valid cell appeared (placed), count increase
        placed=[x for x in post_nap if x["o1_81"]==0 and x["valid"]]
        pre_placed=[x for x in pre_nap if x["o1_81"]==0 and x["valid"]]
        rec["success"]=(len(placed)>len(pre_placed))
        # overlap: target chain contains a BuildingClass after
        rec["link_after"]=any(v and 'BuildingClass' in v for v in chain_after.get("rttiA",[])+chain_after.get("rttiB",[]))
        shot(tag+"_after")
        m.close()
        return rec

    # run A group
    res["stage"]="A"; save_checkpoint(res)
    for i,a in enumerate(A_targets):
        rec=run_trial("A",i,a)
        res.setdefault("trials",[]).append(rec); save_checkpoint(res)
        print("A",i+1,"success",rec["success"],"loop",rec["loop_ok"],"green",rec["colors_with"]["green"],
              "red",rec["colors_with"]["red"],flush=True)
    # run B/C interleaved
    res["stage"]="BC"; save_checkpoint(res)
    for tr in trials:
        if tr[0]=="A": continue
        group,idx,anchor=tr
        rec=run_trial(group,idx,anchor)
        res.setdefault("trials",[]).append(rec); save_checkpoint(res)
        print(group,idx+1,"success",rec.get("success"),"loop",rec.get("loop_ok"),
              "green",rec.get("colors_with",{}).get("green"),"red",rec.get("colors_with",{}).get("red"),flush=True)
    # write TSV from trials
    with open(TSV,"w",encoding="utf-8") as f:
        f.write("group\ttrial\ttarget_cell\tanchor\thover_before\thover_after_cursor\thover_after_click\t"
                "loop_ok\titers\tgreen_with\tred_with\tgreen_no\tred_no\tsuccess\tnapowr_count\t"
                "target_chain_before\tlink_after\tnotes\n")
        for r in res.get("trials",[]):
            bl=res.get("baselines",{}).get("G"+r["group"],{})
            cnb=bl.get("colors_noghost",{})
            f.write("\t".join([r["group"],str(r["idx"]),str(r.get("target_cell")),str(r.get("anchor")),
                str(r.get("hover_before")),str(r.get("hover_after_cursor")),str(r.get("hover_after_click")),
                str(r.get("loop_ok")),str(r.get("iters")),
                str(r.get("colors_with",{}).get("green")),str(r.get("colors_with",{}).get("red")),
                str(cnb.get("green")),str(cnb.get("red")),
                str(r.get("success")),str(len([x for x in r.get("napowr_after",[]) if x.get("o1_81")==0 and x.get("valid")])),
                str(r.get("chain_before",{}).get("lenA")),str(r.get("link_after")),
                str(r.get("notes","")).replace("\t"," ").replace("\n"," ")])+"\n")
    res["stage"]="done"; save_checkpoint(res)
    print("DONE",flush=True)
    return 0

if __name__=="__main__":
    sys.exit(main())
