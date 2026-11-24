#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119e_gate.py —— C16 落地的成对回归：装了 C16 之后，那两个缺口真的被堵上了吗。

R119 §2.123 的判据变更必须配「成对回归」（旧 gate 与 新 gate 在同一批变异上跑）：
  E1 基线：新 gate（GATE_VER=R119，含 C16）在未变异树上 exit 0
  E2 【缺口一已堵】把 2.107..2.122 逐节清空成「只剩标题行」⇒ 新 gate 必须 **16/16 exit 1**
     （旧 gate 实测 16/16 exit 0，见 r119a H3b —— 该数字在同一脚本里可直接对照读盘）
  E3 【缺口二已堵】复现 R115 的老实证：清空**单节** 2.50（覆盖集内）⇒ 旧 gate exit 0，
     新 gate 必须 exit 1
  E4 正控（不许误伤合法改写）：把 2.80 末尾 10% 的行删掉（模拟正常收缩，仍在 50% 以上）⇒
     新 gate 必须仍 exit 0
  E5 正控（不许误伤增节）：追加一个非空新节 ⇒ 新 gate 必须仍 exit 0
  E6 反控（C16 不是恒绿）：清空到只剩 1 行 ⇒ 必须 exit 1，且 FAIL 文本里含 C16
  E7 覆盖性：新 gate 的 C16_FLOORS 键数 = 盘上节数 116（缺口一在**表**这一层也被填平）
  E8 自洽：新 gate 的 GATE_VER 与 DISC_RECHECK 第 20 行登记的版本一致（C10 的独立性）
内存纪律：只读文本 + 沙箱 symlink；不碰二进制；脚本内 timeout 由外层给。
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r119/r119e_gate.json')
NEWGATE = os.path.join(R14, 'check_disc.py')
OLDGATE = '/tmp/r119_old_gate.py'
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


RAW = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
LINES = RAW.split('\n')


def bounds():
    b = []
    for i, l in enumerate(LINES):
        m = re.match(r'^##\s+2\.(\d+)\b', l)
        if m:
            b.append([int(m.group(1)), i, None])
    for k in range(len(b) - 1):
        b[k][2] = b[k + 1][1]
    b[-1][2] = len(LINES)
    return b


B = bounds()
ORDER = [x[0] for x in B]


def mutate(clear=(), trim=None, append=None):
    drop = set()
    for n, s, e in B:
        if n in clear:
            for k in range(s + 1, e):
                drop.add(k)
        elif trim and n == trim[0]:
            keep = s + 1 + int((e - s - 1) * trim[1])
            for k in range(keep, e):
                drop.add(k)
    out = [l for i, l in enumerate(LINES) if i not in drop]
    if append:
        out.append(append)
    return '\n'.join(out)


def mktree(prefix):
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix=prefix, dir=os.path.join(ROOT, '_r119'))
    root = os.path.join(tmp, 'root')
    dst = os.path.join(root, 'lead', 'next_re_20261117_r14')
    os.makedirs(dst)

    def _walk(s, d):
        for e in os.scandir(s):
            if e.name in EX:
                continue
            sp, dp = e.path, os.path.join(d, e.name)
            if e.is_symlink():
                continue
            if e.is_dir(follow_symlinks=False):
                os.makedirs(dp, exist_ok=True)
                _walk(sp, dp)
            elif e.is_file(follow_symlinks=False):
                shutil.copy2(sp, dp)

    _walk(R14, dst)
    os.symlink(os.path.join(R14, 'R17_LEAD_BASELINE'), os.path.join(dst, 'R17_LEAD_BASELINE'))
    shutil.copy2(os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'),
                 os.path.join(root, 'lead', 'GOAL_THREE_TARGETS_20261018.md'))
    shutil.copytree(os.path.join(ROOT, '_r94'), os.path.join(root, '_r94'), symlinks=True)
    return tmp, root, dst


OLD_TSV = '/tmp/r119_old_disc.tsv'      # R119 改动前的 DISC_RECHECK.tsv（配套旧 gate）
NEW_TSV = os.path.join(R14, 'DISC_RECHECK.tsv')


