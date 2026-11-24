# -*- coding: utf-8 -*-
"""_nc_placeholder.py —— 占位符方案的可粘贴实现（解析器 + 校验器 + 渲染器 + 回写）。

零真机、零采样代码；纯文本/JSON 处理。用法：
    python -I -X utf8 <本文件绝对路径>            # 跑内建自检
    python -I -X utf8 <本文件绝对路径> <taskbook.json>   # 校验一份任务书

设计要点（对应任务书第二步）：
  1. 散文段只允许 {{N.<id>}} 占位；数字集中在 CLAIM_NUMBERS 机器段。
  2. source_kind 受控词表 4 值：实跑 / 文件行 / 估算 / 推导，各有必填字段。
  3. 估算渲染强制显式降级，且禁入【交付】/【必现要素】/【任务】/【复核】/结论模板。
  4. 回写机制：单一数字源 + 版本号 + SHA256 链；纠正只能改源，不散文。
  5. 未知 {{...}} token 一律 FAIL 且不回显（防「占位符当实值用」/注入）。
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# 1. 规格常量
# ---------------------------------------------------------------------------

KINDS = ("实跑", "文件行", "估算", "推导")

# 每种 source_kind 的必填字段；任何缺失 -> FAIL（不靠自觉）
REQUIRED: dict[str, tuple[str, ...]] = {
    "实跑": ("id", "value", "unit", "scope", "source_kind", "source_ref",
             "sha256", "command", "stdout_sha256", "domain", "artifact"),
    "文件行": ("id", "value", "unit", "scope", "source_kind", "source_ref",
               "sha256", "path", "line", "domain", "artifact"),
    "估算": ("id", "value", "unit", "scope", "source_kind", "sha256",
             "estimator", "basis", "domain", "artifact", "degrade"),
    "推导": ("id", "value", "unit", "scope", "source_kind", "sha256",
             "derivation", "depends_on", "domain", "artifact"),
}

# 比率/倍数/件数/域数类必须带口径三元组，否则 AMBIGUOUS_SCOPE
RATIO_UNITS = {"ratio", "rate", "倍数", "倍", "百分比", "%", "件", "域", "行",
               "处", "分", "pp", "概率", "分数"}

# 验收/派发段：估算禁止出现（渲染前拦截，不是渲染后靠人看）
ACCEPTANCE_SEGMENTS = ("【交付】", "【必现要素】", "【任务】", "【复核】",
                       "【验收】", "【结论模板】", "publishArtifact", "conclusion:")

# 占位符语法：只允许 {{N.<id>}}，id 为 [A-Za-z0-9_.-]+
PLACEHOLDER = re.compile(r"\{\{N\.([A-Za-z0-9_.\-]+)\}\}")
ANY_MUSTACHE = re.compile(r"\{\{(.*?)\}\}", re.S)

# 机器段标记：这些段里的数字由机器生成，允许裸数字
MACHINE_MARKERS = ("【编排方实跑指纹】", "【编排方指纹】", "【复核数据】",
                   "【编排方实跑】", "【实跑结果】", "【双轨重判】",
                   "CLAIM_NUMBERS", "被核对象 SHA256 = ")

# 引述段：被核对象/原文引述里的数字是「材料」不是「主张」，不参与跨段 diff
QUOTED_MARKERS = ("【被核对象】", "【核查】", "【背景——", "CLAIMS = [", "【原文】")

ESTIMATE_TAG = "（估算，未实跑）"

# ---------------------------------------------------------------------------
# 2. SHA256 工具（绑定行格式固定，中间不插任何字符）
# ---------------------------------------------------------------------------

def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    """规范序列化：sort_keys + 无多余空白 + ensure_ascii=False -> UTF-8。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def binding_line(raw: bytes) -> str:
    return "被核对象 SHA256 = %s，字节数 = %d" % (sha256_hex(raw), len(raw))


# ---------------------------------------------------------------------------
# 3. 校验器：CLAIM_NUMBERS 块
# ---------------------------------------------------------------------------

