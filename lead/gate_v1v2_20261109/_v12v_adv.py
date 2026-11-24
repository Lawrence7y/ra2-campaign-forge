# -*- coding: utf-8 -*-
r"""_v12v_adv.py -- 复核员对抗性检验（③/④/⑤/⑥）。
A. 用撰写人【没见过】的句子试 _v12_rule.classify_v12 是否给确定答案、答案是否正确；
   重点：否定/禁止语境是否被「判反」——真完成断言被禁令词顺带豁免（放宽），或规定式被误抓。
B. 独立复现撰写人 22/14/4 回归计数（直接 import 其样本数组 + 其 rule，逐条实跑）。
C. 独立复核 9 处命中的 U 内 V2_OVERRIDE 是否全空（防整文子串假象）。
D. 统计 S3 默认 V2 究竟触发频率，核「fail-closed 默认」是否名副其实。
零真机、零采样；只读 rule/样本/两域；sys.dont_write_bytecode 防只读域落 __pycache__。
"""
import sys
sys.dont_write_bytecode = True
import importlib.util
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_v1v2_20261109"
sys.path.insert(0, str(WD))

import _v12_rule as R
import _v12_verify as W

BANS_SLOT = ["已补登", "已填入", "已填", "已代填"]
BANS_TRUTH = ["已填", "已代填", "已提交"]


def all_hits(text):
    """对一句话按两域并集词表找全部命中（token, pos, end）。"""
    toks = sorted(set(BANS_SLOT + BANS_TRUTH), key=len, reverse=True)
    out = []
    for t in toks:
        for m in re.finditer(re.escape(t), text):
            out.append((m.start(), t, m.end()))
    return sorted(out)


def run(text, expect, label, token=None):
    hits = all_hits(text)
    if not hits:
        print("  [%s] NO-HIT  expect=%s  TEXT=%s" % (label, expect, text))
        return None
    results = []
    for pos, t, end in hits:
        if token is not None and t != token:
            continue
        v = R.classify_v12(text, pos, end, t)
        markers = ",".join(v["hard"] + v["weak"]) or v["override"] or "DEFAULT_V2+REVIEW"
        print("  [%s] expect=%-4s got=%-4s %s | review=%-5s | %s"
              % (label, expect, v["verdict"], "OK" if v["verdict"] == expect else "**MISMATCH**",
                 v["review_flag"], markers))
        print("        TEXT : %s" % text)
        print("        UNIT : %r" % v["unit"])
        print("        REASON: %s" % v["reason"][:150])
        results.append((v["verdict"], expect, v["review_flag"], markers))
    return results


print("=" * 100)
print("=== A. 撰写人没见过的新句子（判定是否确定 + 是否正确） ===")
print("--- A1 纯身份陈述/规定式（应放过 V1）---")
NOVEL_V1 = [
    ("NV1-a 疑问式", "请核验者逐行确认 §5.4 排查表：见证槽是否已填？", "V1", "已填"),
    ("NV1-b 禁止式", "核验者不得代填身份值，亦不得视为已填。", "V1", "已填"),
    ("NV1-c 紧邻否定", "该槽尚未已填，按协议走 PARTIAL 档。", "V1", "已填"),
    ("NV1-d 占位定语", "把 <已填件路径> 作为 _c7_selfcheck.py 的参数实跑。", "V1", "已填"),
    ("NV1-e 条件分支", "若 G1 见证已填，则核 D2/D3/D4；否则登记 PARTIAL。", "V1", "已填"),
    ("NV1-f 表格列头", "| 件 | 需什么字段 | 是否已填 | 判定条件 |", "V1", "已填"),
]
for lab, t, e, tok in NOVEL_V1:
    run(t, e, lab, tok)

print("--- A2 纯完成断言（应抓住 V2）---")
NOVEL_V2 = [
    ("NV2-a 已填+值", "三个身份字段已填，reviewerSessionId = sess_dwf-dwfrun-9f31。", "V2", "已填"),
    ("NV2-b 已交付", "本会话已提交 ACCEPTANCE_RECORDS_C07.json，门禁 exit 0。", "V2", "已提交"),
    ("NV2-c 已补登", "台账 :5906 已补登 Q6 责任身份，本件归档完毕。", "V2", "已补登"),
    ("NV2-d 硬性宣称", "现已填三值并过增强门禁，绑定行已落盘。", "V2", "已填"),
]
for lab, t, e, tok in NOVEL_V2:
    run(t, e, lab, tok)

print("--- A3 ★ 否定语境判反探针：真完成断言与无关禁令/否定词同句（逗号不切单元）---")
NEG_TRAPS = [
    ("NT-1 禁令在后", "现已填三值并过门禁，不得再改值。", "V2", "已填"),
    ("NT-2 禁令在前", "核验者不得代填，但三值现已填并已交付。", "V2", "已填"),
    ("NT-3 不代填同句", "本件三值已填，不代填见证槽。", "V2", "已填"),
    ("NT-4 不许事后", "三值已填毕，不许事后改值。", "V2", "已填"),
    ("NT-5 未验残留同句", "三值已填，无未验残留，登记闭合。", "V2", "已填"),
    ("NT-6 非字同句", "三值已填，非计划号，正式任务书编号已落实。", "V2", "已填"),
    ("NT-7 纯禁令（对照）", "不许已填。", "V1", "已填"),
    ("NT-8 纯禁令（对照）", "不得视为已填。", "V1", "已填"),
    ("NT-9 双重否定", "三值并非不已填，回件照录即可。", "V2", "已填"),
]
for lab, t, e, tok in NEG_TRAPS:
    run(t, e, lab, tok)

