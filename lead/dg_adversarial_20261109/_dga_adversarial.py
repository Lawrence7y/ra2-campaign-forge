# -*- coding: utf-8 -*-
r"""_dga_adversarial.py — 第二步/第三步/第四步：自造对抗样本攻 DG「不误判」与 7 条不变式。

★ 全部样本由本任务自行构造，不从 DG 自带负样本集（N01-N20 / V01-V15 /
  W01-W30 / H5_EXTRA / 19 式）里挑。脚本用 AST（不执行）从只读件抽取那些
  字符串，逐条断言本样本集与其【零精确重合】，把「未用训练集」变成可复核事实。

零真机、零采样、只 re + 静态文本；只读保护件（hashlib 先验 9 件指纹）；
输出只落本写域 lead/dg_adversarial_20261109/。不修改任何既有件。

实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dg_adversarial_20261109/_dga_adversarial.py
"""
import sys, json, hashlib, importlib.util, re, ast
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dg_adversarial_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

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
print("=== (0) 只读件指纹先验 ===")
for rel, (sha, n) in EXPECT_FP.items():
    b = (ROOT / rel).read_bytes()
    assert hashlib.sha256(b).hexdigest() == sha and len(b) == n, "指纹失配 " + rel
    print("  MATCH", rel, len(b))


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


DG = _load("_dga2_dg", DG_DIR / "_dg_core.py")
H5 = _load("_dga2_h5", H5P)
G7 = _load("_dga2_g7", G7P)
# 「一行替换」交付形态：第二个真实模块实例，只换 DOUBLE_NEG_RE（照 _dgv_probe.py:27-31）
DROP = _load("_dga2_drop", G7P)
DROP.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert DROP.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

