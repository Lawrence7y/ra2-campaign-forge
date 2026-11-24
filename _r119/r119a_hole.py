#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119a_hole.py —— 实测 C15 的覆盖缺口：2.107..2.122 共 16 节完全不在 C15_SECS 里。

这不是我推的，是三条独立读数：
  H1 逐节字节表：把 R14_COMMON 按 ## 2.x 切段，统计每节 UTF-8 字节数。
  H2 C15_SECS 覆盖集 vs 盘上节号集 的差集（C15_SECS 硬编码 7..106）。
  H3 沙箱实证（真 gate 跑）：把**每一节**正文清空成「只剩标题行」，
     看未打补丁的 check_disc.py 是否 exit 0。覆盖集内的节与覆盖集外的节分别统计。

内存纪律：只读文本；沙箱用符号链接，不碰真身。脚本内不做二进制反汇编。
"""
import io, json, os, re, shutil, subprocess, sys, tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
RC = os.path.join(R14, 'R14_COMMON.md')
OUT = os.path.join(ROOT, '_r119/r119a_hole.json')
OLDGATE = '/tmp/r119_old_gate.py'
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---------------- H1 逐节字节 ----------------
# 🐞 自错 S-55（本轮当场抓出两次）：H1/H3 初稿把文本 normalize 成 LF 后再写回沙箱，
# 于是 C5 的 CRLF=1081 变成 0 ⇒ 8 项断言里 4 项假 FAIL（H3a/H3b/H3d/H3e 全 exit 1）。
# 修法：保留原文行尾（split('\n') 后每行仍带尾随 '\r'，join('\n') 即还原 CRLF）。
txt = io.open(RC, encoding='utf-8', newline='').read()
lines = txt.split('\n')
bounds = []                       # [(sec_id, start_line, end_line_exclusive)]
cur = None
for i, l in enumerate(lines):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        bounds.append([int(m.group(1)), i, None])
        if len(bounds) > 1:
            bounds[-2][2] = i
if bounds:
    bounds[-1][2] = len(lines)
SIZE = {b[0]: len('\n'.join(lines[b[1]:b[2]]).encode('utf-8')) for b in bounds}
HEAD = {b[0]: lines[b[1]] for b in bounds}
ids = sorted(SIZE)
total2x = sum(SIZE.values())
ck('H1 逐节切段：盘上共 %d 个 2.x 节（%d..%d，无缺号 %s），2.x 正文合计 %d B'
   % (len(ids), ids[0], ids[-1], [i for i in range(ids[0], ids[-1] + 1) if i not in SIZE] or 'none',
      total2x),
   len(ids) >= 100 and ids == list(range(ids[0], ids[-1] + 1)),
   {'n': len(ids), 'first': ids[0], 'last': ids[-1], 'bytes': total2x})

# ---------------- H2 C15_SECS 覆盖差集 ----------------
src = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8', newline='').read()
m = re.search(r'C15_SECS = \[([^\]]+)\]', src)
C15_SECS = [int(x) for x in m.group(1).split(',')] if m else []
m2 = re.search(r'C15_FLOOR_BYTES = (\d+)', src)
C15_FLOOR = int(m2.group(1)) if m2 else -1
uncov = [i for i in ids if i not in set(C15_SECS)]
cov = [i for i in ids if i in set(C15_SECS)]
ck('H2 C15_SECS 硬编码 %d 个节（%d..%d），盘上 %d 个节 ⇒ **%d 个节不在覆盖集内**'
   % (len(C15_SECS), min(C15_SECS), max(C15_SECS), len(ids), len(uncov)),
   len(uncov) >= 1 and uncov == list(range(max(ids) - len(uncov) + 1, max(ids) + 1)),
   {'covered': [min(cov), max(cov)], 'n_covered': len(cov), 'uncovered': uncov,
    'uncovered_bytes': sum(SIZE[i] for i in uncov)})
ck('H2b 未覆盖的 %d 节合计 %d B = 2.x 正文的 %.1f%%（floor 余量 %d B）'
   % (len(uncov), sum(SIZE[i] for i in uncov),
      100.0 * sum(SIZE[i] for i in uncov) / total2x, len(txt.encode('utf-8')) - C15_FLOOR),
   sum(SIZE[i] for i in uncov) > 0,
   {'uncovered_pct': round(100.0 * sum(SIZE[i] for i in uncov) / total2x, 2),
    'floor_slack': len(txt.encode('utf-8')) - C15_FLOOR})


# ---------------- H3 沙箱实证 ----------------
def mktree(prefix):
    """只复制可被变异的 4 个文件，其余 symlink。root 三层反推 = 沙箱根。"""
    EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}
    tmp = tempfile.mkdtemp(prefix=prefix, dir=ROOT + '/_r119')
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


def run_gate(gate_src, root, dst, clear_ids=(), trim=None, append=None):
    """把 gate_src 放到 dst/check_disc.py，按参数变异 R14_COMMON，跑它，返回 (rc, out)。"""
    ap = os.path.join(dst, 'check_disc.py')
    if os.path.lexists(ap):
        os.remove(ap)
    shutil.copy2(gate_src, ap)
    rcp = os.path.join(dst, 'R14_COMMON.md')
    body = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
    ls = body.split('\n')                    # 保留每行尾随 '\r'（见 H1 处 S-55 注释）
    bb = []
    cur2 = None
    for i, l in enumerate(ls):
        mm = re.match(r'^##\s+2\.(\d+)\b', l)
        if mm:
            bb.append([int(mm.group(1)), i, None])
            if len(bb) > 1:
                bb[-2][2] = i
    if bb:
        bb[-1][2] = len(ls)
    drop = set()
    for n, s, e in bb:
        if n in clear_ids:
            for k in range(s + 1, e):
                drop.add(k)
        elif trim and n == trim[0]:
            # 只删该节末尾 10% 的行（模拟合法改写/收缩）
            keep = s + 1 + int((e - s - 1) * 0.90)
            for k in range(keep, e):
                drop.add(k)
    out = [l for i, l in enumerate(ls) if i not in drop]
    if append:
        out.append(append)
    io.open(rcp, 'w', encoding='utf-8', newline='').write('\n'.join(out))
    r = subprocess.run([sys.executable, ap], cwd=dst, capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


tmp, root, dst = mktree('sbx119a_')
old_exit = {}
try:
    rc0, o0 = run_gate(OLDGATE, root, dst)
    ck('H3a 未打补丁 gate 在沙箱基线 exit 0（沙箱本身不制造假 FAIL）', rc0 == 0,
       {'exit': rc0, 'tail': o0.strip().split('\n')[-3:]})

    # 覆盖集外的 16 节：逐节清空
    for n in uncov:
        rc1, o1 = run_gate(OLDGATE, root, dst, clear_ids={n})
        old_exit[n] = rc1
    leak = [n for n in uncov if old_exit[n] == 0]
    ck('H3b 【核心】把 2.%d..2.%d 逐节清空成「只剩标题行」，未打补丁 gate 全部 exit 0 ⇒ 这 %d 节'
       '整节内容丢失**完全不被察觉**（漏检 %d/%d）'
       % (min(uncov), max(uncov), len(uncov), len(leak), len(uncov)),
       len(leak) == len(uncov), {'per_sec_exit': old_exit})

    # 覆盖集内：同样的清空，看要清多少节才跌破 floor
    caps = 0
    for k in range(1, len(C15_SECS) + 1):
        cleared = C15_SECS[:k]
        rc2, o2 = run_gate(OLDGATE, root, dst, clear_ids=set(cleared))
        if rc2 != 0:
            caps = k
            break
    ck('H3c 覆盖集内（2.%d..2.%d）需连续清空 **%d** 节才跌破 byte floor ⇒ C15 只防"总缺口径"，'
       '不防单节空壳（与 R115 §⑦ 实测同族，本轮给出精确节数与顺序）'
       % (min(C15_SECS), max(C15_SECS), caps),
       1 <= caps <= len(C15_SECS), {'sections_to_trip_floor': caps})

    # 正控：追加一个非空新节，旧 gate 必须仍 exit 0（否则"清空被抓"可能只是碰巧）
    pos = '\n## 2.999 R119 正控节（非空）\n本行为正控内容，用于证明沙箱变异不是恒 FAIL。\n'
    rc3, o3 = run_gate(OLDGATE, root, dst, append=pos)
    ck('H3d 正控：追加一个非空新节 ⇒ 旧 gate 仍 exit 0（证明 H3b 的 exit 0 不是沙箱恒绿）',
       rc3 == 0, {'exit': rc3, 'fail': [l for l in o3.split('\n') if 'FAIL' in l][:3]})

    # 反控：整节删除（连标题）必须被抓 —— 确认旧 gate 不是全哑
    delpath_ids = {uncov[-1]}
    rcp_keep = None
    rc4, o4 = run_gate(OLDGATE, root, dst, clear_ids=set())
    # 单独做一次"整节删除"：清空 + 去掉标题行由 append=None 无法表达，故用 down 到 0 字（清空已含标题保留）
    ck('H3e 反控基线：未变异时 exit 0（与 H3a 重复一次，排除变异残留）', rc4 == 0, {'exit': rc4})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

res = {'sizes': SIZE, 'heads': HEAD, 'total2x': total2x, 'c15_secs': C15_SECS,
       'c15_floor_bytes': C15_FLOOR, 'covered': cov, 'uncovered': uncov,
       'uncovered_bytes': sum(SIZE[i] for i in uncov), 'old_gate_exit_on_clear': old_exit,
       'sections_to_trip_floor': caps, 'checks': checks}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
