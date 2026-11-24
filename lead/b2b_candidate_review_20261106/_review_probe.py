# -*- coding: utf-8 -*-
"""
_review_probe.py · B2b 候选独立复审探针（范围核验员）
=====================================================
只读母本 / 候选 / 设计 / 预审四件；不做任何真机、采样、hook；不改任何文件。
运行方式（绝对路径 + 隔离模式 + UTF-8）：
    python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b2b_candidate_review_20261106/_review_probe.py

本脚本做 5 件事：
  1) 四件指纹实算（sha256 + 字节数，hashlib，本机无 sha256sum/wc）
  2) difflib 全量比对母本 vs 候选：每个 opcode 变更块 + unified_diff(n=3) 的 9 个 hunk
  3) 逐块归因到 H01..H09（按设计 §4 的锚点内容匹配）；归不到的标「★ 无法归属」
     并逐行做「候选 +/- 行是否在设计 §4 声明的 +/- 行里」的夹带检出
  4) AST 全量扫 copy_post_except_evidence 的所有调用点及参数
  5) AST 扫退出码判据路径是否读 freshness_*
输出：终端 + 同目录 _review_probe_out.txt（由外层 shell 重定向落盘）
"""
import ast
import difflib
import hashlib
import io
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
REVIEW = ROOT / "lead" / "b2b_candidate_review_20261106"

PATHS = {
    "母本": ROOT / "out" / "re_work" / "work_chain" / "CONTINUE_20261003"
            / "lead" / "qc151_u0400_trip" / "qc151_trip.py",
    "候选": ROOT / "lead" / "b2b_candidate_20261106" / "qc151_trip.candidate.py",
    "设计": ROOT / "lead" / "b2b_design_20261106" / "B2B_DESIGN.md",
    "预审": ROOT / "lead" / "b2b_preaudit_20261106" / "B2B_PREAUDIT.md",
}

# TASK.md:20-25 绑定的期望指纹（开工先验，不符即停）
EXPECT = {
    "母本": ("517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636", 399508),
    "候选": ("9656e432f5b571590b757bb78869c274fba40220ce57b7a70da9b4a987b967cc", 420292),
    "设计": ("565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf", 66735),
    "预审": ("3f97f3a4664981961b72a91a60053fe8c867fa9d8e25442e7159c3046ccbf69f", 20615),
}

OUT = []


def emit(line=""):
    OUT.append(str(line))
    print(line)


def rule(title):
    emit("")
    emit("=" * 78)
    emit(title)
    emit("=" * 78)


# ----------------------------------------------------------------------------
# 0) 读文件 + 四件指纹实算
# ----------------------------------------------------------------------------
rule("0 四件指纹实算（hashlib.sha256；字节数 = len(bytes)）")
RAW = {}
TEXT = {}
LINES = {}
for k, p in PATHS.items():
    b = p.read_bytes()
    RAW[k] = b
    TEXT[k] = b.decode("utf-8")          # 设计/候选/母本均 UTF-8；解码失败会直接抛
    LINES[k] = TEXT[k].splitlines()
    sha = hashlib.sha256(b).hexdigest()
    exp_sha, exp_bytes = EXPECT[k]
    ok = (sha == exp_sha and len(b) == exp_bytes)
    emit(f"[{k}] path = {p}")
    emit(f"    sha256 = {sha}")
    emit(f"    bytes  = {len(b)}   lines = {len(LINES[k])}")
    emit(f"    绑定核对 (TASK.md:20-25) = {'MATCH' if ok else '*** DRIFT ***'}"
         f"  expect sha={exp_sha} bytes={exp_bytes}")
    if not ok:
        emit("*** 上游漂移：按 TASK.md §1 应立即停 ***")
        sys.exit(2)

M = LINES["母本"]
C = LINES["候选"]

# ----------------------------------------------------------------------------
# 1) 设计 §4 的 9 个 hunk：抽出各自 +/- 行、上下文行、母本锚点区间
# ----------------------------------------------------------------------------
rule("1 设计 §4 的 9 个 @@ hunk 解析（H01–H09 的锚点内容）")
dl = LINES["设计"]
i4 = next(i for i, l in enumerate(dl) if l.startswith("## 4 完整 diff"))
i5 = next(i for i, l in enumerate(dl) if l.startswith("## 5 字段契约"))
sec4 = dl[i4:i5]