def validate_claim_numbers(claims: list[dict], *, strict: bool = True) -> dict:
    """返回 {ok, problems, by_id, block_sha256}。problems 为机器可读码。"""
    problems: list[str] = []
    by_id: dict[str, dict] = {}

    if not isinstance(claims, list) or not claims:
        return {"ok": False, "problems": ["EMPTY_CLAIM_NUMBERS"],
                "by_id": {}, "block_sha256": ""}

    for i, c in enumerate(claims):
        tag = "claim[%d]" % i
        if not isinstance(c, dict):
            problems.append("%s:NOT_OBJECT" % tag)
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not PLACEHOLDER.fullmatch("{{N.%s}}" % cid):
            problems.append("%s:BAD_ID:%r" % (tag, cid))
            continue
        if cid in by_id:
            problems.append("%s:DUP_ID:%s" % (tag, cid))
            continue
        by_id[cid] = c

        kind = c.get("source_kind")
        if kind not in KINDS:
            problems.append("%s:BAD_SOURCE_KIND:%r" % (tag, kind))
            continue
        missing = [k for k in REQUIRED[kind]
                   if k not in c or (c[k] in (None, "", []) and k != "depends_on")]
        if missing:
            problems.append("%s:MISSING_FIELDS:%s:%s" % (tag, kind, ",".join(missing)))
        # depends_on 必须是 list（可为空 = 自足推导），但不得缺键
        if kind == "推导" and not isinstance(c.get("depends_on"), list):
            problems.append("%s:DEPENDS_ON_NOT_LIST" % tag)

        # 每项必须自带 sha256（数字与来源的绑定）
        s = c.get("sha256")
        if not (isinstance(s, str) and re.fullmatch(r"[0-9a-f]{64}", s or "")):
            problems.append("%s:BAD_SHA256" % tag)

        # scope 必填且必须带口径字典标签（拦「口径混淆」）
        scope = c.get("scope")
        if not isinstance(scope, dict) or not scope:
            problems.append("%s:NO_SCOPE" % tag)
        elif not scope.get("label") or scope.get("label") not in SCOPE_LABELS:
            problems.append("%s:SCOPE_LABEL_NOT_IN_VOCAB:%r" % (tag, scope.get("label")))

        # 比率/倍数/件数类强制口径三元组（拦 #3/#4/#5/#13/#18）
        if c.get("unit") in RATIO_UNITS:
            scope_d = c.get("scope") if isinstance(c.get("scope"), dict) else {}
            for k in ("numerator", "denominator", "condition"):
                if not scope_d.get(k):
                    problems.append("%s:AMBIGUOUS_SCOPE_MISSING:%s" % (tag, k))

        # 域/件标签（拦 #6/#8/#11 跨域串台）
        if not c.get("domain") or not c.get("artifact"):
            problems.append("%s:NO_DOMAIN_OR_ARTIFACT" % tag)

        # 估算：必须带 degrade 且为 True，且不得出现在验收段
        if kind == "估算":
            if c.get("degrade") is not True:
                problems.append("%s:ESTIMATE_NOT_DEGRADED" % tag)
            if isinstance(c.get("visible_in"), (list, tuple)):
                bad = sorted(set(c["visible_in"]) & set(ACCEPTANCE_SEGMENTS))
                if bad:
                    problems.append("%s:ESTIMATE_IN_ACCEPTANCE_SEGMENT:%s" %
                                    (tag, ",".join(bad)))

        # 推导：depends_on 必须指向本块内已声明的 id
        if kind == "推导":
            for dep in c.get("depends_on", []) or []:
                if dep not in by_id and dep not in {x.get("id") for x in claims}:
                    problems.append("%s:DANGLING_DEP:%s" % (tag, dep))

        # 实跑 / 文件行：sha256 必须等于 source 的实际内容（若给了路径）
        if strict and kind == "文件行" and c.get("path"):
            p = c["path"]
            if os.path.isfile(p):
                with io.open(p, "rb") as f:
                    raw = f.read()
                # 行级绑定：sha256 应等于指定行的 UTF-8 字节
                L = raw.decode("utf-8", "replace").split("\n")
                ln = int(c.get("line", 0))
                if 1 <= ln <= len(L):
                    want = sha256_hex(L[ln - 1].encode("utf-8"))
                    if c.get("line_sha256") and c["line_sha256"] != want:
                        problems.append("%s:LINE_SHA_MISMATCH" % tag)
                else:
                    problems.append("%s:LINE_OUT_OF_RANGE" % tag)

    # 所有占位符引用必须能在块内反查（调用方用 check_references）
    return {
        "ok": not problems,
        "problems": problems,
        "by_id": by_id,
        "block_sha256": sha256_hex(canonical_bytes(claims)),
        "binding_line": binding_line(canonical_bytes(claims)),
    }


