# -*- coding: utf-8 -*-
r"""_dgav_verify.py — DG adversarial review: independent re-verification (read-only subjects).

Runs with: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dgav_verify.py
No game processes, no sampling code, no writes outside lead/dg_adversarial_20261109/.
All subject modules are loaded from read-only protected paths via importlib; __pycache__
is suppressed with sys.dont_write_bytecode = True.
"""
import sys, re, ast, json, hashlib, importlib.util, io, contextlib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
TOK = "已生效"

BASE_FP = {
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
PROTECTED_TREES = [
    "lead/dneg_generative_20261109", "lead/h5_governance_20261109",
    "lead/gate_pipeline_20261109", "lead/check_fp_audit_20261109",
]
PROTECTED_FILES = [
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md",
]


def fp_map():
    """Hash only the read-only protected trees and the two ledgers (fast, bounded)."""
    rels = []
    for d in PROTECTED_TREES:
        for p in (ROOT / d).rglob("*"):
            if p.is_file():
                rels.append(p)
    for rel in PROTECTED_FILES:
        rels.append(ROOT / rel)
    out = {}
    for p in rels:
        key = str(p).replace("\\", "/").replace(str(ROOT).replace("\\", "/") + "/", "")
        out[key] = (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size)
    return out


SNAP0 = fp_map()
print("=== (0) 独立指纹重算 + 保护件全量快照（会话初） ===")
for rel, (sha, n) in BASE_FP.items():
    b = (ROOT / rel).read_bytes()
    print("  %s %s %d %s" % ("MATCH   " if hashlib.sha256(b).hexdigest() == sha and len(b) == n
                            else "MISMATCH", hashlib.sha256(b).hexdigest(), len(b), rel))
print("  ALL_MATCH =", all(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha
                          and (ROOT / rel).stat().st_size == n
                          for rel, (sha, n) in BASE_FP.items()))
print("  protected_snapshot_files =", len(SNAP0))


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dgav_dg", DG_DIR / "_dg_core.py")
PS = _load("_dgav_ps", DG_DIR / "_dg_pasteable.py")
H5 = _load("_dgav_h5", H5P)
G7 = _load("_dgav_g7", G7P)
DROP = _load("_dgav_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE

# AST (not executing) extraction of DG's own negative-sample training strings.
TRAIN_FILES = ["_dg_step34.py", "_dgv_probe.py", "_dgv_neg2.py", "_dg_step1.py"]
train_strings = set()
train_per_file = {}
for fn in TRAIN_FILES:
    p = DG_DIR / fn
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    s = set(n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str))
    train_per_file[fn] = s
    train_strings |= s

OUT = {"fingerprints": {rel: list(v) for rel, v in BASE_FP.items()},
       "snapshot0_count": len(SNAP0), "train_per_file": {k: len(v) for k, v in train_per_file.items()}}

# ========================= (1) 19 式 + 十式：自己 import _dg_core 独立跑 =========================
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
print("\n=== (1) 19 式与十式：独立 import _dg_core 实跑 ===")
gap_rows = []
for name, text in GAPS:
    pdg, hdg = DG.dg_scan(text, [TOK])
    r = {"construct": name, "dg_catch": len(pdg) > 0,
         "dg_hit": hdg[0]["hit"] if hdg else "",
         "r12_regex": bool(G7.DOUBLE_NEG_RE.search(name)),
         "h5_regex": bool(H5.H5_DOUBLE_NEG_RE.search(name)),
         "dropin_regex": bool(DG.DG_DROPIN_RE.search(name))}
    gap_rows.append(r)
    print("  %-9s dg_catch=%-5s hit=%-12s R12=%-5s H5=%-5s dropin_regex=%s" %
          (name, r["dg_catch"], r["dg_hit"], r["r12_regex"], r["h5_regex"], r["dropin_regex"]))
print("  → DG 覆盖 %d/19 ; H5 超集字面 %d/19 ; R12 %d/19 ; dropin_regex %d/19" %
      (sum(r["dg_catch"] for r in gap_rows), sum(r["h5_regex"] for r in gap_rows),
       sum(r["r12_regex"] for r in gap_rows), sum(r["dropin_regex"] for r in gap_rows)))
ten_rows = []
for c in DG.R12_TEN:
    text = c + "本件" + TOK
    p12, _ = G7.r12_scan(text, [TOK])
    pdg, _ = DG.dg_scan(text, [TOK])
    pdrop, _ = DROP.r12_scan(text, [TOK])
    ten_rows.append({"construct": c, "r12_catch": len(p12) > 0,
                     "dg_catch": len(pdg) > 0, "dropin_catch": len(pdrop) > 0})
    print("  %-9s R12=%-5s DG=%-5s dropin=%s" %
          (c, ten_rows[-1]["r12_catch"], ten_rows[-1]["dg_catch"], ten_rows[-1]["dropin_catch"]))
print("  → 十式 R12 全 CATCH = %s ; DG 全 CATCH = %s ; dropin 全 CATCH = %s" %
      (all(r["r12_catch"] for r in ten_rows), all(r["dg_catch"] for r in ten_rows),
       all(r["dropin_catch"] for r in ten_rows)))
OUT["step1"] = {"gaps": gap_rows, "ten": ten_rows,
                "dg_cov": sum(r["dg_catch"] for r in gap_rows),
                "h5_cov": sum(r["h5_regex"] for r in gap_rows),
                "r12_cov": sum(r["r12_regex"] for r in gap_rows),
                "r12_ten_all": all(r["r12_catch"] for r in ten_rows),
                "dg_ten_all": all(r["dg_catch"] for r in ten_rows),
                "dropin_ten_all": all(r["dropin_catch"] for r in ten_rows),
                "pasteable_same_pattern": PS.DG_PATTERN == DG.DG_PATTERN,
                "dg_stats": DG.DG_STATS}

# ========================= (2) ★★ 自造 8 条对抗样本，独立判「应判什么」 =========================
# All 8 are newly constructed here (not taken from the DG negative-sample set),
# chosen to attack the same 7 invariants from a fresh angle. Truth values are
# adjudicated here first (my_expected), then the six detectors are run blind.
NEW8 = [
    ("X01", "旧稿不敢不承认总而言之本件不宣告已生效", "PASS",
     "「总而言之」是追补/总结连词，未登记在 DG_BREAK_RE(_dg_core.py:89) / _BQ(:86)；前段 DN 与后段独立否定被跨微句搭桥 ⇒ 应 PASS。攻 ①", "①"),
    ("X02", "前稿并非不宣告(据旧档)本件已生效", "PASS",
     "ASCII 括号 () 未登记于 DG_QUOTE_RE(:92) 的 4 类引号；前段 DN 是括注内引述，正文无 ¬¬P ⇒ 应 PASS。攻 ②", "②"),
    ("X03", "不许不承认本件已生效", "CATCH",
     "「不许(不承认)」= 必须承认，¬(¬P)；MID「许」不在 23 项闭合表(:55-61) ⇒ 真 DN 应 CATCH。攻 ③", "③"),
    ("X04", "非登记甲乙丙丁戊不可才算本件已生效", "CATCH",
     "「非…不可」分离式真 DN；受控补语 5 字 > {0,4}?(:118) ⇒ 应 CATCH。攻 ③", "③"),
    ("X05", "并不否认乙方不宣告已生效", "PASS",
     "「乙方」是第二主语但不在 _SECOND(:88)；NEG2 含完整否定谓语「否认」(:65)，T12 零隔拼接跨主语 ⇒ 两独立否定应 PASS。攻 ④", "④"),
    ("X06", "本件不承认或并不否认已生效", "PASS",
     "「或」是并列标记但二次 veto 只查 hit_text(:182-184)；hit_text='并不否认' 不含「或」⇒ 应 PASS。攻 ⑤/③", "⑤"),
    ("X07", "非不认可本件已生效", "CATCH",
     "「非不认可」= 并非不认可 = 认可，真 DN；却因 PSEUDO_DN 含「非不」(:81-82) 被词首负向前瞻(:116) veto ⇒ 应 CATCH。攻 ⑥", "⑥"),
    ("X08", "不查不验本件已生效", "PASS",
     "「不查」「不验」两个并列独立否定，否定词奇偶=2 会误 CATCH；DG 不用奇偶(:112/⑤)设计上应 PASS。攻 ⑦", "⑦"),
]
novelty = {c[1] for c in NEW8} & train_strings
print("\n=== (2a) 自造 8 条与 DG 训练集精确重合（AST 静态抽取，不执行）===")
for fn, s in train_per_file.items():
    print("  %-20s 字符串 %-4d 与本 8 条精确重合 %d" % (fn, len(s), len({c[1] for c in NEW8} & s)))
print("  自造样本数 = 8 ; 与全部训练集精确重合 =", len(novelty), sorted(novelty))
assert not novelty, "自造样本与训练集重合"

DETECTORS = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]


