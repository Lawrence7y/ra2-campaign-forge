#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 v2 experiment — corrected ghost state machine.
Ghost-in-hand verified by footprint-green probe (not o1). No-ghost baseline captured before pickup.
A=empty, B=infantry cell, C=own vehicle cell (B/C interleaved). Read-only RPM + synthesized input.
Only closes the pid it launches. Writes EVIDENCE/l1_v5_result.json + screenshots + trials_v5.tsv.
"""
import os, sys, time, ctypes, json, struct, subprocess
from collections import Counter
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; CWD=r"D:\Project\ra2-campaign-forge\ra2youli"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID=os.path.join(CARD,"EVIDENCE"); WDIR=os.path.join(CARD,"work")
RESULT=os.path.join(EVID,"l1_v5_result.json"); TSV=os.path.join(EVID,"trials_v5.tsv")
PIDF=os.path.join(WDIR,"game.pid"); MY_PIDS=os.path.join(WDIR,"my_pids.txt")
HOVER=0x88095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
SAFE=(420,2070,360,1120)   # tighter: avoid edge auto-scroll
JX0=(55.6,25.9); JY0=(-55.6,25.9)
PROBE_SCREEN=(1400,560)    # central known-reachable probe cell
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]; u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
pid=None  # set in main; used by helper funcs
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def shot(tag):
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+".png"))
def key_tap(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.08); u32.keybd_event(vk,0,2,0); time.sleep(0.12)
def click_raw(x,y,dwell=0.25):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.12)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(dwell)
def cols(sx,sy,rad=110):
    im=ImageGrab.grab(bbox=(int(sx-rad),int(sy-rad),int(sx+rad),int(sy+rad)),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size; g=r=0
    for y in range(h):
        for x in range(w):
            R,G,B=px[x,y]
            if G>180 and R<90 and B<90: g+=1
            elif R>180 and G<90 and B<90: r+=1
    return {"green":g,"red":r,"total":w*h}
def save(res): json.dump(res,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

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
        out["head"+tag]=hex(head) if head else None; out["len"+tag]=len(nodes)
        out["rtti"+tag]=[(D.rtti_name(m,x)[0] or "?") for x in nodes]
        out["nodes"+tag]=[hex(x) for x in nodes]
    return out

def napowr(m,ph):
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        c=b["cell"]
        out.append({"obj":hex(obj),"o1":b["o1_81"],"o2":b["o2_74"],"cell":[c["cellX"],c["cellY"]],
                    "valid":c["valid"],"lenA":b["chains"]["lenA"]})
    return out

def closed_loop(m,anchor,tag=None,cam_guard=True):
    def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=cp.x,cp.y
    if not (SAFE[0]<=sx<=SAFE[1] and SAFE[2]<=sy<=SAFE[3]): sx,sy=1400,600
    cam0=(rd(m,CAMX),rd(m,CAMY)); jx=list(JX0); jy=list(JY0); trace=[]; ok=False
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.28); cur=hcell(m)
    for it in range(45):
        if cur[0] is None: time.sleep(0.2); cur=hcell(m); continue
        ex,ey=anchor[0]-cur[0],anchor[1]-cur[1]
        trace.append({"it":it,"screen":[round(sx,1),round(sy,1)],"cell":list(cur),"err":[ex,ey],
                      "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)})
        if cam_guard and (rd(m,CAMX),rd(m,CAMY))!=cam0: break
        if ex==0 and ey==0: ok=True; break
        dsx=0.75*(jx[0]*ex+jy[0]*ey); dsy=0.75*(jx[1]*ex+jy[1]*ey)
        ox,oy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (sx,sy)==(ox,oy): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.24)
        nxt=hcell(m)
        ddx,ddy=sx-ox,sy-oy; dcx,dcy=(nxt[0]-cur[0],nxt[1]-cur[1]) if nxt[0] is not None else (0,0)
        if abs(ddx)+abs(ddy)>=8:
            erx=dcx-(jx[0]*ddx+jy[0]*ddy); ery=dcy-(jx[1]*ddx+jy[1]*ddy); n2=ddx*ddx+ddy*ddy
            if n2>0:
                jx[0]+=0.5*erx*ddx/n2; jx[1]+=0.5*ery*ddx/n2
                jy[0]+=0.5*erx*ddy/n2; jy[1]+=0.5*ery*ddy/n2
        cur=nxt
    if tag:
        json.dump({"anchor":list(anchor),"ok":ok,"cur":list(cur) if cur[0] is not None else None,
                   "iters":len(trace),"Jfinal":{"jx":jx,"jy":jy},"trace":trace},
                  open(os.path.join(EVID,tag+"_closedloop.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return ok,cur,(sx,sy),trace

def scan_units(m,ph):
    ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); inf=Counter(); veh=Counter()
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

def find_empty(m,occ,n=40):
    out=[]
    for cy in range(52,70):
        for cx in range(98,122):
            fc=[(x,y) for x in range(cx-1,cx+2) for y in range(cy,cy+2)]
            if any((x,y) in occ for x,y in fc): continue
            if any(not cell_ptr(m,x,y) for x,y in fc): continue
            out.append((cx,cy))
    return out[:n]

def ghost_ready(m,ph,icon,res,tag=""):
    """Return True if ghost is in hand (footprint green at probe). If not, order+pickup until yes."""
    for attempt in range(4):
        force_foreground(game_hwnd(pid),0.4)
        u32.SetCursorPos(*PROBE_SCREEN); time.sleep(0.32)
        c=cols(*PROBE_SCREEN)
        if c["green"]>=3000 or c["red"]>=3000:
            return True  # footprint present (green=valid or red=invalid). grass baseline ~1000; real footprint ~11000+
        # need to pick up. click icon once; observe credits
        m0=W.Mem(pid); pre=rd(m0,ph+0x30C); m0.close()
        force_foreground(game_hwnd(pid),0.4)
        ok,info=click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
        time.sleep(0.5)
        m1=W.Mem(pid); post=rd(m1,ph+0x30C); m1.close()
        ordered = post < pre-5
        if ordered:
            # wait build complete (credits settle)
            for i in range(100):
                time.sleep(0.4)
                m2=W.Mem(pid); cr=rd(m2,ph+0x30C); m2.close()
                if cr<=pre-580: break
            time.sleep(0.8)
            force_foreground(game_hwnd(pid),0.4)
            ok2,_=click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
            time.sleep(0.4)
            res.setdefault("orders",[]).append({"tag":tag,"attempt":attempt,"pre":pre,"post":post,"ordered":ordered,"pickup":ok2})
        else:
            res.setdefault("orders",[]).append({"tag":tag,"attempt":attempt,"pre":pre,"post":post,"ordered":False,"note":"icon click = pickup?"})
        save(res)
    u32.SetCursorPos(*PROBE_SCREEN); time.sleep(0.3)
    c=cols(*PROBE_SCREEN)
    res["ghost_ready_fail"]={"tag":tag,"final_colors":c}
    save(res)
    return c["green"]>=3000 or c["red"]>=3000

# ---------------- main ----------------
res={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"card":"LIVE-L1-v5","stage":"start"}
save(res)
n=int(subprocess.run(["powershell","-NoProfile","-Command","@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True).stdout.strip() or 0)
if n!=0:
    res["abort"]="residual %d"%n; save(res); print("ABORT residual",n); sys.exit(2)
det=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
p=subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
open(PIDF,"w").write(str(p.pid))
with open(MY_PIDS,"a") as f: f.write(time.strftime("%Y-%m-%dT%H:%M:%S")+" pid="+str(p.pid)+"\n")
pid=p.pid; res["pid"]=pid; save(res); print("launched",pid,flush=True)
time.sleep(18)
hwnd=game_hwnd(pid)
try:
    u32.SetWindowPos.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_uint]
    u32.SetWindowPos(hwnd,ctypes.c_void_p(-1),0,0,0,0,0x0002|0x0001)
except Exception: pass
ff=force_foreground(hwnd,0.8); res["fg"]=ff; save(res)
shot("v2_menu")
for name,x,y,w in [("single",720,219,1.4),("skirmish",720,303,2.0)]:
    force_foreground(game_hwnd(pid),0.4)
    ok,info=click_client(pid,x,y,"left",settle=0.4,verify=True)
    res["nav_"+name]=ok; save(res)
    if not ok: res["abort"]="nav "+name; save(res); sys.exit(3)
    time.sleep(w)
shot("v2_sk")
force_foreground(game_hwnd(pid),0.4)
ok,_=click_client(pid,730,263,"left",settle=0.4,verify=True)
res["nav_start"]=ok; save(res)
if not ok: res["abort"]="nav start"; save(res); sys.exit(4)
fr=0; ph=None
for i in range(30):
    time.sleep(0.8)
    m=W.Mem(pid); fr=m.u32(FRAME); ph=P.player_house(m); m.close()
    if fr>5 and ph: break
res["ingame"]={"frame":fr,"ph":hex(ph) if ph else None}; save(res)
if not (fr>5 and ph): res["abort"]="no ingame"; save(res); sys.exit(5)
time.sleep(1.2)
force_foreground(game_hwnd(pid),0.5)
# deploy MCV
m=W.Mem(pid); pts=C.all_player_building_types(m,ph); m.close(); res["pre_deploy"]=pts; save(res)
if "NACNST" not in pts:
    m=W.Mem(pid); ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); mcv=None
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if nm and 'UnitClass' in nm:
            lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
            if lx and ly: mcv=(lx>>8,ly>>8); break
    m.close(); res["mcv"]=mcv; save(res)
    if mcv:
        m=W.Mem(pid); o,c,s,_=closed_loop(m,mcv,"v2_mcv"); m.close(); sx,sy=s
    else: sx,sy=1350,485
    # deploy with retries: click MCV + D, verify NACNST; retry with neighbor screen positions
    def do_deploy(sx,sy):
        force_foreground(game_hwnd(pid),0.6)
        ok,info=click_client(pid,int(sx),int(sy),"left",settle=0.4,verify=True)
        if u32.GetForegroundWindow()==game_hwnd(pid): key_tap(0x44)
        else: force_foreground(game_hwnd(pid),0.4); key_tap(0x44)
        time.sleep(2.2)
        m=W.Mem(pid); p2=C.all_player_building_types(m,ph); m.close()
        return p2
    pts=do_deploy(sx,sy)
    for doff in [(28,13),(-28,-13),(56,28),(-56,-28),(0,30)]:
        if "NACNST" in pts: break
        pts=do_deploy(sx+doff[0],sy+doff[1])
    res["post_deploy"]=pts; save(res)
    if "NACNST" not in pts: res["abort"]="no yard"; save(res); sys.exit(6)
# locate icon
shot("v2_sidebar")
subprocess.run([sys.executable,os.path.join(WDIR,"sidebar_locate.py"),os.path.join(EVID,"v2_sidebar.png")],cwd=WDIR,capture_output=True,text=True)
grid=json.load(open(os.path.join(EVID,"sidebar_grid.json"),encoding="utf-8"))
if not grid.get("chosen"): res["abort"]="no icon"; save(res); sys.exit(7)
icon=tuple(grid["chosen"]["center"]); res["icon"]=icon; save(res); print("icon",icon,flush=True)

# ---- targets first (needed to choose a valid empty baseline cell) ----
m=W.Mem(pid); ph=P.player_house(m)
inf1,veh1=scan_units(m,ph); time.sleep(1.5); inf2,veh2=scan_units(m,ph)
inf_st=[k for k in inf1 if inf1.get(k)==inf2.get(k) and inf1.get(k,0)>=1]
veh_st=[k for k in veh1 if veh1.get(k)==veh2.get(k) and veh1.get(k,0)>=1]
occ=set(inf_st)|set(veh_st)
for i,o in P.enumerate_buildings(m)[2]:
    b=P.one_building(m,i,o)
    if b["cell"].get("valid"): occ.add((b["cell"]["cellX"],b["cell"]["cellY"]))
empty=find_empty(m,occ,n=12); frame=m.u32(FRAME); m.close()
res["targets"]={"inf":{str(k):inf1[k] for k in inf1},"veh":{str(k):veh1[k] for k in veh1},
    "inf_stable":[list(k) for k in sorted(inf_st)],"veh_stable":[list(k) for k in sorted(veh_st)],
    "empty":[list(a) for a in empty],"frame":frame}; save(res)
print("inf",sorted(inf_st),"veh",sorted(veh_st),"empty",empty[:10],flush=True)

# pick reachable A anchors: verify closed-loop convergence, spread >=3 cells apart
m=W.Mem(pid); good_A=[]
for a in empty:
    if any(max(abs(a[0]-g[0]),abs(a[1]-g[1]))<3 for g in good_A):
        continue
    ok,cur,s,_=closed_loop(m,a)
    if ok and cur==a: good_A.append(a)
    if len(good_A)>=5: break
m.close(); res["good_A"]=[list(a) for a in good_A]; save(res)
print("good_A",good_A,flush=True)
if len(good_A)<5: res["note"]="only %d reachable A anchors"%len(good_A)

# ---- NO-GHOST BASELINE at a confirmed empty cell (good_A[0]) ----
base_anchor=good_A[0] if good_A else PROBE_SCREEN
m=W.Mem(pid); okb,curb,sb,_=closed_loop(m,base_anchor); m.close()
force_foreground(game_hwnd(pid),0.4)
u32.SetCursorPos(int(sb[0]),int(sb[1])); time.sleep(0.35)
m=W.Mem(pid); hc0=hcell(m); m.close()
cn=cols(sb[0],sb[1]); shot("v2_baseline_noghost")
res["baseline_noghost"]={"anchor":list(base_anchor),"screen":list(sb),"loop_ok":okb,"cur":list(curb) if curb[0] is not None else None,
    "hover":list(hc0),"colors":cn}; save(res); print("NOGHOST",cn,"hover",hc0,"anchor",base_anchor,flush=True)
PROBE_BASE=(int(sb[0]),int(sb[1]))  # use SAME screen pos for with-ghost baseline

# ---- ensure ghost in hand (first order) ----
if not ghost_ready(m:=W.Mem(pid),ph,icon,res,"init"):
    m.close(); res["abort"]="cannot get ghost"; save(res); sys.exit(8)
m.close()
# with-ghost baseline at SAME screen pos as no-ghost baseline
force_foreground(game_hwnd(pid),0.4)
u32.SetCursorPos(*PROBE_BASE); time.sleep(0.35)
m=W.Mem(pid); hc1=hcell(m); placed0=napowr(m,ph); m.close()
cw=cols(*PROBE_BASE); shot("v2_baseline_withghost")
res["baseline_withghost"]={"anchor":list(base_anchor),"screen":list(PROBE_BASE),"hover":list(hc1),"colors":cw,
    "green_ratio_with":round(cw["green"]/cw["total"],6),
    "green_ratio_no":round(cn["green"]/cn["total"],6),
    "distinguish_x":round(cw["green"]/cn["green"],2) if cn["green"]>0 else None}
save(res); print("WITHGHOST",cw,"ratio",res["baseline_withghost"]["distinguish_x"],flush=True)

# trials: A (5), then B/C interleaved (5 each)
def target_of(group,anchor):
    return (anchor[0],anchor[1]+1) if group in ("B","C") else anchor
def run_trial(group,idx,anchor):
    tag="v2_%s_%02d"%(group,idx+1); rec={"group":group,"idx":idx+1,"anchor":list(anchor)}
    target=target_of(group,anchor); rec["target_cell"]=list(target)
    m=W.Mem(pid); ph2=P.player_house(m)
    rec["hover_before"]=list(hcell(m)); pre_nap=napowr(m,ph2); rec["napowr_before"]=pre_nap
    rec["chain_before"]=cell_chain(m,*target)
    pre_placed=[x for x in pre_nap if x["o1"]==0 and x["valid"]]; m.close()
    # ensure ghost
    m=W.Mem(pid)
    if not ghost_ready(m,ph2,icon,res,tag):
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
nb=max(len(Bc),len(Cc),5)
for i in range(5):
    if Bc:
        b=Bc[i%len(Bc)]; r=run_trial("B",i,(b[0],b[1]-1)); res.setdefault("trials",[]).append(r); save(res)
        print("B",i+1,"success",r["success"],"loop",r["loop_ok"],"G",r["colors_with"]["green"],"R",r["colors_with"]["red"],flush=True)
    if Cc:
        c=Cc[i%len(Cc)]; r=run_trial("C",i,(c[0],c[1]-1)); res.setdefault("trials",[]).append(r); save(res)
        print("C",i+1,"success",r["success"],"loop",r["loop_ok"],"G",r["colors_with"]["green"],"R",r["colors_with"]["red"],flush=True)
res["stage"]="done"; save(res)
# TSV
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
