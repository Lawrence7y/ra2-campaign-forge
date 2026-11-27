#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159i_pin_c16.py — 把新增的 §2.164 纳入 C16_FLOORS 并重钉 C16_FLOORS_SHA256。

为什么必须做：C16b 允许表外新节最多 2 个，但不钉就等于「每轮新增一节 = 每轮白得一张
永久免检票」（与 claims-none 同构）。本轮新增 1 节，现盘 unpinned=1 虽未超限，
但 R158 的做法是**当轮就钉**（163:5671），本轮照办，把 unpinned 压回 0。

幂等。写入纪律：wx 备份 -> 断言旧 sha256 -> 一次性写 -> 回读 -> 真跑门禁。
"""
import hashlib, io, os, re, subprocess, sys, time

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
G = D + '/check_disc.py'
RC = D + '/R14_COMMON.md'
BD = D + '/R17_LEAD_BASELINE'
NEWSEC = 164

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rd(p): return io.open(p, encoding='utf-8', newline='').read()
def rb(p):
    with open(p, 'rb') as f: return f.read()
def sha(b): return hashlib.sha256(b).hexdigest()

src = rd(G); rc = rd(RC)
sha_g0 = sha(rb(G))

# ---- 量每节正文字节（与门禁同一口径：标题行之后到下一节之前）----
def bodies(text):
    out = {}
    cur = None; buf = []
    for line in text.split('\n'):
        m = re.match(r'^##\s+2\.(\d+)\b', line)
        if m:
            if cur is not None:
                out[cur] = len('\n'.join(buf).strip().encode())
            cur = int(m.group(1)); buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = len('\n'.join(buf).strip().encode())
    return out

B = bodies(rc)
print('== 0 · 旧态 ==')
print('  节数 = %d，末节 = %d' % (len(B), max(B)))
ck('0.1 §%d 存在且正文 > 0 B' % NEWSEC, NEWSEC in B and B[NEWSEC] > 0, B.get(NEWSEC))
print('  §%d 正文字节 = %d' % (NEWSEC, B[NEWSEC]))

# ---- 读现表 ----
m = re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
ck('0.2 能抽到 C16_FLOORS 表体', m is not None, None)
body = m.group(1)
pairs = dict((int(k), int(v)) for k, v in re.findall(r'(\d+):\s*(\d+),', body))
print('  表内 %d 项，末项 %d:%d' % (len(pairs), max(pairs), pairs[max(pairs)]))
old_sha = re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", src).group(1)
norm_old = '\n'.join('%d:%d' % (k, pairs[k]) for k in sorted(pairs))
print('  旧表规范化 sha = %s（常量 %s）' % (sha(norm_old.encode())[:16], old_sha[:16]))
ck('0.3 旧表与旧常量一致（反控：写前表没被别人改）',
   sha(norm_old.encode()) == old_sha, (sha(norm_old.encode())[:16], old_sha[:16]))
# 两态判据：未钉 / 已钉都必须能通过（否则幂等复跑必假 FAIL —— S-424/S-445 同族）
ck('0.4 §%d 的钉状态（未钉=本轮要加；已钉=幂等态，两种都合法）' % NEWSEC, True,
   ('already-pinned' if NEWSEC in pairs else 'needs-pin'))

print('\n== 1 · 追加钉 ==')
if NEWSEC in pairs:
    print('  [idempotent] §%d 已在表内' % NEWSEC)
    new_src = src
else:
    pairs2 = dict(pairs)
    pairs2[NEWSEC] = B[NEWSEC]
    # 逐字重建表体：保持原有 "    163: 5671," 缩进与顺序
    lines = []
    for k in sorted(pairs2):
        lines.append('    %d: %d,' % (k, pairs2[k]))
    new_body = '\n' + '\n'.join(lines)
    new_src = src.replace(m.group(1), new_body, 1)
    norm_new = '\n'.join('%d:%d' % (k, pairs2[k]) for k in sorted(pairs2))
    new_sha = sha(norm_new.encode())
    new_src = new_src.replace(old_sha, new_sha, 1)
    print('  [repin] C16_FLOORS +{%d: %d}；sha %s -> %s'
          % (NEWSEC, B[NEWSEC], old_sha[:16], new_sha[:16]))
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = os.path.join(BD, 'check_disc.py.before_r159_c16pin_%s.bak' % stamp)
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(rb(G))
    ck('1.1 备份已建（wx 独占）', os.path.exists(bak), os.path.basename(bak))
    ck('1.2 备份 sha == 写前实读', sha(rb(bak)) == sha_g0, None)
    with io.open(G, 'w', encoding='utf-8', newline='') as f: f.write(new_src)

back = rd(G)
print('\n== 2 · 回读 ==')
m2 = re.search(r'C16_FLOORS = \{(.*?)\n\}', back, re.S)
pairs3 = dict((int(k), int(v)) for k, v in re.findall(r'(\d+):\s*(\d+),', m2.group(1)))
ck('2.1 §%d 已在表内且下限 == 实测正文字节' % NEWSEC,
   pairs3.get(NEWSEC) == B[NEWSEC], (pairs3.get(NEWSEC), B[NEWSEC]))
ck('2.2 其余 %d 项逐项未变（反控：只加一项）' % len(pairs),
   all(pairs3.get(k) == v for k, v in pairs.items()), len(pairs))
ck('2.3 项数 == %d' % (len(pairs) + (0 if NEWSEC in pairs else 1)),
   len(pairs3) == len(pairs) + (0 if NEWSEC in pairs else 1), len(pairs3))
norm3 = '\n'.join('%d:%d' % (k, pairs3[k]) for k in sorted(pairs3))
ck('2.4 新常量 == 新表规范化 sha',
   re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'", back).group(1) == sha(norm3.encode()), None)
ck('2.5 无 CR（LF-only）', back.count('\r') == 0, back.count('\r'))

print('\n== 3 · 真跑门禁 ==')
p = subprocess.run([sys.executable, G], capture_output=True, text=True, timeout=180, cwd=D)
out = p.stdout + p.stderr
hard = [l for l in out.split('\n') if re.match(r'^\s*(\[FAIL\]|FAIL)\b', l)]
ck('3.1 exit 0', p.returncode == 0, p.returncode)
ck('3.2 无 FAIL 行', hard == [], hard[:3])
c16 = [l.strip() for l in out.split('\n') if 'C16 per-section' in l]
print('  ', c16[0] if c16 else None)
ck('3.3 unpinned == 0（本轮新增节已被钉住）',
   c16 and 'unpinned 0' in c16[0], c16[0] if c16 else None)
ck('3.4 hollow/deficient == 0、missing == 0',
   c16 and 'hollow/deficient 0' in c16[0] and 'missing 0' in c16[0], None)
ck('3.5 C16d 表钉 ok', 'C16d floor-table pin' in out and 'OK' in out, None)
ck('3.6 C10 仍 ok(R159)', 'ok(R159)' in out, None)

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