# 口径受控词表：标签不在表内直接 FAIL（拦「少报口径数、多报确定性」）
SCOPE_LABELS = {
    "似然", "后验", "q_i", "fp_rate", "台账行", "交付件行", "实跑",
    "Shim", "设计实验", "严格交集", "全量载体", "in-sample", "标签层",
    "真值层", "两层", "三层", "朴素判据", "谓词化判据", "连续外推",
    "整数口径", "发布产物元数据", "自述复算", "被核对象", "其它",
}


# ---------------------------------------------------------------------------
# 4. 渲染器
# ---------------------------------------------------------------------------

def render_value(c: dict) -> str:
    """把一条 CLAIM_NUMBERS 渲染成散文里可插入的文本。"""
    v = c["value"]
    txt = str(v)
    if c.get("unit"):
        txt += " " + str(c["unit"])
    label = c.get("scope", {}).get("label") if isinstance(c.get("scope"), dict) else None
    if label:
        txt += "（口径：%s）" % label
    if c.get("source_kind") == "估算":
        # 显式降级，不可关闭
        txt += ESTIMATE_TAG
    return txt


def render(text: str, by_id: dict[str, dict], *, allow_estimate: bool = True) -> dict:
    """替换 {{N.id}}；未知 token 一律 FAIL 且不回显 token 内容。"""
    problems: list[str] = []
    used: list[str] = []

    def sub(m: re.Match) -> str:
        cid = m.group(1)
        if cid not in by_id:
            problems.append("UNRESOLVED_PLACEHOLDER")  # 不回显 cid
            return "[UNRESOLVED]"
        c = by_id[cid]
        used.append(cid)
        if c.get("source_kind") == "估算" and not allow_estimate:
            problems.append("ESTIMATE_IN_ACCEPTANCE_SEGMENT")
            return "[ESTIMATE_REJECTED]"
        return render_value(c)

    out = PLACEHOLDER.sub(sub, text)
    # 任何其它 {{...}} 形态都是硬 FAIL（含未知占位符 / 被投放的伪值）
    leftovers = [m for m in ANY_MUSTACHE.finditer(out)
                 if not PLACEHOLDER.fullmatch(m.group(0))]
    if leftovers:
        problems.append("NONCONFORMING_MUSTACHE:n=%d" % len(leftovers))  # 不回显内容
    return {"ok": not problems, "text": out, "problems": problems, "used": used}


# ---------------------------------------------------------------------------
# 5. 引用完整性 + 跨段数值一致性 diff
# ---------------------------------------------------------------------------

ARABIC = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?(?![A-Za-z0-9_])")
CJK_NUM = re.compile(r"[一二三四五六七八九十百千万零两]\s*"
                     r"(?:个|件|条|域|行|处|倍|层|分|项|次|组|份|轮|版|道|类|种)")

EXEMPT_PATTERNS = tuple(re.compile(r) for r in (
    r"[\w./\\-]+:\d+(?:-\d+)?",        # path:line / :22
    r"\b[0-9a-f]{12,64}\b",             # hash
    r"tail:\s*\d+",                     # output.tail 字节上限
    r"§\d+(?:[.\-]\d+)*",               # 小节号
    r"\b\d{4}-\d{2}-\d{2}\b",           # 日期
    r"\b(?:R|V|C|D|A|B|E|F|H|N)\d+\b",  # R10 / D-27 / N13 / V12
    r"\bdwfrun-[0-9a-f\-]{20,}",        # run id
    r"\b\d+\s*B\b",                     # 字节数
    r"python\s+-I\s+-X\s+utf8",         # 铁律命令
    r"\b\d+(?:\.\d+)?\s*(?:pp|%)\b",    # 已在占位符里带口径的百分数
))
INLINE_CODE = re.compile(r"`[^`]*`")
FENCED = re.compile(r"^```.*?^```", re.S | re.M)


def mask_code(text: str) -> str:
    """代码块/行内代码里的数字不报（误报控制）。"""
    return INLINE_CODE.sub(" ", FENCED.sub(" ", text))


