# -*- coding: utf-8 -*-
"""_gv_pred_check.py — 复核员独立谓词复核台（ask ①②③④）。
A 四谓词 × 四真实件：期望 problems 全 0（消误报）。
B 绑定行回验独立重算（不走 R11，自己 hashlib）：四真实件引用路径现盘哈希/字节比对。
C 复核员自建真违规样本 GV-A..K（不复用作者 TV）：期望逐个 FAIL；单重否定对照不拦。
D 奇偶计数反例：真实件 CANDIDATE 与 TV3 上实跑奇偶法，对照 R10/R12。
E 补丁代码块 ≡ 模块：静态归一化逐行包含性比对（无 exec）。
"""
import hashlib, pathlib, re, sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead/gate_fp7_20261108"
sys.path.insert(0, str(WD))
import _g7_predicates as G  # 被核对象本体

FILES = [
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md",
]
AT = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
R9T = {FILES[0]: ["APPROVE_SCOPE"], FILES[1]: ["APPROVE_SCOPE"],
       FILES[2]: ["复核"], FILES[3]: ["复核"]}
fails = []

def check(sec, label, got, want):
    ok = got == want
    if not ok:
        fails.append((sec, label, got, want))
    print(("PASS" if ok else "FAIL") + " [" + sec + "] " + label + "  got=" + repr(got)
          + ("" if ok else "  want=" + repr(want)))

# ---------- A 四谓词 × 四真实件 ----------
print("== A 四谓词 × 四真实件（期望 problems 全 0）==")
texts = {}
for rel in FILES:
    p = ROOT / rel
    t = p.read_text(encoding="utf-8", errors="replace")
    texts[rel] = t
    r9p, r9w = G.r9_check(t, R9T[rel])
    r10p, r10w, _ = G.r10_scan(t, AT)
    r12p, _ = G.r12_scan(t, AT)
    r11p, r11w, r11b = G.r11_scan(t, p.parent, root=ROOT)
    check("A", rel.split("/")[-1] + " R9", r9p, [])
    check("A", rel.split("/")[-1] + " R10", r10p, [])
    check("A", rel.split("/")[-1] + " R12", r12p, [])
    check("A", rel.split("/")[-1] + " R11", r11p, [])
    print("      warn R10=%d R11=%d  bindings=%s" % (len(r10w), len(r11w),
          [(b["path"] and b["path"][-40:], b["match"]) for b in r11b]))

# ---------- B 绑定回验独立重算 ----------
print("== B 绑定行回验独立重算（自算 hashlib，不经 R11）==")
CASES = [
    (FILES[0], "lead/n4_yi_final_20261108/_cs_semantic_review_GLM_20261108.md", "ee27b4ca"),
    (FILES[1], "_lv_subject_reply.txt", "6888379a"),
    (FILES[3], "_review_reply_transcript.json", "91d1317f"),
    (FILES[3], "_verify_reply.json", "1fe6b1b6"),
]
for rel, path, prefix in CASES:
    doc_dir = (ROOT / rel).parent
    hit = None
    for base in (doc_dir, ROOT):
        c = base / path
        if c.is_file():
            hit = c
            tag = "doc_dir" if base == doc_dir else "root"
            break
    if hit is None:
        check("B", rel.split("/")[-1] + " → " + path[-38:], "not-on-disk", "FOUND")
        continue
    b = hit.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    ok = h.startswith(prefix)
    check("B", rel.split("/")[-1] + " → " + path[-38:] + "(" + tag + ") 前缀符哈希", ok, True)
    print("      full=%s bytes=%d" % (h, len(b)))
obs = texts[FILES[2]].splitlines()[365]
check("B", "OBS:366 行内无反引号路径（R11 仅警告）", "`" in obs, False)

# ---------- C 自建真违规样本（复核员原创，不复用作者 TV）----------
print("== C 自建真违规样本逐个 FAIL + 单重否定对照不拦 ==")
GVS = [
    ("GV-A 自指正面断言(特此宣告)", "本件特此宣告已生效。", "R10"),
    ("GV-B 正面断言已入账", "本候选已入账。", "R10"),
    ("GV-C 正面断言放行", "本回件放行 N-5。", "R10"),
    ("GV-D 双重否定(不得不)", "本件不得不宣告已生效。", "R12"),
    ("GV-E 双重否定(并非不)", "并非不宣告已生效。", "R12"),
    ("GV-F 双重否定(不能不)", "谁都不能不承认已生效。", "R12"),
    ("GV-J 对照:单重否定", "本件不宣告已生效。", None),
]
for name, sample, expect_rule in GVS:
    r10p, r10w, _ = G.r10_scan(sample, AT)
    r12p, _ = G.r12_scan(sample, AT)
    if expect_rule == "R10":
        check("C", name + " → R10 fail", len(r10p) >= 1, True)
    elif expect_rule == "R12":
        check("C", name + " → R12 fail", len(r12p) >= 1, True)
        check("C", name + " → R10 不误报(分工)", r10p, [])
    else:
        check("C", name + " → R10 豁免且 R12 不拦", (r10p, r12p), ([], []))
