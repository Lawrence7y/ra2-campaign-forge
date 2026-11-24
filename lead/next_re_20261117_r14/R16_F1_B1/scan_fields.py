# -*- coding: utf-8 -*-
"""
R16_F1_B1 — 只读取数：从 gamemd.exe 独立解出 18 行的 vt/COL/RTTI/装表点/函数体。

复用 PROBE_802/probe.py 的已验证函数（Image / TextScan / vtable_start / col_of /
scan_dd / load_atlas_sizes / body_ranges / which_body / col_name_match）。
输入：derived_set.tsv（本目录，entry 升序 76 行的前 18）。
只读打开 gamemd.exe；不写 coverage/PANEL/其它目录；只写本目录 scan_raw.json。
"""
import os, sys, json, re
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
SRC = os.path.join(HERE, 'derived_set.tsv')
OUT = os.path.join(HERE, 'scan_raw.json')


def slot_from_name(name):
    m = re.search(r'v?slot(\d+)', name, re.I)
    return int(m.group(1)) if m else None


def cls_from_name(name):
    if '::' not in name:
        return name
    return name.split('::')[0]


def main():
    sha = probe.sha256(EXE)
    assert sha == probe.EXPECT_SHA, 'binary sha mismatch: %s' % sha
    print('sha256 ok:', sha)

    # 本批 18 行
    with open(SRC, encoding='utf-8') as f:
        lines = f.read().splitlines()
    rows = []
    for ln in lines[1:19]:  # 前 18 数据行
        c = ln.split('\t')
        rows.append(dict(entry=c[0].upper(), subsystem=c[1], name=c[2],
                         audit_dir=c[3], ring4_at=c[4]))
    assert len(rows) == 18 and len(set(r['entry'] for r in rows)) == 18
    print('batch rows:', len(rows))

    # coverage 原始 name（delta 第 3 列要用 coverage 的原文）
    with open(COV, 'rb') as f:
        raw = f.read()
    cov = {}
    for ln in raw.split(b'\n'):
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)

    atlas_sizes = probe.load_atlas_sizes()
    img = probe.Image(EXE)
    ts = probe.TextScan(img)
    ranges = probe.body_ranges(atlas_sizes)
    bad = [(k, ts.direct.get(int(k, 16), 0), v) for k, v in probe.ANCHORS.items()
           if ts.direct.get(int(k, 16), 0) != v]
    print('method anchors:', 'OK' if not bad else 'MISMATCH %s' % bad)
    print('.text insns %d (skip %d)' % (ts.n_insn, ts.n_skip))

    out = dict(sha=sha, anchors_ok=(not bad),
               anchor_detail={k: ts.direct.get(int(k, 16), 0) for k in probe.ANCHORS},
               rows=[])
    for r in rows:
        e = int(r['entry'], 16)
        want_slot = slot_from_name(r['name'])
        name_cls = cls_from_name(r['name'])
        covrow = cov.get(r['entry'])
        cov_name = covrow[2].decode('utf-8', 'replace') if covrow else None
        entry_body_size = atlas_sizes.get(r['entry'])
        entry_body = (e, e + entry_body_size) if entry_body_size else None

        cands = []
        for hit in probe.scan_dd(img, e):
            w = probe.vtable_start(img, hit)
            if w is None:
                cands.append(dict(hit='%08X' % hit, sec=img.sec_of(hit),
                                  vt=None, slot=None, col=None, off=None,
                                  td=None, mangled=None, sites=[]))
                continue
            v, ci = w
            slot = (hit - v) // 4
            off = img.u32(ci['col'] + 4)
            # 装表点：imm32 == vt 的 mov [reg+disp],imm32，含每个点的体内外判定
            sites = []
            for site_va, disp in ts.installs_of(v):
                inside = bool(entry_body and entry_body[0] <= site_va < entry_body[1])
                func = probe.which_body(ranges, site_va)
                sites.append(dict(site='%08X' % site_va, disp=disp,
                                  inside_entry=inside,
                                  func=('%08X' % func if func is not None else None)))
            cands.append(dict(hit='%08X' % hit, sec=img.sec_of(hit),
                              vt='%08X' % v, slot=slot, col='%08X' % ci['col'],
                              off=off, td='%08X' % ci['td'], mangled=ci['name'],
                              cls_match=probe.col_name_match(name_cls, ci['name']),
                              sites=sites))

        out['rows'].append(dict(
            entry=r['entry'], subsystem=r['subsystem'], name=r['name'],
            cov_name=cov_name, audit_dir=r['audit_dir'], ring4_at=r['ring4_at'],
            want_slot=want_slot, name_cls=name_cls,
            entry_body_size=entry_body_size,
            entry_body=('%08X-%08X' % entry_body if entry_body else None),
            candidates=cands))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote', OUT)

    # 摘要
    for row in out['rows']:
        print('\n%s %-40s cov_name=%-40s want_slot=%s body=%s' % (
            row['entry'], row['name'], row['cov_name'], row['want_slot'], row['entry_body']))
        print('  ring4_at:', row['ring4_at'][:110])
        for c in row['candidates']:
            if c['vt'] is None:
                print('  hit %s sec=%s : NO vt' % (c['hit'], c['sec']))
            else:
                out_sites = [s['site'] + ('@' + s['func'] if s['func'] else '') for s in c['sites'] if not s['inside_entry']]
                in_sites = [s['site'] for s in c['sites'] if s['inside_entry']]
                print('  hit %s -> vt=%s slot=%s col=%s off=%s td=%s mg=%s cls=%s' % (
                    c['hit'], c['vt'], c['slot'], c['col'], c['off'], c['td'],
                    c['mangled'], c['cls_match']))
                print('     OUT sites:', ','.join(out_sites) or '-', ' IN sites:', ','.join(in_sites) or '-')
    return 0


if __name__ == '__main__':
    sys.exit(main())
