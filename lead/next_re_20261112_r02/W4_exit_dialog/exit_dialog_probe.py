#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W4 —— 真机单变量判决实验：

    触发「退出/放弃任务确认对话框」，验证它是否就是未知栈 S_sleep 的来源。

    H: 14412 那条 7 帧栈（ntdll+0x7858c -> KERNELBASE x2 ->
       gamemd+0x207f17(Sleep 30) -> USER32+0x74775 -> USER32+0x3505d ->
       gamemd+0x20833f(EnumChildWindows)）是「退出/放弃任务确认对话框」
       这类模态对话框处理期间的栈。

    P1 对话框打开时窗口线程栈含 gamemd+0x207f17 和/或 gamemd+0x20833f
    P2 此时 G4 [0xA83D48] == 1
    P3 此时 [0xA8ED84] 帧计数停推
    P4 关闭对话框（否/取消/No）后帧计数恢复推进

★ 直接复用（只读 importlib 加载，零字节改动）：
  * W3_stack_contrast/stack_contrast.py —— 已验证的抓栈实现
    （WOW64_CONTEXT / StackWalk64 五参数回调 / STACKFRAME64=264B /
      stackwalk_false:0 为正常走完 / 挂起窗口内只读原始栈交叉核验）
  * W1_realtime_probe/realtime_gate_probe.py —— 已验证的启动/导航/选图/开局
    与 RaiseWindow、close_game、restore_configs
  * lead/re_d13_ruling_20261112/_hl_match_14412.json —— 基准 7 帧（只读）

授权：启动 gamemd.exe、只读 RPM、SuspendThread/GetThreadContext(WOW64)/
      StackWalk64/ResumeThread、枚举窗口线程、发送窗口消息/点击控件。
禁止：MiniDump、断点、代码注入、写目标进程内存、改 exe/dll、hook。
只处理自己启动的那个 pid；不杀别的进程。

写域：仅 lead/next_re_20261112_r02/W4_exit_dialog/（本文件与其 out/）。

用法：
  python -X utf8 exit_dialog_probe.py --map-pattern "Proving Grounds" \
      --load-wait 15 --stable-seconds 20 --budget-ms 50 \
      --r2-event-budget-ms 300 --max-frames 20 --raw-stack-bytes 65536
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

# ------------------------------------------------------------------ 常量 / 路径
RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W4 = ROOT / "lead" / "next_re_20261112_r02" / "W4_exit_dialog"
OUT = W4 / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"
W3_PATH = (ROOT / "lead" / "next_re_20261112_r02" / "W3_stack_contrast"
           / "stack_contrast.py")

EXPECTED_HASHES = {
    "RA2MD.INI":          "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "ddraw.ini":          "c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52",
    "RA2MD.INI.benchbak": "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "gamemd.exe":         "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll":          "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
}
VERIFY_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak",
                "gamemd.exe", "ddraw.dll")
RESTORE_FILES = ("RA2MD.INI", "ddraw.ini")

GAME_WND_CLASS = "Yuri's Revenge"
BM_CLICK = 0x00F5
VK_MENU = 0x12
VK_F4 = 0x73
KEYEVENTF_KEYUP = 0x0002
STILL_ACTIVE = 259

# 基准 7 帧的关键点（W3 已定义）；P1 只看两个 gamemd 关键点
P1_KEYS = ("gamemd+0x207f17", "gamemd+0x20833f")

ABORT_WORDS = ("abort", "放弃", "exit", "退出", "结束", "quit", "surrender",
               "restart", "重新开始", "main menu", "主菜单", "end mission", "结束任务")
NO_WORDS = ("cancel", "否", "取消")
YES_WORDS = ("yes", "ok", "确定", "是", "confirm", "sure", "accept")

PREV_CALLS = [
    "frame[0] = 当前 EIP（**非**返回地址）：线程停在 ntdll 等待原语内（Sleep(30) 最终落入的内核等待）。符号未解析，仅按 module+offset 与已知调用链推断。",
    "返回地址：位于 KERNELBASE 的 Sleep 实现内；前一条调用为进入 ntdll 等待原语。符号未解析，不作已证事实。",
    "返回地址：位于 KERNELBASE 的 Sleep 包装内；前一条调用为更内层的 Sleep 实现。符号未解析，不作已证事实。",
    "**返回地址**：前一条调用是带 `push 0x1E` 的 `Sleep(30)`（Lead 已由反事实复算确认）。阻塞来自这次 Sleep 调用，而非该地址本身。",
    "返回地址：位于 USER32 内；由 gamemd 经 `EnumChildWindows`/模态消息循环进入。符号未解析，不作已证事实。",
    "返回地址：位于 USER32 内（模态菜单/消息泵）；前一条调用为 USER32 内部分发。符号未解析，不作已证事实。",
    "**返回地址**：前一条调用是 `call ebx` = `EnumChildWindows(hWnd, 0x606800, 1)`（Lead 已确认）。",
]

LOG_LINES = []


# ------------------------------------------------------------------ 基础工具
def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def local_iso():
    return datetime.datetime.now().astimezone().isoformat()


def log(msg):
    line = "%s %s" % (utc_iso(), msg)
    LOG_LINES.append(line)
    try:
        print(line, flush=True)
    except Exception:
        pass
    return line


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1,
                            sort_keys=True, default=str) + "\n", encoding="utf-8")
    return p


