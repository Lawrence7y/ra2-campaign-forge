#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-J 真机主脚本（单进程连续会话，全程只读 RPM + 合成键鼠）。

在 W177-I 已验证的 launch->nav->deploy->order->pickup ghost->闭环->落格 工具链上，
新增本卡核心观测：在放置瞬间高频只读采样 arg2 = [ghost+0x520] 及其标志
  [arg2+0x16BF] / +0x16BE / +0x16B7 / +0xE58 / [0xA8E9A0] / [0xA8E7AC] / [0xA8ED6B]
并对 arg2、owner(+0x21C)、PlayerHouse 全局做 RTTI，判定 arg2 语义（T4）。

调用点静态已核（EVIDENCE/callsite_arg2.txt）：
  0x43F2AE 与 0x449482 两处 call 0x47C620，this=ecx=CellClass*（GetCellAt ret 4 返回），
  4 push = GetCellAt 吃 1（ret 4）+ 0x47C620 吃 3（ret 0xc）；
  函数 prologue [esp+0x20] = 第2栈参 = arg2 = [building+0x520]（building=edi=this）。

不写内存 / 不注入 / 不改 ra2youli / 不联网。每阶段写 checkpoint JSON。
"""
import os, sys, time, ctypes, json, subprocess, struct
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD = r"D:\Project\ra2-campaign-forge\ra2youli"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J"
EVID = os.path.join(CARD, "EVIDENCE")
WDIR = os.path.join(CARD, "work")
PIDF = os.path.join(WDIR, "game.pid")
MY_PIDS = os.path.join(WDIR, "my_pids.txt")
CKPT = os.path.join(WDIR, "run_checkpoint.json")

HOVER = 0x0088095C
CAMX = 0x886FA0
CAMY = 0x886FA4
FRAME = 0xA8ED84
A8E9A0 = 0xA8E9A0
A8E7AC = 0xA8E7AC
A8ED6B = 0xA8ED6B
A_PLAYER_HOUSE = 0x00A83D4C
SAFE = (250, 2050, 250, 1300)
JX_JY = [(55.6, 25.9), (-55.6, 25.9)]  # cellX->screen, cellY->screen (W177-I/J 校准)

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
u32.SetProcessDPIAware()

class PNT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
u32.GetCursorPos.argtypes = [ctypes.POINTER(PNT)]
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_size_t]
b4 = ctypes.create_string_buffer(4)
got = ctypes.c_size_t(0)


def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None


def hcell(m):
    v = rd(m, HOVER)
    return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)


def shot(tag):
    p = os.path.join(EVID, tag + ".png")
    im = ImageGrab.grab(all_screens=False)
    im.save(p)
    return p


def ckpt(log):
    json.dump(log, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def click_synth(x, y, dwell=0.3):
    u32.SetCursorPos(int(x), int(y)); time.sleep(0.2)
    u32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.09); u32.mouse_event(4, 0, 0, 0, 0); time.sleep(dwell)


def vclick(pid, x, y, wait=0.8):
    h = game_hwnd(pid)
    ok, info = click_client(pid, x, y, "left", settle=0.5, verify=True)
    if not ok:
        force_foreground(h, 0.8)
        ok, info = click_client(pid, x, y, "left", settle=0.5, verify=True)
    print("  vclick", x, y, "ok", ok, info, flush=True)
    if not ok:
        raise RuntimeError("foreground click failed: " + info)
    time.sleep(wait)
    return ok


def key_tap(vk):
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.06); u32.keybd_event(vk, 0, 2, 0); time.sleep(0.1)


def flags_from(h, m, tag):
    """读 HouseClass* h 的四个标志字段（h 必须可读）。只读。"""
    if not h:
        return {"ptr": None}
    return {
        "ptr": hex(h),
        "b16BF": m.u8(h + 0x16BF),
        "b16BE": m.u8(h + 0x16BE),
        "b16B7": m.u8(h + 0x16B7),
        "dE58": m.u32(h + 0xE58),
    }


def globs(m):
    return {
        "frame": m.u32(FRAME),
        "A8E9A0": m.u8(A8E9A0),
        "A8E7AC": m.u32(A8E7AC),
        "A8ED6B": m.u8(A8ED6B),
        "hover": hex(rd(m, HOVER)) if rd(m, HOVER) else None,
    }


def identify_ghost_and_arg2(m, ph):
    """找 limbo NAPOWR（owner=player, o1_81=1），读 +0x520(arg2)、+0x21C(owner)，RTTI 三者。"""
    cands = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["type"] != "NAPOWR":
            continue
        if b["owner_21C"] != ph:
            continue
        a520 = m.u32(obj + 0x520)
        a21c = m.u32(obj + 0x21C)
        nm_obj, rtti_obj = D.rtti_name(m, obj)
        nm_520, rtti_520 = D.rtti_name(m, a520)
        nm_21c, rtti_21c = D.rtti_name(m, a21c)
        cands.append({
            "obj": hex(obj),
            "o1_81": b["o1_81"], "o2_74": b["o2_74"],
            "cell": [b["cell"]["cellX"], b["cell"]["cellY"]], "cell_valid": b["cell"]["valid"],
            "arg2_520": hex(a520) if a520 else None,
            "owner_21C": hex(a21c) if a21c else None,
            "arg2_eq_owner": (a520 == a21c),
            "arg2_eq_playerhouse": (a520 == ph),
            "rtti_obj": nm_obj, "rtti_obj_chain": rtti_obj,
            "rtti_520": nm_520, "rtti_520_chain": rtti_520,
            "rtti_21C": nm_21c, "rtti_21C_chain": rtti_21c,
            "flags_arg2": flags_from(a520, m, "arg2"),
            "flags_owner": flags_from(a21c, m, "owner"),
        })
    return cands


def main():
    log = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "card": "W177-J"}
    ckpt(log)
    # 0 residual
    n = int(subprocess.run(["powershell", "-NoProfile", "-Command",
                            "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],
                           capture_output=True, text=True).stdout.strip() or 0)
    if n != 0:
        print("ABORT residual", n, flush=True); log["abort"] = "residual %d" % n; ckpt(log); return 2
    det = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    p = subprocess.Popen([GAME], cwd=CWD, close_fds=True, creationflags=det)
    open(PIDF, "w").write(str(p.pid))
    with open(MY_PIDS, "a") as f:
        f.write(str(p.pid) + "\n")
    log["pid"] = p.pid
    print("launched", p.pid, flush=True); ckpt(log)

    log["boot_wait_s"] = 16
    time.sleep(16)
    hwnd = game_hwnd(p.pid)
    ff = force_foreground(hwnd, 0.8)
    log["initial_foreground"] = ff
    print("initial foreground", ff, flush=True)
    shot("j_menu_check")

    vclick(p.pid, 720, 219, 1.2)   # single player
    vclick(p.pid, 720, 303, 1.8)   # skirmish
    shot("j_sk_setup")
    vclick(p.pid, 730, 263, 0.6)   # start game
    log["nav_done"] = True
    print("nav done", flush=True); ckpt(log)

    for i in range(20):
        time.sleep(0.8)
        m = W.Mem(p.pid); fr = m.u32(FRAME); ph = P.player_house(m); m.close()
        if fr > 5 and ph:
            break
    log["ingame_frame"] = fr
    log["player_house"] = hex(ph) if ph else None
    print("ingame frame", fr, "ph", hex(ph) if ph else None, flush=True); ckpt(log)
    time.sleep(1.5)

    # deploy MCV
    click_synth(1348, 495, 0.5); key_tap(0x44); time.sleep(2.5)
    m = W.Mem(p.pid); ph = P.player_house(m)
    types = C.all_player_building_types(m, ph); m.close()
    log["after_deploy_types"] = types
    print("deploy types", types, flush=True)
    if "NACNST" not in types:
        log["abort"] = "no construction yard"; ckpt(log); shot("j_abort_noyard"); 
        json.dump(log, open(os.path.join(EVID, "j_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 3
    shot("j_ingame")

    # T1 order: locate NAPOWR icon fresh
    r = subprocess.run([sys.executable, os.path.join(WDIR, "sidebar_locate.py"),
                        os.path.join(EVID, "j_ingame.png")], cwd=WDIR, capture_output=True, text=True)
    log["sidebar_locate_stdout"] = r.stdout[-1200:]
    grid = json.load(open(os.path.join(EVID, "sidebar_grid.json"), encoding="utf-8"))
    icon = tuple(grid["chosen"]["center"])
    log["icon"] = icon
    print("icon", icon, flush=True)
    hwnd = game_hwnd(p.pid); force_foreground(hwnd, 0.5)
    m = W.Mem(p.pid); ph = P.player_house(m); pre_credits = m.u32(ph + 0x30C); m.close()
    ok, info = click_client(p.pid, icon[0], icon[1], "left", settle=0.4, verify=True)
    log["order_click"] = {"ok": ok, "info": info, "pre_credits": pre_credits}
    print("order click", ok, flush=True)
    time.sleep(0.5)
    m = W.Mem(p.pid); ph = P.player_house(m)
    post_credits = m.u32(ph + 0x30C); nap = [x for x in C.napowr_objects(m, ph) if x["is_player"]]; m.close()
    log["order_verify"] = {"post_credits": post_credits, "player_napowr": nap}
    print("credits", pre_credits, "->", post_credits, "nap", len(nap), flush=True)
    if not (post_credits < pre_credits or nap):
        log["abort"] = "order failed"; ckpt(log)
        json.dump(log, open(os.path.join(EVID, "j_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 4

    # wait build complete
    target_credits = pre_credits - 600
    for i in range(60):
        time.sleep(0.5)
        m = W.Mem(p.pid); ph = P.player_house(m); cr = m.u32(ph + 0x30C); m.close()
        if cr <= target_credits + 20:
            break
    log["credits_built"] = cr
    print("build done credits", cr, flush=True)
    time.sleep(1.0)

    # pickup ghost
    hwnd = game_hwnd(p.pid); force_foreground(hwnd, 0.5)
    ok2, info2 = click_client(p.pid, icon[0], icon[1], "left", settle=0.3, verify=True)
    log["pickup_click"] = {"ok": ok2, "info": info2}
    print("pickup", ok2, flush=True)
    time.sleep(0.4)
    shot("j_ghost_picked")

    # ---- CORE: identify ghost building + arg2 + RTTI + flags (ghost held, before click) ----
    m = W.Mem(p.pid); ph = P.player_house(m)
    ginfo = identify_ghost_and_arg2(m, ph)
    log["ghost_arg2_ident"] = {"player_house": hex(ph), "globs": globs(m),
                                "playerhouse_flags": flags_from(ph, m, "ph"), "candidates": ginfo}
    print("ghost candidates", json.dumps(ginfo, ensure_ascii=False)[:1500], flush=True)
    ckpt(log)
    m.close()

    # choose target infantry cell far from yard
    m = W.Mem(p.pid); ph = P.player_house(m)
    aitems = m.u32(P.A_ABSTRACT_ITEMS); acount = m.u32(P.A_ABSTRACT)
    yard_cell = None; inf_cells = {}
    for i in range(acount):
        q = m.u32(aitems + 4 * i)
        if not q or (q & 3):
            continue
        if m.u32(q + 0x21C) != ph:
            continue
        nm, _ = D.rtti_name(m, q)
        lx = m.u32(q + 0x9C); ly = m.u32(q + 0xA0)
        if nm and 'BuildingClass' in nm and lx and ly:
            yard_cell = (lx >> 8, ly >> 8)
        if nm and 'InfantryClass' in nm and lx and ly:
            inf_cells.setdefault((lx >> 8, ly >> 8), 0)
            inf_cells[(lx >> 8, ly >> 8)] += 1
    m.close()
    cands = []
    for (cx, cy), cnt in inf_cells.items():
        d = abs(cx - yard_cell[0]) + abs(cy - yard_cell[1]) if yard_cell else 99
        cands.append((d, cx, cy, cnt))
    cands.sort(key=lambda z: (-z[0], -z[3]))
    if not cands:
        log["abort"] = "no infantry"; ckpt(log)
        json.dump(log, open(os.path.join(EVID, "j_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 5
    _, tx, ty, cnt = cands[0]
    anchor = (tx, ty - 1)  # 实测足迹 X[hover-1..hover+1] Y[hover..hover+1]，覆盖 T.y 需 hover.y=T.y-1
    log["target"] = [tx, ty]; log["anchor"] = list(anchor)
    log["yard_cell"] = yard_cell
    log["inf_cells"] = {str(k): v for k, v in inf_cells.items()}
    print("target", (tx, ty), "anchor", anchor, "inf", cnt, flush=True)
    ckpt(log)

    # closed loop to anchor
    def clamp(x, y):
        return (max(SAFE[0], min(SAFE[1], x)), max(SAFE[2], min(SAFE[3], y)))
    cp = PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx, sy = cp.x, cp.y
    if not (250 <= sx <= 2050 and 250 <= sy <= 1300):
        sx, sy = 1400, 600
    m = W.Mem(p.pid)
    cam0 = (rd(m, CAMX), rd(m, CAMY))
    jx = list(JX_JY[0]); jy = list(JX_JY[1]); trace = []; okloop = False
    u32.SetCursorPos(int(sx), int(sy)); time.sleep(0.34)
    cur = hcell(m)
    for it in range(40):
        cx, cy = cur; ex, ey = anchor[0] - cx, anchor[1] - cy
        trace.append({"it": it, "screen": [int(sx), int(sy)], "cell": [cx, cy], "err": [ex, ey],
                      "cam": [rd(m, CAMX), rd(m, CAMY)], "frame": rd(m, FRAME)})
        if (rd(m, CAMX), rd(m, CAMY)) != cam0:
            break
        if ex == 0 and ey == 0:
            okloop = True; break
        dsx = 0.75 * (jx[0] * ex + jy[0] * ey); dsy = 0.75 * (jx[1] * ex + jy[1] * ey)
        osx, osy = sx, sy; sx, sy = clamp(sx + dsx, sy + dsy)
        if (sx, sy) == (osx, osy):
            break
        u32.SetCursorPos(int(sx), int(sy)); time.sleep(0.30)
        nxt = hcell(m)
        dsxo = sx - osx; dsyo = sy - osy; dcxo = nxt[0] - cx; dcyo = nxt[1] - cy
        if abs(dsxo) + abs(dsyo) >= 8:
            erx = dcxo - (jx[0] * dsxo + jy[0] * dsyo); ery = dcyo - (jx[1] * dsxo + jy[1] * dsyo)
            n2 = dsxo * dsxo + dsyo * dsyo
            if n2 > 0:
                jx[0] += 0.5 * erx * dsxo / n2; jx[1] += 0.5 * ery * dsxo / n2
                jy[0] += 0.5 * erx * dsyo / n2; jy[1] += 0.5 * ery * dsyo / n2
        cur = nxt
    log["closed_loop"] = {"ok": okloop, "cur": cur, "iters": len(trace),
                          "J0": {"JX": JX_JY[0], "JY": JX_JY[1]}, "trace": trace}
    print("closed loop", okloop, cur, flush=True)
    shot("j_hover_anchor")
    ckpt(log)
    if not okloop and cur != anchor:
        log["abort"] = "cannot reach anchor"
        json.dump(log, open(os.path.join(EVID, "j_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        m.close(); return 6

    # pre target chain
    base = rd(m, P.CELL_ARRAY)
    def chainf(head, maxn=16):
        nodes = []; seen = set(); q = head
        while q and len(nodes) < maxn:
            if q in seen: break
            seen.add(q); nodes.append(q); q = rd(m, q + 0x30)
        return nodes
    cellp = rd(m, base + ((ty << 9) + tx) * 4)
    hA = rd(m, cellp + 0xE4) if cellp else None
    pre_nodes = chainf(hA)
    rcache = {}
    def rtti(q):
        if q not in rcache:
            rcache[q] = D.rtti_name(m, q)[0]
        return rcache[q]
    pre_rtti = [rtti(x) for x in pre_nodes]
    log["pre_target"] = {"cell": cellp, "headA": hA, "lenA": len(pre_nodes), "rttiA": pre_rtti,
                         "nodesA": [hex(x) for x in pre_nodes]}
    print("pre target", len(pre_nodes), pre_rtti, flush=True)

    # ---- HIGH-FREQ SAMPLING: click-200ms .. click+1000ms ----
    # pick the limbo NAPOWR whose +0x520 we track as arg2
    ghost_obj = None; arg2 = None
    for c in ginfo:
        if c["o1_81"] == 1:
            ghost_obj = int(c["obj"], 16)
            arg2 = int(c["arg2_520"], 16) if c["arg2_520"] else None
            break
    if ghost_obj is None and ginfo:
        ghost_obj = int(ginfo[0]["obj"], 16)
        arg2 = int(ginfo[0]["arg2_520"], 16) if ginfo[0]["arg2_520"] else None
    log["sampling_ghost_obj"] = hex(ghost_obj) if ghost_obj else None
    log["sampling_arg2"] = hex(arg2) if arg2 else None
    print("sampling arg2", hex(arg2) if arg2 else None, flush=True)

    samples = []
    t0 = time.perf_counter()
    click_at = 0.25
    dur = 1.6
    clicked = False; click_frame = None; click_sample_idx = None
    landing = None
    while time.perf_counter() - t0 < dur:
        t = time.perf_counter() - t0
        fr = m.u32(FRAME)
        hv = rd(m, HOVER)
        ch = rd(m, base + ((ty << 9) + tx) * 4)
        hA2 = rd(m, ch + 0xE4) if ch else None
        nA = chainf(hA2)
        # arg2 flags (re-read arg2 pointer from ghost each sample in case it changes)
        a2_now = rd(m, ghost_obj + 0x520) if ghost_obj else None
        rec = {
            "t": round(t, 6), "frame": fr,
            "g_F16BF": m.u8(arg2 + 0x16BF) if arg2 else None,
            "g_F16BE": m.u8(arg2 + 0x16BE) if arg2 else None,
            "g_F16B7": m.u8(arg2 + 0x16B7) if arg2 else None,
            "g_DE58": m.u32(arg2 + 0xE58) if arg2 else None,
            "A8E9A0": m.u8(A8E9A0), "A8E7AC": m.u32(A8E7AC), "A8ED6B": m.u8(A8ED6B),
            "arg2_now": hex(a2_now) if a2_now else None,
            "headA": hex(hA2) if hA2 else None, "lenA": len(nA),
            "rttiA": [rtti(x) for x in nA],
            "hover": hex(hv) if hv else None,
            "hover_cell": [(hv & 0xFFFF) if hv else None, ((hv >> 16) & 0xFFFF) if hv else None],
            "cam": [rd(m, CAMX), rd(m, CAMY)],
            "credits": m.u32(ph + 0x30C) if ph else None,
            "ghost_o1": m.u8(ghost_obj + 0x81) if ghost_obj else None,
        }
        samples.append(rec)
        if not clicked and t >= click_at:
            click_sample_idx = len(samples) - 1
            click_frame = fr
            fb = m.u32(FRAME)
            # foreground verified click at current cursor (still hovering anchor)
            fg = u32.GetForegroundWindow()
            rec["click_fg_ok"] = (fg == hwnd)
            u32.mouse_event(2, 0, 0, 0, 0); time.sleep(0.06); u32.mouse_event(4, 0, 0, 0, 0)
            fa = m.u32(FRAME)
            ch2 = rd(m, base + ((ty << 9) + tx) * 4)
            hA3 = rd(m, ch2 + 0xE4) if ch2 else None
            nA3 = chainf(hA3); fi = m.u32(FRAME)
            rA3 = [rtti(x) for x in nA3]
            landing = {"frame_before": fb, "frame_click": fr, "frame_after": fa, "frame_imm": fi,
                       "frames_elapsed": fi - fb, "headA": hex(hA3) if hA3 else None,
                       "lenA": len(nA3), "rttiA": rA3, "nodesA": [hex(x) for x in nA3],
                       "has_building": any(v and 'BuildingClass' in v for v in rA3),
                       "has_infantry": any(v and 'InfantryClass' in v for v in rA3),
                       "ghost_o1_after": m.u8(ghost_obj + 0x81) if ghost_obj else None,
                       "flags_at_click": {
                           "F16BF": m.u8(arg2 + 0x16BF) if arg2 else None,
                           "F16BE": m.u8(arg2 + 0x16BE) if arg2 else None,
                           "F16B7": m.u8(arg2 + 0x16B7) if arg2 else None,
                           "DE58": m.u32(arg2 + 0xE58) if arg2 else None,
                           "A8E9A0": m.u8(A8E9A0), "A8E7AC": m.u32(A8E7AC), "A8ED6B": m.u8(A8ED6B),
                       }}
            landing["main_ok"] = len(nA3) >= 2 and landing["has_building"]
            clicked = True
            shot("j_after_click")

    dur_actual = samples[-1]["t"]
    jl = os.path.join(EVID, "j_flag_samples.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    frames = sorted(set(s["frame"] for s in samples if s["frame"] is not None))
    log["sampling"] = {
        "file": jl, "n_samples": len(samples), "duration_s": round(dur_actual, 4),
        "rate_per_s": round(len(samples) / dur_actual, 1),
        "distinct_frames": len(frames), "frame_min": frames[0] if frames else None,
        "frame_max": frames[-1] if frames else None, "click_sample_index": click_sample_idx,
        "click_frame": click_frame, "covers_click_frame": bool(click_frame in frames),
        "rtti_cache": {hex(k): v for k, v in rcache.items()},
    }
    log["landing"] = landing
    # distinct flag values observed
    for key in ["g_F16BF", "g_F16BE", "g_F16B7", "g_DE58", "A8E9A0", "A8E7AC", "A8ED6B"]:
        vals = sorted(set(s[key] for s in samples if s[key] is not None))
        log["sampling"]["distinct_" + key] = vals[:20]
    print("SAMPLING", json.dumps({k: log["sampling"][k] for k in
          ["n_samples", "rate_per_s", "distinct_frames", "frame_min", "frame_max",
           "distinct_g_F16BF", "distinct_A8E9A0", "click_frame", "covers_click_frame"]},
          ensure_ascii=False), flush=True)
    print("LANDING", json.dumps(landing, ensure_ascii=False), flush=True)

    log["credits_end"] = m.u32(ph + 0x30C) if ph else None
    log["final_globs"] = globs(m)
    m.close()
    ckpt(log)
    json.dump(log, open(os.path.join(EVID, "j_run.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
