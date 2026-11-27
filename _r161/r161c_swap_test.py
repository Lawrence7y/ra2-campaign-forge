#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161c_swap_test.py —— 把「等长替换盲区」真做一遍，并量它在哪个模式下不可见。

R160 待办 #2 原话：v2 允许等长替换，「要真正守住需对 col2/col5 内容做规范化指纹（逐 fact
内容 sha，而不是只钉字节数）」。本轮不采信也不反驳，直接做三类破坏性实验：
  A 第 2 列等长互换：F28 <-> F34（两条 col2 各 348 B、grade 同为 [流程]）
  B 第 5 列等长互换：F18 <-> F36（两条 col5 各 320 B）
  C 第 2 列等长单点改写（把一个汉字换成另一个同 3 字节汉字）
每工况两种调用：
  生产口径  facts_floors.py <mutated>             （D0 生效）
  自测口径  facts_floors.py <mutated> --ignore-pin（D0 跳过）
沙箱保真：脚本本体**逐字节复制不改一行**，只把被测台账拷到 /tmp 下再传 argv；
因为脚本 ROOT 由其自身位置反推，仍指真实仓库 ⇒ D7 的 178 条证据路径照常解析。
先用未改动副本证明两种口径都 exit 0，再做破坏。
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
P = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
G = R + '/_r160/facts_floors.py'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

SBROOT = tempfile.mkdtemp(prefix='/tmp/r161sb_')

def run(path, extra=()):
    pr = subprocess.run([sys.executable, G, path] + list(extra),
                        capture_output=True, text=True, cwd=R, timeout=300)
    return pr.returncode, (pr.stdout + pr.stderr)

def parse(path):
    ne = [l for l in io.open(path, encoding='utf-8', newline='').read().split('\n') if l]
    return ne[0].split('\t'), [l.split('\t') for l in ne[1:]]

def dump(path, hdr, data):
    with open(path, 'wb') as f:
        f.write(('\n'.join(['\t'.join(hdr)] + ['\t'.join(r) for r in data]) + '\n').encode('utf-8'))

print('== 0 · 沙箱保真（未改动副本两种口径都必须 exit 0）==')
base = SBROOT + '/base.tsv'
shutil.copy2(P, base)
rc_p, o_p = run(base)
rc_i, o_i = run(base, ('--ignore-pin',))
ck('0.1 未改动副本 生产口径 exit 0', rc_p == 0, rc_p)
ck('0.2 未改动副本 自测口径 exit 0', rc_i == 0, rc_i)
ck('0.3 D7 真的解析了证据路径（lost_items=43，未因沙箱位置失真）',
   'lost_items=43' in o_i, [l.strip() for l in o_i.split('\n') if 'D7 evidence' in l][:1])
ck('0.4 副本 sha 与原件一致',
   hashlib.sha256(open(base, 'rb').read()).hexdigest() == hashlib.sha256(open(P, 'rb').read()).hexdigest())
ck('0.5 生产口径基线不打印 --ignore-pin 告警', 'WARNING' not in o_p, 'WARNING' in o_p)

def trial(tag, mutate, desc):
    path = SBROOT + '/' + tag + '.tsv'
    shutil.copy2(P, path)
    hdr, data = parse(path)
    mutate(data)
    dump(path, hdr, data)
    size_same = os.path.getsize(path) == os.path.getsize(P)
    rc1, o1 = run(path)
    rc2, o2 = run(path, ('--ignore-pin',))
    f1 = [l.strip() for l in o1.split('\n') if l.strip().startswith('FAIL')]
    f2 = [l.strip() for l in o2.split('\n') if l.strip().startswith('FAIL')]
    print('\n  [%s] %s' % (tag, desc))
    print('     总字节不变 = %s' % size_same)
    print('     生产口径 exit=%d FAIL=%d  %s' % (rc1, len(f1), [x[:100] for x in f1[:3]]))
    print('     自测口径 exit=%d FAIL=%d  %s' % (rc2, len(f2), [x[:100] for x in f2[:3]]))
    ck('%s 破坏后总字节不变（等长性成立）' % tag, size_same)
    ck('%s 生产口径必须被抓住' % tag, rc1 != 0, rc1)
    return rc1, rc2, f1, f2

def swap(i, a, b):
    def f(data):
        ids = [r[0] for r in data]
        ia, ib = ids.index(a), ids.index(b)
        data[ia][i], data[ib][i] = data[ib][i], data[ia][i]
    return f

def eq_edit(data):
    for r in data:
        if r[0] == 'F45':
            s = r[1]
            for k, ch in enumerate(s):
                if 0x4E00 <= ord(ch) <= 0x9FFF:
                    new = '的' if ch != '的' else '是'
                    r[1] = s[:k] + new + s[k + 1:]
                    print('     （F45 第2列第 %d 个字符 %s -> %s，各 3 B）' % (k, ch, new))
                    return
            raise AssertionError('F45 statement 无 CJK 字符')

print('\n== 1 · 三个等长破坏工况 ==')
r = {}
r['A'] = trial('swap_col2', swap(1, 'F28', 'F34'), '第 2 列互换 F28<->F34（各 348 B、grade 同 [流程]）')
r['B'] = trial('swap_col5', swap(4, 'F18', 'F36'), '第 5 列互换 F18<->F36（各 320 B）')
r['C'] = trial('eq_edit', eq_edit, '第 2 列等长单点改写 F45（汉字换汉字，各 3 B）')

print('\n== 2 · 逐工况结论（真值表）==')
print('  工况 | 生产口径 | 自测口径(--ignore-pin)')
for k in ('A', 'B', 'C'):
    rc1, rc2, f1, f2 = r[k]
    print('   %s   | exit=%d %-8s| exit=%d %s'
          % (k, rc1, '被抓' if rc1 else '漏', rc2, '漏（盲区成立）' if rc2 == 0 else '仍被抓'))
ck('2.1 三工况生产口径全部被抓住', all(v[0] != 0 for v in r.values()), [v[0] for v in r.values()])
ck('2.2 三工况自测口径全部漏（盲区作用域 = --ignore-pin）',
   all(v[1] == 0 for v in r.values()), [v[1] for v in r.values()])
ck('2.3 漏的原因里不含 D6/D7/D8（它们对等长改写不敏感）',
   all(not any(('D6' in x) or ('D7' in x) or ('D8' in x) for x in v[3]) for v in r.values()),
   {k: [x[:40] for x in v[3]] for k, v in r.items()})

shutil.rmtree(SBROOT, ignore_errors=True)
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
