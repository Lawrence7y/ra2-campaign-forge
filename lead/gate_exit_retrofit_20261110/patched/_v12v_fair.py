# -*- coding: utf-8 -*-
r"""_v12v_fair.py -- 复核员公平性复核（③/④/⑥/⑦）。
1) 修正 MIX-02：撰写人 run_mixed 实句用 token=已交付（我上一脚本误用 MIXED_SAMPLES 里
   的另一句 + token=已填，导致 3/4 是我的 harness 错误，须更正）。
2) 证明 A3/A4 对抗句确实「撰写人没见过」：与 _v12_verify.py 全部样本数组逐字比对。
3) 核 boundary(c)「HARD_V1 与 V2_OVERRIDE 同触时两标记一并回报」是否属实。
4) 核 boundary「只用 U/pre/post，不跨单元」是否属实（实现里是否用了 line）。
5) ⑦ 越界：git 状态/mtime + 只读域文件清单，与 9 件基线指纹再对一次。
"""
import sys
sys.dont_write_bytecode = True
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_v1v2_20261109"
sys.path.insert(0, str(WD))
import _v12_rule as R
import _v12_verify as W

print("=== 1. MIX-02 公平复现（按撰写人 run_mixed 实句 + token=已交付）===")
t = "填用流程规定应按模板核对，但三值已实算，绑定行已交付。"
s = t.find("已交付")
v = R.classify_v12(t, s, s + len("已交付"), "已交付")
print("  TEXT = %s" % t)
print("  classify_v12(token=已交付) => verdict=%s override=%r hard=%s weak=%s"
      % (v["verdict"], v["override"], v["hard"], v["weak"]))
t2 = "填用流程规定应按模板核对，但三值已实算已交付。"
print("  MIXED_SAMPLES 数组里的句子 = %s  （与 run_mixed 实句不同，撰写人自己也不一致）" % t2)
print("  [MIX-02] 按 run_mixed 实句复现 = %s" % ("PASS" if v["verdict"] == "V2" else "FAIL"))

print("\n=== 2. 对抗句是否「撰写人没见过」（逐字与其样本数组比对）===")
KNOWN = set()
for arr in (W.V1_SAMPLES, W.V2_SAMPLES, W.MIXED_SAMPLES):
    for row in arr:
        KNOWN.add(row[1])
TRAPS = [
    "现已填三值并过门禁，不得再改值。",
    "核验者不得代填，但三值现已填并已交付。",
    "本件三值已填，不代填见证槽。",
    "三值已填毕，不许事后改值。",
    "三值并非不已填，回件照录即可。",
    "三值已填，且 reviewerRole 与 PERF:151 内部三角色逐字不同。",
    "三值已填；另附先例件一份供比对。",
    "三值已填，或按判定条件走 PARTIAL 档。",
    "三值已填 → 登记闭合，本件留存。",
]
for t in TRAPS:
    print("  %-58s 在撰写人样本集中 = %s" % (t[:56], t in KNOWN))
print("  [UNSEEN] %d/%d 句确为撰写人样本集中没有的新句子" % (sum(t not in KNOWN for t in TRAPS), len(TRAPS)))

print("\n=== 3. boundary(c)『两标记一并回报』核对（同触 HARD_V1 + V2_OVERRIDE）===")
t = "现已填三值并过门禁，不得再改值。"
s = t.find("已填")
v = R.classify_v12(t, s, s + 2, "已填")
in_u = [k for k in R.V2_OVERRIDE if k in v["unit"]]
print("  TEXT = %s" % t)
print("  U 内实际含 V2_OVERRIDE 词族 = %r" % in_u)
print("  classify_v12 回报 override = %r ; hard = %r" % (v["override"], v["hard"]))
print("  『两标记一并回报』= %s" % (bool(v["override"]) and bool(v["hard"])))

print("\n=== 4. boundary『只用 U/pre/post，不跨单元』核对（源码静态 + 行为）===")
src = (WD / "_v12_rule.py").read_text(encoding="utf-8")
for ln, l in enumerate(src.splitlines(), 1):
    if re.search(r"\bline\b", l) and ("H2" in l or "H3" in l or "H4" in l or "H6" in l):
        print("  _v12_rule.py:%d  %s" % (ln, l.strip()))
# 行为证据：； 后面另一子句的「先例」是否穿透到本命中
t = "三值已填；另附先例件一份供比对。"
s = t.find("已填")
v = R.classify_v12(t, s, s + 2, "已填")
print("  TEXT = %s" % t)
print("  U = %r ; 同行另一子句含『先例』= %s" % (v["unit"], "先例" in t))
print("  hard = %r => 跨单元词是否造成 HARD_V1 = %s" % (v["hard"], "H2_引述占位" in v["hard"]))

