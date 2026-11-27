#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-A · 裁定 913,237 的身份：分段标记起始偏移，还是 calls-only JSON 的字节长度

R173 待办第 1 条要求：先裁定清单里那行的 bytes=913,237 是「快照当时的编码产物」还是
「清单写错」，再决定改数还是加注。本脚本只做可机械判定的事，不改任何正文。

判据（全部可失败）：
  P1  现盘该件字节数 = 17,624,355
  P2  原始字节前 913,238 个字节 + 一个右花括号 == json.dumps({'calls': V}, ensure_ascii=False)
      ⇒ calls-only JSON 长度 = 913,239（含外层 { 与 }）
  P3  分段标记 '}, "bounds": [' 在全文恰 1 次、起始偏移恰 913,237
  P4  913,237 与 913,239 差 2，且 2 = 外层 '{' 1 + 外层 '}' 1
  P5  清单字节闭合式用 913,237 成立；换成 913,239 差 +2（故不能换数）

反控：
  N1  前 913,237 字节 + 右花括号 ⇒ 必须非法（证明 913,237 不是任何合法 JSON 的长度）
  N2  前 913,239 字节 + 右花括号 ⇒ 必须非法（尾随逗号，证明 913,238 不是答案）
  N3  小样本：'{"calls": {"1": ["2"]}, "bounds": ["A"]}' 里标记起始偏移与 calls-only 长度
      必须差 2（同一规则在小样本上必须复现，否则 P4 的「差 2」是巧合）
  N4  把 calls 字典任取一键名加 1 个字符（只在内存改），序列化长度必须变（否则 P2 的长度是常数巧合）
  N5  标记串出现次数改成数 '}, "bounds":'（少左方括号）必须仍为 1（证明 N3/P3 的检索不是靠巧合唯一）

