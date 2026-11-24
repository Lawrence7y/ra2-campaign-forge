# -*- coding: utf-8 -*-
r"""_fd_probe2.py — E2(d) 加核：P09/P10 到底能否靠「补词表」消，还是必须改代码。
构造 4 个额外写域改版（都基于 甲Q，即已含 14 边界词 + 2 类引号 + _mask_quotes 代码修复）：
  D1 = 甲Q + 把「与」登记进 DG_BREAK_RE（纯数据）
  D2 = 甲Q + 把「监理方」登记进 DG_SECOND_SUBJ_RE（纯数据，veto 仍查 hit_text）
  D3 = 甲Q + veto 查「hit 之前整窗」scope[:m.start()]
  D4 = 甲Q + 「与」进 BREAK + veto 查 hit 之前整窗（P09+P10 一起）
实跑：python -I -X utf8 .../lead/fp_discriminate_20261109/_fd_probe2.py
"""
import sys, importlib.util, pathlib, re, ast
sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SRC_DG = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
SRC_ADV = ROOT / "lead" / "dg_adversarial_20261109" / "_dga_adversarial.py"
dg_src = SRC_DG.read_text(encoding="utf-8")

# 取 甲Q 的 override 尾部（不含原件正文）
jiaq = (WD / "_fd_dg_core_jiaQ.py").read_text(encoding="utf-8")
JQ_OVERRIDE = jiaq[jiaq.index("# ===== _fd_ OVERRIDE"):]

VETO_HEAD = r'''
def dg_double_neg(pre, post=""):
    p = _mask_quotes(pre)
    scope = _scope(p)
    m = DG_DROPIN_RE.search(scope)
    if not m:
        return {"hit": False, "hit_text": "", "template": "", "scope": scope, "reason": "no match"}
    hit_text = m.group(0)
    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"
'''

def mk(name, extra_data, veto_zone=None, label=""):
    L = [JQ_OVERRIDE]
    if extra_data.get("break"):
        L.append("DG_BREAK_RE = _fd_re.compile(DG_BREAK_RE.pattern + '|' + '|'.join(_fd_re.escape(w) for w in " + repr(extra_data["break"]) + "))")
    if extra_data.get("second"):
        L.append("DG_SECOND_SUBJ_RE = _fd_re.compile(DG_SECOND_SUBJ_RE.pattern + '|' + '|'.join(_fd_re.escape(w) for w in " + repr(extra_data["second"]) + "))")
    if veto_zone:
        L.append(VETO_HEAD)
        L.append("    zone = " + veto_zone)
        L.append("    if DG_SECOND_SUBJ_RE.search(zone) or DG_COORD_RE.search(zone):")
        L.append('        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope, "reason": "veto"}')
        L.append('    return {"hit": True, "hit_text": hit_text, "template": tmpl, "scope": scope, "reason": "hit"}')
    body = dg_src + "\n# --- " + label + " ---\n" + "\n".join(L) + "\n"
    (WD / name).write_text(body, encoding="utf-8")
    print("  WROTE", name, label)


mk("_fd_dg_core_D1.py", {"break": ["与"]}, None, "D1 = 甲Q + 「与」进 DG_BREAK_RE（纯数据）")
mk("_fd_dg_core_D2.py", {"second": ["监理方"]}, None, "D2 = 甲Q + 「监理方」进 _SECOND（纯数据，veto 仍查 hit_text）")
mk("_fd_dg_core_D3.py", {}, "scope[:m.start()]", "D3 = 甲Q + veto 查 hit 之前整窗")
mk("_fd_dg_core_D4.py", {"break": ["与"]}, "scope[:m.start()]", "D4 = 甲Q + 「与」进 BREAK + veto 查 hit 之前整窗")
mk("_fd_dg_core_D5.py", {}, "scope[:m.start()] + scope[m.end():]", "D5 = 甲Q + veto 查整窗去掉 hit_text（不补任何词）")
mk("_fd_dg_core_D6.py", {"second": ["监理方"]}, "scope[:m.start()] + scope[m.end():]",
   "D6 = D5 + 「监理方」进 _SECOND")


def load(name, path):
    s = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


tree = ast.parse(SRC_ADV.read_text(encoding="utf-8"))
CASES = next(ast.literal_eval(n.value) for n in tree.body
             if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CASES" for t in n.targets))
TOKS = ["已生效", "已入账", "已追加", "可应用母本", "放行 N-5"]


def score(DG):
    fp, fn = [], []
    for cid, shape, text, exp, why, attack in CASES:
        if exp == "AMBIG":
            continue
        toks = [t for t in TOKS if t in text] or ["已生效"]
        v = "CATCH" if DG.dg_scan(text, toks)[0] else "PASS"
        if exp == "PASS" and v == "CATCH":
            fp.append(cid)
        elif exp == "CATCH" and v == "PASS":
            fn.append(cid)
    return fp, fn


print("\n=== (E2d) D1-D4 与基线对照（41 条全集）===")
for label, fn in [("原版", "_fd_dg_core_orig.py"), ("(甲)只补数据", "_fd_dg_core_jia.py"),
                  ("(甲Q)", "_fd_dg_core_jiaQ.py"), ("D1 +与进BREAK", "_fd_dg_core_D1.py"),
                  ("D2 +监理方进_SECOND", "_fd_dg_core_D2.py"),
                  ("D3 veto查hit前窗", "_fd_dg_core_D3.py"),
                  ("D4 与+BREAK/veto前窗", "_fd_dg_core_D4.py"),
                  ("D5 veto整窗去hit", "_fd_dg_core_D5.py"),
                  ("D6 D5+监理方进_SECOND", "_fd_dg_core_D6.py")]:
    DG = load("_fd_p2_" + fn.replace(".py", ""), WD / fn)
    fp, fn2 = score(DG)
    P09 = "旧稿并不否认与监理方不宣告已生效"
    P10 = "本件不承认或并不否认已生效"
    v9 = "CATCH" if DG.dg_scan(P09, ["已生效"])[0] else "PASS"
    v10 = "CATCH" if DG.dg_scan(P10, ["已生效"])[0] else "PASS"
    print("  %-24s fp=%d fn=%-2d | P09=%-5s P10=%-5s | fp_ids=%s | fn_new=%s" %
          (label, len(fp), len(fn2), v9, v10, fp, [x for x in fn2 if x not in
           ["C01", "C02", "C03", "C04", "C05", "C07", "C08", "C09", "C10", "C11", "C12"]]))
