# -*- coding: utf-8 -*-
"""B2b 母本结构勘查探针（只读母本；只写本目录下的 _b2b_probe_out.txt）。

用途：把 qc151_trip.py 中与 B2b 改动相关的函数、行号、调用点、早退路径
逐项实测打印。每项给「行号 + 该行原文（截断到 120 字符）」。
运行：python -I -X utf8 <本文件绝对路径>
"""
import ast
import hashlib
from pathlib import Path

MOTHER = Path(
    r"D:\Project\ra2-campaign-forge\out\re_work\work_chain"
    r"\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"
)
OUT = Path(
    r"D:\Project\ra2-campaign-forge\lead\b2b_design_20261106"
    r"\_b2b_probe_out.txt"
)
WIDTH = 120

_lines: list[str] = []


def emit(s: str = "") -> None:
    _lines.append(s)


def txt(n: int) -> str:
    """1-based 行号；原文超过 120 字符则截断到 120 字符。"""
    if not (1 <= n <= len(LINES)):
        return f"{n}: <行号越界/未找到>"
    s = LINES[n - 1]
    return f"{n}: {s[:WIDTH]}"


def pr(n: int, label: str = "") -> None:
    emit(f"  {label}{txt(n)}" if label else f"  {txt(n)}")


def pr_range(a: int, b: int, label: str = "") -> None:
    if label:
        emit(f"  {label}")
    for n in range(a, b + 1):
        pr(n)


