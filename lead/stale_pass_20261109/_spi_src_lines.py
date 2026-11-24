import os
ROOT = "D:/Project/ra2-campaign-forge"
SPEC = {
 "lead/masking_effect_20261109/MASKING_EFFECT_AUDIT.md": list(range(176, 182)) + list(range(202, 254)) + [335, 375, 376, 377, 379, 380, 381, 384, 385, 386, 388, 390, 391, 393, 398, 399, 403, 404, 405],
 "lead/check_masking_20261109/CHECK_MASKING_INJECT.md": [25, 124, 125, 126, 138, 154, 179, 211, 231, 271, 331, 392, 515, 634, 640, 642, 650, 652, 664, 695],
 "lead/d27_ruling_20261106/check_d27.py": list(range(1, 19)) + list(range(53, 101)),
 "lead/d29_ruling_20261106/check_d29.py": list(range(1, 16)) + list(range(50, 106)),
 "lead/d30_ruling_20261106/check_d30.py": list(range(1, 16)) + list(range(50, 106)),
 "lead/d28_ruling_20261106/check_d28.py": list(range(1, 17)) + list(range(54, 56)) + list(range(85, 116)),
 "lead/refsync_scope_20261109/_rs_carrier_scan.py": [165, 194, 229, 343, 344, 345, 346, 347, 348, 349],
}
for rel, lines in SPEC.items():
    p = os.path.join(ROOT, rel)
    print("=" * 100)
    print("FILE:", rel)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        data = f.read().splitlines()
    print("TOTAL_LINES =", len(data))
    seen = set()
    for n in sorted(set(lines)):
        if 1 <= n <= len(data):
            print(f"{n}: {data[n-1]}")
        else:
            print(f"{n}: <OUT_OF_RANGE>")
    # count of '## ' headings for rulings
    if rel.startswith("lead/d") and "RULING" in rel:
        print("H2_COUNT =", sum(1 for x in data if x.startswith("## ")))
