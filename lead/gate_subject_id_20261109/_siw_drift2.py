# -*- coding: utf-8 -*-
# 终稿轮自验（R3）：核心三域（counterpart/d13d14_cards/direction_ruling）max 现值复查
# + 本轮已产出件的指纹（供终稿 §5.2 绑定）。单层 glob，无递归。产出 _siw_drift2_out.txt。
import hashlib, pathlib, time

R = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = R / 'lead/gate_subject_id_20261109'
t0 = time.perf_counter()
lines = []
for d in ['lead/counterpart_fix_20261109', 'lead/d13d14_cards_20261108', 'lead/direction_ruling_20261108']:
    p = R / d
    mds = sorted(p.glob('*.md'))
    items = [(m.name, m.stat().st_size) for m in mds]
    und = [x for x in items if x[0].startswith('_')]
    bare = [x for x in items if not x[0].startswith('_')]
    mxu = max(und, key=lambda x: x[1]) if und else None
    mxb = max(bare, key=lambda x: x[1]) if bare else None
    picked = max(items, key=lambda x: x[1])[0] if items else '(无 md)'
    diff = (mxu[1] - mxb[1]) if (mxu and mxb) else None
    lines.append('%-40s md=%d max=%s maxIsUnderscore=%s bareMax=%s(%dB) diff=%s' % (
        d, len(items), picked, picked.startswith('_'),
        mxb[0] if mxb else '-', mxb[1] if mxb else 0,
        ('%dB' % diff) if diff is not None else '-'))
lines.append('')
for nm in ['_siw_verify_out.txt', '_siw_fixcheck_out.txt']:
    b = (WD / nm).read_bytes()
    lines.append('被核对象 SHA256 = %s，字节数 = %d（lead/gate_subject_id_20261109/%s）' % (
        hashlib.sha256(b).hexdigest(), len(b), nm))
elapsed = time.perf_counter() - t0
lines.append('')
lines.append('dirsVisited=0（3 域单层 glob + 2 文件 read，无 walk）elapsedSec=%.3f' % elapsed)
out = '\n'.join(lines) + '\n'
(WD / '_siw_drift2_out.txt').write_text(out, encoding='utf-8')
print(out)
