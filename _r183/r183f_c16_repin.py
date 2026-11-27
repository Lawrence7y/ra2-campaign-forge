# -*- coding: utf-8 -*-
"""R183 F：C16 重钉 180 -> 181（把 2.187 纳入），fail-closed：旧表复算命中旧 pin 作硬闸。
S-183f1：本脚本首次创建时因 cd 位置错落到 lead/ 下而未真正生成 ⇒ 四件套里「已重钉」的说法
         一度超前。本轮按「先跑真实脚本、再让文字成立」的顺序补跑；2.188 留作 unpinned。
"""
import ast, hashlib, io, os, re, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
CD = os.path.join(TIER, 'check_disc.py')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

src = io.open(CD, encoding='utf-8').read()
raw = src.encode('utf-8')
print('== A · 旧态 ==')
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
FL = ast.literal_eval('{' + m.group(1) + '}')
PIN = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src).group(1)
ck('A1 旧表 180 条 / 最大 id 186', len(FL) == 180 and max(FL) == 186, (len(FL), max(FL)))
ck('A2 旧 pin == 70f66602…', PIN.startswith('70f66602'), PIN[:16])
ck('A3 旧表复算命中旧 pin（硬闸）',
   hashlib.sha256('\n'.join('%d:%d' % (k, FL[k]) for k in sorted(FL)).encode()).hexdigest() == PIN)
ck('A4 check_disc 现体量 %d B' % len(raw), len(raw) > 0, len(raw))

print('== B · 现盘实测 ==')
rc = io.open(os.path.join(TIER, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
secs = [(int(x.group(1)), x.start()) for x in re.finditer(r'(?m)^##\s+2\.(\d+)\b', rc)] + [(None, len(rc))]
body = {}
for i in range(len(secs) - 1):
    num, a = secs[i]
    body[num] = len(rc[a:secs[i + 1][1]].encode('utf-8'))
ck('B1 现盘 182 节（7..188）', sorted(body) == list(range(7, 189)), (len(body), min(body), max(body)))
ck('B2 旧表 180 条全部在现盘', all(k in body for k in FL))
unp = sorted(set(body) - set(FL))
ck('B3 未钉节 == [187, 188]', unp == [187, 188], unp)
ck('B4 2.187 实测 %d B' % body[187], body[187] == 8277, body[187])
HALF = body[187] // 2
ck('B5 floor = 8,277 // 2 = %d' % HALF, HALF == 4138, HALF)

print('== C · 构造新表 ==')
NF = dict(FL); NF[187] = HALF
NEWPIN = hashlib.sha256('\n'.join('%d:%d' % (k, NF[k]) for k in sorted(NF)).encode()).hexdigest()
ck('C1 新表 181 条 / 最大 id 187', len(NF) == 181 and max(NF) == 187)
ck('C2 新 pin != 旧 pin', NEWPIN != PIN, (NEWPIN[:16], PIN[:16]))
ck('C3 反控 A：187 floor 调大 1 ⇒ pin 变',
   hashlib.sha256('\n'.join('%d:%d' % (k, (NF[k] + 1 if k == 187 else NF[k])) for k in sorted(NF)).encode()).hexdigest() != NEWPIN)
ck('C4 反控 B：删 187 ⇒ pin 变',
   hashlib.sha256('\n'.join('%d:%d' % (k, NF[k]) for k in sorted(NF) if k != 187).encode()).hexdigest() != NEWPIN)
ck('C5 其余 180 条逐条未变', all(NF[k] == FL[k] for k in FL))
ns = src.replace('   186: 3512,\n}', '   186: 3512,\n   187: %d,\n}' % HALF, 1)
ck('C6 表尾已插入 187', '   187: %d,\n}' % HALF in ns)
ns = ns.replace("C16_FLOORS_SHA256 = '%s'" % PIN, "C16_FLOORS_SHA256 = '%s'" % NEWPIN, 1)
ck('C7 pin 已换', ("C16_FLOORS_SHA256 = '%s'" % NEWPIN) in ns)
NF2 = ast.literal_eval('{' + re.search(r'C16_FLOORS = \{(.*?)\n\}', ns, re.S).group(1) + '}')
ck('C8 新源码表逐条相同', NF2 == NF)
ck('C9 新源码 pin 可复算命中',
   hashlib.sha256('\n'.join('%d:%d' % (k, NF2[k]) for k in sorted(NF2)).encode()).hexdigest() == NEWPIN)
ck('C10 可编译', compile(ns, CD, 'exec') is not None)
print('   差异行数 = %d' % sum(1 for a, b in zip(src.split('\n'), ns.split('\n')) if a != b))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)

o = hashlib.sha256(raw).hexdigest()
bak = os.path.join(BASE, 'check_disc.py.before_r183_c16_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f: f.write(raw)
ck('D1 备份独占且 sha 一致', hashlib.sha256(open(bak, 'rb').read()).hexdigest() == o)
io.open(CD, 'w', encoding='utf-8', newline='').write(ns)
back = open(CD, 'rb').read()
ck('D2 回读一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(ns.encode()).hexdigest())
print('   check_disc.py %d -> %d B（%+d）; sha %s -> %s' % (len(raw), len(back), len(back) - len(raw), o[:16], hashlib.sha256(back).hexdigest()[:16]))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