# =====================================================================
# ★ 自造对抗集：41 条。每条 (id, 形态, text, expect, reason, attack)
#   expect ∈ {PASS, CATCH, AMBIG}
#     PASS  = 不是双重否定（两个独立否定 / 跨微句 / 引文），门禁应放过
#     CATCH = 真双重否定（¬(¬P)），门禁应抓
#     AMBIG = 近似但语义不同，真值需所有者/语言学裁定；主统计不计 fp/fn，
#             另给 forced 口径（每条另注明保守应判）做敏感性分析
#   attack = 该样本攻的是 7 条不变式里的哪一条（'' = 非专项攻击）
# =====================================================================
CASES = [
    # ---- P 组：两个独立否定（应 PASS）：逗号 / 并列 / 递进 / 无标点连写 ----
    ("P01", "逗号分隔", "旧稿不承认，本件不宣告已生效", "PASS",
     "两个否定各管一个主语/谓语：¬承认(旧稿) ∧ ¬宣告(本件)，非 ¬(¬P)；逗号切断", ""),
    ("P02", "顿号并列", "旧稿未登记、本件亦未宣告已生效", "PASS",
     "顿号并列两项独立否定，两次 ¬ 不互相支配", ""),
    ("P03", "递进/追加", "无越权断言，也不出现放行 N-5 类措辞，本件不采信已生效", "PASS",
     "三项独立否定递进了两重逗号；无任何 ¬¬P 管辖链", ""),
    ("P04", "无标点连写", "前段不采信母本后段不宣告本件已生效", "PASS",
     "无标点但两个否定之间隔着实词「母本后段」，不是 ¬¬P", ""),
    ("P05", "并列成语式", "不核不录，本件不采信已生效", "PASS",
     "「不…不…」并列动作，两次独立否定；逗号后第三否定亦独立", ""),
    ("P06", "无标点转折", "前稿不敢不承认其实本件不宣告已生效", "PASS",
     "「其实」是转折/追补连词，但不在 DG_BREAK_RE(`_dg_core.py:89`) 也不在 _BQ(`:86`)；"
     "前段 DN 与后段独立否定被强行搭桥", "①"),
    ("P07", "无标点转折", "前稿不敢不承认说到底本件不宣告已生效", "PASS",
     "「说到底」未登记为边界词，跨两独立否定搭桥", "①"),
    ("P08", "无标点让步", "旧稿并不否认尽管本件不宣告已生效", "PASS",
     "「尽管」未登记；「并不否认」是完整否定谓语，「本件不宣告」另起主语", "①④"),
    ("P09", "第二主语", "旧稿并不否认与监理方不宣告已生效", "PASS",
     "「监理方」是第二主语但不在 _SECOND(`_dg_core.py:88`) 表内；"
     "且 NEG2 的「否认」本身即完整否定谓语，零通配 T12 仍能拼出跨主语命中", "③④"),
    ("P10", "并列项", "本件不承认或并不否认已生效", "PASS",
     "「或」在 DG_COORD_RE(`:91`) 内，但二次 veto 只查 hit_text(`:182-184`)，"
     "hit_text='并不否认' 不含「或」⇒ 并列否决不生效", "⑤"),
    ("P11", "未登记引号", "\"并非不宣告已生效\"只是引文，本件不采信该说法", "PASS",
     "ASCII 双引号不在 DG_QUOTE_RE(`_dg_core.py:92`) 的 4 类引号内；"
     "DN 只是引文，正文「不采信」为独立否定", "②"),
    ("P12", "未登记引号", "《并不否认已生效》只是引文，本件不采信该说法", "PASS",
     "书名号《》未登记；引证跨度未被 _mask_quotes 屏蔽", "②"),
    ("P13", "关联并列", "既不宣告旧稿已入账，也不宣告本件已生效", "PASS",
     "「既…也…」关联并列两项独立否定", ""),
    ("P14", "无标点递进", "不予登记亦不宣告本件已生效", "PASS",
     "无标点、两次独立否定，中间「亦」为副词但不是 MID 合法项", ""),
    ("P15", "带转折的真否定", "旧稿不承认，但本件也不宣告已生效", "PASS",
     "转折后仍是单重否定；两处都只有 ¬，无 ¬¬P", ""),
    ("P16", "跨句周遍", "莫不称颂旧稿，本件不采信已生效", "PASS",
     "前句「莫不」周遍 DN，逗号切断；token 落在后句独立否定内", ""),
    ("P17", "引号内置空格", "「 并非不宣告已生效 」只是引文，本件不采信该说法", "PASS",
     "DG 的 _mask_quotes 把跨度内部置空格（含内置空格）⇒ PASS 正确；"
     "但 R12 字面与 H5 字面不看引证，均误命中。用于对照 ② 的另一侧", "②"),
    # ---- C 组：真双重否定（应 CATCH），含 19 式之外构式 ----
    ("C01", "未登记 MID", "不容不宣告本件已生效", "CATCH",
     "不容(不宣告) = 必须宣告，¬(¬P)。MID「容」不在 23 项闭合表(`_dg_core.py:55-61`)", "③"),
    ("C02", "未登记 MID", "未许不宣告本件已生效", "CATCH",
     "未曾允许(不宣告) = 必须宣告。MID「许」未登记", "③"),
    ("C03", "未登记 MID", "别想不登记本件已入账", "CATCH",
     "别想(不登记) = 必须登记。MID「想」未登记", "③"),
    ("C04", "未登记 MID", "甭想不承认本件已生效", "CATCH",
     "甭想(不承认) = 必须承认。MID「想」未登记", "③"),
    ("C05", "未登记 MID", "没准不承认本件已生效", "CATCH",
     "没准(不承认) = 不许不承认。MID「准」未登记", "③"),
    ("C06", "分离式 COMP=4", "非登记五份原件不可才算本件已生效", "CATCH",
     "「非…不可」分离式真 DN；COMP='五份原件' 恰 4 字，落在 ≤4 边界内", "③"),
    ("C07", "分离式 COMP=5", "非登记五份原始件不可才算本件已生效", "CATCH",
     "同一构式，COMP='五份原始件' 5 字 ⇒ 唯一通配 {0,4}? 越界(`_dg_core.py:118`)，真 DN 漏判", "③"),
    ("C08", "分离式含并列", "非登记一或二不可才算本件已生效", "CATCH",
     "「非…不可」= 必须登记，是真 DN；COMP 含「或」触发 DG_COORD_RE 二次 veto(`:182-184`)，"
     "把真 DN 当成「两个独立否定项」否决掉", "⑤"),
    ("C09", "分离式含第二主语", "非登记本件不可才算本件已生效", "CATCH",
     "「非…不可」真 DN；COMP 含 _SECOND 项「本件」被 comp 负向前瞻(`:118`)排除，真 DN 漏判", "④"),
    ("C10", "第二主语即主语", "并非本件不宣告已生效", "CATCH",
     "「本件」是「不宣告」的主语，而「并非」管辖整个命题：¬(本件¬宣告) = 本件宣告。"
     "第二主语存在但【确实】是双重否定", "④"),
    ("C11", "PSEUDO veto", "非不承认本件已生效", "CATCH",
     "「非不」在 PSEUDO_DN 12 项(`:81-82`)内被词首负向前瞻否决；但「非不承认」= 并非不承认 = 承认，是真 DN", "⑥"),
    ("C12", "PSEUDO veto", "非不认可本件已生效", "CATCH",
     "同上，「非不认可」= 并非不认可；被同一 veto 否决", "⑥"),
    ("C13", "19 式外构式", "何尝不认为本件已生效", "CATCH",
     "反问型 ¬(¬认为)，19 式与 H5 28 支字面表均未登记", ""),
    ("C14", "19 式外构式", "不见得不认为本件已生效", "CATCH",
     "「不见得」+ NEG2「不」构成 ¬(¬认为)；H5 字面表未登记", ""),
    ("C15", "19 式外构式", "岂敢不承认本件已生效", "CATCH",
     "反问型真 DN，19 式 / H5 字面表均未登记", ""),
    ("C16", "19 式外构式", "不由得不承认本件已生效", "CATCH",
     "「不由得不」= 忍不住要承认，真 DN；H5 字面表未登记", ""),
    ("C17", "带转折的真 DN", "虽未明说，但并非不宣告本件已生效", "CATCH",
     "转折后的微句内才是真 DN；转折词应切断前句而不切断后句内的 ¬¬P", ""),
    ("C18", "带转折的真 DN", "本件虽未登记，然而亦非不宣告已生效", "CATCH",
     "「然而」后微句内「亦非不」= ¬(¬宣告)，真 DN", ""),
    ("C19", "三否定词", "未漏核，并非不宣告本件已生效", "CATCH",
     "否定词 3 个（未/非/不）；奇偶计数会误豁免，不用奇偶是对的（`_g7_predicates.py:74-75`）", "⑦"),
    ("C20", "PSEUDO 位置局部性对照", "莫不是不承认本件已生效", "AMBIG",
     "「莫不是」疑问副词使整句成为反问而非完成断言；内层「不是不承认」= 承认（¬¬P）。"
     "真值需裁定；用作对照说明 ⑥ 的 veto 是位置局部的、不是全域屏蔽"
     "（命中从「不是不」处另起，DG/H5/R12 全 CATCH）", "⑥"),
    # ---- A 组：近似但语义不同（歧义句）----
    ("A01", "歧义", "非但不否认本件已生效", "AMBIG",
     "「非但…」关联连词（伪构式）与「不否认」完整否定谓语两解："
     "若取「非但不 + 否认」则只有一个有效否定（应 PASS）；若取「非(但不否认)」则近似 ¬¬P。"
     "保守口径应 PASS/NEEDS_HUMAN，不直接 CATCH", "⑥"),
    ("A02", "歧义", "莫非并不否认本件已生效", "AMBIG",
     "「莫非」疑问副词 + 「并不否认」真 DN；整句是反问而非完成断言，"
     "在「完成断言」语境下是否算越权需人工裁定。保守口径应 PASS/NEEDS_HUMAN", "⑥⑦"),
    ("A03", "歧义", "不无关系地宣告本件已生效", "AMBIG",
     "「不无」弱化肯定作状语修饰「地宣告」，不是对 token 的 ¬¬P 断言；"
     "DNEG_GENERATIVE.md:132/:469 自陈此项需所有者裁定。保守口径应 PASS/NEEDS_HUMAN", "⑥⑦"),
    ("A04", "歧义", "没不承认本件已生效", "AMBIG",
     "「没不」被 PSEUDO_DN 否决；口语「没不承认」= 没有不承认 = 承认（真 DN），"
     "但是否成词/是否合法汉语有争议。保守口径应 CATCH 若承认为真 DN", "⑥"),
]
# AMBIG 的保守（forced）应判，用于敏感性分析；逐条给理由见上
FORCED = {"A01": "PASS", "A02": "PASS", "A03": "PASS", "A04": "CATCH", "C20": "CATCH"}

