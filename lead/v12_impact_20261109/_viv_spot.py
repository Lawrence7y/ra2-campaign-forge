"""Spot checks: co-triggers, S3 fallback viability, protected-dir write scan."""
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "v12_impact_20261109"
RULE = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
N13P = Path(str(ROOT) + "/lead/gate_n13_20261109/_n13_predicates.py")


def load(p, n):
    s = importlib.util.spec_from_file_location(n, str(p))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


R = load(RULE, "_viv_rule3")
G7 = load(G7P, "_viv_g73")
N13 = load(N13P, "_viv_n13p")

print("=== 1. independent co-trigger recount over 32 domains ===")
own = json.loads((WD / "_viv_shadow_own.json").read_text(encoding="utf-8"))
bl = json.loads((ROOT / "lead" / "gate_rejudge32_20261109" / "_rj_delivery_baseline.json").read_text(encoding="utf-8"))
texts = {}
for r in bl["rows"]:
    texts[r["domain"]] = (ROOT / r["domain"] / r["main"]).read_text(encoding="utf-8")
co_ov, co_weak = [], []
for row in own["rows"]:
    t = texts[row["domain"]]
    for h in row["hits"]:
        tok, pos, end = h["token"], h["pos"], h["pos"] + len(h["token"])
        line, U, off, is_table, rel_u = R._unit_and_line(t, pos, end, tok)
        pre = U[:max(0, rel_u)]
        adj_neg = bool(pre) and (pre[-1] in R.ADJ_NEG_CHARS or bool(R.ADJ_NEG_RE.search(pre)))
        prohibit = any(k in R._strip_quotes(U) for k in R.PROHIBIT)
        ov = [k for k in R.V2_OVERRIDE if k in U] or bool(R.V2_OVERRIDE_RE.search(U))
        weak = bool(R.W1_RE.search(pre)) or bool(R.W1_NUM_RE.match(U) or R.W1_NUM_RE.match(line))
        if h["hard"] and ov:
            co_ov.append((row["domain"], h["line"], tok, [k for k in R.V2_OVERRIDE if k in U],
                          "would_fire" if (ov and not adj_neg and not prohibit) else "blocked"))
        if h["hard"] and weak:
            co_weak.append((row["domain"], h["line"], tok))
print("hard_AND_override =", len(co_ov), co_ov)
print("hard_AND_weak     =", len(co_weak), co_weak)

print()
print("=== 2. S3 fallback proposal: would 'fall back to R10/N13' fix the 3 S3 misblocks? ===")
s3 = [("N13_POS/P09", "② RULING_DIRECTION.md 整体状态 **unconfirmed**（:5/:77）——**本节登记「以乙替代甲」是登记动作，不宣告 N-4 正式绑定已生效**（与补登件自述一致）。", "已生效"),
      ("N13_POS/P15", "### 3 已追加 grep 结果（清单）", "已追加"),
      ("R10_TV/TV3:L10", "作为对照，上一轮回件不宣告 N-4 正式绑定已生效（单重否定，应豁免）。", "已生效")]
r10fn = [getattr(G7, k) for k in dir(G7) if callable(getattr(G7, k))
         and getattr(getattr(G7, k), "__code__", None)
         and getattr(getattr(G7, k), "__code__").co_argcount == 2
         and "r10_context" in getattr(getattr(G7, k), "__code__").co_names
         and "warnings" in getattr(getattr(G7, k), "__code__").co_varnames][0]
for cid, text, tok in s3:
    pos = text.find(tok)
    v = R.classify_v12(text, pos, pos + len(tok), tok)
    k = G7.r10_context(text, pos, pos + len(tok))["kind"]
    probs, warns, _ = r10fn(text, [tok])
    r13probs, _ = N13.r13_assertions(text, N13.DEFAULT_TOKENS, r10fn, G7.r12_scan)
    print("  %-17s V12=%s review=%s | R10 kind=%-11s R10_problems=%d | R13(N13 gate) problems=%d" %
          (cid, v["verdict"], v["review_flag"], k, len(probs), len(r13probs)))

print()
print("=== 3. author probe S3 double-count source (read-only static inspection) ===")
src = (WD / "_vi_probe.py").read_text(encoding="utf-8").split("\n")
for i in (137, 138, 139, 140, 141, 158, 159, 160, 161, 162, 230, 231):
    print("  _vi_probe.py:%-4d %s" % (i + 1, src[i].strip()))

print()
print("=== 4. N13 regression script: any write calls? ===")
n13reg = (ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py").read_text(encoding="utf-8")
print("  write_text/write_bytes/json.dump occurrences:",
      [l.strip() for l in n13reg.split("\n") if re.search(r"write_text|write_bytes|json\.dump\(", l)][:10])
