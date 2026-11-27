# -*- coding: utf-8 -*-
"""R171 H：gate_runner.py 的 V550 -> V551 指针更新（5 处文本，均为 V550 字样/目录号）。"""
import hashlib, io, json, os, re, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
GR = os.path.join(ROOT, '_r161', 'gate_runner.py')
BAK = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_LEAD_BASELINE',
                   'gate_runner.py.before_r171_V551_%s.bak' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
pins = json.load(io.open(os.path.join(HERE, 'r171f_pins.json'), encoding='utf-8'))

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

src = io.open(GR, 'rb').read()
text = src.decode('utf-8')
print('  改前 gate_runner.py = %d B / sha %s' % (len(src), hashlib.sha256(src).hexdigest()[:16]))

ck('P0 改前含 V550 目录号', 'R17_R122_FACTINDEX_V550' in text)
ck('P0b 改前不含 V551', 'R17_R123_FACTINDEX_V551' not in text)
n550 = text.count('V550')
n122 = text.count('R17_R122_FACTINDEX_V550')
print('  改前 V550 字样 %d 处、目录号 %d 处' % (n550, n122))

new = text.replace('R17_R122_FACTINDEX_V550', 'R17_R123_FACTINDEX_V551')
# 注释里单独的 V550 字样（不带目录号）也要一并改，避免报错信息指向旧件
new = new.replace('现盘 V550', '现盘 V551').replace('sha256(V550/', 'sha256(V551/') \
           .replace('len(V550/', 'len(V551/')
ck('P1 改写后 V550 字样归 0', new.count('V550') == 0, new.count('V550'))
print('  改后 V551 字样 %d 处' % new.count('V551'))

# ---- 备份 + 写 ----
with io.open(BAK, 'xb') as f:
    f.write(src)
ck('P2 备份独占创建', os.path.isfile(BAK) and io.open(BAK, 'rb').read() == src)
io.open(GR, 'wb').write(new.encode('utf-8'))
back = io.open(GR, 'rb').read()
ck('P2b 回读逐字节 == 待写', back == new.encode('utf-8'))

# ---- 反控：只差 V550->V551 相关行 ----
o_l, n_l = text.split('\n'), new.split('\n')
dl = [i for i in range(min(len(o_l), len(n_l))) if o_l[i] != n_l[i]]
print('  变化 %d 行: %s' % (len(dl), [(i, o_l[i].strip()[:52]) for i in dl]))
ck('N1 行数不变', len(o_l) == len(n_l))
ck('N1b 变化行恰 5 行（与 R170 记录的 gate_runner 5 处一致）', len(dl) == 5, len(dl))
ck('N1c 每变化行都只差 V55x 字样',
   all(o_l[i].replace('V550', 'V551') == n_l[i] or
       o_l[i].replace('R17_R122_FACTINDEX_V550', 'R17_R123_FACTINDEX_V551') == n_l[i]
       for i in dl), [(i, o_l[i][:60], n_l[i][:60]) for i in dl])

# ---- 实跑 ----
p = subprocess.run([sys.executable, GR], capture_output=True, text=True, timeout=900)
out = p.stdout + p.stderr
ck('N2 gate_runner exit 0', p.returncode == 0, out[-1200:])
for tag in ('G1', 'G2', 'G3'):
    ck('N2b %s 打印 ok' % tag, re.search(r'%s\b[^\n]*ok' % tag, out) is not None,
       [l for l in out.split('\n') if tag in l][:2])
print('   ' + '\n   '.join([l for l in out.strip().split('\n') if l.strip().startswith(('G', '  G'))][-14:]))

io.open(os.path.join(HERE, 'r171h_gr.json'), 'w', encoding='utf-8').write(json.dumps(
    {'gr_sha_before': hashlib.sha256(src).hexdigest(),
     'gr_sha_after': hashlib.sha256(back).hexdigest(),
     'bak': os.path.relpath(BAK, ROOT), 'changed_lines': dl}, indent=1))
print('\n=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)
