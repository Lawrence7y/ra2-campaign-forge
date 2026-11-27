#!/usr/bin/env python3
"""R169 N（校验版）：FACT_INDEX_CURRENT.md 指针 V549 的回读校验。

首版两条断言写错（S-563）：
  · N3 要求「全文不含 V547」，但第 22 行「补一个 V547 草稿就会静默指错」是**举例说明**，
    本来就该保留 —— 判据应是「V547 只出现在举例句里，不出现在版本目录/路径/sha/字节数字段」；
  · N4 要求「V548 与 V549 都出现」，但历史段用的是区间写法 V530..V549，V548 被区间覆盖，
    不应要求字面出现 —— 判据应是「区间上界 == V549 且快照数 == 549-530+1 == 20」。
本版只读校验，不再写盘。
"""
import hashlib, json, re, os
ROOT = '/home/t628/projects/ra2-campaign-forge'
T = ROOT + '/lead/next_re_20261117_r14'
CUR = T + '/FACT_INDEX_CURRENT.md'
V549 = T + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
V548 = T + '/R17_R120_FACTINDEX_V548/FACT_INDEX.tsv'

raw = open(V549, 'rb').read(); sha549 = hashlib.sha256(raw).hexdigest(); B549 = len(raw)
rb = open(CUR, 'rb').read(); rt = rb.decode('utf-8')
lines = rt.split('\n')

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

fields = [ln for ln in lines if ln.startswith('| ')]
chk('N1 指针 sha256 == 现盘 V549', sha549 in rt, sha549[:16])
chk('N2 指针字节数 == 现盘 V549', ('| 字节数 | %d |' % B549) in rt, B549)
chk('N3 V547 只出现在举例句里（不出现在任何表格字段行）',
    all('V547' not in ln for ln in fields),
    {'v547_in_fields': [ln[:60] for ln in fields if 'V547' in ln],
     'v547_lines': [ln[:60] for ln in lines if 'V547' in ln]})
chk('N4 历史区间上界 == V549 且快照数 == 20（= 549-530+1，V548 由区间覆盖）',
    'V530..V549' in rt and '20 个' in rt and (549 - 530 + 1) == 20, 'ok')
chk('N5 版本目录 / 相对路径指向 V549 目录',
    'R17_R121_FACTINDEX_V549' in rt and rt.count('R17_R121_FACTINDEX_V549') == 2,
    rt.count('R17_R121_FACTINDEX_V549'))
chk('N6 旧 sha / 旧字节数 / 旧版本目录三者全不残留',
    '919263cf' not in rt and '109220' not in rt and 'R17_R119_FACTINDEX_V547' not in rt, 'ok')
chk('N7 LF-only', rb.count(b'\r') == 0, rb.count(b'\r'))
chk('N8 声明轮次 R169 且守门脚本声明已指 V549',
    '| 声明轮次 | R169 |' in rt and 'D0 已钉 V549 的 sha256' in rt, 'ok')
chk('N9 反控：V548 仍在盘且 sha 未变（指针升级不删历史版本）',
    hashlib.sha256(open(V548, 'rb').read()).hexdigest().startswith('ef1716cf'), 'ef1716cf')

out = {'v549_sha': sha549, 'v549_bytes': B549, 'cur_sha': hashlib.sha256(rb).hexdigest(),
       'cur_bytes': len(rb), 'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open(ROOT + '/_r169/r169n_pointer.json', 'w'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:200])
print('FAIL count =', out['fail'])
