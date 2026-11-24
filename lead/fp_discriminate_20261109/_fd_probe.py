# -*- coding: utf-8 -*-
r"""_fd_probe.py — 定点复核：(i) 甲 对 P11/P12 为何补了引号仍不消；
(ii) 4 类引号歧义是否改变结论；(iii) 交付形态 guard 缺失（co_names）；
(iv) veto 作用域变体对 P09/P10 的逐条作用域文本。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_probe.py
"""
import sys, importlib.util, pathlib, json
sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
SRC_G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]
P11 = '"并非不宣告已生效"只是引文，本件不采信该说法'
P12 = '《并不否认已生效》只是引文，本件不采信该说法'
P09 = '旧稿并不否认与监理方不宣告已生效'
P10 = '本件不承认或并不否认已生效'

print("=== (i) P11/P12: 补词表后 _mask_quotes / _scope / DG_DROPIN_RE 逐层 ===")
for label, fn in [("原版", "_fd_dg_core_orig.py"), ("(甲)只补数据", "_fd_dg_core_jia.py"),
                  ("(甲4)+4类引号", "_fd_dg_core_jia4.py"), ("(甲Q)+改_mask_quotes", "_fd_dg_core_jiaQ.py")]:
    DG = load("_fd_probe_" + fn.replace(".py", ""), WD / fn)
    for cid, text in [("P11", P11), ("P12", P12)]:
        tok = next(t for t in TOKS if t in text)
        m = __import__("re").search(__import__("re").escape(tok), text)
        pre = text[:m.start()]
        masked = DG._mask_quotes(pre)
        scope = DG._scope(masked)
        mm = DG.DG_DROPIN_RE.search(scope)
        p, h = DG.dg_scan(text, [tok])
        print("  %-18s %s | pre=%r" % (label, cid, pre))
        print("      QUOTE_RE.search(pre)=%-5s masked=%r scope=%r" %
              (bool(DG.DG_QUOTE_RE.search(pre)), masked, scope))
        print("      DG_DROPIN_RE.search(scope)=%r  dg_scan=%s" % (mm.group(0) if mm else "", "CATCH" if p else "PASS"))

print("\n=== (ii) 4 类引号歧义：甲(2类) vs 甲4(4类) 在 7 fp 上逐条 verdict ===")
A = load("_fd_probe_A", WD / "_fd_dg_core_jia.py")
B = load("_fd_probe_B", WD / "_fd_dg_core_jia4.py")
CASES = [("P06", "前稿不敢不承认其实本件不宣告已生效"), ("P07", "前稿不敢不承认说到底本件不宣告已生效"),
         ("P08", "旧稿并不否认尽管本件不宣告已生效"), ("P09", P09), ("P10", P10),
         ("P11", P11), ("P12", P12)]
same = True
for cid, text in CASES:
    va = "CATCH" if A.dg_scan(text, ["已生效"])[0] else "PASS"
    vb = "CATCH" if B.dg_scan(text, ["已生效"])[0] else "PASS"
    same &= (va == vb)
    print("  %-4s 甲=%-5s 甲4=%-5s 同=%s" % (cid, va, vb, va == vb))
print("  [verdict] 7 fp 上 甲 与 甲4 逐条全同 =", same, "⇒ 「4 类引号」歧义不改变本实验 E2 结论")

print("\n=== (iii) 交付形态 guard 缺失（不执行原件，仅静态 co_names + 源码行）===")
G7 = load("_fd_probe_g7", SRC_G7)
guards = ["dg_double_neg", "_mask_quotes", "_scope", "DG_SECOND_SUBJ_RE",
          "DG_COORD_RE", "DG_QUOTE_RE", "DG_BREAK_RE"]
for fnname in ["r10_context", "r12_scan"]:
    co = getattr(G7, fnname).__code__.co_names
    print("  %-12s " % fnname + " ".join("%s=%s" % (g, g in co) for g in guards))
lines = SRC_G7.read_text(encoding="utf-8").splitlines()
for ln in [76, 92, 144]:
    print("  _g7_predicates.py:%d | %s" % (ln, lines[ln - 1]))
dneg = (ROOT / "lead/dneg_generative_20261109/DNEG_GENERATIVE.md").read_text(encoding="utf-8").splitlines()
print("  DNEG_GENERATIVE.md:173 | " + dneg[172])

print("\n=== (iv) P09/P10 veto 作用域文本（原版 hit_text vs 各候选 zone）===")
DG0 = load("_fd_probe_orig2", WD / "_fd_dg_core_orig.py")
for cid, text in [("P09", P09), ("P10", P10)]:
    tok = next(t for t in TOKS if t in text)
    import re as _re
    m = _re.search(_re.escape(tok), text)
    pre = text[:m.start()]
    masked = DG0._mask_quotes(pre)
    scope = DG0._scope(masked)
    mm = DG0.DG_DROPIN_RE.search(scope)
    print("  %s pre=%r" % (cid, pre))
    print("     scope=%r  hit=%r  m.start=%d m.end=%d" % (scope, mm.group(0), mm.start(), mm.end()))
    print("     hit_text-only zone = %r ; SECOND=%s COORD=%s" %
          (mm.group(0), bool(DG0.DG_SECOND_SUBJ_RE.search(mm.group(0))), bool(DG0.DG_COORD_RE.search(mm.group(0)))))
    print("     whole-scope zone   = %r ; SECOND=%s COORD=%s" %
          (scope, bool(DG0.DG_SECOND_SUBJ_RE.search(scope)), bool(DG0.DG_COORD_RE.search(scope))))
    print("     N2-tail zone       = %r ; SECOND=%s COORD=%s" %
          (scope[mm.end():], bool(DG0.DG_SECOND_SUBJ_RE.search(scope[mm.end():])), bool(DG0.DG_COORD_RE.search(scope[mm.end():]))))
    print("     before-hit zone    = %r ; SECOND=%s COORD=%s" %
          (scope[:mm.start()], bool(DG0.DG_SECOND_SUBJ_RE.search(scope[:mm.start()])), bool(DG0.DG_COORD_RE.search(scope[:mm.start()]))))
    print("     含「监理方」=%s 含「与」=%s 含「或」=%s 含「本件」=%s" %
          ("监理方" in scope, "与" in scope, "或" in scope, "本件" in scope))

print("\n=== (v) 4 类未登记引号：DG_ADVERSARIAL.md:184 原文 ===")
dg = (ROOT / "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md").read_text(encoding="utf-8").splitlines()
for ln in [181, 184, 185]:
    print("  DG_ADVERSARIAL.md:%d | %s" % (ln, dg[ln - 1]))
print("  FP_PATTERN_ANALYSIS.md:104 | " +
      (ROOT / "lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md").read_text(encoding="utf-8").splitlines()[103])
