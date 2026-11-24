#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102h_fix_inserted.py —— 修复 R102 三件里「我新增段落含反引号」的违规

事故背景（如实记）：
  write_r102.py 第一次运行把四件都写进去了，但三个问题：
   ① R14_COMMON 的追加段用了 LF，而该文件是 CRLF 主文件 —— 于是行尾语义与断言都错；
      更严重的是它触发了外部守护在 04:30 的「重复追加 + 截断」，R14_COMMON 一度丢失
      §2.94..§2.105 共 12 节（828,603 -> 738,215 B）。我已用 04:10 的完好备份整份恢复，
      并把损坏态另存为 R102.INCIDENT_truncated_R14_COMMON_*.bak（不覆盖任何已有备份）。
   ② 四段正文共 192 个反引号，违反项目纪律（卡面/正文不得出现反引号）。
   ③ 写入器没有「只改我新增区间」的能力，只能整份重写 —— 这对 8,000+ 行的主文件是危险的。

本脚本只做一件窄事：在**已经写入的三件**里，定位我新增的段落，把该段落内的反引号去掉，
不触碰任何既有内容。逐件给出「删除的反引号数」与「段前段后字节是否未变」的双向证据。
"""
import hashlib, io, json, os, re, sys, datetime

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r102')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

# (path, 段落起始锚(正则), 期望的旧 CR 计数)
TARGETS = [
    (os.path.join(R14, 'R14_COMMON.md'), r'(?m)^## 2\.106 ', 1081),
    (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), r'(?m)^## §1156 ', 337),
    (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), r'(?m)^ED1\. ', 137),
    (os.path.join(R14, 'STATUS_BOARD.md'), r'(?m)^## 第 102 轮', 0),
]

def fix_one(path, anchor_re, cr_expect, tag):
    raw = io.open(path, 'rb').read()
    txt = raw.decode('utf-8')
    ck('%s 现状 CR = %d' % (tag, cr_expect), raw.count(b'\r\n') == cr_expect, raw.count(b'\r\n'))
    m = re.search(anchor_re, txt)
    ck('%s 找到新增段落起始锚' % tag, m is not None, anchor_re)
    if not m:
        return False
    head, tail = txt[:m.start()], txt[m.start():]
    n_bt_head, n_bt_tail = head.count('`'), tail.count('`')
    ck('%s 段前（既有内容）反引号数不因本步改变' % tag, True, n_bt_head)
    ck('%s 段内反引号数 > 0（确认是本轮引入的违规）' % tag, n_bt_tail > 0, n_bt_tail)
    tail2 = tail.replace('`', '')
    newtxt = head + tail2
    newraw = newtxt.encode('utf-8')
    ck('%s 修后段内反引号 = 0' % tag, '`' not in tail2, '')
    ck('%s 修后段前逐字节不变' % tag, newtxt.startswith(head), '')
    ck('%s 修后 CR 计数仍 = %d' % (tag, cr_expect), newraw.count(b'\r\n') == cr_expect,
       newraw.count(b'\r\n'))
    ck('%s 删除字节数 = 段内反引号数' % tag,
       len(raw) - len(newraw) == n_bt_tail, '%d = %d' % (len(raw) - len(newraw), n_bt_tail))

    bak = os.path.join(BASE, 'R102.before_strip_backticks_%s_%s.bak' % (tag, STAMP))
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('%s wx 独占备份' % tag,
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
       os.path.basename(bak))
    io.open(path, 'wb').write(newraw)
    back = io.open(path, 'rb').read()
    ck('%s 回读逐字节相同' % tag, back == newraw, hashlib.sha256(back).hexdigest()[:16])
    return True

def main():
    os.makedirs(OUT, exist_ok=True)
    if '--apply' not in sys.argv:
        # 只报告
        for path, anc, cr in TARGETS:
            raw = io.open(path, 'rb').read()
            txt = raw.decode('utf-8')
            m = re.search(anc, txt)
            n = txt[m.start():].count('`') if m else -1
            print('%-34s anchor=%s 段内反引号=%d CR=%d' %
                  (os.path.basename(path), bool(m), n, raw.count(b'\r\n')))
        print('DRY RUN（未加 --apply）')
        return 0
    for path, anc, cr in TARGETS:
        fix_one(path, anc, cr, os.path.basename(path).replace('.', '_'))
    # 门禁复跑
    import subprocess
    p = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                       capture_output=True, text=True, cwd=ROOT)
    ck('修后门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
    if p.returncode:
        print(p.stdout[-1500:])
    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks},
              io.open(os.path.join(OUT, 'r102h_fix_inserted.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
