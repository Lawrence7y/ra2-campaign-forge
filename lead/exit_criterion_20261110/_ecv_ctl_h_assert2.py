"""ECV control H: 两条带裁决词的 assert 承载裁决、无出口。
预期：GATE + E3_IMPLICIT → NEEDS_FIX。合成件，绝不执行。"""
assert 1 + 1 == 2, "sanity FAIL: arithmetic broken"
assert "a" in "abc", "FAIL: alphabet check"
print("controls done")
