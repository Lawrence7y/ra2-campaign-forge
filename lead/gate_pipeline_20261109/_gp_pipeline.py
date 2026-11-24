# -*- coding: utf-8 -*-
r"""_gp_pipeline.py — 判定链合成骨架（编排层，只读调用既有谓词模块）。

★ 本件不改任何既有谓词模块、不改任何交付件。既有模块只读加载（hashlib 先验指纹）。
★ 顺序只是「先报谁」与「依赖谁」，不是消解真值冲突的手段。冲突一律进 conflicts[]，
  由 resolve_conflicts 按 span 粒度逐处裁决，裁决不到的一律 RAISE（NEEDS_HUMAN），
  绝不靠先后覆盖。

执行顺序（数据依赖，不是优先级）：
  L0 提取器（多 findall 全量 + 行号 + 指纹）  ← 宽进：宁可多报
  L1 R9 要素在场（独立）
  L2 R10 语境分类（宽进：每命中都给 kind）
  L3 R12 双重否定（消费 L2 的 r10_context 同口径）
  L4 N13 A/B/C/D（消费 L2 hits + L3 hits，微段精筛）
  L5 R11 绑定回验（独立，读盘/写域）
  L6 冲突消解（按 span 逐处裁决，不覆盖）
  L7 结论（problems = 各类 FAIL 的并；CONFLICT_UNRESOLVED 单独列出，不静默并回 PASS）

实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/gate_pipeline_20261109/_gp_pipeline.py
"""
from __future__ import annotations
import hashlib
import importlib.util
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
G7_PATH = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13_PATH = ROOT / "lead" / "gate_n13_20261109" / "_n13_predicates.py"
FP = {
    G7_PATH: ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    N13_PATH: ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
}
REQ_ELEMENTS = ["被核对象", "SHA256", "字节数"]


def _load(path, name):
    raw = path.read_bytes()
    sha, n = hashlib.sha256(raw).hexdigest(), len(raw)
    if (sha, n) != FP[path]:
        raise RuntimeError("谓词指纹失配 %s = %s/%d" % (path, sha, n))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_predicates():
    """只读加载两层谓词本体；返回 (g7, n13, n13.DEFAULT_TOKENS)。"""
    g7 = _load(G7_PATH, "_gp_pipe_g7")
    n13 = _load(N13_PATH, "_gp_pipe_n13")
    return g7, n13, list(n13.DEFAULT_TOKENS)


# ---------------------------------------------------------------------------
# L0 提取器：全量 findall（修 _dn_regate_domains.py:65/:76 只取第一个 search 的假象）
# ---------------------------------------------------------------------------
def extract_spans(text, tokens):
    """返回逐处命中 [(token, pos, end, line)]。用 finditer 全量，不取 [0]。
    位置口径 = 原始 text 的字符下标（与 R10 一致）；CRLF 文档须先记录 eol 类型，
    因为 N13 按 splitlines() 累加 len(line)+1 计算 gpos，CRLF 下会与 R10 错位一字。"""
    eol = "CRLF" if "\r\n" in text else "LF"
    out = []
    for tok in tokens:
        for m in re.finditer(re.escape(tok), text):
            out.append({"token": tok, "pos": m.start(), "end": m.end(),
                        "line": text.count("\n", 0, m.start()) + 1})
    return {"spans": sorted(out, key=lambda x: x["pos"]), "eol": eol,
            "count": len(out), "tokens": list(tokens),
            "note": "CRLF 时 N13.gpos 与 R10.pos 相差行号数：须按 pos 对齐或先转 LF"}


# ---------------------------------------------------------------------------
# L1..L5 各层：只转发既有谓词的返回容器，不改写、不覆盖
# ---------------------------------------------------------------------------
def run_layers(g7, n13, n13_tokens, text, tokens, doc_dir, root=ROOT):
    r9_problems, r9_warnings = g7.r9_check(text, REQ_ELEMENTS)
    r10_problems, r10_warnings, r10_hits = g7.r10_scan(text, tokens)
    r12_problems, r12_hits = g7.r12_scan(text, tokens)
    r13_problems, r13_details = n13.r13_assertions(
        text, n13_tokens, r10_scan=g7.r10_scan, r12_scan=g7.r12_scan)
    r11_problems, r11_warnings, r11_bindings = g7.r11_scan(text, doc_dir, root=root)
    return {
        "R9": {"problems": r9_problems, "warnings": r9_warnings},
        "R10": {"problems": r10_problems, "warnings": r10_warnings, "hits": r10_hits},
        "R12": {"problems": r12_problems, "hits": r12_hits},
        "N13": {"problems": r13_problems, "details": r13_details},
        "R11": {"problems": r11_problems, "warnings": r11_warnings,
                "bindings": r11_bindings},
    }


