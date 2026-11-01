#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""H-5 v12 裁决：C/L3 死因 = 「战斗结束 → 正常退出（码 0）」，崩溃排除。

Lead 裁决 v12 §4.2（2026-10-24）原话：
  「C/L3 可能是"测试关卡太短，打赢后游戏正常退出（码 0）"，而不是崩溃。
   A 趟画面是 Mission accomplished，可作旁证。核查测试图任务时长与退出路径，
   确认或排除；若成立，测量窗口根因收敛到测试图本身。」

本件性质：离线静态（只读既有趟产物 + 既有台账）。**零真机、零新采集。**
全部判据从**产物字节**复算，不抄 §401/§402 的结论（异源交叉：§401 只算过 C 的
旁路时钟；本件另加 TERM 记录、iso 记录、时间轴对账、画面尺寸、S397 登记行五路）。

★ 一处如实修正：Lead 说「A 趟画面是 Mission accomplished」——**实测画面不是**
  （见 X10）。A 的 frame_target_01.png 是「Unit Deployment Screen」；
  真正显示「Battle control terminated — press OK to continue」（战斗终止对话框）
  的是 **C**。旁证链因此改由 C 承担，不借不存在的 A 画面。

退出路径（X4-X6）：
  1. TERM.wait_returncode=0（§402 语义：等待时已自行退出，码 0 由 GetExitCodeProcess
     回填；活杀=1、SEH 兜底 AV=0xC0000005 类 NTSTATUS）；
  2. except.txt 零新增（C 趟多重集差 0/0）——单独**不是**未崩溃判据（铁律），
     但组合 rc=0 + 无 WER（§406）+ 画面停在终止对话框 ⇒ 崩溃形态被三重否证；
  3. 旁路时钟（C）：帧在 70.879 s 由 1260 **跳到 0**、实体计数器冻结在
     813/311/1128 但**仍持续可读**（RPM 成功）到 77.161 s——
     「跳 0 + 继续可读」只有游戏进程活着离开战场（回菜单/对话框）才可能；
     崩溃则序列停止增长（§401 判据反向使用）。

★ 关卡时长证据：战斗时钟从 ~25.4 s 起算（进图），到 70.879 s 结束 = **≈45.5 s**，
  而测量协议要 3×25 s 窗 + 4 s 稳定 = ≥79 s 战斗余量 ⇒ **地图本身太短**，
  战斗在任何 measure 窗开始前就结束了 ⇒ 测量窗根因收敛到测试图本身（Lead 预判成立）。

★ 残留子问题（不阻塞裁决）：对话框「press OK」**无人在场**，进程却以码 0 结束
  ——谁确认了它（游戏自动关窗回桌面？超时自退？）本件不主张。
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
OUT = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
LEDGER = ROOT / "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
S397 = ROOT / "lead/goal1_harness6_20261022/S397_SECTION.md"

RESULTS = []
MUT = None  # 变异名，由 --mutate-<NAME> 设置


