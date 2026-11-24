#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W39 · Live verification driver for MAPSELMD.INI campaign progression.

Modes:
  skip_no          - W27 Live Campaign as-built (SkipMapSelect=no) + loose
                     appended MAPSELMD.INI (6,108 B / 2 stages)  [MAIN TEST]
  skip_yes         - Distinguishing experiment (SkipMapSelect=yes on ECH01/ECH02)
  control_official - Negative control: loose MAPSELMD.INI replaced by the
                     official 5,573 B (NO appended stages), SkipMapSelect=no

Always restores BATTLEMD.INI, ECH01.MAP, ECH02.MAP, MAPSELMD.INI,
RA2MD.INI, ddraw.ini, closes own gamemd.exe, verifies 0 residual gamemd.exe,
and writes kind=meta_end.
"""
from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

BATTLE = L.GAME / "BATTLEMD.INI"
BATTLE_ORIG = L.OUT / "BATTLEMD.INI.asbuilt"
BATTLE_D2 = L.OUT / "BATTLEMD.INI.D2_sov1_ech01"
ECH01 = L.GAME / "ECH01.MAP"
ECH02 = L.GAME / "ECH02.MAP"
ECH01_ORIG = L.OUT / "ECH01.MAP.asbuilt"
ECH02_ORIG = L.OUT / "ECH02.MAP.asbuilt"
MAPSEL_CUR = L.GAME / "MAPSELMD.INI"
# byte-exact restore target = the deployed appended variant (11cc1cac...)
MAPSEL_APPENDED = L.OUT / "MAPSELMD.INI.w39_deployed"
MAPSEL_OFFICIAL = L.OUT / "MAPSELMD.OFFICIAL.INI"

MARKERS = ["ECH01.MAP", "ECH02.MAP", "RA2F_ECH01", "RA2F_ECH02", "W27 A1", "W27 A2"]


def snap_state(pid, hproc, sink: L.Sink, label: str):
    cs = L.controls(pid)
    cnt = L.read_counters(hproc) if hproc else None
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    sink.step("screen", label=label, counters=cnt, visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"],
                             "id": c["ctrl_id"]} for c in cs])
    return cs, cnt, vis


def wait_main_menu(pid, sink: L.Sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return
        time.sleep(1.5)
    raise RuntimeError("main menu timeout")


def poll_controls(pid, hproc, sink: L.Sink, label: str, timeout_s: float,
                  want_any: list[str], interval: float = 1.5):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        cs, cnt, vis = snap_state(pid, hproc, sink, label)
        hit = [w for w in want_any if any(w.lower() in (v or "").lower() for v in vis)]
        if hit:
            sink.step("poll_hit", label=label, hits=hit,
                      elapsed_s=round(time.monotonic() - t0, 2))
            return True, cs, cnt, vis
        time.sleep(interval)
    sink.step("poll_timeout", label=label, timeout_s=timeout_s, wanted=want_any)
    return False, None, None, []


def launch_one(sink: L.Sink, tag: str, state: dict):
    pre = L.list_gamemd()
    sink.step("pre_launch_guard", tag=tag, gamemd_processes=pre, n=len(pre))
    if pre:
        raise RuntimeError(f"residual gamemd before launch: {pre}")
    launcher = L.launch_game(sink)
    pid = L.wait_for_pid(launcher, sink)
    state["pid"] = pid
    # W39 step-0 gate: MUST run within 30 s of launch. Abort immediately if the
    # observation process cannot see the interactive desktop (W35's blocker).
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


def set_skip_mapsel(map_path: Path, value: str) -> bytes:
    raw = map_path.read_bytes()
    txt = raw.decode("latin-1")
    if "SkipMapSelect=no" in txt:
        new_txt = txt.replace("SkipMapSelect=no", f"SkipMapSelect={value}", 1)
    elif "SkipMapSelect=yes" in txt:
        new_txt = txt.replace("SkipMapSelect=yes", f"SkipMapSelect={value}", 1)
    else:
        raise RuntimeError(f"SkipMapSelect= not found in {map_path}")
    new_bytes = new_txt.encode("latin-1")
    map_path.write_bytes(new_bytes)
    return new_bytes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["skip_no", "skip_yes", "control_official"],
                    required=True)
    ap.add_argument("--mapsel-click", default=None,
                    help="Optional x,y screen coords to click if interactive MapSelect appears")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    tag = args.tag or f"w39_{args.mode}"
    sink = L.Sink(tag)
    sink.step("run_start", kind="meta_start", mode=args.mode,
              mapsel_click=args.mapsel_click,
              mapsel_present=(L.GAME / "MAPSELMD.INI").is_file(),
              mapsel_sha256=(L.sha256_file(L.GAME / "MAPSELMD.INI")
                             if (L.GAME / "MAPSELMD.INI").is_file() else None))

    state = {"pid": None, "hwnd": None, "hproc": None}
    try:
        # Save as-built originals if not yet saved, or read from current sandbox
        if not BATTLE_ORIG.is_file():
            BATTLE_ORIG.write_bytes(BATTLE.read_bytes())
        if not ECH01_ORIG.is_file():
            ECH01_ORIG.write_bytes(ECH01.read_bytes())
        if not ECH02_ORIG.is_file():
            ECH02_ORIG.write_bytes(ECH02.read_bytes())

        # D2 entry: [SOV1] Scenario=SOV01umd.MAP -> Scenario=ECH01.MAP (sandbox only)
        raw_b = BATTLE_ORIG.read_bytes()
        assert raw_b.count(b"Scenario=SOV01umd.MAP") == 1
        mod_b = raw_b.replace(b"Scenario=SOV01umd.MAP", b"Scenario=ECH01.MAP")
        BATTLE.write_bytes(mod_b)
        BATTLE_D2.write_bytes(mod_b)
        sink.step("battle_d2_applied", sha256=L.sha256_file(BATTLE),
                  bytes=len(mod_b))

        if args.mode == "skip_yes":
            set_skip_mapsel(ECH01, "yes")
            set_skip_mapsel(ECH02, "yes")
            (L.OUT / "ECH01.MAP.skip_yes").write_bytes(ECH01.read_bytes())
            (L.OUT / "ECH02.MAP.skip_yes").write_bytes(ECH02.read_bytes())
            sink.step("skip_yes_applied",
                      ech01_sha256=L.sha256_file(ECH01),
                      ech02_sha256=L.sha256_file(ECH02))

        if args.mode == "control_official":
            # Single-variable negative control: loose MAPSELMD.INI becomes the
            # unmodified official 5,573 B (no appended stages). Everything else
            # (D2 entry, SkipMapSelect=no, installed package) stays identical.
            assert MAPSEL_OFFICIAL.is_file()
            MAPSEL_CUR.write_bytes(MAPSEL_OFFICIAL.read_bytes())
            sink.step("control_official_mapsel_applied",
                      sha256=L.sha256_file(MAPSEL_CUR),
                      bytes=MAPSEL_CUR.stat().st_size,
                      appended_sha256=L.sha256_file(MAPSEL_APPENDED))

        pid, hwnd, hproc = launch_one(sink, tag, state)
        snap_state(pid, hproc, sink, "S0_main_menu")
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="click_NewCampaign")
        snap_state(pid, hproc, sink, "S2_campaign_menu")
        L.screenshot(sink, f"{tag}_campaign_menu", hwnd)

        # Click Soviet badge (window origin may be non-zero; use window rect offset)
        wrect = L.rect(hwnd) or [0, 0, 1366, 768]
        bx = wrect[0] + 210
        by = wrect[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        L.screenshot(sink, f"{tag}_after_badge", hwnd)
        snap_state(pid, hproc, sink, "after_badge")

        # Skip movies with Enter x2
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # Wait for A1 in-game (frame > 30) or briefing button
        t0 = time.monotonic()
        a1_loaded = False
        while time.monotonic() - t0 < 75:
            cs, cnt, vis = snap_state(pid, hproc, sink, "waiting_A1")
            for btn in ("GUI:Play", "GUI:StartGame"):
                if L.find_btn(pid, btn):
                    L.click(pid, btn, sink, wait_s=2.0, label=f"click_{btn}")
            if cnt and (cnt.get("frame") or 0) > 30:
                a1_loaded = True
                m1 = L.memory_search(hproc, MARKERS, sink, "A1_ingame")
                sink.step("A1_ingame", elapsed_s=round(time.monotonic() - t0, 2),
                          counters=cnt,
                          marker_counts={k: v["count"] for k, v in m1["hits"].items()})
                L.screenshot(sink, f"{tag}_A1_ingame", hwnd)
                break
            time.sleep(1.5)
        if not a1_loaded:
            L.screenshot(sink, f"{tag}_A1_timeout", hwnd)
            raise RuntimeError("A1 did not load within 75s")

        # Wait for survive(8) victory screen -> GUI:Continue
        ok, cs, cnt, vis = poll_controls(
            pid, hproc, sink, "wait_victory", 60,
            want_any=["GUI:Continue"], interval=1.0
        )
        if not ok:
            L.screenshot(sink, f"{tag}_no_victory", hwnd)
            raise RuntimeError("Victory screen (GUI:Continue) did not appear within 60s")

        L.screenshot(sink, f"{tag}_victory", hwnd)
        sink.step("pre_continue_state", counters=cnt, visible=vis)

        # Click GUI:Continue
        L.click(pid, "GUI:Continue", sink, wait_s=2.0, label="click_Continue")

        # Observe post-Continue behavior for up to 60s
        t1 = time.monotonic()
        outcome = "unknown"
        shot_taken_at = set()
        clicked_mapsel = False
        while time.monotonic() - t1 < 60:
            if not L.process_alive(pid):
                outcome = "process_exited"
                sink.step("post_continue_exited", elapsed_s=round(time.monotonic() - t1, 2))
                break
            cs, cnt, vis = snap_state(pid, hproc, sink, "post_continue")
            el = time.monotonic() - t1

            # 1) Error dialog check (W27 saw a GUI:OK / 確定 dialog)
            err_triggers = ("GUI:OK", "確定", "無法啟始", "無法啟動")
            if any(any(t.lower() in (v or "").lower() for t in err_triggers)
                   for v in vis):
                outcome = "error_dialog_GUI_OK"
                L.screenshot(sink, f"{tag}_error_dialog", hwnd)
                cs_d, cnt_d, vis_d = snap_state(pid, hproc, sink, "error_dialog_controls")
                branch_tokens = ["UnableMapSelect", "Invalid stage",
                                 "Invalid side", "Unable to initialize choices",
                                 "Unable to create font", "無法啟始選取地圖"]
                m_err = L.memory_search(hproc, MARKERS + branch_tokens,
                                        sink, "post_continue_error")
                sink.step("error_dialog_observed", elapsed_s=round(el, 2),
                          counters=cnt, visible=vis,
                          dialog_all_controls=[{"cls": c["cls"], "text": c["text"],
                                                "vis": c["visible"]}
                                               for c in cs_d],
                          marker_counts={k: v["count"] for k, v in m_err["hits"].items()})
                break

            # 2) Check if A2 loaded in-game: frame advancing AND (scen_filename == ECH02.MAP or ECH02 marker)
            fn = (cnt or {}).get("scen_filename") or ""
            if "ech02" in fn.lower() and (cnt or {}).get("frame", 0) > 10:
                # Sample again after 2.5s to prove timer is incrementing
                f1 = cnt.get("frame")
                time.sleep(2.5)
                cs2, cnt2, vis2 = snap_state(pid, hproc, sink, "A2_timer_confirm")
                f2 = (cnt2 or {}).get("frame")
                L.screenshot(sink, f"{tag}_A2_ingame", hwnd)
                m_a2 = L.memory_search(hproc, MARKERS, sink, "post_continue_A2")
                outcome = "A2_loaded"
                sink.step("A2_confirmed", elapsed_s=round(el, 2),
                          frame_t1=f1, frame_t2=f2,
                          frame_delta=(f2 - f1) if (f1 is not None and f2 is not None) else None,
                          counters_t2=cnt2,
                          marker_counts={k: v["count"] for k, v in m_a2["hits"].items()})
                # Extra hard indicator #3: in-game Esc menu control texts.
                L.key(L.VK_ESCAPE, sink, "A2_esc_open")
                cs_e, cnt_e, vis_e = snap_state(pid, hproc, sink, "A2_esc_menu")
                esc_want = ("GUI:ResumeMission", "GUI:SaveGame",
                            "GUI:AbortMission", "GUI:GameControls",
                            "GUI:GameOptions", "GUI:LoadGame")
                esc_hits = [v for v in vis_e
                            if any(w.lower() in (v or "").lower() for w in esc_want)]
                sink.step("A2_esc_menu_controls", hits=esc_hits, visible=vis_e)
                L.screenshot(sink, f"{tag}_A2_esc_menu", hwnd)
                L.key(L.VK_ESCAPE, sink, "A2_esc_close")
                break

            # Periodic screenshots at ~5s, ~12s, ~25s to see interactive MapSelect / loading
            for mark_s in (5, 12, 25):
                if el >= mark_s and mark_s not in shot_taken_at:
                    shot_taken_at.add(mark_s)
                    L.screenshot(sink, f"{tag}_post_continue_{mark_s}s", hwnd)
                    L.memory_search(hproc, MARKERS, sink, f"post_continue_{mark_s}s")

            # Optional click on interactive MapSelect screen if coords given
            if args.mapsel_click and not clicked_mapsel and el >= 6.0:
                cx, cy = [int(x) for x in args.mapsel_click.split(",")]
                L.real_mouse_click(sink, "click_mapselect_target",
                                   wrect[0] + cx, wrect[1] + cy, wait_s=2.0)
                clicked_mapsel = True
                L.screenshot(sink, f"{tag}_after_mapsel_click", hwnd)

            time.sleep(1.5)

        if outcome == "unknown":
            L.screenshot(sink, f"{tag}_post_continue_timeout", hwnd)
            m_to = L.memory_search(hproc, MARKERS, sink, "post_continue_timeout")
            sink.step("post_continue_timeout",
                      marker_counts={k: v["count"] for k, v in m_to["hits"].items()})

        sink.step("run_outcome", outcome=outcome, mode=args.mode)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        hproc = state.get("hproc")
        pid = state.get("pid")
        hwnd = state.get("hwnd")
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
        # Restore sandbox files byte-exactly
        for orig, cur, name in [
            (BATTLE_ORIG, BATTLE, "BATTLEMD.INI"),
            (ECH01_ORIG, ECH01, "ECH01.MAP"),
            (ECH02_ORIG, ECH02, "ECH02.MAP"),
            (MAPSEL_APPENDED, MAPSEL_CUR, "MAPSELMD.INI"),
        ]:
            try:
                if orig.is_file():
                    cur.write_bytes(orig.read_bytes())
                sink.step("restore_file", file=name,
                          sha256=L.sha256_file(cur) if cur.is_file() else None,
                          byte_identical=(orig.is_file() and cur.is_file()
                                          and cur.read_bytes() == orig.read_bytes()))
            except Exception as e:
                sink.step("restore_file_error", file=name, error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_configs_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", mode=args.mode,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
