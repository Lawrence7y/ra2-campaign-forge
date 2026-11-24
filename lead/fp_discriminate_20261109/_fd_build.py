# -*- coding: utf-8 -*-
r"""_fd_build.py — 判别实验执行员：建沙箱副本 + 改版核（甲/乙/甲c/乙2）。只写本任务写域。
纪律：原件零改动（只 copyfile 读源）；改版只落 lead/fp_discriminate_20261109/。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/fp_discriminate_20261109/_fd_build.py
"""
import sys, hashlib, shutil, difflib
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(r"D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "fp_discriminate_20261109"
SB = WD / "_fd_sandbox"
SB.mkdir(parents=True, exist_ok=True)


def sha(p):
    b = Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


SRC_CORE = ROOT / "lead" / "dneg_generative_20261109" / "_dg_core.py"
SRC_G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
DST_CORE = SB / "_dg_core_base.py"
DST_G7 = SB / "_g7_predicates_base.py"

print("=== 0) 沙箱副本（逐字节校验） ===")
shutil.copyfile(SRC_CORE, DST_CORE)
shutil.copyfile(SRC_G7, DST_G7)
for src, dst in ((SRC_CORE, DST_CORE), (SRC_G7, DST_G7)):
    h1, n1 = sha(src)
    h2, n2 = sha(dst)
    ok = (h1 == h2 and n1 == n2)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h1, n1))
    print("  copy %s -> %s : %s" % (src.name, dst.name, "OK" if ok else "MISMATCH"))
    assert ok, "copy mismatch"

base = DST_CORE.read_text(encoding="utf-8")


def apply(txt, old, new, tag):
    cnt = txt.count(old)
    assert cnt == 1, "%s: old-string count = %d (expect 1)" % (tag, cnt)
    return txt.replace(old, new)


# ---------- 公共 old 串（与原件逐字一致） ----------
OLD_BR = r'DG_BREAK_RE = re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另")'
BRK14 = "|其实|说到底|尽管|换言之|与此同时|反倒|结果|终究|总而言之|归根结底|话说回来|退一步说|哪怕|说白了"
NEW_BR = r'DG_BREAK_RE = re.compile(r"[" + _BREAK + r"]|但|但是|然而|不过|却|只是|反之|相反|另外|另' + BRK14 + '")'
OLD_QT = r'DG_QUOTE_RE = re.compile(r"「[^」\n]*」|『[^』\n]*』|“[^”\n]*”|`[^`\n]*`")'
NEW_QT = ("DG_QUOTE_RE = re.compile(r'「[^」\\n]*」|『[^』\\n]*』|“[^”\\n]*”|`[^`\\n]*`"
          "|\"[^\"\\n]*\"|《[^》\\n]*》')")
OLD_MQ = '    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`")):'
NEW_MQ = ('    for op, cl in (("「", "」"), ("『", "』"), ("“", "”"), ("`", "`"),'
          ' (\'"\', \'"\'), ("《", "》")):')
OLD_VETO = '''    hit_text = m.group(0)
    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"
    if DG_SECOND_SUBJ_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含第二主语：两否定不互相支配"}
    if DG_COORD_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含并列标记：两个独立否定项"}'''
NEW_VETO = '''    hit_text = m.group(0)
    tmpl = "T3_split" if m.group("t3") else "T12_adjacent"
    rest = scope[:m.start()] + scope[m.end():]
    if _DG_NEG1_RE.search(rest):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "甲c: hit 链外同窗出现第二否定算子 -> 两否定各自独立"}
    if DG_COORD_RE.search(rest):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "甲c: hit 链外同窗出现并列标记 -> 两个独立否定项"}
    if DG_SECOND_SUBJ_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含第二主语：两否定不互相支配"}
    if DG_COORD_RE.search(hit_text):
        return {"hit": False, "hit_text": hit_text, "template": tmpl, "scope": scope,
                "reason": "命中链内含并列标记：两个独立否定项"}'''
