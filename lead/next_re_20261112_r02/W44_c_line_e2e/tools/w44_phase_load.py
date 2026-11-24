#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 4b - LIVE LOAD (K2): after K1 fully exited (residual 0),
relaunch from a cold process, GUI:LoadSavedGame -> load the save made in A2,
and confirm we are back INSIDE A2 (not a menu / loading screen / error).

NOTE: K2 deliberately does NOT re-apply the D2 [SOV1] hijack - loading a save
bypasses the campaign-menu badge entry, so this re-checks save/load under the
as-built formal pipeline state (only the v12 package installed).
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "saveload"
MARKERS = ["ECH01.MAP", "ECH02.MAP", "RA2F1", C.CSF_TEXT,
           "RA2F:942506FC", "MISSING:", "W44Q3SAVE",
           "RA2F_ECH01_2004FB14", "RA2F_ECH02_1E0DEBE8"]


def snap(pid, hproc, sink, label):
    cs = L.controls(pid)
    cnt = L.read_counters(hproc) if hproc else None
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    sink.step("screen", label=label, counters=cnt, visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"],
                             "id": c["ctrl_id"]} for c in cs])
    return cs, cnt, vis


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready",
                      elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return
        time.sleep(1.5)
    raise RuntimeError("main menu timeout")


def launch_one(sink, tag, state):
    pre = L.list_gamemd()
    sink.step("pre_launch_guard", tag=tag, gamemd_processes=pre, n=len(pre))
    if pre:
        raise RuntimeError("residual gamemd before launch: %r" % pre)
    launcher = L.launch_game(sink)
    pid = L.wait_for_pid(launcher, sink)
    state["pid"] = pid
    L.desktop_precheck(sink)
    hwnd = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60:
        hwnd = L.game_hwnd(pid)
        if hwnd:
            break
        time.sleep(1.0)
    state["hwnd"] = hwnd
    hproc = L.open_proc(pid)
    state["hproc"] = hproc
    wait_main_menu(pid, sink)
    L.force_foreground(hwnd)
    sink.step("instance_ready", tag=tag, pid=pid, hwnd=hwnd,
              rect=L.rect(hwnd) if hwnd else None,
              title=L.wtxt(hwnd) if hwnd else None)
    return pid, hwnd, hproc


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None}
    ok = False
    in_game = False
    try:
        meta_p = C.OUT / "save_meta.json"
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  save=meta, formal_pipeline_note="no D2 hijack applied in K2")
        copy = Path(meta["copy"])
        assert copy.is_file()
        sink.step("save_copy_pre", sha256=L.sha256_file(copy),
                  matches_record=(L.sha256_file(copy) == meta["sha256"]))

        pid, hwnd, hproc = launch_one(sink, "K2", state)
        snap(pid, hproc, sink, "K2_S0_main_menu")
        L.screenshot(sink, "w44_load_K2_S0_main_menu", hwnd)

        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                label="K2_click_SinglePlayer")
        L.click(pid, "GUI:LoadSavedGame", sink, wait_s=2.5,
                label="K2_click_LoadSavedGame")
        cs, cnt, vis = snap(pid, hproc, sink, "K2_load_dialog")
        L.screenshot(sink, "w44_load_K2_load_dialog", hwnd)
        for c in cs:
            if c["cls"] in ("ListBox", "ComboBox"):
                n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                sink.step("load_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                          rect=c["rect"], n_items=n)
                if n:
                    L.read_listbox(hproc, c["hwnd"], sink, "load_items")
        lb = [c for c in cs if c["cls"] == "Button" and c["visible"]
              and c["text"] in ("GUI:Load", "GUI:LoadGame")]
        sink.step("load_dialog_buttons", buttons=[c["text"] for c in lb])

        # select our save by item name (read-only listbox item names)
        selected = None
        for c in cs:
            if c["cls"] not in ("ListBox", "ComboBox"):
                continue
            n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
            for i in range(n):
                d = int(L.smt(c["hwnd"], L.LB_GETITEMDATA, i)) & 0xFFFFFFFF
                nm = L.read_utf16_ptr(hproc, d) or ""
                if "W44Q3SAVE" in nm or meta["name"].lower().split(".")[0] in nm.lower():
                    L.smt(c["hwnd"], L.LB_SETCURSEL, i)
                    selected = {"index": i, "name": nm, "hwnd": c["hwnd"]}
                    break
            if selected:
                break
        sink.step("K2_load_selected", selected=selected, target_save=meta["name"])

        if lb:
            L.click_hwnd(lb[0]["hwnd"], sink, "K2_click_GUI_Load", wait_s=4.0)

        # wait until we are back in-game
        t0 = time.monotonic()
        k2 = None
        while time.monotonic() - t0 < 90:
            c2, k2, v2 = snap(pid, hproc, sink, "K2_after_load")
            if any("OK" in (v or "") for v in v2):
                sink.step("K2_load_error_dialog", visible=v2)
                L.screenshot(sink, "w44_load_K2_error", hwnd)
                break
            if k2 and k2.get("frame", 0) > 30:
                in_game = True
                sink.step("K2_load_ingame", counters=k2, visible=v2,
                          elapsed_s=round(time.monotonic() - t0, 2))
                break
            time.sleep(1.5)
        L.screenshot(sink, "w44_load_K2_after_load", hwnd)
        m2 = L.memory_search(hproc, MARKERS, sink, "K2_loaded_memory")

        # in-game Esc menu => control presence (not a display verdict)
        L.key(L.VK_ESCAPE, sink, "K2_Esc_ingame_menu_check")
        c3, k3, v3 = snap(pid, hproc, sink, "K2_esc_menu")
        L.screenshot(sink, "w44_load_K2_esc_menu", hwnd)
        esc_want = ("GUI:ResumeMission", "GUI:SaveGame", "GUI:AbortMission",
                    "GUI:GameControls", "GUI:GameOptions", "GUI:LoadGame")
        esc_hits = [v for v in v3
                    if any(w.lower() in (v or "").lower() for w in esc_want)]

        post_sha = L.sha256_file(copy) if copy.is_file() else None
        sink.step("K2_load_observation", in_game_evidence=in_game,
                  counters=k3, esc_hits=esc_hits, esc_visible=v3,
                  save_name=meta["name"], save_sha256=meta["sha256"],
                  save_copy_sha256_after=post_sha,
                  save_copy_matches=(post_sha == meta["sha256"]),
                  markers={k: v["count"] for k, v in m2["hits"].items()})

        fn = (k3 or {}).get("scen_filename") or ""
        ok = bool(in_game and "ech02" in fn.lower()
                  and len(esc_hits) >= 3
                  and m2["hits"].get("ECH02.MAP|ascii", {}).get("count", 0) >= 1
                  and post_sha == meta["sha256"])
        sink.step("K2_result", ok=ok, in_game=in_game, scen_filename=fn,
                  esc_hits=len(esc_hits),
                  ech02_ascii=m2["hits"].get("ECH02.MAP|ascii", {}).get("count"),
                  save_copy_matches=(post_sha == meta["sha256"]))
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-5000:])
    finally:
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            if pid:
                L.close_game(pid, hwnd, sink)
        except Exception as e:
            sink.step("close_error", error=repr(e))
        try:
            C.heal(sink, label="K2_finally")
        except Exception as e:
            sink.step("heal_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  in_game=in_game, gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