DESIGN_HUNKS = []      # [{'idx','header','m_start','m_count','c_start','c_count','plus','minus','ctx'}]
cur = None
for l in sec4:
    s = l.strip()
    if s == "```diff":
        cur = {"plus": [], "minus": [], "ctx": [], "header": None}
        continue
    if cur is not None and s == "```":
        DESIGN_HUNKS.append(cur)
        cur = None
        continue
    if cur is None:
        continue
    if l.startswith("@@ "):
        cur["header"] = l.strip()
        continue
    if l.startswith("+") and not l.startswith("+++"):
        cur["plus"].append(l[1:])
    elif l.startswith("-") and not l.startswith("---"):
        cur["minus"].append(l[1:])
    elif l.startswith(" "):
        cur["ctx"].append(l[1:])
    # 其余（空串等）忽略

import re
for n, h in enumerate(DESIGN_HUNKS, 1):
    m = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", h["header"] or "")
    if m:
        h["idx"] = n
        h["m_start"], h["m_count"], h["c_start"], h["c_count"] = map(int, m.groups())
        h["m_end"] = h["m_start"] + h["m_count"] - 1   # 母本 1-based 锚点区间（含上下文）
        h["c_end"] = h["c_start"] + h["c_count"] - 1
        h["H"] = f"H{n:02d}"
    else:
        emit(f"!!! 设计 hunk #{n} 头无法解析: {h['header']!r}")

emit(f"设计 §4 hunk 数 = {len(DESIGN_HUNKS)}  (§4:202 / §7:658 声明 = 9)")

# 设计 §7 对照表（H01..H09 的文字描述）
s7 = next(i for i, l in enumerate(dl) if l.startswith("## 7 改动清单"))
s8 = next(i for i, l in enumerate(dl) if l.startswith("## 8 未验"))
SEC7 = {}
for l in dl[s7:s8]:
    mm = re.match(r"\|\s*(H\d\d)\s*\|\s*(.*?)\s*\|", l)
    if mm:
        SEC7[mm.group(1)] = mm.group(2)
for n, h in enumerate(DESIGN_HUNKS, 1):
    H = f"H{n:02d}"
    emit(f"[{H}] {h['header']}  母本锚点 {h['m_start']}-{h['m_end']}"
         f" | +{len(h['plus'])} -{len(h['minus'])} ctx{len(h['ctx'])}")
    emit(f"      §7: {SEC7.get(H, '(未读到)')}")

DESIGN_PLUS = [x for h in DESIGN_HUNKS for x in h["plus"]]
DESIGN_MINUS = [x for h in DESIGN_HUNKS for x in h["minus"]]
DP = Counter(DESIGN_PLUS)
DM = Counter(DESIGN_MINUS)
emit(f"设计 §4 合计: + 行 {len(DESIGN_PLUS)} / - 行 {len(DESIGN_MINUS)}")

# ----------------------------------------------------------------------------
# 2) difflib 全量比对母本 vs 候选
# ----------------------------------------------------------------------------
rule("2 difflib 全量比对：母本 vs 候选")
sm = difflib.SequenceMatcher(None, M, C, autojunk=False)
OPS_ALL = sm.get_opcodes()
OPS_CHG = [o for o in OPS_ALL if o[0] != "equal"]
UD = list(difflib.unified_diff(M, C, fromfile="mother", tofile="candidate",
                               n=3, lineterm=""))
UD_HDRS = [l for l in UD if l.startswith("@@ ")]
emit(f"母本行数 = {len(M)}；候选行数 = {len(C)}；SequenceMatcher opcode 变更块 = {len(OPS_CHG)}"
     f"；unified_diff(n=3) hunk 头 = {len(UD_HDRS)}")

emit("-- 2.1 全部 opcode 变更块（起止行号 + 行数）--")
for n, (tag, i1, i2, j1, j2) in enumerate(OPS_CHG, 1):
    emit(f"  block#{n:02d} {tag:<7} 母本 {i1+1}-{i2} ({i2-i1} 行)"
         f"  ->  候选 {j1+1}-{j2} ({j2-j1} 行)")
    for x in M[i1:i2]:
        emit(f"      - {x}")
    for x in C[j1:j2]:
        emit(f"      + {x}")

