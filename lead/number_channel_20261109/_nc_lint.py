# -*- coding: utf-8 -*-
"""_nc_lint.py —— 派发前 lint 的可粘贴实现。

用法:
    python -I -X utf8 <本文件绝对路径>                      # 跑 5 正例 / 5 反例自检
    python -I -X utf8 <本文件绝对路径> <draft.dwf.ts>       # 真实草稿预检（只读）

零真机、零采样代码。不改任何既有件。
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys

import importlib.util

# 从同目录加载占位符模块（绝对路径，避免 cwd 劫持）
_DIR = r"D:\Project\ra2-campaign-forge\lead\number_channel_20261109"
_spec = importlib.util.spec_from_file_location(
    "ncph", _DIR + r"\_nc_placeholder.py")
ncph = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ncph)

# ---------------------------------------------------------------------------
# 1. 段落判定：散文段 vs 机器段（不靠自觉，靠结构 + 生成方式）
# ---------------------------------------------------------------------------

# 判定优先级（先匹配先定）：
#   (A) 机器段：数组元素以 `"..." + <标识符>` 拼接运行时 stdout / JSON.stringify
#       -> 该段内容由 world.run 生成，允许裸数字。
#   (B) 引述段：显式标记 QUOTED（被核对象 / CLAIMS / 原文），数字是材料不是主张，
#       允许裸数字，但不参与跨段 diff。
#   (C) 散文段：纯字符串字面量（无 `+` 拼接），一律禁裸数字。
#   (D) 代码块：``` 围栏 / 行内 `...` 内的数字不报（误报控制）。
#
# 关键：判定依据是**该行是不是运行时拼接**，不是「看起来像不像背景」。
# 编排方不能靠改标题把散文段洗成机器段；要标机器段必须用 `+ fpText` 形式。

MACHINE_CONCAT = re.compile(
    r'^\s*"[^"]*"\s*\+\s*[A-Za-z_$][\w$.]*'
    r'|^\s*"[^"]*"\s*\+\s*JSON\.stringify\(')
PROSE_STRING = re.compile(r'^\s*"(.*)"\s*,?\s*$')
QUOTED_OPEN = re.compile(r"【被核对象】|【核查】|【原文】|【背景——|"
                         r"CLAIMS\s*=\s*\[|【逐条原说法】|【复核】|【核查】")
QUOTED_CLOSE = re.compile(r"【背景(?!——)|【任务|【交付】|【纪律】|IRON|"
                          r"【编排方|【复核数据】|【实跑结果】")
MACHINE_MARK = re.compile(
    r"【编排方实跑指纹】|【编排方指纹】|【复核数据】|【编排方实跑】|"
    r"【实跑结果】|【双轨重判】|CLAIM_NUMBERS|被核对象 SHA256 = ")
FENCE_OPEN = re.compile(r"^\s*```")
INLINE_CODE = re.compile(r"`[^`]*`")

# 验收段：估算禁入（且裸数字零容忍）
ACCEPTANCE = re.compile(r"【交付】|【必现要素】|【任务】|【复核】|【验收】|"
                        r"【结论模板】|publishArtifact|conclusion:")


def classify_lines(ask_block: str) -> dict:
    """把 ASK_ANALYST 数组内容按行分类，返回 {prose, machine, quoted, code}。

    ★ 状态化：QUOTED_OPEN 到 QUOTED_CLOSE 之间的**整段**（含 "1. ..." 编号行）
    都算引述段，不只看打开标记那一行。这是「不靠自觉」的关键——编排方
    不能把被核错值写成下一行就绕开。
    """
    prose, machine, quoted, code = [], [], [], []
    in_fence = False
    in_quoted = False
    for lineno, line in enumerate(ask_block.split("\n"), 1):
        if FENCE_OPEN.match(line):
            in_fence = not in_fence
            code.append((lineno, line))
            continue
        if in_fence:
            code.append((lineno, line))
            continue
        # 引述段打开标记优先于运行时拼接：
        # `"【被核对象】" + JSON.stringify(finding)` 既是拼接也是引述开头，
        # 必须按「打开引述区」处理，否则后续编号行会被误判成散文裸数。
        if QUOTED_OPEN.search(line):
            in_quoted = True
            quoted.append((lineno, line))
            continue
        if MACHINE_CONCAT.search(line) or MACHINE_MARK.search(line):
            in_quoted = False
            machine.append((lineno, line))
            continue
        if in_quoted:
            if QUOTED_CLOSE.search(line):
                in_quoted = False
                # 关闭标记所在行按散文处理（通常是【任务】/【交付】）
            else:
                quoted.append((lineno, line))
                continue
        m = PROSE_STRING.match(line)
        if m:
            # 行内代码先摘掉；剩余部分才算散文
            body = INLINE_CODE.sub(" ", m.group(1))
            prose.append((lineno, body))
    return {"prose": prose, "machine": machine, "quoted": quoted, "code": code}


# ---------------------------------------------------------------------------
# 2. lint 规则（逐条列，对应任务书第三步 (a)）
# ---------------------------------------------------------------------------

RULES = {
    "BARE_ARABIC": "散文段出现阿拉伯裸数字（未走 {{N.id}}）",
    "BARE_CJK_NUMERAL": "散文段出现中文数字+量词（十个域 / 四条问题 / 三层连乘）",
    "AMBIGUOUS_SCOPE": "比率/倍数/件数/域数无 {分子,分母,条件} 三元组或口径标签不在受控词表",
    "CROSS_DOMAIN_LEAK": "数字的 domain/artifact 与本轮 DIR 不一致（拿相邻域的数填空）",
    "DESIGN_EXPERIMENT_UNMARKED": "Shim/第二模块实例/沙箱副本/设计实验数值未标 DESIGN_ONLY",
    "DESIGN_EXPERIMENT_IN_ACCEPTANCE": "设计实验数值出现在验收段或与实跑数字同表",
    "ESTIMATE_NOT_DEGRADED": "估算未渲染成「（估算，未实跑）」",
    "ESTIMATE_IN_ACCEPTANCE": "估算出现在【交付】/【必现要素】/【任务】/【复核】/结论模板",
    "UNRESOLVED_PLACEHOLDER": "{{N.id}} 在 CLAIM_NUMBERS 里查不到（不回显 token 内容）",
    "NONCONFORMING_MUSTACHE": "出现非 {{N.*}} 形态的 {{...}}（未知占位符 / 投放伪值）",
    "BAD_SOURCE_KIND": "source_kind 不在受控词表 实跑/文件行/估算/推导",
    "MISSING_FIELDS": "source_kind 对应的必填字段缺失",
    "BAD_SHA256": "数字未绑定 64 位 sha256",
    "STALE_NUMBER_SOURCE": "任务书未复贴当前数字源块哈希（纠正没回写）",
    "STALE_VERSION": "任务书数字源 version 滞后",
    "CROSS_SECTION_VALUE_NOT_USED": "机器段贴了对值，散文段未引用（贴了≠用了）",
    "DANGLING_DEP": "推导的 depends_on 指向不存在的 id",
}

# 设计实验词（拦 #6 / #17）
DESIGN_WORDS = ("Shim", "第二模块实例", "沙箱副本", "内存 Shim", "设计实验",
                "模拟输出", "shadow", "DESIGN_ONLY")

# 豁免白名单（数字在代码块里不报；以下形态在散文里也不报）
EXEMPT_PATTERNS = tuple(re.compile(r) for r in (
    r"[\w./\\-]+:\d+(?:-\d+)?",          # path:line / :22 / KEFF_CALC.md:110-112
    r"\b[0-9a-f]{12,64}\b",               # SHA256 片段
    r"tail:\s*\d+",                        # output.tail 字节上限
    r"§\s*\d+(?:[.\-]\d+)*",              # 小节号（含 §3.2）
    r"\b\d{4}-\d{2}-\d{2}\b",             # 日期
    r"\b(?:R|V|C|D|A|B|E|F|H|N)-?\d+\b",  # R10 / D-27 / N13 / V12（整 token 吃掉）
    r"\bdwfrun-[0-9a-f\-]{20,}",          # run id
    r"\b\d+\s*B\b",                        # 字节数
    r"python\s+-I\s+-X\s+utf8",           # 铁律命令
    r"被核对象 SHA256\s*=\s*[0-9a-f]{64}",  # 绑定行（连哈希一起吃掉）
    r"字节数\s*=\s*\d+",                  # 绑定行的字节数
    r"\b(?:exit|verdict|ok|HEAD|version)=\d*\b",  # 常量名
    r"(?<![A-Za-z0-9])20\d{2}(?![A-Za-z0-9])",   # 孤立年份兜底
    r"\b[A-Za-z_][A-Za-z0-9_]*=\d+(?:\.\d+)?\b",  # 常量赋值 bindings=0 / tail=16384
    r"(?<![A-Za-z0-9])0(?![A-Za-z0-9.])",        # 孤立 0（布尔/空值语义，非计数主张）
))
# 中文数字的**语法性**用法（非计数主张），不报：
# 一个/一类/两件/第一/第二/一下/一点/一回事/两回事/三者/两者
CJK_GRAMMATICAL = re.compile(
    r"(?:一个|一类|一样|一下|一点|一并|一度|一概|一旦|一两|"
    r"一件|两件|这件事|两件事|这两|那一|第一|第二|第三|"
    r"一回事|两回事|一者|二者|三者|两者|一方面|另一方面|"
    r"一来|二来|一时|一问|一答|一体|一并)")


def mask_exempt(text: str) -> str:
    for p in EXEMPT_PATTERNS:
        text = p.sub(" ", text)
    return text


ARABIC = re.compile(r"(?<![A-Za-z0-9_])\d+(?:\.\d+)?(?![A-Za-z0-9_])")
CJK_NUM = re.compile(r"[一二三四五六七八九十百千万零两]\s*"
                     r"(?:个|件|条|域|行|处|倍|层|分|项|次|组|份|轮|版|道|类|种)")


# ---------------------------------------------------------------------------
# 3. lint 主函数
# ---------------------------------------------------------------------------

def lint(ask_block: str, claim_numbers: list[dict],
         *, source: dict | None = None, dir_hint: str = "") -> dict:
    """返回 {ok, findings:[{rule,line,detail}], summary}。"""
    findings: list[dict] = []

    def add(rule: str, line: int, detail: str) -> None:
        findings.append({"rule": rule, "line": line, "detail": detail})

    cls = classify_lines(ask_block)
    v = ncph.validate_claim_numbers(claim_numbers, strict=False)
    for p in v["problems"]:
        rule = p.split(":")[1] if ":" in p else "MISSING_FIELDS"
        add(rule if rule in RULES else "MISSING_FIELDS", 0, p)

    # R1/R2 散文段裸数字 + 中文数字
    for lineno, body in cls["prose"]:
        t = mask_exempt(body)
        n_ar = len(ARABIC.findall(t))
        # 语法性中文数字（一个/一类/两件/第一步…）不算计数主张
        t_cjk = CJK_GRAMMATICAL.sub(" ", t)
        n_cjk = len(CJK_NUM.findall(t_cjk))
        if n_ar:
            add("BARE_ARABIC", lineno, "n=%d" % n_ar)
        if n_cjk:
            add("BARE_CJK_NUMERAL", lineno, "n=%d" % n_cjk)
        # R5/R6 设计实验标色
        if any(w in body for w in DESIGN_WORDS) and "DESIGN_ONLY" not in body:
            add("DESIGN_EXPERIMENT_UNMARKED", lineno, "design word present")
        if any(w in body for w in DESIGN_WORDS) and ACCEPTANCE.search(body):
            add("DESIGN_EXPERIMENT_IN_ACCEPTANCE", lineno, "design word in acceptance")
        # R7/R8 估算：按**解析后的 id**判，不靠字面 tag（占位符里没有 tag）
        if "估算" in body and ncph.ESTIMATE_TAG not in body:
            add("ESTIMATE_NOT_DEGRADED", lineno, "估算 without tag")
        if ACCEPTANCE.search(body):
            for cid in ncph.PLACEHOLDER.findall(body):
                c = v["by_id"].get(cid)
                if c and c.get("source_kind") == "估算":
                    add("ESTIMATE_IN_ACCEPTANCE", lineno,
                        "estimate id in acceptance segment")
            if ncph.ESTIMATE_TAG in body:
                add("ESTIMATE_IN_ACCEPTANCE", lineno, "estimate tag in acceptance")

    # R9/R10 占位符合法性（所有段，含机器段；不回显 token 内容）
    for kind in ("prose", "machine", "quoted"):
        for lineno, line in cls[kind]:
            r = ncph.render(line, v["by_id"])
            for p in r["problems"]:
                rule = p.split(":")[0]
                add(rule if rule in RULES else "UNRESOLVED_PLACEHOLDER", lineno, p)

    # R3 比率/口径：validate 已覆盖三元组；这里额外查散文里的「倍数/率」是否带口径标签。
    # 只在**已报裸数字**的行上附属报，避免与 BARE_* 重复计数、也避免对纯结构行误报。
    bare_lines = {f["line"] for f in findings
                  if f["rule"] in ("BARE_ARABIC", "BARE_CJK_NUMERAL")}
    for lineno, body in cls["prose"]:
        if lineno in bare_lines and "口径" not in body and "{{N." not in body:
            add("AMBIGUOUS_SCOPE", lineno, "numeric without 口径 label")

    # R4 跨域串台
    if dir_hint:
        for cid, c in v["by_id"].items():
            art = str(c.get("artifact", ""))
            dom = str(c.get("domain", ""))
            if art and dom and dom not in dir_hint and art not in dir_hint:
                add("CROSS_DOMAIN_LEAK", 0, "id=%s domain=%s" % (cid, dom))

    # R14/R15 数字源链
    if source is not None:
        chk = ncph.check_chain(ask_block, source)
        if not chk["ok"]:
            add(chk["problem"], 0, "chain mismatch")

    # R16 跨段 diff（机器段贴了值、散文段没引用）
    machine_txt = "\n".join(x[1] for x in cls["machine"])
    prose_txt = "\n".join(x[1] for x in cls["prose"])
    diff = ncph.cross_section_diff(machine_txt, prose_txt, v)
    for p in diff["problems"]:
        add("CROSS_SECTION_VALUE_NOT_USED", 0, p)

    return {
        "ok": not findings,
        "findings": findings,
        "summary": {
            "prose_lines": len(cls["prose"]),
            "machine_lines": len(cls["machine"]),
            "quoted_lines": len(cls["quoted"]),
            "code_lines": len(cls["code"]),
            "n_findings": len(findings),
            "by_rule": {r: sum(1 for f in findings if f["rule"] == r)
                        for r in sorted({f["rule"] for f in findings})},
            "block_sha256": v["block_sha256"],
        },
    }


def lint_draft(path: str) -> dict:
    """只读预检真实 .dwf.ts：抽 ASK_ANALYST 块，无 CLAIM_NUMBERS -> 报全量裸数。"""
    txt = io.open(path, "r", encoding="utf-8", errors="replace").read()
    m = re.search(r"const\s+ASK_ANALYST\s*=\s*\[(.*?)\n\s*\]\.join", txt, re.S)
    block = m.group(1) if m else ""
    # 历史草稿没有 CLAIM_NUMBERS：用空表，仍可测裸数字密度（预期 FAIL）
    return lint(block, [], dir_hint="")


# ---------------------------------------------------------------------------
# 4. 自检样本：正例 5 / 反例 5
# ---------------------------------------------------------------------------

def _claims():
    return ncph._demo_claims()


def _good(idx: int) -> tuple[str, str, list, dict | None]:
    """正例：应 ok=true。"""
    src = {"block_sha256": "", "version": 1,
           "claims": _claims()}
    src["block_sha256"] = hashlib.sha256(
        ncph.canonical_bytes(src["claims"])).hexdigest()
    hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(src["claims"]))
    cases = [
        ("占位符齐全无裸数",
         hdr + '\n  "【背景】实测为 {{N.domains_nonempty}} 与 {{N.bindings_zero}}。",\n'),
        ("机器段允许裸数",
         hdr + '\n  "【编排方实跑指纹】" + fpText,\n'
         '  "【背景】沿用 {{N.domains_nonempty}}。",\n'),
        ("代码块内数字不报",
         hdr + '\n  "【背景】判据见 `for bad in [...]: if tail: 16384 in t: P(13 域)`, 实测 {{N.domains_nonempty}}。",\n'),
        ("引述段允许裸数",
         hdr + '\n  "【被核对象】" + JSON.stringify(finding),\n'
         '  "  19. 「族级/全单元 = 32768 倍」→ 心算成 16384。",\n'
         '  "【背景】正确值 {{N.ratio_32768}}。",\n'),
        ("豁免形态不报",
         hdr + '\n  "【背景】见 KEFF_CALC.md:110-112、§3.2、2026-11-09、R10、D-27；实测 {{N.rho_threshold}}。",\n'),
    ]
    return cases[idx][0], cases[idx][1], _claims(), src


def _bad(idx: int) -> tuple[str, str, list, dict | None]:
    """反例：应 ok=false 且命中预期规则。"""
    src = {"block_sha256": "", "version": 1, "claims": _claims()}
    src["block_sha256"] = hashlib.sha256(
        ncph.canonical_bytes(src["claims"])).hexdigest()
    hdr = "【数字源】version=1\n" + ncph.binding_line(ncph.canonical_bytes(src["claims"]))
    cases = [
        ("阿拉伯裸数字", "BARE_ARABIC",
         hdr + '\n  "【背景】实测 13 个域仍有门禁问题。",\n'),
        ("中文数字+量词", "BARE_CJK_NUMERAL",
         hdr + '\n  "【背景】十个域仍报问题，五个域 bindings=0。",\n'),
        ("估算进验收段", "ESTIMATE_IN_ACCEPTANCE",
         hdr + '\n  "【交付】{{N.est_effort}} 的进度必须达成。",\n'),
        ("未解析占位符", "UNRESOLVED_PLACEHOLDER",
         hdr + '\n  "【背景】实测为 {{N.no_such_id}}。",\n'),
        ("数字源哈希滞后", "STALE_NUMBER_SOURCE",
         '【数字源】version=1\n被核对象 SHA256 = ' + "0" * 64 + '，字节数 = 1\n'
         '  "【背景】实测 {{N.domains_nonempty}}。",\n'),
    ]
    name, rule, text = cases[idx]
    # 前 4 例需要完整 claims；第 5 例需要错误的 source
    s = src
    if rule == "STALE_NUMBER_SOURCE":
        s = {"block_sha256": "1" * 64, "version": 1, "claims": _claims()}
    return name, text, _claims(), s, rule


def selftest() -> dict:
    rows = []
    for i in range(5):
        name, block, claims, src = _good(i)
        r = lint(block, claims, source=src)
        rows.append({"case": "POS%d" % (i + 1), "name": name,
                     "expect": "ok", "got_ok": r["ok"],
                     "pass": r["ok"] is True,
                     "findings": r["findings"][:4],
                     "summary": r["summary"]})
    for i in range(5):
        name, block, claims, src, want = _bad(i)
        r = lint(block, claims, source=src)
        hit = [f["rule"] for f in r["findings"]]
        rows.append({"case": "NEG%d" % (i + 1), "name": name,
                     "expect": "fail:" + want, "got_ok": r["ok"],
                     "pass": (r["ok"] is False and want in hit),
                     "rules_hit": hit[:8],
                     "summary": r["summary"]})
    return {"n": len(rows), "n_pass": sum(1 for x in rows if x["pass"]),
            "rows": rows}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        out = lint_draft(sys.argv[1])
        out["draft"] = sys.argv[1]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(selftest(), ensure_ascii=False, indent=2))
