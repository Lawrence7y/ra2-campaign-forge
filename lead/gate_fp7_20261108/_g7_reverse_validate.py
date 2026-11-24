# -*- coding: utf-8 -*-
r"""_g7_reverse_validate.py — R9/R10/R11/R12 反向验证总控（只读既有件；唯一写域内自建样本）。
S1 正向消误报：四份真实交付件 × 四谓词，期望 problems=0；
S2 朴素门禁 FP 复现：既有 858e5e0b 门禁正则 + 编排方 bind_naive + 包裹字面要素，
   期望在真实件上复现第 5/8 类误报（对照组）；
S3 真违规样本：期望逐个 FAIL（不漏判）；
S4 双重否定对照：编排方式否定回看会把 TV3 判成「否定语境」（漏判），R12 判违规；
S5 bind_any 对照：全域 SHA256=hex 会让 TV4 蒙混过关，R11 判违规；
S6 第 5 类 FP 复现与消除：拆断/包裹形态，naive 漏判、R9 命中；
S7 保护件零漂移核对（9 件指纹 vs 编排方清单）。
"""
import hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead/gate_fp7_20261108"
sys.path.insert(0, str(WD))
from _g7_predicates import (naive_gate, NAIVE_BIND, r9_check, r9_element_present,
                            r10_scan, r12_scan, r11_scan, NEG_RE, NEG_WINDOW)

FILES = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]
ASSERT_TOKENS = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
ELEM_TOKENS = ["APPROVE_SCOPE"]
REAL_858E5E0B_BIND = re.compile(r"被核对象 SHA256\s*=\s*`?([0-9a-fA-F]{64})`?")
ORCH_BIND_NAIVE = re.compile(r"被核对象 SHA256\s*=\s*[0-9a-fA-F]{64}")
ORCH_BIND_RELAXED = re.compile(r"被核对象[^。\n]{0,160}?SHA256\s*=\s*`?[0-9a-fA-F]{64}")
ORCH_BIND_ANY = re.compile(r"SHA256\s*=\s*`?[0-9a-fA-F]{64}")
CORNER_LIT = "「APPROVE_SCOPE」"

def sha(p):
    b = pathlib.Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)

def tv(name):
    return WD / name

def load(name):
    return tv(name).read_text(encoding="utf-8")

results, ran = [], 0

def expect(sec, label, got, want):
    ok = got == want
    results.append((sec, label, ok, got, want))
    print(("PASS" if ok else "FAIL") + "  [" + sec + "] " + label + "  got=" + repr(got)
          + ("  want=" + repr(want) if not ok else ""))
    return ok

# ---------- S1 正向：四真实件 × R9/R10/R12/R11 ----------
print("== S1 正向消误报（四真实件，期望全部 problems=0）==")
# R9 要素词表取决于各门禁 ask：APPROVE_SCOPE 属 bexec_n4/n4_yi/ledger 族门禁词表，
# 对 OBSERVATION/C97 不适用——这两件改用件内确在场的控制词演示 R9 与 naive 等价。
R9_TOKENS = {
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ELEM_TOKENS,
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ELEM_TOKENS,
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": ["复核"],
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md": ["复核"],
}
for rel in FILES:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8", errors="replace")
    r9p, r9w = r9_check(t, R9_TOKENS[rel])
    r10p, r10w, r10h = r10_scan(t, ASSERT_TOKENS)
    r12p, r12h = r12_scan(t, ASSERT_TOKENS)
    r11p, r11w, r11b = r11_scan(t, p.parent, root=ROOT)
    expect("S1", rel.split("/")[-1] + " R9(" + ",".join(R9_TOKENS[rel]) + ")", r9p, [])
    expect("S1", rel.split("/")[-1] + " R10", r10p, [])
    expect("S1", rel.split("/")[-1] + " R12", r12p, [])
    expect("S1", rel.split("/")[-1] + " R11", r11p, [])
    print("    detail %s: R10 hits=%s | R11 bindings=%s warn=%d R10warn=%d"
          % (rel.split("/")[-1], json.dumps(r10h, ensure_ascii=False),
             json.dumps([{k: b[k] for k in ("path", "match")} for b in r11b], ensure_ascii=False),
             len(r11w), len(r10w)))

