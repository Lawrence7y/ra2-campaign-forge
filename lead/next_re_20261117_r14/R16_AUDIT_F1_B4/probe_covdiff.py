# -*- coding: utf-8 -*-
"""对比 pin（开卡时）与现盘 coverage.tsv 的差异：哪些 entry 变了、变在哪列。"""
import io, re, sys
sys.dont_write_bytecode = True

R14 = r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14"
PIN = R14 + "/R16_AUDIT_F1_B4/_pin_coverage.tsv"
LIVE = R14 + "/COVERAGE/coverage.tsv"
B4 = ("006E6470 0071CDA0 0071E1D0 0071F8C0 0071F930 0071FA80 007220A0 007220D0 "
      "00726860 007268D0 00726950 00727BF0 00727C80 007281A0 00749F30 0074BA30 "
      "0075E0C0 0075E2C0").split()


def load(p):
    d = {}
    order = []
    for i, ln in enumerate(io.open(p, encoding='utf-8-sig')):
        if i == 0:
            continue
        c = ln.rstrip('\r\n').split('\t')
        if len(c) < 8:
            continue
        d[c[0].strip().upper()] = c
        order.append(c[0].strip().upper())
    return d, order


a, oa = load(PIN)
b, ob = load(LIVE)
print('pin rows=%d live rows=%d  same_order=%s' % (len(a), len(b), oa == ob))

added = [e for e in b if e not in a]
removed = [e for e in a if e not in b]
print('added=%d removed=%d' % (len(added), len(removed)))
if added:
    print('  added:', ' '.join(added[:40]))

chg = []
for e in b:
    if e in a and a[e] != b[e]:
        dif = [i for i in range(8) if a[e][i] != b[e][i]]
        chg.append((e, dif))
print('changed rows=%d' % len(chg))
for e, dif in chg:
    print('  %s cols=%s  old4_len=%d new4_len=%d old_had_w=%s new_had_w=%s'
          % (e, dif, len(a[e][3]), len(b[e][3]),
             '④ 活表槽位见证' in a[e][3], '④ 活表槽位见证' in b[e][3]))

print()
print('B4 rows changed?')
for e in B4:
    if e not in b:
        print('  %s MISSING in live' % e)
        continue
    same = a[e] == b[e]
    print('  %s same=%s  live_has_witness=%s' % (e, same, '④ 活表槽位见证' in b[e][3]))
