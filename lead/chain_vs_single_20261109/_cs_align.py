# -*- coding: utf-8 -*-
# _cs_align.py : 公平性对照实验（只读加载既有谓词；语料在本脚本内显式重建并与只读 JSON 逐行核对）
#   A. 复现 harness 原口径：N13 单层恒用固定三词 T
#   B. 对齐口径：N13 单层改用该行自己的 tokens（与 chain 的 gate_check 输入一致）
#   C. 换「R10 考题」「中性第三方考题」「留出集」看排名
# ★ 不使用 exec/eval 加载外部源码文本：用 importlib 正常导入 + 显式字面重建，
#   并以 JSON rows 的 (id,family,expect,tokens,text_head) 逐行核对重建保真度。
import os, sys, json, pathlib, importlib.util, hashlib, collections, re
ROOT = r"D:\Project\ra2-campaign-forge"
os.chdir(ROOT)
WD = pathlib.Path(ROOT) / "lead" / "gate_pipeline_20261109"
OUTDIR = WD.parent / "chain_vs_single_20261109"
N13_PATH = WD.parent / "gate_n13_20261109" / "_n13_predicates.py"
G7_PATH = WD.parent / "gate_fp7_20261108" / "_g7_predicates.py"
V12_PATH = WD.parent / "gate_v1v2_20261109" / "_v12_rule.py"
N13_REG = WD.parent / "gate_n13_20261109" / "_n13_regression.py"

def _load(path, name, want=None):
    raw = path.read_bytes()
    if want:
        assert (hashlib.sha256(raw).hexdigest(), len(raw)) == want, "fingerprint mismatch " + str(path)
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

g7 = _load(G7_PATH, "_cs_al_g7", ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743))
n13 = _load(N13_PATH, "_cs_al_n13", ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649))
v12 = _load(V12_PATH, "_cs_al_v12", ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148))
R10FN = g7.r10_scan
T = list(n13.DEFAULT_TOKENS)
T_C07_SLOT = ["已补登", "已填入", "已填", "已代填"]
T_C07_TRUTH = ["已填", "已代填", "已提交"]
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
reg = _load(N13_REG, "_cs_al_n13reg")  # 模块级无写操作，__main__ 有保护

# ---- 显式重建语料（逐字抄 _gp_regression.py:61-130，不执行其源码文本） ----
CORPUS = []
def add(cid, family, text, expect, tokens, note):
    CORPUS.append({"id": cid, "family": family, "text": text,
                   "expect": expect, "tokens": tokens, "note": note})

for sid, text, note, src in reg.NEGATIVES:
    add("N13-" + sid, "N13_NEG", text, "CATCH", T, "逐字：" + src + " | " + note)
for sid, text, expect, src in reg.POSITIVES:
    add("N13-" + sid, "N13_POS", text, "PASS", T, "逐字：" + src)
for name, rel, expect in [
    ("TV2", "lead/gate_fp7_20261108/_g7_tv2_overreach_positive.md", "CATCH"),
    ("TV3", "lead/gate_fp7_20261108/_g7_tv3_double_negation.md", "CATCH"),
]:
    add("R10-" + name, "R10_TV", (pathlib.Path(ROOT) / rel).read_text(encoding="utf-8"),
        expect, BAD_BAN, "逐字读盘 " + rel)
for rel in [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]:
    add("R10-REAL-" + pathlib.Path(rel).stem, "R10_REAL",
        (pathlib.Path(ROOT) / rel).read_text(encoding="utf-8"), "PASS", BAD_BAN,
        "逐字读盘 " + rel + "（g7 S1：R10 problems=0）")
for cid, text, note in [
    ("R10-CTX-01", "不宣告 N-4 正式绑定已生效。", "否定式（C）"),
    ("R10-CTX-02", "**不得写成「本笔已生效」**；本件只登记。", "禁止 + 引证跨度"),
    ("R10-CTX-03", "或回件出现「可应用/放行 N-5」断言", "短引证跨度内提及"),
    ("R10-CTX-04", "并无越权断言：本件不出现「可应用母本…」。", "两独立否定短语"),
    ("R10-CTX-05", "本件并非不宣告已生效", "双重否定（R12 应 CATCH）"),
    ("R10-CTX-06", "审阅不得不承认本候选已生效", "双重否定（R12 应 CATCH）"),
    ("R10-CTX-07", "**已入账核查实跑命令**：", "A 检索动作（N13 放过）"),
    ("R10-CTX-08", "## 2 · 上游指纹 + 已入账 grep 结果", "B 小节标题"),
    ("R10-CTX-09", "| 笔 | 已入账? |", "B 表头列名"),
    ("R10-CTX-10", "### 1(c) 有没有已入账的？", "A 问句"),
    ("R10-CTX-11", "本交付件改为五节：§1 总览 / §2 已入账 grep / §3 冲突", "B 目录枚举"),
]:
    exp = "CATCH" if cid in ("R10-CTX-05", "R10-CTX-06") else "PASS"
    add(cid, "R10_CTX", text, exp, BAD_BAN, "构造/逐字形态：" + note)
