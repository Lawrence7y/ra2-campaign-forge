"""Step 1: filter coverage.tsv for rows needing semantic repair.

Criteria (per SEMFIX-SLOTS card):
  - col4 (one_line_semantics) contains "槽语义未证"
  - col5 (grade) == "[已证]"
  - col2 (subsystem) != "S22"

Header is comma-separated; data rows are TAB-separated with 8 columns.
"""
import sys

COVERAGE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"


def main():
    rows = []
    with open(COVERAGE, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\n")
        assert header.strip().split(",") == [
            "entry", "subsystem", "name", "one_line_semantics",
            "grade", "evidence_path", "n_sources", "conflict",
        ], header
        for lineno, line in enumerate(f, start=2):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) != 8:
                print(f"WARN line {lineno}: {len(parts)} cols", file=sys.stderr)
                continue
            entry, subsystem, name, semantics, grade, evpath, nsrc, conflict = parts
            if "槽语义未证" in semantics and grade == "[已证]" and subsystem != "S22":
                rows.append({
                    "entry": entry,
                    "subsystem": subsystem,
                    "name": name,
                    "semantics": semantics,
                    "grade": grade,
                    "evpath": evpath,
                    "nsrc": nsrc,
                    "conflict": conflict,
                    "lineno": lineno,
                })
    print(f"TOTAL={len(rows)}")
    by_sub = {}
    for r in rows:
        by_sub[r["subsystem"]] = by_sub.get(r["subsystem"], 0) + 1
    print("BY_SUBSYSTEM=" + ",".join(f"{k}:{v}" for k, v in sorted(by_sub.items())))
    print("--- rows ---")
    for r in rows:
        print(f'{r["entry"]}\t{r["subsystem"]}\t{r["name"]}\t{r["semantics"]}')


if __name__ == "__main__":
    main()
