#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r119g_audit.py —— §2.12 规则 D：主会话亲自复算审计员 hy4 的 8 条结论（A1..A7 + Q4）。

审计员文件：_r119/x119audit_gate.md（9,428 B）。它给出 7 条判定：1 【成立】、2 【成立】、
3 【成立】、4 【不成立】、5 【成立】、6 【成立】、7 【成立】。本脚本不采信任何一条，
逐条用**独立读数**复算：

  A1 复算审计①：「50% 下界会误伤删长重写」—— 统计 [3072,6144) 区间的节数、
     以及 2.8 / 2.11 的实测字节与下界，再用沙箱实证「2.8 删末尾 60% 行」是否 FAIL。
  A2 复算审计②：表外新节的免检票 —— 读脚本 C16_UNPINNED_MAX，实证「新增 1 个 title-only
     空壳节」是否被 C16 看见（这是审计指出的真缺口：票换成了 2 张但票上没内容约束）。
  A3 复算审计③：「同改表与常量可无声通过，弱于 C14」—— 沙箱实证把某节 floor 改小 + 清空该节。
  A4 复算审计④：「CRLF 不是差值原因」—— 逐字节核对 preamble 与 116 个边界 LF 的分解。
  A5 复算审计⑤：三处 +0x10 值（0x818858/0x820270 → 0x7f9594；0x817bc0 → 0x59524753）。
  A6 复算审计⑥：0x817bc0 的 9 站点 8 个 [0x7e15fc] + 1 个 [ecx]。
  A7 复算审计⑦：9 个站点从 push 起 32 字节内出现 ff 15 的 8 个、出现 ff 11 的 1 个。
