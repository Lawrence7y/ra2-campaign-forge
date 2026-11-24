# -*- coding: utf-8 -*-
r"""_fd_e2.py — 判别实验 E2（+ 第一步 (b) 独立基线复现）。
零真机 / 零采样 / 零 hook；只 re + 静态文本 + AST 静态抽取 CASES；
只读保护目录（不 import 任何保护目录模块），所有改版模块都从写域 _fd_*.py 加载。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_e2.py
输出：_fd_e2_stdout.txt / _fd_e2_out.json（均在写域）
"""
import sys, json, hashlib, ast, re, importlib.util, pathlib
sys.dont_write_bytecode = True

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
SRC_G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
SRC_ADV = ROOT / "lead" / "dg_adversarial_20261109" / "_dga_adversarial.py"
SRC_JSON = ROOT / "lead" / "dg_adversarial_20261109" / "_dga_adversarial_out.json"

out_lines = []
def P(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    out_lines.append(s)


def load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size


# ================= 第一步 (a) 素材复核 =================
P("=== (1a) 素材指纹（编排方实跑基线 + 本会话独立重算）===")
orch = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md": ("d80b8b0e389da9c88121d648ac90331751586ff9c1710fce07880ee0f87d2d6b", 45189),
    "lead/fp_pattern_20261109/_fp_recompute_out.json": ("476be04d9b72c6f343a81906e71f70072992bf2ca949c5c0aa8cf6fc0d6c9fff", 17850),
    "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md": ("e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb", 42689),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md": ("94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4", 46334),
}
for rel, (h, n) in orch.items():
    p = ROOT / rel
    hh, nn = sha(p)
    P("  [orch] %-62s sha=%s bytes=%d MATCH=%s" % (rel, hh, nn, (hh == h and nn == n)))
for rel in ["lead/advset_indep_20261109/_dga_adversarial_out.json", "lead/gate_fp7_20261108/_dg_core.py"]:
    p = ROOT / rel
    P("  [orch MISSING-check] %-60s exists=%s" % (rel, p.exists()))

# CASES 原文：AST 静态抽取（不 exec 保护脚本）
tree = ast.parse(SRC_ADV.read_text(encoding="utf-8"), filename=str(SRC_ADV))
CASES = None
FORCED = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name) and t.id == "CASES":
                CASES = ast.literal_eval(node.value)
            if isinstance(t, ast.Name) and t.id == "FORCED":
                FORCED = ast.literal_eval(node.value)
P("\n=== (1a) 7 条 fp 原文 / 11 条 fn 原文 / 8 条正确负样本原文（AST 静态抽取，逐条）===")
d = json.loads(SRC_JSON.read_text(encoding="utf-8"))
jcases = {c["id"]: c for c in d["cases"]}
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
FP7 = ["P06", "P07", "P08", "P09", "P10", "P11", "P12"]
FN11 = ["C01", "C02", "C03", "C04", "C05", "C07", "C08", "C09", "C10", "C11", "C12"]
NEG8 = ["P01", "P02", "P03", "P04", "P05", "P13", "P14", "P15"]
NEG_CORRECT2 = ["P16", "P17"]
cmap = {c[0]: c for c in CASES}
text_match_all = True
for group, ids in [("fp7", FP7), ("fn11", FN11), ("neg8_correct", NEG8), ("neg_correct2_d1nonempty", NEG_CORRECT2)]:
    P("  --- %s ---" % group)
    for cid in ids:
        c = cmap[cid]
        j = jcases[cid]
        same_text = (c[2] == j["text"])
        same_exp = (c[3] == j["expect"])
        text_match_all &= same_text and same_exp
        P("  %-4s expect=%-5s text_match_json=%-5s expect_match_json=%-5s | %s" %
          (cid, c[3], same_text, same_exp, c[2]))
P("  [1a-verdict] 26 条 text+expect 与 _dga_adversarial_out.json 逐条全同 = %s" % text_match_all)

# ================= 第一步 (b) 独立基线复现 =================
P("\n=== (1b) 独立基线复现：DG_pure strict n=36 fp=7 fn=11（自写扫描，不读现成 JSON 分数）===")
DG0 = load("_fd_e2_orig", WD / "_fd_dg_core_orig.py")

def detect_pure(DG, text):
    """自写 DG_pure 判定：与上游 detect() 等价（dg_scan + TOKS），但独立实现。"""
    toks = [t for t in TOKS if t in text] or ["已生效"]
    problems, hits = DG.dg_scan(text, toks)
    return "CATCH" if problems else "PASS", (hits[0]["hit"] if hits else "")

