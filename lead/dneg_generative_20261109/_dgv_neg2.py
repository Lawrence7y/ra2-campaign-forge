# -*- coding: utf-8 -*-
r"""_dgv_neg2.py — ③④ 扩展：30 条自造刁钻负样本，重点找「base=PASS 但 DG=CATCH」的新增误判。
判据：所有句子都是【两个独立否定短语】或【跨微句/引文/转折/第二主语的否定污染】，
    人工逐条给 why，token 落在后一个独立否定短语内，期望 gate=PASS。
三路：base（原十式）/ DG 纯函数 dg_scan / 真实一行替换模块（第二个真实模块实例）。
零真机、零采样；只读既有件；输出只落写域。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_neg2.py
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


BASE = _load("_dgv2_base", G7P)
ONE = _load("_dgv2_one", G7P)
DG = _load("_dgv2_dg", WD / "_dg_core.py")
ONE.DOUBLE_NEG_RE = DG.DG_DROPIN_RE
assert ONE.r10_context.__globals__["DOUBLE_NEG_RE"] is DG.DG_DROPIN_RE

P = _load("_dgv2_P", ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py")
N13 = _load("_dgv2_n13", P.N13_PATH)
T = list(N13.DEFAULT_TOKENS)
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

# 每条：(id, 文本, 为什么是两个独立否定 / 为什么应 PASS)
# 前置构式刻意选【原十式之外、DG 生成式之内】的，才能暴露新增误判。
CASES = [
    ("W01", "旧稿并不否认然而本件不宣告已生效",
     "「旧稿并不否认」是前段独立否定谓语，「本件不宣告」是后段独立否定；转折词「然而」隔开，无标点"),
    ("W02", "旧稿并不否认不过本件不宣告已生效",
     "同上，转折词「不过」；DG_BREAK_RE 含「不过」但 GOVERN 的 BQ 不含"),
    ("W03", "旧稿并不否认却本件不宣告已生效",
     "同上，转折词「却」"),
    ("W04", "旧稿并不否认但本件不宣告已生效",
     "同上，转折词「但」"),
    ("W05", "旧稿并非没有宣告只是本件不宣告已生效",
     "「并非没有宣告」前段独立构式，「只是」后另起单重否定"),
    ("W06", "旧稿未尝不认为反之本件不宣告已生效",
     "「未尝不认为」+ 转折「反之」+ 后段独立否定"),
    ("W07", "旧稿不敢不承认另外本件不宣告已生效",
     "「不敢不承认」+ 「另外」另起一句，无标点"),
    ("W08", "「并不否认」只是引文，本件不采信该说法且已生效未定",
     "DN 在引文内，正文另为独立否定；_mask_quotes 只存在于纯函数，dropin 无此步"),
    ("W09", "「并非没有宣告」只是引文，本件不采信该说法",
     "DN 在引证跨度内；正文「不采信」为独立否定；token 在引文内"),
    ("W10", "并不否认甲方不宣告已生效",
     "「并不否认」与「甲方不宣告」分属两个主语/两个谓语；第二主语「甲方」不在 _SECOND 表"),
    ("W11", "并不否认对方不宣告已生效",
     "第二主语「对方」不在 _SECOND 表"),
    ("W12", "并不否认复核方不宣告已生效",
     "第二主语「复核方」不在 _SECOND 表"),
    ("W13", "并不否认本笔不宣告已生效",
     "第二主语「本笔」在 _SECOND 表内，但 veto 只查 hit_text 不含本笔"),
    ("W14", "并不否认本件不宣告已生效",
     "第二主语「本件」在 _SECOND 表内，veto 只查 hit_text，仍不生效"),
    ("W15", "本件不承认、并不否认均不成立已生效",
     "顿号并列两项独立否定；_scope 只在纯函数里切断，dropin 无"),
    ("W16", "无越权断言：本件不出现「可应用母本…」。",
     "docstring :74-75 原句，两个独立否定短语"),
    ("W17", "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；",
     "CANDIDATE:155 逐字形态"),
    ("W18", "不闻不问，本件已生效。", "「不…不…」并列成语"),
    ("W19", "不卑不亢地说明本件已生效。", "并列成语"),
    ("W20", "非但不宣告已生效，还否认入账。", "伪构式 + 逗号"),
    ("W21", "本件不宣告已生效，但台账已入账。", "转折 + 逗号切断"),
    ("W22", "莫不称快，本件不出现放行 N-5 断言", "前句周遍 DN，后句独立否定"),
    ("W23", "别处不得不承认但本件不宣告已生效", "前段 DN + 后段独立否定（原十式也命中，作对照）"),
    ("W24", "不得不承认旧稿却本件不宣告已生效", "同上，转折词「却」"),
    ("W25", "「并非不宣告已生效」只是引文，本件不采信该说法。", "十式内 DN 在引文（对照）"),
    ("W26", "旧稿并非毫无依据然而本件不宣告已生效", "「并非毫无」+ 转折 + 独立否定"),
    ("W27", "旧稿不会不承认相反本件不宣告已生效", "「不会不」+ 转折「相反」+ 独立否定"),
    ("W28", "旧稿岂能不说反倒本件不宣告已生效", "「岂能不」+ 「反倒」（不在 BREAK 表）+ 独立否定"),
    ("W29", "旧稿不由得不说其实本件不宣告已生效", "「不由得不」+ 「其实」（不在 BREAK 表）+ 独立否定"),
    ("W30", "旧稿没说不登记然而本件不宣告已生效", "「没说不」+ 转折 + 独立否定"),
]


def gate(mod, text, toks):
    r = P.gate_check(text, toks, WD, mod, N13, T)
    adj = [p for p in r["problems"] if p["rule_id"] in ("ADJUDICATED", "NEEDS_HUMAN")]
    return "CATCH" if adj else "PASS"


print("=== ③④ 30 条自造负样本：base / DG纯函数 / 一行替换（期望全 PASS）===")
rows = []
for cid, text, why in CASES:
    toks = [t for t in TOKS if t in text] or ["已生效"]
    b = gate(BASE, text, toks)
    pdg, hdg = DG.dg_scan(text, toks)
    pure = "CATCH" if pdg else "PASS"
    o = gate(ONE, text, toks)
    # 定位命中
    hits = []
    for tok in toks:
        for m in re.finditer(re.escape(tok), text):
            s = max(0, m.start() - BASE.NEG_WINDOW)
            bd = max(text.rfind(c, 0, m.start()) for c in BASE.CLAUSE_BREAK)
            if bd > s: s = bd
            pre = text[s:m.start()]
            h = DG.DG_DROPIN_RE.search(pre)
            if h: hits.append(h.group(0))
    r = {"id": cid, "text": text, "why": why, "base": b, "pure": pure, "oneline": o,
         "pure_hit": hdg[0]["hit"] if hdg else "", "raw_hits": hits[:3]}
    rows.append(r)
    print("  %-4s base=%-5s pure=%-5s oneline=%-5s pure_hit=%-9s raw=%-12s | %s" %
          (cid, b, pure, o, r["pure_hit"][:9], ",".join(r["raw_hits"])[:12], text[:38]))

new_base_dropin = [r["id"] for r in rows if r["base"] == "PASS" and r["oneline"] == "CATCH"]
new_base_pure = [r["id"] for r in rows if r["base"] == "PASS" and r["pure"] == "CATCH"]
print("\n  → base=PASS 且 一行替换=CATCH（新增误判）= %d : %s" % (len(new_base_dropin), new_base_dropin))
print("  → base=PASS 且 DG纯函数=CATCH（新增误判）= %d : %s" % (len(new_base_pure), new_base_pure))
print("  → 一行替换总 CATCH = %d/%d; 纯函数总 CATCH = %d/%d; base 总 CATCH = %d/%d" %
      (sum(r["oneline"] == "CATCH" for r in rows), len(rows),
       sum(r["pure"] == "CATCH" for r in rows), len(rows),
       sum(r["base"] == "CATCH" for r in rows), len(rows)))

# ★ 特别核 docstring 点名的「无越权断言…不出现」家族：把前置构式换成 DG 新增项
print("\n=== ③④-补 「无越权断言…不出现」骨架 × DG 新增构式 ===")
SKELETON = [
    "无越权断言：本件不出现「可应用母本…」。",
    "并无越权断言：审阅回件不出现「可应用母本 / 放行 N-5」类断言；",
    "无越权断言：本件不出现可应用母本。",
    "无越权断言，本件不出现放行 N-5。",
]
for s in SKELETON:
    toks = [t for t in TOKS if t in s]
    print("  base=%-5s pure=%-5s oneline=%-5s | %s" %
          (gate(BASE, s, toks), "CATCH" if DG.dg_scan(s, toks)[0] else "PASS",
           gate(ONE, s, toks), s[:50]))

out = {"cases": rows, "new_fp_dropin": new_base_dropin, "new_fp_pure": new_base_pure,
       "totals": {"oneline_catch": sum(r["oneline"] == "CATCH" for r in rows),
                  "pure_catch": sum(r["pure"] == "CATCH" for r in rows),
                  "base_catch": sum(r["base"] == "CATCH" for r in rows), "n": len(rows)}}
(WD / "_dgv_neg2_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_neg2_out.json")