内存纪律：只读文本 + 单遍 skipdata 扫描；沙箱用 symlink；不整段 detail。
"""
import collections
import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r119/r119g_audit.json')
RAW = io.open(os.path.join(R14, 'R14_COMMON.md'), encoding='utf-8', newline='').read()
checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


LINES = RAW.split('\n')
B = []
for i, l in enumerate(LINES):
    m = re.match(r'^##\s+2\.(\d+)\b', l)
    if m:
        B.append([int(m.group(1)), i, None])
for k in range(len(B) - 1):
    B[k][2] = B[k + 1][1]
B[-1][2] = len(LINES)
SIZE = {n: len('\n'.join(LINES[s:e]).encode('utf-8')) for n, s, e in B}
LINE0 = {n: s for n, s, e in B}


def content_lines(n):
    s, e = None, None
    for i, j, k in B:
        if i == n:
            s, e = j, k
    return sum(1 for l in LINES[s + 1:e] if l.strip() and not l.lstrip().startswith('#'))


# ---------------- A1 ----------------
grp = sorted(n for n, sz in SIZE.items() if 3072 <= sz < 6144)
ck('A1a 复算审计①的分母：[3072,6144) 区间共 %d 节（审计报 64）' % len(grp),
   len(grp) == 64, {'n': len(grp), 'ids': grp})
ck('A1b 复算 2.8 = %d B（审计报 3749），其 50%% 下界 = %d；2.11 = %d B（审计报 1540），下界 = %d'
   % (SIZE[8], SIZE[8] // 2, SIZE[11], SIZE[11] // 2),
   SIZE[8] == 3749 and SIZE[11] == 1540, {'2.8': SIZE[8], '2.11': SIZE[11]})


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


def mutate(clear=(), keep_frac=None, append=None):
    drop = set()
    for n, s, e in B:
        if n in clear:
            for k in range(s + 1, e):
                drop.add(k)
        elif keep_frac and n == keep_frac[0]:
            keep = s + 1 + int((e - s - 1) * keep_frac[1])
            for k in range(keep, e):
                drop.add(k)
    out = [l for i, l in enumerate(LINES) if i not in drop]
    if append:
        out.append(append)
    return '\n'.join(out)


def run_gate(dst, body, gate=None):
    ap = os.path.join(dst, 'check_disc.py')
    if os.path.lexists(ap):
        os.remove(ap)
    shutil.copy2(gate or os.path.join(R14, 'check_disc.py'), ap)
    io.open(os.path.join(dst, 'R14_COMMON.md'), 'w', encoding='utf-8', newline='').write(body)
    r = subprocess.run([sys.executable, ap], cwd=dst, capture_output=True, text=True, timeout=300)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


tmp, root, dst = mktree('sbx119g_')
try:
    # A1c 复算审计①的核心指控：2.8 删 60% 行（模拟「删 3 KB 重复论证后只重写 1 KB」）
    # 审计①**成立**（我复算：50% 下界下 exit 1，误伤面 64 节）⇒ 修复：下界由 50% 降到 25%，
    # 下限 300 B。修复后必须同时满足两条：40% 保留不 FAIL（不误伤）、10% 保留仍 FAIL（有牙）。
    rc_a, o_a = run_gate(dst, mutate(keep_frac=(8, 0.40)))
    rc_b, o_b = run_gate(dst, mutate(keep_frac=(8, 0.10)))
    ck('A1c 复算审计①并验证修复：2.8 保留 40%% 行 ⇒ exit %d（不误伤）；保留 10%% ⇒ exit %d（有牙）'
       % (rc_a, rc_b), rc_a == 0 and rc_b != 0,
       {'keep40': rc_a, 'keep10': rc_b,
        'fail10': [l for l in o_b.split('\n') if 'C16' in l and 'FAIL' in l][:1]})

    # A2 复算审计②：追加一个 title-only 空壳新节。审计②**成立**（旧 C16 下 exit 0）⇒ 已修 C16c。
    rc2, o2 = run_gate(dst, mutate(append='\n## 2.998 R119 title-only 空壳新节\n'))
    ck('A2 复算审计②并验证修复（C16c）：追加只有标题行的表外新节 ⇒ exit %d 且 FAIL 点名 C16c'
       % rc2, rc2 != 0 and 'C16c' in o2,
       {'exit': rc2, 'fail': [l for l in o2.split('\n') if 'C16c' in l][:1]})

    # A3 复算审计③：同改表与常量
    src = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8', newline='').read()
    m = re.search(r'([\s,{]50: )(\d+)(,)', src)   # 自错 S-67：floor 表是同一行内 '..., 50: 2771, 51:'
    patched = src[:m.start()] + m.group(1) + '1' + m.group(3) + src[m.end():]
    gp = os.path.join(tmp, 'gate_tampered.py')
    io.open(gp, 'w', encoding='utf-8', newline='').write(patched)
    rc3, o3 = run_gate(dst, mutate(clear={50}), gate=gp)
    ck('A3 复算审计③并验证修复（C16d）：把 2.50 的 floor 由 %s 改小为 1 而不同步改 sha 并清空该节 '
       '⇒ exit %d 且 FAIL 点名 C16d' % (m.group(2), rc3),
       rc3 != 0 and 'C16d' in o3,
       {'exit': rc3, 'fail': [l for l in o3.split('\n') if 'C16d' in l][:1]})

    # A4 复算审计④：preamble + 116 边界 LF 分解
    first = B[0][1]
    pre = '\n'.join(LINES[:first])
    tot = len(pre.encode('utf-8')) + sum(SIZE.values())
    ck('A4 复算审计④：preamble = %d B（审计报 230247），preamble+116 节 = %d，文件 %d，差 %d'
       '（审计称 116 B = 1 个节前 LF + 115 个节间 LF）'
       % (len(pre.encode('utf-8')), tot, len(RAW.encode('utf-8')),
          len(RAW.encode('utf-8')) - tot),
       len(pre.encode('utf-8')) == 230247 and len(RAW.encode('utf-8')) - tot == 116,
       {'preamble': len(pre.encode('utf-8')), 'diff': len(RAW.encode('utf-8')) - tot})
    cr_in_sec = sum(1 for n, s, e in B for l in LINES[s:e] if l.endswith('\r'))
    ck('A4b 复算审计④：116 节内部的 CR 个数 = %d（审计报 0）；全文 CR = %d'
       % (cr_in_sec, RAW.count('\r')), cr_in_sec == 0 and RAW.count('\r') == 1081,
       {'cr_in_sections': cr_in_sec, 'cr_total': RAW.count('\r')})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---------------- A5..A7：二进制面 ----------------
raw = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb').read()
SECS = [('.text', 0x401000, 0x3df38d, 0x1000, 0x3e0000), ('.rdata', 0x7e1000, 0x30074, 0x3e1000, 0x31000),
        ('.data', 0x812000, 0x367be4, 0x412000, 0x6c000), ('.rsrc', 0xb7a000, 0x18128, 0x47e000, 0x19000),
        ('.detour', 0xb93000, 0x2718, 0x497000, 0x3000)]


def fo(va):
    for n, b, vs, pr, rs in SECS:
        if b <= va < b + max(rs, vs):
            o = pr + (va - b)
            return o if 0 <= o < len(raw) else None
    return None


def u32(va):
    o = fo(va)
    return struct.unpack_from('<I', raw, o)[0] if o is not None and o + 4 <= len(raw) else None


ck('A5 复算审计⑤：+0x10 值 0x818858→%s、0x820270→%s、0x817bc0→%s（审计报 0x7f9594 / '
   '0x7f9594 / 0x59524753）'
   % (hex(u32(0x818868)), hex(u32(0x820280)), hex(u32(0x817bd0))),
   u32(0x818868) == 0x7f9594 and u32(0x820280) == 0x7f9594 and u32(0x817bd0) == 0x59524753,
   {'three': [hex(u32(0x818868)), hex(u32(0x820280)), hex(u32(0x817bd0))]})

sys.path.insert(0, os.path.join(ROOT, '_r112'))
import r112_lib as L2                                    # noqa: E402
MD = L2.MD
code = raw[0x1000:0x1000 + 0x3e0000]
ins = [(a, mn, ops) for (a, sz, mn, ops) in MD.disasm_lite(code, 0x401000)]
push_sites = [a for a, mn, ops in ins if mn == 'push' and ops == hex(0x817bc0)]
after = []
for a in push_sites:
    j = next(k for k, (x, m, o) in enumerate(ins) if x == a)
    for z in range(j + 1, min(j + 12, len(ins))):
        if ins[z][1] == 'call':
            after.append((hex(a), ins[z][1] + ' ' + ins[z][2], hex(ins[z][0])))
            break
n_iat = sum(1 for _, c, _ in after if c == 'call dword ptr [0x7e15fc]')
n_ecx = sum(1 for _, c, _ in after if c == 'call dword ptr [ecx]')
ck('A6 复算审计⑥：0x817bc0 的 %d 个 push 站点中，第一条 call = [0x7e15fc] 的 %d 个、'
   '= [ecx] 的 %d 个（审计报 9 / 8 / 1）'
   % (len(push_sites), n_iat, n_ecx),
   len(push_sites) == 9 and n_iat == 8 and n_ecx == 1, {'after': after})

# A7：从 push 起 32 字节内的 ff 15 / ff 11
n15 = n11 = 0
for a in push_sites:
    o = fo(a)
    blk = raw[o:o + 32]
    if b'\xff\x15' in blk:
        n15 += 1
    if b'\xff\x11' in blk:
        n11 += 1
ck('A7 复算审计⑦：9 个站点从 push 起 32 字节内出现 ff 15 的 %d 个、出现 ff 11 的 %d 个'
   '（审计报 8 / 1）' % (n15, n11), n15 == 8 and n11 == 1, {'ff15': n15, 'ff11': n11})

# A2b：审计②指出的「票上没内容约束」—— 量化 content-line 判据的可行性
cl = {n: content_lines(n) for n, _, _ in B}
shell = mutate(append='\n## 2.998 R119 title-only 空壳新节\n')
ck('A2b 反证「修法可行」：现有 116 节的非空非标题正文行数最少为 %d（2.%d），'
   '若给表外新节加「>= 1 行正文」约束，title-only 空壳必被抓住而正常短节不受影响'
   % (min(cl.values()), min(cl, key=cl.get)),
   min(cl.values()) >= 1, {'min_id': min(cl, key=cl.get), 'min_lines': min(cl.values())})

json.dump({'A1_group': grp, 'A2_free_ticket': True, 'A3_same_edit_passes': True,
           'A4_preamble': len(pre.encode('utf-8')), 'A5': [hex(u32(0x818868)), hex(u32(0x820280)), hex(u32(0x817bd0))],
           'A6': after, 'A7': {'ff15': n15, 'ff11': n11}, 'content_lines_min': min(cl.values()),
           'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
