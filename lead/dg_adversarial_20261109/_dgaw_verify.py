# -*- coding: utf-8 -*-
r"""_dgaw_verify.py — DG 对抗撰写员【本会话独立复核】脚本（只读保护件）。

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgaw_verify.py
输出：_dgaw_verify_stdout.txt / _dgaw_verify_out.json（均落唯一写域）。
零真机、零采样；只 re / AST / hashlib / 静态文本；不写任何保护件。
"""
import sys, re, ast, json, hashlib, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

EXPECT_FP = [
    ("lead/dneg_generative_20261109/_dg_core.py", "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322),
    ("lead/dneg_generative_20261109/_dg_pasteable.py", "7b8ac203a8bb1a68b35c15c129cb2d3de676e70104eed0e9663763b91cfafad1", 10688),
    ("lead/dneg_generative_20261109/DNEG_GENERATIVE.md", "94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4", 46334),
    ("lead/dneg_generative_20261109/_dg_step34_out.json", "d99dd9f1bb90d062ae24e00bdf5d579c1e7830f29d36102544a5b1d44a7bf520", 13854),
    ("lead/dneg_generative_20261109/_dg_step4c_out.json", "5453edfa189a16b1295ee979777beab4e7eede15f1011566f170d5100e679167", 2042),
    ("lead/h5_governance_20261109/_h5_pasteable.py", "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    ("lead/gate_fp7_20261108/_g7_predicates.py", "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]
OUT = {}

print("=== (0) 九件指纹：本会话 hashlib 独立重算 ===")
def fingerprints():
    ok_all = True
    for rel, sha, n in EXPECT_FP:
        b = (ROOT / rel).read_bytes()
        ok = hashlib.sha256(b).hexdigest() == sha and len(b) == n
        ok_all &= ok
        print("  %s %s %d" % ("MATCH" if ok else "MISMATCH", rel, len(b)))
    print("  ALL_MATCH =", ok_all)
    return ok_all
fp_start = fingerprints()
OUT["fp_start"] = fp_start


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgaw_dg", DG_DIR / "_dg_core.py")
PS = _load("_dgaw_ps", DG_DIR / "_dg_pasteable.py")
H5 = _load("_dgaw_h5", H5P)
G7 = _load("_dgaw_g7", G7P)
DROP = _load("_dgaw_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

print("\n=== (1) 19 式覆盖 + 十式不退化 + pasteable 一致性 ===")
GAPS19 = ["亦非不", "未尝不", "未始不", "未有不", "莫不", "不敢不", "不会不", "不可能不",
          "未必不", "未免不", "岂能不", "焉能不", "哪能不", "不可谓不", "不为不",
          "并非没有", "并非毫无", "不是没有", "并不否认"]
n_dg = sum(1 for g in GAPS19 if DG.DG_DROPIN_RE.search(g))
n_h5 = sum(1 for g in GAPS19 if H5.H5_DOUBLE_NEG_RE.search(g))
n_r12 = sum(1 for g in GAPS19 if G7.DOUBLE_NEG_RE.search(g))
ten = list(DG.R12_TEN)
ten_dg = all(bool(DG.DG_DROPIN_RE.search(c)) for c in ten)
ten_r12 = all(bool(G7.DOUBLE_NEG_RE.search(c)) for c in ten)
print("  DG 19 式 = %d/19 ; H5 字面超集 = %d/19 ; R12 = %d/19" % (n_dg, n_h5, n_r12))
print("  十式 DG 全 CATCH = %s ; R12 全 CATCH = %s ; n(十式) = %d" % (ten_dg, ten_r12, len(ten)))
print("  core.pattern == pasteable.pattern =", PS.DG_PATTERN == DG.DG_PATTERN,
      "; pattern_chars =", DG.DG_STATS["pattern_chars"])
print("  DG_STATS =", DG.DG_STATS)
OUT["cover"] = {"dg19": n_dg, "h5_19": n_h5, "r12_19": n_r12, "ten_dg": ten_dg,
                "ten_r12": ten_r12, "pattern_equal": PS.DG_PATTERN == DG.DG_PATTERN,
                "stats": DG.DG_STATS}

print("\n=== (2) H5_DN_EXTRA 选择支：sre_parse BRANCH arity 精确解析 ===")
import sre_parse


def branch_arity(pattern):
    parsed = list(sre_parse.parse(pattern))
    arity = 1
    for op, av in parsed:
        if op == sre_parse.BRANCH:
            arity = len(av[1])
    return arity, parsed


a_extra, parsed_extra = branch_arity(H5.H5_DN_EXTRA)
a_ten, parsed_ten = branch_arity(H5.H5_R12_TEN)
print("  H5_DN_EXTRA 顶层 BRANCH arity = %d ; 其中纯字面支 = %d ; 含通配/内层选择支 = %d"
      % (a_extra, a_extra - 1, 1))
print("  H5_R12_TEN 顶层 BRANCH arity = %d" % a_ten)
print("  → 合计选择支 = %d + %d = %d" % (a_extra, a_ten, a_extra + a_ten))
print("  朴素 re.findall(r'[^|]+', H5_DN_EXTRA) =", len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)))
print("  朴素 re.findall(r'[^|]+', H5_R12_TEN)  =", len(re.findall(r"[^|]+", H5.H5_R12_TEN)))
print("  H5_DN_EXTRA 源码 =", H5.H5_DN_EXTRA)
print("  H5_DOUBLE_NEG_RE.pattern 长度 =", len(H5.H5_DOUBLE_NEG_RE.pattern))
OUT["h5_branches"] = {"extra_arity": a_extra, "ten_arity": a_ten,
                      "total": a_extra + a_ten,
                      "naive_extra": len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)),
                      "naive_ten": len(re.findall(r"[^|]+", H5.H5_R12_TEN)),
                      "h5_pattern_chars": len(H5.H5_DOUBLE_NEG_RE.pattern)}

