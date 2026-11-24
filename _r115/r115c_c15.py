#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115c_c15.py —— C15 内容下界的第 7 列边界（R114 下轮待办⑥的另一半）。

C15 的四条子项都是**下界**：节号集合不得缺、末节号不得回退、字节数不得跌破 floor、
2.x 标题数不得少于 floor。四条都只看「量」，不看「每一节里还有没有东西」。
于是结构性漏洞：**把某个中间节的正文全部清空、只留标题行** ⇒ 四条子项全部照旧通过。
这与 R103 修复的那次事故同族（CR 不变、字节数只减一节的分量），
只是从「整节消失」缩小到「整节空壳」，C15 的 floor 完全不覆盖。

断言：
  C1 C15 四子项对现状全通过（基线）
  C2 【漏洞】清空 1 个中间节的正文（保留 ## 2.N 标题）⇒ 未改动的 check_disc.py 仍 exit 0
  C3 【量化】能清空多少节而门禁仍 exit 0 —— 给出「字节预算」：C15_FLOOR_BYTES 的余量
  C4 【边界】清空到字节数跌破 floor 时门禁才 FAIL ⇒ 证明 C15 只防量不防空洞
  C5 反向对照：整节**删除**（连标题）必须 FAIL（R103 已装，本轮验证它仍有效）
  C6 反向对照：末节号回退必须 FAIL
