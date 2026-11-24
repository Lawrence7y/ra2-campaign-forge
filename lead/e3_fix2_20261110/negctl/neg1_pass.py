# -*- coding: utf-8 -*-
"""负控 1：except Exception: pass 包住一个会失败的检查，之后无任何传播。

try 体内 `ok = ok and (int("x") == 1)` 的 int("x") 必然抛 ValueError；
handler 体为 pass，不重抛、不登记、不置哨兵、不返回非零。
ok 之后再做一项独立检查并直接喂出口 —— 失败在异常通道里被吞掉，出口看不到。
预期：GATE + E3=FAIL（真吞没必须被抓到）。合成件，绝不执行。
"""
import sys

ok = True
try:
    ok = ok and (int("x") == 1)
except Exception:
    pass
ok = ok and (2 > 1)
print("PASS: 全部通过" if ok else "FAIL: 未通过")
sys.exit(0 if ok else 1)
