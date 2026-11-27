#!/usr/bin/env python3
"""R146 L：C7d 文本指纹 + C7_ROW_SHA['20'] 重钉（逐字照抄门禁口径）。

门禁口径（不许自己发挥）：
  raw   = DISC_RECHECK.tsv 全文
  rows  = raw.split('\n')[1:]        （**丢表头**）
  blob  = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r)==7)
  C7_ROW_SHA[key] = sha256('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()))
S-320/S-325 教训：断言要比长度与形状，不只比值；整常量替换不做前缀拼接。
"""
import io, os, re, json, hashlib, time, sys
BASE = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL = os.path.join(BASE, 'R17_LEAD_BASELINE')
GATE = os.path.join(BASE, 'check_disc.py')
RCH = os.path.join(BASE, 'DISC_RECHECK.tsv')
FAILS = []
def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c: FAILS.append(n)
    return bool(c)
def rd(p): return io.open(p, encoding='utf-8', newline='').read()

def c7d(raw_text):
    raw = raw_text.split('\n')
    rows = [l.split('\t') for l in raw[1:]]
    blob = '\n'.join('%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip()) for r in rows if len(r) == 7)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), rows

raw1 = rd(RCH)
gate = rd(GATE)
ck('DR CR == 0', raw1.count('\r') == 0)
ck('DR 32 行（表头 + 31）', len([l for l in raw1.split('\n') if l.strip()]) == 32,
   len([l for l in raw1.split('\n') if l.strip()]))
ck('主键 20 的 col6 已是 R146', "grep=(?m)^GATE_VER = 'R146'" in raw1)
ck('只有一行含 GATE_VER', sum(1 for l in raw1.split('\n') if 'GATE_VER' in l) == 1)

h_new, rows = c7d(raw1)
pinned = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", gate).group(1)
ck('门禁内 C7_TEXT_SHA256 长度 64', len(pinned) == 64, len(pinned))
ck('旧钉前缀 13ea4fd3（R145 钉）', pinned.startswith('13ea4fd3'), pinned[:16])
ck('新算值 != 旧钉（说明 TSV 的改动被指纹捕捉到）', h_new != pinned, [pinned[:16], h_new[:16]])
ck('新算值长度 64', len(h_new) == 64, len(h_new))

row20 = [r for r in rows if len(r) == 7 and r[0] == '20'][0]
h_row20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
old_row20 = re.search(r"'20': '([0-9a-f]+)'", gate).group(1)
ck('门禁内 C7_ROW_SHA[20] 长度 64', len(old_row20) == 64, len(old_row20))
ck('C7_ROW_SHA[20] 旧值前缀 378ef7cd（R145 钉）', old_row20.startswith('378ef7cd'), old_row20[:16])
ck('C7_ROW_SHA[20] 新值长度 64', len(h_row20) == 64, len(h_row20))
ck('C7_ROW_SHA[20] 新值 != 旧值', h_row20 != old_row20)
# 反控：把表头塞回去重算应得另一个值（证明「丢表头」这个口径是敏感的）
h_hdr, _ = c7d('HEADER\n' + raw1)
ck('反控：含表头重算得不同值', h_hdr != h_new, [h_new[:16], h_hdr[:16]])
# 反控：先打印目标行再断言（S-299）
ck('打印目标行确认为主键 20', row20[0] == '20' and row20[1] == '§2.27', [row20[0], row20[1]])

g2 = gate.replace("C7_TEXT_SHA256 = '%s'" % pinned, "C7_TEXT_SHA256 = '%s'" % h_new)
ck('C7_TEXT_SHA256 已整常量替换', ("C7_TEXT_SHA256 = '%s'" % h_new) in g2)
g2 = g2.replace("'20': '%s'" % old_row20, "'20': '%s'" % h_row20)
ck("C7_ROW_SHA['20'] 已整常量替换", ("'20': '%s'" % h_row20) in g2)
ck('替换后两条常量长度均为 64',
   len(re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", g2).group(1)) == 64
   and len(re.search(r"'20': '([0-9a-f]+)'", g2).group(1)) == 64)
ck('替换后内容变化且 CR 仍 0', g2 != gate and g2.count('\r') == 0)

src = open(GATE, 'rb').read()
dst = os.path.join(BL, 'check_disc.py.before_r146_c7d_' + time.strftime('%Y%m%d_%H%M%S') + '.bak')
io.open(dst, 'xb').write(src)
ck('备份 wx 独占且逐字节相同', open(dst, 'rb').read() == src, os.path.basename(dst))
io.open(GATE, 'w', encoding='utf-8', newline='').write(g2)
gb = rd(GATE)
ck('门禁回读含新 C7d 与新行钉', h_new in gb and h_row20 in gb)
ck('门禁回读 CR == 0', gb.count('\r') == 0)

json.dump({'fails': FAILS, 'c7d_old': pinned, 'c7d_new': h_new,
           'row20_old': old_row20, 'row20_new': h_row20},
          open('/home/t628/projects/ra2-campaign-forge/_r146/r146l_c7d.json', 'w'), indent=1)
print('\n=== C7d 重钉 FAILS %d ===' % len(FAILS)); print(FAILS)
sys.exit(1 if FAILS else 0)
