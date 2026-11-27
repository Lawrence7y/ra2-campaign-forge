#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 H：C16 下界重钉（把 §2.189 / §2.190 / §2.191 三节纳表，unpinned 3 -> 0）。

为什么必须做：R184 写 §2.189、R185 写 §2.190 时都未把它们钉进 C16_FLOORS，
本轮再写 §2.191 后 unpinned 变成 3 > C16_UNPINNED_MAX(2)，主门禁 C16b 判 FAIL
（这正是 C16b 存在的理由：新节不钉就等于白得一张永久免检票）。

沿 R170 同法：实测本节字节 -> floor = 一半 -> 重钉 C16_FLOORS_SHA256。
反控：GATE_VER / C7_TEXT_SHA256 / C14_TEXT_SHA256 / FREEZE_SHA256 一字未动。
"""
import hashlib, io, os, py_compile, re, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
CD = ROOT + '/lead/next_re_20261117_r14/check_disc.py'
RC = ROOT + '/lead/next_re_20261117_r14/R14_COMMON.md'
BAK = ROOT + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))
def sha(b): return hashlib.sha256(b).hexdigest()

b0 = open(CD, 'rb').read()
bak = os.path.join(BAK, 'check_disc.py.before_r186_C16.bak')
if not os.path.exists(bak):
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(b0)
ck('M0 备份 sha 相同', sha(open(bak, 'rb').read()) == sha(b0), bak.split('/')[-1])

txt = open(RC, 'rb').read().decode('utf-8')
segs = []; cur = None; buf = []
for line in txt.split('\n'):
    m = re.match(r'^##\s+2\.(\d+)\b', line)
    if m:
        if cur is not None: segs.append((cur, len('\n'.join(buf).encode())))
        cur = int(m.group(1)); buf = [line]
    elif cur is not None: buf.append(line)
if cur is not None: segs.append((cur, len('\n'.join(buf).encode())))
d = dict(segs)
ck('M1a §2.189 / §2.190 / §2.191 三节都在盘上', all(k in d for k in (189, 190, 191)), sorted(d)[-4:])
szs = {k: d[k] for k in (189, 190, 191)}
fls = {k: v // 2 for k, v in szs.items()}
ck('M1b 三节字节与 floor=一半', all(v > 1000 for v in szs.values()), (szs, fls))

src = open(CD, encoding='utf-8').read()
m = re.search(r'^C16_FLOORS = \{(.*?)^\}', src, re.M | re.S)
ns = {}; exec(m.group(0), ns)
F = dict(ns['C16_FLOORS']); old_len = len(F)
norm_old = '\n'.join('%d:%d' % (k, ns['C16_FLOORS'][k]) for k in sorted(ns['C16_FLOORS']))
sha_old = hashlib.sha256(norm_old.encode()).hexdigest()
cur_const = re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src, re.M).group(1)
ck('M2 旧表重算命中旧常量', sha_old == cur_const, (sha_old[:16], cur_const[:16]))
ck('M2b 旧表 182 条 / 189..191 均不在表内',
   old_len == 182 and not any(k in F for k in (189, 190, 191)), old_len)

for k in (189, 190, 191): F[k] = fls[k]
norm_new = '\n'.join('%d:%d' % (k, F[k]) for k in sorted(F))
sha_new = hashlib.sha256(norm_new.encode()).hexdigest()
ck('M3 新 sha != 旧 sha', sha_new != sha_old, (sha_new[:16], sha_old[:16]))

# 在 188: 2806, 之后插入三行（保持键有序；缩进取原行实际缩进）
m188 = re.search(r'^(\s*)188: 2806,[ \t]*$', src, re.M)
ck('M4a0 定位到 188: 2806 行', m188 is not None)
ind = m188.group(1)
ins = '\n'.join('%s%d: %d,' % (ind, k, fls[k]) for k in (189, 190, 191))
src2 = re.sub(r'^(\s*)188: 2806,[ \t]*$', lambda mm: mm.group(0) + '\n' + ins, src, count=1, flags=re.M)
ck('M4a 插入点命中（188 行后新增 3 行，缩进 = %r）' % ind, src2 != src and ins in src2)
src2 = re.sub(r"^C16_FLOORS_SHA256 = '[0-9a-f]{64}'", "C16_FLOORS_SHA256 = '%s'" % sha_new,
              src2, count=1, flags=re.M)
ck('M4b sha 常量已换', ("C16_FLOORS_SHA256 = '%s'" % sha_new) in src2, sha_new[:16])
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
io.open(CD, 'w', encoding='utf-8', newline='').write(src2)
py_compile.compile(CD, doraise=True)

src3 = open(CD, encoding='utf-8').read()
m3 = re.search(r'^C16_FLOORS = \{(.*?)^\}', src3, re.M | re.S)
ns3 = {}; exec(m3.group(0), ns3)
ck('M5 读回：三节在表内且值 = 一半',
   all(ns3['C16_FLOORS'].get(k) == fls[k] for k in (189, 190, 191)),
   {k: ns3['C16_FLOORS'].get(k) for k in (189, 190, 191)})
ck('M6 读回：其余 %d 条逐条不变' % (old_len),
   all(ns3['C16_FLOORS'][k] == ns['C16_FLOORS'][k] for k in ns['C16_FLOORS']), old_len)
ck('M7 新 sha 常量 == 由新表重算',
   re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src3, re.M).group(1) == sha_new, sha_new[:16])
ck('M8 反控：GATE_VER 未变（仍 R166）', re.search(r"^GATE_VER = '([^']+)'", src3, re.M).group(1) == 'R166')
for name in ('C7_TEXT_SHA256', 'C14_TEXT_SHA256', 'FREEZE_SHA256'):
    v0 = re.search(r"^%s = '([0-9a-f]{64})'" % name, src, re.M).group(1)
    v1 = re.search(r"^%s = '([0-9a-f]{64})'" % name, src3, re.M).group(1)
    ck('M9 反控：%s 一字未动' % name, v0 == v1, v0[:16])
ck('M10 反控：表条数 182 -> 185', len(ns3['C16_FLOORS']) == 185, len(ns3['C16_FLOORS']))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('C16_FLOORS: %d -> %d 条；新增 %s；floor 各取本节字节一半' % (old_len, len(ns3['C16_FLOORS']), fls))
sys.exit(1 if fails else 0)