OLD_MQDEF = "def _mask_quotes(s):"
NEW_MQDEF = "_DG_NEG1_RE = re.compile(_alt(NEG1))\n\n\ndef _mask_quotes(s):"

variants = {}

# ---------- (甲) 只补护栏：14 边界词 + ASCII 双引号/书名号 ----------
t = base
t = apply(t, OLD_BR, NEW_BR, "甲 DG_BREAK_RE")
t = apply(t, OLD_QT, NEW_QT, "甲 DG_QUOTE_RE")
t = apply(t, OLD_MQ, NEW_MQ, "甲 _mask_quotes pairs")
variants["_fd_dg_core_jia.py"] = t

# ---------- (甲c) 甲 + 改代码：二次 veto 由只查 hit_text 改为查整窗 ----------
t = variants["_fd_dg_core_jia.py"]
t = apply(t, OLD_VETO, NEW_VETO, "甲c veto 整窗")
t = apply(t, OLD_MQDEF, NEW_MQDEF, "甲c _DG_NEG1_RE")
variants["_fd_dg_core_jiac.py"] = t

# ---------- (乙) 只删构式：NEG1 删 不敢/并不/并非 ----------
t = base
t = apply(t, '    "并非", "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",',
          '    "并不是", "不是", "亦非", "绝不", "决不", "从不", "从未",', "乙 删并非")
t = apply(t, '    "不能", "不可", "不得", "没有", "不敢", "不会", "不可能", "不该", "不应",',
          '    "不能", "不可", "不得", "没有", "不会", "不可能", "不该", "不应",', "乙 删不敢")
t = apply(t, '    "没法", "无法", "不见得", "不一定", "不否认", "并不",',
          '    "没法", "无法", "不见得", "不一定", "不否认",', "乙 删并不")
variants["_fd_dg_core_yi.py"] = t

# ---------- (乙2) 敏感性：改删 NEG2 的 否认/不承认 ----------
t = base
t = apply(t, '    "否认", "不承认", "不认为", "不宣告", "不出现",',
          '    "不认为", "不宣告", "不出现",', "乙2 删否认/不承认")
variants["_fd_dg_core_yi2.py"] = t

print("\n=== 1) 改版核落盘 + 绑定行 + diff 摘要 ===")
difflines = []
for name, txt in variants.items():
    p = WD / name
    p.write_text(txt, encoding="utf-8", newline="")
    h, n = sha(p)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h, n))
    print("  %s  (lines %d)" % (name, txt.count("\n") + 1))
    diff = list(difflib.unified_diff(base.splitlines(), txt.splitlines(),
                                     "_dg_core_base", name, lineterm="", n=1))
    difflines.append("\n".join(diff))
(WD / "_fd_variants_diff.txt").write_text("\n\n".join(difflines), encoding="utf-8")
print("  diff -> _fd_variants_diff.txt (%d chars)" % sum(len(d) for d in difflines))

print("\n=== 2) 改版核自检：NEG1/NEG2 删词与 BREAK/QUOTE 词数 ===")
import types
def load(name, path):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(Path(path).read_text(encoding="utf-8"), str(path), "exec"), m.__dict__)
    return m
import re
for name in ["_fd_dg_core_jia.py", "_fd_dg_core_jiac.py", "_fd_dg_core_yi.py", "_fd_dg_core_yi2.py"]:
    m = load("v", WD / name)
    print("%s: n_NEG1=%d n_MID=%d n_NEG2=%d break_extra=%s quote_alt=%s" % (
        name, len(set(m.NEG1)), len(set(m.MID)), len(set(m.NEG2)),
        len(BRK14.split("|")) - 1,
        bool(re.search(r'《', m.DG_QUOTE_RE.pattern))))

print("\n=== 3) 原件复核（构建后） ===")
for f in [SRC_CORE, SRC_G7]:
    h, n = sha(f)
    print("被核对象 SHA256 = %s，字节数 = %d" % (h, n))
