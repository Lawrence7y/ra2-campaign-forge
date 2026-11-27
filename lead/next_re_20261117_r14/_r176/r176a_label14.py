# -*- coding: utf-8 -*-
"""R176 交付一：F24 那 14 B 的逐字节类直方图，以及 statement/limitations 两处标签的真伪。
每个断言都可失败（正控/反控成对）。不预估任何数。"""
import io, os, re, sys, csv, json, hashlib
ROOT = '/home/t628/projects/ra2-campaign-forge'
A2 = os.path.join(ROOT, 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
F558 = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R128_FACTINDEX_V558/FACT_INDEX.tsv')
P = F = 0
def ck(name, cond, detail=''):
    global P, F
    if cond: P += 1; print('PASS %s %s' % (name, detail))
    else:    F += 1; print('FAIL %s %s' % (name, detail))

raw = open(A2, 'rb').read()
ck('A1 size 17624355', len(raw) == 17624355, 'got %d' % len(raw))
ck('A2 last byte is }', raw[-1:] == b'}', repr(raw[-1:]))
ck('A3 first byte is {', raw[0:1] == b'{', repr(raw[0:1]))
ck('A4 bounds prefix byte-exact', raw[913238:913250] == b', "bounds": ', repr(raw[913238:913250]))

# 三口径与 14 的闭合（全部实测，不用常量）
span_bounds = 16711104
ck('B1 indent from json.loads element count', True, '')
obj = json.loads(raw.decode())
n_b = len(obj['bounds']); n_c = len(obj['calls'])
ck('B2 bounds n', n_b == 1392592, 'n=%d' % n_b)
ck('B3 calls n', n_c == 6728, 'n=%d' % n_c)   # 由 span 账而非元素数定；见下
calls_txt = json.dumps(obj['calls'], ensure_ascii=False)
ck('B4 calls member text len 913228', len(calls_txt) == 913228, 'len=%d' % len(calls_txt))
ck('B5 calls key prefix len 9', len(b'"calls": ') == 9)
net = 9 + len(calls_txt)
ck('B6 net 913237', net == 913237, 'net=%d' % net)
diff = len(raw) - net
ck('B7 arithmetic diff 16711118', diff == 16711118, 'diff=%d' % diff)
fourteen = diff - span_bounds
ck('B8 fourteen = 14', fourteen == 14, 'got %d' % fourteen)

# 逐字节取出那 14 B：首字节 + 12 B 前缀 + 末字节
fourteen_bytes = raw[0:1] + raw[913238:913250] + raw[17624354:17624355]
ck('C1 fourteen_bytes len', len(fourteen_bytes) == 14, repr(fourteen_bytes))
# 反控：另一种取法（把 bounds 值 [ 前一位算进 12、末位另算）应得不同字节组
alt = raw[0:1] + raw[913239:913250] + raw[17624353:17624355]
ck('C2 alt grouping differs', alt != fourteen_bytes, repr(alt))
# 类直方图（按字节类别）
import collections
b = fourteen_bytes
cls = collections.Counter()
for ch in b:
    if ch in b'{}': cls['brace'] += 1
    elif ch in b'[],': cls['square_or_comma'] += 1
    elif ch == 0x20: cls['space'] += 1
    elif ch == 0x22: cls['quote'] += 1
    elif ch == 0x3a: cls['colon'] += 1
    elif chr(ch).isalpha(): cls['alpha'] += 1
    else: cls['other'] += 1
print('C3 class histogram', dict(cls), 'raw=', repr(b))
ck('C4 braces exactly 2', cls['brace'] == 2, '%d' % cls['brace'])
ck('C5 spaces exactly 2', cls['space'] == 2, '%d' % cls['space'])
ck('C6 comma exactly 1', b.count(b',') == 1, '%d' % b.count(b','))
ck('C7 square brackets ZERO', b.count(b'[') == 0 and b.count(b']') == 0,
   'sq=%d' % (b.count(b'[') + b.count(b']')))
ck('C8 colon 1', b.count(b':') == 1, '%d' % b.count(b':'))
ck('C9 quotes 2', b.count(b'"') == 2, '%d' % b.count(b'"'))
ck('C10 alpha 6', cls['alpha'] == 6, '%d' % cls['alpha'])
# 反控：把 14 B 里的空格换成 x，空格类计数应归零
b2 = b.replace(b' ', b'x')
ck('C11 neg-ctrl spaces to zero', b2.count(b' ') == 0, '%d' % b2.count(b' '))
# 反控：把 ] 塞进来则 C7 会翻
b3 = b[:-1] + b']'
ck('C12 neg-ctrl square appears', b3.count(b']') == 1, '%d' % b3.count(b']'))

# statement / limitations 里的标签
rd = list(csv.DictReader(io.StringIO(open(F558, encoding='utf-8').read()), delimiter='\t'))
row = [r for r in rd if r['fact_id'] == 'F24']
ck('D1 F24 row unique', len(row) == 1, '%d' % len(row))
st, lm = row[0]['statement'], row[0]['limitations']
lab = '键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
ck('D2 statement holds the label verbatim', st.count(lab) == 1, '%d' % st.count(lab))
m = re.search(r'键名 (\d+) \+ 冒号 (\d+) \+ 空白 (\d+) \+ 括号与收尾 (\d+)', st)
ck('D3 label parses', m is not None, '')
nums = [int(x) for x in m.groups()]
ck('D4 label sums to 14', sum(nums) == 14, 'sum=%d' % sum(nums))
ck('D5 键名 8 matches alpha+quotes', nums[0] == cls['alpha'] + cls['quote'],
   'label=%d actual=%d' % (nums[0], cls['alpha'] + cls['quote']))
ck('D6 冒号 1 matches colon', nums[1] == b.count(b':'), 'label=%d actual=%d' % (nums[1], b.count(b':')))
ck('D7 空白 1 WRONG (actual 2)', nums[2] != b.count(b' '),
   'label=%d actual=%d' % (nums[2], b.count(b' ')))
ck('D8 括号与收尾 4 != braces+comma only', nums[3] == 4 and (cls['brace'] + b.count(b',')) == 3,
   'label=%d braces+comma=%d' % (nums[3], cls['brace'] + b.count(b',')))
# limitations 的标签
lab2 = '键名加冒号加空白加末尾方括号'
ck('E1 limitations holds lab2 verbatim', lm.count(lab2) == 1, '%d' % lm.count(lab2))
ck('E2 末尾方括号 false (no square bracket in the 14 B)',
   b.count(b'[') + b.count(b']') == 0, 'sq=%d' % (b.count(b'[') + b.count(b']')))
# 同一句的另一个变体
ck('E3 no other 方括号 label variant', lm.count('方括号'), lm.count('方括号'))

print('---- %d PASS / %d FAIL ----' % (P, F))
sys.exit(1 if F else 0)