# ---------- S2 朴素门禁 FP 复现（对照组）----------
print("== S2 朴素门禁在真实件上复现第 5/8 类误报（期望 problems 非空）==")
for rel in ["lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
            "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"]:
    t = (ROOT / rel).read_text(encoding="utf-8")
    fp858 = naive_gate(t, [], bind_re=REAL_858E5E0B_BIND)
    fp_orch = naive_gate(t, [], bind_re=ORCH_BIND_NAIVE)
    print("    %s" % rel.split("/")[-1])
    print("      既有858e5e0b正则: %s" % fp858)
    print("      编排方bind_naive : %s" % fp_orch)
    expect("S2", rel.split("/")[-1] + " 858e5e0b正则复现缺绑定行", bool(fp858), True)
    expect("S2", rel.split("/")[-1] + " bind_naive复现缺绑定行", bool(fp_orch), True)
t_c = (ROOT / FILES[0]).read_text(encoding="utf-8")
fp5 = naive_gate(t_c, [CORNER_LIT])
print("    第5类：CANDIDATE 用包裹字面量「APPROVE_SCOPE」当要素 → %s" % fp5)
expect("S2", "CANDIDATE 包裹字面量复现缺要素", bool(fp5), True)

# ---------- S3 真违规样本（期望全部 FAIL）----------
print("== S3 真违规样本逐个 FAIL ==")
t1 = load("_g7_tv1_missing_element.md")
expect("S3", "TV1 缺要素 → R9 fail", r9_check(t1, ELEM_TOKENS)[0] != [], True)
t2 = load("_g7_tv2_overreach_positive.md")
p2, _, _ = r10_scan(t2, ASSERT_TOKENS)
expect("S3", "TV2 正面越权断言 ×5 → R10 fail", len(p2), 5)
t5 = load("_g7_tv5_forged_binding.md")
p5, _, _ = r11_scan(t5, WD, root=ROOT)
expect("S3", "TV5 伪造绑定（hex≠现盘）→ R11 fail", len([x for x in p5 if "失配" in x]) >= 1, True)
t6 = load("_g7_tv6_binding_missing_obj.md")
p6, _, _ = r11_scan(t6, WD, root=ROOT)
expect("S3", "TV6 绑定指向不在盘 → R11 fail", len([x for x in p6 if "不在盘" in x]) >= 1, True)
t4 = load("_g7_tv4_no_binding.md")
p4, _, _ = r11_scan(t4, WD, root=ROOT)
expect("S3", "TV4 无绑定行（仅指纹引证）→ R11 fail", any("缺 SHA256 绑定行" in x for x in p4), True)

# ---------- S4 双重否定对照 ----------
print("== S4 双重否定：编排方式否定回看会漏判，R12 拦下 ==")
t3 = load("_g7_tv3_double_negation.md")
orch_negated = sum(1 for m in re.finditer("已生效", t3)
                   if NEG_RE.search(t3[max(0, m.start() - NEG_WINDOW):m.start()]))
r10p3, _, _ = r10_scan(t3, ASSERT_TOKENS)
r12p3, _ = r12_scan(t3, ASSERT_TOKENS)
print("    TV3 编排式否定回看判定为「否定语境」的已生效命中 = %d / %d（漏判对照：三处全豁）"
      % (orch_negated, len(re.findall("已生效", t3))))