def detect(text):
    toks = [t for t in TOKS if t in text] or [TOK]
    r = {k: "PASS" for k in DETECTORS}
    hits = {}
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    hits["DG_pure"] = h[0]["hit"] if h else ""
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    raw = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            mm = DG.DG_DROPIN_RE.search(text[:m.start()])
            if mm:
                raw.append(mm.group(0))
    hits["DG_dropin"] = raw[0] if raw else ""
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hits["H5_lit"] = ml.group(0) if ml else ""
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"
    hits["H5_gov"] = hh
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12_lit"] = m12.group(0) if m12 else ""
    return r, hits


print("\n=== (2b) 自造 8 条：人工真值 vs 六判定器（独立实跑）===")
new_rows = []
for cid, text, exp, why, attack in NEW8:
    r, h = detect(text)
    new_rows.append({"id": cid, "text": text, "my_expected": exp, "why": why,
                     "attack": attack, "verdicts": r, "hits": h})
    print("  %-4s my_exp=%-5s | DG_pure=%-5s DG_drop=%-5s H5_lit=%-5s H5_gov=%-5s R12=%-5s R12_lit=%-5s | %s" %
          (cid, exp, r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["H5_gov"],
           r["R12"], r["R12_lit"], text[:34]))
    print("       DG_pure hit=%s ; DG_dropin hit=%s ; H5_lit hit=%s" %
          (h["DG_pure"], h["DG_dropin"], h["H5_lit"]))
