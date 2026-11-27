#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R151 A：11-22 快照遗存核定（只读，不改任何文件）。

回答 R150 待办第 2 项，并纠正 R150 自身两处口径错误：
 (i)  snapshot 根是 lead/（不是 next_re_20261117_r14/），r137a 的 snapkey 剥 lead/ 后
      仍保留 next_re_... 前缀 —— 实测核对；
 (ii) 4 行「自行复算」自述（L39793/39816/39850/39910）**并不点名** R17_R41_RECOMPUTE；
      而 R41 事项 2 原文（L40805/40818/40825/40845）点名它 —— R150 把两条依赖链混成一条；
 (iii) 四 token 承载行实测 14 行，R150 记 13 行；多出的 L47367 落在 R150 自己的 §1205 里；
 (iv) 台账对 R41_RECOMPUTE 的引用在「带 R17_ 前缀」口径下 7 行、「R41_RECOMPUTE 子串」口径下 8 行。

正控：已知在盘件（R14_COMMON.md / LEAD_LOCK / v540 FACT_INDEX）必须快照命中且现盘存在；
负控：自造文件名快照 0 命中、现盘不存在；反控：同尺寸命中判据不得恒空。
"""
import hashlib, json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
SNAP = os.path.join(D14, 'R17_R72_T1_CLEANSCALE', 'files_tier_A_snap2.tsv')
FIX = os.path.join(D14, 'R17_R112_FACTINDEX_V540', 'FACT_INDEX.tsv')
LEDGER = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

def items(col):
    out = []
    for seg in col.split(';'):
        s = seg.strip()
        if not s: continue
        out.append(s.split('(')[0].split('（')[0].strip())
    return out

def snapkey(rel):
    return rel[5:] if rel.startswith('lead/') else rel

# ---------- 0. 快照 ----------
sb = open(SNAP, 'rb').read()
snap_sha = hashlib.sha256(sb).hexdigest()
srows = [l.rstrip('\n').split('\t') for l in sb.decode('utf-8', 'replace').split('\n')]
sdata = [r for r in srows[1:] if r and r[0].strip()]
snap_bytes = {r[0].strip(): int(r[2]) for r in sdata if len(r) > 2 and r[2].isdigit()}
print('SNAP %d B sha256=%s rows=%d' % (len(sb), snap_sha, len(sdata)))
ck('0.1 表头五列', srows[0] == ['rel', 'ext', 'bytes', 'mtime_ns', 'selfkind'], srows[0])
ck('0.2 24,723 数据行', len(sdata) == 24723, len(sdata))
# 实测：rel 是 lead/ 相对路径，跨多个同级目录（next_re_20261117_r14/、next_re_20261112_r02/、
# .mimosa/ …），全表 0 行以 lead/ 开头 ⇒ 比对键须整体剥 'lead/'。
_tops = {}
for r in sdata:
    _tops[r[0].split('/')[0]] = _tops.get(r[0].split('/')[0], 0) + 1
print('  快照顶层目录 %d 个，前 6：%s' % (len(_tops), sorted(_tops.items(), key=lambda x: -x[1])[:6]))
ck('0.3 rel 为 lead/ 相对路径且无 lead/ 前缀',
   sum(1 for r in sdata if r[0].startswith('lead/')) == 0 and len(_tops) > 3, len(_tops))
ck('0.4 剥 lead/ 后与快照 rel 同形（非恒等）',
   all(snapkey('lead/' + r[0]) == r[0] for r in sdata[:500]), repr(sdata[0][0]))
mt = [int(r[3]) for r in sdata if len(r) > 3 and r[3].isdigit()]
ck('0.5 mtime 上界 = 2026-11-22 04:30 UTC 附近',
   1795321847 < max(mt) / 1e9 < 1795500000, round(max(mt) / 1e9, 2))

# ---------- 1. 现盘 size 索引 ----------
disk_size, nf = {}, 0
for dp, dn, fn in os.walk(ROOT):
    if '/.git' in dp: continue
    for f in fn:
        p = os.path.join(dp, f)
        try:
            if os.path.islink(p): continue
            st = os.stat(p)
        except OSError: continue
        disk_size.setdefault(st.st_size, []).append(os.path.relpath(p, ROOT))
        nf += 1
print('现盘普通文件 %d / 不同尺寸 %d' % (nf, len(disk_size)))
ck('1.1 索引非空且尺寸去重 < 文件数', 0 < len(disk_size) < nf, (len(disk_size), nf))
ck('R1 同尺寸判据非恒空', any(len(v) > 0 for v in disk_size.values()))

# ---------- 2. FACT_INDEX ----------
fb = open(FIX, 'rb').read()
fix_sha = hashlib.sha256(fb).hexdigest()
frows = [l.split('\t') for l in fb.decode('utf-8').split('\n')[1:] if l.strip()]
by_fid = {r[0]: r for r in frows}
ck('2.1 v540 sha256 = fabd1e57…', fix_sha.startswith('fabd1e57'), fix_sha[:12])
ck('2.2 54 数据行 / 全五列', len(frows) == 54 and all(len(r) == 5 for r in frows), len(frows))

def resolve(p):
    q = p.replace('\\', '/')
    return any(os.path.exists(c) for c in (os.path.join(ROOT, q), os.path.join(ROOT, 'lead', q)))

per = {}
for r in frows:
    its = items(r[3])
    per[r[0]] = dict(n=len(its), live=sum(1 for p in its if resolve(p)))
    per[r[0]]['dead'] = per[r[0]]['n'] - per[r[0]]['live']
tn = sum(v['n'] for v in per.values()); tl = sum(v['live'] for v in per.values())
ck('2.3 证据项 178 / 存活 135 / 失联 43', (tn, tl, tn - tl) == (178, 135, 43), (tn, tl, tn - tl))
ck('2.4 零存活行恰 F23', [k for k, v in per.items() if v['live'] == 0] == ['F23'],
   [k for k, v in per.items() if v['live'] == 0])
ck('2.5 F23 两项全失联', per['F23']['n'] == 2 and per['F23']['dead'] == 2, per['F23'])
ck('2.6 F35 五项、四活一失',
   per['F35']['n'] == 5 and per['F35']['live'] == 4 and per['F35']['dead'] == 1, per['F35'])

# ---------- 3. 核心：快照遗存 ----------
def probe(rel, label):
    sk = snapkey(os.path.join('lead', 'next_re_20261117_r14', rel))
    in_snap = sk in snap_bytes
    nb = snap_bytes.get(sk)
    same = disk_size.get(nb, []) if nb is not None else []
    od = os.path.exists(os.path.join(D14, rel))
    print('  %-40s snap=%-5s bytes=%-9s ondisk=%-5s same_size=%d'
          % (label or rel, in_snap, nb, od, len(same)))
    return dict(in_snapshot=in_snap, snap_bytes=nb, on_disk=od,
                same_size_hits=len(same), same_size_paths=same[:5])

print('\n[A] F23 计数依赖 coverage.tsv')
cov = probe('COVERAGE/coverage.tsv', 'COVERAGE/coverage.tsv')
ck('3.A.1 快照有记录且 bytes=4,147,334', cov['in_snapshot'] and cov['snap_bytes'] == 4147334, cov)
ck('3.A.2 现盘同名件不存在', not cov['on_disk'])
ck('3.A.3 4,147,334 B 现盘 0 同尺寸命中', len(disk_size.get(4147334, [])) == 0,
   disk_size.get(4147334, [])[:3])
ck('3.A.4 快照内 4,147,334 B 唯一（可反查指向该件）',
   sum(1 for v in snap_bytes.values() if v == 4147334) == 1)
cov_deriv = [p for p in disk_size.get(4147334, [])]
all_cov = [f for f in __import__('glob').glob(os.path.join(ROOT, '**', '*coverage*.tsv'), recursive=True)]
ck('3.A.5 现盘任何 *coverage*.tsv 均不存在', len(all_cov) == 0, all_cov[:5])

print('\n[B] R17_R41_RECOMPUTE 三件')
r41 = {r: probe('R17_R41_RECOMPUTE/' + r, r) for r in
       ('REPORT.md', 'crosscheck.json', 'numbers.tsv')}
ck('3.B.1 三件全部在快照有记录', all(v['in_snapshot'] for v in r41.values()),
   {k: v['in_snapshot'] for k, v in r41.items()})
ck('3.B.2 三件快照字节数与 R150 台账记载一致（11,824 / 1,864 / 2,289）',
   [r41['REPORT.md']['snap_bytes'], r41['crosscheck.json']['snap_bytes'],
    r41['numbers.tsv']['snap_bytes']] == [11824, 1864, 2289],
   [v['snap_bytes'] for v in r41.values()])
ck('3.B.3 三件现盘同名件全部不存在', not any(v['on_disk'] for v in r41.values()))
ck('3.B.4 REPORT.md 的 11,824 B 现盘 0 同尺寸命中（唯一尺寸）',
   len(disk_size.get(11824, [])) == 0, disk_size.get(11824, [])[:3])
ck('3.B.5 R17_R41_RECOMPUTE 目录现盘不存在',
   not os.path.exists(os.path.join(D14, 'R17_R41_RECOMPUTE')))

print('\n[C] 乙类 11 条 / 甲类 5 目录')
YI = ['COVERAGE/PANEL.md', 'GATE_BEHAV/PROGRESS.md', 'HANDOFF_R14_R3.md', 'HANDOFF_R16.md',
      'NAMED_PUSH_AUDIT10/VERDICT.md', 'R17_AUDIT_R9/VERDICT.md', 'R17_AUDIT_FI_V5/VERDICT.md',
      'R17_DELIVERY/DELIVERY_SUMMARY.md', 'S10_KPROVED/_audit/VERDICT.md',
      'S13_K10/_audit/VERDICT.md', 'S13_K12/_audit/VERDICT.md']
yi = {r: probe(r, r) for r in YI}
ck('3.C.1 乙类 11 条全部在快照有记录', all(v['in_snapshot'] for v in yi.values()),
   [k for k, v in yi.items() if not v['in_snapshot']])
ck('3.C.2 乙类 11 条现盘全部不存在', not any(v['on_disk'] for v in yi.values()),
   [k for k, v in yi.items() if v['on_disk']])
JIA = ['R17_LEDGER_1062', 'R17_LEDGER_1063', 'R17_LEDGER_1063R', 'R17_LEDGER_1064', 'R17_LEDGER_1065']
P = 'next_re_20261117_r14/'
jia = {d: sum(1 for k in snap_bytes if k.startswith(P + d + '/')) for d in JIA}
print('  甲类 5 目录快照件数：', jia)
ck('3.C.3 甲类 5 目录在快照各有 >=3 件', all(v >= 3 for v in jia.values()), jia)

# ---------- 4. 台账引用与四行自述的分离 ----------
lb = open(LEDGER, 'rb').read().decode('utf-8', 'replace')
ll = lb.split('\n')
ck('4.0 台账行数 47,376', len(ll) == 47376, len(ll))
exact = [i + 1 for i, l in enumerate(ll) if 'R17_R41_RECOMPUTE' in l]
substr = [i + 1 for i, l in enumerate(ll) if 'R41_RECOMPUTE' in l]
print('  带前缀 R17_R41_RECOMPUTE 命中行：%s（%d）' % (exact, len(exact)))
print('  子串 R41_RECOMPUTE 命中行：%s（%d）' % (substr, len(substr)))
ck('4.1 带前缀口径 7 行、子串口径 8 行（R150 记的 8 是子串口径）',
   (len(exact), len(substr)) == (7, 8), (len(exact), len(substr)))
ck('4.2 子串多出的那一行恰 L47359（R150 自己的补记节标题）',
   set(substr) - set(exact) == {47359}, set(substr) - set(exact))
SELF = [39793, 39816, 39850, 39910]
ck('4.3 四行自述无一点名 R41_RECOMPUTE（R150 混链的关键）',
   not any('R41_RECOMPUTE' in ll[n - 1] for n in SELF),
   {n: ('R41_RECOMPUTE' in ll[n - 1]) for n in SELF})
R41ITEM = [40805, 40818, 40825, 40845]
ck('4.4 R41 事项原文四行全部点名 R41_RECOMPUTE',
   all('R41_RECOMPUTE' in ll[n - 1] for n in R41ITEM),
   {n: ('R41_RECOMPUTE' in ll[n - 1]) for n in R41ITEM})
def tok(num):
    s = str(num)
    # 双侧边界都禁 [0-9,]：否则 293 会命中字节串 293,512 的前三位（R151 被审计员当场抓到的缺陷）。
    if len(s) > 3:
        return re.compile('(?<![0-9,])' + s[:-3] + ',' + s[-3:] + '(?![0-9,])'
                          + '|(?<![0-9,])' + s + '(?![0-9,])')
    return re.compile('(?<![0-9,])' + s + '(?![0-9,])')
T = {n: tok(n) for n in (458, 291, 293, 1196)}
carry = [i + 1 for i, l in enumerate(ll) if all(rx.search(l) for rx in T.values())]
print('  四 token 同行承载行（严格双边界）：%s（%d）' % (carry, len(carry)))
ck('4.5 承载行严格口径 12 行', len(carry) == 12, len(carry))
# 病型登记：R150 记 13 行、其口径下实为 14 行；两行是 293,512 字节串造成的假命中。
FAKE = [39648, 39793]
for n in FAKE:
    ck('4.6 L%d 的 293 实为字节串 293,512 前缀（假命中）' % n,
       '293,512' in ll[n - 1], [ll[n - 1][max(0, m.start() - 8):m.start() + 12]
                                for m in re.finditer('293', ll[n - 1])])
ck('4.6b 假命中行不在严格集里，且严格集比 R150 的 13 行少恰这两行、多 L47367',
   not (set(FAKE) & set(carry))
   and sorted(set([39648, 39793, 39816, 39850, 39910, 40811, 44032, 44069, 44087,
                   47079, 47085, 47313, 47353]) - set(carry)) == FAKE
   and sorted(set(carry) - set([39648, 39793, 39816, 39850, 39910, 40811, 44032, 44069,
                                 44087, 47079, 47085, 47313, 47353])) == [47367],
   carry)
ck('4.6c L47367 落在 §1205 内（标题在 L47359）',
   47367 in carry and ll[47358].startswith('## §1205'), ll[47358][:20])
# 反控：换个只排除 293,5xx 字节形态的写法，行集必须与严格集相同（判据稳健）。
alt = [i + 1 for i, l in enumerate(ll)
       if all((re.compile('(?<![0-9,])293(?![0-9,])') if n == 293 else T[n]).search(l)
              for n in (458, 291, 293, 1196))]
ck('4.6d 反控：换写法后行集与严格集逐项相同', alt == carry, (len(alt), len(carry)))
for bad in ('11196', '0x1196', '111,196', '11960', '4580', '2910', '2931'):
    ck('4.7 负控 %s 不命中 458/291' % bad,
       not T[458].search(bad) and not T[291].search(bad))
ck('4.8 R41 事项 2 正文载 F23 四口径数值：L40811 载 458/291/293/1,196，L40809 载 18,498',
   all(x in ll[40810] for x in ('458', '291', '293', '1,196'))
   and '18,498' in ll[40808], ll[40810][:80])
ck('4.9 L40810 不载上述任何一数（R151 初版把行号记成 40810，被审计员纠正）',
   not any(x in ll[40809] for x in ('458', '291', '293', '1,196', '18,498')), ll[40809][:60])

# ---------- 5. 控项 ----------
print('\n[控项]')
# 正控必须落在快照覆盖范围内：R14_COMMON.md 在快照且在盘。
ck('P1 R14_COMMON.md 快照命中', (P + 'R14_COMMON.md') in snap_bytes)
ck('P2 R14_COMMON.md 现盘存在', os.path.exists(os.path.join(D14, 'R14_COMMON.md')))
# 关键限定：快照缺席 != 从未存在。以下两件都在盘却都不在快照里 ⇒ 快照非全覆盖。
SNAP_BLIND = [P + 'COMPACT_STATE.md', P + 'R17_R112_FACTINDEX_V540/FACT_INDEX.tsv']
blind_disk = [os.path.exists(os.path.join(ROOT, 'lead', k)) for k in SNAP_BLIND]
print('  快照盲区探针 %s -> snap=%s disk=%s'
      % ([k.split('/')[-1] for k in SNAP_BLIND],
         [k in snap_bytes for k in SNAP_BLIND], blind_disk))
ck('P3 快照缺席≠从未存在：这两件在盘但快照 0 命中',
   all(blind_disk) and not any(k in snap_bytes for k in SNAP_BLIND),
   dict(zip([k.split('/')[-1] for k in SNAP_BLIND],
            [k in snap_bytes for k in SNAP_BLIND])))
# 故「在快照中命中」是充分不必要条件：只能证曾存在，不能证现在在盘。
ck('P4 LEAD_LOCK / v540 在快照外（登记为盲区，不作正控）',
   (P + 'LEAD_LOCK') not in snap_bytes and (LOCK and os.path.exists(LOCK)),
   'LEAD_LOCK 快照缺席但现盘存在')
ck('N1 自造路径快照 0 命中', (P + 'R17_R41_RECOMPUTE/ZZZ_R151_NOT_REAL.md') not in snap_bytes)
ck('N2 自造路径现盘不存在',
   not os.path.exists(os.path.join(D14, 'R17_R41_RECOMPUTE', 'ZZZ_R151_NOT_REAL.md')))
# 反控：把已证「在盘」的经验用在被证「不在盘」的件上必须给出否定——判据不恒真。
ck('N3 同一判据对在盘件给真、对已失件给假（判据有鉴别力）',
   os.path.exists(os.path.join(D14, 'R14_COMMON.md'))
   and not os.path.exists(os.path.join(D14, 'COVERAGE/coverage.tsv')))

json.dump(dict(snap=dict(path=SNAP, sha256=snap_sha, bytes=len(sb), rows=len(sdata)),
               fix=dict(path=FIX, sha256=fix_sha, rows=len(frows)),
               ledger=dict(path=LEDGER, lines=len(ll)),
               coverage=cov, r41=r41, yi=yi, jia=jia,
               ledger_refs=dict(exact=exact, substr=substr),
               carry_rows=carry, self_declare=SELF, r41_item=R41ITEM,
               snap_blind=[k.split('/')[-1] for k in SNAP_BLIND],
               disk=dict(files=nf, sizes=len(disk_size)),
               fails=fails),
          open(os.path.join(ROOT, '_r151', 'r151a_recompute_snap.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nFAIL %d 条：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
