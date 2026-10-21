# -*- coding: utf-8 -*-
"""负控：证明 _dispatch_expand.py 对 [esi+0x555A] 的普查与分派展开有判别力。

两个变异，各自必须转红：
  N-1 把 LATCH 从 0x555A 改成 0x555B ⇒ D6 的置1/清0/判读三组断言应全部落空。
  N-2 把 MSG_HI 从 0x215 改成 0x213 ⇒ 会少掉 msg 0x215 分支，D1 的「恰好 5 个」应失败。

做法：import 主脚本，改模块级常量后调 main()。不启子进程、不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "_dispatch_expand.py")

src = io.open(MAIN, encoding="utf-8").read()
for anchor in ("LATCH = 0x555A", "MSG_HI = 0x215"):
    if anchor not in src:
        print("★ 主脚本缺锚点 %r，负控前提失效" % anchor)
        sys.exit(1)


def run(name, mutate):
    spec = importlib.util.spec_from_file_location("de_" + name, MAIN)
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
    return rc, buf.getvalue()


def m_latch(mod):
    mod.LATCH = 0x555B


def m_msghi(mod):
    mod.MSG_HI = 0x213


ok = True
for name, fn in (("N-1 LATCH 0x555A->0x555B", m_latch),
                 ("N-2 MSG_HI 0x215->0x213", m_msghi)):
    rc, out = run(name.replace(" ", "_"), fn)
    nfail = out.count("[FAIL]")
    hits = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    print("%-26s rc=%d  FAIL=%d" % (name, rc, nfail))
    for l in hits[:4]:
        print("    " + l)
    if rc == 0 or nfail == 0:
        print("  ★ %s 未转红" % name)
        ok = False

if not ok:
    sys.exit(1)
print("★ 两个负控均按预期转红")
sys.exit(0)
