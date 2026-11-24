# -*- coding: utf-8 -*-
# 终稿轮自验（3/3）：对 GATE_SUBJECT_ID_FIX.md 做要素/禁词/绑定行独立复算（与门禁同口径），并算本件哈希。
# 产出 _siw_selfcheck_out.txt。
import hashlib, pathlib, re, time

R = pathlib.Path('D:/Project/ra2-campaign-forge')
WD = R / 'lead/gate_subject_id_20261109'
t0 = time.perf_counter()
p = WD / 'GATE_SUBJECT_ID_FIX.md'
t = p.read_text(encoding='utf-8')
probs = []
for s in ['## 1', '## 2', '## 3', '## 4', '## 5']:
    if s not in t:
        probs.append('缺小节 ' + s)
KW = ['max(st_size)', '中间稿', '下划线', '受害面', '根因', '可操纵性', '绕过',
      '显式命名', '三方案', '全量清单', '未改任何历史件', '未验']
missing = [k for k in KW if k not in t]
probs += ['缺要素 ' + k for k in missing]
BAD = ['已改门禁', '已改历史件', '已修复']
hits = [b for b in BAD if b in t]
probs += ['含禁词 ' + b for b in hits]
binds = re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}，字节数 = \d+', t)
binds_loose = re.findall(r'被核对象 SHA256 = [0-9a-fA-F]{64}', t)
b = p.read_bytes()
h = hashlib.sha256(b).hexdigest()
elapsed = time.perf_counter() - t0
out = ('FILE=GATE_SUBJECT_ID_FIX.md\nsha256=%s\nbytes=%d\nsections=5/5(%s)\nkeywords=%d/12 missing=%s\n'
       'forbiddenHits=%s\nbindingLines(strict)=%d bindingLines(loose)=%d\nSELF_OK=%s\nelapsedSec=%.3f\n'
       % (h, len(b), 'all' if all(s in t for s in ['## 1', '## 2', '## 3', '## 4', '## 5']) else 'MISSING',
          12 - len(missing), missing, hits, len(binds), len(binds_loose), not probs, elapsed))
(WD / '_siw_selfcheck_out.txt').write_text(out, encoding='utf-8')
print(out)
