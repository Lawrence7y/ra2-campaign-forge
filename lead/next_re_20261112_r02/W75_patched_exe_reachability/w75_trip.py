#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W75 · ONE TRIP (trip A = patched exe, trip B = original exe).
Same sandbox, same navigation, same hot-zone screen coords, same reads.
Per-trip lock: claim w75 at start -> release to lead in finally.
Only self-launched gamemd pid is ever closed. Writes ONLY inside W75.

Usage: python w75_trip.py --trip A | --trip B
"""
from __future__ import annotations
import argparse, json, shutil, sys, time
import w75_lib as L

OUT = L.OUT
OUT.mkdir(parents=True, exist_ok=True)


def json_dump(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1,
                                       default=str), encoding="utf-8")


def wait_text(pid, text, timeout_s, sink, retry_click=None, tag=""):
    t = time.monotonic()
    while time.monotonic() - t < timeout_s:
        cs = L.controls(pid)
        hits = [c for c in cs if text.lower() in (c.get("text") or "").lower()]
        if hits:
            sink.step("wait_text_found", tag=tag, text=text,
                      elapsed_s=round(time.monotonic() - t, 2),
                      hits=[(c["text"], c["cls"], c["visible"])
                            for c in hits[:6]])
            return hits
        if retry_click and (time.monotonic() - t) > 6.0:
            L.click(pid, retry_click, sink, wait_s=0.6,
                    label=tag + "_retry_" + retry_click)
            time.sleep(1.0)
        time.sleep(0.5)
    cs = L.controls(pid)
    sink.step("wait_text_timeout", tag=tag, text=text,
              controls=[(c["text"], c["cls"], c["ctrl_id"])
                        for c in cs[:60]])
    return None


def control_summary(cs):
    ids = [c["ctrl_id"] for c in cs]
    return {"n_controls": len(cs),
            "n_visible": sum(1 for c in cs if c["visible"]),
            "ctrl_ids": sorted(set(ids)),
            "has_1771": 1771 in ids,
            "count_1771": ids.count(1771),
            "n_1770": ids.count(1770),
            "n_1772": ids.count(1772),
            "controls_1771": [c for c in cs if c["ctrl_id"] == 1771],
            "controls_1770": [c for c in cs if c["ctrl_id"] == 1770],
            "controls_1772": [c for c in cs if c["ctrl_id"] == 1772]}


def top_window_summary(pid):
    rows = []
    for h in L.top_windows(pid):
        rows.append({"hwnd": int(h), "cls": L.wcls(h), "text": L.wtxt(h),
                     "visible": bool(L.u.IsWindowVisible(h)),
                     "rect": L.rect(h)})
    return rows


def error_windows(pid):
    """Heuristic: native dialog class or error-ish text anywhere in this pid."""
    keys = ("error", "unable", "cannot", "failed", "警告", "錯誤", "错误",
            "無法", "无法", "gui:ok", "assert", "exception", "fatal")
    out = []
    for c in L.controls(pid):
        t = (c.get("text") or "").lower()
        cl = (c.get("cls") or "").lower()
        if (cl in ("#32770", "tooltips_class32")
                or ("tooltips" in cl)
                or any(k in t for k in keys)):
            out.append(c)
    return out


def tooltip_windows(pid):
    out = []
    for c in L.controls(pid):
        cl = (c.get("cls") or "").lower()
        if "tooltip" in cl or (c.get("text") and
                               ("tutorial" in (c.get("text") or "").lower()
                                or "campaignanim" in (c.get("text") or "").lower())):
            out.append(c)
    return out


def hotzone_from_control(c):
    r = c.get("rect")
    if not r or len(r) != 4:
        return None
    return {"cx": (r[0] + r[2]) // 2, "cy": (r[1] + r[3]) // 2,
            "rect": r, "source": "ctrl_id_1771_GetWindowRect"}


def hotzone_fallback_from_1770(c1770):
    """W61 template: 1770 @(125,34) 174x87, new 1771 @(310,34) 110x87
    (DIALOG units). Convert via 1770's observed screen rect."""
    r = c1770.get("rect") if c1770 else None
    if not r or len(r) != 4:
        return None
    sx = (r[2] - r[0]) / 174.0
    sy = (r[3] - r[1]) / 87.0
    left = r[0] + 185 * sx
    top = r[1] + 0 * sy
    width = 110 * sx
    height = 87 * sy
    return {"cx": int(left + width / 2), "cy": int(top + height / 2),
            "rect": [int(left), int(top), int(left + width), int(top + height)],
            "source": "geometry_fallback_from_1770_template",
            "note": "DIALOG units (310,34)110x87 vs 1770 (125,34)174x87"}


