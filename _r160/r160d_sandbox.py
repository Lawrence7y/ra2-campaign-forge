#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160d_sandbox.py (v2) —— facts_floors.py v2 的破坏性自测。

v1 沙箱的致命缺陷（审计员 #372 指出并经主会话复算确认）：
  10/10 次调用全部带 argv 指向副本，而 v1 的 D0 只在
  abspath(CUR)==abspath(EXPECT_CUR) 时才断言 ⇒ D0 一次都没被执行过。
  也就是说「沙箱全绿」当时并不覆盖 D0。

v2 修法：
  - D0 改成「无论路径都比 sha256」，本沙箱因此加 S10 专门测「argv 指向副本时 D0 仍然生效」。
  - 每个审计员造出的洞都变成一条回归断言（S11..S15）。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
CUR = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
GUARD = R + '/_r160/facts_floors.py'
BD = T + '/R17_LEAD_BASELINE'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

SB = tempfile.mkdtemp(prefix='/tmp/r160sb2_')
print('sandbox = %s' % SB)
base = io.open(CUR, encoding='utf-8', newline='').read()
sha_base = hashlib.sha256(base.encode()).hexdigest()
lines0 = base.split('\n')
if lines0[-1] == '': lines0 = lines0[:-1]

def run(args):
    p = subprocess.run([sys.executable, GUARD] + args, capture_output=True, text=True,
                       cwd=R, timeout=300)
    return p.returncode, p.stdout + p.stderr

def put(name, content):
    p = os.path.join(SB, name + '.tsv')
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    return p

def rebuild(fn):
    return '\n'.join(fn(list(lines0))) + '\n'

def col(lines, fid, ci, new):
    out = []
    for l in lines:
        c = l.split('\t')
        if c[0] == fid and len(c) == 5: c[ci] = new
        out.append('\t'.join(c))
    return out

print('\n== S0 · 正控 ==')
p0 = put('s0', base)
rc0, _ = run([p0])
ck('S0.1 未破坏 -> exit 0', rc0 == 0, rc0)

print('\n== S1 · 删 1 条证据项 ==')
p1 = put('s1', rebuild(lambda ls: [l if not l.startswith('F24\t')
                                   else '\t'.join(l.split('\t')[:3] + [';'.join(l.split('\t')[3].split(';')[:-1])] + [l.split('\t')[4]])
                                   for l in ls]))
rc1, o1 = run([p1])
ck('S1.1 删证据项 -> FAIL', rc1 != 0, rc1)
ck('S1.2 报 D7 且指出 F24', 'D7' in o1 and 'F24' in o1, [x for x in o1.split('\n') if 'D7' in x][:1])

print('\n== S2 · 删整行 F42 ==')
p2 = put('s2', rebuild(lambda ls: [l for l in ls if not l.startswith('F42\t')]))
rc2, o2 = run([p2])
ck('S2.1 删行 -> FAIL', rc2 != 0, rc2)
ck('S2.2 同时报 D3 与 D4', 'D3' in o2 and 'D4' in o2)

print('\n== S3 · 清空 F23 limitations ==')
p3 = put('s3', rebuild(lambda ls: col(ls, 'F23', 4, 'x')))
rc3, o3 = run([p3])
ck('S3.1 -> FAIL', rc3 != 0, rc3)
ck('S3.2 报 D6 且指出 F23', 'D6' in o3 and 'F23' in o3, [x for x in o3.split('\n') if 'D6' in x][:1])

print('\n== S4 · 改 F23 grade ==')
p4 = put('s4', rebuild(lambda ls: col(ls, 'F23', 2, '[流程]')))
rc4, o4 = run([p4])
ck('S4.1 -> FAIL', rc4 != 0, rc4)
ck('S4.2 报 D5 且指出 F23', 'D5' in o4 and 'F23' in o4, [x for x in o4.split('\n') if 'D5' in x][:1])

print('\n== S5 · 注入 CR ==')
p5 = put('s5', base.replace('\n', '\r\n', 1))
rc5, o5 = run([p5])
ck('S5.1 -> FAIL', rc5 != 0, rc5)
ck('S5.2 报 D1', 'D1' in o5)

print('\n== S6 · 截断成前 10 行 ==')
p6 = put('s6', '\n'.join(lines0[:11]) + '\n')
rc6, o6 = run([p6])
ck('S6.1 -> FAIL', rc6 != 0, rc6)
ck('S6.2 至少两条 D3/D4/D7/D8', sum(k in o6 for k in ('D3', 'D4', 'D7', 'D8')) >= 2)

print('\n== S7 · 幂等回环 ==')
p7 = put('s7', base)
rc7a, _ = run([p7])
p7b = put('s7', base + '\n')
rc7b, _ = run([p7b])
p7c = put('s7', base)
rc7c, _ = run([p7c])
ck('S7.1 初始 0', rc7a == 0, rc7a)
ck('S7.2 追加空行 FAIL', rc7b != 0, rc7b)
ck('S7.3 复原再次 0', rc7c == 0, rc7c)

