# -*- coding: utf-8 -*-
"""_integ_probe_isolated.py — D-25 第 6 步「隔离副本离线集成」探针。

对象（全部只读，除隔离副本为本写域文件）：
  母本   out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py
  候选   lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py
  隔离   lead/b2b_isolated_20261107/qc151_trip.isolated.py
  候选diff lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff
  批准设计 lead/b2b_design_20261106/B2B_DESIGN.md（§4 九 hunk）

方法（与 R3 同法，CANDIDATE_SEMANTIC_REVIEW_R3.md:6 / _review_probe_r3.py:411-416 /
_test_candidate_lf.py:40-57）：
  importlib.util.spec_from_file_location + unittest.mock.patch 拦截
  ctypes.windll.user32.SetProcessDPIAware（拦截目标字符串，防真调用；非采样代码），
  模块名独立（qc151_trip_isolated_integ），绝不触发 `if __name__ == "__main__"` 入口。
零真机、零采样代码；九 hunk 重建为纯内存操作。检查项：
  [1] 指纹与逐字节同一性   [2] ast.parse   [3] 隔离加载与符号
  [4] 函数级离线冒烟       [5] diff 统计   [6] 决定性重建（设计九hunk / 候选diff）
  [7] 九锚点定位
"""
import ast
import difflib
import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
ISOL = ROOT / "lead/b2b_isolated_20261107/qc151_trip.isolated.py"
DIFF = ROOT / "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
DESIGN = ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"

EXPECT_MOTHER = ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508)
EXPECT_CAND = ("ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2", 412759)
EXPECT_DIFF = ("72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9", 18454)
EXPECT_DESIGN = ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735)

ANCHORS = [
    ("H1", 'FRESHNESS_GROUP = "FRESHNESS"'),
    ("H2", "backup_mtime_pre:{name}"),
    ("H3", "def make_pre_freshness_snapshot(except_path: Path) -> dict:"),
    ("H4", "def copy_post_except_evidence("),
    ("H5", "pre_freshness_snapshot: dict | None = None) -> int:"),
    ("H6", "pre_freshness_snapshot=pre_freshness_snapshot"),
    ("H7", "_pre_freshness_snapshot: dict | None = None"),
    ("H8", "_pre_freshness_snapshot = make_pre_freshness_snapshot("),
    ("H9", "pre_freshness_snapshot=_pre_freshness_snapshot"),
]

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append(bool(cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))


def fp(p: Path):
    d = p.read_bytes()
    return hashlib.sha256(d).hexdigest(), len(d)


print("=" * 72)
print("== [1] 指纹与逐字节同一性（hashlib 实算） ==")
mother_bytes = MOTHER.read_bytes()
cand_bytes = CAND.read_bytes()
isol_bytes = ISOL.read_bytes()
diff_bytes = DIFF.read_bytes()
design_bytes = DESIGN.read_bytes()
hm, bm = hashlib.sha256(mother_bytes).hexdigest(), len(mother_bytes)
hc, bc = hashlib.sha256(cand_bytes).hexdigest(), len(cand_bytes)
hi, bi = hashlib.sha256(isol_bytes).hexdigest(), len(isol_bytes)
hdf, bdf = hashlib.sha256(diff_bytes).hexdigest(), len(diff_bytes)
hdg, bdg = hashlib.sha256(design_bytes).hexdigest(), len(design_bytes)
print(f"母本:     sha256={hm} bytes={bm} LF={mother_bytes.count(b'\n')} CR={mother_bytes.count(b'\r')}")
print(f"候选:     sha256={hc} bytes={bc} LF={cand_bytes.count(b'\n')} CR={cand_bytes.count(b'\r')}")
print(f"隔离副本: sha256={hi} bytes={bi} LF={isol_bytes.count(b'\n')} CR={isol_bytes.count(b'\r')}")
print(f"候选diff: sha256={hdf} bytes={bdf}")
print(f"批准设计: sha256={hdg} bytes={bdg}")
check("母本 == 绑定记录 517889c6.../399508", (hm, bm) == EXPECT_MOTHER, f"{hm}/{bm}")
check("候选 == 绑定记录 ca23c116.../412759", (hc, bc) == EXPECT_CAND, f"{hc}/{bc}")
check("候选diff == 绑定记录 72b10802.../18454", (hdf, bdf) == EXPECT_DIFF, f"{hdf}/{bdf}")
check("批准设计 == 绑定记录 565771d8.../66735", (hdg, bdg) == EXPECT_DESIGN, f"{hdg}/{bdg}")
check("★ 隔离副本 SHA256 == 候选 SHA256（逐字节同一）", (hi, bi) == (hc, bc), f"{hi}/{bi} vs {hc}/{bc}")
check("隔离副本 CR=0（纯 LF，N-1 不复发）", isol_bytes.count(b"\r") == 0, f"CR={isol_bytes.count(b'\r')}")