# =====================================================================
# ★ 未用训练集的可复核验证：AST 抽取 DG 自带负样本集，精确零重合断言
# =====================================================================
TRAIN_SOURCES = {
    "N01-N20 (_dg_step34.py:63-84)": DG_DIR / "_dg_step34.py",
    "V01-V15 (_dgv_probe.py:72-97)": DG_DIR / "_dgv_probe.py",
    "W01-W30 (_dgv_neg2.py:40-88)": DG_DIR / "_dgv_neg2.py",
    "19式 (_dg_step1.py:30-50)": DG_DIR / "_dg_step1.py",
    "H5_EXTRA17 (_dg_step34.py:89-93)": DG_DIR / "_dg_step34.py",
}
train_strings = {}
for tag, p in TRAIN_SOURCES.items():
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    strs = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strs.add(node.value)
    train_strings[tag] = strs
all_train = set().union(*train_strings.values())
my_texts = {c[2] for c in CASES}
overlap = sorted(my_texts & all_train)
print("\n=== (N) 对抗集与 DG 自带负样本集精确重合检查（AST 静态抽取，不执行）===")
for tag, s in train_strings.items():
    print("  %-42s 抽取字符串 %d 条，与本集精确重合 %d" %
          (tag, len(s), len(my_texts & s)))
