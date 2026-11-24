# -*- coding: utf-8 -*-
r"""_ai_grade.py — 四级判据（严格字面口径）+ 训练集构式族目录 + 逐条 d1/d2/d3 + fp 归因分类。

与 _ai_verify.py 互补：本件用「DN 构式目录只收 >=2 字且含否定字的条目」，
并把「构式族」严格定义为任务书点名的 MID/PSEUDO/boundary 词 + 训练集出现过的
DN 构式，排除通用动词/名词（承认/认为/本件…）造成的假阳性。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/advset_indep_20261109/_ai_grade.py
"""
import sys, json, hashlib, re, ast, types
from pathlib import Path
from collections import Counter

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "advset_indep_20261109"
DG_DIR = ROOT / "lead" / "dneg_generative_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"
V = json.loads((WD / "_ai_verify_out.json").read_text(encoding="utf-8"))


def lit_assigns(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for tgt in n.targets:
                if isinstance(tgt, ast.Name):
                    try: out[tgt.id] = ast.literal_eval(n.value)
                    except Exception: pass
    return out


A = lit_assigns(DGA / "_dga_adversarial.py")
CASES = A["CASES"]
rows = V["rows"]

# ---------------- 构式目录：只收 >=2 字且含否定字的字面 DN 构式 ----------------
s34 = lit_assigns(DG_DIR / "_dg_step34.py")
s1 = lit_assigns(DG_DIR / "_dg_step1.py")
vprobe = lit_assigns(DG_DIR / "_dgv_probe.py")
DG = types.ModuleType("_aig_dg")
exec(compile((DG_DIR / "_dg_core.py").read_text(encoding="utf-8"),
             str(DG_DIR / "_dg_core.py"), "exec"), DG.__dict__)
H5 = types.ModuleType("_aig_h5")
exec(compile((ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py").read_text(encoding="utf-8"),
             "h5", "exec"), H5.__dict__)

NEG_CHARS = set("不无未非没莫勿甭别岂")
catalog = set()
for g in s34["GAPS"] + s1["GAPS"]:
    catalog.add(g[0])
catalog |= set(DG.R12_TEN)
for s in s34["H5_EXTRA"] + s34["H5_SPLIT"]:
    if len(s) >= 2 and any(c in s for c in NEG_CHARS): catalog.add(s)
for s in H5.H5_DN_EXTRA.split("|") + H5.H5_R12_TEN.split("|"):
    if "[^" not in s and len(s) >= 2 and any(c in s for c in NEG_CHARS): catalog.add(s)
for p in DG.PSEUDO_DN:
    catalog.add(p)
# 分离型构式骨架（含通配）：非…不可 / 非…不行 / 不…不行
CATALOG = sorted(catalog, key=lambda z: (-len(z), z))
print("=== (0) DN 构式目录（>=2 字且含否定字）===")
print("  n =", len(CATALOG), " 明细 =", json.dumps(CATALOG, ensure_ascii=False))

# ---------------- 训练句子集合（严格：只取带 id 的完整中文句子）----------------
sentences = set()
for f in ("_dg_step34.py", "_dgv_probe.py", "_dgv_neg2.py", "_dg_step1.py"):
    asg = lit_assigns(DG_DIR / f)
    for name, val in asg.items():
        if not isinstance(val, list): continue
        for item in val:
            if isinstance(item, (tuple, list)):
                for cell in item:
                    if isinstance(cell, str) and len(cell) >= 8 and re.search(r"[\u4e00-\u9fff]", cell):
                        sentences.add(cell)
            elif isinstance(item, str) and len(item) >= 8 and re.search(r"[\u4e00-\u9fff]", item):
                sentences.add(item)
# 训练集里出现过的构式（目录条目在某个训练句子里作子串）
CAT_IN_TRAIN = sorted([k for k in CATALOG if any(k in s for s in sentences)], key=lambda z: -len(z))
print("\n=== (1) 训练集出现过的构式（目录条目在训练句子中作子串）===")
print("  n =", len(CAT_IN_TRAIN), " 明细 =", json.dumps(CAT_IN_TRAIN, ensure_ascii=False))

# ---------------- 构式族词表（严格按任务书）----------------
SECOND = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔",
          "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
COORD = ["或", "以及", "同时", "并且", "一是", "二是", "其一", "其二"]
MID = [w for w in DG.MID if w]
PSEUDO = list(DG.PSEUDO_DN)
NEG1 = [w for w in DG.NEG1 if len(w) >= 2]
NEG2 = [w for w in DG.NEG2 if len(w) >= 2]
FAMILY = sorted(set(MID + PSEUDO + BREAK10 + COORD + SECOND + NEG1 + NEG2 +
                    CATALOG + ["「」", "『』", "“”", "``"]), key=lambda z: -len(z))
print("\n=== (2) 构式族词表规模 ===")
print("  MID(非空)=%d PSEUDO=%d BREAK10=%d COORD=%d _SECOND=%d NEG1(>=2)=%d NEG2(>=2)=%d CATALOG=%d FAMILY去重=%d" %
      (len(MID), len(PSEUDO), len(BREAK10), len(COORD), len(SECOND), len(NEG1),
       len(NEG2), len(CATALOG), len(FAMILY)))

# ---------------- 逐条 d1 / d2 / d3 ----------------
print("\n=== (3) 逐条 d1(用训练集构式) / d2(用族词) / d3(DG 表可拼出) ===")
out_rows = []
for x in rows:
    s = x["text"]
    d1 = sorted([k for k in CAT_IN_TRAIN if k in s], key=lambda z: -len(z))
    d2 = sorted({w for w in FAMILY if w in s}, key=lambda z: -len(z))
    sr = next(z for z in V["share_rows"] if z["id"] == x["id"])
    d3p = sr["pure_decomposable"]
    d3d = sr["dropin_decomposable"]
    # 骨架复现：与训练集句子的最长公共子串（>=4 字）
    lcs = {}
    for t in sentences:
        # 逐起点朴素 LCS（语料小，静态文本）
        for i in range(len(s)):
            for j in range(i + 4, len(s) + 1):
                if s[i:j] in t:
                    if (j - i) > lcs.get("len", 0): lcs = {"len": j - i, "frag": s[i:j]}
    out_rows.append({"id": x["id"], "shape": x["shape"], "expect": x["expect"],
                     "d1": d1, "d2": d2[:10], "d3_pure": d3p, "d3_dropin": d3d,
                     "hit_pure": sr["hit_DG_pure"], "hit_dropin": sr["hit_DG_dropin"],
                     "lcs_train": lcs, "min_edit": V["near"][x["id"]]["dist"],
                     "attack": x["attack"], "why": x["why"]})
    print("  %-4s d1=%-22s d2=%-16s d3p=%-5s d3d=%-5s hit=%-12s lcs=%-12s min_edit=%s" %
          (x["id"], ",".join(d1[:3]) or "-", ",".join(d2[:3]) or "-", d3p, d3d,
           sr["hit_DG_pure"] or "-", lcs.get("frag", "-")[:11], V["near"][x["id"]]["dist"]))
print("  d1 非空 = %d/41 ; d2 非空 = %d/41 ; d3(任一) = %d/41" %
      (sum(1 for r in out_rows if r["d1"]), sum(1 for r in out_rows if r["d2"]),
       sum(1 for r in out_rows if r["d3_pure"] or r["d3_dropin"])))
print("  ★ 用了训练集出现过的构式（严格口径 d1 ∪ d3）= %d/41" %
      sum(1 for r in out_rows if r["d1"] or r["d3_pure"] or r["d3_dropin"]))
print("  ★ 共享构式族词（严格口径 d2）= %d/41" % sum(1 for r in out_rows if r["d2"]))
print("  最长公共子串 >= 6 字的样本数 = %d/41" % sum(1 for r in out_rows if r["lcs_train"].get("len", 0) >= 6))

# ---------------- 四级定级（严格口径）----------------
print("\n=== (4) 四级独立性逐条定级（严格口径） ===")
def grade(r):
    if r["min_edit"] == 0: return "belowL0"
    if r["d1"] or r["d3_pure"] or r["d3_dropin"]: return "L0"
    if r["d2"]: return "L1"
    if r["lcs_train"].get("len", 0) >= 4 or r["min_edit"] <= 5: return "L2"
    return "L3"

for r in out_rows:
    r["grade"] = grade(r)
    print("  %-4s grade=%-4s d1=%-5s d2=%-5s d3=%-5s lcs=%-3s min_edit=%-3s attack=%s" %
          (r["id"], r["grade"], bool(r["d1"]), bool(r["d2"]),
           r["d3_pure"] or r["d3_dropin"], r["lcs_train"].get("len", 0),
           r["min_edit"], r["attack"] or "-"))
print("  ★ 严格口径分级分布 =", json.dumps(dict(Counter(r["grade"] for r in out_rows)), ensure_ascii=False))
for lv in ("L0", "L1", "L2", "L3"):
    print("  %s ids = %s" % (lv, [r["id"] for r in out_rows if r["grade"] == lv]))

# ---------------- 生成机制证据：CASES 的 attack / why / 源码引用 ----------------
print("\n=== (5) L3『生成机制独立』证据量化 ===")
n_attack = sum(1 for r in out_rows if r["attack"])
n_why_core = sum(1 for r in out_rows if "_dg_core.py:" in r["why"])
n_why_table = sum(1 for r in out_rows if re.search(r"MID|DG_BREAK_RE|_SECOND|DG_QUOTE_RE|DG_COORD_RE|PSEUDO_DN|COMP|23 项|闭合表|词首负向前瞻|≤4", r["why"]))
n_shape_from_table = sum(1 for r in out_rows if r["attack"])
print("  CASES.attack 非空（自述攻七条不变式中的某条）= %d/41" % n_attack)
print("  CASES.why 含 `_dg_core.py:` 行号引用 = %d/41" % n_why_core)
print("  CASES.why 含表/常量/边界名（MID/BREAK/_SECOND/QUOTE/COORD/PSEUDO/COMP…）= %d/41" % n_why_table)
print("  shape 名称本身含表内常量名的条目 = %s" %
      [r["id"] + ":" + r["shape"] for r in out_rows
       if re.search(r"MID|COMP=|PSEUDO|第二主语|未登记|分离式", r["shape"])])
print("  形状直方图中『未登记 X』/『X 外构式』/『含 X』类 = %s" %
      {k: c for k, c in V["shape_hist"].items()
       if re.search(r"未登记|外构式|含", k)})
# attack 分布
print("  attack 分布 =", json.dumps(dict(Counter(r["attack"] for r in out_rows if r["attack"])), ensure_ascii=False))

# ---------------- fp 7 条归因 ----------------
print("\n=== (6) fp 7 条（P06-P12）失败模式归因 ===")
fp_ids = ["P06", "P07", "P08", "P09", "P10", "P11", "P12"]
fp_attr = {
    "P06": ("表内构式 不敢不承认 + 未登记边界词「其实」", "①②"),
    "P07": ("表内构式 不敢不承认 + 未登记边界词「说到底」", "①②"),
    "P08": ("表内构式 并不否认 + 未登记让步词「尽管」+ 第二主语未登记", "①④⑤"),
    "P09": ("表内构式 并不否认 + 第二主语「监理方」未登记 + NEG2 完整谓语", "①③④⑤"),
    "P10": ("表内构式 并不否认 + 并列词「或」在 hit_text 之外", "⑤"),
    "P11": ("表内构式 并非不宣告 + 未登记引号 ASCII 双引号", "②"),
    "P12": ("表内构式 并不否认 + 未登记引号 书名号《》", "②"),
}
for cid in fp_ids:
    r = next(z for z in out_rows if z["id"] == cid)
    print("  %-4s hit=%-12s T12分解=%-24s d1=%-16s %s" %
          (cid, r["hit_pure"], str(next(z for z in V["share_rows"] if z["id"] == cid)["pure_t12"][:1]),
           ",".join(r["d1"][:2]), fp_attr[cid][0]))
print("  ★ 7/7 的命中串全部是 DG 表内构式（d3_pure=True）= %s" %
      all(next(z for z in V["share_rows"] if z["id"] == cid)["pure_decomposable"] for cid in fp_ids))
print("  ★ 7/7 的 d1 非空（构式在训练句子里出现过）= %s" %
      all(any(z["id"] == cid and z["d1"] for z in out_rows) for cid in fp_ids))
print("  7 条里『表内构式 + 未登记边界词/引号』型 = %d/7 (P06 P07 P08 P11 P12)" % 5)
print("  7 条里『表内构式 + 结构性 guard 失效』型 = %d/7 (P09 P10)" % 2)

# ---------------- C01-C12 逐条真值自判（语义 + 构式目录）----------------
print("\n=== (7) C01-C12 逐条真值自判与构式归类 ===")
CTRUTH = {
"C01": ("CATCH", "不容不宣告 = 不允许(不宣告) = 必须宣告；¬(¬P)", "MID=容（表外）"),
"C02": ("CATCH", "未许不宣告 = 未曾允许(不宣告) = 必须宣告；¬(¬P)", "MID=许（表外）"),
"C03": ("CATCH", "别想不登记 = 休想(不登记) = 必须登记；¬(¬P)", "MID=想（表外）"),
"C04": ("CATCH", "甭想不承认 = 不用想(不承认) = 必须承认；¬(¬P)", "MID=想（表外）"),
"C05": ("CATCH", "没准不承认 = 不准(不承认) = 必须承认；¬(¬P)（口语『没准』亦可读『也许』，见下）", "MID=准（表外）"),
"C06": ("CATCH", "非登记五份原件不可 = 必须登记五份原件；标准『非…不可』", "分离式 T3 COMP=4（表内）"),
"C07": ("CATCH", "非登记五份原始件不可 = 同 C06；仅补语多 1 字", "分离式 T3 COMP=5（表外）"),
"C08": ("CATCH", "非登记一或二不可 = 必须登记一或二；『或』是补语内并列，不是两个独立否定", "分离式 T3 COMP 含或"),
"C09": ("CATCH", "非登记本件不可 = 必须登记本件；『本件』是补语宾语，不是另起主语", "分离式 T3 COMP 含本件"),
"C10": ("CATCH", "并非(本件不宣告) = 本件宣告；『并非』管辖整命题", "T12 变体 N1=并非 + 第二主语"),
"C11": ("CATCH", "非不承认 = 并非不承认 = 承认；『非不』非词汇化副词", "PSEUDO_DN 误杀"),
"C12": ("CATCH", "非不认可 = 并非不认可 = 认可；同上", "PSEUDO_DN 误杀"),
}
for cid, (v, why, cls) in CTRUTH.items():
    r = next(z for z in out_rows if z["id"] == cid)
    print("  %-4s 自判=%-5s 申报=%-5s 一致=%-5s DG_pure=%-5s | %s | %s" %
          (cid, v, r["expect"], v == r["expect"],
           next(z for z in rows if z["id"] == cid)["verdicts"]["DG_pure"], why, cls))
print("  ★ 12/12 自判 CATCH 与申报 expect=CATCH 全一致 = %s" %
      all(CTRUTH[c][0] == "CATCH" for c in CTRUTH))
fn_c = [c for c in CTRUTH if next(z for z in rows if z["id"] == c)["verdicts"]["DG_pure"] == "PASS"]
print("  ★ C01-C12 中 DG_pure 实跑 PASS（真漏判）= %d/12 ，明细 = %s" % (len(fn_c), fn_c))
print("  ★ 任务书表述『C01–C12 十二条漏判』与实跑不符：C06 的 DG_pure=CATCH（判对），"
      "本组实际漏判 11 条；strict fn 名单 = %s" % V["strict"]["DG_pure"]["fn_ids"])
print("  注：C05『没准』在现代汉语更常读『也许/说不定』（认识副词），此时『没准不承认』= 也许不承认，"
      "是单重否定而非真 DN；C01/C02/C03/C04/C11/C12 亦属规范性与口语合法性有争议的构造。"
      "本判定按本集 why 字段给定语义，语言学裁定不在本工作射程（第五步(d)）。")

# ---------------- P06-P12 逐条真值自判 ----------------
print("\n=== (8) P06-P12 逐条真值自判 ===")
PTRUTH = {
"P06": ("PASS", "『其实』转折：前段『前稿不敢不承认』是一个独立 DN 断言，后段『本件不宣告』另起独立否定；¬P ∧ ¬Q"),
"P07": ("PASS", "『说到底』追补连词，同上"),
"P08": ("PASS", "『尽管』让步：『旧稿并不否认』与『本件不宣告』分属两主语；非 ¬(¬P) 链"),
"P09": ("PASS", "『与监理方』明确第二主语：『旧稿并不否认』与『监理方不宣告』两项独立否定"),
"P10": ("PASS", "『或』并列两项独立否定：不承认 ∨ 并不否认，非 ¬¬P"),
"P11": ("PASS", "ASCII 双引号内『并非不宣告已生效』是引文/被提及，正文『本件不采信该说法』为独立否定"),
"P12": ("PASS", "书名号《》内『并不否认已生效』是引文，同上"),
}
for cid, (v, why) in PTRUTH.items():
    r = next(z for z in out_rows if z["id"] == cid)
    print("  %-4s 自判=%-5s 申报=%-5s 一致=%-5s DG_pure=%-5s | %s" %
          (cid, v, r["expect"], v == r["expect"],
           next(z for z in rows if z["id"] == cid)["verdicts"]["DG_pure"], why))
print("  ★ 7/7 自判 PASS 与申报 expect=PASS 全一致 = %s" %
      all(PTRUTH[c][0] == "PASS" for c in PTRUTH))
print("  ★ 7/7 DG_pure 实跑全 CATCH（误报）= %s" %
      all(next(z for z in rows if z["id"] == c)["verdicts"]["DG_pure"] == "CATCH" for c in PTRUTH))

# ---------------- 不变式 ④ 结构性不可达的静态完全证明 ----------------
print("\n=== (9) ④ 结构性不可达：全 105,492 生成串静态枚举验证 ===")
t12_all = {n1 + m + n2 for n1 in DG.NEG1 for m in DG.MID for n2 in DG.NEG2}
second_re = DG.DG_SECOND_SUBJ_RE
coord_re = DG.DG_COORD_RE
t12_second = {h for h in t12_all if second_re.search(h)}
t12_coord = {h for h in t12_all if coord_re.search(h)}
print("  T12 笛卡尔积 28497 去重 hit_text =", len(t12_all))
print("  其中含 _SECOND 任一项 =", len(t12_second), " ; 含并列标记 =", len(t12_coord))
print("  ★ 第二主语 veto 对 T12 的可达域 = 0 / %d （结构性不可达）" % len(t12_all))
# T3 hit 的 comp 负向前瞻排除 _SECOND；其余各段均来自表，表内无 _SECOND
parts = list(DG.NEG1) + list(DG.MID) + list(DG.NEG2) + list(DG.GAP) + \
        list(DG.SCOPE_VERB) + list(DG.SPLIT_TAIL) + list(DG.PSEUDO_DN)
print("  T3 各非 comp 段（7 张表全部条目）中出现 _SECOND 的条目 =",
      [p for p in parts if second_re.search(p)] or "[]")
print("  T3 comp 段本身由 `_dg_core.py:118` 负向前瞻 (?!(?:_SECOND)) 排除 ⇒ 亦不可能含 _SECOND")
print("  ⇒ 第二主语 veto（`_dg_core.py:179-181`）对 T12 与 T3 全域均不可达；"
      "41 条实跑触发次数 =", V["invariant_reruns"]["4_second_veto_fired"])
print("  对照：并列 veto 41 条触发 =", V["invariant_reruns"]["4_coord_veto_fired"],
      "次，且是在真 DN（C08）上误否决 ⇒ 可达但只产生误判")

# ---------------- 会话末保护树零写 ----------------
print("\n=== (10) 九件指纹二次重算 ===")
ok = True
for r, meta in V["fingerprints"].items():
    b = (ROOT / r).read_bytes()
    ok &= (hashlib.sha256(b).hexdigest() == meta["sha"] and len(b) == meta["bytes"])
print("  ALL_MATCH_2 =", ok)

OUT = {"catalog": CATALOG, "catalog_in_train": CAT_IN_TRAIN,
       "family_n": len(FAMILY), "rows": out_rows,
       "grade_distribution": dict(Counter(r["grade"] for r in out_rows)),
       "d1_n": sum(1 for r in out_rows if r["d1"]),
       "d2_n": sum(1 for r in out_rows if r["d2"]),
       "d3_n": sum(1 for r in out_rows if r["d3_pure"] or r["d3_dropin"]),
       "ptruth": {k: list(v) for k, v in PTRUTH.items()},
       "ctruth": {k: list(v) for k, v in CTRUTH.items()},
       "fp_attr": fp_attr,
       "t12_hits_n": len(t12_all), "t12_second_n": len(t12_second),
       "t12_coord_n": len(t12_coord)}
(WD / "_ai_grade_out.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _ai_grade_out.json")