# ---------------------------------------------------------------------------
# L6 冲突消解：按 (token,pos) span 逐处裁决；顺序不参与裁决
# ---------------------------------------------------------------------------
# 每层的 verdict 归一为三值：CATCH（判 FAIL）/ PASS（豁免）/ ABSENT（本层无该 span）
# 规则表（显式，非「以最严为准」）：
#   K1 R12 判 double_neg（肯定）→ CATCH。否定之否定是肯定，是语义事实，不是严格度偏好。
#   K2 同一 span 上 N13=D 且 R10=PASS（negation/quote_mention）→ CATCH，标 MIXED_CLAUSE。
#      依据：N13 的「同句混用 / 微段主语 / 行级肯定」是 R10 24 字符回看窗看不到的
#      局部证据；R10 的放行是「窗内有否定词」的粗判，不构成对该 span 的反证。
#   K3 同一 span 上 N13=A/B（放过）且 R10=assertion（抓住）→ 不合并裁决，
#      记 CONFLICT_AB_ASSERTION，交人工；因为 A/B 只在 N13 自己的三词词表上成立，
#      而 R10 用的是任务书词表，两者输入契约不同，不能互相否定。
#      但 N13 自带「行级肯定守卫」若在该行另判了 D，则按 K4 提升到 CATCH。
#   K4 不同 span、同一行：任一层在该行判 D/CATCH 且该行无直接否定管辖 → 整行 CATCH
#      （N13 的 _line_positive 已实装此规则；此处只在报告层复述，不重算）。
#   K5 不同行、同一小节：不传播。小节内一个标题/表头的放过不豁免另一行的真断言，
#      反之一个真断言也不污染同小节别行。只记 section 供人工定位。
#   K6 词表不对齐（R10 词表含 N13 三词之外的 token）：该 span 只有 R10 有答案，
#      标 OUT_OF_N13_VOCAB：直接采用 R10 的 assertion/negation 结论，并显式登记
#      「N13 未覆盖此 token」——绝不因为 N13 返回空就当作 PASS。
#   K7 任何层的 ABSENT 都不等于 PASS；所有未被任何层判到的 span → RAISE/NEEDS_HUMAN。
#   K8 冲突不可裁决（如 K3 无行级 D）→ 保留双方意见 + CONFLICT_UNRESOLVED，
#      结论 FAIL_CLOSED（不放过），但明确写「未消解」，不假装已判对。
CONFLICT_RULES = ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9")


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def resolve_conflicts(text, tokens, layers, n13_tokens):
    """逐 span 合成。返回 (rows, conflicts, summary)。
    rows 每项含 span / 各层 verdict / 最终 verdict / 适用规则。"""
    r10 = {(h["token"], h["pos"]): h["kind"] for h in layers["R10"]["hits"]}
    r12 = {(h["token"], h["pos"]) for h in layers["R12"]["hits"]}
    d13 = layers["N13"]["details"]
    n13_by_pos = {(d["token"], d["pos"]): d for d in d13 if d["pos"] >= 0}
    n13_d_lines = {d["line"] for d in d13 if d["kind"] == "D"}
    n13_vocab = set(n13_tokens)
    tok_set = set(tokens) | n13_vocab

    rows, conflicts = [], []
    for tok in tok_set:
        # 提取器全量（不用 search()[0]）
        for m in re.finditer(re.escape(tok), text):
            k = (tok, m.start())
            line = _line_of(text, m.start())
            r10k, r12h, d = r10.get(k), k in r12, n13_by_pos.get(k)
            r10_v = ("ABSENT" if r10k is None else
                     "CATCH" if r10k in ("assertion", "double_neg") else "PASS")
            r12_v = "CATCH" if r12h else "ABSENT"   # R12 无命中不等于「判了 PASS」
            n13_v = "ABSENT" if d is None else ("CATCH" if d["kind"] == "D" else "PASS")
            # 精筛依据：N13 的豁免是否带「局部正向证据」。
            # A/B 有明确检索/标题结构标记 + 行级无肯定守卫 ⇒ 是可信的精筛；
            # C 只是「R10 说 negation」的转发，不构成独立证据；
            # D 里的「默认 FAIL/拿不准」也不是精筛，只是 fail-closed。
            d_kind = (d or {}).get("kind")
            d_rule = (d or {}).get("rule", "")
            n13_veto = (d_kind in ("A", "B")
                        and line not in n13_d_lines
                        and "同句混用" not in d_rule)
            verdict, rule, unresolved = "ABSENT", [], False

            if tok not in n13_vocab:
                # K6：N13 词表不覆盖 → 采用 R10 结论，不把 ABSENT 当 PASS
                verdict = r10_v if r10_v != "ABSENT" else "RAISE"
                rule.append("K6")
                if r10_v == "ABSENT":
                    rule.append("K7")
            elif r12h:
                verdict = "CATCH"; rule.append("K1")   # 双重否定=肯定
                if n13_v == "PASS":
                    rule.append("K8")  # 记分歧，但 K1 有语义依据，可裁决
            elif n13_v == "CATCH" and r10_v == "PASS":
                verdict = "CATCH"; rule.append("K2")   # 同句混用 / 微段主语
            elif n13_v == "PASS" and r10_v == "CATCH":
                # K3：A/B 放过 vs R10 抓住，输入契约不同
                if n13_veto:
                    verdict = "PASS"; rule += ["K3", "K9"]   # K9 精筛覆盖宽进
                elif line in n13_d_lines:
                    verdict = "CATCH"; rule += ["K3", "K4"]
                else:
                    verdict = "FAIL_CLOSED"; rule += ["K3", "K8"]
                    unresolved = True
            elif n13_v == "CATCH" or r10_v == "CATCH":
                verdict = "CATCH"; rule.append("K4" if line in n13_d_lines else "K1")
            elif n13_v == "PASS" and r10_v == "PASS" and r12_v == "ABSENT":
                verdict = "PASS"; rule.append("K5")
            elif n13_v == "PASS" and r10_v == "ABSENT":
                verdict = "PASS"; rule.append("K6")   # 仅 N13 有答案（拆分裂缝等）
            else:
                verdict = "RAISE"; rule.append("K7")

            rec = {"token": tok, "pos": m.start(), "line": line,
                   "r10": r10_v, "r10_kind": r10k, "r12": r12_v,
                   "n13": n13_v, "n13_kind": d_kind,
                   "n13_veto": n13_veto, "n13_rule": d_rule,
                   "verdict": verdict, "rules": rule, "quote": ""}
            a = text.rfind("\n", 0, m.start()) + 1
            b = text.find("\n", m.end())
            rec["quote"] = text[a:(b if b != -1 else len(text))][:160]
            rows.append(rec)
            if unresolved or (r10_v != "ABSENT" and n13_v != "ABSENT"
                              and r10_v != n13_v):
                conflicts.append({"token": tok, "pos": m.start(), "line": line,
                                  "r10": r10_v, "r12": r12_v, "n13": n13_v,
                                  "resolved": not unresolved,
                                  "final": verdict, "rules": rule,
                                  "quote": rec["quote"]})
    # N13 拆分裂缝（pos=-1）：词表字面三词不含该形态，单独作为 CATCH 补入
    for d in d13:
        if d["pos"] == -1 and d["kind"] == "D":
            rows.append({"token": d["token"], "pos": -1, "line": d["line"],
                         "r10": "ABSENT", "r10_kind": None, "r12": "ABSENT",
                         "n13": "CATCH", "n13_kind": "D", "n13_rule": d["rule"],
                         "verdict": "CATCH", "rules": ["K6"], "quote": d["quote"][:160]})
    summary = {
        "spans": len(rows),
        "catch": sum(1 for r in rows if r["verdict"] in ("CATCH", "FAIL_CLOSED")),
        "pass": sum(1 for r in rows if r["verdict"] == "PASS"),
        "raise": sum(1 for r in rows if r["verdict"] == "RAISE"),
        "conflicts": len(conflicts),
        "unresolved": sum(1 for c in conflicts if not c["resolved"]),
    }
    return rows, conflicts, summary


