#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137-a · FACT_INDEX v5.32 证据链现盘可解析度普查（只读）

目的：F23/F35 的「证据链核验」此前只记「引用的 PANEL.md / DELIVERY_SUMMARY.md 已失」，
从未做过全表普查。本脚本机械测量 54 条 F 项的第 4 列 evidence_paths：
逐条拆成 (路径, 括号内定位符)，判「文件是否在现盘存在」「字节数」「是否在 11-22 快照清单里」。

设计约束（防 OOM / 防恒真断言）：
  - 只读小文本，不碰 gamemd.exe 大段反汇编。
  - 每条断言都带反控（对一个已知不存在的路径必须判 False）。
  - 不做「or True」型恒真断言。
"""
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
FIX = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
SNAP = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv')

RES = []
FAIL = 0


def chk(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + ('  :: ' + str(detail)[:220] if detail else ''))


def load_tsv(p):
    return [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]


def win2posix(p):
    """把台账里的 Windows 相对路径化成 posix 相对路径。"""
    return p.replace('\\', '/').strip()


def parse_entry(e):
    """'path(A/B)' -> ('path', 'A/B')；'path' -> ('path', '')。
    只在最后一个顶层 '(' 处切分，避免 §2.9四 之类括号嵌套误伤。
    已知形态：(§2.6/§13.1/§13.2)、(R17 第 20–21 轮 段)、(M69 / M102)、(§2.9四)。
    """
    e = e.strip()
    if not e:
        return None, None
    i = e.find('(')
    if i < 0:
        return e, ''
    # 括号必须闭合在末尾
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]


def main():
    rows = load_tsv(FIX)
    hdr = rows[0]
    chk('A0 header shape', hdr[:2] == ['fact_id', 'statement'], hdr[:5])
    body = [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]
    chk('A1 fact rows == 54', len(body) == 54, len(body))

    # ---- 拆 entry ----
    entries = []   # (fact_id, raw_entry, path, loc)
    for r in body:
        for e in r[3].split(';'):
            e = e.strip()
            if not e:
                continue
            p, loc = parse_entry(e)
            if p is None:
                continue
            entries.append((r[0], e, p, loc))
    chk('A2 total evidence entries > 100', len(entries) > 100, len(entries))

    # ---- 反控 N1: 已知不存在的路径必须判 no ----
    ghost = 'lead/next_re_20261117_r14/__NO_SUCH_FILE_R137__.md'
    chk('N1 ghost path not on disk', not os.path.exists(os.path.join(ROOT, ghost)), ghost)

    # ---- 现盘存在性 ----
    stat = {}
    for fid, raw, p, loc in entries:
        rel = win2posix(p)
        ab = os.path.join(ROOT, rel)
        if rel not in stat:
            try:
                st = os.stat(ab)
                stat[rel] = st.st_size
            except OSError:
                stat[rel] = None
    exist = {k: v for k, v in stat.items() if v is not None}
    missing = sorted(k for k, v in stat.items() if v is None)
    chk('A3 distinct paths measured == len(stat)', len(stat) == len(set(
        win2posix(p) for _, _, p, _ in entries)), (len(stat), len(entries)))
    chk('A4 some files exist (not all-missing) and some are missing (not all-present)',
        len(exist) > 0 and len(missing) > 0, (len(exist), len(missing)))

    # ---- 按 entry 计（同一文件被多行引用各算一次）----
    e_exist = sum(1 for _, _, p, _ in entries if stat.get(win2posix(p)) is not None)
    e_miss = len(entries) - e_exist
    print('\n[entry 口径] 总 %d / 命中 %d / 未命中 %d' % (len(entries), e_exist, e_miss))
    print('[distinct 口径] 总 %d / 命中 %d / 未命中 %d' % (len(stat), len(exist), len(missing)))

    # ---- 反控 N2: 把同一个路径清单整体加一个错前缀，命中数必须降到 0 ----
    bogus = sum(1 for k in stat if os.path.exists(os.path.join(ROOT, '__x__', k)))
    chk('N2 bogus-prefix recount is 0', bogus == 0, bogus)

    # ---- 快照清单：这批路径在 11-22 快照里有没有记录 ----
    snap = set()
    if os.path.exists(SNAP):
        for r in load_tsv(SNAP)[1:]:
            if len(r) >= 2 and r[0].strip():
                snap.add(r[0].strip())
    chk('A5 snapshot list loaded (>20000 rows)', len(snap) > 20000, len(snap))

    # S-253（自错，A7 当场抓出）：快照清单的遍历根是 lead\，清单里的 rel 不含 lead/ 前缀，
    # 而台账 evidence_paths 带 lead\ 前缀。初版直接拿带前缀的键去比对，16/16 全判「快照无记录」，
    # 与 R136 已证「DELIVERY_SUMMARY.md 在 11-22 快照里」直接矛盾 —— 是比对键错，不是结论。
    def snapkey(rel):
        return rel[5:] if rel.startswith('lead/') else rel

    in_snap = sorted(k for k in stat if snapkey(k) in snap)
    miss_in_snap = sorted(k for k in missing if snapkey(k) in snap)
    miss_not_in_snap = sorted(k for k in missing if snapkey(k) not in snap)
    chk('A6b snapkey strip is not identity for all (prefix really removed)',
        any(snapkey(k) != k for k in stat) and all(not snapkey(k).startswith('lead/') for k in stat),
        'sample ' + repr(sorted(snapkey(k) for k in stat)[:2]))
    print('[缺失且快照有记录] %d ; [缺失且快照也无记录] %d' %
          (len(miss_in_snap), len(miss_not_in_snap)))
    chk('A6 missing-but-in-snapshot is a proper subset of missing',
        set(miss_in_snap) <= set(missing), len(miss_in_snap))
    chk('A7 snapshot coverage discriminates (not 0 and not len(stat))',
        0 < len(in_snap) < len(stat), (len(in_snap), len(stat)))

    # ---- 逐行：该行是否 *全部* 证据失联 ----
    by_fact = {}
    for fid, raw, p, loc in entries:
        by_fact.setdefault(fid, []).append(win2posix(p))
    all_dead, part_dead, all_ok = [], [], []
    for fid, ps in sorted(by_fact.items()):
        hits = [x for x in ps if stat.get(x) is not None]
        if not hits:
            all_dead.append(fid)
        elif len(hits) == len(ps):
            all_ok.append(fid)
        else:
            part_dead.append(fid)
    print('\n[整行失联] %d %s' % (len(all_dead), all_dead))
    print('[部分失联] %d %s' % (len(part_dead), part_dead))
    print('[全链在位] %d %s' % (len(all_ok), all_ok))
    chk('A8 three buckets cover all facts', len(all_dead) + len(part_dead) + len(all_ok) == len(by_fact),
        (len(all_dead), len(part_dead), len(all_ok), len(by_fact)))
    chk('A9 each bucket is non-empty (measurement has discrimination)',
        len(all_dead) > 0 and len(all_ok) > 0, 'dead=%d ok=%d' % (len(all_dead), len(all_ok)))

    # ---- F23 / F35 定点 ----
    focus = {}
    for fid in ('F23', 'F35', 'F24', 'F29'):
        ps = by_fact.get(fid, [])
        focus[fid] = {
            'entries': len(ps),
            'paths': ps,
            'dead': [x for x in ps if stat.get(x) is None],
            'live': [x for x in ps if stat.get(x) is not None],
        }
    chk('A10 F23 has evidence entries', focus['F23']['entries'] > 0, focus['F23']['entries'])
    chk('A11 F35 has evidence entries', focus['F35']['entries'] > 0, focus['F35']['entries'])
    print('\n[F23]');  [print('   ', ('LIVE ' if stat.get(x) is not None else 'DEAD '), x) for x in focus['F23']['paths']]
    print('[F35]');  [print('   ', ('LIVE ' if stat.get(x) is not None else 'DEAD '), x) for x in focus['F35']['paths']]

    # ---- 反控 N3: 只把路径的最后一段换成不存在名，命中数必须 0 ----
    n3 = 0
    for k in stat:
        alt = os.path.join(os.path.dirname(k), '__zzz__.md')
        if os.path.exists(os.path.join(ROOT, alt)):
            n3 += 1
    chk('N3 basename-substituted paths all absent', n3 == 0, n3)

    # ---- 汇总 ----
    out = {
        'fix': os.path.relpath(FIX, ROOT),
        'rows': len(body),
        'entries_total': len(entries),
        'entries_live': e_exist,
        'entries_dead': e_miss,
        'distinct_total': len(stat),
        'distinct_live': len(exist),
        'distinct_dead': len(missing),
        'missing_list': missing,
        'missing_in_snapshot': miss_in_snap,
        'missing_not_in_snapshot': miss_not_in_snap,
        'facts_all_dead': all_dead,
        'facts_part_dead': part_dead,
        'facts_all_ok': all_ok,
        'focus': focus,
        'assertions': RES,
        'fail': FAIL,
    }
    with io.open(os.path.join(ROOT, '_r137/r137a_evidchain.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\n=== assertions %d, FAIL %d ===' % (len(RES), FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
