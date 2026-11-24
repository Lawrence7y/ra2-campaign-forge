#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L2 experiment — NON-pixel primary criterion.

Primary criterion (per card): after placement, read the target/landing cell's
+0xE4/+0xE8 object chain and lenA. A newly added BuildingClass node => placed & occupies cell.
No pixel is used for any verdict.

Ghost-in-hand is detected purely from memory: a player NAPOWR BuildingClass with
o1(+0x81)==1 and Location cell == (0,0), valid==False.

The actual landing cell is the newly placed object's Location (obj+0x9C/0xA0 >> 8),
i.e. ground truth from memory; hover offset (hover-Location) is calibrated from A trials
and used only to AIM the cursor so B/C land on the intended unit cell.

Only closes the pid it launches. Read-only RPM + synthesized input. No mem write/inject/net.
"""
import os, sys, time, ctypes, json, struct, subprocess
from collections import Counter
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
CWD  = r"D:\Project\ra2-campaign-forge\ra2youli"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L2"
EVID = os.path.join(CARD, "EVIDENCE"); WDIR = os.path.join(CARD, "work")
RESULT = os.path.join(EVID, "l2_result.json")
TSV = os.path.join(EVID, "trials.tsv")
PIDF = os.path.join(WDIR, "game.pid")
MY_PIDS = os.path.join(WDIR, "my_pids.txt")

HOVER = 0x88095C; CAMX = 0x886FA0; CAMY = 0x886FA4; FRAME = 0xA8ED84
SAFE = (500, 2020, 400, 1090)          # interior: avoid edge auto-scroll
JX = (55.6, 25.9); JY = (-55.6, 25.9)  # px per +1 cellX / +1 cellY (LIVE-L1 PROBE_TABLE)
ICON = (2336, 472)                      # NAPOWR build tile (LIVE-L1 verified, 2560x1440)

u32 = ctypes.windll.user32; k32 = ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
class PNT(ctypes.Structure): _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
u32.GetCursorPos.argtypes = [ctypes.POINTER(PNT)]; u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_size_t]
b4 = ctypes.create_string_buffer(4); got = ctypes.c_size_t(0)
pid = None

def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None

def hcell(m):
    v = rd(m, HOVER); return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)

def save(res):
    json.dump(res, open(RESULT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def key_tap(vk):
    u32.keybd_event(vk, 0, 0, 0); time.sleep(0.08); u32.keybd_event(vk, 0, 2, 0); time.sleep(0.12)

def clamp(x, y):
    return (max(SAFE[0], min(SAFE[1], x)), max(SAFE[2], min(SAFE[3], y)))

# ---- memory: chains & buildings ----
def cell_ptr(m, cx, cy):
    base = m.u32(P.CELL_ARRAY); idx = (cy << 9) + cx
    if not base or idx < 0 or idx >= 0x40000: return None
    c = m.u32(base + idx * 4)
    return c if (c and c != P.INVALID_CELL) else None

def chain_at(m, cx, cy):
    """Main-criterion readout: cell +0xE4/+0xE8 chains for a map cell (x,y)."""
    c = cell_ptr(m, cx, cy)
    if not c: return {"valid": False, "cell": None, "lenA": 0, "lenB": 0,
                      "rttiA": [], "rttiB": [], "nodesA": [], "nodesB": []}
    out = {"valid": True, "cell": hex(c),
           "selfcx": m.u16(c + P.CELL_CX), "selfcy": m.u16(c + P.CELL_CY)}
    for tag, off in (("A", P.CELL_E4), ("B", P.CELL_E8)):
        head = m.u32(c + off); nodes = []; seen = set(); p = head
        while p and len(nodes) < 32 and p not in seen:
            seen.add(p); nodes.append(p); p = m.u32(p + P.O_NEXT)
        out["head" + tag] = hex(head) if head else None
        out["len" + tag] = len(nodes)
        out["nodes" + tag] = [hex(x) for x in nodes]
        out["rtti" + tag] = [(D.rtti_name(m, x)[0] or "?") for x in nodes]
    return out

def napowr(m, ph):
    out = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["owner_21C"] != ph or b["type"] != "NAPOWR": continue
        c = b["cell"]
        out.append({"obj": hex(obj), "addr": obj, "o1": b["o1_81"], "o2": b["o2_74"],
                    "cell": [c["cellX"], c["cellY"]], "valid": c["valid"],
                    "lenA": b["chains"]["lenA"]})
    return out

def ghost_in_hand(m, ph):
    g = [o for o in napowr(m, ph) if o["o1"] == 1 and o["cell"] == [0, 0] and not o["valid"]]
    return bool(g)

def placed_set(m, ph):
    return [o for o in napowr(m, ph) if o["o1"] == 0 and o["valid"]]

def scan_units(m, ph):
    ai = m.u32(P.A_ABSTRACT_ITEMS); ac = m.u32(P.A_ABSTRACT)
    inf = Counter(); veh = Counter(); det = {}
    for i in range(ac):
        q = m.u32(ai + 4 * i)
        if not q or (q & 3) or m.u32(q + P.O_OWNER) != ph: continue
        nm, _ = D.rtti_name(m, q)
        if not nm: continue
        lx = m.u32(q + P.O_LOCX); ly = m.u32(q + P.O_LOCY)
        if lx is None or ly is None: continue
        c = ((lx >> 8), (ly >> 8))
        if 'InfantryClass' in nm:
            inf[c] += 1; det.setdefault(c, []).append("inf")
        elif 'UnitClass' in nm:
            veh[c] += 1; det.setdefault(c, []).append("veh")
    return inf, veh, det

def cell_chain_kind(m, cx, cy):
    """0=no objects, 'inf'/'veh'/'bld' by dominant RTTI, else 'mix'."""
    ch = chain_at(m, cx, cy)
    kinds = []
    for t in ("A", "B"):
        for r in ch.get("rtti" + t, []):
            if "InfantryClass" in r: kinds.append("inf")
            elif "UnitClass" in r: kinds.append("veh")
            elif "BuildingClass" in r: kinds.append("bld")
    if not kinds: return "empty", ch
    k = Counter(kinds)
    return (k.most_common(1)[0][0] if len(k) == 1 else "mix"), ch

# ---- input / aim ----
def hcell_now():
    return hcell(_mm) if _mm else (None, None)

_mm = None  # module-level Mem used by aim

def aim_cell(target, tag=None, maxit=34, settle=0.16):
    """Iteratively move cursor until hover(0x88095C)==target. Returns (ok,cur,screen,trace)."""
    cp = PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx, sy = float(cp.x), float(cp.y)
    if not (SAFE[0] <= sx <= SAFE[1] and SAFE[2] <= sy <= SAFE[3]): sx, sy = 1400.0, 700.0
    cam0 = (rd(_mm, CAMX), rd(_mm, CAMY)); trace = []; ok = False; cur = (None, None)
    u32.SetCursorPos(int(sx), int(sy)); time.sleep(0.25); cur = hcell(_mm)
    for it in range(maxit):
        if cur[0] is None:
            time.sleep(0.2); cur = hcell(_mm); continue
        ex, ey = target[0] - cur[0], target[1] - cur[1]
        trace.append({"it": it, "screen": [round(sx, 1), round(sy, 1)], "cell": list(cur),
                      "err": [ex, ey], "cam": [rd(_mm, CAMX), rd(_mm, CAMY)], "frame": rd(_mm, FRAME)})
        if (rd(_mm, CAMX), rd(_mm, CAMY)) != cam0: break
        if ex == 0 and ey == 0: ok = True; break
        dsx = 0.8 * (JX[0] * ex + JY[0] * ey)
        dsy = 0.8 * (JX[1] * ex + JY[1] * ey)
        ox, oy = sx, sy; sx, sy = clamp(sx + dsx, sy + dsy)
        if (round(sx), round(sy)) == (round(ox), round(oy)): break
        u32.SetCursorPos(int(sx), int(sy)); time.sleep(settle)
        cur = hcell(_mm)
    if tag:
        json.dump({"target": list(target), "ok": ok, "cur": list(cur) if cur[0] is not None else None,
                   "iters": len(trace), "trace": trace},
                  open(os.path.join(EVID, tag + "_aim.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    return ok, cur, (sx, sy), trace

def click_here(dwell=0.6):
    fb = rd(_mm, FRAME)
    u32.mouse_event(0x0002, 0, 0, 0, 0); time.sleep(0.07)
    u32.mouse_event(0x0004, 0, 0, 0, 0); time.sleep(dwell)
    fa = rd(_mm, FRAME)
    return fb, fa

# ---- ghost acquisition (memory-confirmed) ----
def ensure_ghost(ph, res, tag):
    global _mm
    if ghost_in_hand(_mm, ph): return True
    for attempt in range(6):
        force_foreground(game_hwnd(pid), 0.35)
        pre = rd(_mm, ph + 0x30C)
        ok, _ = click_client(pid, ICON[0], ICON[1], "left", settle=0.35, verify=True)
        time.sleep(0.55)
        if ghost_in_hand(_mm, ph):
            res.setdefault("ghost", []).append({"tag": tag, "attempt": attempt, "note": "pickup", "pre": pre})
            save(res); return True
        post = rd(_mm, ph + 0x30C)
        if post is not None and pre is not None and post < pre - 5:
            # order placed; wait for build completion then pick up
            for _ in range(90):
                time.sleep(0.3)
                cr = rd(_mm, ph + 0x30C)
                if cr is not None and cr <= pre - 560: break
            time.sleep(0.6)
            force_foreground(game_hwnd(pid), 0.35)
            click_client(pid, ICON[0], ICON[1], "left", settle=0.35, verify=True)
            time.sleep(0.5)
            res.setdefault("ghost", []).append({"tag": tag, "attempt": attempt,
                                                "note": "order+build+pickup", "pre": pre, "post": post})
        else:
            res.setdefault("ghost", []).append({"tag": tag, "attempt": attempt,
                                                "note": "icon click", "pre": pre, "post": post})
        save(res)
        if ghost_in_hand(_mm, ph): return True
    res["ghost_fail"] = {"tag": tag, "napowr": napowr(_mm, ph), "credit": rd(_mm, ph + 0x30C)}
    save(res); return False

# ---------------- main ----------------
res = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "card": "LIVE-L2", "stage": "start",
       "criterion": "read landing-cell +0xE4/+0xE8 chain after click; new BuildingClass => placed"}
save(res)
n = int(subprocess.run(["powershell", "-NoProfile", "-Command",
                        "@(Get-Process gamemd -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip() or 0)
if n != 0:
    res["abort"] = "residual %d" % n; save(res); print("ABORT residual", n); sys.exit(2)
det = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
p = subprocess.Popen([GAME], cwd=CWD, close_fds=True, creationflags=det)
open(PIDF, "w").write(str(p.pid))
with open(MY_PIDS, "a") as f: f.write(time.strftime("%Y-%m-%dT%H:%M:%S") + " pid=" + str(p.pid) + "\n")
pid = p.pid; res["pid"] = pid; save(res); print("launched", pid, flush=True)
time.sleep(18)
hwnd = game_hwnd(pid)
try:
    u32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    u32.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0, 0x0002 | 0x0001)
except Exception: pass
res["fg"] = force_foreground(hwnd, 0.8); save(res)
for name, x, y, w in [("single", 720, 219, 1.4), ("skirmish", 720, 303, 2.0)]:
    force_foreground(game_hwnd(pid), 0.4)
    ok, _ = click_client(pid, x, y, "left", settle=0.4, verify=True)
    res["nav_" + name] = ok; save(res)
    if not ok: res["abort"] = "nav " + name; save(res); sys.exit(3)
    time.sleep(w)
force_foreground(game_hwnd(pid), 0.4)
ok, _ = click_client(pid, 730, 263, "left", settle=0.4, verify=True)
res["nav_start"] = ok; save(res)
if not ok: res["abort"] = "nav start"; save(res); sys.exit(4)
fr = 0; ph = None
for _ in range(30):
    time.sleep(0.8)
    m = W.Mem(pid); fr = m.u32(FRAME); ph = P.player_house(m); m.close()
    if fr > 5 and ph: break
res["ingame"] = {"frame": fr, "ph": hex(ph) if ph else None}; save(res)
if not (fr > 5 and ph): res["abort"] = "no ingame"; save(res); sys.exit(5)
time.sleep(1.0)
# deploy MCV (reuse LIVE-L1 robust retry)
force_foreground(game_hwnd(pid), 0.5)
m = W.Mem(pid); pts = C.all_player_building_types(m, ph); m.close()
if "NACNST" not in pts:
    m = W.Mem(pid); ai = m.u32(P.A_ABSTRACT_ITEMS); ac = m.u32(P.A_ABSTRACT); mcv = None
    for i in range(ac):
        q = m.u32(ai + 4 * i)
        if not q or (q & 3) or m.u32(q + P.O_OWNER) != ph: continue
        nm, _ = D.rtti_name(m, q)
        if nm and 'UnitClass' in nm:
            lx = m.u32(q + P.O_LOCX); ly = m.u32(q + P.O_LOCY)
            if lx and ly: mcv = (lx >> 8, ly >> 8); break
    m.close(); res["mcv"] = mcv; save(res)
    _mm = W.Mem(pid)
    if mcv:
        a, cur, s, _ = aim_cell(mcv, "l2_mcv"); sx, sy = s
    else: sx, sy = 1400, 700
    _mm.close(); _mm = None
    def do_deploy(dx, dy):
        force_foreground(game_hwnd(pid), 0.6)
        click_client(pid, int(sx + dx), int(sy + dy), "left", settle=0.4, verify=True)
        if u32.GetForegroundWindow() == game_hwnd(pid): key_tap(0x44)
        else: force_foreground(game_hwnd(pid), 0.4); key_tap(0x44)
        time.sleep(2.2)
        mm = W.Mem(pid); p2 = C.all_player_building_types(mm, ph); mm.close(); return p2
    pts = do_deploy(0, 0)
    for doff in [(28, 13), (-28, -13), (56, 28), (-56, -28), (0, 30), (0, -30)]:
        if "NACNST" in pts: break
        pts = do_deploy(*doff)
    res["post_deploy"] = pts; save(res)
    if "NACNST" not in pts: res["abort"] = "no yard"; save(res); sys.exit(6)
res["stage"] = "ingame"; save(res)

# open persistent Mem for trials
_mm = W.Mem(pid)
ph = P.player_house(_mm)
res["credit_start"] = rd(_mm, ph + 0x30C); save(res)

# ---- discover on-screen empty cells to serve as A anchors ----
def reachable(cells, want):
    good = []
    for c in cells:
        # compute required screen pos from an approximate linearization around (1400,700) hover anchor
        ok, cur, s, _ = aim_cell(c)
        if ok and cur == c: good.append((c, s))
        if len(good) >= want: break
    return good

# Build a hover->screen calibration anchor: current cursor center
inf1, veh1, det1 = scan_units(_mm, ph); time.sleep(1.2)
inf2, veh2, det2 = scan_units(_mm, ph)
inf_st = {k: v for k, v in inf1.items() if inf2.get(k) == v and v >= 1}
veh_st = {k: v for k, v in veh1.items() if veh2.get(k) == v and v >= 1}
occ = set(inf_st) | set(veh_st)
# base / buildings occupied
for i, o in P.enumerate_buildings(_mm)[2]:
    b = P.one_building(_mm, i, o)
    if b["cell"].get("valid"): occ.add((b["cell"]["cellX"], b["cell"]["cellY"]))
# candidate empty cells near map center (visible region); wide scan
empty_cands = []
for cy in range(48, 76):
    for cx in range(92, 128):
        if (cx, cy) in occ: continue
        if not cell_ptr(_mm, cx, cy): continue
        empty_cands.append((cx, cy))
# prioritize cells closest to screen center via quick aim sampling of a subset
center_cell = None
u32.SetCursorPos(1400, 700); time.sleep(0.3); center_cell = hcell(_mm)
res["center_cell"] = list(center_cell) if center_cell[0] is not None else None
empty_cands.sort(key=lambda c: (abs(c[0] - (center_cell[0] or 106)) + abs(c[1] - (center_cell[1] or 62))))
empty_good = reachable(empty_cands[:60], 8)
res["targets"] = {
    "center_cell": list(center_cell) if center_cell[0] is not None else None,
    "inf_st": {str(k): v for k, v in inf_st.items()},
    "veh_st": {str(k): v for k, v in veh_st.items()},
    "empty_good": [[list(c), [round(z, 1) for z in s]] for c, s in empty_good],
}
save(res)
print("center", center_cell, "inf", len(inf_st), "veh", len(veh_st), "empty_good", len(empty_good), flush=True)

offset = None  # (dx,dy) hover - landing, calibrated from A successes

def run_trial(group, idx, want_land):
    """want_land = cell where we want building to land (A: empty cell; B: inf cell; C: veh cell)."""
    global offset
    tag = "l2_%s_%02d" % (group, idx + 1)
    rec = {"group": group, "idx": idx + 1, "want_land": list(want_land)}
    pre_placed = placed_set(_mm, ph)
    pre_addrs = {o["addr"] for o in pre_placed}
    rec["chain_before"] = chain_at(_mm, *want_land)
    rec["kind_before"], _ = cell_chain_kind(_mm, *want_land)
    rec["credit_before"] = rd(_mm, ph + 0x30C)
    if not ensure_ghost(ph, res, tag):
        rec.update(success=False, verdict="no_ghost", note="could not obtain ghost"); save(res); return rec
    # aim hover so landing == want_land: hover = want_land + offset
    hover_target = (want_land[0] + (offset[0] if offset else 1),
                    want_land[1] + (offset[1] if offset else 0))
    rec["hover_target"] = list(hover_target)
    ok, cur, screen, trace = aim_cell(hover_target, tag)
    rec["aim_ok"] = ok; rec["aim_cur"] = list(cur) if cur[0] is not None else None
    rec["aim_iters"] = len(trace); rec["screen"] = [round(z, 1) for z in screen]
    rec["hover_click"] = list(hcell(_mm))
    fb, fa = click_here(dwell=0.7)
    time.sleep(0.5)
    rec["frame_before"] = fb; rec["frame_after"] = fa
    post_placed = placed_set(_mm, ph)
    new = [o for o in post_placed if o["addr"] not in pre_addrs]
    rec["new_buildings"] = new
    rec["napowr_after"] = napowr(_mm, ph)
    rec["credit_after"] = rd(_mm, ph + 0x30C)
    rec["hover_after_click"] = list(hcell(_mm))
    placed_ok = len(new) > 0
    landing = new[0]["cell"] if new else None
    rec["landing_cell"] = landing
    # MAIN CRITERION: chain at landing cell; new BuildingClass node with new object's addr
    if landing:
        ch = chain_at(_mm, *landing)
        rec["chain_at_landing"] = ch
        nodes = set(ch.get("nodesA", []) + ch.get("nodesB", []))
        rttis = ch.get("rttiA", []) + ch.get("rttiB", [])
        rec["new_bld_in_chain"] = any(new[0]["obj"] in ch.get("nodesA", []) or
                                      new[0]["obj"] in ch.get("nodesB", []) for _ in [0])
        rec["has_buildingclass"] = any("BuildingClass" in r for r in rttis)
    else:
        rec["chain_at_landing"] = chain_at(_mm, *want_land)
        rec["new_bld_in_chain"] = False; rec["has_buildingclass"] = False
    # verdict fields
    rec["placed"] = placed_ok
    rec["occupies_want"] = (landing == list(want_land))
    rec["success"] = bool(placed_ok and rec["has_buildingclass"])  # main criterion
    if group == "A":
        rec["verdict"] = "A_success" if rec["success"] else "A_fail"
        # calibrate offset
        if rec["success"] and landing:
            hc = rec["hover_click"]
            if hc[0] is not None:
                off = (hc[0] - landing[0], hc[1] - landing[1])
                rec["calibrated_offset"] = list(off)
                if offset is None: offset = off
    elif group == "B":
        rec["verdict"] = ("B_overlap_allowed" if (rec["success"] and rec["occupies_want"])
                          else ("B_rejected" if not placed_ok else "B_other"))
    else:
        rec["verdict"] = ("C_overlap_allowed" if (rec["success"] and rec["occupies_want"])
                          else ("C_rejected" if not placed_ok else "C_other"))
    save(res)
    return rec

# ---- A group start gate ----
res["stage"] = "A"; save(res)
A_recs = []
for i, (c, s) in enumerate(empty_good[:6]):
    r = run_trial("A", i, c); A_recs.append(r)
    res.setdefault("trials", []).append(r); save(res)
    print("A", i + 1, "success", r["success"], "land", r["landing_cell"], "aim", r["aim_ok"], flush=True)
A_succ = sum(1 for r in A_recs if r["success"])
res["A_gate"] = {"n": len(A_recs), "success": A_succ, "fail": len(A_recs) - A_succ,
                 "pass": A_succ > len(A_recs) / 2 if A_recs else False, "offset": list(offset) if offset else None}
save(res)
print("A_gate", res["A_gate"], flush=True)
if not res["A_gate"]["pass"]:
    res["stage"] = "STOP_A_gate_fail"; save(res)
    print("STOP: A gate failed", flush=True)
else:
    # ---- B/C interleaved ----
    res["stage"] = "BC"; save(res)
    Bc = sorted(inf_st.keys()); Cc = sorted(veh_st.keys())
    # choose on-screen unit cells: verify reachable aiming (hover target = cell + offset)
    def on_screen(cell):
        ht = (cell[0] + (offset[0] if offset else 1), cell[1] + (offset[1] if offset else 0))
        ok, cur, s, _ = aim_cell(ht)
        return ok
    Bc = [c for c in Bc if on_screen(c)][:5]
    Cc = [c for c in Cc if on_screen(c)][:5]
    res["BC_targets"] = {"B": [list(c) for c in Bc], "C": [list(c) for c in Cc]}; save(res)
    print("BC targets B", Bc, "C", Cc, flush=True)
    for i in range(5):
        if i < len(Bc):
            r = run_trial("B", i, Bc[i]); res.setdefault("trials", []).append(r); save(res)
            print("B", i + 1, r["verdict"], "land", r["landing_cell"], "want", Bc[i], flush=True)
        if i < len(Cc):
            r = run_trial("C", i, Cc[i]); res.setdefault("trials", []).append(r); save(res)
            print("C", i + 1, r["verdict"], "land", r["landing_cell"], "want", Cc[i], flush=True)
    res["stage"] = "done"; save(res)

# TSV
with open(TSV, "w", encoding="utf-8") as f:
    f.write("group\tidx\twant_land\thover_click\tlanding\tplaced\toccupies_want\tlenA_land\tlenB_land\thas_buildingclass\tverdict\taim_ok\n")
    for r in res.get("trials", []):
        ch = r.get("chain_at_landing", {})
        f.write("\t".join([r["group"], str(r["idx"]), str(r.get("want_land")), str(r.get("hover_click")),
            str(r.get("landing_cell")), str(r.get("placed")), str(r.get("occupies_want")),
            str(ch.get("lenA")), str(ch.get("lenB")), str(r.get("has_buildingclass")),
            str(r.get("verdict")), str(r.get("aim_ok"))]) + "\n")
print("DONE", flush=True)
