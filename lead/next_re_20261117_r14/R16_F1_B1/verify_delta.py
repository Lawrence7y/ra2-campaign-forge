# -*- coding: utf-8 -*-
"""
R16_F1_B1 — 独立复核 delta.tsv / fields.tsv（只读 coverage / gamemd；只写本目录 print）。

复核：
  A. delta 8 列；entry 集 == 18 行；col1/2/3/5/6/7/8 与当前盘上 coverage 逐字节相同
  B. col4 严格以当前 coverage 原 col4 字节为前缀；grade == [已证]
  C. 每行 ④ 含 '④ 活表槽位见证'、含 §12.6、不含 §12.4
  D. 6 项字节复核（回 gamemd.exe 独立再算）+ 类一致 + 体外 + imm==vt
  E. 行行不同（全文 + entry 归一）
BAD=0 才算通过。
"""
import os, sys, json, re, hashlib
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')
VJSON = os.path.join(HERE, 'verify_summary.json')


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_sha = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    print('coverage NOW sha:', cov_sha, 'bytes:', cov_bytes)
    with open(VJSON, encoding='utf-8') as f:
        vj = json.load(f)
    print('coverage gen sha:', vj['cov_before'], 'bytes:', vj['cov_bytes'],
          'MATCH NOW:', cov_sha == vj['cov_before'] and cov_bytes == vj['cov_bytes'])

    with open(COV, 'rb') as f:
        cov = {}
        for ln in f.read().split(b'\n'):
            if not ln:
                continue
            c = ln.split(b'\t')
            if len(c) == 8:
                try:
                    e = c[0].decode('ascii').upper()
                except Exception:
                    continue
                cov.setdefault(e, c)

    # delta bytes
    with open(DELTA, 'rb') as f:
        dlines = f.read().split(b'\n')
    dhdr = dlines[0].decode('utf-8').rstrip('\r')
    assert dhdr == 'entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tn_sources\tconflict'
    drows = [ln for ln in dlines[1:] if ln]
    print('delta rows:', len(drows))
    BAD = []

    texts = []
    for ln in drows:
        c = ln.split(b'\t')
        if len(c) != 8:
            BAD.append(('colcount', ln[:40], len(c)))
            continue
        e = c[0].decode('ascii').upper()
        orig = cov.get(e)
        if orig is None:
            BAD.append(('entry-not-in-cov', e))
            continue
        # A: byte-identical cols
        for i in (0, 1, 2, 4, 5, 6, 7):
            if c[i] != orig[i]:
                BAD.append(('col%d-diff' % (i + 1), e))
        # B: prefix + grade
        if not c[3].startswith(orig[3]):
            BAD.append(('col4-not-prefix', e))
        if c[4] != '[已证]'.encode('utf-8'):
            BAD.append(('grade', e, c[4]))
        # C: ④ / §
        sem = c[3].decode('utf-8', 'replace')
        if '④ 活表槽位见证' not in sem:
            BAD.append(('no-witness', e))
        if '§12.6' not in sem:
            BAD.append(('no-12.6', e))
        if '§12.4' in sem:
            BAD.append(('has-12.4', e))
        texts.append(sem)

    # fields entry set == delta entry set
    with open(FIELDS, encoding='utf-8') as f:
        fl = f.read().splitlines()
    fhdr = fl[0]
    assert fhdr == ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                    'col_offset\trtti_addr\trtti_mangled\tinstall_site\tinstall_func\t'
                    'status(OK|SKIP)\tsame_source\tnote'), fhdr
    fent = [ln.split('\t')[0].upper() for ln in fl[1:] if ln]
    dent = [ln.split(b'\t')[0].decode('ascii').upper() for ln in drows]
    if set(fent) != set(dent) or len(fent) != len(dent):
        BAD.append(('fields-delta-entry-mismatch',))
    if any(ln.split('\t')[11] != 'OK' for ln in fl[1:] if ln):
        BAD.append(('fields-status-not-OK',))
    if any(ln.split('\t')[12] != 'no' for ln in fl[1:] if ln):
        BAD.append(('fields-same_source-not-no',))

    # D: independent byte checks (reuse fields values, re-read binary)
    import capstone
    img = probe.Image(EXE)
    n6 = 0
    for ln in fl[1:]:
        if not ln:
            continue
        c = ln.split('\t')
        e, slot, vt, col, off, td, mg, site = (
            c[0].upper(), int(c[2]), int(c[3], 16), int(c[5], 16),
            int(c[6]), int(c[7], 16), c[8], int(c[9], 16))
        ei = int(e, 16)
        c1 = img.u32(vt + slot * 4) == ei
        c2 = img.u32(vt - 4) == col
        c3 = img.u32(col + 4) == off
        c4 = img.u32(col + 12) == td
        c5 = img.cstr(td + 8, 256) == mg
        code = bytes(img.buf[site - img.base:site - img.base + 12])
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        ins = next(md.disasm(code, site))
        imm = (ins.operands[1].imm & 0xFFFFFFFF
               if ins.mnemonic == 'mov' and len(ins.operands) == 2
               and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
        c6 = imm == vt
        if not all([c1, c2, c3, c4, c5, c6]):
            BAD.append(('byte6', e, c1, c2, c3, c4, c5, c6))
        else:
            n6 += 1
    print('byte6 all-True rows:', n6, '/', len(fent))

    # E: uniqueness on appended ④ (extract after '；④ 活表')
    app = [t.split('；④ 活表', 1)[1] if '；④ 活表' in t else t for t in texts]
    print('distinct appended ④ full:', len(set(app)), '/', len(app))
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for t in app]
    print('distinct appended ④ entry-normalized:', len(set(norm)), '/', len(norm))
    if len(set(app)) != len(app) or len(set(norm)) != len(norm):
        BAD.append(('uniqueness',))

    print('\nBAD count:', len(BAD))
    for b in BAD:
        print(' ', b)
    print('RESULT:', 'PASS' if not BAD else 'FAIL')
    return 0 if not BAD else 1


if __name__ == '__main__':
    sys.exit(main())
