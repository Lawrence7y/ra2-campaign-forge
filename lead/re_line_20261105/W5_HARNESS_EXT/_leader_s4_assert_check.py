# -*- coding: utf-8 -*-
"""W5 独立核查：扩项副本的 S-4 硬断言在「枚举失败」路径下是否仍成立。

疑点（我读代码时发现）：
  `s4_injection_gate` 的 W5 hook 在 `_s4_injection_gate_mother(...)` 返回**之后**
  才检查 `_W5_STATE["ra2render_hits"] / ["ra2loader_hits"]`。
  而这两个键只在 `s4_scan_names` 被调用时填充（W5EXT s4-scan-hook）。
  母本在 `names is None`（枚举失败）分支**提前 return False**，走不到 `s4_scan_names`。
  ⇒ 该分支下 `_W5_STATE` 两键仍是初始值（需查初始值是什么）。

本脚本只做**静态**检查 + 离线 Python 语义模拟，不运行副本主流程、零真机。
"""
import ast
import io
import os
import re
import sys

P = r'D:/Project/ra2-campaign-forge/lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py'
print("target:", P)
src = io.open(P, encoding='utf-8', errors='replace').read()
lines = src.splitlines()
print("size:", len(src), "lines:", len(lines))

print("\n=== 1. _W5_STATE 的初始定义 ===")
i0 = None
for i, l in enumerate(lines):
    if re.match(r'^_W5_STATE\s*=', l):
        i0 = i
        break
if i0 is None:
    print("  NOT FOUND")
else:
    for j in range(i0, min(i0 + 14, len(lines))):
        print("  %d\t%s" % (j + 1, lines[j][:150]))

print("\n=== 2. _W5_STATE 所有键的写入点 ===")
for i, l in enumerate(lines):
    if '_W5_STATE[' in l and '=' in l and '== ' not in l:
        print("  %d\t%s" % (i + 1, l.strip()[:140]))

print("\n=== 3. s4_scan_names 的调用点（母本体内）===")
for i, l in enumerate(lines):
    if 's4_scan_names(' in l:
        print("  %d\t%s" % (i + 1, l.strip()[:140]))

print("\n=== 4. 枚举失败分支的 return（在 s4_scan_names 调用之前？）===")
# 找 s4_injection_gate 体内 names is None 分支
gate_start = None
for i, l in enumerate(lines):
    if re.match(r'^def s4_injection_gate\(pid: int, rec: Recorder', l):
        gate_start = i
        break
print("  W5 hook 版 s4_injection_gate 起于行", gate_start + 1 if gate_start is not None else None)
# 母本体（被 _s4_injection_gate_mother 别名）里的 names is None
mn = None
for i, l in enumerate(lines):
    if re.match(r'^def s4_injection_gate\(pid: int, rec: Recorder, authorized: bool = False\) -> bool:', l) and i != gate_start:
        mn = i
        break
if mn is None:
    # 母本行号不同，改用 if names is None
    for i, l in enumerate(lines):
        if 'if names is None:' in l:
            mn = i
            print("  找到 'if names is None:' 于行", i + 1)
            break
if mn is not None:
    for j in range(mn, min(mn + 40, len(lines))):
        print("  %d\t%s" % (j + 1, lines[j][:150]))
        if j > mn + 2 and re.match(r'^\s+return False', lines[j]):
            print("  ^^^ 该分支提前 return False")
            break

print("\n=== 5. 结论推导 ===")
init_block = "\n".join(lines[i0:i0 + 14]) if i0 is not None else ""
has_render_init = "ra2render_hits" in init_block
print("  _W5_STATE 初始块是否含 ra2render_hits 键:", has_render_init)
print("  若为 False ⇒ 枚举失败分支下该键**不存在**，")
print("     W5 hook 里 `_W5_STATE.get('ra2render_hits') or []` 得到 []，")
print("     而 `not res`（res=False）会触发 `FAILED_INJECTION_SUSPECTED` 分支 ⇒ **仍然阻断**。")
print("  ⇒ 需确认 hook 用的是 .get() 而不是 [] 索引。")
hook_uses_get = "_W5_STATE.get('ra2render_hits')" in src or '_W5_STATE.get("ra2render_hits")' in src
print("  hook 用 .get() 取值:", hook_uses_get)

print("\n=== 6. 语法与禁止面（副本自身）===")
try:
    ast.parse(src)
    print("  AST parse: OK")
except SyntaxError as e:
    print("  AST parse: FAIL", e)
for api in ("WriteProcessMemory", "CreateRemoteThread", "SuspendThread",
            "MiniDumpWriteDump", "StackWalk", "SetWindowsHookEx"):
    print("  %-20s = %d" % (api, src.count(api)))

print("\n=== 7. flag-off 语义：_W5_STATE['on'] 缺省 ===")
if i0 is not None:
    print("  init 块含 'on':", '"on"' in init_block or "'on'" in init_block)
print("\nDONE")
