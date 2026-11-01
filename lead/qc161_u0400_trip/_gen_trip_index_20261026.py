# -*- coding: utf-8 -*-
"""C26 轮全趟索引生成器（REVIEW_S438 账目项：不覆盖旧 summary，从逐趟 _rec.json 原件生成）。

只读 _rec.json / measure_w*.json / _launch_result.json ⇒ 产出
lead/qc161_u0400_trip/c2ab/TRIP_INDEX_20261026.md。零游戏、零写他域。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
C2AB = ROOT / "lead/qc161_u0400_trip/c2ab"
LAUNCH = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def rd(p):
    return json.loads(p.read_text(encoding="utf-8"))

rows = []

# —— ② c2ab 六趟 ——
for d in sorted(C2AB.glob("*_c2")):
    r = rd(d / "_rec.json")
    lp = r.get("layout_pre_close") or {}
    rows.append({
        "trip_id": d.name, "line": "② A/B", "arm": "CTRL" if r["tag"].startswith("CTRL") else "MAIN",
        "config": "Guard=%s Bail=%s Dry=%s" % (r["guard_enable"], r["exitbail_enable"], r["dry_run"]),
        "exited": r.get("exited_within_watch"),
        "after_s": r.get("exit_after_close_s"),
        "exitcode": r.get("final_exitcode"),
        "n_sample": r.get("n_sample"),
        "layout_ok": lp.get("ok"),
        "except_changed": r.get("except_changed"),
        "a8": r.get("a8_verdict"), "carrier_del": r.get("carrier_deleted"),
        "wall_s": r.get("wall_s"),
        "validity": "有效",
        "xverify": "覆盖（V2/V3/V4，XVERIFY_C2AB_20261026.md 全 CONFIRMED）",
    })
for d in sorted(C2AB.glob("*_L1REG")):
    r = rd(d / "_rec.json")
    lp = r.get("layout_pre_close") or {}
    lp2 = r.get("layout_post_close_alive") or {}
    rows.append({
        "trip_id": d.name, "line": "② L1REG（局内关窗）",
        "arm": "MAIN配置进局",
        "config": "Guard=1 Bail=1 Dry=0 + harness7 导航三连",
        "exited": r.get("exited_within_watch"),
        "after_s": r.get("exit_after_close_s"),
        "exitcode": r.get("final_exitcode"),
        "in_battle": r.get("in_battle"),
        "frame_adv": r.get("frame_advance_total"),
        "play_wall": r.get("play_wall_s"),
        "layout_live": r.get("hook_live_during_play"),
        "exitstate_play": r.get("exitstate_during_play"),
        "except_changed": r.get("except_changed"),
        "except_keys_present": ("except_after" in r),
        "a8": r.get("a8_verdict"), "carrier_del": r.get("carrier_deleted"),
        "validity": "有效（R3=关窗后20s自然退出判据不成立）",
        "xverify": ("161412：首份判定书 V6 审过（except 直接通道 UNVERIFIABLE）"
                    if "161412" in d.name else
                    "200938：**待异族补核**（XVERIFY_L1REG2 在途/待落）"),
    })

# —— ① e 系列 ——
for suf, kind in (("e1", "短路臂"), ("e4", "keep-rect 对照臂")):
    p = LAUNCH / ("l1_20261023%s" % suf)
    if not p.is_dir():
        continue
    res = rd(p / "_launch_result.json") if (p / "_launch_result.json").exists() else {}
    gate = {}
    stat = {}
    mp = p / "measure_w0.json"
    if mp.exists():
        m = rd(mp)
        gate = m.get("gate", {})
        stat = {k: m.get("stats", {}).get(k) for k in
                ("fps_avg", "frame_ms_p50", "frame_ms_p90", "frame_ms_p99",
                 "frame_ms_max", "tick_miss", "logic_frames", "max_stall_s")}
    rows.append({
        "trip_id": "l1_20261023%s" % suf, "line": "① 环境门（%s）" % kind,
        "arm": "Arm A 直启零注入",
        "config": "harness7 %s / --measure 1 / fullscreen" % (
            "d019e8be（短路缺省）" if suf == "e1" else "d019e8be + --h7-keep-rect-wait"),
        "rc": res.get("rc", res.get("exit_code")),
        "gate_pre_fps15": gate.get("pre_fps15"), "units0": gate.get("units0"),
        "gate_ok": gate.get("ok"),
        "w0": stat,
        "validity": ("作废（units0=0/no_advance，档位证据未取得）" if suf == "e1"
                     else "有效（pre_fps15≥25 ⇒ 本会话 31 档可判；W0 受测窗未复现严重停顿）"),
        "xverify": "① 未独立核验——**单列状态：待独立核验**（不受②判定书覆盖）",
    })

# argparse 失败两例（非趟）
rows.append({"trip_id": "e2/e3（未成行）", "line": "① 发射尝试",
             "arm": "-", "config": "--extra-argv \"--h7-keep-rect-wait\"（空格分隔值）",
             "validity": "非趟（launcher argparse 在预检前拒收，rc=2 零副作用、无载体无进程）",
             "xverify": "-"})

# —— 离线非趟件（不计趟数，但登记在盘）——
rows.append({"trip_id": "gate_rerun_20261026", "line": "② 离线",
             "validity": "非趟（工件门禁复跑 14/14 PASS rc=0）",
             "path": str(C2AB.parent / "d09a_c2_candidate/_gate_rerun_20261026.out")})

out = ["# C26 轮全趟索引（2026-10-26，生成件 `_gen_trip_index_20261026.py`，数据源=逐趟 `_rec.json` 原件）",
       "",
       "趟数终账：**有效 7（②6 + ①1）/ 作废 1（e1）/ 非趟 3（e2、e3 参数失败；gate_rerun 离线）**。",
       "本索引不替代也不删除任何原始记录；`c2ab_summary.json` 系第二遍 A/B 时被覆写——",
       "首批两趟原件在 `_rec.json` 目录内完整在盘（本索引逐条列路径）。",
       "",
       "| trip_id | 线/臂 | 配置 | 关窗后自然退出 | exitcode | 布局/进局 | except | a8/载体 | 有效性 | 异族核验覆盖 |",
       "|--|--|--|--|--|--|--|--|--|--|"]
for r in rows:
    exitc = r.get("exited")
    exit_txt = ("**%s s 退出**" % r["after_s"]) if exitc else ("150 s 未退" if exitc is False else "-")
    lay = []
    if "layout_ok" in r: lay.append("hook/cave=%s" % r["layout_ok"])
    if "in_battle" in r: lay.append("in_battle=%s" % r["in_battle"])
    if "frame_adv" in r: lay.append("帧+%s/%ss" % (r["frame_adv"], r["play_wall"]))
    exc = r.get("except_changed", r.get("except_keys_present"))
    exc_txt = {True: "变 ★", False: "不变"}.get(r.get("except_changed"),
              "键缺失(161412)" if r.get("except_keys_present") is False else "-")
    if r.get("except_keys_present") is True and r.get("except_changed") is False:
        exc_txt = "前后哈希相等（6694b75e…）"
    cfg = r.get("config", "-")
    if r.get("gate_pre_fps15") is not None:
        w0 = r.get("w0", {})
        def _f(x):
            return ("%.1f" % x) if isinstance(x, (int, float)) else x
        cfg += "；gate: pre_fps15=%s units0=%s ok=%s / W0 p50=%s p99=%s max=%s mf=%s" % (
            _f(r["gate_pre_fps15"]), r.get("units0"), r.get("gate_ok"),
            _f(w0.get("frame_ms_p50")), _f(w0.get("frame_ms_p99")), _f(w0.get("frame_ms_max")),
            w0.get("logic_frames"))
    out.append("| %s | %s | %s | %s | %s | %s | %s | %s/%s | %s | %s |" % (
        r["trip_id"], r.get("arm", "-"), cfg, exit_txt,
        r.get("exitcode", r.get("rc", "-")),
        " ".join(lay) or "-", exc_txt, r.get("a8", "-"), r.get("carrier_del", "-"),
        r["validity"], r.get("xverify", "-")))

out += ["",
        "## 口径备注（REVIEW_S438 逐条落地）",
        "- **事件日志零命中**（13:32–13:48 / 16:14–16:26）=「查询时窗内未观察到登记事件」，",
        "  **不**证明无 AV；except/直接异常/进程状态三通道证据力各报各的。",
        "- **exitstate 恒 0**（200938 close 后）= 采样未观察到闩 1，**不能**据此定位断点、",
        "  不能推出 c″ 未触发或「必在 0x6BE0B6 之前」——C26-06 离线分析任务书据此收紧。",
        "- **PostMessageW 返回值未入 161412/200938 记录**=投递≠处理，装置有效性未闭合；",
        "  观测驱动候选（_drive_c2_x_probe.py）已补记返回值+错误+hwnd/pid/tid。",
        "- 「缺省 0」实证状态：**未验证**——CTRL 是显式写 0（非键缺失）；两件事分报。",
        "- ① e4：W0 数字来自来源线原件**未逐项异族复算**；W1（logic_frames=-3557）/W2（0 帧）",
        "  自性能样本**剔除**；「自然终局」归因未闭合（待场景证据）。",
        ""]

target = C2AB / "TRIP_INDEX_20261026.md"
target.write_text("\n".join(out), encoding="utf-8", newline="\n")
print("wrote", target, target.stat().st_size, "bytes;", len(rows), "rows")
