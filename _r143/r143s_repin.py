#!/usr/bin/env python3
"""R143 B：把新节 §2.148 钉进 C16 逐节下界（表外新节默认 0 = 白得免检票），并重钉 sha。

纪律（R142 立）：① 新节必须显式入表，否则 C16_NEW_MIN=0 等于永久免检；
② 重钉前先用「去掉新项重算」复现旧钉，验明方法无误（不是我在改判据）。
"""
import hashlib, io, json, os, re, time

BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
OUT = '/home/t628/projects/ra2-campaign-forge/_r143/r143s_repin.json'
cc, cc_n = [], 0
def ck(n, c, d=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

src = open(GATE, 'rb').read()
txt = src.decode('utf-8')
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', txt, re.S)
ck('B0 找到 C16_FLOORS 定义', m is not None)
body = m.group(1)
pairs = [(int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', body)]
d = dict(pairs)
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]+)'", txt).group(1)
ck('B1 表项 141 条', len(d) == 141, len(d))
ck('B2 旧钉 = d164deff', old_sha.startswith('d164deff'), old_sha[:16])

def norm(dd):
    return '\n'.join('%d:%d' % (k, dd[k]) for k in sorted(dd))
ck('B3 方法可复现旧钉（用现表重算 == 旧常量）', hashlib.sha256(norm(d).encode()).hexdigest() == old_sha)

# 实测 §2.148 字节
blob = open(os.path.join(BASE, 'R14_COMMON.md'), 'rb').read()
i = blob.rindex(b'## 2.148')
sec = blob[i:]
ck('B4 §2.148 存在且 >= 4000 B', len(sec) >= 4000, len(sec))
# C16 的度量口径：与其它节同法（去尾换行）
size = len(sec) - 1 if sec.endswith(b'\n') else len(sec)
floor = size - 21
ck('B5 下界留 21 B 余量（与 146 节同法）', floor == size - 21, (size, floor))
d2 = dict(d); d2[148] = floor
new_sha = hashlib.sha256(norm(d2).encode()).hexdigest()
ck('B6 新钉 != 旧钉（真的改了表）', new_sha != old_sha)

# 备份 + 写
dst = os.path.join(BL, 'check_disc.py.before_r143_repin_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(src)
ck('B7 备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))

new_txt = txt.replace("146: 8400, 147: 2200,", "146: 8400, 147: 2200, 148: %d," % floor)
ck('B8 表内已插入 148 项', ('148: %d,' % floor) in new_txt)
new_txt = new_txt.replace("C16_FLOORS_SHA256 = '%s'" % old_sha, "C16_FLOORS_SHA256 = '%s'" % new_sha)
ck('B9 常量已换成新钉', new_sha in new_txt)
open(GATE, 'wb').write(new_txt.encode('utf-8'))
after = open(GATE, 'rb').read()
ck('B10 写后回读含 148 项', b'148: %d,' % floor in after)
ck('B11 写后回读含新钉', new_sha.encode() in after)
ck('B12 旧钉已不在', old_sha.encode() not in after)

# 独立复算：从写后的文件重新解析表并重算 sha
t2 = after.decode('utf-8')
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', t2, re.S)
d3 = dict((int(a), int(b)) for a, b in re.findall(r'(\d+):\s*(\d+)', m2.group(1)))
ck('B13 写后表 142 条', len(d3) == 142, len(d3))
ck('B14 写后表自算 sha == 常量', hashlib.sha256(norm(d3).encode()).hexdigest() == new_sha)
ck('B15 148 项 == 实测 - 21', d3[148] == size - 21, (d3[148], size))

json.dump(dict(checks=cc_n, fails=cc, old=old_sha, new=new_sha, floor=floor, sec_bytes=size,
               rows=len(d3)), io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 重钉：正控 %d / FAIL %d ===' % (cc_n, len(cc)))
if cc: print('FAILS:', cc)
