# -*- coding: utf-8 -*-
r"""_h5_patch.py — 在【内存副本】上机械施加 _h5_pasteable.py 的补丁，把修后源码
写到本任务写域的 _h5_v12_patched.py，再以普通模块方式 import；绝不写回
_v12_rule.py、绝不写任何只读件。

用途：第四步(c)(d)(e) 的回归对照（旧 vs 修后）。输出只落本任务写域。
"""
import sys, hashlib, importlib.util
from pathlib import Path

sys.dont_write_bytecode = True          # 防在只读域生成 __pycache__
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RULE_PATH = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
PASTE_PATH = HERE / "_h5_pasteable.py"
PATCHED_OUT = HERE / "_h5_v12_patched.py"
EXPECT_SHA = "15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0"
EXPECT_BYTES = 9148


def _import(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_patched():
    raw = RULE_PATH.read_bytes()
    sha, n = hashlib.sha256(raw).hexdigest(), len(raw)
    if sha != EXPECT_SHA or n != EXPECT_BYTES:
        raise RuntimeError("source fingerprint mismatch: %s/%d" % (sha, n))
    rule_src = raw.decode("utf-8")
    paste_src = PASTE_PATH.read_text(encoding="utf-8")

    # 片段 = _h5_pasteable.py 去掉模块 docstring 之后的全部内容
    first = paste_src.find('"""')
    second = paste_src.find('"""', first + 3)
    snippet = paste_src[second + 3:].lstrip("\n")

    # ---- 四处精确替换 ----
    old1 = """    adj_neg = bool(pre) and (pre[-1] in ADJ_NEG_CHARS or bool(ADJ_NEG_RE.search(pre)))
    prohibit_U = any(k in U_bare for k in PROHIBIT)"""
    new1 = """    gov = h5_govern(pre, post)
    adj_neg = gov["adj_neg"]
    prohibit_U = gov["prohibit_governs"]
    double_neg = gov["double_neg"]"""
    assert rule_src.count(old1) == 1, "replacement 1 anchor not unique"

    old2 = """    if adj_neg or prohibit_U or "无已填" in U:
        hard.append("H5_否定禁止管辖")"""
    new2 = """    if (adj_neg or prohibit_U or "无已填" in U) and not double_neg:
        hard.append("H5_否定禁止管辖")"""
    assert rule_src.count(old2) == 1, "replacement 2 anchor not unique"

    old3 = """    if hard:
        return {"verdict": "V1", "hard": hard, "weak": [], "override": "",
                "unit": U, "line": line, "review_flag": False,
                "reason": "HARD_V1 结构：" + ",".join(hard) + "（完成词不可能充当断言谓语）"}"""
    new3 = """    if double_neg:
        return {"verdict": "V2", "hard": [], "weak": [],
                "override": "H5_DOUBLE_NEG:" + gov["dn_hit"],
                "unit": U, "line": line, "review_flag": False,
                "reason": "H5 双重否定=肯定：管辖前缀内含双重否定构式，完成词为真断言"}
""" + old3
    assert rule_src.count(old3) == 1, "replacement 3 anchor not unique"

    old4 = """    if hit_override and not adj_neg and not prohibit_U:"""
    new4 = """    if hit_override and not adj_neg and not prohibit_U and not double_neg:"""
    assert rule_src.count(old4) == 1, "replacement 4 anchor not unique"

    patched = (rule_src.replace(old1, new1).replace(old2, new2)
               .replace(old3, new3).replace(old4, new4))
    marker = "def classify_v12(text, start, end, token):"
    assert patched.count(marker) == 1, "classify_v12 marker not unique"
    patched = patched.replace(marker, snippet + "\n\n" + marker)

    PATCHED_OUT.write_text(patched, encoding="utf-8")
    mod = _import("_h5_v12_patched", PATCHED_OUT)
    return mod


def verdict_from(r):
    return "PASS" if r["verdict"] == "V1" else "CATCH"


if __name__ == "__main__":
    raw = RULE_PATH.read_bytes()
    print("被核对象 SHA256 = %s，字节数 = %d" % (hashlib.sha256(raw).hexdigest(), len(raw)))
    mod = build_patched()
    p = PATCHED_OUT.read_bytes()
    print("patched source sha256 = %s bytes = %d" % (hashlib.sha256(p).hexdigest(), len(p)))
    print("h5_govern imported =", callable(getattr(mod, "h5_govern", None)),
          " classify_patched =", callable(getattr(mod, "classify_v12", None)))
