#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P2a DIAGNOSTIC D1 (NOT the as-built package).

Changes ONLY the sandbox BATTLEMD98.INI Description line from the builder's
free text to the engine's known-good CSF label DESC:ALL1, then relaunches to
see whether the appended campaign becomes a visible/selectable menu entry.
The file is restored byte-exactly at the end and `verify` is re-run.
All observations are read-only (window/control text + bounded RPM + passive
screen capture). One serial instance, closed and restored at the end.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

INI = L.GAME / "BATTLEMD98.INI"
ORIG = L.OUT / "BATTLEMD98.INI.asbuilt"
DIAG = L.OUT / "BATTLEMD98.INI.D1_desc_all1"


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2))
            return
        time.sleep(2.0)
    raise RuntimeError("main menu timeout")


def main():
    sink = L.Sink("p2a_D1_diagnostic")
    pid = hwnd = hproc = None
    try:
        raw = INI.read_bytes()
        ORIG.write_bytes(raw)
        sink.step("D1_setup", original_sha256=L.sha256_file(INI),
                  original_bytes=len(raw),
                  original_line=[l for l in raw.split(b"\r\n")
                                 if l.startswith(b"Description=")])
        modified = raw.replace(
            b"Description=W27LIVE two-mission chain probe A1 to A2",
            b"Description=DESC:ALL1")
        if modified == raw:
            raise RuntimeError("D1 replacement did not match; aborting")
        INI.write_bytes(modified)
        DIAG.write_bytes(modified)
        sink.step("D1_file_written", sha256=L.sha256_file(INI),
                  bytes=len(modified),
                  new_line=[l for l in modified.split(b"\r\n")
                            if l.startswith(b"Description=")],
                  note="sandbox-only diagnostic; NOT the as-built package")

        pre = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch; STOP per card")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        hproc = L.open_proc(pid)
        wait_main_menu(pid, sink)
        L.force_foreground(hwnd)
        cb = L.rpm(hproc, 0x00A83D08, 4)
        sink.step("battle_table_count_D1",
                  count=int.from_bytes(cb, "little") if cb else None)
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="to_SP")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="to_CampaignMenu")
        cs = L.snap(pid, sink, "D1_campaign_menu")
        L.screenshot(sink, "p2a_D1_campaign_menu", hwnd)
        r = L.memory_search(hproc, ["W27LIVE", "MISSING:", "DESC:ALL1",
                                    "DESC:SOV1", "RA2F1", "ECH01.MAP",
                                    "W27 A1"], sink, "D1_memory")
        sink.step("D1_verdict_data",
                  static_controls=[{"rect": c["rect"], "text": c["text"]}
                                   for c in cs if c["cls"] == "Static"],
                  visible_buttons=[c["text"] for c in cs
                                   if c["cls"] == "Button" and c["visible"]],
                  missing_w27live_count=r["hits"]["W27LIVE|utf16le"]["count"])
        # mouse-wheel scroll over the two panels (passive targeting)
        L.real_mouse_click(sink, "D1_noop_focus", 210, 285, wait_s=0.2)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            L.close_game(pid, hwnd, sink)
        except Exception as e:
            sink.step("close_error", error=repr(e))
        try:
            if ORIG.is_file():
                INI.write_bytes(ORIG.read_bytes())
            sink.step("D1_restore", sha256=L.sha256_file(INI),
                      original_sha256=L.sha256_file(ORIG),
                      byte_identical=INI.read_bytes() == ORIG.read_bytes())
        except Exception as e:
            sink.step("D1_restore_error", error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p2a_done", gamemd_residual=L.list_gamemd())
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