def score(DG, cases, strict=True):
    fp, fn, amb = [], [], []
    verdict = {}
    for cid, shape, text, exp, why, attack in cases:
        e = exp if strict else FORCED.get(cid, exp)
        if e == "AMBIG":
            amb.append(cid)
            continue
        v, h = detect_pure(DG, text)
        verdict[cid] = {"v": v, "hit": h, "expect": e}
        if e == "PASS" and v == "CATCH":
            fp.append(cid)
        elif e == "CATCH" and v == "PASS":
            fn.append(cid)
    return {"n": len(cases) - len(amb), "amb": amb, "fp": fp, "fn": fn, "verdict": verdict}

S0 = score(DG0, CASES)
P("  [baseline] n=%d amb_excluded=%d fp=%d fn=%d" % (S0["n"], len(S0["amb"]), len(S0["fp"]), len(S0["fn"])))
P("  [baseline] fp_ids = %s" % S0["fp"])
P("  [baseline] fn_ids = %s" % S0["fn"])
jscore = d["scoring_strict"]["DG_pure"]
P("  [baseline] 与 _dga_adversarial_out.json:scoring_strict.DG_pure 对照：fp_ids 全同 = %s ; fn_ids 全同 = %s ; n 全同 = %s"
  % (S0["fp"] == jscore["fp_ids"], S0["fn"] == jscore["fn_ids"], S0["n"] == jscore["n_scored"]))

# ================= 第一步 (c) 护栏常量实际内容 =================
P("\n=== (1c) 护栏常量实际内容（直读原件 + 运行时 introspection）===")
lines = SRC_DG.read_text(encoding="utf-8").splitlines()
for ln in [85, 86, 88, 89, 90, 91, 92]:
    P("  _dg_core.py:%d | %s" % (ln, lines[ln - 1]))
P("  DG_BREAK_RE.pattern = %r" % DG0.DG_BREAK_RE.pattern)
P("  DG_QUOTE_RE.pattern = %r" % DG0.DG_QUOTE_RE.pattern)
P("  DG_SECOND_SUBJ_RE.pattern = %r" % DG0.DG_SECOND_SUBJ_RE.pattern)
P("  DG_COORD_RE.pattern = %r" % DG0.DG_COORD_RE.pattern)
P("  DG_BREAK_RE 的 10 个转折词 = ['但','但是','然而','不过','却','只是','反之','相反','另外','另']（源码 :89）")
P("  _BQ = r%r（:86） ; _BREAK = r%r（:85）" % (lines[86 - 1].split("=", 1)[1].strip(), lines[85 - 1].split("=", 1)[1].strip()))
P("  DG_QUOTE_RE 现有 4 类 = 「」/『』/“”/``（:92）")
P("  _SECOND 14 项 = 本笔|本件|本节|本回件|本候选|该笔|该件|此笔|台账|母本|本域|本轮|审阅回件|复核回件  + 第\\s*\\d+\\s*笔 正则项（:88）")
P("  DG_COORD_RE = re.compile(r'[/／]|、|或|以及|同时|并且|一是|二是|其一|其二')（:91）")

# ================= E2 消融 =================
P("\n=== (E2) 消融：全 41 条 × 各改版，逐条 fp/fn 进出 ===")
VARIANTS = [
    ("原版", "_fd_dg_core_orig.py"),
    ("(甲)只补数据", "_fd_dg_core_jia.py"),
    ("(甲4)14边界词+4类引号", "_fd_dg_core_jia4.py"),
    ("(甲B)另一批14词", "_fd_dg_core_jiaB.py"),
    ("(甲Q)甲+改_mask_quotes", "_fd_dg_core_jiaQ.py"),
    ("(甲QV)甲Q+veto查整窗", "_fd_dg_core_jiaQV.py"),
    ("(甲QVD)甲QV+补监理方/与", "_fd_dg_core_jiaQVD.py"),
    ("(甲QVN)甲Q+veto查N2后整窗", "_fd_dg_core_jiaQVN.py"),
    ("(乙_min)只删最小表项", "_fd_dg_core_yi_min.py"),
    ("(乙_full)删全部分解并集", "_fd_dg_core_yi_full.py"),
]
results = {}
for label, fn in VARIANTS:
    DG = load("_fd_e2_" + fn.replace(".py", ""), WD / fn)
    S = score(DG, CASES)
    results[label] = S
    fp_out = [x for x in S["fp"] if x not in S0["fp"]]
    fp_gone = [x for x in S0["fp"] if x not in S["fp"]]
    fn_new = [x for x in S["fn"] if x not in S0["fn"]]
    fn_gone = [x for x in S0["fn"] if x not in S["fn"]]
    P("  --- %s ---" % label)
    P("    fp=%d fn=%d | fp_ids=%s" % (len(S["fp"]), len(S["fn"]), S["fp"]))
    P("    fn_ids=%s" % S["fn"])
    P("    fp 消掉=%s ; fp 新增=%s ; fn 新增=%s ; fn 消掉=%s" % (fp_gone, fp_out, fn_new, fn_gone))
    # 8 条正确负样本 + P16/P17 是否退化
    neg_bad = [cid for cid in NEG8 + NEG_CORRECT2 if S["verdict"][cid]["v"] == "CATCH"]
    P("    8 正确负样本 + P16/P17 退化（变 CATCH）=%s" % neg_bad)
    # 真阳 CATCH 保住数（19 CATCH + 1 AMBIG forced CATCH 不计 strict）
    tp_kept = [cid for cid, shape, text, exp, why, attack in CASES
               if exp == "CATCH" and S["verdict"][cid]["v"] == "CATCH"]
    P("    expect=CATCH 判对条数 = %d/19 ; 逐条=%s" % (len(tp_kept), tp_kept))

