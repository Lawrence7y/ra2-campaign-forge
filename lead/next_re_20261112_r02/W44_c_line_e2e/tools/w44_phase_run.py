#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 4a - LIVE RUN (K1): A1 -> victory -> GUI:Continue -> A2,
then in-game SaveGame, then full process exit with residual 0.

Also judges the CSF "campaign menu description area" question on the
GUI:CampaignMenu screen with FULL screenshots + enlarged crops (never control
text as the display evidence), plus read-only RPM markers.

Hard discipline: WMI launch, single instance lock already held, no injection /
no writes to game memory / no exe edits. All observations are window/control
enumeration, read-only RPM, elapsed timers and passive screenshots.
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

TAG = "run"
BATTLE = C.GAME / "BATTLEMD.INI"
BATTLE_ORIG = C.OUT / "BATTLEMD.INI.asbuilt"
BATTLE_D2 = C.OUT / "BATTLEMD.INI.D2_sov1_ech01"
ECH01 = C.GAME / "ECH01.MAP"
ECH02 = C.GAME / "ECH02.MAP"
MAPSEL = C.GAME / "MAPSELMD.INI"
CSF = C.GAME / "ra2md.csf"
ASBUILT = ("ECH01.MAP", "ECH02.MAP", "MAPSELMD.INI", "ra2md.csf",
           "BATTLEMD98.INI", "BATTLEMD.INI")

MARKERS = ["ECH01.MAP", "ECH02.MAP", "RA2F1",
           "RA2F_ECH01_2004FB14", "RA2F_ECH02_1E0DEBE8",
           C.CSF_TEXT, "RA2F:942506FC", "MISSING:", "DESC:SOV1"]
CSF_NEEDLES = [C.CSF_TEXT, "RA2F:942506FC", "MISSING:", "DESC:SOV1",
               "GUI:SinglePlayer", "ECH01.MAP", "ECH02.MAP"]


def crop(sink, src_label, box, scale, out_label):
    """Enlarge a region of an already-captured screenshot (pure pixel evidence)."""
    from PIL import Image
    p = L.OUT / ("screen_%s.png" % src_label)
    img = Image.open(p).convert("RGB")
    c = img.crop(box)
    c = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
    q = L.OUT / ("crop_%s.png" % out_label)
    c.save(q)
    sink.step("crop", src=src_label, box=list(box), scale=scale,
              path=str(q), size=[c.width, c.height])
    return q


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
    # step-0 desktop gate MUST run within 30 s of WMI launch
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


