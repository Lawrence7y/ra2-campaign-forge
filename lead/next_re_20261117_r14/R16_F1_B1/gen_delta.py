# -*- coding: utf-8 -*-
"""
R16_F1_B1 — 字段独立复核 + 生成 fields.tsv / delta.tsv（F1 缺口 B1，18 行）。

回 gamemd.exe 只读复算 6 项字节：
  u32(vt+slot*4)==entry ; u32(vt-4)==COL ; u32(COL+4)==offset ;
  u32(COL+12)==TD ; cstr(TD+8)==mangled ; capstone imm32@site==vt
另核 rtti_class==row_class、装表点体外、site 与 ring4_at 主站点一致。
披露指针节号 §12.6（不是 §12.4）。只写本目录；coverage.tsv / gamemd.exe 只读。
fields.tsv 14 列（含 same_source，照卡面 §5.2）。
"""
import os, sys, json, re, hashlib, collections
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
SCAN = os.path.join(HERE, 'scan_raw.json')
AUDIT = os.path.join(R14, 'R16_PROBE_4GAP', 'scan_F1_audit.tsv')
FIELDS = os.path.join(HERE, 'fields.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')
VJSON = os.path.join(HERE, 'verify_summary.json')

DISC = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
        '见 R14_COMMON §12.6 与 PANEL 对应披露）')

FIELD_HEADER = ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                'col_offset\trtti_addr\trtti_mangled\tinstall_site\tinstall_func\t'
                'status(OK|SKIP)\tsame_source\tnote')
DELTA_HEADER = ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                'evidence_path\tn_sources\tconflict')


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def primary_site_from_ring4(ring4):
    """从审计 ring4_at 取主装表点（@前缀 / 'ctor X @Y' / 'ctor X: Y mov' / 裸地址）。"""
    m = re.search(r'@([0-9A-Fa-f]{8})', ring4)
    if m:
        return m.group(1).upper()
    m = re.search(r'ctor\s+[0-9A-Fa-f]{8}:\s*([0-9A-Fa-f]{8})\s+mov', ring4)
    if m:
        return m.group(1).upper()
    m = re.match(r'^\s*([0-9A-Fa-f]{8})\s*$', ring4)
    if m:
        return m.group(1).upper()
    return None


def fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry):
    return ('④ 活表槽位见证：%s::slot%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
            'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
            '④升级句：%s::slot%s（④ 表属类与行名类一致，均为 %s；'
            '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                cls, slot, vt, slot, entry, col, off, td, mg, site, func,
                cls, slot, cls, vt, slot, DISC))


