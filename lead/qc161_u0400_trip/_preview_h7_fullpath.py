#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§420：补 §416 的缺口 —— **三窗全通路径**下的 harness7 形态预演。

§416 用的是 `l1_20261023`（w0 就 no_advance 短路），只走到判档器 `:430` 那个
短路分支的 `h7_smoke_section` 调用。而真机 h7a 若顺利，会走 `:536` 那个
**正常完成路径**的调用 —— 那条路上 `h7_smoke_section` 之前还有三窗断言、
之后还有 [5] except 与 [6] 开机指纹。**这条路径从没在 harness7 标记下跑过。**

本件用 `l1c_20261021`（w0/w1/w2 均 ok，三窗齐全）造 harness7 三形态副本，
验证：
  A. 完整路径下三形态判型仍正确（不被前置断言干扰）
  B. 三窗断言与冒烟断言**同时**出现在输出里（证明冒烟段真的被执行到）
  C. 负控：短路臂 frame 不塌 ⇒ 冒烟段变红；且三窗断言仍绿（两段互不干扰）

★ 只读真实产物，改副本。不碰盘上任何原产物。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JUDGE = Path(__file__).resolve().parent / "_judge_l1_20261023.py"
TRIP = ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003" / "lead" / "qc161_u0400_trip"
SOURCE = TRIP / "l1c_20261021"     # 三窗齐全：w0/w1/w2 verdict 均 ok
H7_SHA16 = "d019e8beecfb5fd8"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def load_recs(p):
    o = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(o, list)
    return o


def set_last(recs, group, key, value):
    hits = [r for r in recs if isinstance(r, dict)
            and r.get("group") == group and r.get("key") == key]
    assert hits, "缺少 %s.%s" % (group, key)
    hits[-1]["value"] = value


def add(recs, group, key, value):
    recs.append({"group": group, "key": key, "value": value,
                 "source": "argv:--fullscreen", "note": "§420 合成"})


