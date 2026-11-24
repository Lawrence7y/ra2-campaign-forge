#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单进程连续会话：launch->nav->deploy->order NAPOWR->wait->pickup ghost->闭环->落格+采样->收尾。
避免会话间空闲退出。全程只读 RPM + 合成输入。"""
import os, sys, time, ctypes, json, subprocess, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD=r"D:\Project\ra2-campaign-forge\ra2youli"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID=os.path.join(CARD,"EVIDENCE"); WDIR=os.path.join(CARD,"work")
PIDF=os.path.join(WDIR,"game.pid"); MY_PIDS=os.path.join(WDIR,"my_pids.txt")
HOVER=0x0088095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
SAFE=(250,2050,250,1300)
JX_JY=[(55.6,25.9),(-55.6,25.9)]  # cellX->screen, cellY->screen
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
u32.SetProcessDPIAware()
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
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
    im=ImageGrab.grab(all_screens=False); im.save(p)
    return p
def click_synth(x,y,dwell=0.3):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.2)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.09); u32.mouse_event(4,0,0,0,0); time.sleep(dwell)
def vclick(pid,x,y,wait=0.8):
    """前台校验点击：失败则重试 force_foreground 一次，仍失败抛异常。"""
    h=game_hwnd(pid)
    ok,info=click_client(pid,x,y,"left",settle=0.5,verify=True)
    if not ok:
        force_foreground(h,0.8)
        ok,info=click_client(pid,x,y,"left",settle=0.5,verify=True)
    print("  vclick",x,y,"ok",ok,info,flush=True)
    if not ok: raise RuntimeError("foreground click failed: "+info)
    time.sleep(wait)
    return ok
def key_tap(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.06); u32.keybd_event(vk,0,2,0); time.sleep(0.1)

def main():
    log={"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    # 0 residual
    n=int(subprocess.run(["powershell","-NoProfile","-Command","@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],capture_output=True,text=True).stdout.strip() or 0)
    if n!=0: print("ABORT residual",n); return 2
    det=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP
    p=subprocess.Popen([GAME],cwd=CWD,close_fds=True,creationflags=det)
    open(PIDF,"w").write(str(p.pid))
    with open(MY_PIDS,"a") as f: f.write(str(p.pid)+"\n")
    log["pid"]=p.pid; print("launched",p.pid,flush=True)
    # 等 intro splash(Westwood logo) 播完、主菜单渲染出来（首成功会话 launch.py 等了12s+截图时间）
    log["boot_wait_s"]=16
    time.sleep(16)
    hwnd=game_hwnd(p.pid)
    ff=force_foreground(hwnd,0.8); print("initial foreground",ff,flush=True)
    shot("full_menu_check")
    # nav: single->skirmish->start （全部前台校验点击）
    vclick(p.pid,720,219,1.2)   # single player
    vclick(p.pid,720,303,1.8)   # skirmish
    # start 按钮位置需从截图确认；先截图
    shot("full_sk_setup")
    vclick(p.pid,730,263,0.6)   # start game
    print("nav done",flush=True)
    # wait ingame frame>5
    for i in range(20):
        time.sleep(0.8)
        m=W.Mem(p.pid); fr=m.u32(FRAME); ph=P.player_house(m); m.close()
        if fr>5 and ph: break
    log["ingame_frame"]=fr; print("ingame frame",fr,flush=True)
    time.sleep(1.5)
    # deploy MCV: select center vehicle, press D
    click_synth(1348,495,0.5); key_tap(0x44); time.sleep(2.5)
    m=W.Mem(p.pid); ph=P.player_house(m)
    types=C.all_player_building_types(m,ph); m.close()
    log["after_deploy_types"]=types; print("deploy types",types,flush=True)
    if "NACNST" not in types:
        log["abort"]="no construction yard"; print("ABORT no yard",flush=True)
        json.dump(log,open(os.path.join(EVID,"full_run.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        return 3
    shot("full_ingame")
    # T2 order: locate icon fresh then click once
    subprocess.run([sys.executable,os.path.join(WDIR,"sidebar_locate.py"),os.path.join(EVID,"full_ingame.png")],cwd=WDIR,capture_output=True,text=True)
    grid=json.load(open(os.path.join(EVID,"sidebar_grid.json"),encoding="utf-8"))
    icon=tuple(grid["chosen"]["center"])
    log["icon"]=icon
    hwnd=game_hwnd(p.pid); force_foreground(hwnd,0.5)
    m=W.Mem(p.pid); ph=P.player_house(m)
    pre_credits=m.u32(ph+0x30C); m.close()
    ok,info=click_client(p.pid,icon[0],icon[1],"left",settle=0.4,verify=True)
    log["order_click"]={"ok":ok,"info":info,"pre_credits":pre_credits}
    print("order click",ok,"pre",pre_credits,flush=True)
    time.sleep(0.5)
    m=W.Mem(p.pid); ph=P.player_house(m)
    post_credits=m.u32(ph+0x30C); nap=[n for n in C.napowr_objects(m,ph) if n["is_player"]]; m.close()
    log["order_verify"]={"post_credits":post_credits,"player_napowr":nap}
    print("credits after order",post_credits,"player nap",len(nap),flush=True)
    if not (post_credits<pre_credits or nap):
        log["abort"]="order failed"; print("ABORT order failed",flush=True)
        json.dump(log,open(os.path.join(EVID,"full_run.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        return 4
    # wait build complete (credits stop dropping near -600)
    target_credits=pre_credits-600
    for i in range(60):
        time.sleep(0.5)
        m=W.Mem(p.pid); ph=P.player_house(m); cr=m.u32(ph+0x30C); m.close()
        if cr<=target_credits+20: break
    log["credits_built"]=cr; print("build done credits",cr,flush=True)
    time.sleep(1.0)
    # pickup ghost
    hwnd=game_hwnd(p.pid); force_foreground(hwnd,0.5)
    ok2,info2=click_client(p.pid,icon[0],icon[1],"left",settle=0.3,verify=True)
    log["pickup_click"]={"ok":ok2,"info":info2}
    print("pickup",ok2,flush=True)
    time.sleep(0.4)
    shot("full_ghost")
    # dynamic target selection: infantry cell far from yard
    m=W.Mem(p.pid); ph=P.player_house(m)
    base=rd(m,P.CELL_ARRAY)
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT)
    yard_cell=None
    for i in range(acount):
        q=m.u32(aitems+4*i)
        if not q or (q&3): continue
        if m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if nm and 'BuildingClass' in nm:
            lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
            if lx and ly: yard_cell=(lx>>8,ly>>8)
    inf_cells={}
    for i in range(acount):
        q=m.u32(aitems+4*i)
        if not q or (q&3): continue
        if m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if not nm or 'InfantryClass' not in nm: continue
        lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
        if lx and ly: inf_cells.setdefault((lx>>8,ly>>8),0); inf_cells[(lx>>8,ly>>8)]+=1
    m.close()
    # pick cell with >=1 inf, far from yard, and anchor reachable
    cands=[]
    for (cx,cy),cnt in inf_cells.items():
        d=abs(cx-yard_cell[0])+abs(cy-yard_cell[1]) if yard_cell else 99
        cands.append((d,cx,cy,cnt))
    cands.sort(key=lambda z:(-z[0],-z[3]))
    if not cands:
        log["abort"]="no infantry"; print("ABORT no inf",flush=True); return 5
    _,tx,ty,cnt=cands[0]
    anchor=(tx-1,ty-2)
    log["target"]= [tx,ty]; log["anchor"]=list(anchor); log["yard_cell"]=yard_cell
    log["inf_cells"]={str(k):v for k,v in inf_cells.items()}
    print("target",(tx,ty),"inf",cnt,"anchor",anchor,"yard",yard_cell,flush=True)
    # closed loop to anchor
    def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=cp.x,cp.y
    if not(250<=sx<=2050 and 250<=sy<=1300): sx,sy=1400,600
    m=W.Mem(p.pid)
    cam0=(rd(m,CAMX),rd(m,CAMY))
    jx=list(JX_JY[0]); jy=list(JX_JY[1]); trace=[]; okloop=False
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.34)
    cur=hcell(m)
    for it in range(40):
        cx,cy=cur; ex,ey=anchor[0]-cx,anchor[1]-cy
        trace.append({"it":it,"screen":[int(sx),int(sy)],"cell":[cx,cy],"err":[ex,ey],
                      "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)})
        if (rd(m,CAMX),rd(m,CAMY))!=cam0: break
        if ex==0 and ey==0: okloop=True; break
        dsx=0.75*(jx[0]*ex+jy[0]*ey); dsy=0.75*(jx[1]*ex+jy[1]*ey)
        osx,osy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (sx,sy)==(osx,osy): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.30)
        nxt=hcell(m)
        dsxo=sx-osx; dsyo=sy-osy; dcxo=nxt[0]-cx; dcyo=nxt[1]-cy
        if abs(dsxo)+abs(dsyo)>=8:
            erx=dcxo-(jx[0]*dsxo+jy[0]*dsyo); ery=dcyo-(jx[1]*dsxo+jy[1]*dsyo)
            n2=dsxo*dsxo+dsyo*dsyo
            if n2>0:
                jx[0]+=0.5*erx*dsxo/n2; jx[1]+=0.5*ery*dsxo/n2
                jy[0]+=0.5*erx*dsyo/n2; jy[1]+=0.5*ery*dsyo/n2
        cur=nxt
    log["closed_loop"]={"ok":okloop,"cur":cur,"iters":len(trace),"Jfinal":{"jx":jx,"jy":jy},"trace":trace,
                        "J0":{"JX":JX_JY[0],"JY":JX_JY[1]}}
    print("closed loop ok",okloop,"cur",cur,flush=True)
    shot("full_hover_anchor")
    if not okloop and cur!=(anchor[0],anchor[1]):
        log["abort"]="cannot reach anchor"; json.dump(log,open(os.path.join(EVID,"full_run.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2); m.close(); return 6
    # pre target chain
    cell=rd(m,base+((ty<<9)+tx)*4)
    hA=rd(m,cell+0xE4) if cell else None
    def chainf(head,maxn=16):
        nodes=[]; seen=set(); q=head
        while q and len(nodes)<maxn:
            if q in seen: break
            seen.add(q); nodes.append(q); q=rd(m,q+0x30)
        return nodes
    pre_nodes=chainf(hA)
    pre_rtti=[D.rtti_name(m,x)[0] for x in pre_nodes]
    log["pre_target"]={"cell":cell,"headA":hA,"lenA":len(pre_nodes),"rttiA":pre_rtti,
                       "nodesA":[hex(x) for x in pre_nodes]}
    print("pre target",len(pre_nodes),pre_rtti,flush=True)
    # high-freq sampling with click inside
    rcache={}
    def rtti(q):
        if q not in rcache: rcache[q]=D.rtti_name(m,q)[0]
        return rcache[q]
    samples=[]; t0=time.perf_counter(); dur=2.3; clicked=False; click_idx=None; click_frame=None
    while time.perf_counter()-t0<dur:
        fr=rd(m,FRAME); h=rd(m,HOVER); cx=rd(m,CAMX); cy=rd(m,CAMY)
        ch=rd(m,base+((ty<<9)+tx)*4)
        hA=rd(m,ch+0xE4) if ch else None; hB=rd(m,ch+0xE8) if ch else None
        nA=chainf(hA); nB=chainf(hB)
        samples.append({"t":round(time.perf_counter()-t0,6),"frame":fr,
                        "headA":hA,"lenA":len(nA),"rttiA":[rtti(x) for x in nA],
                        "headB":hB,"lenB":len(nB),"rttiB":[rtti(x) for x in nB],
                        "hover":h,"hover_cell":[h&0xFFFF if h else None,(h>>16)&0xFFFF if h else None],
                        "cam":[cx,cy],"credits":rd(m,ph+0x30C)})
        if not clicked and samples[-1]["t"]>0.3:
            click_idx=len(samples)-1; click_frame=fr
            fb=rd(m,FRAME)
            u32.mouse_event(2,0,0,0,0); time.sleep(0.06); u32.mouse_event(4,0,0,0,0)
            fa=rd(m,FRAME)
            ch2=rd(m,base+((ty<<9)+tx)*4); hA2=rd(m,ch2+0xE4) if ch2 else None
            nA2=chainf(hA2); fi=rd(m,FRAME)
            rA2=[rtti(x) for x in nA2]
            log["landing"]={"frame_before":fb,"frame_click":fr,"frame_after":fa,"frame_imm":fi,
                            "frames_elapsed":fi-fb,"headA":hA2,"lenA":len(nA2),"rttiA":rA2,
                            "nodesA":[hex(x) for x in nA2],
                            "has_building":any(v and 'BuildingClass' in v for v in rA2),
                            "has_infantry":any(v and 'InfantryClass' in v for v in rA2)}
            log["landing"]["main_ok"]=len(nA2)>=2 and log["landing"]["has_building"]
            clicked=True
            shot("full_after_click")
    dur_actual=samples[-1]["t"]
    jl=os.path.join(EVID,"t4_full_samples.jsonl")
    with open(jl,"w",encoding="utf-8") as f:
        for s in samples: f.write(json.dumps(s,ensure_ascii=False)+"\n")
    frames=sorted(set(s["frame"] for s in samples if s["frame"] is not None))
    log["sampling"]={"file":jl,"n_samples":len(samples),"duration_s":round(dur_actual,4),
                     "rate_per_s":round(len(samples)/dur_actual,1),
                     "distinct_frames":len(frames),"frame_min":frames[0] if frames else None,
                     "frame_max":frames[-1] if frames else None,"click_sample_index":click_idx,
                     "click_frame":click_frame,"covers_click_frame":bool(click_frame in frames),
                     "rtti_cache":{hex(k):v for k,v in rcache.items()}}
    # push analysis
    pre_inf_this=set(log["pre_target"]["nodesA"])
    last=[s for s in samples if s["t"]>dur_actual-0.5]
    li=[any(v and 'InfantryClass' in v for v in s["rttiA"]) for s in last[-3:]]
    lb=[any(v and 'BuildingClass' in v for v in s["rttiA"]) for s in last[-3:]]
    lsame=log["landing"]["has_infantry"] and log["landing"]["has_building"]
    log["push_analysis"]={"pre_inf_this":sorted(pre_inf_this),"landing_instant_same_cell":bool(lsame),
                          "last3_infantry_present":li,"last3_building_present":lb,
                          "longterm_stable_same_cell":bool(lsame and all(li) and all(lb)),
                          "pushed_away_after_landing":bool(lsame and not all(li) and all(lb)),
                          "last3_rttiA":[s["rttiA"] for s in last[-3:]]}
    log["credits_end"]=rd(m,ph+0x30C); m.close()
    json.dump(log,open(os.path.join(EVID,"full_run.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("LANDING",json.dumps(log["landing"],ensure_ascii=False),flush=True)
    print("SAMPLING",json.dumps(log["sampling"],ensure_ascii=False),flush=True)
    print("PUSH",json.dumps(log["push_analysis"],ensure_ascii=False),flush=True)
    return 0

if __name__=="__main__": sys.exit(main())
