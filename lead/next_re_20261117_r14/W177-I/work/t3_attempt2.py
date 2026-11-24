#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3 第2次尝试：用实测地基偏移 [hover-1..hover+1, hover..hover+1] 重算 anchor，
在步兵格落格。单进程：order->build->pickup->闭环(修正anchor)->采样点击->原子读。"""
import os,sys,time,ctypes,json,struct
from PIL import ImageGrab
import w177_core as W, wb_probe as P, wc_probe as C, dsnap as D
from w177_click import click_client,game_hwnd,force_foreground

U=ctypes.windll.user32;K=ctypes.windll.kernel32;U.SetProcessDPIAware()
EVID=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I\EVIDENCE"
class PNT(ctypes.Structure):_fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
U.GetCursorPos.argtypes=[ctypes.POINTER(PNT)];U.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
U.mouse_event.argtypes=[ctypes.c_ulong]*4+[ctypes.c_size_t]
b4=ctypes.create_string_buffer(4);got=ctypes.c_size_t(0)
def rd(m,va):
    if K.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:return struct.unpack('<I',b4.raw)[0]
    return None
def hc(m):
    v=rd(m,0x88095C);return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def vclick(pid,x,y,w=0.6):
    ok,info=click_client(pid,x,y,"left",settle=0.5,verify=True)
    if not ok: force_foreground(game_hwnd(pid),0.8);ok,info=click_client(pid,x,y,"left",settle=0.5,verify=True)
    if not ok: raise RuntimeError(info)
    time.sleep(w);return ok
def clamp(x,y):return(max(250,min(2050,x)),max(250,min(1300,y)))

def main():
    pid=W.pid_of()
    if not pid:print("no gamemd");return 2
    force_foreground(game_hwnd(pid),0.8)
    m=W.Mem(pid);ph=P.player_house(m)
    log={"pid":pid}
    # icon (已知中心)
    icon=(2336,472)
    # 找步兵格（3个 infantry，远离已放置的 NAPOWR 105-107,60-61 与 yard 108,58）
    aitems=m.u32(P.A_ABSTRACT_ITEMS);acount=m.u32(P.A_ABSTRACT)
    inf={}
    for i in range(acount):
        q=m.u32(aitems+4*i)
        if not q or(q&3) or m.u32(q+0x21C)!=ph:continue
        nm,_=D.rtti_name(m,q)
        if not nm or 'InfantryClass' not in nm:continue
        lx=m.u32(q+0x9C);ly=m.u32(q+0xA0)
        if lx and ly:inf[(lx>>8,ly>>8)]=inf.get((lx>>8,ly>>8),0)+1
    # 选 3-inf 且 x>=110 (远离已放建筑)
    cands=[(cnt,cx,cy) for (cx,cy),cnt in inf.items() if cnt>=1 and cx>=110]
    cands.sort(key=lambda z:(-z[0],z[1]))
    if not cands:print("no inf");return 3
    _,tx,ty=cands[0]
    # 实测 footprint: X{hover-1,hover,hover+1}, Y{hover,hover+1}
    # 使 T 在 footprint 中心列、下排: hover=(tx,ty-1)
    anchor=(tx,ty-1)
    log.update({"target":[tx,ty],"anchor":anchor,"inf_cells":{str(k):v for k,v in inf.items()}})
    print("target",(tx,ty),"anchor",anchor,"inf",[c for c in cands[:4]],flush=True)
    # order
    pre=m.u32(ph+0x30C)
    vclick(pid,*icon,0.4)
    m2=W.Mem(pid);post=m2.u32(ph+0x30C);m2.close()
    print("order credits",pre,"->",post,flush=True)
    log["order"]={"pre":pre,"post":post}
    if post>=pre: print("ORDER FAILED");return 4
    # wait build
    tgt=pre-600
    for i in range(60):
        time.sleep(0.5);mm=W.Mem(pid);cr=mm.u32(ph+0x30C);mm.close()
        if cr<=tgt+20:break
    log["built_credits"]=cr;print("built",cr,flush=True)
    time.sleep(0.8)
    # pickup
    force_foreground(game_hwnd(pid),0.6)
    vclick(pid,*icon,0.3)
    m=W.Mem(pid);log["pickup_credits"]=m.u32(ph+0x30C)
    time.sleep(0.3)
    # closed loop to corrected anchor
    cp=PNT();U.GetCursorPos(ctypes.byref(cp));sx,sy=cp.x,cp.y
    if not(250<=sx<=2050 and 250<=sy<=1300):sx,sy=1400,600
    cam0=(rd(m,0x886FA0),rd(m,0x886FA4));jx=[55.6,25.9];jy=[-55.6,25.9];trace=[];ok_=False
    U.SetCursorPos(int(sx),int(sy));time.sleep(0.34);cur=hc(m)
    for it in range(40):
        cx,cy=cur;ex,ey=anchor[0]-cx,anchor[1]-cy
        trace.append({"it":it,"screen":[int(sx),int(sy)],"cell":[cx,cy],"err":[ex,ey],"cam":[rd(m,0x886FA0),rd(m,0x886FA4)],"frame":rd(m,0xA8ED84)})
        if (rd(m,0x886FA0),rd(m,0x886FA4))!=cam0:break
        if ex==0 and ey==0:ok_=True;break
        dsx=0.75*(jx[0]*ex+jy[0]*ey);dsy=0.75*(jx[1]*ex+jy[1]*ey)
        ox,oy=sx,sy;sx,sy=clamp(sx+dsx,sy+dsy)
        if(sx,sy)==(ox,oy):break
        U.SetCursorPos(int(sx),int(sy));time.sleep(0.30)
        nx=hc(m);dxo=sx-ox;dyo=sy-oy;dcxo=nx[0]-cx;dcyo=nx[1]-cy
        if abs(dxo)+abs(dyo)>=8:
            erx=dcxo-(jx[0]*dxo+jy[0]*dyo);ery=dcyo-(jx[1]*dxo+jy[1]*dyo);n2=dxo*dxo+dyo*dyo
            if n2>0:jx[0]+=0.5*erx*dxo/n2;jx[1]+=0.5*ery*dxo/n2;jy[0]+=0.5*erx*dyo/n2;jy[1]+=0.5*ery*dyo/n2
        cur=nx
    log["loop"]={"ok":ok_,"cur":cur,"trace":trace,"J0":{"JX":[55.6,25.9],"JY":[-55.6,25.9]},"Jf":{"jx":jx,"jy":jy}}
    print("loop",ok_,cur,flush=True)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"t3b_preview.png"))
    if not ok_ and cur!=anchor:print("CANNOT REACH");return 5
    # pre target
    base=rd(m,P.CELL_ARRAY)
    cell=rd(m,base+((ty<<9)+tx)*4);hA=rd(m,cell+0xE4) if cell else None
    def chainf(head,maxn=16):
        n=[];s=set();p=head
        while p and len(n)<maxn and p not in s:s.add(p);n.append(p);p=rd(m,p+0x30)
        return n
    pre=chainf(hA)
    log["pre_target"]={"cell":cell,"headA":hA,"lenA":len(pre),"rttiA":[D.rtti_name(m,x)[0] for x in pre],"nodesA":[hex(x) for x in pre]}
    print("pre target",len(pre),log["pre_target"]["rttiA"],flush=True)
    # sampling + click
    rc={}
    def rtti(q):
        if q not in rc:rc[q]=D.rtti_name(m,q)[0]
        return rc[q]
    samples=[];t0=time.perf_counter();dur=2.3;clicked=False;ci=None;cf=None
    while time.perf_counter()-t0<dur:
        fr=rd(m,0xA8ED84);h=rd(m,0x88095C)
        ch=rd(m,base+((ty<<9)+tx)*4);hA=rd(m,ch+0xE4) if ch else None;hB=rd(m,ch+0xE8) if ch else None
        nA=chainf(hA);nB=chainf(hB)
        samples.append({"t":round(time.perf_counter()-t0,6),"frame":fr,"headA":hA,"lenA":len(nA),"rttiA":[rtti(x) for x in nA],"headB":hB,"lenB":len(nB),"rttiB":[rtti(x) for x in nB],"hover":h,"cam":[rd(m,0x886FA0),rd(m,0x886FA4)],"credits":rd(m,ph+0x30C)})
        if not clicked and samples[-1]["t"]>0.3:
            ci=len(samples)-1;cf=fr;fb=rd(m,0xA8ED84)
            U.mouse_event(2,0,0,0,0);time.sleep(0.05);U.mouse_event(4,0,0,0,0)
            fa=rd(m,0xA8ED84)
            ch2=rd(m,base+((ty<<9)+tx)*4);hA2=rd(m,ch2+0xE4) if ch2 else None
            nA2=chainf(hA2);fi=rd(m,0xA8ED84);rA=[rtti(x) for x in nA2]
            log["landing"]={"fb":fb,"fc":fr,"fa":fa,"fi":fi,"frames_elapsed":fi-fb,"headA":hA2,"lenA":len(nA2),"rttiA":rA,"nodesA":[hex(x) for x in nA2],"has_building":any(v and 'BuildingClass' in v for v in rA),"has_infantry":any(v and 'InfantryClass' in v for v in rA)}
            log["landing"]["main_ok"]=len(nA2)>=2 and log["landing"]["has_building"]
            clicked=True
            ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"t3b_after_click.png"))
    da=samples[-1]["t"];frames=sorted(set(s["frame"] for s in samples if s["frame"]))
    jl=os.path.join(EVID,"t4_attempt2_samples.jsonl")
    with open(jl,"w",encoding="utf-8") as f:
        for s in samples:f.write(json.dumps(s,ensure_ascii=False)+"\n")
    log["sampling"]={"file":jl,"n":len(samples),"dur":round(da,4),"rate":round(len(samples)/da,1),"distinct_frames":len(frames),"fmin":frames[0],"fmax":frames[-1],"click_frame":cf,"covers":bool(cf in frames),"ci":ci,"rtti_cache":{hex(k):v for k,v in rc.items()}}
    # push
    last=[s for s in samples if s["t"]>da-0.5]
    li=[any(v and 'InfantryClass' in v for v in s["rttiA"]) for s in last[-3:]]
    lb=[any(v and 'BuildingClass' in v for v in s["rttiA"]) for s in last[-3:]]
    lsame=log["landing"]["has_infantry"] and log["landing"]["has_building"]
    log["push"]={"landing_same":bool(lsame),"last_inf":li,"last_bld":lb,"longterm":bool(lsame and all(li) and all(lb)),"pushed":bool(lsame and not all(li) and all(lb)),"last_rtti":[s["rttiA"] for s in last[-3:]]}
    log["credits_end"]=rd(m,ph+0x30C);m.close()
    json.dump(log,open(os.path.join(EVID,"t3b_full.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("LANDING",json.dumps(log["landing"],ensure_ascii=False),flush=True)
    print("SAMPLE",json.dumps({k:log["sampling"][k] for k in ["n","dur","rate","distinct_frames","fmin","fmax","click_frame","covers"]},ensure_ascii=False),flush=True)
    print("PUSH",json.dumps(log["push"],ensure_ascii=False),flush=True)
    return 0
if __name__=="__main__":main()