def main():
    cov_before = sha256p(COV)
    cov_bytes = os.path.getsize(COV)
    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    img = probe.Image(EXE)

    # audit same_source
    audit_ss = {}
    with open(AUDIT, encoding='utf-8') as f:
        h = f.readline().split('\t')
        ix = {k: i for i, k in enumerate(h)}
        for ln in f:
            c = ln.rstrip('\r\n').split('\t')
            if len(c) == len(h):
                audit_ss[c[ix['entry']].upper()] = c[ix['same_source']]

    # coverage raw bytes
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

    field_lines, delta_lines, verify, texts = [], [], [], []
    for r in scan['rows']:
        entry = r['entry']
        cls = r['name'].split('::')[0]
        slot = str(r['want_slot'])
        ring4 = r['ring4_at']
        p_site = primary_site_from_ring4(ring4)
        ss = audit_ss.get(entry, '-')

        # 选候选：vt 可解 + slot==name槽 + mangled 精确等于 .?AV<cls>@@ + OUT sites 含 ring4 主站点
        chosen = None
        eligibles = []
        for c in r['candidates']:
            if c['vt'] is None or c['slot'] != r['want_slot']:
                continue
            if c['mangled'] != '.?AV%s@@' % cls:
                continue
            eligibles.append(c)
            out_sites = [s for s in c['sites'] if not s['inside_entry'] and s['func']]
            if p_site and any(s['site'] == p_site for s in out_sites):
                chosen = (c, [s for s in out_sites if s['site'] == p_site][0])
        if chosen is None and eligibles:
            # 退回：取第一个有体外带 func 站点的类一致候选（记 note）
            for c in eligibles:
                out_sites = [s for s in c['sites'] if not s['inside_entry'] and s['func']]
                if out_sites:
                    chosen = (c, out_sites[0])
                    break

        ok = True
        checks = []
        if chosen is None:
            ok = False
            checks.append('no class-consistent candidate with outside install site')
            vt = col = off = td = mg = site = func = '未取得'
            n_same_slot = len([c for c in r['candidates'] if c['slot'] == r['want_slot']])
        else:
            c, s = chosen
            vt, col, off, td, mg = c['vt'], c['col'], str(c['off']), c['td'], c['mangled']
            site, func = s['site'], s['func']
            e_int, vt_int = int(entry, 16), int(vt, 16)
            slot_int = int(slot)
            c1 = img.u32(vt_int + slot_int * 4) == e_int
            checks.append('u32(vt+slot*4)==entry:%s' % c1)
            c2 = img.u32(vt_int - 4) == int(col, 16)
            checks.append('u32(vt-4)==COL:%s' % c2)
            c3 = img.u32(int(col, 16) + 4) == int(off)
            checks.append('u32(COL+4)==offset:%s' % c3)
            c4 = img.u32(int(col, 16) + 12) == int(td, 16)
            checks.append('u32(COL+12)==TD:%s' % c4)
            c5 = img.cstr(int(td, 16) + 8, 256) == mg
            checks.append('cstr(TD+8)==mangled:%s' % c5)
            # c6: capstone decode imm32@site == vt
            import capstone
            si = int(site, 16)
            code = bytes(img.buf[si - img.base:si - img.base + 12])
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.detail = True
            ins = next(md.disasm(code, si))
            imm = (ins.operands[1].imm & 0xFFFFFFFF
                   if ins.mnemonic == 'mov' and len(ins.operands) == 2
                   and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
            c6 = (imm == vt_int)
            checks.append('imm32@site(decoded)==vt:%s (insn=%s)' % (c6, ins.mnemonic))
            # 类一致 + 体外 + site==ring4 主站点
            exact = (mg == '.?AV%s@@' % cls)
            checks.append('rtti_exact_class==row_class:%s' % exact)
            checks.append('install_site_outside_entry:%s' % (not s['inside_entry']))
            checks.append('site==ring4_primary(%s):%s' % (p_site, site == p_site))
            ok = all([c1, c2, c3, c4, c5, c6, exact, not s['inside_entry']])
            n_same_slot = len([c for c in r['candidates'] if c['slot'] == r['want_slot']])

        verify.append(dict(entry=entry, ok=ok, checks=checks))
        note = ('%s 第 %s 槽；vt=%s COL=%s TD=%s；ring4_at 主装表点 %s 解码 imm=%s，'
                '宿主 %s（atlas 命中），体外；slot%d 命中 %d 张表，按「表属类与行名类一致」'
                '+ ring4 站点取 %s；same_source=%s；src=scan_F1_audit.tsv#%s -> '
                'scan_dd(.rdata/.data) -> probe.vtable_start()' % (
                    cls, slot, vt, col, td, site, vt, func,
                    int(slot), n_same_slot, mg, ss, entry))
        src_vt = ('R16_F1_B1/scan_fields.py: scan_F1_audit.tsv#%s ring4_at=%s ; '
                  'scan_dd(.rdata/.data) hit -> probe.vtable_start() -> vt=%s ; '
                  'slot==name(%s)=%s ; site==ring4_primary=%s' % (
                      entry, ring4[:40], vt, r['name'], slot, site))
        status = 'OK' if ok else 'SKIP'
        field_lines.append('\t'.join([
            entry, cls, slot, vt, src_vt, col, off, td, mg, site, func,
            status, ss, note]))

        if ok:
            t = fourth_text(cls, slot, vt, col, off, td, mg, site, func, entry)
            texts.append((entry, t))
            orig = cov.get(entry)
            if orig is None:
                raise RuntimeError('entry %s not in coverage.tsv' % entry)
            new_sem = orig[3] + '；'.encode('utf-8') + t.encode('utf-8')
            outcols = [orig[0], orig[1], orig[2], new_sem,
                       orig[4], orig[5], orig[6], orig[7]]
            for i in (0, 1, 2, 4, 5, 6, 7):
                assert outcols[i] == orig[i], 'col %d changed %s' % (i + 1, entry)
            assert outcols[3].startswith(orig[3]), 'col4 prefix broken %s' % entry
            assert '④ 活表槽位见证' not in orig[3].decode('utf-8', 'replace'), \
                'already has witness %s' % entry
            delta_lines.append(b'\t'.join(outcols).decode('utf-8'))

    with open(FIELDS, 'w', encoding='utf-8', newline='\n') as f:
        f.write(FIELD_HEADER + '\n')
        f.write('\n'.join(field_lines) + '\n')
    with open(DELTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(DELTA_HEADER + '\n')
        f.write('\n'.join(delta_lines) + '\n')

    cov_after = sha256p(COV)
    print('coverage.tsv bytes:', cov_bytes)
    print('coverage sha BEFORE:', cov_before)
    print('coverage sha AFTER :', cov_after, 'unchanged:', cov_before == cov_after)
    print('fields rows:', len(field_lines), 'delta rows:', len(delta_lines))
    print('\nbyte verification:')
    for v in verify:
        print(' ', v['entry'], 'OK' if v['ok'] else 'FAIL', '; '.join(v['checks']))

    print('\nuniqueness:')
    print('  distinct full texts:', len(set(t for _e, t in texts)), '/', len(texts))
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for _e, t in texts]
    print('  distinct entry-normalized:', len(set(norm)), '/', len(norm))
    vt_set = set(); slot_set = set(); cls_set = set(); site_set = set()
    for v, r in zip(verify, scan['rows']):
        if v['ok']:
            ch = None
            for c in r['candidates']:
                if c['vt'] and c['mangled'] == '.?AV%s@@' % r['name'].split('::')[0] \
                        and c['slot'] == r['want_slot']:
                    for s in c['sites']:
                        if not s['inside_entry'] and s['func'] and s['site'] == primary_site_from_ring4(r['ring4_at']):
                            ch = c
                            site_set.add(s['site'])
                            break
                    if ch:
                        break
            vt_set.add(ch['vt'] if ch else 'NA')
            slot_set.add(str(r['want_slot']))
            cls_set.add(r['name'].split('::')[0])
    print('  distinct vt:%d slot:%d class:%d site:%d' % (
        len(vt_set), len(slot_set), len(cls_set), len(site_set)))

    with open(VJSON, 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after, cov_bytes=cov_bytes,
                       n_fields=len(field_lines), n_delta=len(delta_lines),
                       verify=verify,
                       n_distinct_full=len(set(t for _e, t in texts)),
                       n_distinct_norm=len(set(norm)),
                       n_distinct_vt=len(vt_set), n_distinct_slot=len(slot_set),
                       n_distinct_cls=len(cls_set), n_distinct_site=len(site_set),
                       sample=(texts[0][1] if texts else '')),
                  f, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
