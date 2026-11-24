#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整 T2 尝试：order -> wait ready -> pickup ghost -> 高频采样+放置 -> 校验落格。
用法: t2_place.py <cx> <cy> <sx> <sy> <tag> [dur] [click_at]
"""
import sys, os, time, json, ctypes, struct
from ctypes import wintypes as wt
import w177_core as W
import wb_probe as P
import dsnap as D

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
u32 = ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
LD, LU = 0x0002, 0x0004
k32 = ctypes.windll.kernel32
ICON = (2328, 480)
VA_LO, VA_HI = 0x00400000, 0x00900000
def dok(o): return bool(o) and (o&3)==0 and 0x00100000<=o<=0x7FFFFFFF
def dva(v): return bool(v) and VA_LO<=v<=VA_HI

class FM:
    def __init__(self,h):
        self.h=h; self.b4=ctypes.create_string_buffer(4); self.b1=ctypes.create_string_buffer(1)
        self.b32=ctypes.create_string_buffer(32); self.got=ctypes.c_size_t(0)
    def rd(self,va,buf,n):
        if k32.ReadProcessMemory(self.h,ctypes.c_void_p(va),buf,n,ctypes.byref(self.got)) and self.got.value==n:return buf.raw[:n]
        return None
    def u32(self,va):
        b=self.rd(va,self.b4,4);return struct.unpack("<I",b)[0] if b else None
    def u8(self,va):
        b=self.rd(va,self.b1,1);return b[0] if b else None
    def name(self,td):
        b=self.rd(td+8,self.b32,32)
        if not b:return None
        z=b.find(b"\x00");s=b if z<0 else b[:z]
        try:s=s.decode("latin-1")
        except:return None
        return s if s.startswith(".?A") else None

def rtti(fm,obj):
    vp=fm.u32(obj) if dok(obj) else None
    if not dva(vp):return None,vp
    col=fm.u32(vp-4)
    if not dva(col):return None,vp
    td=fm.u32(col+0xC)
    if not dva(td):return None,vp
    return fm.name(td),vp

def bare_click(x,y):
    u32.SetCursorPos(x,y);time.sleep(0.12)
    u32.mouse_event(LD,0,0,0,0);time.sleep(0.07);u32.mouse_event(LU,0,0,0,0);time.sleep(0.12)

def player_napowr(m,ph):
    items=m.u32(P.A_ABSTRACT_ITEMS);count=m.u32(P.A_ABSTRACT);out=[]
    for i in range(count):
        p=m.u32(items+4*i)
        if not p or (p&3):continue
        if m.u32(p)==0x7E3EBC and m.u32(p+0x21C)==ph and P.ascii_at(m,m.u32(p+0x520)+0x24,12)=="NAPOWR":
            out.append(p)
    return out

def napowr_cells(m,target):
    base=m.u32(P.CELL_ARRAY);mapc=P.MAP_SINGLETON;w=m.u32(mapc+0x14C);h=m.u32(mapc+0x150);hits=[]
    for cy in range(h):
        rb=base+((cy<<9))*4;buf=ctypes.create_string_buffer(w*4);got=ctypes.c_size_t(0)
        if not W.k32.ReadProcessMemory(m.h,ctypes.c_void_p(rb),buf,w*4,ctypes.byref(got)):continue
        for cx in range(w):
            cell=int.from_bytes(buf.raw[cx*4:cx*4+4],"little")
            if not cell or cell==P.INVALID_CELL:continue
            p=m.u32(cell+0xE4);seen=set()
            while p and p not in seen and len(seen)<16:
                seen.add(p)
                if p==target:hits.append((cx,cy));break
                p=m.u32(p+0x30)
    return sorted(hits)

def main():
    cx=int(sys.argv[1]);cy=int(sys.argv[2]);sx=int(sys.argv[3]);sy=int(sys.argv[4]);tag=sys.argv[5]
    dur=float(sys.argv[6]) if len(sys.argv)>6 else 2.0
    click_at=float(sys.argv[7]) if len(sys.argv)>7 else 0.40
    pid=W.pid_of();m=W.Mem(pid);fm=FM(m.h);ph=P.player_house(m)
    c0=m.u32(ph+0x30C)
    before=set(player_napowr(m,ph))
    rec={"tag":tag,"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"pid":pid,"frame0":m.u32(W.A_FRAME),
         "credit_before":c0,"target_cell":[cx,cy],"screen":[sx,sy],"existing_napowr":[hex(x) for x in before]}
    # --- order ---
    bare_click(*ICON);time.sleep(0.4)
    rec["credit_after_order"]=m.u32(ph+0x30C)
    # wait ready (credit settles to c0-600)
    target_credit=c0-600
    for _ in range(30):
        time.sleep(0.3)
        if m.u32(ph+0x30C)==target_credit:break
    time.sleep(0.8)
    rec["credit_ready"]=m.u32(ph+0x30C);rec["frame_ready"]=m.u32(W.A_FRAME)
    # --- pickup ---
    bare_click(*ICON);time.sleep(0.35)
    u32.SetCursorPos(sx,sy);time.sleep(0.30)
    # verify footprint green
    from PIL import ImageGrab
    img=ImageGrab.grab(all_screens=False).convert("RGB");px=img.load()
    r=g=0
    for yy in range(max(0,sy-90),min(1440,sy+90)):
        for xx in range(max(0,sx-90),min(2560,sx+90)):
            R,G,B=px[xx,yy]
            if R>150 and G<90 and B<90:r+=1
            if G>140 and R<120 and B<120:g+=1
    rec["footprint_red"]=r;rec["footprint_green"]=g
    # --- hifreq sample + click ---
    cellbase=fm.u32(P.CELL_ARRAY);idx=(cy<<9)+cx;cell=fm.u32(cellbase+idx*4)
    rows=[];t0=time.perf_counter();clicked=False;click_t=None
    while True:
        t=time.perf_counter()-t0
        if not clicked and t>=click_at:
            u32.mouse_event(LD,0,0,0,0);u32.mouse_event(LU,0,0,0,0);click_t=t;clicked=True
        frame=fm.u32(W.A_FRAME);a7=fm.u32(0xA8E7AC);a9=fm.u8(0xA8E9A0)
        hA=fm.u32(cell+0xE4) if cell else None;hB=fm.u32(cell+0xE8) if cell else None
        def walk(head,maxn=12):
            nodes=[];seen=set();p=head
            while p and len(nodes)<maxn and dok(p):
                if p in seen:nodes.append({"this":hex(p),"rtti":"[CYCLE]"});break
                seen.add(p);nm,vp=rtti(fm,p)
                nodes.append({"this":hex(p),"vptr":hex(vp) if vp else None,"rtti":nm if nm else "[未证]",
                              "layer94":fm.u32(p+0x94) if dok(p) else None,"owner":fm.u32(p+0x21C) if dok(p) else None})
                p=fm.u32(p+0x30)
            return nodes
        nA=walk(hA);nB=walk(hB)
        rows.append([round(t,6),frame,a7,a9,hex(hA) if hA else None,hex(hB) if hB else None,len(nA),len(nB),nA,nB,
                     1 if (click_t is not None and abs(t-click_t)<0.001) else 0])
        if t>=dur:break
    wall=time.perf_counter()-t0
    hpath=os.path.join(EVID,tag+"_hifreq.jsonl")
    with open(hpath,"w",encoding="utf-8") as f:
        f.write(json.dumps({"tag":tag,"columns":["t","frame","a8e7ac","a8e9a0","headA","headB","lenA","lenB","nodesA","nodesB","click"],
                            "n":len(rows),"wall":wall,"rate":len(rows)/wall,"click_t":click_t,
                            "cell":hex(cell) if cell else None,"ts":rec["ts"]},ensure_ascii=False)+"\n")
        for rr in rows:f.write(json.dumps(rr,ensure_ascii=False)+"\n")
    rec["hifreq_n"]=len(rows);rec["hifreq_rate"]=len(rows)/wall;rec["click_t"]=click_t
    time.sleep(1.0)
    # --- verify ---
    after=set(player_napowr(m,ph));new=after-before
    rec["credit_after"]=m.u32(ph+0x30C);rec["new_napowr"]=[hex(x) for x in new]
    rec["result_cells"]={}
    for obj in new:
        rec["result_cells"][hex(obj)]=napowr_cells(m,obj)
    # target cell final detail
    rec["target_final"]={"frame":m.u32(W.A_FRAME)}
    cd=D.cell_detail(m,cx,cy)
    rec["target_final"]["lenA"]=cd.get("lenA");rec["target_final"]["lenB"]=cd.get("lenB")
    rec["target_final"]["nodesA"]=[{"this":n["this"],"rtti":n["rtti_name"],"owner":n["owner_hex"],"layer94":n["layer_94"]} for n in cd.get("nodesA",[])]
    opath=os.path.join(EVID,tag+"_result.json")
    with open(opath,"w",encoding="utf-8") as f:json.dump(rec,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps({k:rec[k] for k in ("tag","credit_before","credit_after_order","credit_ready","footprint_red","footprint_green","hifreq_n","hifreq_rate","click_t","credit_after","new_napowr","result_cells","target_final")},ensure_ascii=False,default=str))
    print("hifreq",hpath,"result",opath)
    m.close()
    return 0

if __name__=="__main__":sys.exit(main())