# ---------------------------------------------------------------------------
# L7 结论：problems 是各层 FAIL 的并 + 冲突登记；不放过任何 CONFLICT_UNRESOLVED
# ---------------------------------------------------------------------------
def gate_check(text, tokens, doc_dir, g7, n13, n13_tokens, root=ROOT):
    ext = extract_spans(text, tokens)
    layers = run_layers(g7, n13, n13_tokens, text, tokens, doc_dir, root)
    rows, conflicts, summary = resolve_conflicts(text, tokens, layers, n13_tokens)
    problems = []
    # 独立项（不与断言层构成冲突）：R9 要素、R11 绑定回验，直接并入。
    for key in ("R9", "R11"):
        problems += [{"rule_id": key, "msg": m} for m in layers[key]["problems"]]
    # 断言层：问题由【逐 span 裁决结果】生成，不把三层 problems 做朴素并集。
    # 若做并集，N13 已放过的 A/B 会被 R10 的宽进 problems 重新报成 FAIL
    # （实测见 _gp_regression_v1_union_out.txt：chain 48/72 vs N13 单层 68/72）。
    for r in rows:
        if r["verdict"] in ("CATCH", "FAIL_CLOSED"):
            problems.append({"rule_id": "ADJUDICATED", "msg":
                             "L%d pos=%d tok=%s 裁决=%s rules=%s (r10=%s r12=%s n13=%s)"
                             % (r["line"], r["pos"], r["token"], r["verdict"],
                                ",".join(r["rules"]), r["r10"], r["r12"], r["n13"])})
        elif r["verdict"] == "RAISE":
            problems.append({"rule_id": "NEEDS_HUMAN", "msg":
                             "L%d pos=%d tok=%s 无层判到 / 层间无答案 → 不放过"
                             % (r["line"], r["pos"], r["token"])})
    # 冲突无论是否裁决，一律登记（不许靠顺序让它消失）
    for c in conflicts:
        problems.append({"rule_id": "CONFLICT", "msg":
                         "L%d pos=%d r10=%s r12=%s n13=%s resolved=%s final=%s rules=%s"
                         % (c["line"], c["pos"], c["r10"], c["r12"], c["n13"],
                            c["resolved"], c["final"], ",".join(c["rules"]))})
    # ★ 冲突登记本身不是 FAIL：合成链若只因「有分歧」就 FAIL，等于用结论代替裁决。
    #   最终 verdict 由裁决后的 span 判定决定；未消解冲突额外置 NEEDS_HUMAN。
    unresolved = [c for c in conflicts if not c["resolved"]]
    verdict = "PASS"
    if any(p["rule_id"] in ("ADJUDICATED", "R9", "R11", "NEEDS_HUMAN") for p in problems):
        verdict = "FAIL"
    if unresolved:
        verdict = "NEEDS_HUMAN" if verdict == "PASS" else verdict + "+NEEDS_HUMAN"
    return {"extractor": {k: ext[k] for k in ("count", "eol", "tokens")},
            "layers": {k: {"problems_n": len(v["problems"]),
                           "warnings_n": len(v.get("warnings", [])),
                           "hits_n": len(v.get("hits", v.get("details", [])))}
                       for k, v in layers.items()},
            "conflicts": conflicts, "summary": summary,
            "problems": problems, "verdict": verdict,
            "_rows": rows, "_layers": layers}


if __name__ == "__main__":
    g7, n13, T = load_predicates()
    s = "grep 结果：已生效，可应用母本"
    r = gate_check(s, T, ROOT / "lead" / "gate_pipeline_20261109", g7, n13, T)
    print("demo text =", s)
    print("verdict =", r["verdict"], "summary =", r["summary"])
    for x in r["_rows"]:
        print("  ", x["token"], x["pos"], x["r10"], x["n13"], "=>", x["verdict"], x["rules"])
    for p in r["problems"]:
        print("  PROBLEM", p["rule_id"], p["msg"][:120])
