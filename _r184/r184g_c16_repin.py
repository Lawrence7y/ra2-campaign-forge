# -*- coding: utf-8 -*-
"""R184 G：C16 重钉 181 -> 182（把上一轮的 2.188 纳入），fail-closed：旧表复算命中旧 pin 作硬闸。
本轮新增的 2.189 留作 unpinned（1 <= C16_UNPINNED_MAX = 2）。
"""
import ast
import hashlib
import io
import os
import re
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
CD = os.path.join(TIER, 'check_disc.py')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0


def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


# S-184g1 自错（D3 当场抓出）：io.open(...).read() 默认做 universal newlines 翻译，
# 会把 CRLF 折成 LF ⇒ 写回时 499 行的行尾全被改成 LF。必须 newline='' 原样读。
# S-184g2 自错：初版把 CR 数写成 499（那是「按行号错位比对」算出的假差异数），
# 实测 check_disc 本来就是全 LF、CR == 0；真正的成因是下面这条被 D3 抓出的比对方式。
ck('A0 check_disc 全 LF（CR == 0、LF == 1344、75,318 B）',
   open(CD, 'rb').read().count(b'\r') == 0
   and open(CD, 'rb').read().count(b'\n') == 1344, 
   (open(CD, 'rb').read().count(b'\r'), open(CD, 'rb').read().count(b'\n')))
ck('A0b 默认读法会把 CR 折成 0（这就是 S-184g1 的成因）',
   io.open(CD, encoding='utf-8').read().count('\r') == 0)
src = io.open(CD, encoding='utf-8', newline='').read()
raw = src.encode('utf-8')
print('== A · 旧态 ==')
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
FL = ast.literal_eval('{' + m.group(1) + '}')
PIN = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src).group(1)
ck('A1 旧表 181 条 / 最大 id 187', len(FL) == 181 and max(FL) == 187, (len(FL), max(FL)))
ck('A2 旧 pin == 5311d6b9…', PIN.startswith('5311d6b9'), PIN[:16])
ck('A3 旧表复算命中旧 pin（硬闸）',
   hashlib.sha256('\n'.join('%d:%d' % (k, FL[k]) for k in sorted(FL)).encode()).hexdigest() == PIN)
ck('A4 check_disc 现体量 75,318 B', len(raw) == 75318, len(raw))

print('== B · 现盘实测 ==')
rc = io.open(os.path.join(TIER, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
secs = [(int(x.group(1)), x.start()) for x in re.finditer(r'(?m)^##\s+2\.(\d+)\b', rc)] + [(None, len(rc))]
body = {}
for i in range(len(secs) - 1):
    num, a = secs[i]
    body[num] = len(rc[a:secs[i + 1][1]].encode('utf-8'))
ck('B1 现盘 182 节（7..188）', sorted(body) == list(range(7, 189)), (len(body), min(body), max(body)))
ck('B2 旧表 181 条全部在现盘', all(k in body for k in FL))
unp = sorted(set(body) - set(FL))
ck('B3 未钉节 == [188]', unp == [188], unp)
ck('B4 2.188 实测 5,612 B', body[188] == 5612, body[188])
HALF = body[188] // 2
ck('B5 floor = 5,612 // 2 = %d' % HALF, HALF == 2806, HALF)

print('== C · 构造新表 ==')
NF = dict(FL)
NF[188] = HALF
NEWPIN = hashlib.sha256('\n'.join('%d:%d' % (k, NF[k]) for k in sorted(NF)).encode()).hexdigest()
ck('C1 新表 182 条 / 最大 id 188', len(NF) == 182 and max(NF) == 188)
ck('C2 新 pin != 旧 pin', NEWPIN != PIN, (NEWPIN[:16], PIN[:16]))
ck('C3 反控 A：188 floor 调大 1 ⇒ pin 变',
   hashlib.sha256('\n'.join('%d:%d' % (k, (NF[k] + 1 if k == 188 else NF[k]))
                            for k in sorted(NF)).encode()).hexdigest() != NEWPIN)
ck('C4 反控 B：删 188 ⇒ pin 变',
   hashlib.sha256('\n'.join('%d:%d' % (k, NF[k]) for k in sorted(NF) if k != 188)
                  .encode()).hexdigest() != NEWPIN)
ck('C5 其余 181 条逐条未变', all(NF[k] == FL[k] for k in FL))
ns = src.replace('   187: 4138,\n}', '   187: 4138,\n   188: %d,\n}' % HALF, 1)
ck('C6 表尾已插入 188', '   188: %d,\n}' % HALF in ns)
ns = ns.replace("C16_FLOORS_SHA256 = '%s'" % PIN, "C16_FLOORS_SHA256 = '%s'" % NEWPIN, 1)
ck('C7 pin 已换', ("C16_FLOORS_SHA256 = '%s'" % NEWPIN) in ns)

print('== D · 语法与新表可复算 ==')
C2 = {}
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', ns, re.S)
F2 = ast.literal_eval('{' + m2.group(1) + '}')
P2 = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", ns).group(1)
ck('D1 新表可 ast 取出 182 条', len(F2) == 182 and F2[188] == HALF)
ck('D2 新 pin == 新表规范化 sha',
   hashlib.sha256('\n'.join('%d:%d' % (k, F2[k]) for k in sorted(F2)).encode()).hexdigest() == P2)
print('     check_disc 差异行数 = %d' % sum(1 for a, b in zip(src.split('\n'), ns.split('\n')) if a != b))
# S-184g2 自错复现：初版用 zip 按行号逐位比对 ⇒ 表尾插入 1 行后其后 499 行全部错位，
# 「差异行数 = 499」是错位造出来的，不是真改了 499 行。改用 difflib 的编辑操作计数。
import difflib
_ops = [o for o in difflib.SequenceMatcher(None, src.split('\n'), ns.split('\n')).get_opcodes()
        if o[0] != 'equal']
ck('D3 编辑操作恰 3 个（表尾 insert 1 行 + pin replace 1 行 + 前一项的 equal 边界）',
   len(_ops) == 2, [(o[0], o[2] - o[1], o[4] - o[3]) for o in _ops])
_ins = [o for o in _ops if o[0] == 'insert']
_rep = [o for o in _ops if o[0] == 'replace']
ck('D4 恰 1 处 insert（插入 188 行）', len(_ins) == 1 and (_ins[0][4] - _ins[0][3]) == 1,
   [(o[0], o[4] - o[3]) for o in _ins])
ck('D5 恰 1 处 replace（pin 行，各 1 行）',
   len(_rep) == 1 and (_rep[0][2] - _rep[0][1]) == 1 and (_rep[0][4] - _rep[0][3]) == 1,
   [(o[0], o[2] - o[1], o[4] - o[3]) for o in _rep])

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    sys.exit(1)

print('== E · 写盘 ==')
o = hashlib.sha256(raw).hexdigest()
bak = os.path.join(BASE, 'check_disc.py.before_r184c16_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('E1 备份独占且 sha 相同', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
assert open(CD, 'rb').read() == raw
io.open(CD, 'w', encoding='utf-8', newline='').write(ns)
back = open(CD, 'rb').read()
ck('E2 回读一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(ns.encode('utf-8')).hexdigest())
print('   check_disc.py %d -> %d B ; sha %s…' % (len(raw), len(back), hashlib.sha256(back).hexdigest()[:16]))
print()
print('断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('C16_FLOORS 181 -> 182 条 ; pin %s… -> %s…' % (PIN[:16], NEWPIN[:16]))
sys.exit(1 if fails else 0)
