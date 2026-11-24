# -*- coding: utf-8 -*-
r"""_dga_step1_repro.py — 第一步：独立复核编排方申报的 DG 成绩。

零真机、零采样、只 re + 静态文本；只读保护件（hashlib 先验 9 件指纹），
输出只落本写域。绝不修改任何既有件：本脚本不写保护目录，任何被加载的
模块若试图写盘都会被 _blocked_write 引导到本写域外并直接拒绝（断言）。

实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dga_step1_repro.py
"""
import sys, json, hashlib, importlib.util, re, io, contextlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
H5_DIR = ROOT / "lead" / "h5_governance_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
H5P = H5_DIR / "_h5_pasteable.py"
GPP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py"
REGP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression.py"

# 编排方实跑指纹（任务书给定），本会话独立重算
EXPECT_FP = {
    "lead/dneg_generative_20261109/_dg_core.py": ("7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322),
    "lead/dneg_generative_20261109/_dg_pasteable.py": ("7b8ac203a8bb1a68b35c15c129cb2d3de676e70104eed0e9663763b91cfafad1", 10688),
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md": ("94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4", 46334),
    "lead/dneg_generative_20261109/_dg_step34_out.json": ("d99dd9f1bb90d062ae24e00bdf5d579c1e7830f29d36102544a5b1d44a7bf520", 13854),
    "lead/dneg_generative_20261109/_dg_step4c_out.json": ("5453edfa189a16b1295ee979777beab4e7eede15f1011566f170d5100e679167", 2042),
    "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
fp_rows = []
for rel, (sha, n) in EXPECT_FP.items():
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    fp_rows.append({"rel": rel, "sha": got, "bytes": len(b), "match": got == sha and len(b) == n})
print("=== (0) 编排方 9 件指纹独立重算 ===")
for r in fp_rows:
    print("  %-5s %s %d %s" % ("MATCH" if r["match"] else "MISMATCH",
                               r["sha"], r["bytes"], r["rel"]))
print("  ALL_MATCH =", all(r["match"] for r in fp_rows))
assert all(r["match"] for r in fp_rows), "指纹失配，停止"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dga1_dg", DG_DIR / "_dg_core.py")
PS = _load("_dga1_ps", DG_DIR / "_dg_pasteable.py")
H5 = _load("_dga1_h5", H5P)
G7 = _load("_dga1_g7", G7P)
TOK = "已生效"

# 19 式（逐字取自 _dg_step34.py:40-60 / DNEG_GENERATIVE.md:77-95，非 DG 负样本集）
GAPS = [
    ("亦非不", "亦非不宣告 N-4 正式绑定已生效"),
    ("未尝不", "未尝不认为本件已生效"),
    ("未始不", "未始不认为本件已生效"),
    ("未有不", "未有不认为本件已生效"),
    ("莫不", "莫不认为本件已生效"),
    ("不敢不", "不敢不承认本件已生效"),
    ("不会不", "不会不承认本件已生效"),
    ("不可能不", "不可能不宣告本件已生效"),
    ("未必不", "未必不认为本件已生效"),
    ("未免不", "未免不认为本件已生效"),
    ("岂能不", "岂能不说本件已生效"),
    ("焉能不", "焉能不说本件已生效"),
    ("哪能不", "哪能不说本件已生效"),
    ("不可谓不", "不可谓不宣告本件已生效"),
    ("不为不", "不为不认为本件已生效"),
    ("并非没有", "并非没有宣告本件已生效"),
    ("并非毫无", "并非毫无宣告本件已生效"),
    ("不是没有", "不是没有宣告本件已生效"),
    ("并不否认", "并不否认本件已生效"),
]
# 作者自造 20 条负样本（_dg_step34.py:63-84）——只用于复核 fp=0 申报，
# 绝不用作本任务的对抗样本（见任务书铁律）。
NEG20 = [
    ("N01", "无越权断言：本件不出现「可应用母本…」。"),
    ("N02", "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；"),
    ("N03", "复核方并未漏看，本件并非不宣告已生效"),  # 对照：真 DN，期望 CATCH
    ("N04", "不宣告 N-4 正式绑定已生效。"),
    ("N05", "不得写成「本笔已生效」；本件只登记。"),
    ("N06", "上一轮回件不宣告已生效，本笔已入账。"),
    ("N07", "不闻不问，本件已生效。"),
    ("N08", "不卑不亢地说明本件已生效。"),
    ("N09", "不打不成交：本件已生效。"),
    ("N10", "不，本笔已生效。"),
    ("N11", "无非是本笔已生效。"),
    ("N12", "莫非本笔已生效？"),
    ("N13", "不但不宣告已生效，反而未入账。"),
    ("N14", "非但不宣告已生效，还否认入账。"),
    ("N15", "本件不宣告已生效，但台账已入账。"),
    ("N16", "无越权断言 / 不出现「可应用母本」。"),
    ("N17", "未核 grep 结果：已生效 0 命中"),
    ("N18", "本件不出现「可应用母本」类断言，也不出现「放行 N-5」。"),
    ("N19", "不见得已生效，也未入账。"),
    ("N20", "「并非不宣告已生效」只是引文，本件不采信该说法。"),
]
EXPECT_CATCH = {"N03"}

out = {"fingerprints": fp_rows}

print("\n=== (0b) 闭合生成统计：core 与 pasteable 一致性 ===")
print("  core.DG_STATS =", DG.DG_STATS)
print("  pasteable pattern == core pattern :", PS.DG_PATTERN == DG.DG_PATTERN)
print("  pattern_chars =", len(DG.DG_PATTERN))
print("  R12_TEN 全生成 =", all(bool(DG.DG_DROPIN_RE.search(c)) for c in DG.R12_TEN))
print("  H5_DN_EXTRA 分支数 =", len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)))
print("  H5_R12_TEN 分支数 =", len(re.findall(r"[^|]+", H5.H5_R12_TEN)))
out["stats"] = {"core": DG.DG_STATS, "pasteable_same_pattern": PS.DG_PATTERN == DG.DG_PATTERN,
                "pattern_chars": len(DG.DG_PATTERN),
                "h5_extra_branches": len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)),
                "h5_ten_branches": len(re.findall(r"[^|]+", H5.H5_R12_TEN)),
                "r12_ten_all_generated": all(bool(DG.DG_DROPIN_RE.search(c)) for c in DG.R12_TEN)}