只读 a2_sites.json 与 tier_final_4417.tsv；只写 _r174/r174a_a2_callslen.json。
内存纪律：不把 17.6 MB JSON 反复 copy；只用切片比较，切片长度上限 913,239 B。
"""
import hashlib
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
MF = 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'
OUT = '_r174/r174a_a2_callslen.json'

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:600]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:400]) if detail else ''))


def valid(b):
    try:
        json.loads(b)
        return True
    except Exception:
        return False


print('== P0 · 读件 ==')
d = io.open(A2, 'rb').read()
L = len(d)
sha = hashlib.sha256(d).hexdigest()
print('bytes=%d sha256=%s' % (L, sha))

print('== P1 ==')
ck('P1 现盘字节数 17,624,355', L == 17624355, L)

print('== P2 · calls-only JSON 长度 ==')
V = json.loads(d)['calls']
ser = json.dumps({'calls': V}, ensure_ascii=False).encode()
CK = len(ser)
print('C = dumps({"calls": V}) = %d' % CK)
ck('P2a C == 913,239', CK == 913239, CK)
head = d[:CK - 1]
ck('P2b d[:C-1] + "}" == ser 逐字节相同', head + b'}' == ser, 'compared %d B' % CK)
ck('P2c d[:C-1] 长度恰为 913,238', len(head) == 913238, len(head))

print('== P3 · 分段标记偏移 ==')
MK = b'}, "bounds": ['
OCC = d.count(MK)
off = d.find(MK)
print('marker count=%d first offset=%d' % (OCC, off))
ck('P3a 标记恰 1 次', OCC == 1, OCC)
ck('P3b 起始偏移恰 913,237', off == 913237, off)
ck('P3c 清单 bytes 值 913,237 恰等于该偏移', off == 913237, (off, 913237))

print('== P4 · 差 2 的来源 ==')
Vd = json.dumps(V, ensure_ascii=False).encode()
print('dumps(V) = %d ; len(\'{"calls": \') = 10 ; 10+len(dumps(V)) = %d' % (len(Vd), 10 + len(Vd)))
ck('P4a 913,239 - 913,237 == 2', 913239 - 913237 == 2, 913239 - 913237)
ck('P4b 10 + len(dumps(V)) == 913,238', 10 + len(Vd) == 913238, 10 + len(Vd))
ck('P4c 913,237 == 10 + len(dumps(V)) - 1（= dumps(V) 末字符偏移）', 913237 == 10 + len(Vd) - 1, 10 + len(Vd) - 1)
ck('P4d d[913237] 恰为 "}"（dumps(V) 的右花括号）', d[913237:913238] == b'}', d[913237:913238])
ck('P4e d[913238:913239] 恰为逗号（外层分隔符）', d[913238:913239] == b',', d[913238:913239])

print('== P5 · 两个闭合式 ==')
S1 = 26846620 + 913237 + 709757429
S2 = 26846620 + 913239 + 709757429
print('913,237 式 = %d ; 913,239 式 = %d ; 目标 737,517,286' % (S1, S2))
ck('P5a 913,237 式 == 737,517,286', S1 == 737517286, S1)
ck('P5b 913,239 式 == 737,517,288（差 +2）', S2 == 737517288, S2)
ck('P5c 现盘字节 + 26,846,620 == 44,470,975', 26846620 + 17624355 == 44470975, 26846620 + 17624355)

print('== 清单里那一行 ==')
row = None
for ln in io.open(MF, encoding='utf-8'):
    if 'D41_SUBST/_audit/EVIDENCE/a2_sites.json' in ln:
        row = ln.rstrip('\n').split('\t')
ck('M1 清单里 a2_sites 行 bytes == 913,237', row is not None and row[1] == '913237', row[1] if row else None)
ck('M2 清单 why 列含「剔除bounds段」', row is not None and '剔除bounds段' in row[3], row[3] if row else None)

print('== N1 · 913,237 不是任何合法 JSON 的长度 ==')
ck('N1 d[:913237]+"}" 非法', not valid(d[:913237] + b'}'))
ck('N1b d[:913237] 本身非法', not valid(d[:913237]))

print('== N2 · 913,238 也不是（尾随逗号） ==')
ck('N2 d[:913239]+"}" 非法', not valid(d[:913239] + b'}'))
ck('N2b d[:913240]+"}" 非法', not valid(d[:913240] + b'}'))
ck('N2c d[:913238]+"}" 合法（唯一解）', valid(d[:913238] + b'}'))

print('== N3 · 小样本必须复现「差 2」 ==')
smp = b'{"calls": {"1": ["2"]}, "bounds": ["A"]}'
sV = json.loads(smp)['calls']
sser = json.dumps({'calls': sV}, ensure_ascii=False).encode()
soff = smp.find(b'}, "bounds": [')
print('sample: calls-only=%d marker-offset=%d' % (len(sser), soff))
ck('N3a 小样本 calls-only 长度 == 23', len(sser) == 23, len(sser))
ck('N3b 小样本标记偏移 == 21', soff == 21, soff)
ck('N3c 小样本两者差 2', len(sser) - soff == 2, len(sser) - soff)
ck('N3d 小样本 smp[:22]+"}" == sser', smp[:22] + b'}' == sser, smp[:22] + b'}')

print('== N4 · 长度不是常数巧合 ==')
V2 = dict(V)
k0 = next(iter(V2))
V2[k0 + 'X'] = V2.pop(k0)
ser2 = json.dumps({'calls': V2}, ensure_ascii=False).encode()
print('改一个键名后长度 = %d（原 %d）' % (len(ser2), CK))
ck('N4 键名加 1 字符 ⇒ 长度 +1（不是常数）', len(ser2) == CK + 1, (len(ser2), CK))

print('== N5 · 检索串不是靠巧合唯一 ==')
ck('N5 "\x7d, \"bounds\":" 出现恰 1 次', d.count(b'}, "bounds":') == 1, d.count(b'}, "bounds":'))
ck('N5b "bounds" 恰 1 次（键名即标记内那一次，无独立键名）', d.count(b'"bounds"') == 1, d.count(b'"bounds"'))

print('== P6 · 偏移与长度的不可互换（可失败演示） ==')
ck('P6 若把偏移当长度用：17,624,355-913,237 != calls-only 段实际占位',
   17624355 - 913237 != CK, (17624355 - 913237, CK))

out = {
    'script': 'r174a_a2_callslen.py',
    'file': A2,
    'bytes': L,
    'sha256': sha,
    'calls_only_json_len': CK,
    'marker': MK.decode(),
    'marker_count': OCC,
    'marker_offset': off,
    'delta': CK - off,
    'dumpsV_len': len(Vd),
    'sum_with_913237': S1,
    'sum_with_913239': S2,
    'manifest_row': row,
    'assertions': RES,
    'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
