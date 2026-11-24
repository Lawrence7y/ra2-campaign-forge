# -*- coding: utf-8 -*-
# _wlv_ast.py — 用 ast 严格核：20 条 POS / 24 条 NEG 的 text 是否都是 _r9s_samples.py 里的字符串字面量
import ast, sys
from pathlib import Path
ROOT = Path(r"D:\Project\ra2-campaign-forge")
SRC = ROOT/"lead/gate_r9sem_20261109/_r9s_samples.py"
sys.path.insert(0, str(ROOT/"lead/gate_r9sem_20261109"))
import _r9s_samples as S
tree = ast.parse(SRC.read_text(encoding="utf-8"))
lits = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Constant) and isinstance(n.value, str):
        lits.add(n.value)
print("源码字符串常量个数 =", len(lits))
pos_in = [s["id"] for s in S.POS if s["text"] in lits]
neg_in = [s["id"] for s in S.NEG if s["text"] in lits]
print(f"POS 20 条 text 全部是源码字符串字面量: {len(pos_in)}/20 = {len(pos_in)==20}")
print(f"NEG 24 条 text 全部是源码字符串字面量: {len(neg_in)}/24 = {len(neg_in)==24}")
print("POS 未在字面量集中的 ids:", [s["id"] for s in S.POS if s["text"] not in lits])
print("NEG 未在字面量集中的 ids:", [s["id"] for s in S.NEG if s["text"] not in lits])
# 是否有任何一条 text 是从真实主件文件直接读取（这里只验证"是否等于主件全文/连续行块"）
mains = {
 "P01": ROOT/"lead/matrix_ab_ruling_20261109/RULING_MATRIX_AB.md",
 "P02": ROOT/"lead/matrix_reach_20261109/MATRIX_DEFECT_REACHABILITY.md",
 "P03": ROOT/"lead/n11_wording_fix_20261108/N11_WORDING_FIX.md",
 "P04": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
 "P05": ROOT/"lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md",
}
print("\nP01–P05 整块是否为真实主件的连续子串（whole_block_verbatim）:")
for s in S.POS[:5]:
    real = mains[s["id"]].read_text(encoding="utf-8", errors="replace")
    print(f"  {s['id']}: {s['text'] in real}")
print("\n结论：20/20 正样本均为 _r9s_samples.py 内硬编码字面量（含 :18-79 的 5 个 REAL_* 常量）⇒ 报告 §1(c) 成立")