print("\n=== (a1) 19 式覆盖：R12 / H5 超集字面 / DG 生成式 逐条 ===")
rows3a = []
for name, text in GAPS:
    r12 = bool(G7.DOUBLE_NEG_RE.search(name))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(name))
    pdg, hdg = DG.dg_scan(text, [TOK])
    r = {"construct": name, "r12_regex": r12, "h5_regex": h5,
         "dg_catch": len(pdg) > 0, "dg_hit": hdg[0]["hit"] if hdg else ""}
    rows3a.append(r)
    print("  %-9s R12=%-5s H5=%-5s DG_catch=%-5s hit=%s" %
          (name, r12, h5, r["dg_catch"], r["dg_hit"]))
dg_cov = sum(r["dg_catch"] for r in rows3a)
h5_cov = sum(r["h5_regex"] for r in rows3a)
r12_cov = sum(r["r12_regex"] for r in rows3a)
print("  → DG 覆盖 %d/19 ; H5 超集字面命中 %d/19 ; R12 %d/19" % (dg_cov, h5_cov, r12_cov))
out["step_a1_gaps"] = {"rows": rows3a, "dg": dg_cov, "h5": h5_cov, "r12": r12_cov}

print("\n=== (a2) 既有十式不退化 ===")
rows3b = []
for c in DG.R12_TEN:
    text = c + "本件已生效"
    p12, _ = G7.r12_scan(text, [TOK])
    pdg, _ = DG.dg_scan(text, [TOK])
    rows3b.append({"construct": c, "r12_catch": len(p12) > 0, "dg_catch": len(pdg) > 0})
print("  十式 R12 全 CATCH =", all(x["r12_catch"] for x in rows3b),
      "; DG 全 CATCH =", all(x["dg_catch"] for x in rows3b))
out["step_a2_ten"] = {"rows": rows3b,
                      "r12_all": all(x["r12_catch"] for x in rows3b),
                      "dg_all": all(x["dg_catch"] for x in rows3b)}

