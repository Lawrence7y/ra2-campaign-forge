#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 diagnostic arm D_CSF_POS (positive control, NOT part of the v12 chain).

Question: when OUR text is put on an OFFICIAL label that DOES have a rendered
UI slot, does it render? If yes while the main arm did not render it, then the
negative campaign-menu verdict is not "CSF did not load" but "the appended
campaign's Description has no rendered slot".

Overrides two known-visible official labels in a TEMPORARY loose ra2md.csf:
  * GUI:SinglePlayer  (W40 E-arm proved this renders on main-menu button 1)
  * DESC:SOV1         (official Soviet campaign blurb under the badge)
The installed v12 ra2md.csf is saved and restored BYTE-EXACTLY afterwards,
then verify --json must be exit 0 again.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "csf_control"
INSTALLED_BAK = C.OUT / "ra2md.csf.installed"
VARIANT = C.OUT / "ra2md.csf.poscontrol"


def crop(sink, src_label, box, scale, out_label):
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
                             "vis": c["visible"], "rect": c["rect"]} for c in cs])
    return cs, cnt, vis


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
    t0 = time.monotonic()
    while time.monotonic() - t0 < 120:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready",
                      elapsed_s=round(time.monotonic() - t0, 2))
            break
        time.sleep(1.5)
    L.force_foreground(hwnd)
    sink.step("instance_ready", tag=tag, pid=pid, hwnd=hwnd,
              rect=L.rect(hwnd) if hwnd else None)
    return pid, hwnd, hproc


def make_variant(sink):
    """Build a complete-CSF variant with two official labels overridden."""
    sys.path.insert(0, str(C.V12))
    from ra2forge import csf as csf_mod
    data = csf_mod.read_csf(INSTALLED_BAK, strict=True)
    before = {}
    for name in ("GUI:SinglePlayer", "DESC:SOV1", "DESC:ALL1", "RA2F:942506FC"):
        lbl = data.get_label(name, case_insensitive=True)
        before[name] = {"present": lbl is not None,
                        "value": lbl.text if lbl is not None else None}
    sink.step("official_labels_before", labels=before,
              num_labels=data.num_labels)
    changed = []
    for name in ("GUI:SinglePlayer", "DESC:SOV1"):
        lbl = data.get_label(name, case_insensitive=True)
        if lbl is None:
            sink.step("label_missing", label=name)
            continue
        # keep the original value KIND/extra; only replace the text
        lbl.values[0].text = C.CSF_TEXT
        changed.append(name)
    sink.step("variant_labels_changed", changed=changed)
    csf_mod.write_csf(VARIANT, data, require_complete=True)
    chk = csf_mod.read_csf(VARIANT, strict=True)
    sink.step("variant_written", path=str(VARIANT), size=VARIANT.stat().st_size,
              sha256=L.sha256_file(VARIANT), num_labels=chk.num_labels,
              gui_singleplayer=chk.get("GUI:SinglePlayer", case_insensitive=True),
              desc_sov1=chk.get("DESC:SOV1", case_insensitive=True),
              baseline_labels=csf_mod.assert_complete_csf(chk)["baseline_labels"])
    return changed


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None}
    ok = False
    restored = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="diagnostic arm; NOT the v12 package chain",
                  csf_text=C.CSF_TEXT)
        csf_game = C.GAME / "ra2md.csf"
        INSTALLED_BAK.write_bytes(csf_game.read_bytes())
        sink.step("installed_csf_saved", sha256=L.sha256_file(INSTALLED_BAK),
                  size=INSTALLED_BAK.stat().st_size)
        changed = make_variant(sink)
        csf_game.write_bytes(VARIANT.read_bytes())
        sink.step("variant_deployed", sha256=L.sha256_file(csf_game),
                  size=csf_game.stat().st_size)

        pid, hwnd, hproc = launch_one(sink, "K3", state)
        snap(pid, hproc, sink, "K3_S0_main_menu")
        L.screenshot(sink, "w44_ctrl_S0_main_menu", hwnd)
        crop(sink, "w44_ctrl_S0_main_menu", (0, 0, 800, 600), 2,
             "w44_ctrl_main_menu_content2x")
        m0 = L.memory_search(hproc, [C.CSF_TEXT, "GUI:SinglePlayer", "MISSING:"],
                             sink, "K3_main_menu_memory")

        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                label="K3_click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                label="K3_click_NewCampaign")
        cs, cnt, vis = snap(pid, hproc, sink, "K3_campaign_menu")
        L.screenshot(sink, "w44_ctrl_campaign_menu", hwnd)
        crop(sink, "w44_ctrl_campaign_menu", (0, 0, 860, 620), 3,
             "w44_ctrl_campaign_menu_content3x")
        mc = L.memory_search(hproc, [C.CSF_TEXT, "DESC:SOV1", "MISSING:"],
                             sink, "K3_campaign_menu_memory")
        sink.step("K3_csf_judgment_inputs",
                  note="display verdict MUST come from screenshots; control "
                       "texts only establish control presence/visibility",
                  visible_control_texts=vis,
                  csf_text_utf16_count=mc["hits"].get(C.CSF_TEXT + "|utf16le", {}).get("count"),
                  csf_text_ascii_count=mc["hits"].get(C.CSF_TEXT + "|ascii", {}).get("count"),
                  missing_count=mc["hits"].get("MISSING:|ascii", {}).get("count"),
                  labels_changed=changed)
        ok = True
        sink.step("K3_result", ok=ok)
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
        # byte-exact restore of the installed v12 CSF
        try:
            csf_game = C.GAME / "ra2md.csf"
            csf_game.write_bytes(INSTALLED_BAK.read_bytes())
            restored = (csf_game.read_bytes() == INSTALLED_BAK.read_bytes())
            sink.step("installed_csf_restored", sha256=L.sha256_file(csf_game),
                      expected=L.sha256_file(INSTALLED_BAK),
                      byte_identical=restored)
            v = C.v12_cmd(sink, "verify_after_csf_control",
                          ["verify", "--game", str(C.GAME), "--json"])
            sink.step("verify_after_csf_control_exit", exit_code=v["exit_code"],
                      stdout_tail=v["stdout_tail"][-2500:])
        except Exception as e:
            sink.step("restore_csf_error", error=repr(e))
        try:
            C.heal(sink, label="K3_finally")
        except Exception as e:
            sink.step("heal_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  csf_restored=restored,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if (ok and restored) else 1


if __name__ == "__main__":
    raise SystemExit(main())
