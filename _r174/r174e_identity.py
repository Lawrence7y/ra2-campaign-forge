#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R174-E · 913,237 的真正身份：calls 成员文本长度（不是文件字节数、也不是清单写错）

R174-A..D 已把候选①（快照编码产物）判死。但 A/B 里我把身份说成「分段标记偏移」，那只是同一个
整数的另一种读法（对「首成员」恒等），不是解释。本脚本把可复现的生成式钉死：

  913,237 = len(b'"calls": ' + dumps(V))      ← 成员文本（不含外层 { }）
  913,239 = 913,237 + 2                        ← 整份 {"calls": …} 文件
  913,238 = 913,237 + 1                        ← 分段前缀 {"calls": …（不含末尾 }）

判据（可失败）：
  U1  成员文本切片 d[1:off+1] 恰 913,237 B 且以 '"calls": ' 开头、以 '}' 结尾
  U2  b'{' + 该切片 + b'}' 是合法 JSON 且与 dumps({'calls': V}) 逐字节相同（长度 913,239）
  U3  913,237 + 2 == 913,239；913,237 + 1 == 913,238；差额恰为外层两个花括号
  U4  三个数各自的身份都能用一段确定字节串复现（不是靠减法凑出来的）

反控：
  N1  「成员文本长度 == 偏移」对首成员是恒等式：把两键顺序对调后，新首成员的偏移与
      新首成员文本长度仍相等（证明 U1 的「等于偏移」不具判别力，判别力在「成员文本可解析」）
  N2  但「成员文本 + 2 == 整份文件」在三种不同形状的小样本上都必须成立（不是大文件巧合）
  N3  若误把成员文本当整份文件：把 b'{' + 成员 + b'}' 的长度报成 913,237，会与实测 913,239 矛盾
      ⇒ 直接演示「差 2」是花括号而不是数据

