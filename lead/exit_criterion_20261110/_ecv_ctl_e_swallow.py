"""ECV control E: 门禁内吞异常（except: pass 惰性体）。
预期：GATE + E3 FAIL → NEEDS_FIX。合成件，绝不执行。"""
import sys

ok = True
try:
    ok = ok and (int("x") == 1)
except Exception:
    pass
ok = ok and (2 > 1)
print("[PASS]" if ok else "[FAIL]")
sys.exit(0 if ok else 1)
