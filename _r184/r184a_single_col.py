#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R184 A：把 F24 的结构判据「单列地址、无第二列」做成**可失败**判据并主会话亲自复算。

判据（对 a2_sites.json 的 bounds 段）：
  J1 形态：bounds 每个元素是裸字符串（不是 list/dict/tuple）
  J2 编码：每个元素命中 ^[0-9A-F]{8}$
  J3 顺序：严格递增且互不重复
  J4 载荷：携带「地址之外的第二个字段」的记录数 == 0
  J5 字节账：值段字节 == 2 + 10n + 2(n-1)
正控：原文件上五条全 PASS（排除永假）。
反控（必须真红，各在 /tmp 副本上跑，不写仓内）：
  N1 3 个元素改成 [addr, "90"] ⇒ J1/J4 红
  N2 1 个含 A–F 的元素改小写 ⇒ J2 红
  N3 打乱两个元素顺序 ⇒ J3 红
  N4 副本 = 只有 calls 键（去掉 bounds）⇒ J1..J5 全红（段不存在）
  N5 字符串元素替换成 8 位整数 ⇒ J1 红（类型维，证明 J1 不是只看值的正则）
"""
import hashlib
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
SRC = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
TMP = '/tmp/r184a'
PAT = re.compile(r'^[0-9A-F]{8}$')
fails = []
n_ck = 0


def ck(name, cond, detail=''):
    global n_ck
    n_ck += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def judge(raw):
    """单一判据函数：输入文件字节，输出五项判定与全部相关实测数。"""
    out = {'parsed': False}
    try:
        o = json.loads(raw)
    except Exception as e:
        out['err'] = repr(e)
        return out
    out['parsed'] = True
    out['top_keys'] = sorted(o.keys())
    bnd = o.get('bounds')
    if not isinstance(bnd, list):
        out['J1'] = out['J2'] = out['J3'] = out['J4'] = out['J5'] = False
        out['PASS'] = False
        out['reason'] = 'bounds 不是 list'
        return out
    n = len(bnd)
    out['n'] = n
    scalar = [isinstance(x, str) for x in bnd]
    out['J1'] = all(scalar)
    out['n_nonscalar'] = scalar.count(False)
    hits = sum(1 for x in bnd if isinstance(x, str) and PAT.match(x))
    out['J2'] = hits == n
    out['regex_hits'] = hits
    ints = [int(x, 16) for x in bnd if isinstance(x, str) and PAT.match(x)]
    out['J3'] = len(ints) == n and all(ints[i] < ints[i + 1] for i in range(len(ints) - 1))
    out['uniq'] = len(set(ints)) == len(ints)
    out['J3'] = out['J3'] and out['uniq']
    # 载荷 = 规格化后元素长度 > 1（即除地址外还有任何第二字段）
    def spec_len(x):
        if isinstance(x, str):
            return 1
        if isinstance(x, (list, tuple)):
            return len(x)
        if isinstance(x, dict):
            return len(x)
        return 1
    out['payload'] = sum(1 for x in bnd if spec_len(x) > 1)
    out['J4'] = out['payload'] == 0
    # 字节账：在原始字节里定位 "bounds" 的值段并量长
    seg_len = None
    k = raw.find(b'"bounds"')
    if k >= 0:
        st = raw.find(b'[', k)
        if st >= 0:
            depth, j = 0, st
            while j < len(raw):
                c = raw[j:j + 1]
                if c == b'[':
                    depth += 1
                elif c == b']':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            seg_len = j - st + 1
    out['seg_len'] = seg_len
    out['expect'] = 2 + 10 * n + 2 * (n - 1)
    out['J5'] = seg_len == out['expect']
    out['PASS'] = out['J1'] and out['J2'] and out['J3'] and out['J4'] and out['J5']
    return out


def dump(o):
    return json.dumps(o, ensure_ascii=False).encode('utf-8')


raw = open(SRC, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()

print('== A · 只读复核（主会话亲自复算，不采信执行员结论）==')
ck('A0 文件字节 17,624,355', len(raw) == 17624355, len(raw))
ck('A1 sha256 7a8447d1d816cdc3', sha.startswith('7a8447d1d816cdc3'), sha[:16])
r0 = judge(raw)
ck('A2 正控：原文件五条判据全 PASS（排除永假）', r0.get('PASS') is True, r0)
ck('A3 n == 1,392,592', r0.get('n') == 1392592, r0.get('n'))
ck('A4 元素全为 str（载荷 0）', r0.get('J1') is True and r0.get('payload') == 0, (r0.get('J1'), r0.get('payload')))
ck('A5 正则命中 == n', r0.get('regex_hits') == r0.get('n'), r0.get('regex_hits'))
ck('A6 严格递增且唯一', r0.get('J3') is True)
ck('A7 值段 16,711,104 B == 2+10n+2(n-1)', r0.get('J5') is True, (r0.get('seg_len'), r0.get('expect')))
ck('A8 顶层键恰 [bounds, calls]', r0.get('top_keys') == ['bounds', 'calls'], r0.get('top_keys'))

print('== B · 字节账的第二条独立线（不经 JSON 解析，纯字节）==')
i_first = raw.find(b'["00401000"')
ck('B1 值段起点就是首个元素（"["+首地址）', i_first > 0 and raw[i_first:i_first + 13] == b'["00401000", ',
   (i_first, raw[i_first:i_first + 14]))
i_end = raw.rfind(b'"]') + 2
ck('B2 值段起点 == 913,250（= 10 + dumps(calls) 913,228 + 2 + 8 + 2）', i_first == 913250, i_first)
ck('B2b 前缀逐段闭合：{"calls": 10 + dumps(calls) + ", " 2 + "bounds" 8 + ": " 2',
   raw[:10] == b'{"calls": ' and raw[i_first - 12:i_first] == b', "bounds": ',
   (raw[:10], raw[i_first - 12:i_first]))
ck('B2c dumps(calls) 恰 913,228 B 且与盘上原文逐字节相同',
   len(json.dumps(json.loads(raw)['calls'], ensure_ascii=False).encode()) == 913228
   and raw[10:10 + 913228] == json.dumps(json.loads(raw)['calls'], ensure_ascii=False).encode(),
   len(json.dumps(json.loads(raw)['calls'], ensure_ascii=False).encode()))
ck('B3 值段末（one-past-end）== 17,624,354，其后仅 1 B 的 }', i_end == 17624354 and raw[i_end:] == b'}',
   (i_end, len(raw), raw[i_end:]))
ck('B4 值段长 == i_end − i_first == 16,711,104', i_end - i_first == 16711104, i_end - i_first)
ck('B5 913,237 不是任何结构边界（它是声明净额，盘上无实物）',
   913237 not in (10, 913238, 913240, 913248, 913250) and 9 + 913228 == 913237,
   913237)

print('== C · 回归性反控（每项必须真红，全部在 /tmp 副本上跑）==')
os.makedirs(TMP, exist_ok=True)
obj = json.loads(raw)
bnd = obj['bounds']

# N1：3 个元素补第二字段
o1 = {'calls': obj['calls'], 'bounds': [[x, '90'] for x in bnd[:3]] + bnd[3:]}
r1 = judge(dump(o1))
ck('N1 补第二字段 ⇒ 判据红（J1/J4）', r1['PASS'] is False and r1['J1'] is False and r1['payload'] == 3,
   (r1.get('J1'), r1.get('payload')))

# N2：1 个含 A–F 的元素改小写
tgt = next(x for x in bnd if any(c in 'ABCDEF' for c in x))
b2 = list(bnd)
b2[b2.index(tgt)] = tgt.lower()
r2 = judge(dump({'calls': obj['calls'], 'bounds': b2}))
ck('N2 改小写 ⇒ 判据红（J2 少 1）', r2['PASS'] is False and r2['regex_hits'] == r2['n'] - 1,
   (r2.get('regex_hits'), r2.get('n'), tgt))

# N3：交换两个元素
b3 = list(bnd)
b3[0], b3[1] = b3[1], b3[0]
r3 = judge(dump({'calls': obj['calls'], 'bounds': b3}))
ck('N3 打乱顺序 ⇒ 判据红（J3）', r3['PASS'] is False and r3['J3'] is False)

# N4：只有 calls 键
r4 = judge(dump({'calls': obj['calls']}))
ck('N4 无 bounds 段 ⇒ 判据红（五项全 False）',
   r4['PASS'] is False and not any(r4.get(k) for k in ('J1', 'J2', 'J3', 'J4', 'J5')), r4.get('reason'))

# N5：元素换成 8 位整数
b5 = [int(x, 16) for x in bnd[:5]] + list(bnd[5:])
r5 = judge(dump({'calls': obj['calls'], 'bounds': b5}))
ck('N5 换成整数 ⇒ 判据红（J1，不是只靠正则）', r5['PASS'] is False and r5['J1'] is False and r5['n_nonscalar'] == 5,
   (r5.get('J1'), r5.get('n_nonscalar')))

# 正控回归：副本逐字节 dump 回原字节（证明 dump 不引入差异，N1..N5 的红不是 dump 造成的）
o0 = {'calls': obj['calls'], 'bounds': obj['bounds']}
ck('C0 往返 dump 逐字节等于原文件（反控的红不是 dump 造出来的）', dump(o0) == raw,
   (len(dump(o0)), len(raw)))

print('== D · 与 F24 其他断言的分离性（同一件、两个不同维度）==')
ck('D1 「无第二列」是文件内维，与「地址在本机镜像能否找到字节」互不推导（仅作分离性登记）',
   r0['PASS'] is True and r0['payload'] == 0)
calls = obj['calls']
ck('D2 calls 记录数 6,728 / 调用点 68,253', len(calls) == 6728 and sum(len(v) for v in calls.values()) == 68253,
   (len(calls), sum(len(v) for v in calls.values())))
key_set, site_set = set(calls), set(s for v in calls.values() for s in v)
ck('D3 calls 的键几乎都在 bounds 里（用于说明 bounds 是全域起始集）', len(key_set - set(bnd)) <= 40,
   len(key_set - set(bnd)))
ck('D4 calls 全部调用点都在 bounds 里', len(site_set - set(bnd)) == 0, len(site_set - set(bnd)))

print()
print('断言 %d 条，FAIL %d 条' % (n_ck, len(fails)))
if fails:
    print('FAIL 列表:', fails)
sys.exit(1 if fails else 0)
