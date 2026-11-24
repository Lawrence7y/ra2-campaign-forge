# -*- coding: utf-8 -*-
# _fdv_run1.py — 复核员独立重跑（不复用执行员任何改版件/输出件）：
#   (A) AST 只读抽取 CASES/FORCED；(B) 编排方素材 26 条逐条核对；
#   (C) 守卫常量核对；(D) 我的 detect + 基线 strict 对账（vs 编排方 _dga_adversarial_out.json）；
#   (E) E2 全臂（base/甲/纯改代码/甲c/甲c无豁免/甲4引号/乙/乙2/乙3/灾难/甲+并列词/甲+监理方进_SECOND）
#       + R12_TEN 锚 + DG_dropin 交付形态 + 隐藏代价探针；
#   (F) 我的最小实现逐 fp 根因解剖（P06..P12）。
# 零真机；只读保护件；写域内 _fdv_* 输出；dont_write_bytecode。
import sys, os, json, re, ast, importlib.util
sys.dont_write_bytecode = True

ROOT = r"D:/Project/ra2-campaign-forge"
WD = ROOT + r"/lead/fp_discriminate_20261109"
SB = WD + r"/_fdv_sandbox"
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
out = {}

def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

DG0 = load_mod("_fdv_dg_base", SB + "/_fdv_dg_core_base.py")
G70 = load_mod("_fdv_g7_base", SB + "/_fdv_g7_base.py")

# ================= (A) AST 抽取 =================
src = open(ROOT + "/lead/dg_adversarial_20261109/_dga_adversarial.py", encoding="utf-8").read()
tree = ast.parse(src)
CASES = FORCED = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if getattr(t, "id", None) == "CASES":
                CASES = ast.literal_eval(node.value)
            if getattr(t, "id", None) == "FORCED":
                FORCED = ast.literal_eval(node.value)
assert isinstance(CASES, list) and len(CASES) == 41, "CASES 抽取异常: %r" % type(CASES)
assert isinstance(FORCED, dict) and len(FORCED) == 5
CASES = [dict(id=c[0], shape=c[1], text=c[2], expect=c[3]) for c in CASES]
BYID = {c["id"]: c for c in CASES}
print("[A] CASES AST 抽取 = %d 条（P17+C20+A4）；FORCED = %s" % (len(CASES), FORCED))
out["cases_n"] = len(CASES)

def toks_of(text):
    return [t for t in TOKS if t in text] or ["已生效"]

# ================= (B) 编排方素材逐条核对 =================
MATERIAL = {
    # fp（expect=PASS, tokens=["已生效"]）
    "P06": ("PASS", "前稿不敢不承认其实本件不宣告已生效"),
    "P07": ("PASS", "前稿不敢不承认说到底本件不宣告已生效"),
    "P08": ("PASS", "旧稿并不否认尽管本件不宣告已生效"),
    "P09": ("PASS", "旧稿并不否认与监理方不宣告已生效"),
    "P10": ("PASS", "本件不承认或并不否认已生效"),
    "P11": ("PASS", '"并非不宣告已生效"只是引文，本件不采信该说法'),
    "P12": ("PASS", "《并不否认已生效》只是引文，本件不采信该说法"),
    # fn（expect=CATCH）
    "C01": ("CATCH", "不容不宣告本件已生效"),
    "C02": ("CATCH", "未许不宣告本件已生效"),
    "C03": ("CATCH", "别想不登记本件已入账"),
    "C04": ("CATCH", "甭想不承认本件已生效"),
    "C05": ("CATCH", "没准不承认本件已生效"),
    "C07": ("CATCH", "非登记五份原始件不可才算本件已生效"),
    "C08": ("CATCH", "非登记一或二不可才算本件已生效"),
    "C09": ("CATCH", "非登记本件不可才算本件已生效"),
    "C10": ("CATCH", "并非本件不宣告已生效"),
    "C11": ("CATCH", "非不承认本件已生效"),
    "C12": ("CATCH", "非不认可本件已生效"),
    # neg_ok（expect=PASS）
    "P01": ("PASS", "旧稿不承认，本件不宣告已生效"),
    "P02": ("PASS", "旧稿未登记、本件亦未宣告已生效"),
    "P03": ("PASS", "无越权断言，也不出现放行 N-5 类措辞，本件不采信已生效"),
    "P04": ("PASS", "前段不采信母本后段不宣告本件已生效"),
    "P05": ("PASS", "不核不录，本件不采信已生效"),
    "P13": ("PASS", "既不宣告旧稿已入账，也不宣告本件已生效"),
    "P14": ("PASS", "不予登记亦不宣告本件已生效"),
    "P15": ("PASS", "旧稿不承认，但本件也不宣告已生效"),
}
mat_rows = []
for cid, (exp, text) in MATERIAL.items():
    ok = BYID[cid]["text"] == text and BYID[cid]["expect"] == exp
    tok_ok = toks_of(text) == ["已生效"]  # 素材 7 条 fp 标注 tokens=["已生效"]
    mat_rows.append({"id": cid, "identical": ok, "tok_consistent": tok_ok})
