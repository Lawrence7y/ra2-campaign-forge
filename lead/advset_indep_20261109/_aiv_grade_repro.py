# -*- coding: utf-8 -*-
r"""_aiv_grade_repro.py — 逐条复判：按【被核对象 §2.1】目录口径精确重建 24/17，
并检验交付脚本 grade() 分支是否与 §2.1 定义一致。只 re/ast/hashlib，不 import 保护件。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/advset_indep_20261109/_aiv_grade_repro.py
"""
import sys, re, ast, json, types, hashlib
from pathlib import Path
from collections import Counter

sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "advset_indep_20261109"
DGD = ROOT / "lead" / "dneg_generative_20261109"
DGA = ROOT / "lead" / "dg_adversarial_20261109"


def lit(path):
    t = ast.parse(Path(path).read_text(encoding="utf-8"), filename=str(path))
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign):
            for g in n.targets:
                if isinstance(g, ast.Name):
                    try: out[g.id] = ast.literal_eval(n.value)
                    except Exception: pass
    return out


def mem(name, p):
    m = types.ModuleType(name)
    exec(compile(Path(p).read_text(encoding="utf-8"), str(p), "exec"), m.__dict__)
    return m


DG = mem("_aivg_dg", DGD / "_dg_core.py")
H5 = mem("_aivg_h5", ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py")
CASES = lit(DGA / "_dga_adversarial.py")["CASES"]

s34, s1, vp = lit(DGD / "_dg_step34.py"), lit(DGD / "_dg_step1.py"), lit(DGD / "_dgv_probe.py")
NEG_CHARS = set("不无未非没莫勿甭别岂")
catalog = set()
for g in s34["GAPS"] + s1["GAPS"]:
    catalog.add(g[0])
catalog |= set(DG.R12_TEN)
for s in s34["H5_EXTRA"] + s34["H5_SPLIT"]:
    if len(s) >= 2 and any(c in s for c in NEG_CHARS): catalog.add(s)
for s in H5.H5_DN_EXTRA.split("|") + H5.H5_R12_TEN.split("|"):
    if "[^" not in s and len(s) >= 2 and any(c in s for c in NEG_CHARS): catalog.add(s)
for p in DG.PSEUDO_DN: catalog.add(p)
CATALOG = sorted(catalog, key=lambda z: (-len(z), z))

# 训练句子：严格按 _ai_grade.py:65-76（带 id 的完整中文句子）
sentences = set()
for f in ("_dg_step34.py", "_dgv_probe.py", "_dgv_neg2.py", "_dg_step1.py"):
    for name, val in lit(DGD / f).items():
        if not isinstance(val, list): continue
        for item in val:
            if isinstance(item, (tuple, list)):
                for cell in item:
                    if isinstance(cell, str) and len(cell) >= 8 and re.search(r"[\u4e00-\u9fff]", cell):
                        sentences.add(cell)
            elif isinstance(item, str) and len(item) >= 8 and re.search(r"[\u4e00-\u9fff]", item):
                sentences.add(item)
CAT_IN_TRAIN = sorted([k for k in CATALOG if any(k in s for s in sentences)], key=lambda z: -len(z))

SECOND = ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔", "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"]
BREAK10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
COORD = ["或", "以及", "同时", "并且", "一是", "二是", "其一", "其二"]
FAMILY = sorted(set([w for w in DG.MID if w] + list(DG.PSEUDO_DN) + BREAK10 + COORD + SECOND +
                    [w for w in DG.NEG1 if len(w) >= 2] + [w for w in DG.NEG2 if len(w) >= 2] +
                    CATALOG + ["「」", "『』", "“”", "``"]), key=lambda z: -len(z))


def lev(a, b):
    if a == b: return 0
    if len(a) < len(b): a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def lcs(a, bset):
    best = 0
    for i in range(len(a)):
        for j in range(i + 1, len(a) + 1):
            frag = a[i:j]
            if len(frag) <= best: continue
            if any(frag in t for t in bset): best = len(frag)
    return best


T12 = {n1 + m + n2 for n1 in DG.NEG1 for m in DG.MID for n2 in DG.NEG2}
REPORT_STD = {
    "L0": "P06,P07,P08,P09,P10,P11,P12,P16,P17,C06,C08,C11,C12,C13,C14,C15,C16,C17,C18,C19,C20,A01,A02,A03".split(","),
    "L1": "P01,P02,P03,P04,P05,P13,P14,P15,C01,C02,C03,C04,C05,C07,C09,C10,A04".split(","),
}

print("=== (0) 目录/族表规模（复现 _ai_grade_stdout.txt:2,5,8）===")
print("  CATALOG = %d ; CAT_IN_TRAIN = %d ; FAMILY = %d ; 训练句子 = %d" %
      (len(CATALOG), len(CAT_IN_TRAIN), len(FAMILY), len(sentences)))

# d3 用【被核对象】_ai_verify_out.json:share_rows（只读 JSON 逐条提取，不采信 stdout 结论）
V = json.loads((WD / "_ai_verify_out.json").read_text(encoding="utf-8"))
share = {z["id"]: z for z in V["share_rows"]}

print("\n=== (1) 41 条逐条复判（按 §2.1 定义：L0→L1→L2→L3 逐级必要条件）===")
out = {}
for cid, shape, text, exp, why, attack in CASES:
    sr = share[cid]
    d1 = [k for k in CAT_IN_TRAIN if k in text]
    d2 = [w for w in FAMILY if w in text]
    d3 = bool(sr["pure_decomposable"]) or bool(sr["dropin_decomposable"])
    L = lcs(text, sentences)
    E = min((lev(text, t) for t in sentences), default=10 ** 9)
    # §2.1 定义：L1 需 ¬∃c∈C_train ∧ hit 不可拼；L2 需 L1 ∧ ¬∃f∈F ∧ LCS<4 ∧ edit>5；L3 需 L2 ∧ 盲化
    if d1 or d3:
        g = "L0"
    elif d2:
        g = "L1"
    elif L >= 4 or E <= 5:
        g = "L1"
    else:
        g = "L2"  # 盲化另判；本集无一到此
    out[cid] = g
    print("  %-4s %-4s d1=%-5s d2=%-5s d3=%-5s LCS=%-2d edit=%-2d | %s" %
          (cid, g, bool(d1), bool(d2), d3, L, E, text[:22]))
dist = dict(Counter(out.values()))
print("  ★ 我按被核对象口径逐条复判分布 =", json.dumps(dist, ensure_ascii=False))
print("  ★ 与 _AI_ADVSET_INDEPENDENCE.md:178-181 逐条一致 =",
      all(out[c] == lv for lv, ids in REPORT_STD.items() for c in ids) and
      set(out) == set(REPORT_STD["L0"] + REPORT_STD["L1"]))
print("  ★ L2 = %d ; L3 = %d" % (sum(1 for g in out.values() if g == "L2"),
                                  sum(1 for g in out.values() if g == "L3")))

print("\n=== (2) 交付脚本 grade() 与 §2.1 定义的一致性检验 ===")
def their_grade(d1, d2, d3p, d3d, L, E):
    if E == 0: return "belowL0"
    if d1 or d3p or d3d: return "L0"
    if d2: return "L1"
    if L >= 4 or E <= 5: return "L2"
    return "L3"


cases = [
    ("近重复：LCS=8 edit=2 无族词", [], [], False, False, 8, 2, "L1"),
    ("远距：LCS=2 edit=9 无族词", [], [], False, False, 2, 9, "L2"),
    ("远距+未盲化(attack=③)：LCS=2 edit=9 无族词", [], [], False, False, 2, 9, "L2"),
]
for name, d1, d2, d3p, d3d, L, E, expect in cases:
    got = their_grade(d1, d2, d3p, d3d, L, E)
    print("  %-46s 交付脚本=%-4s 定义应为=%-4s 一致=%s" %
          (name, got, expect, got == expect))
print("  ★ 结论：本集 d2 非空 41/41 ⇒ :138-139 两分支从未进入，故 24/17 与 L2=L3=0 不受影响；"
      "但机检谓词本身与 §2.1 定义相反（近重复被判 L2、远距被判 L3、L3 不查盲化）。")

print("\n=== (3) 只给分布不给逐条？交付件实文核查 ===")
for fn in ("_ai_grade_stdout.txt", "_ai_verify_stdout.txt"):
    lines = (WD / fn).read_text(encoding="utf-8").splitlines()
    ids = [ln.strip().split()[0] for ln in lines
           if re.match(r"^\s+(P|C|A)\d{2}\s", ln) and ("grade=" in ln or "d1=" in ln)]
    uniq = sorted(set(ids))
    print("  %-24s 含逐条分级行 = %d ; 唯一 id = %d ; 覆盖 41 条 = %s" %
          (fn, len(ids), len(uniq), len(uniq) == 41))
md = (WD / "_AI_ADVSET_INDEPENDENCE.md").read_text(encoding="utf-8")
print("  主报告 :178-181 明列 L0/L1/L2/L3 各行 ids = %s" %
      ("L0 ids" in md and "L1 ids" in md and "L2 | **0**" in md))
print("  ★ 判定：撰写人确实逐条判了（两脚本各 41 行 + 报告 4 行 ids），不是只给分布。")

print("\n=== (4) 指纹收尾 ===")
b = (WD / "_AI_ADVSET_INDEPENDENCE.md").read_bytes()
print("  被核对象 SHA256 = %s，字节数 = %d" % (hashlib.sha256(b).hexdigest(), len(b)))
