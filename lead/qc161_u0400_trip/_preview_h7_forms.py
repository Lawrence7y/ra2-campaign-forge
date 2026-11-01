#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§416：用**真实 harness6 产物**改造成 harness7 三形态，验证判档器判型。

★ 为什么不能只用合成样本：`_verify_h2e_smoke.py` 的 S1–S10 都是
  `mk_trip()` 手搓的最小 JSON，只含判档器要读的那几个键。它们能证明
  「判据逻辑对不对」，但证明不了「真实产物 + 真实键序 + 真实附加键」
  下判型是否仍然正确。本件补的正是这一层。

★ 改法是**纯加法**（只在 rec 列表里 append / 顶替同名键），不删任何真实行：
  1. 顶替 `META.fullscreen` 的值（全屏臂保留 True，窗口臂**删掉**该行）
  2. 全屏臂 append `FRAME.h7_fs_rect_wait_skipped`
  3. 短路臂把 `pre_capture_wait_polls` 与 `stage_seconds:frame` 改成短路后的值
  4. 全部 append `MEASURE.h7_nav_to_measure`（harness7 无条件写）

★ 本件**只读真实产物**（copy 到临时目录再改），不碰任何盘上原产物。
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
SOURCE = TRIP / "l1_20261023"          # harness6 全屏趟（polls=251 / frame=125.703）
H7_SHA16 = "d019e8beecfb5fd8"


def load_recs(p: Path) -> list[dict]:
    obj = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(obj, list), "真实产物应为记录列表"
    return obj


def set_value(recs, group, key, value, drop=False):
    """顶替（取最后一次出现）或删除某条记录。"""
    hits = [r for r in recs
            if isinstance(r, dict) and r.get("group") == group and r.get("key") == key]
    assert hits, "真实产物里没有 %s.%s —— 前提不成立" % (group, key)
    if drop:
        for r in hits:
            recs.remove(r)
        return
    hits[-1]["value"] = value


def add(recs, group, key, value, source="argv:--fullscreen"):
    recs.append({"group": group, "key": key, "value": value,
                 "source": source, "note": "§416 合成（形态预演）"})