print("  自造样本数 =", len(CASES), "; 与全部训练集精确重合 =", len(overlap), overlap)
assert not overlap, "对抗样本与 DG 训练集重合，违反任务书铁律"

# =====================================================================
# 六个判定器
#   DG_pure   = DG.dg_scan（设计稿声称「不误判」的纯函数，带 4 条 guard）
#   DG_dropin = 一行替换真实模块（_dgv_probe.py 口径，guard 全不执行）
#   H5_lit    = H5_DOUBLE_NEG_RE 字面超集（编排方说「H5 也 19/19」的那个对象）
#   H5_gov    = H5.h5_govern(pre,post)["double_neg"]（带 G1-G4 作用域）
#   R12       = G7.r12_scan（既有门禁谓词）
#   R12_lit   = G7.DOUBLE_NEG_RE 字面十式
# =====================================================================
DETECTORS = ["DG_pure", "DG_dropin", "H5_lit", "H5_gov", "R12", "R12_lit"]


def detect(text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    r = {k: "PASS" for k in DETECTORS}
    hits = {}
    # DG 纯函数
    p, h = DG.dg_scan(text, toks)
    r["DG_pure"] = "CATCH" if p else "PASS"
    hits["DG_pure"] = h[0]["hit"] if h else ""
    # DG 一行替换
    pd, _ = DROP.r12_scan(text, toks)
    r["DG_dropin"] = "CATCH" if pd else "PASS"
    raw = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            mm = DG.DG_DROPIN_RE.search(text[:m.start()])
            if mm:
                raw.append(mm.group(0))
    hits["DG_dropin"] = raw[0] if raw else ""
    # H5 字面超集
    ml = H5.H5_DOUBLE_NEG_RE.search(text)
    r["H5_lit"] = "CATCH" if ml else "PASS"
    hits["H5_lit"] = ml.group(0) if ml else ""
    # H5 管辖函数
    hg, hh = False, ""
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            g = H5.h5_govern(text[:m.start()], text[m.end():])
            if g["double_neg"]:
                hg, hh = True, g["dn_hit"]
    r["H5_gov"] = "CATCH" if hg else "PASS"
    hits["H5_gov"] = hh
    # R12
    p12, _ = G7.r12_scan(text, toks)
    r["R12"] = "CATCH" if p12 else "PASS"
    m12 = G7.DOUBLE_NEG_RE.search(text)
    r["R12_lit"] = "CATCH" if m12 else "PASS"
    hits["R12_lit"] = m12.group(0) if m12 else ""
    # 奇偶计数（仅信息，用于 ⑦）
    negc = 0
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            s = max(0, m.start() - G7.NEG_WINDOW)
            bd = max(text.rfind(ch, 0, m.start()) for ch in G7.CLAUSE_BREAK)
            if bd > s:
                s = bd
            negc = max(negc, len(G7.NEG_RE.findall(text[s:m.start()])))
    return r, hits, negc, toks


print("\n=== (2) 41 条自造对抗样本逐条实跑（六判定器）===")
rows = []
for cid, shape, text, exp, why, attack in CASES:
    r, hits, negc, toks = detect(text)
    rows.append({"id": cid, "shape": shape, "text": text, "expect": exp,
                 "forced": FORCED.get(cid, exp), "why": why, "attack": attack,
                 "tokens": toks, "neg_count": negc, "verdicts": r, "hits": hits})
    print("  %-4s exp=%-5s | DG_pure=%-5s DG_drop=%-5s H5_lit=%-5s H5_gov=%-5s R12=%-5s R12_lit=%-5s | %s" %
          (cid, exp, r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["H5_gov"],
           r["R12"], r["R12_lit"], text[:30]))


def score(rows, key, forced=False):
    fp = fn = amb = 0
    fp_ids, fn_ids = [], []
    for x in rows:
        exp = x["forced"] if forced else x["expect"]
        if exp == "AMBIG":
            amb += 1
            continue
        got = x["verdicts"][key]
        if exp == "PASS" and got == "CATCH":
            fp += 1
            fp_ids.append(x["id"])
        elif exp == "CATCH" and got == "PASS":
            fn += 1
            fn_ids.append(x["id"])
    return {"n_scored": len(rows) - amb, "n_ambig_excluded": amb,
            "fp": fp, "fn": fn, "fp_ids": fp_ids, "fn_ids": fn_ids}


# forced 口径下，AMBIG 条目已按保守应判计入，不再排除
def score_forced(rows, key):
    fp = fn = 0
    fp_ids, fn_ids = [], []
    for x in rows:
        exp, got = x["forced"], x["verdicts"][key]
        if exp == "PASS" and got == "CATCH":
            fp += 1
            fp_ids.append(x["id"])
        elif exp == "CATCH" and got == "PASS":
            fn += 1
            fn_ids.append(x["id"])
    return {"n_scored": len(rows), "n_ambig_excluded": 0,
            "n_ambig_forced": sum(1 for x in rows if x["expect"] == "AMBIG"),
            "fp": fp, "fn": fn, "fp_ids": fp_ids, "fn_ids": fn_ids}


print("\n=== (2/4a) fp / fn 统计（严格口径：AMBIG 不计）===")
strict = {}
for k in DETECTORS:
    strict[k] = score(rows, k)
    print("  %-10s n=%-3d fp=%-2d %-28s fn=%-2d %s" %
          (k, strict[k]["n_scored"], strict[k]["fp"], str(strict[k]["fp_ids"]),
           strict[k]["fn"], str(strict[k]["fn_ids"])))
print("\n=== (2/4a) fp / fn 统计（forced 口径：全部 41 条，AMBIG 按保守应判计入）===")
forced = {}
for k in DETECTORS:
    forced[k] = score_forced(rows, k)
    print("  %-10s n=%-3d fp=%-2d %-28s fn=%-2d %s" %
          (k, forced[k]["n_scored"], forced[k]["fp"], str(forced[k]["fp_ids"]),
           forced[k]["fn"], str(forced[k]["fn_ids"])))

# =====================================================================
# (3) 7 条不变式逐条攻击 + 4 处特别攻击
# =====================================================================
print("\n=== (3a) 不变式 ① 边界词表未穷尽：未登记转折/让步词扫描 ===")
BREAK_WORDS = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另",
               "其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "可", "反倒说", "结果", "终究"]
break_rows = []
for w in BREAK_WORDS:
    t = "前稿不敢不承认" + w + "本件不宣告已生效"
    r, _, _, _ = detect(t)
    in_break = bool(DG.DG_BREAK_RE.search(w))
    in_bq = bool(re.search("[" + DG._BQ + "]", w))
    break_rows.append({"word": w, "in_DG_BREAK_RE": in_break, "in_BQ": in_bq,
                       "DG_pure": r["DG_pure"], "DG_dropin": r["DG_dropin"],
                       "H5_gov": r["H5_gov"], "R12": r["R12"], "text": t})
    print("  %-6s BREAK=%-5s BQ=%-5s DG_pure=%-5s DG_drop=%-5s H5_gov=%-5s R12=%s" %
          (w, in_break, in_bq, r["DG_pure"], r["DG_dropin"], r["H5_gov"], r["R12"]))
unreg_fp = [x["word"] for x in break_rows if not x["in_DG_BREAK_RE"]
            and x["DG_pure"] == "CATCH"]
print("  → 未登记边界词中 DG_pure 仍 CATCH（应 PASS）的词 =", unreg_fp)

print("\n=== (3b) 不变式 ③ MID 23 项闭合表：未登记虚词造成真 DN 漏判 ===")
MID_CAND = ["容", "许", "想", "准", "愿", "甘", "料", "要", "需", "欲", "肯", "屑", "便", "该", "应",
            "得", "能", "可", "敢", "会", "尝", "曾", "有", "必", "免", "始", "谓", "为", "是", "说"]
mid_rows = []
for w in MID_CAND:
    t = "不" + w + "不宣告本件已生效"
    _, h, _, _ = detect(t)
    dgp = detect(t)[0]["DG_pure"]
    mid_rows.append({"mid": w, "in_MID_table": w in set(DG.MID), "DG_pure": dgp,
                     "hit": h["DG_pure"], "text": t})
    print("  MID=%-3s 在表内=%-5s DG_pure=%-5s hit=%-8s | %s" %
          (w, w in set(DG.MID), dgp, h["DG_pure"], t[:24]))
unreg_miss = [x["mid"] for x in mid_rows if not x["in_MID_table"] and x["DG_pure"] == "PASS"]
print("  → 未登记 MID 且真 DN 被漏判 =", unreg_miss, "（共 %d 个）" % len(unreg_miss))

print("\n=== (3c) 不变式 ③ COMP ≤4 字：补语长度扫描 ===")
comp_rows = []
for n in range(0, 8):
    comp = "原" * n
    t = "非登记" + comp + "不可才算本件已生效"
    r, h, _, _ = detect(t)
    comp_rows.append({"n": n, "comp": comp, "DG_pure": r["DG_pure"],
                      "DG_dropin": r["DG_dropin"], "hit": h["DG_dropin"], "text": t})
    print("  COMP 字数=%d DG_pure=%-5s DG_drop=%-5s hit=%-16s | %s" %
          (n, r["DG_pure"], r["DG_dropin"], h["DG_dropin"], t[:26]))
print("  → ≤4 命中 / >4 漏判；边界在 n=4→5 之间（与 `_dg_core.py:118` {0,4}? 一致）")

print("\n=== (3d) 不变式 ④ 第二主语：否决不可达性静态证明 + 双向反例 ===")
parts = (list(DG.NEG1) + list(DG.MID) + list(DG.NEG2) + list(DG.GAP) +
         list(DG.SCOPE_VERB) + list(DG.SPLIT_TAIL))
second_tokens = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔",
                 "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"]