def poll_controls(pid, hproc, sink, label, timeout_s, want_any, interval=1.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        cs, cnt, vis = snap(pid, hproc, sink, label)
        hit = [w for w in want_any
               if any(w.lower() in (v or "").lower() for v in vis)]
        if hit:
            sink.step("poll_hit", label=label, hits=hit,
                      elapsed_s=round(time.monotonic() - t0, 2))
            return True, cs, cnt, vis
        time.sleep(interval)
    sink.step("poll_timeout", label=label, timeout_s=timeout_s, wanted=want_any)
    return False, None, None, []


def do_save(pid, hproc, hwnd, sink):
    """Esc -> GUI:SaveGame -> name -> GUI:Save; returns save metadata."""
    L.key(L.VK_ESCAPE, sink, "K1_Esc_open_ingame_menu")
    cs, cnt, vis = snap(pid, hproc, sink, "K1_esc_menu")
    L.screenshot(sink, "w44_run_K1_esc_menu", hwnd)
    esc_want = ("GUI:ResumeMission", "GUI:SaveGame", "GUI:AbortMission",
                "GUI:GameControls", "GUI:GameOptions", "GUI:LoadGame")
    sink.step("K1_esc_menu_controls",
              hits=[v for v in vis if any(w.lower() in (v or "").lower()
                                         for w in esc_want)])
    before = L.save_inventory(sink, "K1_before_save")
    L.click(pid, "GUI:SaveGame", sink, wait_s=2.0, label="K1_click_SaveGame")
    cs, cnt, vis = snap(pid, hproc, sink, "K1_save_dialog")
    L.screenshot(sink, "w44_run_K1_save_dialog", hwnd)
    for c in cs:
        if c["cls"] in ("ListBox", "ComboBox"):
            n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
            sink.step("save_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                      rect=c["rect"], n_items=n)
            if n:
                L.read_listbox(hproc, c["hwnd"], sink, "save_items")
    sv = [c for c in cs if c["cls"] == "Button" and c["visible"]
          and c["text"] == "GUI:Save"]
    boxes = [c for c in cs if c["cls"] == "ListBox"
             and int(L.smt(c["hwnd"], L.LB_GETCOUNT)) > 0]
    edits = [c for c in cs if c["cls"] == "Edit"]
    sink.step("save_dialog_plan", save_buttons=[c["text"] for c in sv],
              n_boxes=len(boxes), n_edits=len(edits))
    if boxes:
        L.smt(boxes[0]["hwnd"], L.LB_SETCURSEL, 0)
        r = boxes[0]["rect"]
        L.real_mouse_click(sink, "K1_click_first_slot",
                           (r[0] + r[2]) // 2, r[1] + 10, wait_s=0.6)
    if edits:
        r = edits[0]["rect"]
        L.real_mouse_click(sink, "K1_focus_name_field",
                           (r[0] + r[2]) // 2, (r[1] + r[3]) // 2, wait_s=0.6)
        L.type_ascii(sink, "K1_type_save_name", "W44Q3SAVE")
        L.wm_settext(sink, "K1_wm_settext", edits[0]["hwnd"], "W44Q3SAVE")
    snap(pid, hproc, sink, "K1_after_name")
    L.screenshot(sink, "w44_run_K1_after_name", hwnd)
    if sv:
        L.click_hwnd(sv[0]["hwnd"], sink, "K1_click_GUI_Save", wait_s=3.0)
    snap(pid, hproc, sink, "K1_after_save")
    L.screenshot(sink, "w44_run_K1_after_save", hwnd)
    after = L.save_inventory(sink, "K1_after_save_files")
    bmap = {x["name"]: x for x in before}
    added = [f for f in after if f["name"] not in bmap]
    changed = [f for f in after if f["name"] in bmap
               and f["sha256"] != bmap[f["name"]]["sha256"]]
    sink.step("K1_save_file", added=added, changed=changed,
              before_n=len(before), after_n=len(after))
    if not (added or changed) and sv:
        sink.step("K1_save_retry", note="click GUI:Save once more")
        L.click_hwnd(sv[0]["hwnd"], sink, "K1_click_GUI_Save_retry", wait_s=3.0)
        after = L.save_inventory(sink, "K1_after_save_retry")
        added = [f for f in after if f["name"] not in bmap]
        changed = [f for f in after if f["name"] in bmap
                   and f["sha256"] != bmap[f["name"]]["sha256"]]
        sink.step("K1_save_file_retry", added=added, changed=changed)
    saved = None
    for f in (added + changed):
        src = C.GAME / f["name"]
        if src.is_file():
            dst = C.OUT / ("save_" + f["name"])
            dst.write_bytes(src.read_bytes())
            sink.step("K1_save_copied", src=str(src), dst=str(dst),
                      sha256=L.sha256_file(dst), size=dst.stat().st_size)
            saved = {"name": f["name"], "sha256": f["sha256"],
                     "size": f["size"], "copy": str(dst),
                     "label": "W44Q3SAVE"}
            break
    if saved:
        (C.OUT / "save_meta.json").write_text(
            json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
        sink.step("save_meta_written", **saved)
    return saved


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None}
    ok = False
    outcome = "unknown"
    saved = None
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  csf_text=C.CSF_TEXT, csf_label="RA2F:942506FC",
                  design_note="v12 package: --mapselmd + --csf-out/--csf-base")

        # save as-built copies for byte-exact restore
        for n in ASBUILT:
            p = C.GAME / n
            if p.is_file():
                (C.OUT / (n + ".asbuilt")).write_bytes(p.read_bytes())
        # D2 entry: [SOV1] Scenario=SOV01umd.MAP -> ECH01.MAP (sandbox only)
        raw_b = BATTLE.read_bytes()
        cnt_sov = raw_b.count(b"Scenario=SOV01umd.MAP")
        sink.step("D2_precheck", sov1_count=cnt_sov,
                  battle_sha256=L.sha256_file(BATTLE))
        if cnt_sov != 1:
            raise RuntimeError("expected exactly one SOV1 Scenario line, got %d"
                               % cnt_sov)
        mod_b = raw_b.replace(b"Scenario=SOV01umd.MAP", b"Scenario=ECH01.MAP")
        BATTLE.write_bytes(mod_b)
        BATTLE_ORIG.write_bytes(raw_b)
        BATTLE_D2.write_bytes(mod_b)
        sink.step("D2_applied", sha256=L.sha256_file(BATTLE), bytes=len(mod_b))

        pid, hwnd, hproc = launch_one(sink, "K1", state)
        snap(pid, hproc, sink, "S0_main_menu")
        L.screenshot(sink, "w44_run_S0_main_menu", hwnd)
        m0 = L.memory_search(hproc, CSF_NEEDLES, sink, "S0_main_menu_memory")

        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                label="click_NewCampaign")
        cs, cnt, vis = snap(pid, hproc, sink, "S2_campaign_menu")
        L.screenshot(sink, "w44_run_S2_campaign_menu", hwnd)
        # ---- CSF description-area judgment: SCREENSHOTS ONLY ----
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        ww, wh = wr[2] - wr[0], wr[3] - wr[1]
        crop(sink, "w44_run_S2_campaign_menu",
             (0, 0, max(400, ww // 2), wh), 2, "w44_campaign_menu_left")
        crop(sink, "w44_run_S2_campaign_menu",
             (max(400, ww // 2), 0, ww, wh), 2, "w44_campaign_menu_right")
        crop(sink, "w44_run_S2_campaign_menu",
             (0, 0, ww, wh), 2, "w44_campaign_menu_full2x")
        mc = L.memory_search(hproc, CSF_NEEDLES + ["點選蘇聯圖示", "點選盟軍圖示"],
                             sink, "S2_campaign_menu_memory")
        sink.step("S2_csf_judgment_inputs",
                  note="display verdict MUST come from the screenshots; "
                       "control texts here only establish control presence/visibility",
                  visible_control_texts=vis,
                  csf_text_ascii_count=mc["hits"].get(C.CSF_TEXT + "|ascii", {}).get("count"),
                  csf_text_utf16_count=mc["hits"].get(C.CSF_TEXT + "|utf16le", {}).get("count"),
                  label_ascii_count=mc["hits"].get("RA2F:942506FC|ascii", {}).get("count"),
                  missing_count=mc["hits"].get("MISSING:|ascii", {}).get("count"))

        # Soviet badge (official entry) -> A1
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        L.screenshot(sink, "w44_run_after_badge", hwnd)
        snap(pid, hproc, sink, "after_badge")
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # A1 in-game
        t0 = time.monotonic()
        a1 = False
        while time.monotonic() - t0 < 75:
            cs, cnt, vis = snap(pid, hproc, sink, "waiting_A1")
            for btn in ("GUI:Play", "GUI:StartGame"):
                if L.find_btn(pid, btn):
                    L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
            if cnt and (cnt.get("frame") or 0) > 30:
                a1 = True
                m1 = L.memory_search(hproc, MARKERS, sink, "A1_ingame_memory")
                sink.step("A1_ingame", elapsed_s=round(time.monotonic() - t0, 2),
                          counters=cnt,
                          marker_counts={k: v["count"]
                                         for k, v in m1["hits"].items()})
                L.screenshot(sink, "w44_run_A1_ingame", hwnd)
                break
            time.sleep(1.5)
        if not a1:
            L.screenshot(sink, "w44_run_A1_timeout", hwnd)
            raise RuntimeError("A1 did not load within 75 s")

        # victory screen -> GUI:Continue
        okv, cs, cnt, vis = poll_controls(
            pid, hproc, sink, "wait_victory", 60,
            want_any=["GUI:Continue"], interval=1.0)
        if not okv:
            L.screenshot(sink, "w44_run_no_victory", hwnd)
            raise RuntimeError("GUI:Continue did not appear within 60 s")
        L.screenshot(sink, "w44_run_victory", hwnd)
        sink.step("pre_continue_state", counters=cnt, visible=vis)

        L.click(pid, "GUI:Continue", sink, wait_s=2.0, label="click_Continue")

        # post-Continue observation: A2 loaded or error dialog
        t1 = time.monotonic()
        while time.monotonic() - t1 < 60:
            if not L.process_alive(pid):
                outcome = "process_exited"
                sink.step("post_continue_exited",
                          elapsed_s=round(time.monotonic() - t1, 2))
                break
            cs, cnt, vis = snap(pid, hproc, sink, "post_continue")
            el = time.monotonic() - t1
            err = ("GUI:OK", "確定", "無法啟始", "無法啟動")
            if any(any(t.lower() in (v or "").lower() for t in err) for v in vis):
                outcome = "error_dialog_GUI_OK"
                L.screenshot(sink, "w44_run_error_dialog", hwnd)
                me = L.memory_search(hproc, MARKERS + ["UnableMapSelect"],
                                     sink, "post_continue_error")
                sink.step("error_dialog_observed", elapsed_s=round(el, 2),
                          counters=cnt, visible=vis,
                          marker_counts={k: v["count"]
                                         for k, v in me["hits"].items()})
                break
            fn = (cnt or {}).get("scen_filename") or ""
            if "ech02" in fn.lower() and (cnt or {}).get("frame", 0) > 10:
                f1 = cnt.get("frame")
                time.sleep(2.5)
                cs2, cnt2, vis2 = snap(pid, hproc, sink, "A2_timer_confirm")
                f2 = (cnt2 or {}).get("frame")
                L.screenshot(sink, "w44_run_A2_ingame", hwnd)
                m2 = L.memory_search(hproc, MARKERS, sink, "post_continue_A2_memory")
                outcome = "A2_loaded"
                sink.step("A2_confirmed", elapsed_s=round(el, 2),
                          frame_t1=f1, frame_t2=f2,
                          frame_delta=(f2 - f1) if (f1 is not None and f2 is not None) else None,
                          counters_t2=cnt2,
                          marker_counts={k: v["count"]
                                         for k, v in m2["hits"].items()})
                # in-game Esc menu (control presence only)
                L.key(L.VK_ESCAPE, sink, "A2_esc_open")
                cs_e, cnt_e, vis_e = snap(pid, hproc, sink, "A2_esc_menu")
                esc_want = ("GUI:ResumeMission", "GUI:SaveGame",
                            "GUI:AbortMission", "GUI:GameControls",
                            "GUI:GameOptions", "GUI:LoadGame")
                sink.step("A2_esc_menu_controls",
                          hits=[v for v in vis_e
                                if any(w.lower() in (v or "").lower()
                                       for w in esc_want)],
                          visible=vis_e)
                L.screenshot(sink, "w44_run_A2_esc_menu", hwnd)
                L.key(L.VK_ESCAPE, sink, "A2_esc_close")
                break
            for mark_s in (5, 12, 25):
                pass
            time.sleep(1.5)
        if outcome == "unknown":
            L.screenshot(sink, "w44_run_post_continue_timeout", hwnd)
            mt = L.memory_search(hproc, MARKERS, sink, "post_continue_timeout")
            sink.step("post_continue_timeout",
                      marker_counts={k: v["count"] for k, v in mt["hits"].items()})
        sink.step("run_outcome", outcome=outcome)

        # ---- save in A2 (only if A2 actually loaded) ----
        if outcome == "A2_loaded":
            saved = do_save(pid, hproc, hwnd, sink)

        ok = (outcome == "A2_loaded" and saved is not None)
        sink.step("K1_result", ok=ok, outcome=outcome,
                  saved=bool(saved))
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
        # byte-exact restore of every file we touched (not the package files:
        # those are managed by install/uninstall and stay until phase 7)
        for n in ("BATTLEMD.INI", "ECH01.MAP", "ECH02.MAP"):
            orig = C.OUT / (n + ".asbuilt")
            cur = C.GAME / n
            try:
                if orig.is_file():
                    cur.write_bytes(orig.read_bytes())
                sink.step("restore_file", file=n,
                          sha256=L.sha256_file(cur) if cur.is_file() else None,
                          byte_identical=(orig.is_file() and cur.is_file()
                                          and cur.read_bytes() == orig.read_bytes()))
            except Exception as e:
                sink.step("restore_file_error", file=n, error=repr(e))
        try:
            C.heal(sink, label="K1_finally")
        except Exception as e:
            sink.step("heal_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  outcome=outcome, saved=bool(saved),
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
