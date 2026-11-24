"""ECV control B: 文件名像探针（probe），本体是真门禁（And 聚合 + 内联动态出口）。
预期：GATE + OK（E1 动态 / E2 And 聚合≥2 / E3 无吞 / E4 同名驱动）。合成件，绝不执行。"""
import sys

ok = True
ok = ok and (4 % 2 == 0)
ok = ok and (6 % 2 == 0)
print("[PASS] evens hold" if ok else "[FAIL] odd detected")
sys.exit(0 if ok else 1)
