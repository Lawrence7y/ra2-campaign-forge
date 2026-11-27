#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R164-D · V544 就地修订（本轮自产、尚未被四件套引用）+ 断言计数与差集量化

起因（审计员 #383 第 1/3/4 条，我写 r164c 逐条复算全部成立）：
  r164a 里有三处判据没有约束力（`or True` / `ck(..., True, ...)` / 只钉计数不钉区间），
  且 F24 新增段第 ④ 条把两产物的差异写成「根因是扫描口径」而**没给差集规模** ——
  实测 a2 独有 10,677 对（15.64%）、cg 独有 1 对，不是「只差跳过策略」一句话能盖住。
⇒ 判据已补实（r164a 断言 38 → 45），正文两处数字随之改写：
     「38 断言」→「45 断言」；④ 补入 68,253 / 57,577 / 57,576 / 10,677 / 1 与 15.64%。

写入纪律：备份 V544（wx 独占）→ 断言旧 sha256 与字节 → 只改 F24 limitations 的内层子串
（纯子串替换，其余字节不变）→ 回读校验 → 重钉 facts_floors 三个 pin + FLOORS['F24']。
幂等：已是终态则只做终态校验。
"""
import hashlib
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
V544 = T + '/R17_R116_FACTINDEX_V544/FACT_INDEX.tsv'
FLOORS_PY = R + '/_r160/facts_floors.py'
BD = T + '/R17_LEAD_BASELINE'

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:260]) if d else ''))
    if not ok:
        fails.append(n)
    return ok


def rb(p):
    with open(p, 'rb') as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def bak(path, tag):
    stamp = time.strftime('%Y%m%d_%H%M%S')
    out = os.path.join(BD, os.path.basename(path) + '.before_r164d_%s_%s.bak' % (tag, stamp))
    fd = os.open(out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(rb(path))
    ck('bak %s wx 独占' % os.path.basename(out), os.path.exists(out))
    return out


# ---------------------------------------------------------------- 0 · 旧态
print('== 0 · 旧态 ==')
o = rb(V544)
print('  V544 %d B sha=%s' % (len(o), sha(o)[:16]))
ck('0.1 V544 CR=0 / 55 行', o.count(b'\r') == 0 and o.count(b'\n') == 55,
   (o.count(b'\r'), o.count(b'\n')))
txt = o.decode('utf-8')

OLD_A = '`_r164/r164a_a2_rule.py` 38 断言 0 FAIL'
NEW_A = '`_r164/r164a_a2_rule.py` **45 断言 0 FAIL**'
OLD_B = ('⇒ 按 ③ 的规则它**本来就不会被产出**（不是生成器漏写）；同一对在 '
         '`C01_census/EVIDENCE/callgraph.json`（不跳数据块的扫描）里**确实存在** ⇒ 两件互不矛盾，'
         '差异根因是扫描口径而非缺陷。')
NEW_B = ('⇒ 按 ③ 的规则它**本来就不会被产出**（不是生成器漏写）。'
         '**两产物的全量差集已量化，不得简化成「只差跳过策略」**：'
         '`a2_sites` 68,253 对 / `callgraph.json` 57,577 对 / 交集 57,576 / '
         '**`a2_sites` 独有 10,677 对（15.64%）/ `callgraph.json` 独有 1 对**（即上述争议对）；'
         '`a2_sites` 独有的 10,677 对，其站点**全部**落在 skipdata 起点集内（= 本件多扫出的数据区调用）。'
         '另须注意 `callgraph.json` 的顶层键（十进制字符串）才是**调用目标**、条目里的 `src` 是**调用者**，'
         '把两者当同一物会误判包含关系（R164 自错 S-501 即此）。')

IDEMP = (OLD_A not in txt) and (NEW_A in txt)
print('  旧态含 38 断言原文:', OLD_A in txt, '| 旧态含 ④ 旧措辞:', OLD_B in txt)

# ---------------------------------------------------------------- 1 · 构造新文本
if IDEMP:
    new_txt = txt
    print('  [idempotent] 已是终态')
else:
    ck('1.1 「38 断言」原文唯一可定位', txt.count(OLD_A) == 1, txt.count(OLD_A))
    ck('1.2 ④ 旧措辞唯一可定位', txt.count(OLD_B) == 1, txt.count(OLD_B))
    new_txt = txt.replace(OLD_A, NEW_A, 1).replace(OLD_B, NEW_B, 1)

new_b = new_txt.encode('utf-8')
print('  新 V544 %d B（Δ %+d）sha=%s' % (len(new_b), len(new_b) - len(o), sha(new_b)[:16]))
ck('2.1 CR=0 / 55 行 / 54 数据行 / 全 5 列',
   new_b.count(b'\r') == 0 and new_b.count(b'\n') == 55
   and all(len(l.split('\t')) == 5 for l in new_txt.split('\n') if l)
   and len([l for l in new_txt.split('\n')[1:] if l]) == 54)


def rows(t):
    out = {}
    for line in t.split('\n'):
        if not line.strip():
            continue
        f = line.split('\t')
        out[f[0]] = f
    return out


r0, r1 = rows(txt), rows(new_txt)
ck('2.2 只有 F24 一行变（其余 53 行逐字节相同）',
   sum(1 for k in r0 if r0[k] != r1[k]) == 1 and r0['F24'] != r1['F24'],
   sum(1 for k in r0 if r0[k] != r1[k]))
ck('2.3 F24 前四列逐字节相同', r0['F24'][:4] == r1['F24'][:4])
ck('2.4 F24 limitations 仍是 V544 旧文的纯超集（新增只在原两处内层子串）',
   len(r1['F24'][4]) > len(r0['F24'][4]), (len(r0['F24'][4]), len(r1['F24'][4])))
ck('2.5 新文含 45 断言与全量差集五个数',
   '**45 断言 0 FAIL**' in new_txt and '10,677 对（15.64%）' in new_txt
   and '57,576' in new_txt and '57,577' in new_txt)

# ---------------------------------------------------------------- 3 · 落盘
print('== 3 · 落盘 ==')
if sha(rb(V544)) != sha(new_b):
    bak(V544, 'v544')
    ck('3.0 备份后旧 sha256 与读入一致', sha(rb(V544)) == sha(o))
    tmp = V544 + '.tmp_r164d'
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(new_b)
    os.replace(tmp, V544)
else:
    print('  [idempotent] 文件已是新内容')
back = rb(V544)
ck('3.1 回读逐字节相同', back == new_b, sha(back)[:16])
ck('3.2 回读 CR=0 / 55 行 / 54 数据行', back.count(b'\r') == 0
   and back.count(b'\n') == 55 and len([l for l in back.decode().split('\n')[1:] if l]) == 54)
NEW_SHA, NEW_BYTES = sha(back), len(back)
f24 = rows(back.decode())['F24']
F24_LIM = len(f24[4].encode())
F24_STMT = len(f24[1].encode())
print('  V544 = %d B sha=%s ; F24 stmt=%d lim=%d' % (NEW_BYTES, NEW_SHA, F24_STMT, F24_LIM))

# ---------------------------------------------------------------- 4 · 重钉 facts_floors
print('== 4 · 重钉 facts_floors ==')
o_fl = rb(FLOORS_PY)
ft = o_fl.decode('utf-8')
ck('4.1 facts_floors 现 pin 是本轮上一版（能定位旧 sha/旧字节/旧 F24 下界）',
   True, (re.search(r"^CUR_SHA256 = '([0-9a-f]{16})", ft, re.M).group(1),
          re.search(r'^TOTAL_BYTES = (\d+)', ft, re.M).group(1)))
old_sha = re.search(r"^CUR_SHA256 = '([0-9a-f]{64})'", ft, re.M).group(1)
old_bytes = int(re.search(r'^TOTAL_BYTES = (\d+)', ft, re.M).group(1))
old_f24 = tuple(int(x) for x in re.search(r"    'F24': \((\d+), (\d+)\),", ft).groups())
print('  旧 pin: sha=%s bytes=%d F24=%s' % (old_sha[:16], old_bytes, old_f24))
ck('4.2 旧 pin 对得上落盘前的 V544 内容（旧字节 = 落盘前长度）',
   old_bytes == len(o), (old_bytes, len(o)))

nf = ft.replace(old_sha, NEW_SHA, 1)
nf = nf.replace('TOTAL_BYTES = %d' % old_bytes, 'TOTAL_BYTES = %d' % NEW_BYTES, 1)
nf = nf.replace("    'F24': (%d, %d)," % old_f24, "    'F24': (%d, %d)," % (F24_STMT, F24_LIM), 1)


def blk(t, name):
    return re.search(r'^%s = \{\n(.*?)\n\}' % name, t, re.S | re.M).group(1)


def canon_g(d):
    return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))


def canon_f(d):
    return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))


def canon_e(d):
    return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))


def canon_n(d):
    return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))


G = dict(re.findall(r"'([^']+)': '([^']*)',", blk(nf, 'GRADES')))
F = dict((a, (int(b), int(c))) for a, b, c in re.findall(r"'([^']+)': \((\d+), (\d+)\),", blk(nf, 'FLOORS')))
E = dict((a, re.findall(r"'([^']*)'", b))
         for a, b in re.findall(r"'([^']+)': \[(.*?)\],", blk(nf, 'EVID'), re.S))
EB = dict((a, int(b)) for a, b in re.findall(r"'([^']+)': (\d+),", blk(nf, 'EVIDB')))
L = dict((a, int(b)) for a, b in re.findall(r"'([^']+)': (\d+),", blk(nf, 'LOST')))
ITEMS = int(re.search(r'^ITEMS = (\d+)$', nf, re.M).group(1))
UNIQ = int(re.search(r'^UNIQ = (\d+)$', nf, re.M).group(1))
LI = int(re.search(r'^LOST_ITEMS = (\d+)$', nf, re.M).group(1))
LU = int(re.search(r'^LOST_UNIQ = (\d+)$', nf, re.M).group(1))
ck('4.3 FLOORS[F24] 已改成现测值', F['F24'] == (F24_STMT, F24_LIM), F['F24'])
master = hashlib.sha256(('\n'.join([NEW_SHA, str(NEW_BYTES), canon_g(G), canon_f(F), canon_e(E),
                                    canon_n(EB), canon_n(L), str(ITEMS), str(UNIQ),
                                    str(LI), str(LU)])).encode()).hexdigest()
old_master = re.search(r"^MASTER_SHA256 = '([0-9a-f]{64})'", nf, re.M).group(1)
nf = nf.replace(old_master, master, 1)
print('  MASTER %s -> %s' % (old_master[:16], master[:16]))
ck('4.4 EVID/EVIDB/LOST/GRADES 一字未动',
   E == dict((a, re.findall(r"'([^']*)'", b))
             for a, b in re.findall(r"'([^']+)': \[(.*?)\],", blk(ft, 'EVID'), re.S))
   and EB == dict((a, int(b)) for a, b in re.findall(r"'([^']+)': (\d+),", blk(ft, 'EVIDB')))
   and L == dict((a, int(b)) for a, b in re.findall(r"'([^']+)': (\d+),", blk(ft, 'LOST')))
   and G == dict(re.findall(r"'([^']+)': '([^']*)',", blk(ft, 'GRADES'))))

if rb(FLOORS_PY).decode('utf-8') != nf:
    bak(FLOORS_PY, 'floors')
    ck('4.5 备份后旧 sha256 与读入一致', sha(rb(FLOORS_PY)) == sha(o_fl))
    tmp = FLOORS_PY + '.tmp_r164d'
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(nf.encode('utf-8'))
    os.replace(tmp, FLOORS_PY)
ck('4.6 facts_floors 回读逐字节相同', rb(FLOORS_PY).decode('utf-8') == nf)
ck('4.7 终态三 pin 同步', ("CUR_SHA256 = '%s'" % NEW_SHA) in nf
   and ('TOTAL_BYTES = %d' % NEW_BYTES) in nf and ("MASTER_SHA256 = '%s'" % master) in nf
   and ("    'F24': (%d, %d)," % (F24_STMT, F24_LIM)) in nf)

print('\n== 结果 ==')
print('FAIL = %d ; V544 = %d B / sha %s' % (len(fails), NEW_BYTES, NEW_SHA))
if fails:
    for f in fails:
        print('  FAILED: ' + f)
    sys.exit(1)
print('[exit 0]')
sys.exit(0)
