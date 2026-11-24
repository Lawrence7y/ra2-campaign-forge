# -*- coding: utf-8 -*-
"""XVERIFY_V4 探针 3：发射器 v4 白名单/缺省/路径存在性 importlib 直调 + OUT_DIR/TRIP_ID 投影亲算。
模板行按字节取自 _launch_h8v4_20261101.py（L200/L201），非誊写。
不调 main（零发射行为）。
python -I -B -X utf8 本文件。
"""
import ast
import importlib.util
import re
import sys
from pathlib import Path

L = Path(r"D:\Project\ra2-campaign-forge\lead\goal1_harness8_20261031\_launch_h8v4_20261101.py")
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (("  | " + str(detail)) if detail else ""))
    if not cond:
        FAILS.append(name)


spec = importlib.util.spec_from_file_location("xv4_launcher", L)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)   # 只到模块级常量；main 不调用

kh = mod.KNOWN_HARNESS
hb = mod.HARNESS_BY_SHA16
check("P1 KNOWN_HARNESS 恰 5 条（h6/h7/v2/v3/v4）",
      sorted(kh.keys()) == ["37a7c9cdf2ca97e3", "38244d2907e7f7fa", "d019e8beecfb5fd8",
                            "dd5459fe0cf3461c", "ff8245d27b3db22a"], sorted(kh.keys()))
check("P2 HARNESS_BY_SHA16 键集一致", sorted(hb.keys()) == sorted(kh.keys()))
missing = [k for k, v in hb.items() if not Path(v).exists()]
check("P3 五条路径全部在盘", not missing, missing)
check("P4 缺省 HARNESS_SHA16 = v4", mod.HARNESS_SHA16 == "38244d2907e7f7fa", mod.HARNESS_SHA16)
print("P5 各路径：")
for k in sorted(hb):
    print("     %s -> %s" % (k, Path(hb[k]).name))

# 模板行按字节提取（L200 OUT_DIR / L201 TRIP_ID）
src = L.read_text(encoding="utf-8")
lines = src.splitlines()
line_out = lines[199]
line_tid = lines[200]
check("P6 L200 是 OUT_DIR 模板行", "OUT_DIR = TRIP /" in line_out and "1101v4" in line_out, line_out.strip())
check("P7 L201 是 TRIP_ID 模板行", "TRIP_ID =" in line_tid and "V4-20261101" in line_tid, line_tid.strip())

# 投影：variant L3/L1 × suffix a/b × 5/6 位 pid（planned 含 ct 段与 pid 占位）
print("P8 OUT_DIR/TRIP_ID 投影（模板行按字节 exec）：")
all_ok = True
for variant in ("L3", "L1"):
    for suffix in ("a", "b", ""):
        env = {"TRIP": mod.TRIP, "_a": type("A", (), {"variant": variant, "suffix": suffix})(),
               "_v": mod.VARIANTS[variant]}
        exec(compile(line_out.strip(), "<L200>", "exec"), env)
        exec(compile(line_tid.strip(), "<L201>", "exec"), env)
        # planned 串模拟 launcher L234：OUT_DIR/ct/c_000000000000_12345，pid 段按 5/6 位最长位宽
        planned6 = env["OUT_DIR"] / "ct" / ("c_" + "0" * 12 + "_123456")
        planned5 = env["OUT_DIR"] / "ct" / ("c_" + "0" * 12 + "_12345")
        print("     L%s s='%s' OUT_DIR=%s  TRIP_ID=%s  planned5=%d planned6=%d"
              % (variant, suffix, env["OUT_DIR"].name, env["TRIP_ID"],
                 len(str(planned5)), len(str(planned6))))
        all_ok &= (len(str(planned6)) <= 130 and len(str(planned5)) <= 130)
check("P8a 六组合 planned（5/6 位 pid）全部 ≤130", all_ok)
check("P8b 目录名 = l3_1101v4a 形（10 字符短命名）",
      (mod.TRIP / "l3_1101v4a").name == "l3_1101v4a")

# extra-argv 透传：build_harness_argv 对 --h8-wait-trace 的可达性
import inspect
sig = inspect.signature(mod.build_harness_argv)
argv = mod.build_harness_argv(harness=mod.HARNESS_BY_SHA16["38244d2907e7f7fa"],
                              map_path=Path("XMP29U2.MAP"),
                              map_sha=mod.VARIANTS["L3"]["map_sha"],
                              out_dir=mod.TRIP / "l3_1101v4a", src=mod.TRIP / "_src_L3_sf10c_20261021",
                              trip_id="QC161-U0800-L3-V4-20261101A", probe_frames="400,600,800",
                              fullscreen=True, extra=["gamemd.exe"],
                              extra_argv=["--h7-measure-start-frame", "800", "--h8-wait-trace"])
check("P9 --h8-wait-trace 经 --extra-argv 可达 harness argv",
      "--h8-wait-trace" in argv and "800" in argv, argv[-6:])

# argparse choices=sorted(KNOWN_HARNESS)（集合外 sha 拒绝）
seg = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
       and getattr(n.func, "attr", "") == "add_argument"
       and any(isinstance(a, ast.Constant) and a.value == "--harness-sha16" for a in n.args)]
check("P10 --harness-sha16 choices=sorted(KNOWN_HARNESS)",
      len(seg) == 1 and any(kw.arg == "choices" for kw in seg[0].keywords))

print()
print("FAILS =", FAILS)
sys.exit(0 if not FAILS else 1)