# GV-G 伪造绑定（指向真盘文件 _g7_predicates.py，哈希/字节伪造）
gv_g = "被核对象（本写域 `_g7_predicates.py`）SHA256 = `" + "1" * 64 + "`，字节数 = 999。"
p_g, w_g, b_g = G.r11_scan(gv_g, WD, root=ROOT)
check("C", "GV-G 伪造绑定(真盘+错哈希) → R11 失配", len([x for x in p_g if "失配" in x]) >= 1, True)
# GV-H 绑定指向不在盘
gv_h = "被核对象（`_gv_no_such_object_xyz.md`）SHA256 = `" + "2" * 64 + "`，字节数 = 12。"
p_h, _, _ = G.r11_scan(gv_h, WD, root=ROOT)
check("C", "GV-H 指向不在盘 → R11 不在盘", len([x for x in p_h if "不在盘" in x]) >= 1, True)
# GV-I 缺要素（raw+normalized 双缺）
gv_i = "# 回件\n\n范围签署审阅完成，签署主体/时点/条件齐备。"
check("C", "GV-I 真缺要素 → R9 fail", G.r9_check(gv_i, ["APPROVE_SCOPE"])[0] != [], True)
# GV-K 包裹/拆断形态在场（R9 不误报）
gv_k = "签署要件：`APPROVE_SCOPE` 由签发人签署（本件不代签）。"
check("C", "GV-K 反引号包裹 → R9 在场", G.r9_check(gv_k, ["APPROVE_SCOPE"])[0], [])
gv_k2 = "要件：APPROVE_\nSCOPE（换行拆断）。"
check("C", "GV-K2 拆断形态 → R9 在场", G.r9_check(gv_k2, ["APPROVE_SCOPE"])[0], [])
# GV-L 残余探针：分离型双重否定肯定式（作者 §6.2 自报未覆盖）
gv_l = "本件并非漏看，亦非不宣告已生效。"
r10pL, _, _ = G.r10_scan(gv_l, AT)
r12pL, _ = G.r12_scan(gv_l, AT)
print("      GV-L 分离型『非…不宣告』：R10 problems=%d R12 problems=%d（全 0=残余漏检实证）"
      % (len(r10pL), len(r12pL)))

# ---------- D 奇偶计数反例 ----------
print("== D 奇偶计数法反例（真实件 + TV3 实跑）==")
NEG = re.compile(r"(不|无|未|非|禁|勿|否决|排除|不宣告|不得)")
def parity_problems(text, toks):
    """奇偶法：窗内否定词奇数=否定语境豁免，偶数=判违规。"""
    probs = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            pre = text[max(0, m.start() - 24):m.start()]
            if len(NEG.findall(pre)) % 2 == 0:
                probs.append(tok)
    return probs
par_c = parity_problems(texts[FILES[0]], AT)
r10p_c, _, _ = G.r10_scan(texts[FILES[0]], AT)
print("      CANDIDATE: 奇偶法判违规 %d 处 %s；R10 判违规 %d 处" % (len(par_c), par_c, len(r10p_c)))
check("D", "奇偶法在真实件 CANDIDATE 制造新误报(>0)", len(par_c) > 0, True)
check("D", "R10/R12 同件零误报", (r10p_c, G.r12_scan(texts[FILES[0]], AT)[0]), ([], []))
t3 = (WD / "_g7_tv3_double_negation.md").read_text(encoding="utf-8")
par_t3 = parity_problems(t3, AT)
r12p_t3, _ = G.r12_scan(t3, AT)
print("      TV3: 奇偶法判违规 %d 处（漏掉双重否定）；R12 拦 %d 处" % (len(par_t3), len(r12p_t3)))
check("D", "奇偶法对 TV3 双重否定全豁免(漏判)", len(par_t3), 0)
check("D", "R12 对 TV3 拦下 ≥2", len(r12p_t3) >= 2, True)

# ---------- E 补丁代码块 ≡ 模块（静态归一化包含性比对）----------
print("== E 补丁代码块与模块静态一致性 ==")
patch = (WD / "_g7_patch.md").read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)```", patch, re.S)
print("      patch 内 python 代码块数 = %d" % len(blocks))
def norm_lines(code):
    out = []
    for ln in code.splitlines():
        ln = re.sub(r"#.*$", "", ln)          # 去行尾注释
        ln = re.sub(r"\s+", " ", ln).strip()  # 归一化空白
        if ln:
            out.append(ln)
    return out
mod = norm_lines((WD / "_g7_predicates.py").read_text(encoding="utf-8"))
all_ok = True
for i, b in enumerate(blocks):
    pl = norm_lines(b)
    missing = [ln for ln in pl if ln not in mod]
    ok = not missing
    all_ok = all_ok and ok
    print("      block%d: %d 行归一化语句，%s（未匹配 %d）"
          % (i, len(pl), "全部逐行含于 _g7_predicates.py" if ok else "有出入", len(missing)))
    for ln in missing:
        print("        MISS: " + ln[:110])
check("E", "三代码块归一化后逐行含于谓词模块", all_ok, True)

print()
print("==== _gv_pred_check verdict: FAIL=%d ====" % len(fails))
for f in fails:
    print("FAILED:", f)
