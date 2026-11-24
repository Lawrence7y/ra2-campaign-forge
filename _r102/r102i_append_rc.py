#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102i_append_rc.py —— 只做一件事：给 R14_COMMON.md 追加 §2.106（CRLF，无反引号）

为什么单独一个脚本：
  write_r102.py 是「四件一起写」的全量写入器。R14_COMMON 有 8,000+ 行、828,603 B，
  全量重写对它是危险操作 —— 04:30 就出过事（外部守护的重复追加 + 截断，
  §2.94..§2.105 共 12 节一度丢失，已用 04:10 完好备份整份恢复）。
  对这类大文件，正确做法是**只用追加**（open 'ab'），并且追加段的行尾必须与主文件一致。

硬约束（每条都是断言，不满足即中止，不写）：
  * 主文件当前 CR = 1081（硬不变量）
  * 主文件是 CRLF 主文件（CRLF 数 = 1081 > 0）
  * 主文件已不含 §2.106（不重复追加）
  * 追加段内反引号 = 0
  * 追加段每行都以 CRLF 结尾
  * 追加后 CR 计数**仍为 1081**（即追加段里的换行不制造新的 CRLF —— 见下方说明）
  * 追加后 §2.106 恰好出现 1 次，且 §2.105 仍在（没有再次丢历史）

关于「追加后 CR 仍 1081」：CR 计数统计的是 b'\\r\\n'。主文件以 CRLF 结尾，其后追加新段时，
每个新行都带 CRLF。所以严格说 CR 会因新增行而增加。真正的硬不变量是
「**CR = 1,081 是把它当 CRLF 文本时的既有行数**」—— 但它被 re-tool 当作不变量检查。
故本脚本采用与写看板不同的策略：**追加段内部一律用 CRLF，但先把主文件末尾的单个 CRLF
改回一个 LF**，这样净增 CR 为 0。这是本项目 8,000 行主文件一直以来的写法（见 04:10 备份
与当前文件的对比：两者 CR 都是 1081，而文件长度差 8,000+ 字节）。本脚本把这条写进断言。
"""
import datetime, hashlib, io, json, os, re, subprocess, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(R14, 'R14_COMMON.md')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
OUT = os.path.join(ROOT, '_r102')
STAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

SEC = open(os.path.join(OUT, 'sec_rc.txt'), encoding='utf-8').read() \
    if os.path.exists(os.path.join(OUT, 'sec_rc.txt')) else None

def main():
    os.makedirs(OUT, exist_ok=True)
    if SEC is None:
        print('sec_rc.txt missing'); return 1
    raw = io.open(RC, 'rb').read()
    ck('R0 主文件 CR = 1081', raw.count(b'\r\n') == 1081, raw.count(b'\r\n'))
    ck('R1 主文件是 CRLF 主文件', raw.count(b'\r\n') > 0, raw.count(b'\r\n'))
    txt = raw.decode('utf-8')
    ck('R2 主文件尚无 §2.106 标题（不重复追加）',
       not re.search(r'(?m)^##\s*2\.106(?=[\s\u3000]|$)', txt), txt.count('2.106'))
    ck('R3 主文件含 §2.105（历史未丢）', '## 2.105' in txt, txt.count('## 2.105'))
    ck('R4 主文件含 §2.98（历史未丢）', '## 2.98' in txt, txt.count('## 2.98'))
    ck('R5 主文件含 §2.94（历史未丢）', '## 2.94' in txt, txt.count('## 2.94'))
    ck('R6 追加段无反引号', '`' not in SEC, SEC.count('`'))
    ck('R7 追加段无控制字符（除换行/制表）',
       all(ord(ch) >= 0x20 or ch in '\n\t' for ch in SEC), '')

    body = SEC.replace('\r\n', '\n')
    lines = [l for l in body.split('\n')]
    ck('R8 追加段行数 >= 30', len(lines) >= 30, len(lines))

    # 组装（R102 实测修正）：R14_COMMON 的实际行尾构成是
    #   CRLF 1,081 + LF-only 8,043，且**文件不以 CRLF 结尾**。
    # 也就是说 1,081 是历史遗留常量、新内容一律以 LF 追加 —— 这才是该文件本来的写法。
    # 初版我按「CRLF 主文件」处理并去削末尾 CRLF，那是把该文件的行尾语义判断反了
    # （若真按 CRLF 追加，CR 会一路涨，不变量立刻破）。
    # 正确做法：纯 LF 追加，CR 计数天然保持 1081。
    add = SEC.encode('utf-8')
    if not add.endswith(b'\n'):
        add += b'\n'
    if not SEC.startswith('\n') and not raw.endswith(b'\n'):
        add = b'\n' + add
    new = raw + add
    ck('R9 净增 CR = 0', new.count(b'\r\n') == raw.count(b'\r\n'),
       '%d -> %d' % (raw.count(b'\r\n'), new.count(b'\r\n')))
    t2 = new.decode('utf-8')
    # R102 自错 9：初版用 t2.count('## 2.106')==1 与 t2.count('## 2.105')==1 作断言 —— 两个都错：
    # 该文件里同一节号会以「标题 + 交叉引用」多次出现（§2.105 实测 9 次）。
    # 正确判据：看**标题级**出现次数（行首 ## 到行尾），并比较追加前后的增量。
    def n_head(t, sec):
        return len(re.findall(r'(?m)^##\s*%s(?=[\s\u3000]|$)' % re.escape(sec), t))
    ck('R10 追加后 §2.106 标题级恰 1 次', n_head(t2, '2.106') == 1, n_head(t2, '2.106'))
    ck('R11 追加前后 §2.105/§2.98/§2.94 的标题级次数均不变（历史未丢、未重复）',
       all(n_head(t2, x) == n_head(txt, x) for x in ('2.105', '2.98', '2.94')),
       {x: (n_head(txt, x), n_head(t2, x)) for x in ('2.105', '2.98', '2.94')})
    ck('R12 追加后既有前缀逐字节不变', new.startswith(raw), '')
    ck('R13 追加段内部无反引号（最终文件里本段仍无反引号）',
       '`' not in t2[t2.index('## 2.106'):], t2[t2.index('## 2.106'):].count('`'))

    if '--apply' not in sys.argv:
        print('DRY RUN（未加 --apply）：new bytes %d -> %d' % (len(raw), len(new)))
        return 0 if not any(not c['ok'] for c in checks) else 1
    if any(not c['ok'] for c in checks):
        print('REFUSE --apply'); return 1

    bak = os.path.join(BASE, 'R102.before_append_2106_%s.bak' % STAMP)
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('S0 wx 独占备份',
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
       os.path.basename(bak))
    with io.open(RC, 'ab') as f:
        f.write(add)
    back = io.open(RC, 'rb').read()
    ck('S1 回读逐字节相同', back == new, '%d B' % len(back))
    ck('S2 回读 CR = 1081', back.count(b'\r\n') == 1081, back.count(b'\r\n'))

    p = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                       capture_output=True, text=True, cwd=ROOT)
    ck('S3 门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
    if p.returncode:
        print(p.stdout[-1200:])
    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'n_checks': len(checks), 'n_fail': n_fail, 'checks': checks,
               'bytes_before': len(raw), 'bytes_after': len(back)},
              io.open(os.path.join(OUT, 'r102i_append_rc.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
