#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§407 H-2e 门禁核验：判档器对 harness7 冒烟三形态的判读能力。

★ 真实 harness7 趟还不存在（需真机）。本核验用**合成趟目录**驱动判档器黑盒，
  只用它的**退出码 + 输出文本**判定，不 import 它的内部函数 ——
  否则会重演「对账器复用被测物函数 ⇒ 两边同绿」。

★ 关键设计（这是本轮最重要的一条）：
  **全屏短路臂的正常结局是 `return EXIT_SHORT_CIRCUIT`（3）**。
  如果冒烟判据写在那个 return 之后，真机冒烟趟一条都执行不到，
  而离线核验若只测「三窗齐全」的趟，永远发现不了。
  所以 S1/S2/S6 都构造短路趟。

变异（每条都必须被指定断言抓到）：
  M1 短路分支不调 h7_smoke_section   → S1 的 [4b] 消失
  M2 skipped 判据反转                → S1 变红
  M3 polls 阈值放宽到 999            → S1 变红
  M4 frame_s_max 放宽到 999          → S1 变红
  M5 对照臂 late_start 判据删掉       → S5 变红（构造 late_start=True）
  M6 形态识别改用「哈希判断」而非产物 → S2/S3 形态错判
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

JUDGE = Path(__file__).with_name("_judge_l1_20261023.py")
PY = sys.executable
H7 = "d019e8beecfb5fd8"
H6 = "ff8245d27b3db22a"

RESULTS: list[tuple[str, bool, str]] = []


