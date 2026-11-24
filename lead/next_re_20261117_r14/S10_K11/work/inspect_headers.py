
import csv, os, glob
root=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14'
for pat in [root+r'/*/coverage_delta.tsv', root+r'/COVERAGE/coverage.tsv']:
    for p in glob.glob(pat):
        with open(p, encoding='utf-8-sig', errors='replace', newline='') as f:
            r=csv.reader(f, delimiter='\t')
            h=next(r, [])
            if len(h)==9:
                print('NINE', os.path.basename(os.path.dirname(p)), p, h)
                break
# print first 3 lines from a representative 9-col file and S10_K8F header
for p in [root+r'/S10_K8F/coverage_delta.tsv', root+r'/S10_K10/coverage_delta.tsv', root+r'/S10_K9/coverage_delta.tsv', root+r'/S06_K4/coverage_delta.tsv']:
    print('\n###', p)
    with open(p, encoding='utf-8-sig', errors='replace', newline='') as f:
        for i,row in zip(range(3), csv.reader(f, delimiter='\t')): print(i, len(row), row)