for cid, rel, toks, expect in [
    ("REAL-SLOT", "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md", T_C07_SLOT, "PASS"),
    ("REAL-TRUTH", "lead/c07_truth_protocol_20261109/C07_TRUTH_SELF_PROOF.md", T_C07_TRUTH, "PASS"),
    ("REAL-BOUND", "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", T, "PASS"),
]:
    add(cid, "REAL3", (pathlib.Path(ROOT) / rel).read_text(encoding="utf-8"), expect, toks,
        "逐字读盘 " + rel + "（编排方指纹已复核）")
for cid, text, expect, note in [
    ("GP-C01", "grep 结果：已生效，可应用母本", "CATCH", "F03：A 标记劫持真断言"),
    ("GP-C02", "不宣告 X 已生效，但 Y 已入账", "CATCH", "同句混用"),
    ("GP-C04", "并非不宣告已生效", "CATCH", "R12 双重否定"),
    ("GP-C05", "未核 grep 结果：已入账 0 命中", "PASS", "前置否定标签 + A 检索结果"),
    ("GP-C06", "未核 grep 结果：已生效 0 命中", "PASS", "同上（已生效）"),
    ("GP-C07", "未核：已入账 grep 结果 = 0 命中", "PASS", "同上（标签在冒号前）"),
    ("GP-C08", "grep 结果：已入账", "CATCH", "裸完成词拿不准默认 FAIL"),
    ("GP-C09", "未验：本笔已入账", "CATCH", "N19 前置标签 + 主语"),
    ("GP-C10", "grep 结果：第 5 笔已入账", "CATCH", "N20 A 标记 + 主语"),
]:
    add(cid, "GP_CONFLICT", text, expect, T, note)
for cid, text, note in [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", "分离型双重否定=肯定"),
    ("GP-A2", "本件登记闭合，母本即日起适用", "同义完成断言"),
    ("GP-A3", "三值填毕，见证已由编排方签字", "C07 域同义完成断言"),
]:
    add(cid, "GP_ALLPASS_TRUE_ASSERTION", text, "CATCH", T, note)

print("重建 CORPUS len =", len(CORPUS))

# ---- 逐行核对重建保真度（对只读 JSON） ----
O = json.loads((WD / "_gp_regression_out.json").read_text(encoding="utf-8"))
J = {r["id"]: r for r in O["rows"]}
mism = []
for it in CORPUS:
    j = J.get(it["id"])
    if j is None:
        mism.append((it["id"], "missing")); continue
    head = it["text"][:90].replace("\n", "\\n")
    if not (j["family"] == it["family"] and j["expect"] == it["expect"]
            and list(j["tokens"]) == list(it["tokens"]) and j["text_head"] == head):
        mism.append((it["id"], (j["family"], it["family"], j["expect"], it["expect"],
                                list(j["tokens"]) == list(it["tokens"]), j["text_head"] == head)))
print("重建 vs JSON 逐行核对: 共有 %d 行，不一致 %d 行 %s" % (len(J), len(mism), mism[:5]))

def stat(rows, key):
    ok = fp = fn = 0
    for r in rows:
        e, p = r["expect"], r[key]
        if e == p: ok += 1
        elif e == "PASS": fp += 1
        else: fn += 1
    return ok, fp, fn, len(rows)

aligned = []
for it in CORPUS:
    row = dict(J[it["id"]])          # 只读复制，带 harness 的 naive/r10/r12/n13/chain
    p, _ = n13.r13_assertions(it["text"], it["tokens"], r10_scan=R10FN, r12_scan=g7.r12_scan)
    row["n13_aligned"] = "CATCH" if p else "PASS"
    aligned.append(row)