n_ok = sum(1 for r in mat_rows if r["identical"])
print("[B] 素材逐条 identical = %d/%d（%s）" % (n_ok, len(MATERIAL),
      "ALL-OK" if n_ok == 26 else [r["id"] for r in mat_rows if not r["identical"]]))
out["material_check"] = {"n": len(MATERIAL), "identical": n_ok, "rows": mat_rows}

# ================= (C) 守卫常量核对 =================
gc = {
    "NEG1": len(set(DG0.NEG1)), "MID": len(set(DG0.MID)), "NEG2": len(set(DG0.NEG2)),
    "PSEUDO_DN": len(set(DG0.PSEUDO_DN)), "GAP": len(set(DG0.GAP)),
    "SCOPE_VERB": len(set(DG0.SCOPE_VERB)), "SPLIT_TAIL": len(set(DG0.SPLIT_TAIL)),
    "NEG2_完整否定谓语5": [w for w in ("否认", "不承认", "不认为", "不宣告", "不出现") if w in set(DG0.NEG2)],
    "敢_in_MID": "敢" in set(DG0.MID),
    "DG_BREAK_RE_words": ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"],
    "或_in_BREAK": bool(DG0.DG_BREAK_RE.search("或")),
    "与_in_BREAK": bool(DG0.DG_BREAK_RE.search("与")),
    "监理方_in_SECOND": bool(DG0.DG_SECOND_SUBJ_RE.search("监理方")),
    "SECOND_字面14": ["本笔", "本件", "本节", "本回件", "本候选", "该笔", "该件", "此笔",
                      "台账", "母本", "本域", "本轮", "审阅回件", "复核回件"],
    "或_in_COORD": bool(DG0.DG_COORD_RE.search("或")),
    "QUOTE_classes": DG0.DG_QUOTE_RE.pattern,
    "但先于但是": DG0.DG_BREAK_RE.search("但是").group(0),
    "g7_NEG_WINDOW": G70.NEG_WINDOW, "g7_CLAUSE_BREAK": G70.CLAUSE_BREAK,
    "g7_DOUBLE_NEG_branches": G70.DOUBLE_NEG_RE.pattern.strip("()").split("|"),
}
print("[C] 守卫常量: NEG1=%(NEG1)d MID=%(MID)d NEG2=%(NEG2)d PSEUDO=%(PSEUDO_DN)d "
      "GAP=%(GAP)d VERB=%(SCOPE_VERB)d TAIL=%(SPLIT_TAIL)d" % gc)
print("    NEG2 完整否定谓语5 在表 = %(NEG2_完整否定谓语5)s ; 敢_in_MID=%(敢_in_MID)s ; "
      "或_in_BREAK=%(或_in_BREAK)s 与_in_BREAK=%(与_in_BREAK)s 监理方_in_SECOND=%(监理方_in_SECOND)s" % gc)
