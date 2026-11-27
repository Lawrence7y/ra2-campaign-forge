#!/usr/bin/env python3
"""R145 L：两张 TSV 的版本串同步 + C7d/FREEZE 重钉（照抄门禁口径，S-312 教训）。

门禁口径（必须逐字照抄，不许自己发挥）：
  C7d: rows = [l.split('\\t') for l in raw[1:]]  （**丢表头**）
       blob = '\\n'.join('%s\\t%s\\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r)==7)
  FREEZE: sha256(DISC_UNVERIFIABLE.tsv 整文件字节)
本脚本先打印目标行再断言（S-299 教训：行号 vs 主键）。
"""
import hashlib, io, json, os, re, subprocess, time
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
GATE = os.path.join(BASE, 'check_disc.py')
RCH = os.path.join(BASE, 'DISC_RECHECK.tsv')
UNV = os.path.join(BASE, 'DISC_UNVERIFIABLE.tsv')
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
cc = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: cc.append(n)

def c7d_hash(raw_text):
    raw = raw_text.split('\n')
    rows = [l.split('\t') for l in raw[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), rows

raw0 = io.open(RCH, encoding='utf-8').read()
lines = raw0.split('\n')
ck('C1 表头 + 31 数据行 = 32 行', len([l for l in lines if l.strip()]) == 32, len([l for l in lines if l.strip()]))
ck('C2 第 21 行（1-based）主键是 20', lines[20].split('\t')[0] == '20', lines[20].split('\t')[0])
ck('C3 第 21 行 col6 现在是 R144', "'R144'" in lines[20], lines[20].split('\t')[5])
ck('C4 只有这一行含 GATE_VER 串', sum(1 for l in lines if "GATE_VER" in l) == 1, sum(1 for l in lines if "GATE_VER" in l))
h_old, rows0 = c7d_hash(raw0)
gate_src = open(GATE).read()
ck('C5 方法复现旧 C7d 钉（丢表头 31 行）', h_old.startswith("636db13b"), h_old[:16])
ck('C6 旧钉与门禁常量一致', "C7_TEXT_SHA256 = '636db13b" in gate_src)

# 改 TSV
newline = lines[20].replace("grep=(?m)^GATE_VER = 'R144'", "grep=(?m)^GATE_VER = 'R145'")
ck('C7 只在 col6 里替换了一个版本串', newline != lines[20] and newline.count("'R145'") == 1, newline.split('\t')[5])
lines2 = list(lines); lines2[20] = newline
raw1 = '\n'.join(lines2)
ck('C8 TSV 仍 32 行、列数不变', len([l for l in lines2 if l.strip()]) == 32 and all(len(a.split('\t')) == len(b.split('\t')) for a, b in zip(lines, lines2) if a.strip()))
dst = os.path.join(BL, 'DISC_RECHECK.tsv.before_r145_sync_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(raw0.encode('utf-8'))
ck('C9 备份 wx 独占', open(dst, encoding='utf-8').read() == raw0, os.path.basename(dst))
open(RCH, 'w', encoding='utf-8', newline='').write(raw1)

h_new, rows1 = c7d_hash(raw1)
row20 = [r for r in rows1 if len(r) == 7 and r[0] == '20'][0]
h_row20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
ck('C10 新 C7d != 旧 C7d', h_new != h_old, [h_old[:16], h_new[:16]])
# S-312 反控：把表头塞回去重算应得另一个值，证明差异只来自我的改动
h_withhdr, _ = c7d_hash('HEADER\n' + raw1)
ck('C11 反控：含表头重算得不同值（证明口径敏感）', h_withhdr != h_new, [h_new[:16], h_withhdr[:16]])

g2 = gate_src.replace("C7_TEXT_SHA256 = '636db13b", "C7_TEXT_SHA256 = '%s" % h_new[:64])
g2 = g2.replace("'20': 'bc77a9d9574965e09603086498ef31b87bb195f192db413ff97c89e472dbe5f3'",
                "'20': '%s'" % h_row20)
ck('C12 C7_TEXT_SHA256 已换新钉', h_new in g2)
ck('C13 C7_ROW_SHA[20] 已换新钉', h_row20 in g2)
open(GATE, 'w').write(g2)

# FREEZE
ub = open(UNV, 'rb').read()
ul = ub.decode('utf-8').split('\n')
target = [i for i, l in enumerate(ul) if l.split('\t')[0] == '20']
ck('C14 DISC_UNVERIFIABLE 里主键 20 恰 1 行', len(target) == 1, target)
i20 = target[0]
ck('C15 该行（1-based %d）col4 现在是 R144' % (i20 + 1), "'R144'" in ul[i20], ul[i20].split('\t')[3][:60])
u_old = hashlib.sha256(ub).hexdigest()
ck('C16 方法复现旧 FREEZE 钉', u_old.startswith('c49e2582'), u_old[:16])
ul2 = list(ul)
ul2[i20] = ul[i20].replace("grep=(?m)^GATE_VER = 'R144'", "grep=(?m)^GATE_VER = 'R145'")
ck('C17 只改了一个版本串', ul2[i20] != ul[i20] and "'R145'" in ul2[i20], ul2[i20].split('\t')[3][:60])
ub2 = '\n'.join(ul2).encode('utf-8')
dst2 = os.path.join(BL, 'DISC_UNVERIFIABLE.tsv.before_r145_sync_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst2, 'xb') as f: f.write(ub)
ck('C18 备份 wx 独占', open(dst2, 'rb').read() == ub, os.path.basename(dst2))
open(UNV, 'wb').write(ub2)
u_new = hashlib.sha256(ub2).hexdigest()
ck('C19 新 FREEZE != 旧', u_new != u_old, [u_old[:16], u_new[:16]])
g3 = open(GATE).read().replace("FREEZE_SHA256 = 'c49e2582", "FREEZE_SHA256 = '%s" % u_new[:64])
ck('C20 FREEZE_SHA256 已换新钉', u_new in g3)
open(GATE, 'w').write(g3)
json.dump({'fails': cc, 'c7d_old': h_old, 'c7d_new': h_new, 'row20_new': h_row20,
           'freeze_old': u_old, 'freeze_new': u_new, 'unv_line': i20 + 1},
          io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145l_sync.json', 'w'), indent=1)
print('\n=== 同步：FAIL %d ===' % len(cc))
