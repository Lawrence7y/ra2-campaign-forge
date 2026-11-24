import io, os, re, shutil
V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
L = io.open(V, encoding='utf-8').read().split('\n')
print('=== around L175-190 (R1) ===')
for i in range(168, 196):
    if i < len(L):
        print('  L%-4d %s' % (i + 1, L[i].rstrip()[:130]))