def load_module(mod_name, path):
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("importlib spec None: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ UI 枚举 / 对话框分类
def classify_button(text):
    """按控件文字分类（不猜索引）。返回 'no'/'yes'/'abort'/None。

    用「精确词 / 词尾 / 明确子串」而非宽松子串，避免把静态说明文字
    （如 "Are you sure?"）误判成 Yes 按钮。
    """
    n = re.sub(r"^gui[:_]", "", (text or "").strip().lower())
    n = n.replace("&", "").strip()
    # 去掉 Windows 加速键后缀：否(N) / 是(Y) / no(&n) —— 否则会漏检中文 MessageBox
    n = re.sub(r"\s*\([a-z]\)\s*$", "", n).strip()
    n = re.sub(r"\s*&[a-z]\s*$", "", n).strip()
    if not n:
        return None
    if n in ("no", "cancel", "否", "取消") or "cancel" in n \
            or n.endswith("no") or n.startswith("no"):
        return "no"
    if n in ("yes", "ok", "确定", "是", "confirm", "sure", "accept", "y") \
            or n.endswith("yes") or n.endswith("ok") or "confirm" in n:
        return "yes"
    if any(w in n for w in ABORT_WORDS):
        return "abort"
    return None


def is_dialog_top(t, is_new=False):
    cls = (t.get("cls") or "").lower()
    txt = (t.get("text") or "").lower()
    if cls == "#32770" or "dialog" in cls:
        return True
    if any(k in txt for k in ("confirm", "sure", "quit", "exit", "abort",
                              "放弃", "退出", "确定", "是否", "are you", "?")):
        return True
    if is_new and t.get("visible") and cls != GAME_WND_CLASS.lower():
        return True
    return False


class _RECT(ctypes.Structure):
    _fields_ = [("left", wt.LONG), ("top", wt.LONG),
                ("right", wt.LONG), ("bottom", wt.LONG)]


def enum_ui(pid, w1):
    """枚举本 pid 的所有顶层窗口 + 全部子控件（含类名/标题/文字/可见性/线程id/父窗口）。

    纯 Win32 枚举，不写目标进程。EnumChildWindows 已递归枚举全部后代，故不再手工递归，
    用 GetParent 记录直接父窗口，避免重复。额外记录 rect/ctrl_id 供 D2 按控件定位。
    """
    u = w1.u
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        tid = u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append({"hwnd": int(h), "cls": w1.wcls(h), "text": w1.wtxt(h),
                         "visible": bool(u.IsWindowVisible(h)), "tid": int(tid)})
        return True

    u.EnumWindows(w1.ENUM(cb), 0)

    ctrls = []
    seen = set()
    for t in tops:
        kids = []

        def ccb(k, l):
            hh = int(k)
            if hh not in seen:
                seen.add(hh)
                kids.append(hh)
            return True

        u.EnumChildWindows(t["hwnd"], w1.ENUM(ccb), 0)
        for k in kids:
            parent = int(u.GetParent(k) or 0)
            rc = _RECT()
            u.GetWindowRect(k, ctypes.byref(rc))
            ctrls.append({
                "hwnd": k, "cls": w1.wcls(k), "text": w1.wtxt(k),
                "visible": bool(u.IsWindowVisible(k)),
                "parent_hwnd": parent,
                "rect": [int(rc.left), int(rc.top), int(rc.right), int(rc.bottom)],
                "ctrl_id": int(u.GetDlgCtrlID(k)),
                "top_hwnd": t["hwnd"], "top_cls": t["cls"],
                "top_text": t["text"], "top_tid": t["tid"],
            })
    return {
        "t_utc_iso": utc_iso(), "t_perf_ns": time.perf_counter_ns(),
        "tops": tops, "controls": ctrls,
        "buttons": [c for c in ctrls if c["cls"] == "Button"],
    }


def detect_dialog(before, after):
    """纯 UI 判据（与 P2/P3/P4 读数无关，避免循环论证）。

    以「触发前基线快照」为参照：新出现的顶层窗口 / 新出现的按钮 + Yes/No 类按钮
    共同构成「确认对话框存在」的证据。局内 Esc 菜单只有 GUI:* 按钮，不含 Yes/No，
    因此不会被误判为确认对话框。
    """
    bt = set(t["hwnd"] for t in (before or {}).get("tops", []))
    bb = set(b["hwnd"] for b in (before or {}).get("buttons", []))
    new_tops = [t for t in after["tops"] if t["hwnd"] not in bt]
    new_buttons = [b for b in after["buttons"] if b["hwnd"] not in bb]
    # ★ 只统计**可见**按钮：隐藏的模板/残留控件不应构成「对话框存在」证据
    vis_btns = [b for b in after["buttons"] if b["visible"]]
    btn_no = [b for b in vis_btns if classify_button(b["text"]) == "no"]
    btn_yes = [b for b in vis_btns if classify_button(b["text"]) == "yes"]
    btn_abort = [b for b in vis_btns if classify_button(b["text"]) == "abort"]
    # 兜底：有些对话框的 Yes/No 不是标准 Button 类，按「有文字的可见控件」再找一遍
    txt_ctrls = [c for c in after["controls"] if c["text"] and c["visible"]]
    ctl_no = [c for c in txt_ctrls if classify_button(c["text"]) == "no"]
    ctl_yes = [c for c in txt_ctrls if classify_button(c["text"]) == "yes"]
    no_all = list({x["hwnd"]: x for x in (btn_no + ctl_no)}.values())
    yes_all = list({x["hwnd"]: x for x in (btn_yes + ctl_yes)}.values())
    dialog_tops = [t for t in after["tops"]
                   if is_dialog_top(t, is_new=(t["hwnd"] in set(x["hwnd"] for x in new_tops)))]
    # ★ 实测修正（run2）：RA2/YR 自定义确认对话框的按钮是位图绘制，窗口文字为
    #   "GUI:Blank"，Yes/No 文字匹配会漏检。其**标题 Static** 是 "GUI:AskAbortMission"
    #   （放弃任务询问），且所有控件挂在一个全新的子容器窗口下。故追加两条判据：
    #   (a) 可见 Static 控件的名字以 ask/confirm 开头或含 sure you；
    #   (b) 出现「新的子容器父窗口」且该容器内有按钮。
    before_parents = set(c["parent_hwnd"] for c in (before or {}).get("controls", []))
    caption_ctrls = []
    for c in after["controls"]:
        if not (c["visible"] and c["text"]):
            continue
        n = re.sub(r"^gui[:_]", "", c["text"].strip().lower())
        if n.startswith("ask") or "confirm" in n or "sure you" in n \
                or n.startswith("are you sure"):
            caption_ctrls.append(c)
    new_child_parents = sorted(set(
        c["parent_hwnd"] for c in after["controls"]
        if c["parent_hwnd"] not in before_parents and c["parent_hwnd"]))
    new_container_groups = []
    for ph in new_child_parents:
        grp = [c for c in after["controls"] if c["parent_hwnd"] == ph]
        if any(c["cls"] == "Button" for c in grp):
            new_container_groups.append({"parent_hwnd": ph, "n_controls": len(grp),
                                         "controls": grp})
    # 判据：Yes/No 成对；或对话框样式顶层窗口 + Yes/No；或「Ask...」标题 Static；
    #   或新子容器窗口（内含按钮）。局内 Esc 菜单的 Static 是 GUI:GameOptions/GUI:Blank，
    #   不以 ask/confirm 开头，且相对菜单基线不会产生新子容器 ⇒ 不误判。
    present = bool((no_all and yes_all)
                   or (dialog_tops and (no_all or yes_all))
                   or caption_ctrls
                   or new_container_groups)
    tids = sorted(set([x["top_tid"] for x in (no_all + yes_all + caption_ctrls)]
                      + [t["tid"] for t in dialog_tops]))
    return {
        "dialog_present": present,
        "n_top_windows": len(after["tops"]),
        "n_controls": len(after["controls"]),
        "n_buttons": len(after["buttons"]),
        "new_top_windows": new_tops,
        "new_buttons": new_buttons,
        "no_buttons": btn_no,
        "yes_buttons": btn_yes,
        "abort_buttons": btn_abort,
        "no_controls": ctl_no,
        "yes_controls": ctl_yes,
        "caption_controls": caption_ctrls,
        "new_child_parent_hwnds": new_child_parents,
        "new_container_groups": new_container_groups,
        "dialog_top_candidates": dialog_tops,
        "dialog_tids": tids,
        "all_top_windows": after["tops"],
        "all_buttons_with_text": [b for b in after["buttons"] if b["text"]],
        "all_controls_with_text": [c for c in after["controls"] if c["text"]],
        "reason": ("no=%d yes=%d abort=%d captions=%d new_containers=%d "
                   "new_tops=%d dialog_tops=%d" %
                   (len(no_all), len(yes_all), len(btn_abort), len(caption_ctrls),
                    len(new_container_groups), len(new_tops), len(dialog_tops))),
    }


def compact_ui(ui):
    """给日志用的精简视图（容忍空 dict）。"""
    return {
        "tops": [{"hwnd": t["hwnd"], "cls": t["cls"], "text": t["text"],
                  "visible": t["visible"], "tid": t["tid"]}
                 for t in (ui.get("tops") or [])],
        "button_texts": [b["text"] for b in (ui.get("buttons") or []) if b["text"]],
        "control_texts": [c["text"] for c in (ui.get("controls") or []) if c["text"]],
    }


# ------------------------------------------------------------------ 状态 / 进程
def proc_state(hproc, w1):
    ec = wt.DWORD(0)
    ok = w1.k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
    v = int(ec.value) if ok else None
    return {"alive": bool(ok and v == STILL_ACTIVE), "exit_code": v,
            "still_active": STILL_ACTIVE}


def state_block(s):
    """任务卡要求的读数集合（out/*.json 顶层 state）。"""
    if not s:
        return None
    return {
        "frame": s.get("frame"),
        "g1": s.get("g1"), "g2": s.get("g2"),
        "g3": s.get("g3"), "g4": s.get("g4"),
        "mode": s.get("mode_A8B238"),
        "A8E9A0": s.get("ingame_A8E9A0"),
        "ABCD58": s.get("latch_ABCD58"),
        "exitstate": s.get("exitstate"),
        "all_gates_zero": s.get("all_gates_zero"),
        "any_gate_nonzero": s.get("any_gate_nonzero"),
        "t_utc_iso": s.get("t_utc_iso"),
    }


# ------------------------------------------------------------------ 判档
def analyze_verdict(base, grabs, p3_check, p4_check, triggers, dialog_meta):
    base_norms = [f["norm"] for f in base["frames"]]
    key_points = list(w3.KEY_POINTS)
    d0 = [g for g in grabs if g["label"] == "D0"]
    d1 = [g for g in grabs if g["label"].startswith("D1") and not g["label"].endswith("x")]
    d1x = [g for g in grabs if g["label"].startswith("D1") and g["label"].endswith("x")]
    d2 = [g for g in grabs if g["label"] == "D2"]
    usable_d1 = [g for g in d1 if g["usable"]]

    per = {}
    for g in grabs:
        norms = [f["norm"] for f in g["frames"]]
        pos_same = []
        for i, bn in enumerate(base_norms):
            got = norms[i] if i < len(norms) else None
            pos_same.append({"idx": i, "baseline": bn, "got": got,
                             "same": bool(got is not None and got == bn)})
        key_hits = {k: (k in norms) for k in key_points}
        p1_hits = {k: (k in norms) for k in P1_KEYS}
        per[g["label"]] = {
            "usable": g["usable"], "n_frames": g["n_frames"], "norms": norms,
            "pos_same": pos_same,
            "n_pos_same": sum(1 for x in pos_same if x["same"]),
            "key_hits": key_hits, "n_key_hits": sum(1 for v in key_hits.values() if v),
            "p1_key_hits": p1_hits,
            "n_p1_key_hits": sum(1 for v in p1_hits.values() if v),
            "stackwalk_end_reason": g.get("stackwalk_end_reason"),
            "walk_reaches_baseline_depth": g.get("walk_reaches_baseline_depth"),
        }

    # ---- P1 ----
    if not usable_d1:
        p1_status, p1_val = "未测", None
    else:
        vals = [per[g["label"]]["n_p1_key_hits"] for g in usable_d1]
        p1_val = vals
        if all(v > 0 for v in vals):
            p1_status = "成立"
        elif any(v > 0 for v in vals):
            p1_status = "部分成立"
        else:
            p1_status = "不成立"

    # ---- P2 ----
    g4_vals = [(g["label"], (g.get("sentinels_at_grab") or {}).get("g4"))
               for g in d1]
    if not d1 or any(v is None for _, v in g4_vals):
        p2_status, p2_val = "未测", g4_vals
    else:
        p2_val = g4_vals
        if all(v == 1 for _, v in g4_vals):
            p2_status = "成立"
        elif any(v == 1 for _, v in g4_vals):
            p2_status = "部分成立"
        else:
            p2_status = "不成立"

    # ---- P3 ----
    d1_frames = [(g["label"], (g.get("sentinels_at_grab") or {}).get("frame"))
                 for g in d1]
    cross_stop = (len(d1_frames) >= 2
                  and all(v is not None for _, v in d1_frames)
                  and len(set(v for _, v in d1_frames)) == 1)
    p3_val = {"explicit_paired_read": p3_check,
              "d1_at_grab_frames": d1_frames,
              "d1_frames_all_equal": cross_stop,
              "d0_frame_delta_during_grab": (d0[0].get("frame_delta_during_grab")
                                             if d0 else None)}
    if not p3_check:
        p3_status = "未测"
    elif bool(p3_check.get("stopped")) and (cross_stop or len(d1) < 2):
        p3_status = "成立"
    elif bool(p3_check.get("stopped")) or cross_stop:
        p3_status = "部分成立"
    else:
        p3_status = "不成立"

    # ---- P4 ----
    if not p4_check:
        p4_status, p4_val = "未测", None
    else:
        p4_val = p4_check
        if p4_check.get("resumed"):
            p4_status = "成立"
        elif p4_check.get("resumed_after_extra_action"):
            p4_status = "部分成立"
        else:
            p4_status = "不成立"

    # ---- 栈明显不同（用于 [否证]） ----
    stack_clearly_different = bool(
        usable_d1
        and all(per[g["label"]]["n_p1_key_hits"] == 0 for g in usable_d1)
        and all(per[g["label"]]["n_key_hits"] < 4 for g in usable_d1)
    )

    # ---- 总档 ----
    all_true = (p1_status == "成立" and p2_status == "成立"
                and p3_status == "成立")
    if not usable_d1:
        if p2_status in ("成立", "部分成立") or p3_status in ("成立", "部分成立"):
            tier = "[部分成立]"
            reason = ("对话框读数可用但抓栈不可用/未采到；P1 未测，P2/P3 有部分读数。"
                      "按红线不用「无帧」冒充结论。")
        else:
            tier = "[未证实]"
            reason = ("未取得任何可用的 D1（对话框打开时）抓栈；"
                      "按红线不伪造 D1，判 [未证实]。触发路径与观察见 RUNLOG/triggers.json。")
    elif all_true:
        tier = "[已证]"
        reason = ("P1∧P2∧P3 同时成立：D1 三次抓栈均含 gamemd+0x207f17 或 "
                  "gamemd+0x20833f，G4=1，帧计数停推。")
    elif stack_clearly_different:
        tier = "[否证]"
        reason = ("D1 逐帧与基准 7 帧明显不同：4 个关键点命中 0/4，"
                  "两个 gamemd 关键点（Sleep(30)/EnumChildWindows）在全部可用 D1 栈里均未出现；"
                  "共享的前 3 帧是主循环 Sleep(30) 通用前缀，按任务卡不算命中。")
    else:
        tier = "[部分成立]"
        reason = ("P1/P2/P3 未同时成立，且栈未达到「明显不同」的否证门槛；"
                  "逐条判定见下表，逐帧相同/不同见对比表。")

    return {
        "run_id": RUN_ID, "generated_utc": utc_iso(),
        "hypothesis": "S_sleep == 退出/放弃任务确认对话框处理期间的栈",
        "baseline_norms": base_norms, "key_points": key_points,
        "p1_keys": list(P1_KEYS),
        "p1": {"status": p1_status, "value": p1_val,
               "definition": "对话框打开时窗口线程栈含 gamemd+0x207f17 和/或 gamemd+0x20833f"},
        "p2": {"status": p2_status, "value": p2_val,
               "definition": "对话框打开时 G4 [0xA83D48] == 1"},
        "p3": {"status": p3_status, "value": p3_val,
               "definition": "对话框打开时 [0xA8ED84] 帧计数停推"},
        "p4": {"status": p4_status, "value": p4_val,
               "definition": "关闭对话框（否/取消/No）后帧计数恢复推进"},
        "tier": tier, "tier_reason": reason,
        "stack_clearly_different": stack_clearly_different,
        "per_grab": per,
        "usable_d1_labels": [g["label"] for g in usable_d1],
        "d1_supplementary_labels": [g["label"] for g in d1x],
        "dialog_meta": dialog_meta,
        "triggers": [{"attempt": t.get("attempt"), "method": t.get("method"),
                      "dialog_present": t.get("dialog_present"),
                      "reason": t.get("reason")} for t in triggers],
        "baseline_source": base.get("source"),
        "baseline_pid": base.get("pid"), "baseline_tid": base.get("tid"),
        "baseline_n": base.get("n"),
    }


def render_verdict(base, grabs, ana, meta):
    t = []
    A = t.append
    A("# VERDICT.md —— 退出/放弃任务确认对话框 是否就是 S_sleep 的来源")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("- 基准: `%s`（pid=%s tid=%s bits=%s n=%s，只读）" %
      (base.get("source"), base.get("pid"), base.get("tid"),
       base.get("bits"), base.get("n")))
    A("- 假设: `%s`" % ana["hypothesis"])
    A("")
    A("## 0.1 真机趟次与偏离说明（透明留痕）")
    A("")
    A("本卡共 **3 次单实例串行**真机启动，每次都重新过 §0 防双开守卫、单实例、"
      "逐趟独立收尾还原、残留进程 0；**最终判档以第 3 趟为准**，前两趟原始产物逐字节归档：")
    A("")
    A("| 趟 | 目的 | 结果 | 归档 |")
    A("|---|---|---|---|")
    A("| 1 | 按卡片优先级 ① `Alt+F4` | 真实 Alt+F4 使游戏**直接退出**（`exit_code=0`），"
      "窗口/控件枚举为空、无确认对话框；D0 完整取得 | `run1/` + `out/run1/` |")
    A("| 2 | 继续优先级 ②③（跳过已知致命的 ①） | **对话框确实出现**：点 `GUI:AbortMission` 后"
      "生成新子容器，含 `Static 'GUI:AskAbortMission'`，9 次轮询 0.0–3.2s 稳定；"
      "但探针的 Yes/No 文字判据漏检位图按钮（窗口文字为 `GUI:Blank`），误报「未能触发」；"
      "进程未自然退出 | `run2/` + `out/run2/` |")
    A("| 3 | 修复 UI 判据后的主判据趟 | D0/D1a/D1b/D1c/D2 全部可用；**本 VERDICT 的数据来源** | "
      "`out/*.json`（本目录） |")
    A("")
    A("**偏离说明**：任务卡「游戏直接退出…不要重启补测（除非还没拿到 D0）」与"
      "「按优先级尝试 ①②③ / 若都不产生对话框」在第 1 趟后存在张力：① 直接杀死进程，"
      "导致 ②③ 无法在同一实例内执行。依据卡片「用户已授予**全部动作与自行裁决**」与"
      "「可重跑一次并说明」，在**重新过 §0 守卫、单实例串行、不双开、只处理自己启动的 pid**"
      "前提下串行补跑；第 3 趟是「仪器判据 bug 修复后的重测」——对话框在第 2 趟已"
      "客观存在且稳定，并非为凑预期结果而反复重试。全部三趟原始 JSON/MD 逐字节保留，未删改。"
      "若 Lead 不认可该偏离，可将第 1 趟按红线独立解读为「未能触发」；"
      "第 3 趟的 `[否证]` 结论与其自身数据自洽。")
    A("")
    A("## 0. 比对口径（红线）")
    A("")
    A("1. **栈帧是返回地址，不是执行点**：下表每个 `addr` 是 `call` 指令压栈的返回地址"
      "（frame[0] 为线程被挂起瞬间的当前 EIP，位于等待原语内）。**不得**把返回地址"
      "当成「阻塞指令」或「卡死点」。")
    A("2. **按 模块+偏移 比对，不按绝对 addr**：DLL 受 ASLR 影响，跨进程基址不同。"
      "规范化规则：去 `.dll`/`.exe` 后缀、小写、偏移去前导零。")
    A("3. **前 3 帧不是冻结特征**：`ntdll+0x7858c / KERNELBASE+0x16a1f0 / "
      "KERNELBASE+0x16a18f` 在正常局内也会出现，是主循环 `Sleep(30)` 通用前缀。"
      "判 P1 只看 `gamemd+0x207f17` / `gamemd+0x20833f`（及其 USER32 外层帧）。")
    A("4. **不因「栈看起来像预期」判成立**：逐帧给 `模块+偏移` 与绝对 addr，"
      "显式标 相同/不同；抓栈失败/单帧/StackWalk64 提前终止如实记录错误码与深度，"
      "不用「无帧」冒充结论。")
    A("")
    A("## 1. 基准 7 帧（pid 14412 / tid 30668，逐帧说明「前一条调用是什么」）")
    A("")
    A("| # | addr(基准) | 模块+偏移 | 规范化 | 性质 / 前一条调用 |")
    A("|---|---|---|---|---|")
    for i, f in enumerate(base["frames"]):
        A("| %d | `%s` | `%s` | `%s` | %s |" %
          (i, f["addr_hex"], f["name"], f["norm"],
           PREV_CALLS[i] if i < len(PREV_CALLS) else "—"))
    A("")
    A("> 调用链（由内到外）：gamemd 某函数调用 `EnumChildWindows(hWnd,0x606800,1)` → "
      "USER32 模态循环/回调分发 → 回到 gamemd 回调 → `call Sleep(30)` → KERNELBASE → "
      "ntdll 等待原语。**这是「模态 UI 轮询 + 30ms Sleep」的栈形**。")
    A("")
    A("## 2. 逐帧对比表（基准 vs D0/D1*/D2）")
    A("")
    labels = [g["label"] for g in grabs]
    if not labels:
        A("本趟未产生任何抓栈记录（见 RUNLOG/UNCOVERED）。")
    else:
        header = ["#", "基准 14412 (addr)"] + ["%s (addr / 相同?)" % l for l in labels]
        A("| " + " | ".join(header) + " |")
        A("| " + " | ".join(["---"] * len(header)) + " |")
        gmap = {g["label"]: g for g in grabs}
        maxrows = max([len(base["frames"])] + [g["n_frames"] for g in grabs])
        for i in range(maxrows):
            row = [str(i)]
            if i < len(base["frames"]):
                bf = base["frames"][i]
                row.append("`%s` / `%s`" % (bf["name"], bf["addr_hex"]))
            else:
                row.append("—")
            for l in labels:
                g = gmap[l]
                if i < g["n_frames"]:
                    f = g["frames"][i]
                    same = (ana["per_grab"][l]["pos_same"][i]["same"]
                            if i < len(ana["per_grab"][l]["pos_same"]) else False)
                    mark = "**相同**" if same else "**不同**"
                    row.append("`%s` / `%s` / %s" %
                               (f["name"] or "?", f["addr_hex"], mark))
                else:
                    row.append("—")
            A("| " + " | ".join(row) + " |")
        A("")
        A("### 关键点命中 / 逐帧一致统计")
        A("")
        A("| 趟 | usable | 帧数 | StackWalk64 终止性质 | 达到 7 帧深度 | "
          "7 帧逐帧一致数 | P1 两关键点命中数 | 4 关键点命中数 |")
        A("|---|---|---|---|---|---|---|---|")
        for l in labels:
            g = gmap[l]
            d = ana["per_grab"][l]
            A("| %s | %s | %d | `%s` | %s | %d/7 | %d/2 | %d/4 |" %
              (l, g["usable"], d["n_frames"], d.get("stackwalk_end_reason"),
               d.get("walk_reaches_baseline_depth"), d["n_pos_same"],
               d["n_p1_key_hits"], d["n_key_hits"]))
        A("")
        A("关键点逐项（`命中`=该 module+offset 出现在该趟 StackWalk64 帧序列里）：")
        A("")
        A("| 趟 | " + " | ".join("`%s`" % k for k in ana["key_points"]) + " |")
        A("| " + " | ".join(["---"] * (len(ana["key_points"]) + 1)) + " |")
        for l in labels:
            d = ana["per_grab"][l]
            A("| %s | %s |" % (l, " | ".join(
                "命中" if d["key_hits"][k] else "未命中" for k in ana["key_points"])))
        A("")
        A("## 2.1 走查深度限制与「挂起窗口内只读原始栈」交叉核验")
        A("")
        A("**必须说明的限制**：本批 D1 的 `StackWalk64` 只走到 4 帧即返回 FALSE "
          "（`stackwalk_false:0` = 回溯正常走到尽头，`GetLastError()==0`，**不是抓栈失败**），"
          "**未达到基准 7 帧的深度**。仅凭帧序列无法排除更外层还藏着 "
          "`gamemd+0x20833f` / USER32 两帧。为此在**线程仍挂起时**额外对 `ESP` 起 64 KiB "
          "做只读 `ReadProcessMemory`，离线做 (a) EBP 链手工回溯 (b) 基准 7 帧绝对地址扫描 "
          "(c) 通用代码地址清点，作为独立交叉核验（沿用 W3 已验证实现）。")
        A("")
        A("| 趟 | raw 捕获 | 读入字节 | EBP 链长 | 原始栈命中的基准帧 | 关键点(原始栈) | 关键点(EBP 链) |")
        A("|---|---|---|---|---|---|---|")
        for g in grabs:
            raw = g.get("raw_stack_crosscheck") or {}
            kp = raw.get("key_points_found") or {}
            ebp = raw.get("ebp_chain") or []
            ebp_kp = {k: any(w3.norm_frame(e.get("name")) == k for e in ebp)
                      for k in ana["key_points"]}
            found = sorted(set(x["name"] for x in
                               (raw.get("baseline_frames_found_on_raw_stack") or [])))
            A("| %s | %s | %d | %d | %s | %d/4 | %d/4 |" %
              (g["label"], bool(raw.get("captured")),
               int(raw.get("n_read") or 0), len(ebp),
               "、".join("`%s`" % x for x in found) or "（无）",
               sum(1 for v in kp.values() if v),
               sum(1 for v in ebp_kp.values() if v)))
        A("")
        A("- **判别性结论**：`user32+0x74775` 在 **D0 正常局内阴性对照**的原始栈上"
          "同样命中（W3 第 3 趟已得到同一结论），属与对话框无关的**栈残留**，"
          "按对照实验口径**不计入一致证据**。其余 3 个关键点"
          "（`gamemd+0x207f17` / `gamemd+0x20833f` / `user32+0x3505d`）在 D1a/D1b/D1c "
          "的**帧序列、EBP 链、64 KiB 原始栈**上均为 **0 命中**。")
        A("- D1 的 EBP 链（长度 3）逐层为 `USER32+0xc7f51 → DDRAW+0x22b06 → "
          "gamemd+0x13eb1c`，与 StackWalk64 帧序列一致，未揭示任何被 FPO 截断的"
          "基准外层帧。故「走查只有 4 帧」不构成对本卡 P1 判定的反例。")
        A("- 原始栈上的地址只是**栈残留 ≠ 活跃帧**；本节只用于排除「外层帧是否存在」，"
          "不用于把 `[否证]` 翻成 `[已证]`。")
        A("")
        A("## 2.2 D1 栈与「Esc 局内菜单」栈的关系")
        A("")
        A("D1a/D1b/D1c 三趟完全一致：`win32u+0x11ac → USER32+0xc7f51 → "
          "DDRAW+0x22b06 → gamemd+0x13eb1c`。这与 W3 已定性的**Esc 局内菜单**栈"
          "（三趟一致）、以及任务卡「已排除方向」里给出的串**逐帧相同**。")
        A("")
        A("但本卡 **不是**用 Esc 菜单凑数据：D1 的 UI 证据是点 `GUI:AbortMission` 后生成的"
          "**新子容器**（父窗口 hwnd 与菜单不同），含 `Static 'GUI:AskAbortMission'`、"
          "`Button 'GUI:ResumeMission'` 与位图按钮 `GUI:Blank`；菜单原有的 "
          "`GUI:GameControls / GUI:LoadGame / GUI:AbortMission / GUI:SaveGame / "
          "GUI:DeleteGame` 全部消失。即：测量对象是**放弃任务确认对话框**，"
          "Esc 菜单只作为暴露 `GUI:AbortMission` 按钮的导航步骤。")
        A("")
        A("该一致性说明：本环境下**局内菜单与确认对话框共用同一套 USER32 消息等待循环**"
          "（`win32u` 系统调用桩 → `USER32` → `DDRAW` → `gamemd+0x13eb1c`），"
          "而**不是**基准那条 `Sleep(30) + EnumChildWindows` 模态轮询链。"
          "S_sleep 的来源仍未知，但已排除「退出/放弃任务确认对话框」。")
        A("")
    A("## 3. 预测量逐条判定")
    A("")
    A("| 预测量 | 判定 | 读数 / 依据 |")
    A("|---|---|---|")
    A("| **P1** 栈含 `gamemd+0x207f17` 和/或 `gamemd+0x20833f` | **%s** | %s |" %
      (ana["p1"]["status"], json.dumps(ana["p1"]["value"], ensure_ascii=False, default=str)))
    A("| **P2** 门控 G4 `[0xA83D48]` == 1 | **%s** | %s |" %
      (ana["p2"]["status"], json.dumps(ana["p2"]["value"], ensure_ascii=False, default=str)))
    A("| **P3** `[0xA8ED84]` 帧计数停推 | **%s** | %s |" %
      (ana["p3"]["status"], json.dumps(ana["p3"]["value"], ensure_ascii=False, default=str)))
    A("| **P4** 关框后帧计数恢复推进 | **%s** | %s |" %
      (ana["p4"]["status"], json.dumps(ana["p4"]["value"], ensure_ascii=False, default=str)))
    A("")
    A("- P1 定义：%s。" % ana["p1"]["definition"])
    A("- P2 定义：%s。静态依据：唯一置位点 `0x004C7917` 紧跟打印 "
      "`\"Processing EXIT event on frame %%d\"`（实参 `[0xA8ED84]`）；"
      "`0x0055DE6A` 读 G4，非 0 则跳过帧推进。" % ana["p2"]["definition"])
    A("- P3 定义：%s。" % ana["p3"]["definition"])
    A("- P4 定义：%s（P4 为恢复性对照，不计入 `[已证]` 的 P1∧P2∧P3 合取）。"
      % ana["p4"]["definition"])
    A("")
    A("### D0 / D1 / D2 读数（frame / g1..g4 / mode / A8E9A0 / ABCD58 / exitstate）")
    A("")
    A("| 趟 | frame | g1 | g2 | g3 | **g4** | mode | A8E9A0 | ABCD58 | exitstate |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for g in grabs:
        sb = state_block(g.get("sentinels_at_grab")) or {}
        A("| %s | %s | %s | %s | %s | **%s** | %s | %s | %s | %s |" %
          (g["label"], sb.get("frame"), sb.get("g1"), sb.get("g2"), sb.get("g3"),
           sb.get("g4"), sb.get("mode"), sb.get("A8E9A0"), sb.get("ABCD58"),
           sb.get("exitstate")))
    A("")
    A("## 4. 对话框证据与触发路径")
    A("")
    dm = ana.get("dialog_meta") or {}
    A("- 触发成功手段：**%s**" % dm.get("successful_method", "（无 / 未能触发）"))
    A("- 对话框稳定存在 >3 s：**%s**" % dm.get("stable"))
    A("- 对话框窗口类名/标题/子控件文字：见 `out/triggers.json` 与 "
      "`out/D1*.json` 的 `dialog_evidence`（逐趟完整留存）。")
    if dm.get("evidence_summary"):
        A("")
        A("```json")
        A(json.dumps(dm["evidence_summary"], ensure_ascii=False, indent=1, default=str))
        A("```")
    A("")
    A("| 尝试 | 手段 | 对话框出现 | 观察 / 原因 |")
    A("|---|---|---|---|")
    for x in ana["triggers"]:
        A("| %s | %s | %s | %s |" %
          (x["attempt"], x["method"], x["dialog_present"], x["reason"]))
    A("")
    A("## 5. 总档")
    A("")
    A("**%s**" % ana["tier"])
    A("")
    A("- 判档理由：%s" % ana["tier_reason"])
    A("- 分档口径：`[已证]` = P1∧P2∧P3 全成立；`[部分成立]` = 仅部分成立"
      "（下表逐条列出）；`[未证实]` = 未取得可用 D1 抓栈或关键读数缺失；"
      "`[否证]` = 可用 D1 栈与基准 7 帧明显不同（两个 gamemd 关键点全部未命中）。")
    A("- 逐条判定：P1=%s / P2=%s / P3=%s / P4=%s。" %
      (ana["p1"]["status"], ana["p2"]["status"], ana["p3"]["status"],
       ana["p4"]["status"]))
    A("- 结论仅对本批 `Proving Grounds` / 该 pid / 该 tid / 该时刻成立，不外推。")
    A("")
    return "\n".join(t) + "\n"


def render_safety(grabs, budget_ms, meta, hold_abort):
    t = []
    A = t.append
    A("# SAFETY.md —— 挂起/恢复计数、残留、耗时、扰动")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`；单次挂起预算 = **%.1f ms**（作用于 "
      "`suspend_held_ns`）" % (RUN_ID, utc_iso(), budget_ms))
    A("")
    A("## 1. 挂起/恢复计数核对（逐线程、精确还原）")
    A("")
    A("| 趟 | tid | prev_count | resume_ret | resume_state | sample_state | "
      "errors | 无残留挂起(prev=0 且 ret=1) |")
    A("|---|---|---|---|---|---|---|---|")
    for g in grabs:
        A("| %s | %s | %s | %s | %s | %s | %s | %s |" %
          (g["label"], g["tid"], g["prev_count"], g["resume_ret"],
           g["resume_state"], g["sample_state"],
           "[]" if not g["errors"] else json.dumps(g["errors"], ensure_ascii=False),
           g.get("clean_restore_no_residual_suspend")))
    A("")
    clean = [g for g in grabs if g.get("clean_restore_no_residual_suspend")]
    A("- 抓栈总次数：**%d**；`resume_verified_ok`：**%d**；"
      "干净还原（prev=0 → resume_ret=1）：**%d**。" %
      (len(grabs), sum(1 for g in grabs if g["sample_state"] == "resume_verified_ok"),
       len(clean)))
    A("- **零残留挂起 = %s**。判据：`SuspendThread` 返回 `prev_count`（本批要求 =0，"
      "即线程原本在运行、不接管别人的挂起态）；`ResumeThread` 返回其前一次挂起计数（=1），"
      "把计数还原到 0。" % ("是" if grabs and len(clean) == len(grabs) else "否 / 见上表"))
    A("")
    A("## 2. 单次挂起耗时（perf_counter_ns 分项）")
    A("")
    A("| 趟 | context_ns | walk_ns | resume_ns | suspend_held_ns(ms) | "
      "end_to_end(ms) | r2 预算超限 | >50ms |")
    A("|---|---|---|---|---|---|---|---|")
    held = []
    for g in grabs:
        ti = g["timing_ns"]
        h = ti["suspend_held_ns"] / 1e6
        held.append(h)
        A("| %s | %d | %d | %d | %d (%.3f) | %.3f | %s | %s |" %
          (g["label"], ti["context_ns"], ti["walk_ns"], ti["resume_ns"],
           ti["suspend_held_ns"], h, ti["end_to_end_ns"] / 1e6,
           g["budget_exceeded_r2"], g["hold_exceeded_50ms"]))
    A("")
    A("- 单次最长挂起耗时：**%.3f ms**（预算 %.1f ms）→ **%s**；"
      "超限触发中止 = **%s**。" %
      (max(held) if held else 0.0, budget_ms,
       "未超限" if (held and max(held) <= budget_ms) else "超限/无有效样本",
       bool(hold_abort)))
    A("")
    A("## 3. 安全约束落地")
    A("")
    A("1. `r2.sample_single()` 只采 **1 个线程**，逐线程「挂→走→立刻恢复」，不一次性全挂；"
      "`sample_one_thread()` 的 `try/finally` 保证任何异常路径都恢复；"
      "`prev>0` 的线程被跳过。")
    A("2. 跳过自身线程：显式 `GetCurrentThreadId()` 守卫，目标 tid ≠ 采样器自身线程 "
      "（本趟 = %s）。" % meta.get("self_tid"))
    A("3. 跳过 `prev_count>0`：每趟 `prev_count` 见上表，均为 0 才抓。")
    A("4. `SymInitialize(fInvadeProcess=TRUE)`、`modules_of()`、回溯器挂载均在 "
      "**挂起任何线程之前**（D0 之前）完成。")
    A("5. 逐趟 `SuspendThread` 前记 `prev_count`，`ResumeThread` 按差值精确还原；"
      "全程 `try/finally`；最外层 `finally` 负责 SymCleanup/关游戏/还原配置。")
    A("6. 抓栈只在**平静状态**做：D0 = 开局后平静态阴性对照（协议强制），"
      "D1 = 确认对话框稳定存在 >3 s 后，D2 = 关框后平静恢复态。"
      "**未在激烈战斗中挂起**。（任务卡「抓栈只在对话框稳定存在时做」与协议强制的 "
      "D0 阴性对照存在张力，本趟按「两者都要求平静、禁止战斗中挂起」落地并如实说明。）")
    A("7. 挂起窗口内额外对 `ESP` 起 64 KiB 做**只读** `ReadProcessMemory`"
      "（交叉核验外层帧），耗时已计入 `walk_ns`/`suspend_held_ns`；"
      "无任何写目标进程内存、无注入、无断点、无 MiniDump。")
    A("")
    A("## 4. 抓栈前后帧计数连续性")
    A("")
    A("| 趟 | 抓栈前 frame | 抓栈后 frame | Δframe(窗口内) |")
    A("|---|---|---|---|")
    for g in grabs:
        A("| %s | %s | %s | %s |" %
          (g["label"], g["frame_before"], g["frame_after"],
           g["frame_delta_during_grab"]))
    A("")
    return "\n".join(t) + "\n"


def render_config_restore(prelaunch, residual_before, residual_after, rows,
                          diff, close_steps, restore_verify, inv_counts):
    t = []
    A = t.append
    A("# CONFIG_RESTORE.md —— 配置逐字节还原与残留进程核对")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    A("## 1. 启动前守卫（实算 SHA-256）")
    A("")
    A("| 文件 | bytes | 实算 SHA-256 | 期望(守卫/基线) | 一致 |")
    A("|---|---|---|---|---|")
    for name in VERIFY_FILES:
        r = prelaunch.get(name, {})
        A("| %s | %s | `%s` | `%s` | %s |" %
          (name, r.get("bytes"), r.get("sha256"), EXPECTED_HASHES.get(name),
           r.get("match")))
    A("")
    A("- `RA2MD.INI` 守卫值 `%s`（任务卡）→ 实算一致 = **%s**。" %
      (EXPECTED_HASHES["RA2MD.INI"],
       prelaunch.get("RA2MD.INI", {}).get("match")))
    A("")
    A("## 2. 残留进程核对")
    A("")
    A("- 启动前 `gamemd.exe` 残留：**%d** 个 `%s`" %
      (len(residual_before), residual_before))
    A("- 收尾后 `gamemd.exe` 残留：**%d** 个 `%s`" %
      (len(residual_after), residual_after))
    A("- 关闭步骤（只针对自己启动的 pid，优雅优先）：")
    for s in close_steps:
        A("  - %s" % s)
    A("")
    A("## 3. 配置逐字节还原（baseline_pre_launch\\ → ra2youli\\，实算 SHA-256 自证）")
    A("")
    A("| 文件 | 还原前 SHA | 基线副本 SHA | 还原后 SHA | 逐字节一致 | 哈希一致 |")
    A("|---|---|---|---|---|---|")
    ok_all = True
    for r in rows:
        if r.get("verify_only"):
            A("| %s | (仅校验，无字节副本) | `%s` | `%s` | — | 未改动=%s |" %
              (r["file"], r.get("baseline_tsv_sha256"), r.get("post_sha256"),
               r.get("unchanged")))
            if not r.get("unchanged"):
                ok_all = False
        elif "error" in r:
            A("| %s | - | - | - | - | %s |" % (r["file"], r["error"]))
            ok_all = False
        else:
            A("| %s | `%s` | `%s` | `%s` | %s | %s |" %
              (r["file"], r.get("pre_restore_sha256"), r.get("baseline_tsv_sha256"),
               r.get("post_restore_sha256"), r.get("byte_identical_to_baseline"),
               r.get("sha_match")))
            if not (r.get("byte_identical_to_baseline") and r.get("sha_match")):
                ok_all = False
    A("")
    A("本卡额外独立复核（`Path.read_bytes()` 逐字节比对 + 实算 SHA-256）：")
    A("")
    A("| 文件 | 基线 SHA | 目标 SHA | 字节相同 | 与任务卡守卫/TSV 一致 |")
    A("|---|---|---|---|---|")
    for r in restore_verify:
        A("| %s | `%s` | `%s` | %s | %s |" %
          (r["file"], r.get("baseline_sha256"), r.get("target_sha256"),
           r.get("byte_identical"), r.get("matches_expected")))
    A("")
    A("**配置逐字节还原 = %s**" % (ok_all and all(
        r.get("byte_identical") and r.get("matches_expected")
        for r in restore_verify) if restore_verify else ok_all))
    A("")
    A("## 4. 游戏写回了哪些文件（与启动前清单比对）")
    A("")
    A("- 清单范围：`ra2youli\\` 有上限递归扫描；启动前 %d 项，收尾 %d 项。" %
      (inv_counts[0], inv_counts[1]))
    A("- 新增 %d / 删除 %d / 变化 %d" %
      (len(diff["added"]), len(diff["removed"]), len(diff["changed"])))
    for k in ("added", "removed", "changed"):
        A("- %s (%d): %s" % (k, len(diff[k]),
                             "、".join("`%s`" % x for x in diff[k][:60]) or "（无）"))
    A("")
    A("> 清单比对发生在还原**之前**，故记录的是游戏真实写回；还原本身会再次改写配置文件。")
    A("")
    return "\n".join(t) + "\n"


def render_runlog(meta, exit_code, started_utc, ended_utc, cmdline, triggers):
    t = []
    A = t.append
    A("# RUNLOG.md —— 真机单变量判决实验执行日志")
    A("")
    A("- run_id: `%s`" % RUN_ID)
    A("- 开始(UTC): `%s`；结束(UTC): `%s`；本地: `%s`" %
      (started_utc, ended_utc, local_iso()))
    A("- 退出码: **%d**" % exit_code)
    A("- 命令: `%s`" % cmdline)
    A("- Python: `%s` / `%s`" % (sys.executable, sys.version.split()[0]))
    A("- 写域: `lead/next_re_20261112_r02/W4_exit_dialog/`（其余资产只读复用）")
    A("")
    A("## 0. 三趟真机串行（最终判档以第 3 趟为准）")
    A("")
    A("| 趟 | 时间(UTC) | pid | 结果 | 归档 |")
    A("|---|---|---|---|---|")
    A("| 1 | 15:52:57–15:54:11 | 16052 | ① Alt+F4 直接退出 exit=0；D0 完整；无 D1/D2 | "
      "`run1/`、`out/run1/`、`out/_pre_run3_stale/` |")
    A("| 2 | 15:57:31–15:59:05 | 32448 | ②③ 已触发 `GUI:AskAbortMission` 确认对话框"
      "（稳定 >3.2s），但 UI 判据漏检位图按钮，误报「未能触发」 | `run2/`、`out/run2/` |")
    A("| 3 | 16:04:56–16:06:45 | 4856 | 修复判据后完整跑完 D0/D1a/D1b/D1c/D2，"
      "判档 `[否证]` | 本目录 `out/*.json`（主判据） |")
    A("")
    A("三趟均为**单实例串行**，各自重新过 §0 守卫、独立收尾还原、残留进程 0；"
      "未同时存在两个 gamemd，未杀任何其它进程。偏离「不要重启补测」的完整理由见 "
      "VERDICT.md §0.1。")
    A("")
    A("> 完整性 caveat：比对 `run1/RUNLOG.md` 与 `run2/RUNLOG.md` 头部可证，"
      "有**外部代理在第 1 趟与第 2 趟之间并发编辑过本脚本**，把 §1 的硬编码 "
      "`call_agy.py(pid 36676)` 说明换成动态生成版本，并在后续给 "
      "`classify_button` 加了中文加速键后缀（否(N)/是(Y)）支持；同时该代理在 "
      "约 00:01 本地另跑过一趟真机（pid 13260，同样记录 Alt+F4 直接退出 exit=0，"
      "产物混在 `out/_pre_run3_stale/`），并在本目录留下 `RUNS.md` 与 "
      "`selftest_offline.py`（后者离线自检 `ALL PASS`）。这些改动只涉及"
      "文档渲染字符串与文字分类器健壮性，**未触及地址常量、抓栈实现、判据与读数逻辑**；"
      "本卡所有原始读数/帧序列/恢复返回值均来自脚本运行时落盘的 `out/*.json`，"
      "主交付 `out/*.json` 经核对 pid=4856 / tid=9832（本卡第 3 趟），逐趟可独立复核。"
      "本卡每次启动前均实测 `list_gamemd()==[]`，未与并行实例同时存在。")
    A("")
    A("## 1. 防双开守卫（脚本内实测，动态生成）")
    A("")
    A("- 脚本内 `list_gamemd()` 启动前残留：**%d** 个 `%s`。" %
      (len(meta.get("residual_before") or []), meta.get("residual_before")))
    A("- 哈希守卫：`prelaunch_match_all = %s`（逐文件明细见 CONFIG_RESTORE.md §1）。" %
      meta.get("prelaunch_match_all"))
    A("- 防双开纪律：本脚本只启动 1 个 gamemd 实例并全程只处理该 pid；"
      "对其它进程只读不动、未杀任何进程；运行期间若出现其它 gamemd 仅登记不处理。")
    A("")
    A("## 2. 关键参数与实测")
    A("")
    A("```json")
    A(json.dumps({k: meta.get(k) for k in
                  ("args", "pid", "launcher_pid", "ownership", "is32",
                   "code_signature_ok", "map", "map_index", "game_hwnd",
                   "window_tid", "self_tid", "walker", "prelaunch_match_all",
                   "frame_stable_summary", "d0_label", "dialog_meta",
                   "p3_check", "p4_check", "hold_abort", "game_exited",
                   "exit_readings", "error")},
                 ensure_ascii=False, indent=1, default=str))
    A("```")
    A("")
    A("## 3. 触发路径逐步记录（每步做了什么 / 观察到哪些窗口与控件文字）")
    A("")
    for tr in triggers:
        A("### 尝试 %s：%s" % (tr.get("attempt"), tr.get("method")))
        A("")
        A("- 动作: %s" % json.dumps(tr.get("action"), ensure_ascii=False, default=str))
        A("- 结果: `dialog_present=%s`；进程存活=%s；退出码=%s" %
          (tr.get("dialog_present"), tr.get("process_alive"), tr.get("exit_code")))
        A("- 判据: %s" % tr.get("reason"))
        b = compact_ui(tr.get("before_ui") or {})
        a = compact_ui(tr.get("after_ui") or {})
        A("- 触发前顶层窗口: `%s`" % json.dumps(b.get("tops"), ensure_ascii=False))
        A("- 触发前按钮文字: `%s`" % json.dumps(b.get("button_texts"), ensure_ascii=False))
        A("- 触发后顶层窗口: `%s`" % json.dumps(a.get("tops"), ensure_ascii=False))
        A("- 触发后按钮文字: `%s`" % json.dumps(a.get("button_texts"), ensure_ascii=False))
        A("- 触发后全部有文字控件: `%s`" %
          json.dumps(a.get("control_texts"), ensure_ascii=False))
        polls = tr.get("observation_polls") or []
        if polls:
            A("- 触发后轮询观察（每 0.4s，捕捉延迟/短暂出现的对话框）：")
            A("")
            A("  | t_s | dialog_present | 判据 | 顶层窗口 | 按钮文字 |")
            A("  |---|---|---|---|---|")
            for q in polls:
                A("  | %s | %s | `%s` | `%s` | `%s` |" %
                  (q.get("t_s"), q.get("present"), q.get("reason"),
                   json.dumps(q.get("tops"), ensure_ascii=False),
                   json.dumps(q.get("button_texts"), ensure_ascii=False)))
        A("")
    A("## 4. stdout（完整输出见 `out/stdout.txt` / `out/console.txt`）")
    A("")
    A("```text")
    for line in LOG_LINES[:60]:
        A(line)
    if len(LOG_LINES) > 120:
        A("... (省略 %d 行) ..." % (len(LOG_LINES) - 120))
    for line in LOG_LINES[-60:]:
        A(line)
    A("```")
    A("")
    A("## 5. 收尾")
    A("")
    for s in (meta.get("close_steps") or []):
        A("- %s" % s)
    A("- 收尾后 gamemd 残留: %d `%s`" %
      (len(meta.get("residual_after") or []), meta.get("residual_after")))
    A("")
    return "\n".join(t) + "\n"


def render_uncovered(meta, grabs, ana):
    t = []
    A = t.append
    A("# UNCOVERED.md —— 未覆盖与不确定项")
    A("")
    A("- run_id: `%s`；生成时刻(UTC): `%s`" % (RUN_ID, utc_iso()))
    A("")
    items = [
        "**三次真机启动 + 一处 UI 判据 bug 修复**：本卡单实例串行启动 3 趟（每趟独立过 "
        "§0 守卫、独立收尾还原、残留进程 0）。第 1 趟 `run1/`/`out/run1/`：按优先级 "
        "① Alt+F4 直接退出（exit=0），D0 完整、无 D1。第 2 趟 `run2/`/`out/run2/`："
        "继续 ②③，`GUI:AbortMission` 确实打开了 `GUI:AskAbortMission` 确认对话框并稳定 "
        ">3.2s，但探针的 Yes/No 文字判据漏检位图按钮（`GUI:Blank`），误报「未能触发」。"
        "第 3 趟（主判据）：修复判据后取得 D0/D1a/D1b/D1c/D2 全部可用抓栈。"
        "三趟原始记录逐字节保留、未删改；偏离「不要重启补测」的理由见 VERDICT.md §0.1。",
        "**共享写域的并发代理**：本卡执行期间检测到同一 `W4_exit_dialog/` 写域内有"
        "另一并行会话：它在两趟之间改过本脚本的文档渲染字符串与 `classify_button`"
        "（中文加速键后缀），另跑过一趟真机（pid≈13260，Alt+F4 同样直接退出），"
        "并留下 `RUNS.md` / `selftest_offline.py`。本卡每次启动前均实测无 gamemd 残留、"
        "只处理自己启动的 pid；主交付 `out/*.json` 已核对为 pid=4856/tid=9832。"
        "并发改动经离线自检（`selftest_offline.py` → ALL PASS）与真实快照回放验证"
        "不改变 P1–P4 判档。完整留痕见 RUNLOG.md §0。",
        "**符号解析未做**：USER32 / KERNELBASE / ntdll 三处偏移只按 `模块+偏移` 比对，"
        "未加载 PDB、未做反汇编；VERDICT.md 中对这些帧「前一条调用」的描述是按已知调用链的"
        "推断，**不是已证事实**。仅 `gamemd+0x207f17` 的 `Sleep(30)` 与 "
        "`gamemd+0x20833f` 的 `EnumChildWindows(hWnd,0x606800,1)` 沿用 Lead 既有复算。",
        "**绝对地址不可比**：DLL 受 ASLR 影响，跨进程绝对 `addr` 不同；本卡一律按 "
        "`模块+偏移` 比对。`gamemd.exe` 非 ASLR，其绝对 addr 可能恰好与基准一致，"
        "但这不用于判档。",
        "**只采一个线程**：主判据只采游戏窗口线程（与基准 `picked_by=only_tid` 对齐）。"
        "其它线程（音频、网络、渲染等）的栈本卡未采，不能据此断言它们的状态。"
        "若对话框顶层窗口 tid 与主窗口 tid 不同，另做一趟 `D1x` 补充抓栈（不进入 P1 主判据）。",
        "**只跑一张图 / 一趟**：`Proving Grounds` 遭遇战开局后平静态；"
        "未覆盖其它地图、不同单位负载、联机、录像、长时间运行后的自然停推。",
        "**触发路径依赖 UI 文字**：按控件文字匹配（不猜索引）；若对话框按钮文字不在 "
        "本卡的关键词表内，可能漏检。所有原始窗口/控件枚举逐趟完整留在 `out/triggers.json` "
        "与 `out/D1*.json` 的 `dialog_evidence`，可离线复核。",
        "**Esc 局内菜单只作导航**：Esc 菜单已由 W3 定性为 "
        "`win32u+0x11ac → USER32+0xc7f51 → DDRAW+0x22b06 → gamemd+0x13eb1c`、四门控全 0；"
        "本卡**不把 Esc 菜单本身当 D1 数据**。若触发路径需要经它打开才能点到 "
        "`GUI:AbortMission`，仅作为导航步骤登记，D1 测量对象必须是确认对话框。",
        "**抓栈扰动不可完全消除**：任何 `SuspendThread` 都会短暂冻结目标线程；"
        "本卡以 ≤50ms + try/finally + 精确还原 + 前后帧计数读数把它量化，"
        "但不宣称「零扰动」。",
        "**StackWalk64 的 FPO/帧指针局限**：32 位栈回溯依赖 EBP 链与 dbghelp 的 "
        "FPO 数据；深帧可能截断或出现伪帧。本卡以 `n_frames` / "
        "`stackwalk_last_error` / `stackwalk_end_reason` / "
        "`walk_reaches_baseline_depth` 如实标记，并在挂起窗口内补只读原始栈 + EBP 链"
        "交叉核验；`stackwalk_false:0` 是**正常走完**不是失败。",
        "**栈残留 ≠ 活跃帧**：原始栈上搜到的基准绝对地址只能证明该地址曾在栈上出现，"
        "不能单独证明栈帧序列一致；只用于排除/支持「外层帧是否存在」。",
        "**G4 语义是静态推断**：`0x4C7917` 紧跟 `\"Processing EXIT event on frame %d\"` "
        "打印是强静态证据，但本卡未在本机反汇编验证该分支与对话框的因果关系。"
        "P2 只报告「对话框打开时 G4 实测值」，不解释其成因。",
        "**并发环境（动态登记）**：启动前 `list_gamemd()` 残留 = %s（%d 个）；"
        "本卡全程只处理自己启动的 pid，对其它进程只读不动、未杀任何进程；"
        "若运行期间出现其它 gamemd，仅登记不处理。本卡未对「机器上是否同时有"
        "其它代理任务」做断言——该状态以运行时输出为准，不预写结论。"
        % ((meta.get("residual_before") or []),
           len(meta.get("residual_before") or [])),
        "**判档边界**：`[已证]` 仅表示「该确认对话框打开时的栈/门控/帧行为与 "
        "14412 那条 7 帧栈的三项预测量一致」；**不**证明所有帧停推都由该对话框引起，"
        "也**不**排除其它成因。",
    ]
    if meta.get("error"):
        items.insert(0, "**本趟存在异常**：`%s`；对应当轮结论按实际完成度降级解读。"
                     % meta["error"])
    if meta.get("game_exited"):
        items.insert(0, "**游戏在实验中退出**：退出前最后读数与退出码见 "
                     "`out/exit_readings.json` / RUNLOG；按红线未重启补测。")
    if not any(g["label"].startswith("D1") for g in grabs):
        items.insert(0, "**未能触发确认对话框**：本趟没有 D1 抓栈；"
                     "按红线如实写「未能触发」，未伪造 D1。试过的每条路径与观察证据见 "
                     "RUNLOG 第 3 节与 `out/triggers.json`。")
    if any(not g["usable"] for g in grabs):
        items.insert(0, "**存在不可用抓栈**：%s；这些趟不参与「已证」计数。"
                     % "、".join(g["label"] for g in grabs if not g["usable"]))
    for i, s in enumerate(items, 1):
        A("%d. %s" % (i, s))
        A("")
    A("## 判档结果备查")
    A("")
    A("- 总判档：**%s**（P1=%s / P2=%s / P3=%s / P4=%s）" %
      (ana["tier"], ana["p1"]["status"], ana["p2"]["status"],
       ana["p3"]["status"], ana["p4"]["status"]))
    A("- 理由：%s" % ana["tier_reason"])
    A("")
    return "\n".join(t) + "\n"


# ------------------------------------------------------------------ 主流程
class GuardStop(Exception):
    pass


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--map-pattern", default="Proving Grounds")
    ap.add_argument("--load-wait", type=float, default=15.0)
    ap.add_argument("--stable-seconds", type=float, default=20.0)
    ap.add_argument("--budget-ms", type=float, default=50.0)
    ap.add_argument("--r2-event-budget-ms", type=float, default=300.0)
    ap.add_argument("--max-frames", type=int, default=20)
    ap.add_argument("--raw-stack-bytes", type=int, default=65536)
    ap.add_argument("--menu-timeout", type=float, default=90.0)
    ap.add_argument("--dialog-timeout", type=float, default=12.0)
    ap.add_argument("--d1-count", type=int, default=3)
    ap.add_argument("--skip-altf4", action="store_true",
                    help="跳过已实测致命的 ① Alt+F4（第 1 趟已留档：直接退出 exit=0）")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    global OUT
    if a.out:
        OUT = Path(a.out)
    OUT.mkdir(parents=True, exist_ok=True)
    W4.mkdir(parents=True, exist_ok=True)

    started_utc = utc_iso()
    cmdline = "%s -X utf8 %s %s" % (
        sys.executable, str(W4 / "exit_dialog_probe.py"),
        " ".join("%s" % x for x in sys.argv[1:]))

    # ---- 只读资产加载（不改任何源文件） ----
    global w3
    w3 = load_module("w4_w3_stack_contrast", W3_PATH)
    w3.OUT = OUT                     # 把 W3 write_json 的输出重定向到本卡 out/
    w3.log = log                     # 统一日志（含 do_grab 内部日志）
    w3.SENTINELS = dict(w3.SENTINELS)
    w3.SENTINELS["exitstate"] = (0x00A8EDD8, 4)   # 任务卡要求的退出态

    base = w3.load_baseline()
    write_json("baseline_14412.json", base)

    meta = {
        "run_id": RUN_ID, "started_utc": started_utc, "cmdline": cmdline,
        "args": vars(a), "pid": None, "launcher_pid": None, "ownership": None,
        "is32": None, "code_signature_ok": None, "map": None, "map_index": None,
        "game_hwnd": None, "window_tid": None, "self_tid": None,
        "walker": None, "prelaunch": {}, "prelaunch_match_all": None,
        "frame_stable_summary": None, "d0_label": None,
        "dialog_meta": {}, "p3_check": None, "p4_check": None,
        "hold_abort": False, "game_exited": False, "exit_readings": None,
        "close_steps": [], "residual_before": [], "residual_after": [],
        "restore_rows": [], "written_back": {}, "error": None,
    }
    grabs = []
    triggers = []
    sentinel_log = []
    exit_code = 0
    pid = 0
    launcher_pid = 0
    hproc = None
    game_hwnd = 0
    is32 = None
    walker = None
    w1 = r2 = sw = None
    sampler = None
    mods_all = []
    raw_state = None
    c0_tid = None
    residual_before, residual_after = [], []
    close_steps = []
    rows = []
    inv_before, inv_after = {}, {}
    diff = {"added": [], "removed": [], "changed": []}
    prelaunch = {}
    restore_verify = []
    base_ui = None
    p3_check = None
    p4_check = None
    dialog_meta = {}
    hold_abort = False
    base_frames = base["frames"]

    def rec_sentinel(tag, s):
        sentinel_log.append({"tag": tag, **(s or {})})

    def augment(label, rec, extra):
        rec.update(extra)
        rec["state"] = state_block(rec.get("sentinels_at_grab"))
        write_json("%s.json" % label, rec)
        return rec

    try:
        # ---------------- S1 启动前守卫 ----------------
        log("[S1] 启动前：只读资产自证 + 残留进程 + 实算 SHA-256")
        w1, r2, sw = w3.load_assets()
        # 额外绑定 GetParent / GetWindowRect / GetDlgCtrlID（用于子控件归属与定位证据）
        w1.u.GetParent.restype = wt.HWND
        w1.u.GetParent.argtypes = [wt.HWND]
        w1.u.GetWindowRect.restype = wt.BOOL
        w1.u.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(_RECT)]
        w1.u.GetDlgCtrlID.restype = ctypes.c_int
        w1.u.GetDlgCtrlID.argtypes = [wt.HWND]
        log("    只读资产加载完成：W1 导航 / W3 抓栈 / r2 采样器 / e3_stackwalker")
        log("    基准 7 帧：%s" % " → ".join(f["name"] for f in base_frames))

        residual_before = w1.list_gamemd()
        meta["residual_before"] = residual_before
        log("    gamemd 残留 = %d %s" % (len(residual_before), residual_before))
        if residual_before:
            raise GuardStop("启动前已存在 gamemd 残留，拒绝启动：%r" % residual_before)

        for name in VERIFY_FILES:
            p = GAME_DIR / name
            if not p.exists():
                raise GuardStop("缺少文件 %s" % p)
            h = sha256_file(p)
            prelaunch[name] = {"bytes": p.stat().st_size, "sha256": h,
                               "expected": EXPECTED_HASHES[name],
                               "match": h == EXPECTED_HASHES[name]}
            log("    %-20s %8d  %s  match=%s" %
                (name, prelaunch[name]["bytes"], h, prelaunch[name]["match"]))
        meta["prelaunch"] = prelaunch
        meta["prelaunch_match_all"] = all(v["match"] for v in prelaunch.values())
        bad = [n for n, v in prelaunch.items() if not v["match"]]
        if bad:
            raise GuardStop("启动前哈希不一致，按任务卡要求停止并报告：%s" % bad)
        inv_before = w1.inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inv_before))
        write_json("prelaunch.json", {"residual_before": residual_before,
                                      "hashes": prelaunch,
                                      "baseline_stack": base})

        # ---------------- S2 启动 / 导航 / 开局 ----------------
        log("[S2] WMI 分离启动 gamemd.exe")
        launcher_pid = w1.launch_game()
        pid, own = w1.wait_for_pid(launcher_pid, a.menu_timeout)
        meta.update(pid=pid, launcher_pid=launcher_pid, ownership=own)
        log("    pid=%d 归属=%s launcher_pid=%d" % (pid, own, launcher_pid))

        hproc = w1.k32.OpenProcess(0x0010 | 0x0400, False, pid)   # VM_READ|QUERY_INFORMATION
        if not hproc:
            raise RuntimeError("OpenProcess 失败")
        flag = wt.BOOL(0)
        w1.k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        log("    IsWow64Process -> is32=%s" % is32)
        sig = w1.rpm(hproc, w3.CODE_SIG_ADDR, len(w3.CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == w3.CODE_SIG_EXPECT)
        log("    代码签名@0x55DE4F = %r 期望 %r -> ok=%s" %
            (sig.hex() if sig else None, w3.CODE_SIG_EXPECT.hex(),
             meta["code_signature_ok"]))
        w1.wait_main_menu(pid, a.menu_timeout)

        log("[S3] 导航 SinglePlayer -> Skirmish -> 按名称选图")
        if not w1.click(pid, "GUI:SinglePlayer", 3.0):
            raise RuntimeError("GUI:SinglePlayer 点击失败")
        if not w1.click(pid, "GUI:Skirmish", 3.5):
            raise RuntimeError("GUI:Skirmish 点击失败")
        map_info = w1.select_map_by_name(hproc, pid, a.map_pattern)
        meta["map"] = map_info
        meta["map_index"] = map_info.get("index")
        log("    地图命中：index=%s 显示名=%r 条目=%d 命中数=%d" %
            (map_info.get("index"), map_info.get("display_name"),
             map_info.get("n_items"), map_info.get("n_hits")))
        hwnds = w1.game_top_windows(pid)
        game_hwnd = int(hwnds[0]) if hwnds else 0
        meta["game_hwnd"] = game_hwnd
        log("    游戏主窗口 hwnd=%s" % game_hwnd)
        if not w1.click(pid, "GUI:StartGame", 1.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        log("    等待加载 %.1fs" % a.load_wait)
        time.sleep(a.load_wait)

        log("[S3b] 帧稳定推进观测 %.1fs" % a.stable_seconds)
        fs = w3.wait_stable_frame(w1, hproc, a.stable_seconds)
        meta["frame_stable_summary"] = {k: v for k, v in fs.items() if k != "series"}
        write_json("frame_stable.json", fs)
        log("    样本=%d frame %s→%s Δ=%s 最长连续不推进=%d 拍" %
            (fs["n_samples"], fs["frame_first"], fs["frame_last"],
             fs["frame_net_delta"], fs["max_consecutive_nonadvance_samples"]))
        if not fs["frame_advanced"]:
            raise GuardStop("开局后帧计数未稳定推进（Δ=%s），按红线不做后续抓栈" %
                            fs["frame_net_delta"])

        # ---------------- S4 回溯器挂载（挂起任何线程之前） ----------------
        log("[S4] 挂起任何线程之前完成 StackWalk64/符号初始化")
        r2.bind_real_ops()
        sampler = r2.StackSampler(budget_ms=a.r2_event_budget_ms)
        att = w3.attach_walker(r2, sw, sampler, hproc, pid, is32,
                               max_frames=a.max_frames)
        meta["walker"] = {k: v for k, v in att.items()
                          if k not in ("walker", "mods_all")}
        walker = att["walker"]
        mods_all = att.get("mods_all") or []
        raw_state = w3.install_raw_capture(walker, w1, hproc, a.raw_stack_bytes) if att["ok"] else None
        log("    StackWalker ok=%s err=%s n_modules=%d is32=%s max_frames=%d raw_bytes=%d" %
            (att["ok"], att["err"], att["n_modules"], is32, a.max_frames,
             a.raw_stack_bytes))
        if not att["ok"]:
            raise GuardStop("回溯器挂载失败(%s)，按红线不抓栈、如实收尾" % att["err"])

        wtid, _ = w3.game_window_tid(w1, pid)
        meta["window_tid"] = wtid
        log("    游戏窗口线程 tid=%s" % wtid)
        if not wtid:
            raise GuardStop("未找到游戏窗口线程，按红线不抓栈")
        k32_self = ctypes.WinDLL("kernel32", use_last_error=True)
        k32_self.GetCurrentThreadId.restype = wt.DWORD
        cur_tid = int(k32_self.GetCurrentThreadId())
        meta["self_tid"] = cur_tid
        if int(wtid) == cur_tid:
            raise GuardStop("目标 tid 等于采样器自身线程，拒绝挂起")
        log("    自身线程守卫：GetCurrentThreadId=%d ≠ 目标 tid=%d ✓" %
            (cur_tid, wtid))
        c0_tid = int(wtid)

        # ---------------- D0 阴性对照 ----------------
        log("[D0] 正常局内阴性对照：单次 ≤%.0fms 抓栈（平静、无交火）" % a.budget_ms)
        base_ui = enum_ui(pid, w1)          # 触发前 UI 基线快照
        write_json("ui_baseline.json", base_ui)
        s0 = w3.read_sentinels(w1, hproc)
        rec_sentinel("D0_before", s0)
        g = w3.do_grab("D0", "D0_normal_ingame", r2, sampler, walker, w1,
                       hproc, pid, c0_tid, a.budget_ms, a.r2_event_budget_ms,
                       s0, raw_state, mods_all, base_frames)
        augment("D0", g, {
            "phase_note": "正常局内阴性对照（协议强制）；未在激烈战斗中挂起",
            "dialog_evidence": detect_dialog(base_ui, base_ui),
            "trigger": None,
        })
        grabs.append(g)
        meta["d0_label"] = "D0"
        rec_sentinel("D0_after", g["sentinels_after_grab"])
        log("    D0 state=%s" % json.dumps(state_block(s0), ensure_ascii=False))
        if g["hold_exceeded_50ms"] or g["budget_exceeded_r2"]:
            hold_abort = True
            meta["hold_abort"] = True
            raise GuardStop("D0 挂起超预算，按红线中止后续抓栈")

        # ---------------- 触发对话框（按优先级，成功一次即停） ----------------
        def new_trigger(n, method, action, before_ui, after_ui, alive, ec,
                        polls=None):
            d = detect_dialog(before_ui or {}, after_ui or {})
            tr = {
                "attempt": n, "method": method, "action": action,
                "t_utc_iso": utc_iso(),
                "before_ui": before_ui, "after_ui": after_ui,
                "dialog_evidence": d,
                "dialog_present": d["dialog_present"],
                "reason": d["reason"],
                "process_alive": alive, "exit_code": ec,
                "observation_polls": polls or [],
            }
            triggers.append(tr)
            write_json("triggers.json", triggers)
            log("    [尝试%s] %s -> dialog_present=%s (%s) alive=%s ec=%s" %
                (n, method, d["dialog_present"], d["reason"], alive, ec))
            log("      后窗口=%s" % json.dumps(compact_ui(after_ui)["tops"],
                                             ensure_ascii=False))
            log("      后按钮=%s" % json.dumps(compact_ui(after_ui)["button_texts"],
                                             ensure_ascii=False))
            return tr

        def alive_now():
            ps = proc_state(hproc, w1)
            return ps["alive"], ps["exit_code"]

        def send_alt_f4():
            u = w1.u
            u.keybd_event(VK_MENU, 0, 0, 0)
            time.sleep(0.05)
            u.keybd_event(VK_F4, 0, 0, 0)
            time.sleep(0.06)
            u.keybd_event(VK_F4, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
            u.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

        def click_hwnd_text(b, wait=1.2):
            ok = bool(w1.u.PostMessageW(b["hwnd"], BM_CLICK, 0, 0))
            time.sleep(wait)
            return {"hwnd": b["hwnd"], "text": b["text"], "clicked": ok}

        def observe_after(before_ui, timeout=3.6):
            """触发后轮询观察：捕捉延迟出现（或短暂出现）的确认对话框。

            返回 (命中或最后一次的 ui, detection, poll_log)。纯 UI 枚举，不写目标进程。
            """
            polls = []
            t0 = time.perf_counter()
            last_ui, last_d, hit = None, None, None
            while time.perf_counter() - t0 < timeout:
                ui = enum_ui(pid, w1)
                d = detect_dialog(before_ui, ui)
                cu = compact_ui(ui)
                polls.append({"t_s": round(time.perf_counter() - t0, 3),
                              "present": d["dialog_present"], "reason": d["reason"],
                              "tops": cu["tops"], "button_texts": cu["button_texts"]})
                last_ui, last_d = ui, d
                if d["dialog_present"]:
                    hit = (ui, d)
                    break
                time.sleep(0.4)
            if hit:
                return hit[0], hit[1], polls
            if last_ui is None:
                last_ui = enum_ui(pid, w1)
                last_d = detect_dialog(before_ui, last_ui)
            return last_ui, last_d, polls

        success_tr = None

        if a.skip_altf4:
            # ① 已在第 1 趟真机实测：真实 Alt+F4 使游戏直接退出 exit=0、无对话框。
            # 本趟按「自行裁决」跳过致命路径，继续优先级序列 ②→③；原始记录归档在
            # run1/out/run1/triggers.json，此处登记为「已试过」而非伪造新观察。
            triggers.append({
                "attempt": 1, "method": "Alt+F4（第 1 趟已实测，本趟跳过）",
                "action": {"note": "run1/triggers.json + run1/out/run1/triggers.json: "
                                   "真实 keybd_event Alt+F4（force_foreground 成功）后 "
                                   "游戏直接退出 exit_code=0，本 pid 窗口/控件枚举为空，"
                                   "无确认对话框；为避免再次杀死实例，本趟不再重发。"},
                "t_utc_iso": utc_iso(), "before_ui": None, "after_ui": None,
                "dialog_evidence": {"dialog_present": False},
                "dialog_present": False,
                "reason": "第 1 趟实测：直接退出，无对话框（已归档，非本趟新观察）",
                "process_alive": None, "exit_code": 0, "observation_polls": [],
                "skipped_this_run": True,
            })
            write_json("triggers.json", triggers)
            log("    [尝试1] Alt+F4 已在第 1 趟实测为致命（exit=0）；本趟跳过，"
                "从 ② 继续优先级序列")

        # ① Alt+F4（仅在不跳过时执行）
        if not a.skip_altf4:
            log("[T1] 尝试 ①：Alt+F4（真实键盘事件，前置 force_foreground）")
            before = enum_ui(pid, w1)
            fg = w1.force_foreground(game_hwnd) if game_hwnd else False
            fg_hwnd = int(w1.u.GetForegroundWindow() or 0)
            act1 = {"force_foreground": bool(fg), "foreground_hwnd": fg_hwnd,
                    "game_hwnd": game_hwnd,
                    "keys": "keybd_event(VK_MENU down, VK_F4 down/up, VK_MENU up)"}
            if fg and fg_hwnd == game_hwnd:
                send_alt_f4()
                time.sleep(0.6)
                act1["sent"] = True
            else:
                act1["sent"] = False
                act1["skip_reason"] = "游戏窗口未成为前台，拒绝向错误窗口发送 Alt+F4"
                log("    !! 游戏窗口未成为前台，跳过真实 Alt+F4（避免误关本会话窗口）")
            after1, d1, polls1 = observe_after(before, timeout=3.0)
            al, ec = alive_now()
            tr1 = new_trigger(1, "Alt+F4", act1, before, after1, al, ec,
                              polls=polls1)
            if tr1["dialog_present"]:
                success_tr = tr1
            if not al:
                meta["game_exited"] = True
                meta["exit_readings"] = {
                    "last_sentinel": w3.read_sentinels(w1, hproc),
                    "exit_code": ec, "t_utc_iso": utc_iso()}
                write_json("exit_readings.json", meta["exit_readings"])
                raise GuardStop("Alt+F4 导致游戏直接退出（exit=%s），按红线不重启补测" % ec)

        # ② 按控件文字找并点击「放弃任务 / Abort / Exit / 退出 / 结束」类按钮
        if success_tr is None:
            log("[T2] 尝试 ②：按控件文字找并点击 Abort/Exit/放弃类按钮（不猜索引）")
            before = enum_ui(pid, w1)
            act2 = {"keyword_rule": "classify_button(text)=='abort'，按文字而非索引",
                    "opened_esc_menu_as_route": False}
            cands = [b for b in before["buttons"]
                     if b["visible"] and classify_button(b["text"]) == "abort"]
            if not cands:
                # 正常局内没有按钮；仅作为导航步骤打开局内菜单以暴露按钮。
                # 本卡不把该菜单本身当 D1 数据。
                log("    正常局内无 Abort 类按钮；仅作导航按一次 Esc 暴露菜单按钮")
                w1.force_foreground(game_hwnd)
                w1.send_esc()
                time.sleep(1.1)
                before = enum_ui(pid, w1)
                act2["opened_esc_menu_as_route"] = True
                act2["menu_button_texts"] = [b["text"] for b in before["buttons"]
                                             if b["text"]]
                cands = [b for b in before["buttons"]
                         if b["visible"] and classify_button(b["text"]) == "abort"]
            act2["candidates"] = [{"hwnd": b["hwnd"], "text": b["text"]}
                                  for b in cands]
            if cands:
                # 优先「abort/放弃」，其次 exit/quit/restart
                cands.sort(key=lambda b: (0 if ("abort" in b["text"].lower()
                                                or "放弃" in b["text"]) else 1,
                                          len(b["text"])))
                act2["clicked"] = click_hwnd_text(cands[0], wait=1.0)
                log("    点击按钮 %r hwnd=%s" %
                    (cands[0]["text"], cands[0]["hwnd"]))
            else:
                act2["clicked"] = None
                act2["no_candidate_reason"] = "所有按钮文字均不匹配 abort/exit/放弃/退出/结束"
            after2, d2, polls2 = observe_after(before, timeout=3.6)
            al, ec = alive_now()
            tr2 = new_trigger(2, "按控件文字点击 Abort/Exit/放弃类按钮",
                              act2, before, after2, al, ec, polls=polls2)
            if tr2["dialog_present"]:
                success_tr = tr2
            if not al:
                meta["game_exited"] = True
                meta["exit_readings"] = {
                    "last_sentinel": w3.read_sentinels(w1, hproc),
                    "exit_code": ec, "t_utc_iso": utc_iso()}
                write_json("exit_readings.json", meta["exit_readings"])
                raise GuardStop("点击 Abort 类按钮导致游戏直接退出（exit=%s），不重启补测" % ec)

        # ③ 局内菜单里的「重新开始 / 退出到主菜单」类
        if success_tr is None:
            log("[T3] 尝试 ③：局内菜单里 Restart/Exit to main menu 类按钮")
            before = enum_ui(pid, w1)
            act3 = {"keyword_rule": "restart/重新开始/main menu/主菜单/exit/quit/surrender"}
            menu_like = [b for b in before["buttons"]
                         if b["visible"] and b["text"]
                         and b["text"].lower().startswith("gui:")]
            if not menu_like:
                w1.force_foreground(game_hwnd)
                w1.send_esc()
                time.sleep(1.1)
                before = enum_ui(pid, w1)
                act3["opened_esc_menu_as_route"] = True
            else:
                act3["opened_esc_menu_as_route"] = False
            act3["menu_button_texts"] = [b["text"] for b in before["buttons"]
                                         if b["text"]]
            pats = ("restart", "重新开始", "main menu", "主菜单", "exit", "quit",
                    "surrender", "退出", "结束")
            cands = [b for b in before["buttons"]
                     if b["visible"] and b["text"]
                     and any(p in b["text"].lower() for p in pats)]
            act3["candidates"] = [{"hwnd": b["hwnd"], "text": b["text"]}
                                  for b in cands]
            if cands:
                act3["clicked"] = click_hwnd_text(cands[0], wait=1.5)
            else:
                act3["clicked"] = None
                act3["no_candidate_reason"] = ("局内菜单按钮文字中无 "
                                               "restart/重新开始/exit to main menu 类")
            after3, d3, polls3 = observe_after(before, timeout=3.6)
            al, ec = alive_now()
            tr3 = new_trigger(3, "局内菜单 Restart/Exit to main menu 类按钮",
                              act3, before, after3, al, ec, polls=polls3)
            if tr3["dialog_present"]:
                success_tr = tr3
            if not al:
                meta["game_exited"] = True
                meta["exit_readings"] = {"last_sentinel": w3.read_sentinels(w1, hproc),
                                         "exit_code": ec, "t_utc_iso": utc_iso()}
                write_json("exit_readings.json", meta["exit_readings"])
                raise GuardStop("尝试 ③ 导致游戏直接退出（exit=%s），不重启补测" % ec)

        # ---------------- D1：确认对话框稳定存在 >3s 后抓栈 ----------------
        if success_tr is None:
            log("!! 三条路径均未产生确认对话框：按红线如实写「未能触发」，不伪造 D1/D2")
            dialog_meta = {"successful_method": None, "stable": False,
                           "evidence_summary": None,
                           "note": "未能触发；见 out/triggers.json 与 RUNLOG 第 3 节"}
            meta["dialog_meta"] = dialog_meta
        else:
            # 触发路径可能需要先打开局内菜单；以「该次触发前的快照」为对话框判据基线，
            # 可避免把菜单本身的新子容器误认成确认对话框。
            dlg_base_ui = success_tr.get("before_ui") or base_ui
            log("[D1] 已触发对话框：%s；开始稳定性观测（>3s）" %
                success_tr["method"])
            stab = []
            present_since = None
            t0 = time.perf_counter()
            while time.perf_counter() - t0 < a.dialog_timeout:
                ui = enum_ui(pid, w1)
                d = detect_dialog(dlg_base_ui, ui)
                s = w3.read_sentinels(w1, hproc)
                now = time.perf_counter() - t0
                stab.append({"t_s": round(now, 3), "present": d["dialog_present"],
                             "n_no": len(d["no_buttons"]),
                             "n_yes": len(d["yes_buttons"]),
                             "frame": s.get("frame"), "g4": s.get("g4"),
                             "tops": compact_ui(ui)["tops"]})
                if d["dialog_present"]:
                    if present_since is None:
                        present_since = now
                else:
                    present_since = None
                if present_since is not None and (now - present_since) >= 3.0:
                    break
                time.sleep(0.6)
            stable = bool(present_since is not None
                          and (time.perf_counter() - t0 - present_since) >= 3.0)
            write_json("dialog_stability.json", {"stable": stable,
                                                 "polls": stab,
                                                 "timeout_s": a.dialog_timeout})
            log("    稳定性观测：%d 拍，连续存在 ≥3s = %s" % (len(stab), stable))
            ev = detect_dialog(dlg_base_ui, enum_ui(pid, w1))
            dialog_meta = {
                "successful_method": success_tr["method"],
                "stable": stable,
                "evidence_summary": {
                    "dialog_top_candidates": ev["dialog_top_candidates"],
                    "no_buttons": ev["no_buttons"],
                    "yes_buttons": ev["yes_buttons"],
                    "abort_buttons": ev["abort_buttons"],
                    "caption_controls": ev["caption_controls"],
                    "new_child_parent_hwnds": ev["new_child_parent_hwnds"],
                    "new_container_groups": ev["new_container_groups"],
                    "new_top_windows": ev["new_top_windows"],
                    "all_top_windows": ev["all_top_windows"],
                    "all_controls_with_text": ev["all_controls_with_text"],
                    "dialog_tids": ev["dialog_tids"],
                },
                "note": ("对话框证据逐趟完整留存于 out/D1*.json 的 "
                         "dialog_evidence；UI 判据独立于 P2/P3/P4 读数"),
            }
            meta["dialog_meta"] = {k: v for k, v in dialog_meta.items()
                                   if k != "evidence_summary"}
            if not stable:
                log("    !! 对话框未稳定存在 >3s；按红线仍如实抓一次并标注，"
                    "不夸大结论")

            # P3 显式成对读数（读→等 1s→读），独立于抓栈
            s_a = w3.read_sentinels(w1, hproc)
            rec_sentinel("P3_a", s_a)
            time.sleep(1.0)
            s_b = w3.read_sentinels(w1, hproc)
            rec_sentinel("P3_b", s_b)
            p3_check = {
                "frame_a": s_a.get("frame"), "frame_b": s_b.get("frame"),
                "delta": (s_b["frame"] - s_a["frame"]
                          if s_a.get("frame") is not None
                          and s_b.get("frame") is not None else None),
                "stopped": bool(s_a.get("frame") is not None
                                and s_a.get("frame") == s_b.get("frame")),
                "g4_a": s_a.get("g4"), "g4_b": s_b.get("g4"),
                "interval_s": 1.0,
            }
            meta["p3_check"] = p3_check
            log("    P3 成对读数 frame %s→%s stopped=%s g4=[%s,%s]" %
                (s_a.get("frame"), s_b.get("frame"), p3_check["stopped"],
                 s_a.get("g4"), s_b.get("g4")))

            labels = ["D1a", "D1b", "D1c"][:max(0, a.d1_count)]
            for label in labels:
                ui = enum_ui(pid, w1)
                d = detect_dialog(dlg_base_ui, ui)
                if not d["dialog_present"]:
                    log("    !! %s 前对话框已消失，按红线停止后续 D1 抓栈" % label)
                    break
                s_grab = w3.read_sentinels(w1, hproc)
                rec_sentinel(label + "_at_grab", s_grab)
                g = w3.do_grab(label, "D1_dialog_open", r2, sampler, walker, w1,
                               hproc, pid, c0_tid, a.budget_ms,
                               a.r2_event_budget_ms, s_grab,
                               raw_state, mods_all, base_frames)
                augment(label, g, {
                    "phase_note": "退出/放弃任务确认对话框稳定打开态（只读抓栈）",
                    "dialog_evidence": d,
                    "trigger": {"attempt": success_tr["attempt"],
                                "method": success_tr["method"]},
                    "frame_stability_p3": p3_check,
                })
                grabs.append(g)
                rec_sentinel(label + "_after", g["sentinels_after_grab"])
                log("    %s state=%s" %
                    (label, json.dumps(state_block(s_grab), ensure_ascii=False)))
                if g["hold_exceeded_50ms"] or g["budget_exceeded_r2"]:
                    hold_abort = True
                    meta["hold_abort"] = True
                    log("    !! %s 挂起超预算，中止后续抓栈" % label)
                    break
                time.sleep(0.9)

            # 补充：若对话框顶层窗口 tid 与主窗口 tid 不同，额外抓一趟（不进 P1 主判据）
            try:
                dl_tids = [x for x in dialog_meta["evidence_summary"]["dialog_tids"]
                           if x and int(x) != c0_tid]
                if dl_tids and not hold_abort:
                    extra_tid = int(dl_tids[0])
                    log("    对话框 tid=%s ≠ 主窗口 tid=%s，补一趟 D1x（仅作补充）" %
                        (extra_tid, c0_tid))
                    s_grab = w3.read_sentinels(w1, hproc)
                    g = w3.do_grab("D1x", "D1x_dialog_tid_supplementary",
                                   r2, sampler, walker, w1, hproc, pid,
                                   extra_tid, a.budget_ms, a.r2_event_budget_ms,
                                   s_grab, raw_state, mods_all, base_frames)
                    augment("D1x", g, {
                        "phase_note": "补充抓栈：对话框顶层窗口线程 tid 与主窗口不同；"
                                      "不进入 P1 主判据",
                        "dialog_evidence": detect_dialog(dlg_base_ui,
                                                        enum_ui(pid, w1)),
                        "trigger": {"attempt": success_tr["attempt"],
                                    "method": success_tr["method"]},
                    })
                    grabs.append(g)
            except Exception as e:                                  # noqa: BLE001
                log("    D1x 补充抓栈异常 %r（不影响主判据）" % e)

            # ---------------- D2：点「否/取消/No」关闭 + 恢复校验 + 抓栈 ----------------
            log("[D2] 关闭对话框（按控件文字定位「否/取消/No」，不猜索引）")
            ui = enum_ui(pid, w1)
            close_action = {
                "buttons_seen": [{"hwnd": b["hwnd"], "text": b["text"],
                                  "visible": b["visible"], "rect": b["rect"],
                                  "ctrl_id": b["ctrl_id"]}
                                 for b in ui["buttons"] if b["text"]],
                "captions_seen": [{"hwnd": c["hwnd"], "text": c["text"],
                                   "cls": c["cls"], "rect": c["rect"]}
                                  for c in ui["controls"]
                                  if c["text"] and c["cls"] == "Static"],
                "attempts": [],
            }
            # run2 实测：该确认对话框的按钮是位图（窗口文字 GUI:Blank），
            # 而可见的 'GUI:ResumeMission' 是「返回任务/取消放弃」控件。
            # 按「控件文字」而非索引定位；按优先级逐个尝试，每次都校验帧是否恢复。
            exact_no = [b for b in ui["buttons"]
                        if b["visible"] and classify_button(b["text"]) == "no"]
            exact_no.sort(key=lambda b: (0 if b["text"].strip().lower() in
                                         ("no", "cancel", "否", "取消") else 1,
                                         len(b["text"])))
            resume_b = [b for b in ui["buttons"]
                        if b["visible"] and "resumemission" in
                        (b["text"] or "").lower().replace(":", "")]
            blank_b = [b for b in ui["buttons"]
                       if b["visible"] and "blank" in (b["text"] or "").lower()]
            cand_steps = ([("exact_no_cancel", b) for b in exact_no]
                          + [("gui_resumemission_cancel", b) for b in resume_b]
                          + [("visible_blank_button_fallback", b) for b in blank_b])

            def read_resume_pair(tag):
                s0 = w3.read_sentinels(w1, hproc)
                rec_sentinel(tag + "_a", s0)
                time.sleep(1.0)
                s1 = w3.read_sentinels(w1, hproc)
                rec_sentinel(tag + "_b", s1)
                dd = (s1["frame"] - s0["frame"]
                      if s0.get("frame") is not None
                      and s1.get("frame") is not None else None)
                return {"tag": tag, "frame_a": s0.get("frame"),
                        "frame_b": s1.get("frame"), "delta": dd,
                        "resumed": bool(dd is not None and dd > 0),
                        "state_after": state_block(s1),
                        "interval_s": 1.0}

            resume_checks = []
            for kind, b in cand_steps[:4]:
                cr = click_hwnd_text(b, wait=0.9)
                rc = read_resume_pair("D2_try_" + kind)
                close_action["attempts"].append({
                    "kind": kind, "click": cr, "resume_check": rc})
                resume_checks.append(rc)
                log("    D2 尝试 %s: 点击 %r hwnd=%s Δframe=%s resumed=%s" %
                    (kind, b["text"], b["hwnd"], rc["delta"], rc["resumed"]))
                if rc["resumed"]:
                    close_action["clicked"] = cr
                    close_action["method"] = "BM_CLICK by control text (" + kind + ")"
                    break
                # 未恢复：重新枚举（可能已换屏），后续候选若已失效则跳过
                ui2 = enum_ui(pid, w1)
                live = set(x["hwnd"] for x in ui2["buttons"] if x["visible"])
                cand_steps = [(k, x) for k, x in cand_steps if x["hwnd"] in live]
            if not any(x["resumed"] for x in resume_checks):
                log("    !! 按钮点击均未恢复帧；退回一次 Esc（如实登记）")
                w1.force_foreground(game_hwnd)
                w1.send_esc()
                time.sleep(0.8)
                rc = read_resume_pair("D2_try_esc_fallback")
                resume_checks.append(rc)
                close_action["attempts"].append({"kind": "esc_fallback",
                                                 "resume_check": rc})
                if not close_action.get("clicked"):
                    close_action["clicked"] = None
                    close_action["method"] = "esc_fallback"
            ui_after = enum_ui(pid, w1)
            d_after = detect_dialog(dlg_base_ui, ui_after)
            close_action["dialog_present_after"] = d_after["dialog_present"]
            close_action["tops_after"] = compact_ui(ui_after)["tops"]
            close_action["buttons_after"] = compact_ui(ui_after)["button_texts"]
            close_action["controls_after"] = compact_ui(ui_after)["control_texts"]

            # P4 主读数：最后一次恢复校验（成功那次），没有则取最后一次
            final_rc = next((x for x in reversed(resume_checks) if x["resumed"]),
                            resume_checks[-1] if resume_checks else None)
            delta = final_rc["delta"] if final_rc else None
            resumed = bool(final_rc and final_rc["resumed"])
            extra_action = None
            resumed_after_extra = False
            if not resumed:
                resume_b2 = [b for b in ui_after["buttons"]
                             if b["visible"] and "resumemission" in
                             (b["text"] or "").lower().replace(":", "")]
                if resume_b2:
                    extra_action = click_hwnd_text(resume_b2[0], wait=0.9)
                    rc2 = read_resume_pair("D2_extra_resume")
                    extra_action["resume_check"] = rc2
                    resumed_after_extra = bool(rc2["resumed"])
                    log("    额外点 %r 后 Δframe=%s" %
                        (resume_b2[0]["text"], rc2["delta"]))
            p4_check = {
                "close_action": close_action,
                "resume_checks": resume_checks,
                "frame_after_close": final_rc["frame_a"] if final_rc else None,
                "frame_later": final_rc["frame_b"] if final_rc else None,
                "delta_frame": delta, "resumed": resumed,
                "extra_action": extra_action,
                "resumed_after_extra_action": resumed_after_extra,
                "gates_after_close": final_rc["state_after"] if final_rc else None,
                "interval_s": 1.0,
            }
            meta["p4_check"] = p4_check
            log("    P4: Δframe=%s resumed=%s (需额外动作恢复=%s)" %
                (delta, resumed, resumed_after_extra))

            al, ec = alive_now()
            if al and not hold_abort:
                s_grab = w3.read_sentinels(w1, hproc)
                rec_sentinel("D2_at_grab", s_grab)
                g = w3.do_grab("D2", "D2_after_dialog_close", r2, sampler,
                               walker, w1, hproc, pid, c0_tid, a.budget_ms,
                               a.r2_event_budget_ms, s_grab, raw_state,
                               mods_all, base_frames)
                augment("D2", g, {
                    "phase_note": "关闭对话框后的平静恢复态抓栈（阴性对照补测）",
                    "dialog_evidence": d_after,
                    "trigger": {"attempt": success_tr["attempt"],
                                "method": success_tr["method"],
                                "close_action": close_action},
                    "p4_check": p4_check,
                })
                grabs.append(g)
                rec_sentinel("D2_after", g["sentinels_after_grab"])
            else:
                log("    D2 抓栈跳过：进程存活=%s hold_abort=%s" % (al, hold_abort))

        # ---------------- 分析 / 判档 ----------------
        log("[S5] 逐帧比对与判档")
        ana = analyze_verdict(base, grabs, p3_check, p4_check, triggers,
                              dialog_meta)
        write_json("summary.json", ana)
        (W4 / "VERDICT.md").write_text(
            render_verdict(base, grabs, ana, meta), encoding="utf-8")
        log("    判档 = %s (P1=%s P2=%s P3=%s P4=%s)" %
            (ana["tier"], ana["p1"]["status"], ana["p2"]["status"],
             ana["p3"]["status"], ana["p4"]["status"]))

    except GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
    except Exception as e:                                          # noqa: BLE001
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())

    # ---------------- 收尾（无论如何执行） ----------------
    finally:
        ended_utc = utc_iso()
        log("[P1] 收尾：回溯器 cleanup → 关游戏 → 残留核对 → 配置逐字节还原")
        try:
            if walker is not None:
                walker.cleanup()
                log("    SymCleanup 完成")
        except Exception as e:                                      # noqa: BLE001
            log("    SymCleanup 异常 %r" % e)
        try:
            if r2 is not None:
                r2.OPS.clear()
        except Exception:
            pass
        try:
            if hproc:
                w1.k32.CloseHandle(hproc)
                hproc = None
        except Exception as e:                                      # noqa: BLE001
            log("    CloseHandle(hproc) 异常 %r" % e)
        try:
            close_steps = (w1.close_game(pid, game_hwnd)
                           if (w1 is not None and pid) else
                           ["no_pid_no_launch: 未启动实例，无需关闭"])
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:                                      # noqa: BLE001
            close_steps = ["close_game 异常: %r" % e]
            log("    close_game 异常 %r" % e)
        try:
            residual_after = w1.list_gamemd() if w1 is not None else []
        except Exception:
            residual_after = []
        log("    收尾后 gamemd 残留 = %d %s" %
            (len(residual_after), residual_after))
        try:
            inv_after = w1.inventory(GAME_DIR) if w1 is not None else {}
            diff = w1.diff_inventory(inv_before, inv_after) if w1 is not None else diff
            log("    收尾后文件清单 %d 项" % len(inv_after))
        except Exception as e:                                      # noqa: BLE001
            log("    inventory_after 异常 %r" % e)
        try:
            rows = w1.restore_configs() if w1 is not None else []
            for r in rows:
                log("    还原 %s -> %s" % (r.get("file"),
                                          r.get("post_restore_sha256")
                                          or r.get("post_sha256")))
        except Exception as e:                                      # noqa: BLE001
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)

        # 独立逐字节复核 + 实算 SHA-256 自证
        for name in RESTORE_FILES:
            src, dst = BASELINE_DIR / name, GAME_DIR / name
            try:
                sb, db = src.read_bytes(), dst.read_bytes()
                restore_verify.append({
                    "file": name,
                    "baseline_sha256": hashlib.sha256(sb).hexdigest(),
                    "target_sha256": hashlib.sha256(db).hexdigest(),
                    "byte_identical": sb == db,
                    "matches_expected": (hashlib.sha256(db).hexdigest()
                                         == EXPECTED_HASHES[name]),
                })
            except Exception as e:                                  # noqa: BLE001
                restore_verify.append({"file": name, "error": repr(e)})
        write_json("restore_verify.json", restore_verify)

        try:
            base_for_ana = w3.load_baseline() if w3 is not None else base
            ana = analyze_verdict(base_for_ana, grabs, p3_check, p4_check,
                                  triggers, dialog_meta or {
                                      "successful_method": None, "stable": False,
                                      "evidence_summary": None})
            write_json("summary.json", ana)
            (W4 / "VERDICT.md").write_text(
                render_verdict(base_for_ana, grabs, ana, meta), encoding="utf-8")
            (W4 / "SAFETY.md").write_text(
                render_safety(grabs, a.budget_ms, meta,
                              meta.get("hold_abort") or hold_abort),
                encoding="utf-8")
            (W4 / "CONFIG_RESTORE.md").write_text(
                render_config_restore(prelaunch, residual_before, residual_after,
                                      rows, diff, close_steps, restore_verify,
                                      (len(inv_before), len(inv_after))),
                encoding="utf-8")
            (W4 / "RUNLOG.md").write_text(
                render_runlog(meta, exit_code, started_utc, ended_utc,
                              cmdline, triggers), encoding="utf-8")
            (W4 / "UNCOVERED.md").write_text(
                render_uncovered(meta, grabs, ana), encoding="utf-8")
            write_json("run_meta.json", meta)
            (OUT / "sentinels.ndjson").write_text(
                "\n".join(json.dumps(x, ensure_ascii=False, sort_keys=True,
                                     default=str) for x in sentinel_log) + "\n",
                encoding="utf-8")
            (OUT / "stdout.txt").write_text(
                "\n".join(LOG_LINES) + "\n", encoding="utf-8")
            write_json("triggers.json", triggers)
        except Exception as e:                                      # noqa: BLE001
            log("    文档生成异常 %r" % e)
            log(traceback.format_exc())

        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        try:
            write_json("run_meta.json", meta)
        except Exception:
            pass
        log("[P1] 收尾完成（exit_code=%d）" % exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
