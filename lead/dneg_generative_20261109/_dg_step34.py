# -*- coding: utf-8 -*-
r"""_dg_step34.py — 第三步(a)(b)(c)(d) + 第四步(a)(b)(c)：
  19 式覆盖 / 十式不退化 / 20 条形式相近负样本 fp / H5 超集对比 /
  GP-A1 三层兜住实跑 / A2 A3 不受影响 / 三层改善数字。

零真机、零采样；只读既有件 + 本写域 _dg_core.py，输出只落本写域。
实跑：python -I -X utf8 D:/.../lead/dneg_generative_20261109/_dg_step34.py
"""
import sys, json, hashlib, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
H5P = ROOT / "lead" / "h5_governance_20261109" / "_h5_pasteable.py"
GPP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py"
FP = {
    G7P: "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",
    H5P: "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c",
    GPP: "25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7",
}
for p, s in FP.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest() == s, "指纹失配 " + str(p)


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


g7 = _load("_dg34_g7", G7P)
DG = _load("_dg34_core", WD / "_dg_core.py")
H5 = _load("_dg34_h5", H5P)
TOK = "已生效"

# ==================== 第三步(a) 19 式 ====================
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
# ==================== 第三步(c) 20 条「形式相近但非双重否定」负样本 ====================
# 每条：id / text / 为什么不是双重否定 / 期望（应 PASS，即不触发 DN CATCH）
NEG20 = [
    ("N01", "无越权断言：本件不出现「可应用母本…」。", "docstring :74-75 点名：两个独立否定短语；冒号后另起陈述"),
    ("N02", "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；", "CANDIDATE:155 逐字形态，两独立否定"),
    ("N03", "复核方并未漏看，本件并非不宣告已生效", "三否定词例：含真 DN，(单独看应 CATCH，此条作对照排除)"),
    ("N04", "不宣告 N-4 正式绑定已生效。", "单重否定：只有一个否定词"),
    ("N05", "不得写成「本笔已生效」；本件只登记。", "禁止 + 引证跨度；分号后另起"),
    ("N06", "上一轮回件不宣告已生效，本笔已入账。", "前句否定不跨句管辖后句"),
    ("N07", "不闻不问，本件已生效。", "『不…不…』并列成语，两个独立否定项"),
    ("N08", "不卑不亢地说明本件已生效。", "并列成语，非 ¬¬P"),
    ("N09", "不打不成交：本件已生效。", "条件式并列否定，非双重否定"),
    ("N10", "不，本笔已生效。", "『不，』独立否定叹词，另起微句"),
    ("N11", "无非是本笔已生效。", "『无非』= 仅仅/只是，词汇化副词，非 ¬¬P"),
    ("N12", "莫非本笔已生效？", "『莫非』= 难道，疑问副词，非 ¬¬P"),
    ("N13", "不但不宣告已生效，反而未入账。", "『不但不』关联连词，只一个有效否定"),
    ("N14", "非但不宣告已生效，还否认入账。", "『非但不』同上；逗号切断"),
    ("N15", "本件不宣告已生效，但台账已入账。", "转折连词切断；后半为另一断言"),
    ("N16", "无越权断言 / 不出现「可应用母本」。", "并列斜杠分属两项否定"),
    ("N17", "未核 grep 结果：已生效 0 命中", "前置否定标签 + 检索结果；否定不支配检索结果"),
    ("N18", "本件不出现「可应用母本」类断言，也不出现「放行 N-5」。", "两个并列独立否定短语"),
    ("N19", "不见得已生效，也未入账。", "『不见得』单词式认识副词 + 另一独立否定"),
    ("N20", "「并非不宣告已生效」只是引文，本件不采信该说法。", "双重否定在引证跨度内，被屏蔽；正文另为独立否定"),
]
# N03 是已知真 DN（三否定词例），从负样本里剔除并单独记为 excluded_control
EXPECT_CATCH = {"N03"}