OUT["step2_new8"] = {"train_overlap": sorted(novelty), "rows": new_rows}

# ★ 抽 8 条「撰写人自造的 20 条对抗样本」，自己独立判「应判什么」并核对它的 exp 标注
# The review's 41 cases live in _dga_adversarial.py:CASES; extract by AST, never import/execute it.
adv_tree = ast.parse((WD / "_dga_adversarial.py").read_text(encoding="utf-8"),
                     filename=str(WD / "_dga_adversarial.py"))
CASES = None
for node in adv_tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "CASES" for t in node.targets):
        CASES = ast.literal_eval(node.value)
        break
assert CASES and len(CASES) == 41
by_id = {c[0]: c for c in CASES}
PICK = ["P01", "P06", "C01", "C07", "C10", "C17", "A01", "A04"]
# My independent truth adjudication, written BEFORE looking at DG verdicts.
MY_ADJ = {
    "P01": ("PASS", "「旧稿不承认」与「本件不宣告」是两个各管自己主语/谓语的独立否定，逗号切断；无 ¬¬P。"),
    "P06": ("PASS", "「前稿不敢不承认」在前段 DN，「其实本件不宣告」是另起主语的真否定；「其实」作追补转折，前段 ¬¬P 不支配后段谓词，整句对 token 无完成断言。"),
    "C01": ("CATCH", "「不容(不宣告)」= 必须宣告，¬(¬P) 真双重否定；MID「容」未登记是 DG 的漏判面。"),
    "C07": ("CATCH", "「非…不可」分离式真 DN，补语「五份原始件」5 字；长度限制不应当由真值决定。"),
    "C10": ("CATCH", "「并非」管辖整个命题「本件不宣告」：¬(本件¬宣告)= 本件宣告；「本件」是该谓词主语而非第二主语。"),
    "C17": ("CATCH", "转折后微句「并非不宣告」= 宣告，¬¬P；前句「虽未明说」不取消后句肯定。"),
    "A01": ("AMBIG", "「非但不否认」至少两解：关联连词「非但…」+「不否认」(单重否定、弱化肯定)，或「非(但不否认)」近似 ¬¬P；门禁语境下应 NEEDS_HUMAN，不宜二值硬判。与作者保守 forced=PASS 口径一致但标注为 AMBIG。"),
    "A04": ("AMBIG", "「没不承认」口语可解为「没有不承认」= 承认（真 DN），但「没不」是否成词/是否规范有争议，且 DG 把「没不」列 PSEUDO_DN；应 NEEDS_HUMAN，真值需语言学裁定。"),
}
print("\n=== (2c) ★ 抽 8 条撰写人自造样本：我独立判「应判什么」并核对 exp 标注 ===")
print("  （标注来自 _dga_adversarial.py:CASES，AST 静态抽取不执行该脚本）")
pick_rows = []
all_exp_agree = True
for cid in PICK:
    c = by_id[cid]
    author_exp, author_why = c[3], c[4]
    my_exp, my_why = MY_ADJ[cid]
    r, h = detect(c[2])
    agree = (author_exp == my_exp)
    all_exp_agree = all_exp_agree and agree
    pick_rows.append({"id": cid, "text": c[2], "author_exp": author_exp,
                      "author_why": author_why, "my_exp": my_exp, "my_why": my_why,
                      "exp_agree": agree, "verdicts": r, "hits": h,
                      "author_forced": ({"A01": "PASS", "A02": "PASS", "A03": "PASS",
                                         "A04": "CATCH", "C20": "CATCH"}.get(cid, author_exp))})
    print("  %-4s author_exp=%-5s my_exp=%-5s AGREE=%-5s | DG_pure=%-5s DG_drop=%-5s H5_lit=%-5s H5_gov=%-5s R12=%-5s | %s" %
          (cid, author_exp, my_exp, agree, r["DG_pure"], r["DG_dropin"], r["H5_lit"],
           r["H5_gov"], r["R12"], c[2][:36]))
    print("       作者理由: %s" % author_why[:80])
    print("       我的理由: %s" % my_why[:80])