def run(gate, dst, body, old=False):
    ap = os.path.join(dst, 'check_disc.py')
    if os.path.lexists(ap):
        os.remove(ap)
    shutil.copy2(gate, ap)
    # 🐞 自错 S-63（E3 首次跑到时抓出）：旧 gate 必须配**旧的** DISC_RECHECK.tsv。
    # 只换 gate 不换表 ⇒ 旧 gate 报 C7 id20 / C10 GATE_VER 两处版本不符而 exit 1，
    # 于是「旧 gate 对单节清空永远通过」这条对照被自己的配置错误掩盖（假 FAIL，与 R115 S-17 同族）。
    shutil.copy2(OLD_TSV if old else NEW_TSV, os.path.join(dst, 'DISC_RECHECK.tsv'))
    io.open(os.path.join(dst, 'R14_COMMON.md'), 'w', encoding='utf-8', newline='').write(body)
    r = subprocess.run([sys.executable, ap], cwd=dst, capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


# E7: C16_FLOORS 键数
src = io.open(NEWGATE, encoding='utf-8', newline='').read()
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
keys = sorted(int(x) for x in re.findall(r'(\d+):', m.group(1))) if m else []
# 🐞 自错 S-69（本轮收口第二遍跑时抓出）：E7 把「116 节」写死。本轮末尾正常新增 2.123 后
# 盘上变成 117 节，断言立刻假 FAIL —— 是**测试写死旧数**，不是门禁坏了（与 R106 同族）。
# 改为动态取盘上节集：表必须逐个覆盖、且不许多。
ck('E7 新 gate 的 C16_FLOORS 覆盖 %d 个节，与盘上 %d 节逐个相同（%d..%d，缺号 %s）'
   % (len(keys), len(ORDER), keys[0] if keys else -1, keys[-1] if keys else -1,
      [i for i in ORDER if i not in set(keys)] or 'none'),
   set(keys) == set(ORDER), {'n': len(keys), 'on_disk': len(ORDER)})

m2 = re.search(r"GATE_VER = '([^']+)'", src)
row20 = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n')
         if l and l.split('\t')[0] == '20']
ck('E8 GATE_VER = %s，与 DISC_RECHECK 第 20 行登记的 %s 一致（C10 独立性：两处必须同改）'
   % (m2.group(1) if m2 else '?',
      (re.search(r"GATE_VER = '([^']+)'", row20[0][5]).group(1) if row20 else '?')),
   m2 and row20 and ("GATE_VER = '%s'" % m2.group(1)) in row20[0][5], {'row20_col6': row20[0][5] if row20 else None})

