#!/usr/bin/env python3
"""R147 L：修正看板第 147 轮标题格式（对齐既有 '## 🟢 R17 第 N 轮（…）' 约定）。

原因（自错 S-337）：r147k 写看板时我用了 '## 第 147 轮（R147）· …'，而既有
145/146 两轮都是 '## 🟢 R17 第 146 轮（2026-11-27 02:0x–03:0x）· …'。
同轮同一份文档里混用两种标题格式会让"按标题切段"的工具漏掉本轮段。
同时 r147k 里那条'第146轮段仍恰1次'断言写错了匹配串（真实标题带 🟢 R17 前缀），
这里一并改正为正确串并重算。
"""
import io, os, json, time, hashlib

HERE = '/home/t628/projects/ra2-campaign-forge'
BRD = HERE + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
BL = HERE + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE'

OLD = '## 第 147 轮（R147）· 0x8871E0 单例论据重建 + R144 §七更正'
NEW = '## 🟢 R17 第 147 轮（2026-11-27 03:0x–04:0x）· 0x8871E0 单例论据重建（四条机器码支点）；R144 §七「0x7E6060 未找到装表站点」被负位移站点 0x4A8660 证伪并就地更正'

FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        FAILS.append(n)

def read(p):
    return io.open(p, encoding='utf-8', newline='').read()

s0 = read(BRD)
ck('前置 旧标题出现恰 1 次', s0.count(OLD) == 1, s0.count(OLD))
ck('前置 新标题尚未出现（幂等）', NEW not in s0, NEW in s0)
ck('前置 CR == 0', s0.count('\r') == 0, s0.count('\r'))

if FAILS:
    print(json.dumps({'aborted': FAILS}, ensure_ascii=False))
    raise SystemExit(2)

src = open(BRD, 'rb').read()
dst = os.path.join(BL, 'STATUS_BOARD.md.before_r147_board_title_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
with io.open(dst, 'xb') as f:
    f.write(src)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))

s1 = s0.replace(OLD, NEW, 1)
with io.open(BRD, 'w', encoding='utf-8', newline='') as f:
    f.write(s1)
s2 = read(BRD)

ck('回读 逐字节相同', s2 == s1)
ck('回读 CR 仍 0', s2.count('\r') == 0, s2.count('\r'))
ck('回读 新标题出现恰 1 次', s2.count(NEW) == 1, s2.count(NEW))
ck('回读 旧标题消失', s2.count(OLD) == 0, s2.count(OLD))
ck('回读 第146轮段恰 1 次（正确前缀串）', s2.count('## 🟢 R17 第 146 轮') == 1, s2.count('## 🟢 R17 第 146 轮'))
ck('回读 第145轮段恰 1 次', s2.count('## 🟢 R17 第 145 轮') == 1, s2.count('## 🟢 R17 第 145 轮'))
ck('回读 第147轮段恰 1 次（正确前缀串）', s2.count('## 🟢 R17 第 147 轮') == 1, s2.count('## 🟢 R17 第 147 轮'))
n = s2.count('\n')
ck('回读 行数 <= 300', n <= 300, n)

out = {'fails': FAILS, 'lines': n, 'cr': s2.count('\r'),
       'sha': hashlib.sha256(s2.encode()).hexdigest()}
json.dump(out, open(HERE + '/_r147/r147l_board_title.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
