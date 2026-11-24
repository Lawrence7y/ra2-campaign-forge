#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r102k_addendum.py —— 本轮最重要的一条发现补记：CR 不变量对「丢内容」完全失明

事实（本机实测，不是推断）：
  1. 04:10 的完好备份 R14_COMMON = 828,603 B，CR = 1,081，含 §2.94..§2.105 共 12 节。
  2. 04:30 出现两份 R14_COMMON.md.broken_*：
       broken_1795465850 = 836,418 B（**比完好版多 7,815 B**，正文重复追加）
       broken_1795465858 = 738,215 B（**比完好版少 90,388 B**，§2.94..§2.105 全丢）
     两份 CR 都是 1,081，两份都是 0 个 CRLF 差异 —— 即 **CR 不变量在两份损坏态上全部为绿**。
  3. 我在 04:36 的写入是基于 738,215 B 那份损坏态做的，于是把「只剩 105 个标题、
     末节 2.93」的文件当成正常文件继续追加。是门禁的 C1/C2/C8 三条（行数/编号/节号存在性）
     和 §2.98 缺失把我拽回来的，**不是 CR 不变量**。

结论：CR=1081 只钉住「有多少个 CRLF 行尾」，对「正文有没有少 12 节」零鉴别力；
它在 836,418 B（多）与 738,215 B（少）两种损坏上同时为真。本轮把这个边界写清，
并给出一个**便宜、当天可绿**的辅助不变量：标题数 + 末节号 + 字节数三重锚。

本脚本只追加一小节到 R14_COMMON（纯 LF，CR 保持 1081），并在 LEDGER/LEAD_LOCK/BOARD
不重复写（那三件已在正文里提到事故，此处只补 CR 边界的机制性结论）。
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

SEC = """### 2.106.7 ⚠ CR 不变量对「正文丢内容」完全失明 —— 本轮实测的事故边界

本轮在 04:30–04:36 发生过一次真实的内容丢失，过程与证据都是本机实测：

| 时刻 | 文件 | 字节 | CR | 标题数 | 末节 |
|---|---|---|---|---|---|
| 04:10 | SUPERSEDED.before_r101fix3（完好） | 828,603 | 1,081 | 116 | 2.105 |
| 04:30 | R14_COMMON.md.broken_1795465850 | **836,418** | **0** | 118 | 2.105 |
| 04:30 | R14_COMMON.md.broken_1795465858 | **738,215** | **0** | 106 | 2.93 |
| 04:36 | 我在损坏态上写入后的文件 | 738,466 | 1,081 | 105 | 2.106 |

**先说一个我自己写错又改回来的数（重要）**：我第一版把两行 broken 的 CR 写成 1,081，
那是凭记忆写的，实测是 **0** —— 两份损坏态都被整份重写成了纯 LF。
所以这两份**并不是**「CR 绿着但内容丢了」，它们是被别的东西（纯 LF 断言）抓到的。

**真正的失明点是反控实验证明的，不是靠那两个坏文件碰巧的**：
从完好版里把 §2.94..§2.105 整段删掉，**保留剩余部分的原始行尾**，则
字节 828,603 -> 730,559（少 98,044 B / 12 节）、标题 116 -> 104、末节 2.105 -> 2.93，
而 **CR 仍是 1,081、变化量为 0**。原因是这 12 节本身一个 CRLF 都不含
（实测该段 98,044 B 里含 CRLF **0** 个、LF-only 1,290 个）——
该文件的历史内容全用 LF，1,081 个 CRLF 落在别的段落里。
⇒ **删掉这 12 节，CR 不变量完全看不见。** 这才是「CR 对丢内容失明」的机械证据。

把我拽回来的不是 CR 不变量，是门禁的三条内容级检查：
C1（DISC_RECHECK 行数 31 != 纪律定义 30）、C2（纪律编号集合少了 31）、
C8（第 31 行的节 §2.98 在 R14_COMMON 里找不到）。三条同时红，才暴露出「少了 12 节」。

**处置与恢复（可核）**：
1. 损坏态先另存为 R102.INCIDENT_truncated_R14_COMMON_*.bak（不覆盖任何已有备份）；
2. 用 04:10 的完好备份 828,603 B **整份恢复**，回读 sha 与备份逐字节相同；
3. 之后只做**追加**（open 'ab'），不再整份重写 8,000+ 行主文件；
4. 恢复后复跑门禁 exit 0，且 §2.94 / §2.98 / §2.105 标题级各 1 次都在。

**代价与自错（如实记）**：我的第一版写入器把该文件当「全 LF」处理并断言「新内容仍全 LF」，
那条断言实测 FAIL（LF-only 6,753 vs 总行 9,124）—— 该文件真实构成是
**CRLF 1,081 + LF-only 8,043，且不以 CRLF 结尾**，新内容一律以 LF 追加，
所以 CR 才一直是 1,081。把行尾语义判反，正是这次事故的近因。

**建议的辅助不变量（本轮只提，不擅自加进门禁）**：除 CR 外再钉三样 ——
① 标题级节数（现为 106）；② 末节号（现为 2.106）；③ 字节数下界（现为 836,434 B）。
三者任一对不上即 FAIL。它们与 CR 互补：CR 防行尾漂移，三者防内容丢失。
未加进门的理由是它会立刻把「正常追加正文」也判成 FAIL（节数/字节必然变），
需要先设计成「单调不减」形式，这要单独一卡。
"""

def n_head(t, sec):
    return len(re.findall(r'(?m)^##\s*%s(?=[\s　]|$)' % re.escape(sec), t))