in_parts = [(s, [p for p in parts if s in p]) for s in second_tokens]
print("  _SECOND 任一项是否出现在任何闭合表条目内 =",
      {s: v for s, v in in_parts if v} or "{}（全为空）")
print("  → T12 的 hit_text = N1+MID+N2；T3 的 hit_text = N1+GAP+V+COMP+TAIL，"
      "而 comp 的负向前瞻(`_dg_core.py:118`)已排除 _SECOND ⇒ "
      "`dg_double_neg` 的第二主语 veto(`:179-181`) 结构性不可达（与 DNEG_GENERATIVE.md:174 一致）")
ss_cases = ["并非本件不宣告已生效", "并非该件不宣告已生效", "并非本笔不宣告已生效",
            "非登记本件不可才算本件已生效", "非登记原件不可才算本件已生效",
            "旧稿并不否认与监理方不宣告已生效", "并不否认甲方不宣告已生效"]
ss_rows = []
for t in ss_cases:
    r, h, _, _ = detect(t)
    ss_rows.append({"text": t, "verdicts": r, "hits": h})
    print("  %-34s DG_pure=%-5s DG_drop=%-5s H5_lit=%-5s H5_gov=%-5s R12=%-5s hit=%s" %
          (t[:32], r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["H5_gov"],
           r["R12"], h["DG_dropin"]))
