#!/usr/bin/env python3
import sys,re,os
EV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED\EVIDENCE'
e=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
lr=re.compile(r'^([0-9A-F]{8})\s+([0-9a-f]+)\s+(\S+)\s*(.*)$')
for ln in open(os.path.join(EV,'dis_%s.txt'%e),encoding='utf-8'):
    m=lr.match(ln.rstrip('\n'))
    if m and lo<=int(m.group(1),16)<=hi:
        print(ln.rstrip('\n'))
