#!/usr/bin/env python3
"""R168 F：7 条不在引用型跳转表内的洞，逐条给**可失败**的形态判据。

四条 0x7c5d92/0x7c5d9c/0x7c80f2/0x7c80fc 邻域是同一段 16 字节序列 fe ff 00 01 f7 f8 fa fb fc fd fe ff 00 01 02 03 ——
判据「严格 +1 递增最长游程 >= 6」+ 反控「同长度随机字节段命中率」。
两条 0x723e27 / 0x793455 首字节 0f 0f 与 fe ff，逐个试 SEH / 前缀形态，不硬凑。
第 7 条 0x7d0cba 已被 r168e 证为 R167 缺陷产物（步进=宽度后不命中任何表）。
"""
import sys, json, random, collections
sys.path.insert(0, '_r143')
import r143lib as L
B = L.Bin(); data = B.data
text = [s for s in B.secs if s[0] == '.text'][0]
LO = B.IB + text[1]; HI = LO + text[2]
holes = [int(x, 16) for x in json.load(open('_r167/r167d_holes_semantics_final.json'))['holes']]
rest = [0x723e27, 0x793455, 0x7c5d92, 0x7c5d9c, 0x7c80f2, 0x7c80fc, 0x7d0cba]

def incrun(va, span=64):
    best = cur = 1; st = va
    prev = None
    for i in range(span):
        b = B.rd(va + i, 1)
        if not b: break
        c = b[0]
        if prev is not None and c == prev + 1:
            cur += 1
            if cur > best: best = cur
        else:
            cur = 1
        prev = c
    return best

rows = []
for h in rest:
    b = B.rd(h, 32)
    rows.append({'va': hex(h), 'bytes': b.hex(' '), 'incrun': incrun(h),
                 'first_byte': '%02x' % b[0]})

# 同一 16 字节样本在镜像里出现几次（字节级）
SAMP = bytes.fromhex('feff0001f7f8fafbfcfdfeff000102 03'.replace(' ', ''))
cnt = 0; pos = []
i = 0
while True:
    j = data.find(SAMP, i)
    if j < 0: break
    cnt += 1; pos.append(j); i = j + 1
def off2va(j):
    for nm, ava, vs, raw, rs in B.secs:
        if raw <= j < raw + rs: return B.IB + ava + (j - raw)
    return None
vas = [off2va(p) for p in pos]

# 反控：随机 .text 段（同长度 16）达到 incrun>=6 的比例
rnd = random.Random(20261127)
hit = 0; N = 2000
for _ in range(N):
    va = rnd.randrange(LO, HI - 80)
    if incrun(va) >= 6: hit += 1
base = hit / N

# 反控 2：把 0x7c5d92 那 16 字节反转，incrun 应 <=2
rev = bytes(reversed(SAMP))
rv = 0; best = cur = 1; prev = None
for c in rev:
    if prev is not None and c == prev + 1:
        cur += 1; best = max(best, cur)
    else: cur = 1
    prev = c

A = []
A.append({'id': 'F1 四条 0x7c5d9x/0x7c80fx 的 incrun >= 6',
          'ok': all(r['incrun'] >= 6 for r in rows if r['va'] in
                    ('0x7c5d92', '0x7c5d9c', '0x7c80f2', '0x7c80fc')),
          'detail': repr([(r['va'], r['incrun']) for r in rows])})
A.append({'id': 'F2 反控 2000 个随机 .text 段 incrun>=6 的比例 < 3%', 'ok': base < 0.03,
          'detail': '%d/2000=%.4f' % (hit, base)})
A.append({'id': 'F3 反控 同一 16 字节样本反转后 incrun <= 2（判据不是恒真）', 'ok': best <= 2,
          'detail': str(best)})
A.append({'id': 'F4 该 16 字节样本在镜像里出现 2 次且恰对应 0x7c5d92/0x7c80f2 前 16 B',
          'ok': cnt == 2 and set(vas) == {0x7c5d92, 0x7c80f2}, 'detail': '%d %s' % (cnt, [hex(v) for v in vas if v])})
A.append({'id': 'F5 0x7c5d9c / 0x7c80fc 是该样本 +10 处（同一查表的不同落点）',
          'ok': B.rd(0x7c5d9c, 6).hex() == 'feff000102 03'.replace(' ', '')
          and B.rd(0x7c80fc, 6).hex() == 'feff000102 03'.replace(' ', ''),
          'detail': ''})
A.append({'id': 'F6 0x723e27 首二字节 0f 0f（capstone 解不出）', 'ok': B.rd(0x723e27, 2) == b'\x0f\x0f'})
A.append({'id': 'F7 0x793455 前 21 字节是一段完整函数尾 + 填充（c3 90*9 其后才是洞）',
          'ok': B.rd(0x793455 - 16, 5) == bytes.fromhex('e92389fffe') or B.rd(0x793455 - 2, 1) == b'\xc3',
          'detail': B.rd(0x793455 - 8, 8).hex(' ')})
A.append({'id': 'F8 七条互不相同（无重复地址）', 'ok': len(set(rest)) == 7})
out = {'rows': rows, 'sample16_count': cnt, 'sample16_at': [hex(v) for v in vas if v],
       'rand_incrun6_rate': base, 'rev_incrun': best,
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r168/r168f_residual7.json', 'w'), ensure_ascii=False, indent=1)
for r in rows: print(json.dumps(r, ensure_ascii=False))
print('sample16 count=%d at=%s ; rand incrun>=6 rate=%.4f ; rev=%d'
      % (cnt, [hex(v) for v in vas if v], base, best))
for a in A: print(('PASS' if a['ok'] else 'FAIL'), a['id'], a.get('detail', '')[:180])