# 纯函数 veto 实际触发次数
veto_fired = 0
for x in rows:
    for tok in x["tokens"]:
        for m in re.finditer(re.escape(tok), x["text"]):
            d = DG.dg_double_neg(x["text"][:m.start()])
            if "第二主语" in d["reason"] or "并列标记" in d["reason"]:
                veto_fired += 1
print("  → 41 条样本上纯函数二次 veto 实际触发次数 =", veto_fired)

print("\n=== (3e) 不变式 ⑤ 并列否决：只查 hit_text 的双向后果 ===")
coord_rows = []
for t in ["本件不承认或并不否认已生效", "本件不承认、并不否认均不成立已生效",
          "非登记一或二不可才算本件已生效", "非登记甲、乙不可才算本件已生效",
          "非登记原件不可才算本件已生效"]:
    r, h, _, _ = detect(t)
    coord_rows.append({"text": t, "verdicts": r, "hits": h})
    print("  %-34s DG_pure=%-5s DG_drop=%-5s H5_lit=%-5s R12=%-5s raw_hit=%s" %
          (t[:32], r["DG_pure"], r["DG_dropin"], r["H5_lit"], r["R12"], h["DG_dropin"]))

print("\n=== (3f) 不变式 ⑥ PSEUDO_DN 12 项：词汇化 veto 与真 DN 的冲突 ===")
pseudo_rows = []
for p in DG.PSEUDO_DN:
    t = p + "不承认本件已生效"
    raw = bool(DG.DG_DROPIN_RE.search(t[:t.find("已生效")]))
    pure = bool(DG.dg_scan(t, ["已生效"])[0])
    pseudo_rows.append({"pseudo": p, "text": t, "raw": raw, "pure": pure})
    print("  PSEUDO=%-5s raw_regex=%-5s DG_pure=%-5s | %s" % (p, raw, pure, t[:26]))
