# -*- coding: utf-8 -*-
"""RR-P14：发射器副本 main() 的**预检 fail-closed 端到端**（只走「预检不过 ⇒ return 2」分支，
   该分支在 OUT_DIR.mkdir / spawnv **之前**返回 ⇒ 零写入、零发射、零真机）。

用例：
  E1 game_procs 桩入 1 个 gamemd.exe ⇒ A8 got="1" ≠ want="0" ⇒ 期望 main() 返回 2
  E2 game_procs 桩入 2 个 ⇒ 同上
  E3 A11 桩坏（--harness-sha16 用 d019e8be，但把 HARNESS_BY_SHA16 指向缺失文件）⇒ 期望 2
  E4 out-dir 门禁：构造超长 suffix ⇒ 期望在 A8 之后 return 2（也验证 130 门禁仍在链上）
★ 对照组（不执行）：真实环境 A8=0 ⇒ 会继续 mkdir+spawn ⇒ **禁止运行**。
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"


def load(name):
    sp = importlib.util.spec_from_file_location(name, str(COPY))
    m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m
    sp.loader.exec_module(m)
    return m


def run_case(tag, argv, fake_game_procs=None, harness_map=None, trip_override=None):
    m = load("rr14_" + tag)
    logs = []
    real_print = print
    m.game_procs = lambda: (list(fake_game_procs) if fake_game_procs is not None
                            else [])
    if harness_map is not None:
        m.HARNESS_BY_SHA16 = harness_map
    if trip_override is not None:
        m.TRIP = trip_override
    out = []

    def cap(*a, **k):
        s = " ".join(str(x) for x in a)
        out.append(s)
        return real_print(*a, **k)
    m.print = cap
    import builtins
    old = builtins.print
    builtins.print = cap
    argv_bak = sys.argv
    sys.argv = ["_launch_h8_20261031.py"] + argv
    try:
        rc = m.main()
    finally:
        sys.argv = argv_bak
        builtins.print = old
    preflight = [l for l in out if "A8" in l or "门禁" in l or "预检" in l
                 or "A11" in l]
    suf = argv[argv.index("--suffix") + 1] if "--suffix" in argv else ""
    wrote = (m.TRIP / ("l3_20261031h" + suf)).exists()
    return {"rc": rc, "suffix": suf, "preflight_lines": preflight,
            "out_dir_created": wrote}


def main():
    res = {}
    # E1/E2：A8 fail-closed（真实件都在，A1/A2/A11 应 OK，只有 A8 红）
    for tag, gp in (("E1_one_game_proc", ["gamemd.exe"]),
                    ("E2_two_game_procs", ["gamemd.exe", "ra2loader.exe"])):
        res[tag] = run_case(tag, ["--variant", "L3", "--suffix", "zz_rr"],
                            fake_game_procs=gp)
        res[tag]["fake_game_procs"] = gp
    # E4：out-dir 门禁（A8 正常 0，但 suffix 超长 ⇒ len>130 ⇒ return 2）
    res["E4_outdir_gate"] = run_case(
        "E4", ["--variant", "L3", "--suffix", "_RRVERYLONGSUFFIX_0000000"],
        fake_game_procs=[])
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p14_preflight_failclosed.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
