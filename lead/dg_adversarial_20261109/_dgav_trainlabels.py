# -*- coding: utf-8 -*-
r"""_dgav_trainlabels.py — attack the "training-set self-certification" and the
unverified generative-advantage numbers (16/17, 0/4, 31->31).

Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgav_trainlabels.py
Read-only subjects; all writes confined to lead/dg_adversarial_20261109/.
"""
import sys, re, ast, json, hashlib, importlib.util, io, contextlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgav2_dg", DG_DIR / "_dg_core.py")
H5 = _load("_dgav2_h5", H5P)
G7 = _load("_dgav2_g7", G7P)
DROP = _load("_dgav2_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
TOKS = ["已生效", "已入账", "已追加"]
OUT = {}

# ★ AST (not executing) extraction of the 20 author-authored negative samples
src = ast.parse((WD / "_dga_step1_repro.py").read_text(encoding="utf-8"),
                filename=str(WD / "_dga_step1_repro.py"))
NEG20 = EXPECT = None
for node in src.body:
    if isinstance(node, ast.Assign):
        names = [getattr(t, "id", "") for t in node.targets]
        if "NEG20" in names:
            NEG20 = ast.literal_eval(node.value)
        if "EXPECT_CATCH" in names:
            EXPECT = ast.literal_eval(node.value)
assert NEG20 and len(NEG20) == 20 and EXPECT == {"N03"}

# My independent truth adjudication of 8 of those 20, written before running detectors.
MY_ADJ = {
    "N01": ("PASS", "「无越权断言」与「不出现」是两处独立否定，冒号+主语切换，无 ¬¬P 支配链。"),
    "N03": ("CATCH", "「并未漏看」+「并非不宣告」：后段 ¬(¬宣告)=宣告，三否定词下仍是真 DN，作正对照正确。"),
    "N05": ("PASS", "「不得写成」是禁止算子，引文内「已生效」是被禁止的字样而非断言；无 ¬¬P。"),
    "N06": ("PASS", "「上一轮回件不宣告」与「本笔已入账」跨逗号两个独立命题，各只有单重否定。"),
    "N07": ("PASS", "「不闻不问」是并列成语式两个独立否定，token 在无否定的后句；不构成 ¬¬P。"),
    "N11": ("PASS", "「无非是」已词汇化为「不过是」，只有一个有效否定，不是 ¬(¬P)。"),
    "N14": ("PASS", "「非但…还…」是关联递进，「非但不」只有一个有效否定；H5 通配支应 PASS 却误命中。"),
    "N20": ("PASS", "¬¬P 只出现在「」引文内，主句「不采信该说法」明确拒绝它；对 token 无双重否定断言。"),
}
print("=== (A) 抽 8 条 DG 作者训练集：独立判真值 vs 作者标注 ===")
print("  （只做标注核验；这 20 条绝不作为对抗样本，铁律禁止用训练集自证）")
pick = []
for cid, text in NEG20:
    if cid not in MY_ADJ:
        continue
    author = "CATCH" if cid in EXPECT else "PASS"
    mine = MY_ADJ[cid][0]
    agree = author == mine
    pick.append({"id": cid, "text": text, "author_exp": author, "my_exp": mine,
                 "agree": agree, "my_why": MY_ADJ[cid][1]})
    print("  %-4s author=%-5s mine=%-5s AGREE=%-5s | %s" % (cid, author, mine, agree, text[:40]))
    print("       我的理由: %s" % MY_ADJ[cid][1])
print("  → 8 条标注全一致 =", all(x["agree"] for x in pick))
OUT["A_pick8"] = {"all_agree": all(x["agree"] for x in pick), "rows": pick}

# ★★ fp=0 under BOTH the pure function and the declared one-line deliverable
print("\n=== (B) ★★ fp=0 口径复核：纯函数 vs 申报的「一行替换」交付形态 ===")
rows = []
for cid, text in NEG20:
    toks = [t for t in TOKS if t in text] or ["已生效"]
    ppure, hp = DG.dg_scan(text, toks)
    pdrop, _ = DROP.r12_scan(text, toks)
    pbase, _ = G7.r12_scan(text, toks)
    r = {"id": cid, "text": text, "author_exp": "CATCH" if cid in EXPECT else "PASS",
         "pure": "CATCH" if ppure else "PASS",
         "dropin": "CATCH" if pdrop else "PASS",
         "base_r12": "CATCH" if pbase else "PASS",
         "pure_hit": hp[0]["hit"] if hp else ""}
    rows.append(r)
    print("  %-4s exp=%-5s pure=%-5s dropin=%-5s base=%-5s hit=%-12s | %s" %
          (cid, r["author_exp"], r["pure"], r["dropin"], r["base_r12"], r["pure_hit"], text[:36]))
for form in ["pure", "dropin", "base_r12"]:
    fp = [x["id"] for x in rows if x["author_exp"] == "PASS" and x[form] == "CATCH"]
    fn = [x["id"] for x in rows if x["author_exp"] == "CATCH" and x[form] == "PASS"]
    print("  → %-9s 真负样本 n=19 ; fp = %d %s ; N03 = %s" %
          (form, len(fp), fp, next(x[form] for x in rows if x["id"] == "N03")))
OUT["B_neg20"] = {"rows": rows,
                  "fp": {f: [x["id"] for x in rows if x["author_exp"] == "PASS" and x[f] == "CATCH"]
                         for f in ["pure", "dropin", "base_r12"]}}

# ★★ 16/17 vs 0/17 与 分离型 0/4：独立重跑（复核回件标「未验」的两个数字）
CONSTRUCTS17 = ["何尝不", "安能不", "岂敢不", "没法不", "并非未", "并非无",
                "不由得不", "忍不住不", "不见得不", "不一定不", "不是没",
                "非写成已入账不可", "非登记不可", "非说不", "没说不", "没法不说", "非但不"]
print("\n=== (C) ★★ DNEG_GENERATIVE.md:346 的 16/17 vs 0/17 独立重跑 ===")
c17 = []
for c in CONSTRUCTS17:
    dg = bool(DG.DG_DROPIN_RE.search(c))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(c))
    r12 = bool(G7.DOUBLE_NEG_RE.search(c))
    c17.append({"construct": c, "dg": dg, "h5": h5, "r12": r12})
    print("  %-16s DG=%-5s H5=%-5s R12=%s" % (c, dg, h5, r12))