emit("-- 2.2 unified_diff(n=3) 的 9 个 hunk 头（与设计 §4 逐字核对）--")
for n, hdr in enumerate(UD_HDRS, 1):
    des = DESIGN_HUNKS[n-1]["header"] if n-1 < len(DESIGN_HUNKS) else "(无)"
    emit(f"  hunk#{n:02d} candidate = {hdr}")
    emit(f"            design     = {des}   {'SAME' if hdr == des else '*** DIFFERENT ***'}")

# 实际 +/- 行 vs 设计声明 +/- 行（逐行多重集比对 = 夹带检出）
ACT_PLUS = [l[1:] for l in UD if l.startswith("+") and not l.startswith("+++")]
ACT_MINUS = [l[1:] for l in UD if l.startswith("-") and not l.startswith("---")]
AP, AM = Counter(ACT_PLUS), Counter(ACT_MINUS)
extra_plus = list((AP - DP).elements())     # 候选有、设计未声明 = 夹带
missing_plus = list((DP - AP).elements())   # 设计声明但候选没有 = 缺实现
extra_minus = list((AM - DM).elements())
missing_minus = list((DM - AM).elements())
emit(f"候选实际 + 行 {len(ACT_PLUS)} / - 行 {len(ACT_MINUS)}；"
     f"设计声明 + 行 {len(DESIGN_PLUS)} / - 行 {len(DESIGN_MINUS)}")
emit(f"★ 候选 + 行中设计未声明（夹带嫌疑） = {len(extra_plus)}")
for x in extra_plus:
    emit(f"    EXTRA_PLUS   {x!r}")
emit(f"★ 设计声明 + 行候选缺失 = {len(missing_plus)}")
for x in missing_plus:
    emit(f"    MISSING_PLUS {x!r}")
emit(f"★ 候选 - 行中设计未声明 = {len(extra_minus)}")
for x in extra_minus:
    emit(f"    EXTRA_MINUS  {x!r}")
emit(f"★ 设计声明 - 行候选缺失 = {len(missing_minus)}")
for x in missing_minus:
    emit(f"    MISSING_MINUS {x!r}")

# ----------------------------------------------------------------------------
# 3) 逐差异块归因到 H01..H09
# ----------------------------------------------------------------------------
rule("3 逐差异块归因 H01–H09（按设计 §4 锚点内容匹配）")
# 每个 opcode 块的「改变行」在设计哪个 hunk 的 +/- 行里出现 => 归属该 H
# 归因凭据：块的 + 行逐行属于某 H 的 plus 多重集；- 行属于某 H 的 minus 多重集
H_PLUS = {h["H"]: Counter(h["plus"]) for h in DESIGN_HUNKS}
H_MINUS = {h["H"]: Counter(h["minus"]) for h in DESIGN_HUNKS}
# 母本锚点区间（用于第二凭据：块落在哪个 hunk 的母本覆盖区间内）
H_RANGE = {h["H"]: (h["m_start"], h["m_end"]) for h in DESIGN_HUNKS}


def line_owners(lines, table):
    """逐行返回这些行能归属的 H 集合（多重集口径：每个 H 独立判「是否含有该行」）"""
    owners = set()
    for x in lines:
        for H, cnt in table.items():
            if cnt.get(x, 0) > 0:
                owners.add(H)
    return owners