print("  → 8 条标注全部与我的独立判定一致 =", all_exp_agree,
      "; 不一致条数 =", len([x for x in pick_rows if not x["exp_agree"]]))
OUT["step2_pick8"] = {"all_exp_agree": all_exp_agree, "rows": pick_rows}

# ★ 顺带核对作者全 41 条的 fp/fn 统计是否由逐条结果复算得出
def score_all(rows, key, forced=False):
    fp, fn, n = [], [], 0
    for x in rows:
        exp = x["forced"] if forced else x["expect"]
        if exp == "AMBIG":
            continue
        n += 1
        got = x["verdicts"][key]
        if exp == "PASS" and got == "CATCH":
            fp.append(x["id"])
        elif exp == "CATCH" and got == "PASS":
            fn.append(x["id"])
    return {"n": n, "fp": len(fp), "fp_ids": fp, "fn": len(fn), "fn_ids": fn}


FORCED = {"A01": "PASS", "A02": "PASS", "A03": "PASS", "A04": "CATCH", "C20": "CATCH"}
recomputed_rows = []
for c in CASES:
    cid, shape, text, exp, why, attack = c
    r, h = detect(text)
    recomputed_rows.append({"id": cid, "expect": exp, "forced": FORCED.get(cid, exp),
                           "verdicts": r, "hits": h})
print("\n=== (2d) 作者 41 条用我的独立 detect() 重算 fp/fn（核对申报数字）===")
for k in DETECTORS:
    s = score_all(recomputed_rows, k)
    f = score_all(recomputed_rows, k, forced=True)
    print("  %-10s strict fp=%-2d %-30s fn=%-2d | forced fp=%-2d fn=%-2d" %
          (k, s["fp"], str(s["fp_ids"]), s["fn"], f["fp"], f["fn"]))
OUT["step2_recompute41"] = {k: {"strict": score_all(recomputed_rows, k),
                                "forced": score_all(recomputed_rows, k, forced=True)}
                            for k in DETECTORS}

# ========================= (3) ★★ 7 条不变式至少重跑 3 条（这里 7 条全跑） =========================
INV = {}
print("\n=== (3①) 不变式① 句界/逗号/冒号/转折切断：未登记词扫描 ===")
BREAK_WORDS = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "可", "反倒说", "结果", "终究",
               "总而言之", "归根结底", "话说回来", "退一步说"]
