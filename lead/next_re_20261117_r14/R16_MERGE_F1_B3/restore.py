# -*- coding: utf-8 -*-
"""Restore coverage.tsv to the exact pre-merge state (sha 6428B4EB) after the off-by-one bug.

Bug recap: replacements used cov_data indices (header excluded) but were applied to
cov_rows (header included), so target T at cov_rows position P had its new4 written
into row P-1 instead. Restore: for each target T, set row (P-1).col4 back to the
original col4 of that row's entry, taken from the audit pin (rows untouched by
B1/B2/concurrent writer), and verify the full-file sha equals the recorded before sha.
"""
import csv, os, sys, hashlib, json

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PIN = os.path.join(ROOT, "R16_AUDIT_F1_B3", "_pin_coverage.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B3")
DELTA = os.path.join(ROOT, "R16_F1_B3", "delta.tsv")
EXPECTED_BEFORE_SHA = "6428B4EB06280BD56C250CC1156E0B24A72E6BC4A11B5E9FD17E500718642D5F"
EXPECTED_BEFORE_BYTES = 4058895


def read_rows(path):
    txt = open(path, "rb").read().decode("utf-8")
    lines = txt.split("\n")
    if lines[-1] == "":
        lines = lines[:-1]
    return [ln.split("\t") for ln in lines]


def main():
    before4 = json.load(open(os.path.join(OUT, "before_col4.json"), encoding="utf-8"))
    ddata = list(csv.reader(open(DELTA, encoding="utf-8-sig", newline=""), delimiter="\t"))[1:]
    new4_by_entry = {r[0].strip().upper(): r[3] for r in ddata}

    cur_rows = read_rows(COV)
    pin_rows = read_rows(PIN)
    pin_col4 = {r[0].strip().upper(): r[3] for r in pin_rows if len(r) >= 4}

    # sanity: pin must agree with the recorded before-col4 for all 18 targets
    # (proves the pin is a reliable source for untouched rows in this region)
    for e, orig4 in before4.items():
        assert pin_col4.get(e) == orig4, ("pin disagrees with before for target", e)

    # For each target, find P (target row index), the buggy row is P-1.
    restored = [list(r) for r in cur_rows]
    report = []
    for e, orig4 in before4.items():
        Ps = [i for i, r in enumerate(cur_rows) if len(r) >= 4 and r[0].strip().upper() == e]
        assert len(Ps) == 1, (e, Ps)
        P = Ps[0]
        buggy = P - 1
        be = cur_rows[buggy][0].strip().upper()
        # sanity: buggy row currently holds this target's new4
        assert cur_rows[buggy][3] == new4_by_entry[e], ("buggy row content mismatch", e, be)
        # restore buggy row's col4: authoritative before_col4 if it is a target, else pin
        if be in before4 and be != e:
            orig_buggy = before4[be]
        elif be in pin_col4:
            orig_buggy = pin_col4[be]
        else:
            raise AssertionError(("no source for buggy row", be))
        restored[buggy][3] = orig_buggy
        report.append((e, P, be, buggy))

    # Reconstruct full text (LF only, no trailing LF)
    txt = "\n".join("\t".join(r) for r in restored)
    data = txt.encode("utf-8")
    sha = hashlib.sha256(data).hexdigest().upper()
    print("restored bytes=", len(data), "sha=", sha)
    print("expected bytes=", EXPECTED_BEFORE_BYTES, "sha=", EXPECTED_BEFORE_SHA)
    ok = (len(data) == EXPECTED_BEFORE_BYTES and sha == EXPECTED_BEFORE_SHA)
    print("EXACT RESTORE =", ok)
    if not ok:
        # show which restored rows differ from pin to help debug
        print("--- compare restored vs pin ---")
        diff = 0
        for i, (rr, pr) in enumerate(zip(restored, pin_rows)):
            if rr != pr:
                diff += 1
                if diff <= 30:
                    print(" row", i, "entry", rr[0], "col4 differs; restoredlen", len(rr[3]), "pinlen", len(pr[3]))
        print("total rows differing from pin:", diff)
        return

    # Write restored file
    with open(COV, "wb") as f:
        f.write(data)
    with open(os.path.join(OUT, "restore_report.json"), "w", encoding="utf-8") as f:
        json.dump({"ok": True, "target": [{"e": e, "P": P, "buggy_row_entry": be, "buggy_row_idx": b}
                                          for e, P, be, b in report]}, f, ensure_ascii=False, indent=1)
    print("WROTE restored coverage.tsv")


if __name__ == "__main__":
    main()
