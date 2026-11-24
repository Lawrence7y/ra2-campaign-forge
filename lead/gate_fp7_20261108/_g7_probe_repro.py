# -*- coding: utf-8 -*-
r"""_g7_probe_repro.py — 复核编排方「三类误报在四份真实件上的实测」。
探针定义逐字取自派发本工作流的载荷 dwfrun-fed3c2a2 PROBE_CODE：
  BAD_BAN=['已生效','可应用母本','放行 N-5','已入账','已追加']
  否定回看：命中点前 24 字符内 re.search(r'(不|无|未|非|禁|勿|否决|排除|不宣告|不得)')
  bind_naive   = r'被核对象 SHA256\s*=\s*[0-9a-fA-F]{64}'            （hex 不允许反引号）
  bind_relaxed = r'被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}'
  bind_any     = r'SHA256\s*=\s*`?[0-9a-fA-F]{64}'
只读。追加第 5 类量化：APPROVE_SCOPE 的包裹形态分类计数。
"""
import json, pathlib, re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
FILES = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
NEG_RE = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")
BIND_NAIVE = re.compile(r"被核对象 SHA256\s*=\s*[0-9a-fA-F]{64}")
BIND_RELAXED = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}")
BIND_ANY = re.compile(r"SHA256\s*=\s*`?[0-9a-fA-F]{64}")

res = {}
for rel in FILES:
    p = ROOT / rel
    if not p.is_file():
        res[rel] = {"missing": True}
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    naive = {b: t.count(b) for b in BAD_BAN}
    neg = {}
    for b in BAD_BAN:
        n = 0
        for m in re.finditer(re.escape(b), t):
            s = max(0, m.start() - 24)
            pre = t[s:m.start()]
            if NEG_RE.search(pre):
                n += 1
        neg[b] = n
    # 第 5 类追加量化：APPROVE_SCOPE 包裹形态
    forms = {"bare": 0, "backtick": 0, "corner": 0, "lowercase": 0, "split": 0}
    for m in re.finditer(r"APPROVE_SCOPE", t):
        pre1 = t[m.start() - 1] if m.start() > 0 else ""
        post1 = t[m.end()] if m.end() < len(t) else ""
        if pre1 == "`" and post1 == "`":
            forms["backtick"] += 1
        elif pre1 == "「" and post1 in "」/、 ":
            forms["corner"] += 1
        else:
            forms["bare"] += 1
    forms["lowercase"] = len(re.findall(r"approve_scope", t, re.I)) - forms["backtick"] - forms["corner"] - forms["bare"] if re.findall(r"approve_scope", t, re.I) else 0
    # 被换行拆断的形态（APPROVE\nSCOPE / APPROVE_\nSCOPE）
    forms["split"] = len(re.findall(r"APPROVE[_\s]*\n\s*SCOPE", t))
    res[rel] = {
        "naiveHits": naive,
        "negated": neg,
        "bind_naive": len(BIND_NAIVE.findall(t)),
        "bind_relaxed": len(BIND_RELAXED.findall(t)),
        "bind_any": len(BIND_ANY.findall(t)),
        "approve_forms": forms,
        "bytes": p.stat().st_size,
    }

print(json.dumps(res, ensure_ascii=False, indent=1))
