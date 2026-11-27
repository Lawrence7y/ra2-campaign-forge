#!/usr/bin/env python3
"""R169 N：FACT_INDEX_CURRENT.md 指针 V547 -> V549（该指针已连续两轮未更新：R168 升 V548 时漏改）。

纪律：
  · 备份 wx 独占 → 断言旧 sha 与 CR → 一次性写 → 回读校验；
  · 指针里的 sha256 / 字节数必须与现盘 V549 实测一致（不许从别处抄）；
  · 历史版本声明段必须把 V548 也列进去（否则「18 个可独立复核快照」这个数字会失真）。
"""
import hashlib, json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
CUR = T + '/FACT_INDEX_CURRENT.md'
V549 = T + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
BAKDIR = T + '/R17_LEAD_BASELINE'

def sha(b): return hashlib.sha256(b).hexdigest()

raw = open(V549, 'rb').read()
sha549 = sha(raw); B549 = len(raw)
assert sha549.startswith('f1d32127') and B549 == 117545

src = open(CUR, 'rb').read()
bak = os.path.join(BAKDIR, 'FACT_INDEX_CURRENT.md.before_r169_PTR.bak')
fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(src)
assert sha(open(bak, 'rb').read()) == sha(src)

old = src.decode('utf-8')
A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('N0 旧指针确实是 V547（本轮更正的是两轮未更新的陈旧指针）',
    'R17_R119_FACTINDEX_V547' in old and '919263cf' in old and '109220' in old,
    {'has_v547': 'R17_R119_FACTINDEX_V547' in old})

new = old
new = new.replace('R17_R119_FACTINDEX_V547', 'R17_R121_FACTINDEX_V549')
new = new.replace('919263cf03f51bd4ec933ec8ad1d07ee599e93cc4b9b6362d33e5442328b2ec9', sha549)
new = new.replace('| 字节数 | 109220 |', '| 字节数 | %d |' % B549)
new = new.replace('| 声明轮次 | R167 |', '| 声明轮次 | R169 |')
new = new.replace('版本号 530..547 连续无缺，V547 同时是「版本号最大」且「其目录序号 R119 为最大」，且 R119 下只有这一个 FACT_INDEX 目录（三项同时成立才写本文件）',
                  '版本号 530..549 连续无缺，V549 同时是「版本号最大」且「其目录序号 R121 为最大」，且 R121 下只有这一个 FACT_INDEX 目录（三项同时成立才写本文件）')
new = new.replace('它每��运行都会实测 sha256，本文件只是静态文本）。',
                  '它每次运行都会实测 sha256，本文件只是静态文本）。')
new = new.replace('V530..V547 是 18 个可独立复核的快照', 'V530..V549 是 20 个可独立复核的快照')
new = new.replace('D0 已钉 V547 的 sha256', 'D0 已钉 V549 的 sha256')
assert new != old
assert '\r' not in new
open(CUR, 'w', encoding='utf-8', newline='').write(new)

rb = open(CUR, 'rb').read()
rt = rb.decode('utf-8')
chk('N1 指针内的 sha256 与现盘 V549 一致', sha549 in rt, sha549[:16])
chk('N2 指针内的字节数与现盘 V549 一致', ('| 字节数 | %d |' % B549) in rt, B549)
chk('N3 不再残留 V547 / 旧 sha / 旧字节数',
    'V547' not in rt and '919263cf' not in rt and '109220' not in rt,
    {'v547': rt.count('V547'), 'old_sha': rt.count('919263cf'), 'old_bytes': rt.count('109220')})
chk('N4 历史版本段已含 V548 与 V549（20 个快照）', 'V548' in rt and 'V549' in rt and '20 个' in rt, 'ok')
chk('N5 LF-only', rb.count(b'\r') == 0, rb.count(b'\r'))
chk('N6 声明轮次 R169', '| 声明轮次 | R169 |' in rt, 'ok')

out = {'v549_sha': sha549, 'v549_bytes': B549, 'cur_sha_before': sha(src),
       'cur_sha_after': sha(rb), 'backup': os.path.basename(bak),
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169n_pointer.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
