# -*- coding: utf-8 -*-
r"""_fd_e1e5.py — 判别实验 E1（2×2 析因）与 E5（负对照扩样）。
零真机 / 零采样；只 re + 静态文本；所有 DG 模块从写域 _fd_*.py 加载（不 import 保护目录）。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_e1e5.py
输出：_fd_e1e5_stdout.txt / _fd_e1e5_out.json
"""
import sys, json, importlib.util, pathlib, hashlib
sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"

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


TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]

def verdict(DG, text):
    toks = [t for t in TOKS if t in text] or ["已生效"]
    p, h = DG.dg_scan(text, toks)
    return "CATCH" if p else "PASS", (h[0]["hit"] if h else "")


DG0 = load("_fd_e1_orig", WD / "_fd_dg_core_orig.py")
DG_JIA = load("_fd_e1_jia", WD / "_fd_dg_core_jia.py")
DG_JIAQ = load("_fd_e1_jiaq", WD / "_fd_dg_core_jiaQ.py")
DG_YI = load("_fd_e1_yi", WD / "_fd_dg_core_yi_full.py")

# ================= 构式与边界词定义 =================
# 表内：5 条，全部由 NEG1/MID/NEG2 闭合表可拼（来自 fp7 命中串 / C15,C16 命中串）
IN_CONSTRUCTS = ["不敢不承认", "并不否认", "并非不宣告", "岂敢不承认", "不由得不承认"]
# 表外：5 条语义等价真 DN，MID 不在 23 项闭合表（对应上游 C01-C05 的构式部分）
OUT_CONSTRUCTS = ["不容不宣告", "未许不宣告", "别想不登记", "甭想不承认", "没准不承认"]
# 已登记边界词：DG_BREAK_RE 10 词里的 5 个（_dg_core.py:89）
REG_WORDS = ["但", "然而", "不过", "另外", "反之"]
# 未登记边界词：14 词表里的 5 个（_ai_verify.py:486-487）
UNREG_WORDS = ["其实", "说到底", "尽管", "换言之", "与此同时"]

P("\n=== (E1-0) 前置校验：表内/表外构式是否真的「可拼 / 不可拼」===")
for c in IN_CONSTRUCTS:
    m = DG0.DG_DROPIN_RE.search(c)
    P("  IN  %-10s 单独 DG_DROPIN_RE.search = %r" % (c, m.group(0) if m else None))
for c in OUT_CONSTRUCTS:
    m = DG0.DG_DROPIN_RE.search(c)
    P("  OUT %-10s 单独 DG_DROPIN_RE.search = %r" % (c, m.group(0) if m else None))
for w in REG_WORDS:
    P("  REG %-6s DG_BREAK_RE.search = %s" % (w, bool(DG0.DG_BREAK_RE.search(w))))
for w in UNREG_WORDS:
    P("  UNREG %-6s DG_BREAK_RE.search = %s" % (w, bool(DG0.DG_BREAK_RE.search(w))))

# ================= E1 2×2 =================
TEMPLATE = "{构式}{边界词}本件不宣告已生效"
CELLS = [
    ("格1_表内x已登记", IN_CONSTRUCTS, REG_WORDS),
    ("格2_表内x未登记", IN_CONSTRUCTS, UNREG_WORDS),
    ("格3_表外x已登记", OUT_CONSTRUCTS, REG_WORDS),
    ("格4_表外x未登记", OUT_CONSTRUCTS, UNREG_WORDS),
]

def build_cell(cons, words):
    rows = []
    for c in cons:
        for w in words:
            rows.append({"construct": c, "boundary": w,
                         "text": c + w + "本件不宣告已生效"})
    return rows


P("\n=== (E1) 2×2 析因：固定模板 %s ；每格 5 构式 × 5 边界词 = 25 条 ===" % TEMPLATE)
e1 = {}
MODS = [("原版", DG0), ("(甲)只补数据", DG_JIA), ("(甲Q)甲+改_mask_quotes", DG_JIAQ),
        ("(乙_full)删全部分解并集", DG_YI)]