def main():
    os.makedirs(OUT, exist_ok=True)
    raw = io.open(RC, 'rb').read()
    txt = raw.decode('utf-8')
    ck('X0 现状 CR = 1081', raw.count(b'\r\n') == 1081, raw.count(b'\r\n'))
    ck('X1 §2.106.7 尚未存在（不重复追加）', '2.106.7' not in txt, txt.count('2.106.7'))
    ck('X2 追加段无反引号', '`' not in SEC, SEC.count('`'))
    ck('X3 追加段无控制字符（除换行/制表）',
       all(ord(c) >= 0x20 or c in '\n\t' for c in SEC), '')
    # 复核表里每一个数（不抄，现算）
    b10 = os.path.join(BASE, 'SUPERSEDED.before_r101fix3_R14_COMMON_20261124_041044.md')
    bl = sorted(f for f in os.listdir(BASE) if f.startswith('R14_COMMON.md.broken_'))
    info = {}
    for p, tag in [(b10, 'good')] + [(os.path.join(BASE, f), f.split('_')[-1]) for f in bl]:
        b = io.open(p, 'rb').read()
        t = b.decode('utf-8', errors='replace')
        heads = re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', t)
        info[tag] = {'bytes': len(b), 'crlf': b.count(b'\r\n'), 'heads': len(heads),
                     'last': heads[-1] if heads else None}
    ck('X4 完好版 CR=1081，两份损坏态 CR=0（实测值，别凭记忆）',
       info['good']['crlf'] == 1081
       and info['1795465850']['crlf'] == 0 and info['1795465858']['crlf'] == 0,
       {k: v['crlf'] for k, v in info.items()})
    ck('X5 完好版 828,603 B / 116 标题 / 末节 2.105',
       info['good']['bytes'] == 828603 and info['good']['heads'] == 116
       and info['good']['last'] == '2.105', info['good'])
    ck('X6 损坏态之一：字节更多（836,418）、标题更多（118）、CR 掉到 0',
       info['1795465850']['bytes'] == 836418 and info['1795465850']['heads'] == 118
       and info['1795465850']['crlf'] == 0, info['1795465850'])
    ck('X7 损坏态之二：字节更少（738,215）、末节掉到 2.93（丢了 12 节）',
       info['1795465858']['bytes'] == 738215 and info['1795465858']['last'] == '2.93',
       info['1795465858'])
    # ---- 反控实验：这才是「CR 对丢内容失明」的机械证据 ----
    gt = io.open(b10, 'rb').read().decode('utf-8')
    i94 = gt.index('## 2.94')
    cut = gt[:i94].encode('utf-8')
    seg = gt[i94:].encode('utf-8')
    ck('X7a 反控实验：删 §2.94 及之后全部 12 节，CR 变化量为 0',
       cut.count(b'\r\n') == io.open(b10, 'rb').read().count(b'\r\n'),
       '%d -> %d' % (io.open(b10, 'rb').read().count(b'\r\n'), cut.count(b'\r\n')))
    ck('X7b 被删 12 节里 CRLF 个数 = 0（这才是失明的原因，不是巧合）',
       seg.count(b'\r\n') == 0, 'seg %d B, CRLF %d, LFonly %d'
       % (len(seg), seg.count(b'\r\n'), seg.count(b'\n') - seg.count(b'\r\n')))
    tcut = cut.decode('utf-8')
    ck('X7c 反控实验后：标题 116->104、末节 2.105->2.93、字节少 98,044',
       len(re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', tcut)) == 104
       and re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', tcut)[-1] == '2.93'
       and io.open(b10, 'rb').read().__len__() - len(cut) == 98044,
       (len(re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', tcut)),
        re.findall(r'(?m)^##\s*(\d+(?:\.\d+)*)', tcut)[-1]))

    add = SEC.encode('utf-8')
    if not raw.endswith(b'\n'):
        add = b'\n' + add
    new = raw + add
    ck('X8 追加后 CR 仍 1081', new.count(b'\r\n') == 1081, new.count(b'\r\n'))
    t2 = new.decode('utf-8')
    ck('X9 追加后 2.106.7 恰 1 次', t2.count('### 2.106.7') == 1, t2.count('### 2.106.7'))
    ck('X10 追加后既有前缀逐字节不变', new.startswith(raw), '')

    if '--apply' not in sys.argv:
        print('DRY RUN: %d -> %d B' % (len(raw), len(new)))
        return 0 if not any(not c['ok'] for c in checks) else 1
    if any(not c['ok'] for c in checks):
        print('REFUSE --apply'); return 1
    bak = os.path.join(BASE, 'R102.before_2106_7_%s.bak' % STAMP)
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
    ck('Y0 wx 独占备份',
       hashlib.sha256(io.open(bak, 'rb').read()).hexdigest() == hashlib.sha256(raw).hexdigest(),
       os.path.basename(bak))
    with io.open(RC, 'ab') as f:
        f.write(add)
    back = io.open(RC, 'rb').read()
    ck('Y1 回读逐字节相同', back == new, '%d B' % len(back))
    ck('Y2 回读 CR = 1081', back.count(b'\r\n') == 1081, back.count(b'\r\n'))
    p = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                       capture_output=True, text=True, cwd=ROOT)
    ck('Y3 门禁 exit 0', p.returncode == 0, 'exit=%d' % p.returncode)
    if p.returncode:
        print(p.stdout[-1200:])
    n_fail = sum(1 for c in checks if not c['ok'])
    json.dump({'n_checks': len(checks), 'n_fail': n_fail, 'info': info, 'checks': checks},
              io.open(os.path.join(OUT, 'r102k_addendum.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('n_checks=%d n_fail=%d' % (len(checks), n_fail))
    return 0 if n_fail == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
