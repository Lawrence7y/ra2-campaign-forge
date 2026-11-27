# -*- coding: utf-8 -*-
"""r178i：FACT_INDEX_CURRENT.md 指针补到 V561。
该文件仍不被任何门禁读取（本轮第七次确认）—— 先给证据再改。
"""
import glob, hashlib, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
BASE = os.path.join(TIER, 'R17_LEAD_BASELINE')
NEWDIR = 'R17_R129_FACTINDEX_V561'
NEWSHA = 'dd2c55c6f8aeadf3195bf1dc7fc9bf39ce70ed5ad771c76d52b80e86fe25fee7'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


# 1. 先证「无门禁读它」
gates = {
    'check_disc.py': os.path.join(TIER, 'check_disc.py'),
    'facts_floors.py': os.path.join(ROOT, '_r160/facts_floors.py'),
    'gate_runner.py': os.path.join(ROOT, '_r161/gate_runner.py'),
}
tot = 0
for k, p in gates.items():
    s = open(p, encoding='utf-8').read()
    n = s.count('FACT_INDEX_CURRENT')
    tot += n
    print('  %-18s FACT_INDEX_CURRENT 命中 %d' % (k, n))
ck('A1 三个门禁合计命中 0（指针无门禁读，第七次确认）', tot == 0, tot)

# 2. 实测新版本存在且 sha 对
p = os.path.join(TIER, NEWDIR, 'FACT_INDEX.tsv')
raw = open(p, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
ck('B1 V561 存在', os.path.exists(p))
ck('B2 V561 sha 匹配', sha == NEWSHA, sha[:16])
ck('B3 V561 bytes 133317', len(raw) == 133317, len(raw))

dirs = sorted(glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V[0-9][0-9][0-9]')),
              key=lambda d: int(re.search(r'_V(\d+)$', d).group(1)))
vers = [int(re.search(r'_V(\d+)$', d).group(1)) for d in dirs]
# 反控：三位数过滤后不应再混入 V53 / V58 这类两位数旧版
ck('B4a 无两位数旧版混入', all(v >= 100 for v in vers), [v for v in vers if v < 100])
want = [v for v in vers if 530 <= v <= 561]
ck('B4b 版本号 530..561 连续 32 份', want == list(range(530, 562)),
   (len(want), want[:2], want[-2:]))
ck('B5 V561 是最大版本', max(vers) == 561)

# 3. 改指针
src = open(PTR, encoding='utf-8').read()
ck('C1 指针 CR=0', '\r' not in src, src.count('\r'))
ck('C2 旧指针指 V560', 'R17_R128_FACTINDEX_V560' in src)
ck('C3 指针不被门禁读已证', True)

new = src
new = new.replace('R17_R128_FACTINDEX_V560', NEWDIR)
new = new.replace('ede48f3c3204804013658046b17ebc7cff23e5b5ec024407a2f79555147ce6a4', NEWSHA)
new = new.replace('| 字节数 | 130510 |', '| 字节数 | 133317 |')
new = new.replace('| 声明轮次 | R177 |', '| 声明轮次 | R178 |')
new = new.replace('版本号 530..560 连续无缺', '版本号 530..561 连续无缺')
new = new.replace('（现盘 530..560 连续 31 份）', '（现盘 530..561 连续 32 份）')
new = new.replace('V530..V560 是 31 个可独立复核的快照', 'V530..V561 是 32 个可独立复核的快照')
new = new.replace('**R177 四次订正**', '**R178 第五次订正**')
new = new.replace('R128 下现已有 V556/V557/V558/V559/V560 五份，同一轮内可生成多版，'
                  '故「只有这一个目录」「R128 下三份」「R128 下四份」三种写法均已失效',
                  'R128 同一目录下已累计 V556..V560 五份、R129 目录下为 V561，同一轮内可生成多版，'
                  '故「只有这一个目录」「三份」「四份」「五份」四种写法均已失效')
ck('D1 新指针含新目录', NEWDIR in new, new.count(NEWDIR))
ck('D2 新指针含新 sha', NEWSHA in new)
ck('D3 新指针含 133317', '133317' in new)
ck('D4 新指针含 R178', 'R178' in new)
ck('D5 新指针不含旧 sha', 'ede48f3c32048040' not in new, new.count('ede48f3c32048040'))
ck('D6 新指针 CR=0', '\r' not in new, new.count('\r'))
ck('D7 声明依据已第五次订正', '第五次订正' in new)
ck('D8 530..561 表述在位', '530..561' in new)

if FAIL:
    print('ABORT %d FAIL' % FAIL); sys.exit(1)
bak = os.path.join(BASE, 'FACT_INDEX_CURRENT.md.before_r178.bak')
with open(bak, 'xb') as f:
    f.write(src.encode('utf-8'))
ck('E1 备份 sha == 前态', hashlib.sha256(open(bak, 'rb').read()).hexdigest()
   == hashlib.sha256(src.encode()).hexdigest())
open(PTR, 'w', encoding='utf-8', newline='').write(new)
ck('E2 回读一致', open(PTR, encoding='utf-8').read() == new)
print()
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
