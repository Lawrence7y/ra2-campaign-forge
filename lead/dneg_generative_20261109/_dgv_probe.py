# -*- coding: utf-8 -*-
r"""_dgv_probe.py — 独立复核②③④：自造刁钻负样本，同时测两条路径。
路径 A = 设计稿的纯函数 DG.dg_scan()（带 _mask_quotes/_scope/第二主语/并列 veto）
路径 B = 设计稿声称的【一行替换】真实落地形态：仅把 g7.DOUBLE_NEG_RE 换成
         DG.DG_DROPIN_RE，r10_context(:92) 与 r12_scan(:144) 零改动。
零真机、零采样；只读既有件 + 本写域；输出只落本写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_probe.py
"""
import sys, json, hashlib, importlib.util, re
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
assert hashlib.sha256(G7P.read_bytes()).hexdigest() == \
    "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"


def _load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# 两个独立模块实例：base 保持原状，drop 模拟一行替换
base = _load("_dgv_base", G7P)
drop = _load("_dgv_drop", G7P)
DG = _load("_dgv_dg", WD / "_dg_core.py")
drop.DOUBLE_NEG_RE = DG.DG_DROPIN_RE          # 内存模拟，不写任何既有件

# 复用 _dg_pasteable.py 独立编译结果，核对与 _dg_core.py 是否同一 pattern
PS = _load("_dgv_paste", WD / "_dg_pasteable.py")
print("=== (0) 独立粘贴件编译核对 ===")
print("  pasteable.DG_STATS =", PS.DG_STATS)
print("  pattern 与 core 相同 =", PS.DG_PATTERN == DG.DG_PATTERN)
print("  pattern_chars =", len(PS.DG_PATTERN))
print("  R12_TEN 全生成 =", all(bool(PS.DG_DROPIN_RE.search(c)) for c in PS.R12_TEN))
print("  DG_STATS(core) =", DG.DG_STATS)

TOK = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

# ② 自己实跑 r10_scan / r12_scan 复核 ≥6 条漏判（不用撰写人的脚本/结论）
GAPS = [
    "亦非不宣告 N-4 正式绑定已生效",
    "未尝不认为本件已生效",
    "莫不认为本件已生效",
    "不敢不承认本件已生效",
    "不会不承认本件已生效",
    "并非没有宣告本件已生效",
    "并不否认本件已生效",
    "岂能不说本件已生效",
    "不可谓不宣告本件已生效",
    "不是没有宣告本件已生效",
]
print("\n=== ② 自跑 base.r10_scan / base.r12_scan 复核 10 条漏判 ===")
gap_rows = []
for t in GAPS:
    p10, w10, h10 = base.r10_scan(t, TOK)
    p12, h12 = base.r12_scan(t, TOK)
    kinds = [h["kind"] for h in h10]
    r = {"text": t, "r10_problems": len(p10), "r10_kinds": kinds,
         "r12_problems": len(p12), "double_neg_regex_hit": bool(base.DOUBLE_NEG_RE.search(t)),
         "漏判": (len(p12) == 0 and not base.DOUBLE_NEG_RE.search(t))}
    gap_rows.append(r)
    print("  %-34s r10_problems=%d kinds=%s r12=%d regex=%s 漏判=%s" %
          (t[:32], len(p10), ",".join(kinds), len(p12), r["double_neg_regex_hit"], r["漏判"]))
print("  → 确认漏判 %d/%d" % (sum(r["漏判"] for r in gap_rows), len(gap_rows)))

