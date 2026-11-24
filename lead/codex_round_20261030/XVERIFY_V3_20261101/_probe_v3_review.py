# -*- coding: utf-8 -*-
"""XVERIFY_V3_20261101 复核探针（只读被审件；本文件自位于写域）。

三段：
  P1 发射器 OUT_DIR 投影亲算（6 组合 planned 长度 vs 130 门禁）
  P2 发射器 importlib 直调承继验证（sizeof(PE32)=568 / 白名单 / 缺省 sha / list_procs）
  P3 harness8 v3 桩测：H8-5 gate-override 语义（armed ha 型 / armed 无推进 / 非武装）
                      H8-6 doze 表达式（None→0.002 / 500→0.002 / 50→0.02 / 20→0.05）
P3 的代码段全部用 ast 从 qc151_trip.harness8_v3.py 按字节提取，不是誊写。
"""
import ast
import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
V3 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8_v3.py"
LAUNCHER = ROOT / "lead/goal1_harness8_20261031/_launch_h8v3_20261101.py"
TRIP = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
            r"\CONTINUE_20261003\lead\qc161_u0400_trip")

fails = []


def ck(name, cond, detail=""):
    print("  [%s] %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        fails.append(name)


# ============ P1 OUT_DIR 投影亲算 ============
print("=" * 70)
print("P1 发射器 OUT_DIR 投影亲算（模板 l%s_1101v3%s，_launch_h8v3_20261101.py:200）")
print("=" * 70)
src = LAUNCHER.read_text(encoding="utf-8")
# 从发射器源码按字节取模板行，防誊写漂移
tpl_line = [l for l in src.splitlines()
            if "OUT_DIR = TRIP /" in l and "1101v3" in l][0].strip()
print("  模板行（发射器源文）: %s" % tpl_line)
for variant in ("L3", "L1"):
    for suffix in ("a", "b", "c"):
        out_dir = TRIP / ("l%s_1101v3%s" % (variant[1:].lower(), suffix))
        planned = out_dir / "ct" / ("c_" + "0" * 12 + "_12345")
        n = len(str(planned))
        ck("planned %s" % out_dir.name, n <= 130,
           "len=%d %s（发射器 _launch_h8v3_20261101.py:234-238 同式）"
           % (n, planned))

# ============ P2 发射器 importlib 承继直调 ============
print("=" * 70)
print("P2 发射器 importlib 直调（不调 main；R-1 承继 + 白名单 + 缺省）")
print("=" * 70)
spec = importlib.util.spec_from_file_location("launch_v3_probe", LAUNCHER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("  sizeof(PE32) = %d" % mod.ctypes.sizeof(mod.PE32))
ck("sizeof(PE32)==568（R-1 修复承继）", mod.ctypes.sizeof(mod.PE32) == 568)
fields = [f[0] for f in mod.PE32._fields_]
print("  PE32 字段数 = %d: %s" % (len(fields), fields))
ck("PE32 含 th32ParentProcessID（10 个 _fields_ 条目=内核 9 字段+szExeFile）",
   len(fields) == 10 and "th32ParentProcessID" in fields)
ck("白名单 4 条", set(mod.KNOWN_HARNESS) == {
    "ff8245d27b3db22a", "d019e8beecfb5fd8",
    "dd5459fe0cf3461c", "37a7c9cdf2ca97e3"},
   str(sorted(mod.KNOWN_HARNESS)))
ck("HARNESS_BY_SHA16 与 KNOWN_HARNESS 键一致且路径存在",
   set(mod.HARNESS_BY_SHA16) == set(mod.KNOWN_HARNESS)
   and all(p.is_file() for p in mod.HARNESS_BY_SHA16.values()))
ck("缺省 HARNESS_SHA16 = v3", mod.HARNESS_SHA16 == "37a7c9cdf2ca97e3",
   mod.HARNESS_SHA16)
# 白名单条目与实际文件哈希逐一比对
for sha16, p in sorted(mod.HARNESS_BY_SHA16.items()):
    got = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    ck("白名单 %s ↔ 实测 %s" % (sha16, got), got == sha16, p.name)
procs = mod.list_procs()
print("  list_procs() 实调返回 %d 个进程（本机）" % len(procs))
ck("list_procs 可调用（Process32FirstW 正常，R-1 生效）",
   isinstance(procs, dict) and len(procs) > 0)
gp = mod.game_procs()
ck("game_procs 无游戏残留（A8 预检前置态）", gp == [], str(gp))

# ============ P3 harness8 v3 桩测 ============
print("=" * 70)
print("P3a H8-5 gate-override 语义桩测（代码段 ast 按字节提取自 v3 文件）")
print("=" * 70)
v3src = V3.read_text(encoding="utf-8")
tree = ast.parse(v3src)
gate_block_src = None
doze_src = None
for node in ast.walk(tree):
    if isinstance(node, ast.If):
        t = ast.unparse(node.test)
        if t == "H8_MEASURE_START_FRAME is not None":
            body_src = ast.unparse(node.body[0]) if node.body else ""
            if any("h7_gate_override" in ast.unparse(s) for s in node.body):
                gate_block_src = ast.get_source_segment(v3src, node)
        for s in ast.walk(node):
            if isinstance(s, ast.Assign):
                if any(isinstance(tg, ast.Name) and tg.id == "_h8_doze_s"
                       for tg in s.targets):
                    doze_src = ast.get_source_segment(v3src, s)
if not gate_block_src:
    # unparse 差异兜底：文本搜索
    raise SystemExit("FATAL: gate-override 块未定位")
print("  gate-override 块源段（%d 字符）已按字节提取" % len(gate_block_src))
print("  doze 源段: %s" % doze_src)


class _RecStub:
    def __init__(self):
        self.rows = []

    def add(self, group, key, value, source, note=""):
        self.rows.append((group, key, value, source, note))


def run_gate(h8_msf, s_samples, units0, pre_fps15, orig_gate_ok):
    ns = {"H8_MEASURE_START_FRAME": h8_msf, "s_samples": s_samples,
          "units0": units0, "pre_fps15": pre_fps15,
          "gate_ok": orig_gate_ok, "rec": _RecStub(),
          "round": round, "bool": bool}
    exec(compile(gate_block_src, "<gate-override-extract>", "exec"), ns)
    return ns["gate_ok"], ns["rec"]


# ha 型输入：pre_fps15=2.678（<3 原闸必拒），settle 内帧推进（124→138），units0=880
ck("P3a-1 armed+ha型（fps=2.678<3、帧推进、units0=880）⇒ gate_ok=True",
   run_gate(400, [(0.0, 124), (1.0, 128), (4.0, 138)], 880, 2.678, False)[0]
   is True)
# 覆盖前原 gate_ok=True 也应被重算为 True（不受原值污染）
ck("P3a-2 armed+ha型 原值 True ⇒ 仍 True",
   run_gate(400, [(0.0, 124), (4.0, 138)], 880, 2.678, True)[0] is True)
# armed 但 settle 内零帧推进 ⇒ gate_ok=False
ck("P3a-3 armed+零帧推进（帧数恒 124）⇒ gate_ok=False",
   run_gate(400, [(0.0, 124), (4.0, 124)], 880, 2.678, False)[0] is False)
# armed + units0=None ⇒ False
ck("P3a-4 armed+units0=None ⇒ gate_ok=False",
   run_gate(400, [(0.0, 124), (4.0, 138)], None, 2.678, False)[0] is False)
# 非武装：块零执行，gate_ok 保持原值（False 与 True 两态）
g, r = run_gate(None, [(0.0, 124), (4.0, 124)], 880, 2.678, False)
ck("P3a-5 非武装 gate_ok 原值 False 保持", g is False)
g, r = run_gate(None, [(0.0, 124), (4.0, 138)], 880, 2.678, True)
ck("P3a-6 非武装 gate_ok 原值 True 保持（零改动）", g is True)
ck("P3a-7 非武装零 rec 行", len(r.rows) == 0, str(r.rows))
# armed 记录行内容
g, r = run_gate(400, [(0.0, 124), (4.0, 138)], 880, 2.678, False)
ck("P3a-8 armed 落 h7_gate_override 记录",
   len(r.rows) == 1 and r.rows[0][1] == "h7_gate_override"
   and r.rows[0][2]["armed"] is True
   and r.rows[0][2]["frames_advanced"] is True
   and r.rows[0][2]["pre_fps15_as_data"] == 2.678
   and r.rows[0][2]["gate_ok"] is True, str(r.rows[0][:3] if r.rows else None))

print("=" * 70)
print("P3b H8-6 doze 表达式桩测（源段提取同上）")
print("=" * 70)
ns0 = {"min": min}
exec(compile("def _f(H8_WAIT_HZ):\n    %s\n    return _h8_doze_s"
             % doze_src, "<doze-extract>", "exec"), ns0)
f = ns0["_f"]
ck("P3b-1 H8_WAIT_HZ=None ⇒ 0.002（v2 等价）", f(None) == 0.002, repr(f(None)))
ck("P3b-2 H8_WAIT_HZ=500 ⇒ 0.002", f(500) == 0.002, repr(f(500)))
ck("P3b-3 H8_WAIT_HZ=50 ⇒ 0.02（对照趟）", f(50) == 0.02, repr(f(50)))
ck("P3b-4 H8_WAIT_HZ=20 ⇒ 0.05（帽边界）", f(20) == 0.05, repr(f(20)))
ck("P3b-5 H8_WAIT_HZ=10 ⇒ 0.05（帽兜底，argparse 已拒 <20）",
   f(10) == 0.05, repr(f(10)))

print("=" * 70)
print("探针汇总：%s（fails=%d）" % ("全 PASS" if not fails else "有 FAIL", len(fails)))
sys.exit(1 if fails else 0)