print("\n=== 5. ⑦ 只读域越界检查：git status + 指纹复算 ===")
BASELINE = {
    "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md": ("05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651),
    "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md": ("5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
for rel, (sha0, n0) in BASELINE.items():
    p = ROOT / rel
    b = p.read_bytes()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    print("  %-62s MATCH_BASELINE=%s mtime=%s" % (rel, sha == sha0 and n == n0,
          __import__("datetime").datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")))
print("  --- git status 对只读路径 ---")
r = subprocess.run(["git", "status", "--porcelain", "--",
                    "lead/c07_slot_20261109", "lead/c07_truth_protocol_20261109",
                    "lead/gate_fp7_20261108/_g7_predicates.py",
                    "lead/gate_r9r12_20261109/_g9_gate.py",
                    "lead/gate_doc_name_fix_20261109",
                    ".zcode/workflow-runs",
                    "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"],
                   cwd=str(ROOT), capture_output=True, text=True)
print("  " + (r.stdout.strip().replace("\n", "\n  ") if r.stdout.strip() else "(无输出)"))
r2 = subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=str(ROOT), capture_output=True, text=True)
print("  git log -1 = %s" % r2.stdout.strip())
print("  --- 写域文件清单（本复核员新增一律 _v12v_ 前缀）---")
for p in sorted(WD.iterdir()):
    if p.is_file():
        print("  %-40s bytes=%d" % (p.name, p.stat().st_size))
print("[V12V-FAIR-END]")

# ---------- 出口追加（仅追加；原件 1-110 行一字未改）----------
# 原型：lead/dtrigger_compare_20261107/_check_dtrigger.py:31-35 + :226-228
# 【A】原件对【本脚本自身的检查】及产物通道（全部是 print(stdout)，无写盘、
#      无 assert、无 sys.exit/SystemExit；CONST_EXIT_CENSUS.md:736 登记 NO_EXIT_AT_ALL，
#      EXIT_CRITERION.md:501 / _ec_s4_results.json 登记 :34 的 PASS/FAIL 裁决对的 E0）：
#   :34   [MIX-02]  "PASS" if v["verdict"]=="V2" else "FAIL"  —— 唯一的互斥 PASS/FAIL 裁决对
#   :53-54 [UNSEEN] 9/9 句确为撰写人样本集中没有的新句子（逐句 t not in KNOWN）
#   :92   6 件 MATCH_BASELINE=sha==sha0 and n==n0 —— 只读域基线指纹复算
#   :110  [V12V-FAIR-END] 为流程结束标记，非判定
# 【不纳入 ok 的部分】以下都是对【被测对象 _v12_rule.py / 撰写人样本 / 只读域】
#   的领域观测值，不是本脚本对自身的检查结果，取反塞进合取会改掉原判定：
#   :30/:62-64 classify_v12 的 verdict/override/hard/weak、:64 『两标记一并回报』=False、
#   :69-70 源码静态命中 line 的 4 行、:77 跨单元词是否造成 HARD_V1=True、
#   :94-105 git status / git log / 写域清单。它们的 False/True 正是复核结论的证据。
# 【C3】rg 全库 --include=*.py 无 import _v12v_fair / spec_from_file_location 引用；
#   本件无 if __name__ == "__main__" 守卫，是「一次性复核脚本」而非库本体；
#   :19-23 的 ROOT/WD/sys.path 与 import 属原件，一字未动。新增名字全部以下划线开头
#   或为模板要求的 ok/check，均写在文件末尾的追加块里，未新增任何 import，
#   不向模块命名空间引入额外公共名字、不覆盖调用方同名符号。
# 【不改语义】不重复打印任何原有行、不改写任何既有变量；只把 :34/:54/:92
#   三个式子的布尔值（逐字取自原件的判定表达式）合取成一个 ok，再追加结论行与出口。
#   :34 的 v 在 :59/:74 被同名覆盖，故此处用局部变量 _t1/_s1/_v1 重算该纯函数
#   （_v12_rule.py:108-170 classify_v12 只读入参、无 IO/写盘/随机），
#   不引用被覆盖的模块级 v，也不给任何原有名字赋新值。
ok = True

def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)          # 合取聚合：全部通过才真
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

_t1 = "填用流程规定应按模板核对，但三值已实算，绑定行已交付。"   # 原件 :26
_s1 = _t1.find("已交付")                                        # 原件 :27
_v1 = R.classify_v12(_t1, _s1, _s1 + len("已交付"), "已交付") # 原件 :28
check(":34 [MIX-02] 按 run_mixed 实句复现 verdict==V2", _v1["verdict"] == "V2")
check(":54 [UNSEEN] 9/9 对抗句均不在撰写人样本集", all(_t not in KNOWN for _t in TRAPS))
for _rel, (_sha0, _n0) in BASELINE.items():                     # 原件 :88-92 同式
    _b = (ROOT / _rel).read_bytes()
    check(":92 MATCH_BASELINE " + _rel,
          hashlib.sha256(_b).hexdigest() == _sha0 and len(_b) == _n0)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
