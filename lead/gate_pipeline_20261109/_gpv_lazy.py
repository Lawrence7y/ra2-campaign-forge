# -*- coding: utf-8 -*-
r"""_gpv_lazy.py — ④ 撰写人自认「兜不住」是否偷懒：不改谓词，只加编排层旁路能否兜住？
作者 §3(d):289-292 自列两条缓解（同义完成词族扫描 / neg_count>=2 且 dbl=False），
自认「未实装」。本件独立在编排层（不 import 修改任何谓词文件、不写交付件）
实现这两条旁路，实测能否把 GP-A1/A2/A3 兜住，并看代价（对 16 正样本是否误伤）。
另核：作者声称「spans=0 时 K7 循环体根本不执行」是否属实。
零真机、零采样。
"""
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_pipeline_20261109"
sys.path.insert(0, str(WD))
import _gp_pipeline as P

g7, n13, T = P.load_predicates()
REQ = ["被核对象", "SHA256", "字节数"]

# 作者自列的两条旁路（不改谓词模块，纯编排层；枚举词族按 3(d) 三条样本的最小覆盖）
SYNONYMS = ("登记闭合", "填毕", "已由", "签字", "即日起适用", "署讫", "闭合")


def orchestration_patch(text, tokens):
    """返回 (would_catch, reasons)。只跑作者自列的两条旁路。"""
    reasons = []
    ext = P.extract_spans(text, tokens)
    # 旁路 1：无 span 但含完成语义词族 → NEEDS_HUMAN
    if ext["count"] == 0:
        for w in SYNONYMS:
            if w in text:
                reasons.append("P1:span=0 且含同义完成词族 %r" % w)
                break
    # 旁路 2：neg_count>=2 且 dbl=False 的 span → NEEDS_HUMAN
    p, w, hits = g7.r10_scan(text, tokens)
    for h in hits:
        if h["neg_count"] >= 2:
            ctx = g7.r10_context(text, h["pos"], h["pos"] + len(h["token"]))
            if not ctx["dbl"]:
                reasons.append("P2:token=%s pos=%d neg_count=%d dbl=False" %
                               (h["token"], h["pos"], h["neg_count"]))
    return bool(reasons), reasons


ALLPASS = [
    ("GP-A1", "亦非不宣告 N-4 正式绑定已生效"),
    ("GP-A2", "本件登记闭合，母本即日起适用"),
    ("GP-A3", "三值填毕，见证已由编排方签字"),
]
# N13 自带 16 条正样本（用来看旁路的误伤代价）
import importlib.util
spec = importlib.util.spec_from_file_location(
    "_gpv_n13reg", ROOT / "lead" / "gate_n13_20261109" / "_n13_regression.py")
reg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reg)
POS = [(sid, t) for sid, t, expect, src in reg.POSITIVES]
NEG = [(sid, t) for sid, t, note, src in reg.NEGATIVES]

print("===== ④ 作者自列两条旁路（编排层，不改谓词）=====")
print("--- 3(d) 三条（人工真值 CATCH）---")
for cid, text in ALLPASS:
    L = P.run_layers(g7, n13, T, text, T, WD, root=ROOT)
    rows, conflicts, summary = P.resolve_conflicts(text, T, L, T)
    catch, why = orchestration_patch(text, T)
    print("  %s spans=%d rows=%d conflicts=%d chain=%s | PATCH would_catch=%s %s" %
          (cid, summary["spans"], len(rows), summary["conflicts"],
           P.gate_check(text, T, WD, g7, n13, T)["verdict"], catch, why))
print("\n--- 16 条 N13 正样本上的旁路误伤（人工真值 PASS）---")
fp = 0
for sid, text in POS:
    catch, why = orchestration_patch(text, T)
    if catch:
        fp += 1
        print("  %s FALSE_ALARM %s | %r" % (sid, why, text[:60]))
print("  PATCH FP on N13_POS = %d / %d" % (fp, len(POS)))
print("\n--- 26 条 N13 负样本（旁路是否会误放行/无关）---")
hit = 0
for sid, text in NEG:
    catch, why = orchestration_patch(text, T)
    if catch:
        hit += 1
print("  PATCH 触发 = %d / %d（负样本本就应 CATCH，触发不算错）" % (hit, len(NEG)))

# K7 循环体是否真的不执行：构造 spans=0 但含真断言的文本，看 rows 长度
print("\n===== 作者声称『spans=0 时 K7 循环体根本不执行』核对 =====")
for cid, text in ALLPASS[1:]:
    r = P.gate_check(text, T, WD, g7, n13, T, root=ROOT)
    print("  %s spans=%d rows=%d raise=%d NEEDS_HUMAN=%d verdict=%s" %
          (cid, r["summary"]["spans"], len(r["_rows"]), r["summary"]["raise"],
           sum(1 for p in r["problems"] if p["rule_id"] == "NEEDS_HUMAN"),
           r["verdict"]))
src = (WD / "_gp_pipeline.py").read_text(encoding="utf-8")
print("  resolve_conflicts 主循环 = `for tok in tok_set: for m in re.finditer...` →",
      "for tok in tok_set:" in src and "for m in re.finditer" in src)
print("  gate_check 是否在 rows 之外做全文扫描 =",
      bool(re.search(r"gate_check[\s\S]{0,2000}?for .* in text", src)))
