import os
ROOT = "D:/Project/ra2-campaign-forge"
SPEC = {
 "lead/PENDING_DECISIONS.md": [90,91,92,93,94,95,96,97,98,99,100,101,103,105,107,109,110,111,113,117,125,127,129,130,131,156,157,158,160,162,186,199,348],
 "lead/GOAL_THREE_TARGETS_20261018.md": [246,256,260,261,262,263,303,325,327,1192],
 "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": [234,235,236,237,238,239,240,241,242,243,247,251,252,253,254,258,260,273,274,276,282,283,284,285,286,292,293,294,295,296,297,298,299],
 "lead/d27_ruling_20261106/RULING_D27.md": [1,2,3,4,5,6,7,12,16,17,18,58,69,75,77],
 "lead/d29_ruling_20261106/RULING_D29.md": [1,2,3,4,5,6,10,14,18,19,20,26,28,47,67,71],
 "lead/d30_ruling_20261106/RULING_D30.md": [1,2,3,4,5,6,20,28,47,62,76],
 "lead/d28_ruling_20261106/RULING_D28.md": [1,2,3,4,5,7,9,30,32,34,36,42,72,78],
}
for rel, lines in SPEC.items():
    p = os.path.join(ROOT, rel)
    print("=" * 100)
    print("FILE:", rel)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        data = f.read().splitlines()
    print("TOTAL_LINES =", len(data))
    for n in lines:
        if 1 <= n <= len(data):
            print(f"{n}: {data[n-1]}")
        else:
            print(f"{n}: <OUT_OF_RANGE>")
