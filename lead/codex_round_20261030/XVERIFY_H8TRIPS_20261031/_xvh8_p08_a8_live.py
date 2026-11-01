#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B2 对账探针 p08：发射器 A8/R-1 修复面实测（sizeof PE32 + 进程枚举 + 当前游戏进程数）
   与 launcher tee 的 [WARN] 行归属核验（只读，零发射）。
"""
import io, sys, ctypes, hashlib, os
from ctypes import wintypes as wt
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.abspath("lead/goal1_harness8_20261031"))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "lh8", "lead/goal1_harness8_20261031/_launch_h8_20261031.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)          # 顶层只建 Path/常量，不发射（亲读 :18-48）
print("launcher sha256[:16] =", hashlib.sha256(open("lead/goal1_harness8_20261031/_launch_h8_20261031.py", "rb").read()).hexdigest()[:16])
print("PE32 sizeof          =", ctypes.sizeof(m.PE32), "（§486 主张 568；R-1 失效值 560）")
lp = m.list_procs()
print("list_procs 条数      =", len(lp), "（随负载浮动，非常量；B1/RR 记 499/543/557/558）")
gp = m.game_procs()
print("game_procs 当前      =", gp, "⇒ 与 tee 的 A8 got=0 同形（现刻复测）")
# WARN 行归属：harness 侧唯一打印点
h8 = open("lead/goal1_harness8_20261031/qc151_trip.harness8.py", encoding="utf-8").read().splitlines()
print("harness8 'carrier dir len' 打印点行号 =", [i + 1 for i, l in enumerate(h8) if "carrier dir len" in l])
lf = open("lead/goal1_harness8_20261031/_launch_h8_20261031.py", encoding="utf-8").read().splitlines()
print("launcher 'carrier dir len' 打印点行号 =", [i + 1 for i, l in enumerate(lf) if "carrier dir len" in l])
tee = open("lead/codex_round_20261030/LEADER_battle/launcher_h8_t1_20261031.txt", encoding="utf-8", errors="replace").read().splitlines()
print("tee t1 前两行 =", tee[:2])
print("tee t1 是否含 harness 侧其它输出（如 MEASURE/窗表）=", any("MEASURE" in l or "fps" in l for l in tee))