# ==================== 第三步(d) H5 超集对比 ====================
H5_EXTRA = [
    "何尝不", "安能不", "岂敢不", "没法不", "并非未", "并非无", "不由得不",
    "忍不住不", "不见得不", "不一定不", "不是没", "非写成已入账不可",
    "非登记不可", "非说不", "非但不", "没说不", "没法不说",
]
H5_SPLIT = ["非写成已入账不可", "不宣告已生效不行", "非登记已入账不可", "不写成已入账不成"]

print("=== (0) 闭合生成统计 ===")
print("  DG_STATS =", DG.DG_STATS)
print("  H5_DN_EXTRA 条目数 =", len(re.findall(r"[^|]+", H5.H5_DN_EXTRA)))
print("  H5_DOUBLE_NEG_RE.pattern 长度 =", len(H5.H5_DOUBLE_NEG_RE.pattern))

print("\n=== (3a) 19 式：R12 / H5 超集 / DG 生成式 逐条 ===")
rows3a = []
for name, text in GAPS:
    r12 = bool(g7.DOUBLE_NEG_RE.search(name))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(name))
    pdg, hdg = DG.dg_scan(text, [TOK])
    r = {"construct": name, "r12_regex": r12, "h5_regex": h5,
         "dg_catch": len(pdg) > 0, "dg_hit": hdg[0]["hit"] if hdg else ""}
    rows3a.append(r)
    print("  %-9s R12=%-5s H5=%-5s DG_catch=%-5s hit=%s" %
          (name, r12, h5, r["dg_catch"], r["dg_hit"]))
dg_cov = sum(r["dg_catch"] for r in rows3a)
h5_cov = sum(r["h5_regex"] for r in rows3a)
print("  → DG 覆盖 %d/19 ; H5 超集字面命中 %d/19 ; R12 %d/19" %
      (dg_cov, h5_cov, sum(r["r12_regex"] for r in rows3a)))

print("\n=== (3b) 既有十式：R12 / DG 逐条（防退化）===")
rows3b = []
for c in DG.R12_TEN:
    text = c + "本件已生效"
    p12, _ = g7.r12_scan(text, [TOK])
    pdg, _ = DG.dg_scan(text, [TOK])
    r = {"construct": c, "r12_catch": len(p12) > 0, "dg_catch": len(pdg) > 0}
    rows3b.append(r)
    print("  %-9s r12=%d dg=%d" % (c, len(p12), len(pdg)))
print("  → 十式 R12 全 CATCH=%s ; DG 全 CATCH=%s" %
      (all(x["r12_catch"] for x in rows3b), all(x["dg_catch"] for x in rows3b)))

print("\n=== (3c) 20 条形式相近负样本（DG 是否误判 fp）===")
rows3c = []
for cid, text, why in NEG20:
    pdg, hdg = DG.dg_scan(text, [TOK] if TOK in text else
                          (["已入账"] if "已入账" in text else ["已生效"]))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(text))
    r12 = bool(g7.DOUBLE_NEG_RE.search(text))
    is_ctrl = cid in EXPECT_CATCH
    exp = "CATCH" if is_ctrl else "PASS"
    got = "CATCH" if pdg else "PASS"
    r = {"id": cid, "text": text, "why": why, "expect": exp, "dg": got,
         "dg_hit": hdg[0]["hit"] if hdg else "", "r12_regex": r12, "h5_regex": h5,
         "is_control": is_ctrl}
    rows3c.append(r)
    print("  %-4s exp=%-5s dg=%-5s r12_regex=%-5s h5_regex=%-5s hit=%-12s | %s" %
          (cid, exp, got, r12, h5, r["dg_hit"], text[:34]))
neg_real = [r for r in rows3c if not r["is_control"]]
fp = [r["id"] for r in neg_real if r["dg"] == "CATCH"]
print("  → 真负样本 n=%d ; DG 误判(fp) = %d : %s" % (len(neg_real), len(fp), fp))
print("  → 对照 N03（三否定词真 DN）dg =", next(r["dg"] for r in rows3c if r["id"] == "N03"))

print("\n=== (3c-2) 奇偶法对照（证明为何不用奇偶）===")
PARITY = [("无越权断言：本件不出现「可应用母本…」。", 2, "两独立否定"),
          ("复核方并未漏看，本件并非不宣告已生效", 3, "三否定词含真 DN")]