# 三张主表：原版 / 甲 / 乙_full（+ 甲QV 作为「(甲) 改代码」上界）
P("\n=== (E2) 三张逐条进出表（原版 / 甲 / 乙_full）+ 甲QV 对照 ===")
for label in ["原版", "(甲)只补数据", "(乙_full)删全部分解并集", "(甲QV)甲Q+veto查整窗", "(甲QVD)甲QV+补监理方/与", "(甲QVN)甲Q+veto查N2后整窗"]:
    S = results[label]
    P("  ### %s  fp=%d fn=%d ###" % (label, len(S["fp"]), len(S["fn"])))
    for cid in FP7:
        P("    fp? %-4s %-9s -> %-5s hit=%s" % (cid, "orig=CATCH", S["verdict"][cid]["v"], S["verdict"][cid]["hit"]))
    for cid in FN11:
        P("    fn? %-4s %-9s -> %-5s hit=%s" % (cid, "orig=PASS", S["verdict"][cid]["v"], S["verdict"][cid]["hit"]))
    for cid in NEG8 + NEG_CORRECT2:
        P("    neg %-4s %-9s -> %-5s" % (cid, "orig=PASS", S["verdict"][cid]["v"]))

# P09/P10 逐改版诊断
P("\n=== (E2d) P09 / P10 特别核：逐改版 verdict + 命中/切断原因 ===")
for label, fn in VARIANTS:
    DG = load("_fd_e2d_" + fn.replace(".py", ""), WD / fn)
    rec = []
    for cid in ["P09", "P10"]:
        text = cmap[cid][2]
        toks = [t for t in TOKS if t in text] or ["已生效"]
        v, h = detect_pure(DG, text)
        # 取该 token 前的 dg_double_neg 原始 reason
        m0 = re.search(re.escape(toks[0]), text)
        r = DG.dg_double_neg(text[:m0.start()]) if m0 else {}
        rec.append("%s:%s(hit=%r,reason=%r)" % (cid, v, r.get("hit_text", ""), r.get("reason", "")[:44]))
    P("  %-28s %s" % (label, " | ".join(rec)))

# ================= 写盘 =================
out = {
    "orch_fingerprints": {rel: {"sha256": sha(ROOT / rel)[0], "bytes": sha(ROOT / rel)[1], "match": sha(ROOT / rel) == v}
                          for rel, v in orch.items()},
    "cases_ast": [{"id": c[0], "shape": c[1], "text": c[2], "expect": c[3]} for c in CASES],
    "id_groups": {"fp7": FP7, "fn11": FN11, "neg8_correct": NEG8, "neg_correct2": NEG_CORRECT2},
    "baseline_independent": {"n": S0["n"], "amb": S0["amb"], "fp_ids": S0["fp"], "fn_ids": S0["fn"],
                             "match_stored": {"fp": S0["fp"] == jscore["fp_ids"], "fn": S0["fn"] == jscore["fn_ids"]}},
    "guard_constants": {
        "DG_BREAK_RE.pattern": DG0.DG_BREAK_RE.pattern,
        "DG_QUOTE_RE.pattern": DG0.DG_QUOTE_RE.pattern,
        "DG_SECOND_SUBJ_RE.pattern": DG0.DG_SECOND_SUBJ_RE.pattern,
        "DG_COORD_RE.pattern": DG0.DG_COORD_RE.pattern,
    },
    "e2_results": {k: {"fp": v["fp"], "fn": v["fn"],
                       "fp_gone": [x for x in S0["fp"] if x not in v["fp"]],
                       "fp_new": [x for x in v["fp"] if x not in S0["fp"]],
                       "fn_new": [x for x in v["fn"] if x not in S0["fn"]],
                       "fn_gone": [x for x in S0["fn"] if x not in v["fn"]],
                       "neg10_degraded": [cid for cid in NEG8 + NEG_CORRECT2 if v["verdict"][cid]["v"] == "CATCH"],
                       "per_case": {cid: {"v": d0["v"], "hit": d0["hit"]} for cid, d0 in v["verdict"].items()}}
                   for k, v in results.items()},
}
(WD / "_fd_e2_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(WD / "_fd_e2_stdout.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print("\n[write] _fd_e2_stdout.txt lines =", len(out_lines))
