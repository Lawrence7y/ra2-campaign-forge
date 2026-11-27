# -*- coding: utf-8 -*-
"""R183 E：三门反向控制（不触碰生产）—— 证明本轮重钉不是恒真。
控1 D0：给 facts_floors 传一份多 1 B 的台账副本 ⇒ sha 漂移必 FAIL。
控2 D6/D8：传一份 F35 第 5 列被缩回的副本 ⇒ 触发 D0，但用 --ignore-pin 隔离后可单独看 D6/D8/D9。
控3 D10：在沙箱指针副本上把 sha 末位改坏 ⇒ 用独立小脚本复算 D10 的两条比较。
控4 C19/C20：把指针副本的「版本目录」改成 V563 ⇒ 复算 C19/C20 的三方一致性必 FAIL。
全部在 /tmp 沙箱内完成，生产文件 sha 前后一致。
"""
import hashlib, io, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
LED = os.path.join(TIER, 'R17_R131_FACTINDEX_V564/FACT_INDEX.tsv')
FF = os.path.join(ROOT, '_r160/facts_floors.py')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
SB = tempfile.mkdtemp(prefix='r183e_')

fails, n = [], 0
def ck(name, cond, detail=''):
    global n
    n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond: fails.append(name)

def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()

before = (sha(FF), sha(LED), sha(PTR))
print('沙箱 %s' % SB)
print('生产 sha 前置：facts %s / led %s / ptr %s' % (before[0][:12], before[1][:12], before[2][:12]))

def run(gate, args):
    p = subprocess.run([sys.executable, gate] + args, capture_output=True, text=True, timeout=600)
    return p.returncode, p.stdout + p.stderr

print('== 控1 · D0：台账内改 1 个字（等结构、等长，只让 sha 漂移）==')
# S-183e3（判据缺陷）：初版用「文件末尾追加 1 B」，那会破坏最后一行结构 ⇒ 脚本在 D4 段
# 抛 IndexError，D0 的 FAIL 消息根本没打印到 stdout，而 exit 1 是崩出来的 ⇒ 断言假 FAIL。
# 改为：在 F35 第 5 列末尾把一个汉字换成另一个汉字，列数/行数/CR 全不变。
import csv as _csv
_a = list(_csv.reader(io.open(LED, encoding='utf-8'), delimiter='\t'))
_d = {r[0]: r for r in _a[1:]}
_lim = _d['F35'][4]
assert '口径' in _lim
_d['F35'][4] = _lim.replace('口径', '口徑', 1)
_b = io.StringIO(); _csv.writer(_b, delimiter='\t', lineterminator='\n').writerows([_a[0]] + [_d[r[0]] for r in _a[1:]])
led2 = os.path.join(SB, 'led_1char.tsv')
io.open(led2, 'w', encoding='utf-8', newline='').write(_b.getvalue())
ck('1a0 副本仍 55 行 × 5 列 / 字节数不变（只换了一个字）',
   len(_b.getvalue().encode()) == len(open(LED, 'rb').read()), len(_b.getvalue().encode()))
rc, out = run(FF, [led2])
ck('1a 副本 sha 漂移 ⇒ facts_floors exit 1', rc == 1, rc)
ck('1b 报 D0 sha 漂移', 'D0 sha256 drifted' in out, [l for l in out.split('\n') if 'D0' in l][:3])