print("  → DG %d/17 ; H5 %d/17 ; R12 %d/17（作者申报 16/17 vs 0/17）" %
      (sum(x["dg"] for x in c17), sum(x["h5"] for x in c17), sum(x["r12"] for x in c17)))
SPLIT4 = ["非写成已入账不可", "不宣告已生效不行", "非登记已入账不可", "不写成已入账不成"]
print("\n=== (C2) DNEG_GENERATIVE.md:347 分离型 post 整句 0/4 独立重跑 ===")
s4 = []
for t in SPLIT4:
    toks = [x for x in TOKS if x in t] or ["已生效"]
    ppure, _ = DG.dg_scan(t, toks)
    pdrop, _ = DROP.r12_scan(t, toks)
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(t))
    s4.append({"text": t, "dg_pure": "CATCH" if ppure else "PASS",
               "dg_dropin": "CATCH" if pdrop else "PASS", "h5_lit": "CATCH" if h5 else "PASS"})
    print("  %-22s DG_pure=%-5s DG_dropin=%-5s H5_lit=%-5s" %
          (t, s4[-1]["dg_pure"], s4[-1]["dg_dropin"], s4[-1]["h5_lit"]))
print("  → DG_pure CATCH %d/4 ; DG_dropin CATCH %d/4 ; H5_lit CATCH %d/4" %
      (sum(x["dg_pure"] == "CATCH" for x in s4), sum(x["dg_dropin"] == "CATCH" for x in s4),
       sum(x["h5_lit"] == "CATCH" for x in s4)))
