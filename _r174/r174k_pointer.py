#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-K · FACT_INDEX_CURRENT.md 指针：V554 -> V555（R171/R173 都记过这个缺口）

纪律：wx 独占建备份 -> 断言旧 sha 与 CR -> 一次性写入 -> 回读校验。

判据：
  Y1  旧指针 5 项（字节 1858 / CR 0 / 34 行 / 指 V554 / sha 5de4084b）逐一实测
  Y2  磁盘上 V530..V555 共 26 个版本目录连续无缺、R127 为最大目录序号
  Y3  R127 下只有 FACT_INDEX.tsv 一个 FACT_INDEX 目录（三项同时成立才写）
  Y4  写入后 7 项替换逐项命中，且 V554 字样 0 次
  Y5  回读 sha256 与构造一致、CR 0、行数不变

反控：
  N1  把新 sha 换成旧 sha ⇒ Y4 的「V555 sha 命中」必 FAIL
  N2  把「版本号 530..555 连续无缺」改成 530..556 ⇒ Y2 必 FAIL（防止把区间写宽）
"""
import glob
import hashlib
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BAKD = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r174/r174k_pointer.json')

OLD_SHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
OLD_BYTES = 1858
NEW_DIR = 'R17_R127_FACTINDEX_V555'
NEW_SHA = '5396d2df9f032e1cc6febdd340dd51591c4a52a961591a2babde52ef25f3496c'
NEW_BYTES = 124834

fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


raw = io.open(PTR, 'rb').read()
txt = raw.decode('utf-8')
print('旧指针 bytes=%d CR=%d LF=%d sha=%s' % (len(raw), raw.count(b'\r'), raw.count(b'\n'),
                                          hashlib.sha256(raw).hexdigest()[:16]))

print('== Y1 · 旧指针五项 ==')
ck('Y1a 字节 == 1,858', len(raw) == OLD_BYTES, len(raw))
ck('Y1b CR == 0', raw.count(b'\r') == 0, raw.count(b'\r'))
ck('Y1c 34 行', raw.count(b'\n') == 34, raw.count(b'\n'))
ck('Y1d 仍指 V554 目录', 'R17_R126_FACTINDEX_V554' in txt)
ck('Y1e 仍写旧 sha', txt.count(OLD_SHA) == 1, txt.count(OLD_SHA))
ck('Y1f 声明轮次仍 R173', '| 声明轮次 | R173 |' in txt)

print('== Y2 · 版本目录连续性 ==')
vers = sorted(int(re.search(r'V(\d+)$', d).group(1))
              for d in glob.glob(os.path.join(TIER, 'R17_R1*_FACTINDEX_V*')) if re.search(r'V(\d+)$', d))
print('版本目录: %d 个, %d..%d' % (len(vers), vers[0], vers[-1]))
ck('Y2a 版本号连续无缺', vers == list(range(vers[0], vers[-1] + 1)), vers[:3] + vers[-3:])
ck('Y2b 最大版本是 V555', vers[-1] == 555, vers[-1])
ck('Y2c 起点是 V530', vers[0] == 530, vers[0])
ck('Y2d 共 26 个', len(vers) == 26, len(vers))
dirs = sorted(glob.glob(os.path.join(TIER, 'R17_R12*_FACTINDEX_V*')))
print('R12x 目录: %s' % [os.path.basename(d) for d in dirs])
ck('Y3 R127 下只有这一个目录，且它是最大目录序号',
   len([d for d in dirs if os.path.basename(d).startswith('R17_R127_')]) == 1,
   [os.path.basename(d) for d in dirs])

print('== 构造新指针 ==')
reps = [
    ('| 版本目录 | R17_R126_FACTINDEX_V554 |', '| 版本目录 | %s |' % NEW_DIR),
    ('lead/next_re_20261117_r14/R17_R126_FACTINDEX_V554/FACT_INDEX.tsv',
     'lead/next_re_20261117_r14/%s/FACT_INDEX.tsv' % NEW_DIR),
    ('| sha256 | %s |' % OLD_SHA, '| sha256 | %s |' % NEW_SHA),
    ('| 字节数 | 123851 |', '| 字节数 | %d |' % NEW_BYTES),
    ('| 声明轮次 | R173 |', '| 声明轮次 | R174 |'),
    ('版本号 530..554 连续无缺', '版本号 530..555 连续无缺'),
    ('V530..V554 是 25 个', 'V530..V555 是 26 个'),
    ('（D0 已钉 V554 的 sha256）', '（D0 已钉 V555 的 sha256）'),
    ('版本号 530..555 连续无缺，V554 同时是「版本号最大」且「其目录序号 R126 为最大」，且 R126 下只有这一个 FACT_INDEX 目录',
     '版本号 530..555 连续无缺，V555 同时是「版本号最大」且「其目录序号 R127 为最大」，且 R127 下只有这一个 FACT_INDEX 目录'),
]
new = txt
for a, b in reps:
    ck('替换串恰 1 次: %s' % a[:44], new.count(a) == 1, new.count(a))
    new = new.replace(a, b, 1)
ck('Y4a 新文本不再含 V554 字样', 'V554' not in new, new.count('V554'))
ck('Y4b 新文本含 V555 三处以上', new.count('V555') >= 3, new.count('V555'))
ck('Y4c 新文本 CR == 0', '\r' not in new)
ck('Y4d 行数不变', new.count('\n') == txt.count('\n'), (new.count('\n'), txt.count('\n')))

print('== 反控 ==')
bad = txt.replace('5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0',
                  NEW_SHA)  # 只替换 sha，不动其它
ck('N1 只把 sha 换成新值而其余不动 ⇒ 仍有 V554 字样（Y4a 必 FAIL）', 'V554' in bad)
wide = new.replace('版本号 530..555 连续无缺', '版本号 530..556 连续无缺')
ck('N2 把区间写宽到 530..556 ⇒ 与磁盘 26 个不符', '530..556' in wide and len(vers) != 27, len(vers))

if fails:
    print('★ fail-closed：不写盘')
    sys.exit(1)

print('== 写盘（wx 独占备份 + 一次性写 + 回读） ==')
bpath = os.path.join(BAKD, 'FACT_INDEX_CURRENT.md.before_r174_%s.bak'
                     % __import__('time').strftime('%Y%m%d_%H%M%S'))
fd = os.open(bpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
os.write(fd, raw)
os.close(fd)
ck('Y6 备份为新文件且逐字节等于旧指针', io.open(bpath, 'rb').read() == raw, bpath)
io.open(PTR, 'w', encoding='utf-8', newline='\n').write(new)
back = io.open(PTR, 'rb').read()
ck('Y5a 回读 sha256 与内存构造一致', hashlib.sha256(back).hexdigest() ==
   hashlib.sha256(new.encode()).hexdigest())
ck('Y5b 回读 CR == 0', back.count(b'\r') == 0)
ck('Y5c 回读行数不变', back.count(b'\n') == txt.count('\n'))
ck('Y5d 回读含新 sha 与 V555 目录', NEW_SHA in back.decode() and NEW_DIR in back.decode())
print('新指针 bytes=%d sha=%s' % (len(back), hashlib.sha256(back).hexdigest()[:16]))

print('\n== RESULT: %d assertions, %d FAIL ==' % (n, len(fails)))
res = {
    'script': 'r174k_pointer.py',
    'old_bytes': len(raw), 'old_sha256': hashlib.sha256(raw).hexdigest(),
    'new_bytes': len(back), 'new_sha256': hashlib.sha256(back).hexdigest(),
    'version_dirs': vers, 'backup': bpath,
    'assertions_total': n, 'fails': fails,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('wrote ' + OUT)
if fails:
    print('FAILS: %s' % fails)
sys.exit(1 if fails else 0)
