# -*- coding: utf-8 -*-
"""r179h：C16 随 §2.184 重钉（177 -> 178 节）。

C16 规则：每节正文必须 >= 登记下界，下界 = 建表时实测字节的一半。
纪律：ast 取旧表与旧 pin，用旧表复算旧 sha 命中 C16_FLOORS_SHA256 作硬闸；只插新 id，
其余 177 条逐条不变；三条反控均须使表 sha 变。
"""
import ast, hashlib, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
CD = os.path.join(ROOT, 'lead/next_re_20261117_r14/check_disc.py')
RC = os.path.join(ROOT, 'lead/next_re_20261117_r14/R14_COMMON.md')
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_LEAD_BASELINE')
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


src = open(CD, encoding='utf-8').read()
tree = ast.parse(src)
fl = pin = None
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == 'C16_FLOORS':
            fl = ast.literal_eval(node.value)
        if node.targets[0].id == 'C16_FLOORS_SHA256':
            pin = ast.literal_eval(node.value)
ck('A1 取到 C16_FLOORS（177 条）', fl is not None and len(fl) == 177, len(fl) if fl else None)
ck('A2 取到 C16_FLOORS_SHA256', pin is not None, pin[:16] if pin else None)
ck('A3 表内无 184', 184 not in fl)


def norm(d): return '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))


oldsha = hashlib.sha256(norm(fl).encode('utf-8')).hexdigest()
ck('B1 硬闸：旧表复算命中旧 pin', oldsha == pin, (oldsha[:16], pin[:16]))
if oldsha != pin:
    print('ABORT 硬闸未命中'); sys.exit(1)

rawrc = open(RC, 'rb').read()
ck('B2 R14_COMMON CR=1081', rawrc.count(b'\r') == 1081, rawrc.count(b'\r'))
lines = rawrc.decode('utf-8').split('\n')
cur = None; buf = []; secs = {}
for l in lines:
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None: secs[cur] = len('\n'.join(buf).encode())
        cur = int(m.group(1)); buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None: secs[cur] = len('\n'.join(buf).encode())
ck('C1 已测 178 节', len(secs) == 178, len(secs))
ck('C2 新增节恰 184 且 7275 B', secs.get(184) == 7275, secs.get(184))
floor_new = secs[184] // 2
ck('C3 新 floor = 7275 // 2 = 3637', floor_new == 3637, floor_new)
ck('C4 其余 177 节逐节字节未变（floor 仍成立）',
   all(secs[k] >= fl[k] for k in fl), [k for k in fl if secs[k] < fl[k]][:3])

newfl = dict(fl); newfl[184] = floor_new
ck('D1 表 177 -> 178 条', len(newfl) == 178)
ck('D2 只有 184 是新增键', sorted(set(newfl) - set(fl)) == [184])
ck('D3 其余 177 条逐条不变', all(newfl[k] == fl[k] for k in fl))

newnorm = norm(newfl)
newsha = hashlib.sha256(newnorm.encode('utf-8')).hexdigest()
ck('E1 新表 sha 与旧不同', newsha != pin, newsha[:16])
# 反控三条
c1 = dict(newfl); c1[184] = floor_new + 1
ck('F1 反控：184 floor +1 使 sha 变', hashlib.sha256(norm(c1).encode()).hexdigest() != newsha)
c2 = dict(newfl); del c2[184]
ck('F2 反控：删 184 使 sha 回到旧值', hashlib.sha256(norm(c2).encode()).hexdigest() == pin)
c3 = dict(newfl); c3[183] = newfl[183] + 1
ck('F3 反控：改 183 使 sha 变', hashlib.sha256(norm(c3).encode()).hexdigest() != newsha)

# 构造新源码：把 C16_FLOORS 的末项替换成「末项 + 新项」
# S-661：原稿按「4 空格缩进」写尾串，实测表项是 **3 空格缩进**（183: 4344,）⇒ G1 得 0 次。
old_tail = '   183: %d,\n}' % fl[183]
new_tail = '   183: %d,\n   184: %d,\n}' % (fl[183], floor_new)
ck('G1 旧表尾串恰 1 次', src.count(old_tail) == 1, src.count(old_tail))
src2 = src.replace(old_tail, new_tail, 1)
ck('G2 旧 pin 恰 1 次', src2.count("C16_FLOORS_SHA256 = '%s'" % pin) == 1)
src2 = src2.replace("C16_FLOORS_SHA256 = '%s'" % pin, "C16_FLOORS_SHA256 = '%s'" % newsha, 1)
a, b = src.split('\n'), src2.split('\n')
ck('G3 行数 +1', len(b) == len(a) + 1, (len(a), len(b)))
# S-662：原稿按**同下标**逐行比，插入一行后全体后移 ⇒ 差异列成几十行（假 FAIL）。
# 正确做法：从 b 里删掉那一行插入行，再与原文件逐行比，此时差异应恰为 pin 那一行。
_ins = '   184: %d,' % floor_new
ck('G4a 插入行恰 1 行', b.count(_ins) == 1, b.count(_ins))
b2 = [x for x in b if x != _ins]
ck('G4b 删掉插入行后行数与原件相同', len(b2) == len(a), (len(b2), len(a)))
diff = [i for i in range(len(a)) if a[i] != b2[i]]
ck('G4c 除 pin 行外逐行无改写', len(diff) == 1 and "C16_FLOORS_SHA256 = '" in a[diff[0]],
   [a[i][:40] for i in diff])

if FAIL:
    print('ABORT 未写盘'); sys.exit(1)
bp = os.path.join(BASE, 'R179_check_disc.before_c16_repin.bak')
if not os.path.exists(bp):
    fd = os.open(bp, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    with os.fdopen(fd, 'wb') as f: f.write(open(CD, 'rb').read())
if '--dry' in sys.argv:
    print('--dry 通过。新 pin = %s' % newsha); sys.exit(0)
open(CD, 'w', encoding='utf-8', newline='').write(src2)
ck('H1 回读一致', open(CD, encoding='utf-8', newline='').read() == src2)
print('新 C16 pin = %s' % newsha)
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
