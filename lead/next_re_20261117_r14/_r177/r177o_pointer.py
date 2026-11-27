# -*- coding: utf-8 -*-
"""R177：FACT_INDEX_CURRENT.md 指针 V559 -> V560（本文件仍不被任何门禁读 —— 第六次确认）。"""
import glob, hashlib, os, re, sys
P = F = 0
def ck(n, c, d=''):
    global P, F
    if c: P += 1; print('PASS', n, d)
    else: F += 1; print('FAIL', n, d)

PT = 'FACT_INDEX_CURRENT.md'
NEW = 'R17_R128_FACTINDEX_V560'
dst = os.path.join(NEW, 'FACT_INDEX.tsv')
raw = open(dst, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
ck('A1 V560 sha', sha == 'ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4', sha[:16])
ck('A2 V560 bytes', len(raw) == 130510, len(raw))
ck('A3 行数 55', raw.count(b'\n') == 55, raw.count(b'\n'))
ck('A4 CR=0', raw.count(b'\r') == 0)

# 事实核对：版本目录闭世界
vers = sorted(int(m.group(1)) for d in glob.glob('R17_R*_FACTINDEX_V5*')
              for m in [re.search(r'_V(\d+)$', d)] if m and int(m.group(1)) >= 530)
ck('B1 530..560 连续 31 份', vers == list(range(530, 561)), (vers[0], vers[-1], len(vers)))
ck('B2 V560 是最大版本号', vers[-1] == 560)

txt = open(PT, encoding='utf-8').read()
old_txt = txt
ck('C1 旧指针指 V559', 'R17_R128_FACTINDEX_V559' in txt)
ck('C2 旧 sha 在指针里', 'e4642d554d8ba9f1' in txt)
ck('C3 指针 CR=0', '\r' not in txt)

new = txt.replace('R17_R128_FACTINDEX_V559', NEW)
new = new.replace('e4642d554d8ba9f1dab25b6a2b456e365252051035f9104003b58ff622d489e9', sha)
new = new.replace('| 字节数 | 129405 |', '| 字节数 | %d |' % len(raw))
new = new.replace('| 声明轮次 | R176 |', '| 声明轮次 | R177 |')
# 声明依据段：R128 下现盘 530..560 共 31 份
new = re.sub(r'版本号 530\.\.[0-9]+ 连续无缺',
             '版本号 530..560 连续无缺（**R177 四次订正**：R128 下现已有 V556/V557/V558/V559/V560 五份，'
             '同一轮内可生成多版，故「只有这一个目录」「R128 下三份」「R128 下四份」三种写法均已失效；'
             '现依据固定为「版本号最大（现盘 530..560 连续 31 份）+ 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」）', new)
new = re.sub(r'V530\.\.V[0-9]+ 是 [0-9]+ 个可独立复核的快照', 'V530..V560 是 31 个可独立复核的快照', new)
new = re.sub(r'R128 下现已有 V[0-9/，、]*\*?\*?[一二三四五]?份?', 'R128 下现已有 V556/V557/V558/V559/V560 五份', new) if False else new
new = new.replace('（D0 已钉 V557 的 sha256）', '（D0 已钉 V560 的 sha256）')

ck('D1 新目录串在指针 恰 2 次', new.count(NEW) == 2, new.count(NEW))
ck('D2 旧目录串已无', 'R17_R128_FACTINDEX_V559' not in new, new.count('R17_R128_FACTINDEX_V559'))
ck('D3 新 sha 出现 1 次', new.count(sha) == 1, new.count(sha))
ck('D4 字节数 130510', '| 字节数 | 130510 |' in new)
ck('D5 声明轮次 R177', '| 声明轮次 | R177 |' in new)
ck('D6 CR 仍 0', '\r' not in new)
ck('D7 版本域写成 530..560 连续 31 份', '530..560 连续 31 份' in new)
ck('D8 「R128 下五份」写明', 'V556/V557/V558/V559/V560 五份' in new)
ck('D9 快照份数 31', 'V530..V560 是 31 个可独立复核的快照' in new or '31 个可独立复核' in new)

# 门禁不读指针（第六次确认）
grep_hits = {}
for f in ('/home/t628/projects/ra2-campaign-forge/_r160/facts_floors.py',
          '/home/t628/projects/ra2-campaign-forge/_r161/gate_runner.py',
          'check_disc.py'):
    t = open(f, encoding='utf-8', errors='replace').read()
    grep_hits[os.path.basename(f)] = t.count('FACT_INDEX_CURRENT')
print('  指针被门禁读取次数:', grep_hits)
ck('E1 三个门禁都不读指针（第六次确认）', sum(grep_hits.values()) == 0, grep_hits)

if F:
    print('ABORT %d FAIL' % F); sys.exit(1)
with open(PT, 'wb') as f:
    f.write(new.encode('utf-8'))
rb = open(PT, 'rb').read()
ck('F1 回读相等', rb == new.encode('utf-8'))
ck('F2 回读 CR=0', rb.count(b'\r') == 0)
print('指针 = %d B / cr=%d' % (len(rb), rb.count(b'\r')))
print('---- %d PASS / %d FAIL ----' % (P, F))
