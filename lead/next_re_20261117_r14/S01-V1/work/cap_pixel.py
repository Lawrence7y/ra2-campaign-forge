#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""截图 + 像素分析：抓游戏窗口客户区（DPI-aware），在左上 800x600 绘制区里
找黄色文字连通块（按钮文字），输出连通块 bbox 供按钮定位。
只读截图（GDI），合成输入由 w159_click 负责。
"""
import ctypes, sys, os
from ctypes import wintypes as wt
import w159_probe as W

u32 = ctypes.windll.user32
gdi = ctypes.windll.gdi32

def pid_of():
    return W.pid_of()

def game_hwnd(pid):
    found = []
    def cb(hwnd, lparam):
        t = wt.DWORD()
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(t))
        if t.value == pid and u32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    EP = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    u32.EnumWindows(EP(cb), 0)
    return found[0] if found else None

def capture(hwnd, path, w=800, h=600):
    """用屏幕 DC BitBlt 抓 hwnd 左上角 w×h（游戏只画在左上 800x600）。"""
    try: u32.SetProcessDPIAware()
    except Exception: pass
    u32.SetForegroundWindow(hwnd)
    import time; time.sleep(0.5)
    r = wt.RECT(); u32.GetWindowRect(hwnd, ctypes.byref(r))
    sx, sy = r.left, r.top
    hdc = u32.GetDC(0)
    memdc = gdi.CreateCompatibleDC(hdc)
    bmp = gdi.CreateCompatibleBitmap(hdc, w, h)
    gdi.SelectObject(memdc, bmp)
    gdi.BitBlt(memdc, 0, 0, w, h, hdc, sx, sy, 0x00CC0020)  # SRCCOPY
    # save via PIL if available
    try:
        from PIL import Image
        # get bits
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_=[("biSize",wt.DWORD),("biWidth",wt.LONG),("biHeight",wt.LONG),
                      ("biPlanes",wt.WORD),("biBitCount",wt.WORD),("biCompression",wt.DWORD),
                      ("biSizeImage",wt.DWORD),("biXPelsPerMeter",wt.LONG),("biYPelsPerMeter",wt.LONG),
                      ("biClrUsed",wt.DWORD),("biClrImportant",wt.DWORD)]
        bi = BITMAPINFOHEADER(); bi.biSize=ctypes.sizeof(bi); bi.biWidth=w; bi.biHeight=-h
        bi.biPlanes=1; bi.biBitCount=24; bi.biCompression=0
        buf = ctypes.create_string_buffer(w*h*3)
        gdi.GetDIBits(memdc, bmp, 0, h, buf, ctypes.byref(bi), 0)
        img = Image.frombytes("RGB",(w,h),buf.raw)
        img.save(path)
        print("saved %s (%dx%d)" % (path,w,h))
    except Exception as e:
        print("PIL save failed: %r" % e)
    gdi.DeleteObject(bmp); gdi.DeleteDC(memdc); u32.ReleaseDC(0,hdc)

def analyze_blue_buttons(path, x=720):
    """按钮高亮底：b>120 且 r<40 且 g<60。返回 x 列上的 y-band 列表 [(y0,y1,center)]。"""
    from PIL import Image
    im = Image.open(path).convert("RGB"); px = im.load()
    w,h = im.size
    bands=[]; start=None
    for y in range(h):
        r,g,b = px[x,y]
        on = (b>120 and r<45 and g<70)
        if on and start is None: start=y
        elif not on and start is not None:
            if y-start>=4: bands.append((start,y-1,(start+y-1)//2))
            start=None
    if start is not None and h-start>=4: bands.append((start,h-1,(start+h-1)//2))
    return bands

def analyze_yellow(path):
    """黄色文字：R>150,G>120,B<90。返回连通块 bbox。"""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w,h = im.size
    px = im.load()
    mask = [[False]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r,g,b = px[x,y]
            if r>140 and g>110 and b<95 and r>b+60 and g>b+40:
                mask[y][x]=True
    # 连通块 (4-邻接)
    seen=[[False]*w for _ in range(h)]
    comps=[]
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not seen[y][x]:
                stack=[(x,y)]; seen[y][x]=True
                xs=[]; ys=[]
                while stack:
                    cx,cy=stack.pop(); xs.append(cx); ys.append(cy)
                    for nx,ny in ((cx+1,cy),(cx-1,cy),(cx,cy+1),(cx,cy-1)):
                        if 0<=nx<w and 0<=ny<h and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx]=True; stack.append((nx,ny))
                if len(xs)>=6:
                    comps.append((min(xs),min(ys),max(xs),max(ys),len(xs)))
    comps.sort(key=lambda c:(c[1],c[0]))
    return comps

if __name__ == "__main__":
    base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S01-V1\EVIDENCE"
    pid = pid_of()
    if not pid: print("gamemd not running"); sys.exit(2)
    hwnd = game_hwnd(pid)
    print("pid=%d hwnd=0x%X" % (pid, hwnd or 0))
    tag = sys.argv[1] if len(sys.argv)>1 else "menu"
    path = os.path.join(base, "screen_%s.png" % tag)
    capture(hwnd, path)
    comps = analyze_yellow(path)
    bands = analyze_blue_buttons(path)
    print("yellow connected components (>=6px), %d total:" % len(comps))
    for c in comps[:60]:
        print("  bbox=(%d,%d)-(%d,%d) area=%d" % c)
    print("blue button-highlight bands at x=720: %d" % len(bands))
    for b in bands:
        print("  y=[%d,%d] center=%d" % b)
    with open(os.path.join(base,"yellow_comps_%s.txt"%tag),"w") as f:
        for c in comps: f.write("%d %d %d %d %d\n"%c)
    with open(os.path.join(base,"blue_bands_%s.txt"%tag),"w") as f:
        for b in bands: f.write("%d %d %d\n"%b)
