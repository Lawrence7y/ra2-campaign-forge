# -*- coding: utf-8 -*-
r"""_fd_setup.py — 判别实验：建沙箱（只读原件 → 写域副本 + 静态改版）。
零真机 / 零采样；只 re + 静态文本；不 import 任何保护目录里的模块。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_setup.py
"""
import sys, hashlib, pathlib
sys.dont_write_bytecode = True

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
SRC_G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

dg_src = SRC_DG.read_text(encoding="utf-8")
g7_src = SRC_G7.read_text(encoding="utf-8")

print("=== (S0) 读入原件 ===")
print("  _dg_core.py  chars=", len(dg_src), "sha256=", hashlib.sha256(SRC_DG.read_bytes()).hexdigest())
print("  _g7_predicates.py chars=", len(g7_src), "sha256=", hashlib.sha256(SRC_G7.read_bytes()).hexdigest())

# ---- 14 个未登记边界词：两处上游，均登记在案（D7）----
BREAK14_A = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "结果", "终究",
             "总而言之", "归根结底", "话说回来", "退一步说", "哪怕", "说白了"]   # _ai_verify.py:486-487
BREAK14_B = ["其实", "说到底", "尽管", "换言之", "与此同时", "反倒", "可", "反倒说",
             "结果", "终究", "总而言之", "归根结底", "话说回来", "退一步说"]   # DG_ADVERSARIAL.md:177

# 未登记引号的 regex 片段（单引号 Python 字面量，双引号是普通字符）
Q_DOUBLE = r'"[^"\n]*"'
Q_BOOK = r'《[^》\n]*》'
Q_PAREN = r'\([^)\n]*\)'
Q_SINGLE = r"'[^'\n]*'"
QUOTE_NEW2 = [Q_DOUBLE, Q_BOOK]
QUOTE_NEW4 = [Q_DOUBLE, Q_BOOK, Q_PAREN, Q_SINGLE]

ORIG_QUOTE_SRC = r'r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`"'


def override(break14, quote_parts, *, extend_mask_loop=False, veto_scope=False,
             veto_n2tail=False, second_extra=(), coord_extra=(), label=""):
    """生成尾部覆盖块。只覆盖模块全局名 / 重定义纯函数；原件正文一字未改。"""
    L = ["# ===== _fd_ OVERRIDE (" + label + ") : 由 _fd_setup.py 生成，原件正文一字未改 =====",
         "import re as _fd_re",
         "_FD_BREAK14 = " + repr(break14),
         "_FD_QUOTE_NEW = " + repr(quote_parts),
         'DG_BREAK_RE = _fd_re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另|" '
         '+ "|".join(_fd_re.escape(w) for w in _FD_BREAK14))',
         'DG_QUOTE_RE = _fd_re.compile(' + ORIG_QUOTE_SRC + ' + "|" + "|".join(_FD_QUOTE_NEW))']
    if second_extra:
        L.append('DG_SECOND_SUBJ_RE = _fd_re.compile(r"(?:" + _SECOND + r")|" '
                 '+ "|".join(_fd_re.escape(w) for w in ' + repr(list(second_extra)) + '))')
    if coord_extra:
        L.append('DG_COORD_RE = _fd_re.compile(r"[/／]|、|或|以及|同时|并且|一是|二是|其一|其二|" '
                 '+ "|".join(_fd_re.escape(w) for w in ' + repr(list(coord_extra)) + '))')
    if extend_mask_loop:
        L += [
            "def _mask_quotes(s):",
            "    def blank(m):",
            "        g = m.group(0)",
            '        return g[0] + " " * (len(g) - 2) + g[-1]',
            "    out = DG_QUOTE_RE.sub(blank, s)",
            '    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`"),',
            '                   (\'"\', \'"\'), ("《", "》")):',
            "        i = out.find(op)",
            "        if i >= 0 and out.find(cl, i + 1) < 0:",
            "            return out[:i + 1]",
            "    return out",
        ]
    if veto_scope or veto_n2tail:
        L += [
            'def dg_double_neg(pre, post=""):',
            "    p = _mask_quotes(pre)",
            "    scope = _scope(p)",
            "    m = DG_DROPIN_RE.search(scope)",
            "    if not m:",
            '        return {"hit": False, "hit_text": "", "template": "", "scope": scope,',
            '                "reason": "scope 内无 N1-M-N2 管辖链"}',
            "    hit_text = m.group(0)",
            '    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"',
        ]
        if veto_scope:
            L.append("    zone = scope")
            L.append('    why2 = "整窗内含第二主语"')
            L.append('    whyc = "整窗内含并列标记"')
        else:
            L.append("    zone = scope[m.end():]")
            L.append('    why2 = "N2 后整窗含第二主语"')
            L.append('    whyc = "N2 后整窗含并列标记"')
        L += [
            "    if DG_SECOND_SUBJ_RE.search(zone):",
            '        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,',
            '                "reason": why2}',
            "    if DG_COORD_RE.search(zone):",
            '        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,',
            '                "reason": whyc}',
            '    return {"hit": True, "hit_text": hit_text, "template": tmpl, "scope": scope,',
            '            "reason": "同微句内 N1 支配 N2"}',
        ]
    return "\n".join(L) + "\n"


