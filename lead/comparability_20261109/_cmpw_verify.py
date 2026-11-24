# -*- coding: utf-8 -*-
"""_cmpw_verify.py — 交付前独立复算（只读既有件，只 print，不写任何既有产物）。
调用：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/comparability_20261109/_cmpw_verify.py
"""
import hashlib
import json
import math
import os
import pathlib

ROOT = pathlib.Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "comparability_20261109"
P72 = ROOT / "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json"
P74 = ROOT / "lead/gate_pipeline_20261109/_gp_regression_out.json"
REPORT = WD / "_cmp_AUDIT_20261109.md"

FINGERPRINTS = {
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json": ("68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358", 37461),
    "lead/gate_pipeline_20261109/_gp_regression.py": ("1804e5bfb4c3ded9c0f19a44ae6e409b890a5b7c192657253a6694f2be5df1d3", 13017),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md": ("3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    "lead/chain_vs_single_20261109/_cs_align_out.json": ("9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698", 11594),
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
JUDGE = ("naive", "r10", "r12", "n13", "chain")
ALLCOLS = JUDGE + ("layer_conflicts", "layer_unresolved")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pbin(b, c):
    """配对 exact binomial 双侧 p（b+c>0 时）。"""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


print("=== [1] 九件编排方指纹独立复算 ===")
n_match = 0
for rel, (eh, eb) in FINGERPRINTS.items():
    p = ROOT / rel
    raw = p.read_bytes()
    h, n = sha(raw), len(raw)
    ok = (h == eh and n == eb)
    n_match += ok
    print("  %s %s sha=%s bytes=%d expected=%s/%d" %
          ("MATCH" if ok else "MISMATCH", rel, h, n, eh[:12], eb))
print("  BASELINE_MATCH %d/%d" % (n_match, len(FINGERPRINTS)))

A = json.loads(P72.read_text(encoding="utf-8"))
B = json.loads(P74.read_text(encoding="utf-8"))
ra = {r["id"]: r for r in A["rows"]}
rb = {r["id"]: r for r in B["rows"]}
ids_a, ids_b = set(ra), set(rb)
common = sorted(ids_a & ids_b)
only_a, only_b = sorted(ids_a - ids_b), sorted(ids_b - ids_a)

print("\n=== [2] id 集差（72 版=A / 74 版=B） ===")
print("  n72=%d n74=%d common=%d" % (len(ids_a), len(ids_b), len(common)))
print("  ids_only_72=%s" % only_a)
print("  ids_only_74=%s" % only_b)
for i in only_b:
    r = rb[i]
    print("    74独有 %s family=%s expect=%s text=%r note=%r" % (i, r["family"], r["expect"], r["text_head"], r["note"]))
for i in only_a:
    r = ra[i]
    print("    72独有 %s family=%s expect=%s text=%r note=%r" % (i, r["family"], r["expect"], r["text_head"], r["note"]))

print("\n=== [3] expect 变更逐条 ===")
exp_ch = [i for i in common if ra[i]["expect"] != rb[i]["expect"]]
for i in exp_ch:
    print("  %s: %s -> %s | text=%r | 全判定列相同? %s" %
          (i, ra[i]["expect"], rb[i]["expect"], ra[i]["text_head"],
           all(ra[i][c] == rb[i][c] for c in ALLCOLS)))
print("  n_expect_changes=%d" % len(exp_ch))

print("\n=== [4] 文本 / tokens / family / note 变更逐条（共有 71 条） ===")
for fld in ("text_head", "tokens", "family", "note"):
    ch = [i for i in common if ra[i][fld] != rb[i][fld]]
    print("  %s 变更 %d 条 %s" % (fld, len(ch), ch))
    if fld == "note":
        for i in ch:
            print("    %s: 72=%r -> 74=%r" % (i, ra[i]["note"], rb[i]["note"]))

print("\n=== [5] GP-C03 与 GP-A1 逐列比对 ===")
x, y = ra["GP-C03"], rb["GP-A1"]
print("  text 相同? %s ; tokens 相同? %s ; expect 相同? %s" %
      (x["text_head"] == y["text_head"], x["tokens"] == y["tokens"], x["expect"] == y["expect"]))
print("  全判定列相同? %s" % all(x[c] == y[c] for c in ALLCOLS))
print("  family: %s -> %s" % (x["family"], y["family"]))
tkeys_a = {r["text_head"] for r in A["rows"]}
tkeys_b = {r["text_head"] for r in B["rows"]}
print("  unique text keys: 72=%d 74=%d shared=%d only72=%s only74_texts=%s" %
      (len(tkeys_a), len(tkeys_b), len(tkeys_a & tkeys_b), sorted(tkeys_a - tkeys_b),
       [r["text_head"] for r in B["rows"] if r["text_head"] in (tkeys_b - tkeys_a)]))

print("\n=== [6] conflicts / unresolved / 逐层统计 / 类别先验 ===")
for nm, d in (("72", A), ("74", B)):
    rows = d["rows"]
    cs = sum(r["layer_conflicts"] for r in rows)
    us = sum(r["layer_unresolved"] for r in rows)
    st = {}
    for m in JUDGE:
        ok = sum(1 for r in rows if r[m] == r["expect"])
        fp = sum(1 for r in rows if r[m] != r["expect"] and r["expect"] == "PASS")
        fn = sum(1 for r in rows if r[m] != r["expect"] and r["expect"] == "CATCH")
        st[m] = (ok, fp, fn)
    same = all(d["single_layer_vs_chain"][m]["ok"] == st[m][0] and
               d["single_layer_vs_chain"][m]["fp"] == st[m][1] and
               d["single_layer_vs_chain"][m]["fn"] == st[m][2] for m in JUDGE)
    nc = sum(1 for r in rows if r["expect"] == "CATCH")
    print("  %s版 declared conflicts=%d unresolved=%d | recomputed=%d/%d | 逐层10/10 MATCH? %s" %
          (nm, d["chain_conflicts_total"], d["chain_unresolved_total"], cs, us, same))
    print("    n=%d CATCH=%d PASS=%d | stats=%s" % (len(rows), nc, len(rows) - nc, st))
    print("    by_family=%s" % sorted(d["by_family"].keys()))
print("  sources 逐字相同? %s ; not_in_corpus 逐字相同? %s" %
      (A["sources"] == B["sources"], A["not_in_corpus"] == B["not_in_corpus"]))
print("  74版 未登记族=%s" % sorted(set(B["by_family"]) - set(B["sources"])))

print("\n=== [7] chain 翻转 / unresolved 集合 ===")
cc = [i for i in common if ra[i]["chain"] != rb[i]["chain"]]
uc = [i for i in common if ra[i]["layer_unresolved"] != rb[i]["layer_unresolved"]]
print("  chain_changed=%d | unresolved_changed=%d | 集合恒等? %s" % (len(cc), len(uc), set(cc) == set(uc)))
print("  chain_changed ids=%s" % cc)
print("  18行全部 CATCH->PASS? %s ; 全部 74expect=PASS? %s ; 全部72 unresolved>0? %s" %
      (all(ra[i]["chain"] == "CATCH" and rb[i]["chain"] == "PASS" for i in cc),
       all(rb[i]["expect"] == "PASS" for i in cc),
       all(ra[i]["layer_unresolved"] > 0 for i in cc)))
print("  v1 unresolved 合计(翻转行)=%d ; 全72版=%d" %
      (sum(ra[i]["layer_unresolved"] for i in cc), A["chain_unresolved_total"]))
print("  layer_conflicts 共有行变更数=%d" %
      sum(1 for i in common if ra[i]["layer_conflicts"] != rb[i]["layer_conflicts"]))
print("  四个单层列共有71行逐行相同? %s" %
      all(all(ra[i][m] == rb[i][m] for m in JUDGE[:-1]) for i in common))

print("\n=== [8] 21 分分解 ===")
def chain_ok(d):
    return sum(1 for r in d["rows"] if r["chain"] == r["expect"])
o72, o74 = chain_ok(A), chain_ok(B)
print("  72版 chain %d/%d=%.2f%% ; 74版 chain %d/%d=%.2f%% ; raw_delta=%d ; pp=%.2f" %
      (o72, len(A["rows"]), 100.0 * o72 / len(A["rows"]), o74, len(B["rows"]),
       100.0 * o74 / len(B["rows"]), o74 - o72,
       100.0 * (o74 / len(B["rows"]) - o72 / len(A["rows"]))))
strict = [i for i in common if ra[i]["expect"] == rb[i]["expect"]
          and ra[i]["text_head"] == rb[i]["text_head"]
          and ra[i]["tokens"] == rb[i]["tokens"]]
d_frozen = sum(1 for i in strict if rb[i]["chain"] == rb[i]["expect"]) - sum(1 for i in strict if ra[i]["chain"] == ra[i]["expect"])
d_flip = sum(1 for i in exp_ch if (rb[i]["chain"] == rb[i]["expect"]) - (ra[i]["chain"] == ra[i]["expect"]) == 1)
d_new = sum(1 for i in only_b if rb[i]["chain"] == rb[i]["expect"])
d_del = -sum(1 for i in only_a if ra[i]["chain"] == ra[i]["expect"])
print("  strict n=%d ; decomposition frozen=%+d flipped=%+d new=%+d deleted=%+d sum=%+d" %
      (len(strict), d_frozen, d_flip, d_new, d_del, d_frozen + d_flip + d_new + d_del))
print("  3 条翻标行 chain 输出相同? %s" % all(ra[i]["chain"] == rb[i]["chain"] for i in exp_ch))
print("  GP-C03->GP-A1 文本相同且两边都错? %s | 72错=%s 74错=%s" %
      (ra["GP-C03"]["text_head"] == rb["GP-A1"]["text_head"],
       ra["GP-C03"]["chain"] != ra["GP-C03"]["expect"], rb["GP-A1"]["chain"] != rb["GP-A1"]["expect"]))

print("\n=== [9] 68 条冻结子集反推 ===")
v1ok = sum(1 for i in strict if ra[i]["chain"] == ra[i]["expect"])
v2ok = sum(1 for i in strict if rb[i]["chain"] == rb[i]["expect"])
b = sum(1 for i in strict if ra[i]["chain"] != ra[i]["expect"] and rb[i]["chain"] == rb[i]["expect"])
c = sum(1 for i in strict if ra[i]["chain"] == ra[i]["expect"] and rb[i]["chain"] != rb[i]["expect"])
print("  strict n=%d v1_72_chain_ok=%d v2_74_chain_ok=%d chain_changed=%d" %
      (len(strict), v1ok, v2ok, sum(1 for i in strict if ra[i]["chain"] != rb[i]["chain"])))
print("  paired b=%d c=%d p_2sided=%s" % (b, c, pbin(b, c)))
for ex in ("CATCH", "PASS"):
    sub = [i for i in strict if ra[i]["expect"] == ex]
    print("  %s n=%d : %s" % (ex, len(sub),
          {m: (sum(1 for i in sub if ra[i][m] == ra[i]["expect"]),
               sum(1 for i in sub if rb[i][m] == rb[i]["expect"])) for m in JUDGE}))
print("  单层4列在strict上逐行相同? %s" %
      all(all(ra[i][m] == rb[i][m] for m in JUDGE[:-1]) for i in strict))

print("\n=== [10] 版内配对显著性复算 ===")
for nm, d in (("72", A), ("74", B)):
    rows = d["rows"]
    bb = sum(1 for r in rows if r["n13"] == r["expect"] and r["chain"] != r["expect"])
    c_c = sum(1 for r in rows if r["n13"] != r["expect"] and r["chain"] == r["expect"])
    print("  %s版 chain vs n13: b=%d c=%d p_2sided=%s (n13_ok=%d chain_ok=%d)" %
          (nm, bb, c_c, pbin(bb, c_c),
           sum(1 for r in rows if r["n13"] == r["expect"]), chain_ok(d)))
sub = strict
bb = sum(1 for i in sub if rb[i]["n13"] == rb[i]["expect"] and rb[i]["chain"] != rb[i]["expect"])
c_c = sum(1 for i in sub if rb[i]["n13"] != rb[i]["expect"] and rb[i]["chain"] == rb[i]["expect"])
print("  68子集 74版 chain vs n13: b=%d c=%d p_2sided=%s" % (bb, c_c, pbin(bb, c_c)))

print("\n=== [11] 被核报告指纹 / 绑定行格式 ===")
raw = REPORT.read_bytes()
print("  _cmp_AUDIT_20261109.md sha256=%s bytes=%d" % (sha(raw), len(raw)))
import re
txt = raw.decode("utf-8")
lines = [l for l in txt.splitlines() if l.startswith("被核对象 SHA256 = ")]
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
good = [l for l in lines if pat.match(l)]
print("  绑定行总数=%d 合规=%d (regex ^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\\d+)$)" % (len(lines), len(good)))

print("\n=== [12] 只读零越界辅助 ===")
rep = (ROOT / "lead/gate_pipeline_20261109/_gpv_repro_out.json").read_bytes()
cur = P74.read_bytes()
print("  _gpv_repro_out.json 与 74版产物 same bytes? %s" % (rep == cur))
print("  write-domain path = %s" % WD)
print("\nDONE")
