# -*- coding: utf-8 -*-
"""负控：证明 _vtable_closure.py 的 PASS 有判别力。

变异：把 SLOT_L3 从 42 改成 41 ⇒ slot[41] 的值不是 0x4A8960，H2 必须转红。
若仍全绿，说明「slot 42 == L3 宿主」这条没有判别力。

做法：import 主脚本（sys.exit 只在 __main__ 下触发），改模块级常量后调 main()。
不启子进程、不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(HERE, "_vtable_closure.py")

src = io.open(MAIN, encoding="utf-8").read()
if "SLOT_L3 = 42" not in src:
    print("★ 主脚本已无 SLOT_L3 = 42 锚点，负控前提失效")
    sys.exit(1)

spec = importlib.util.spec_from_file_location("vc_neg", MAIN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.SLOT_L3 = 41      # 只改这一处

buf = io.StringIO()
old = sys.stdout
sys.stdout = buf
try:
    rc = mod.main()
finally:
    sys.stdout = old

out = buf.getvalue()
nfail = out.count("[FAIL]")
print("负控（SLOT_L3: 42 -> 41）rc=%d  FAIL=%d" % (rc, nfail))
for line in out.splitlines():
    if "[FAIL]" in line:
        print("  " + line.strip())
if rc == 0 or nfail == 0:
    print("★ 负控未转红 ⇒ slot 断言无判别力")
    sys.exit(1)
print("★ 负控按预期转红")
sys.exit(0)