rows1 = []
for w in BREAK_WORDS:
    t = "前稿不敢不承认" + w + "本件不宣告" + TOK
    r, h = detect(t)
    rows1.append({"word": w, "in_BREAK": bool(DG.DG_BREAK_RE.search(w)),
                  "in_BQ": bool(re.search("[" + DG._BQ + "]", w)),
                  "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"],
                  "R12": r["R12"], "hit": h["DG_pure"]})
    print("  %-8s BREAK=%-5s BQ=%-5s DG_pure=%-5s DG_drop=%-5s hit=%s" %
          (w, rows1[-1]["in_BREAK"], rows1[-1]["in_BQ"], r["DG_pure"], r["DG_dropin"], h["DG_pure"]))
unreg_fp = [x["word"] for x in rows1 if not x["in_BREAK"] and x["DG_pure"] == "CATCH"]
print("  → 未登记边界词中 DG_pure 仍 CATCH（应 PASS）= %d : %s" % (len(unreg_fp), unreg_fp))
INV["1"] = {"rows": rows1, "unreg_fp": unreg_fp}

print("\n=== (3②) 不变式② 引证屏蔽：4 类引号 vs 未登记引号 ===")
QUOTE_CASES = [
    ("「」(登记+内置空格)", "「 并非不宣告已生效 」只是引文，本件不采信该说法", "PASS"),
    ("ASCII 双引号(未登记)", '"并非不宣告已生效"只是引文，本件不采信该说法', "PASS"),
    ("书名号《》(未登记)", "《并不否认已生效》只是引文，本件不采信该说法", "PASS"),
    ("ASCII 括号()(未登记)", "(并非不宣告已生效)只是括注，本件不采信该说法", "PASS"),
    ("ASCII 单引号(未登记)", "'并非不宣告已生效'只是引文，本件不采信该说法", "PASS"),
]
rows2 = []
for tag, t, exp in QUOTE_CASES:
    r, h = detect(t)
    rows2.append({"tag": tag, "text": t, "expect": exp, **r})
    print("  %-24s exp=%-5s DG_pure=%-5s DG_drop=%-5s R12=%-5s H5_lit=%-5s hit=%s" %
          (tag, exp, r["DG_pure"], r["DG_dropin"], r["R12"], r["H5_lit"], h["DG_pure"]))
print("  → DG_QUOTE_RE 4 类 =", DG.DG_QUOTE_RE.pattern)
INV["2"] = {"rows": rows2, "quote_re": DG.DG_QUOTE_RE.pattern}

print("\n=== (3③) 不变式③ T12 零通配 + MID 闭合表 + COMP≤4：三向扫描 ===")
mid_rows = []
for w in ["容", "许", "想", "愿", "甘", "料", "要", "需", "欲", "得", "能", "可", "敢", "会"]:
    t = "不" + w + "不宣告本件" + TOK
    r, h = detect(t)
    mid_rows.append({"mid": w, "in_MID": w in set(DG.MID), "DG_pure": r["DG_pure"],
                     "hit": h["DG_pure"]})
    print("  MID=%-3s 在表内=%-5s DG_pure=%-5s hit=%-8s" %
          (w, mid_rows[-1]["in_MID"], r["DG_pure"], h["DG_pure"]))
comp_rows = []
for n in range(0, 8):
    t = "非登记" + "原" * n + "不可才算本件" + TOK
    r, h = detect(t)
    comp_rows.append({"n": n, "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"],
                      "hit": h["DG_dropin"]})
    print("  COMP=%d DG_pure=%-5s DG_drop=%-5s hit=%s" %
          (n, r["DG_pure"], r["DG_dropin"], h["DG_dropin"]))
# NEG2 complete negative predicates produce zero-gap cross-subject hits
neg2_rows = []
for s in ["并不否认与监理方不宣告已生效", "并不否认甲方不宣告已生效",
          "不承认与监理方不宣告已生效", "不认为与监理方不宣告已生效"]:
    r, h = detect(s)
    neg2_rows.append({"text": s, "DG_pure": r["DG_pure"], "hit": h["DG_pure"]})
    print("  NEG2跨主语 %-24s DG_pure=%-5s hit=%s" % (s[:22], r["DG_pure"], h["DG_pure"]))
