# -*- coding: utf-8 -*-
"""
check_col.py —— census_no_ring4 类 V1 行的「②④ 是否同一张表」核对（§12.3 决定性判据）。

背景：`classification_trace.tsv` 有 `source` 列。本卡实测 census_no_ring4 的 V1 行
**全部** `source == 'vtable'`，即 ②（类属）的证据**就是那张虚表**。于是问：
该行 ④ 若用「被活虚表槽持有」，用的**是不是同一张表**？同表 ⇒ §12.3（D-40 ④② 同源）判死；
异表（如 ② 来自基类表、④ 来自派生类表 / 模板表）才算可能的独立链。

判法（机械，逐行）：
  trace.name 形如 `ClassName::slotN` ⇒ trace 类名 = ClassName
  RTTI 解出的 COL 装饰名 `. ?AVClassName@@`（模板 `.?AV?$DynamicVectorClass@PAVX@@@@` 取其内层 X）
  ⇒ same_table = (trace 类名 与 COL 类名 相容)

相容判定沿用 PROBE_802 的 col_name_match()：模板伪名 `T_A_B__` 要求每个片段都出现在装饰名里，
否则要求类名是装饰名的子串。

只读：只写 R16_PROBE_4GAP\。
跑法：python check_col.py
"""
import sys
sys.dont_write_bytecode = True

import os
import io
import re
import json
import importlib.util
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
PROBE802 = os.path.join(R14, 'PROBE_802')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')


def load_p802():
    name = 'p802'
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name,
                                                  os.path.join(PROBE802, 'probe.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_trace():
    import glob
    tr = {}
    for f in glob.glob(os.path.join(R14, 'C*_census', 'EVIDENCE',
                                    'classification_trace.tsv')):
        L = io.open(f, encoding='utf-8-sig').read().splitlines()
        h = L[0].split('\t')
        for l in L[1:]:
            c = l.split('\t')
            if len(c) < len(h):
                continue
            d = dict(zip(h, c))
            try:
                a = '%08X' % int(d['entry'])
            except (ValueError, KeyError):
                continue
            tr.setdefault(a, d)
    return tr


def rd(p):
    L = io.open(os.path.join(HERE, p), encoding='utf-8-sig').read().splitlines()
    h = L[0].split('\t')
    return [dict(zip(h, l.split('\t'))) for l in L[1:]]


def trace_class(name):
    """`BulletClass::Draw` / `BuildingClass::slot82` / `T_X_Y__::slot2` → 类名。"""
    if '::' not in name:
        return None
    return name.rsplit('::', 1)[0]


def main():
    P = load_p802()
    tr = load_trace()
    img = P.Image(EXE)
    rows = rd('scan_F4_census_no_ring4.tsv')
    v1 = [r for r in rows if r['V1'] == 'y']
    print('census gap rows %d ; V1 rows %d' % (len(rows), len(v1)))

    out = []
    for r in v1:
        e = int(r['entry'], 16)
        t = tr.get(r['entry'], {})
        tname = t.get('name', '')
        tsrc = t.get('source', '?')
        tcls = trace_class(tname) or ''
        # 该 entry 命中的所有虚表 + COL 类名
        cols, slots, vts = [], [], []
        for hit in P.scan_dd(img, e):
            ws = P.vtable_start(img, hit)
            if ws is None:
                continue
            v, c = ws
            vts.append(v)
            slots.append((hit - v) // 4)
            cols.append(c['name'])
        # 相容：trace 类名 vs 任一 COL 名
        m = [P.col_name_match(tcls, cn) for cn in cols] if cols else []
        same = 'match' if 'match' in m else ('nomatch' if m else 'none')
        out.append(dict(entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
                        trace_name=tname, trace_source=tsrc, trace_class=tcls,
                        vt_count=len(vts), cols=';'.join(cols[:3]),
                        slots=','.join(str(s) for s in sorted(set(slots)))[:40],
                        same_table=same, verdict=r['verdict'],
                        install_site=r['install_site'],
                        sem_unproved=r['sem_unproved']))

    path = os.path.join(HERE, 'check_col.tsv')
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('entry\tsubsystem\tname\ttrace_name\ttrace_source\ttrace_class\t'
                 'vt_count\tcol_names\tslots\tsame_table\tverdict\tinstall_site\t'
                 'sem_unproved\n')
        for r in out:
            fh.write('%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                r['entry'], r['subsystem'], r['name'], r['trace_name'],
                r['trace_source'], r['trace_class'], r['vt_count'], r['cols'],
                r['slots'], r['same_table'], r['verdict'], r['install_site'],
                r['sem_unproved']))

    agg = dict(
        n=len(out),
        same_table=sum(1 for r in out if r['same_table'] == 'match'),
        diff_table=sum(1 for r in out if r['same_table'] == 'nomatch'),
        no_col=sum(1 for r in out if r['same_table'] == 'none'),
        yes_rows=sum(1 for r in out if r['verdict'] == 'yes'),
        yes_and_diff=sum(1 for r in out if r['verdict'] == 'yes'
                         and r['same_table'] == 'nomatch'),
        yes_and_same=sum(1 for r in out if r['verdict'] == 'yes'
                         and r['same_table'] == 'match'),
        diff_and_sem_clean=sum(1 for r in out if r['same_table'] == 'nomatch'
                               and r['sem_unproved'] == '0'),
        diff_entries=[r['entry'] for r in out if r['same_table'] == 'nomatch'],
        file='check_col.tsv',
    )
    print('[col] 同表(② 就是该表) %d / 异表 %d / 无 COL %d'
          % (agg['same_table'], agg['diff_table'], agg['no_col']))
    print('[col] yes 49 里：同表 %d / 异表 %d'
          % (agg['yes_and_same'], agg['yes_and_diff']))
    print('[col] 异表行:', ', '.join(agg['diff_entries'][:20]) or '-')
    with io.open(os.path.join(HERE, 'check_col.json'), 'w', encoding='utf-8') as fh:
        json.dump(agg, fh, ensure_ascii=False, indent=1)
    return agg


if __name__ == '__main__':
    main()