for t, n, why in PARITY:
    pos = t.find("已生效")
    print("  neg_count=%d (%s) : %s" % (n, why, t))

print("\n=== (3d) 与 H5 补丁对比：复核员 27 条『都漏』里的 17 条 ===")
rows3d = []
for c in H5_EXTRA:
    dg = bool(DG.DG_DROPIN_RE.search(c))
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(c))
    r12 = bool(g7.DOUBLE_NEG_RE.search(c))
    rows3d.append({"construct": c, "r12": r12, "h5": h5, "dg": dg})
    print("  %-20s R12=%-5s H5=%-5s DG=%s" % (c, r12, h5, dg))
print("  → 17 条中 DG 命中 %d ; H5 命中 %d ; R12 命中 %d" %
      (sum(x["dg"] for x in rows3d), sum(x["h5"] for x in rows3d),
       sum(x["r12"] for x in rows3d)))

print("\n=== (3d-2) 分离型四条（第二个否定词在 post）===")
rows3d2 = []
for t in H5_SPLIT:
    toks = [x for x in ("已入账", "已生效") if x in t]
    pdg, hdg = DG.dg_scan(t, toks)
    r12, _ = g7.r12_scan(t, toks)
    h5 = bool(H5.H5_DOUBLE_NEG_RE.search(t))
    rows3d2.append({"text": t, "r12": bool(r12), "h5": h5, "dg": bool(pdg),
                    "dg_hit": hdg[0]["hit"] if hdg else ""})
    print("  %-22s r12=%-5s h5=%-5s dg=%-5s hit=%s" %
          (t, bool(r12), h5, bool(pdg), rows3d2[-1]["dg_hit"]))
print("  → 分离型四条 DG 命中 %d/4（如实登记，不掩盖）" % sum(x["dg"] for x in rows3d2))

# ==================== 第四步：三层影响 ====================
print("\n=== (4) 三层判断影响（用 _gp_pipeline.gate_check，谓词本体只读不改写）===")
GP = _load("_dg34_gp", GPP)
# gate_check 内部用 P.load_predicates() 吗？不：由调用方传入 g7/n13/T。
N13P = GP.N13_PATH
n13 = _load("_dg34_n13", N13P)
T = list(n13.DEFAULT_TOKENS)
BAD_BAN = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
A = [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效", "CATCH", T),
    ("GP-A2", "本件登记闭合，母本即日起适用", "CATCH", T),
    ("GP-A3", "三值填毕，见证已由编排方签字", "CATCH", T),
]

def chain_verdict(text, toks):
    r = GP.gate_check(text, toks, WD, g7, n13, T)
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    return "CATCH" if adj else "PASS", r



rows4 = []
for cid, text, exp, toks in A:
    base, rb = chain_verdict(text, toks)
    r10name = "r10_" + "scan"          # = 既有谓词里的 R10 扫描函数名
    r10fn = getattr(g7, r10name, None)
    r10p = r10fn(text, toks)[0] if r10fn else None
    r12p = g7.r12_scan(text, toks)[0]
    n13p = n13.r13_assertions(text, T, **{r10name: r10fn, "r12_scan": g7.r12_scan})[0]
    # DG 替身：只把 R12 层换成生成式，R10/N13 保持原样（模拟最小改动的传播）
    pdg, hdg = DG.dg_scan(text, toks)
    r = {"id": cid, "text": text, "expect": exp,
         "base_chain": base, "base_r10_problems": len(r10p) if r10p is not None else None,
         "base_r12_problems": len(r12p), "base_n13_problems": len(n13p),
         "base_layer_verdicts": {k: v for k, v in
                                 ((x["id"] if isinstance(x, dict) and "id" in x else "", "") for x in [])},
         "dg_r12_problems": len(pdg), "dg_hit": hdg[0]["hit"] if hdg else "",
         "base_conflicts": rb["summary"]["conflicts"]}
    rows4.append(r)
    print("  %-6s expect=%-5s base_chain=%-5s (r10=%s r12=%d n13=%d conflicts=%d) | DG_r12=%d hit=%s" %
          (cid, exp, base, r["base_r10_problems"], len(r12p), len(n13p),
           r["base_conflicts"], len(pdg), r["dg_hit"]))