print('== 控2 · D6：F35 第 5 列缩回旧长度（用 --ignore-pin 隔离指纹）==')
import csv
rows = list(csv.reader(io.open(LED, encoding='utf-8'), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}
old_lim = d['F35'][4]
# 找回首版长度：把 R183 补段整段删掉（只留 R152 段之后的旧尾），使字节数 < floor
cut = old_lim.split('**【R183 补·该作用域是逐版实测的】**')[0] + '（截断副本）'
d['F35'][4] = cut
rows2 = [rows[0]] + [d[r[0]] for r in rows[1:]]
b = io.StringIO(); csv.writer(b, delimiter='\t', lineterminator='\n').writerows(rows2)
led3 = os.path.join(SB, 'led_shrunk.tsv'); io.open(led3, 'w', encoding='utf-8', newline='').write(b.getvalue())
rc, out = run(FF, ['--ignore-pin', led3])
ck('2a 截断副本 + ignore-pin 仍 exit 1（D6/D8 抓到缩水）', rc == 1, rc)
ck('2b 报 D6 F35.lim 缩水', 'F35.lim' in out and 'D6 per-fact bytes SHRANK' in out,
   [l for l in out.split('\n') if 'D6' in l][:2])
ck('2c 报 D8 总字节缩水', 'D8 total bytes SHRANK' in out,
   [l for l in out.split('\n') if 'D8' in l][:2])

print('== 控3 · D10：指针副本 sha 末位改坏 ==')
p0 = io.open(PTR, encoding='utf-8', newline='').read()
good = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', p0).group(1)
bad = good[:-1] + ('0' if good[-1] != '0' else '1')
p1 = p0.replace(good, bad, 1)
ck('3a 两 sha 前 63 位相同，只有末位不同（证明 [:16] 比对会失明）',
   good[:63] == bad[:63] and good[:16] == bad[:16], (good[:16], bad[:16]))
ck('3b 末位不同', good != bad)
# 复算 D10 的三条比较（与 facts_floors 同式）
m = re.search(r'\| 字节数 \| (\d+) \|', p1)
pb = int(m.group(1))
cur = open(LED, 'rb').read(); cs = hashlib.sha256(cur).hexdigest()
ck('3c D10(A) 指针 sha != 现盘 sha ⇒ 会 FAIL', bad != cs, (bad[:16], cs[:16]))
ck('3d D10(B) 指针字节 == TOTAL_BYTES（未改动，故只有 A 与 C 会红）', pb == len(cur), (pb, len(cur)))

print('== 控4 · C19/C20：指针副本版本目录改回 V563 ==')
p2 = p0.replace('R17_R131_FACTINDEX_V564', 'R17_R131_FACTINDEX_V563')
ck('4a 副本里相对路径指向 V563（文件存在但 sha 不同）',
   'V563/FACT_INDEX.tsv' in p2 and os.path.exists(os.path.join(TIER, 'R17_R131_FACTINDEX_V563/FACT_INDEX.tsv')))
rel = re.search(r'\| 相对路径 \| (\S+) \|', p2).group(1)
abs_p = os.path.join(ROOT, rel)
ck('4b C19(a)：路径存在', os.path.exists(abs_p))
# S-183e1（方向错）：初版把期望写成 ==，实际控制就是要它 !=（副本指 V563 而指针 sha 是 V564 的）
ck('4c C19(b)：该文件 sha != 指针 sha（不等即 C19 会红）', sha(abs_p) != good, (sha(abs_p)[:16], good[:16]))
ck('4d C20：该绝对路径 != facts_floors.EXPECT_CUR 解析结果（否 ⇒ FAIL）',
   abs_p != LED, (abs_p.split('/')[-2], LED.split('/')[-2]))

print('== 控5 · 生产未被触碰 ==')
after = (sha(FF), sha(LED), sha(PTR))
ck('5a 三门脚本 + 台账 + 指针 sha 前后一致', before == after, before)
# S-183e2：本机 TMPDIR=/mnt/ssd/tmp，初版一律按 /tmp 断言 ⇒ 假 FAIL。判据改为「不在库根之内」。
ck('5b 沙箱不在库根之内', not os.path.abspath(SB).startswith(ROOT + '/'), SB)
shutil.rmtree(SB, ignore_errors=True)
ck('5c 沙箱已清理', not os.path.exists(SB))

print('\n== %d 断言, %d FAIL ==' % (n, len(fails)))
sys.exit(1 if fails else 0)
