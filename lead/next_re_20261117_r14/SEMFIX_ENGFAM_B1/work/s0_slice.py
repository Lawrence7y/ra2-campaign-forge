"""B1 slice: reproduce the 34 target rows, sort by entry ascending, take first 17.

Slice rule: 34 rows (semantic unproven/unverified/not proven; all S17, all [已证],
all in atlas) sorted by numeric entry ascending; B1 = first 17.
"""
from __future__ import annotations

import json
from pathlib import Path

from semfix_lib import COVERAGE, load_target_rows

OUT_DIR = Path(__file__).resolve().parent.parent


def main():
    rows = load_target_rows()
    print(f"semantic-filter rows = {len(rows)}")
    # verify card assumptions
    subsystems = sorted(set(r[1] for r in rows))
    grades = sorted(set(r[4] for r in rows))
    print("subsystems =", subsystems)
    print("grades =", grades)
    assert len(rows) == 34, len(rows)
    assert subsystems == ["S17"], subsystems
    assert grades == ["[已证]"], grades

    # sort by numeric entry ascending
    rows_sorted = sorted(rows, key=lambda r: int(r[0], 16))
    b1 = rows_sorted[:17]
    b2 = rows_sorted[17:]

    print("\n--- B1 (first 17, entry ascending) ---")
    for r in b1:
        print(r[0], r[1], r[2], "|", r[3])
    print("\nB1 entries:", " ".join(r[0] for r in b1))
    print("\n--- B2 (remaining 17) ---")
    print("B2 entries:", " ".join(r[0] for r in b2))

    # persist slice rows (full 6-column source rows) for downstream scripts
    (OUT_DIR / "work" / "slice_b1.json").write_text(
        json.dumps(b1, indent=2), encoding="utf-8"
    )
    print("\nwrote work/slice_b1.json")


if __name__ == "__main__":
    main()