def make_variant(dst: Path, mode: str):
    dst.mkdir(parents=True, exist_ok=True)
    for name in ("_launch_result.json", "qc151_fields.json", "measure_w0.json"):
        shutil.copy2(SOURCE / name, dst / name)

    lr = json.loads((dst / "_launch_result.json").read_text(encoding="utf-8"))
    lr["harness_sha16"] = H7_SHA16
    (dst / "_launch_result.json").write_text(
        json.dumps(lr, ensure_ascii=False, indent=2), encoding="utf-8")

    recs = load_recs(dst / "qc151_fields.json")
    # ★★ §421 修正合成失真：真实 harness7 只在短路臂写 h7_nav_to_measure
    #   （`:4970` 条件 `nav_end_t is not None and fs_rect_wait_skipped`）。
    #   keep/窗口臂现实中不写 ⇒ 不得注入。
    n2m = {"nav_to_measure_s": 12.5, "limit_s": 90.0,
           "late_start": False, "fs_rect_wait_skipped": True}

    if mode == "windowed":
        set_value(recs, "META", "fullscreen", None, drop=True)
        add(recs, "FRAME", "pre_capture_wait_polls", 0, "script:rect_of")
        add(recs, "BUDGET", "stage_seconds:frame", 0.14)
    elif mode == "short":
        # ★ §422 双写契约：short 臂 META=True(:7373) 与 FRAME dict(:8087) 都写
        add(recs, "META", "h7_fs_rect_wait_skipped", True, "argv:--fullscreen")
        add(recs, "FRAME", "h7_fs_rect_wait_skipped",
            {"skipped": True, "deadline_orig_was_set": True,
             "rect_at_skip": [0, 0, 2560, 1440],
             "capture_fixed_wh": [800, 600], "reason": "全屏恒非 800×600"})
        add(recs, "FRAME", "pre_capture_wait_polls", 0, "script:rect_of")
        add(recs, "BUDGET", "stage_seconds:frame", 1.32)
        n2m["fs_rect_wait_skipped"] = True
        # ★ 只有 short 臂真机写 n2m（`:4970` 要求 fs_rect_wait_skipped=True）
        add(recs, "MEASURE", "h7_nav_to_measure", n2m, "script:_measure_run")
    elif mode == "keep":
        # ★ §422：对照臂真机**只写 META=False**（`:7378`；FRAME 被外层 if 挡住）
        add(recs, "META", "h7_fs_rect_wait_skipped", False,
            "argv:--h7-keep-rect-wait")
    else:
        raise SystemExit("unknown mode")
    (dst / "qc151_fields.json").write_text(
        json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")


def run_judge(d: Path):
    p = subprocess.run([sys.executable, str(JUDGE), "--trip-dir", str(d)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    if not (SOURCE / "_launch_result.json").is_file():
        print("★ 真实产物缺失：%s" % SOURCE)
        return 1
    checks = []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        print("  %s %s%s" % ("✓" if ok else "✗", name,
                             ("  | " + detail) if detail else ""))

    tmp = Path(tempfile.mkdtemp(prefix="h7_preview_"))
    try:
        print("\n=== A. 三形态预演（真实产物改造） ===")
        verdicts = {}
        for mode, want_form, want_rc_ok in (
                ("windowed", "windowed", True),
                ("short", "fullscreen_short", True),
                ("keep", "fullscreen_keep", True)):
            d = tmp / mode
            make_variant(d, mode)
            rc, out = run_judge(d)
            verdicts[mode] = (rc, out)
            form_line = [l for l in out.splitlines() if "形态（由 META" in l]
            print("\n--- %s (rc=%d) ---" % (mode, rc))
            if form_line:
                print("   " + form_line[0].strip())
            for l in out.splitlines():
                if "PASS" in l or "FAIL" in l:
                    if any(k in l for k in ("polls", "skipped", "frame", "冒烟",
                                            "fullscreen")):
                        print("   " + l.strip())
            chk("%s ⇒ 判型 %s" % (mode, want_form),
                any(want_form in l for l in form_line),
                form_line[0].strip() if form_line else "形态行缺失")

        print("\n=== B. 承重性：三形态必须给出**不同**判定 ===")
        forms = {}
        for mode, (_rc, out) in verdicts.items():
            hit = [l for l in out.splitlines() if "形态（由 META" in l]
            forms[mode] = hit[0].split(":")[-1].strip() if hit else None
        chk("三种形态互不相同", len(set(forms.values())) == 3, str(forms))

        print("\n=== C. 负控：窗口形态被改成「写了 skipped」必须变红 ===")
        d = tmp / "windowed_bad"
        make_variant(d, "windowed")
        recs = load_recs(d / "qc151_fields.json")
        add(recs, "META", "h7_fs_rect_wait_skipped", False,
            "负控：窗口臂不该写")
        (d / "qc151_fields.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        rc, out = run_judge(d)
        red = [l for l in out.splitlines() if l.strip().startswith("✗") and "PASS" not in l]
        chk("窗口臂写了 skipped ⇒ 冒烟判据变红",
            "FAIL" in out and any("skipped" in l for l in out.splitlines() if "FAIL" in l),
            "FAIL 行数=%d" % sum(1 for l in out.splitlines() if "FAIL" in l))

        print("\n=== D. 负控：短路臂 frame 段没降下来必须变红 ===")
        d = tmp / "short_slow"
        make_variant(d, "short")
        recs = load_recs(d / "qc151_fields.json")
        set_value(recs, "BUDGET", "stage_seconds:frame", 125.7)
        (d / "qc151_fields.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        rc, out = run_judge(d)
        chk("短路臂 frame=125.7 s ⇒ 红在 frame_s_max",
            "FAIL" in out and "2.0" in out,
            [l.strip() for l in out.splitlines() if "FAIL" in l][:2].__str__())

        print("\n=== E. 负控：对照臂 polls 掉到 96 必须红在 polls_min ===")
        d = tmp / "keep_short"
        make_variant(d, "keep")
        recs = load_recs(d / "qc151_fields.json")
        set_value(recs, "FRAME", "pre_capture_wait_polls", 96)
        set_value(recs, "BUDGET", "stage_seconds:frame", 48.2)
        (d / "qc151_fields.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        rc, out = run_judge(d)
        chk("对照臂 polls=96 ⇒ 仍判 keep 且红在 polls_min",
            "fullscreen_keep" in out and "200" in out and "FAIL" in out,
            [l.strip() for l in out.splitlines() if "FAIL" in l][:2].__str__())
        chk("★ 承重：该趟不得被判成 windowed（§414 的缺陷）",
            "windowed" not in [l.split(":")[-1].strip()
                               for l in out.splitlines() if "形态（由 META" in l],
            "形态行=%s" % [l for l in out.splitlines() if "形态（由 META" in l])

        print("\n=== F. n2m 在场性（§421 修正的承重断言）===")
        # ★ 真机 harness7 只在 short 臂写 h7_nav_to_measure（`:4970`）。
        #   合成样本必须**复现这个不对称**，否则 keep 臂的 late_start 断言
        #   验的是「在场且 False」而真机是「缺席」——语义漂移。
        #   ★ 首版 §421 修过头（连 short 也删）时本段 8/8 照样绿，
        #     正因缺这两条 ⇒ 补上后「short 缺 n2m」会红在 :266 那条断言。
        _rc, out_short = verdicts["short"]
        _rc, out_keep = verdicts["keep"]
        _n2m_line = [l.strip() for l in out_short.splitlines()
                     if "短路臂记录了 nav_to_measure_s" in l]
        chk("short 臂必须记录 nav_to_measure_s（真机 :4970 会写）",
            bool(_n2m_line) and "PASS" in _n2m_line[0] and "FAIL" not in _n2m_line[0],
            _n2m_line[0] if _n2m_line else "断言行缺失（合成没注入 n2m）")
        _late_line = [l.strip() for l in out_keep.splitlines()
                      if "late_start 不得出现" in l]
        chk("keep 臂不得有 h7_nav_to_measure（真机不写）⇒ late_start=None 通过",
            bool(_late_line) and "PASS" in _late_line[0] and "None" in _late_line[0],
            _late_line[0] if _late_line else "断言行缺失")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 78)
    ok = sum(1 for _n, o, _d in checks if o)
    print("  checks passed: %d/%d" % (ok, len(checks)))
    bad = [n for n, o, _d in checks if not o]
    if bad:
        print("  FAILED: %s" % bad)
        print("  RESULT: FAIL")
        return 1
    print("  RESULT: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
