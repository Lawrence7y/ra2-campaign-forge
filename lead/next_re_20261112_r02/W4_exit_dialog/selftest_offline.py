# -*- coding: utf-8 -*-
"""W4 离线自检 v2：不启动游戏、不碰任何进程，只验证纯逻辑
（classify_button / detect_dialog / analyze_verdict / render_*）。
适配当前 exit_dialog_probe.py 的 API（w3-import 版）。"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
W4 = ROOT / "lead" / "next_re_20261112_r02" / "W4_exit_dialog"
W3_PATH = (ROOT / "lead" / "next_re_20261112_r02" / "W3_stack_contrast"
           / "stack_contrast.py")


def load_module(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m = load_module("w4mod", W4 / "exit_dialog_probe.py")
w3 = load_module("w4self_w3", W3_PATH)
m.w3 = w3                      # analyze_verdict 依赖 w3.KEY_POINTS

fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(extra) if extra else ""))
    if not cond:
        fails.append(name)


# 1) classify_button
check("cb_no", m.classify_button("否(N)") == "no")
check("cb_no2", m.classify_button("Cancel") == "no")
check("cb_yes", m.classify_button("是(Y)") == "yes")
check("cb_abort", m.classify_button("GUI:AbortMission") == "abort")
check("cb_none", m.classify_button("GUI:ResumeMission") is None)

# 2) detect_dialog（合成 enum_ui 形状）
def ctrl(h, cls, text, vis=True, tid=7, top=100):
    return {"hwnd": h, "cls": cls, "text": text, "visible": vis,
            "parent_hwnd": top, "top_hwnd": top,
            "top_cls": "Yuri's Revenge", "top_text": "RA2", "top_tid": tid}


def btn(h, text, vis=True):
    return ctrl(h, "Button", text, vis)


def ui_of(tops, ctrls):
    return {"t_utc_iso": "", "t_perf_ns": 0, "tops": tops, "controls": ctrls,
            "buttons": [c for c in ctrls if c["cls"] == "Button"]}


main_ui = ui_of([{"hwnd": 100, "cls": "Yuri's Revenge", "text": "RA2",
                  "visible": True, "tid": 7}],
                [btn(101, "GUI:ResumeMission")])
menu_ui = ui_of([{"hwnd": 100, "cls": "Yuri's Revenge", "text": "RA2",
                  "visible": True, "tid": 7}],
                [btn(101, "GUI:ResumeMission"), btn(102, "GUI:AbortMission"),
                 btn(103, "GUI:Restart")])
msgbox_ui = ui_of([{"hwnd": 100, "cls": "Yuri's Revenge", "text": "RA2",
                    "visible": True, "tid": 7},
                   {"hwnd": 200, "cls": "#32770", "text": "退出",
                    "visible": True, "tid": 7}],
                  [btn(101, "GUI:ResumeMission", vis=False),
                   btn(201, "是(Y)", vis=False), btn(202, "否(N)"),
                   btn(203, "是(Y)")])

d_menu = m.detect_dialog(main_ui, menu_ui)
check("det_menu_false", d_menu["dialog_present"] is False, d_menu["reason"])
d_msg = m.detect_dialog(main_ui, msgbox_ui)
check("det_msgbox_true", d_msg["dialog_present"] is True, d_msg["reason"])
check("det_no_btn", len(d_msg["no_buttons"]) == 1 and "否" in d_msg["no_buttons"][0]["text"])
check("det_yes_btn", len(d_msg["yes_buttons"]) == 1)
check("det_new_top", len(d_msg["new_top_windows"]) == 1)
check("det_tids", d_msg["dialog_tids"] == [7], d_msg["dialog_tids"])
check("cb_accel_no", m.classify_button("no(&N)") == "no")
check("cb_accel_yes", m.classify_button("是(Y)") == "yes")

# 3) analyze_verdict
base = w3.load_baseline()
base_norms = [f["norm"] for f in base["frames"]]
d0_norms = ["ntdll.dll+0x7858c", "KERNELBASE.dll+0x16a1f0",
            "KERNELBASE.dll+0x16a18f", "gamemd.exe+0x15e332"]
esc_norms = ["win32u.dll+0x11ac", "USER32.dll+0xc7f51", "DDRAW.dll+0x22b06",
             "gamemd.exe+0x13eb1c", "gamemd.exe+0x111111", "gamemd.exe+0x222222"]


def mk_grab(label, norms, usable=True, g4=0, fb=100, fa=100):
    frames = [{"idx": i, "addr": 0, "addr_hex": hex(0), "name": n,
               "module": None, "offset": None, "offset_hex": None,
               "norm": w3.norm_frame(n)} for i, n in enumerate(norms)]
    s = {"frame": fa, "g1": 0, "g2": 0, "g3": 0, "g4": g4, "mode_A8B238": 4,
         "ingame_A8E9A0": 1, "latch_ABCD58": 0, "exitstate": 0,
         "all_gates_zero": (g4 == 0), "any_gate_nonzero": (g4 != 0)}
    return {"label": label, "tid": 7, "usable": usable, "n_frames": len(norms),
            "frames": frames, "stackwalk_end_reason": "normal_end_of_walk",
            "walk_reaches_baseline_depth": len(norms) >= 7,
            "frame_before": fb, "frame_after": fa,
            "frame_delta_during_grab": fa - fb,
            "sentinels_at_grab": dict(s), "sentinels_after_grab": dict(s),
            "prev_count": 0, "resume_ret": 1, "resume_ok": True,
            "sample_state": "resume_verified_ok", "resume_state": "verified_ok",
            "errors": [], "hold_exceeded_50ms": False, "budget_exceeded_r2": False,
            "clean_restore_no_residual_suspend": True,
            "timing_ns": {"context_ns": 1, "walk_ns": 2, "resume_ns": 3,
                          "suspend_held_ns": 1000, "end_to_end_ns": 5000}}


p3_ok = {"frame_a": 104, "frame_b": 104, "delta": 0, "stopped": True,
         "g4_a": 1, "g4_b": 1, "interval_s": 1.0}
p4_ok = {"close_action": {"method": "BM_CLICK by control text"}, "resumed": True,
         "delta_frame": 9, "resumed_after_extra_action": False, "interval_s": 1.0}
trig_ok = [{"attempt": 1, "method": "Alt+F4", "dialog_present": True, "reason": "no=1 yes=1"}]
dlg_meta = {"successful_method": "Alt+F4", "stable": True, "evidence_summary": None}

grabs_ok = [mk_grab("D0", d0_norms, fb=100, fa=104),
            mk_grab("D1a", base_norms, g4=1, fb=104, fa=104),
            mk_grab("D1b", base_norms, g4=1, fb=104, fa=104),
            mk_grab("D1c", base_norms, g4=1, fb=104, fa=104),
            mk_grab("D2", esc_norms, fb=104, fa=113)]
ana = m.analyze_verdict(base, grabs_ok, p3_ok, p4_ok, trig_ok, dlg_meta)
check("ana_P1", ana["p1"]["status"] == "成立", ana["p1"])
check("ana_P2", ana["p2"]["status"] == "成立", ana["p2"]["value"])
check("ana_P3", ana["p3"]["status"] == "成立")
check("ana_P4", ana["p4"]["status"] == "成立")
check("ana_tier_proved", ana["tier"] == "[已证]", ana["tier"])
check("ana_d1x_filter", "D1x" not in ana["usable_d1_labels"])

grabs_ref = [mk_grab("D0", d0_norms, fb=100, fa=104),
             mk_grab("D1a", esc_norms, g4=0, fb=104, fa=104)]
ana2 = m.analyze_verdict(base, grabs_ref, dict(p3_ok, g4_a=0, g4_b=0),
                         p4_ok, trig_ok, dlg_meta)
check("ana_tier_refute", ana2["tier"] == "[否证]", ana2["tier"] + " " + ana2["tier_reason"])

grabs_nt = [mk_grab("D0", d0_norms, fb=100, fa=104)]
ana3 = m.analyze_verdict(base, grabs_nt, None, None,
                         [{"attempt": 1, "method": "Alt+F4", "dialog_present": False,
                           "reason": "no=0 yes=0"}],
                         {"successful_method": None, "stable": False,
                          "evidence_summary": None})
check("ana_tier_unverified", ana3["tier"] == "[未证实]", ana3["tier"])

# 4) render smoke
try:
    txt = m.render_verdict(base, grabs_ok, ana,
                           {"pid": 1, "is32": True, "map": {"display_name": "x"},
                            "self_tid": 9})
    check("render_verdict", "预测量逐条判定" in txt and "总档" in txt)
except Exception as e:                                          # noqa: BLE001
    check("render_verdict", False, repr(e))
try:
    m.render_safety(grabs_ok, 50.0, {"self_tid": 9}, False)
    m.render_config_restore({"RA2MD.INI": {"bytes": 1, "sha256": "a", "match": True}},
                            [], [], [], {"added": [], "removed": [], "changed": []},
                            [], [], (0, 0))
    m.render_runlog({"residual_before": [], "prelaunch_match_all": True,
                      "close_steps": [], "residual_after": [],
                      "map": {"display_name": "x"}, "args": {}},
                     0, "a", "b", "c", trig_ok)
    m.render_uncovered({"residual_before": [], "map": {}}, grabs_ok, ana)
    check("render_others", True)
except Exception as e:                                          # noqa: BLE001
    check("render_others", False, repr(e))

print("RESULT: %s" % ("ALL PASS" if not fails else "FAILS=%s" % fails))
sys.exit(0 if not fails else 1)