ATTRIB = []          # (block#, tag, m_range, c_range, {H or None}, note)
for n, (tag, i1, i2, j1, j2) in enumerate(OPS_CHG, 1):
    minus = M[i1:i2]
    plus = C[j1:j2]
    owners_plus = {H for H in H_PLUS if all(H_PLUS[H].get(x, 0) > 0 for x in plus)} if plus else set(H_PLUS)
    owners_minus = {H for H in H_MINUS if all(H_MINUS[H].get(x, 0) > 0 for x in minus)} if minus else set(H_MINUS)
    # 严格口径：+ 行全部能在某 H 的 + 行里找到，且 - 行全部能在同 H 的 - 行里找到
    owners = owners_plus & owners_minus
    # 锚点区间口径：母本块起点落在 H 覆盖区间内
    m_lo, m_hi = i1 + 1, i2
    range_hit = [H for H, (a, b) in H_RANGE.items() if not (m_hi < a or m_lo > b)]
    note = ""
    matched = sorted(owners)
    if len(matched) == 1:
        H = matched[0]
    elif len(matched) > 1:
        # 多个 H 都含这些行时，用母本锚点区间收敛
        inter = [x for x in matched if x in range_hit]
        H = inter[0] if len(inter) == 1 else (range_hit[0] if len(range_hit) == 1 else None)
        note = f"多候选 {matched} / 区间 {range_hit} => 取 {H}"
    else:
        # 内容未命中：若块完全无改变行（不可能）或纯上下文，尝试区间
        H = range_hit[0] if len(range_hit) == 1 else None
        note = f"内容未命中设计 +/- 行；区间候选 {range_hit}"
    ATTRIB.append((n, tag, (i1+1, i2), (j1+1, j2), H, note, plus, minus, range_hit))

emit("-- 3.1 逐块归属（opcode 块 = 12 个；unified hunk = 9 个）--")
attr_ok = 0
unattributed = []
for (n, tag, mr, cr, H, note, plus, minus, range_hit) in ATTRIB:
    if H:
        attr_ok += 1
        emit(f"  block#{n:02d} 母本 {mr[0]}-{mr[1]} / 候选 {cr[0]}-{cr[1]}"
             f"  => 归属 {H}  {note}")
    else:
        unattributed.append((n, tag, mr, cr, plus, minus, range_hit, note))
        emit(f"  block#{n:02d} 母本 {mr[0]}-{mr[1]} / 候选 {cr[0]}-{cr[1]}"
             f"  => ★ 无法归属  {note}")
        for x in minus:
            emit(f"        - {x!r}")
        for x in plus:
            emit(f"        + {x!r}")

emit("")
emit("-- 3.2 按 unified_diff 9 个 hunk 归属（设计 §4 / §7 口径）--")
UD_HUNKS = []         # 每个 unified hunk 的 header / plus / minus
cur = None
for l in UD:
    if l.startswith("@@ "):
        if cur:
            UD_HUNKS.append(cur)
        cur = {"header": l, "plus": [], "minus": []}
    elif cur is not None:
        if l.startswith("+") and not l.startswith("+++"):
            cur["plus"].append(l[1:])
        elif l.startswith("-") and not l.startswith("---"):
            cur["minus"].append(l[1:])
if cur:
    UD_HUNKS.append(cur)
for n, h in enumerate(UD_HUNKS, 1):
    H = f"H{n:02d}"
    des = DESIGN_HUNKS[n-1] if n-1 < len(DESIGN_HUNKS) else None
    hdr_same = (des is not None and h["header"] == des["header"])
    p_same = (des is not None and h["plus"] == des["plus"])
    m_same = (des is not None and h["minus"] == des["minus"])
    verdict = "归属 " + H if (hdr_same and p_same and m_same) else "★ 无法归属"
    emit(f"  hunk#{n:02d} {h['header']} => {verdict}"
         f"  [header={'SAME' if hdr_same else 'DIFF'} +行={'SAME' if p_same else 'DIFF'}"
         f"(候选{len(h['plus'])}/设计{len(des['plus']) if des else '?'}) "
         f"-行={'SAME' if m_same else 'DIFF'}"
         f"(候选{len(h['minus'])}/设计{len(des['minus']) if des else '?'})]")
    if not p_same and des is not None:
        cp, dp = Counter(h["plus"]), Counter(des["plus"])
        for x in (cp - dp).elements():
            emit(f"        候选多出的 + 行: {x!r}")
        for x in (dp - cp).elements():
            emit(f"        候选缺少的 + 行: {x!r}")
    if not m_same and des is not None:
        cm, dm = Counter(h["minus"]), Counter(des["minus"])
        for x in (cm - dm).elements():
            emit(f"        候选多出的 - 行: {x!r}")
        for x in (dm - cm).elements():
            emit(f"        候选缺少的 - 行: {x!r}")