print("\n### [A] 复现/对齐：全 74 条逐层成绩")
print("%-20s %9s %5s %5s %5s %8s" % ("layer", "correct", "fp", "fn", "n", "acc"))
for key, label in [("naive", "naive"), ("r10", "r10"), ("r12", "r12"),
                   ("n13", "n13(harness固定T)"), ("n13_aligned", "n13(对齐per-row)"),
                   ("chain", "chain")]:
    ok, fp, fn, n = stat(aligned, key)
    print("%-20s %9d %5d %5d %5d %7.2f%%" % (label, ok, fp, fn, n, 100.0 * ok / n))

print("\n### [B] 对齐后 N13 单层失败行（与 chain 对比）")
for r in aligned:
    if r["expect"] != r["n13_aligned"]:
        print("  %-14s fam=%-28s expect=%-5s n13_fixed=%-5s n13_aligned=%-5s chain=%-5s | %s"
              % (r["id"], r["family"], r["expect"], r["n13"], r["n13_aligned"], r["chain"], r["text_head"][:48]))
print("  对齐后 chain 与 n13_aligned 判定完全一致? ",
      all(r["chain"] == r["n13_aligned"] for r in aligned))
diff = [(r["id"], r["chain"], r["n13_aligned"]) for r in aligned if r["chain"] != r["n13_aligned"]]
print("  不一致条数 =", len(diff), diff[:10])

print("\n### [C] 换考题集排名（对齐口径 vs harness 口径）")
G = {
    "N13自家考题(42)": {"N13_NEG", "N13_POS"},
    "R10考题(17)": {"R10_TV", "R10_REAL", "R10_CTX"},
    "中性第三方(15)": {"REAL3", "GP_CONFLICT", "GP_ALLPASS_TRUE_ASSERTION"},
    "全74": None,
}
for name, fams in G.items():
    sub = aligned if fams is None else [r for r in aligned if r["family"] in fams]
    sc = [(k, stat(sub, k)[0]) for k in ("naive", "r10", "r12", "n13", "n13_aligned", "chain")]
    rank = sorted(sc, key=lambda x: -x[1])
    print("  %-22s n=%2d  %s" % (name, len(sub), " > ".join("%s=%d" % x for x in rank)))

print("\n### [D] 留出集推演：N13 自家 42 条按序号奇偶切 train/holdout")
n13own = [r for r in aligned if r["family"] in {"N13_NEG", "N13_POS"}]
for tag, keep in [("train(奇数序号)", lambda i: i % 2 == 1), ("holdout(偶数序号)", lambda i: i % 2 == 0)]:
    sub = [r for i, r in enumerate(n13own) if keep(i)]
    print("  %-20s n=%2d  " % (tag, len(sub)),
          "  ".join("%s=%d" % (k, stat(sub, k)[0]) for k in ("n13", "n13_aligned", "chain")))

print("\n### [E] 中性第三方 15 条上各层 FP/FN 明细")
sub = [r for r in aligned if r["family"] in {"REAL3", "GP_CONFLICT", "GP_ALLPASS_TRUE_ASSERTION"}]
for k in ("naive", "r10", "r12", "n13", "n13_aligned", "chain"):
    ok, fp, fn, n = stat(sub, k)
    print("  %-14s ok=%2d fp=%d fn=%d n=%d" % (k, ok, fp, fn, n))

print("\n### [F] V1V2 独立谓词在 GP-A 三条上的覆盖（独立证据能兜住吗）")
for cid in ("GP-A1", "GP-A2", "GP-A3"):
    it = next(x for x in CORPUS if x["id"] == cid)
    s = it["text"]
    hits = []
    for tok in set(list(v12.V2_OVERRIDE) + ["已生效", "签字", "适用"]):
        for m in re.finditer(re.escape(tok), s):
            c = v12.classify_v12(s, m.start(), m.end(), tok)
            if c["verdict"] == "V2":
                hits.append((tok, m.start(), c["reason"][:32]))
    print("  %-6s %-32s V2命中=%s" % (cid, s[:30], hits if hits else "无"))

out = {"rebuild_consistent": len(mism) == 0,
       "aligned_per_row": [{"id": r["id"], "family": r["family"], "expect": r["expect"],
                            "n13_fixed": r["n13"], "n13_aligned": r["n13_aligned"],
                            "chain": r["chain"]} for r in aligned]}
(OUTDIR / "_cs_align_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _cs_align_out.json")
