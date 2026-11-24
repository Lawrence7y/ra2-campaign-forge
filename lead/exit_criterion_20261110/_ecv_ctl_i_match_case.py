"""ECV control I: match/case 两臂 print PASS/FAIL——规格只覆盖 if/elif/IfExp。
预期：两判据都落 PROBE（覆盖缺口实证，不是任何一方的 bug）。合成件，绝不执行。"""
import sys

ok = len(sys.argv) > 1
match ok:
    case True:
        print("[PASS] args present")
    case False:
        print("[FAIL] args missing")
sys.exit(0)
