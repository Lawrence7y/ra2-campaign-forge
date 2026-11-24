#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对照实验：同一 ghost 放到"全绿"空格，验证放置机制可用并测实际地基偏移。
程序化检测落格预览颜色（绿=valid/红=invalid）；找全绿点点击；读落格后 BuildingClass 的 cell，
与 hover cell 比较得实际 offset。只读 RPM + 合成输入。"""
import os, sys, time, ctypes, json, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import game_hwnd, force_foreground

HOVER=0x88095C
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
EVID=os.path.join(CARD,"EVIDENCE")
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
    return None
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def footprint_colors(sx,sy,rad=110):
    """在光标周围区域统计纯绿/纯红像素数（RA2 落格预览色）。"""
    im=ImageGrab.grab(bbox=(sx-rad,sy-rad,sx+rad,sy+rad),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size
    green=red=0
    for y in range(h):
        for x in range(w):
            r,g,b=px[x,y]
            if g>180 and r<90 and b<90: green+=1
            elif r>180 and g<90 and b<90: red+=1
    return green,red

def main():
    pid=W.pid_of()
    if not pid: print("no gamemd"); return 2
    h=game_hwnd(pid)
    fg=force_foreground(h,0.8); print("fg",fg,flush=True)
    m=W.Mem(pid); ph=P.player_house(m)
    log={"pid":pid,"fg":fg,"credits":rd(m,ph+0x30C)}
    # 候选屏幕点（空白地形，离建造场/单位远）
    cands=[(1900,850),(1750,900),(1000,900),(900,700),(1600,1000),(2000,700),(1100,1050)]
    chosen=None
    for sx,sy in cands:
        u32.SetCursorPos(sx,sy); time.sleep(0.3)
        hc=hcell(m)
        g,r=footprint_colors(sx,sy)
        log.setdefault("candidates",[]).append({"screen":[sx,sy],"hover":hc,"green":g,"red":r})
        print("cand",(sx,sy),"hover",hc,"green",g,"red",r,flush=True)
        if g>200 and r<30:
            chosen=(sx,sy,hc); break
    if not chosen:
        # 放宽：绿>红
        for c in log["candidates"]:
            if c["green"]>c["red"] and c["green"]>100:
                chosen=(c["screen"][0],c["screen"][1],c["hover"]); break
    if not chosen:
        log["abort"]="no green spot"; json.dump(log,open(os.path.join(EVID,"control_place.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2); m.close(); return 3
    sx,sy,hc=chosen
    u32.SetCursorPos(sx,sy); time.sleep(0.3)
    g,r=footprint_colors(sx,sy)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"control_preview.png"))
    log["chosen"]={"screen":[sx,sy],"hover":hc,"green":g,"red":r}
    print("chosen",log["chosen"],flush=True)
    # 点击放置
    fb=rd(m,0xA8ED84)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.08); u32.mouse_event(4,0,0,0,0); time.sleep(0.6)
    fa=rd(m,0xA8ED84)
    time.sleep(1.0)
    # 读玩家 NAPOWR 是否落地
    pl=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]==ph and b["type"]=="NAPOWR":
            c=b["cell"]
            pl.append({"obj":hex(obj),"o1":b["o1_81"],"cell":[c["cellX"],c["cellY"]],
                       "cell_valid":c["valid"],"lenA":b["chains"]["lenA"]})
    log["after"]={"frame_before":fb,"frame_after":fa,"player_napowr":pl,"credits":rd(m,ph+0x30C)}
    if pl and pl[0]["cell_valid"]:
        bx,by=pl[0]["cell"]
        log["measured_offset"]={"hover":hc,"building_cell":[bx,by],"offset":[bx-hc[0],by-hc[1]]}
        print("PLACED cell",(bx,by),"offset from hover",log["measured_offset"]["offset"],flush=True)
    else:
        print("NOT placed",pl,flush=True)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"control_after.png"))
    m.close()
    json.dump(log,open(os.path.join(EVID,"control_place.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("saved",flush=True)
    return 0

if __name__=="__main__": main()