def sample(sink, hproc, label, tag, samples):
    p = L.read_w75_point(hproc, label=label)
    samples.append(p)
    sink.step("mem_sample", tag=tag, **p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trip", choices=["A", "B"], required=True)
    a = ap.parse_args()
    trip = a.trip
    tag = "trip" + trip
    S = L.Sink(tag)
    summary = {"trip": trip, "ok": False, "tag": tag}
    pid = None
    hwnd = None
    hproc = None
    locked = False

    try:
        # ---------- 0. exe selection + pre-lock gate ---------------------
        expected_exe_sha = (L.EXPECTED["patch_gamemd_sha"] if trip == "A"
                            else L.EXPECTED["real_gamemd_sha"])
        src_exe = (OUT / "gamemd_patched.exe" if trip == "A"
                   else OUT / "pristine_gamemd.exe")
        dst_exe = L.GAME / "gamemd.exe"
        # HARD GUARD: destination must be inside THIS card's sandbox
        assert str(dst_exe).startswith(str(L.W75)), "refusing to write outside W75"
        assert dst_exe.name.lower() == "gamemd.exe"
        assert dst_exe.parent == L.GAME
        pre_state = L.lock_read()
        S.step("pre_lock_state", lock=pre_state,
               gamemd_processes=L.list_gamemd())
        if not pre_state or pre_state.get("owner") != "lead":
            raise RuntimeError("LOCK NOT FREE (owner=%r) -- abort trip %s"
                               % (pre_state and pre_state.get("owner"), trip))
        before_swap_sha = L.sha256_file(dst_exe)
        shutil.copyfile(src_exe, dst_exe)
        in_place_sha = L.sha256_file(dst_exe)
        S.step("exe_swap", trip=trip, src=str(src_exe), dst=str(dst_exe),
               before_swap_sha=before_swap_sha, in_place_sha=in_place_sha,
               expected=expected_exe_sha,
               matches_expected=in_place_sha == expected_exe_sha,
               W61_source_unmodified=(
                   L.sha256_file(L.W61_PATCHED) == L.EXPECTED["patch_gamemd_sha"]))
        if in_place_sha != expected_exe_sha:
            raise RuntimeError("exe swap sha mismatch")

        # ---------- 1. claim per-trip lock --------------------------------
        L.lock_claim("w75", "W75 TRIP %s (%s) IN PROGRESS: sandbox gamemd.exe "
                     "sha=%s; one lock per trip" %
                     (trip, "patched exe" if trip == "A" else "original exe",
                      in_place_sha[:12]))
        locked = True
        S.step("lock_claimed", lock=L.lock_read())

        # ---------- 2. desktop precheck -----------------------------------
        pc = L.desktop_precheck(S)
        summary["desktop_precheck"] = pc

        # ---------- 3. launch ---------------------------------------------
        launcher = L.launch_game(S)
        pid = L.wait_for_pid(launcher, S, timeout_s=90)
        S.step("own_pid", pid=pid, all_gamemd=L.list_gamemd())
        summary["pid"] = pid
        time.sleep(3.0)
        S.step("early_alive_check", alive=L.process_alive(pid),
               exit_code=L.exit_code(pid),
               controls_n=len(L.controls(pid)),
               top_windows=top_window_summary(pid))
        if not L.process_alive(pid):
            S.screenshot(S, tag + "_early_crash_desktop")
            raise RuntimeError("game process died during startup (pid=%s)" % pid)

        # ---------- 4. main menu ------------------------------------------
        t0 = time.monotonic()
        hwnd = None
        while time.monotonic() - t0 < 90:
            hwnd = L.game_hwnd(pid)
            if hwnd and L.find_btn(pid, "GUI:SinglePlayer"):
                break
            if not L.process_alive(pid):
                S.screenshot(S, tag + "_menu_crash_desktop")
                raise RuntimeError("game died before main menu")
            time.sleep(0.5)
        if not hwnd or not L.find_btn(pid, "GUI:SinglePlayer"):
            S.screenshot(S, tag + "_no_main_menu_desktop")
            raise RuntimeError("main menu not reached (GUI:SinglePlayer absent)")
        S.step("main_menu_ready", hwnd=hwnd, rect=L.rect(hwnd),
               elapsed_s=round(time.monotonic() - t0, 2),
               top_windows=top_window_summary(pid))
        L.screenshot(S, tag + "_main_menu", hwnd)
        L.force_foreground(hwnd)
        if not L.click(pid, "GUI:SinglePlayer", S, wait_s=1.2,
                       label=tag + "_click_SinglePlayer"):
            raise RuntimeError("GUI:SinglePlayer click failed")
        if not wait_text(pid, "GUI:NewCampaign", 25, S,
                         retry_click="GUI:SinglePlayer", tag=tag):
            raise RuntimeError("GUI:NewCampaign not reached")
        if not L.click(pid, "GUI:NewCampaign", S, wait_s=2.0,
                       label=tag + "_click_NewCampaign"):
            raise RuntimeError("GUI:NewCampaign click failed")
        if not wait_text(pid, "GUI:CampaignMenu", 25, S,
                         retry_click="GUI:NewCampaign", tag=tag):
            raise RuntimeError("GUI:CampaignMenu not reached")
        S.step("campaign_menu_reached", hwnd=L.game_hwnd(pid),
               rect=L.rect(L.game_hwnd(pid) or hwnd))
        summary["campaign_menu_reached"] = True

        # ---------- 5. controls enumeration -------------------------------
        cs = L.controls(pid)
        csum = control_summary(cs)
        json_dump("controls_%s.json" % tag,
                  {"trip": trip, "pid": pid, "n_controls": len(cs),
                   "summary": csum, "controls": cs,
                   "top_windows": top_window_summary(pid)})
        S.step("controls_enum", tag=tag, **{k: csum[k] for k in
               ("n_controls", "n_visible", "has_1771", "count_1771",
                "n_1770", "n_1772", "ctrl_ids")})
        summary["controls"] = csum
        L.screenshot(S, tag + "_campaign_menu", L.game_hwnd(pid) or hwnd)

        # ---------- 6. hot zone geometry ----------------------------------
        hz = None
        if csum["controls_1771"]:
            hz = hotzone_from_control(csum["controls_1771"][0])
        if hz is None and csum["controls_1770"]:
            hz = hotzone_fallback_from_1770(csum["controls_1770"][0])
        if trip == "B":
            # Same screen coords as trip A (strict A/B control)
            hp = OUT / "hotzone.json"
            if hp.is_file():
                hz = json.loads(hp.read_text(encoding="utf-8"))
                hz["source"] = "tripA_hotzone_reused_for_tripB"
        if hz is None:
            raise RuntimeError("cannot determine hot-zone coords")
        if trip == "A":
            json_dump("hotzone.json", hz)
        S.step("hotzone", tag=tag, **hz)
        summary["hotzone"] = hz
        cx, cy = int(hz["cx"]), int(hz["cy"])

        # ---------- 7. memory baseline ------------------------------------
        hproc = L.open_proc(pid)
        if not hproc:
            raise RuntimeError("OpenProcess(VM_READ) failed")
        samples = []
        base = sample(S, hproc, "campaign_menu_baseline", tag, samples)
        summary["baseline"] = base

        # ---------- 8. hover -> tooltip -----------------------------------
        L.move_mouse(S, tag + "_hover", cx, cy, wait_s=2.2)
        cs_h = L.controls(pid)
        tt = tooltip_windows(pid)
        json_dump("controls_%s_hover.json" % tag,
                  {"trip": trip, "n_controls": len(cs_h),
                   "tooltip_candidates": tt, "controls": cs_h,
                   "top_windows": top_window_summary(pid)})
        S.step("hover_result", tag=tag, tooltip_candidates=tt,
               n_controls=len(cs_h),
               error_windows=error_windows(pid))
        L.screenshot(S, tag + "_hover_tooltip", L.game_hwnd(pid) or hwnd)
        L.screenshot(S, tag + "_hover_tooltip_desktop")
        hov = sample(S, hproc, "after_hover", tag, samples)
        summary["after_hover"] = hov

        # ---------- 9. click hot zone -------------------------------------
        L.real_mouse_click(S, tag + "_click_hotzone", cx, cy, wait_s=0.35)
        p0 = sample(S, hproc, "after_click_t0", tag, samples)
        time.sleep(0.8)
        p1 = sample(S, hproc, "after_click_t1", tag, samples)
        L.screenshot(S, tag + "_after_click", L.game_hwnd(pid) or hwnd)
        time.sleep(1.5)
        p2 = sample(S, hproc, "after_click_t2", tag, samples)
        time.sleep(2.0)
        p3 = sample(S, hproc, "after_click_t3", tag, samples)
        L.screenshot(S, tag + "_after_click_late", L.game_hwnd(pid) or hwnd)
        L.screenshot(S, tag + "_after_click_desktop")
        cs_a = L.controls(pid)
        ew = error_windows(pid)
        json_dump("controls_%s_after_click.json" % tag,
                  {"trip": trip, "n_controls": len(cs_a),
                   "error_windows": ew, "controls": cs_a,
                   "top_windows": top_window_summary(pid)})
        S.step("after_click_state", tag=tag,
               process_alive=L.process_alive(pid),
               exit_code=L.exit_code(pid),
               error_windows=ew,
               n_controls=len(cs_a),
               top_windows=top_window_summary(pid))
        summary["after_click"] = {"t0": p0, "t1": p1, "t2": p2, "t3": p3,
                                 "process_alive": L.process_alive(pid),
                                 "exit_code": L.exit_code(pid),
                                 "error_windows": ew,
                                 "n_controls_after": len(cs_a)}

        # ---------- 10. crash / resource-load log evidence ---------------
        logs = {}
        for n in ("except.txt", "ra2render.log"):
            p = L.GAME / n
            logs[n] = {"size": p.stat().st_size if p.is_file() else None,
                       "sha256": L.sha256_file(p) if p.is_file() else None}
        base_logs = json.loads((OUT / "log_baseline.json").read_text(
            encoding="utf-8"))
        log_changed = {n: (logs[n]["sha256"] != base_logs[n]["sha256"])
                       for n in logs}
        S.step("log_delta", tag=tag, current=logs, baseline=base_logs,
               changed=log_changed)
        summary["log_delta"] = {"current": logs, "baseline": base_logs,
                                "changed": log_changed}
        with (OUT / ("scen_readings_%s.ndjson" % tag)).open(
                "w", encoding="utf-8", newline="\n") as f:
            for row in samples:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                   default=str, separators=(",", ":")) + "\n")
        json_dump("scen_readings_%s.json" % tag, samples)
        summary["n_mem_samples"] = len(samples)
        summary["ok"] = True

    except Exception as e:
        import traceback
        S.step("TRIP_ERROR", tag=tag, error=repr(e),
               traceback=traceback.format_exc()[-2500:])
        summary["ok"] = False
        summary["error"] = repr(e)
        print("TRIP %s ERROR: %r" % (trip, e), file=sys.stderr, flush=True)
    finally:
        # ---------- 11. close ONLY our own pid ---------------------------
        try:
            if pid:
                steps = L.close_game(pid, hwnd, S)
                summary["close_steps"] = steps
                summary["residual_own_pid"] = L.process_alive(pid)
                summary["all_gamemd_after"] = L.list_gamemd()
        except Exception as e:
            S.step("CLOSE_ERROR", error=repr(e))
            summary["close_error"] = repr(e)
        # ---------- 12. byte-exact config restore ------------------------
        try:
            rows = L.restore_configs(S)
            summary["config_restore_all_match"] = all(r["match"] for r in rows)
            summary["config_restore_rows"] = rows
        except Exception as e:
            S.step("RESTORE_ERROR", error=repr(e))
            summary["restore_error"] = repr(e)
        # ---------- 13. restore sandbox exe to ORIGINAL ------------------
        try:
            shutil.copyfile(OUT / "pristine_gamemd.exe", L.GAME / "gamemd.exe")
            restored_sha = L.sha256_file(L.GAME / "gamemd.exe")
            S.step("sandbox_exe_restored_to_original",
                   sha256=restored_sha,
                   matches_real=restored_sha == L.EXPECTED["real_gamemd_sha"])
            summary["sandbox_exe_final_sha"] = restored_sha
        except Exception as e:
            S.step("EXE_RESTORE_ERROR", error=repr(e))
            summary["exe_restore_error"] = repr(e)
        # ---------- 14. always release lock back to lead -----------------
        try:
            purpose = ("W75 TRIP %s FINISHED (ok=%s, has_1771=%s, "
                       "pid=%s, self-launched gamemd closed, residual=%s; "
                       "configs byte-restored, sandbox exe=ORIGINAL; "
                       "restored owner=lead)" %
                       (trip, summary.get("ok"),
                        summary.get("controls", {}).get("has_1771"),
                        pid, summary.get("residual_own_pid")))
            L.lock_release("lead", purpose)
            S.step("lock_released", lock=L.lock_read())
            summary["lock_after"] = L.lock_read()
        except Exception as e:
            S.step("LOCK_RELEASE_ERROR", error=repr(e))
            summary["lock_release_error"] = repr(e)
        S.close()

    json_dump("TRIP_%s.json" % trip, summary)
    print("TRIP %s DONE ok=%s" % (trip, summary.get("ok")), flush=True)
    sys.exit(0 if summary.get("ok") else 2)


if __name__ == "__main__":
    main()