# ----------------------------------------------------------------------------
# 4) AST: copy_post_except_evidence 全部调用点及参数
# ----------------------------------------------------------------------------
rule("4 AST 全量扫 copy_post_except_evidence 调用点及参数（候选）")
ctree = ast.parse(TEXT["候选"], filename=str(PATHS["候选"]))


def dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return dotted(node.value) + "." + node.attr
    return ast.unparse(node)


def enclosing_func(tree):
    """返回 {node: 最近的函数全名}"""
    mp = {}
    stack = []

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            stack.append(node.name)
            mp[node] = ".".join(stack)
            self.generic_visit(node)
            stack.pop()

        def visit_AsyncFunctionDef(self, node):
            stack.append(node.name)
            mp[node] = ".".join(stack)
            self.generic_visit(node)
            stack.pop()
    V().visit(tree)
    # 自顶向下给所有节点标注
    owner = {}

    class W(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, node):
            self.stack.append(node.name)
            owner[node] = ".".join(self.stack)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node):
            self.stack.append(node.name)
            owner[node] = ".".join(self.stack)
            self.generic_visit(node)
            self.stack.pop()

        def generic_visit(self, node):
            owner[node] = ".".join(self.stack) if self.stack else "<module>"
            super().generic_visit(node)
    W().visit(tree)
    return owner


OWNER = enclosing_func(ctree)
CALLS = []
for node in ast.walk(ctree):
    if isinstance(node, ast.Call):
        fn = dotted(node.func)
        if fn == "copy_post_except_evidence" or fn.endswith(".copy_post_except_evidence"):
            args = [ast.unparse(a) for a in node.args]
            kws = [(k.arg, ast.unparse(k.value)) for k in node.keywords]
            CALLS.append((node.lineno, fn, args, kws, OWNER.get(node, "?")))
emit(f"候选里 copy_post_except_evidence 调用点总数 = {len(CALLS)}")
CALL_LIST = sorted(CALLS)
for ln, fn, args, kws, owner in CALL_LIST:
    emit(f"  候选:{ln}  in {owner}  {fn}(...)")
    emit(f"      位置参数 ({len(args)}): {args}")
    emit(f"      关键字参数 ({len(kws)}): {kws}")
    has = any(k == "pre_freshness_snapshot" for k, _ in kws)
    emit(f"      pre_freshness_snapshot 传参 = {'YES' if has else '*** NO ***'}")

