#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fix_r116_count.py —— R116 落盘后的**数字自错修正**（S-30）。

自错 S-30：四件套里写的「12 个脚本共 51 项断言」是错的。
逐项枚举本身是对的（r116a 7 + b 8 + c 7 + d 5 + e 6 + f 6 + g 5 + h 4 + i 5 + j 5 + k 7 + l 11），
但求和算出 51 —— 实际 sum = **76**。R14_COMMON 段更写成了「9 个脚本」（应为 12 个）。
这类错误正是「数字先实测再填」要防的：我枚举了分项却没把分项加一遍。
本脚本按写入纪律就地修正四处（R14_COMMON / 台账 / LEAD_LOCK / 看板），
并逐条补断言（不是只改数，要把「先加一遍」变成机检）。

纪律：备份独占创建 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验 CR 不变。
注意 R14_COMMON 是混合行尾（1081 CR + 其余裸 LF），故用**字节级**替换，
不重新拼接行（R115 自错 S-20 的教训）。
"""
import hashlib, json, os, sys, time

ROOT = '/home/t628/projects/ra2-campaign-forge'
W = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BASE = os.path.join(W, 'R17_LEAD_BASELINE')
SEG = os.path.join(ROOT, '_r116')
checks = []
PART = [7, 8, 7, 5, 6, 6, 5, 4, 5, 5, 7, 11]


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def crlf(p):
    d = open(p, 'rb').read()
    return d.count(b'\r'), d.count(b'\n'), len(d)


stamp = time.strftime('%Y%m%d_%H%M%S')
job = [0]


def backup(path):
    job[0] += 1
    bak = os.path.join(BASE, '%s.before_R116_fixcount_j%d_%s.bak'
                       % (os.path.basename(path), job[0], stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(path, 'rb').read())
    ck('B %s 备份独占创建且字节一致' % os.path.basename(path), sha(bak) == sha(path),
       os.path.basename(bak))
    return bak


TOT = sum(PART)
ck('N0 分项求和实测：%d 个脚本 %s ⇒ sum = %d（原落盘写的 51 是错的，差 %d）'
   % (len(PART), PART, TOT, abs(51 - TOT)),
   TOT == 76 and TOT != 51, {'parts': PART, 'sum': TOT})

# (path, old_bytes, new_bytes, 期望 CR)
RC = os.path.join(W, 'R14_COMMON.md')
LED = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
BRD = os.path.join(W, 'STATUS_BOARD.md')

JOBS = []

# 1) R14_COMMON：9 个 -> 12 个；51 -> 76
JOBS.append((RC, '断言与稳定性',
             '本轮 9 个脚本共 **51 项断言**（'.encode('utf-8'),
             '本轮 12 个脚本共 **76 项断言**（'.encode('utf-8'),
             1081))

# 2) 台账：51 -> 76
JOBS.append((LED, 'R116.10',
             'R116.10 **断言与纪律**：12 个脚本共 51 项断言全 PASS'.encode('utf-8'),
             'R116.10 **断言与纪律**：12 个脚本共 76 项断言全 PASS'.encode('utf-8'),
             337))

# 3) 看板：51 -> 76
JOBS.append((BRD, '断言与纪律',
             '12 个脚本共 **51 项断言全 PASS**'.encode('utf-8'),
             '12 个脚本共 **76 项断言全 PASS**'.encode('utf-8'),
             0))

# 4) LEAD_LOCK：在 ER10 之前插入 ER9b 的断言计数（含 S-30 自错登记）
JOBS.append((LCK, 'ER10',
             'ER10. **方法论（记住）**：'.encode('utf-8'),
             ('ER9b. **断言计数**：本轮 12 个脚本共 **76 项断言**'
              '（r116a 7 + b 8 + c 7 + d 5 + e 6 + f 6 + g 5 + h 4 + i 5 + j 5 + k 7 + l 11）全 PASS。'
              '🐞 自错 S-30：初落盘写的是「12 个脚本共 51 项断言」（R14_COMMON 段更误写「9 个脚本」），'
              '分项枚举本身对、**求和算错**；已机检更正为 76 并回读校验。'
              '教训：「数字先实测再填」必须包含「把分项加一遍」这一步。\n\n'
              'ER10. **方法论（记住）**：').encode('utf-8'),
             137))

for path, tag, old, new, want_cr in JOBS:
    cr_b, lf_b, by_b = crlf(path)
    ck('W1 %s 旧 CR==%d（实测 %d / LF %d / %d B）' % (os.path.basename(path), want_cr, cr_b, lf_b, by_b),
       cr_b == want_cr, (cr_b, lf_b, by_b))
    data = open(path, 'rb').read()
    cnt = data.count(old)
    ck('W1b %s 目标串在文件中唯一出现（实测 %d 次）' % (os.path.basename(path), cnt),
       cnt == 1, {'tag': tag, 'count': cnt, 'old': old[:40].decode('utf-8', 'replace')})
    if cnt != 1:
        continue
    backup(path)
    open(path, 'wb').write(data.replace(old, new, 1))
    back = open(path, 'rb').read()
    cr_a, lf_a, by_a = crlf(path)
    ck('W3 %s 回读 CR==%d（不变）实测 %d' % (os.path.basename(path), want_cr, cr_a), cr_a == want_cr,
       (cr_a, lf_a, by_a))
    # 自错 S-31（本轮自抓）：W4 初版断言「旧串已消失」，但对**前缀保持型插入**
    # （ER9b 插在 ER10 之前，new 里仍以 old 开头）旧串**必然还在**，断言恒假。
    # 正确判据：新串必须出现、且回读 == 单次替换结果。前向替换用「旧串消失」，插入用「新串出现」。
    is_insert = new.startswith(old) or old in new
    ok_content = (back == data.replace(old, new, 1))
    ok_old = (old not in back) if not is_insert else (new in back)
    ck('W4 %s 回读 == 单次替换结果（逐字节）；%s'
       % (os.path.basename(path),
          '插入型：新串必须出现' if is_insert else '替换型：旧串必须消失'),
       ok_content and ok_old, {'bytes': by_a, 'insert_form': is_insert})

# ---- 全库复核：四件套里不再出现错误的 51 / 9 个脚本 ----
for path, want_cr, bad in ((RC, 1081, ['9 个脚本共 **51', '51 项断言**（']),
                           (LED, 337, ['共 51 项断言']),
                           (LCK, 137, []),
                           (BRD, 0, ['**51 项断言全 PASS**'])):
    d = open(path, 'rb').read()
    nm = os.path.basename(path)
    left = [b for b in bad if b.encode('utf-8') in d]
    ck('V %s 已无错误计数残留（%d 处）' % (nm, len(left)), not left, left)
    ck('V2 %s CR 仍为 %d' % (nm, want_cr), d.count(b'\r') == want_cr, d.count(b'\r'))
    ck('V3 %s 含正确计数 76' % nm, b'76' in d, 'ok')

ck('V4 LEAD_LOCK 含 ER9b 计数说明与 S-30 自错登记',
   b'ER9b.' in open(LCK, 'rb').read() and b'S-30' in open(LCK, 'rb').read(), 'ok')

json.dump({'sum': TOT, 'parts': PART, 'checks': checks},
          open(os.path.join(SEG, 'fix_r116_count.json'), 'w'), indent=1, ensure_ascii=False)
bad = sum(1 for c in checks if not c['ok'])
print('\n--- fix_r116_count: %d checks, PASS %d, FAIL %d ---'
      % (len(checks), len(checks) - bad, bad))
sys.exit(1 if bad else 0)
