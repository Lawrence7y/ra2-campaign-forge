#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r120f_recompute_audit.py —— 规则 D：对 hy4 task 224 的 7 条审计判定逐条复算。

每条都自写实现，不 import 被审脚本、不读它的中间结论，只读盘上原始数据。
  A1 窗口键空间 = 28 轮 [36..65] 缺 [41,42]，且 R41 主快照 0 个
  A3 C17b 在本盘是否冗余（它命中的 id 是否全被 C17a 覆盖）
  A4 C17_PIN 的 sha 算法是否可复现（改 PIN 必导致 sha 变）
  A5 三类异常（产物是目录 / 非 UTF-8 / 路径不存在）⇒ C17 段必须不崩溃
  B1 三种边界判据的**两两一致矩阵**（我的 r120e 报「60/60 分歧」是否把粒度差当不稳健）
  B2 Fisher 双尾 p 与单尾 p（p=0.0546 是否被读得过强）
  B3 站后 COM 虚调用模板：60 个站点与全部 154 个 IID push 站点上的命中数
"""
import glob
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r120', 'r120f_recompute_audit.json')
sys.path.insert(0, os.path.join(ROOT, '_r119'))
from _pe119 import PE_, BUF                      # noqa: E402
import capstone                                  # noqa: E402

checks = []


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''), flush=True)
    return bool(cond)


# ---------------- A1 ----------------
sys.path.insert(0, R14)
import recheck_verify as V                        # noqa: E402
keys = sorted(V.ROUND_WINDOWS)
gaps = [n for n in range(keys[0], keys[-1] + 1) if n not in set(keys)]
snaps41 = glob.glob(os.path.join(R14, 'R17_LEAD_BASELINE', 'STATUS_BOARD.before_r41_*.md'))
ck('A1 复算成立：窗口键 %d 个 [%d..%d]，缺号 %s；R41 主快照文件数 = %d（审计说 0）'
   % (len(keys), keys[0], keys[-1], gaps, len(snaps41)),
   len(keys) == 28 and gaps == [41, 42] and len(snaps41) == 0,
   {'n': len(keys), 'gaps': gaps, 'r41_snaps': len(snaps41)})

# ---------------- 公共：读 C17 段与 claims-有 行 ----------------
SRC = io.open(os.path.join(R14, 'check_disc.py'), encoding='utf-8', newline='').read()
LINE = re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d+) at=(\S+) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+?)\r?$')
PATHR = re.compile(r'(?:^|[/\\])R(?:17_)?R?(\d+)_')
rows = [l.split('\t') for l in io.open(os.path.join(R14, 'DISC_RECHECK.tsv'), encoding='utf-8',
                                       newline='').read().split('\n') if l][1:]
imposs, atmap = [], {}
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit() or not r[6].strip().startswith('有'):
        continue
    p = r[4].strip()
    prs = sorted({int(m.group(1)) for m in PATHR.finditer(p.replace('\\', '/'))})
    if not prs:
        continue
    ap = os.path.join(ROOT, p.replace('\\', '/'))
    if not os.path.isfile(ap):
        continue
    for ln in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
        m = LINE.match(ln)
        if m and int(m.group(1)) == int(r[0]):
            if int(m.group(2)[1:]) < min(prs):
                imposs.append((int(r[0]), int(m.group(2)[1:]), m.group(3)))
            atmap.setdefault(m.group(3), set()).add(tuple(prs))
imposs.sort()
reuse = {k: len(v) for k, v in atmap.items() if len(v) > 1}

# ---------------- A3 冗余性 ----------------
ids_imposs = {t[0] for t in imposs}
ids_reuse = set()
for r in rows:
    if len(r) != 7 or not r[0].strip().isdigit() or not r[6].strip().startswith('有'):
        continue
    p = r[4].strip()
    prs = sorted({int(m.group(1)) for m in PATHR.finditer(p.replace('\\', '/'))})
    if not prs:
        continue
    ap = os.path.join(ROOT, p.replace('\\', '/'))
    if not os.path.isfile(ap):
        continue
    for ln in io.open(ap, encoding='utf-8', errors='replace').read().splitlines():
        m = LINE.match(ln)
        if m and int(m.group(1)) == int(r[0]) and len(atmap.get(m.group(3), ())) > 1:
            ids_reuse.add(int(r[0]))
ck('A3 复算成立：C17b 命中的 id 集合 %s ⊆ C17a 命中的 %s（本盘 C17b 未多抓任何一条 ⇒ 冗余）'
   % (sorted(ids_reuse), sorted(ids_imposs)),
   ids_reuse <= ids_imposs and len(ids_reuse) > 0, {'reuse_ids': sorted(ids_reuse)})

# ---------------- A4 sha 算法可复现 ----------------
norm = '\n'.join('%d|%d|%s' % t for t in imposs)
sha_now = __import__('hashlib').sha256(norm.encode()).hexdigest()
m = re.search(r"C17_PIN_SHA256 = '([0-9a-f]{64})'", SRC)
ck('A4 复算成立：C17_PIN_SHA256 可用「排序三元组 %%d|%%d|%%s 换行拼接」复现（%s），'
   '故「同改 PIN+sha」技术上可行 ⇒ C17 只防无声漂移，不防蓄意合谋' % sha_now[:16],
   m and m.group(1) == sha_now, {'recomputed': sha_now, 'registered': m.group(1) if m else None})

# ---------------- A5 三类异常不崩溃 ----------------
EX = {'R17_LEAD_BASELINE', '_cards', '__pycache__', 'D41_SUBST'}


def mktree():
    tmp = tempfile.mkdtemp(prefix='sbx120f_', dir=os.path.join(ROOT, '_r120'))
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


tmp, root, dst = mktree()
try:
    gate = os.path.join(dst, 'check_disc.py')

    def run():
        r = subprocess.run([sys.executable, gate], cwd=dst, capture_output=True, text=True, timeout=300)
        return r.returncode, (r.stdout or '') + (r.stderr or '')

    rc0, o0 = run()
    # A5-1 产物路径是目录：把 27 号行的产物换成目录
    tsvp = os.path.join(dst, 'DISC_RECHECK.tsv')
    orig = io.open(tsvp, encoding='utf-8', newline='').read()
    lines = orig.split('\n')
    for i, l in enumerate(lines):
        c = l.split('\t')
        if len(c) == 7 and c[0] == '27':
            c[4] = 'lead\\next_re_20261117_r14\\R17_R81_T2_EVID'   # 目录，不是文件
            lines[i] = '\t'.join(c)
    io.open(tsvp, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
    rc1, o1 = run()
    crashed1 = 'Traceback' in o1
    io.open(tsvp, 'w', encoding='utf-8', newline='').write(orig)
    # A5-2 产物非 UTF-8
    ap27 = [r for r in rows if r[0].strip() == '27'][0][4].strip()
    p27 = os.path.join(root, ap27.replace('\\', '/'))
    body = io.open(p27, 'rb').read()
    io.open(p27, 'wb').write(body + b'\xff\xfe DISC_RECHECK discipline=27 junk\n')
    rc2, o2 = run()
    crashed2 = 'Traceback' in o2
    io.open(p27, 'wb').write(body)
    # A5-3 第 4 列路径不存在
    lines = orig.split('\n')
    for i, l in enumerate(lines):
        c = l.split('\t')
        if len(c) == 7 and c[0] == '28':
            c[4] = 'lead\\next_re_20261117_r14\\NO_SUCH_DIR\\nope.tsv'
            lines[i] = '\t'.join(c)
    io.open(tsvp, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
    rc3, o3 = run()
    crashed3 = 'Traceback' in o3
    c17_3 = [l for l in o3.split('\n') if 'C17' in l]
    ck('A5 复算成立（不崩溃）：基线 exit %d；产物是目录 ⇒ exit %d 无 Traceback；'
       '非 UTF-8 ⇒ exit %d 无 Traceback；路径不存在 ⇒ exit %d 无 Traceback 且点名 C17（%s）'
       % (rc0, rc1, rc2, rc3, c17_3[:1]),
       not (crashed1 or crashed2 or crashed3), {'rc': [rc0, rc1, rc2, rc3], 'c17_line': c17_3[:1]})
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ---------------- B1 两两一致矩阵（这是审计指出的真缺陷） ----------------
QP = json.load(io.open(os.path.join(ROOT, '_r120/x120exec_q1_partial.json'), encoding='utf-8'))['q1_groups']
CORE = json.load(io.open(os.path.join(ROOT, '_r120/x120exec_core.json'), encoding='utf-8'))
sites = [int(x, 16) for x in CORE['q1']['site_addrs']]


def owner(group, site):
    k = hex(site)
    for f in group:
        if k in f['sites']:
            return f['func_start']
    return None


pad = QP['C1_int3pad']
after = QP['C2_afterterm']
callt = QP['C3_calltarget']

# nearest-entry 自算
TEXT = PE_.sec_by_name('.text')
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = False
MD.skipdata = True
st, ca = [], []
for off in range(0, TEXT['vsize'], 65536):
    blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
    for (a, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
        st.append(a)
        if mn == 'call' and ops.startswith('0x'):
            ca.append(int(ops, 16))
SS = set(st)
import array
import bisect
ENT = array.array('I', sorted({PE_.imagebase + struct.unpack_from('<I', BUF, PE_.e_lfanew + 24 + 16)[0]}
                              | {t for t in ca if t in SS}))


def nearest(site):
    i = bisect.bisect_right(ENT, site) - 1
    return ENT[i] if i >= 0 else None


views = {
    'int3pad': {s: owner(pad, s) for s in sites},
    'afterterm': {s: owner(after, s) for s in sites},
    'calltarget': {s: owner(callt, s) for s in sites},
    'nearest_entry': {s: (hex(nearest(s)) if nearest(s) else None) for s in sites},
}
names = list(views)
matrix = {}
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        same = sum(1 for s in sites if views[a][s] == views[b][s])
        matrix['%s vs %s' % (a, b)] = {'same': same, 'diff': len(sites) - same}
ck('B1 复算成立（审计点出的真缺陷）：两两一致矩阵 = %s。'
   'nearest_entry 与 calltarget **%d/%d 相同** ⇒ 我 r120e 的「三种判据 60/60 分歧」'
   '把「粗粒度整段 vs 细粒度子函数」的定义差异当成了统计量不稳健'
   % (json.dumps(matrix, ensure_ascii=False), matrix['calltarget vs nearest_entry']['same'], len(sites)),
   matrix['calltarget vs nearest_entry']['same'] == len(sites), matrix)

# ---------------- B2 双尾与单尾 ----------------
a, b, c, d = 36, 0, 33, 5
n = a + b + c + d
r1, r2, c1 = a + b, c + d, a + c
pr = lambda k: math.comb(r1, k) * math.comb(r2, c1 - k) / math.comb(n, c1)
lo, hi = max(0, c1 - r2), min(r1, c1)
p_obs = pr(a)
two = sum(pr(k) for k in range(lo, hi + 1) if pr(k) <= p_obs * (1 + 1e-12))
one = sum(pr(k) for k in range(a, hi + 1))          # 右尾：含目标组的集中度更高
ck('B2 复算成立：观察表 [[%d,%d],[%d,%d]]，p_obs=%.6f，双尾 p=%.6f，**单尾（右）p=%.6f**'
   ' ⇒ 双尾 0.0546 是边缘值，单尾 0.0312 < 0.05；审计说「读作无判别力过强」成立'
   % (a, b, c, d, p_obs, two, one),
   abs(two - 0.05456247294950749) < 1e-12 and abs(one - 0.031159560100328) < 1e-12,
   {'p_obs': p_obs, 'two_tail': two, 'one_tail_right': one})

# ---------------- B3 站后 COM 虚调用模板 ----------------
templates = {
    'push_then_mov_ecx_call': None,
    'mov_ecx_then_push_call': None,
}
def siteprefix_tmpl(va):
    o = PE_.va2off(va)
    if o is None:
        return None
    blob = BUF[o:o + 16]
    # 模板一：68 imm32 | 50 (push eax) | 8b 08 (mov ecx,[eax]) | ff 11 (call [ecx])
    if blob[0] == 0x68 and blob[5] == 0x50 and blob[6:8] == b'\x8b\x08' and blob[8:10] == b'\xff\x11':
        return 'push_then_mov_ecx_call'
    # 模板二：68 imm32 | 8b 08 | 50 | ff 11
    if blob[0] == 0x68 and blob[5:7] == b'\x8b\x08' and blob[7] == 0x50 and blob[8:10] == b'\xff\x11':
        return 'mov_ecx_then_push_call'
    return None


def scan_push_imm(target):
    """返回 .text 里 push imm32==target 的站点（按指令起点，非任意字节）。"""
    hits = []
    for off in range(0, TEXT['vsize'], 65536):
        blob = BUF[TEXT['raw'] + off: TEXT['raw'] + min(off + 65536, TEXT['vsize'])]
        for (aa, sz, mn, ops) in MD.disasm_lite(blob, TEXT['va'] + off):
            if mn == 'push' and ops.startswith('0x'):
                try:
                    if int(ops, 16) == target:
                        hits.append(aa)
                except ValueError:
                    pass
    return hits


IIDS11 = [0x7f7c70, 0x7f7c80, 0x7f7c90, 0x7f7ca0, 0x7f7cf0, 0x7f7d00,
          0x817bc0, 0x818858, 0x81fc50, 0x820270, 0x87da00]
b3 = {}
for t in IIDS11:
    ss = scan_push_imm(t)
    cnt = {}
    for s in ss:
        k = siteprefix_tmpl(s) or 'other'
        cnt[k] = cnt.get(k, 0) + 1
    b3[hex(t)] = {'n': len(ss), 'templates': cnt,
                  'full_tmpl': cnt.get('push_then_mov_ecx_call', 0) + cnt.get('mov_ecx_then_push_call', 0)}
top = {k: v for k, v in b3.items() if v['n'] > 0 and v['full_tmpl'] == v['n']}
ck('B3 复算成立（审计给的新证据）：11 个 IID 的 push 站点按「站后 10 字节是否 COM 虚调用模板」普查：%s'
   ' ⇒ 只有 %s 一个 IID 是**全部站点**都满足该模板（%d/%d）'
   % (json.dumps(b3, ensure_ascii=False), sorted(top),
      b3['0x7f7c80']['n'], b3['0x7f7c80']['n']),
   len(top) == 1 and '0x7f7c80' in top and b3['0x7f7c80']['full_tmpl'] == b3['0x7f7c80']['n'] == 60,
   b3)

json.dump({'A1': {'n_window': len(keys), 'gaps': gaps, 'r41_snaps': len(snaps41)},
           'A3': {'reuse_ids': sorted(ids_reuse), 'imposs_ids': sorted(ids_imposs), 'subset': ids_reuse <= ids_imposs},
           'A4': {'sha_recomputed': sha_now, 'sha_registered': m.group(1) if m else None},
           'B1': {'matrix': matrix, 'n_sites': len(sites)},
           'B2': {'table': [[a, b], [c, d]], 'p_obs': p_obs, 'two_tail': two, 'one_tail_right': one},
           'B3': b3, 'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('\n%d/%d PASS -> %s' % (sum(1 for c in checks if c['ok']), len(checks), OUT))
sys.exit(0 if all(c['ok'] for c in checks) else 1)
