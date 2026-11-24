# -*- coding: utf-8 -*-
# _sgv_mtime.py —— 复核步骤②补充：全仓（除 out/ 与 .git）引用语料路径的 .py 按 mtime 分窗清点
import subprocess, os, time, json

BASE = r'D:\Project\ra2-campaign-forge'
os.chdir(BASE)
out = subprocess.run(['grep', '-rl', '--include=*.py', '-e', 'qc161_u0400_trip', '.'],
                     capture_output=True).stdout.decode('utf-8', 'replace')
files = [l.strip().replace('\\', '/') for l in out.splitlines() if l.strip()]
buckets = {}
for f in files:
    p = f[2:] if f.startswith('./') else f
    if not os.path.isfile(p):
        continue
    mt = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(p)))
    buckets.setdefault(mt, []).append(p)
for mt in sorted(buckets):
    print('%s  %3d' % (mt, len(buckets[mt])))
print('--- in-window 2026-11-05..07 detail ---')
for mt in ('2026-11-05', '2026-11-06', '2026-11-07'):
    for p in sorted(buckets.get(mt, [])):
        print(mt, p)
