# -*- coding: utf-8 -*-
"""
R16-F1-OTHER14 — 独立复核（verify_delta 角色）。

不读 scan_raw.json 的结论，重新只读打开 coverage.tsv / gamemd.exe：
  A. delta.tsv 8 列 × 14 行；entry 集 == 卡面 14 行；
     第 1/2/3/5/6/7/8 列与现盘 coverage 逐字节相同；第 4 列严格以原第 4 列为前缀；
     grade 列逐字节 == [已证]；追加文本含 §12.6 且不含 §12.4。
  B. fields.tsv 12 列；category/form/same_source_judged/pre_has_ring4/status 取值合法；
     OK 行数 == delta 行数。
  C. 回二进制重算：slot 6 项 + direct 4 项（复用 scan.py 的 key_addrs 解析，但重新读盘）。
  D. coverage.tsv / gamemd.exe sha256 与 scan/gen 一致。
只写本目录 verify_delta.json。
"""
import os, sys, json, re, hashlib
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
OTHER14 = os.path.join(R14, 'R16_PROBE_F1_PIVOT', 'other14.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')
RAW = os.path.join(HERE, 'scan_raw.json')
OUT = os.path.join(HERE, 'verify_delta.json')

EXPECT = ['0040BC10', '0040F8F0', '0040FEC0', '00422CA0', '0046B910',
          '0048AFD0', '0048B020', '004AF540', '004B5AB0', '0054EBA0',
          '0062B380', '0065BED0', '0065C200', '0075E510']