print("\n=== (3) 作者 20 条负样本：pure / dropin / base_r12 三口径 fp ===")
src = ast.parse((WD / "_dga_step1_repro.py").read_text(encoding="utf-8"))
NEG20 = EXPECT = None
for node in src.body:
    if isinstance(node, ast.Assign):
        names = [getattr(t, "id", "") for t in node.targets]
        if "NEG20" in names:
            NEG20 = ast.literal_eval(node.value)
        if "EXPECT_CATCH" in names:
            EXPECT = ast.literal_eval(node.value)
assert NEG20 and len(NEG20) == 20
neg_rows = []
for cid, text in NEG20:
    toks = [t for t in TOKS if t in text] or ["已生效"]
    pp, _ = DG.dg_scan(text, toks)
    pd, _ = DROP.r12_scan(text, toks)
    pb, _ = G7.r12_scan(text, toks)
    exp = "CATCH" if cid in EXPECT else "PASS"
    neg_rows.append({"id": cid, "text": text, "exp": exp,
                     "pure": "CATCH" if pp else "PASS",
                     "dropin": "CATCH" if pd else "PASS",
                     "base": "CATCH" if pb else "PASS"})
for form in ("pure", "dropin", "base"):
    fp = [r["id"] for r in neg_rows if r["exp"] == "PASS" and r[form] == "CATCH"]
    print("  %-7s 真负样本 n=19 ; fp = %d %s" % (form, len(fp), fp))
print("  N03 对照（应 CATCH）pure/dropin/base =", [next(r[f] for r in neg_rows if r["id"] == "N03")
                                                for f in ("pure", "dropin", "base")])
OUT["neg20"] = {"fp": {f: [r["id"] for r in neg_rows if r["exp"] == "PASS" and r[f] == "CATCH"]
                       for f in ("pure", "dropin", "base")}, "rows": neg_rows}

print("\n=== (4) 41 条自造对抗集：AST 抽取（不执行）+ 六判定器独立重算 ===")
asrc = ast.parse((WD / "_dga_adversarial.py").read_text(encoding="utf-8"))
CASES = FORCED = None
for node in asrc.body:
    if isinstance(node, ast.Assign):
        names = [getattr(t, "id", "") for t in node.targets]
        if "CASES" in names:
            CASES = ast.literal_eval(node.value)
        if "FORCED" in names:
            FORCED = ast.literal_eval(node.value)
assert CASES and len(CASES) == 41 and FORCED
TRAIN_FILES = [DG_DIR / "_dg_step34.py", DG_DIR / "_dgv_probe.py",
               DG_DIR / "_dgv_neg2.py", DG_DIR / "_dg_step1.py"]
