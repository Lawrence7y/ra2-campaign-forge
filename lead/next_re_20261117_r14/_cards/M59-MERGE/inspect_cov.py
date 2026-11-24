import csv, os

cov = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'

with open(cov, 'r', encoding='utf-8', newline='') as f:
    raw = f.read()

# line endings
print('CRLF count:', raw.count('\r\n'), 'LF total:', raw.count('\n'))
lines = raw.split('\n')
if lines and lines[-1] == '':
    lines = lines[:-1]
print('total lines (incl header):', len(lines))

header = lines[0]
print('HEADER:', repr(header))
cols = header.split('\t')
print('header col count:', len(cols))

# column count distribution
from collections import Counter
cc = Counter(len(l.split('\t')) for l in lines)
print('column-count distribution:', dict(cc))

# show first 2 data rows
for l in lines[1:3]:
    print('ROW:', repr(l[:300]))
