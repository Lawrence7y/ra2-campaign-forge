# -*- coding: utf-8 -*-
# _cs_attrib.py : 归因 2 条负收益 + 3 条共漏 + 证据独立性定量
# 只读加载既有谓词（hashlib 先验指纹），不改任何谓词模块/语料。
import os, sys, json, pathlib, importlib.util, hashlib, collections
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
WD = pathlib.Path(ROOT) / "lead" / "gate_pipeline_20261109"
N13_PATH = WD.parent / "gate_n13_20261109" / "_n13_predicates.py"
G7_PATH = WD.parent / "gate_fp7_20261108" / "_g7_predicates.py"
V12_PATH = WD.parent / "gate_v1v2_20261109" / "_v12_rule.py"

def _load(path, name, want=None):
    raw = path.read_bytes()
    if want:
        h, n = hashlib.sha256(raw).hexdigest(), len(raw)
        assert (h, n) == want, "fingerprint mismatch %s %s/%d" % (path, h, n)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

g7 = _load(G7_PATH, "_cs_g7", ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743))
n13 = _load(N13_PATH, "_cs_n13", ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649))
v12 = _load(V12_PATH, "_cs_v12", ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148))
sys.path.insert(0, str(WD))
import _gp_pipeline as P
R10FN = g7.r10_scan
T = list(n13.DEFAULT_TOKENS)
T_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
T_C07_TRUTH = ["已填", "已代填", "已提交"]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]

def n13v(text, toks):
    p, _ = n13.r13_assertions(text, toks, r10_scan=R10FN, r12_scan=g7.r12_scan)
    return "CATCH" if p else "PASS", p

print("### [0] 回归 harness 的 N13 调用契约核查（_gp_regression.py:142-145）")
print("  judge_one(mode='n13') 恒用 T =", T, "（不看 item['tokens']）")
print("  judge_one(mode='chain') 用 gate_check(text, item['tokens'], ..., T)；toks = item['tokens']")
print("  两者不同：REAL-SLOT/TRUTH 与全部 R10_* 行，N13 单层实际是在【固定三词词表】上考的\n")

