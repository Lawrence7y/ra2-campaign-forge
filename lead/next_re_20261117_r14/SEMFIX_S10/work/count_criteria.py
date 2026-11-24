# -*- coding: utf-8 -*-
import os,collections
L=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\ROW_VERDICTS.tsv"
targets=set(['0045A560','0045A610','004D4200','004D4280','004D4B20','004D4CB0','004D4DC0','004D5070','004D5350','004D6AA0','004D9290','004DA2C0','004DA530','004DDF90','0051F3E0','005B2FD0','005B3060','005B3570','005B35E0','005B3650','005B36B0','006B1850','006B1900','006B8660','006B8710'])
cnt=collections.Counter()
for ln in open(L,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    c=ln.split('\t')
    if c[0] in targets: cnt[c[5]]+=1
print(dict(cnt))