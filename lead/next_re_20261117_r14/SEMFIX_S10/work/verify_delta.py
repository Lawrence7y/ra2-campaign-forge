# -*- coding: utf-8 -*-
import os, hashlib
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10"
COV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
DEL  = os.path.join(CARD,'coverage_delta.tsv')
rows={}
for ln in open(COV,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    c=ln.split('\t')
    if len(c)>=6: rows[c[0]]=c
dl=open(DEL,encoding='utf-8').read().split('\n')
hdr=dl[0].split('\t')
print('HEADER', hdr, 'ncol=',len(hdr))
drows={}; widths=set()
for ln in dl[1:]:
    if not ln.strip(): continue
    c=ln.split('\t'); widths.add(len(c)); drows[c[0]]=c
print('data rows',len(drows),'widths',widths)
print('cols expected 8:', all(w==8 for w in widths))
grade_bad=[]; name_bad=[]; sub_bad=[]; evp_bad=[]; oldnew_bad=[]
for e,c in drows.items():
    dr=rows[e]
    if c[4]!=dr[4]: grade_bad.append((e,c[4],dr[4]))
    if c[2]!=dr[2]: name_bad.append((e,c[2],dr[2]))
    if c[1]!=dr[1]: sub_bad.append((e,c[1],dr[1]))
    if c[5]!=dr[5]: evp_bad.append((e,c[5],dr[5]))
    if c[7]!='[已证]→[已证]': oldnew_bad.append((e,c[7]))
print('GRADE mismatches:',grade_bad)
print('NAME mismatches:',name_bad)
print('SUBSYSTEM mismatches:',sub_bad)
print('EVIDENCE_PATH mismatches:',evp_bad)
print('OLD→NEW mismatches:',oldnew_bad)
targets=set(['0045A560','0045A610','004D4200','004D4280','004D4B20','004D4CB0','004D4DC0','004D5070','004D5350','004D6AA0','004D9290','004DA2C0','004DA530','004DDF90','0051F3E0','005B2FD0','005B3060','005B3570','005B35E0','005B3650','005B36B0','006B1850','006B1900','006B8660','006B8710'])
print('entry set exact:', set(drows)==targets, 'extra=',set(drows)-targets,'missing=',targets-set(drows))
sha=hashlib.sha256(open(COV,'rb').read()).hexdigest()
print('coverage.tsv sha256',sha)