print("--- A4 ★ 无关行内词触发 HARD_V1（判据是否真按命中局部语境）---")
LINE_TRAPS = [
    ("LT-1 逐字在后", "三值已填，且 reviewerRole 与 PERF:151 内部三角色逐字不同。", "V2", "已填"),
    ("LT-2 先例在后", "三值已填；另附先例件一份供比对。", "V2", "已填"),
    ("LT-3 按字在后", "三值已填，按 NEXT:23 原序写入记录。", "V2", "已填"),
    ("LT-4 或字条件在后", "三值已填，或按判定条件走 PARTIAL 档。", "V2", "已填"),
    ("LT-5 → 在后", "三值已填 → 登记闭合，本件留存。", "V2", "已填"),
]
for lab, t, e, tok in LINE_TRAPS:
    run(t, e, lab, tok)

print("\n" + "=" * 100)
print("=== B. 独立复现撰写人 22/14/4 回归（直接调其 rule + 其样本数组）===")
def reproduce(samples, tag):
    ok = 0
    for sid, text, token, expected, note in samples:
        s = text.find(token)
        v = R.classify_v12(text, s, s + len(token), token)
        good = v["verdict"] == expected
        ok += good
        print("  %-30s expect=%s got=%s %s" % (sid, expected, v["verdict"], "PASS" if good else "FAIL"))
    print("  [%s] %d/%d PASS" % (tag, ok, len(samples)))
    return ok, len(samples)

v1ok, v1n = reproduce(W.V1_SAMPLES, "V1")
v2ok, v2n = reproduce(W.V2_SAMPLES, "V2")

# MIXED 复现（照抄撰写人 run_mixed 的 4 条实句）
print("  [MIXED] 独立复算 4 条")
MIX = [
    ("MIX-01", "是否已填？现已填三值并过门禁。", "V2"),
    ("MIX-02", "填用流程规定应按模板核对，但三值已实算，绑定行已交付。", "V2"),
    ("MIX-03", "若见证槽已填，则查 G1/G2；现已填三值。", "V2"),
    ("MIX-04", "排查表列头「是否已填」；若见证槽已填，则查 G1/G2。", "V1"),
]
mok = 0
for sid, t, exp in MIX:
    cls = [R.classify_v12(t, m.start(), m.end(), "已填")["verdict"]
           for m in re.finditer("已填", t)]
    agg = "V2" if "V2" in cls else "V1"
    good = agg == exp
    mok += good
    print("  %-8s hits=%s agg=%s expect=%s %s" % (sid, cls, agg, exp, "PASS" if good else "FAIL"))
print("  [MIXED] %d/4 PASS" % mok)
print("  [REGRESSION-REPRO] V1 %d/%d ; V2 %d/%d ; MIXED %d/4" % (v1ok, v1n, v2ok, v2n, mok))

print("\n" + "=" * 100)
print("=== C. 9 处真命中：U 内 V2_OVERRIDE 是否全空（独立复算）===")
DOCS = [
    ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md", BANS_SLOT),
    ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md", BANS_TRUTH),
]
tot = 0
for name, path, bans in DOCS:
    text = path.read_bytes().decode("utf-8")
    for tok in bans:
        for m in re.finditer(re.escape(tok), text):
            tot += 1
            v = R.classify_v12(text, m.start(), m.end(), tok)
            in_u = [k for k in R.V2_OVERRIDE if k in v["unit"]]
            L = text.count("\n", 0, m.start()) + 1
            print("  %-32s L%-4d tok=%-6s V12=%s U内V2_OVERRIDE=%r hard=%s"
                  % (name, L, tok, v["verdict"], in_u, v["hard"]))
print("  [C-TOTAL] hits=%d" % tot)

print("\n" + "=" * 100)
print("=== D. S3(DEFAULT_V2+REVIEW) 触发频率：新句子里『判不了』究竟出现几次 ===")
PLAIN = [
    "三个身份字段已填。",
    "三值已填，登记闭合。",
    "本会话已提交登记件。",
    "C07 责任身份已补登。",
    "见证槽已代填，值照录。",
    "两处落笔已补登并复核。",
    "三值已填毕，未验项清零。",
]
n_default = 0
for t in PLAIN:
    for pos, tok, end in all_hits(t):
        v = R.classify_v12(t, pos, end, tok)
        tag = ",".join(v["hard"] + v["weak"]) or v["override"] or "DEFAULT_V2+REVIEW"
        if v["review_flag"]:
            n_default += 1
        print("  %-46s got=%-4s review=%-5s | %s" % (t[:44], v["verdict"], v["review_flag"], tag))
print("  [D] plain-V2 句中走 S3(判不了/默认V2) 的命中 = %d / %d" %
      (n_default, sum(len(all_hits(t)) for t in PLAIN)))
print("[V12V-ADV-END]")