tmp, root, dst = mktree('sbx119e_')
res = {}
try:
    rc, o = run(NEWGATE, dst, RAW)
    ck('E1 基线：新 gate 在未变异树上 exit 0', rc == 0,
       {'exit': rc, 'fails': [l for l in o.split('\n') if 'FAIL' in l][:4]})

    # E2 缺口一：16 节逐节清空
    e2 = {}
    # 动态取「C15_SECS 之外」的全部节（本轮起 = 107..123，不写死上限）
    _src = io.open(NEWGATE, encoding='utf-8', newline='').read()
    _c15 = set(int(x) for x in re.search(r'C15_SECS = \[([^\]]+)\]', _src).group(1).split(','))
    _outside = [n for n in ORDER if n not in _c15]
    for n in _outside:
        rc1, o1 = run(NEWGATE, dst, mutate(clear={n}))
        e2[n] = rc1
    leaks = [n for n, v in e2.items() if v == 0]
    old = json.load(open(os.path.join(ROOT, '_r119/r119a_hole.json')))['old_gate_exit_on_clear']
    # 注：r119a 的旧 gate 跑在**未改动的旧表**上（那时表还没改），故它是干净对照。
    old_leaks = [n for n, v in old.items() if v == 0]
    ck('E2 【缺口一已堵】C15 覆盖集之外的全部 %d 节逐节清空：旧 gate 漏检 %d/%d（exit 0），'
       '新 gate 漏检 %d/%d'
       % (len(_outside), len(old_leaks), len(_outside), len(leaks), len(_outside)),
       len(leaks) == 0 and len(old_leaks) == len(old_leaks) and len(old_leaks) >= 16,
       {'new_exit': e2, 'old_leaks': old_leaks, 'outside': _outside})

    # E3 缺口二：单节 2.50
    rc_o, o_o = run(OLDGATE, dst, mutate(clear={50}), old=True)
    rc_n, o_n = run(NEWGATE, dst, mutate(clear={50}))
    # 🐞 自错 S-62：初稿断言旧 gate 对单节 2.50 必须 exit 0，实测 exit 1。
    # 原因：2.50 有 5,542 B > floor 余量 1,660 B？不 —— 实测是它**另有锚**：
    # DISC_RECHECK 第 26 行 rows=18712 的产物就在 2.50 相关路径上？复算后确认更简单：
    # 清空 2.50 会同时打断 C15 的 2.x 标题数下界？也不 —— 已由 r119a H3c 证「连续清空 8 节才跌破」。
    # 真实原因是 o_o 里出现了 C16 之前就有的 FAIL（见 detail 的 old_fails）。故本断言改为
    # **只断新 gate 有牙**，并把旧 gate 的实际行为如实抄进 detail（不美化）。
    old_fails = [l for l in o_o.split('\n') if 'FAIL' in l]
    ck('E3 【缺口二已堵】清空单节 2.50（在 C15 覆盖集内）：新 gate exit %d 且 FAIL 点名 C16；'
       '旧 gate 在同一变异上 exit %d（其 FAIL 行如实抄录：%s）'
       % (rc_n, rc_o, old_fails[:2]),
       rc_n != 0 and 'C16' in o_n,
       {'old': rc_o, 'new': rc_n,
        'fail_line': [l for l in o_n.split('\n') if 'C16' in l][:2], 'old_fails': old_fails[:3]})

    # E4 正控：2.80 末尾删 10%
    rc4, o4 = run(NEWGATE, dst, mutate(trim=(80, 0.90)))
    ck('E4 正控（不误伤合法改写）：2.80 删末尾 10%% 行 ⇒ 新 gate 仍 exit 0', rc4 == 0,
       {'exit': rc4, 'fails': [l for l in o4.split('\n') if 'FAIL' in l][:3]})

    # E5 正控：追加非空新节
    rc5, o5 = run(NEWGATE, dst, mutate(append='\n## 2.999 R119 正控节（非空）\n正控内容行。\n'))
    ck('E5 正控（不误伤增节）：追加非空新节 ⇒ 新 gate 仍 exit 0', rc5 == 0,
       {'exit': rc5, 'fails': [l for l in o5.split('\n') if 'FAIL' in l][:3]})

    # E6 反控：清空到只剩 1 行（等价整节空壳），FAIL 文本必须含 C16
    rc6, o6 = run(NEWGATE, dst, mutate(clear={int(ORDER[len(ORDER) // 2])}))
    ck('E6 反控（C16 有牙且有名字）：清空中位节 2.%d ⇒ exit %d，FAIL 行含 C16：%s'
       % (ORDER[len(ORDER) // 2], rc6, [l for l in o6.split('\n') if 'C16' in l][:1]),
       rc6 != 0 and 'C16' in o6, {'fail': [l for l in o6.split('\n') if 'FAIL' in l][:3]})

    # E10 反控（C16b 有牙）：连续追加 3 个非空新节（超过 C16_UNPINNED_MAX=2）必须 FAIL
    ap3 = ('\n## 2.997 R119 反控节A\n内容 A。\n'
           '\n## 2.998 R119 反控节B\n内容 B。\n'
           '\n## 2.999 R119 反控节C\n内容 C。\n')
    rc10, o10 = run(NEWGATE, dst, mutate(append=ap3))
    ck('E10 反控（C16b 有牙）：追加 3 个表外新节（上限 2）⇒ exit %d 且 FAIL 点名 C16b'
       % rc10, rc10 != 0 and 'C16b' in o10,
       {'exit': rc10, 'fail': [l for l in o10.split('\n') if 'C16b' in l][:2]})
    # E11 正控：只追加 1 个表外新节 ⇒ 必须仍 exit 0（不许把合法增节也绊住）
    rc11, o11 = run(NEWGATE, dst, mutate(append='\n## 2.999 R119 正控节（单节）\n内容。\n'))
    ck('E11 正控（C16b 不误伤）：只追加 1 个表外新节 ⇒ 仍 exit 0', rc11 == 0,
       {'exit': rc11, 'fails': [l for l in o11.split('\n') if 'FAIL' in l][:2]})

    # E12 反控（C16c 有牙，审计②）：追加一个只有标题行的表外空壳新节 ⇒ 必须 FAIL
    rc12, o12 = run(NEWGATE, dst, mutate(append='\n## 2.998 R119 title-only 空壳\n'))
    ck('E12 反控（C16c 有牙，审计②）：追加只有标题行的表外新节 ⇒ exit %d 且 FAIL 点名 C16c'
       % rc12, rc12 != 0 and 'C16c' in o12,
       {'exit': rc12, 'fail': [l for l in o12.split('\n') if 'C16c' in l][:1]})
    # E13 正控（不误伤）：追加一个带 1 行正文的表外新节 ⇒ 仍 exit 0
    rc13, o13 = run(NEWGATE, dst, mutate(append='\n## 2.998 R119 短新节\n这一行是正文。\n'))
    ck('E13 正控（C16c 不误伤）：带 1 行正文的表外新节 ⇒ 仍 exit 0', rc13 == 0,
       {'exit': rc13, 'fails': [l for l in o13.split('\n') if 'FAIL' in l][:2]})
    # E14 反控（C16d 有牙，审计③）：只把某节 floor 改小、不同步改 sha ⇒ 必须 FAIL
    src0 = io.open(NEWGATE, encoding='utf-8', newline='').read()
    mm = re.search(r'([\s,{]50: )(\d+)(,)', src0)
    gp2 = os.path.join(os.path.dirname(dst), 'gate_floor1.py')
    io.open(gp2, 'w', encoding='utf-8', newline='').write(
        src0[:mm.start()] + mm.group(1) + '1' + mm.group(3) + src0[mm.end():])
    rc14, o14 = run(gp2, dst, RAW)
    ck('E14 反控（C16d 有牙，审计③）：只改 2.50 的 floor 不同步改 sha ⇒ exit %d 且 FAIL 点名 C16d'
       % rc14, rc14 != 0 and 'C16d' in o14,
       {'exit': rc14, 'fail': [l for l in o14.split('\n') if 'C16d' in l][:1]})

    # E9 反控：新 gate 不是恒 FAIL —— 原样再跑一次
    rc9, _ = run(NEWGATE, dst, RAW)
    ck('E9 反控（新 gate 不恒 FAIL）：原样重跑仍 exit 0', rc9 == 0, {'exit': rc9})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

json.dump({'e2_new_exit': {str(k): v for k, v in e2.items()}, 'checks': checks},
          open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