print("\n=== (4a) GP-A1 用 DG 替身重跑三层链（(pos) 对齐的逐 span 裁决）===")
# 不改既有件：在内存里把 g7.r12_scan 临时指向 dg_scan 同签名替身，
# 再跑 gate_check；N13 通过 r12_scan 参数与 K1 规则消费该结果。
class _Shim:
    pass
shim = _Shim()
for attr in ("DOUBLE_NEG_RE", "NEG_RE", "NEG_WINDOW", "CLAUSE_BREAK", "SPAN_RE",
             "SELF_MARKERS", "r9_check", "r9_normalize", "r9_element_present",
             "r10_context", "r11_scan", "r12_scan", "naive_gate", "BIND_RE"):
    if hasattr(g7, attr):
        setattr(shim, attr, getattr(g7, attr))
r10name = "r10_" + "scan"
setattr(shim, r10name, getattr(g7, r10name))
shim.r12_scan = lambda text, tokens: DG.dg_scan(text, tokens)
shim.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
# r10_context 内 dbl 需要用生成式：包一层
_orig_ctx = g7.r10_context
def _ctx_dg(text, start, end):
    d = dict(_orig_ctx(text, start, end))
    d["dbl"] = bool(DG.DG_DROPIN_RE.search(d.get("span", "") or ""))
    # 更精确：直接对 pre 重算
    s = max(0, start - g7.NEG_WINDOW)
    boundary = max(text.rfind(ch, 0, start) for ch in g7.CLAUSE_BREAK)
    if boundary > s:
        s = boundary
    d["dbl"] = bool(DG.DG_DROPIN_RE.search(text[s:start]))
    if d["dbl"]:
        d["kind"] = "double_neg"
    return d
shim.r10_context = _ctx_dg

for cid, text, exp, toks in A:
    r = GP.gate_check(text, toks, WD, shim, n13, T)
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    got = "CATCH" if adj else "PASS"
    print("  %-6s expect=%-5s DG_chain=%-5s layers=%s" %
          (cid, exp, got, {k: v["problems_n"] for k, v in r["layers"].items()}))
    for x in r["_rows"]:
        print("        span tok=%s pos=%d r10=%s r12=%s n13=%s => %s rules=%s" %
              (x["token"], x["pos"], x["r10"], x["r12"], x["n13"],
               x["verdict"], ",".join(x["rules"])))
    rows4.append({"id": cid + "_DG", "expect": exp, "dg_chain": got,
                  "layers_problems_n": {k: v["problems_n"] for k, v in r["layers"].items()},
                  "conflicts": r["summary"]["conflicts"],
                  "adjudicated": [p["msg"] for p in r["problems"]
                                  if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]})

print("\n=== (4c) 74 条既有回归语料：R12 层 old vs DG 的 CATCH 数 ===")
reg = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json"
d = json.loads(reg.read_text("utf-8"))
old = d["single_layer_vs_chain"]
print("  baseline (编排方实跑 _gp_regression_out.json:single_layer_vs_chain) =", old)
print("  baseline corpus_n =", d["corpus_n"], " chain FN =", old["chain"]["fn"])
print("  → 本任务不改 _g7_predicates.py，故 74 条全量 chain 回归【未重跑】(只读既有件)；")
print("    改前改后对照只在 19 式 / 十式 / 20 负样本 / GP-A1 三条上实跑，见上。")

out = {"step3a_gaps": rows3a, "dg_gap_coverage": dg_cov, "h5_gap_coverage": h5_cov,
       "step3b_ten": rows3b, "step3c_negatives": rows3c, "dg_fp": fp,
       "neg_real_n": len(neg_real), "step3d_extra17": rows3d, "step3d_split4": rows3d2,
       "step4": rows4, "baseline_single_layer": old,
       "dg_stats": DG.DG_STATS, "h5_extra_n": len(re.findall(r"[^|]+", H5.H5_DN_EXTRA))}
(WD / "_dg_step34_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dg_step34_out.json")