def write_variant(name, override_text, note=""):
    body = dg_src + "\n# --- " + note + " ---\n" + override_text
    (WD / name).write_text(body, encoding="utf-8")
    print("  WROTE", name, "chars=", len(body), "note=", note)


(WD / "_fd_dg_core_orig.py").write_text(dg_src, encoding="utf-8")
(WD / "_fd_g7_predicates_orig.py").write_text(g7_src, encoding="utf-8")
print("  WROTE _fd_dg_core_orig.py  (exact copy)")
print("  WROTE _fd_g7_predicates_orig.py (exact copy)")

write_variant("_fd_dg_core_jia.py", override(BREAK14_A, QUOTE_NEW2, label="甲"),
              "甲 = 只补数据：14 未登记边界词 + ASCII 双引号/书名号")
write_variant("_fd_dg_core_jia4.py", override(BREAK14_A, QUOTE_NEW4, label="甲4"),
              "甲4 = 只补数据：14 未登记边界词 + 上游探针的 4 类未登记引号")
write_variant("_fd_dg_core_jiaB.py", override(BREAK14_B, QUOTE_NEW2, label="甲B"),
              "甲B = 只补数据：另一批 14 边界词 + 2 类引号（D7 敏感性）")
write_variant("_fd_dg_core_jiaQ.py", override(BREAK14_A, QUOTE_NEW2, extend_mask_loop=True, label="甲Q"),
              "甲Q = 甲 + 改代码（_mask_quotes 未闭合开界符循环补 2 类）")
write_variant("_fd_dg_core_jiaQV.py",
              override(BREAK14_A, QUOTE_NEW2, extend_mask_loop=True, veto_scope=True, label="甲QV"),
              "甲QV = 甲Q + 改代码（二次 veto 查整窗 scope）")
write_variant("_fd_dg_core_jiaQVD.py",
              override(BREAK14_A, QUOTE_NEW2, extend_mask_loop=True, veto_scope=True,
                       second_extra=("监理方",), coord_extra=("与",), label="甲QVD"),
              "甲QVD = 甲QV + 补数据（监理方→_SECOND、与→DG_COORD_RE）")
write_variant("_fd_dg_core_jiaQVN.py",
              override(BREAK14_A, QUOTE_NEW2, extend_mask_loop=True, veto_n2tail=True, label="甲QVN"),
              "甲QVN = 甲Q + veto 改查 N2 后整窗（不是 whole-scope）")

print("=== (S1) 沙箱静态改版建立完成 ===")
