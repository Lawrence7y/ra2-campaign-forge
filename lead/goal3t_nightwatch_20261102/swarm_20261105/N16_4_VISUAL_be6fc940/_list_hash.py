# -*- coding: utf-8 -*-
# N16-4 visual inspector helper: list files, hash, mtime, json alignment.
import glob, os, json, hashlib, datetime

ROOT = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'

subs = sorted(glob.glob(os.path.join(ROOT, '*', 'measure_w*_end_x.png')))
roots = sorted(glob.glob(os.path.join(ROOT, 'measure_w*_end_x.png')))

print('SUB_COUNT', len(subs))
for p in subs:
    print('SUB', p)

print('ROOT_COUNT', len(roots))
for p in roots:
    print('ROOT', p)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def mt(path):
    st = os.stat(path)
    return datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S'), st.st_size

print()
print('=== hashes / mtime / size ===')
groups = {}
for p in subs + roots:
    d = sha256(p)
    t, s = mt(p)
    tag = 'SUB' if p in subs else 'ROOT'
    groups.setdefault(d, []).append(p)
    print(tag, d[:16], 'mtime=' + t, 'size=' + str(s), p)

print()
print('=== duplicate byte groups ===')
for d, ps in sorted(groups.items()):
    if len(ps) > 1:
        print('GROUP', d[:16])
        for p in ps:
            print('   ', p)
