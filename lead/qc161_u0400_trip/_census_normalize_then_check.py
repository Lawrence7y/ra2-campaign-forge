#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§412 全仓普查：`先归一化、后判上溯` 同类缺陷有几处。

为什么必做：§410–§411 在 `_vk_io.py` 找到「先 realpath(abspath()) 把上溯分量
折叠掉、之后再判 `..` ⇒ 恒假死条件」这一缺陷。按既有纪律，
**修一处必须全仓搜同类**——否则只修当场文件，缺陷会在别处以同族复现。

判据（不靠单行 grep，避免注释/字符串误命中）：
  同一函数体内，若「含归一化算子（realpath/abspath/resolve）的赋值」
  出现在「含上溯/前缀校验的行」**之前**，且校验对象是归一化后的值
  ⇒ 标记为可疑（SUSPECT）。
  若校验在归一化之前，或使用 commonpath 前缀法 ⇒ OK。

复跑：python lead/qc161_u0400_trip/_census_normalize_then_check.py
退出码：0 = 普查完成（不表示零缺陷）。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {".git", ".mimosa", "__pycache__", "node_modules"}

# ★ 不用 rglob 全树扫：本仓 lead/ 下有数百 GB 的证据目录（既有记忆已记），
#   全树遍历会挂死。改为「git 索引里已跟踪的 .py」——这正是仓库真正的内容面，
#   未跟踪的临时目录不在其中，也符合「查仓库代码」的本意。
def tracked_py() -> list[Path]:
    import subprocess
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=str(ROOT),
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=120)
    return [ROOT / x for x in out.stdout.splitlines() if x.strip()]

NORM_FUNCS = {"realpath", "abspath", "resolve"}


def norm_targets(node: ast.AST) -> set[str]:
    """该表达式里出现的归一化算子的**实参变量名**。"""
    out: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else "")
            if name in NORM_FUNCS:
                for a in n.args:
                    if isinstance(a, ast.Name):
                        out.add(a.id)
    return out


def has_norm_call(node: ast.AST) -> bool:
    """该表达式是否**直接调用了**归一化算子（不论实参形态）。"""
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else "")
            if name in NORM_FUNCS:
                return True
    return False


def is_upward_check(node: ast.AST) -> tuple[str, bool]:
    """判该语句的**校验语义**，返回 (类别, 是否安全形式)。

    ★★ 关键区分（本轮实测踩到的坑）：归一化之后有两种检查，性质相反：

      (A) 检查「上溯**分量**是否还在」 —— 归一化已把分量折叠掉 ⇒ **恒假死条件**。
          `if ".." in parts:`（parts 来自已归一化值）
          ⇒ DEAD。

      (B) 检查「归一化后的路径是否**仍落在基目录内**」 —— 这是**正确**做法：
          先归一化再用 startswith/commonpath 判包含，正是防穿越的标准写法。
          `if not str(resolved).startswith(str(base)):`
          ⇒ VALID（顺序对了才安全）。

    初版把两类都算成「可疑」，于是 8 处 `check_carrier_boundary` 与
    `extract_mix` 的正确前缀校验被误报，而 `_vk_io` 的真死条件混在同一堆里。
    ⇒ 判据必须落在「检查的语义」上，不能落在「检查的形状」上。
    """
    src = ast.unparse(node)
    if "commonpath" in src:
        return "VALID", True
    has_dotdot = ("'..'" in src) or ('".."' in src)
    has_prefix = "startswith" in src
    if has_dotdot:
        # 判「分量是否还在」⇒ 归一化后恒假
        return "DEAD", False
    if has_prefix:
        # 判「是否在基目录内」⇒ 正确顺序
        return "VALID", True
    return "OTHER", False