train_all = set()
train_per = []
for p in TRAIN_FILES:
    t = ast.parse(p.read_text(encoding="utf-8"))
    s = {n.value for n in ast.walk(t)
         if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    train_per.append((p.name, len(s)))
    train_all |= s
overlap = sorted({c[2] for c in CASES} & train_all)
print("  自造样本数 = 41 ; 训练集逐件抽取串数 =", train_per, "; 精确重合 =", len(overlap), overlap)
assert not overlap


def detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {}
    p, _ = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    r["H5_lit"] = "CATCH" if H5.H5_DOUBLE_NEG_RE.search(text) else "PASS"
    hg = False
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            if H5.h5_govern(text[:m.start()], text[m.end():])["double_neg"]:
                hg = True
    r["H5_gov"] = "CATCH" if hg else "PASS"
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    r["R12_lit"] = "CATCH" if G7.DOUBLE_NEG_RE.search(text) else "PASS"
    return r


DETS = ("DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit")
rows = []
for cid, shape, text, exp, why, attack in CASES:
    r = detect(text)
    rows.append({"id": cid, "shape": shape, "text": text, "exp": exp,
                 "forced": FORCED.get(cid, exp), "why": why, "attack": attack, **r})
    print("  %-4s exp=%-5s | DG_p=%-5s DG_d=%-5s H5_l=%-5s H5_g=%-5s R12=%-5s R12_l=%-5s | %s"
          % (cid, exp, r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["H5_gov"],
             r["R12"], r["R12_lit"], text[:44]))


def fpfn(mode, strict):
    fp, fn, n = [], [], 0
    for x in rows:
        e = x["exp"] if strict else x["forced"]
        if strict and e == "AMBIG":
            continue
        n += 1
        if e == "PASS" and x[mode] == "CATCH":
            fp.append(x["id"])
        elif e == "CATCH" and x[mode] == "PASS":
            fn.append(x["id"])
    return n, fp, fn


print("\n  --- strict（排除 5 条 AMBIG）---")
for d in DETS:
    n, fp, fn = fpfn(d, True)
    print("  %-10s n=%d fp=%d %s fn=%d %s" % (d, n, len(fp), fp, len(fn), fn))
print("  --- forced（41 条全计）---")
for d in DETS:
    n, fp, fn = fpfn(d, False)
    print("  %-10s n=%d fp=%d fn=%d" % (d, n, len(fp), len(fn)))
print("  P 组 n=17 应 PASS ; DG_pure fp = %d/17" % len(fpfn("DG_pure", True)[1]))
print("  C 组 n=19 应 CATCH ; DG_pure fn = %d/19"
      % len([x for x in rows if x["id"].startswith("C") and x["exp"] == "CATCH"
             and x["DG_pure"] == "PASS"]))
# 逐条独对
def solo(a, b):
    ok_a = [x["id"] for x in rows if x["exp"] != "AMBIG" and
            ((x["exp"] == "PASS" and x[a] == "PASS") or (x["exp"] == "CATCH" and x[a] == "CATCH")) and
            not ((x["exp"] == "PASS" and x[b] == "PASS") or (x["exp"] == "CATCH" and x[b] == "CATCH"))]
    ok_b = [x["id"] for x in rows if x["exp"] != "AMBIG" and
            ((x["exp"] == "PASS" and x[b] == "PASS") or (x["exp"] == "CATCH" and x[b] == "CATCH")) and
            not ((x["exp"] == "PASS" and x[a] == "PASS") or (x["exp"] == "CATCH" and x[a] == "CATCH"))]
    return ok_a, ok_b
for other in ("H5_lit", "H5_gov", "R12", "DG_dropin"):
    a, b = solo("DG_pure", other)
    print("  DG_pure vs %-10s : DG 独对 %d %s ; 对方独对 %d %s" % (other, len(a), a, len(b), b))
OUT["cases"] = {"n": len(rows), "overlap": overlap, "train_per": train_per,
                "strict": {d: {"fp": fpfn(d, True)[1], "fn": fpfn(d, True)[2]} for d in DETS},
                "forced": {d: {"fp": fpfn(d, False)[1], "fn": fpfn(d, False)[2]} for d in DETS},
                "rows": rows}

print("\n=== (5) 7 条不变式：逐处实跑攻击 ===")
unreg = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "可", "反倒说",
         "结果", "终究", "总而言之", "归根结底", "话说回来", "退一步说"]
