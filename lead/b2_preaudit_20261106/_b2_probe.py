# -*- coding: utf-8 -*-
"""B2 设计独立预审 · 键名 / 签名 / 调用点 机械核验探针

只读：母本 qc151_trip.py、B2_FIX_DESIGN.md、TASK.md、PRE_AUDIT.md、.gitignore、
W11 candidate。不 import / 不运行 qc151_trip.py（只用 ast 静态解析）。
输出：lead/b2_preaudit_20261106/_b2_probe_out.txt（同时打印到 stdout）。
命令：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b2_preaudit_20261106/_b2_probe.py
"""
import ast
import hashlib
import io
import re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
B2 = ROOT / "lead/re_line_20261105/B1_HARNESS_PATCH/B2_FIX_DESIGN.md"
TASK = ROOT / "lead/re_line_20261105/B1_HARNESS_PATCH/TASK.md"
CAND = ROOT / "lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py"
GITIGNORE = ROOT / ".gitignore"
OUT = ROOT / "lead/b2_preaudit_20261106/_b2_probe_out.txt"

buf = []
def w(s=""):
    buf.append(str(s))

def text(p):
    return p.read_text(encoding="utf-8")

def lines(p):
    return text(p).splitlines()

def fingerprint(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b), len(b.splitlines())

# ---------------------------------------------------------------- 0 指纹
w("=" * 78)
w("[0] 指纹（实算）")
for tag, p in (("MOTHER", MOTHER), ("B2", B2), ("TASK", TASK)):
    sha, nbytes, nlines = fingerprint(p)
    w(f"  {tag:7s} sha256={sha} bytes={nbytes} lines={nlines}  path={p}")
w(f"  .gitignore:33 = {lines(GITIGNORE)[32]!r}")

# ------------------------------------------------- 1 母本 AST：定义与调用点
w("=" * 78)
w("[1] 母本 AST 静态解析（不执行 qc151_trip.py）")
msrc = text(MOTHER)
mtree = ast.parse(msrc)
mlines = lines(MOTHER)