for modlabel, MOD in MODS:
    P("  ######## 判定器/改版 = %s ########" % modlabel)
    for cellname, cons, words in CELLS:
        rows = build_cell(cons, words)
        n_catch = 0
        detail = []
        for r in rows:
            v, h = verdict(MOD, r["text"])
            n_catch += (v == "CATCH")
            detail.append({"construct": r["construct"], "boundary": r["boundary"],
                           "text": r["text"], "v": v, "hit": h})
        rate = n_catch / len(rows)
        P("    %-20s n=%d CATCH=%d 率=%.2f ; CATCH 明细=%s" %
          (cellname, len(rows), n_catch, rate,
           [(d["construct"], d["boundary"]) for d in detail if d["v"] == "CATCH"]))
        e1.setdefault(modlabel, {})[cellname] = {"n": len(rows), "catch": n_catch,
                                                  "rate": rate, "rows": detail}
    # 2×2 边缘
    r1 = e1[modlabel]["格1_表内x已登记"]["rate"]
    r2 = e1[modlabel]["格2_表内x未登记"]["rate"]
    r3 = e1[modlabel]["格3_表外x已登记"]["rate"]
    r4 = e1[modlabel]["格4_表外x未登记"]["rate"]
    P("    [2x2] 格1=%.2f 格2=%.2f 格3=%.2f 格4=%.2f" % (r1, r2, r3, r4))
    P("    [判据] 格3/格4 恒 PASS = %s ; 格4 也 CATCH = %s ; 格2 是唯一 CATCH 格 = %s" %
      (r3 == 0 and r4 == 0, r4 > 0, r2 > 0 and r1 == 0 and r3 == 0 and r4 == 0))
    P("    [交互] 表内主效应(未登记边界下)=%.2f ; 表外同条件=%.2f ; 差=%.2f" %
      (r2 - r1, r4 - r3, (r2 - r1) - (r4 - r3)))

# ================= E5 负对照扩样 =================
P("\n=== (E5) 负对照扩样：7 条「表内构式 + 正确切断」（与 fp 组等规模）===")
NEG7 = [
    ("E5-1", "已登记边界词「但」", "前稿不敢不承认但本件不宣告已生效"),
    ("E5-2", "已登记边界词「然而」", "前稿不敢不承认然而本件不宣告已生效"),
    ("E5-3", "已登记边界词「另外」", "旧稿并不否认另外本件不宣告已生效"),
    ("E5-4", "已登记边界词「却」", "旧稿并不否认却本件不宣告已生效"),
    ("E5-5", "正确引号「」", "「并非不宣告已生效」只是引文，本件不采信该说法"),
    ("E5-6", "正确引号『』", "『并不否认已生效』只是引文，本件不采信该说法"),
    ("E5-7", "正确第二主语构造（本件为主语，逗号切断）", "旧稿并不否认，本件不宣告已生效"),
]
e5 = {}
for modlabel, MOD in MODS:
    res = []
    for cid, mech, text in NEG7:
        v, h = verdict(MOD, text)
        res.append({"id": cid, "mech": mech, "text": text, "v": v, "hit": h})
    n_pass = sum(1 for r in res if r["v"] == "PASS")
    P("  %-26s PASS=%d/7 ; 逐条=%s" %
      (modlabel, n_pass, [(r["id"], r["v"], r["hit"]) for r in res]))
    e5[modlabel] = {"n_pass": n_pass, "rows": res}

# E5 附加诊断：第二主语 veto 本身是否可达（无标点的第二主语构造）
P("\n=== (E5-附加) 第二主语 veto 可达性诊断（不计入 7 条）===")
PROBES = [
    ("无标点第二主语", "旧稿并不否认本件不宣告已生效"),
    ("无标点自定义第二主语", "旧稿并不否认与监理方不宣告已生效"),
    ("有标点第二主语", "旧稿并不否认，本件不宣告已生效"),
]
for label, text in PROBES:
    import re as _re
    tok = next(t for t in TOKS if t in text)
    m = _re.search(_re.escape(tok), text)
    pre = text[:m.start()]
    masked = DG0._mask_quotes(pre)
    scope = DG0._scope(masked)
    mm = DG0.DG_DROPIN_RE.search(scope)
    v, h = verdict(DG0, text)
    P("  %-18s v=%-5s hit=%r | hit_text 内 SECOND=%s COORD=%s | 整窗 SECOND=%s COORD=%s" %
      (label, v, h,
       bool(DG0.DG_SECOND_SUBJ_RE.search(mm.group(0))) if mm else None,
       bool(DG0.DG_COORD_RE.search(mm.group(0))) if mm else None,
       bool(DG0.DG_SECOND_SUBJ_RE.search(scope)), bool(DG0.DG_COORD_RE.search(scope))))

# ================= 写盘 =================
out = {"e1": {k: {c: {"n": v["n"], "catch": v["catch"], "rate": v["rate"]} for c, v in d.items()}
              for k, d in e1.items()},
       "e5": e5,
       "in_constructs": IN_CONSTRUCTS, "out_constructs": OUT_CONSTRUCTS,
       "reg_words": REG_WORDS, "unreg_words": UNREG_WORDS,
       "template": TEMPLATE,
       "src_sha256": hashlib.sha256(SRC_DG.read_bytes()).hexdigest()}
(WD / "_fd_e1e5_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
(WD / "_fd_e1e5_stdout.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print("\n[write] _fd_e1e5_stdout.txt lines =", len(out_lines))