REAL = {
    "REAL-SLOT": ("lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_C07_SLOT, "PASS"),
    "REAL-TRUTH": ("lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_C07_TRUTH, "PASS"),
    "REAL-BOUND": ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T, "PASS"),
}
A = {
    "GP-A1": "亦非不宣告 N-4 正式绑定已生效",
    "GP-A2": "本件登记闭合，母本即日起适用",
    "GP-A3": "三值填毕，见证已由编排方签字",
}

print("### [1] 三件真实文档：逐 span 裁决明细（找把 PASS 判成 CATCH 的 K 规则）")
for cid, (rel, toks, expect) in REAL.items():
    text = (pathlib.Path(ROOT) / rel).read_text(encoding="utf-8")
    r = P.gate_check(text, toks, WD, g7, n13, T)
    catches = [x for x in r["_rows"] if x["verdict"] in ("CATCH", "FAIL_CLOSED", "RAISE")]
    rules = collections.Counter(tuple(x["rules"]) for x in catches)
    print("\n-- %s  expect=%s  chain_verdict=%s  spans=%d  catch_like=%d" %
          (cid, expect, r["verdict"], len(r["_rows"]), len(catches)))
    print("   裁决为 CATCH/FAIL_CLOSED/RAISE 的规则组合:", {"/".join(k): v for k, v in rules.items()})
    print("   前 6 个 catch span:")
    for x in catches[:6]:
        print("     L%-4d pos=%-6d tok=%-10s r10=%-7s r12=%-7s n13=%-7s kind=%-4s => %-12s rules=%-12s veto=%s | %s"
              % (x["line"], x["pos"], x["token"], x["r10"], x["r12"], x["n13"],
                 str(x["n13_kind"]), x["verdict"], ",".join(x["rules"]), x["n13_veto"],
                 x["quote"][:64].replace("\n", " ")))
    vt, pt = n13v(text, T)
    vo, po = n13v(text, toks)
    print("   单层 N13(固定三词 T) = %s (problems=%d)" % (vt, len(pt)))
    print("   单层 N13(该行词表 %s) = %s (problems=%d)" % (list(toks), vo, len(po)))
    print("   chain =", "CATCH" if any(p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN") for p in r["problems"]) else "PASS")

print("\n### [2] GP-A1/A2/A3：三层全部无 span / 无命中的根因（K7 为何未触发）")
for cid, s in A.items():
    print("\n-- %s : %s" % (cid, s))
    for name, toks in [("T(三词)", T), ("BAD_BAN(五词)", BAD_BAN),
                       ("C07_SLOT", T_C07_SLOT), ("C07_TRUTH", T_C07_TRUTH)]:
        hits = [(t, s.find(t)) for t in toks if t in s]
        print("   %-14s 字面命中=%s" % (name, hits if hits else "无"))
    pr10, _, h10 = R10FN(s, T)
    pr12, h12 = g7.r12_scan(s, T)
    p13, d13 = n13.r13_assertions(s, T, r10_scan=R10FN, r12_scan=g7.r12_scan)
    r = P.gate_check(s, T, WD, g7, n13, T)
    print("   R10 problems=%d hits=%s | R12 problems=%d hits=%s | N13 problems=%d details=%s"
          % (len(pr10), [(h["token"], h["kind"]) for h in h10], len(pr12),
             [(h["token"], h["pos"]) for h in h12], len(p13),
             [(d["token"], d["kind"]) for d in d13]))
    print("   chain rows=%d verdict=%s" % (len(r["_rows"]), r["verdict"]))
    print("   → tok_set=set(tokens)|n13三词；finditer 无命中 ⇒ rows 空 ⇒ K7 不进入循环 ⇒ PASS")
    for tok in ("已生效", "登记闭合", "填毕", "签字", "适用"):
        idx = s.find(tok)
        if idx >= 0:
            c = v12.classify_v12(s, idx, idx + len(tok), tok)
            print("   V1V2 独立谓词 tok=%-6s -> %-3s reason=%s" % (tok, c["verdict"], c["reason"][:56]))

print("\n### [3] 三条证据不独立路径：实跑定量")
print("\n-- (3a) N13 的 C 类是否转发 R10：")
for s in ["不宣告 N-4 正式绑定已生效。", "亦非不宣告 N-4 正式绑定已生效", "**不得写成「本笔已生效」**"]:
    _, _, h10 = R10FN(s, T)
    _, d13 = n13.r13_assertions(s, T, r10_scan=R10FN, r12_scan=g7.r12_scan)
    print("   %-32s R10 kinds=%s | N13 kinds=%s rules=%s" %
          (s[:30], [h["kind"] for h in h10], [d["kind"] for d in d13],
           [d["rule"][:36] for d in d13]))
print("\n-- (3b) R12 是否复用 r10_context：逐处比较 r12 hits 与 r10 double_neg hits")
SAMPLES = ["本件并非不宣告已生效", "审阅不得不承认本候选已生效", "亦非不宣告 N-4 正式绑定已生效",
           "并非不宣告已生效", "不得写成「本笔已生效」", "不宣告 X 已生效，但 Y 已入账"]
for s in SAMPLES:
    _, _, h10 = R10FN(s, T); _, h12 = g7.r12_scan(s, T)
    dns = [(h["token"], h["pos"]) for h in h10 if h["kind"] == "double_neg"]
    r12s = [(h["token"], h["pos"]) for h in h12]
    print("   %-36s R10_double_neg=%-22s R12_hits=%-22s 相同=%s" %
          (s[:34], str(dns), str(r12s), set(dns) == set(r12s)))
print("\n-- (3c) 三层共用字面词表（从 74 行 JSON 统计）:")
o = json.load((WD / "_gp_regression_out.json").open(encoding="utf-8"))
rows = o["rows"]
c = collections.Counter(tuple(r["tokens"]) for r in rows)
for k, v in c.most_common():
    print("   %2d/74 行 tokens=%s" % (v, list(k)))
print("   N13.DEFAULT_TOKENS =", T)
print("   judge_one(n13) 恒用 T；gate_check 的 n13_tokens 恒传 T；extract_spans/tok_set 用 n13_vocab=T")

print("\n### [4] 半定量：三层「都判 PASS」时的有效独立层数（74 行实测）")
pass_rows = [r for r in rows if r["n13"] == "PASS" and r["r10"] == "PASS" and r["r12"] == "PASS"]
print("   三层(R10,R12,N13) 全 PASS 的行: %d" % len(pass_rows))
print("   两两一致率（在 74 行上，PASS/CATCH 二值）:")
for a, b in [("naive", "r10"), ("naive", "n13"), ("r10", "r12"), ("r10", "n13"), ("r12", "n13")]:
    same = sum(1 for r in rows if r[a] == r[b])
    print("     %-6s vs %-6s same=%2d/74 = %.1f%%" % (a, b, same, 100.0 * same / 74))
n13p = [r for r in rows if r["n13"] == "PASS"]
for col in ("r10", "r12", "naive"):
    k = sum(1 for r in n13p if r[col] == "PASS")
    print("   P(%s=PASS | N13=PASS) = %d/%d = %.3f" % (col, k, len(n13p), k / len(n13p)))
wrong = [r for r in pass_rows if r["expect"] == "CATCH"]
print("   三层全 PASS 共 %d 行，其中 expect=CATCH（一起漏）= %d 行: %s" %
      (len(pass_rows), len(wrong), [r["id"] for r in wrong]))
allp = [r for r in rows if all(r[c] == "PASS" for c in ("naive", "r10", "r12", "n13"))]
print("   四层(naive,R10,R12,N13)全 PASS 共 %d 行，其中 expect=CATCH = %d 行: %s" %
      (len(allp), sum(1 for r in allp if r["expect"] == "CATCH"),
       [r["id"] for r in allp if r["expect"] == "CATCH"]))

print("\n### [5] K6/K3 分支在两件真实文档上的覆盖统计（词表不对齐的后果）")
for cid, (rel, toks, expect) in REAL.items():
    if cid == "REAL-BOUND":
        continue
    text = (pathlib.Path(ROOT) / rel).read_text(encoding="utf-8")
    r = P.gate_check(text, toks, WD, g7, n13, T)
    n13_vocab = set(T)
    out_of_vocab = [x for x in r["_rows"] if x["token"] not in n13_vocab]
    in_vocab = [x for x in r["_rows"] if x["token"] in n13_vocab]
    print("   %-11s spans=%3d  在 N13 三词内=%3d  词表外(K6 仅 R10 有答案)=%3d" %
          (cid, len(r["_rows"]), len(in_vocab), len(out_of_vocab)))
    print("      词表外 span 的裁决分布: %s" %
          dict(collections.Counter((x["verdict"], "/".join(x["rules"])) for x in out_of_vocab)))
