# -*- coding: utf-8 -*-
"""只读交叉核：用 atlas 的「函数起点」表（不看 size）给剩余装表点定性。"""
import sys

sys.dont_write_bytecode = True
HERE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_F1_B5'
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8')
import verify as V

img = V.Img(V.EXE)
ts = V.TextScan(img)
atlas = V.load_atlas()
starts = sorted(int(k, 16) for k, v in atlas.items() if v)
import bisect


def nearest_start(va):
    i = bisect.bisect_right(starts, va) - 1
    return starts[i] if i >= 0 else None


for s in ('0075ED37', '007637E4', '007638C6', '00771F57', '0075ECAA',
          '0075F6A4', '00763845', '00763CA7', '00771F28'):
    va = int(s, 16)
    g = nearest_start(va)
    end = g + atlas['%08X' % g]
    p = V.func_profile(ts, img, g, end)
    at = V.atexit_sites(ts, img, g)
    print('%s -> func %08X [%08X,%08X) inside=%s atexit=%s del_dtor=%s base_ctor=%s base_dtor=%s'
          % (s, g, g, end, (g <= va < end),
             ['%08X' % x[0] for x in at], p['del_dtor'],
             ('%08X' % p['base_ctor']) if p['base_ctor'] else None,
             ('%08X' % p['base_dtor']) if p['base_dtor'] else None))
