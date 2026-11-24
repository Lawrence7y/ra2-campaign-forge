#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-I 真机驱动：launch / shot / state / click / key。
全部只读内存 + 合成输入；只启动/关闭本卡自己的 gamemd。截图写入本卡 EVIDENCE。"""
import os, sys, time, ctypes, json, subprocess, argparse
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
from w177_click import click_client, game_hwnd, force_foreground

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD = r"D:\Project\ra2-campaign-forge\ra2youli"
HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)
EVID = os.path.join(CARD, "EVIDENCE")
PIDF = os.path.join(HERE, "game.pid")
MY_PIDS = os.path.join(HERE, "my_pids.txt")
u32 = ctypes.windll.user32
try:
    u32.SetProcessDPIAware()
except Exception:
    pass


def residual_count():
    return int(subprocess.run(["powershell", "-NoProfile", "-Command",
        "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True).stdout.strip() or "0")


def nonblack_ratio(img):
    """自检抓图：非黑像素占比（每 8px 采样）。"""
    im = img.convert("RGB")
    w, h = im.size
    px = im.load()
    tot = hit = 0
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            r, g, b = px[x, y]
            tot += 1
            if r + g + b > 24:
                hit += 1
    return hit / tot if tot else 0.0


def state(tag=None):
    pid = W.pid_of()
    rec = {"tag": tag, "pid": pid, "gamemd_count": residual_count()}
    if pid:
        m = W.Mem(pid)
        ph = P.player_house(m)
        rec.update({
            "mode": m.u32(W.A_MODE),
            "frame": m.u32(W.A_FRAME),
            "objects": m.u32(W.A_ABSTRACT),
            "playerHouse": hex(ph) if ph else None,
            "credits_30C": m.u32(ph + 0x30C) if ph else None,
            "building_array_count": W.building_array(m)[1],
            "cam": [m.u32(0x886FA0), m.u32(0x886FA4)],
        })
        m.close()
    return rec


def shot(tag, full=True, bbox=None):
    img = ImageGrab.grab(bbox=(tuple(int(x) for x in bbox.split(",")) if bbox else None),
                         all_screens=False)
    nb = nonblack_ratio(img)
    path = os.path.join(EVID, tag + ".png")
    img.save(path)
    return {"path": path, "size": list(img.size), "nonblack_ratio": round(nb, 4)}


def cmd_launch(args):
    if residual_count() != 0:
        print("ABORT residual gamemd count=%d" % residual_count()); return 2
    det = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen([GAME], cwd=CWD, close_fds=True, creationflags=det)
    open(PIDF, "w").write(str(p.pid))
    with open(MY_PIDS, "a") as f:
        f.write(str(p.pid) + "\n")
    print("launched pid=%d (DETACHED)" % p.pid, flush=True)
    for i in range(12):
        time.sleep(1.0)
        s = state("boot%d" % i)
        print("  t+%ds pid=%s mode=%s frame=%s" % (i + 1, s["pid"], s["mode"], s["frame"]), flush=True)
        if s["pid"] and s["frame"] and s["frame"] > 0:
            break
    return 0


def cmd_state(args):
    s = state(args.tag)
    print(json.dumps(s, ensure_ascii=False), flush=True)
    if args.json:
        json.dump(s, open(os.path.join(EVID, (args.tag or "state") + "_state.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


def cmd_shot(args):
    r = shot(args.tag, full=not args.bbox, bbox=args.bbox)
    print(json.dumps(r, ensure_ascii=False), flush=True)
    s = state(args.tag + "_shot")
    print(json.dumps(s, ensure_ascii=False), flush=True)
    return 0


def cmd_click(args):
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    hwnd = game_hwnd(pid)
    fg = force_foreground(hwnd, 0.5) if hwnd else False
    print("foreground_ready=%s hwnd=%s" % (fg, hex(hwnd) if hwnd else None), flush=True)
    if not fg:
        print("ABORT foreground failed"); return 3
    ok, info = click_client(pid, args.x, args.y, args.button, settle=0.4, verify=True)
    print("click ok=%s %s" % (ok, info), flush=True)
    return 0 if ok else 3


def cmd_nav(args):
    """一键导航：单点->遭遇战->开始游戏（坐标来自前卡已验证的物理坐标）。"""
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    steps = [("singleplayer", 720, 219, 1.2),
             ("skirmish", 720, 304, 1.5)]
    for name, x, y, wait in steps:
        hwnd = game_hwnd(pid)
        fg = force_foreground(hwnd, 0.4) if hwnd else False
        ok, info = click_client(pid, x, y, "left", settle=0.4, verify=True)
        print("nav %s fg=%s ok=%s %s" % (name, fg, ok, info), flush=True)
        time.sleep(wait)
        shot("nav_" + name)
    print(json.dumps(state("nav_done"), ensure_ascii=False), flush=True)
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("launch")
    sp = sub.add_parser("shot"); sp.add_argument("tag"); sp.add_argument("--bbox", default=None)
    sp = sub.add_parser("state"); sp.add_argument("--tag", default=None); sp.add_argument("--json", action="store_true")
    sp = sub.add_parser("click"); sp.add_argument("x", type=int); sp.add_argument("y", type=int)
    sp.add_argument("--button", choices=["left", "right"], default="left")
    sub.add_parser("nav")
    a = ap.parse_args()
    return {"launch": cmd_launch, "shot": cmd_shot, "state": cmd_state,
            "click": cmd_click, "nav": cmd_nav}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
