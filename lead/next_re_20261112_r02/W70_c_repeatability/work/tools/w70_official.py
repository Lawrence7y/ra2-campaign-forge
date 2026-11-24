# -*- coding: utf-8 -*-
r"""W70 T2 · FUNCTIONAL check: after install -> uninstall -> byte-restore,
RESTART the game and walk the OFFICIAL Soviet campaign entry (original [SOV1]).

The whole point: "能卸载" != "卸载后游戏正常".  Byte-restore only proves the
file is back; this script proves the OFFICIAL campaign is actually PLAYABLE.

Criteria (T2):
  * restart gamemd.exe on the RESTORED sandbox (fresh process),
  * reach the campaign menu, click the Soviet badge,
  * Scen+0x125C must be the OFFICIAL map name (== [SOV1] Scenario from the
    real BATTLEMD.INI), and must NOT be RA2F_M1.MAP / M2 / M3,
  * frame advancing (>30) => genuinely in-mission, not a stale string,
  * screenshot of campaign menu + entering the official first mission.

LOCK DISCIPLINE (per trip): gate on owner==lead & 0 live gamemd -> owner=w70
-> launch -> observe -> ALWAYS release back to owner=lead in finally.

REAL-MACHINE: WMI Win32_Process.Create launches ONLY sandbox gamemd.exe;
read-only RPM / EnumWindows / ImageGrab; close only the pid WE launched.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w70_lib as L
import w70_common as C

TAG = "t2_official"
L.SHOT_PREFIX = "t2_"

EXPECTED_OFFICIAL = None      # filled from OFFICIAL_SOV1.json
FORBIDDEN = ["RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP"]
ERR_TOKENS = ("GUI:OK", "確定", "无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "Invalid stage")


class OfficialError(RuntimeError):
    def __init__(self, msg, **detail):
        super().__init__(msg)
        self.detail = detail


def w59(sink, hproc, label):
    p = L.read_w59_point(hproc, label)
    sink.step("w59_point", **p)
    return p


def shot(sink, hwnd, label):
    try:
        return str(L.screenshot(sink, label, hwnd))
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def snap(sink, pid, hproc, label):
    cs = L.controls(pid)
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    p = w59(sink, hproc, label + "_w59")
    sink.step("screen_state", label=label, visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"]} for c in cs])
    return cs, vis, p


def is_error_dialog(vis):
    return any(any(t.lower() in (v or "").lower() for t in ERR_TOKENS)
               for v in vis)


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready",
                      elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return
        time.sleep(1.5)
    raise OfficialError("main menu timeout (%ss)" % timeout_s)


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False}
    ok = False
    verdict = "不可用（未跑成：未进入官方第一关）"
    result = {}
    try:
        # ---- official [SOV1] expectation ----------------------------------
        o = json.loads((C.OUT / "OFFICIAL_SOV1.json").read_text(encoding="utf-8"))
        expected = o["sov1_scenario"]
        result["expected_official_sov1_scenario"] = expected
        result["expected_source_sha256"] = o["source_sha256"]
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  expected_official_0x125C=expected,
                  forbidden=FORBIDDEN,
                  note="functional T2: official campaign after uninstall+restore")

        # ---- (0) LOCK GATE -------------------------------------------------
        pre = L.list_gamemd()
        lock_txt = C.lock_read()
        owner = ""
        for ln in lock_txt.splitlines():
            if ln.startswith("owner="):
                owner = ln.split("=", 1)[1].strip()
        sink.step("lock_gate_before", lock_content=lock_txt, owner=owner,
                  gamemd_processes=pre, n=len(pre))
        if owner != "lead" or pre:
            t0 = time.monotonic()
            while time.monotonic() - t0 < 60:
                time.sleep(5)
                owner2 = ""
                for ln in C.lock_read().splitlines():
                    if ln.startswith("owner="):
                        owner2 = ln.split("=", 1)[1].strip()
                if owner2 == "lead" and not L.list_gamemd():
                    owner = owner2
                    break
            sink.step("lock_gate_after_wait", owner=owner,
                      gamemd_processes=L.list_gamemd())
            if owner != "lead" or L.list_gamemd():
                raise OfficialError("lock gate refused: owner=%r, live=%r"
                                    % (owner, L.list_gamemd()))
        C.lock_claim_w70("W70 T2 official-campaign functional check: "
                         "after uninstall+byte-restore, restart game, "
                         "walk OFFICIAL [SOV1] Soviet campaign entry")
        state["lock_taken"] = True
        sink.step("lock_claimed", owner="w70", content=C.lock_read())

        # ---- (1) launch ----------------------------------------------------
        if L.list_gamemd():
            raise OfficialError("residual gamemd before launch (not ours)")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        state["pid"] = pid
        L.desktop_precheck(sink)          # within 30 s of WMI launch
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
        if not hproc:
            raise OfficialError("OpenProcess(PROCESS_VM_READ) returned NULL")
        wait_main_menu(pid, sink)
        L.force_foreground(hwnd)
        sink.step("instance_ready", pid=pid, hwnd=hwnd,
                  rect=L.rect(hwnd) if hwnd else None,
                  title=L.wtxt(hwnd) if hwnd else None)
        snap(sink, pid, hproc, "S0_main_menu")
        shot(sink, hwnd, "S0_main_menu")

        # ---- (2) campaign menu --------------------------------------------
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="click_NewCampaign")
        cs, vis, p = snap(sink, pid, hproc, "S2_campaign_menu")
        shot(sink, hwnd, "S2_campaign_menu")
        sink.step("campaign_menu", visible=vis, w59=p)

        # ---- (3) OFFICIAL Soviet badge ([SOV1] is restored) ----------------
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        L.force_foreground(hwnd)
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        shot(sink, hwnd, "after_SOVIET_badge")
        snap(sink, pid, hproc, "after_badge")
        # skip intro/briefing movies (same as W63)
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # ---- (4) wait for the OFFICIAL first mission ----------------------
        t0 = time.monotonic()
        traj = []
        entered = None
        while time.monotonic() - t0 < 150:
            cs, vis, p = snap(sink, pid, hproc, "wait_official_mission")
            fn = p.get("scen_filename") or ""
            frame = p.get("frame") or 0
            traj.append({"t": round(time.monotonic() - t0, 1),
                         "fn": fn, "frame": frame,
                         "stage": p.get("scen_stage_idx"),
                         "eog": p.get("scen_end_of_game"),
                         "vis": vis[:12]})
            if is_error_dialog(vis):
                shot(sink, hwnd, "error_official")
                raise OfficialError("error dialog while entering official mission",
                                    visible=vis, w59=p, trajectory=traj[-20:])
            for btn in ("GUI:Play", "GUI:StartGame"):
                if L.find_btn(pid, btn):
                    L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
            forbidden_hit = any(f.lower() in fn.lower() for f in FORBIDDEN)
            if forbidden_hit:
                shot(sink, hwnd, "error_still_our_map")
                raise OfficialError("Scen+0x125C is STILL our injected map %r "
                                    "after uninstall -> official entry NOT restored"
                                    % fn, w59=p, trajectory=traj[-20:])
            is_official = (expected and
                           fn.strip().lower() == expected.strip().lower())
            if fn and frame > 30 and (is_official or
                                      (not fn.upper().startswith("RA2F") and
                                       ".MAP" in fn.upper())):
                shot_enter = shot(sink, hwnd, "enter_official_mission")
                sink.step("official_mission_entered", elapsed_s=round(
                    time.monotonic() - t0, 2), w59=p,
                    screenshot=shot_enter,
                    matches_official_sov1=is_official,
                    frame_trajectory=traj[-12:])
                entered = {"fn": fn, "frame": frame, "w59": p,
                           "matches_official_sov1": is_official,
                           "screenshot": shot_enter}
                break
            if not L.process_alive(pid):
                shot(sink, hwnd, "process_exited")
                raise OfficialError("gamemd exited before official mission loaded",
                                    trajectory=traj[-20:])
            # periodically nudge past movies (idempotent: harmless if in-game)
            if len(traj) % 5 == 0:
                L.key(L.VK_RETURN, sink, "Enter_nudge_%d" % len(traj))
            time.sleep(1.5)
        if entered is None:
            shot(sink, hwnd, "timeout_official_mission")
            raise OfficialError("timeout (150s) waiting for official first mission",
                                trajectory=traj[-25:])

        # ---- verdict -------------------------------------------------------
        result.update({
            "entered_official_mission": True,
            "observed_0x125C": entered["fn"],
            "expected_0x125C": expected,
            "matches_official_sov1": entered["matches_official_sov1"],
            "not_our_injected_map": not any(
                f.lower() in entered["fn"].lower() for f in FORBIDDEN),
            "frame_advancing": entered["frame"] > 30,
            "frame": entered["frame"],
            "w59": entered["w59"],
            "screenshots": {
                "campaign_menu": str(C.OUT / "screen_t2_S2_campaign_menu.png"),
                "enter_official": entered["screenshot"],
            },
            "trajectory": traj,
            "MSG_UnableMapSelect_seen": any(
                "UnableMapSelect" in " ".join(x["vis"]).lower()
                for x in traj if x.get("vis")),
        })
        if (result["matches_official_sov1"] and result["not_our_injected_map"]
                and result["frame_advancing"]
                and not result["MSG_UnableMapSelect_seen"]):
            verdict = "官方入口恢复可用"
            ok = True
        else:
            verdict = ("恢复但异常（进了非 RA2F 图但 %s：matches=%s frame=%s "
                       "UnableMapSelect=%s）"
                       % (entered["fn"], result["matches_official_sov1"],
                          result["frame_advancing"],
                          result["MSG_UnableMapSelect_seen"]))
        sink.step("t2_verdict", ok=ok, verdict=verdict, **{
            k: v for k, v in result.items() if k not in ("trajectory", "w59")})
    except OfficialError as e:
        verdict = "不可用（%s）" % str(e)
        sink.step("t2_blocked", verdict=verdict, detail=e.detail)
    except Exception as e:
        verdict = "不可用（FATAL %r）" % (e,)
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        # (a) close ONLY the game we launched
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        close_steps = []
        if pid:
            try:
                close_steps = L.close_game(pid, hwnd, sink)
            except Exception as e:
                sink.step("close_error", error=repr(e))
        residual = L.list_gamemd()
        sink.step("trip_cleanup", close_steps=close_steps,
                  gamemd_residual=residual, residual_zero=(len(residual) == 0))
        # (b) ALWAYS release the lock to lead with a status note
        if state["lock_taken"]:
            C.lock_release("W70 T2 official-campaign check FINISHED "
                           "(ok=%s, verdict=%s): self-launched gamemd closed, "
                           "residual=%d; restored owner=lead."
                           % (ok, verdict, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        # (c) persist
        result.update({"ok": ok, "verdict": verdict,
                       "gamemd_residual": residual,
                       "lock_final": C.lock_read()})
        (C.OUT / "T2_OFFICIAL.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  verdict=verdict, gamemd_residual=residual,
                  lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
