#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-D · 判死候选①：913,237 不是「11-22 快照当时的编码产物」，而是清单声明列的转抄值

R173 待办①留两个候选：
  ① 913,237 是快照当时那份 calls-only 文件的真实字节数（即当时的编码产物）
  ② 清单的 bytes 列写的不是文件字节数，而是「剔段后应有体积」的声明值
本脚本用**当时的**快照表裁定：`_r67/unique_content_4417.tsv` 生成于 2026-11-22 21:16，
它有独立的 bytes 列与 decl_bytes 列，二者并列可比。

判据（可失败）：
  T1  unique_content 里该行 bytes == 17,624,355（= 现盘字节数），decl_bytes == 913,237
      ⇒ 同一个「11-22 时刻」，文件本身就是 17,624,355 B
  T2  该行 sha256 == 现盘 sha256（7a8447d1…）⇒ 内容自 11-22 未变
  T3  故候选① 死：当时的编解码产物不可能是 913,237
  T4  两表的 bytes 列在同一条 rel 上逐字不同（17,624,355 vs 913,237），
      而 tier_final 的 bytes 与 unique_content 的 decl_bytes 逐字相同
      ⇒ tier_final.bytes 记录的是声明值而非文件字节

反控：
  N1  全表 4,417 行里 bytes != decl_bytes 的行数必须恰 1（若有很多行，则本判据不具选择性）
  N2  该 1 行的 rel 必须是 a2_sites.json
  N3  sum(decl_bytes) 必须 == 737,517,286（证明 decl 列才是 F24 正文引用的那一列）
  N4  sum(bytes) 必须 == ≠ 737,517,286（证明 bytes 列不能用于 F24 的闭合式）
  N5  另取一行（bytes == decl_bytes 的正常行）验证两列确实相等、不是恒不等

只读 _r67/unique_content_4417.tsv、R17_R101 清单、a2_sites.json；只写 _r174/r174d_snapshot_verdict.json。
"""
import csv
import hashlib
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
UC = 'lead/next_re_20261117_r14/_r67/unique_content_4417.tsv'
TF = 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r174/r174d_snapshot_verdict.json'
REL = 'next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
TOTAL = 737517286

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:400]) if detail else ''))


uc_rows = list(csv.DictReader(io.open(UC, encoding='utf-8'), delimiter='\t'))
tf_rows = list(csv.DictReader(io.open(TF, encoding='utf-8'), delimiter='\t'))
print('unique_content rows=%d cols=%s' % (len(uc_rows), list(uc_rows[0].keys())))
print('tier_final rows=%d cols=%s' % (len(tf_rows), list(tf_rows[0].keys())))

uc = {r['rel']: r for r in uc_rows}
tf = {r['rel']: r for r in tf_rows}
ck('T0a 两表都含该 rel', REL in uc and REL in tf, (REL in uc, REL in tf))

print('== T1 · 11-22 当时的 bytes 列 ==')
u = uc[REL]
t = tf[REL]
print('unique_content: bytes=%s decl_bytes=%s' % (u['bytes'], u['decl_bytes']))
print('tier_final    : bytes=%s' % t['bytes'])
ck('T1a unique_content.bytes == 17,624,355', u['bytes'] == '17624355', u['bytes'])
ck('T1b unique_content.decl_bytes == 913,237', u['decl_bytes'] == '913237', u['decl_bytes'])
ck('T1c tier_final.bytes == 913,237', t['bytes'] == '913237', t['bytes'])

print('== T2 · 内容自 11-22 未变 ==')
sha_disk = hashlib.sha256(io.open(A2, 'rb').read()).hexdigest()
print('uc.sha256=%s' % u['sha256'])
print('disk sha =%s' % sha_disk)
ck('T2a 快照 sha256 == 现盘 sha256', u['sha256'] == sha_disk, (u['sha256'][:16], sha_disk[:16]))
ck('T2b 快照 sha256 == 7a8447d1d816cdc3…', sha_disk.startswith('7a8447d1d816cdc3'), sha_disk[:16])

print('== T3 · 候选① 死 ==')
ck('T3 同一时刻文件本身是 17,624,355 B ⇒ 不可能存在 913,237 B 的版本',
   u['bytes'] == '17624355' and u['decl_bytes'] == '913237' and u['sha256'] == sha_disk,
   'bytes=%s decl=%s sha_match=%s' % (u['bytes'], u['decl_bytes'], u['sha256'] == sha_disk))

print('== T4 · 两表的 bytes 列口径不同 ==')
ck('T4a tier_final.bytes == unique_content.decl_bytes', t['bytes'] == u['decl_bytes'], (t['bytes'], u['decl_bytes']))
ck('T4b tier_final.bytes != unique_content.bytes', t['bytes'] != u['bytes'], (t['bytes'], u['bytes']))

print('== N1/N2 · 选择性 ==')
diff = [r for r in uc_rows if r['bytes'] != r['decl_bytes']]
print('bytes != decl_bytes 的行数 = %d' % len(diff))
ck('N1 全表恰 1 行 bytes != decl_bytes', len(diff) == 1, len(diff))
ck('N2 该行的 rel 就是 a2_sites.json', len(diff) == 1 and diff[0]['rel'] == REL,
   diff[0]['rel'] if diff else None)

print('== N3/N4 · 两列的 sum ==')
s_decl = sum(int(r['decl_bytes']) for r in uc_rows)
s_bytes = sum(int(r['bytes']) for r in uc_rows)
print('sum(decl_bytes)=%d ; sum(bytes)=%d ; 目标 %d' % (s_decl, s_bytes, TOTAL))
ck('N3 sum(decl_bytes) == 737,517,286', s_decl == TOTAL, s_decl)
ck('N4 sum(bytes) != 737,517,286（差恰 16,711,118）', s_bytes != TOTAL and s_bytes - TOTAL == 16711118,
   s_bytes - TOTAL)

print('== N5 · 正常行两列确实相等 ==')
norm = [r for r in uc_rows if r['bytes'] == r['decl_bytes']]
ck('N5 其余 4,416 行 bytes == decl_bytes', len(norm) == 4416, len(norm))

print('== T5 · 与该件无关的旁证：tier_final 只有 4 列、无 sha 列 ==')
ck('T5a tier_final 列数 4', list(tf_rows[0].keys()) == ['rel', 'bytes', 'source', 'why_content'],
   list(tf_rows[0].keys()))
ck('T5b tier_final 全文无 sha256 字样', 'sha256' not in io.open(TF, encoding='utf-8').read().lower())
ck('T5c unique_content 有 sha256 列', 'sha256' in list(uc_rows[0].keys()), list(uc_rows[0].keys()))

out = {
    'script': 'r174d_snapshot_verdict.py',
    'unique_content_rows': len(uc_rows),
    'uc_row': u,
    'tf_row': t,
    'disk_sha256': sha_disk,
    'rows_bytes_ne_decl': len(diff),
    'sum_decl_bytes': s_decl,
    'sum_bytes': s_bytes,
    'delta': s_bytes - TOTAL,
    'verdict': 'candidate1_dead',
    'assertions': RES, 'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
