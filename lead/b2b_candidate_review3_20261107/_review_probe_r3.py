# -*- coding: utf-8 -*-
"""R3 语义复审探针（lead/b2b_candidate_review3_20261107/_review_probe_r3.py）

复审对象：lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py（只读）
对照设计：lead/b2b_design_20261106/B2B_DESIGN.md + STATE_MATRIX.json（只读）

★ 铁律：零真机 / 零采样代码 / 不 import qc151_trip 母本。
★ 候选加载方式：importlib.util.spec_from_file_location + unittest.mock.patch 拦截
  SetProcessDPIAware（与 tests/test_candidate.py:40-57 同法，任务书许可的
  「importlib + DPI patch」路径；模块名独立，绝不触发 __main__ 入口）。
★ 本探针除自身 stdout 外不写任何文件（含 %TEMP%）。
输出：全部打印到 stdout（由调用方重定向到 _review_probe_r3_out.txt）。
"""
import ast
import difflib
import hashlib
import importlib.util
import json
import re
import unittest.mock as mock
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DIFF = ROOT / "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
DESIGN = ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
N1BIND = ROOT / "lead/b2b_n1_binding_20261107/N1_BINDING.md"
MATRIX_JSON = ROOT / "lead/b2b_design_20261106/STATE_MATRIX.json"

PASS_OK = []
PASS_BAD = []


