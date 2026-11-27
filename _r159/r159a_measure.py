#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r159a_measure.py — R159 一次性取证。

目标：把「每轮改 GATE_VER 必连锁 C12/C12b/C7d 三 FAIL」这件事从**手工串**变成**可机械复算的事实**，
并顺带量清三件挂账：C14_ROW_SHA 的 30 条错位（OE13 登记的真缺陷）、C7 三死分支、F08/F23/F35 的
证据链与监控缺口。

一次运行打印全部证据 + 正反控。本脚本**只读**，不写任何被门禁管辖的文件。
"""
import hashlib
import io
import os
import re
import sys

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
G = D + '/check_disc.py'
DR = D + '/DISC_RECHECK.tsv'
UN = D + '/DISC_UNVERIFIABLE.tsv'
FI = D + '/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv'

fails = []
def ck(name, cond, detail=''):
    ok = bool(cond)
    print(('  PASS ' if ok else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not ok:
        fails.append(name)
    return ok

def rd(p):
    return io.open(p, encoding='utf-8', newline='').read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

# ---------- 0 · 门禁基线 + 四个不变量 ----------
print('== 0 · 门禁与不变量基线 ==')
src = rd(G)
gate_ver = re.search(r"GATE_VER = '([^']+)'", src).group(1)
print('  GATE_VER =', gate_ver)
ck('0.1 脚本无 CR（LF-only）', src.count('\r') == 0, src.count('\r'))

raw = [l for l in rd(DR).replace('\r\n', '\n').split('\n') if l.strip()]
rows = [l.split('\t') for l in raw[1:]]
ck('0.2 live 表 31 数据行、每行 7 列',
   len(rows) == 31 and all(len(r) == 7 for r in rows),
   (len(rows), sorted({len(r) for r in rows})))

unraw = [l for l in rd(UN).replace('\r\n', '\n').split('\n') if l.strip()]
unrows = [l.split('\t') for l in unraw[1:] if l.split('\t')[0].strip().isdigit()]
freeze_ids = sorted(int(r[0]) for r in unrows)
print('  冻结档 ids =', freeze_ids)

# ---------- 1 · 「自指行」是哪些 ----------
print('\n== 1 · 自指行普查（col5 以 check_disc.py 结尾）==')
self_rows = [r for r in rows if r[4].strip().replace('/', '\\').endswith('check_disc.py')]
ck('1.1 自指行恰 1 条', len(self_rows) == 1, [r[0] for r in self_rows])
ck('1.2 自指行 id 为 20', self_rows[0][0] == '20', self_rows[0][0])
sid = self_rows[0][0]
ck('1.3 自指行 col6 里含 GATE_VER 锚', "GATE_VER = '" in self_rows[0][5], self_rows[0][5][:60])
ck('1.4 自指行 col6 的版本 == 门禁实际版本',
   ("GATE_VER = '%s'" % gate_ver) in self_rows[0][5], gate_ver)
ck('1.5 自指行 id 在冻结档里', int(sid) in freeze_ids, (sid, int(sid) in freeze_ids))

# ---------- 2 · C7d / C14 两表口径（与门禁逐字一致）----------
print('\n== 2 · 两张 sha 表的口径与实测对齐 ==')
def c7_blob(r):
    return '%s\t%s\t%s' % (r[0], r[4].strip(), r[5].strip())

def c14_blob(r):
    return '%s\t%s\t%s\t%s' % (r[0], r[1], r[2], r[3])

c7_blob_all = '\n'.join(c7_blob(r) for r in rows if len(r) == 7)
c14_blob_all = '\n'.join(c14_blob(r) for r in rows if len(r) == 7)
c7_text_now = sha(c7_blob_all.encode('utf-8'))
c14_text_now = sha(c14_blob_all.encode('utf-8'))
c7_pin = re.search(r"C7_TEXT_SHA256 = '([0-9a-f]{64})'", src).group(1)
c14_pin = re.search(r"C14_TEXT_SHA256 = '([0-9a-f]{64})'", src).group(1)
ck('2.1 C7_TEXT_SHA256 与实测一致', c7_text_now == c7_pin, (c7_text_now[:16], c7_pin[:16]))
ck('2.2 C14_TEXT_SHA256 与实测一致', c14_text_now == c14_pin, (c14_text_now[:16], c14_pin[:16]))

def grab_dict(name):
    """按行取字典（S-412 教训：不能用 index('\\n}') 跨行取，两字典同行书写会合并）。"""
    return grab_dict_in(src, name)

def grab_dict_in(text, name):
    for line in text.split('\n'):
        if line.startswith(name + ' = {'):
            return dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'", line))
    return None

c7_row = grab_dict('C7_ROW_SHA')
c14_row = grab_dict('C14_ROW_SHA')
ck('2.3 C7_ROW_SHA 有 31 项', c7_row is not None and len(c7_row) == 31,
   len(c7_row) if c7_row else None)
ck('2.4 C14_ROW_SHA 有 31 项', c14_row is not None and len(c14_row) == 31,
   len(c14_row) if c14_row else None)
ck('2.5 两表键集合相同', sorted(c7_row) == sorted(c14_row), None)

# ---------- 3 · C14_ROW_SHA 到底是哪一列的口径（两态：修前 / 修后）----------
# 本脚本是**缺陷的取证记录**，不能只对「修前」成立 —— 那正是 S-424/S-445 的错法
# （把某时刻的状态当不变式，修好之后同一脚本必假 FAIL）。
# 故 §3/§4 一律写成**两态判据**：拿当前钉判一次（应为已修）、拿 R158 备份里的旧钉再判一次
# （应为缺陷原样），两条都成立才算通过。修与没修两种盘面下本脚本都应 exit 0。
print('\n== 3 · C14_ROW_SHA 逐条口径判定（当前 + R158 旧钉两态）==')
from collections import Counter

def classify(pins):
    v = {}
    for r in rows:
        k = r[0]
        h7 = sha(c7_blob(r).encode('utf-8'))
        h14 = sha(c14_blob(r).encode('utf-8'))
        pv = pins.get(k)
        if pv == h14 and pv == h7:
            v[k] = 'ambiguous'
        elif pv == h14:
            v[k] = 'C14'
        elif pv == h7:
            v[k] = 'C7'
        else:
            v[k] = 'neither'
    return v

def grab_dict_in(text, name):
    for line in text.split('\n'):
        if line.startswith(name + ' = {'):
            return dict(re.findall(r"'(\d+)':\s*'([0-9a-f]{64})'", line))
    return None

vc_now = classify(c14_row)
vn = Counter(vc_now.values())
print('  当前态分布 =', dict(vn))
ck('3.1 当前态：31 条全部是真正的 C14 口径哈希（OE13 说其中 30 条是 C7 口径 ⇒ 方向相反）',
   vn['C14'] == 31, vn['C14'])
ck('3.2 当前态：0 条是 C7 口径（OE13 的核心断言不成立）', vn['C7'] == 0, vn['C7'])
ck('3.3 当前态：无 neither ⇒ 本轮已把唯一那条修掉', vn['neither'] == 0,
   [k for k, v in vc_now.items() if v == 'neither'])
ck('3.4 C7_ROW_SHA 31/31 全对（反控：同一脚本同一解析口径）',
   all(c7_row[r[0]] == sha(c7_blob(r).encode('utf-8')) for r in rows), None)

# 3.5 从 R158 备份取出旧钉，重放「缺陷原样」，证明 §3 的结论不是修完才编的
bak = D + '/R17_LEAD_BASELINE/check_disc.py.before_r158_repin_20261127_064742.bak'
ck('3.5 R158 备份在盘（缺陷的原始现场）', os.path.exists(bak), bak)
if os.path.exists(bak):
    bsrc = rd(bak)
    b14 = grab_dict_in(bsrc, 'C14_ROW_SHA')
    b7 = grab_dict_in(bsrc, 'C7_ROW_SHA')
    vb = classify(b14)
    vnb = Counter(vb.values())
    print('  R158 旧钉分布 =', dict(vnb))
    ck('3.6 旧钉态：30 条 C14 正确、1 条 neither（缺陷原样可重放）',
       vnb['C14'] == 30 and vnb['neither'] == 1 and vnb['C7'] == 0, dict(vnb))
    ck('3.7 旧钉态：neither 那条就是 self 行', [k for k, v in vb.items() if v == 'neither'] == [sid], sid)
    # 3.8 旧钉的来源：把 id20 的 col6 逐版本改写，看哪一版等于旧钉
    r20 = [r for r in rows if r[0] == sid][0]
    prov = []
    for v in ['R%d' % n for n in range(140, 161)]:
        cand = list(r20)
        cand[5] = "grep=(?m)^GATE_VER = '%s'" % v
        if sha(c7_blob(cand).encode('utf-8')) == b14[sid]:
            prov.append(v)
    print('    旧钉等于 C7 口径哈希的 GATE_VER =', prov)
    ck('3.8 旧钉恰等于 R157 版第 20 行的 C7 口径哈希（唯一命中）', prov == ['R157'], prov)
    ck('3.9 旧钉不等于同期的 C14 口径哈希（它从一开始就不是 C14 口径）',
       b14[sid] != sha(c14_blob(r20).encode('utf-8')), b14[sid][:16])
    ck('3.10 反控：R158 只改了 C7 的 id20，C14 表未动',
       b7[sid] != c7_row[sid] and all(b14[k] == c14_row[k] for k in b14 if k != sid),
       ('C7[20] %s->%s' % (b7[sid][:12], c7_row[sid][:12])))

# ---------- 4 · 错位的可测后果（两态）----------
print('\n== 4 · 后果模拟（纯计算，不写文件；当前钉 vs 旧钉两态）==')
def c14_diag(rows_mod, pins):
    """逐字复刻 check_disc.py 的 C14 漂移分支：先比整表指纹，不匹配才逐行诊断。"""
    blob = '\n'.join(c14_blob(r) for r in rows_mod if len(r) == 7)
    fired = sha(blob.encode('utf-8')) != c14_pin
    drift = []
    if fired:
        for r in rows_mod:
            if len(r) == 7 and pins.get(r[0]) != sha(c14_blob(r).encode('utf-8')):
                drift.append(r[0])
    return fired, drift

def poke(target):
    mod = [list(r) for r in rows]
    for r in mod:
        if r[0] == target:
            r[1] = r[1] + 'X'
    return mod

def poke_many(ids):
    mod = [list(r) for r in rows]
    for r in mod:
        if r[0] in ids:
            r[1] = r[1] + 'X'
    return mod

old_pins = b14 if os.path.exists(bak) else c14_row
r20 = [r for r in rows if r[0] == sid][0]

# 4.1 反控：一个字不改 ⇒ 分支不进入（两态都成立）
ck('4.1 反控：不改任何字符 ⇒ 整表指纹匹配、分支不进入、诊断一条也不列（两态同）',
   c14_diag(rows, c14_row) == (False, []) and c14_diag(rows, old_pins) == (False, []),
   (c14_diag(rows, c14_row), c14_diag(rows, old_pins)))

# 4.2 旧钉：真漂移 1 行 ⇒ 报「目标 + 假阳性 20」
for target in ('1', '7'):
    f, d = c14_diag(poke(target), old_pins)
    ck('4.2 旧钉：改 id %s ⇒ 报出 %s（目标 + 常驻假阳性 20）' % (target, sorted(d)),
       f and sorted(d) == sorted([target, sid]), sorted(d))
# 4.3 当前钉：同一扰动只报目标本身（这就是修复效果）
for target in ('1', '7'):
    f, d = c14_diag(poke(target), c14_row)
    ck('4.3 当前钉：改 id %s ⇒ 只报 %s（假阳性已消失）' % (target, sorted(d)),
       f and d == [target], sorted(d))

# 4.4 只改 col6 ⇒ 分支不进入（col6 不在 C14 口径内）
mod = [list(r) for r in rows]
for r in mod:
    if r[0] == sid:
        r[5] = "grep=(?m)^GATE_VER = 'R159'"
ck('4.4 只改 col6 ⇒ 分支不进入、无告警（C14 口径只取 col1..col4，反控）',
   c14_diag(mod, c14_row) == (False, []), c14_diag(mod, c14_row))

# 4.5 截断窗口（check_disc.py:620 用 _c14_drift[:12]）：旧钉态下 id20 会被挤出
f11, d11 = c14_diag(poke_many([str(i) for i in range(1, 12)]), old_pins)
f12, d12 = c14_diag(poke_many([str(i) for i in range(1, 13)]), old_pins)
print('    旧钉 改 id1..11 ⇒ 漂移 %d 条，窗口 %s，id20 在内=%s' % (len(d11), d11[:12], sid in d11[:12]))
print('    旧钉 改 id1..12 ⇒ 漂移 %d 条，窗口 %s，id20 在内=%s' % (len(d12), d12[:12], sid in d12[:12]))
ck('4.5 旧钉：漂移 11 行时 id 20 仍在窗口内', f11 and sid in d11[:12], (len(d11), d11[:12]))
ck('4.6 旧钉：漂移 12 行时 id 20 被截断挤出 ⇒ 假阳性被天然掩盖',
   f12 and sid not in d12[:12], (len(d12), d12[:12]))

# 4.7 旧钉态：真改 id20 第 2 列 ⇒ 报出集合与「什么都没改也报 20」相同 ⇒ 掩蔽
mod = [list(r) for r in rows]
for r in mod:
    if r[0] == sid:
        r[1] = r[1] + 'EDIT'
f, d = c14_diag(mod, old_pins)
ck('4.7 旧钉：真改 id 20 第 2 列 ⇒ 报出集合仍是 [20]，无法与假阳性区分（掩蔽）',
   f and d == [sid], d)

# 4.8 当前钉：同一改动能被正常识别
f, d = c14_diag(mod, c14_row)
ck('4.8 当前钉：同一改动报出 [20] 且此前无告警 ⇒ 真漂移不再被掩蔽', f and d == [sid], d)

# 4.9 修法最小性：当前钉与「按 C14 口径重算」逐条相同，说明只动了那一条
c14_rebuilt = {r[0]: sha(c14_blob(r).encode('utf-8')) for r in rows}
ck('4.9 当前钉 == 按 C14 口径对现表重算的全部 31 条（修法即「重钉成正确口径」）',
   c14_row == c14_rebuilt, None)
if os.path.exists(bak):
    ck('4.10 相对 R158 旧钉只动了 1 个值（反控：修法最小）',
       sum(1 for k in b14 if b14[k] != c14_row[k]) == 1,
       [k for k in b14 if b14[k] != c14_row[k]])

# ---------- 5 · C7 三死分支（exists / bytes= / none）的自然命中普查 ----------
print('\n== 5 · C7 死分支：形态在 31 行里的自然命中数 ==')
shapes = {'grep=': 0, 'grepcount=': 0, 'rows=': 0, 'exists': 0, 'bytes=': 0, 'none': 0}
for r in rows:
    expr = r[5].strip()
    if expr.startswith('grepcount='):
        shapes['grepcount='] += 1
        continue
    if expr.startswith('grep='):
        shapes['grep='] += 1
        continue
    if expr.startswith('rows='):
        shapes['rows='] += 1
        continue
    if expr.startswith('bytes='):
        shapes['bytes='] += 1
        continue
    if expr.strip() == 'none':
        shapes['none'] += 1
        continue
    if 'exists' in expr:
        shapes['exists'] += 1
print('  实测 =', shapes)
ck('5.1 三形态（exists/bytes=/none）实测全 0', shapes['exists'] == 0 and shapes['bytes='] == 0
   and shapes['none'] == 0, (shapes['exists'], shapes['bytes='], shapes['none']))
ck('5.2 正控：另三形态（grep=/grepcount=/rows=）计数非 0，说明普查器本身在工作',
   shapes['grep='] > 0 and shapes['grepcount='] > 0 and shapes['rows='] > 0,
   (shapes['grep='], shapes['grepcount='], shapes['rows=']))
# 5.3 这 31 行里有没有「本来就是判产物存在性/字节数」的行？逐行看断言式形态
exist_like = [r[0] for r in rows if re.search(r'(存在|在盘|字节|大小|sha256|字节数)', r[4] + r[5])]
print('  含「存在/在盘/字节/sha256」字样的行 ids =', exist_like)

# ---------- 6 · FACT_INDEX 三件的证据链 + 缺口 ----------
print('\n== 6 · F08 / F23 / F35 证据链在盘性（单一仓库根口径）==')
fi = rd(FI).split('\n')
frows = [l.split('\t') for l in fi if l.strip()][1:]
fd = {r[0]: r for r in frows}
print('  FACT_INDEX 数据行', len(frows))
def evid_state(r):
    out = []
    for seg in r[3].split(';'):
        seg = seg.strip()
        if not seg:
            continue
        q = seg.replace('\\', '/').split('(')[0]
        out.append((seg, os.path.exists(os.path.join(R, q))))
    return out
for fid in ('F08', 'F23', 'F35'):
    st = evid_state(fd[fid])
    live = sum(1 for _, e in st if e)
    print('  %s grade=%s 证据项 %d 活 %d 失 %d' % (fid, fd[fid][2], len(st), live, len(st) - live))
    for seg, e in st:
        print('     ', 'OK  ' if e else 'MISS', seg[:100])
ck('6.1 F23 两项证据全失（整行失联）',
   all(not e for _, e in evid_state(fd['F23'])), None)
ck('6.2 F35 五项 = 4 活 1 失（v5.34 起口径）',
   sum(1 for _, e in evid_state(fd['F35']) if e) == 4, None)

# 6.3 缺口：有没有任何东西在监控 F08 这个逐轮被写死的字段
FLOOR = D + '/FACTS_FLOORS.tsv'
ck('6.3 现盘不存在 FACTS_FLOORS.tsv（本轮的监控缺口）', not os.path.exists(FLOOR),
   os.path.exists(FLOOR))
# 6.4 反控：门禁源码里是否已有任何对 FACT_INDEX 的读取
ck('6.4 门禁 check_disc.py 完全不读 FACT_INDEX（缺口是结构性的，不是漏配）',
   'FACT_INDEX' not in src, [l.strip()[:60] for l in src.split('\n') if 'FACT_INDEX' in l])

print('\nFAILS=%d' % len(fails))
sys.exit(0 if not fails else 1)
