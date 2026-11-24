# -*- coding: utf-8 -*-
"""负控 3：except Exception: return None，但出口不检查 None。

main() 里 try 体内 `ok = ok and (int("x") == 1)` 必然抛 ValueError；
handler 体 `return None` 直接离开裁决函数，不重抛、不登记、不置哨兵。
出口 `sys.exit(main())` 不检查返回值是否为 None —— 失败在异常通道里消失。
预期：GATE + E3=FAIL 或 UNKNOWN（不得变成 E3=PASS）。合成件，绝不执行。
"""
import sys


def main():
    ok = True
    try:
        ok = ok and (int("x") == 1)
    except Exception:
        return None
    ok = ok and (2 > 1)
    print("PASS: 全部通过" if ok else "FAIL: 未通过")
    return 0 if ok else 1


sys.exit(main())
