# -*- coding: utf-8 -*-
"""M63 merge: apply 6 PASS rows to coverage.tsv ONLY (columns 4/5/6).
Byte-precise: reads raw bytes, splits on LF, replaces only fields[3],[4],[5]
of the 6 unique target rows; verifies nothing else changed.
"""
import hashlib, json, os, sys
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
WORK = os.path.join(ROOT, "MERGE_M63", "work")
BAK = os.path.join(WORK, "coverage.tsv.bak")

PASS = ["005414C0", "0071F8C0", "0041F580", "00503040", "00512290", "00512480"]
FAIL = ["005C46E0", "0065AC40"]
EXPECT_GRADE = {
    "005414C0": "[静态推断]", "0071F8C0": "[未证]",
    "0041F580": "[静态推断]", "00503040": "[静态推断]",
    "00512290": "[静态推断]", "00512480": "[静态推断]",
}
DELTA_PATH = {
    "005414C0": os.path.join(ROOT, "NAMED_PUSH_S18_B1", "delta.tsv"),
    "0071F8C0": os.path.join(ROOT, "NAMED_PUSH_S18_B2", "delta.tsv"),
    "0041F580": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00503040": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00512290": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
    "00512480": os.path.join(ROOT, "NAMED_PUSH_S14_B1", "delta.tsv"),
}
NEW_GRADE = "[已证]".encode("utf-8")
NEW_EVID = b"NAMED_PUSH_AUDIT/VERDICT.md"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def get_delta_sem_raw(entry):
    """Return exact raw bytes of one_line_semantics (col 4, 0-idx 3) from delta.tsv."""
    with open(DELTA_PATH[entry], "rb") as f:
        lines = f.read().split(b"\n")
    found = []
    for ln in lines:
        if not ln:
            continue
        fld = ln.split(b"\t")
        if len(fld) >= 6 and fld[0].strip().upper() == entry.encode("ascii"):
            found.append(fld[3])
    if len(found) != 1:
        raise RuntimeError("delta semantics for %s not unique: %d" % (entry, len(found)))
    return found[0]


def main():
    before_bytes = open(COV, "rb").read()
    before_sha = sha(before_bytes)
    # keep a backup in MERGE_M63/work (allowed deliverable area)
    open(BAK, "wb").write(before_bytes)

    sem_raw = {e: get_delta_sem_raw(e) for e in PASS}
    # cross-check with before.json csv-parsed values
    bj = json.load(open(os.path.join(WORK, "before.json"), encoding="utf-8"))
    for e in PASS:
        assert sem_raw[e].decode("utf-8") == bj["delta_semantics"][e], (
            "delta raw vs csv-parsed mismatch for " + e)

    lines = before_bytes.split(b"\n")
    seen = {e: 0 for e in PASS + FAIL}
    changed_idx = []
    for i, ln in enumerate(lines):
        if not ln:
            continue
        fld = ln.split(b"\t")
        if len(fld) != 8:
            continue
        entry = fld[0].strip().upper().decode("ascii", "replace")
        if entry not in seen:
            continue
        seen[entry] += 1
        if entry in PASS:
            assert seen[entry] == 1, "duplicate PASS entry " + entry
            assert fld[4].decode("utf-8") == EXPECT_GRADE[entry], (
                "grade mismatch for %s: %s" % (entry, fld[4]))
            orig_cols = [fld[0], fld[1], fld[2], fld[6], fld[7]]
            new_fld = list(fld)
            new_fld[3] = sem_raw[entry]
            new_fld[4] = NEW_GRADE
            new_fld[5] = NEW_EVID
            assert len(new_fld) == 8
            lines[i] = b"\t".join(new_fld)
            changed_idx.append((i + 1, entry, orig_cols))
    assert all(seen[e] == 1 for e in PASS + FAIL), seen

    after_bytes = b"\n".join(lines)
    open(COV, "wb").write(after_bytes)
    after_sha = sha(after_bytes)

    # ---- post-write verification (byte-level diff) ----
    before_lines = before_bytes.split(b"\n")
    after_lines = after_bytes.split(b"\n")
    assert len(before_lines) == len(after_lines), "line count changed"
    diff_idx = [i for i in range(len(before_lines)) if before_lines[i] != after_lines[i]]
    assert len(diff_idx) == 6, "expected 6 changed lines, got %d" % len(diff_idx)
    for i in diff_idx:
        bf = before_lines[i].split(b"\t")
        af = after_lines[i].split(b"\t")
        assert len(bf) == len(af) == 8
        # untouched columns 1,2,3,7,8 (0-idx 0,1,2,6,7)
        for k in (0, 1, 2, 6, 7):
            assert bf[k] == af[k], "untouched col %d changed on line %d" % (k + 1, i + 1)
        entry = bf[0].decode("ascii")
        assert entry in PASS
        assert af[3] == sem_raw[entry]
        assert af[4] == NEW_GRADE
        assert af[5] == NEW_EVID

    # FAIL rows byte-identical
    for e in FAIL:
        bl = [l for l in before_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]]
        al = [l for l in after_lines if l.split(b"\t")[0:1] == [e.encode("ascii")]]
        assert len(bl) == len(al) == 1 and bl[0] == al[0], "FAIL row changed: " + e

    # data rows / columns
    data = [l for l in after_lines[1:] if l]
    assert len(data) == 18498, "data rows " + str(len(data))
    assert all(len(l.split(b"\t")) == 8 for l in data)

    result = {
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "before_bytes": len(before_bytes),
        "after_bytes": len(after_bytes),
        "changed_lines_1based": [d[0] for d in changed_idx],
        "changed_entries": [d[1] for d in changed_idx],
        "diff_line_count": len(diff_idx),
        "data_rows": len(data),
        "all_8col": True,
        "fail_rows_unchanged": True,
    }
    with open(os.path.join(WORK, "coverage_merge_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print(json.dumps(result, ensure_ascii=False, indent=1))


main()