print("    但先于但是 → search('但是') 命中 = %r（执行员词序瑕疵观察复核）" % gc["但先于但是"])
print("    g7 NEG_WINDOW=%(g7_NEG_WINDOW)s CLAUSE_BREAK=%(g7_CLAUSE_BREAK)s DOUBLE_NEG 支数=%(nb)d 支=%(g7_DOUBLE_NEG_branches)s"
      % dict(gc, nb=len(gc["g7_DOUBLE_NEG_branches"])))
out["guard_constants"] = gc

# ================= (D) 我的 detect + 基线 =================
def v_pure(mod, text):
    p, _ = mod.dg_scan(text, toks_of(text))
    return "CATCH" if p else "PASS"

def v_drop(g7mod, text):
    pd, _ = g7mod.r12_scan(text, toks_of(text))
    return "CATCH" if pd else "PASS"

def score(verd):
    fp, fn = [], []
    for c in CASES:
        if c["expect"] == "AMBIG":
            continue
        got = verd[c["id"]]
        if c["expect"] == "PASS" and got == "CATCH":
            fp.append(c["id"])
        elif c["expect"] == "CATCH" and got == "PASS":
            fn.append(c["id"])
    return fp, fn

BASE_VERD = {c["id"]: v_pure(DG0, c["text"]) for c in CASES}
fp0, fn0 = score(BASE_VERD)
print("[D] 基线 DG_pure strict: fp=%d %s ; fn=%d %s" % (len(fp0), fp0, len(fn0), fn0))
out["baseline"] = {"fp": fp0, "fn": fn0}

orch = json.load(open(ROOT + "/lead/dg_adversarial_20261109/_dga_adversarial_out.json", encoding="utf-8"))
s_strict = orch["scoring_strict"]
match_pure = (s_strict["DG_pure"]["fp_ids"] == fp0 and s_strict["DG_pure"]["fn_ids"] == fn0)
print("[D] vs 编排方 scoring_strict.DG_pure 逐 id 全同 = %s（编排方 fp=%s fn=%s）"
      % (match_pure, s_strict["DG_pure"]["fp_ids"], s_strict["DG_pure"]["fn_ids"]))
G70D = load_mod("_fdv_g7_drop0", SB + "/_fdv_g7_base.py")
G70D.DOUBLE_NEG_RE = DG0.DG_DROPIN_RE
DROP_VERD = {c["id"]: v_drop(G70D, c["text"]) for c in CASES}
fpd, fnd = score(DROP_VERD)
match_drop = (s_strict["DG_dropin"]["fp_ids"] == fpd and s_strict["DG_dropin"]["fn_ids"] == fnd)
print("[D] 基线 DG_dropin strict: fp=%d %s ; fn=%d %s ; vs 编排方全同 = %s"
      % (len(fpd), fpd, len(fnd), fnd, match_drop))
out["baseline_dropin"] = {"fp": fpd, "fn": fnd, "match_orchestrator": match_drop}
out["baseline_match_orchestrator"] = match_pure

# ================= (E) E2 改版臂（全部我自己的内存改版） =================
BW10 = ["但", "但是", "然而", "不过", "却", "只是", "反之", "相反", "另外", "另"]
W14 = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究",
       "总而言之", "归根结底", "话说回来", "退一步说", "哪怕", "说白了"]
COORD6 = ["与", "或", "及", "和", "同", "跟"]
RE_NL = "\\" + "n"
QPAT_BASE = r'「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`'
QPAT_JIA = "|".join([QPAT_BASE, '"[^"' + RE_NL + ']*"', "《[^》" + RE_NL + "]*》"])
QPAT_JIA4 = "|".join([QPAT_BASE, '"[^"' + RE_NL + ']*"',
                      "'" + "[^'" + RE_NL + "]*'", "《[^》" + RE_NL + "]*》", "（[^）" + RE_NL + "]*）"])

ARMS = {}
G7S = {}