def sha256p(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def cov_map():
    c = {}
    for ln in open(COV, 'rb').read().split(b'\n'):
        if not ln:
            continue
        x = ln.split(b'\t')
        if len(x) == 8:
            try:
                c[x[0].decode('ascii').upper()] = x
            except Exception:
                pass
    return c


def tsv_rows(path, ncol):
    out = []
    with open(path, encoding='utf-8') as f:
        hdr = f.readline().rstrip('\r\n').split('\t')
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            out.append(c)
    return hdr, out


def main():
    raw = json.load(open(RAW, encoding='utf-8'))
    cov = cov_map()
    cov_sha = sha256p(COV)
    exe_sha = sha256p(EXE)
    errors = []

    if cov_sha != raw['cov_sha_before'] or cov_sha != raw['cov_sha_after']:
        errors.append('coverage.tsv sha changed since scan/gen: %s' % cov_sha)
    if exe_sha != raw['exe_sha']:
        errors.append('gamemd.exe sha changed: %s' % exe_sha)

    dh, dr = tsv_rows(DELTA, 8)
    if len(dh) != 8 or dh != ['entry', 'subsystem', 'name', 'one_line_semantics',
                              'grade', 'evidence_path', 'n_sources', 'conflict']:
        errors.append('delta header wrong: %r' % dh)
    if len(dr) != 14:
        errors.append('delta row count %d != 14' % len(dr))
    entries = [r[0] for r in dr]
    if set(entries) != set(EXPECT) or len(set(entries)) != 14:
        errors.append('delta entry set mismatch: %r' % entries)

    for r in dr:
        if len(r) != 8:
            errors.append('%s delta row has %d cols' % (r[0], len(r)))
            continue
        e = r[0]
        orig = cov.get(e)
        if orig is None:
            errors.append('%s not in coverage' % e)
            continue
        for i in (0, 1, 2, 4, 5, 6, 7):
            if r[i].encode('utf-8') != orig[i]:
                errors.append('%s col %d byte mismatch: delta=%r cov=%r'
                              % (e, i + 1, r[i], orig[i].decode('utf-8', 'replace')))
        if not r[3].encode('utf-8').startswith(orig[3]):
            errors.append('%s col4 not strict prefix' % e)
        if r[4] != '[已证]':
            errors.append('%s grade changed: %r' % (e, r[4]))
        added = r[3][len(orig[3].decode('utf-8', 'replace')):]
        if '§12.6' not in added:
            errors.append('%s added text missing §12.6' % e)
        if '§12.4' in added:
            errors.append('%s added text has §12.4' % e)
        if r[0].startswith('004AF') is False and r[0].startswith('004B5') is False:
            if '④ 活表槽位见证' not in added:
                errors.append('%s slot row missing 活表槽位见证' % e)
        else:
            if 'direct call' not in added:
                errors.append('%s direct row missing direct call form' % e)

    fh, fr = tsv_rows(FIELDS, 12)
    if len(fh) != 12:
        errors.append('fields header has %d cols != 12' % len(fh))
    if len(fr) != 14:
        errors.append('fields row count %d != 14' % len(fr))
    n_ok = 0
    allowed_cat = {'sem_virtual_witness_only', 'sem_live_table_install'}
    allowed_form = {'direct_call', 'slot_witness'}
    for c in fr:
        if len(c) != 12:
            errors.append('fields row %s has %d cols' % (c[0] if c else '?', len(c)))
            continue
        if c[3] not in allowed_cat:
            errors.append('%s bad category %s' % (c[0], c[3]))
        if c[4] not in allowed_form:
            errors.append('%s bad form %s' % (c[0], c[4]))
        if c[7] not in ('yes', 'no'):
            errors.append('%s bad same_source_judged %s' % (c[0], c[7]))
        if c[9] not in ('是', '否'):
            errors.append('%s bad pre_has_ring4 %s' % (c[0], c[9]))
        if c[10] not in ('OK', 'SKIP'):
            errors.append('%s bad status %s' % (c[0], c[10]))
        if c[10] == 'OK':
            n_ok += 1
    if n_ok != len(dr):
        errors.append('fields OK %d != delta rows %d' % (n_ok, len(dr)))

    # C. 回二进制重算（用 scan.py 记录的关键地址，逐行回 exe 核）
    img = probe.Image(EXE)
    ts = probe.TextScan(img)
    atlas = probe.load_atlas_sizes()
    ranges = probe.body_ranges(atlas)
    by_entry = {r['entry']: r for r in raw['rows']}
    bin_ok = 0
    for e in EXPECT:
        r = by_entry[e]
        if r['form'] == 'slot_witness':
            vt = int(r['vt'], 16)
            si = r['slot_idx']
            # c6: 体外 mov [dest],imm32==vt 装表点存在（独立重算，不读 scan 的 site_recs）
            import capstone
            md6 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md6.detail = True
            c6_ok = False
            for sva, _disp in ts.installs_of(vt):
                body6 = probe.which_body(ranges, sva)
                so6 = sva - img.base
                ins6 = next(md6.disasm(bytes(img.buf[so6:so6 + 12]), sva), None)
                imm6 = (ins6.operands[1].imm & 0xFFFFFFFF) if (
                    ins6 and ins6.mnemonic == 'mov' and len(ins6.operands) == 2
                    and ins6.operands[1].type == capstone.x86.X86_OP_IMM) else None
                if imm6 == vt and body6 != int(e, 16):
                    c6_ok = True
                    break
            checks = {
                'c1': img.u32(vt + si * 4) == int(e, 16),
                'c2': img.u32(vt - 4) == int(r['col'], 16),
                'c3': img.u32(int(r['col'], 16) + 4) == r['off'],
                'c4': img.u32(int(r['col'], 16) + 12) == int(r['td'], 16),
                'c5': img.cstr(int(r['td'], 16) + 8, 256) == r['mangled'],
                'c6': c6_ok,
            }
            if all(checks.values()):
                bin_ok += 1
            else:
                errors.append('%s binary recheck fail %r' % (e, checks))
        else:
            site = int(r['site'], 16)
            so = site - img.base
            raw5 = bytes(img.buf[so:so + 5])
            import capstone
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.detail = True
            ins = next(md.disasm(bytes(img.buf[so:so + 8]), site), None)
            tgt = (ins.operands[0].imm & 0xFFFFFFFF) if (
                ins and ins.mnemonic == 'call' and ins.operands
                and ins.operands[0].type == capstone.x86.X86_OP_IMM) else None
            rel = int.from_bytes(raw5[1:5], 'little', signed=True)
            checks = {
                'd1': raw5[0] == 0xE8,
                'd2': site + 5 + rel == int(e, 16),
                'd3': tgt == int(e, 16),
                'd4': (probe.which_body(ranges, site) not in (None, int(e, 16))),
            }
            if all(checks.values()):
                bin_ok += 1
            else:
                errors.append('%s binary recheck fail %r' % (e, checks))

    # 行行不同自检（entry 归一后）
    added_texts = []
    for r in dr:
        e = r[0]
        orig = cov[e][3].decode('utf-8', 'replace')
        added_texts.append(r[3][len(orig):])
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for t in added_texts]
    n_full, n_norm = len(set(added_texts)), len(set(norm))

    res = dict(cov_sha=cov_sha, exe_sha=exe_sha,
               cov_bytes=os.path.getsize(COV), exe_bytes=os.path.getsize(EXE),
               delta_rows=len(dr), fields_rows=len(fr), fields_ok=n_ok,
               bin_ok=bin_ok, bin_total=len(EXPECT),
               n_distinct_full=n_full, n_distinct_norm=n_norm,
               errors=errors, passed=(not errors and n_full == 14 and n_norm == 14
                                      and bin_ok == 14))
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('cov sha', cov_sha, 'exe sha', exe_sha)
    print('delta rows', len(dr), 'fields rows', len(fr), 'fields OK', n_ok)
    print('binary recheck', bin_ok, '/', len(EXPECT))
    print('distinct full/normalized:', n_full, '/', n_norm)
    print('ERRORS:', errors if errors else 'none')
    print('PASSED:', res['passed'])
    return 0 if res['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