print("  → veto 是【词首】负向前瞻(`_dg_core.py:116`)：命中从 veto 词之后另起时仍会 CATCH"
      "（对照 C20「莫不是不承认」、K「无非不是不承认」）")

print("\n=== (3g) 不变式 ⑦ 不做奇偶计数：奇偶法 vs DG 的四象限 ===")
parity_rows = []
for cid, text, exp in [
    ("G1", "不查不验本件已生效", "PASS"),           # 2 否定词， parity 会误 CATCH
    ("G2", "未漏核，并非不宣告本件已生效", "CATCH"),  # 3 否定词， parity 会误 PASS
    ("G3", "非登记五份原始件不可才算本件已生效", "CATCH"),  # 2 否定词，parity 对、DG 错
    ("G4", "前稿不敢不承认其实本件不宣告已生效", "PASS"),  # 奇数，parity 对、DG 错
]:
    r, h, negc, _ = detect(text)
    parity = "CATCH" if negc % 2 == 0 and negc > 0 else "PASS"
    parity_rows.append({"id": cid, "text": text, "expect": exp, "neg_count": negc,
                        "parity_verdict": parity, "DG_pure": r["DG_pure"], "hits": h})
    print("  %s neg_count=%d expect=%-5s parity=%-5s DG_pure=%-5s | %s" %
          (cid, negc, exp, parity, r["DG_pure"], text[:34]))