def check(label, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    (PASS_OK if cond else PASS_BAD).append(label)
    print(f"[{tag}] {label}" + (f" | {detail}" if detail else ""))


# ============================================================ [1] 五件指纹
print("=" * 78)
print("== [1] 五件指纹实算（hashlib，本探针实跑） ==")


def fp(p: Path):
    d = p.read_bytes()
    return hashlib.sha256(d).hexdigest(), len(d), d.count(b"\n"), d.count(b"\r")


f_mother = fp(MOTHER)
f_cand = fp(CAND)
f_diff = fp(DIFF)
f_design = fp(DESIGN)
f_n1 = fp(N1BIND)
for name, f, path in (("母本", f_mother, MOTHER), ("候选", f_cand, CAND),
                      ("候选diff", f_diff, DIFF), ("设计", f_design, DESIGN),
                      ("N1绑定", f_n1, N1BIND)):
    print(f"{name}: sha256={f[0]} bytes={f[1]} LF={f[2]} CR={f[3]} path={path}")

check("母本指纹 == 绑定记录 517889c6.../399508",
      f_mother[0] == "517889c68f037ab63f9c38300e627d34457b7be9fab0362e425783c7ec5ba636"
      and f_mother[1] == 399508)
check("候选指纹 == 绑定记录 ca23c116.../412759",
      f_cand[0] == "ca23c116064b25a61d6072f93458673990b0bf766b2430524f1980addd3c76d2"
      and f_cand[1] == 412759)
check("N-1 已解除：候选 CR=0（纯 LF）", f_cand[3] == 0, f"CR={f_cand[3]}")
check("N-1 已解除：母本 CR=0（纯 LF）", f_mother[3] == 0, f"CR={f_mother[3]}")
check("CANDIDATE_LF.diff 指纹 == 72b10802.../18454",
      f_diff[0] == "72b108021637cf7d225a9b109a542ec10c934abb1a8e40b8850a82c6bea9cdb9"
      and f_diff[1] == 18454)
check("设计指纹 == 565771d8.../66735",
      f_design[0] == "565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf"
      and f_design[1] == 66735)

mother_text = MOTHER.read_text(encoding="utf-8")
cand_text = CAND.read_text(encoding="utf-8")
mother_lines = mother_text.splitlines()
cand_lines = cand_text.splitlines()
print(f"mother splitlines={len(mother_lines)} cand splitlines={len(cand_lines)}")

# ============================================================ [2] AST 扫描
print("=" * 78)
print("== [2] AST 全量扫描（ast.parse，不加载模块） ==")

cand_ast = ast.parse(cand_text, filename=str(CAND))
check("候选 ast.parse 成功", True)

top_funcs = {n.name: n for n in cand_ast.body if isinstance(n, ast.FunctionDef)}


def call_targets(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                out.append((node, fn.id))
            elif isinstance(fn, ast.Attribute):
                out.append((node, fn.attr))
    return out


calls = call_targets(cand_ast)

# --- 2a. copy_post_except_evidence 所有调用点
print("-- 2a. copy_post_except_evidence 调用点 --")
cpe_calls = [(n, q) for (n, q) in calls if q == "copy_post_except_evidence"]
print(f"调用点个数 = {len(cpe_calls)}")
for n, _ in cpe_calls:
    pos = [ast.unparse(a) for a in n.args]
    kws = [(k.arg, ast.unparse(k.value)) for k in n.keywords]
    print(f"  调用行={n.lineno} 位置实参={pos} 关键字实参={kws}")
check("copy_post_except_evidence 调用点恰 1 处", len(cpe_calls) == 1)
if cpe_calls:
    n0 = cpe_calls[0][0]
    check("唯一调用点关键字传参 pre_freshness_snapshot=pre_freshness_snapshot",
          any(k.arg == "pre_freshness_snapshot" and isinstance(k.value, ast.Name)
              and k.value.id == "pre_freshness_snapshot" for k in n0.keywords))

cpe_def = top_funcs.get("copy_post_except_evidence")
sig_args = [a.arg for a in cpe_def.args.args]
print(f"copy_post_except_evidence def @:{cpe_def.lineno} 参数={sig_args} "
      f"默认值个数={len(cpe_def.args.defaults)}")
check("def 末参 = pre_freshness_snapshot 且默认 None",
      sig_args[-1] == "pre_freshness_snapshot" and len(cpe_def.args.defaults) >= 1
      and cpe_def.args.defaults[-1].value is None)

# --- 2b. finalize_trip 签名 / 调用点 / 绑定模拟
print("-- 2b. finalize_trip 签名 / 调用点 / 静态绑定模拟 --")
ft_def = top_funcs.get("finalize_trip")
assert ft_def is not None
ft_args = [a.arg for a in ft_def.args.args]
ft_defaults = ft_def.args.defaults
print(f"finalize_trip def @:{ft_def.lineno} 共 {len(ft_args)} 参={ft_args}")
print(f"默认值个数={len(ft_defaults)} 末参={ft_args[-1]}")
check("finalize_trip 末形参 = pre_freshness_snapshot 带默认",
      ft_args[-1] == "pre_freshness_snapshot" and len(ft_defaults) >= 1
      and ft_defaults[-1].value is None)

ft_calls = [(n, q) for (n, q) in calls if q == "finalize_trip"]
print(f"finalize_trip 调用点个数 = {len(ft_calls)}")


def simulate_bind(defnode, callnode):
    """静态绑定模拟（按 CPython 传参规则），返回 None=兼容 或 TypeError 文本。"""
    args = [a.arg for a in defnode.args.args]
    ndef = len(defnode.args.defaults)
    nreq = len(args) - ndef
    pos, kws = callnode.args, callnode.keywords
    if len(pos) > len(args):
        return f"TypeError: too many positional ({len(pos)} > {len(args)})"
    if any(k.arg is None for k in kws):
        return "TypeError: **kwargs unsupported in simulation"
    bound = {}
    for i in range(len(pos)):
        bound[args[i]] = "positional"
    for k in kws:
        if k.arg not in args:
            return f"TypeError: unexpected keyword '{k.arg}'"
        if k.arg in bound:
            return f"TypeError: duplicate '{k.arg}'"
        bound[k.arg] = "kw"
    missing = [a for a in args[:nreq] if a not in bound]
    if missing:
        return f"TypeError: missing required {missing}"
    return None


for n, _ in ft_calls:
    pos = [ast.unparse(a) for a in n.args]
    kws = [k.arg for k in n.keywords]
    r = simulate_bind(ft_def, n)
    print(f"  调用行={n.lineno} 位置实参({len(pos)}) 关键字({len(kws)})={kws} "
          f"=> {'OK（不抛 TypeError）' if r is None else r}")
check("finalize_trip 所有调用点兼容新形参（静态绑定模拟）",
      all(simulate_bind(ft_def, n) is None for n, _ in ft_calls))
check("finalize_trip 调用点含 pre_freshness_snapshot 关键字",
      any(any(k.arg == "pre_freshness_snapshot" for k in n.keywords)
          for n, _ in ft_calls))

# --- 2c. F/E 分离：退出码判据 AST 扫描
print("-- 2c. 退出码判据是否读 freshness_* --")
crit_nodes = [node for node in ast.walk(cand_ast)
              if isinstance(node, ast.If) and "no_new_exception" in ast.unparse(node.test)]
print(f"含 no_new_exception 的 If 判据节点 = {len(crit_nodes)}")
crit_lines = []
for node in crit_nodes:
    seg = "\n".join(cand_text.splitlines()[node.lineno - 1:node.end_lineno])
    crit_lines.append((node.lineno, seg))
    print(f"  判据 If @:{node.lineno}-{node.end_lineno} "
          f"含'freshness'(ci)={'freshness' in seg.lower()}")
check("退出码判据块（no_new_exception If 整块）零 freshness_*",
      len(crit_nodes) >= 1 and all("freshness" not in s.lower() for _, s in crit_lines))
if crit_nodes:
    lo, hi = crit_nodes[0].lineno, crit_nodes[0].end_lineno
    cand_block = "\n".join(cand_lines[lo - 1:hi])
    mother_block = "\n".join(mother_lines[5984:5990])
    print(f"候选判据块 :{lo}-{hi} vs 母本 :5985-5990 逐字相等 = {cand_block == mother_block}")
    check("E 判据块逐字未改（候选==母本 :5985-5990）", cand_block == mother_block)

EXIT_FUNCS = ["note_cleanup_failure", "merge_cleanup_code", "except_set_diff",
              "run_guarded_steps", "_main_wrapper"]
for fname in EXIT_FUNCS:
    node = top_funcs.get(fname)
    if node is None:
        check(f"退出码相关函数 {fname} 存在", False, "未找到")
        continue
    seg = "\n".join(cand_text.splitlines()[node.lineno - 1:node.end_lineno])
    cnt = len(re.findall(r"freshness", seg, re.IGNORECASE))
    print(f"  {fname} @:{node.lineno}-{node.end_lineno} 含'freshness'(ci)次数={cnt}")
    check(f"退出码相关函数 {fname} 体零 freshness", cnt == 0)

main_node = top_funcs.get("main")
if main_node:
    seg = "\n".join(cand_text.splitlines()[main_node.lineno - 1:main_node.end_lineno])
    hits = [(main_node.lineno + i, ln.strip()[:96])
            for i, ln in enumerate(seg.splitlines()) if "freshness" in ln.lower()]
    print(f"  main @:{main_node.lineno} 含'freshness'(ci)行数={len(hits)}（应全为 H07/H08/H09 数据行）")
    for ln, txt in hits:
        print(f"    :{ln} {txt}")

# --- 2d. _emit_f 内 rec.add 计数（设计 B2B_DESIGN.md:83 = 固定 7 个，全 FRESHNESS_GROUP）
print("-- 2d. _emit_f rec.add 计数 --")
emit_f = None
for node in ast.walk(cpe_def):
    if isinstance(node, ast.FunctionDef) and node.name == "_emit_f":
        emit_f = node
assert emit_f is not None
rec_adds = [n for n in ast.walk(emit_f)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "add"]
print(f"_emit_f @:{emit_f.lineno}-{emit_f.end_lineno} 内 rec.add 调用数 = {len(rec_adds)}")
emit_keys = []
for n in rec_adds:
    g = ast.unparse(n.args[0]) if n.args else "?"
    k = ast.unparse(n.args[1]) if len(n.args) > 1 else "?"
    emit_keys.append((g, k, n.lineno))
    print(f"  :{n.lineno} group={g} key={k}")
check("_emit_f 固定 7 个 rec.add（设计 :83）", len(rec_adds) == 7, f"实际={len(rec_adds)}")
check("_emit_f 7 个全部写 FRESHNESS_GROUP",
      all(g == "FRESHNESS_GROUP" for g, _, _ in emit_keys))
pref = [k for g, k, _ in emit_keys if "FRESHNESS_KEY_PREFIX" in k]
indep = [k for g, k, _ in emit_keys if "FRESHNESS_KEY_PREFIX" not in k]
print(f"  带前缀键({len(pref)})={pref}")
print(f"  独立名键({len(indep)})={indep}")
pref_names = sorted(x.rsplit("+ ", 1)[-1].strip("'\"") for x in pref)
indep_names = sorted(x.strip("'\"") for x in indep)
check("4 键带前缀 + 3 键同 group 独立名（设计 §5 精确口径）",
      len(pref) == 4 and len(indep) == 3
      and pref_names == ["confidence", "is_new", "note", "verdict"]
      and indep_names == ["captured_at_iso", "pre_snapshot_state",
                          "usable_as_crash_evidence"])

all_fresh_adds = []
for node in ast.walk(cand_ast):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "add" and node.args \
            and isinstance(node.args[0], ast.Name) and node.args[0].id == "FRESHNESS_GROUP":
        all_fresh_adds.append((node.lineno,
                               ast.unparse(node.args[1]) if len(node.args) > 1 else "?"))
print(f"模块全量 rec.add(FRESHNESS_GROUP, ...) 次数 = {len(all_fresh_adds)}")
for ln, k in all_fresh_adds:
    print(f"  :{ln} key={k}")
check("全文件 FRESHNESS_GROUP rec.add = 8（7 _emit_f + 1 H08）",
      len(all_fresh_adds) == 8 and any("captured_at_iso_pre" in k for _, k in all_fresh_adds))

# ============================================================ [3] difflib 全量 diff + 逐 hunk 归因
print("=" * 78)
print("== [3] difflib 全量 diff（母本 vs 候选）+ 逐 hunk 归因 H1–H9 ==")

sm = difflib.SequenceMatcher(None, mother_lines, cand_lines, autojunk=False)
changed = [op for op in sm.get_opcodes() if op[0] != "equal"]
plus_lines, minus_lines = [], []
for tag, i1, i2, j1, j2 in changed:
    if tag in ("replace", "delete"):
        minus_lines.extend(mother_lines[i1:i2])
    if tag in ("replace", "insert"):
        plus_lines.extend(cand_lines[j1:j2])
print(f"变更 opcode 块数 = {len(changed)}  +行 = {len(plus_lines)}  -行 = {len(minus_lines)}")

design_lines = DESIGN.read_text(encoding="utf-8").splitlines()
blocks, cur, in_diff = [], None, False
for ln in design_lines:
    if ln.strip() == "```diff":
        in_diff, cur = True, []
        continue
    if in_diff and ln.strip() == "```":
        blocks.append(cur)
        in_diff = False
        continue
    if in_diff:
        cur.append(ln)
print(f"设计稿 ```diff 块数 = {len(blocks)}")

d_plus, d_minus, hunk_hdrs = [], [], []
for b in blocks:
    for ln in b:
        if ln.startswith("@@"):
            hunk_hdrs.append(ln)
        elif ln.startswith("+"):
            d_plus.append(ln[1:])
        elif ln.startswith("-"):
            d_minus.append(ln[1:])
print(f"设计 hunk 头数 = {len(hunk_hdrs)}  设计+行 = {len(d_plus)}  设计-行 = {len(d_minus)}")
for h in hunk_hdrs:
    print(f"  {h}")

import collections
check("候选+ 行多重集 == 设计+ 行多重集",
      collections.Counter(plus_lines) == collections.Counter(d_plus),
      f"候选独有={sum((collections.Counter(plus_lines) - collections.Counter(d_plus)).values())} "
      f"设计独有={sum((collections.Counter(d_plus) - collections.Counter(plus_lines)).values())}")
check("候选- 行多重集 == 设计- 行多重集",
      collections.Counter(minus_lines) == collections.Counter(d_minus))
check("+行=255 / -行=13（设计 §4 口径）", len(plus_lines) == 255 and len(minus_lines) == 13)

H_RANGES = []
for h in hunk_hdrs:
    m = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", h)
    a, b_, c, d_ = map(int, m.groups())
    H_RANGES.append((a, a + b_ - 1, h))
print("由 hunk 头解析的母本 '-侧' 区间：")
for lo, hi, h in H_RANGES:
    print(f"  母本 {lo}-{hi}  <- {h}")

print("-- 逐变更块归因 --")
unattributed = []
for tag, i1, i2, j1, j2 in changed:
    mlo, mhi = i1 + 1, max(i2, i1)  # insert 时 i2==i1
    hit = None
    for lo, hi, h in H_RANGES:
        if mlo >= lo - 2 and mhi <= hi + 2:
            hit = f"⊆H区间(母本{lo}-{hi})"
            break
    if hit is None:
        unattributed.append((tag, mlo, mhi, j1 + 1, j2))
    print(f"  {tag:8s} 母本:{mlo}-{mhi} 候选:{j1 + 1}-{j2} => {hit or '★ 未归入任何 H 区间'}")
check("所有变更块均归入 H1–H9 区间（行文本口径）", len(unattributed) == 0,
      f"未归入块数={len(unattributed)}")

mother_ke = mother_text.splitlines(keepends=True)
cand_ke = cand_text.splitlines(keepends=True)
sm2 = difflib.SequenceMatcher(None, mother_ke, cand_ke, autojunk=False)
ch2 = [op for op in sm2.get_opcodes() if op[0] != "equal"]
plus2 = sum(j2 - j1 for t, _, _, j1, j2 in ch2 if t in ("replace", "insert"))
minus2 = sum(i2 - i1 for t, i1, i2, _, _ in ch2 if t in ("replace", "delete"))
print(f"字节级 keepends：变更块={len(ch2)} +行={plus2} -行={minus2}")
check("字节级口径与行文本口径一致（无行尾噪声，N-1 不复发）",
      len(ch2) == len(changed) and plus2 == 255 and minus2 == 13)


def apply_hunks(mother_lines_, hunks_):
    """标准 unified diff 应用（上下文/-行逐行断言母本原文）。"""
    out, pos = [], 0
    for body in hunks_:
        m = re.match(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@", body[0])
        assert m, body[0]
        start = int(m.group(1)) - 1
        out.extend(mother_lines_[pos:start])
        pos = start
        consumed = 0
        for ln in body[1:]:
            if ln.startswith(" ") or ln == "":
                assert mother_lines_[pos] == (ln[1:] if ln else ""), \
                    f"上下文不符 @母本:{pos + 1}: {mother_lines_[pos]!r} vs {ln!r}"
                out.append(mother_lines_[pos])
                pos += 1
                consumed += 1
            elif ln.startswith("-"):
                assert mother_lines_[pos] == ln[1:], \
                    f"-侧不符 @母本:{pos + 1}: {mother_lines_[pos]!r} vs {ln[1:]!r}"
                pos += 1
                consumed += 1
            elif ln.startswith("+"):
                out.append(ln[1:])
            elif ln.startswith("\\"):
                pass
            else:
                raise AssertionError(f"未知 diff 行: {ln!r}")
        assert consumed == int(m.group(2)), \
            f"hunk {body[0]} 声称 -{m.group(2)} 行，实际消费 {consumed}"
    out.extend(mother_lines_[pos:])
    return out


bodies = [[ln for ln in b if not ln.startswith("\\")] for b in blocks]
recon_text = "\n".join(apply_hunks(mother_lines, bodies)) + "\n"
check("决定性①：母本 + 设计 §4 九 hunk 重建 == 候选（逐字节）",
      recon_text == cand_text,
      f"重建sha16={hashlib.sha256(recon_text.encode('utf-8')).hexdigest()[:16]} "
      f"候选sha16={f_cand[0][:16]}")

diff_lines_all = DIFF.read_text(encoding="utf-8").splitlines()
hdr_idx = [i for i, ln in enumerate(diff_lines_all) if ln.startswith("@@ ")]
check("CANDIDATE_LF.diff @@ 头恰 9 个", len(hdr_idx) == 9, f"实际={len(hdr_idx)}")
diff_hunks = []
for k, i in enumerate(hdr_idx):
    end = hdr_idx[k + 1] if k + 1 < len(hdr_idx) else len(diff_lines_all)
    diff_hunks.append(diff_lines_all[i:end])
try:
    recon2 = "\n".join(apply_hunks(mother_lines, diff_hunks)) + "\n"
    check("决定性②：母本 + CANDIDATE_LF.diff == 候选（逐字节）", recon2 == cand_text)
except AssertionError as exc:
    check("决定性②：母本 + CANDIDATE_LF.diff == 候选（逐字节）", False, str(exc))

# ============================================================ [4] 语义验证（importlib + DPI patch 隔离加载）
print("=" * 78)
print("== [4] 语义验证（importlib 隔离加载 + DPI patch，同 tests/test_candidate.py:40-57） ==")

with mock.patch("ctypes.windll.user32.SetProcessDPIAware", return_value=1):
    spec = importlib.util.spec_from_file_location("qc151_candidate_mod_r3", str(CAND))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
NS = vars(mod)
print("模块加载成功（模块名 qc151_candidate_mod_r3，未触发 __main__ 入口）")
cls = NS["classify_except_freshness"]
mks = NS["make_pre_freshness_snapshot"]
cpe = NS["copy_post_except_evidence"]
check("FRESHNESS_SNAPSHOT_STATES = (unknown, absent_confirmed, present, error)",
      NS["FRESHNESS_SNAPSHOT_STATES"] == ("unknown", "absent_confirmed", "present", "error"))
check("FRESHNESS_VERDICTS 9 值", len(NS["FRESHNESS_VERDICTS"]) == 9)
check("FRESHNESS_CONFIDENCES = (high, medium, low, none)",
      NS["FRESHNESS_CONFIDENCES"] == ("high", "medium", "low", "none"))

# --- 4a. 14 行状态矩阵
print("-- 4a. STATE_MATRIX.json 14 行逐行比对 --")
rows = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
check("STATE_MATRIX.json 共 14 行", len(rows) == 14, f"实际={len(rows)}")

POST_PRESENT = {"exists": True, "size": 10, "sha256": "a" * 64, "mtime_post": 100.0}
POST_PRESENT_NO_SHA = {"exists": True, "size": 10, "mtime_post": 100.0}
POST_GONE = {"exists": False}
FIX = {
    1: (None, POST_PRESENT),
    2: ({"state": "unknown"}, POST_GONE),
    3: ({"state": "error", "error": "boom"}, POST_PRESENT),
    4: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0},
        dict(POST_PRESENT, read_error="boom")),
    5: ({"state": "absent_confirmed", "exists": False}, POST_PRESENT),
    6: ({"state": "absent_confirmed", "exists": False}, POST_GONE),
    7: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0},
        dict(POST_PRESENT, mtime_post=100.0)),
    8: ({"state": "present", "sha256": "a" * 64, "mtime_pre": None}, POST_PRESENT),
    9: ({"state": "present", "sha256": "b" * 64, "mtime_pre": 100.0}, POST_PRESENT),
    10: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0},
         dict(POST_PRESENT, mtime_post=200.0)),
    11: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0},
         dict(POST_PRESENT, mtime_post=50.0)),
    12: ({"state": "present", "mtime_pre": 100.0}, POST_PRESENT),
    13: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0}, POST_PRESENT_NO_SHA),
    14: ({"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0}, POST_GONE),
}
IS_NEW_EXPECT = {1: None, 2: None, 3: None, 4: None, 5: True, 6: False, 7: False,
                 8: False, 9: True, 10: True, 11: True, 12: None, 13: None, 14: None}
matrix_ok = True
for idx, r in enumerate(rows, 1):
    pre, post = FIX[idx]
    out = cls(pre, post)
    ok = (out["verdict"] == r["verdict"] and out["confidence"] == r["confidence"]
          and out["usable_as_crash_evidence"] == r["usableAsCrashEvidence"]
          and out["is_new"] == IS_NEW_EXPECT[idx])
    matrix_ok = matrix_ok and ok
    print(f"  行{idx:2d} {r['state']:<22} -> verdict={out['verdict']:<22} "
          f"conf={out['confidence']:<7} is_new={out['is_new']!s:<5} "
          f"crash_ev={out['usable_as_crash_evidence']} match={ok}")
check("14/14 状态矩阵逐行 match（verdict+conf+crash_ev+is_new）", matrix_ok)

# --- 4b. 三态可分（裁定一口径）
print("-- 4b. 三态可分（状态值层面） --")
o_unknown = cls(None, POST_PRESENT)
o_absent = cls({"state": "absent_confirmed", "exists": False}, POST_PRESENT)
o_present = cls({"state": "present", "sha256": "b" * 64, "mtime_pre": 100.0}, POST_PRESENT)
vs = (o_unknown["verdict"], o_absent["verdict"], o_present["verdict"])
print(f"  unknown          -> {o_unknown['verdict']}/{o_unknown['confidence']}")
print(f"  absent_confirmed -> {o_absent['verdict']}/{o_absent['confidence']}")
print(f"  present          -> {o_present['verdict']}/{o_present['confidence']}")
check("三态 verdict 两两不等（状态值层面可分）", len(set(vs)) == 3, f"{vs}")
check("裁定一验收点：absent_confirmed 与 unknown 输出不同",
      dict(o_absent) != dict(o_unknown))
check("原始输入 None/{}/{'exists':False} 归一 = 设计意图（不阻断）",
      all(cls(p, POST_PRESENT)["verdict"] == "unknown"
          for p in (None, {}, {"exists": False})))

# --- 4c. unknown 恒 none 穷举
print("-- 4c. unknown 恒 none 穷举 --")
PRE_VARIANTS = [None, {}, {"exists": False}, {"state": "zzz"}, {"state": None},
                {"state": "unknown"}, {"state": "unknown", "exists": False}, 123, "x"]
POST_VARIANTS = [{}, POST_GONE, POST_PRESENT, dict(POST_PRESENT, read_error="boom")]
leak, combo_n = 0, 0
for p_ in PRE_VARIANTS:
    for q_ in POST_VARIANTS:
        o_ = cls(p_, q_)
        combo_n += 1
        if o_["verdict"] == "unknown" and o_["confidence"] != "none":
            leak += 1
        if o_["usable_as_crash_evidence"] is not False:
            leak += 100
print(f"  组合数={combo_n} 泄漏(unknown+非none 或 crash_ev≠False)={leak}")
check("unknown 恒 none 且 crash_ev 恒 False（穷举 36 组零泄漏）",
      leak == 0 and combo_n == 36)

# --- 4d. make_pre_freshness_snapshot（只读输入：候选自身文件 / 不存在路径）
print("-- 4d. make_pre_freshness_snapshot（纯只读输入） --")
sn_present = mks(CAND)
sn_absent = mks(ROOT / "definitely_nonexistent_for_r3_probe.txt")
print(f"  候选自身文件 -> state={sn_present['state']} exists={sn_present['exists']} "
      f"sha==真实指纹={sn_present['sha256'] == f_cand[0]} "
      f"epoch={'set' if sn_present['captured_at_epoch'] else 'None'} "
      f"iso={'set' if sn_present['captured_at_iso'] else 'None'}")
print(f"  不存在路径 -> state={sn_absent['state']} exists={sn_absent['exists']}")
check("snapshot: 在场文件 -> present + sha 与实算一致 + 双时刻齐",
      sn_present["state"] == "present" and sn_present["sha256"] == f_cand[0]
      and bool(sn_present["captured_at_epoch"]) and bool(sn_present["captured_at_iso"]))
check("snapshot: 不存在 -> absent_confirmed（非 unknown）",
      sn_absent["state"] == "absent_confirmed" and sn_absent["exists"] is False)

# ============================================================ [5] 三路径落盘（内存 stub，零磁盘写）
print("=" * 78)
print("== [5] copy_post_except_evidence 三路径落盘（全内存 stub，零磁盘写） ==")


class FakeStat:
    def __init__(self, size, mtime):
        self.st_size = size
        self.st_mtime = mtime


class FakeFile:
    def __init__(self, name, data=b"", mtime=1700000000.0, exists=True,
                 fail_read=False, fail_write=False):
        self.name, self.data, self.mtime = name, data, mtime
        self._exists, self.fail_read, self.fail_write = exists, fail_read, fail_write

    def exists(self):
        return self._exists

    def read_bytes(self):
        if self.fail_read:
            raise OSError("boom-read")
        return self.data

    def stat(self):
        return FakeStat(len(self.data), self.mtime)

    def write_bytes(self, b):
        if self.fail_write:
            raise OSError("boom-write")
        self.data = b

    def write_text(self, t, encoding="utf-8"):
        self.data = t.encode(encoding)

    def __str__(self):
        return self.name

    def __fspath__(self):
        return self.name


class FakeDir:
    def __init__(self, name, files=None):
        self.name = name
        self.files = dict(files or {})

    def __truediv__(self, key):
        if key not in self.files:
            self.files[key] = FakeFile(f"{self.name}/{key}", exists=False)
        return self.files[key]

    def __str__(self):
        return self.name

    def __fspath__(self):
        return self.name


class RecStub:
    def __init__(self):
        self.rows = []

    def add(self, group, key, value, source, note=""):
        self.rows.append({"group": group, "key": key, "value": value,
                          "source": source, "note": note})


F_KEYS = ["freshness_verdict", "freshness_confidence", "freshness_is_new",
          "freshness_note", "pre_snapshot_state", "usable_as_crash_evidence",
          "captured_at_iso"]
INFO_12 = ["source", "evidence_path", "size", "sha256", "note", "mtime_post",
           "freshness_verdict", "freshness_confidence", "freshness_note",
           "captured_at_iso", "pre_snapshot_state", "pre_freshness_snapshot"]


def run_path(pre_snap, carrier, out):
    rec = RecStub()
    raised = None
    try:
        cpe(rec, carrier, out, pre_freshness_snapshot=pre_snap)
    except Exception as exc:
        raised = exc
    return rec, raised


preA = {"state": "present", "sha256": "a" * 64, "mtime_pre": 100.0,
        "captured_at_iso": "2030-01-01T00:00:00+00:00"}

# ★ stub 说明：母本基础设施 sha256_file（母本 :416-422，非 H1–H9 改动）用内建 open()
#   读真实磁盘；内存 FakeFile 无磁盘实体。按 R2 先例（_r2_paths_out.txt，修正
#   sha256_file stub 后得干净结果），三路径合成期以等价 stub（read_bytes 摘要）替换之，
#   仅影响母本既有基础设施，不影响候选 H1–H9 代码路径。
NS["sha256_file"] = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

carrier1 = FakeDir("carrier", {"except.txt": FakeFile("carrier/except.txt", data=b"XYZ")})
rec1, raise1 = run_path(preA, carrier1, FakeDir("out"))
f1 = [r for r in rec1.rows if r["group"] == "FRESHNESS"]
ec1 = [r for r in rec1.rows if r["group"] == "EXCEPT" and r["key"] == "evidence_copy"]
e1 = [r for r in rec1.rows if r["group"] == "ERROR"]
print(f"正常: FRESHNESS行={len(f1)} 键序={[r['key'] for r in f1]}")
print(f"      evidence_copy行={len(ec1)} value为dict={isinstance(ec1[0]['value'], dict) if ec1 else None}")
print(f"      12键={sorted(ec1[0]['value'].keys()) == sorted(INFO_12) if ec1 and isinstance(ec1[0]['value'], dict) else False}")
print(f"      ERROR行={len(e1)} raise={raise1!r}")
check("正常路径: 7 个 F 字段落盘", len(f1) == 7 and [r["key"] for r in f1] == F_KEYS)
check("正常路径: EXCEPT.evidence_copy 为 12 键 dict",
      len(ec1) == 1 and isinstance(ec1[0]["value"], dict)
      and sorted(ec1[0]["value"].keys()) == sorted(INFO_12))
check("正常路径: 无 ERROR 行、不抛", len(e1) == 0 and raise1 is None)

carrier2 = FakeDir("carrier2")
rec2, raise2 = run_path(preA, carrier2, FakeDir("out2"))
f2 = [r for r in rec2.rows if r["group"] == "FRESHNESS"]
ec2 = [r for r in rec2.rows if r["group"] == "EXCEPT" and r["key"] == "evidence_copy"]
e2 = [r for r in rec2.rows if r["group"] == "ERROR"]
stages2 = [r["note"].split("；")[0] for r in f2 if r["key"] == "freshness_verdict"]
print(f"src_missing: FRESHNESS行={len(f2)} evidence_copy行={len(ec2)} "
      f"value={ec2[0]['value'] if ec2 else None} ERROR行={len(e2)} stage={stages2} raise={raise2!r}")
check("src_missing: 7 个 F 字段落盘（stage=src_missing）",
      len(f2) == 7 and stages2 == ["stage=src_missing"])
check("src_missing: evidence_copy 行在且 value=None（设计 :434-435 / :605）",
      len(ec2) == 1 and ec2[0]["value"] is None)
check("src_missing: 无 ERROR 行、不抛", len(e2) == 0 and raise2 is None)

carrier3 = FakeDir("carrier3", {"except.txt": FakeFile("carrier3/except.txt",
                                                       data=b"Q", fail_read=True)})
rec3, raise3 = run_path(preA, carrier3, FakeDir("out3"))
f3 = [r for r in rec3.rows if r["group"] == "FRESHNESS"]
ec3 = [r for r in rec3.rows if r["group"] == "EXCEPT" and r["key"] == "evidence_copy"]
e3 = [r for r in rec3.rows if r["group"] == "ERROR"]
stages3 = [r["note"].split("；")[0] for r in f3 if r["key"] == "freshness_verdict"]
verdict3 = [r["value"] for r in f3 if r["key"] == "freshness_verdict"]
conf3 = [r["value"] for r in f3 if r["key"] == "freshness_confidence"]
print(f"copy_failed: FRESHNESS行={len(f3)} evidence_copy行={len(ec3)} ERROR行={len(e3)} "
      f"ERROR键={[r['key'] for r in e3]} stage={stages3} verdict={verdict3} conf={conf3} "
      f"raise={raise3!r}")
check("copy_failed: 7 F 落盘（stage=copy_failed，verdict=post_read_error/none）",
      len(f3) == 7 and stages3 == ["stage=copy_failed"] and verdict3 == ["post_read_error"]
      and conf3 == ["none"])
check("copy_failed: 3 条 ERROR 留痕（failed/stage/traceback）",
      len(e3) == 3 and [r["key"] for r in e3] ==
      ["freshness_copy_failed", "freshness_copy_stage", "freshness_copy_traceback"])
check("copy_failed: 无 evidence_copy 行 + 原异常重抛（设计 :434-435，裁定二不阻断）",
      len(ec3) == 0 and isinstance(raise3, OSError))

sevenF3 = [len(f1) == 7, len(f2) == 7, len(f3) == 7]


def _is_12key(ec):
    return bool(ec) and isinstance(ec[0]["value"], dict) \
        and sorted(ec[0]["value"].keys()) == sorted(INFO_12)


info2 = [_is_12key(ec1), _is_12key(ec2), _is_12key(ec3)]
ec_cnt3 = [len(ec1), len(ec2), len(ec3)]
print(f"汇总: 7F三路径={sevenF3}  info12键dict[正常,src_missing,copy_failed]={info2}  "
      f"ec行存在[正常,src_missing,copy_failed]={[bool(x) for x in (ec1, ec2, ec3)]}  ec次数={ec_cnt3}")
check("7F 三路径全落盘 = [True,True,True]", sevenF3 == [True, True, True])
check("12键info value [正常,src_missing,copy_failed] = [True,False,False]（裁定二口径）",
      info2 == [True, False, False])
check("evidence_copy 行落点 [正常,src_missing,copy_failed] = [有,有,无]（裁定二/设计 :434-435）",
      [bool(ec1), bool(ec2), bool(ec3)] == [True, True, False] and ec_cnt3 == [1, 1, 0])

# ============================================================ [6] 汇总
print("=" * 78)
print(f"== [6] 汇总: PASS={len(PASS_OK)} FAIL={len(PASS_BAD)} ==")
if PASS_BAD:
    print("FAIL 清单：")
    for x in PASS_BAD:
        print(f"  - {x}")
print("PROBE_DONE")
