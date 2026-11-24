# -*- coding: utf-8 -*-
"""负控 2：except Exception: print('x') 只打印不传播。

try 体内 `ok = ok and (int("x") == 1)` 的 int("x") 必然抛 ValueError；
handler 体只有 print('x')，不重抛、不登记、不置哨兵、不返回非零。
print 在本判据里只算「有动作」，不算把失败传到出口的传播（这是已声明的静态局限：
打印无害文案但丢失失败）。本负控要求：放宽后 print 仍不得被当作失败传播。
预期：GATE + E3=FAIL 或 UNKNOWN（不得变成 E3=PASS）。合成件，绝不执行。
"""
import sys

ok = True
try:
    ok = ok and (int("x") == 1)
except Exception:
    print("x")
ok = ok and (2 > 1)
print("PASS: 全部通过" if ok else "FAIL: 未通过")
sys.exit(0 if ok else 1)
