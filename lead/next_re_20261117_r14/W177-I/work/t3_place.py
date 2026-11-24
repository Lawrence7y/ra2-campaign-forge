#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3+T4：闭环到 anchor -> 高頻采样(覆盖点击帧) -> 落格 -> ≤2帧原子读 -> 3s推挤诊断。
只读 RPM + 合成输入；不写内存/不注入。主判据 nA>=2 且含 BuildingClass。"""
import os, sys, time, ctypes, json, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import dsnap as D
from w177_click import game_hwnd, force_foreground

HOVER=0x0088095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
SAFE=(250,2050,250,1300)
TARGET=(113,63)   # 3 InfantryClass, far from yard(108,58)
ANCHOR=(112,61)   # = T-(1,2): foundation (112..114, 62..63) covers T(113,63)
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID=os.path.join(CARD,"EVIDENCE")
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]

# 审计拟合：cell->screen 的 px/格 正向 J
JX=(55.6,25.9)   # cellX +1 -> screen (+55.6,+25.9)
JY=(-55.6,25.9)  # cellY +1 -> screen (-55.6,+25.9)

b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
    return None
def hover_cell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))

def closed_loop(m, sx, sy, tx, ty, maxit=40):
    """自适应闭环：迭代到 hover==(tx,ty)，相机变了就报停。"""
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.34)
    cam0=(rd(m,CAMX),rd(m,CAMY))
    trace=[]; jx=list(JX); jy=list(JY)
    cur=hover_cell(m)
    ok=False
    for it in range(maxit):
        cx,cy=cur; ex,ey=tx-cx,ty-cy
        rec={"it":it,"screen":[int(sx),int(sy)],"cell":[cx,cy],"err":[ex,ey],
             "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)}
        trace.append(rec)
        if (rec["cam"])!=(cam0): return {"ok":False,"reason":"camera moved","trace":trace,"cur":cur}
        if ex==0 and ey==0: ok=True; break
        # 用 J 求屏幕增量: ds = Jx*ex + Jy*ey  (damped)
        damp=0.75
        dsx=damp*(jx[0]*ex+jy[0]*ey)
        dsy=damp*(jx[1]*ex+jy[1]*ey)
        nsx,nsy=clamp(sx+dsx,sy+dsy)
        if (nsx,nsy)==(int(sx),int(sy)):
            return {"ok":False,"reason":"clamped","trace":trace,"cur":cur}
        osx,osy=sx,sy
        sx,sy=nsx,nsy
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.30)
        nxt=hover_cell(m)
        # 自适应修正 J（Broyden rank-1）
        dsxo=sx-osx; dsyo=sy-osy
        dcxo=nxt[0]-cx; dcyo=nxt[1]-cy
        if abs(dsxo)+abs(dsyo)>=8:
            predx=jx[0]*dsxo+jy[0]*dsyo; predy=jx[1]*dsxo+jy[1]*dsyo
            erx=dcxo-predx; ery=dcyo-predy
            n2=dsxo*dsxo+dsyo*dsyo
            if n2>0:
                jx[0]+=0.5*erx*dsxo/n2; jx[1]+=0.5*ery*dsxo/n2
                jy[0]+=0.5*erx*dsyo/n2; jy[1]+=0.5*ery*dsyo/n2
        cur=nxt
    if ok:
        time.sleep(0.2)
        c2=hover_cell(m)
        if c2!=(tx,ty) or (rd(m,CAMX),rd(m,CAMY))!=cam0:
            return {"ok":False,"reason":"confirm failed","trace":trace,"cur":c2}
    return {"ok":ok,"trace":trace,"cur":cur,"screen":[int(sx),int(sy)],"cam0":cam0,
            "J0":{"JX":JX,"JY":JY},"Jfinal":{"jx":jx,"jy":jy}}

def cell_ptr(m,tx,ty,base):
    idx=(ty<<9)+tx
    return rd(m,base+idx*4)

def chain_fast(m,head,maxn=16):
    nodes=[]; seen=set(); p=head; cyc=False
    while p and len(nodes)<maxn:
        if p in seen: cyc=True; break
        seen.add(p); nodes.append(p); p=rd(m,p+0x30)
    return nodes,cyc

def main():
    pid=W.pid_of()
    if not pid: print("no gamemd"); return 2
    hwnd=game_hwnd(pid)
    fg=force_foreground(hwnd,0.5) if hwnd else False
    print("fg",fg,flush=True)
    if not fg: return 3
    m=W.Mem(pid); ph=P.player_house(m)
    base=rd(m,P.CELL_ARRAY)  # cell array base via dword
    # wb_probe.CELL_ARRAY is address of dword holding base
    base=rd(m,P.CELL_ARRAY)
    rec={"pid":pid,"target":TARGET,"anchor":ANCHOR,"foreground":fg,
         "frame_start":rd(m,FRAME),"credits_start":rd(m,ph+0x30C)}

    # pre target chain
    cell=cell_ptr(m,*TARGET,base)
    hA=rd(m,cell+0xE4) if cell else None
    nA,_=chain_fast(m,hA)
    rec["pre_target"]={"cell":cell,"headA":hA,"lenA":len(nA),
                       "nodesA":[hex(x) for x in nA],
                       "rttiA":[D.rtti_name(m,x)[0] for x in nA]}
    print("pre target lenA",len(nA),rec["pre_target"]["rttiA"],flush=True)

    # closed loop to anchor (start from current cursor pos)
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp))
    sx0,sy0=(cp.x,cp.y)
    if not (250<=sx0<=2050 and 250<=sy0<=1300): sx0,sy0=1400,600
    g=closed_loop(m,sx0,sy0,*ANCHOR)
    rec["goto"]=g
    print("goto ok",g["ok"],"cur",g["cur"],"iters",len(g["trace"]),flush=True)
    if not g["ok"]:
        # retry from last screen
        ls=g["trace"][-1]["screen"]
        g2=closed_loop(m,ls[0],ls[1],*ANCHOR)
        rec["goto2"]=g2
        if not g2["ok"] and hover_cell(m)!=ANCHOR:
            print("ABORT: cannot reach anchor",flush=True)
            json.dump(rec,open(os.path.join(EVID,"t3_place.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
            m.close(); return 4
    rec["hover_at_click"]=hover_cell(m)
    rec["cam_at_click"]=[rd(m,CAMX),rd(m,CAMY)]
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"t3_placement_preview.png"))

    # ---- high-freq sampling covering the click ----
    rtti_cache={}
    def rtti(p):
        if p not in rtti_cache: rtti_cache[p]=D.rtti_name(m,p)[0]
        return rtti_cache[p]
    samples=[]
    click_idx=[None]
    frame_click=[None]
    dur=2.3
    t0=time.perf_counter()
    clicked=False
    while time.perf_counter()-t0 < dur:
        idx=len(samples)
        fr=rd(m,FRAME); h=rd(m,HOVER); cx=rd(m,CAMX); cy=rd(m,CAMY)
        ch=cell_ptr(m,*TARGET,base)
        hA=rd(m,ch+0xE4) if ch else None; hB=rd(m,ch+0xE8) if ch else None
        nA,_=chain_fast(m,hA); nB,_=chain_fast(m,hB)
        s={"t":round(time.perf_counter()-t0,6),"frame":fr,
           "headA":hA,"lenA":len(nA),"rttiA":[rtti(x) for x in nA],
           "headB":hB,"lenB":len(nB),"rttiB":[rtti(x) for x in nB],
           "hover":h,"hover_cell":[h&0xFFFF if h else None,(h>>16)&0xFFFF if h else None],
           "cam":[cx,cy],"credits":rd(m,ph+0x30C)}
        samples.append(s)
        # 在中段点击（确保窗口覆盖点击帧：前后都有样本）
        if not clicked and s["t"]>0.3:
            frame_before=rd(m,FRAME)
            u32.mouse_event(2,0,0,0,0); time.sleep(0.06); u32.mouse_event(4,0,0,0,0)
            frame_after=rd(m,FRAME)
            click_idx[0]=idx; frame_click[0]=fr
            # 立即原子读（一次紧凑链读）
            ch2=cell_ptr(m,*TARGET,base)
            hA2=rd(m,ch2+0xE4) if ch2 else None
            nA2,_=chain_fast(m,hA2)
            frame_imm=rd(m,FRAME)
            rec["landing"]={"frame_before":frame_before,"frame_click_frame":fr,
                            "frame_after":frame_after,"frame_imm":frame_imm,
                            "frames_elapsed":frame_imm-frame_before,
                            "target_cell":ch2,"headA":hA2,"lenA":len(nA2),
                            "rttiA":[rtti(x) for x in nA2],
                            "nodesA":[hex(x) for x in nA2]}
            rttiA=rec["landing"]["rttiA"]
            rec["landing"]["has_building"]=any(v and 'BuildingClass' in v for v in rttiA)
            rec["landing"]["has_infantry"]=any(v and 'InfantryClass' in v for v in rttiA)
            rec["landing"]["main_ok"]=(len(nA2)>=2 and rec["landing"]["has_building"])
            clicked=True
            ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"t3_after_click.png"))
    dur_actual=samples[-1]["t"]
    # write JSONL (full, no truncation)
    jl=os.path.join(EVID,"t4_landing_samples.jsonl")
    with open(jl,"w",encoding="utf-8") as f:
        for s in samples: f.write(json.dumps(s,ensure_ascii=False)+"\n")
    frames=sorted(set(s["frame"] for s in samples if s["frame"] is not None))
    rec["sampling"]={"file":jl,"n_samples":len(samples),"duration_s":round(dur_actual,4),
                     "rate_per_s":round(len(samples)/dur_actual,1) if dur_actual else 0,
                     "distinct_frames":len(frames),
                     "frame_min":frames[0] if frames else None,"frame_max":frames[-1] if frames else None,
                     "click_sample_index":click_idx[0],"click_frame":frame_click[0],
                     "covers_click_frame":bool(frame_click[0] in frames),
                     "rtti_cache":{hex(k):v for k,v in rtti_cache.items()}}
    # push analysis: 落格瞬间同格 vs 长期稳定同格（分别给结论）
    # pre infantry this set：从下单前已存的 pre_target head 重新取（retro 读当前不可靠，用 pre 记录）
    pre_inf_this=set(rec["pre_target"]["nodesA"])
    last=[s for s in samples if s["t"]>dur_actual-0.5]
    last_inf_present=[any(v and 'InfantryClass' in v for v in s["rttiA"]) for s in last[-3:]]
    last_bld_present=[any(v and 'BuildingClass' in v for v in s["rttiA"]) for s in last[-3:]]
    landing_same = rec["landing"]["has_infantry"] and rec["landing"]["has_building"]
    rec["push_analysis"]={
        "pre_inf_this":sorted(pre_inf_this),
        "landing_instant_same_cell":bool(landing_same),
        "last3_rttiA":[s["rttiA"] for s in last[-3:]],
        "last3_infantry_present":last_inf_present,
        "last3_building_present":last_bld_present,
        "longterm_stable_same_cell":bool(landing_same and all(last_inf_present) and all(last_bld_present)),
        "pushed_away_after_landing":bool(landing_same and not all(last_inf_present) and all(last_bld_present)),
        "lenA_last":[s["lenA"] for s in last[-3:]]}
    rec["credits_end"]=rd(m,ph+0x30C)
    m.close()
    p=os.path.join(EVID,"t3_place.json")
    json.dump(rec,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("LANDING",json.dumps(rec.get("landing"),ensure_ascii=False),flush=True)
    print("SAMPLING",json.dumps(rec["sampling"],ensure_ascii=False),flush=True)
    print("saved",p,flush=True)
    return 0 if rec["landing"]["main_ok"] else 5

if __name__=="__main__": sys.exit(main())
