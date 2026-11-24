# -*- coding: utf-8 -*-
"""只读交叉核：00772CD0/00772EB0 的槽位↔语义绑定（是否各自调用读/写包装）。"""
import sys

sys.dont_write_bytecode = True
HERE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_F1_B5'
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8')
import verify as V

img = V.Img(V.EXE)
ts = V.TextScan(img)
for entry, want, want2 in ((0x772CD0, 0x410380, '读包装 Load 侧'),
                           (0x772EB0, 0x410320, '写包装 Save 侧')):
    end = V.body_extent(ts, img, entry)
    p = V.func_profile(ts, img, entry, end)
    print('%08X body=[%08X,%08X) callees=%s' % (
        entry, entry, end, ' '.join('%08X' % c for c in p['callees'][:16])))
    print('        含 %08X (%s) ? %s' % (want, want2, want in p['callees']))

# 反向一致性：slot5 函数不应调写包装、slot6 不应调读包装
for entry, bad in ((0x772CD0, 0x410320), (0x772EB0, 0x410380)):
    end = V.body_extent(ts, img, entry)
    p = V.func_profile(ts, img, entry, end)
    print('%08X 含不该有的 %08X ? %s' % (entry, bad, bad in p['callees']))
