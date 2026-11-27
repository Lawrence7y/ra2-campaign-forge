#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 I：把 C16 逐节下界表补上 §2.179 与 §2.180（172 → 174 节）。

存在理由（实测）：加 §2.180 后 check_disc 报「unpinned 2」，而 C16_UNPINNED_MAX == 2
⇒ 下一轮再加一节就会直接 FAIL。故本轮必须显式重钉（这正是 C16b 的设计意图）。

fail-closed 顺序（S-619/S-602 纪律）：
 1) 解析现有 C16_FLOORS 与 C16_FLOORS_SHA256，用**旧表**重算 sha 必须命中旧 pin（硬闸）；
 2) 实测 §2.179 / §2.180 的字节，floor = 实测 // 2（与既有 172 条同一口径）；
 3) 只插入 179/180 两行，其余 172 条逐条不变；
 4) 重算 sha、统一写盘、回读断言；
 5) 反控：把 180 的 floor 调大 1 ⇒ 新 sha 变化；删 180 整行 ⇒ sha 变化且 unpinned 变 1。
"""
import hashlib, io, json, os, re, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
CD = os.path.join(TIER, 'check_disc.py')
RC = os.path.join(TIER, 'R14_COMMON.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r175/r175i_c16.json')
stamp = time.strftime('%Y%m%d_%H%M%S')
fails, n, res = [], 0, {}
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)
    res[name] = bool(cond)

src = io.open(CD, encoding='utf-8').read()
m = re.search(r"^C16_FLOORS = \{\n(.*?)^\}", src, re.M | re.S)
ck('A1 找到 C16_FLOORS 表', m is not None, m is not None)
pairs = re.findall(r"^\s*(\d+):\s*(\d+),\s*$", m.group(1), re.M)
old_tbl = {int(k): int(v) for k, v in pairs}
ck('A2 旧表 172 条', len(old_tbl) == 172, len(old_tbl))
ck('A3 旧表最大 id 178、最小 7', (min(old_tbl), max(old_tbl)) == (7, 178), (min(old_tbl), max(old_tbl)))
old_pin = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src, re.M).group(1)
ck('A4 旧 pin == 5a767e7c…', old_pin.startswith('5a767e7c'), old_pin[:16])

def table_sha(tbl):
    return hashlib.sha256('\n'.join('%d:%d' % (k, tbl[k]) for k in sorted(tbl)).encode()).hexdigest()

ck('A5 用旧表按 check_disc 自身规范化重算 sha 命中旧 pin（硬闸，不命中不写盘）',
   table_sha(old_tbl) == old_pin, (table_sha(old_tbl)[:16], old_pin[:16]))

rc = io.open(RC, encoding='utf-8', newline='').read()
s179 = rc.rfind('## 2.179')
s180 = rc.rfind('## 2.180')
ck('B1 §2.179 定位成功且恰 1 次', s179 > 0 and rc.count('## 2.179') == 1, (s179, rc.count('## 2.179')))
ck('B2 §2.180 定位成功且恰 1 次', s180 > s179 and rc.count('## 2.180') == 1, (s180, rc.count('## 2.180')))
b179 = len(rc[s179:s180].encode('utf-8'))
b180 = len(rc[s180:].encode('utf-8'))
f179, f180 = b179 // 2, b180 // 2
print('     §2.179 = %d B ⇒ floor %d ; §2.180 = %d B ⇒ floor %d' % (b179, f179, b180, f180))
ck('B3 floor 均为正且小于实测（下界语义）', 0 < f179 < b179 and 0 < f180 < b180, (f179, b179, f180, b180))
ck('B4 179/180 不在旧表里', 179 not in old_tbl and 180 not in old_tbl, (179 in old_tbl, 180 in old_tbl))
ck('B5 §2.179 字节 > 既有最短节（不会误伤）', b179 > 20, b179)

new_tbl = dict(old_tbl)
new_tbl[179] = f179
new_tbl[180] = f180
ck('B6 新表 174 条', len(new_tbl) == 174, len(new_tbl))
ck('B7 原 172 条逐条不变', all(new_tbl[k] == old_tbl[k] for k in old_tbl), True)
new_pin = table_sha(new_tbl)
ck('B8 新 pin 与旧不同（否则 C16d 恒真）', new_pin != old_pin, (new_pin[:16], old_pin[:16]))

# ---- 反控 ----
t2 = dict(new_tbl); t2[180] = f180 + 1
ck('N1 把 180 的 floor 调大 1 ⇒ 表 sha 变化', table_sha(t2) != new_pin, (table_sha(t2)[:16], new_pin[:16]))
t3 = dict(new_tbl); del t3[180]
ck('N2 删 180 整行 ⇒ 表 sha 变化', table_sha(t3) != new_pin, (table_sha(t3)[:16], new_pin[:16]))
t4 = dict(new_tbl); t4[179] = old_tbl[178]
ck('N3 把 179 的 floor 抄成 178 的值 ⇒ 表 sha 变化', table_sha(t4) != new_pin, (table_sha(t4)[:16], new_pin[:16]))

# ---- 构造新源码 ----
anchors = sorted(old_tbl)[-1]
last_line = '    %d: %d,\n' % (anchors, old_tbl[anchors])
ck('C1 旧表末行锚串恰 1 次', src.count(last_line) == 1, src.count(last_line))
new_src = src.replace(last_line, last_line + '    179: %d,\n    180: %d,\n' % (f179, f180), 1)
new_src = new_src.replace("C16_FLOORS_SHA256 = '%s'" % old_pin, "C16_FLOORS_SHA256 = '%s'" % new_pin, 1)
ck('C2 新源码含 179/180 两行', ('    179: %d,\n' % f179) in new_src and ('    180: %d,\n' % f180) in new_src, True)
ck('C3 新源码 pin 已换', ("C16_FLOORS_SHA256 = '%s'" % new_pin) in new_src, new_pin[:16])
m2 = re.search(r"^C16_FLOORS = \{\n(.*?)^\}", new_src, re.M | re.S)
tbl2 = {int(k): int(v) for k, v in re.findall(r"^\s*(\d+):\s*(\d+),\s*$", m2.group(1), re.M)}
ck('C4 新源码可重解析出 174 条且与内存表逐条相等', tbl2 == new_tbl, (len(tbl2), tbl2 == new_tbl))
ck('C5 新源码可编译', compile(new_src, CD, 'exec') is not None, True)
dl = sum(1 for a, b in zip(src.split('\n'), new_src.split('\n')) if a != b)
print('     check_disc 差异行数 = %d（期望 2：插入 2 行 / pin 行改动合并计入）' % dl)

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails))
    io.open(OUT, 'w', encoding='utf-8').write(json.dumps({'fails': fails, 'res': res}, ensure_ascii=False, indent=1))
    sys.exit(1)

raw = io.open(CD, 'rb').read()
osha = hashlib.sha256(raw).hexdigest()
bak = os.path.join(BASE, 'check_disc.py.before_r175_c16_%s.bak' % stamp)
fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(raw)
ck('D1 备份 sha 命中旧 sha', hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == osha, os.path.basename(bak))
io.open(CD, 'w', encoding='utf-8', newline='').write(new_src)
back = io.open(CD, 'rb').read()
ck('D2 回读与构造一致', back == new_src.encode('utf-8'), len(back))
res.update({'old_pin': old_pin, 'new_pin': new_pin, 'floor179': f179, 'floor180': f180,
            'bytes179': b179, 'bytes180': b180, 'diff_lines': dl, 'assertions': n, 'fails': fails})
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
