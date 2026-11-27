#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 E：FACT_INDEX v5.40 -> v5.41，只对 F35 与 F24 两行做**追加式**补记（不改历史、不改别的行）。

F35：limitations 里 R138 段的「唯一一项即…两条整行」在 v5.40 已与同行 statement ④ 相反，
     本轮用【R152 补】把该句的成立范围钉死（v5.30–V5.33 才成立），不删除旧句。
F24：把三桶漂移的可重跑入口（清单 sha + 脚本 sha + 测量时刻）钉进正文。

写入纪律：wx 独占备份 -> 断言旧 sha/字节数/行数/CR -> 一次性写入 -> 回读校验 -> 其余 52 行逐字节相同。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
SRC = os.path.join(BASE, 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
DSTDIR = os.path.join(BASE, 'R17_R113_FACTINDEX_V541')
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
BAK = os.path.join(BASE, 'R17_LEAD_BASELINE',
                   'FACT_INDEX.tsv.before_R152_v541_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
PIN = json.load(open(os.path.join(ROOT, '_r152/r152d_buckets_pin.json')))
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


src = open(SRC, 'rb').read()
ck('1 源 88,786 B', len(src) == 88786, len(src))
ck('2 源 sha fabd1e57…',
   hashlib.sha256(src).hexdigest() == 'fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a',
   hashlib.sha256(src).hexdigest()[:16])
ck('3 源全 LF（CR 0）', b'\r' not in src, src.count(b'\r'))
text = src.decode('utf-8')
lines = text.split('\n')
ck('4 源 56 段（表头 + 54 行 + 尾空）', len(lines) == 56 and lines[-1] == '', len(lines))

rows = [l.split('\t') for l in lines if l.strip()]
hdr, data = rows[0], rows[1:]
ck('5 每行 5 列', all(len(r) == 5 for r in data), set(len(r) for r in data))
orig = {r[0]: list(r) for r in data}

# ---------- 追加文本 ----------
F35_ADD = (' **【R152 补·上句的成立范围】** 上文「本条 evidence_paths **唯一一项即该已失文件**」'
           '与「与 F23 并列的**两条整行证据链失联项**」两句，**只在 v5.30–V5.33 成立**：'
           '实测那四版 F35 第 4 列**恰 1 项且该项（`COVERAGE/PANEL.md`）失联**（1 项 / 0 活 / 1 失）；'
           '**自 v5.34 起第 4 列变 5 项**（0->5 的分界就在 V533->V534），v5.34–v5.41 每版恒为 '
           '**5 项 / 4 活 / 1 失**，整行全失联的事实项**只剩 F23**（`_r152/r152a` 1.1–1.3 与 '
           '`_r152/r152c` 1.4/1.5/2.5，共 9 断言）。⇒ 引用上两句**必须带「v5.33 及以前口径」**，'
           '脱作用域引用会与同行 statement ④ 直接相反。另：字面串在 V530/V531/V532 的 limitations 里 '
           '**0 次**（三版 limitations 均为 184 字符），首现于 **V533**（695 字符），v5.34 起每版**各残留 1 次**'
           '（同一句两串：`唯一一项即` 1 + `两条整行` 1）—— 即这两句是 **V533 写下的、V534 改成 5 项后未回收的残留句**，'
           '不是「一直如此」（`_r152/r152c` 2.1–2.4）。')

F24_ADD = (' **【R152 补·三桶漂移的可重跑入口】** 上文 65 / 64 / 4,352 三桶此前只给读数、未钉时刻与清单 sha，'
           '本轮补齐：**清单 `tier_final_4417.tsv` = 696,579 B / sha256 `%s` / 4,417 行**（sum(bytes) = 737,517,286）；'
           '**脚本 `_r148/r148b_f24_survival.py` sha256 `%s`**；**测量时刻 %s（UTC）**。'
           '同口径复算得：现盘**存在 65 件 / 44,470,975 B**、**与清单同字节 64 件 / 26,846,620 B**、'
           '**字节不同 1 件**（`a2_sites.json` 913,237 -> 17,624,355，差 **+16,711,118 B**）、'
           '**不存在 4,352 件 / 709,757,429 B**；三桶件数之和 **65 + 4,352 = 4,417**、'
           '按清单口径的字节和 **26,846,620 + 913,237 + 709,757,429 = 737,517,286** 逐字节闭合。'
           '正控：`rel` 拼仓库根 ⇒ 存在 **0 件**（证明根选对了）。'
           '（`_r152/r152d_buckets_pin.py` 10 断言 0 FAIL，记录 `_r152/r152d_buckets_pin.json`）'
           '⇒ 引用三桶必须同写**测量时刻 + 清单 sha**，否则不可复现。'
           % (PIN['list']['sha256'], PIN['script']['sha256'], PIN['measured_at_utc']))

# F35 追加到 limitations（第 5 列）；F24 追加到 statement（第 2 列）
ck('6 F35 锚点（limitations 尾）唯一', orig['F35'][4].endswith('而**具体数值不可重数**。'), orig['F35'][4][-40:])
ck('7 F24 锚点（statement 尾）唯一', orig['F24'][1].endswith('（反控实测，`r148b` 断言 10）。'),
   orig['F24'][1][-40:])
ck('8 F35 limitations 现长 1,433', len(orig['F35'][4]) == 1433, len(orig['F35'][4]))
ck('9 F24 statement 现长 5,375', len(orig['F24'][1]) == 5375, len(orig['F24'][1]))

new = {k: list(v) for k, v in orig.items()}
new['F35'][4] = new['F35'][4] + F35_ADD
new['F24'][1] = new['F24'][1] + F24_ADD
ck('10 F35 追加后长度 = 1433 + %d' % len(F35_ADD), len(new['F35'][4]) == 1433 + len(F35_ADD))
ck('11 F24 追加后长度 = 5375 + %d' % len(F24_ADD), len(new['F24'][1]) == 5375 + len(F24_ADD))

out_lines = ['\t'.join(hdr)] + ['\t'.join(new[r[0]]) for r in data] + ['']
out_text = '\n'.join(out_lines)
out = out_text.encode('utf-8')
ck('12 输出仍 56 段 / 全 LF', out_text.split('\n').__len__() == 56 and b'\r' not in out,
   (len(out_text.split('\n')), out.count(b'\r')))
ck('13 grade / evidence_paths 两列一字未动',
   all(new[k][2] == orig[k][2] and new[k][3] == orig[k][3] for k in orig), '')

# ---------- wx 备份 ----------
fd = os.open(BAK, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(src)
ck('14 备份 wx 独占创建且逐字节相同', open(BAK, 'rb').read() == src, os.path.basename(BAK))

# ---------- 写 ----------
os.makedirs(DSTDIR, exist_ok=True)
open(DST, 'wb').write(out)
back = open(DST, 'rb').read()
ck('15 回读一致', back == out, len(back))
ck('16 输出 54 数据行', len([l for l in back.decode('utf-8').split('\n') if l.strip()]) - 1 == 54, '')

# ---------- 其余 52 行逐字节相同 ----------
b0 = {l.split('\t')[0]: l for l in text.split('\n') if l.strip()}
b1 = {l.split('\t')[0]: l for l in back.decode('utf-8').split('\n') if l.strip()}
changed = [k for k in b0 if b0[k] != b1[k]]
ck('17 只有 F35 与 F24 两行变化', sorted(changed) == ['F24', 'F35'], changed)
ck('18 其余 52 行逐字节相同', len([k for k in b0 if b0[k] == b1[k]]) == 53, len([k for k in b0 if b0[k] == b1[k]]))

print('\n新 sha256 =', hashlib.sha256(back).hexdigest())
print('新字节数 =', len(back))
for (k, v) in sorted([('F35_lim', new['F35'][4]), ('F24_stmt', new['F24'][1])]):
    print('  %s: 新长 %d（+%d）' % (k, len(v), len(v) - len(orig[k.split("_")[0]][4 if k == 'F35_lim' else 1])))
json.dump({'src_bytes': len(src), 'src_sha256': hashlib.sha256(src).hexdigest(),
           'dst_bytes': len(back), 'dst_sha256': hashlib.sha256(back).hexdigest(),
           'changed': sorted(changed), 'fails': fails},
          open(os.path.join(ROOT, '_r152/r152e_write_v541.json'), 'w'), ensure_ascii=False, indent=1)
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
