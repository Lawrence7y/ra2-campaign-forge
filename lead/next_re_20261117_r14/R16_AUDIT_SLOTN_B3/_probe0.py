# -*- coding: utf-8 -*-
# read-only format probe
import sys
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
SLOTN = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PROBE_802\slotN43.tsv"

raw = open(COV, 'rb').read()
lines = raw.split(b'\n')
print("coverage nlines(raw split) =", len(lines))
print("L0:", lines[0][:400])
print("L1:", lines[1][:400])
print("L2:", lines[2][:200])
print("tabs L1:", lines[1].count(b'\t'), "L2:", lines[2].count(b'\t'))

raw2 = open(SLOTN, 'rb').read()
l2 = raw2.split(b'\n')
print("\nslotN43 nlines =", len(l2))
for i in (0, 1, 30, 31, 32, 33, 43):
    print(i, l2[i][:260])