def make_variant(dst, mode):
    dst.mkdir(parents=True, exist_ok=True)
    # ★ 三窗齐全的趟要拷齐 5 份：_launch_result + fields + measure_w0/w1/w2
    for name in ("_launch_result.json", "qc151_fields.json",
                 "measure_w0.json", "measure_w1.json", "measure_w2.json"):
        shutil.copy2(SOURCE / name, dst / name)

    lr = json.loads((dst / "_launch_result.json").read_text(encoding="utf-8"))
    lr["harness_sha16"] = H7_SHA16
    (dst / "_launch_result.json").write_text(
        json.dumps(lr, ensure_ascii=False, indent=2), encoding="utf-8")

    recs = load_recs(dst / "qc151_fields.json")
    # ★★ §421 修正合成失真：真实 harness7 只在**短路臂**写 h7_nav_to_measure
    #   （`:4970` 条件 `nav_end_t is not None and fs_rect_wait_skipped`，
    #    而 `fs_rect_wait_skipped` 初值 False、仅 `--fullscreen` 未 opt-out 才置 True）。
    #   ⇒ **keep 臂与窗口臂现实中不写这条记录**。此前三形态都注入它，
    #   使 keep 臂的 `late_start 不得出现` 断言被验成「记录在场且 False」，
    #   而真机该臂的真实形态是「记录缺席」—— 两者都绿但语义不同。
    #   修正后：只有 short 注入，keep/windowed 不注入 ⇒ 复现真机形态。
    if mode == "short":
        add(recs, "MEASURE", "h7_nav_to_measure",
            {"nav_to_measure_s": 12.5, "limit_s": 90.0,
             "late_start": False, "fs_rect_wait_skipped": True})

    if mode == "windowed":
        set_last(recs, "META", "fullscreen", None)
        recs[:] = [r for r in recs
                   if not (isinstance(r, dict) and r.get("group") == "META"
                           and r.get("key") == "fullscreen")]
        set_last(recs, "FRAME", "pre_capture_wait_polls", 0)
        set_last(recs, "BUDGET", "stage_seconds:frame", 0.14)
    elif mode == "short":
        # ★ §422 双写契约：short 臂 META=True 与 FRAME dict 都写
        add(recs, "META", "h7_fs_rect_wait_skipped", True)
        add(recs, "FRAME", "h7_fs_rect_wait_skipped",
            {"skipped": True, "deadline_orig_was_set": True,
             "rect_at_skip": [0, 0, 2560, 1440],
             "capture_fixed_wh": [800, 600], "reason": "全屏恒非 800×600"})
        set_last(recs, "FRAME", "pre_capture_wait_polls", 0)
        set_last(recs, "BUDGET", "stage_seconds:frame", 1.32)
    elif mode == "keep":
        # ★ §422：对照臂真机只写 META=False（FRAME 被外层 if 挡住）
        add(recs, "META", "h7_fs_rect_wait_skipped", False)
    else:
        raise SystemExit("bad mode")
    (dst / "qc151_fields.json").write_text(
        json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")


def run_judge(d):
    p = subprocess.run([sys.executable, str(JUDGE), "--trip-dir", str(d)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    if not (SOURCE / "measure_w2.json").is_file():
        print("★ 源趟不是三窗齐全：%s" % SOURCE)
        return 1

    # 先确认源趟确实是三窗全通
    vs = [json.loads((SOURCE / ("measure_w%d.json" % i)).read_text(encoding="utf-8")).get("verdict")
          for i in range(3)]
    print("源趟 %s 三窗 verdict = %s" % (SOURCE.name, vs))
    if any(v != "ok" for v in vs):
        print("★ 源趟不是三窗全通，本预演前提不成立")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="h7_full_"))
    try:
        print("\n=== A. 三窗全通路径 × 三形态 ===")
        outs = {}
        for mode in ("windowed", "short", "keep"):
            d = tmp / mode
            make_variant(d, mode)
            rc, out = run_judge(d)
            outs[mode] = out
            form = [l for l in out.splitlines() if "形态（由 META" in l]
            # 判是否走到 [4b]
            reached = "[4b]" in out
            smoke_lines = [l for l in out.splitlines()
                           if ("polls" in l or "skipped" in l or "frame" in l)
                           and ("PASS" in l or "FAIL" in l)]
            print("\n--- %s (rc=%d) ---" % (mode, rc))
            if form:
                print("   " + form[0].strip())
            print("   走到 [4b]: %s   冒烟断言行数: %d" % (reached, len(smoke_lines)))
            for l in smoke_lines[:5]:
                print("   " + l.strip())
            chk = {
                "windowed": "windowed",
                "short": "fullscreen_short",
                "keep": "fullscreen_keep",
            }[mode]
            rec("%s ⇒ 三窗全通路径下判型 %s" % (mode, chk),
                bool(form) and chk in form[0],
                form[0].strip() if form else "形态行缺失")
            rec("%s 冒烟段确实被执行到（走到 [4b] 且有冒烟断言）" % mode,
                reached and len(smoke_lines) > 0,
                "smoke=%d" % len(smoke_lines))

        print("\n=== B. 两段共存：三窗断言与冒烟断言同时出现在同一份输出 ===")
        out = outs["short"]
        has_three = "[1] measure 三窗" in out
        has_smoke = "[4b]" in out
        rec("同一趟输出里同时含 [1] 三窗段与 [4b] 冒烟段",
            has_three and has_smoke,
            "三窗段=%s 冒烟段=%s" % (has_three, has_smoke))

        print("\n=== C. 负控：短路臂 frame 不塌 ⇒ 冒烟段红，三窗段仍绿 ===")
        d = tmp / "short_slow"
        make_variant(d, "short")
        recs = load_recs(d / "qc151_fields.json")
        set_last(recs, "BUDGET", "stage_seconds:frame", 123.7)
        (d / "qc151_fields.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        rc, out = run_judge(d)
        fails = [l.strip() for l in out.splitlines() if "FAIL" in l]
        rec("短路臂 frame=123.7 ⇒ 冒烟段红（红在 frame_s_max）",
            any("2.0" in l or "frame" in l for l in fails), str(fails[:2]))
        # 三窗段落（[1]）不该因此变红
        three_fail = [l for l in fails if "measure 三窗" in l or "w0.verdict" in l]
        rec("★ 三窗段落不因冒烟判据变红（两段互不干扰）",
            not three_fail, str(three_fail[:2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 78)
    ok = sum(1 for _n, o, _d in RESULTS if o)
    print("  checks passed: %d/%d" % (ok, len(RESULTS)))
    bad = [n for n, o, _d in RESULTS if not o]
    if bad:
        print("  FAILED: %s" % bad)
        print("  RESULT: FAIL")
        return 1
    print("  RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