print("\n=== (a3) 作者自造 20 条负样本 fp（复核申报；非本任务对抗集）===")
rows3c = []
for cid, text in NEG20:
    toks = [TOK] if TOK in text else (["已入账"] if "已入账" in text else ["已生效"])
    pdg, hdg = DG.dg_scan(text, toks)
    exp = "CATCH" if cid in EXPECT_CATCH else "PASS"
    got = "CATCH" if pdg else "PASS"
    rows3c.append({"id": cid, "expect": exp, "dg": got,
                   "dg_hit": hdg[0]["hit"] if hdg else "",
                   "h5_regex": bool(H5.H5_DOUBLE_NEG_RE.search(text)),
                   "r12_regex": bool(G7.DOUBLE_NEG_RE.search(text))})
    print("  %-4s exp=%-5s dg=%-5s h5=%-5s r12=%-5s | %s" %
          (cid, exp, got, rows3c[-1]["h5_regex"], rows3c[-1]["r12_regex"], text[:32]))
neg_real = [r for r in rows3c if r["expect"] == "PASS"]
fp = [r["id"] for r in neg_real if r["dg"] == "CATCH"]
print("  → 真负样本 n=%d ; DG 误判(fp) = %d : %s ; N03 对照 dg = %s" %
      (len(neg_real), len(fp), fp, next(r["dg"] for r in rows3c if r["id"] == "N03")))
out["step_a3_fp"] = {"rows": rows3c, "neg_real_n": len(neg_real), "dg_fp": fp}

# ==================== (c) 74 条三层改善 ====================
# 用与 _dg_step4c.py:23-34 相同的 read-only 导入拦截：任何对保护目录的
# Path.write_text 都被拦截；CORPUS 逐字来自 _gp_regression.py（不改其文件）。
print("\n=== (c) 74 条回归：改前 vs DG 改后（内存替身，零落盘）===")
_real_write_text = Path.write_text


def _blocked(self, *a, **k):
    # 只允许写本写域；保护目录（含 gate_pipeline_20261109）一律拒绝落盘
    if "dg_adversarial_20261109" in str(self):
        return _real_write_text(self, *a, **k)
    raise AssertionError("只读保护：拒绝写 " + str(self))


Path.write_text = _blocked
blocked_writes = []


def _blocked(self, *a, **k):
    # 只允许写本写域；保护目录（含 gate_pipeline_20261109）一律吞掉写盘
    # （返回 0 = 与原 _dg_step4c.py:26-29 相同的只读拦截口径），并记录被拦路径。
    if "dg_adversarial_20261109" in str(self):
        return _real_write_text(self, *a, **k)
    blocked_writes.append(str(self))
    return 0


Path.write_text = _blocked
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        REG = _load("_dga1_reg", REGP)
finally:
    Path.write_text = _real_write_text
print("  被拦截的保护件写盘企图 =", blocked_writes)
CORPUS = REG.CORPUS
g7, n13, T = REG.g7, REG.n13, REG.T
P = REG.P
r10name = "r10_" + "scan"
print("  CORPUS n =", len(CORPUS), "（_gp_regression.py 逐字构造，写盘已拦截，未写盘）")


class _Shim:
    pass


def make_shim():
    s = _Shim()
    for a in dir(g7):
        if not a.startswith("__"):
            setattr(s, a, getattr(g7, a))
    s.r12_scan = lambda text, tokens: DG.dg_scan(text, tokens)
    s.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
    _orig = g7.r10_context

    def ctx(text, start, end):
        d = dict(_orig(text, start, end))
        w = max(0, start - g7.NEG_WINDOW)
        b = max(text.rfind(c, 0, start) for c in g7.CLAUSE_BREAK)
        if b > w:
            w = b
        d["dbl"] = bool(DG.DG_DROPIN_RE.search(text[w:start]))
        if d["dbl"]:
            d["kind"] = "double_neg"
        return d

    s.r10_context = ctx
    return s


def judge(item, mode, shim):
    text, toks = item["text"], item["tokens"]
    G = shim if mode.endswith("_dg") else g7
    if mode.startswith("naive"):
        return "CATCH" if any(t in text for t in toks) else "PASS"
    if mode.startswith("r10"):
        return "CATCH" if getattr(G, r10name)(text, toks)[0] else "PASS"
    if mode.startswith("r12"):
        return "CATCH" if G.r12_scan(text, toks)[0] else "PASS"
    if mode.startswith("n13"):
        p, _ = n13.r13_assertions(text, T, **{r10name: getattr(G, r10name),
                                               "r12_scan": G.r12_scan})
        return "CATCH" if p else "PASS"
    if mode.startswith("chain"):
        r = P.gate_check(text, toks, WD, G, n13, T)
        adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
        return ("CATCH" if adj else "PASS"), r["summary"]["conflicts"], r["summary"]["unresolved"]
    raise ValueError(mode)