INV["3"] = {"mid": mid_rows, "comp": comp_rows, "neg2": neg2_rows,
            "mid_miss": [x["mid"] for x in mid_rows if not x["in_MID"] and x["DG_pure"] == "PASS"]}

print("\n=== (3④) 不变式④ 第二主语负向前瞻 + 二次 veto：可达性 + 反例 ===")
parts = list(DG.NEG1) + list(DG.MID) + list(DG.NEG2) + list(DG.GAP) + list(DG.SCOPE_VERB) + list(DG.SPLIT_TAIL)
second_tokens = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔",
                 "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"]
in_parts = {s: [p for p in parts if s in p] for s in second_tokens if any(s in p for p in parts)}
ss_cases = ["并非本件不宣告已生效", "并非该件不宣告已生效", "并非本笔不宣告已生效",
            "非登记本件不可才算本件已生效", "非登记原件不可才算本件已生效",
            "并不否认乙方不宣告已生效", "并不否认甲方不宣告已生效"]
ss_rows = []
for t in ss_cases:
    r, h = detect(t)
    ss_rows.append({"text": t, "DG_pure": r["DG_pure"], "H5_lit": r["H5_lit"], "hit": h["DG_dropin"]})
    print("  %-32s DG_pure=%-5s H5_lit=%-5s hit=%s" % (t[:30], r["DG_pure"], r["H5_lit"], h["DG_dropin"]))
veto_fired = 0
for x in recomputed_rows:
    orig = by_id[x["id"]][2]
    toks = [t for t in TOKS if t in orig] or [TOK]
    for tok in toks:
        for m in re.finditer(re.escape(tok), orig):
            d = DG.dg_double_neg(orig[:m.start()])
            if "第二主语" in d["reason"] or "并列标记" in d["reason"]:
                veto_fired += 1
print("  _SECOND 任一项出现在闭合表条目内 =", in_parts or "{}（全为空）")
print("  → 41 条上纯函数二次 veto 实际触发次数 =", veto_fired)
INV["4"] = {"second_in_parts": in_parts, "rows": ss_rows, "veto_fired": veto_fired}

print("\n=== (3⑤) 不变式⑤ 并列项否决只查 hit_text：双向后果 ===")
coord_rows = []
for t in ["本件不承认或并不否认已生效", "本件不承认、并不否认均不成立已生效",
          "非登记一或二不可才算本件已生效", "非登记甲、乙不可才算本件已生效",
          "非登记原件不可才算本件已生效"]:
    r, h = detect(t)
    coord_rows.append({"text": t, "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"],
                       "hit": h["DG_dropin"]})
    print("  %-32s DG_pure=%-5s DG_drop=%-5s raw_hit=%s" %
          (t[:30], r["DG_pure"], r["DG_dropin"], h["DG_dropin"]))
INV["5"] = {"rows": coord_rows}

print("\n=== (3⑥) 不变式⑥ PSEUDO_DN 12 项：词首 veto 与真 DN 冲突 ===")
pseudo_rows = []
for p in DG.PSEUDO_DN:
    t = p + "不承认本件" + TOK
    raw = bool(DG.DG_DROPIN_RE.search(t[:t.find(TOK)]))
    pure = bool(DG.dg_scan(t, [TOK])[0])
    pseudo_rows.append({"pseudo": p, "raw": raw, "pure": pure})
    print("  PSEUDO=%-5s raw_regex=%-5s DG_pure=%-5s" % (p, raw, pure))
INV["6"] = {"rows": pseudo_rows,
            "raw_false": [x["pseudo"] for x in pseudo_rows if not x["raw"]],
            "raw_true": [x["pseudo"] for x in pseudo_rows if x["raw"]]}

