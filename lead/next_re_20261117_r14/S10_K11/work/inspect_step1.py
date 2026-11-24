
import csv, os
root=r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14'
paths=[
 root+r'/S10_K8F/_audit/VERDICT.md',
 root+r'/S10_K8F/coverage_delta.tsv',
 root+r'/COVERAGE/coverage.tsv',
 root+r'/M4_merge/coverage.tsv',
]
for path in paths:
    print('\n###', path, 'mtime=', os.path.getmtime(path), 'size=', os.path.getsize(path))
    if path.endswith('.md'):
        text=open(path, encoding='utf-8-sig', errors='replace').read()
        for line in text.splitlines():
            if any(s.lower() in line.lower() for s in ['DFE00','DFCB0','措辞','残留']): print(line)
    else:
        with open(path, encoding='utf-8-sig', errors='replace', newline='') as f:
            for i,row in enumerate(csv.reader(f, delimiter='\t')):
                if i<2 or any(cell.strip().upper().lstrip('0X') in ('4DFE00','4DFCB0') for cell in row[:5]):
                    print(i, repr(row))
