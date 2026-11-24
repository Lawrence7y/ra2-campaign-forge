# -*- coding: utf-8 -*-
"""_nc2_placeholder.py —— 占位符/校验/渲染/回写（补强版，回应复核 verdict=partial）。

★ 与旧版 _nc_placeholder.py 的差别（逐条对应复核破口）：
  (1) sha256 不再是「任意 64 位十六进制」，而是 = claim_digest(c)：
      对「除计算字段外的整条声明（含 value 与证据）」做规范序列化取 SHA256。
      改 value 13→999 而不重算 → BAD_CLAIM_DIGEST，硬 FAIL。
  (2) source_kind 由机器核证据，不再靠撰写人自报：
      实跑   -> 必须有 stdout_path 在盘文件，其 sha256 == stdout_sha256，
                且 value 作为数值 token 出现在该 stdout 里；
      文件行 -> 必须 path:line + line_sha256，实读该行、核行哈希、且当行含 value；
      推导   -> 用受限 AST 求值器重算 derivation，与 value 数值相等；
      估算   -> 无外部证据，但必须 degrade=true、渲染降级、禁入验收段。
      默认 strict=True；任何一条证据不闭合 -> ok=false。
  (3) 未知 {{...}} 不仅报 FAIL，且从渲染文本中整段抹除（不回显 token 内容）。
  (4) check_chain 不再只验链尖：核 history 版本序列 / prev_sha256 连续性 /
      block_sha256 与 claims 的自洽 / 每条 source_block_sha256 无循环依赖。
  (5) cross_section_diff 遇到任何静态 `+ IDENT` 拼接即 UNRENDERED_MACHINE_SEGMENT，
      不再被「绑定行里含数字」击败（lint 必须喂渲染后文本）。

零真机、零采样代码；不执行任务书里的 command（见 §未验项）。
用法：python -I -X utf8 <绝对路径>/_nc2_placeholder.py > <绝对路径>/_nc2_placeholder_demo_out.json
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# 1. 规格常量
# ---------------------------------------------------------------------------

KINDS = ("实跑", "文件行", "估算", "推导")

REQUIRED: dict[str, tuple[str, ...]] = {
    "实跑": ("id", "value", "unit", "scope", "source_kind", "source_ref",
             "sha256", "command", "command_exit", "stdout_path",
             "stdout_sha256", "domain", "artifact"),
    "文件行": ("id", "value", "unit", "scope", "source_kind", "source_ref",
               "sha256", "path", "line", "line_sha256", "domain", "artifact"),
    "估算": ("id", "value", "unit", "scope", "source_kind", "source_ref",
             "sha256", "estimator", "basis", "degrade", "domain", "artifact"),
    "推导": ("id", "value", "unit", "scope", "source_kind", "source_ref",
             "sha256", "derivation", "depends_on", "domain", "artifact"),
}

RATIO_UNITS = {"ratio", "rate", "倍数", "倍", "百分比", "%", "件", "域", "行",
               "处", "分", "pp", "概率", "分数"}

SCOPE_LABELS = {
    "似然", "后验", "q_i", "fp_rate", "台账行", "交付件行", "实跑",
    "Shim", "设计实验", "严格交集", "全量载体", "in-sample", "标签层",
    "真值层", "两层", "三层", "朴素判据", "谓词化判据", "连续外推",
    "整数口径", "发布产物元数据", "自述复算", "被核对象", "其它",
}

ACCEPTANCE_SEGMENTS = ("【交付】", "【必现要素】", "【任务】", "【复核】",
                       "【验收】", "【结论模板】", "publishArtifact",
                       "conclusion:", "description:")

PLACEHOLDER = re.compile(r"\{\{N\.([A-Za-z0-9_.\-]+)\}\}")
ANY_MUSTACHE = re.compile(r"\{\{(.*?)\}\}", re.S)
ESTIMATE_TAG = "（估算，未实跑）"
NONCONFORMING_MARK = "[NONCONFORMING_MUSTACHE]"
UNRESOLVED_MARK = "[UNRESOLVED]"

# 计算字段：不进 claim_digest，也不进块哈希链（避免循环依赖）
COMPUTED_FIELDS = ("sha256", "source_block_sha256", "correction")

_NUM_TOKEN = re.compile(r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?(?![A-Za-z0-9_.])")

# 静态源码里的运行时拼接（lint 必须喂渲染后文本，见到即 FAIL）
RUNTIME_CONCAT = re.compile(
    r'"[^"]*"\s*\+\s*[A-Za-z_$][\w$.]*'
    r'|"\s*\+\s*JSON\.stringify\s*\(')

# ---------------------------------------------------------------------------
# 2. SHA256 工具
# ---------------------------------------------------------------------------

def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def binding_line(raw: bytes) -> str:
    return "被核对象 SHA256 = %s，字节数 = %d" % (sha256_hex(raw), len(raw))


def claim_digest(c: dict) -> str:
    """★ 数字与证据的绑定：对「声明主体（去掉计算字段）」取 SHA256。

    改 value / 改 stdout_sha256 / 改 path:line / 改 scope 任一字节，digest 都变。
    撰写人不能只填一个「看起来像哈希」的 64 位串蒙混。
    """
    body = {k: v for k, v in c.items() if k not in COMPUTED_FIELDS}
    return sha256_hex(canonical_bytes(body))


def seal_claim(c: dict) -> dict:
    """生成/重算一条声明的 sha256。作者不能手写 sha256，只能由工具从证据算。"""
    out = dict(c)
    out.pop("source_block_sha256", None)
    out["sha256"] = claim_digest(out)
    return out


def _norm_value(value: Any) -> str:
    if isinstance(value, bool):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


# ---------------------------------------------------------------------------
# 3. 受限 AST 求值器（只用于「推导」重算，绝不 exec / 不调用任意函数）
# ---------------------------------------------------------------------------

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)
_ALLOWED_FUNCS = {
    "log2": math.log2, "log10": math.log10, "log": math.log,
    "sqrt": math.sqrt, "round": round, "abs": abs, "min": min, "max": max,
}


def safe_eval(expr: str, names: dict[str, float]) -> float:
    r"""只允许 字面量 / 加减乘除乘方取模 / 括号 / 白名单函数 / 白名单变量。"""
    tree = ast.parse(expr, mode="eval")

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return float(names[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARY):
            v = ev(node.operand)
            return +v if isinstance(node.op, ast.UAdd) else -v
        if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
            a, b = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
            if isinstance(node.op, ast.Pow): return a ** b
            return a % b
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in _ALLOWED_FUNCS and not node.keywords:
            return float(_ALLOWED_FUNCS[node.func.id](*[ev(x) for x in node.args]))
        raise ValueError("DISALLOWED_AST_NODE:%s" % type(node).__name__)
    return float(ev(tree))


# ---------------------------------------------------------------------------
# 4. 证据机核（★ 不靠自觉的核心）
# ---------------------------------------------------------------------------

def verify_evidence(c: dict, *, root: str, by_id: dict[str, dict]) -> list[str]:
    """返回问题码列表；空 = 证据闭合。所有路径按 root 解析，绝不执行命令。"""
    problems: list[str] = []
    kind = c.get("source_kind")
    val = _norm_value(c.get("value"))

    if kind == "实跑":
        sp = c.get("stdout_path")
        if not isinstance(sp, str) or not sp:
            return ["实跑:NO_STDOUT_ARTIFACT"]
        path = sp if os.path.isabs(sp) else os.path.join(root, sp)
        if not os.path.isfile(path):
            return ["实跑:STDOUT_ARTIFACT_MISSING"]
        raw = io.open(path, "rb").read()
        if sha256_hex(raw) != c.get("stdout_sha256"):
            problems.append("实跑:STDOUT_SHA256_MISMATCH")
        if c.get("command_exit") != 0:
            problems.append("实跑:COMMAND_EXIT_NOT_ZERO")
        if val and val not in set(_NUM_TOKEN.findall(raw.decode("utf-8", "replace"))):
            problems.append("实跑:VALUE_NOT_IN_STDOUT")
        # 注意：command 本身不重跑（见文件头「未验」声明）。
        if not isinstance(c.get("command"), str) or not c["command"].strip():
            problems.append("实跑:NO_COMMAND")

    elif kind == "文件行":
        p, ln = c.get("path"), c.get("line")
        if not isinstance(p, str) or not isinstance(ln, int):
            return ["文件行:BAD_PATH_OR_LINE"]
        path = p if os.path.isabs(p) else os.path.join(root, p)
        if not os.path.isfile(path):
            return ["文件行:FILE_MISSING"]
        lines = io.open(path, "r", encoding="utf-8", errors="replace").read().split("\n")
        if not (1 <= ln <= len(lines)):
            return ["文件行:LINE_OUT_OF_RANGE"]
        line_bytes = lines[ln - 1].encode("utf-8")
        if sha256_hex(line_bytes) != c.get("line_sha256"):
            problems.append("文件行:LINE_SHA256_MISMATCH")
        if val and val not in set(_NUM_TOKEN.findall(lines[ln - 1])):
            problems.append("文件行:VALUE_NOT_IN_LINE")

    elif kind == "推导":
        deps = c.get("depends_on")
        if not isinstance(deps, list):
            return ["推导:DEPENDS_ON_NOT_LIST"]
        names: dict[str, float] = {}
        for dep in deps:
            if dep not in by_id:
                problems.append("推导:DANGLING_DEP")
            else:
                try:
                    names[dep] = float(by_id[dep]["value"])
                except (TypeError, ValueError):
                    problems.append("推导:DEP_NOT_NUMERIC")
        expr = c.get("derivation")
        if not isinstance(expr, str) or not expr.strip():
            return ["推导:NO_DERIVATION"]
        try:
            got = safe_eval(expr, names)
            want = float(c["value"])
            # 容忍「声明值按 8 位小数登记」的舍入：以声明值的十进制位数为容差，
            # 但不允许 13 vs 999 这种实质错值蒙混（rel_tol=1e-6 上限）。
            s = _norm_value(c["value"])
            decimals = len(s.split(".")[1]) if "." in s else 0
            tol = max(1e-12, 10 ** (-decimals) / 2) if decimals else 1e-9
            if not math.isclose(got, want, rel_tol=1e-9, abs_tol=min(tol, 1e-6)):
                problems.append("推导:DERIVATION_VALUE_MISMATCH")
        except (ValueError, ZeroDivisionError, OverflowError, SyntaxError):
            problems.append("推导:DERIVATION_UNEVALUABLE")

    elif kind == "估算":
        # 估算不需要外部证据；但必须显式降级。留空由 validate 的必填/降级检查处理。
        pass
    return problems


# ---------------------------------------------------------------------------
# 5. 校验器
# ---------------------------------------------------------------------------

def validate_claim_numbers(claims: list[dict], *, strict: bool = True,
                           root: str = "") -> dict:
    """默认 strict=True：任何一条证据不闭合 -> ok=false（不再「标了实跑就过」）。"""
    problems: list[str] = []
    by_id: dict[str, dict] = {}
    if not isinstance(claims, list) or not claims:
        return {"ok": False, "problems": ["EMPTY_CLAIM_NUMBERS"],
                "by_id": {}, "block_sha256": "", "binding_line": ""}

    for i, c in enumerate(claims):
        tag = "claim[%d]" % i
        if not isinstance(c, dict):
            problems.append("%s:NOT_OBJECT" % tag)
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not PLACEHOLDER.fullmatch("{{N.%s}}" % cid):
            problems.append("%s:BAD_ID" % tag)
            continue
        if cid in by_id:
            problems.append("%s:DUP_ID" % tag)
            continue
        by_id[cid] = c

        kind = c.get("source_kind")
        if kind not in KINDS:
            problems.append("%s:BAD_SOURCE_KIND" % tag)
            continue
        missing = [k for k in REQUIRED[kind]
                   if k not in c or (c[k] in (None, "", []) and k != "depends_on")]
        if missing:
            problems.append("%s:MISSING_FIELDS:%s" %
                            (tag, ",".join(missing)))
        # ★ 数字-证据绑定：sha256 必须 == claim_digest(c)
        s = c.get("sha256")
        if not (isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s or "")):
            problems.append("%s:BAD_SHA256" % tag)
        elif s != claim_digest(c):
            problems.append("%s:BAD_CLAIM_DIGEST" % tag)

        scope = c.get("scope")
        if not isinstance(scope, dict) or not scope:
            problems.append("%s:NO_SCOPE" % tag)
        elif scope.get("label") not in SCOPE_LABELS:
            problems.append("%s:SCOPE_LABEL_NOT_IN_VOCAB" % tag)
        if c.get("unit") in RATIO_UNITS:
            sd = scope if isinstance(scope, dict) else {}
            for k in ("numerator", "denominator", "condition"):
                if not sd.get(k):
                    problems.append("%s:AMBIGUOUS_SCOPE_MISSING:%s" % (tag, k))
        if not c.get("domain") or not c.get("artifact"):
            problems.append("%s:NO_DOMAIN_OR_ARTIFACT" % tag)

        if kind == "估算":
            if c.get("degrade") is not True:
                problems.append("%s:ESTIMATE_NOT_DEGRADED" % tag)
            if isinstance(c.get("visible_in"), (list, tuple)):
                bad = sorted(set(c["visible_in"]) & set(ACCEPTANCE_SEGMENTS))
                if bad:
                    problems.append("%s:ESTIMATE_IN_ACCEPTANCE_SEGMENT" % tag)

        if strict:
            for p in verify_evidence(c, root=root, by_id=by_id):
                problems.append("%s:EVIDENCE_UNVERIFIED:%s" % (tag, p))

    raw = canonical_bytes(claims)
    return {"ok": not problems, "problems": problems, "by_id": by_id,
            "block_sha256": sha256_hex(raw), "binding_line": binding_line(raw)}


# ---------------------------------------------------------------------------
# 6. 渲染器
# ---------------------------------------------------------------------------

def render_value(c: dict) -> str:
    # ★ 与 _norm_value 用同一规范化，否则推导值 32768.0 渲染成 "32768.0"，
    #   跨段 diff 的 token 匹配会把「贴了也用了」误报成 UNUSED。
    txt = _norm_value(c["value"]) or str(c["value"])
    if c.get("unit"):
        txt += " " + str(c["unit"])
    label = c.get("scope", {}).get("label") if isinstance(c.get("scope"), dict) else None
    if label:
        txt += "（口径：%s）" % label
    if c.get("source_kind") == "估算":
        txt += ESTIMATE_TAG          # 恒追加，不可关闭
    return txt


def render(text: str, by_id: dict[str, dict], *, allow_estimate: bool = True) -> dict:
    """★ 未知 {{...}} 一律 FAIL 且不回显 token 内容（连渲染文本也不回显）。"""
    problems: list[str] = []
    used: list[str] = []

    def sub(m: re.Match) -> str:
        cid = m.group(1)
        if cid not in by_id:
            problems.append("UNRESOLVED_PLACEHOLDER")
            return UNRESOLVED_MARK
        c = by_id[cid]
        used.append(cid)
        if c.get("source_kind") == "估算" and not allow_estimate:
            problems.append("ESTIMATE_IN_ACCEPTANCE_SEGMENT")
            return "[ESTIMATE_REJECTED]"
        return render_value(c)

    out = PLACEHOLDER.sub(sub, text)
    # 非 {{N.*}} 形态：整段抹除，不把 token 原文留在输出里
    n_bad = 0
    def kill(m: re.Match) -> str:
        nonlocal n_bad
        if PLACEHOLDER.fullmatch(m.group(0)):
            return m.group(0)
        n_bad += 1
        return NONCONFORMING_MARK
    out = ANY_MUSTACHE.sub(kill, out)
    if n_bad:
        problems.append("NONCONFORMING_MUSTACHE:n=%d" % n_bad)
    return {"ok": not problems, "text": out, "problems": problems, "used": used}


# ---------------------------------------------------------------------------
# 7. 跨段 diff（只对渲染后全文跑）
# ---------------------------------------------------------------------------

def cross_section_diff(machine_text: str, prose_text: str, v: dict,
                       *, rendered: bool) -> dict:
    """★ 静态 `+ IDENT` 拼接源码冒充已渲染全文 -> 直接 FAIL，不假报通过。

    旧版会被「绑定行里含数字」击败（_ncv_probe4_out.json）。本版逐行判：
    `+ IDENT` 所在行本身没有数值 token 就是未渲染，别的行的数字不作数。
    """
    # ★ 只在「确实存在运行时拼接」时才需要渲染后全文；没有拼接的纯文本
    #   任务书可直接做数值 diff（否则所有正例都会被误报）。
    has_concat = bool(RUNTIME_CONCAT.search(machine_text))
    if has_concat and not rendered:
        return {"ok": False, "problems": ["UNRENDERED_MACHINE_SEGMENT"],
                "note": "调用方未声明已渲染全文；必须在 ASK_ANALYST.join('\\n') "
                        "渲染后的全文上跑。"}
    if has_concat:
        # ★ 逐行判：任何 `+ IDENT` 行若整行看不到数值 token，即静态源码冒充。
        # 绑定行里的数字（另一行）不能替它构成通过。
        for line in machine_text.split("\n"):
            if RUNTIME_CONCAT.search(line) and not _NUM_TOKEN.search(line):
                return {"ok": False, "problems": ["UNRENDERED_MACHINE_SEGMENT"],
                        "note": "静态源码 `+ vfText` 看不到运行时值；"
                                "绑定行里的数字不能替它构成通过。"}
    problems: list[str] = []
    machine_tokens = set(_NUM_TOKEN.findall(machine_text))
    # ★ 先把散文里的 {{N.id}} 解析成实际数值再取 token；否则「贴了也用了」
    #   的正例会被误报成 CROSS_SECTION_VALUE_NOT_USED（占位符本身不含数字）。
    r = render(prose_text, v["by_id"])
    prose_tokens = set(_NUM_TOKEN.findall(r["text"]))
    for cid, c in v["by_id"].items():
        val = _norm_value(c["value"])
        if val and val in machine_tokens and val not in prose_tokens:
            problems.append("CROSS_SECTION_VALUE_NOT_USED:%s" % cid)
    return {"ok": not problems, "problems": problems,
            "note": "引述段由调用方从 prose_text 中排除，避免把 #19/#20 被核错值误报。"}


# ---------------------------------------------------------------------------
# 8. 回写机制（★ 全链自洽，非只验链尖）
# ---------------------------------------------------------------------------

NUMBER_SOURCE = "lead/number_channel_20261109/_nc_number_source.json"


def chain_block_bytes(store: dict) -> bytes:
    """块哈希只覆盖 claims 的证据主体（排除计算字段），避免循环依赖。"""
    claims = [{k: v for k, v in c.items() if k != "source_block_sha256"}
              for c in store["claims"]]
    return canonical_bytes(claims)


def load_source(path: str) -> dict:
    return json.load(io.open(path, "r", encoding="utf-8"))


def save_source(path: str, store: dict) -> dict:
    """纠正 -> 只改这里；版本 +1，prev 指向旧块，history 留证。"""
    prev = store.get("block_sha256", "")
    store["version"] = int(store.get("version", 0)) + 1
    store["prev_sha256"] = prev
    if prev:
        store.setdefault("prev_hashes", []).append(prev)
    block = sha256_hex(chain_block_bytes(store))
    store["block_sha256"] = block
    store["binding_line"] = binding_line(chain_block_bytes(store))
    for c in store["claims"]:
        c["source_block_sha256"] = block   # 与最终块哈希一致（非循环）
    io.open(path, "w", encoding="utf-8").write(
        json.dumps(store, ensure_ascii=False, sort_keys=True, indent=2))
    return store


def correct_value(path: str, cid: str, new_value: Any, *, evidence: str) -> dict:
    store = load_source(path)
    hit = [c for c in store["claims"] if c.get("id") == cid]
    if not hit:
        return {"ok": False, "problem": "UNKNOWN_ID"}
    c = hit[0]
    old = c["value"]
    if old == new_value:
        return {"ok": True, "changed": False, "version": store["version"]}
    c["value"] = new_value
    c["sha256"] = claim_digest(c)          # ★ 值变了，证据摘要同步重算
    c["correction"] = {"from": old, "to": new_value, "evidence": evidence}
    store.setdefault("history", []).append(
        {"id": cid, "from": old, "to": new_value, "evidence": evidence,
         "at_version": int(store.get("version", 0)) + 1})
    return {"ok": True, "changed": True, "store": save_source(path, store)}


def taskbook_header(store: dict) -> str:
    return ("【数字源】%s version=%d\n%s" %
            (NUMBER_SOURCE, store["version"], store["binding_line"]))


def check_chain(taskbook_text: str, store: dict) -> dict:
    """★ 全链校验：链尖 + 版本 + history 序列 + prev 连续性 + 块自洽。"""
    m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})", taskbook_text)
    if not m:
        return {"ok": False, "problem": "NO_BINDING_LINE"}
    ver = store.get("version")
    if not isinstance(ver, int) or ver < 1:
        return {"ok": False, "problem": "BAD_VERSION"}
    if ("version=%d" % ver) not in taskbook_text:
        return {"ok": False, "problem": "STALE_VERSION"}
    # 块自洽（抹掉 claims / 断链都会在这里被抓）
    if sha256_hex(chain_block_bytes(store)) != store.get("block_sha256"):
        return {"ok": False, "problem": "BLOCK_HASH_MISMATCH"}
    if m.group(1) != store["block_sha256"]:
        return {"ok": False, "problem": "STALE_NUMBER_SOURCE"}
    for c in store.get("claims", []):
        if c.get("source_block_sha256") != store["block_sha256"]:
            return {"ok": False, "problem": "CLAIM_BLOCK_HASH_MISMATCH"}
        if c.get("sha256") != claim_digest(c):
            return {"ok": False, "problem": "BAD_CLAIM_DIGEST"}
    hist = store.get("history")
    if not isinstance(hist, list):
        return {"ok": False, "problem": "NO_HISTORY"}
    # 每次纠正必须有一条 history，版本号 2..ver 连续且不重复
    expected = list(range(2, ver + 1))
    got = sorted(int(h.get("at_version", -1)) for h in hist
                 if isinstance(h, dict) and all(
                     k in h for k in ("id", "from", "to", "evidence", "at_version")))
    if got != expected:
        return {"ok": False, "problem": "HISTORY_CHAIN_BROKEN"}
    if ver > 1:
        p = store.get("prev_sha256")
        prev_hashes = store.get("prev_hashes")
        if not (isinstance(p, str) and re.fullmatch(r"[0-9a-f]{64}", p)) \
                or not isinstance(prev_hashes, list) \
                or len(prev_hashes) < ver - 1 \
                or prev_hashes[-1] != p:
            return {"ok": False, "problem": "PREV_SHA256_BROKEN"}
    return {"ok": True, "problem": ""}


# ---------------------------------------------------------------------------
# 9. 演示用声明（全部证据闭合，由 build_demo() 生成在盘证据文件）
# ---------------------------------------------------------------------------

def build_demo(root: str) -> list[dict]:
    """生成 5 条声明 + 1 份实跑 stdout 证据文件（都落本任务写域）。"""
    ev_dir = os.path.join(root, "lead", "number_channel_20261109")
    stdout_path = os.path.join(ev_dir, "_nc2_demo_stdout.txt")
    io.open(stdout_path, "w", encoding="utf-8").write(
        "gateProblems 非空 13 域\nbindings=0 6 域\n")
    stdout_sha = sha256_hex(io.open(stdout_path, "rb").read())

    gate_rel = "lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md"
    gate_abs = os.path.join(root, gate_rel.replace("/", os.sep))
    line51 = io.open(gate_abs, "r", encoding="utf-8").read().split("\n")[50]
    line_sha = sha256_hex(line51.encode("utf-8"))

    def base(cid, value, unit, kind, label, **kw):
        c = {"id": cid, "value": value, "unit": unit,
             "scope": {"label": label, "numerator": kw.pop("numerator", "n/a"),
                       "denominator": kw.pop("denominator", "n/a"),
                       "condition": kw.pop("condition", "n/a")},
             "source_kind": kind, "source_ref": "demo",
             "domain": "gate_rejudge32", "artifact": "GATE_REJUDGE_32.md", **kw}
        return seal_claim(c)

    raw = [
        base("domains_nonempty", 13, "域", "实跑", "全量载体",
             command="python -I -X utf8 <rejudge.py>", command_exit=0,
             stdout_path="lead/number_channel_20261109/_nc2_demo_stdout.txt",
             stdout_sha256=stdout_sha),
        base("bindings_zero", 6, "域", "实跑", "全量载体",
             command="python -I -X utf8 <rejudge.py>", command_exit=0,
             stdout_path="lead/number_channel_20261109/_nc2_demo_stdout.txt",
             stdout_sha256=stdout_sha),
        base("ratio_32768", 32768, "倍", "推导", "两层",
             derivation="0.25/7.62939453125e-06", depends_on=[]),
        base("rho_threshold", 0.14013134, "无量纲", "推导", "连续外推",
             derivation="(18/log2(40)-1)/17", depends_on=[]),
        base("est_effort", 25, "%", "估算", "其它",
             estimator="编排方", basis="历史任务书耗时", degrade=True,
             visible_in=["【背景】"]),
    ]
    # 推导值按声明的 8 位精度收敛；用推导重算值覆盖（仍由工具 seal）
    out = []
    for c in raw:
        if c["source_kind"] == "推导":
            v = safe_eval(c["derivation"], {})
            c = dict(c)
            c["value"] = round(v, 8)
            c = seal_claim(c)
        out.append(c)
    # 文件行声明（用真实在盘行，值 13 出现在该行）
    fl = base("domains_from_file", 13, "域", "文件行", "全量载体",
              path=gate_rel, line=51, line_sha256=line_sha)
    out.append(fl)
    return out


if __name__ == "__main__":
    root = r"D:\Project\ra2-campaign-forge"
    claims = build_demo(root)
    v = validate_claim_numbers(claims, strict=True, root=root)
    print(json.dumps({"validate": v, "n_claims": len(claims),
                      "binding_line": v["binding_line"]},
                     ensure_ascii=False, indent=2))