# 定义签名
emit("-- 4.1 定义签名 --")
for node in ast.walk(ctree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
            node.name in ("copy_post_except_evidence", "finalize_trip"):
        a = node.args
        pos = [x.arg for x in a.posonlyargs + a.args]
        defaults = [ast.unparse(d) for d in a.defaults]
        emit(f"  候选:{node.lineno} def {node.name}("
             f"pos={pos}, defaults={defaults}, "
             f"kwonly={[x.arg for x in a.kwonlyargs]}, "
             f"kw_defaults={[ast.unparse(d) if d else None for d in a.kw_defaults]})")

# ----------------------------------------------------------------------------
# 5) AST: 退出码判据路径是否读 freshness_*
# ----------------------------------------------------------------------------
rule("5 AST 扫退出码判据路径是否读 freshness_*（候选）")
# 口径（设计 §6:629/:635/:639 + TASK.md:68）：
#   E 唯一口径 = except_set_diff (:672-708 母本 / 候选 :? ) + :5984-5990 集合差块
#   影响退出码 = note_cleanup_failure(...) 各调用 + merge_cleanup_code / CLEANUP_FAILURES
# 做法：定位这些函数体 / 调用语句的源码行区间，逐 token 找 freshness_* 名字。

# 5.1 命名收集：所有含 freshness 的标识符（Name/Attribute/Constant str）
FRESH_NAMES = []
for node in ast.walk(ctree):
    if isinstance(node, ast.Name) and "freshness" in node.id:
        FRESH_NAMES.append((node.lineno, "Name", node.id))
    elif isinstance(node, ast.Attribute) and "freshness" in node.attr:
        FRESH_NAMES.append((node.lineno, "Attr", node.attr))
    elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
            and "freshness_" in node.value:
        FRESH_NAMES.append((node.lineno, "Str", node.value[:60]))
emit(f"候选 AST 中含 'freshness' 的标识符/字符串总数 = {len(FRESH_NAMES)}")
by_line = defaultdict(list)
for ln, kind, name in FRESH_NAMES:
    by_line[ln].append(f"{kind}:{name}")
emit(f"分布在 {len(by_line)} 个行号上：{sorted(by_line)}")

# 5.2 定义退出码判据函数集合
EXIT_FUNC_NAMES = {"except_set_diff"}          # E 唯一口径实现
# note_cleanup_failure / merge_cleanup_code / CLEANUP_FAILURES 相关定义
AUX_FUNC_NAMES = {"note_cleanup_failure", "merge_cleanup_code", "main",
                  "finalize_trip", "_write_final_records", "run_guarded_steps"}
DEF_RANGES = {}
for node in ast.walk(ctree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
            node.name in EXIT_FUNC_NAMES | AUX_FUNC_NAMES:
        DEF_RANGES.setdefault(node.name, []).append((node.lineno, node.end_lineno))
emit("-- 5.1 退出码判据相关函数体区间（候选行号）--")
for name in sorted(DEF_RANGES):
    emit(f"  {name}: {DEF_RANGES[name]}")

# 5.3 所有 note_cleanup_failure 调用语句的源码区间
NC_CALLS = []
for node in ast.walk(ctree):
    if isinstance(node, ast.Call) and dotted(node.func) == "note_cleanup_failure":
        NC_CALLS.append((node.lineno, node.end_lineno, ast.unparse(node.func),
                         [ast.unparse(a) for a in node.args]))
emit(f"-- 5.2 note_cleanup_failure 调用点 = {len(NC_CALLS)} --")
for lo, hi, fn, args in sorted(NC_CALLS):
    emit(f"  候选:{lo}-{hi} {fn}(...)  args={args}")

# 5.4 「退出码判据路径」的并集区间：
#     except_set_diff 函数体 + finalize_trip 里 _except_diff 函数体（:5984-5990 对应）
#     + 全部 note_cleanup_failure 调用语句行 + note_cleanup_failure/merge_cleanup_code 定义体
JUDGMENT_RANGES = []
for name in ("except_set_diff", "note_cleanup_failure", "merge_cleanup_code"):
    for lo, hi in DEF_RANGES.get(name, []):
        JUDGMENT_RANGES.append((f"def {name}", lo, hi))
for lo, hi, _, _ in NC_CALLS:
    JUDGMENT_RANGES.append(("note_cleanup_failure call", lo, hi))
# finalize_trip 内的 _except_diff（集合差判据块）
for node in ast.walk(ctree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
            node.name in ("_except_diff", "_ctrl_post", "_t0_t1_sha_diff"):
        JUDGMENT_RANGES.append((f"def {node.name}", node.lineno, node.end_lineno))
# main 里读取 CLEANUP_FAILURES / merge_cleanup_code 的语句
MF_LINES = [i for i, l in enumerate(C, 1)
            if "CLEANUP_FAILURES" in l or "merge_cleanup_code" in l]
emit(f"-- 5.3 含 CLEANUP_FAILURES / merge_cleanup_code 的行 = {len(MF_LINES)} --")
for ln in MF_LINES:
    emit(f"  候选:{ln} {C[ln-1].strip()}")
    JUDGMENT_RANGES.append(("cleanup/exit read", ln, ln))

# 判定：是否有 freshness 标识符落在上述任一判据区间内
HITS = []
for ln, items in by_line.items():
    for tag, lo, hi in JUDGMENT_RANGES:
        if lo <= ln <= hi:
            HITS.append((ln, tag, lo, hi, items))
emit("")
emit(f"★ 退出码判据区间内读到 freshness_* 的命中数 = {len(HITS)}")
for ln, tag, lo, hi, items in sorted(HITS):
    emit(f"  HIT 候选:{ln} in [{tag} {lo}-{hi}] -> {items}")

# 5.5 更严格的逐 token 扫描：判据区间源码里是否出现 freshness_ 字面量
emit("")
emit("-- 5.4 判据区间源码逐行扫 'freshness_' 字面量（含注释行，从严）--")
covered = set()
for tag, lo, hi in JUDGMENT_RANGES:
    for x in range(lo, hi + 1):
        covered.add(x)
lit_hits = [(x, C[x-1]) for x in sorted(covered)
            if 1 <= x <= len(C) and "freshness_" in C[x-1]]
emit(f"  判据覆盖行号数 = {len(covered)}；其中含 'freshness_' 字面量的行 = {len(lit_hits)}")
for x, line in lit_hits:
    emit(f"  LIT 候选:{x} {line.rstrip()}")

# 5.6 补充：E 口径函数 except_set_diff 与集合差判据块逐字是否改动
emit("")
emit("-- 5.5 E 口径实现是否被 9 个 hunk 改动（母本 :672-708 / :5984-5990）--")
for label, mstart, mend in (("except_set_diff", 672, 708),
                            ("finalize_trip._except_diff 判据块", 5984, 5990)):
    overlap = [(i1+1, i2) for (tag, i1, i2, j1, j2) in OPS_CHG
               if not (i2 < mstart or i1+1 > mend)]
    emit(f"  {label} 母本 {mstart}-{mend}: 与之重叠的 opcode 变更块 = {overlap}"
         f"  => {'UNCHANGED（E 口径未被改）' if not overlap else '*** 被改动 ***'}")

# ----------------------------------------------------------------------------
# 7) 重建验证（最强口径）：把设计 §4 的 9 个 hunk 逐字套回母本，与候选逐行比
#    多重集比对抓不出「同样几行但换了位置/顺序」；重建能。
#    每个 hunk 内的行按 diff 顺序记 ' '(ctx) / '-'(del) / '+'(add)。
#    母本窗口 = hunk 里所有 ctx + '-' 行（按出现顺序），应等于母本对应行；
#    替换后窗口 = hunk 里所有 ctx + '+' 行（按出现顺序），应等于候选对应行。
# ----------------------------------------------------------------------------
rule("7 重建验证：设计 §4 的 9 个 hunk 逐字套回母本 == 候选？")
DH_BODY = []       # 与 DESIGN_HUNKS 对齐，保存每行 (kind, text)
cur = None
for l in sec4:
    s = l.strip()
    if s == "```diff":
        cur = []
        continue
    if cur is not None and s == "```":
        DH_BODY.append(cur)
        cur = None
        continue
    if cur is None:
        continue
    if l.startswith("@@ "):
        continue
    if l.startswith("+") and not l.startswith("+++"):
        cur.append(("+", l[1:]))
    elif l.startswith("-") and not l.startswith("---"):
        cur.append(("-", l[1:]))
    elif l.startswith(" "):
        cur.append((" ", l[1:]))
emit(f"参与重建的 hunk 体数 = {len(DH_BODY)}")

RECON = list(M)              # 母本副本
rebuild_errors = []
# 关键：9 个 hunk 的母本锚点互不重叠但「插入行数」会改变后续行号，
# 因此不能按固定行号就地反复切片；改为在原母本行号上收集替换片段，
# 最后按 start 升序一次性线性拼接（避免行号漂移）。
PATCHES = []                 # (start_1based, old_len, new_win, H)
for n, (h, body) in enumerate(zip(DESIGN_HUNKS, DH_BODY), 1):
    H = h["H"]
    start = h["m_start"]           # 1-based
    old_win = [t for k, t in body if k in (" ", "-")]
    new_win = [t for k, t in body if k in (" ", "+")]
    got = M[start-1: start-1+len(old_win)]
    if got != old_win:
        rebuild_errors.append((H, "母本窗口不匹配", start, len(old_win), got[:3], old_win[:3]))
        emit(f"  [{H}] 母本 {start}-{start+len(old_win)-1} 窗口逐字核对 = MISMATCH")
    else:
        emit(f"  [{H}] 母本 {start}-{start+len(old_win)-1} 窗口逐字核对 = MATCH"
             f"  (ctx+'-' {len(old_win)} 行 -> ctx+'+' {len(new_win)} 行)")
    PATCHES.append((start, len(old_win), new_win, H))

# 线性拼接（按 start 升序，区间不重叠）
PATCHES.sort(key=lambda x: x[0])
RECON = []
pos = 0                      # 已消费的母本行（0-based）
for start, old_len, new_win, H in PATCHES:
    RECON.extend(M[pos: start-1])
    RECON.extend(new_win)
    pos = start - 1 + old_len
RECON.extend(M[pos:])
emit(f"  套用片段数 = {len(PATCHES)}；相邻片段重叠检查 = "
     f"{'无重叠' if all(PATCHES[i][0]+PATCHES[i][1]-1 < PATCHES[i+1][0] for i in range(len(PATCHES)-1)) else '*** 有重叠 ***'}")

RECON_EQ = (RECON == C)
emit("")
emit(f"重建文本行数 = {len(RECON)}；候选行数 = {len(C)}")
emit(f"★ 设计 §4 逐字套用(母本) == 候选 逐行一致 = {RECON_EQ}")
if not RECON_EQ:
    for k in range(min(len(RECON), len(C))):
        if RECON[k] != C[k]:
            emit(f"  首个不一致 行 {k+1}: 重建={RECON[k]!r} / 候选={C[k]!r}")
            break
    emit(f"  重建窗口错误条目 = {rebuild_errors}")
# 重建文本能否被 AST 解析
try:
    ast.parse("\n".join(RECON) + "\n", filename="<rebuilt>")
    emit("重建文本 ast.parse = PASS")
except SyntaxError as e:
    emit(f"重建文本 ast.parse = FAIL {e}")

# ----------------------------------------------------------------------------
# 8) 汇总
# ----------------------------------------------------------------------------
rule("8 汇总")
emit(f"差异块总数（opcode 变更块） = {len(OPS_CHG)}")
emit(f"unified_diff(n=3) hunk 数   = {len(UD_HDRS)}（对应设计 §4 的 H01–H09）")
emit(f"可归属数（逐 opcode 块）     = {attr_ok}")
emit(f"无法归属数（逐 opcode 块）   = {len(unattributed)}")
emit(f"候选 + 行中设计未声明 = {len(extra_plus)}；设计 + 行候选缺失 = {len(missing_plus)}")
emit(f"候选 - 行中设计未声明 = {len(extra_minus)}；设计 - 行候选缺失 = {len(missing_minus)}")
emit(f"copy_post_except_evidence 调用点 = {len(CALLS)}；"
     f"其中传 pre_freshness_snapshot = "
     f"{sum(1 for _,_,_,kws,_ in CALLS if any(k=='pre_freshness_snapshot' for k,_ in kws))}")
emit(f"退出码判据区间读到 freshness_* 命中 = {len(HITS)}；"
     f"判据区间内 'freshness_' 字面量行 = {len(lit_hits)}")
emit(f"重建验证（设计 §4 逐字套回母本 == 候选）= {RECON_EQ}"
     f"；母本窗口逐字核对错误数 = {len(rebuild_errors)}")
emit("")
emit("判据区间口径说明：except_set_diff 函数体 + note_cleanup_failure/merge_cleanup_code"
     " 定义体 + 17 个 note_cleanup_failure 调用语句 + finalize_trip 内 _except_diff/"
     "_ctrl_post/_t0_t1_sha_diff 函数体 + 含 CLEANUP_FAILURES/merge_cleanup_code 的 28 行；"
     "另实读候选 :7421-7444 最终退出码收口段（main()/merge_cleanup_code/_write_final_records/"
     "SystemExit(written)），该段无 freshness_* 。")
emit("")
if unattributed or extra_plus or extra_minus or missing_plus or missing_minus or HITS or lit_hits:
    emit("★★ 存在需点名项：")
    for (n, tag, mr, cr, plus, minus, range_hit, note) in unattributed:
        emit(f"   ★ 无法归属 block#{n:02d} 母本 {mr[0]}-{mr[1]} / 候选 {cr[0]}-{cr[1]} {note}")
        for x in minus:
            emit(f"        - {x!r}")
        for x in plus:
            emit(f"        + {x!r}")
    for x in extra_plus:
        emit(f"   ★ 夹带（候选 + 行设计未声明）: {x!r}")
    for x in extra_minus:
        emit(f"   ★ 夹带（候选 - 行设计未声明）: {x!r}")
else:
    emit("（逐块均可归属；无夹带；退出码判据未读 freshness_*）")
emit("")
emit("END")
