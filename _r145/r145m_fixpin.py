#!/usr/bin/env python3
"""R145 M：修复 r145l 的常量替换 bug（S-320）—— 我只替换了引号后的前 8 个 hex 字符，
旧常量的剩余 56 个 hex 被留在原地 ⇒ 常量变成 120 个 hex，门禁报「值 == 值 却不相等」。

修法：用整常量正则替换（C7_TEXT_SHA256 / FREEZE_SHA256 各一次），并加三条可失败断言：
  R1 新常量长度必须恰 64
  R2 回读常量必须等于实测值
  R3 反控：把「只替换前缀」的错法再跑一遍，必须得到长度 != 64 的串（证明修法有分辨力）
"""
import hashlib, io, json, os, re, time
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

raw = io.open(RCH, encoding='utf-8').read()
h_new, rows = c7d_hash(raw)
row20 = [r for r in rows if len(r) == 7 and r[0] == '20'][0]
h_row20 = hashlib.sha256(('%s\t%s\t%s' % (row20[0], row20[4].strip(), row20[5].strip())).encode()).hexdigest()
u_new = hashlib.sha256(open(UNV, 'rb').read()).hexdigest()

src = open(GATE).read()
m7 = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", src)
mfr = re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", src)
ck('R0 找到两个常量', m7 is not None and mfr is not None)
ck('R0b 现状：C7 常量长度 120（被污染的形态）', len(m7.group(1)) == 120, len(m7.group(1)))
ck('R0c 现状：FREEZE 常量长度 120', len(mfr.group(1)) == 120, len(mfr.group(1)))
# 反控：错法（只换前 8 hex）必须产生长度 != 64 的串
bad = re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{8}", "C7_TEXT_SHA256 = '%s" % h_new[:8], src)
got_bad = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", bad).group(1)
ck('R1 反控：只换前缀的错法得到长度 != 64（128 或 120）', len(got_bad) != 64, len(got_bad))

t2 = re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]+'", "C7_TEXT_SHA256 = '%s'" % h_new, src)
t2 = re.sub(r"FREEZE_SHA256 = '[0-9a-f]+'", "FREEZE_SHA256 = '%s'" % u_new, t2)
t2 = re.sub(r"'20': '[0-9a-f]+'", "'20': '%s'" % h_row20, t2, count=1)
ck('R2 三个常量都已整串替换', h_new in t2 and u_new in t2 and h_row20 in t2)
dst = os.path.join(BL, 'check_disc.py.before_r145_fixpin_%s.bak' % time.strftime('%Y%m%d_%H%M%S'))
with io.open(dst, 'xb') as f: f.write(src.encode('utf-8'))
ck('R3 备份 wx 独占且逐字节相同', open(dst, encoding='utf-8').read() == src, os.path.basename(dst))
open(GATE, 'w').write(t2)
back = open(GATE).read()
ck('R4 回读 C7 常量 == 实测且长度 64', re.search(r"C7_TEXT_SHA256 = '([0-9a-f]+)'", back).group(1) == h_new and len(h_new) == 64, len(h_new))
ck('R5 回读 FREEZE 常量 == 实测且长度 64', re.search(r"FREEZE_SHA256 = '([0-9a-f]+)'", back).group(1) == u_new and len(u_new) == 64, len(u_new))
ck('R6 回读 ROW[20] == 实测', re.search(r"'20': '([0-9a-f]+)'", back).group(1) == h_row20, h_row20[:16])
ck('R7 门禁文件里不再有 120 hex 的常量', not re.search(r"= '[0-9a-f]{120}'", back))
json.dump({'fails': cc, 'c7d': h_new, 'row20': h_row20, 'freeze': u_new},
          io.open('/home/t628/projects/ra2-campaign-forge/_r145/r145m_fixpin.json', 'w'), indent=1)
print('\n=== 修复常量：FAIL %d ===' % len(cc))