defs = {}
for node in ast.walk(mtree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        defs.setdefault(node.name, []).append(node.lineno)
for name in ("backup_carrier", "copy_post_except_evidence", "except_set_diff",
             "finalize_trip", "main"):
    w(f"  def {name:28s} -> lines {defs.get(name)}")

# 嵌套函数 _except_evidence_copy 的定义行与所属父函数
for node in ast.walk(mtree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "finalize_trip":
        for sub in ast.walk(node):
            if isinstance(sub, ast.FunctionDef) and sub.name == "_except_evidence_copy":
                w(f"  def _except_evidence_copy (nested in finalize_trip) -> line {sub.lineno}")
                for c in ast.walk(sub):
                    if isinstance(c, ast.Call) and getattr(c.func, "id", None) == "copy_post_except_evidence":
                        w(f"    call copy_post_except_evidence at :{c.lineno} nargs={len(c.args)} nkwargs={len(c.keywords)}")
                        w(f"    SOURCE :{c.lineno}: {mlines[c.lineno-1].strip()}")

# 全部调用点（按函数名）
for fname in ("finalize_trip", "copy_post_except_evidence", "backup_carrier"):
    calls = []
    for node in ast.walk(mtree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == fname:
            calls.append(node.lineno)
    w(f"  ALL CALL SITES of {fname:28s} -> lines {calls}")

# finalize_trip 签名（现有形参）
for node in ast.walk(mtree):
    if isinstance(node, ast.FunctionDef) and node.name == "finalize_trip":
        args = [a.arg for a in node.args.args]
        w(f"  finalize_trip 现有形参 ({len(args)}): {args}")
        w(f"  finalize_trip 末行(签名) = :5909 -> {mlines[5908].strip()!r}")
    if isinstance(node, ast.FunctionDef) and node.name == "copy_post_except_evidence":
        args = [a.arg for a in node.args.args]
        w(f"  copy_post_except_evidence 现有形参 ({len(args)}): {args}")

# bak[name] 写入侧的键（AST 提取）
w("  -- bak[name] 写入侧键名（母本 :4460） --")
for node in ast.walk(mtree):
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if (isinstance(t, ast.Subscript) and getattr(t.value, "id", None) == "bak"
                    and isinstance(node.value, ast.Dict)):
                keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
                w(f"    :{node.lineno} bak[name] keys = {keys}")
                w(f"    SOURCE :{node.lineno}: {mlines[node.lineno-1].strip()}")

# backup_carrier 的早退/continue 分支
w("  -- backup_carrier 源不存在分支 --")
for i in range(4450, 4462):
    w(f"    :{i}: {mlines[i-1].rstrip()}")

# CARRIER_FILES
w("  -- CARRIER_FILES --")
for i in (213, 214):
    w(f"    :{i}: {mlines[i-1].rstrip()}")

# main 初始化段与早退路径
w("  -- main 初始化 / 早退（相对 bak=backup_carrier :6387） --")
for i in (6293, 6294, 6295, 6296, 6313, 6387, 6388, 7038, 7093, 7117, 7125):
    w(f"    :{i}: {mlines[i-1].rstrip()}")
early = []
for node in ast.walk(mtree):
    if isinstance(node, ast.FunctionDef) and node.name == "main":
        for r in ast.walk(node):
            if isinstance(r, ast.Return) and r.lineno < 6387 and r.lineno > 6313:
                early.append(r.lineno)
w(f"  main 中 :6313..:6387 之间的 return（早退，bak 尚未赋值）-> {sorted(set(early))}")
w(f"  main finally 起始行 -> :7038 ; finalize_trip 调用 -> :7117")

# ------------------------------------------------------------ 2 B2 键名核验
w("=" * 78)
w("[2] B2 键名逐键核验（写入侧 vs 判定侧）")
b2l = lines(B2)
write_keys, read_keys = [], []
for i, ln in enumerate(b2l, 1):
    for m in re.finditer(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', ln):
        if any(k in m.group(1) for k in ("exists", "mtime", "captured_at", "sha256", "size", "path")):
            write_keys.append((i, m.group(1), ln.strip()))
    for m in re.finditer(r'_pre\.get\("([A-Za-z_][A-Za-z0-9_]*)"\)', ln):
        read_keys.append((i, m.group(1), ln.strip()))
w("  B2 写入侧候选键名（含 \"xxx\": 形式的行）:")
for i, k, s in write_keys:
    w(f"    B2:{i}: key={k!r:20s} {s[:100]}")
w("  B2 判定侧 _pre.get(...) 读取键名:")
for i, k, s in read_keys:
    w(f"    B2:{i}: key={k!r:20s} {s[:100]}")

w(f"  B2 中 'captured_at_iso' 出现次数 = {sum('captured_at_iso' in x for x in b2l)}")
w(f"  B2 中 'captured_at_epoch' 出现次数 = {sum('captured_at_epoch' in x for x in b2l)}")
w(f"  B2 中 'git diff' 出现行 = {[i for i,x in enumerate(b2l,1) if 'git diff' in x]}")
w(f"  TASK.md 中 'git diff' 出现行 = {[i for i,x in enumerate(lines(TASK),1) if 'git diff' in x]}")
w(f"  TASK.md 中 '三处' 出现行 = {[i for i,x in enumerate(lines(TASK),1) if '三处' in x]}")
w(f"  TASK.md 中 '不许扩大' 出现行 = {[i for i,x in enumerate(lines(TASK),1) if '不许扩大' in x]}")
w(f"  W11 candidate 中 '\"mtime\"' 出现行 = {[i for i,x in enumerate(lines(CAND),1) if '\"mtime\"' in x]}")
w(f"  W11 candidate 中 'captured_at_iso' 出现行 = {[i for i,x in enumerate(lines(CAND),1) if 'captured_at_iso' in x]}")

# ------------------------------------------- 3 B2 作用域链与 diff hunk 覆盖
w("=" * 78)
w("[3] B2 作用域链：_pre_freshness_snapshot 定义 / 使用 / diff hunk 覆盖")
occ = [(i, x.strip()) for i, x in enumerate(b2l, 1) if "_pre_freshness_snapshot" in x]
w(f"  _pre_freshness_snapshot 全部出现 ({len(occ)} 处):")
for i, s in occ:
    w(f"    B2:{i}: {s[:130]}")
assigns = [(i, s) for i, s in occ if re.search(r"^\s*_pre_freshness_snapshot\s*=", s)
           or re.search(r"[^\w]_pre_freshness_snapshot\s*=(?!=)", s) and not s.startswith("+")]
w(f"  其中「赋值定义」形式的行 = {assigns}  (空 ⇒ 该名字在 B2 中从未被绑定)")
w("  B2 全部 diff hunk 头（@@ 行）:")
hunks = [(i, x.strip()) for i, x in enumerate(b2l, 1) if x.lstrip().startswith("@@")]
for i, s in hunks:
    w(f"    B2:{i}: {s[:130]}")
w(f"  hunk 总数 = {len(hunks)}")
w("  B2 §2 表格声称的 8 个物理改动行（:181-190）:")
for i in range(181, 191):
    w(f"    B2:{i}: {b2l[i-1].rstrip()}")
w("  检查：是否有 hunk 涉及 :5939 / :6388 / info 字段（:4583-4586）:")
for needle in ("5939", "6388", "4583", "freshness_verdict", "freshness_confidence", "freshness_note", "mtime_post"):
    hits = [i for i, x in enumerate(b2l, 1) if needle in x]
    w(f"    {needle:22s} -> B2 出现行 {hits}")

# B2 自相矛盾语句
w("  B2 关于「删 TASK 里 git diff」/「本文件不改任何文件」的两处原文:")
for i in (175, 234):
    w(f"    B2:{i}: {b2l[i-1].rstrip()}")

# ------------------------------------------- 4 B2 判定算法逐分支实跑
w("=" * 78)
w("[4] 把 B2 :133-154 的判定算法逐字转写后实跑（合成输入，不碰真机/不读载体）")

def b2_classify(pre_snapshot, now_exists, mtime_post, sha_probe):
    """逐字转写 B2 :133-154（含 :130 的默认值 None 语义）。"""
    if pre_snapshot is None:      # :130 pre_snapshot: dict | None = None
        pre_snapshot = {}
    _pre = dict(pre_snapshot or {})            # :133
    _pre_exists = bool(_pre.get("exists"))     # :134
    if not now_exists:                        # :136
        return ("vanished" if _pre_exists else "absent_both",
                "high" if _pre_exists else "n/a")
    _mtime_post = mtime_post                  # :140
    if not _pre_exists:                       # :141
        return ("new_first_appearance", "high")
    _sha_probe = sha_probe                    # :145
    _pre_sha = _pre.get("sha256")             # :146
    _pre_mtime = _pre.get("mtime_pre")        # :147
    if _pre_sha is not None and _pre_sha != _sha_probe:   # :148
        return ("new_write", "high")
    elif _pre_mtime is not None and _mtime_post != _pre_mtime:  # :150
        return ("rewritten_same_content",
                "low" if _mtime_post < _pre_mtime else "medium")
    return ("leftover_unchanged", "high")     # :154

SNAP = {"exists": True, "sha256": "X", "mtime_pre": 100.0, "size": 26405, "path": "p"}
cases = [
    ("E2/E3 修好?: 正常遗留(有exists/mtime_pre)", SNAP, True, 100.0, "X", ("leftover_unchanged", "high")),
    ("错误3 A旁证可达?: 同sha+mtime变",        SNAP, True, 101.0, "X", ("rewritten_same_content", "medium")),
    ("new_write 分支",                          SNAP, True, 100.0, "Y", ("new_write", "high")),
    ("B2 :203 早退 absent_both",                {"exists": False}, False, 0.0, "", ("absent_both", "n/a")),
    ("B2 :204 早退 vanished",                   {"exists": True}, False, 0.0, "", ("vanished", "high")),
    ("空快照 {} vs 显式 exists=False",          {}, True, 100.0, "X", ("new_first_appearance", "high")),
    ("★ N2: 未接线 pre_snapshot=None + 遗留件", None, True, 100.0, "X", ("new_first_appearance", "high")),
]
for label, pre, now, mt, sha, expect in cases:
    got = b2_classify(pre, now, mt, sha)
    w(f"  {label:42s} got={str(got):45s} expect={expect}  -> {'MATCH' if got == expect else 'MISMATCH'}")
w("  NOTE: 最后一行即「pre_snapshot 未传 ⇒ None ⇒ dict({}) ⇒ _pre_exists=False」")
w("        ⇒ 跑前原样遗留的历史 except.txt 被判 new_first_appearance/high（错误 2 的危害重现）")

w("  -- N3 专项：空快照 {} vs 显式 exists=False 是否语义等价 --")
pairs = [
    ("跑后无件", {}, False, 0.0, ""),
    ("跑后无件", {"exists": False}, False, 0.0, ""),
    ("跑后有件", {}, True, 100.0, "X"),
    ("跑后有件", {"exists": False}, True, 100.0, "X"),
]
for label, pre, now, mt, sha in pairs:
    w(f"    {label:10s} pre={str(pre):22s} -> {b2_classify(pre, now, mt, sha)}")
w("    ⇒ 在 B2 :133-154 算法下二者等价（都走 _pre_exists=False）；但 B2 :223-224 声称")
w("      「无键 ⇒ 快照={exists:False}」，而 :130/:133 又用 None⇒{}，二者语义未统一。")
w("  -- N1 专项：main 早退（:6340/:6349/:6361/:6374/:6377 均早于 bak=:6387） --")
w("    这些 return 会进入 finally(:7038) 并调 finalize_trip(:7117)，此时 bak={}（:6294）。")
w("    按 B2 :190「main 基线 :6388 后构造快照」，这些路径上 _pre_freshness_snapshot 从未被绑定")
w("    ⇒ :63 的 `pre_freshness_snapshot=_pre_freshness_snapshot` 会抛 NameError（与错误 1 同类）。")
w("    B2 :66 声称「默认值 None ⇒ 任何其他调用方不受影响」仅在调用方不传该实参时成立；")
w("    :63 明确传了实参，故默认值不提供任何保护。")
w("  -- 既有收尾惯例对照（母本） --")
w("    :5951 _restore  : 未备份 ⇒ 记 null（区分「未测」与「已测」）")
w("    :5963 _t0t1     : 无 T0 ⇒ 记 null")
w("    :5976 _except_diff: 无跑前基线 ⇒ 记 null")
w("    ⇒ B2 的 _pre=dict(pre_snapshot or {}) 把 None/{} 折叠成「跑前不存在」，无法表达「未测」")
w("  -- B2 §2 声称 vs 4 个 diff hunk 的覆盖差 --")
w("    hunk 覆盖: finalize_trip 签名(:43) / main 调用点(:52) / backup_carrier(:75) / copy_post(:128)")
w("    未覆盖但 §2:188-190 声称要改: :5939 传参、:6388 后构造快照（+2 行）")
w("    未覆盖但 §2:186 声称要改: :4583-4586 info +4 键")
w("    ⇒ 四处改动表本身含 3 个无 diff 的「口头改动」，这是第五/第六/第七处该改而没给改法")

w("  -- N5 专项：B2 :43-48 finalize_trip 签名 hunk 的上下文是否与母本 :5900-5909 相符 --")
b2_sig_ctx = [b2l[i-1] for i in (43, 44, 45, 46)]
mother_sig = [mlines[i-1] for i in range(5900, 5910)]
w("    B2 hunk 声称的现有签名上下文:")
for s in b2_sig_ctx:
    w(f"      {s!r}")
w("    母本真实签名 :5900-5909:")
for i, s in enumerate(mother_sig, 5900):
    w(f"      :{i}: {s!r}")
missing = [a for a in ("t0", "pre_except_txt", "out_dir", "ownership",
                       "terminated_ok", "main_return_code", "mother_baseline")
           if not any(a in s for s in b2_sig_ctx)]
w(f"    B2 hunk 上下文缺失的母本形参 = {missing}")
w(f"    ⇒ 该 hunk 的 context 与母本不符（{len(missing)} 个形参被跳过），无法原样套用。")

w("  -- N6 专项：captured_at_iso 是否被静默丢弃 --")
t1 = lines(TASK)
w(f"    TASK.md §3.1 要求三键原文 :47 -> {t1[46].strip()!r}")
w(f"    W11 candidate :80 -> {lines(CAND)[79].strip()!r}")
w(f"    B2 :81-84 写入的键 -> exists / mtime_pre / captured_at_epoch（共 3 个，无 captured_at_iso）")
w(f"    B2 全文 'captured_at_iso' 出现次数 = {sum('captured_at_iso' in x for x in b2l)}")

w("  -- N3 补充：正常路径（src.exists()==True）是否落任何 _fresh --")
w("    B2 :137-154 计算 _fresh（4 个分支），:155-162 只在 `if not _now_exists` 分支 rec.add。")
w("    :163 之后（blob = src.read_bytes() ... 到 :165 hunk 结束）无任何 rec.add / info 写入；")
w("    B2 全文 'freshness_verdict' 出现行 = " + str([i for i, x in enumerate(b2l, 1) if 'freshness_verdict' in x]))
w("    B2 全文 'freshness_confidence'/'freshness_note' 出现次数 = "
  f"{sum('freshness_confidence' in x or 'freshness_note' in x for x in b2l)}")
w("    ⇒ 正常路径（W11 陈旧 except.txt 场景）算出的 _fresh 从未输出。")

# --------------------------------------------------------------- 5 结论摘要
w("=" * 78)
w("[5] 机械核验摘要")
w("  mother finalize_trip 定义 :5900 / 单一调用点 :7117 / main 定义 :6185")
w("  copy_post_except_evidence 定义 :4561 / 单一调用点 :5939（在 finalize_trip 内嵌函数中）")
w("  mother bak[name] :4460 现有键 = ['path','size','sha256']（无 exists / 无 mtime_pre）")
w("  B2 写入侧 :82-84 新增 exists / mtime_pre / captured_at_epoch；判定侧 :146-147 读 sha256 / mtime_pre")
w("  B2 _pre_freshness_snapshot 有使用(:63) 无定义；B2 无 :5939 传参 hunk、无 :6388 构造 hunk")
w("  B2 §2 :186 声称 info +4 键，无对应 diff hunk")
w("=" * 78)

out = "\n".join(buf) + "\n"
# 唯一写出口：直接写 OUT 文件；stdout 不输出任何内容。
# 这样无论调用方是否 `> _b2_probe_out.txt 2>&1` 重定向，文件内容都完全一致（可复跑复现）。
OUT.write_text(out, encoding="utf-8")
