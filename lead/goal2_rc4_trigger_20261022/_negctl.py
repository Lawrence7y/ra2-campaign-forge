# -*- coding: utf-8 -*-
"""负控：证明 _window_anchor.py 的 PASS 有真实判别力。

两个变异，各自必须转红：
  N-1 把 EXPECT_WNDPROC 改一位 ⇒ F1 的 lpfnWndProc 断言失败。
  N-2 把索引表整体左移一格 ⇒ 等价于「忘了 msg-1」，F7 的分派语义断言失败。

做法：import 主脚本（sys.exit 只在 __main__ 下触发），
改模块级常量 / 包装 va2off 后调 main()。不启子进程、不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "_window_anchor.py")

src = io.open(MAIN, encoding="utf-8").read()
if "EXPECT_WNDPROC = 0x007775C0" not in src:
    print("★ 主脚本已被改动，负控前提（N-1）失效")
    sys.exit(1)
if "0x00777A98" not in src:
    print("★ 主脚本已无 0x777A98 锚点，负控前提（N-2）失效")
    sys.exit(1)


def run(mutate):
    spec = importlib.util.spec_from_file_location("wan", MAIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
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


def m1(mod):
    mod.EXPECT_WNDPROC = 0x007775C1


def m2(mod):
    real = mod.va2off

    def shifted(secs, va):
        if va == 0x00777A98:
            return real(secs, va) - 1
        return real(secs, va)
    mod.va2off = shifted


ok = True
for name, fn, must in (("N-1 WndProc 改一位", m1, "lpfnWndProc"),
                       ("N-2 索引表左移一格", m2, "WM_CREATE")):
    rc, nfail, out = run(fn)
    hits = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    print("%-22s rc=%d  FAIL=%d" % (name, rc, nfail))
    for l in hits[:3]:
        print("    " + l)
    if rc == 0 or nfail == 0:
        print("  ★ %s 未转红" % name)
        ok = False
    elif not any(must in l for l in hits):
        print("  ★ %s 转红了但没命中 %s（可能红在别处）" % (name, must))
        ok = False

if not ok:
    sys.exit(1)
print("★ 两个负控均按预期转红且命中目标断言")
sys.exit(0)
