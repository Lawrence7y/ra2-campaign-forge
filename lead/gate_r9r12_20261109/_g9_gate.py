# -*- coding: utf-8 -*-
"""_g9_gate.py — R9/R10/R11/R12 四谓词可复用门禁模块（实装层）。

日期：2026-11-09。写域：lead/gate_r9r12_20261109/（本模块为本任务唯一新写门禁件）。

★ 谓词本体零改写：四个修正谓词直接 import 自
  lead/gate_fp7_20261108/_g7_predicates.py（R9=r9_check/r9_element_present/r9_normalize,
  R10=r10_scan/r10_context, R11=r11_scan, R12=r12_scan），
  加载前用 hashlib 实算指纹并与编排方派发值比对，失配即拒绝运行。
★ 朴素门禁对照直接复用同模块的 naive_gate（既有门禁家族现状，第 5/8 类误报在此复现），
  另加越权词朴素字面计数对照（口径 = GATE_FALSE_POSITIVE_5_6_7.md:40 探针 BAD_BAN 家族）。

检查计数（第 3 类「空跑通过」防线）：
  R9  items = len(必需要素清单)          —— 每要素一项
  R10 items = len(禁用词清单)            —— 每禁用词一项全文扫描
  R12 items = len(禁用词清单)            —— 每禁用词一项双重否定复核
  R11 items = 1 + len(绑定行)            —— 「≥1 条绑定行」强制项 + 每条绑定行回验一项
  任一谓词 items == 0 ⇒ 该谓词判 FAIL_EMPTY（计 FAIL），problems 记「空跑」。
  R11 的 items 恒 ≥1（存在性检查本身即一项）。

词表卫生（第 5 类防线，patch §1 注②）：词表 token 先剥离包裹字符（` ´ “ ” ‘ ’ 「 」 『 』）
再交谓词；发生剥离即在 config_warnings 登记（不静默）。

执行顺序（_g7_patch.md §1）：R9 → R10 → R12 → R11（R12 消费 R10 语境分类，R11 收尾）。
输出：dict（JSON 可序列化），含每谓词 items/hits/豁免/problems/warnings/verdict 与总判定。
零真机、零采样代码；仅 import hashlib/importlib.util/json/re/pathlib。
"""

import hashlib
import importlib.util
import re
from pathlib import Path

REPO_ROOT = Path(r"D:\Project\ra2-campaign-forge")
G7_PREDICATES_PATH = REPO_ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743


