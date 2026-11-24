# -*- coding: utf-8 -*-
"""_integ_make_copies.py — 任务项 2 的测试/门禁「路径副本」生成器。

R3 同法（CANDIDATE_SEMANTIC_REVIEW_R3.md 附 2）：原件逐字节复制，改动仅限路径解析行，
判定逻辑一字不改；原件（lead/b2b_candidate_review3_20261107/ 下）只读不改一字。
  1) _test_candidate_lf.py → _integ_test_isolated.py   仅改第 37 行 CANDIDATE_PATH → 隔离副本
  2) _check_candidate_r3.py → _integ_check_isolated.py 仅改 56/61/63/64 四行路径解析 → 隔离副本
diff 证明落本写域：_integ_test_isolated_diff.txt / _integ_check_isolated_diff.txt
"""
import difflib
import hashlib
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead/b2b_isolated_20261107"
TEST_SRC = ROOT / "lead/b2b_candidate_review3_20261107/_test_candidate_lf.py"
GATE_SRC = ROOT / "lead/b2b_candidate_review3_20261107/_check_candidate_r3.py"

ok = True


def fp(p: Path):
    d = p.read_bytes()
    return hashlib.sha256(d).hexdigest(), len(d)


def copy_with_line_changes(src: Path, dst: Path, expect_changes: dict, diff_out: Path):
    """expect_changes: {0-based 行号: (旧行全等串, 新行全等串)}；其余行必须逐字节一致。"""
    global ok
    raw = src.read_bytes()
    assert raw.count(b"\r") == 0, f"{src.name} 含 CR，需先核行尾"
    lines = raw.decode("utf-8").split("\n")
    new_lines = list(lines)
    for idx, (old_l, new_l) in expect_changes.items():
        if lines[idx] != old_l:
            print(f"!! {src.name} 第 {idx + 1} 行与预期旧值不符:\n   实际: {lines[idx]!r}\n   预期: {old_l!r}")
            ok = False
            continue
        new_lines[idx] = new_l
    changed = [i for i in range(len(lines)) if lines[i] != new_lines[i]]
    if set(changed) != set(expect_changes):
        print(f"!! {src.name} 变更行集 {changed} != 预期 {sorted(expect_changes)}")
        ok = False
    dst.write_bytes("\n".join(new_lines).encode("utf-8"))
    # diff 证明（unified，n=1）
    dl = list(difflib.unified_diff(lines, new_lines, fromfile=str(src.relative_to(ROOT)), tofile=str(dst.relative_to(ROOT)), n=1, lineterm=""))
    diff_out.write_text("\n".join(dl) + "\n", encoding="utf-8", newline="\n")
    hs, bs = fp(src)
    hd, bd = fp(dst)
    print(f"{src.name} → {dst.name}")
    print(f"  源  sha256={hs} bytes={bs}")
    print(f"  副本 sha256={hd} bytes={bd}")
    print(f"  变更行(1-based) = {[i + 1 for i in changed]} （其余 {len(lines) - len(changed)} 行逐字节一致）")
    print(f"  diff 证明 → {diff_out.name}")
    return hd, bd


print("== [1] 测试副本（仅改 CANDIDATE_PATH） ==")
t_new = 'CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_isolated_20261107/qc151_trip.isolated.py"'
t_old = 'CANDIDATE_PATH = PROJECT_ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"'
h_test, b_test = copy_with_line_changes(TEST_SRC, WD / "_integ_test_isolated.py", {36: (t_old, t_new)}, WD / "_integ_test_isolated_diff.txt")

print("== [2] 门禁副本（仅改 4 行路径解析） ==")
g_changes = {
    55: ('BASE = (Path.cwd() / "lead" / "b2b_candidate_lf_20261107").resolve()',
         'BASE = (Path.cwd() / "lead" / "b2b_isolated_20261107").resolve()'),
    60: ('CANDIDATE_REL = "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"',
         'CANDIDATE_REL = "lead/b2b_isolated_20261107/qc151_trip.isolated.py"'),
    62: ('TEST_PY_REL = "lead/b2b_candidate_review3_20261107/_test_candidate_lf.py"',
         'TEST_PY_REL = "lead/b2b_isolated_20261107/_integ_test_isolated.py"'),
    63: ('TEST_OUT_REL = "lead/b2b_candidate_review3_20261107/_test_rerun_out.txt"',
         'TEST_OUT_REL = "lead/b2b_isolated_20261107/_integ_test_isolated_out.txt"'),
}
h_gate, b_gate = copy_with_line_changes(GATE_SRC, WD / "_integ_check_isolated.py", g_changes, WD / "_integ_check_isolated_diff.txt")

print("== [3] 汇总 ==")
print("COPIES_OK =", ok)
raise SystemExit(0 if ok else 1)