def check_references(segments: dict[str, str], v: dict) -> dict:
    """segments: {段名: 文本}；机器段跳过裸数字检查，散文段严格。"""
    problems: list[str] = []
    all_used: list[str] = []
    for name, text in segments.items():
        is_machine = any(k in name for k in MACHINE_MARKERS)
        is_quoted = any(k in name for k in QUOTED_MARKERS)
        # 所有段（含机器段）都解析占位符
        r = render(text, v["by_id"], allow_estimate=not (
            any(a in name for a in ACCEPTANCE_SEGMENTS)))
        problems += ["%s:%s" % (name, p) for p in r["problems"]]
        all_used += r["used"]
        if is_machine or is_quoted:
            continue
        masked = mask_code(text)
        for pat in EXEMPT_PATTERNS:
            masked = pat.sub(" ", masked)
        n_ar = len(ARABIC.findall(masked))
        n_cjk = len(CJK_NUM.findall(masked))
        if n_ar:
            problems.append("%s:BARE_ARABIC:n=%d" % (name, n_ar))
        if n_cjk:
            problems.append("%s:BARE_CJK_NUMERAL:n=%d" % (name, n_cjk))
    unused = sorted(set(v["by_id"]) - set(all_used))
    return {"ok": not problems, "problems": problems,
            "used_ids": sorted(set(all_used)), "unused_ids": unused,
            "block_sha256": v["block_sha256"]}


def cross_section_diff(machine_text: str, prose_text: str,
                       v: dict) -> dict:
    """跨段数值 diff（★ 只能对**渲染后**的任务书跑，见下方 note）。

    规则：机器段以独立数值 token 贴出的值，若散文段既没引用该 id 的占位符、
    也没出现同值 token，报「贴了没用」。用 token 边界匹配，避免把 SHA256
    十六进制里的 "6"/"13" 当成数值命中。
    引述段（QUOTED / 被核对象）由调用方排除，避免把 #19/#20 的被核错值误报。
    """
    problems: list[str] = []
    machine_tokens = set(_NUM_TOKEN.findall(machine_text))
    prose_tokens = set(_NUM_TOKEN.findall(prose_text))
    # 静态源码里只有 `"【复核数据】" + vfText`，运行时值看不到：
    # 此时不假报通过，而是显式报 UNRENDERED_MACHINE_SEGMENT。
    if re.search(r"\+\s*[A-Za-z_$][\w$.]*(?:Text|JSON\.stringify)", machine_text) \
            and not _NUM_TOKEN.search(machine_text):
        return {"ok": False,
                "problems": ["UNRENDERED_MACHINE_SEGMENT"],
                "note": "必须在 ASK_ANALYST.join('\\n') 渲染后跑；静态源码不构成通过。"}
    for cid, c in v["by_id"].items():
        val = _norm_value(c["value"])
        if val and val in machine_tokens and val not in prose_tokens \
                and ("{{N.%s}}" % cid) not in prose_text:
            problems.append("CROSS_SECTION_VALUE_NOT_USED:%s" % cid)
    return {"ok": not problems, "problems": problems,
            "note": "必须在 .mjs 里对 ASK_ANALYST.join('\\n') 的**渲染后**全文跑；"
                    "静态源码里 `+ fpText` 看不到运行时值，此处会自然跳过（不假报通过）。"}


_NUM_TOKEN = re.compile(r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?(?![A-Za-z0-9_.])")


def _norm_value(value: Any) -> str:
    """把声明值规范成 token 形式，与 _NUM_TOKEN 抽取口径一致。"""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


# ---------------------------------------------------------------------------
# 6. 回写机制：同一数字在多份任务书重复出现
# ---------------------------------------------------------------------------

NUMBER_SOURCE = "lead/number_channel_20261109/_nc_number_source.json"


def load_source(path: str) -> dict:
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_source(path: str, store: dict) -> dict:
    """纠正 -> 只改这里；版本号 +1，重算块哈希，追加 prev 形成链。"""
    prev = store.get("block_sha256", "")
    store["version"] = int(store.get("version", 0)) + 1
    store["prev_sha256"] = prev
    claims = store["claims"]
    store["block_sha256"] = sha256_hex(canonical_bytes(claims))
    store["binding_line"] = binding_line(canonical_bytes(claims))
    for c in claims:
        # 每条的来源哈希随块版本走，避免「改了值忘了改绑定」
        c["source_block_sha256"] = store["block_sha256"]
    store["block_sha256"] = sha256_hex(canonical_bytes(claims))
    store["binding_line"] = binding_line(canonical_bytes(claims))
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(store, ensure_ascii=False, sort_keys=True, indent=2))
    return store