def scan_func(fn: ast.AST) -> list[str]:
    """返回该函数内的可疑行说明。

    ★ 必须做**一跳污点传播**：`_vk_io` 的形态是
        p = realpath(abspath(raw))      ← 归一化，写进 p
        parts = p.replace(...).split()  ← p 派生出 parts
        if ".." in parts:               ← 校验 parts
      只看「校验变量==归一化目标」会漏掉 `parts`（它不是 p）⇒ 判据假绿。
      故：归一化目标集合 T 先算出，再把「由 T 中变量直接派生出的变量」并入 T。
    """
    stmts = [n for n in fn.body if isinstance(n, ast.stmt)]
    tainted: dict[str, int] = {}
    for st in stmts:
        if not isinstance(st, (ast.Assign, ast.AnnAssign)) or st.value is None:
            continue
        tgts = ([t.id for t in st.targets if isinstance(t, ast.Name)]
                if isinstance(st, ast.Assign)
                else ([st.target.id] if isinstance(st.target, ast.Name) else []))
        if not tgts:
            continue
        if has_norm_call(st.value):
            for t in tgts:
                tainted.setdefault(t, st.lineno)
            continue
        # 一跳派生：源表达式中引用了已污染变量 ⇒ 结果也污染
        names = {n.id for n in ast.walk(st.value) if isinstance(n, ast.Name)}
        src_lines = [tainted[v] for v in names if v in tainted]
        if src_lines:
            for t in tgts:
                tainted.setdefault(t, min(src_lines))
    if not tainted:
        return []

    out = []
    for st in stmts:
        cat, safe = is_upward_check(st)
        if cat != "DEAD" or safe:
            continue
        names = {n.id for n in ast.walk(st) if isinstance(n, ast.Name)}
        for v, ln in tainted.items():
            if v in names and st.lineno > ln:
                out.append("L%d 校验 `%s` 的**上溯分量是否还在**，"
                           "但其来源已于 L%d 归一化 ⇒ 分量已被折叠 ⇒ 判断恒假"
                           % (st.lineno, v, ln))
                break
    return out


def main() -> int:
    print("=" * 92)
    print("§412 全仓普查：`先归一化、后判上溯` 同类缺陷")
    print("=" * 92)

    n_files = 0
    suspect_files = 0
    safe_files = 0
    rows: list[tuple[str, str, str]] = []

    for p in sorted(tracked_py()):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not p.is_file():
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        n_files += 1
        found = []
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for msg in scan_func(n):
                    found.append((n.name, msg))
        if found:
            suspect_files += 1
            for name, msg in found:
                rows.append((str(rel), name, msg))
                print("  ★ %-52s %s()" % (str(rel), name))
                print("      %s" % msg)

    print("\n[汇总]")
    print("  扫描 .py 文件 = %d" % n_files)
    print("  可疑文件 = %d（可疑点 %d 个）" % (suspect_files, len(rows)))

    # ★★ 阳性对照：判据必须先能抓到已知样本，否则「0 条」毫无意义。
    #   已知样本 = tools/verify_kit/_vk_io.py（§410/§411 已实测的空守卫）。
    known = [r for r in rows if r[0].endswith("verify_kit\\_vk_io.py")
             or r[0].endswith("verify_kit/_vk_io.py")]
    print("\n[阳性对照] 必须抓到已知样本 _vk_io.py")
    if known:
        print("  ✓ 抓到 %d 处 ⇒ 判据有效" % len(known))
    else:
        print("  ✗ **未抓到** ⇒ 判据失效，上面「可疑=N」的数字全部不可信")
        print("    （本轮实测已发生一次：初版无污点传播 ⇒ 漏掉 _vk_io ⇒ 假绿 0 条）")
        return 1

    # 排除本线自己的判定件，它们**故意**在内含坏例
    own = [r for r in rows if r[0].startswith("lead\\qc161_u0400_trip")
           or r[0].startswith("lead/qc161_u0400_trip")]
    print("\n[剔除本线判定件] %d 处（它们故意内含坏例，不计入他线缺陷）"
          % len(own))
    other = [r for r in rows if r not in own]
    print("  剔除后可疑点 = %d 个，涉及文件 %d 个"
          % (len(other), len({r[0] for r in other})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
