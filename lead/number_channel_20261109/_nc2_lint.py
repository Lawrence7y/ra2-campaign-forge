# -*- coding: utf-8 -*-
"""_nc2_lint.py —— 派发前 lint（补强版，回应复核 verdict=partial）。

★ 与旧版 _nc_lint.py 的差别（逐条对应复核破口）：
  (2) 删掉「含【编排方实跑指纹】等标题即机器段」的 MACHINE_MARK 规则：
      机器段**只**由「该行是运行时拼接（`"..." + IDENT`）」或显式
      `// MACHINE_SEGMENT` 注释声明判定，纯字符串标题一律是散文。
  (3) 验收段（ACCEPTANCE）优先于 QUOTED_OPEN：【复核】【交付】里的估算必 FAIL。
      引述段只在「确为被核材料」时开（【被核对象】/【原文】/CLAIMS = [）。
  (4) 扫描范围不再只抽首个 ASK_ANALYST：
      - 所有 `const XXX = [ ... ].join` 数组；
      - 全文所有 publishArtifact / conclusion: / description: 行（独立扫描）。
      故 868215ce 的 lowered:170/217/226 都在射程内。
  (5) 跨段 diff 保留 UNRENDERED_MACHINE_SEGMENT 规则码，不再映射成
      CROSS_SECTION_VALUE_NOT_USED；静态 `+ vfText` 即使带绑定行也 FAIL。
  (6) 自检扩到 20 例，覆盖全部 18 条声明规则 + 5 条真实损害行。
  (1) source_kind 的证据机核由 _nc2_placeholder.validate_claim_numbers(strict=True)
      完成；错值 10 标「实跑」但无 stdout 证据 -> EVIDENCE_UNVERIFIED -> FAIL。

零真机、零采样代码；不改任何既有件。
用法：
  python -I -X utf8 <绝对路径>/_nc2_lint.py > <绝对路径>/_nc2_lint_selftest_out.json
  python -I -X utf8 <绝对路径>/_nc2_lint.py <draft.dwf.ts> > <绝对路径>/_nc2_lint_real_draft_out.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import sys

_DIR = r"D:\Project\ra2-campaign-forge\lead\number_channel_20261109"
ROOT = r"D:\Project\ra2-campaign-forge"
_spec = importlib.util.spec_from_file_location(
    "nc2ph", os.path.join(_DIR, "_nc2_placeholder.py"))
ncph = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ncph)

# ---------------------------------------------------------------------------
# 1. 段落判定（★ 靠结构，不靠标题）
# ---------------------------------------------------------------------------

# 机器段：只认「字符串字面量 + 标识符」的运行时拼接，或显式 MACHINE_SEGMENT 注释
MACHINE_CONCAT = re.compile(
    r'"(?:[^"\\]|\\.)*"\s*\+\s*[A-Za-z_$][\w$.]*'
    r'|"\s*\+\s*JSON\.stringify\s*\('
    r'|//\s*MACHINE_SEGMENT')
PROSE_STRING = re.compile(r'^\s*"(.*)"\s*,?\s*$')

# ★ 引述段收窄：不含【复核】/【核查】/【背景——（那是本任务的主张背景）
QUOTED_OPEN = re.compile(r"【被核对象】|【原文】|【逐条原说法】|CLAIMS\s*=\s*\[")
QUOTED_CLOSE = re.compile(r"【任务|【交付】|【纪律】|IRON|【编排方|【背景(?!——)")

# ★ 验收段优先级最高：出现在这些段里的行，即使被引述区包住也按验收段判
ACCEPTANCE = re.compile(
    r"【交付】|【必现要素】|【任务】|【复核】|【验收】|【结论模板】|"
    r"publishArtifact|conclusion:|description:")

# 全文级扫描：发布产物/结论/lint 可见的所有行（不局限 join 数组）
ARTIFACT_LINES = re.compile(r"publishArtifact|conclusion:|description:")

FENCE_OPEN = re.compile(r"^\s*```")
INLINE_CODE = re.compile(r"`[^`]*`")

RULES = {
    "BARE_ARABIC": "散文段出现阿拉伯裸数字（未走 {{N.id}}）",
    "BARE_CJK_NUMERAL": "散文段出现中文数字+量词",
    "AMBIGUOUS_SCOPE": "比率/倍数/件数缺 {分子,分母,条件} 或口径标签不在词表",
    "CROSS_DOMAIN_LEAK": "domain/artifact 与本轮 DIR 不一致",
    "DESIGN_EXPERIMENT_UNMARKED": "设计实验数值未标 DESIGN_ONLY",
    "DESIGN_EXPERIMENT_IN_ACCEPTANCE": "设计实验数值出现在验收段",
    "ESTIMATE_NOT_DEGRADED": "估算未渲染成「（估算，未实跑）」",
    "ESTIMATE_IN_ACCEPTANCE": "估算出现在验收/发布段",
    "UNRESOLVED_PLACEHOLDER": "{{N.id}} 在 CLAIM_NUMBERS 里查不到（不回显）",
    "NONCONFORMING_MUSTACHE": "出现非 {{N.*}} 形态的 {{...}}（不回显内容）",
    "BAD_SOURCE_KIND": "source_kind 不在受控词表",
    "MISSING_FIELDS": "source_kind 对应的必填字段缺失",
    "BAD_SHA256": "数字未绑定 64 位 sha256",
    "BAD_CLAIM_DIGEST": "sha256 与声明主体（含 value/证据）不匹配",
    "EVIDENCE_UNVERIFIED": "source_kind 的外部证据不闭合（实跑无 stdout / 文件行无当行 / 推导算不对）",
    "DANGLING_DEP": "推导 depends_on 指向不存在的 id",
    "STALE_NUMBER_SOURCE": "任务书未复贴当前数字源块哈希",
    "STALE_VERSION": "数字源 version 滞后",
    "BLOCK_HASH_MISMATCH": "数字源块哈希与 claims 不自洽",
    "HISTORY_CHAIN_BROKEN": "纠正 history 链被抹掉或断版",
    "PREV_SHA256_BROKEN": "prev_sha256 断链",
    "CLAIM_BLOCK_HASH_MISMATCH": "单条 source_block_sha256 与块哈希不一致",
    "CROSS_SECTION_VALUE_NOT_USED": "机器段贴了对值、散文段未引用",
    "UNRENDERED_MACHINE_SEGMENT": "静态 `+ IDENT` 拼接源码冒充已渲染全文",
    "UNPROVEN_ACCEPTANCE_NUMBER": "验收/发布段出现裸数字而该数字无已验证来源",
}

DESIGN_WORDS = ("Shim", "第二模块实例", "沙箱副本", "内存 Shim", "设计实验",
                "模拟输出", "shadow", "DESIGN_ONLY")

EXEMPT_PATTERNS = tuple(re.compile(r) for r in (
    r"[\w./\\-]+:\d+(?:-\d+)?",
    r"\b[0-9a-f]{12,64}\b",
    r"tail:\s*\d+",
    r"§\s*\d+(?:[.\-]\d+)*",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:R|V|C|D|A|B|E|F|H|N)-?\d+\b",
    r"\bdwfrun-[0-9a-f\-]{20,}",
    r"\b\d+\s*B\b",
    r"python\s+-I\s+-X\s+utf8",
    r"被核对象 SHA256\s*=\s*[0-9a-f]{64}",
    r"字节数\s*=\s*\d+",
    r"\b(?:exit|verdict|ok|HEAD|version)=\d*\b",
    r"(?<![A-Za-z0-9])20\d{2}(?![A-Za-z0-9])",
    r"\b[A-Za-z_][A-Za-z0-9_]*=\d+(?:\.\d+)?\b",
    r"(?<![A-Za-z0-9])0(?![A-Za-z0-9.])",
))
CJK_GRAMMATICAL = re.compile(
    r"(?:一个|一类|一样|一下|一点|一并|一度|一概|一旦|一两|"
    r"一件|两件|这件事|两件事|这两|那一|第一|第二|第三|"
    r"一回事|两回事|一者|二者|三者|两者|一方面|另一方面|"
    r"一来|二来|一时|一问|一答|一体)")
ARABIC = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?(?![A-Za-z0-9_])")
CJK_NUM = re.compile(r"[一二三四五六七八九十百千万零两]\s*"
                     r"(?:个|件|条|域|行|处|倍|层|分|项|次|组|份|轮|版|道|类|种)")


def mask_exempt(text: str) -> str:
    for p in EXEMPT_PATTERNS:
        text = p.sub(" ", text)
    return text


def classify_lines(ask_block: str) -> dict:
    """按结构分类：QUOTED 状态化；★ 无标题洗白；ACCEPTANCE 优先于 QUOTED。"""
    prose, machine, quoted, code = [], [], [], []
    in_fence = in_quoted = False
    for lineno, line in enumerate(ask_block.split("\n"), 1):
        if FENCE_OPEN.match(line):
            in_fence = not in_fence
            code.append((lineno, line))
            continue
        if in_fence:
            code.append((lineno, line))
            continue
        # ★ 验收段优先：即使被引述区包住，也作为散文/验收段处理
        if ACCEPTANCE.search(line):
            in_quoted = False
            pm = PROSE_STRING.match(line)
            body = INLINE_CODE.sub(" ", pm.group(1)) if pm else line
            prose.append((lineno, body))
            continue
        if QUOTED_OPEN.search(line):
            in_quoted = True
            quoted.append((lineno, line))
            continue
        if MACHINE_CONCAT.search(line):
            in_quoted = False
            machine.append((lineno, line))
            continue
        if in_quoted:
            if QUOTED_CLOSE.search(line):
                in_quoted = False
                pm = PROSE_STRING.match(line)
                if pm:
                    prose.append((lineno, INLINE_CODE.sub(" ", pm.group(1))))
                continue
            quoted.append((lineno, line))
            continue
        pm = PROSE_STRING.match(line)
        if pm:
            prose.append((lineno, INLINE_CODE.sub(" ", pm.group(1))))
    return {"prose": prose, "machine": machine, "quoted": quoted, "code": code}


def extract_all_join_blocks(txt: str) -> list[str]:
    """★ 抽全文所有 `const XXX = [ ... ].join` 数组，不只首个 ASK_ANALYST。"""
    return [m.group(1) for m in re.finditer(
        r"const\s+\w+\s*=\s*\[(.*?)\n\s*\]\.join", txt, re.S)]


def artifact_lines(txt: str) -> list[tuple[int, str]]:
    """★ 全文 publishArtifact / conclusion: / description: 行独立扫描。"""
    return [(i, l) for i, l in enumerate(txt.split("\n"), 1)
            if ARTIFACT_LINES.search(l)]


# ---------------------------------------------------------------------------
# 2. lint 主函数
# ---------------------------------------------------------------------------

def lint(taskbook_text: str, claim_numbers: list[dict], *, source: dict | None = None,
         dir_hint: str = "", root: str = ROOT, rendered: bool = False) -> dict:
    """taskbook_text = 任务书源码（或 ASK_ANALYST.join 后的渲染全文）。

    rendered=True 表示调用方已把运行时拼接展开；默认 False，见 `+ IDENT` 即 FAIL。
    """
    findings: list[dict] = []

    def add(rule: str, line: int, detail: str) -> None:
        findings.append({"rule": rule, "line": line, "detail": detail})

    # ★ 严格证据机核（旧版 strict=False 是全部 bypass 的根源）
    v = ncph.validate_claim_numbers(claim_numbers, strict=True, root=root)
    for p in v["problems"]:
        code = p.split(":")[1] if ":" in p else p
        # ★ 证据类子码保留具体规则，不笼统折叠成 EVIDENCE_UNVERIFIED
        if "DANGLING_DEP" in p:
            code = "DANGLING_DEP"
        elif code.startswith("EVIDENCE_UNVERIFIED"):
            code = "EVIDENCE_UNVERIFIED"
        add(code if code in RULES else "MISSING_FIELDS", 0, p)

    blocks = extract_all_join_blocks(taskbook_text)
    cls_all = {"prose": [], "machine": [], "quoted": [], "code": []}
    for bi, block in enumerate(blocks):
        cls = classify_lines(block)
        for k in cls_all:
            cls_all[k] += [(bi, ln, body) for ln, body in cls[k]]

    # R1/R2/R5-R8：散文段（含验收段）
    for bi, lineno, body in cls_all["prose"]:
        t = mask_exempt(body)
        if ARABIC.findall(t):
            add("BARE_ARABIC", lineno, "block=%d n=%d" %
                (bi, len(ARABIC.findall(t))))
        if CJK_NUM.findall(CJK_GRAMMATICAL.sub(" ", t)):
            add("BARE_CJK_NUMERAL", lineno, "block=%d" % bi)
        if any(w in body for w in DESIGN_WORDS) and "DESIGN_ONLY" not in body:
            add("DESIGN_EXPERIMENT_UNMARKED", lineno, "design word")
        if any(w in body for w in DESIGN_WORDS) and ACCEPTANCE.search(body):
            add("DESIGN_EXPERIMENT_IN_ACCEPTANCE", lineno, "design in acceptance")
        if "估算" in body and ncph.ESTIMATE_TAG not in body:
            add("ESTIMATE_NOT_DEGRADED", lineno, "估算 without tag")
        if ACCEPTANCE.search(body):
            # ★ 按解析后的 id 判估算；且验收段任何裸数字都须有已验证来源
            for cid in ncph.PLACEHOLDER.findall(body):
                c = v["by_id"].get(cid)
                if c and c.get("source_kind") == "估算":
                    add("ESTIMATE_IN_ACCEPTANCE", lineno, "estimate id in acceptance")
            if ncph.ESTIMATE_TAG in body:
                add("ESTIMATE_IN_ACCEPTANCE", lineno, "estimate tag in acceptance")
            if ARABIC.findall(mask_exempt(body)) and not v["ok"]:
                add("UNPROVEN_ACCEPTANCE_NUMBER", lineno, "bare number, evidence not closed")

    # R9/R10 占位符合法性（所有段；不回显 token）
    for k in ("prose", "machine", "quoted"):
        for bi, lineno, line in cls_all[k]:
            r = ncph.render(line, v["by_id"])
            for p in r["problems"]:
                add(p.split(":")[0] if p.split(":")[0] in RULES
                    else "UNRESOLVED_PLACEHOLDER", lineno, p)

    # ★ R-A：全文发布产物/结论行独立扫描（不是 PROSE_STRING 也能抓）
    for lineno, line in artifact_lines(taskbook_text):
        for cid in ncph.PLACEHOLDER.findall(line):
            c = v["by_id"].get(cid)
            if c and c.get("source_kind") == "估算":
                add("ESTIMATE_IN_ACCEPTANCE", lineno, "estimate in artifact metadata")
        if ncph.ESTIMATE_TAG in line:
            add("ESTIMATE_IN_ACCEPTANCE", lineno, "estimate tag in artifact metadata")
        if ARABIC.findall(mask_exempt(line)) and not v["ok"]:
            add("UNPROVEN_ACCEPTANCE_NUMBER", lineno, "artifact metadata bare number")

    # R3 比率/口径（附在已报裸数字的行上）
    bare = {f["line"] for f in findings if f["rule"] in ("BARE_ARABIC", "BARE_CJK_NUMERAL")}
    for bi, lineno, body in cls_all["prose"]:
        if lineno in bare and "口径" not in body and "{{N." not in body:
            add("AMBIGUOUS_SCOPE", lineno, "numeric without 口径 label")

    # R4 跨域
    if dir_hint:
        for cid, c in v["by_id"].items():
            if str(c.get("domain", "")) not in dir_hint and \
                    str(c.get("artifact", "")) not in dir_hint:
                add("CROSS_DOMAIN_LEAK", 0, "id=%s" % cid)

    # R-链：全链校验
    if source is not None:
        chk = ncph.check_chain(taskbook_text, source)
        if not chk["ok"]:
            add(chk["problem"] if chk["problem"] in RULES
                else "STALE_NUMBER_SOURCE", 0, "chain mismatch")

    # R16/R17 跨段 diff：★ 保留 UNRENDERED 规则码，不映射成 CROSS_SECTION
    machine_txt = "\n".join(x[2] for x in cls_all["machine"])
    prose_txt = "\n".join(x[2] for x in cls_all["prose"])
    diff = ncph.cross_section_diff(machine_txt, prose_txt, v, rendered=rendered)
    for p in diff["problems"]:
        add(p.split(":")[0], 0, p)

    return {"ok": not findings, "findings": findings,
            "summary": {
                "n_join_blocks": len(blocks),
                "prose_lines": len(cls_all["prose"]),
                "machine_lines": len(cls_all["machine"]),
                "quoted_lines": len(cls_all["quoted"]),
                "code_lines": len(cls_all["code"]),
                "artifact_lines": len(artifact_lines(taskbook_text)),
                "n_findings": len(findings),
                "by_rule": {r: sum(1 for f in findings if f["rule"] == r)
                            for r in sorted({f["rule"] for f in findings})},
                "block_sha256": v["block_sha256"],
            }}


def lint_draft(path: str) -> dict:
    """只读预检真实 .dwf.ts：全数组 + 发布行，无 CLAIM_NUMBERS -> 报全量裸数。"""
    txt = io.open(path, "r", encoding="utf-8", errors="replace").read()
    return lint(txt, [], rendered=False)


# ---------------------------------------------------------------------------
# 3. 自检（正例 5 / 反例 5 + 复核破口回归 + 真实损害行）
# ---------------------------------------------------------------------------

def _claims() -> list[dict]:
    return ncph.build_demo(ROOT)


def _src(claims):
    store = {"version": 1, "prev_sha256": "", "history": [],
             "claims": [dict(c) for c in claims], "block_sha256": "",
             "binding_line": ""}
    # 不落盘：直接按 chain_block_bytes 算
    store["block_sha256"] = hashlib.sha256(
        ncph.chain_block_bytes(store)).hexdigest()
    store["binding_line"] = ncph.binding_line(ncph.chain_block_bytes(store))
    for c in store["claims"]:
        c["source_block_sha256"] = store["block_sha256"]
    return store


def _hdr(claims):
    s = _src(claims)
    return "【数字源】version=1\n" + s["binding_line"], s


def selftest() -> dict:
    claims = _claims()
    hdr, src = _hdr(claims)
    rows = []

    def run(case, name, text, expect_ok, want=None, *, source=None,
            rendered=False):
        r = lint(text, claims, source=source, rendered=rendered)
        hit = sorted({f["rule"] for f in r["findings"]})
        ok = (r["ok"] is expect_ok) and (want is None or want in hit)
        rows.append({"case": case, "name": name, "expect_ok": expect_ok,
                     "want": want, "got_ok": r["ok"], "rules_hit": hit,
                     "pass": ok})
        return r

    # --- 正例 5 ---
    run("POS1", "占位符齐全无裸数",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】实测为 {{N.domains_nonempty}} 与 {{N.bindings_zero}}。",\n].join("\\n");\n',
        True, source=src)
    # POS2：机器段真拼接；给出「渲染后」的机器段（含实跑数值 token）才允许裸数。
    # 静态 `+ fpText` 无可见值 -> 由 REG6 专门判 UNRENDERED_MACHINE_SEGMENT。
    run("POS2", "机器段允许裸数（渲染后真拼接）",
        hdr + '\nconst ASK_ANALYST = [\n  "【编排方实跑指纹】" + fpText + " 13 域 6 域",\n  "【背景】沿用 {{N.domains_nonempty}} 与 {{N.bindings_zero}}。",\n].join("\\n");\n',
        True, source=src, rendered=True)
    run("POS3", "代码块内数字不报",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】见 `tail: 16384 与 13 域`；实测 {{N.domains_nonempty}}。",\n].join("\\n");\n',
        True, source=src)
    run("POS4", "引述段允许裸数（被核材料）",
        hdr + '\nconst ASK_ANALYST = [\n  "【被核对象】" + JSON.stringify(finding),\n  "  19. 「32768 倍」→ 心算成 16384。",\n  "【背景】正确值 {{N.ratio_32768}}。",\n].join("\\n");\n',
        True, source=src)
    run("POS5", "豁免形态不报",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】见 KEFF_CALC.md:110-112、§3.2、2026-11-09、R10、D-27；{{N.rho_threshold}}。",\n].join("\\n");\n',
        True, source=src)

    # --- 反例 5（任务书要求的 5 条） ---
    run("NEG1", "阿拉伯裸数字",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】实测 13 个域仍有门禁问题。",\n].join("\\n");\n',
        False, "BARE_ARABIC", source=src)
    run("NEG2", "中文数字+量词",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】十个域仍报问题，五个域 bindings=0。",\n].join("\\n");\n',
        False, "BARE_CJK_NUMERAL", source=src)
    run("NEG3", "估算进验收段",
        hdr + '\nconst ASK_ANALYST = [\n  "【交付】{{N.est_effort}} 的进度必须达成。",\n].join("\\n");\n',
        False, "ESTIMATE_IN_ACCEPTANCE", source=src)
    run("NEG4", "未解析占位符",
        hdr + '\nconst ASK_ANALYST = [\n  "【背景】实测为 {{N.no_such_id}}。",\n].join("\\n");\n',
        False, "UNRESOLVED_PLACEHOLDER", source=src)
    stale = {"block_sha256": "1" * 64, "version": 1, "prev_sha256": "",
             "history": [], "claims": _claims()}
    for c in stale["claims"]:
        c["source_block_sha256"] = stale["block_sha256"]
    r = lint("【数字源】version=1\n被核对象 SHA256 = " + "0" * 64 +
             "，字节数 = 1\nconst ASK_ANALYST = [\n  \"【背景】{{N.domains_nonempty}}。\",\n].join(\"\\n\");\n",
             claims, source=stale)
    hit = sorted({f["rule"] for f in r["findings"]})
    rows.append({"case": "NEG5", "name": "数字源哈希滞后", "expect_ok": False,
                 "want": "BLOCK_HASH_MISMATCH", "got_ok": r["ok"],
                 "rules_hit": hit,
                 "pass": r["ok"] is False and any(
                     h in hit for h in ("STALE_NUMBER_SOURCE", "BLOCK_HASH_MISMATCH"))})

    # --- 复核破口回归（★ 8 条，全部必须被拦） ---
    regressions = [
        ("REG1", "P1 标题洗白",
         hdr + '\nconst ASK_ANALYST = [\n  "【编排方实跑指纹】实测 7 个域、3 处问题。",\n].join("\\n");\n',
         False, "BARE_ARABIC"),
        ("REG2", "P2 【复核】估算（引述优先）",
         hdr + '\nconst ASK_ANALYST = [\n  "【复核】{{N.est_effort}} 必须达成。",\n].join("\\n");\n',
         False, "ESTIMATE_IN_ACCEPTANCE"),
        ("REG3", "P3 publishArtifact 估算",
         hdr + '\n  await __host.publishArtifact("a", "file", ["x", { description: "{{N.est_effort}} 个域" }]);\n',
         False, "ESTIMATE_IN_ACCEPTANCE"),
        ("REG4", "A7 conclusion 估算",
         hdr + '\n  conclusion: "完成 {{N.est_effort}} 个域",\n',
         False, "ESTIMATE_IN_ACCEPTANCE"),
        ("REG5", "错值标实跑无证据",
         hdr + '\nconst ASK_ANALYST = [\n  "【背景】实测 {{N.bogus_run}}。",\n].join("\\n");\n',
         False, "EVIDENCE_UNVERIFIED"),
        ("REG6", "静态 +vfText 假报通过",
         hdr + '\nconst ASK_ANALYST = [\n  "【复核数据】" + vfText,\n  "【背景】{{N.ratio_32768}}。",\n].join("\\n");\n',
         False, "UNRENDERED_MACHINE_SEGMENT"),
        ("REG7", "未知 mustache 不回显",
         hdr + '\nconst ASK_ANALYST = [\n  "【背景】{{NAME_INJECT}} 与 {{N.domains_nonempty}}。",\n].join("\\n");\n',
         False, "NONCONFORMING_MUSTACHE"),
        ("REG8", "历史链被抹掉",
         hdr + '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n',
         False, "HISTORY_CHAIN_BROKEN"),
    ]
    for case, name, text, exp, want in regressions:
        if case == "REG5":
            bogus = dict(claims[0])
            bogus["id"] = "bogus_run"
            bogus["value"] = 10
            bogus["stdout_path"] = "no/such/stdout.txt"
            bogus = ncph.seal_claim(bogus)
            r = lint(text, claims + [bogus], source=None)
            hit = sorted({f["rule"] for f in r["findings"]})
            rows.append({"case": case, "name": name, "expect_ok": exp,
                         "want": want, "got_ok": r["ok"], "rules_hit": hit,
                         "pass": r["ok"] is False and want in hit})
            continue
        if case == "REG8":
            bad = {"version": 3, "prev_sha256": "0" * 64, "history": [],
                   "block_sha256": src["block_sha256"],
                   "claims": [dict(c) for c in claims]}
            for c in bad["claims"]:
                c["source_block_sha256"] = bad["block_sha256"]
            # 复贴 version=3 与当前块哈希，但抹掉两条 history -> 必须报断链
            text3 = text.replace("version=1", "version=3")
            r = lint(text3, claims, source=bad)
            hit = sorted({f["rule"] for f in r["findings"]})
            rows.append({"case": case, "name": name, "expect_ok": exp,
                         "want": want, "got_ok": r["ok"], "rules_hit": hit,
                         "pass": r["ok"] is False and want in hit})
            continue
        run(case, name, text, exp, want, source=src,
            rendered=(case == "REG6"))

    # --- 5 条真实损害行（868215ce lowered:98/110/170/217/226） ---
    real = [
        ("lowered:98", '"  36 处门禁位点改造…**10 个域仍有门禁问题，5 个域 bindings=0**。",'),
        ("lowered:110", '"【任务：对 10 个仍报问题的域做逐域真伪判定】",'),
        ("lowered:170", '"【交付】写 GATE_REJUDGE_32.md … 5 个 bind=0 域逐个定性 …",'),
        ("lowered:217", 'await __host.publishArtifact("artifact#1", "file", [ … description: "10 个仍报问题的域逐个判真伪…" …]);'),
        ("lowered:226", 'conclusion: "… 十个域：" + finding.tenDomains + …'),
    ]
    real_rows = []
    for tag, line in real:
        tb = hdr + "\nconst ASK_ANALYST = [\n" + line + "\n].join(\"\\n\");\n"
        r = lint(tb, claims, source=src)
        real_rows.append({"line": tag, "ok": r["ok"],
                          "A_catches": "UNPROVEN_ACCEPTANCE_NUMBER" in
                                       {f["rule"] for f in r["findings"]}
                                       or "BARE_ARABIC" in {f["rule"] for f in r["findings"]}
                                       or "BARE_CJK_NUMERAL" in {f["rule"] for f in r["findings"]},
                          "rules_hit": sorted({f["rule"] for f in r["findings"]})})

    return {"n": len(rows), "n_pass": sum(1 for x in rows if x["pass"]),
            "rows": rows, "real_damage_lines": real_rows,
            "n_real_caught": sum(1 for x in real_rows if x["A_catches"])}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        out = lint_draft(sys.argv[1])
        out["draft"] = sys.argv[1]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(selftest(), ensure_ascii=False, indent=2))