print("  → 「不做奇偶」避免 G1/G2 两类错，但不防 G3/G4；它不是不误判的保证")

# =====================================================================
# (4c) 维护成本量化
# =====================================================================
print("\n=== (4c) 维护成本：新增一个构式需要动的表 / 扰动面 ===")
S = DG.DG_STATS
n1, mid, n2 = len(set(DG.NEG1)), len(set(DG.MID)), len(set(DG.NEG2))
gap, verb, tail = len(set(DG.GAP)), len(set(DG.SCOPE_VERB)), len(set(DG.SPLIT_TAIL))
maint = {
    "DG_tables": {"NEG1": n1, "MID": mid, "NEG2": n2, "GAP": gap,
                  "SCOPE_VERB": verb, "SPLIT_TAIL": tail,
                  "PSEUDO_DN": len(set(DG.PSEUDO_DN)),
                  "plus_scope_constants": ["_BREAK", "_BQ", "_SECOND", "DG_COORD_RE", "DG_BREAK_RE"]},
    "DG_new_entry_delta": {
        "add_MID_entry_T12_strings": n1 * n2,
        "add_NEG1_entry_strings": mid * n2 + gap * verb * tail,
        "add_NEG2_entry_T12_strings": n1 * mid,
        "add_SPLIT_TAIL_entry_T3_strings": n1 * gap * verb,
        "add_GAP_entry_T3_strings": n1 * verb * tail,
        "add_SCOPE_VERB_entry_T3_strings": n1 * gap * tail,
    },
    "DG_stats": S,
    "H5_literal_branches": {"H5_R12_TEN": len(re.findall(r"[^|]+", H5.H5_R12_TEN)),
                            "H5_DN_EXTRA": len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)),
                            "H5_BRIDGE_RE_operator_branches": 51},
    "H5_new_construct_delta": "1 个字面选择支（H5_DN_EXTRA 加 1 条）= 精确 1 个新串；"
                              "若走通配支则另需改 H5_MICRO_BREAK_RE / H5_SELF_SUBJ_RE 等作用域表",
}
for k, v in maint["DG_new_entry_delta"].items():
    print("  %-42s = %d 个新生成串" % (k, v))
print("  DG 表数 = 7 张闭合表 + 5 组作用域常量；H5 = 2 张 DN 字面表 + 若干作用域正则")
print("  DG 生成串总数 =", S["cartesian_total"], "; H5 DN 字面支数 =",
      maint["H5_literal_branches"]["H5_R12_TEN"] + maint["H5_literal_branches"]["H5_DN_EXTRA"])

out = {
    "fingerprints": {k: {"sha": v[0], "bytes": v[1], "verified": True} for k, v in EXPECT_FP.items()},
    "novelty": {"n_cases": len(CASES),
                "train_sets": {k: len(v) for k, v in train_strings.items()},
                "exact_overlap": overlap,
                "note": "AST 静态抽取只读件的字符串常量；零精确重合；"
                        "本集句子均为自行构造，部分与训练样本共享构式词（如 不敢不承认）但不重合句子"},
    "cases": rows,
    "scoring_strict": strict, "scoring_forced": forced,
    "detectors": DETECTORS,
    "invariant_attacks": {
        "①_break_words": break_rows, "①_unregistered_fp_words": unreg_fp,
        "③_mid": mid_rows, "③_unregistered_miss": unreg_miss,
        "③_comp_sweep": comp_rows, "④_second_subject": ss_rows,
        "④_second_in_parts": {s: v for s, v in in_parts if v},
        "④_veto_fired_on_corpus": veto_fired,
        "⑤_coord": coord_rows, "⑥_pseudo": pseudo_rows, "⑦_parity": parity_rows,
    },
    "maintenance": maint,
}
(WD / "_dga_adversarial_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dga_adversarial_out.json")