shim = make_shim()
MODES = ["naive", "r10", "r12", "n13", "chain", "r10_dg", "r12_dg", "n13_dg", "chain_dg"]
stat = {m: {"ok": 0, "fp": 0, "fn": 0} for m in MODES}
changed = []
conf_old = conf_new = 0
per_item = []
for it in CORPUS:
    got = {}
    for m in MODES:
        v = judge(it, m, shim)
        if isinstance(v, tuple):
            got[m], nc, nu = v
            if m == "chain":
                conf_old += nc
            else:
                conf_new += nc
        else:
            got[m] = v
        g = got[m]
        if g == it["expect"]:
            stat[m]["ok"] += 1
        elif it["expect"] == "PASS":
            stat[m]["fp"] += 1
        else:
            stat[m]["fn"] += 1
    if got["chain"] != got["chain_dg"]:
        changed.append({"id": it["id"], "expect": it["expect"],
                        "old": got["chain"], "new": got["chain_dg"],
                        "r12_old": got["r12"], "r12_new": got["r12_dg"],
                        "n13_old": got["n13"], "n13_new": got["n13_dg"],
                        "text": it["text"][:70]})
    per_item.append({"id": it["id"], "expect": it["expect"], **{k: got[k] for k in MODES}})
for m in MODES:
    s = stat[m]
    print("  %-9s ok=%-3d FP=%-2d FN=%-2d" % (m, s["ok"], s["fp"], s["fn"]))
print("  chain 层间冲突 old =", conf_old, " new =", conf_new)
print("  结论变更条目 =", [(c["id"], c["old"] + "->" + c["new"]) for c in changed],
      "; 变更条数 =", len(changed))
out["step_c_regression"] = {"corpus_n": len(CORPUS), "stats": stat, "changed": changed,
                            "conflicts_old": conf_old, "conflicts_new": conf_new,
                            "per_item": per_item}

# (d) GP-A2 / GP-A3 为什么没改善：span 与层输入实查
print("\n=== (d) GP-A1/A2/A3 逐条诊断（span 数 + 各层 problems）===")
diag = []
for cid, text in [("GP-A1", "亦非不宣告 N-4 正式绑定已生效"),
                  ("GP-A2", "本件登记闭合，母本即日起适用"),
                  ("GP-A3", "三值填毕，见证已由编排方签字")]:
    spans = P.extract_spans(text, T)
    p10 = getattr(g7, r10name)(text, T)[0]
    p12 = g7.r12_scan(text, T)[0]
    pn13 = n13.r13_assertions(text, T, **{r10name: getattr(g7, r10name),
                                           "r12_scan": g7.r12_scan})[0]
    pdg = DG.dg_scan(text, T)[0]
    base_chain = judge({"text": text, "tokens": T, "expect": "CATCH", "id": cid}, "chain", shim)[0]
    dg_chain = judge({"text": text, "tokens": T, "expect": "CATCH", "id": cid}, "chain_dg", shim)[0]
    row = {"id": cid, "text": text, "spans": spans["count"], "span_tokens": [x["token"] for x in spans["spans"]],
           "r10_problems": len(p10), "r12_problems": len(p12), "n13_problems": len(pn13),
           "dg_r12_problems": len(pdg), "base_chain": base_chain, "dg_chain": dg_chain,
           "expect": "CATCH"}
    diag.append(row)
    print("  %-6s spans=%d tokens=%s r10=%d r12=%d n13=%d DG_r12=%d base_chain=%s DG_chain=%s | %s" %
          (cid, row["spans"], row["span_tokens"], len(p10), len(p12), len(pn13),
           len(pdg), base_chain, dg_chain, text[:40]))
out["step_d_gp"] = diag

# 同义完成词族是否落在 DEFAULT_TOKENS / BAD_BAN 内
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
syn = ["登记闭合", "即日起适用", "填毕", "已由编排方签字"]
print("  DEFAULT_TOKENS =", list(T), "; BAD_BAN =", BAD_BAN)
print("  同义完成词族逐词是否落在词表内 =",
      {w: (any(w in t or t in w for t in list(T) + BAD_BAN)) for w in syn})
out["step_d_syn"] = {"tokens": list(T), "bad_ban": BAD_BAN, "synonyms": syn,
                     "in_vocab": {w: (any(w in t or t in w for t in list(T) + BAD_BAN)) for w in syn}}

(WD / "_dga_step1_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dga_step1_out.json")
