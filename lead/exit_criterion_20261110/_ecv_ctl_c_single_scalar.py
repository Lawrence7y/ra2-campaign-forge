"""ECV control C: 单标量内联门——只有一个检查点直接赋给驱动名。
用于探 E2 口径分歧：规格说证据=And聚合/+=/checker调用/出口比较（不含普通赋值）。
合成件，绝不执行。"""
import sys

ok = (2 + 2 == 5)
print("[PASS] math holds" if ok else "[FAIL] math broken")
sys.exit(0 if ok else 1)