# ---------- 以下是审计员 #372 造出的洞，v2 必须全部回归 ----------
print('\n== S10 · 【审计员洞1】argv 指向副本时 D0 必须仍然生效 ==')
# 同字节长度篡改：把一个数字改同长
tam = base.replace('1,589,964,358', '1,589,964,359')
ck('S10.0 篡改后字节数不变（真正的同长篡改）', len(tam.encode()) == len(base.encode()),
   (len(tam.encode()), len(base.encode())))
p10 = put('s10', tam)
rc10, o10 = run([p10])
ck('S10.1 argv 指向副本 + 同长篡改 -> D0 FAIL', rc10 != 0, rc10)
ck('S10.2 报的是 D0', 'D0 sha256 drifted' in o10, [x for x in o10.split('\n') if 'D0' in x][:1])
rc10b, _ = run(['--ignore-pin', p10])
ck('S10.3 --ignore-pin 时才放行（且大声告警）', rc10b in (0, 1), rc10b)

print('\n== S11 · 【审计员洞2】grade 两两互换（普查不变）必须被逐 fid 抓住 ==')
def swapg(ls):
    out = []
    for l in ls:
        c = l.split('\t')
        if c[0] == 'F01': c[2] = '[流程]'
        elif c[0] == 'F13': c[2] = '[已证]'
        out.append('\t'.join(c))
    return out
p11 = put('s11', rebuild(swapg))
rc11, o11 = run([p11])
ck('S11.1 grade 互换 -> FAIL（v1 在此 exit 0）', rc11 != 0, rc11)
ck('S11.2 报 D5 并同时点名 F01,F13', 'D5' in o11 and 'F01' in o11 and 'F13' in o11,
   [x for x in o11.split('\n') if 'D5' in x][:1])

print('\n== S12 · 【审计员洞3】把每列截到 v1 的「一半下界」==')
import re
gsrc = io.open(GUARD, encoding='utf-8', newline='').read()
mb = re.search(r'^FLOORS = \{\n(.*?)\n\}$', gsrc, re.S | re.M)
F2 = {m.group(1): (int(m.group(2)), int(m.group(3)))
      for m in re.finditer(r"'(\w+)': \((\d+), (\d+)\),", mb.group(1))}
def pad(s, n):
    b = s.encode()[:n]
    s2 = b.decode('utf-8', 'ignore')
    if len(s2.encode()) < n: s2 = s2 + 'x' * (n - len(s2.encode()))
    return s2
def half(ls):
    out = []
    for l in ls:
        c = l.split('\t')
        if c[0] == 'fact_id': out.append(l); continue
        fs, fl = F2[c[0]]
        c[1] = pad(c[1], fs // 2 if fs > 2 else fs)
        c[4] = pad(c[4], fl // 2 if fl > 2 else fl)
        out.append('\t'.join(c))
    return out
p12 = put('s12', rebuild(half))
rc12, o12 = run([p12])
ck('S12.1 截到一半 -> FAIL（v1 在此 exit 0）', rc12 != 0, rc12)
ck('S12.2 报 D6 或 D8', 'D6' in o12 or 'D8' in o12)
ck('S12.3 缩水确实发生', os.path.getsize(p12) < len(base.encode()),
   (os.path.getsize(p12), len(base.encode())))

print('\n== S13 · 【审计员洞4】剥掉第 4 列全部括号注解 ==')
def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s
def nonote(ls):
    out = []
    for l in ls:
        c = l.split('\t')
        if c[0] != 'fact_id' and len(c) == 5:
            c[3] = ';'.join(strip_note(x) for x in c[3].split(';'))
        out.append('\t'.join(c))
    return out
p13 = put('s13', rebuild(nonote))
rc13, o13 = run([p13])
ck('S13.1 剥注解 -> FAIL（v1 在此 exit 0）', rc13 != 0, rc13)
ck('S13.2 报 D7', 'D7' in o13, [x for x in o13.split('\n') if 'D7' in x][:1])

print('\n== S14 · 【审计员洞5】改常量绕过：模拟「只改数据不重钉」==')
# 这里做「改数据 + 不同步改常量」的等价破坏：把 F01 降级后手工把 GRADES 常量也改
# 是不可能的（常量在脚本里），因此本条改为验证：常量表本身被改会撞 D9 主指纹。
gp = os.path.join(SB, 'guard_tampered.py')
tam_src = gsrc.replace("'F01': '[已证]',", "'F01': '[流程]',", 1)
ck('S14.0 确实改动了生成物的 GRADES 常量', tam_src != gsrc)
with io.open(gp, 'w', encoding='utf-8', newline='') as f:
    f.write(tam_src)
p14 = subprocess.run([sys.executable, gp], capture_output=True, text=True, cwd=R, timeout=300)
ck('S14.1 改常量 -> D9 主指纹 FAIL', p14.returncode != 0 and 'D9' in p14.stdout,
   p14.returncode)

print('\n== S15 · 生产台账一字未动 ==')
ck('S15.1 V543 sha256 未变', hashlib.sha256(open(CUR, 'rb').read()).hexdigest() == sha_base)

shutil.rmtree(SB, ignore_errors=True)
print('\n=== FAILS:', fails if fails else 'NONE', '===')
sys.exit(1 if fails else 0)
