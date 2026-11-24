# -*- coding: utf-8 -*-
"""
R16_F1_B4 — 只读取数/探查脚本（B4，派生集合第 55-72 行）。

复用 PROBE_802/probe.py 的已验证取数函数，对每行：
  - 解析 ring4_at / reason prose 中的装表点候选
  - dd entry -> vtable_start -> 候选 (vt, slot, col, offset, td, mangled)
  - TextScan.installs_of(vt) 给出该表的全部装表点（imm32==vt by construction）
  - 用 '装表点命中 ring4_at' + 'slot==行名 slot（若有）' + 'RTTI 类一致' 选表
  - 输出全部候选供人工判读；不写 fields/delta，只写本目录 scan_raw.json

只读 gamemd.exe；只写本目录。
"""
import os
import sys
import re
import json

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)

import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
OUT = os.path.join(HERE, 'scan_raw.json')

# B4 18 行 entry（由 derive_set.py 升序第 55-72 行得到）
B4_ENTRIES = [
    '006E6470',
    '0071CDA0', '0071E1D0', '0071F8C0', '0071F930', '0071FA80',
    '007220A0', '007220D0',
    '00726860', '007268D0', '00726950', '00727BF0', '00727C80',
    '007281A0',
    '00749F30', '0074BA30',
    '0075E0C0', '0075E2C0',
]

HEXTOK = re.compile(r'(?<![0-9A-Za-z])([0-9A-Fa-f]{6,8})(?![0-9A-Za-z])')


def site_tokens(text):
    """从 ring4_at prose 抽出 6-8 位十六进制 token（装表点/函数/立即数都抽出来）。"""
    return [t.upper().zfill(8) for t in HEXTOK.findall(text)]


def main():
    sha = probe.sha256(EXE)
    assert sha == probe.EXPECT_SHA, 'binary sha mismatch: %s' % sha
    print('sha256 ok:', sha)

    with open(AUDIT, encoding='utf-8') as f:
        lines = f.read().splitlines()
    hdr = lines[0].split('\t')
    idx = {k: i for i, k in enumerate(hdr)}
    audit = {}
    for ln in lines[1:]:
        c = ln.split('\t')
        if len(c) < len(hdr):
            continue
        audit[c[idx['entry']].upper()] = {k: c[idx[k]] for k in hdr}

    atlas_sizes = probe.load_atlas_sizes()
    img = probe.Image(EXE)
    ts = probe.TextScan(img)
    ranges = probe.body_ranges(atlas_sizes)

    bad = [(k, ts.direct.get(int(k, 16), 0), v) for k, v in probe.ANCHORS.items()
           if ts.direct.get(int(k, 16), 0) != v]
    print('method anchors:', 'OK' if not bad else 'MISMATCH %s' % bad)
    print('.text insns %d (skip %d)' % (ts.n_insn, ts.n_skip))

    out = dict(sha=sha, anchors_ok=(not bad), rows=[])

    for entry in B4_ENTRIES:
        a = audit[entry]
        e = int(entry, 16)
        name = a['name']
        name_slot = probe.slot_from_name(name)
        name_cls = probe.class_from_name(name)
        ring = a['ring4_at']
        toks = site_tokens(ring)

        cands = []
        for hit in probe.scan_dd(img, e):
            w = probe.vtable_start(img, hit)
            if w is None:
                cands.append(dict(hit='%08X' % hit, vt=None, slot=None,
                                  col=None, col_offset=None, td=None,
                                  mangled=None, sites=[], sec_hit=img.sec_of(hit)))
                continue
            v, colinfo = w
            slot = (hit - v) // 4
            col_offset = img.u32(colinfo['col'] + 4)
            sites = ['%08X' % s for s, _d in ts.installs_of(v)]
            cands.append(dict(hit='%08X' % hit, vt='%08X' % v, slot=slot,
                              col='%08X' % colinfo['col'],
                              col_offset=col_offset,
                              td='%08X' % colinfo['td'],
                              mangled=colinfo['name'],
                              sec_vt=img.sec_of(v),
                              sites=sites,
                              cls_match=probe.col_name_match(name_cls, colinfo['name'])))

        # 哪些 ring token 命中了某个候选表的 install sites
        all_sites = set(s for c in cands for s in c['sites'])
        site_hits = [t for t in toks if t in all_sites]
        # 哪些 ring token 解码后 imm32 命中某个候选 vt
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        tok_imm = []
        for t in toks:
            va = int(t, 16)
            off = va - img.base
            if off < 0 or off + 12 > len(img.buf):
                continue
            code = bytes(img.buf[off:off + 12])
            try:
                ins = next(md.disasm(code, va))
            except StopIteration:
                continue
            if (ins.mnemonic == 'mov' and len(ins.operands) == 2
                    and ins.operands[0].type == capstone.x86.X86_OP_MEM
                    and ins.operands[1].type == capstone.x86.X86_OP_IMM):
                imm = ins.operands[1].imm & 0xFFFFFFFF
                if imm in [int(c['vt'], 16) for c in cands if c['vt']]:
                    tok_imm.append((t, '%08X' % imm, ins.op_str))

        row = dict(entry=entry, name=name, subsystem=a['subsystem'],
                   f_reason=a['f_reason'], ring4_at=ring,
                   audit_verdict=a['audit_verdict'], same_source=a['same_source'],
                   n_install_decoded=a['n_install_decoded'],
                   n_install_outside=a['n_install_outside_body'],
                   n_install_inside=a['n_install_inside_body'],
                   name_slot=name_slot, name_cls=name_cls,
                   ring_sites=site_hits, tok_imm=tok_imm,
                   candidates=cands)
        out['rows'].append(row)

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote', OUT)

    for row in out['rows']:
        print('\n=== %s  %s  slot=%s cls=%s ===' % (
            row['entry'], row['name'], row['name_slot'], row['name_cls']))
        print('  ring4_at:', row['ring4_at'])
        print('  ring_sites(hit install):', row['ring_sites'])
        print('  tok_imm(mov->vt):', row['tok_imm'])
        for i, c in enumerate(row['candidates']):
            if c['vt'] is None:
                print('  cand%d hit=%s NO-VT sec=%s' % (i, c['hit'], c['sec_hit']))
            else:
                print('  cand%d hit=%s vt=%s slot=%s col=%s off=%s td=%s mg=%s cls=%s sites=%s' % (
                    i, c['hit'], c['vt'], c['slot'], c['col'], c['col_offset'],
                    c['td'], c['mangled'], c['cls_match'], c['sites']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
