#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 J：GATE_VER R147→R148 + C16_FLOORS 纳入 §2.153 + 五处钉重算。
顺序（与 R147 一致）：先在现表上复现旧钉 -> 再改表 -> 再重钉 -> 最后回读自洽。
"""
import hashlib, io, json, os, re, sys

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
GATE = os.path.join(BASE, 'check_disc.py')
RCH = os.path.join(BASE, 'DISC_RECHECK.tsv')
DUF = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')
TS = '20261127_033700'
FAILS = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)


def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()


def wr(p, s):
    io.open(p, 'w', encoding='utf-8', newline='').write(s)


def bak(p, tag):
    src = open(p, 'rb').read()
    dst = os.path.join(BL, os.path.basename(p) + '.before_r148_' + tag + '_' + TS + '.bak')
    with io.open(dst, 'xb') as f:
        f.write(src)
    ck('备份 wx 且逐字节相同 [%s]' % tag, open(dst, 'rb').read() == src, os.path.basename(dst))


# ---------- 0 C16 现表复现旧钉 ----------
g0 = rd(GATE)
ck('门禁 前置 CR == 0', g0.count('\r') == 0, g0.count('\r'))
old_pin = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", g0).group(1)


def c16_sha(tbl):
    return hashlib.sha256('\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl)).encode('utf-8')).hexdigest()


m = re.search(r'C16_FLOORS = \{(.*?)\n\}', g0, re.S)
body = m.group(1)
TBL = {}
for k, v in re.findall(r'(\d+):\s*(\d+)', body):
    TBL[int(k)] = int(v)
ck('0.1 现表 146 项', len(TBL) == 146, len(TBL))
ck('0.2 现表复现旧钉（算法一致）', c16_sha(TBL) == old_pin, [c16_sha(TBL)[:16], old_pin[:16]])

# ---------- 1 量 §2.153 正文并加表 ----------
rc = rd(os.path.join(BASE, 'R14_COMMON.md'))
cur, buf, sizes = None, [], {}
for l in rc.split('\n'):
    mm = re.match(r'^##\s+2\.(\d+)\b', l)
    if mm:
        if cur is not None:
            sizes[cur] = len('\n'.join(buf).encode('utf-8'))
        cur = int(mm.group(1))
        buf = [l]
    elif cur is not None:
        buf.append(l)
if cur is not None:
    sizes[cur] = len('\n'.join(buf).encode('utf-8'))
ck('1.1 §2.153 已存在于 R14_COMMON', 153 in sizes, sorted(sizes)[-3:])
ck('1.2 §2.153 正文 >= 8,000 B（不是空壳）', sizes[153] >= 8000, sizes[153])
ck('1.3 §2.152 仍在', 152 in sizes, sizes.get(152))
NEW_TBL = dict(TBL)
NEW_TBL[153] = sizes[153] - 21
ck('1.4 新表 147 项', len(NEW_TBL) == 147, len(NEW_TBL))
ck('1.5 旧 146 项一格未动', all(TBL[k] == NEW_TBL[k] for k in TBL), '')
new_pin = c16_sha(NEW_TBL)
ck('1.6 新钉 != 旧钉', new_pin != old_pin, [old_pin[:16], new_pin[:16]])

# ---------- 2 改表 + 重钉 ----------
g1 = re.sub(r"C16_FLOORS = \{.*?\n\}", 'C16_FLOORS = ' + repr(NEW_TBL).replace("'", ''), g0, count=1, flags=re.S)
# repr 的字典格式与既有风格不同但语义等价；改用规范化多行以免破坏可读性
lines = ['C16_FLOORS = {']
keys = sorted(NEW_TBL)
row = []
for i, k in enumerate(keys):
    row.append('%d: %d' % (k, NEW_TBL[k]))
    if len(row) == 5 or i == len(keys) - 1:
        lines.append('    ' + ', '.join(row) + (',' if i < len(keys) - 1 else ','))
        row = []
lines.append('}')
g1 = re.sub(r"C16_FLOORS = \{.*?\n\}", '\n'.join(lines), g0, count=1, flags=re.S)
ck('2.1 新表已写入源码', '153: %d' % NEW_TBL[153] in g1, NEW_TBL[153])
g1 = g1.replace("C16_FLOORS_SHA256 = '%s'" % old_pin, "C16_FLOORS_SHA256 = '%s'" % new_pin)
ck('2.2 C16_FLOORS_SHA256 已替换', new_pin in g1)
# 用源码文本回读表，验证与 NEW_TBL 一致
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', g1, re.S)
T2 = {int(k): int(v) for k, v in re.findall(r'(\d+):\s*(\d+)', m2.group(1))}
ck('2.3 源码回读表 == 目标表（147 项）', T2 == NEW_TBL, (len(T2), len(NEW_TBL)))
ck('2.4 源码回读表重算 == 新钉', c16_sha(T2) == new_pin, c16_sha(T2)[:16])

# ---------- 3 GATE_VER ----------
OLD_A = "grep=(?m)^GATE_VER = 'R147'"
NEW_A = "grep=(?m)^GATE_VER = 'R148'"
ck('3.1 门禁源码 GATE_VER 为 R147', "GATE_VER = 'R147'" in g1)
g1 = g1.replace("GATE_VER = 'R147'", "GATE_VER = 'R148'", 1)
ck('3.2 GATE_VER 已改 R148', "GATE_VER = 'R148'" in g1)

r0 = rd(RCH)
ck('3.3 DISC_RECHECK R147 锚点恰 1 次', r0.count(OLD_A) == 1, r0.count(OLD_A))
ck('3.4 DISC_RECHECK 尚未有 R148 锚点（幂等）', NEW_A not in r0)
r1 = r0.replace(OLD_A, NEW_A, 1)
ck('3.5 DISC_RECHECK CR == 0', r1.count('\r') == 0, r1.count('\r'))

d0 = rd(DUF)
ck('3.6 DISC_UNVERIFIABLE R147 锚点恰 1 次', d0.count(OLD_A) == 1, d0.count(OLD_A))
d1 = d0.replace(OLD_A, NEW_A, 1)


# ---------- 4 C7d / C7_ROW_SHA['20'] / FREEZE ----------
def c7d(raw):
    rows = [l.split('\t') for l in raw.split('\n')[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (x[0], x[4].strip(), x[5].strip()) for x in rows if len(x) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), rows


h_new, rrows = c7d(r1)
h_old_chk, _ = c7d(r0)
pin7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", g1).group(1)
ck('4.1 旧 C7d 钉 == 用旧 TSV 复现值', pin7 == h_old_chk, [pin7[:16], h_old_chk[:16]])
ck('4.2 新 C7d != 旧', h_new != pin7, [pin7[:16], h_new[:16]])
r20 = [x for x in rrows if len(x) == 7 and x[0] == '20'][0]
h20 = hashlib.sha256(('%s\t%s\t%s' % (r20[0], r20[4].strip(), r20[5].strip())).encode('utf-8')).hexdigest()
old20 = re.search(r"'20': '([0-9a-f]{64})'", g1).group(1)
ck('4.3 新 row20 != 旧', h20 != old20, [old20[:16], h20[:16]])
ck('4.4 新 row20 指向 R148 锚点', NEW_A in r20[5], r20[5][:40])
g1 = g1.replace("C7_TEXT_SHA256 = '%s'" % pin7, "C7_TEXT_SHA256 = '%s'" % h_new)
g1 = g1.replace("'20': '%s'" % old20, "'20': '%s'" % h20)
ck('4.5 两钉已替换', h_new in g1 and h20 in g1)

fr_old = re.search(r"FREEZE_SHA256 = '([0-9a-f]{64})'", g1).group(1)
ck('4.6 FREEZE 旧钉 == 旧 DU sha', fr_old == hashlib.sha256(d0.encode('utf-8')).hexdigest(), fr_old[:16])
fr_new = hashlib.sha256(d1.encode('utf-8')).hexdigest()
ck('4.7 FREEZE 新 != 旧', fr_new != fr_old, [fr_old[:16], fr_new[:16]])
g1 = g1.replace("FREEZE_SHA256 = '%s'" % fr_old, "FREEZE_SHA256 = '%s'" % fr_new)

if FAILS:
    print('\n=== 中止（前置不成立）: %d ===' % len(FAILS))
    for f in FAILS:
        print('  ' + f)
    json.dump(dict(fails=FAILS), open('/home/t628/projects/ra2-campaign-forge/_r148/r148j_repin.json',
                                      'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sys.exit(2)

bak(GATE, 'gate')
bak(RCH, 'dr')
bak(DUF, 'du')
wr(RCH, r1)
wr(DUF, d1)
wr(GATE, g1)

gb = rd(GATE)
ck('5.1 门禁回读 CR == 0', gb.count('\r') == 0, gb.count('\r'))
ck('5.2 门禁回读三钉自洽', new_pin in gb and h_new in gb and h20 in gb and fr_new in gb)
ck('5.3 门禁回读 GATE_VER R148', "GATE_VER = 'R148'" in gb)
rb = rd(RCH)
db = rd(DUF)
ck('5.4 DISC_RECHECK 回读 R148 恰 1 次 / R147 0 次',
   rb.count(NEW_A) == 1 and rb.count(OLD_A) == 0, (rb.count(NEW_A), rb.count(OLD_A)))
ck('5.5 DISC_UNVERIFIABLE 回读 R148 恰 1 次 / R147 0 次',
   db.count(NEW_A) == 1 and db.count(OLD_A) == 0, (db.count(NEW_A), db.count(OLD_A)))
ck('5.6 DISC_RECHECK 31 行', len([l for l in rb.split('\n') if l.strip()]) == 32,
   len([l for l in rb.split('\n') if l.strip()]))
ck('5.7 DISC_UNVERIFIABLE 12 行', len([l for l in db.split('\n') if l.strip()]) == 13,
   len([l for l in db.split('\n') if l.strip()]))

print('\nC16 表 146 -> %d 项；钉 %s -> %s' % (len(NEW_TBL), old_pin[:16], new_pin[:16]))
print('C7d %s -> %s' % (pin7[:16], h_new[:16]))
print('row20 %s -> %s' % (old20[:16], h20[:16]))
print('FREEZE %s -> %s' % (fr_old[:16], fr_new[:16]))
print('=== FAILS: %d ===' % len(FAILS))
for f in FAILS:
    print('  ' + f)
json.dump(dict(fails=FAILS, c16_old=old_pin, c16_new=new_pin, c7d_old=pin7, c7d_new=h_new,
               row20_old=old20, row20_new=h20, freeze_old=fr_old, freeze_new=fr_new,
               sec153_bytes=sizes[153]),
          open('/home/t628/projects/ra2-campaign-forge/_r148/r148j_repin.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