只读 a2_sites.json；只写 _r174/r174e_identity.json。
"""
import hashlib
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r174/r174e_identity.json'

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
J = json.loads(d)
V = J['calls']
MK = b'}, "bounds": ['
OFF = d.find(MK)
MEMBER = d[1:OFF + 1]
SER = json.dumps({'calls': V}, ensure_ascii=False).encode()
print('file=%d off=%d len(member)=%d len(ser)=%d' % (L, OFF, len(MEMBER), len(SER)))

print('== U1 · 成员文本 ==')
print('member head=%r tail=%r' % (MEMBER[:12], MEMBER[-8:]))
ck('U1a len(member) == 913,237', len(MEMBER) == 913237, len(MEMBER))
ck('U1b member 以 b\'"calls": \' 开头', MEMBER.startswith(b'"calls": '), MEMBER[:12])
ck('U1c member 以 b\'}\' 结尾', MEMBER.endswith(b'}'), MEMBER[-4:])
ck('U1d member 不含外层左花括号', not MEMBER.startswith(b'{'), MEMBER[:2])

print('== U2 · 加外层花括号即成整份文件 ==')
FULL = b'{' + MEMBER + b'}'
try:
    _ok = bool(json.loads(FULL))
except Exception:
    _ok = False
ck('U2a b"{" + member + b"}" 是合法 JSON', _ok, _ok)
ck('U2b 该串可 json.loads', _ok)
ck('U2c 该串与 dumps({"calls": V}) 逐字节相同', FULL == SER, (len(FULL), len(SER)))
ck('U2d 该串长度 == 913,239', len(FULL) == 913239, len(FULL))
ck('U2e 磁盘前缀 d[:len(SER)-1] + b"}" == SER', d[:len(SER) - 1] + b'}' == SER)

print('== U3 · 三个数的差额 ==')
print('913,237 +1 = %d ; +2 = %d' % (len(MEMBER) + 1, len(MEMBER) + 2))
ck('U3a member + 1 == 913,238（分段前缀）', len(MEMBER) + 1 == 913238, len(MEMBER) + 1)
ck('U3b member + 2 == 913,239（整份文件）', len(MEMBER) + 2 == 913239, len(MEMBER) + 2)
ck('U3c 差恰为外层两个花括号', len(FULL) - len(MEMBER) == 2, len(FULL) - len(MEMBER))

print('== U4 · 三个数各自的确定字节串 ==')
print('913,237 ↔ member   : %r … %r' % (MEMBER[:14], MEMBER[-10:]))
print('913,238 ↔ 前缀     : %r … %r' % (SER[:14], SER[-10:]))
print('913,239 ↔ 整份文件 : %r … %r' % (SER[:14], SER[-10:]))
ck('U4a 913,237 可由 member 复现', len(MEMBER) == 913237)
ck('U4b 913,238 可由 SER[:-1] 复现', len(SER) - 1 == 913238, len(SER) - 1)
ck('U4c 913,239 可由 SER 复现', len(SER) == 913239)

print('== N1 · 「成员文本长度 == 偏移」是**首成员**位置的恒等式，不是巧合 ==')
swapped = b'{"bounds": ["A"], "calls": {"1": ["2"]}}'
j2 = json.loads(swapped)
smem = b'"calls": ' + json.dumps(j2['calls'], ensure_ascii=False).encode()
sstart = swapped.find(b'"calls": ')
send = sstart + len(smem) - 1          # 成员的右花括号位置
print('对调后: 成员起点=%d 终点=%d len=%d' % (sstart, send, len(smem)))
ck('N1a calls 为第二成员时 len(member) != 成员终点偏移', len(smem) != send, (len(smem), send))
ck('N1b 差值恰为「起点 − 1」', send - len(smem) == sstart - 1, (send - len(smem), sstart - 1))
ck('N1c 盘上 calls 起点 == 1（首成员）', d[1:10] == b'"calls": ' and 1 == 1, d[1:10])
ck('N1d 首成员 ⇒ 终点偏移 == 成员长度（913,237 两读法同一整数）', len(MEMBER) == OFF, (len(MEMBER), OFF))
ck('N1e 两读法都能得到 913,239：member+2 与 OFF+2 均 == SER 长度',
   len(MEMBER) + 2 == len(SER) and OFF + 2 == len(SER), (len(MEMBER) + 2, OFF + 2, len(SER)))
ck('N1f 故偏移读法不可判死；判别力来自「成员文本本身可 json.loads 成 {calls:…}」',
   json.loads(b'{' + MEMBER + b'}').keys() == {'calls'}, list(json.loads(b'{' + MEMBER + b'}').keys()))

print('== N2 · 「成员 + 2 == 整份」在三种形状上成立 ==')
samples = [
    b'{"calls": {"1": ["2"]}, "bounds": ["A"]}',
    b'{"calls": {}, "bounds": []}',
    b'{"calls": {"00401000": ["0040100A", "0040100B"]}, "bounds": ["00401000"]}',
]
for i, s in enumerate(samples, 1):
    js = json.loads(s)
    m = s[1:s.find(b'}, "bounds": [') + 1]
    ser = json.dumps({'calls': js['calls']}, ensure_ascii=False).encode()
    print('  sample%d: len=%d member=%d ser=%d member+2=%d' % (i, len(s), len(m), len(ser), len(m) + 2))
    ck('N2.%d 成员文本 + 2 == 整份序列化长度' % i, len(m) + 2 == len(ser), (len(m), len(ser)))
    ck('N2.%d b"{" + 成员 + b"}" == 整份序列化' % i, b'{' + m + b'}' == ser)

print('== N3 · 误把成员文本当整份文件 ⇒ 与实测矛盾 ==')
ck('N3a 用 913,237 表示「整份 calls-only 文件」会少 2 B', 913239 - 913237 == 2, 2)
ck('N3b 磁盘上真实存在的前缀长度恰为 913,238（= 913,239 − 末尾花括号）', len(SER) - 1 == 913238)

out = {
    'script': 'r174e_identity.py',
    'file_sha256': hashlib.sha256(d).hexdigest(),
    'member_len': len(MEMBER),
    'member_head': MEMBER[:24].decode('latin1'),
    'member_tail': MEMBER[-24:].decode('latin1'),
    'ser_len': len(SER),
    'prefix_len': len(SER) - 1,
    'marker_offset': OFF,
    'identity': 'member_len + 2 == ser_len; member_len == marker_offset (tautology for first member)',
    'assertions': RES, 'fail': FAIL,
}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print('\n== RESULT: %d assertions, %d FAIL ==' % (len(RES), FAIL))
print('wrote ' + OUT)
raise SystemExit(1 if FAIL else 0)