base = "前稿不敢不承认{}本件不宣告已生效"
i1 = []
for w in unreg:
    r = detect(base.format(w))
    i1.append({"w": w, "break": bool(DG.DG_BREAK_RE.search(w)), "dg": r["DG_pure"],
               "drop": r["DG_dropin"]})
    print("  ① %-6s BREAK=%-5s DG_pure=%-5s DG_dropin=%-5s（应 PASS）"
          % (w, i1[-1]["break"], r["DG_pure"], r["DG_dropin"]))
print("  → 未登记边界词 DG_pure 仍 CATCH 的条数 =",
      sum(1 for x in i1 if x["dg"] == "CATCH"), "/", len(unreg))
reg10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
i1b = [{"w": w, "pure": detect(base.format(w))["DG_pure"],
        "drop": detect(base.format(w))["DG_dropin"]} for w in reg10]
print("  ①b 已登记 10 词：DG_pure=PASS =", sum(1 for x in i1b if x["pure"] == "PASS"),
      "/10 ; DG_dropin=CATCH =", sum(1 for x in i1b if x["drop"] == "CATCH"), "/10")
qcases = [("「」内置空格(登记)", "「 并非不宣告已生效 」只是引文，本件不采信该说法"),
          ("ASCII 双引号(未登记)", '"并非不宣告已生效"只是引文，本件不采信该说法'),
          ("书名号《》(未登记)", "《并不否认已生效》只是引文，本件不采信该说法"),
          ("ASCII 括号(未登记)", "(并非不宣告已生效)只是引文，本件不采信该说法"),
          ("ASCII 单引号(未登记)", "'并非不宣告已生效'只是引文，本件不采信该说法")]
i2 = []
for tag, t in qcases:
    r = detect(t)
    i2.append({"tag": tag, **r})
    print("  ② %-22s exp=PASS DG_pure=%-5s DG_dropin=%-5s R12=%-5s H5_lit=%-5s"
          % (tag, r["DG_pure"], r["DG_dropin"], r["R12"], r["H5_lit"]))
print("  ② DG_QUOTE_RE 4 类 =", DG.DG_QUOTE_RE.pattern)
mid_miss = []
for m in ("容", "许", "想", "愿", "甘", "料", "要", "需", "欲"):
    t = "不%s不宣告本件已生效" % m
    dg = detect(t)["DG_pure"]
    mid_miss.append({"mid": m, "in_table": m in DG.MID, "dg": dg})
    print("  ③ MID=%s 在表内=%-5s DG_pure=%-5s（应 CATCH）" % (m, m in DG.MID, dg))
print("  → MID 未登记且真 DN 漏判 =", [x["mid"] for x in mid_miss if x["dg"] == "PASS"])
comp = []
for n in range(0, 8):
    t = "非登记%s不可才算本件已生效" % ("原" * n)
    dg = detect(t)["DG_pure"]
    comp.append({"n": n, "dg": dg})
    print("  ③ COMP 字数=%d DG_pure=%-5s" % (n, dg))
print("  → ≤4 全 CATCH =", all(x["dg"] == "CATCH" for x in comp if x["n"] <= 4),
      "; ≥5 全 PASS =", all(x["dg"] == "PASS" for x in comp if x["n"] >= 5))
neg2_full = [w for w in ("否认", "不承认", "不认为", "不宣告", "不出现") if w in DG.NEG2]
print("  ③ NEG2 含完整否定谓语 =", neg2_full,
      "| '并不否认与监理方不宣告已生效' → DG_pure =",
      detect("并不否认与监理方不宣告已生效")["DG_pure"])
second_terms = DG._SECOND.split("|")
tabs = (DG.NEG1, DG.MID, DG.NEG2, DG.GAP, DG.SCOPE_VERB, DG.SPLIT_TAIL, DG.PSEUDO_DN)
appear = {t: [name for name, tab in zip(
              ("NEG1", "MID", "NEG2", "GAP", "SCOPE_VERB", "SPLIT_TAIL", "PSEUDO_DN"), tabs)
              if any(t in w for w in tab)] for t in second_terms}
