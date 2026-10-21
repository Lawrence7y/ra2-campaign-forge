# -*- coding: utf-8 -*-
"""负控：证明 _guard_audit.py 与 _crash_host_structure.py 的 PASS 有判别力。

三段变异，各自必须转红：

  N-1（guard_audit）把已知守卫指令 `cmp ecx, ebx` 的匹配条件破坏
      ⇒ 0x4A8B75 必须从 GUARDED 掉到 UNGUARDED。
      这是最关键的一段：如果 cmp/jcc 匹配写成了 no-op，主脚本仍会全绿，
      而 28/30 这个数字就成了幻觉（§345 已因同类缺陷翻车一次）。

  N-2（guard_audit）把 CRASH 目标改一位 ⇒ 站点数从 30 掉到 0 ⇒
      站点数断言转红。

  N-3（crash_host_structure）把 CRASH 目标改一位 ⇒
      “≥30 个直接 E8 调用者”与“4 宿主都是直接调用者”两条断言转红。

做法：importlib 加载模块 → 改模块级常量/函数 → 直接调 main()。
不启子进程（Mimosa 会把 subprocess 当命令注入拦掉），不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def loadmod(name):
    path = os.path.join(HERE, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, mutate):
    mutate(mod)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = mod.main()
    finally:
        sys.stdout = old
    out = buf.getvalue()
    return rc, out.count("[FAIL]"), out


def m_guard_off(mod):
    """N-1：破坏 cmp/test 匹配 ⇒ 守卫再也识别不出来。"""
    src = mod.analyse
    # 用闭包包一层：把「不匹配任何东西」的哨兵塞进 cmp 分支
    # 最简做法是替换 analyse，让它永不产出 guard_txt。
    def broken(insns, tva, func_of, tb, site_va):
        fs, dv, dt, gt, bt, vd = src(insns, tva, func_of, tb, site_va)
        return fs, dv, dt, "", "", ("UNGUARDED" if dv else "UNKNOWN")
    mod.analyse = broken


def m_target_shift(mod):
    """N-2/N-3：目标改一位 ⇒ 零站点。"""
    mod.CRASH = mod.CRASH + 1


ok = True
cases = []

# N-1
mod = loadmod("_guard_audit")
rc, nf, out = run(mod, m_guard_off)
hit = any("0x4A8B75 判 GUARDED" in l for l in out.splitlines() if "[FAIL]" in l)
print("N-1 guard 匹配置空        rc=%d FAIL=%d 命中目标断言=%s" % (rc, nf, hit))
if rc == 0 or nf == 0 or not hit:
    print("  ★ N-1 未按预期转红（或红在别处）")
    ok = False

# N-2
mod = loadmod("_guard_audit")
rc, nf, out = run(mod, m_target_shift)
hit = any("站点数 == 30" in l for l in out.splitlines() if "[FAIL]" in l)
print("N-2 CRASH 目标偏移        rc=%d FAIL=%d 命中目标断言=%s" % (rc, nf, hit))
if rc == 0 or nf == 0 or not hit:
    print("  ★ N-2 未按预期转红")
    ok = False

# N-3
mod = loadmod("_crash_host_structure")
rc, nf, out = run(mod, m_target_shift)
hit = any("直接 E8 调用者" in l for l in out.splitlines() if "[FAIL]" in l)
print("N-3 宿主结构目标偏移      rc=%d FAIL=%d 命中目标断言=%s" % (rc, nf, hit))
if rc == 0 or nf == 0 or not hit:
    print("  ★ N-3 未按预期转红")
    ok = False

if not ok:
    sys.exit(1)
print("★ 三段负控均按预期转红且命中目标断言")
sys.exit(0)
