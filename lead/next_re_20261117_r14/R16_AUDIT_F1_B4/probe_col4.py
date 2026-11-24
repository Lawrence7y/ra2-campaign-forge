# -*- coding: utf-8 -*-
"""只读探针：看盘上 coverage.tsv 目标行/先例行的第 4 列状态。"""
import io, sys
sys.dont_write_bytecode = True

R14 = r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
COV = R14 + "/COVERAGE/coverage.tsv"

rows = ("006E6470 0071CDA0 0071E1D0 0071F8C0 0071F930 0071FA80 007220A0 007220D0 "
        "00726860 007268D0 00726950 00727BF0 00727C80 007281A0 00749F30 0074BA30 "
        "0075E0C0 0075E2C0").split()
par = "00464AC0 004DE630 004F42F0".split()
want = set(rows + par)

for ln in io.open(COV, encoding='utf-8-sig'):
    c = ln.rstrip('\r\n').split('\t')
    e = c[0].strip().upper()
    if e in want:
        c4 = c[3]
        tag = 'TARGET' if e in rows else 'PRECED'
        print("%s %s | grade=%s | witness=%s | n4=%d | len4=%d | ncols=%d"
              % (tag, e, c[4], '④ 活表槽位见证' in c4, c4.count('④'), len(c4), len(c)))