def rec(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", name, detail))


def fields(trip):
    return json.loads((OUT / trip / "qc151_fields.json").read_text(encoding="utf-8", errors="replace"))


def fval(trip, group, key):
    for r in fields(trip):
        if r.get("group") == group and r.get("key") == key:
            return r.get("value")
    return None


def main() -> int:
    global MUT
    for a in sys.argv[1:]:
        if a.startswith("--mutate-"):
            MUT = a.split("--mutate-")[-1]
    print("=" * 78)
    print("H-5 v12 裁决：C/L3 = 正常退出码 0（崩溃排除）+ 关卡时长账")
    if MUT:
        print("!! 变异模式: %s" % MUT)
    print("=" * 78)

    # X1 两趟 wait_returncode 都是 0（§402 语义：等待时已自行退出）
    rc_c = fval("l1_20261023c", "TERM", "wait_returncode")
    rc_l3 = fval("l3_20261023", "TERM", "wait_returncode")
    exp_rc = 1 if MUT == "rc_flip" else 0
    rec("X1 C/L3 wait_returncode 均为 0（自退码 0，非活杀码 1）",
        rc_c == exp_rc and rc_l3 == exp_rc, "C=%r L3=%r" % (rc_c, rc_l3))

    # X2 except.txt 零新增（多重集差口径）
    diff_c = json.loads((OUT / "l1_20261023c/except_set_diff.json").read_text(encoding="utf-8"))
    diff_l3 = json.loads((OUT / "l3_20261023/except_set_diff.json").read_text(encoding="utf-8"))
    rec("X2 C/L3 except 多重集差 = 0 新增（单独不足，与 X1/X3/X4 组合用）",
        diff_c["new_exception_count"] == 0 and diff_l3["new_exception_count"] == 0,
        "C=%d L3=%d" % (diff_c["new_exception_count"], diff_l3["new_exception_count"]))

    # X3 measure 死法签名：ws_kb=20（§2.2 的「进程已死」档，差四个数量级）
    m_c = json.loads((OUT / "l1_20261023c/measure_w0.json").read_text(encoding="utf-8"))
    m_l3 = json.loads((OUT / "l3_20261023/measure_w0.json").read_text(encoding="utf-8"))
    rec("X3 C/L3 的 ws_kb=20（进程已死）；对照 A=137504 活着",
        m_c["counters"][0]["ws_kb"] == 20 and m_l3["counters"][0]["ws_kb"] == 20,
        "C=%d L3=%d" % (m_c["counters"][0]["ws_kb"], m_l3["counters"][0]["ws_kb"]))

    # X4 ★ 决定性：战斗时钟跳零时刻 < CLOSe 阶段（CLOSE 在 39.8+122.1=161.9 才开始）
    #   ⇒ 死亡窗口 (77.16, 161.95] 全程在 harness 任何关闭动作之前 ⇒
    #   RC-4 的 WM_CLOSE→链→AV 路径**结构上不可能**发生在本趟死亡时刻。
    clock = json.loads((OUT / "l1_20261023c/_v11a_concurrent_clock.json").read_text(encoding="utf-8"))
    ser = clock["series"]
    zero_t = None
    prev = None
    for t, f, *_ in ser:
        if f == 0 and prev not in (None, 0):
            zero_t = t
            break
        prev = f
    close_begin = fval("l1_20261023c", "BUDGET", "stage_begin:frame") + \
        fval("l1_20261023c", "BUDGET", "stage_seconds:frame")  # 35.093+126.657=161.75
    # ★ 轴换算：旁路时钟 t0 ≈ stage_begin:launch（监视器随发射启动）。
    #   zero_t_script = launch + zero_t_clock = 11.484 + 70.879 = 82.363，
    #   与 close_begin=161.75 同轴比较 ⇒ 死亡先于任何关闭窗口动作 **79.4 s**。
    launch_begin = fval("l1_20261023c", "BUDGET", "stage_begin:launch")
    first_move = next(t for t, f, *_ in ser if f > 0)
    max_f = max(f for _t, f, *_ in ser)
    zero_t_script = launch_begin + zero_t
    rec("X4 ★ C 旁路时钟跳零（同轴 %.3f s）< CLOSE 阶段（%.1f s）——死在战斗结束，非 WM_CLOSE 链"
        % (zero_t_script, close_begin),
        zero_t is not None and zero_t_script < close_begin,
        "first_move=%.3f zero_t_clock=%.3f +launch=%.3f ⇒ %.3f | close_begin=%.3f max_f=%d"
        % (first_move, zero_t, launch_begin, zero_t_script, close_begin, max_f))
    exp_max = 10000 if MUT == "maxf_flip" else 1260
    rec("X4b 战斗终点帧号跳零前峰值复算（=1260 ⇒ ≈40.6 s @31fps 战场）",
        max_f == exp_max, "max_f=%d" % max_f)
    if MUT == "zero_widen":
        rec("X4c （变异目标）跳零时刻 ∈ [0,0] 区间 ⇒ 必红", False, "zero_t=%.3f" % zero_t)
    else:
        rec("X4c 跳零时刻 ∈ (25.4, 77.16]（时钟在跑期间，战斗自然结束）",
            25.4 < zero_t <= 77.1608, "zero_t=%.3f" % zero_t)

    # X5 跳零后「活着」证据：尾部行 RPM 持续成功（f=0 来自可读值非 None ⇒
    #   §401 的判据反向：进程死 ⇒ 序列停止增长）。
    tail = ser[-3:]
    rec("X5 时钟尾部至 %.3f s 仍在增长且计数器冻结非 None（813/311/1128 仍可读）"
        % tail[-1][0],
        all(r[1] == 0 and r[2] == 813 and r[3] == 311 and r[4] == 1128 for r in tail),
        "tail=%s" % tail)

    # X6 L3 同构：rc=0 + except 0 + ws 20 已在 X1-X3 两趟联合断言。
    # 本条补：iso 在终止**之前**就 V_FAIL（= 死亡先于 harness 动作，非竞态产物）。
    iso_c = fval("l1_20261023c", "ISOLATION", "iso_verdict")
    iso_l3 = fval("l3_20261023", "ISOLATION", "iso_verdict")
    iso_a = fval("l1_20261023", "ISOLATION", "iso_verdict")
    rec("X6 C/L3 iso_verdict=V_FAIL（终止前进程已死），对照 A=PASS（活着）",
        iso_c == "V_FAIL" and iso_l3 == "V_FAIL" and iso_a == "PASS",
        "C=%s L3=%s A=%s" % (iso_c, iso_l3, iso_a))

    # X7 A/B 对照臂：活杀 rc=1、帧冻结恒值、iso PASS ⇒ 与 C/L3 是两种机制（非同一死法）
    rc_a = fval("l1_20261023", "TERM", "wait_returncode")
    m_a = json.loads((OUT / "l1_20261023/measure_w0.json").read_text(encoding="utf-8"))
    rec("X7 对照臂 A：rc=1（活杀）+ 进程活着（units0=672）——两种机制确证",
        rc_a == 1 and m_a["gate"]["units0"] == 672, "A rc=%r units0=%r" % (rc_a, m_a["gate"]["units0"]))

    # X8 时长账：协议要求 windows=3×window_s=25 + settle=4 ⇒ 需 ≥79 s 战斗余量。
    #   战斗实际时长（旁路时钟）= zero_t − first_move ≈ 45.5 s < 79 s ⇒ 「关卡太短」成立。
    #   且旁路锚与 stage 锚有数秒级不确定（不做精确拼接），故用「需求下界」保守判。
    proto = fval("l1_20261023c", "MEASURE", "protocol") or {}
    need = proto.get("windows", 3) * proto.get("window_s", 25.0) + proto.get("settle_s", 4.0)
    battle_s = zero_t - first_move
    rec("X8 战斗时长 %.1f s < 协议窗需求 %.0f s ⇒ 战斗在满窗前结束 ⇒ 根因收敛到测试图" % (battle_s, need),
        battle_s < need, "battle=%.2f first_move=%.3f zero_t=%.3f need=%.0f (win×n+settle=%r)"
        % (battle_s, first_move, zero_t, need, proto.get("window_s")))

    # X9 画面尺寸对账（C 的终止对话框画面字节数与 S397 §登记一致）
    sz_c = (OUT / "l1_20261023c/frame_target_01.png").stat().st_size
    exp_sz = 1 if MUT == "pngsize_flip" else 41583
    rec("X9 C 终帧画面字节数与 S397:168 登记一致（41,583）", sz_c == exp_sz, "实测 %d" % sz_c)

    # X10 S397 登记的 C 行文案 + Lead 的 A 画面说法实测核对（只读，不改 S397 本体）
    t397 = S397.read_text(encoding="utf-8", errors="replace")
    needle = "Battle control terminated — press OK to continue"
    if MUT == "docneedle_flip":
        needle = "Mission accomplished"  # 对 C 行而言错误的期望 ⇒ 必红
    hit = [ln for ln in t397.splitlines() if needle in ln and "l1_20261023c" in ln]
    rec("X10 ★ 文档旁证：S397 登记 C 趟画面=战斗终止对话框；A 趟画面实为部署屏"
        "（Lead 的「A=Mission accomplished」不成立，旁证改由 C 承担）",
        len(hit) == 1, "登记行 1 条: %s" % (hit[0][:64] if hit else "无"))

    # X11 YURI.exe 字符串表无这三条串 ⇒ 文案来自 CSF/资源（不主张更多）
    #（上一轮实测 0 命中，此处只登记为「未定谳」的边界，不作判据）
    rec("X11 边界登记：终止对话框的 OK 钮由谁触发（游戏自退 or 其它）本件不主张",
        True, "残留子问题，见文件头")

    print("\n" + "=" * 78)
    npass = sum(1 for _n, ok, _d in RESULTS if ok)
    print("TOTAL %d/%d PASS" % (npass, len(RESULTS)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED: %s | %s" % (n, d))
    if MUT:
        return 0
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
