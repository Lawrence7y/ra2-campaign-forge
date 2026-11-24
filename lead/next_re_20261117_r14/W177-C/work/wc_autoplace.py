#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 目标A：自动连续放置 NAPOWR，达到 >=10 次。
每次：下单(扣600) -> 等ready -> 拿起ghost -> 扫描候选点找绿框 -> 点击 -> 三重佐证校验。
避让侧栏边缘(x>2150)与屏幕边缘以防 auto-scroll。全部只读内存+合成输入。
"""
import argparse
import ctypes
import json
import os
import sys
import time
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
from w177_click import click_client, move_client, force_foreground, game_hwnd

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
ICON = (2328, 480)
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# 候选屏幕点：基地(1620,560)周围，避让侧栏(x>2150)与边缘
CAND = [
    (1300,500),(1340,540),(1380,580),(1420,620),(1460,660),
    (1500,500),(1540,540),(1580,580),(1620,500),(1660,540),
    (1700,580),(1740,620),(1780,660),(1820,500),(1860,540),
    (1900,580),(1940,620),(1980,660),(2020,580),(1200,540),
    (1260,600),(1320,660),(1380,720),(1440,760),(1500,680),
    (1560,720),(1620,760),(1680,720),(1740,760),(1800,720),
    (1860,680),(1920,720),(1980,760),(2040,700),(1100,600),
]


def colors(img, sx, sy, rad=70):
    im = img.convert("RGB"); px = im.load(); w, h = im.size
    red = green = 0
    for y in range(max(0, sy-rad), min(h, sy+rad)):
        for x in range(max(0, sx-rad), min(w, sx+rad)):
            r,g,b = px[x,y]
            if r>150 and g<90 and b<90: red+=1
            if g>140 and r<120 and b<120: green+=1
    return red,green


def stable_credit(m, ph, tries=12, gap=0.22):
    prev=None; st=0
    for _ in range(tries):
        cur=m.u32(ph+0x30C)
        if cur==prev:
            st+=1
            if st>=2: return cur
        else: st=0
        prev=cur; time.sleep(gap)
    return m.u32(ph+0x30C)


def placed_objs(m, ph):
    return {o["obj"] for o in C.napowr_objects(m,ph) if o["is_player"] and o["o1_81"]==0 and o["o2_74"]==1 and o["valid"]}


def find_green(pid, cands, used_xy):
    """移动光标找绿框；返回 (x,y,red,green,img) 或 None。"""
    u32=ctypes.windll.user32
    for (x,y) in cands:
        if (x,y) in used_xy: continue
        move_client(pid,x,y); time.sleep(0.16)
        if u32.GetForegroundWindow()!=game_hwnd(pid):
            force_foreground(game_hwnd(pid)); time.sleep(0.10)
        img=ImageGrab.grab(all_screens=False)
        red,green=colors(img,x,y)
        if green>=4000 and red<=1200:
            return (x,y,red,green,img)
    return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--n",type=int,default=10,help="number of NEW placements to attempt")
    ap.add_argument("--prefix",default="A")
    a=ap.parse_args()
    pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
    log_path=os.path.join(EVID,a.prefix+"_autoplace.jsonl")
    results=[]
    used_xy=set()
    start_credit=stable_credit(m,ph)
    print("start_credit",start_credit)

    for k in range(a.n):
        tag="%s%02d"%(a.prefix,k+2)  # A02..A11
        rec={"tag":tag,"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"k":k}
        c0=stable_credit(m,ph)
        before=placed_objs(m,ph)
        rec["credit_before_order"]=c0

        # 下单：点图标扣600
        ok,info=click_client(pid,*ICON,"left")
        time.sleep(0.35)
        c1=stable_credit(m,ph)
        rec["order"]={"ok":ok,"credit_after":c1,"deduct_600":(c1==c0-600),"info":info}
        # 等 ready
        time.sleep(2.2)
        # 拿起 ghost
        ok2,info2=click_client(pid,*ICON,"left")
        rec["pickup"]={"ok":ok2,"info":info2}
        time.sleep(0.30)

        found=find_green(pid,CAND,used_xy)
        if not found:
            rec["result"]="NO_GREEN"; results.append(rec)
            print(json.dumps({"tag":tag,"result":"NO_GREEN","credit":c1},ensure_ascii=False))
            break
        x,y,red,green,img=found
        used_xy.add((x,y))
        img.save(os.path.join(EVID,tag+"_hover.png"))
        rec["target"]={"xy":[x,y],"red":red,"green":green}

        # 点击放置
        u32=ctypes.windll.user32
        if u32.GetForegroundWindow()!=game_hwnd(pid):
            force_foreground(game_hwnd(pid)); time.sleep(0.12)
        u32.SetCursorPos(x,y); time.sleep(0.06)
        u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.10)
        u32.mouse_event(0x0004,0,0,0,0); time.sleep(1.1)
        ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+"_after.png"))

        c2=stable_credit(m,ph)
        after=placed_objs(m,ph)
        new=after-before
        attested=None
        if new:
            # 找新对象的完整记录
            obj=sorted(new)[0]
            o=[z for z in C.napowr_objects(m,ph) if z["obj"]==obj][0]
            in_chain=(obj in o["nodesA"]) or (obj in o["nodesB"])
            attested={"obj":obj,"owner":o["owner"],"owner_is_player":o["is_player"],
                      "o1_81":o["o1_81"],"o2_74":o["o2_74"],"cell":[o["cellX"],o["cellY"]],
                      "valid":o["valid"],"in_cell_chain":in_chain,
                      "lenA":o["lenA"],"lenB":o["lenB"],
                      "nodesA":o["nodesA"],"nodesB":o["nodesB"]}
            attested["attested"]=bool(attested["owner_is_player"] and attested["valid"] and in_chain and o["o1_81"]==0 and o["o2_74"]==1)
        rec["after"]={"credit":c2,"new_placed":sorted(new),"triple":attested}
        rec["success"]=bool(attested and attested["attested"])
        results.append(rec)
        print(json.dumps({"tag":tag,"target":[x,y],"red":red,"green":green,
                          "deduct":rec["order"]["deduct_600"],"success":rec["success"],
                          "triple":attested},ensure_ascii=False))
        with open(log_path,"a",encoding="utf-8") as f:
            f.write(json.dumps(rec,ensure_ascii=False,default=str)+"\n")

    end_credit=stable_credit(m,ph)
    summary={"start_credit":start_credit,"end_credit":end_credit,
             "n_attempted":len(results),
             "n_success":sum(1 for r in results if r.get("success")),
             "spent":start_credit-end_credit}
    with open(os.path.join(EVID,a.prefix+"_autoplace_summary.json"),"w",encoding="utf-8") as f:
        json.dump(summary,f,ensure_ascii=False,indent=2)
    print("SUMMARY",json.dumps(summary,ensure_ascii=False))
    return 0


if __name__=="__main__":
    sys.exit(main())
