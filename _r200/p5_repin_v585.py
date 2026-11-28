#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 台账升版 V583 -> V584：只改 F55 一行（追加第 ⑧ 条实测），其余 55 行逐字节不变。
fail-closed：旧常量复算旧 MASTER 命中旧 pin 作硬闸；新版本目录先写，后改指针（顺序不可反）。
"""
import ast, hashlib, io, os, re, sys, shutil, time
from collections import Counter
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD_DIR = 'R17_R131_FACTINDEX_V584'; NEW_DIR = 'R17_R131_FACTINDEX_V585'
SRC = os.path.join(TIER, OLD_DIR, 'FACT_INDEX.tsv')
DSTDIR = os.path.join(TIER, NEW_DIR)
DST = os.path.join(DSTDIR, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

old = io.open(SRC, encoding='utf-8', newline='').read()
sha_old = hashlib.sha256(old.encode()).hexdigest()
ck('G1a 源 V584 未变（216858 B / aaa569ab… / CR 0）',
   len(old.encode()) == 216858 and sha_old.startswith('aaa569ab') and old.count('\r') == 0,
   (len(old.encode()), sha_old[:16], old.count('\r')))
L = old.split('\n')
ck('G1b 58 段（1 表头 + 56 行 + 尾空）且 5 列', len(L) == 58 and all(len(x.split('\t')) == 5 for x in L[:57]),
   (len(L), [i for i, x in enumerate(L[:57]) if len(x.split('\t')) != 5]))
R = [x.split('\t') for x in L[:57]]
f55 = [r for r in R if r[0] == 'F55'][0]

ADD1 = ('⑪**R200 审计 #503 回填（deepseek，28 回合 / 15.13 分 / 预算 8 分，[OVERTIME]；主会话 _r200/m12_audit503.py 复算 27 断言 0 FAIL）**：'
        '①**口径订正**：全 .text 的 call rel32 指令共 **68,253** 条，其中 target 落在 .text 内的 **68,244** 条，差 **9** 条为**非段内 target**'
        '（0xC0C5A07E / 0x46533E39 / 0xE2E0EC18 / 0xD45A5A67 / 0xE971FEAB / 0xE8D3E98A / 0xFA78B3A7 / 0xF07D1E7E / 0xD87E4995，'
        '调用点 0x409FF2 / 0x52EB58 / 0x52EBC1 / 0x5A0074 / 0x6DFE39 / 0x70E915 / 0x783B68 / 0x7CA1D8 / 0x7DCBC8）。'
        '②**字节法假阳已定位**：字节法比反汇编法多出的 1 条 **0x74836A 是假阳**，落在 **0x748368 adc edx, dword ptr [eax-0x18]（3 字节）的指令体内**，'
        '该指令跨过 0x74836A ⇒ `call 0x7C8B3D` 的真值取**反汇编 4,498**（字节法 4,499 须减 1）。'
        '③**「538 是旧口径数」不成立**：严格正则与宽松正则**同为 538**（差 0），538 是**两口径同值**；'
        '「位移 1..9 的装表 store = 0」也是实测（位移分布 0:532 / 0x10:1 / 0x14:1 / 0x18:1 / 0x34:1 / 0x3F338:1 / 0x3F550:1），不是推断。'
        '④**「更近祖先 0 条」是同义反复**：cat==other 的定义已排掉 imm==vt_d（idx_imm 0）与 imm==vt_b（idx_imm 1），'
        '故 idx_imm ∈ {0,1} 处 0 条是**定义的算术后果**，不算观测；有效观测只有「更远祖先 21 / 不在血缘 21」。'
        '⑤**新增 4 条实测**：s0d 的 **vt_b 去重只有 269**（vt_d 去重 516）⇒ 直基类主表被高度复用；'
        '**6 个无 call 实现**逐一为 **0x4F6830 / 0x5125A0 / 0x554400 / 0x643E80 / 0x7AC700 / 0x7AC870**；'
        '两组对照 **z = 8.19（p<1e-15）/ z = 1.69（p≈0.091）**；逐块口径 **不过滤 55,424 / 过滤 55,419**（与单次迭代差 12,829 / 12,825）。'
        '⑥**宿主判据边界（首次给数）**：1,229 个「宿主」里前一字节 **0x90 占 1,162 / 0xC3 占 16 / 0x00 占 49 / 0xFF 占 2** ⇒ **51 个（4.15%）不像函数起点**；'
        '宿主到调用点距离 **p10 = 91 / p50 = 707 / p90 = 10,125 / max = 41,067 字节** ⇒ **宿主不可当函数**，凡用「宿主」处按此边界理解。')

ADD_EV = ('_r200/m12_audit503.py;_r200/m12_audit503.json')

f55[1] = f55[1] + ADD1
f55[3] = f55[3] + ';' + ADD_EV
new = '\n'.join('\t'.join(r) for r in R) + '\n' + (L[-1] if L[-1] == '' else '')
newraw = new.encode()
ck('G2a 新体 CR 仍 0 / 换行数仍 57（57 行各带一 LF，末行无空行）',
   newraw.count(b'\r') == 0 and new.count('\n') == len(L) - 1,
   (newraw.count(b'\r'), new.count('\n'), len(L) - 1))
ck('G2b 除 F55 外 55 行逐字节未变',
   all(R[i] == L[i].split('\t') for i in range(57) if R[i][0] != 'F55'), True)
# 常量与 MASTER 复算
FF = os.path.join(ROOT, '_r160/facts_floors.py')
src = io.open(FF, encoding='utf-8', newline='').read()
need = ('CUR_SHA256', 'TOTAL_BYTES', 'MASTER_SHA256', 'GRADES', 'FLOORS', 'EVID', 'EVIDB', 'LOST', 'ITEMS', 'UNIQ', 'LOST_ITEMS', 'LOST_UNIQ')
C = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C[nm] = ast.literal_eval(node.value)
ck('G3a 12 常量可 ast 取出', all(k in C for k in need))
def canon_g(d): return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d): return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d): return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d): return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def master(sha, tot, floors, grades, evid, evidb, lost, items, uniq, li, lu):
    return hashlib.sha256(('\n'.join([sha, str(tot), canon_g(grades), canon_f(floors), canon_e(evid),
        canon_eb(evidb), canon_eb(lost), str(items), str(uniq), str(li), str(lu)])).encode()).hexdigest()
old_m = master(C['CUR_SHA256'], C['TOTAL_BYTES'], C['FLOORS'], C['GRADES'], C['EVID'], C['EVIDB'],
               C['LOST'], C['ITEMS'], C['UNIQ'], C['LOST_ITEMS'], C['LOST_UNIQ'])
ck('G3b 旧常量复算旧 MASTER 命中旧 pin（硬闸）', old_m == C['MASTER_SHA256'], (old_m[:16], C['MASTER_SHA256'][:16]))
# 新常量
new_sha = hashlib.sha256(newraw).hexdigest(); new_tot = len(newraw)
def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s
def norm(p): return p.replace('\\', '/').strip()
def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False
items = []
for r in R[1:]:
    for x in r[3].split(';'):
        if x.strip(): items.append((r[0], norm(strip_note(x))))
uniq = set(p for _, p in items)
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
ck('G3c 新增 2 条证据路径全部可解析',
   all(resolvable(x) for x in ADD_EV.split(';')), [x for x in ADD_EV.split(';') if not resolvable(x)])
ck('G3d LOST 多重集逐键未变', dict(lostc) == C['LOST'], (len(lost), len(lostc), C['LOST_ITEMS']))
GRADES2 = dict(C['GRADES']); FLOORS2 = dict(C['FLOORS'])
FLOORS2['F55'] = (len(f55[1].encode()), len(f55[4].encode()))
EVID2 = dict(C['EVID']); EVIDB2 = dict(C['EVIDB'])
EVID2['F55'] = [norm(strip_note(x)) for x in f55[3].split(';') if x.strip()]
EVIDB2['F55'] = len(f55[3].encode())
ck('G3e FLOORS["F55"] 现盘 %s -> %s（stmt 增、lim 不缩）' % (C['FLOORS']['F55'], FLOORS2['F55']),
   C['FLOORS']['F55'] == (37184, 24540) and FLOORS2['F55'][0] > 37184 and FLOORS2['F55'][1] >= 24540,
   (C['FLOORS']['F55'], FLOORS2['F55']))
ck('G3f EVID["F55"] 87 -> %d 条且前 87 条逐项未动' % len(EVID2['F55']),
   len(EVID2['F55']) == 87 + 2 and EVID2['F55'][:87] == C['EVID']['F55'], len(EVID2['F55']))
ck('G3g EVIDB["F55"] 1833 -> %d' % EVIDB2['F55'], C['EVIDB']['F55'] == 1833 and EVIDB2['F55'] != 1833, EVIDB2['F55'])
_low = []
for fid in C['FLOORS']:
    if fid == 'F55': continue
    r = [x for x in R if x[0] == fid][0]
    cur = (len(r[1].encode()), len(r[4].encode())); fl = C['FLOORS'][fid]
    if not (cur[0] >= fl[0] and cur[1] >= fl[1]): _low.append((fid, fl, cur))
ck('G3h 既有 55 条 FLOORS 仍 <= 现盘', not _low, _low[:3])
ck('G3i 既有 55 条 grade 逐条未变',
   all(C['GRADES'][k] == [x for x in R if x[0] == k][0][2] for k in C['GRADES'] if k != 'F55'))
new_m = master(new_sha, new_tot, FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc),
               len(items), len(uniq), len(lost), len(lostc))
ck('G3j 新 MASTER != 旧 MASTER', new_m != old_m, (new_m[:16], old_m[:16]))
ck('G3k 反控 A：F55 lim floor +1 ⇒ MASTER 变',
   master(new_sha, new_tot, {**FLOORS2, 'F55': (FLOORS2['F55'][0], FLOORS2['F55'][1] + 1)}, GRADES2, EVID2, EVIDB2,
          dict(lostc), len(items), len(uniq), len(lost), len(lostc)) != new_m)
ck('G3l 反控 B：EVIDB["F55"] +1 ⇒ MASTER 变',
   master(new_sha, new_tot, FLOORS2, GRADES2, EVID2, {**EVIDB2, 'F55': EVIDB2['F55'] + 1}, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m)
ck('G3m 反控 C：TOTAL_BYTES +1 ⇒ MASTER 变',
   master(new_sha, new_tot + 1, FLOORS2, GRADES2, EVID2, EVIDB2, dict(lostc),
          len(items), len(uniq), len(lost), len(lostc)) != new_m)
print('   ITEMS %d -> %d / UNIQ %d -> %d / LOST %d -> %d / LOST_UNIQ %d -> %d'
      % (C['ITEMS'], len(items), C['UNIQ'], len(uniq), C['LOST_ITEMS'], len(lost), C['LOST_UNIQ'], len(lostc)))
ck('G3n ITEMS/UNIQ 增量 == 2', (len(items) - C['ITEMS'], len(uniq) - C['UNIQ']) == (2, 2),
   (len(items) - C['ITEMS'], len(uniq) - C['UNIQ']))
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
print('== 写盘阶段 1：先建新版本目录 ==')
os.makedirs(DSTDIR, exist_ok=True)
ck('W1a 目标目录不存在同名文件', not os.path.exists(DST), os.path.exists(DST))
io.open(DST, 'wb').write(newraw)
ck('W1b 回读一致（sha / 字节 / CR）',
   hashlib.sha256(io.open(DST, 'rb').read()).hexdigest() == new_sha and
   len(io.open(DST, 'rb').read()) == new_tot and io.open(DST, 'rb').read().count(b'\r') == 0,
   (new_sha[:16], new_tot))
# 更新 facts_floors.py
ns = src
ns = ns.replace("'%s'" % OLD_DIR, "'%s'" % NEW_DIR, 1)
ck('G4a EXPECT_CUR 目录号已换且只 1 处', OLD_DIR not in ns and ns.count(NEW_DIR) == 1,
   (ns.count(OLD_DIR), ns.count(NEW_DIR)))
ns = ns.replace("CUR_SHA256 = '%s'" % C['CUR_SHA256'], "CUR_SHA256 = '%s'" % new_sha, 1)
ns = ns.replace("TOTAL_BYTES = %d" % C['TOTAL_BYTES'], "TOTAL_BYTES = %d" % new_tot, 1)
def block(olddict, newdict, name):
    global ns
    pat = re.compile(r'^%s = \{\n(.*?)\n\}$' % name, re.M | re.S)
    m = pat.search(ns); assert m, name
    body_old = m.group(1)
    def fmt(v):
        if isinstance(v, str): return "'%s'" % v
        if isinstance(v, tuple): return '(%d, %d)' % v
        if isinstance(v, int): return '%d' % v
        return '[%s]' % ', '.join("'%s'" % x for x in v)
    body_new = '\n'.join("    '%s': %s," % (k, fmt(newdict[k])) for k in sorted(newdict))
    ns = ns[:m.start(1)] + body_new + ns[m.end(1):]
    return body_old != body_new
ch_g = block(C['GRADES'], GRADES2, 'GRADES')
ch_f = block(C['FLOORS'], FLOORS2, 'FLOORS')
ch_e = block(C['EVID'], EVID2, 'EVID')
ch_b = block(C['EVIDB'], EVIDB2, 'EVIDB')
ck('G4b 只有 FLOORS / EVID / EVIDB 三表变化', ch_f and ch_e and ch_b and not ch_g, (ch_g, ch_f, ch_e, ch_b))
for name, val in (('ITEMS', len(items)), ('UNIQ', len(uniq)), ('LOST_ITEMS', len(lost)), ('LOST_UNIQ', len(lostc))):
    ns = re.sub(r'^%s = \d+$' % name, '%s = %d' % (name, val), ns, count=1, flags=re.M)
pat = re.compile(r'^LOST = \{\n(.*?)\n\}$', re.M | re.S)
m = pat.search(ns); ck('G4c LOST 表可定位', m is not None)
ns = ns[:m.start(1)] + '\n'.join("    '%s': %d," % (k, lostc[k]) for k in sorted(lostc)) + ns[m.end(1):]
ns = ns.replace("MASTER_SHA256 = '%s'" % C['MASTER_SHA256'], "MASTER_SHA256 = '%s'" % new_m, 1)
C2 = {}
for node in ast.parse(ns).body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
        nm = node.targets[0].id
        if nm in need: C2[nm] = ast.literal_eval(node.value)
ck('G4d 新源码 12 常量可 ast 取出', all(k in C2 for k in need))
ck('G4e 新源码用新常量复算 MASTER 命中新 pin',
   master(C2['CUR_SHA256'], C2['TOTAL_BYTES'], C2['FLOORS'], C2['GRADES'], C2['EVID'], C2['EVIDB'],
          C2['LOST'], C2['ITEMS'], C2['UNIQ'], C2['LOST_ITEMS'], C2['LOST_UNIQ']) == C2['MASTER_SHA256'])
ck('G4f 新源码 F55 floor 与 EVIDB 已换',
   C2['FLOORS']['F55'] == FLOORS2['F55'] and C2['EVIDB']['F55'] == EVIDB2['F55'],
   (C2['FLOORS']['F55'], C2['EVIDB']['F55']))
GR = os.path.join(ROOT, '_r161/gate_runner.py')
gr = io.open(GR, encoding='utf-8', newline='').read()
ck('G5a gate_runner 含旧目录 1 次', gr.count(OLD_DIR) == 1, gr.count(OLD_DIR))
gr2 = gr.replace(OLD_DIR, NEW_DIR, 1)
ck('G5b gate_runner 换后含新目录 1 次 / 旧目录 0 次', gr2.count(NEW_DIR) == 1 and gr2.count(OLD_DIR) == 0)
PTR = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
ptr = io.open(PTR, encoding='utf-8', newline='').read()
ck('G6a 旧版本目录串在指针里出现 2 次', ptr.count(OLD_DIR) == 2, ptr.count(OLD_DIR))
for o, tag in ((C['CUR_SHA256'], 'P2 sha256'), (str(C['TOTAL_BYTES']), 'P3 字节数'),
               ('530..584 连续 55 份', 'P4 自述份数'), ('| 声明轮次 | R199 |', 'P5 声明轮次')):
    ck('G6b %s 在指针里恰 1 次' % tag, ptr.count(o) == 1, ptr.count(o))
ptr2 = ptr.replace(OLD_DIR, NEW_DIR).replace(C['CUR_SHA256'], new_sha, 1) \
    .replace(str(C['TOTAL_BYTES']), str(new_tot), 1) \
    .replace('530..584 连续 55 份', '530..585 连续 56 份', 1) \
    .replace('| 声明轮次 | R199 |', '| 声明轮次 | R200 |', 1)
ck('G6c 指针新体含 V585 与 R200', NEW_DIR in ptr2 and '| 声明轮次 | R200 |' in ptr2)
if fails:
    print('★ fail-closed（写盘阶段 2）：%d 条未过' % len(fails)); sys.exit(1)
print('== 写盘阶段 2：改 facts_floors / gate_runner / 指针 ==')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE'); stamp = time.strftime('%Y%m%d_%H%M%S')
for path, oldraw, newtxt, tag in ((FF, src.encode(), ns, 'facts_floors'),
                                  (GR, gr.encode(), gr2, 'gate_runner'),
                                  (PTR, ptr.encode(), ptr2, 'ptr')):
    bak = os.path.join(BL, '%s.before_r200b_repin_%s.bak' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(oldraw)
    ck('W2 %s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(oldraw).hexdigest())
    assert io.open(path, 'rb').read() == oldraw, '%s 被外部改动' % tag
    io.open(path, 'w', encoding='utf-8', newline='').write(newtxt)
    ck('W3 %s 回读一致' % tag,
       hashlib.sha256(open(path, 'rb').read()).hexdigest() == hashlib.sha256(newtxt.encode()).hexdigest())
print('   NEW_SHA=%s NEW_BYTES=%d NEW_MASTER=%s' % (new_sha, new_tot, new_m))
print('   FLOORS F55=%s EVIDB F55=%d EVID F55=%d 条' % (FLOORS2['F55'], EVIDB2['F55'], len(EVID2['F55'])))
print('   ITEMS=%d UNIQ=%d LOST=%d/%d' % (len(items), len(uniq), len(lost), len(lostc)))
print('\nSUMMARY asserts=%d fails=%d %s' % (n, len(fails), fails))