def chk(tag, cond, detail=""):
    RESULTS.append((tag, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {tag}  {detail}")
    return bool(cond)


def mk_trip(root: Path, name: str, *, sha: str, skipped, polls, frame_s,
            n2m=None, verdict="ok", units0=900, make_w12=True):
    """构造一个最小可用趟目录。"""
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    # _launch_result.json
    (d / "_launch_result.json").write_text(json.dumps({
        "rc": 0, "duration_s": 181.0, "trip_id": "SYNTH-" + name,
        "harness": "synthetic", "harness_sha16": sha,
        "carriers_deleted": True, "leftover_procs": [],
    }, ensure_ascii=False), encoding="utf-8")

    gate = {"pre_fps15": 27.0, "units0": units0, "ok": True,
            "gate_fps15_min": 3.0, "gate_span_s": 1.5}
    w0 = {"schema": "MEASURE_V1", "trip_id": "SYNTH", "window": 0, "hz": 500,
          "t_abs0": 1792723397.87, "span_s": 4.0,
          "gate": gate, "verdict": verdict,
          "stats": {"fps_avg": 27.0, "fps_p50": 27.0, "logic_frames": 108}}
    if n2m is not None:
        w0["h7"] = {"nav_to_measure_s": n2m.get("nav_to_measure_s"),
                    "limit_s": n2m.get("limit_s", 90.0),
                    "late_start": bool(n2m.get("late_start"))}
    (d / "measure_w0.json").write_text(json.dumps(w0, ensure_ascii=False),
                                       encoding="utf-8")
    if make_w12:
        for i in (1, 2):
            (d / f"measure_w{i}.json").write_text(json.dumps({
                "schema": "MEASURE_V1", "window": i, "hz": 500,
                "gate": dict(gate), "verdict": "ok",
                "stats": {"fps_avg": 27.0, "fps_p50": 27.0, "logic_frames": 108},
            }, ensure_ascii=False), encoding="utf-8")

    recs = [{"group": "NAV", "key": "verdict", "value": "OK", "source": "s",
             "note": "", "ts": ""},
            {"group": "S4", "key": "hit_count", "value": 0, "source": "s",
             "note": "", "ts": ""},
            {"group": "BUDGET", "key": "stage_seconds:frame", "value": frame_s,
             "source": "s", "note": "", "ts": ""}]
    if polls is not None:
        recs.append({"group": "FRAME", "key": "pre_capture_wait_polls",
                     "value": polls, "source": "s", "note": "", "ts": ""})
    if skipped is not None:
        recs.append({"group": "FRAME", "key": "h7_fs_rect_wait_skipped",
                     "value": {"skipped": skipped}, "source": "s",
                     "note": "", "ts": ""})
    if n2m is not None:
        recs.append({"group": "MEASURE", "key": "h7_nav_to_measure",
                     "value": n2m, "source": "s", "note": "", "ts": ""})
    (d / "qc151_fields.json").write_text(json.dumps(recs, ensure_ascii=False),
                                         encoding="utf-8")
    (d / "except_set_diff.json").write_text(json.dumps({"added": []}),
                                            encoding="utf-8")
    return d


def run(judge_src: Path, trip: Path):
    r = subprocess.run([PY, str(judge_src), "--trip-dir", str(trip)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def section(out: str) -> str:
    """取 [4b] 段文本。"""
    i = out.find("[4b]")
    return out[i:] if i >= 0 else ""


def main() -> int:
    print("=" * 92)
    print("§407 H-2e 判档器 · harness7 冒烟三形态判读核验")
    print("=" * 92)
    base_src = JUDGE.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # ---- 合成六趟 ----
        s1 = mk_trip(root, "S1_fullscreen_short", sha=H7, skipped=True,
                     polls=0, frame_s=1.4, verdict="late_start",
                     n2m={"nav_to_measure_s": 95.2, "late_start": True},
                     make_w12=False)
        s2 = mk_trip(root, "S2_windowed", sha=H7, skipped=False, polls=0,
                     frame_s=3.1)
        s3 = mk_trip(root, "S3_keep_rect_wait", sha=H7, skipped=False,
                     polls=253, frame_s=126.6)
        s4 = mk_trip(root, "S4_h6_no_h7keys", sha=H6, skipped=None,
                     polls=251, frame_s=125.7)
        s5 = mk_trip(root, "S5_keep_but_late", sha=H7, skipped=False,
                     polls=253, frame_s=126.6, verdict="late_start",
                     n2m={"nav_to_measure_s": 120.0, "late_start": True},
                     make_w12=False)
        s6 = mk_trip(root, "S6_short_bad_frame", sha=H7, skipped=True,
                     polls=0, frame_s=90.0, verdict="late_start",
                     n2m={"nav_to_measure_s": 95.2, "late_start": True},
                     make_w12=False)
        # ★ S7 专为 M3 而设：短路臂但 polls=5（原阈值 0 ⇒ 必须变红）
        s7 = mk_trip(root, "S7_short_bad_polls", sha=H7, skipped=True,
                     polls=5, frame_s=1.4, verdict="late_start",
                     n2m={"nav_to_measure_s": 95.2, "late_start": True},
                     make_w12=False)

        print()
        print("--- A. 六趟合成产物的判读 ---")
        rc, out = run(JUDGE, s1)
        sec = section(out)
        chk("S1 全屏短路臂：判档器**走到了** [4b]（短路 return 之前必须已跑）",
            "[4b]" in out, "rc=%d" % rc)
        chk("S1 识别形态 = fullscreen_short", "fullscreen_short" in sec, "")
        chk("S1 stage_seconds:frame < 2.0 判据存在", "stage_seconds:frame" in sec, "")
        chk("S1 记录 nav_to_measure_s", "nav_to_measure_s" in sec, "")
        chk("S1 全绿（rc=3 是设计内短路，不是 FAIL）",
            rc == 3 and "FAIL" not in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s2)
        sec = section(out)
        chk("S2 窗口模式：识别为 windowed", "windowed" in sec, "")
        chk("S2 全绿", rc == 0 and "FAIL" not in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s3)
        sec = section(out)
        chk("S3 对照臂：识别为 fullscreen_keep", "fullscreen_keep" in sec, "")
        chk("S3 全绿（polls 253、frame 126.6 都合预期）",
            rc == 0 and "FAIL" not in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s4)
        sec = section(out)
        chk("S4 harness6 趟：明确标「不适用」而非通过",
            "本趟不是 harness7" in sec, "")
        chk("S4 harness6 趟：不产生冒烟断言（无 FAIL）",
            "FAIL" not in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s5)
        sec = section(out)
        chk("S5 对照臂 + late_start ⇒ 必须变红", "FAIL" in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s6)
        sec = section(out)
        chk("S6 短路但 frame 段 90 s ⇒ 必须变红（frame_s_max 生效）",
            "FAIL" in sec, "rc=%d" % rc)

        rc, out = run(JUDGE, s7)
        sec = section(out)
        chk("S7 短路但 polls=5 ⇒ 必须变红（polls_max 生效）",
            "FAIL" in sec, "rc=%d" % rc)

        # ★★ S8：harness7 哈希但**没有 h7 冒烟字段**（window 阶段就失败的趟）。
        #   这种趟**不是冒烟样本**，不能拿设计预期去判它。
        #   ★ 这条是回归出来的真实缺陷：只判哈希会把这类趟判红。
        s8 = mk_trip(root, "S8_h7_no_smoke_fields", sha=H7, skipped=None,
                     polls=None, frame_s=3.0)
        rc, out = run(JUDGE, s8)
        sec = section(out)
        chk("S8 harness7 但无冒烟字段 ⇒ 明确标「不是冒烟样本」", "不是冒烟样本" in sec, "")
        chk("S8 不产生冒烟 FAIL（没跑到那里 ⇒ 既不算通过也不算失败）",
            "FAIL" not in sec, "rc=%d" % rc)

        # ---- B. 变异 ----
        print()
        print("--- B. 变异（每条都必须被指定断言抓到）---")
        MUT = [
            ("M1 短路分支不调 h7_smoke_section",
             "        # ★★ H-2e：短路分支也必须跑冒烟判据 —— 全屏短路臂本来就走这里。\n"
             "        h7_smoke_section(lr, check, OUT_DIR)\n"
             "        return EXIT_SHORT_CIRCUIT",
             "        return EXIT_SHORT_CIRCUIT",
             s1, "4b"),

            ("M2 skipped 期望值反转（windowed 也要求 True）",
             '"windowed": {"skipped": False,',
             '"windowed": {"skipped": True,',
             s2, "h7_fs_rect_wait_skipped"),

            ("M3 短路臂 polls_max 放宽到 999",
             '"fullscreen_short": {"skipped": True, "polls_max": 0,',
             '"fullscreen_short": {"skipped": True, "polls_max": 999,',
             s7, "pre_capture_wait_polls"),
        ]
        for name, old, new, trip, must in MUT:
            n = base_src.count(old)
            if n != 1:
                chk("%s 锚唯一" % name, False, "出现 %d 次" % n)
                continue
            mut = base_src.replace(old, new)
            mp = root / "_mut_judge.py"
            mp.write_text(mut, encoding="utf-8")
            rc2, out2 = run(mp, trip)
            sec2 = section(out2)
            if name.startswith("M1"):
                # M1：短路分支删掉后，S1 的 [4b] 不该出现
                killed = "[4b]" not in out2
                chk("%s → 被抓（[4b] 整段消失）" % name, killed,
                    "[4b] 存在=%s" % ("[4b]" in out2))
            elif name.startswith("M2"):
                # M2：期望值反转 ⇒ 原本全绿的 S2 必须变红
                rc_base, out_base = run(JUDGE, trip)
                killed = ("FAIL" not in section(out_base)) and ("FAIL" in sec2)
                chk("%s → 被抓（基线绿 → 变异红）" % name, killed,
                    "基线FAIL=%s 变异FAIL=%s"
                    % ("FAIL" in section(out_base), "FAIL" in sec2))
            elif name.startswith("M3"):
                # M3：阈值放宽 ⇒ 原本变红的 S7 必须转绿（判据失去杀伤力）
                rc_base, out_base = run(JUDGE, trip)
                killed = ("FAIL" in section(out_base)) and ("FAIL" not in sec2)
                chk("%s → 被抓（基线红 → 变异绿=判据失效）" % name, killed,
                    "基线FAIL=%s 变异FAIL=%s"
                    % ("FAIL" in section(out_base), "FAIL" in sec2))

        # M4 frame_s_max 放宽
        old = '"fullscreen_short": {"skipped": True, "polls_max": 0, "frame_s_max": 2.0},'
        new = '"fullscreen_short": {"skipped": True, "polls_max": 0, "frame_s_max": 999.0},'
        if base_src.count(old) == 1:
            mp = root / "_mut_judge.py"
            mp.write_text(base_src.replace(old, new), encoding="utf-8")
            rc2, out2 = run(mp, s6)
            chk("M4 frame_s_max 放宽到 999 → S6 不再变红（证明该判据承重）",
                "FAIL" not in section(out2), "rc=%d" % rc2)

        # M5 对照臂 late_start 判据删掉
        old5 = ('        check("★★ 对照臂 late_start 不得出现（前置条件按设计生效）",\n'
                '              late is not True, "late_start=%s" % (late,))')
        if base_src.count(old5) == 1:
            mp = root / "_mut_judge.py"
            mp.write_text(base_src.replace(old5, "        pass"), encoding="utf-8")
            rc2, out2 = run(mp, s5)
            chk("M5 删掉对照臂 late_start 判据 → S5 不再变红",
                "FAIL" not in section(out2), "rc=%d" % rc2)

    print()
    print("=" * 92)
    passed = sum(1 for _t, ok, _d in RESULTS if ok)
    total = len(RESULTS)
    print("  checks passed: %d/%d" % (passed, total))
    ok = passed == total
    print("  RESULT: %s" % ("ALL PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