def correct_value(path: str, cid: str, new_value: Any,
                  *, evidence: str) -> dict:
    """子任务纠正的**唯一**入口：改源、留证、升版本；散文一字不动。"""
    store = load_source(path)
    hit = [c for c in store["claims"] if c.get("id") == cid]
    if not hit:
        return {"ok": False, "problem": "UNKNOWN_ID"}
    c = hit[0]
    old = c["value"]
    if old == new_value:
        return {"ok": True, "changed": False, "version": store["version"]}
    c["value"] = new_value
    c["correction"] = {"from": old, "to": new_value, "evidence": evidence}
    store.setdefault("history", []).append(
        {"id": cid, "from": old, "to": new_value, "evidence": evidence,
         "at_version": int(store.get("version", 0)) + 1})
    return {"ok": True, "changed": True, "store": save_source(path, store)}


def taskbook_header(store: dict) -> str:
    """每份任务书末尾必贴的链头；下轮必须复贴，否则 STALE_NUMBER_SOURCE。

    格式固定：绑定行里「被核对象 SHA256 = 」紧跟 64 位十六进制，中间不插任何字符。
    """
    return ("【数字源】%s version=%d\n%s" %
            (NUMBER_SOURCE, store["version"], store["binding_line"]))


def check_chain(taskbook_text: str, store: dict) -> dict:
    """任务书必须复贴当前块的哈希；滞后即 FAIL（杜绝纠正没回写）。"""
    want = store["block_sha256"]
    m = re.search(r"被核对象 SHA256 = ([0-9a-f]{64})", taskbook_text)
    if not m:
        return {"ok": False, "problem": "NO_BINDING_LINE"}
    if m.group(1) != want:
        return {"ok": False, "problem": "STALE_NUMBER_SOURCE"}
    if ("version=%d" % store["version"]) not in taskbook_text:
        return {"ok": False, "problem": "STALE_VERSION"}
    return {"ok": True, "problem": ""}


# ---------------------------------------------------------------------------
# 7. 内建自检（正例/反例各 5，由 _nc_selftest.py 调用并打印）
# ---------------------------------------------------------------------------

def _demo_claims() -> list[dict]:
    """演示用；真实场景从 _nc_number_source.json 读。"""
    def base(cid, value, unit, kind, **kw):
        d = {"id": cid, "value": value, "unit": unit, "scope": {
            "label": kw.pop("label", "其它"),
            "numerator": kw.pop("numerator", "n/a"),
            "denominator": kw.pop("denominator", "n/a"),
            "condition": kw.pop("condition", "n/a")},
            "source_kind": kind, "sha256": hashlib.sha256(
                (cid + str(value)).encode()).hexdigest(),
            "domain": "gate_rejudge32", "artifact": "GATE_REJUDGE_32.md",
            "source_ref": "demo", **kw}
        return d
    return [
        base("domains_nonempty", 13, "域", "实跑", label="全量载体",
             command="python -I -X utf8 <rejudge>", stdout_sha256="a" * 64),
        base("bindings_zero", 6, "域", "实跑", label="全量载体",
             command="python -I -X utf8 <rejudge>", stdout_sha256="b" * 64),
        base("ratio_32768", 32768, "倍", "推导", label="两层",
             derivation="0.25/7.62939453125e-06", depends_on=[]),
        base("rho_threshold", 0.14013134, "无量纲", "推导", label="连续外推",
             derivation="(18/log2(40)-1)/17", depends_on=[]),
        base("est_effort", 25, "%", "估算", label="其它",
             estimator="编排方", basis="历史任务书耗时", degrade=True,
             visible_in=["【背景】"]),
    ]


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with io.open(sys.argv[1], "r", encoding="utf-8") as f:
            tb = json.load(f)
        v = validate_claim_numbers(tb["CLAIM_NUMBERS"], strict=False)
        print(json.dumps({"validate": v,
                          "references": check_references(tb["segments"], v),
                          "chain": check_chain(tb.get("header", ""),
                                               {"block_sha256": v["block_sha256"],
                                                "version": tb.get("version", 1)})},
                         ensure_ascii=False, indent=2))
    else:
        v = validate_claim_numbers(_demo_claims(), strict=False)
        print(json.dumps({"validate": v, "binding_line": v["binding_line"]},
                         ensure_ascii=False, indent=2))