def func(name: str, tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def ann(node) -> str:
    return ast.unparse(node) if node is not None else ""


def signature(fd: ast.FunctionDef) -> str:
    a = fd.args
    defaults: list = [None] * (len(a.args) - len(a.defaults)) + list(a.defaults)
    parts = []
    for arg, d in zip(a.args, defaults):
        s = arg.arg
        if arg.annotation is not None:
            s += ": " + ann(arg.annotation)
        if d is not None:
            s += " = " + ast.unparse(d)
        parts.append(s)
    return (f"{fd.name}({', '.join(parts)}) -> {ann(fd.returns)}"
            if fd.returns is not None else f"{fd.name}({', '.join(parts)})")


def top_level_returns(fd: ast.FunctionDef) -> list[int]:
    """main 顶层 return（跳过嵌套函数/类/lambda）。"""
    out: list[int] = []

    def walk(node) -> None:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(ch, ast.Return):
                out.append(ch.lineno)
            walk(ch)

    walk(fd)
    return sorted(out)


def main() -> None:
    global LINES
    blob = MOTHER.read_bytes()
    sha = hashlib.sha256(blob).hexdigest()
    text = blob.decode("utf-8")
    LINES = text.splitlines()
    tree = ast.parse(text)

    emit("=" * 88)
    emit("B2b 母本结构勘查探针输出")
    emit("=" * 88)
    emit(f"母本: {MOTHER}")
    emit(f"实算 sha256: {sha}")
    emit(f"实算字节数: {len(blob)}")
    emit(f"实算行数 (splitlines): {len(LINES)}")
    emit(f"探针运行命令: python -I -X utf8 {Path(__file__).resolve()}")
    emit("")

    # ---------------------------------------------------------------- 1
    emit("[1] def finalize_trip( 完整签名 + 行号")
    ft = func("finalize_trip", tree)
    if ft is None:
        emit("  未找到")
    else:
        emit(f"  def 行号: {ft.lineno}  (函数范围 {ft.lineno}..{ft.end_lineno})")
        pr_range(ft.lineno, 5909, "  签名原文（5900-5909）:")
        emit(f"  AST 签名: {signature(ft)}")
        a = ft.args
        emit(f"  形参个数: {len(a.args)}")
        defaults = [None] * (len(a.args) - len(a.defaults)) + list(a.defaults)
        for arg, d in zip(a.args, defaults):
            emit(f"    - {arg.arg}: 行号 {arg.lineno}, 注解 "
                 f"{ann(arg.annotation) or '<无>'}, 缺省 "
                 f"{ast.unparse(d) if d is not None else '<无（必填）>'}")
    emit("")

    # ---------------------------------------------------------------- 2
    emit("[2] def copy_post_except_evidence( 签名 / 函数体范围 / 行号")
    ce = func("copy_post_except_evidence", tree)
    if ce is None:
        emit("  未找到")
    else:
        emit(f"  def 行号: {ce.lineno}; 函数整体范围: {ce.lineno}..{ce.end_lineno}")
        emit(f"  函数体首语句(docstring)行号: {ce.body[0].lineno}; "
             f"末语句行号: {ce.body[-1].end_lineno}")
        pr_range(4561, 4562, "  签名原文（4561-4562）:")
        emit(f"  AST 签名: {signature(ce)}")
        pr(ce.end_lineno, "  函数末行: ")
    emit("")

    # ---------------------------------------------------------------- 3
    emit("[3] copy_post_except_evidence( 在母本里的所有出现 / 所有调用点")
    emit("  (A) 文本出现（含 def 与调用）:")
    for i, s in enumerate(LINES, 1):
        if "copy_post_except_evidence(" in s:
            pr(i, "")
    emit("  (B) AST 调用点（func 为 Name/Attribute 且名字匹配）:")
    calls = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else "")
            if nm == "copy_post_except_evidence":
                calls.append(n)
    emit(f"  AST 调用点个数: {len(calls)}")
    for c in calls:
        pr(c.lineno, "  调用行: ")
        emit(f"    实参: {[ast.unparse(x) for x in c.args]}")
        emit(f"    关键字实参: {[(k.arg, ast.unparse(k.value)) for k in c.keywords]}")
    pr(5938, "  调用点上一行（5938）: ")
    pr(5939, "  调用点本行（5939）: ")
    emit("")

    # ---------------------------------------------------------------- 4
    emit("[4] def main( 行号；bak = backup_carrier( 行号")
    mn = func("main", tree)
    if mn is None:
        emit("  未找到")
    else:
        emit(f"  def main( 行号: {mn.lineno}  (函数范围 {mn.lineno}..{mn.end_lineno})")
        pr(mn.lineno)
    bak_line = [i for i, s in enumerate(LINES, 1) if "bak = backup_carrier(" in s]
    emit(f"  bak = backup_carrier( 行号: {bak_line}")
    for n in bak_line:
        pr(n)
    emit("")

    # ---------------------------------------------------------------- 5
    emit("[5] main 内所有 return 行号，标出早于 6387 的")
    if mn is None:
        emit("  未找到")
    else:
        rets = top_level_returns(mn)
        emit(f"  main 顶层 return 总数: {len(rets)}; 行号: {rets}")
        for n in rets:
            flag = "早于 6387" if n < 6387 else "不早于 6387"
            pr(n, f"  [{flag}] ")
    emit("")

    # ---------------------------------------------------------------- 6
    emit("[6] 那个 try: / except BaseException / finally: / finalize_trip( 调用")
    big = None
    for n in ast.walk(mn) if mn else []:
        if isinstance(n, ast.Try) and n.lineno == 6313:
            big = n
            break
    if big is None:
        emit("  try(6313) 未找到")
    else:
        emit(f"  try: 行号: {big.lineno} (AST Try 范围 {big.lineno}..{big.end_lineno})")
        pr(6313)
        emit(f"  except 行号(AST handler): {[h.lineno for h in big.handlers]}")
        for h in big.handlers:
            pr(h.lineno)
        fin_lines = [i for i, s in enumerate(LINES, 1)
                     if s.strip() == "finally:" and 7000 <= i <= 7050]
        emit(f"  finally: 关键字行号(文本精确匹配): {fin_lines}")
        for n in fin_lines:
            pr(n)
        emit("  finalize_trip( 调用行(AST Call):")
    fcalls = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "finalize_trip":
            fcalls.append(n.lineno)
    emit(f"  finalize_trip( AST 调用行号: {fcalls}")
    for n in sorted(set(fcalls)):
        pr(n)
    pr_range(7117, 7125, "  调用语句整体（7117-7125）:")
    emit("  注: 7149 为 docstring 中的文字 'finalize_trip()'，非调用:")
    pr(7149)
    emit("")

    # ---------------------------------------------------------------- 7
    emit("[7] def backup_carrier( 行号；bak[name] 写入的键")
    bc = func("backup_carrier", tree)
    if bc is None:
        emit("  未找到")
    else:
        emit(f"  def 行号: {bc.lineno}  (函数范围 {bc.lineno}..{bc.end_lineno})")
        pr(4447)
        emit(f"  AST 签名: {signature(bc)}")
    emit("  bak[...] 赋值语句（AST Subscript 赋值）:")
    bassigns = []
    for n in ast.walk(bc) if bc else []:
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tgts = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in tgts:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) \
                        and t.value.id == "bak":
                    bassigns.append((n.lineno, n))
    for n, node in bassigns:
        pr(n, "  赋值行: ")
        if isinstance(node.value, ast.Dict):
            keys = [ast.unparse(k) for k in node.value.keys]
            emit(f"    写入 bak[name] 的字典键: {keys}")
            for k in node.value.keys:
                emit(f"      - 键 {ast.unparse(k)} (行号 {k.lineno})")
    pr_range(4451, 4451, "  for name in CARRIER_FILES 行: ")
    pr_range(213, 214, "  CARRIER_FILES 定义（name 的取值范围）: ")
    emit("")

    # ---------------------------------------------------------------- 8
    emit("[8] except_set_diff 行号范围 / 禁止 sha 判 crash 原文 / 影响退出码的行")
    es = func("except_set_diff", tree)
    if es is None:
        emit("  未找到")
    else:
        emit(f"  def 行号: {es.lineno}; 函数范围: {es.lineno}..{es.end_lineno}")
        pr(672, "  首行: ")
        pr(es.end_lineno, "  末行: ")
    emit("  禁止用 sha 变化判 crash 的那一行:")
    pr(677)
    emit("  集合差结果里与判定相关的键（700-705）:")
    pr_range(700, 705)
    emit("  影响退出码的代码块（5984-5990；TASK.md:74 记 5985-5990 为唯一影响退出码处）:")
    pr_range(5984, 5990)
    emit("  except_set_diff( 调用行与收尾项登记行:")
    for i, s in enumerate(LINES, 1):
        if "except_set_diff(" in s and not s.lstrip().startswith("def "):
            pr(i, "  出现: ")
    pr(6045, "  收尾项登记: ")
    emit("")

    # ---------------------------------------------------------------- 9
    emit("[9] info = { 字典完整字面量（逐键）与 rec.add( 的 group")
    info_nodes = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "info" for t in n.targets) \
                and isinstance(n.value, ast.Dict):
            info_nodes.append(n)
    emit(f"  info = {{...}} 赋值个数: {len(info_nodes)}")
    for n in info_nodes:
        emit(f"  赋值行号: {n.lineno}..{n.end_lineno}")
        pr_range(n.lineno, n.end_lineno, "  字面量原文:")
        emit(f"  键（AST，共 {len(n.value.keys)} 个）: "
             f"{[ast.unparse(k) for k in n.value.keys]}")
        for k in n.value.keys:
            emit(f"    - {ast.unparse(k)}  (行号 {k.lineno})")
    emit("  把 info 写进 Recorder 的 rec.add 调用:")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "add" and any(
                    isinstance(x, ast.Name) and x.id == "info" for x in n.args):
            emit(f"    调用行号: {n.lineno}; group 实参: "
                 f"{ast.unparse(n.args[0])}; key 实参: {ast.unparse(n.args[1])}")
            pr_range(n.lineno, n.end_lineno, "    调用原文:")
    emit("")

    # ---------------------------------------------------------------- 10
    emit("[10] Recorder.add( 方法行号与参数签名")
    cls = None
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == "Recorder":
            cls = n
            break
    if cls is None:
        emit("  Recorder 类未找到")
    else:
        emit(f"  class Recorder 行号: {cls.lineno}")
        ad = None
        for n in cls.body:
            if isinstance(n, ast.FunctionDef) and n.name == "add":
                ad = n
                break
        if ad is None:
            emit("  add 方法未找到")
        else:
            emit(f"  def add( 行号: {ad.lineno} (范围 {ad.lineno}..{ad.end_lineno})")
            pr(ad.lineno, "  签名原文: ")
            emit(f"  AST 签名: {signature(ad)}")
            a = ad.args
            defaults = [None] * (len(a.args) - len(a.defaults)) + list(a.defaults)
            for arg, d in zip(a.args, defaults):
                emit(f"    - {arg.arg}: 注解 {ann(arg.annotation) or '<无>'}, 缺省 "
                     f"{ast.unparse(d) if d is not None else '<无（必填）>'}")
            pr_range(447, 450, "  方法体:")
    emit("")
    emit("=" * 88)
    emit("探针结束。所有行号均为 1-based；原文按 120 字符截断。")
    emit("=" * 88)

    OUT.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print("\n".join(_lines))
    print(f"\n[PROBE] 输出已写入: {OUT}")
    print(f"[PROBE] 输出行数: {len(_lines)}")


if __name__ == "__main__":
    main()
