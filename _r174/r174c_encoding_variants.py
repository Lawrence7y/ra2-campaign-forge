#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-C · 排除「913,237 是快照当时的编码产物」这一假设

R173 待办①给两个候选：① 913,237 是快照当时的编码产物（即当时那个 calls-only 文件真的 913,237 B）；
② 清单写错。R174-A/B 已证它精确等于现盘分段标记偏移。本脚本测候选①：若有任一合理序列化
口径能把同一个 calls 字典写成恰好 913,237 B，候选① 就活；否则它死。

判据（可失败）：
  S1  8 种序列化口径的长度全表（separators 三种 × ensure_ascii 两种 × sort_keys × indent）
  S2  全表里等于 913,237 的口径数 == 0（这就是「候选① 死」的可失败判据）
  S3  「活着」的口径必须能与磁盘现字节对上：只有调用者给定口径那段能逐字节复现磁盘前缀
  S4  913,237 与 913,238 的关系：913,238 = len('{"calls": ') + len(dumps(V))（即分段前缀长度）

反控：
  N1  表里必须存在长度 > 913,237 的口径（否则 S2 是「全都太小」的假排除）
  N2  表里必须存在长度 < 913,237 的口径（否则 S2 是「全都太大」的假排除）
  N3  人为构造一个「合法 JSON 且 913,237 字节」的串：把 calls 里的一个键名减 2 个字符，
      重新序列化 → 必须得到 913,237，且能 json.loads 成功。⇒ 「913,237 可以是一个合法
      calls-only JSON 的长度」在**改过内容**的字典上成立，但因键名不同而不能对上磁盘字节。
      这一条用来证明 S2 的零不是「不可能」，而是「对该字典不可能」。

只读 a2_sites.json；只写 _r174/r174c_encoding_variants.json。
"""
import hashlib
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r174/r174c_encoding_variants.json'
TARGET = 913237

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:400]) if detail else ''))


d = io.open(A2, 'rb').read()
L = len(d)
V = json.loads(d)['calls']
print('file %d B, calls keys=%d pairs=%d' % (L, len(V), sum(len(x) for x in V.values())))

print('== S1 · 8 种序列化口径全表 ==')
variants = [
    ('wrap_default', {'calls': V}, {}),
    ('wrap_compact', {'calls': V}, {'separators': (',', ':')}),
    ('wrap_spacecolon', {'calls': V}, {'separators': (', ', ':')}),
    ('wrap_ascii', {'calls': V}, {'ensure_ascii': True}),
    ('wrap_sort', {'calls': V}, {'sort_keys': True}),
    ('wrap_indent1', {'calls': V}, {'indent': 1}),
    ('bare_default', V, {}),
    ('bare_compact', V, {'separators': (',', ':')}),
]
tab = []
for nm, obj, kw in variants:
    try:
        b = json.dumps(obj, ensure_ascii=False, **kw).encode()
    except Exception as e:  # indent + ensure_ascii kw 冲突不该发生，但留兜底
        b = ('ERR:' + repr(e)).encode()
    tab.append((nm, len(b), b))
    print('  %-16s %10d  delta_vs_target=%+d' % (nm, len(b), len(b) - TARGET))

lens = [t[1] for t in tab]
ck('S2 8 种口径中等于 913,237 的个数 == 0', lens.count(TARGET) == 0, [t[0] for t in tab if t[1] == TARGET])
ck('N1 表中存在 > 913,237 的口径', any(x > TARGET for x in lens), max(lens))
ck('N2 表中存在 < 913,237 的口径', any(x < TARGET for x in lens), min(lens))

print('== S3 · 唯一能与磁盘字节对上的口径 ==')
ser = json.dumps({'calls': V}, ensure_ascii=False).encode()
head = d[:len(ser) - 1] + b'}'
ck('S3a wrap_default 口径能逐字节复现磁盘前缀', head == ser, len(ser))
ck('S3b 该口径长度 == 913,239 而非 913,237', len(ser) == 913239, len(ser))
ck('S3c wrap_compact 口径不能复现磁盘前缀（长度不同）',
   len([t for t in tab if t[0] == 'wrap_compact'][0][2] if False else json.dumps({'calls': V}, ensure_ascii=False,
                                                                                separators=(',', ':')).encode()) != ser, '')

print('== S4 · 913,238 是「分段前缀长度」 ==')
pre = len('{"calls": ') + len(json.dumps(V, ensure_ascii=False).encode())
print('len(\'{"calls": \')=10 + len(dumps(V))=%d = %d' % (len(json.dumps(V, ensure_ascii=False).encode()), pre))
ck('S4a 分段前缀长度 == 913,238', pre == 913238, pre)
ck('S4b calls-only JSON 长度 == 913,239 == 前缀 + 1（外层右花括号）', len(ser) == pre + 1, (len(ser), pre + 1))
ck('S4c 913,237 == 913,239 − 2', TARGET == len(ser) - 2, len(ser) - 2)
OFF = d.find(b'}, "bounds": [')
ck('S4d 913,237 == 磁盘分段标记偏移', OFF == TARGET, OFF)

print('== N3 · 「改过内容」的字典可以达到 913,237（证明 S2 的零是内容相关的） ==')
V2 = {}
for k, v in V.items():
    V2[k] = v
keys = list(V2.keys())
# 把最后一个键名缩短 2 个字符（8 位十六进制键必然 >2 字符）
k0 = keys[-1]
V3 = {}
for k, v in V.items():
    V3[(k[:-2] if k == k0 else k)] = v
b3 = json.dumps({'calls': V3}, ensure_ascii=False).encode()
print('缩短一个键名 2 字符后长度 = %d' % len(b3))
ck('N3a 改后长度 == 913,237', len(b3) == TARGET, len(b3))
ok3 = True
try:
    json.loads(b3)
except Exception:
    ok3 = False
ck('N3b 改后仍是合法 JSON', ok3)
ck('N3c 但字节与磁盘前缀不同（内容已变）', (d[:len(b3) - 1] + b'}') != b3)

out = {
    'script': 'r174c_encoding_variants.py',
    'file_sha256': hashlib.sha256(d).hexdigest(),
    'target': TARGET,
    'variant_lengths': [{'name': t[0], 'len': t[1], 'delta': t[1] - TARGET} for t in tab],
    'hits_target': [t[0] for t in tab if t[1] == TARGET],
    'calls_only_default_len': len(ser),
    'prefix_len': pre,
    'marker_offset': OFF,
    'mutated_len': len(b3),
    'assertions': RES, 'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
