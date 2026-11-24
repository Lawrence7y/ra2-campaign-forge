# -*- coding: utf-8 -*-
"""
R16_SLOTN_B1 — 只读取数脚本（批次 1，数据行 1..15 of slotN43.tsv）。

复用 PROBE_802/probe.py 的已验证取数函数：Image / TextScan / vtable_start /
col_of / scan_dd / load_atlas_sizes / body_ranges / which_body。

只读打开 ra2youli\\gamemd.exe；只写本目录 scan_raw.json。
不写 coverage.tsv / PANEL / R14_COMMON / 台账 / 其它卡目录。
"""
import os
import sys
import json

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)

import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
SLOTN = os.path.join(PROBE, 'slotN43.tsv')
WORKSCAN = os.path.join(PROBE, 'work_scan.json')
OUT = os.path.join(HERE, 'scan_raw.json')


def main():
    sha = probe.sha256(EXE)
    assert sha == probe.EXPECT_SHA, 'binary sha mismatch: %s' % sha
    print('sha256 ok:', sha)

    # 读本批 15 行（数据行 1..15）
    with open(SLOTN, encoding='utf-8') as f:
        lines = f.read().splitlines()
    data = lines[1:]
    assert len(data) == 43, 'slotN43 data rows != 43'
    batch = []
    for i, ln in enumerate(data[:15], 1):
        c = ln.split('\t')
        assert len(c) == 9, 'row %d col count %d' % (i, len(c))
        batch.append(dict(row=i, entry=c[0], subsystem=c[1], name=c[2],
                          vt_count=int(c[3]), slot_no=c[4], col_ok=c[5],
                          install_ext=c[6], ring4_ok=c[7], reason=c[8]))
    # 前置核对
    ents = [r['entry'] for r in batch]
    assert len(set(ents)) == 15, 'entries not distinct'
    assert all(r['col_ok'] == 'match' for r in batch), 'col_ok != match'
    assert all(r['install_ext'] == 'y' for r in batch), 'install_ext != y'

    with open(WORKSCAN, encoding='utf-8') as f:
        ws = json.load(f)
    site_of = ws['A_agg']['site_of']

    atlas_sizes = probe.load_atlas_sizes()
    img = probe.Image(EXE)
    ts = probe.TextScan(img)
    ranges = probe.body_ranges(atlas_sizes)

    # 方法保真度锚点自检（与 probe.py 一致）
    bad = [(k, ts.direct.get(int(k, 16), 0), v) for k, v in probe.ANCHORS.items()
           if ts.direct.get(int(k, 16), 0) != v]
    print('method anchors:', 'OK' if not bad else 'MISMATCH %s' % bad)
    print('.text insns %d (skip %d)' % (ts.n_insn, ts.n_skip))

    out = dict(sha=sha, anchors_ok=(not bad),
               anchor_detail={k: ts.direct.get(int(k, 16), 0) for k in probe.ANCHORS},
               rows=[])

    for r in batch:
        e = int(r['entry'], 16)
        want_slot = int(r['slot_no'])
        ws_site = site_of.get(r['entry'])

        # dd 命中 (.rdata/.data) -> vtable_start -> COL 明细
        cands = []
        for hit in probe.scan_dd(img, e):
            w = probe.vtable_start(img, hit)
            if w is None:
                cands.append(dict(hit='%08X' % hit, vt=None, slot=None,
                                  col=None, col_offset=None, td=None,
                                  mangled=None, sec_hit=img.sec_of(hit)))
                continue
            v, c = w
            slot = (hit - v) // 4
            col_offset = img.u32(c['col'] + 4)  # offset = u32(COL+4)，与 91 行先例一致
            sites = ['%08X' % s for s, _d in ts.installs_of(v)]
            cands.append(dict(hit='%08X' % hit, vt='%08X' % v, slot=slot,
                              col='%08X' % c['col'],
                              col_offset=col_offset,
                              td='%08X' % c['td'],
                              mangled=c['name'],
                              sec_vt=img.sec_of(v),
                              sites=sites))

        # 选候选：slot==want_slot 且 install sites 含 ws_site（装表点体外）
        chosen = None
        for c in cands:
            if c['vt'] is None:
                continue
            if c['slot'] != want_slot:
                continue
            if ws_site and ws_site in c['sites']:
                chosen = c
                break
        # 退回：只看 slot==want_slot（site 不在该 vt，则记 note）
        fallback = None
        if chosen is None:
            for c in cands:
                if c['vt'] is not None and c['slot'] == want_slot:
                    fallback = c
                    break

        site = ws_site
        func = probe.which_body(ranges, int(site, 16)) if site else None
        func_s = '%08X' % func if func is not None else None

        out['rows'].append(dict(
            row=r['row'], entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
            vt_count=r['vt_count'], slot_no=r['slot_no'], col_ok=r['col_ok'],
            install_ext=r['install_ext'], site=site, func=func_s,
            chosen=chosen, fallback=fallback, candidates=cands,
        ))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote', OUT)

    # 摘要打印
    for row in out['rows']:
        ch = row['chosen'] or row['fallback']
        status = 'OK' if row['chosen'] else ('FALLBACK' if row['fallback'] else 'NONE')
        if ch:
            print('%2d %s %-46s %-8s vt=%s slot=%s col=%s off=%s td=%s mg=%-40s site=%s func=%s' % (
                row['row'], row['entry'], row['name'][:46], status,
                ch['vt'], ch['slot'], ch['col'], ch['col_offset'], ch['td'],
                ch['mangled'], row['site'], row['func']))
        else:
            print('%2d %s %-46s %-8s NO VT CANDIDATE site=%s func=%s' % (
                row['row'], row['entry'], row['name'][:46], status,
                row['site'], row['func']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