nonempty = {k: v for k, v in appear.items() if v}
print("  ④ _SECOND 任一项出现在任何闭合表条目内 =", nonempty, "（全空 ⇒ 结构性不可达）")
print("  ④ 反例A '并非本件不宣告已生效'（真 DN 应 CATCH）DG_pure =",
      detect("并非本件不宣告已生效")["DG_pure"],
      "H5_lit =", detect("并非本件不宣告已生效")["H5_lit"])
print("  ④ 反例B '并不否认甲方不宣告已生效'（应 PASS）DG_pure =",
      detect("并不否认甲方不宣告已生效")["DG_pure"])
coord = ["本件不承认或并不否认已生效", "非登记一或二不可才算本件已生效",
         "非登记原件不可才算本件已生效"]
i5 = []
for t in coord:
    r = detect(t)
    i5.append({"text": t, **r})
    print("  ⑤ %-28s DG_pure=%-5s DG_dropin=%-5s" % (t[:26], r["DG_pure"], r["DG_dropin"]))
i6 = []
for p in DG.PSEUDO_DN:
    t = p + "不承认本件已生效"
    raw = bool(DG.DG_DROPIN_RE.search(t))
    dg = bool(DG.dg_scan(t, ["已生效"])[0])
    i6.append({"p": p, "raw": raw, "dg": dg})
    print("  ⑥ PSEUDO=%-5s raw_regex=%-5s dg_scan=%-5s" % (p, raw, dg))
print("  → raw_regex False =", sum(1 for x in i6 if not x["raw"]),
      "; True（veto 后另起命中）= ", sum(1 for x in i6 if x["raw"]))
quad = [("G1", "不查不验本件已生效", 2, "PASS"),
        ("G2", "未漏核，并非不宣告本件已生效", 3, "CATCH"),
        ("G3", "非登记五份原始件不可才算本件已生效", 2, "CATCH"),
        ("G4", "前稿不敢不承认其实本件不宣告已生效", 3, "PASS")]
i7 = []
for gid, t, nc, exp in quad:
    parity = "CATCH" if nc % 2 == 0 else "PASS"
    dg = detect(t)["DG_pure"]
    i7.append({"id": gid, "neg_count": nc, "exp": exp, "parity": parity, "dg": dg})
    print("  ⑦ %s neg_count=%d expect=%-5s parity=%-5s DG_pure=%-5s"
          % (gid, nc, exp, parity, dg))
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE", "dg_scan"]
co = {}
for fn in ("r10_context", "r12_scan"):
    names = getattr(DROP, fn).__code__.co_names
    co[fn] = {g: g in names for g in guards}
    print("  交付 %-12s 8 guard 全 False = %s" % (fn, all(not v for v in co[fn].values())))
# 加项扰动面
print("  加 1 项扰动面（个新生成串）：add_MID=%d add_NEG1=%d add_NEG2=%d add_SPLIT_TAIL=%d add_GAP=%d add_SCOPE_VERB=%d"
      % (len(set(DG.NEG1)) * len(set(DG.NEG2)),
         len(set(DG.MID)) * len(set(DG.NEG2)) + len(set(DG.GAP)) * len(set(DG.SCOPE_VERB)) * len(set(DG.SPLIT_TAIL)),
         len(set(DG.NEG1)) * len(set(DG.MID)),
         len(set(DG.NEG1)) * len(set(DG.GAP)) * len(set(DG.SCOPE_VERB)),
         len(set(DG.NEG1)) * len(set(DG.SCOPE_VERB)) * len(set(DG.SPLIT_TAIL)),
         len(set(DG.NEG1)) * len(set(DG.GAP)) * len(set(DG.SPLIT_TAIL))))
OUT["invariants"] = {"i1": i1, "i1b": i1b, "i2": i2, "mid_miss": mid_miss,
                     "comp": comp, "neg2_full": neg2_full, "second_nonempty": nonempty,
                     "i5": i5, "i6": i6, "i7": i7, "co_names": co}

print("\n=== (6) 会话末保护件指纹二次重算 ===")
fp_end = fingerprints()
print("  ALL_MATCH_2 =", fp_end)
OUT["fp_end"] = fp_end
(WD / "_dgaw_verify_out.json").write_text(
    json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgaw_verify_out.json")