def _load_g7_predicates():
    """只读加载 _g7_predicates.py；先验指纹，失配拒绝运行。"""
    raw = G7_PREDICATES_PATH.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != G7_SHA256_EXPECTED or len(raw) != G7_BYTES_EXPECTED:
        raise RuntimeError(
            "谓词模块指纹失配：%s = %s/%d ≠ 声明 %s/%d —— 拒绝运行"
            % (G7_PREDICATES_PATH, sha, len(raw), G7_SHA256_EXPECTED, G7_BYTES_EXPECTED)
        )
    spec = importlib.util.spec_from_file_location("_g7_predicates_g9", G7_PREDICATES_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


g7 = _load_g7_predicates()
_WRAP_CHARS = g7._WRAP_CHARS  # 包裹字符集，取自谓词模块原文明示常量


def sanitize_tokens(tokens):
    """词表卫生：剥包裹字符；返回 (清洗后清单, 被清洗的原 token 清单)。"""
    clean, stripped = [], []
    for t in tokens:
        s = "".join(ch for ch in t if ch not in _WRAP_CHARS)
        clean.append(s)
        if s != t:
            stripped.append(t)
    return clean, stripped


def check_deliverable(path, required_elements, forbidden_words,
                      root=REPO_ROOT, doc_dir=None, old_gate_contrast=True):
    """统一入口：给定交付件路径 + 必需要素清单 + 禁用词清单 → JSON 可序列化 dict。

    返回字段：
      file/bytes/sha256/utf8_strict
      checklist{required_elements,forbidden_words,stripped_in_config}
      predicates{R9,R10,R12,R11}  各含 items/hits/豁免/problems/warnings/verdict
      problems/warnings（合并视图，rule_id 必填——R7 输出契约）
      verdict（PASS 仅当四谓词全 PASS）
      old_gate（对照：既有门禁家族现状在同清单下的 problems/越权词命中，不参与判定）
    """
    p = Path(path)
    raw = p.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
        utf8_strict = True
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        utf8_strict = False
    d_dir = Path(doc_dir) if doc_dir is not None else p.parent

    req, req_stripped = sanitize_tokens(list(required_elements))
    forb, forb_stripped = sanitize_tokens(list(forbidden_words))
    config_warnings = []
    if req_stripped:
        config_warnings.append("词表含包裹符已剥离（第 5 类防线）：%r" % (req_stripped,))
    if forb_stripped:
        config_warnings.append("禁用词表含包裹符已剥离（第 5 类防线）：%r" % (forb_stripped,))

    predicates = {}

    # ---- R9 要素在场（包裹归一化） ----
    r9_problems, r9_warnings = g7.r9_check(text, req)
    r9_present = r9_raw = 0
    for k in req:
        ok, layer = g7.r9_element_present(text, k)
        if ok:
            r9_present += 1
            if layer == "raw":
                r9_raw += 1
    r9_items = len(req)
    r9_verdict = "FAIL_EMPTY" if r9_items == 0 else ("FAIL" if r9_problems else "PASS")
    predicates["R9"] = {
        "rule_id": "R9", "name": "包裹归一化要素匹配（第 5 类）",
        "items": r9_items, "present": r9_present, "raw_hits": r9_raw,
        "normalized_only_hits": r9_present - r9_raw,
        "problems": list(r9_problems), "warnings": list(r9_warnings),
        "verdict": r9_verdict,
    }
    if r9_items == 0:
        r9_problems = list(r9_problems) + ["R9 空跑：必需要素清单为空，0 项检查（第 3 类防线：0 项不得 PASS）"]

    # ---- R10 越权断言语境分类（否定/引证豁免） ----
    r10_problems, r10_warnings, r10_hits = g7.r10_scan(text, forb)
    kinds = {"assertion": 0, "negation": 0, "quote_mention": 0, "double_neg": 0}
    for h in r10_hits:
        kinds[h["kind"]] += 1
    r10_items = len(forb)
    r10_verdict = "FAIL_EMPTY" if r10_items == 0 else ("FAIL" if r10_problems else "PASS")
    predicates["R10"] = {
        "rule_id": "R10", "name": "越权断言语境分类（第 6/7 类）",
        "items": r10_items, "occurrences": len(r10_hits), "kinds": kinds,
        "exempted": len(r10_warnings),
        "problems": list(r10_problems), "warnings": list(r10_warnings),
        "verdict": r10_verdict,
    }
    if r10_items == 0:
        r10_problems = list(r10_problems) + ["R10 空跑：禁用词清单为空，0 项检查（第 3 类防线：0 项不得 PASS）"]

    # ---- R12 双重否定守卫（接 R10 之后） ----
    r12_problems, r12_hits = g7.r12_scan(text, forb)
    r12_items = len(forb)
    r12_verdict = "FAIL_EMPTY" if r12_items == 0 else ("FAIL" if r12_problems else "PASS")
    predicates["R12"] = {
        "rule_id": "R12", "name": "双重否定守卫（第 6/7 类反例防线）",
        "items": r12_items, "double_neg_hits": len(r12_hits),
        "problems": list(r12_problems), "warnings": [],
        "verdict": r12_verdict,
    }
    if r12_items == 0:
        r12_problems = list(r12_problems) + ["R12 空跑：禁用词清单为空，0 项检查（第 3 类防线：0 项不得 PASS）"]

    # ---- R11 绑定行容忍匹配 + 引用锚回验 ----
    r11_problems, r11_warnings, bindings = g7.r11_scan(text, d_dir, root=root)
    bindings = [dict(b) for b in bindings]
    n_reverified = sum(1 for b in bindings if b.get("path"))
    n_match = sum(1 for b in bindings if b.get("match") is True)
    r11_items = 1 + len(bindings)  # 存在性强制项 1 + 每条绑定行回验
    r11_verdict = "FAIL" if r11_problems else "PASS"
    predicates["R11"] = {
        "rule_id": "R11", "name": "绑定行路径隔断容忍 + 引用锚回验（第 8 类）",
        "items": r11_items, "bindings": len(bindings), "reverified": n_reverified,
        "match_true": n_match,
        "problems": list(r11_problems), "warnings": list(r11_warnings),
        "binding_details": bindings, "verdict": r11_verdict,
    }

    # ---- 合并视图（rule_id 必填，R7 输出契约） ----
    problems = ([{"rule_id": "R9", "msg": m} for m in r9_problems]
                + [{"rule_id": "R10", "msg": m} for m in r10_problems]
                + [{"rule_id": "R12", "msg": m} for m in r12_problems]
                + [{"rule_id": "R11", "msg": m} for m in r11_problems])
    warnings = ([{"rule_id": "R9", "msg": m} for m in r9_warnings]
                + [{"rule_id": "R10", "msg": m} for m in r10_warnings]
                + [{"rule_id": "R11", "msg": m} for m in r11_warnings]
                + [{"rule_id": "CONFIG", "msg": m} for m in config_warnings])
    overall = "PASS" if all(predicates[k]["verdict"] == "PASS"
                            for k in ("R9", "R10", "R12", "R11")) else "FAIL"

    result = {
        "file": str(p), "bytes": len(raw), "sha256": sha, "utf8_strict": utf8_strict,
        "checklist": {"required_elements": list(required_elements),
                      "forbidden_words": list(forbidden_words)},
        "predicates": predicates,
        "problems": problems, "warnings": warnings, "verdict": overall,
    }

    # ---- 朴素门禁对照（既有门禁家族现状，不参与判定） ----
    if old_gate_contrast:
        old_problems = list(g7.naive_gate(text, list(required_elements)))
        old_forbidden = {}
        for tok in forbidden_words:
            n = text.count(tok)
            if n:
                old_forbidden[tok] = n
        for tok, n in old_forbidden.items():
            old_problems.append("越权断言 %s（朴素字面计数 ×%d）" % (tok, n))
        result["old_gate"] = {
            "note": "既有门禁家族现状对照（g7.naive_gate：紧邻绑定正则+裸子串要素；越权词裸计数）；不参与本模块判定",
            "problems": old_problems, "forbidden_hits": old_forbidden,
        }
    return result


def self_test():
    """模块自检：第 3 类空跑防线与第 5 类词表包裹符防线各一例（用本仓库真实件，只读）。
    返回 (checks, all_pass)。"""
    checks = []
    probe = REPO_ROOT / "lead" / "bexec_n4_20261108" / "B_EXECUTION_SPEC.md"

    # U1 第 3 类：空清单不得 PASS
    r = check_deliverable(probe, [], [])
    ok = (r["verdict"] == "FAIL"
          and sum(1 for x in r["problems"] if "空跑" in x["msg"]) == 3)
    checks.append({"id": "U1_第3类空跑防线", "ok": ok,
                   "detail": "空清单判定=%s，空跑 problems=%d" % (r["verdict"], len(r["problems"]))})

    # U2 第 5 类：词表带包裹符（「被核对象」整体入表）——朴素门禁误报缺要素，本模块剥离后判在场
    r2 = check_deliverable(probe, ["「被核对象」"], ["已生效"])
    naive_missed = any("缺要素" in m for m in r2["old_gate"]["problems"])
    r9_ok = r2["predicates"]["R9"]["verdict"] == "PASS"
    checks.append({"id": "U2_第5类包裹符词表", "ok": bool(naive_missed and r9_ok),
                   "detail": "naive 报缺要素=%s，R9 判在场=%s" % (naive_missed, r9_ok)})

    # U3 谓词指纹自验（加载时已验，此处复述结论）
    checks.append({"id": "U3_谓词指纹", "ok": True,
                   "detail": "_g7_predicates.py 加载前指纹比对 = %s/%d B" % (G7_SHA256_EXPECTED, G7_BYTES_EXPECTED)})

    return checks, all(c["ok"] for c in checks)


if __name__ == "__main__":
    import json
    import sys
    checks, ok = self_test()
    print(json.dumps({"self_test": checks, "all_pass": ok}, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)