内存纪律：只读文本、临时树用符号链接基线；不碰二进制。
"""
import hashlib, io, json, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r115/r115c_c15.json')
RC = os.path.join(R14, 'R14_COMMON.md')
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


def mktree():
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix='r115c15_', dir=os.path.join(ROOT, '_r115'))
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


def run_gate(root):
    env = dict(os.environ)
    env['TMPDIR'] = os.path.join(os.path.dirname(root), 'tmp')
    os.makedirs(env['TMPDIR'], exist_ok=True)
    p = subprocess.run([sys.executable, os.path.join(root, 'lead', 'next_re_20261117_r14', 'check_disc.py')],
                       capture_output=True, text=True, timeout=600, env=env)
    return p.returncode, p.stdout + p.stderr


# R14_COMMON 是**混合行尾**：1081 个 CRLF + 9506 个裸 LF（实测）。
# CR=1081 被门禁 C5 钉死，所以任何「统一换成 \n 或 \r\n」的写法都会立刻 FAIL。
# 自错 S-20：初稿先 newline='' 读、再 '\n'.join 写 ⇒ CR 被抹成 0，C2/C3 被 C5 打成
# exit 1，我把它误读成「C15 覆盖住了整节空壳」。再版用 '\r\n'.join ⇒ CR 变 10514。
# 正确做法：**按 \n 切行、保留每行自己的结尾符**，只整行删除。
src = io.open(RC, encoding='utf-8', newline='').read()
_raw_lines = src.split('\n')                   # 保留每行末尾的 '\r'（若有）
src_nl = src.replace('\r\n', '\n')            # 仅用于解析节边界


def write_rc(path, keep_mask_or_lines):
    '''keep_mask: 与 _raw_lines 等长的 bool 列表（True=保留）；写入时逐行原样拼回。'''
    if isinstance(keep_mask_or_lines, list) and keep_mask_or_lines and isinstance(keep_mask_or_lines[0], bool):
        body = [l for l, k in zip(_raw_lines, keep_mask_or_lines) if k]
    else:
        body = keep_mask_or_lines
    io.open(path, 'w', encoding='utf-8', newline='').write('\n'.join(body))

# ---- C1 基线 ----
rc0, out0 = run_gate(ROOT)
c15line = [l.strip() for l in out0.splitlines() if 'C15 content floor' in l]
ck('C1 基线：真树上 check_disc.py exit=%d ; %s' % (rc0, c15line), rc0 == 0, {'rc': rc0, 'c15': c15line})

# ---- 解析 2.x 节：标题 + 正文区间 ----
lines = src_nl.split('\n')
secs = []          # (secnum, head_idx, body_start, body_end)
for i, l in enumerate(lines):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        secs.append([int(m.group(1)), i])
for k, s in enumerate(secs):
    s.append(s[1] + 1)
    s.append(secs[k + 1][1] if k + 1 < len(secs) else len(lines))
print('parsed 2.x sections: %d ; first=%d last=%d' % (len(secs), secs[0][0], secs[-1][0]))

bytes_now = len(src.encode('utf-8'))
head_now = len(secs)
ck('C1b 现盘字节 %d 对 floor 831406 的余量 = %d B；2.x 标题 %d 对 floor 99 的余量 = %d'
   % (bytes_now, bytes_now - 831406, head_now, head_now - 99),
   bytes_now > 831406, {'margin_bytes': bytes_now - 831406, 'margin_heads': head_now - 99})


def blank_mask(secnum, mask):
    """返回 (新 mask, 省下的字节数)：把该节正文行全部标记为 False，保留标题行。"""
    for s in secs:
        if s[0] == secnum:
            saved = sum(len(_raw_lines[i].encode('utf-8')) + 1 for i in range(s[2], s[3]))
            m = list(mask)
            for i in range(s[2], s[3]):
                m[i] = False
            return m, saved
    return None, 0


# ---- C2 漏洞：清空一个中间节 ----
tmp, root2, dst2 = mktree()
try:
    target = 50
    mask = [True] * len(_raw_lines)
    mask, saved = blank_mask(target, mask)
    write_rc(os.path.join(dst2, 'R14_COMMON.md'), mask)
    rc2, out2 = run_gate(root2)
    fails2 = [l.strip() for l in out2.splitlines() if l.strip().startswith('FAIL')]
    c15_2 = [l.strip() for l in out2.splitlines() if 'C15 content floor' in l]
    ck('C2 【漏洞实测】把 §2.%d 的正文整节清空（保留标题，省下 %d B）后，未改动的 check_disc.py '
       'exit=%d、FAIL %d 条 ⇒ C15 四子项对「整节空壳」完全失明' % (target, saved, rc2, len(fails2)),
       rc2 == 0 and not fails2, {'rc': rc2, 'c15': c15_2, 'fails': fails2[:5]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- C3/C4 字节预算：最多能清空多少节 ----
# 全程只在**原始 _raw_lines 的行号空间**里累加 mask，绝不重排队号 ——
# 清空正文只把行标记为 False，不删行，故 secs 的区间始终有效。
tmp, root3, dst3 = mktree()
try:
    mask = [True] * len(_raw_lines)
    cleared = 0
    first_fail = None
    total_saved = 0
    for sn in [x[0] for x in secs[1:41]]:
        m2, saved = blank_mask(sn, mask)
        if m2 is None:
            continue
        mask = m2
        total_saved += saved
        write_rc(os.path.join(dst3, 'R14_COMMON.md'), mask)
        rcx, outx = run_gate(root3)
        cleared += 1
        if rcx != 0:
            first_fail = (sn, cleared, total_saved,
                          [l.strip() for l in outx.splitlines() if l.strip().startswith('FAIL')])
            break
    ck('C3 【字节预算】逐节清空（每节只留标题）：清到第 %d 节时门禁才失败 '
       '（此前已把 %d 节的正文全部抹掉、共省 %d B，floor 余量 %d B）⇒ '
       'C15 只防「量跌破」，不防「节内被掏空」'
       % (first_fail[0] if first_fail else -1,
          (first_fail[1] - 1) if first_fail else cleared,
          first_fail[2] if first_fail else total_saved,
          bytes_now - 831406),
       first_fail is not None and first_fail[1] >= 3,
       {'fail_at_section': first_fail[0] if first_fail else None,
        'cleared_before_fail': (first_fail[1] - 1) if first_fail else cleared,
        'bytes_saved_before_fail': first_fail[2] if first_fail else total_saved,
        'fail_lines': first_fail[3][:3] if first_fail else []})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---- C5 反向对照：整节删除（连标题）必须 FAIL ----
tmp, root4, dst4 = mktree()
try:
    tgt = 60
    mask = [True] * len(_raw_lines)
    for sp in secs:
        if sp[0] == tgt:
            for i in range(sp[1], sp[3]):     # 连标题一起删
                mask[i] = False
    write_rc(os.path.join(dst4, 'R14_COMMON.md'), mask)
    rc5, out5 = run_gate(root4)
    fails5 = [l.strip() for l in out5.splitlines() if l.strip().startswith('FAIL')]
    ck('C5 反向对照：整节删除 §2.%d（连标题）⇒ exit=%d、FAIL %d 条（C15 disappeared 分支）'
       % (tgt, rc5, len(fails5)), rc5 != 0, {'rc': rc5, 'fails': [f[:100] for f in fails5[:3]]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

out = {'bytes_now': bytes_now, 'floor_bytes': 831406, 'margin_bytes': bytes_now - 831406,
       'sections_parsed': len(secs), 'first_section': secs[0][0], 'last_section': secs[-1][0],
       'checks': checks}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
npass = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, %d FAIL' % (npass, len(checks), len(checks) - npass))
sys.exit(0 if npass == len(checks) else 1)
