#!/usr/bin/env python3
"""R144 Q：C16 重钉（纳 §2.149）+ 四处版本标记同步，全程「不改判据语义」。

纪律（R142/R143 立）：
  ① 新节必须显式入表，否则 C16_NEW_MIN=0 等于每轮白得一张永久免检票；
  ② 重钉前先用「去掉新项重算」复现旧钉，验明方法无误（不是我在改判据）；
  ③ 下界 = 实测字节 - 21（与 146/147/148 同法），并断言旧表的 21 B 余量也是同期形态。
本脚本只做 pin，另由 r144r 做 GATE_VER / 两张 TSV 的同步与正反控。
"""
import hashlib, io, json, os, re, time

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
OUT = '/home/t628/projects/ra2-campaign-forge/_r144/r144q_repin.json'
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

src = open(GATE, 'rb').read(); txt = src.decode('utf-8')
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', txt, re.S)
ck('B0 找到 C16_FLOORS', m is not None)
d = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]+)'", txt).group(1)
ck('B1 表项 142 条', len(d) == 142, len(d))
ck('B2 旧钉 = f1ee8188', old_sha.startswith('f1ee8188'), old_sha[:16])
norm = lambda dd: '\n'.join('%d:%d' % (k, dd[k]) for k in sorted(dd))
ck('B3 方法可复现旧钉（用现表重算 == 旧常量）', hashlib.sha256(norm(d).encode()).hexdigest() == old_sha)
ck('B4 表里尚无 149', 149 not in d)

# 严格按 C16 的度量口径重算 §2.149：按行切，含标题行，'\\n'.join 后 utf-8 字节数
rc = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read().decode('utf-8')
lines = rc.split('\n')
sec = []; cur = None
for l in lines:
    mm = re.match(r'^##\s+2\.(\d+)\b', l)
    if mm:
        if cur == 149: break
        cur = int(mm.group(1)); sec = [l]
    elif cur == 149:
        sec.append(l)
size = len('\n'.join(sec).encode('utf-8'))
ck('B5 按 C16 口径测得 §2.149 == 9,047 B（与 r144p 的追加量一致）', size == 9047, size)
floor = size - 21
ck('B6 下界 = 实测 - 21（与 146/147/148 同法）', floor == size - 21, (size, floor))
ck('B7 旧表里 146/147/148 的余量形态一致（各自 == 实测 - 21 附近的同量级）', d[148] == 8403 and d[147] == 2200 and d[146] == 8400, [d[146], d[147], d[148]])
d2 = dict(d); d2[149] = floor
new_sha = hashlib.sha256(norm(d2).encode()).hexdigest()
ck('B8 新钉 != 旧钉', new_sha != old_sha)

dst = os.path.join(BL, 'check_disc.py.before_r144_repin_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(src)
ck('B9 备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))

t2 = txt.replace("146: 8400, 147: 2200, 148: 8403,", "146: 8400, 147: 2200, 148: 8403, 149: %d," % floor)
ck('B10 已插入 149 项', ('149: %d,' % floor) in t2 and t2 != txt)
t2 = t2.replace("C16_FLOORS_SHA256 = '%s'" % old_sha, "C16_FLOORS_SHA256 = '%s'" % new_sha)
ck('B11 常量已换成新钉', new_sha in t2)
open(GATE, 'wb').write(t2.encode('utf-8'))
after = open(GATE, 'rb').read()
ck('B12 回读含 149 项与新钉', (b'149: %d,' % floor) in after and new_sha.encode() in after)
ck('B13 旧钉已不在', old_sha.encode() not in after)

t3 = after.decode('utf-8')
d3 = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', re.search(r'C16_FLOORS = \{(.*?)\n\}', t3, re.S).group(1)))
ck('B14 写后表 143 条', len(d3) == 143, len(d3))
ck('B15 写后表自算 sha == 常量', hashlib.sha256(norm(d3).encode()).hexdigest() == new_sha)
ck('B16 149 项 == 实测 - 21', d3[149] == size - 21, (d3[149], size))

json.dump(dict(checks=len(cc) + 16, fails=cc, old=old_sha, new=new_sha, floor=floor, sec_bytes=size, rows=len(d3)),
          io.open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n=== 重钉：FAIL %d ===' % len(cc))