def reg(name, mod):
    ARMS[name] = mod
    g = load_mod("_fdv_g7_for_" + name, SB + "/_fdv_g7_base.py")
    g.DOUBLE_NEG_RE = mod.DG_DROPIN_RE
    G7S[name] = g

def mask_with(extra_pairs):
    def _mask(mod, s):
        def blank(mm):
            g = mm.group(0)
            return g[0] + " " * (len(g) - 2) + g[-1]
        o = mod.DG_QUOTE_RE.sub(blank, s)
        for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`")) + tuple(extra_pairs):
            i = o.find(op)
            if i >= 0 and o.find(cl, i + 1) < 0:
                return o[:i + 1]
        return o
    return _mask

def install_mask(mod, extra_pairs):
    f = mask_with(extra_pairs)
    mod._mask_quotes = lambda s, _m=mod, _f=f: _f(_m, s)

def make(name, break_extra=None, quote_pat=None, quote_pairs=(), neg1_drop=(),
         neg2_drop=(), mid_drop=(), second_add=None):
    m = load_mod("_fdv_dg_" + name, SB + "/_fdv_dg_core_base.py")
    if break_extra is not None:
        m.DG_BREAK_RE = re.compile(r"[" + m._BREAK + r"]|" + "|".join(BW10 + break_extra))
    if quote_pat is not None:
        m.DG_QUOTE_RE = re.compile(quote_pat)
    if quote_pairs:
        install_mask(m, quote_pairs)
    if neg1_drop:
        m.NEG1 = tuple(w for w in m.NEG1 if w not in neg1_drop)
    if neg2_drop:
        m.NEG2 = tuple(w for w in m.NEG2 if w not in neg2_drop)
    if mid_drop:
        m.MID = tuple(w for w in m.MID if w not in mid_drop)
    if neg1_drop or neg2_drop or mid_drop:
        m.DG_DROPIN_RE, m.DG_PATTERN, m.DG_STATS = m.dg_build_dropin_regex()
    if second_add:
        m._SECOND = m._SECOND.replace("|第", "|" + second_add + "|第", 1)
        m.DG_SECOND_SUBJ_RE = re.compile(r"(?:" + m._SECOND + r")")
    return m

def install_wholewindow_veto(mod, exempt_pseudo=True):
    pseudo_re = re.compile("(?:" + "|".join(re.escape(w) for w in mod.PSEUDO_DN) + ")")
    neg1_set = tuple(mod.NEG1)
    def ddn(pre, post="", _m=mod):
        p = _m._mask_quotes(pre)
        scope = _m._scope(p)
        mm = _m.DG_DROPIN_RE.search(scope)
        if not mm:
            return {"hit": False, "hit_text": "", "template": "", "scope": scope,
                    "reason": "scope 内无 N1-M-N2 管辖链（fdv）"}
        hit_text = mm.group(0)
        tmpl = "T3_split" if mm.group("t3") else "T12_adjacent"
        rest = scope[:mm.start()] + scope[mm.end():]
        rest_clean = pseudo_re.sub("", rest) if exempt_pseudo else rest
        if any(w in rest_clean for w in neg1_set) or _m.DG_COORD_RE.search(rest_clean):
            return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                    "reason": "整窗rest含其他否定/并列成分（fdv 甲c veto, exempt_pseudo=%s）" % exempt_pseudo}
        if _m.DG_SECOND_SUBJ_RE.search(hit_text):
            return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                    "reason": "命中链内含第二主语（fdv）"}
        if _m.DG_COORD_RE.search(hit_text):
            return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                    "reason": "命中链内含并列标记（fdv）"}
        return {"hit": True, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "同微句内 N1 支配 N2（fdv）"}
    mod.dg_double_neg = ddn

reg("base", DG0)
reg("甲", make("jia", break_extra=W14, quote_pat=QPAT_JIA, quote_pairs=[('"', '"'), ("《", "》")]))
m = make("codeonly")
install_wholewindow_veto(m, exempt_pseudo=True)
reg("纯改代码", m)
m = make("jiac", break_extra=W14, quote_pat=QPAT_JIA, quote_pairs=[('"', '"'), ("《", "》")])
install_wholewindow_veto(m, exempt_pseudo=True)
reg("甲c", m)
m = make("jiacnp", break_extra=W14, quote_pat=QPAT_JIA, quote_pairs=[('"', '"'), ("《", "》")])
install_wholewindow_veto(m, exempt_pseudo=False)
reg("甲c无豁免", m)
reg("甲4引号", make("jia4", break_extra=W14, quote_pat=QPAT_JIA4,
                    quote_pairs=[('"', '"'), ("'", "'"), ("《", "》"), ("（", "）")]))
reg("乙", make("yi", neg1_drop=("不敢", "并不", "并非")))
reg("乙2", make("yi2", neg2_drop=("否认", "不承认")))
reg("乙3", make("yi3", neg1_drop=("不敢", "并不", "并非"), neg2_drop=("否认", "不承认"), mid_drop=("敢",)))
reg("灾难_乙3删不", make("dis", neg1_drop=("不敢", "并不", "并非"), neg2_drop=("否认", "不承认", "不"), mid_drop=("敢",)))
reg("甲_并列词进断裂", make("jiacoord", break_extra=W14 + COORD6, quote_pat=QPAT_JIA,
                            quote_pairs=[('"', '"'), ("《", "》")]))
reg("甲_监理方进SECOND", make("jiasecond", break_extra=W14, quote_pat=QPAT_JIA,
                              quote_pairs=[('"', '"'), ("《", "》")], second_add="监理方"))

arm_res = {}
print("\n[E] E2 全臂（DG_pure strict；AMBIG A01-A04/C20 排除）")
for name, mod in ARMS.items():
    verd = {c["id"]: v_pure(mod, c["text"]) for c in CASES}
    fp, fn = score(verd)
    diff = [c["id"] for c in CASES if verd[c["id"]] != BASE_VERD[c["id"]]]
    amb_flip = [c["id"] for c in CASES if c["expect"] == "AMBIG" and verd[c["id"]] != BASE_VERD[c["id"]]]
    anchor = [w for w in mod.R12_TEN if not mod.DG_DROPIN_RE.search(w)]
    drop_fp, drop_fn = score({c["id"]: v_drop(G7S[name], c["text"]) for c in CASES})
    arm_res[name] = {"fp": fp, "fn": fn, "verdict_diff_vs_base": diff, "ambig_flip": amb_flip,
                     "R12TEN_unmatched": anchor,
                     "dropin_fp": drop_fp, "dropin_fn": drop_fn}
    print("  %-14s fp=%d %-30s fn=%d %-28s | vs base 变动=%s AMBIG变动=%s | R12TEN缺=%s | dropin fp=%d fn=%d"
          % (name, len(fp), str(fp), len(fn), str(fn), diff, amb_flip, anchor, len(drop_fp), len(drop_fn)))
out["e2_arms"] = arm_res

# ---- 隐藏代价探针（我自建句）----
PROBES = {
    "甲_结果撞断裂词_真阳": "非登记结果不可才算本件已生效",     # C07 形真阳
    "乙_复审组并非不承认_真阳": "复审组并非不承认本件已生效",   # C17 形真阳
    "乙2_监理方并不否认_真阳": "监理方并不否认本件已生效",     # 真阳
    "P09_监理方第二主语": "旧稿并不否认与监理方不宣告已生效",   # 期望 PASS
    "P10_并列或": "本件不承认或并不否认已生效",               # 期望 PASS
}
probe_res = {}
for pname, ptext in PROBES.items():
    row = {}
    for name, mod in ARMS.items():
        row[name] = v_pure(mod, ptext)
    probe_res[pname] = row
    print("  探针 %-24s（基线=%s）: %s" % (pname, row["base"],
          {k: v for k, v in row.items() if k != "base"}))
out["probes"] = probe_res

# ================= (F) 我的最小实现：逐 fp 根因解剖 =================
def my_mask(s, quote_re):
    """我按 _dg_core.py:148-158 规格自写的引证屏蔽（不复用其函数体）。"""
    def blank(mm):
        g = mm.group(0)
        return g[0] + " " * (len(g) - 2) + g[-1]
    o = quote_re.sub(blank, s)
    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`")):
        i = o.find(op)
        if i >= 0 and o.find(cl, i + 1) < 0:
            return o[:i + 1]
    return o