OUT["C_17"] = {"rows": c17, "dg": sum(x["dg"] for x in c17),
               "h5": sum(x["h5"] for x in c17), "r12": sum(x["r12"] for x in c17)}
OUT["C_split4"] = s4

# ★★ 真实一行替换口径 31→31（复核回件标「未验」）：不用 Shim
print("\n=== (D) ★★ 74 条回归：真实一行替换口径的层间冲突（复核回件标未验）===")
REGP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression.py"
_real_write = Path.write_text
blocked = []


def _blocked(self, *a, **k):
    if "dg_adversarial_20261109" in str(self):
        return _real_write(self, *a, **k)
    blocked.append(str(self))
    return 0


Path.write_text = _blocked
try:
    with contextlib.redirect_stdout(io.StringIO()):
        REG = _load("_dgav2_reg", REGP)
finally:
    Path.write_text = _real_write
g7, n13, T, P = REG.g7, REG.n13, REG.T, REG.P
print("  CORPUS n =", len(REG.CORPUS), "; 被拦截写盘 =", blocked)


def chain_verdict(G, it):
    r = P.gate_check(it["text"], it["tokens"], WD, G, n13, T)
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    return ("CATCH" if adj else "PASS"), r["summary"]["conflicts"]


def report(G, label):
    ok = fp = fn = conf = 0
    changed = []
    for it in REG.CORPUS:
        v, c = chain_verdict(G, it)
        conf += c
        if v == it["expect"]:
            ok += 1
        elif it["expect"] == "PASS":
            fp += 1
        else:
            fn += 1
    print("  %-12s chain ok=%-3d FP=%-2d FN=%-2d conflicts=%d" % (label, ok, fp, fn, conf))
    return {"ok": ok, "fp": fp, "fn": fn, "conflicts": conf}


base = report(g7, "base(原十式)")
oneline = report(DROP, "oneline(一行)")
print("  → 真实一行替换层间冲突 = %d → %d（DNEG_GENERATIVE.md:393 记 31→31）" %
      (base["conflicts"], oneline["conflicts"]))
OUT["D_oneline"] = {"base": base, "oneline": oneline, "blocked_writes": blocked}

# (E) 自述边界里的表数口径：doc 说 6 张，core 实际几张？
tree = ast.parse((DG_DIR / "_dg_core.py").read_text(encoding="utf-8"))
tables = []
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Tuple, ast.List)):
        for t in node.targets:
            if isinstance(t, ast.Name):
                try:
                    ast.literal_eval(node.value)
                    tables.append((t.id, len(node.value.elts), node.lineno))
                except Exception:
                    pass
print("\n=== (E) _dg_core.py 闭合表数量（AST 静态，DNEG_GENERATIVE.md:163 说 6 张）===")
for name, n, ln in tables:
    print("  %-14s n=%-3d at :%d" % (name, n, ln))
print("  → 顶层闭合表数 =", len(tables))
OUT["E_tables"] = tables

# (F) 末次指纹 + 快照
print("\n=== (F) 保护件末次指纹（hashlib 独立重算）===")
BASE = {
    "lead/dneg_generative_20261109/_dg_core.py": "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1",
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md": "94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4",
    "lead/h5_governance_20261109/_h5_pasteable.py": "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c",
    "lead/gate_fp7_20261108/_g7_predicates.py": "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",
    "lead/PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    "lead/GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
}
ok = True
for rel, sha in BASE.items():
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    ok = ok and got == sha
    print("  %s %s %d %s" % ("MATCH   " if got == sha else "MISMATCH", got, len(b), rel))
print("  ALL_MATCH =", ok)

(WD / "_dgav_trainlabels_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgav_trainlabels_out.json")
