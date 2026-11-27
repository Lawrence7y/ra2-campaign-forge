#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R173 G：把 facts_floors.py 与 gate_runner.py 重钉到 V554。

fail-closed 顺序（严格遵守 S-582 纪律）：
 1) 先备份（wx 独占），断言备份 sha256 == 当前文件 sha256；
 2) 用 ast 从源码取常量（**不用正则**，S-582 就是这么算出假 MASTER 的）；
 3) 用**旧常量**按门禁自己的 canon 五函数复算 MASTER，必须命中旧 MASTER —— 否则不写盘；
 4) 一次性写入 -> 回读断言 sha256 改变且内容按预期只改了 5 处；
 5) 改完实跑，必须 exit 0。
"""
import ast, hashlib, io, json, os, re, shutil, subprocess, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FL = os.path.join(ROOT, '_r160', 'facts_floors.py')
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
NEWDIR = 'R17_R126_FACTINDEX_V554'
NEWSHA = '5de4084b76bbd0e786898beeefe9197bddb599f97bd122635afaee43b98c86b0'
NEWBYTES = 123851
stamp = time.strftime('%Y%m%d_%H%M%S')

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

def bak(p, tag):
    d = os.path.join(BASE, '%s.before_r173_%s_%s.bak' % (os.path.basename(p), tag, stamp))
    fd = os.open(d, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    return d

# ---- 1) 备份 ----
fl_bak = bak(FL, 'v554')
gr_bak = bak(GR, 'v554')
ck('B1 两份备份独占创建成功', os.path.isfile(fl_bak) and os.path.isfile(gr_bak), (fl_bak, gr_bak))
ck('B2 备份 sha256 == 当时文件 sha256',
   hashlib.sha256(open(fl_bak, 'rb').read()).hexdigest() == hashlib.sha256(open(FL, 'rb').read()).hexdigest(),
   hashlib.sha256(open(fl_bak, 'rb').read()).hexdigest()[:16])

# ---- 2) ast 取常量（不用正则）----
src = io.open(FL, encoding='utf-8').read()
tree = ast.parse(src)
consts = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS',
                    'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ',
                    'EXPECT_CUR'):
            try:
                consts[name] = ast.literal_eval(node.value)
            except Exception:
                pass

# S-600：首版 A1 写「11 个」，ast 实取 12 个 ⇒ 假 FAIL；
# S-601：首版 A2 拿 64 位 sha 的 [:16] 去比 8 字符字面量，恒不等 ⇒ 假 FAIL。改成 startswith。
ck('A1 ast 取到 12 个常量、且 EXPECT_CUR 不在其中（它是 join 表达式）',
   len(consts) == 12 and 'EXPECT_CUR' not in consts, sorted(consts))
ck('A2 旧 CUR_SHA256 以 988a9567 开头（V553）',
   consts['CUR_SHA256'].startswith('988a9567'), consts['CUR_SHA256'][:16])
ck('A3 旧 TOTAL_BYTES == 121,010', consts['TOTAL_BYTES'] == 121010, consts['TOTAL_BYTES'])

# ---- 3) 用旧常量复算 MASTER，必须命中旧值（硬闸）----
canon_g = lambda d: '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
canon_f = lambda d: '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
canon_e = lambda d: '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
canon_eb = lambda d: '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
canon_l = lambda d: '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))

def master(c):
    return hashlib.sha256(('\n'.join([
        c['CUR_SHA256'], str(c['TOTAL_BYTES']), canon_g(c['GRADES']), canon_f(c['FLOORS']),
        canon_e(c['EVID']), canon_eb(c['EVIDB']), canon_l(c['LOST']),
        str(c['ITEMS']), str(c['UNIQ']), str(c['LOST_ITEMS']), str(c['LOST_UNIQ'])])).encode()).hexdigest()

m_old = master(consts)
ck('A4 用旧常量复算 MASTER 命中旧 pin ce436f7a…（硬闸：不命中不写盘）',
   m_old == consts['MASTER_SHA256'], (m_old[:16], consts['MASTER_SHA256'][:16]))

# ---- 4) 计算新常量 ----
c2 = dict(consts)
c2['CUR_SHA256'] = NEWSHA
c2['TOTAL_BYTES'] = NEWBYTES
m_new = master(c2)
print('   新 MASTER 前 16 位:', m_new[:16])

# EXPECT_CUR 与 FLOORS 的替换
old_dir = re.search(r"R17_R\d+_FACTINDEX_V\d+", src).group(0)
ck('A5 源码里旧版本目录 == R17_R125_FACTINDEX_V553', old_dir == 'R17_R125_FACTINDEX_V553', old_dir)
old_c24 = consts['FLOORS']['F24']
old_e24 = consts['EVID']['F24']
new_src = src
subs = [
    ("EXPECT_CUR 目录", old_dir, NEWDIR, 1),
    ("CUR_SHA256", consts['CUR_SHA256'], NEWSHA, 1),
    ("TOTAL_BYTES", 'TOTAL_BYTES = %d' % consts['TOTAL_BYTES'], 'TOTAL_BYTES = %d' % NEWBYTES, 1),
    ("MASTER_SHA256", consts['MASTER_SHA256'], m_new, 1),
]
for label, a, b, want in subs:
    got = new_src.count(a)
    ck('A6 %s 在源码出现恰 %d 次（可唯一替换）' % (label, want), got == want, got)

for a, b in [(old_dir, NEWDIR), (consts['CUR_SHA256'], NEWSHA),
             ('TOTAL_BYTES = %d' % consts['TOTAL_BYTES'], 'TOTAL_BYTES = %d' % NEWBYTES),
             (consts['MASTER_SHA256'], m_new)]:
    new_src = new_src.replace(a, b)
ck('A7 替换后旧 sha 与旧 MASTER 在源码中 0 次',
   new_src.count(consts['CUR_SHA256']) == 0 and new_src.count(consts['MASTER_SHA256']) == 0, True)
ck('A8 替换后恰好改了 4 处（按行差分）',
   sum(1 for x, y in zip(src.split('\n'), new_src.split('\n')) if x != y) == 4,
   sum(1 for x, y in zip(src.split('\n'), new_src.split('\n')) if x != y))

# 语法仍合法
try:
    ast.parse(new_src)
    ck('A9 改后源码语法合法', True)
except SyntaxError as e:
    ck('A9 改后源码语法合法', False, e)

if fails:
    print('\n[FAIL-CLOSED] %d 条硬闸未过，不写盘。' % len(fails))
    sys.exit(1)

with open(FL, 'w', encoding='utf-8', newline='') as f:
    f.write(new_src)
back = io.open(FL, encoding='utf-8').read()
ck('C1 回读与计算值逐字节相同', back == new_src, len(back))
ck('C2 回读 sha256 已改变', hashlib.sha256(back.encode()).hexdigest() != hashlib.sha256(src.encode()).hexdigest(),
   hashlib.sha256(back.encode()).hexdigest()[:16])

# ---- gate_runner 只改版本样 ----
gsrc = io.open(GR, encoding='utf-8').read()
ck('D1 gate_runner 里旧目录出现恰 1 次（它只钉 LEDGER 这一处）',
   gsrc.count(old_dir) == 1, gsrc.count(old_dir))
# S-602：首版 D2 断言 gate_runner 里应出现旧 sha —— 实测 0 次，因为 gate_runner 用
# ^CUR_SHA256 正则**从 facts_floors.py 源码里读**该常量（第 185 行），自己只钉 LEDGER 目录。
# 这条断言方向反了（把「不该有」写成「应该有」）。改成断言它确实不持有该字面量，
# 并且它读 facts 的那条正则存在（否则 G3c 恒 None 而假通过）。
ck('D2 gate_runner 自己不持有 CUR_SHA256 字面量、但确有从 facts_floors 读它的正则（方向反了，S-602）',
   gsrc.count(consts['CUR_SHA256']) == 0
   and gsrc.count(r"^CUR_SHA256 = '([0-9a-f]{64})'") >= 1,
   (gsrc.count(consts['CUR_SHA256']), gsrc.count(r"^CUR_SHA256 = '([0-9a-f]{64})'")))
g2 = gsrc.replace(old_dir, NEWDIR).replace(consts['CUR_SHA256'], NEWSHA).replace(
    str(consts['TOTAL_BYTES']), str(NEWBYTES))
ck('D3 gate_runner 改后旧值 0 次', g2.count(old_dir) == 0 and g2.count(consts['CUR_SHA256']) == 0, True)
with open(GR, 'w', encoding='utf-8', newline='') as f:
    f.write(g2)
ck('D4 gate_runner 回读一致', io.open(GR, encoding='utf-8').read() == g2, True)
ck('D5 gate_runner 仍不持有行首 GATE_VER 常量（反控，R170 PA7）',
   not re.search(r'(?m)^GATE_VER\s*=', g2), True)

# ---- 5) 实跑 ----
r1 = subprocess.run([sys.executable, FL], capture_output=True, text=True, timeout=300)
ck('E1 facts_floors 实跑 exit 0', r1.returncode == 0, r1.returncode)
ck('E2 facts_floors 输出里 D0 == 5de4084b…', 'D0 sha=5de4084b' in r1.stdout, r1.stdout.split('\n')[:4])
ck('E3 facts_floors 输出里 D8 == 123851', 'total bytes: 123851' in r1.stdout, 'D8' in r1.stdout)
ck('E4 facts_floors 输出里 D9 前 16 位 == 新 MASTER', ('D9 master pin: %s' % m_new[:16]) in r1.stdout,
   [l for l in r1.stdout.split('\n') if 'D9' in l])
ck('E5 facts_floors 无 FAIL 行', not any(l.strip().startswith('FAIL') for l in r1.stdout.split('\n')),
   [l for l in r1.stdout.split('\n') if l.strip().startswith('FAIL')])

r2 = subprocess.run([sys.executable, GR], capture_output=True, text=True, timeout=300)
ck('F1 gate_runner 实跑 exit 0', r2.returncode == 0, r2.returncode)
ck('F2 gate_runner 输出 G1=G2=G3=ok', 'G1=ok' in r2.stdout and 'G2=ok' in r2.stdout and 'G3=ok' in r2.stdout,
   r2.stdout.strip().split('\n')[-3:])

print()
print('SUMMARY: %d assertions, %d FAIL' % (n, len(fails)))
json.dump(dict(fails=fails, asserts=n, master_old=consts['MASTER_SHA256'], master_new=m_new,
               bytes=NEWBYTES, sha256=NEWSHA, backups=[fl_bak, gr_bak]),
          open('/home/t628/projects/ra2-campaign-forge/_r173/r173g_repin.json', 'w'),
          ensure_ascii=False, indent=1)
sys.exit(1 if fails else 0)
