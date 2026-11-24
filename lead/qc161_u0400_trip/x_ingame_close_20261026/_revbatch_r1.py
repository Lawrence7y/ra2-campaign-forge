# _revbatch_r1.py — independent recompute of M1/M2 numbers from raw timeline rows
# Read-only reviewer script (GLM alien adjudication of D-10 six-arm batch).
import json, os, sys

ROOT = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x"
ARMS = [
    ("P0",   "20261028T084855_0001_P0_ORIG"),
    ("P0N",  "20261028T085311_0001_P0N_INJ_OFF"),
    ("P1",   "20261028T085640_0001_P1_G1B0exp"),
    ("P2",   "20261028T090813_0001_P2_G1B0def"),
    ("P3",   "20261028T091330_0001_P3_G1B1"),
    ("P3m",  "20261028T092052_0001_P3m_MENU"),
]

out = {}
for tag, d in ARMS:
    p = os.path.join(ROOT, d)
    rec = json.load(open(os.path.join(p, "_rec.json"), encoding="utf-8"))
    tl = json.load(open(os.path.join(p, "timeline.json"), encoding="utf-8"))
    rows = tl["close_rows"]
    t0 = rows[0]["t"]
    # --- M1 checks over close_rows
    waits = sorted({r["wait"] for r in rows})
    exs = sorted({r["exitstate"] for r in rows})
    codes = sorted({str(r["code"]) for r in rows})
    cro = sorted({r["code_read_ok"] for r in rows})
    ticks = sorted({r["tick"] for r in rows})
    # first row / last row sentinels
    fr, lr = rows[0], rows[-1]
    # --- M2: frame progression / stop detection
    frames = [r["frame"] for r in rows]
    # rows where frame strictly greater than previous frame
    adv_rows = [i for i in range(1, len(rows)) if frames[i] > frames[i-1]]
    last_adv = adv_rows[-1] if adv_rows else None
    # first index where frame==0 (if any), after being >0
    zero_idx = None
    seen_pos = False
    for i, f in enumerate(frames):
        if f > 0:
            seen_pos = True
        elif f == 0 and seen_pos and zero_idx is None:
            zero_idx = i
    # frame==0 tail constancy: after zero_idx, any nonzero frame?
    revival = []
    if zero_idx is not None:
        revival = [i for i in range(zero_idx, len(rows)) if frames[i] != 0]
    max_frame = max(frames)
    # hwnd/singleton recovery after first zero
    h_zidx = None
    for i, r in enumerate(rows):
        if r["hwnd"] == 0 and r["singleton"] == 0:
            h_zidx = i
            break
    h_revival = []
    if h_zidx is not None:
        h_revival = [i for i in range(h_zidx, len(rows))
                     if rows[i]["hwnd"] != 0 or rows[i]["singleton"] != 0]
    # exitstate any nonzero
    ex_nz = [i for i, r in enumerate(rows) if r["exitstate"] != 0]
    # monotonic time
    mono = all(rows[i]["t"] <= rows[i+1]["t"] for i in range(len(rows)-1))
    # --- rec cross fields
    info = {
        "trip_tag": rec.get("trip_tag"),
        "verdict": rec.get("verdict"),
        "phase": rec.get("phase"),
        "watch_s": rec.get("watch_s"),
        "closed_at_s": rec.get("closed_at_s"),
        "close_rows_n_rec": rec.get("close_rows_n"),
        "close_rows_len": len(rows),
        "rows_match": rec.get("close_rows_n") == len(rows),
        "battle_tl_n_rec": rec.get("battle_tl_n"),
        "battle_tl_len": len(tl["battle_tl"]),
        "pre5_n_rec": rec.get("pre_close_5s_n"),
        "pre5_len": len(tl["pre5"]),
        "waits": waits, "exitstates": exs, "codes": codes, "code_read_ok": cro,
        "ticks_close": ticks,
        "first_row": {k: fr.get(k) for k in ("wait","exitstate","frame","hwnd","singleton","tick","code","code_read_ok")},
        "last_row":  {k: lr.get(k) for k in ("wait","exitstate","frame","hwnd","singleton","tick","code","code_read_ok")},
        "row1":      {k: rows[1].get(k) for k in ("frame","hwnd","singleton")},
        "max_frame": max_frame,
        "n_advancing_rows": len(adv_rows),
        "last_adv_idx": last_adv,
        "last_adv_dt_s": round(rows[last_adv]["t"] - t0, 3) if last_adv is not None else None,
        "frame_zero_first_idx": zero_idx,
        "frame_zero_dt_s": round(rows[zero_idx]["t"] - t0, 3) if zero_idx is not None else None,
        "frame_revival_after_zero": revival[:10],
        "hz_pair_zero_first_idx": h_zidx,
        "hz_pair_zero_dt_s": round(rows[h_zidx]["t"] - t0, 3) if h_zidx is not None else None,
        "hz_revival": h_revival[:10],
        "exitstate_nonzero_idx": ex_nz[:10],
        "time_monotonic": mono,
        "window_span_s": round(rows[-1]["t"] - t0, 3),
        "exited": rec.get("exited"), "exit_kind": rec.get("exit_kind"),
        "final_exitcode": rec.get("final_exitcode"),
        "a8_verdict": rec.get("a8_verdict"), "carrier_deleted": rec.get("carrier_deleted"),
        "except_before": rec.get("except_before"),
        "except_at": rec.get("except_at"), "except_changed": rec.get("except_changed"),
        "post_ok": rec.get("close_delivery", {}).get("post_ok"),
        "post_err": rec.get("close_delivery", {}).get("post_err"),
        "win_pid_match": rec.get("close_delivery", {}).get("win_pid") == rec.get("gamemd_pid"),
    }
    # ticks in battle_tl / pre5 too
    tb = sorted({r["tick"] for r in tl["battle_tl"]})
    tp = sorted({r["sent"]["tick"] for r in tl["pre5"]})
    info["ticks_battle"] = tb
    info["ticks_pre5"] = tp
    # battle exitstate/frame
    info["battle_exitstates"] = sorted({r["exitstate"] for r in tl["battle_tl"]})
    info["battle_frame_first"] = tl["battle_tl"][0]["frame"]
    info["battle_frame_last"] = tl["battle_tl"][-1]["frame"]
    info["scene_before_close"] = {k: rec.get("scene_before_close", {}).get(k) for k in ("frame","hwnd","singleton","exitstate","tick")}
    # post_windows: any #32770 or nonempty after first
    pw = rec.get("post_windows", [])
    classes = []
    nonempty = []
    for i, w in enumerate(pw):
        for win in w.get("visible", []):
            classes.append(win.get("class"))
            nonempty.append((i, win.get("class"), win.get("title")))
    info["post_windows_n"] = len(pw)
    info["post_windows_classes_distinct"] = sorted(set(c for c in classes if c))
    info["post_windows_nonempty_entries"] = nonempty
    out[tag] = info
    print("==== %s ====" % tag)
    for k, v in info.items():
        print("  %-28s %s" % (k, v))

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_revbatch_r1_out.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE _revbatch_r1_out.json")
