import os
ROOT = r"D:\Project\ra2-campaign-forge"
# file -> list of 1-based line numbers to print verbatim
WANT = {
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": [1,11,110,111,123,124,125,149,179,181,204,207,211,212,213,214,215,216,217,218,222,237],
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md": [1,25,41],
 "lead/ledger_appendix_20261108/_lad_tpl.md": [1,87,88,89,151,172],
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": [1,136,165,169,171,174,196],
 "lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md": [88,90,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,127,129,131,135,148,151,168,171],
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md": [1,2,3,4,5,6,7,8,9,10],
}

def show(rel, nums):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    b = open(p,"rb").read()
    lines = b.decode("utf-8").split("\n")  # keeps trailing "" if ends with \n
    print("#### FILE", rel, "bytes=", len(b), "split('\\n') len=", len(lines))
    for n in nums:
        if 1 <= n <= len(lines):
            print(f"{rel}:{n}: {lines[n-1]}")
        else:
            print(f"{rel}:{n}: <OUT_OF_RANGE max={len(lines)}>")
    print()

for rel, nums in WANT.items():
    show(rel, nums)
