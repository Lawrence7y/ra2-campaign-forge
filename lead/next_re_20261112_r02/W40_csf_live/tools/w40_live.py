#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W40 · LIVE driver: two boundaries of a loose ra2md.csf.

Test A : minimal but VALID CSF (1 label "RA2F:TEST0001")  -> W29 predicted
         startup failure with "Unable to initialize 'ra2.csf'".
Test B : full official clone + 1 appended label (5212)   -> startup + text.
Test C : negative control, NO loose ra2md.csf             -> normal startup.

Discipline (hard):
  * single instance lock claimed at start, restored owner=lead in finally
  * WMI Win32_Process.Create launch (detached)
  * step-0 desktop precheck within 30 s of the first launch; abort if it fails
  * read-only Win32 observation only (EnumWindows / ImageGrab / RPM), NO inject
  * finally: close game -> 0 residual -> byte-restore RA2MD.INI/ddraw.ini ->
    remove the loose CSF -> restore BATTLEMD98.INI -> kind=meta_end -> unlock
"""
from __future__ import annotations

import json
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

OUT = L.OUT
GAME = L.GAME
CSF_LOOSE = GAME / "ra2md.csf"
BATTLE98 = GAME / "BATTLEMD98.INI"
BATTLE98_ASBUILT = OUT / "BATTLEMD98.INI.asbuilt"
MAPSEL = GAME / "MAPSELMD.INI"
VAR_A = OUT / "ra2md.csf.minimal"
VAR_B = OUT / "ra2md.csf.full"
VARIANTS = OUT / "csf_variants.json"

OLD_DESC = b"Description=W27LIVE two-mission chain probe A1 to A2"
NEW_DESC = b"Description=RA2F:W40TEST"
MARK_B = "W40_CSF_LIVE_OK_20261113"
LABEL_B = "RA2F:W40TEST"
MARK_A = "W40A_MINIMAL_CSF_SINGLE_LABEL"
LABEL_A = "RA2F:TEST0001"
OLD_TEXT_C = "W27LIVE two-mission chain probe A1 to A2"

ERR_TOKENS = ("unable to initialize", "ra2.csf", "初始化", "初始化字串",
              "無法初始", "无法初始", "reinstall red alert")


def snap(sink: L.Sink, label: str, pid, hproc, extra: dict | None = None):
    cs = L.controls(pid)
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    rec = {"kind": "event", "step": label, "t_utc": L.utc_iso(),
           "t_local": L.local_iso(), "t_monotonic": time.monotonic(),
           "visible_control_texts": vis,
           "all_controls": [{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"],
                             "id": c["ctrl_id"]} for c in cs]}
    if extra:
        rec.update(extra)
    sink.step(label, **{k: v for k, v in rec.items()
                        if k not in ("step", "kind", "t_utc", "t_local", "t_monotonic")})
    return cs, vis


def dialog_view(pid):
    """Return (dialog_windows, visible_buttons, all_visible_texts)."""
    tops = L.top_windows(pid)
    dialogs = []
    for h in tops:
        cls = L.wcls(h)
        txt = L.wtxt(h)
        if cls == "#32770" or any(t in (txt or "").lower() for t in ERR_TOKENS):
            dialogs.append({"hwnd": int(h), "cls": cls, "title": txt,
                            "rect": L.rect(h)})
    cs = L.controls(pid)
    btns = [c for c in cs if c["cls"] == "Button" and c["visible"]]
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    return dialogs, btns, vis


def visible_controls(pid):
    cs = L.controls(pid)
    return sorted({c["text"] for c in cs if c["visible"] and c["text"]}), cs


def deploy_csf(variant: Path, sink: L.Sink, tag: str):
    shutil.copyfile(variant, CSF_LOOSE)
    sink.step("deploy_loose_csf", tag=tag, variant=str(variant),
              deployed_path=str(CSF_LOOSE),
              sha256=L.sha256_file(CSF_LOOSE),
              bytes=CSF_LOOSE.stat().st_size,
              source_sha256=L.sha256_file(variant))


def set_desc_to_our_label(sink: L.Sink, tag: str):
    raw = BATTLE98.read_bytes()
    assert raw.count(OLD_DESC) == 1, "unexpected BATTLEMD98.INI asbuilt"
    new = raw.replace(OLD_DESC, NEW_DESC, 1)
    BATTLE98.write_bytes(new)
    sink.step("battle98_description_rewritten", tag=tag,
              old=OLD_DESC.decode("latin-1"), new=NEW_DESC.decode("latin-1"),
              before_sha256=L.sha256_file(BATTLE98_ASBUILT),
              after_sha256=L.sha256_file(BATTLE98), bytes=len(new))


def restore_one(sink: L.Sink, tag: str):
    rows = []
    # 1. remove the loose CSF we deployed (it did NOT exist in the baseline)
    try:
        existed = CSF_LOOSE.is_file()
        if existed:
            CSF_LOOSE.unlink()
        rows.append({"file": "ra2md.csf", "removed": existed,
                     "still_present": CSF_LOOSE.is_file()})
    except Exception as e:
        rows.append({"file": "ra2md.csf", "error": repr(e)})
    # 2. byte-restore BATTLEMD98.INI
    try:
        if BATTLE98_ASBUILT.is_file():
            BATTLE98.write_bytes(BATTLE98_ASBUILT.read_bytes())
        rows.append({"file": "BATTLEMD98.INI",
                     "sha256": L.sha256_file(BATTLE98),
                     "expected": L.sha256_file(BATTLE98_ASBUILT),
                     "byte_identical": BATTLE98.read_bytes() == BATTLE98_ASBUILT.read_bytes()})
    except Exception as e:
        rows.append({"file": "BATTLEMD98.INI", "error": repr(e)})
    # 3. byte-restore RA2MD.INI / ddraw.ini / benchbak + verify exe/dll
    try:
        cfg = L.restore_configs(sink)
        rows.append({"file": "restore_configs", "rows": cfg})
    except Exception as e:
        rows.append({"file": "restore_configs", "error": repr(e)})
    # 4. loose MAPSELMD.INI is a CONSTANT of this sandbox; record only
    rows.append({"file": "MAPSELMD.INI", "sha256":
                 L.sha256_file(MAPSEL) if MAPSEL.is_file() else None,
                 "unchanged_expected":
                 "11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886"})
    sink.step("restore_after_test", tag=tag, rows=rows,
              gamemd_residual=L.list_gamemd())
    return rows


def run_one(tag: str, variant: Path | None, change_desc: bool,
            needles: list[str], meta_sink: L.Sink) -> dict:
    sink = L.Sink(tag)
    state = {"pid": None, "hwnd": None, "hproc": None, "launcher": None}
    result = {"tag": tag, "variant": str(variant) if variant else None,
              "change_desc": change_desc}
    sink.step("run_start", kind="meta_start", tag=tag,
              desktop_probe_json=str(OUT / "desktop_probe_standalone.json"),
              mapsel_sha256=(L.sha256_file(MAPSEL) if MAPSEL.is_file() else None),
              loose_csf_before=CSF_LOOSE.is_file(),
              battle98_sha256_before=L.sha256_file(BATTLE98),
              csf_variants_json=str(VARIANTS))
    try:
        # ---- pre-launch guard -------------------------------------------
        pre = L.list_gamemd()
        sink.step("pre_launch_guard", tag=tag, gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch: %r" % pre)

        # ---- deploy ------------------------------------------------------
        if variant is not None:
            deploy_csf(variant, sink, tag)
        if change_desc:
            set_desc_to_our_label(sink, tag)
        sink.step("deploy_done", tag=tag,
                  loose_csf_present=CSF_LOOSE.is_file(),
                  loose_csf_sha256=(L.sha256_file(CSF_LOOSE)
                                    if CSF_LOOSE.is_file() else None),
                  battle98_sha256=L.sha256_file(BATTLE98))

        # ---- WMI launch --------------------------------------------------
        launcher = L.launch_game(sink)
        state["launcher"] = launcher
        pid = L.wait_for_pid(launcher, sink, timeout_s=90)
        state["pid"] = pid
        result["pid"] = pid
        # open the handle EARLY so GetExitCodeProcess works after the process
        # exits naturally (we want the real exit code, not a taskkill code).
        hproc = L.open_proc(pid)
        state["hproc"] = hproc
        sink.step("proc_handle", tag=tag, hproc=bool(hproc))

        # ---- STEP 0: desktop precheck (within 30 s of launch) -----------
        t_launch = time.monotonic()
        precheck = L.desktop_precheck(sink)
        result["desktop_precheck"] = precheck
        result["precheck_elapsed_s"] = round(time.monotonic() - t_launch, 2)
        meta_sink.step("step0_precheck_result", tag=tag, **precheck)
        if not precheck.get("pass"):
            # HARD GATE: W35 died on an isolated desktop. Stop the whole card,
            # do not burn time on A/B/C. The outer finally still self-heals.
            raise RuntimeError("STEP0_ABORT_DESKTOP_BLOCKED: %s"
                               % json.dumps(precheck, ensure_ascii=False))

        # ---- wait for game window / outcome ------------------------------
        hwnd = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 45:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        state["hwnd"] = hwnd
        sink.step("game_window", tag=tag, hwnd=hwnd,
                  title=L.wtxt(hwnd) if hwnd else None,
                  rect=L.rect(hwnd) if hwnd else None,
                  elapsed_s=round(time.monotonic() - t0, 2))

        outcome = None
        dialog_rec = None
        t1 = time.monotonic()
        while time.monotonic() - t1 < 70:
            if not L.process_alive(pid):
                outcome = "process_exited_without_main_menu"
                break
            dialogs, btns, vis = dialog_view(pid)
            hit_err = [v for v in vis
                       if any(t in (v or "").lower() for t in ERR_TOKENS)]
            if dialogs or hit_err:
                outcome = "error_dialog"
                dialog_rec = {
                    "dialog_windows": dialogs,
                    "visible_buttons": [{"hwnd": b["hwnd"], "text": b["text"],
                                         "rect": b["rect"]} for b in btns],
                    "visible_control_texts": vis,
                    "err_text_hits": hit_err,
                }
                sink.step("error_dialog_detected", tag=tag, **dialog_rec)
                # full-screen screenshot: a MessageBox can sit outside the
                # game window rect
                try:
                    L.screenshot(sink, "%s_error_dialog_fullscreen" % tag)
                except Exception as e:
                    sink.step("screenshot_error", tag=tag, error=repr(e))
                if hwnd:
                    try:
                        L.screenshot(sink, "%s_error_dialog_gamewnd" % tag, hwnd)
                    except Exception as e:
                        sink.step("screenshot_error_game", tag=tag, error=repr(e))
                break
            if L.find_btn(pid, "GUI:SinglePlayer"):
                outcome = "main_menu_ready"
                break
            time.sleep(1.0)
        if outcome is None:
            outcome = "observation_timeout"
        result["outcome"] = outcome
        result["dialog"] = dialog_rec
        sink.step("startup_outcome", tag=tag, outcome=outcome,
                  elapsed_s=round(time.monotonic() - t1, 2),
                  pid=pid, process_alive=L.process_alive(pid))

        # ---- main-menu / error-detail observation ------------------------
        if outcome == "main_menu_ready":
            if hwnd:
                L.force_foreground(hwnd)
            snap(sink, "S0_main_menu", pid, hproc)
            L.screenshot(sink, "%s_main_menu" % tag, hwnd)
            # memory search (read-only RPM) for our markers / MISSING:
            try:
                m = L.memory_search(hproc, needles, sink, "%s_startup_memory" % tag)
                result["memory_hits"] = {k: v["count"] for k, v in m["hits"].items()}
                result["memory_samples"] = m["hits"]
            except Exception as e:
                sink.step("memory_search_error", tag=tag, error=repr(e))

            if tag.startswith("w40_B"):
                # walk into the campaign menu to look for the label text in UI
                L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.5,
                        label="click_SinglePlayer")
                L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                        label="click_NewCampaign")
                vis, cs = visible_controls(pid)
                sink.step("S2_campaign_menu", tag=tag, visible_control_texts=vis,
                          all_controls=[{"cls": c["cls"], "text": c["text"],
                                         "vis": c["visible"]} for c in cs])
                L.screenshot(sink, "%s_campaign_menu" % tag, hwnd)
                try:
                    m2 = L.memory_search(hproc, needles, sink,
                                         "%s_campaign_memory" % tag)
                    result["campaign_memory_hits"] = {
                        k: v["count"] for k, v in m2["hits"].items()}
                    result["campaign_memory_samples"] = m2["hits"]
                except Exception as e:
                    sink.step("memory_search_error_campaign", tag=tag,
                              error=repr(e))
            elif tag.startswith("w40_C"):
                # negative control: also enter campaign menu for a MISSING: baseline
                L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.5,
                        label="click_SinglePlayer")
                L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                        label="click_NewCampaign")
                vis, cs = visible_controls(pid)
                sink.step("S2_campaign_menu_control", tag=tag,
                          visible_control_texts=vis)
                L.screenshot(sink, "%s_campaign_menu" % tag, hwnd)
        elif outcome == "error_dialog":
            # try to let the game EXIT NATURALLY, then read its exit code
            L.dismiss_dialog(pid, sink, "%s_dismiss_error_dialog" % tag)
            exited, elapsed = L.wait_process_exit(pid, timeout_s=20.0)
            code = L.get_exit_code(hproc)
            result["natural_exit"] = exited
            result["natural_exit_wait_s"] = elapsed
            result["exit_code"] = code
            result["exit_code_still_active"] = (code == L.STILL_ACTIVE)
            sink.step("natural_exit_and_exit_code", tag=tag,
                      exited=exited, wait_s=elapsed, exit_code=code,
                      still_active=(code == L.STILL_ACTIVE),
                      process_alive=L.process_alive(pid))
        elif outcome == "process_exited_without_main_menu":
            code = L.get_exit_code(hproc)
            result["exit_code"] = code
            result["process_exited"] = True
            sink.step("process_exited_exit_code", tag=tag, exit_code=code,
                      process_alive=L.process_alive(pid))

        # ---- capture loose CSF state AFTER the run ------------------------
        result["loose_csf_after_sha256"] = (L.sha256_file(CSF_LOOSE)
                                            if CSF_LOOSE.is_file() else None)
        result["battle98_sha256_after"] = L.sha256_file(BATTLE98)
        sink.step("run_outcome", tag=tag, outcome=outcome, result=result)
    except Exception as e:
        result["fatal"] = repr(e)
        sink.step("FATAL", tag=tag, error=repr(e),
                  traceback=traceback.format_exc()[-4000:])
    finally:
        # close only OUR pid, then byte-restore everything we touched
        pid = state.get("pid")
        hwnd = state.get("hwnd")
        hproc = state.get("hproc")
        try:
            if pid:
                L.close_game(pid, hwnd, sink)
        except Exception as e:
            sink.step("close_error", tag=tag, error=repr(e))
        # residual check AFTER close
        residual = L.list_gamemd()
        result["gamemd_residual_after_close"] = residual
        sink.step("residual_after_close", tag=tag, residual=residual)
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            restore_one(sink, tag)
        except Exception as e:
            sink.step("restore_error", tag=tag, error=repr(e))
        sink.step("meta_end", kind="meta_end", tag=tag, outcome=result.get("outcome"),
                  gamemd_residual=L.list_gamemd(),
                  loose_csf_present=CSF_LOOSE.is_file(),
                  battle98_sha256=L.sha256_file(BATTLE98))
        sink.close()
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = L.Sink("w40_meta")
    meta.step("card_start", kind="meta_start",
              card="W40_csf_live",
              game=str(GAME), real_dir=str(L.ROOT / "ra2youli"),
              variants=str(VARIANTS),
              lock_before=L.LOCK.read_text(encoding="utf-8") if L.LOCK.is_file() else None)
    results = []
    try:
        L.lock_claim("w40", "W40 csf live card running (3 serial game instances)")
        meta.step("lock_claimed", owner="w40",
                  lock_text=L.LOCK.read_text(encoding="utf-8"))

        # A: minimal valid CSF
        results.append(run_one(
            "w40_A_minimal", VAR_A, False,
            [MARK_A, LABEL_A, "MISSING", "MISSING:", "DESC:ALL1",
             "GUI:MainMenu"], meta))
        if any("STEP0_ABORT" in str(r.get("fatal", "")) for r in results):
            meta.step("card_aborted", reason="STEP0 desktop visibility gate failed")
            raise RuntimeError("STEP0_ABORT_DESKTOP_BLOCKED (card stopped)")
        # B: full clone + appended label, with BATTLEMD98.INI pointing at it
        results.append(run_one(
            "w40_B_full", VAR_B, True,
            [MARK_B, LABEL_B, "MISSING", "MISSING:", "W27LIVE",
             "DESC:ALL1", "W40_CSF_LIVE_OK_20261113"], meta))
        if any("STEP0_ABORT" in str(r.get("fatal", "")) for r in results):
            meta.step("card_aborted", reason="STEP0 desktop visibility gate failed")
            raise RuntimeError("STEP0_ABORT_DESKTOP_BLOCKED (card stopped)")
        # C: negative control - no loose CSF at all
        results.append(run_one(
            "w40_C_nocsf", None, False,
            ["MISSING", "MISSING:", OLD_TEXT_C, "DESC:ALL1",
             "W27LIVE"], meta))
    except Exception as e:
        meta.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        # ---- global self-heal -------------------------------------------
        heal = []
        try:
            for r in L.list_gamemd():
                pid = r["pid"]
                heal.append({"pid": pid, "action": "taskkill /F"})
                L.close_game(pid, None, meta)
        except Exception as e:
            heal.append({"error": repr(e)})
        try:
            if CSF_LOOSE.is_file():
                CSF_LOOSE.unlink()
        except Exception as e:
            heal.append({"csf_remove_error": repr(e)})
        try:
            if BATTLE98_ASBUILT.is_file():
                BATTLE98.write_bytes(BATTLE98_ASBUILT.read_bytes())
        except Exception as e:
            heal.append({"battle98_restore_error": repr(e)})
        try:
            cfg = L.restore_configs(meta)
            heal.append({"restore_configs": cfg})
        except Exception as e:
            heal.append({"restore_configs_error": repr(e)})
        final = {
            "gamemd_residual": L.list_gamemd(),
            "loose_ra2md_csf_present": CSF_LOOSE.is_file(),
            "RA2MD_INI_sha256": L.sha256_file(GAME / "RA2MD.INI"),
            "ddraw_ini_sha256": L.sha256_file(GAME / "ddraw.ini"),
            "BATTLEMD98_INI_sha256": L.sha256_file(BATTLE98),
            "MAPSELMD_INI_sha256": (L.sha256_file(MAPSEL) if MAPSEL.is_file() else None),
        }
        meta.step("final_self_heal", heal=heal, **final)
        meta.step("meta_end", kind="meta_end", card="W40_csf_live",
                  results=[{k: r.get(k) for k in
                            ("tag", "outcome", "exit_code", "fatal",
                             "gamemd_residual_after_close", "desktop_precheck")}
                           for r in results], **final)
        L.lock_restore_lead()
        meta.step("lock_restored", owner="lead",
                  lock_text=L.LOCK.read_text(encoding="utf-8"))
        meta.close()

    (OUT / "live_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8")
    print(json.dumps([{k: r.get(k) for k in
                       ("tag", "outcome", "exit_code", "fatal",
                        "pid", "gamemd_residual_after_close")}
                      for r in results], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