# ③④ 自造 12 条更刁钻负样本（全为「两个独立否定短语」或跨微句/引证污染，期望 PASS）
NEG = [
    ("V01", "「并非不宣告已生效」只是引文，本件不采信该说法。",
     "双重否定在引证跨度内；R10 SPAN_RE 覆盖整段，正文另为独立否定"),
    ("V02", "别处不得不承认但本件不宣告已生效",
     "前段 DN + 转折词「但」后另起单重否定；BQ 不含「但」，GOVERN 不切断"),
    ("V03", "旧稿并不否认然而本件不宣告已生效",
     "前段 DN + 转折词「然而」后另起单重否定"),
    ("V04", "并不否认甲方不宣告已生效",
     "两层否定分属不同主语/不同谓语；第二主语「甲方」不在 _SECOND 表内"),
    ("V05", "并没有不承认但本件只登记已入账",
     "前段 DN 与后段独立陈述并列，无标点隔断"),
    ("V06", "无越权断言：本件不出现「可应用母本…」。",
     "docstring :74-75 点名的「两个独立否定短语」原句"),
    ("V07", "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；",
     "CANDIDATE:155 逐字形态"),
    ("V08", "不闻不问，本件已生效。", "不…不… 并列成语"),
    ("V09", "不卑不亢地说明本件已生效。", "并列成语"),
    ("V10", "非但不宣告已生效，还否认入账。", "伪构式 + 逗号切断"),
    ("V11", "本件不宣告已生效，但台账已入账。", "转折连词切断"),
    ("V12", "不得不承认旧稿却本件不宣告已生效",
     "转折词「却」后另起单重否定，无标点"),
    ("V13", "并不否认本笔不宣告已生效",
     "第二主语「本笔」在 _SECOND 表内，但 veto 只作用于 hit_text 而非整段"),
    ("V14", "莫不称快，本件不出现放行 N-5 断言", "周遍 DN 在前句，后句独立否定"),
    ("V15", "本件不承认、并不否认均不成立已生效", "并列的两项独立否定（顿号）"),
]


def verdict_gate(mod, text, toks):
    """返回 (r10_kinds, r12_problems, dbl_any)。"""
    p10, w10, h10 = mod.r10_scan(text, toks)
    p12, h12 = mod.r12_scan(text, toks)
    dbl = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            dbl.append(mod.r10_context(text, m.start(), m.end())["dbl"])
    return [h["kind"] for h in h10], len(p12), any(dbl)


print("\n=== ③④ 15 条自造刁钻负样本：base / DG纯函数 / DG一行替换 三路对照（期望全 PASS）===")
rows = []
for cid, text, why in NEG:
    toks = [t for t in TOK if t in text]
    if not toks:
        toks = ["已生效"]
    k10, n12b, dblb = verdict_gate(base, text, toks)
    pdg, hdg = DG.dg_scan(text, toks)
    k10d, n12d, dbld = verdict_gate(drop, text, toks)
    pure = "CATCH" if pdg else "PASS"
    repl = "CATCH" if n12d > 0 else "PASS"
    r = {"id": cid, "text": text, "why": why, "toks": toks,
         "base_r10_kinds": k10, "base_r12": n12b, "base_dbl": dblb,
         "dg_pure": pure, "dg_pure_hit": hdg[0]["hit"] if hdg else "",
         "drop_r10_kinds": k10d, "drop_dbl": dbld, "drop_r12": n12d,
         "dg_dropin": repl}
    rows.append(r)
    print("  %-4s pure=%-5s dropin=%-5s base_r12=%d drop_r12=%d dbl(base/drop)=%s/%s pure_hit=%-10s | %s" %
          (cid, pure, repl, n12b, n12d, dblb, dbld, r["dg_pure_hit"][:10], text[:40]))

pure_fp = [r["id"] for r in rows if r["dg_pure"] == "CATCH"]
drop_fp = [r["id"] for r in rows if r["dg_dropin"] == "CATCH"]
print("\n  → DG 纯函数 fp = %d : %s" % (len(pure_fp), pure_fp))
print("  → DG 一行替换落地 fp = %d : %s" % (len(drop_fp), drop_fp))

# 额外：把 NEG 里每条 pre 打印出来，便于人工核对 match 来源
print("\n=== 逐条 pre / scope / 原始 regex 命中（drop-in 路径）===")
for cid, text, why in NEG:
    toks = [t for t in TOK if t in text] or ["已生效"]
    tok = toks[0]
    m = re.search(re.escape(tok), text)
    s = max(0, m.start() - base.NEG_WINDOW)
    b = max(text.rfind(c, 0, m.start()) for c in base.CLAUSE_BREAK)
    if b > s:
        s = b
    pre = text[s:m.start()]
    hit = DG.DG_DROPIN_RE.search(pre)
    print("  %-4s tok=%-8s pre=%r  raw_hit=%r  dg_pure=%s" %
          (cid, tok, pre, hit.group(0) if hit else None,
           DG.dg_double_neg(pre)["hit"]))

out = {"gap_rows": gap_rows, "gap_confirmed": sum(r["漏判"] for r in gap_rows),
       "negatives": rows, "pure_fp": pure_fp, "dropin_fp": drop_fp,
       "pasteable_same_pattern": PS.DG_PATTERN == DG.DG_PATTERN,
       "pasteable_stats": PS.DG_STATS, "core_stats": DG.DG_STATS}
(WD / "_dgv_probe_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_probe_out.json")
