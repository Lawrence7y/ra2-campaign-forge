# -*- coding: utf-8 -*-
"""登记前出口 lint —— 只做路由，不含任何判据判定逻辑。

命令行:
    python -I -X utf8 lead/exit_lint_20261110/_el_lint.py <path> [<path> ...]

判据来源:
    D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_criterion.py
    用 importlib.util.spec_from_file_location 动态载入，逐件调用
    analyze_file(abs, rel)。本脚本只把判据返回的 (class, verdict, e, reasons)
    路由成 PASS / REJECT / MANUAL / ERROR，不复制、不重算、不覆盖判据的判定。

stdout 接口:
    每个文件一行: "<verdict> <rel> — <reason>"
    结尾固定一行: "lint: PASS=<n> REJECT=<n> MANUAL=<n> ERROR=<n>"

进程退出码约定（本 lint 的稳定接口）:
    0  全部 PASS
    2  有任何 REJECT（优先于 MANUAL / ERROR）
    3  无 REJECT 但有 MANUAL 或 ERROR

不写任何文件: sys.dont_write_bytecode = True，且全程只有 stdout / stderr 输出。
"""
import sys

sys.dont_write_bytecode = True   # 必须早于动态载入判据，避免落 __pycache__

import importlib.util
import os
import re

CRITERION_PATH = (
    r"D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_criterion.py"
)
REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E_KEYS = ("E0", "E1", "E2", "E3", "E4")
ARTIFACT_NOTE = "登记口径应为产物指纹，不得写 EXIT=0"
SEP = " — "                      # 契约要求的分隔符
_LINE_RE = re.compile(r":(\d+)\b")
_USAGE = ("用法: python -I -X utf8 lead/exit_lint_20261110/_el_lint.py "
          "<path> [<path> ...]")


def load_criterion(path):
    """按契约用 spec_from_file_location 载入判据，返回其 analyze_file。"""
    spec = importlib.util.spec_from_file_location("_el_ec_criterion", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot build spec for criterion: %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.analyze_file


def normalize(arg):
    """→ (绝对路径, 供判据与输出使用的 rel，统一 / 分隔)。"""
    ap = os.path.abspath(arg)
    rel = os.path.relpath(ap, REPO_ROOT) if os.path.isabs(arg) else arg
    return ap, rel.replace("\\", "/")


def one_line(text):
    """保证每个文件只占 stdout 一行；不改动判据语义，只折掉换行。"""
    return str(text).replace("\r", " ").replace("\n", " ").strip()


def failed_e(e):
    """从判据返回的 e 映射里取出非 PASS 的 E 要件（纯格式化，不做判定）。"""
    if not isinstance(e, dict):
        return "(判据未给出 e 映射)"
    bad = ["%s=%s" % (k, e.get(k)) for k in E_KEYS
           if e.get(k) is not None and e.get(k) != "PASS"]
    return ",".join(bad) if bad else "(判据未标记失败 E 要件)"


def first_line_no(reasons):
    """reasons 里出现的第一条行号（按判据给出的顺序）。"""
    if not isinstance(reasons, (list, tuple)):
        return None
    for item in reasons:
        if isinstance(item, (list, tuple)):
            parts = [item[1] if len(item) > 1 else "",
                     item[2] if len(item) > 2 else ""]
        else:
            parts = [item]
        for part in parts:
            m = _LINE_RE.search(str(part))
            if m:
                return m.group(1)
    return None


def route(res):
    """唯一的路由表：判据结果 → (verdict, reason)。"""
    cls = res.get("class")
    vd = res.get("verdict")
    reasons = res.get("reasons", [])

    if cls == "GATE" and vd == "OK":
        return "PASS", ("判据 class=GATE/verdict=OK（四要件状态由判据给出，"
                        "lint 不复核）")
    if cls == "GATE" and vd == "NEEDS_FIX":
        ln = first_line_no(reasons)
        head = ""
        if isinstance(reasons, (list, tuple)) and reasons:
            item = reasons[0]
            if isinstance(item, (list, tuple)) and len(item) > 2:
                head = one_line(item[2])[:120]
        return "REJECT", (
            "判据 class=GATE/verdict=NEEDS_FIX；失败的 E 要件: %s；"
            "reasons 首条行号: %s；reasons[0]=%s"
            % (failed_e(res.get("e")), ln if ln else "无", head or "无"))
    if cls in ("PROBE", "ARTIFACT"):
        return "PASS", ("判据 class=%s/verdict=%s；%s" % (cls, vd, ARTIFACT_NOTE))
    if cls == "UNKNOWN":
        return "MANUAL", ("判据 class=UNKNOWN/verdict=%s ⇒ 逐件人工，"
                          "禁止批量处置" % vd)
    return "MANUAL", ("判据返回未约定组合 class=%r/verdict=%r ⇒ 人工"
                      % (cls, vd))


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    paths = argv[1:]
    counts = {"PASS": 0, "REJECT": 0, "MANUAL": 0, "ERROR": 0}

    if not paths:
        print(_USAGE, file=sys.stderr)
        print("lint: PASS=0 REJECT=0 MANUAL=0 ERROR=0")
        return 3

    try:
        analyze = load_criterion(CRITERION_PATH)
        load_err = None
    except Exception as exc:
        analyze = None
        load_err = "%s: %s" % (type(exc).__name__, one_line(exc))

    for arg in paths:
        ap, rel = normalize(arg)
        if analyze is None:
            verdict, reason = "ERROR", "判据模块载入失败 " + load_err
        else:
            try:
                res = analyze(ap, rel)
                verdict, reason = route(res)
            except Exception as exc:
                verdict = "ERROR"
                reason = "判据抛异常 %s: %s" % (
                    type(exc).__name__, one_line(exc))
        counts[verdict] += 1
        print("%s %s%s%s" % (verdict, rel, SEP, one_line(reason)))

    print("lint: PASS=%d REJECT=%d MANUAL=%d ERROR=%d"
          % (counts["PASS"], counts["REJECT"],
             counts["MANUAL"], counts["ERROR"]))
    if counts["REJECT"]:
        return 2
    if counts["MANUAL"] or counts["ERROR"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
