# -*- coding: utf-8 -*-
# N4 gate reviewer: my OWN polarity classifier for the 5 BAN hits.
# For each hit, print 120 chars of preceding context, the containing sentence,
# and classify by explicit markers: negation ("不/无/未/非/禁/勿/不得"),
# conditional ("若...即翻/出现...即失效"), quotation spans 「」/backticks,
# and whether the sentence asserts the banned proposition as TRUE of this doc.
import json, re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
DOC = ROOT / "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md"
OUT = ROOT / "lead/n4_gate_verdict_20261109/_n4gv_polarity_out.json"
t = DOC.read_text(encoding="utf-8")
lines = t.split("\n")

def sentence_of(pos):
    # split on Chinese full stops / semicolons / newlines, keep bounded
    bounds = [m.end() for m in re.finditer(r"[。！？；\n]", t[:pos])]
    s = bounds[-1] if bounds else 0
    ends = [m.start() for m in re.finditer(r"[。！？；\n]", t[pos:])]
    e = pos + ends[0] + 1 if ends else len(t)
    return t[s:e]

NEG = re.compile(r"不|无|未|非|禁|勿|不得|否决|排除")
SELF_ASSERT = re.compile(r"本件|本文|本 YES|已获批准|现已|特此|宣告")

results = []
for tok in ["可应用母本", "放行 N-5", "已应用", "已签 APPROVE_SCOPE"]:
    for m in re.finditer(re.escape(tok), t):
        pre = t[max(0, m.start()-120):m.start()]
        post = t[m.end():m.end()+80]
        sent = sentence_of(m.start())
        ln = t.count("\n", 0, m.start()) + 1
        in_quote = any(a <= m.start() and m.end() <= b for a, b in
                       [(mm.start(), mm.end()) for mm in re.finditer(r"「[^」\n]*」", t)])
        in_bt = any(a <= m.start() and m.end() <= b for a, b in
                    [(mm.start(), mm.end()) for mm in re.finditer(r"`[^`\n]*`", t)])
        # my classification
        neg_in_sentence = bool(NEG.search(sent[:sent.find(tok)] if tok in sent else sent))
        conditional = bool(re.search(r"若|或回件出现|不出现|任一破坏即失效|即翻|即失效", sent))
        self_assert = bool(SELF_ASSERT.search(sent))
        if self_assert and not neg_in_sentence and not conditional:
            verdict = "ASSERTION (would be a real overreach)"
        elif conditional or neg_in_sentence or in_quote:
            verdict = "EXCLUSION / NEGATION / QUOTE (not an assertion)"
        else:
            verdict = "UNCLASSIFIED (needs manual read)"
        results.append({
            "token": tok, "pos": m.start(), "line": ln,
            "pre120": pre, "post80": post, "sentence": sent.strip(),
            "in_「」quote": in_quote, "in_backticks": in_bt,
            "negation_before_token_in_sentence": neg_in_sentence,
            "conditional_marker": conditional, "self_assert_marker": self_assert,
            "my_polarity_verdict": verdict,
        })

OUT.write_text(json.dumps({"hits": results,
                           "total_hits": len(results),
                           "assertion_count": sum(1 for r in results if r["my_polarity_verdict"].startswith("ASSERTION"))},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"total_hits": len(results),
                  "assertion_count": sum(1 for r in results if r["my_polarity_verdict"].startswith("ASSERTION")),
                  "hits": [{"token": r["token"], "line": r["line"], "sentence": r["sentence"][:220],
                            "verdict": r["my_polarity_verdict"]} for r in results]}, ensure_ascii=False, indent=2))