print("=" * 72)
print("== [2] ast.parse 静态解析（隔离副本） ==")
isol_text = isol_bytes.decode("utf-8")
mother_text = mother_bytes.decode("utf-8")
try:
    tree = ast.parse(isol_text, filename=str(ISOL))
    top = list(tree.body)
    n_func = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in top)
    n_cls = sum(isinstance(n, ast.ClassDef) for n in top)
    check("ast.parse(隔离副本) 成功（0 语法错误）", True, f"顶层节点={len(top)} 顶层函数={n_func} 顶层类={n_cls}")
except SyntaxError as e:
    check("ast.parse(隔离副本) 成功（0 语法错误）", False, f"{e}")
# 关键新增符号在 AST 顶层可定位（与 R3 §5 九锚点落点同源）
top_names = {getattr(n, "name", None) for n in top}
for sym in ["make_pre_freshness_snapshot", "classify_except_freshness", "copy_post_except_evidence",
            "finalize_trip", "main", "Recorder"]:
    check(f"AST 顶层定义存在: {sym}", sym in top_names)

print("=" * 72)
print("== [3] 隔离加载（与 R3 同法：importlib + DPI patch，模块名独立，不触发 __main__） ==")
with patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1):
    spec = importlib.util.spec_from_file_location("qc151_trip_isolated_integ", str(ISOL))
    if spec is None or spec.loader is None:
        raise ImportError(f"无法为隔离副本建立加载规格: {ISOL}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
print("模块加载成功，__name__ =", mod.__name__)
check("模块名独立 == 'qc151_trip_isolated_integ'（未触发 __main__ 入口）", mod.__name__ == "qc151_trip_isolated_integ")
for sym in ["make_pre_freshness_snapshot", "classify_except_freshness", "copy_post_except_evidence",
            "finalize_trip", "main", "Recorder", "FRESHNESS_GROUP"]:
    check(f"模块命名空间符号存在: {sym}", hasattr(mod, sym))
check("FRESHNESS_GROUP == 'FRESHNESS'", getattr(mod, "FRESHNESS_GROUP", None) == "FRESHNESS",
      repr(getattr(mod, "FRESHNESS_GROUP", None)))
check("FRESHNESS_SNAPSHOT_STATES = 4 态", len(getattr(mod, "FRESHNESS_SNAPSHOT_STATES", [])) == 4,
      str(getattr(mod, "FRESHNESS_SNAPSHOT_STATES", None)))
check("FRESHNESS_VERDICTS = 9 值", len(getattr(mod, "FRESHNESS_VERDICTS", [])) == 9,
      str(getattr(mod, "FRESHNESS_VERDICTS", None)))
check("FRESHNESS_CONFIDENCES = 4 值", len(getattr(mod, "FRESHNESS_CONFIDENCES", [])) == 4,
      str(getattr(mod, "FRESHNESS_CONFIDENCES", None)))

print("=" * 72)
print("== [4] 函数级离线冒烟（隔离模块真实函数；纯内存/只读输入，零写盘） ==")
classify = mod.classify_except_freshness
snapmaker = mod.make_pre_freshness_snapshot
# fixture 与 _test_candidate_lf.py:501-534（F01/F02/F03）逐字同源
r_f01 = classify({"state": "absent_confirmed", "exists": False}, {"exists": True, "sha256": "h123", "mtime_post": 100.0})
check("F01 absent_confirmed+跑后在 → new_first_appearance/high/is_new=True/usable=False",
      r_f01["verdict"] == "new_first_appearance" and r_f01["confidence"] == "high"
      and r_f01["is_new"] is True and r_f01["usable_as_crash_evidence"] is False, str(r_f01))
r_f02 = classify({"state": "absent_confirmed", "exists": False}, {"exists": False})
check("F02 absent_confirmed+跑后无 → absent_both/low/is_new=False",
      r_f02["verdict"] == "absent_both" and r_f02["confidence"] == "low" and r_f02["is_new"] is False, str(r_f02))
r_f03 = classify({"state": "present", "exists": True, "sha256": "sha_a", "mtime_pre": 100.0},
                 {"exists": True, "sha256": "sha_a", "mtime_post": 100.0})
check("F03 present+sha同+mtim同 → leftover_unchanged/high/is_new=False",
      r_f03["verdict"] == "leftover_unchanged" and r_f03["confidence"] == "high" and r_f03["is_new"] is False, str(r_f03))
# 未采集形态置信恒非 high（_test_candidate_lf.py:300-309 C2 同形态）
uncollect_conf = []
for pre in [None, {}, {"exists": False}, {"state": "unknown"}]:
    r = classify(pre, {"exists": True, "sha256": "x", "mtime_post": 1.0})
    uncollect_conf.append(r["confidence"])
check("未采集 4 形态置信恒非 high（C2 同形态）", all(c != "high" for c in uncollect_conf), str(uncollect_conf))
# 三态可分（R3 §1 / 裁定一口径）
post_same = {"exists": True, "sha256": "h", "mtime_post": 1.0}
v_unknown = classify(None, post_same)["verdict"]
v_absent = classify({"state": "absent_confirmed", "exists": False}, post_same)["verdict"]
v_present = classify({"state": "present", "exists": True, "sha256": "other", "mtime_pre": 0.0}, post_same)["verdict"]
check("三态可分：unknown / new_first_appearance / new_write 两两不等",
      len({v_unknown, v_absent, v_present}) == 3, f"{v_unknown} / {v_absent} / {v_present}")
# 快照采集器：不存在路径 → absent_confirmed（只读判定，无写盘）
snap_absent = snapmaker(ROOT / "lead/b2b_isolated_20261107/__integ_no_such_file__.txt")
check("快照采集：不存在路径 → absent_confirmed", snap_absent.get("state") == "absent_confirmed", str(snap_absent)[:120])
# 快照采集：在场文件（隔离副本自身，只读输入）→ present 且 sha256 与实算一致
snap_present = snapmaker(ISOL)
check("快照采集：隔离副本自身为只读输入 → present 且 sha256 一致",
      snap_present.get("state") == "present" and snap_present.get("sha256") == hi,
      f"sha={snap_present.get('sha256', '')[:16]}... 双时刻={'captured_at_epoch' in snap_present and 'captured_at_iso' in snap_present}")

print("=" * 72)
print("== [5] diff 统计（隔离副本 vs 母本，difflib 行文本口径） ==")
m_lines = mother_text.split("\n")
i_lines = isol_text.split("\n")
print(f"母本 split 行数 = {len(m_lines)}（LF={mother_text.count(chr(10))}）  隔离副本 split 行数 = {len(i_lines)}（LF={isol_text.count(chr(10))}）")
sm = difflib.SequenceMatcher(a=m_lines, b=i_lines, autojunk=False)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
plus = sum(j2 - j1 for tag, i1, i2, j1, j2 in ops if tag in ("replace", "insert"))
minus = sum(i2 - i1 for tag, i1, i2, j1, j2 in ops if tag in ("replace", "delete"))
check("变更 opcode 块 = 12", len(ops) == 12, str([op[0] for op in ops]))
check("+255 / -13（与 R3 :85 候选口径一致）", (plus, minus) == (255, 13), f"+{plus} / -{minus}")

print("=" * 72)
print("== [6] 决定性重建：母本 + 九 hunk == 隔离副本（逐字节） ==")


def parse_design_diff_blocks(text: str):
    lines = text.split("\n")
    blocks, cur, in_block = [], None, False
    for l in lines:
        s = l.strip()
        if s == "```diff":
            in_block, cur = True, []
        elif in_block and s == "```":
            while cur and cur[-1] == "":
                cur.pop()
            blocks.append(cur)
            in_block, cur = False, None
        elif in_block:
            cur.append(l)
    return [b for b in blocks if any(x.startswith("@@ ") for x in b)]


def apply_hunks(mother_lines, hunk_bodies, source):
    """标准 unified diff 语义套用；逐行断言上下文/`-` 行与母本原文一致、计数与 @@ 头声明一致。"""
    out = list(mother_lines)
    offset = 0
    minus_total = plus_total = 0
    for bi, body_all in enumerate(hunk_bodies, 1):
        hdr_idx = next(i for i, l in enumerate(body_all) if l.startswith("@@ "))
        m = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", body_all[hdr_idx])
        assert m, f"{source} hunk{bi} 头无法解析: {body_all[hdr_idx]!r}"
        old_start, old_count = int(m.group(1)), int(m.group(2) or 1)
        new_count = int(m.group(4) or 1)
        body = body_all[hdr_idx + 1:]
        while body and body[-1] == "":
            body.pop()
        master_idx = old_start - 1          # 上下文/`-` 行按母本原始坐标断言
        out_pos = old_start - 1 + offset    # 输出缓冲按累计 offset 坐标切片
        new_body = []
        consumed = 0
        for l in body:
            tag, rest = (l[0], l[1:]) if l else (" ", "")
            if tag == " ":
                assert mother_lines[master_idx + consumed] == rest, \
                    f"{source} hunk{bi} 上下文行不匹配 母本@{old_start + consumed}: {rest!r} vs {mother_lines[master_idx + consumed]!r}"
                new_body.append(mother_lines[master_idx + consumed])
                consumed += 1
            elif tag == "-":
                assert mother_lines[master_idx + consumed] == rest, \
                    f"{source} hunk{bi} `-` 行不匹配 母本@{old_start + consumed}: {rest!r} vs {mother_lines[master_idx + consumed]!r}"
                consumed += 1
                minus_total += 1
            elif tag == "+":
                new_body.append(rest)
                plus_total += 1
            else:
                raise AssertionError(f"{source} hunk{bi} 非法行首: {l[:40]!r}")
        assert consumed == old_count, f"{source} hunk{bi} 消费行数 {consumed} != 头声明 {old_count}"
        assert len(new_body) == new_count, f"{source} hunk{bi} 产出行数 {len(new_body)} != 头声明 {new_count}"
        out[out_pos:out_pos + consumed] = new_body
        offset += len(new_body) - consumed
    return out, minus_total, plus_total


design_blocks = parse_design_diff_blocks(design_text := design_bytes.decode("utf-8"))
check("设计 §4 ```diff 块数 = 9", len(design_blocks) == 9, f"实际 {len(design_blocks)}")
hdr_old = []
for b in design_blocks:
    hdr = next(l for l in b if l.startswith("@@ "))
    g = re.match(r"@@ -(\d+),(\d+) ", hdr)
    hdr_old.append((int(g.group(1)), int(g.group(2))))
EXPECT_INTERVALS = [(212, 6), (4458, 6), (4558, 8), (4572, 20), (5906, 7), (5936, 7), (6294, 6), (6386, 6), (7122, 7)]
check("设计九 hunk 母本区间 == B2B_DESIGN.md:635 实算区间", hdr_old == EXPECT_INTERVALS, str(hdr_old))
reb_lines, dminus, dplus = apply_hunks(m_lines, design_blocks, "设计§4")
reb_text = "\n".join(reb_lines)
check("设计九 hunk ± 计数 = +255 / -13", (dplus, dminus) == (255, 13), f"+{dplus} / -{dminus}")
check("★ 母本 + 设计 §4 九 hunk == 隔离副本（逐字符串 == 逐字节）",
      reb_text == isol_text and reb_text.encode("utf-8") == isol_bytes,
      f"重建 sha256={hashlib.sha256(reb_text.encode('utf-8')).hexdigest()[:16]}...")

diff_lines = diff_bytes.decode("utf-8").split("\n")
first_hunk = next(i for i, l in enumerate(diff_lines) if l.startswith("@@ "))
header = diff_lines[:first_hunk]
hunk_bodies, cur = [], None
for l in diff_lines[first_hunk:]:
    if l.startswith("@@ "):
        if cur is not None:
            while cur and cur[-1] == "":
                cur.pop()
            hunk_bodies.append(cur)
        cur = [l]
    elif cur is not None:
        cur.append(l)
if cur is not None:
    while cur and cur[-1] == "":
        cur.pop()
    hunk_bodies.append(cur)
check("CANDIDATE_LF.diff @@ 头数 = 9", len(hunk_bodies) == 9, f"实际 {len(hunk_bodies)}")
check("CANDIDATE_LF.diff 头两行 --- +++ 指向母本/候选",
      len(header) >= 2 and header[0].startswith("--- a/out/re_work/") and header[1].startswith("+++ b/lead/b2b_candidate_lf_20261107/"),
      str(header[:2]))
reb2_lines, fminus, fplus = apply_hunks(m_lines, hunk_bodies, "CANDIDATE_LF.diff")
reb2_text = "\n".join(reb2_lines)
check("CANDIDATE_LF.diff ± 计数 = +255 / -13", (fplus, fminus) == (255, 13), f"+{fplus} / -{fminus}")
check("★ 母本 + CANDIDATE_LF.diff == 隔离副本（逐字符串 == 逐字节）",
      reb2_text == isol_text and reb2_text.encode("utf-8") == isol_bytes,
      f"重建 sha256={hashlib.sha256(reb2_text.encode('utf-8')).hexdigest()[:16]}...")

print("=" * 72)
print("== [7] 九锚点定位（门禁 _check_candidate_r3.py:84-94 ANCHORS 同源） ==")
missing = []
for hid, token in ANCHORS:
    if token not in isol_text:
        missing.append(hid)
check("9/9 锚点全部可定位", not missing, "missing=" + str(missing) if missing else "H1–H9 全命中")

print("=" * 72)
npass, nfail = RESULTS.count(True), RESULTS.count(False)
print(f"== 汇总: PASS={npass} FAIL={nfail} ==")
if nfail == 0:
    print("INTEG_PROBE_DONE")
else:
    print("INTEG_PROBE_FAILED")
sys.exit(0 if nfail == 0 else 1)