print("\n=== (3⑦) 不变式⑦ 不做奇偶计数：四象限 ===")
parity_rows = []
for cid, t, exp in [("G1", "不查不验本件已生效", "PASS"),
                    ("G2", "未漏核，并非不宣告本件已生效", "CATCH"),
                    ("G3", "非登记五份原始件不可才算本件已生效", "CATCH"),
                    ("G4", "前稿不敢不承认其实本件不宣告已生效", "PASS")]:
    r, h = detect(t)
    pos = t.find(TOK)
    pre = t[:pos]
    negc = len(G7.NEG_RE.findall(pre))
    parity = "CATCH" if negc % 2 == 0 and negc > 0 else "PASS"
    parity_rows.append({"id": cid, "neg_count": negc, "expect": exp,
                        "parity": parity, "DG_pure": r["DG_pure"]})
    print("  %s neg_count=%d expect=%-5s parity=%-5s DG_pure=%-5s" %
          (cid, negc, exp, parity, r["DG_pure"]))
INV["7"] = {"rows": parity_rows}
OUT["invariants"] = INV

# ========================= (4) 第四步(b)：DG vs H5 优势是否夸大 =========================
print("\n=== (4b) DG vs H5 量化差异 + 生成式价值口径 ===")
S = DG.DG_STATS
h5_ten = len(re.findall(r"[^|]+", H5.H5_R12_TEN))
h5_extra = len(re.findall(r"[^|]+", H5.H5_DN_EXTRA))
print("  DG_STATS =", S)
print("  DG 105492 = %d*%d*%d + %d*%d*%d*%d = %d+%d = %d（笛卡尔积可生成串数）" %
      (S["n_neg1"], S["n_mid"], S["n_neg2"], S["n_neg1"], S["n_gap"], S["n_verb"], S["n_tail"],
       S["cartesian_T12"], S["cartesian_T3"], S["cartesian_total"]))
print("  DG pattern_chars =", len(DG.DG_PATTERN), "; H5 pattern_chars =",
      len(H5.H5_DOUBLE_NEG_RE.pattern), "; H5_R12_TEN 支 =", h5_ten,
      "; H5_DN_EXTRA 支 =", h5_extra)
# 逐条独对（严格口径）
pairs = {}
for a, b in [("DG_pure", "H5_lit"), ("DG_pure", "H5_gov"), ("DG_pure", "R12"),
             ("DG_pure", "DG_dropin")]:
    a_only, b_only = [], []
    for x in recomputed_rows:
        if x["expect"] == "AMBIG":
            continue
        ga, gb = x["verdicts"][a], x["verdicts"][b]
        ea = "CATCH" if x["expect"] == "CATCH" else "PASS"
        if ga == ea and gb != ea:
            a_only.append(x["id"])
        if gb == ea and ga != ea:
            b_only.append(x["id"])
    pairs[a + "_vs_" + b] = {a + "_only": a_only, b + "_only": b_only}
    print("  %-22s %s 独对 %d %s ; %s 独对 %d %s" %
          (a + " vs " + b, a, len(a_only), a_only, b, len(b_only), b_only))
# delivery-form guard static check
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE"]
co = {f: {g: (g in getattr(G7, f).__code__.co_names) for g in guards}
      for f in ["r10_context", "r12_scan"]}
print("  r10_context co_names guard =", co["r10_context"])
print("  r12_scan    co_names guard =", co["r12_scan"])
print("  → 交付形态下 guard 全 False =",
      all(not v for d in co.values() for v in d.values()))
# H5 literal superset is genuinely broad: regex includes wildcard branch
print("  H5 通配支 =", H5.H5_DN_EXTRA.split("|")[-1])
# maintenance deltas
deltas = {"add_MID": S["n_neg1"] * S["n_neg2"],
          "add_NEG2": S["n_neg1"] * S["n_mid"],
          "add_SPLIT_TAIL": S["n_neg1"] * S["n_gap"] * S["n_verb"],
          "add_GAP": S["n_neg1"] * S["n_verb"] * S["n_tail"],
          "add_SCOPE_VERB": S["n_neg1"] * S["n_gap"] * S["n_tail"]}
print("  加项扰动面 =", deltas)
OUT["step4b"] = {"stats": S, "h5_ten": h5_ten, "h5_extra": h5_extra,
                 "h5_pattern_chars": len(H5.H5_DOUBLE_NEG_RE.pattern),
                 "dg_pattern_chars": len(DG.DG_PATTERN),
                 "pairs": pairs, "co_names": co, "deltas": deltas}