expect("S4", "TV3 编排式回看全部豁免（复现漏判）", orch_negated, 3)
expect("S4", "TV3 R10 不报（分工：双重否定交 R12）", len(r10p3), 0)
expect("S4", "TV3 R12 拦下双重否定 ×2（单重否定对照不拦）", len(r12p3), 2)
print("    TV2 对照：编排式回看会把正面断言「已追加至台账」前的「无需再登记」之「无」")
print("    误当否定语境（跨句污染）——R10 子句边界修正后仍判违规。")
orch_tv2 = [tk for tk in ASSERT_TOKENS
            for m in re.finditer(re.escape(tk), t2)
            if NEG_RE.search(t2[max(0, m.start() - NEG_WINDOW):m.start()])]
expect("S4", "TV2 编排式回看误豁免 ≥1（复现跨句污染漏判）", len(orch_tv2) >= 1, True)

# ---------- S5 bind_any 对照 ----------
print("== S5 bind_any 对照：全域 SHA256=hex 会放走 TV4，R11 不会 ==")
ba = len(ORCH_BIND_ANY.findall(t4))
expect("S5", "TV4 bind_any 命中 ≥1（若只查全域会 PASS）", ba >= 1, True)
expect("S5", "TV4 R11 仍 FAIL", any("缺 SHA256 绑定行" in x for x in p4), True)

# ---------- S6 第 5 类 FP 复现与消除 ----------
print("== S6 第 5 类：拆断/包裹形态 naive 漏判、R9 命中 ==")
t7 = load("_g7_tv7_split_token.md")
naive_miss = "APPROVE_SCOPE" not in t7
r9p7, r9w7 = r9_check(t7, ELEM_TOKENS)
expect("S6", "TV7 拆断形态 naive 裸字面漏判（缺要素 FP）", naive_miss, True)
expect("S6", "TV7 R9 判要素在场", r9p7, [])
t7b = load("_g7_tv7b_wrapper_only.md")
corner_gate_miss = CORNER_LIT not in t7b  # 门禁字面量带全角引号 → 漏判反引号形态
expect("S6", "TV7b 包裹字面门禁漏判反引号形态（缺要素 FP）", corner_gate_miss, True)
r9p7b, _ = r9_check(t7b, ELEM_TOKENS)
expect("S6", "TV7b R9 判要素在场", r9p7b, [])
# 包裹字面门禁对真实件（第 5 类的另一形态）
present_c, layer_c = r9_element_present(t_c, "APPROVE_SCOPE")
expect("S6", "CANDIDATE R9 要素在场（raw 层）", (present_c, layer_c), (True, "raw"))
print("    （对照事实：裸子串门禁不会漏反引号/全角包裹形态——包裹符不与 token 相交；")
print("      实测 CANDIDATE 裸写 2 处、反引号 3 处，LEDGER 裸写 1 处、反引号 5 处，")
print("      故第 5 类漏判只发生在门禁字面量带包裹符或要素被拆断两种形态。）")

# ---------- S7 保护件零漂移 ----------
print("== S7 保护件指纹核对（编排方清单 9 件）==")
EXPECT_FP = {
    "lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt": ("543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe", 28128),
    "lead/gate_template_20261108/GATE_FALSE_POSITIVES.md": ("2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244", 25841),
    "lead/gate_validate_20261108/GATE_TEMPLATE_REGRESSION.md": ("c9093cab4f708d3f2bfd721095e9d8458818dd9d36019d996fd952b24e1a5a19", 31507),
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": ("1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b", 23129),
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": ("724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e", 45719),
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": ("c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351),
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md": ("6d88fc9241e31e0d6ed7af4988ab712c8e0f4e4caa9d3d92e4f736bf23f46395", 21690),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
for rel, (h, n) in sorted(EXPECT_FP.items()):
    g = sha(ROOT / rel)
    expect("S7", rel.split("/")[-1] + " 未改动", g, (h, n))

bad = [r for r in results if not r[2]]
print("\n==== verdict: total=%d pass=%d fail=%d ====" % (len(results), len(results) - len(bad), len(bad)))
for r in bad:
    print("FAILED: [%s] %s got=%s want=%s" % (r[0], r[1], r[3], r[4]))
