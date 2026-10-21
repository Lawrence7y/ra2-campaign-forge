# -*- coding: utf-8 -*-
"""负控：把 EXPECT_WNDPROC 改错一位，断言必须转红。

用途：证明 _window_anchor.py 的 PASS 有真实判别力，而不是恒绿。
做法：import 主脚本（其 `sys.exit` 只在 __main__ 下触发），
monkeypatch 掉模块级常量后调 main()，看返回值与 FAIL 计数。
全程不启动任何子进程、不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "_window_anchor.py")

src = io.open(MAIN, encoding="utf-8").read()
if "EXPECT_WNDPROC = 0x007775C0" not in src:
    print("★ 主脚本已被改动，负控前提失效")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("wa_neg", MAIN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.EXPECT_WNDPROC = 0x007775C1      # 只改这一位

buf = io.StringIO()
old = sys.stdout
sys.stdout = buf
try:
    rc = mod.main()
finally:
    sys.stdout = old

out = buf.getvalue()
nfail = out.count("[FAIL]")
print("负控 rc=%d  FAIL=%d" % (rc, nfail))
for line in out.splitlines():
    if "[FAIL]" in line:
        print("  " + line.strip())
if rc == 0 or nfail == 0:
    print("★ 负控未转红 ⇒ 主脚本的 PASS 无判别力")
    sys.exit(1)
print("★ 负控按预期转红（主脚本断言有判别力）")
sys.exit(0)