print("\n=== (4a) 74 条回归（独立 import _gp_regression + 写盘拦截）===")
REGP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression.py"
GPP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py"
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
        REG = _load("_dgav_reg", REGP)
finally:
    Path.write_text = _real_write
print("  CORPUS n =", len(REG.CORPUS), "; 被拦截的保护件写盘企图 =", blocked)
g7, n13, T, P = REG.g7, REG.n13, REG.T, REG.P


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


shim = make_shim()


def judge(item, mode, sh):
    text, toks = item["text"], item["tokens"]
    G = sh if mode.endswith("_dg") else g7
    r10name = "r10_" + "scan"
    if mode.startswith("naive"):
        return "CATCH" if any(t in text for t in toks) else "PASS"
    if mode.startswith("r10"):
        return "CATCH" if getattr(G, r10name)(text, toks)[0] else "PASS"
    if mode.startswith("r12"):
        return "CATCH" if G.r12_scan(text, toks)[0] else "PASS"
    if mode.startswith("n13"):
        p, _ = n13.r13_assertions(text, T, **{r10name: getattr(G, r10name), "r12_scan": G.r12_scan})
        return "CATCH" if p else "PASS"
    if mode.startswith("chain"):
        r = P.gate_check(text, toks, WD, G, n13, T)
        adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
        return ("CATCH" if adj else "PASS"), r["summary"]["conflicts"]
    raise ValueError(mode)


MODES = ["r12", "n13", "chain", "r12_dg", "n13_dg", "chain_dg"]
stat = {m: {"ok": 0, "fp": 0, "fn": 0} for m in MODES}
changed = []
conf_old = conf_new = 0
for it in REG.CORPUS:
    got = {}
    for m in MODES:
        v = judge(it, m, shim)
        if isinstance(v, tuple):
            got[m], nc = v
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
        changed.append(it["id"])
for m in MODES:
    print("  %-9s ok=%-3d FP=%-2d FN=%-2d" % (m, stat[m]["ok"], stat[m]["fp"], stat[m]["fn"]))
print("  chain 层间冲突 old =", conf_old, " new =", conf_new,
      "; 结论变更条目 =", changed)
OUT["step4a_regression"] = {"corpus_n": len(REG.CORPUS), "stats": stat,
                            "changed": changed, "conflicts_old": conf_old,
                            "conflicts_new": conf_new, "blocked_writes": blocked}

# ========================= (5) 第五步(b)：自述边界核对 =========================
print("\n=== (5b) DNEG_GENERATIVE.md 自述边界：grep 实读 ===")
md = (DG_DIR / "DNEG_GENERATIVE.md").read_text(encoding="utf-8").splitlines()
for ln in [163, 167, 173, 174, 175, 184, 336, 347, 350, 352, 391, 393, 415, 418, 424, 428, 457, 462, 463, 469, 473]:
    print("  :%-4d %s" % (ln, md[ln - 1][:150]))
OUT["step5b_lines"] = {ln: md[ln - 1] for ln in [163, 167, 173, 174, 175, 184, 336, 347, 350, 352, 391, 393, 415, 418, 424, 428, 457, 462, 463, 469, 473]}

# ========================= (6) 越界核验：末二次指纹 + 全量快照 =========================
SNAP1 = fp_map()
drift = sorted(set(SNAP0.items()) ^ set(SNAP1.items()))
print("\n=== (6) 越界核验：会话末二次指纹 + 全量快照比对 ===")
for rel, (sha, n) in BASE_FP.items():
    b = (ROOT / rel).read_bytes()
    print("  %s %s %d %s" % ("MATCH   " if hashlib.sha256(b).hexdigest() == sha and len(b) == n
                            else "MISMATCH", hashlib.sha256(b).hexdigest(), len(b), rel))
print("  ALL_MATCH_2 =", all(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == sha
                            and (ROOT / rel).stat().st_size == n
                            for rel, (sha, n) in BASE_FP.items()))
print("  protected_snapshot_files_2 =", len(SNAP1), "; drift_count =", len(drift))
print("  drift =", drift[:10])
OUT["snapshot1_count"] = len(SNAP1)
OUT["protected_drift"] = drift

(WD / "_dgav_verify_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgav_verify_out.json")
