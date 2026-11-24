"""_rsv_lines.py — settle the +1 line-count convention (independent)."""
import os
ROOT = r"D:/Project/ra2-campaign-forge"
files = [
"lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md",
"lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
"lead/GOAL_THREE_TARGETS_20261018.md",
]
for rel in files:
    p = os.path.join(ROOT, rel)
    b = open(p, "rb").read()
    tail = b[-40:]
    print(rel)
    print("  ends_with_LF =", b.endswith(b"\n"), " ends_with_CRLF =", b.endswith(b"\r\n"),
          " CR_count =", b.count(b"\r"), " LF_count =", b.count(b"\n"))
    print("  last40bytes =", repr(tail))
    print("  len(b.decode('utf-8').split(chr(10))) =", len(b.decode("utf-8").split("\n")),
          " ; len(splitlines()) =", len(b.decode("utf-8").splitlines()))
