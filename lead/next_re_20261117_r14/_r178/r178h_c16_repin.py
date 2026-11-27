# -*- coding: utf-8 -*-
"""r178h：C16 随 §2.183 重钉（176 -> 177 节）。

C16 规则：每节正文必须 >= 登记下界，下界 = 建表时实测字节的一半。
纪律：ast 取旧表与旧 pin，用旧表复算旧 sha 命中 C16_FLOORS_SHA256 作硬闸；只插新 id，
其余 176 条逐条不变；三条反控均须使表 sha 变。
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
fl = None
pin = None
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        if node.targets[0].id == 'C16_FLOORS':
            fl = ast.literal_eval(node.value)
        if node.targets[0].id == 'C16_FLOORS_SHA256':
            pin = ast.literal_eval(node.value)
ck('A1 取到 C16_FLOORS', fl is not None and len(fl) == 176, len(fl) if fl else None)
ck('A2 取到 C16_FLOORS_SHA256', pin is not None, pin[:16] if pin else None)
ck('A3 表内无 183', 183 not in fl)


def norm(d):
    return '\n'.join('%d:%d' % (k, d[k]) for k in sorted(d))


oldsha = hashlib.sha256(norm(fl).encode('utf-8')).hexdigest()
ck('B1 硬闸：旧表复算命中旧 pin', oldsha == pin, (oldsha[:16], pin[:16]))
if oldsha != pin:
    print('ABORT 硬闸未命中'); sys.exit(1)

rawrc = open(RC, 'rb').read()
txt = rawrc.decode('utf-8')
ck('B2 R14_COMMON CR=1081', rawrc.count(b'\r') == 1081, rawrc.count(b'\r'))
lines = txt.split('\n')
cur = None
buf = []
secs = {}
for l in lines:
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        if cur is not None:
            secs[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(m.group(1)); buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    secs[cur] = len('\n'.join(buf).encode('utf-8'))
ck('C1 实测节数 177', len(secs) == 177, len(secs))
ck('C2 183 在盘', 183 in secs, secs.get(183))
sz183 = secs[183]
floor183 = sz183 // 2
print('  §2.183 实测 %d B ⇒ 新 floor %d' % (sz183, floor183))
ck('C3 183 字节 > 0', sz183 > 0, sz183)

newfl = dict(fl)
newfl[183] = floor183
ck('D1 表 176 -> 177', len(newfl) == 177, len(newfl))
ck('D2 其余 176 条逐条不变', all(newfl[k] == fl[k] for k in fl), True)
newsha = hashlib.sha256(norm(newfl).encode('utf-8')).hexdigest()
ck('D3 新 sha 与旧不同', newsha != pin, newsha[:16])

# 三条反控
rc1 = dict(newfl); rc1[183] += 1
ck('E1 反控 183 floor +1 ⇒ sha 变',
   hashlib.sha256(norm(rc1).encode()).hexdigest() != newsha)
rc2 = dict(newfl); del rc2[183]
ck('E2 反控 删 183 ⇒ sha 回到旧值',
   hashlib.sha256(norm(rc2).encode()).hexdigest() == pin)
rc3 = dict(newfl); rc3[182] = fl[182] + 1
ck('E3 反控 改 182 ⇒ sha 变',
   hashlib.sha256(norm(rc3).encode()).hexdigest() != newsha)

# 新源码：不自己拼缩进（实测 173..180 是 4 空格、181..182 是 3 空格，混排），
# 直接取盘上 182 那一行的**逐字原文**当锚点，在其后插入 183 行。
lines_src = src.split('\n')
i182 = [i for i, l in enumerate(lines_src) if re.match(r'^\s*182: \d+,$', l)]
ck('F0 盘上 182 行恰 1 处', len(i182) == 1, i182)
anchor = lines_src[i182[0]]
indent = anchor[:len(anchor) - len(anchor.lstrip())]
new_line = '%s183: %d,' % (indent, floor183)
ck('F1 新行缩进与 182 行相同', new_line.startswith(indent) and new_line.strip().startswith('183:'))
new_lines = lines_src[:i182[0] + 1] + [new_line] + lines_src[i182[0] + 1:]
new_src = '\n'.join(new_lines)
new_src = new_src.replace("C16_FLOORS_SHA256 = '%s'" % pin,
                          "C16_FLOORS_SHA256 = '%s'" % newsha, 1)
# S-608/S-587 同族：插入一行后 zip 逐行比会报「之后所有行都变了」（假变化 219 行）。
# 改为：确认新文件 = 旧文件在插入点前 + 1 新行 + 旧文件插入点后，再逐段逐字比。
ck('F2a 新文件 == 旧前段 + 新行 + 旧后段（结构化，不用 zip）',
   new_lines[:i182[0] + 1] == lines_src[:i182[0] + 1]
   and new_lines[i182[0] + 1] == new_line
   and new_lines[i182[0] + 2:] == lines_src[i182[0] + 1:], True)
diffs = [i for i, (a, b) in enumerate(zip(lines_src, new_lines)) if a != b]
# 逐行 zip 比在「插入一行」时会把插入点之后全部报成变化（S-608 同族）。
# 真实判据：所有 zip 报出的差异行都必须落在插入点之后（即全部由移位造成），
# 且插入点之前的行差集为空。这不是恒真断言：把 182 的 floor 改错会让 F2c 变红。
ck('F2b zip 差异全部落在插入点之后（移位，非内容变化）',
   all(i > i182[0] for i in diffs), (len(diffs), i182[0]))
ck('F2c 插入点之前的行逐字未变', lines_src[:i182[0] + 1] == new_lines[:i182[0] + 1])
pin_old = [l for l in lines_src if l.startswith('C16_FLOORS_SHA256')]
# 必须从替换后的 new_src 取，而不是替换前的 new_lines（首版写错，导致恒 FAIL）
pin_new = [l for l in new_src.split('\n') if l.startswith('C16_FLOORS_SHA256')]
ck('F2d pin 行确实被改（1 行）', len(pin_old) == 1 and len(pin_new) == 1 and pin_old != pin_new,
   (pin_old[0][:40] if pin_old else None, pin_new[0][:40] if pin_new else None))
ck('F2e 新 pin 行含新 sha', newsha in pin_new[0] and pin not in pin_new[0])
ck('F3 行数 +1', src.count('\n') + 1 == new_src.count('\n'),
   (src.count('\n'), new_src.count('\n')))
# 反控：新源码里 ast 解析出的表必须等于 newfl
tree2 = ast.parse(new_src)
fl2 = None
for node in tree2.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id == 'C16_FLOORS':
        fl2 = ast.literal_eval(node.value)
ck('F4 新源码 ast 解出的表 == 预期新表', fl2 == newfl,
   (len(fl2) if fl2 else None, newfl.get(183)))

if FAIL:
    print('ABORT %d FAIL' % FAIL); sys.exit(1)
if '--dry' in sys.argv:
    print('--dry 未写盘。新 pin = %s' % newsha)
    print('---- %d PASS / %d FAIL (dry) ----' % (PASS, FAIL)); sys.exit(0)

bak = os.path.join(BASE, 'check_disc.py.before_r178_C16.bak')
with open(bak, 'xb') as f:
    f.write(src.encode('utf-8'))
ck('G1 备份 sha == 前态', hashlib.sha256(open(bak, 'rb').read()).hexdigest()
   == hashlib.sha256(src.encode()).hexdigest())
open(CD, 'w', encoding='utf-8', newline='').write(new_src)
ck('G2 回读一致', open(CD, encoding='utf-8').read() == new_src)
print()
print('新 C16_FLOORS_SHA256 = %s' % newsha)
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