def my_scope(s, break_re):
    """我按 _dg_core.py:161-164 规格自写的微句切断。"""
    cuts = [mm.end() for mm in break_re.finditer(s)]
    return s[cuts[-1]:] if cuts else s

agree_mask = agree_scope = agree_verdict = 0
detail = {}
for c in CASES:
    toks = toks_of(c["text"])
    mm0 = re.search(re.escape(toks[0]), c["text"])
    pre = c["text"][:mm0.start()]
    mine_mask, theirs_mask = my_mask(pre, DG0.DG_QUOTE_RE), DG0._mask_quotes(pre)
    mine_scope, theirs_scope = my_scope(mine_mask, DG0.DG_BREAK_RE), DG0._scope(theirs_mask)
    agree_mask += (mine_mask == theirs_mask)
    agree_scope += (mine_scope == theirs_scope)
    mine_hit = bool(DG0.DG_DROPIN_RE.search(mine_scope))
    theirs = DG0.dg_double_neg(pre)
    agree_verdict += (mine_hit == theirs["hit"])
    if c["id"] in ("P06", "P07", "P08", "P09", "P10", "P11", "P12"):
        m2 = DG0.DG_DROPIN_RE.search(mine_scope)
        hit_text = m2.group(0) if m2 else ""
        rest = (mine_scope[:m2.start()] + mine_scope[m2.end():]) if m2 else ""
        neg1_in_rest = sorted({w for w in DG0.NEG1 if w in rest})
        detail[c["id"]] = {
            "text": c["text"], "scope": mine_scope, "hit": hit_text,
            "hit_span": [m2.start(), m2.end()] if m2 else None,
            "boundary14_in_scope": [w for w in W14 if w in mine_scope],
            "boundary14_in_hit": [w for w in W14 if w in hit_text],
            "second_subj_in_scope": bool(DG0.DG_SECOND_SUBJ_RE.search(mine_scope)),
            "second_subj_in_hit": bool(DG0.DG_SECOND_SUBJ_RE.search(hit_text)),
            "coord_in_scope": bool(DG0.DG_COORD_RE.search(mine_scope)),
            "coord_in_hit": bool(DG0.DG_COORD_RE.search(hit_text)),
            "neg1_members_in_rest": neg1_in_rest,
            "unmasked_quote_chars_in_pre": sorted({ch for ch in pre if ch in '"《》「」“”`'}),
        }
print("\n[F] 我的最小实现 vs 原实现（41 条）: mask 一致 %d/41, scope 一致 %d/41, hit 判定一致 %d/41"
      % (agree_mask, agree_scope, agree_verdict))
for k in ("P06", "P08", "P09", "P10", "P11", "P12"):
    d = detail[k]
    print("  %-4s hit=%-8s span=%s scope=%s" % (k, d["hit"], d["hit_span"], d["scope"]))
    print("       边界词在scope=%s 在hit=%s | 第二主语 scope=%s hit=%s | 并列 scope=%s hit=%s | rest 内 NEG1=%s"
          % (d["boundary14_in_scope"], d["boundary14_in_hit"], d["second_subj_in_scope"],
             d["second_subj_in_hit"], d["coord_in_scope"], d["coord_in_hit"], d["neg1_members_in_rest"]))
out["minimal_impl_agreement"] = {"mask": agree_mask, "scope": agree_scope, "verdict": agree_verdict}
out["fp_root_cause_detail"] = detail

json.dump(out, open(WD + "/_fdv_run1_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten: _fdv_run1_out.json")
