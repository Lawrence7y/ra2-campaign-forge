#!/usr/bin/env python3
# Re-runnable verifier for R14_COMMON.md §2.8 append-only write.
# Checks: (1) prefix sha256 over first BEFORE_LEN bytes == BEFORE_SHA;
#         (2) CR count unchanged (BEFORE_CR); (3) line count / LF count reported.
import hashlib
import pathlib
import sys

BASE = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14")
TARGET = BASE / "R14_COMMON.md"
BACKUP = BASE / "R17_COMMON_2_8" / "R14_COMMON.before_2.8.md"

BEFORE_LEN = 232629
BEFORE_SHA = "6756ad050352a53483ba3391101b54fb4180ed645595d2a3fbde6d0c2e1eda07"
BEFORE_CR = 1081
EXPECTED_AFTER_LEN = 236380
EXPECTED_AFTER_SHA = "e7253e44cbefc446fe8c86519406012fadf10359b212af5f13bd87ea6325cc5d"

def digest(b):
    return hashlib.sha256(b).hexdigest()

def main():
    data = TARGET.read_bytes()
    ok = True

    # 1) prefix hash assertion: old bytes must be byte-identical
    prefix = data[:BEFORE_LEN]
    prefix_sha = digest(prefix)
    prefix_ok = (len(prefix) == BEFORE_LEN and prefix_sha == BEFORE_SHA)
    print("PREFIX_LEN:", len(prefix), "EXPECTED:", BEFORE_LEN)
    print("PREFIX_SHA256:", prefix_sha)
    print("PREFIX_ASSERT:", "PASS" if prefix_ok else "FAIL")
    ok &= prefix_ok

    # 2) backup must equal the exact original bytes
    backup = BACKUP.read_bytes()
    backup_ok = (len(backup) == BEFORE_LEN and digest(backup) == BEFORE_SHA)
    print("BACKUP_ASSERT:", "PASS" if backup_ok else "FAIL")
    ok &= backup_ok

    # 3) CR count must not change; appended part must be LF-only
    cr = data.count(b"\r")
    lf = data.count(b"\n")
    crlf = data.count(b"\r\n")
    bare_lf = lf - crlf
    appended = data[BEFORE_LEN:]
    appended_cr = appended.count(b"\r")
    cr_ok = (cr == BEFORE_CR and appended_cr == 0)
    print("CR_COUNT:", cr, "BEFORE_CR:", BEFORE_CR, "APPENDED_CR:", appended_cr)
    print("CR_ASSERT:", "PASS" if cr_ok else "FAIL")
    ok &= cr_ok

    # 4) after length / hash / line count
    after_ok = (len(data) == EXPECTED_AFTER_LEN and digest(data) == EXPECTED_AFTER_SHA)
    print("AFTER_LEN:", len(data), "EXPECTED:", EXPECTED_AFTER_LEN)
    print("AFTER_SHA256:", digest(data), "EXPECTED:", EXPECTED_AFTER_SHA)
    print("AFTER_ASSERT:", "PASS" if after_ok else "FAIL")
    ok &= after_ok
    print("LINES_TOTAL(by LF):", lf, "BARE_LF:", bare_lf, "CRLF:", crlf)

    print("OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
