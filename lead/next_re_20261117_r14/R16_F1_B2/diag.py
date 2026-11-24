# -*- coding: utf-8 -*-
"""
R16_F1_B2 — 只读诊断：为每个装表点求宿主函数体（atlas），并核装表点在 entry 体外。
同时验证 6 项字节复核。只写本目录 diag.json。
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
SCAN = os.path.join(HERE, 'scan_raw.json')
OUT = os.path.join(HERE, 'diag.json')


def main():
    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    atlas = probe.load_atlas_sizes()
    img = probe.Image(EXE)
    ranges = probe.body_ranges(atlas)
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True

    out = []
    for r in scan['rows']:
        entry = r['entry']
        e = int(entry, 16)
        # 选 site：ring_sites 中命中该行唯一候选 vt 的 install site（取第一个）
        chosen_c = None
        for c in r['candidates']:
            if c['vt'] and c['slot'] == r['name_slot'] and c['cls_match'] == 'match':
                if any(s in c['sites'] for s in r['ring_sites']):
                    chosen_c = c
                    break
        if chosen_c is None:
            # 退回：slot+cls 匹配即可
            for c in r['candidates']:
                if c['vt'] and c['slot'] == r['name_slot'] and c['cls_match'] == 'match':
                    chosen_c = c
                    break
        site = next((s for s in r['ring_sites'] if s in chosen_c['sites']), None)
        site_int = int(site, 16)
        func = probe.which_body(ranges, site_int)
        func_s = '%08X' % func if func is not None else None

        # entry body（atlas）
        esize = atlas.get(entry)
        ebody = (e, e + esize) if esize else None
        outside = not (ebody and ebody[0] <= site_int < ebody[1])
        # 6 项字节复核
        vt = int(chosen_c['vt'], 16)
        slot = int(chosen_c['slot'])
        col = int(chosen_c['col'], 16)
        off = int(chosen_c['col_offset'])
        td = int(chosen_c['td'], 16)
        mg = chosen_c['mangled']
        c1 = img.u32(vt + slot * 4) == e
        c2 = img.u32(vt - 4) == col
        c3 = img.u32(col + 4) == off
        c4 = img.u32(col + 12) == td
        c5 = img.cstr(td + 8, 256) == mg
        code = bytes(img.buf[site_int - img.base:site_int - img.base + 12])
        ins = next(md.disasm(code, site_int))
        imm = (ins.operands[1].imm & 0xFFFFFFFF
               if ins.mnemonic == 'mov' and len(ins.operands) == 2
               and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
        c6 = imm == vt
        clsmatch = probe.col_name_match(r['name_cls'], mg) == 'match'

        out.append(dict(entry=entry, name=r['name'], slot=slot,
                        vt='%08X' % vt, col='%08X' % col, off=off,
                        td='%08X' % td, mg=mg, site=site, func=func_s,
                        entry_size=esize, outside=outside,
                        checks=[c1, c2, c3, c4, c5, c6], clsmatch=clsmatch,
                        ins=ins.op_str,
                        ring4_at=r['ring4_at'],
                        all_sites=chosen_c['sites']))
        print('%s %-48s vt=%s slot=%d col=%s off=%d site=%s func=%s out=%s checks=%s cls=%s' % (
            entry, r['name'][:48], chosen_c['vt'], slot, chosen_c['col'], off,
            site, func_s, outside, ''.join('T' if x else 'F' for x in [c1,c2,c3,c4,c5,c6]),
            clsmatch))

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('wrote', OUT)
    print('ALL OK:', all(o['outside'] and all(o['checks']) and o['clsmatch'] for o in out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
