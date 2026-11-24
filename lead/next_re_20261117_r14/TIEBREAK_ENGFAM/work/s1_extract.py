"""s1: extract the 34 coverage rows, sort, and take the 6-row sample.

Filter (documented verbatim in the report):
    Select-String coverage.tsv -Pattern "unproven|unverified|not proven" -CaseSensitive:$false

Sampling rule (deterministic, no hand picking):
    idx 0            = smallest entry
    idx n-1          = largest entry
    idx floor(k*(n-1)/5), k=1..4   = 4 evenly spaced rows in between
with n = 34 -> 0, 6, 13, 19, 26, 33
"""
import re

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\TIEBREAK_ENGFAM\EVIDENCE"

PAT = re.compile(r"unproven|unverified|not proven", re.I)


def main():
    rows = []
    with open(COV, "r", encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            if not PAT.search(line):
                continue
            c = line.rstrip("\n").split("\t")
            rows.append(dict(line=ln, entry=c[0], sub=c[1], name=c[2],
                             sem=c[3], grade=c[4], ev=c[5]))
    print(f"matched rows: {len(rows)}")
    for r in rows:
        assert r["sub"] == "S17", r
        assert r["grade"] == "[已证]", r
    addr = sorted(int(r["entry"], 16) for r in rows)
    assert len(addr) == len(set(addr)) == 34
    n = len(addr)
    idx = [0] + [k * (n - 1) // 5 for k in range(1, 5)] + [n - 1]
    print("sampled indices:", idx)
    with open(OUT + r"\rows34.tsv", "w", encoding="utf-8") as f:
        f.write("idx\tentry\tsemantics\n")
        for i, a in enumerate(addr):
            sem = next(r["sem"] for r in rows if int(r["entry"], 16) == a)
            f.write(f"{i:02d}\t{a:08X}\t{sem}\n")
    with open(OUT + r"\sample.tsv", "w", encoding="utf-8") as f:
        f.write("idx\tentry\n")
        for i in idx:
            f.write(f"{i:02d}\t{addr[i]:08X}\n")
    print("wrote rows34.tsv / sample.tsv")
    print("\n34 entries in order:")
    print("\n".join(f"{i:02d} {a:08X}" for i, a in enumerate(addr)))
    print("\nsample:")
    for i in idx:
        print(f"  idx {i:02d}  0x{addr[i]:08X}")
    sem0 = rows[0]["sem"]
    print("\nsample semantics (row0):", sem0)


if __name__ == "__main__":
    main()
