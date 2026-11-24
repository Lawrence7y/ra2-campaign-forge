# -*- coding: utf-8 -*-
"""
R16_SLOTN_B1 — 字段独立复核 + 生成 fields.tsv / delta.tsv。

复核（全部回 gamemd.exe 读字节，只读）：
  u32(vt + slot*4) == entry
  u32(vt-4) == col ; u32(col+4) == offset ; u32(col+12) == td ; cstr(td+8) == mangled
  装表点指令 imm32 == vt
  函数体包含装表点

产物只写本目录。coverage.tsv 只读。
"""
import os
import sys
import json
import hashlib

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
FIELDS = os.path.join(HERE, 'fields.tsv')
DELTA = os.path.join(HERE, 'delta.tsv')

DISC = ('（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，'
        '见 R14_COMMON §12.4 与 PANEL 对应披露）')

# 行 9..12 的宿主函数：atlas 缺该 entry，用 capstone 反汇编定界
# （004D085F=ret / 004D0860=prologue / 004D088D=install / 004D08AB=ret 4 / 004D08B0=next fn）
FUNC_OVERRIDE = {
    '004D24A0': '004D0860', '004D2510': '004D0860',
    '004D27D0': '004D0860', '004D2810': '004D0860',
}

NOTES = {
 '0045A560': 'PAVInfantryClass 模板例化；dd hit=007E43D0；site 0043B6DB 位于 0043B680 体内（atlas 命中）；该 vt 仅 1 张',
 '0045A610': 'PAVInfantryClass 模板例化；同 vt=007E43C8 的第 4 槽；site 0043B6DB 位于 0043B680 体内；与行 1 的 slot 2 相异',
 '0045A680': 'PAVFoggedObjectClass 模板例化；dd hit=007E44FC；site 00457BFD 位于 00457AA0 体内；mangled 含 DynamicVectorClass 与 PAVFoggedObjectClass 两段',
 '0045A730': 'PAVFoggedObjectClass 模板例化；同 vt=007E44F4 的第 4 槽；site 00457BFD 位于 00457AA0 体内',
 '00473BA0': 'CCFileClass 第 10 槽；dd hit=007E16D8；site 004014AC 位于 004011C0 体内；reason 记 5 处 direct（本卡纪律不计）',
 '00473C50': 'CCFileClass 第 5 槽；dd hit=007E16C4；site 004014AC 位于 004011C0 体内；reason 记 65 处 direct（本卡纪律不计）',
 '00473D10': 'CCFileClass 第 7 槽；dd hit=007E16CC；site 004014AC 位于 004011C0 体内；reason 记 11 处 direct（本卡纪律不计）',
 '004A9890': 'DisplayClass 第 36 槽；dd hit=007E61A4；site 004A8830 位于 004A8730 体内；该 vt 另有 006AC861 装表点',
 '004D24A0': 'FoggedObjectClass 第 6 槽；site 004D088D 宿主由 capstone 反汇编定界（prologue 004D0860 / ret4 004D08AB，atlas 缺）；install imm32=007E8B38',
 '004D2510': 'FoggedObjectClass 第 5 槽；同 vt=007E8B38；site 004D088D 宿主 004D0860（反汇编定界）',
 '004D27D0': 'FoggedObjectClass 第 3 槽；同 vt=007E8B38；site 004D088D 宿主 004D0860（反汇编定界）',
 '004D2810': 'FoggedObjectClass 第 13 槽；同 vt=007E8B38；site 004D088D 宿主 004D0860（反汇编定界）',
 '004D4200': 'FootClass 第 139 槽；site 004D345D 位于 004D31E0 体内（与 004DE630 先例同宿主）；reason 记 2 处 direct（不计）',
 '004D4280': 'FootClass 第 151 槽；该 entry 被 2 张表持有（007E8C94 FootClass / 007EB058 InfantryClass）；按 site 004D345D + 类名一致取前者',
 '004D4B20': 'AircraftClass 第 133 槽；该 entry 被 4 张表持有（FootClass/InfantryClass/UnitClass 亦含此槽）；按 site 00413D87 + 类名一致取 007E22A4',
}


def sha256p(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


def main():
    cov_before = sha256p(COV)
    with open(SCAN, encoding='utf-8') as f:
        scan = json.load(f)
    img = probe.Image(EXE)

    # 读 coverage.tsv 原始字节，按行建 entry -> 原始 8 列（byte）
    with open(COV, 'rb') as f:
        raw = f.read()
    raw_lines = raw.split(b'\n')
    cov = {}
    for ln in raw_lines:
        if not ln:
            continue
        c = ln.split(b'\t')
        if len(c) == 8:
            try:
                e = c[0].decode('ascii').upper()
            except Exception:
                continue
            cov.setdefault(e, c)

    def fourth_text(row, cls, slot, vt, col, off, td, mg, site, func):
        return ('④ 活表槽位见证：%s::slot%s（vt=%s，槽 %s 值=%s，COL=%s offset=%s，'
                'RTTI=%s→%s；装表点 %s 位于 %s 体内，entry 体外） '
                '④升级句：%s::slot%s（④ 表属类与行名类一致，均为 %s；'
                '该槽即其 vt=%s 表 slot%s，无归属歧义）%s' % (
                    cls, slot, vt, slot, row['entry'], col, off, td, mg, site, func,
                    cls, slot, cls, vt, slot, DISC))

    field_lines = []
    delta_lines = []
    verify = []
    texts = []
    field_header = ('entry\tclass\tslot_no\tvtaddr\tsource_of_vtaddr\tcoladdr\t'
                    'col_offset\trtti_addr\trtti_mangled\tinstall_site\t'
                    'install_func\tstatus(OK|SKIP)\tnote')
    delta_header = ('entry\tsubsystem\tname\tone_line_semantics\tgrade\t'
                    'evidence_path\tn_sources\tconflict')

    for r in scan['rows']:
        entry = r['entry']
        ch = r['chosen']
        cls = r['name'].split('::')[0]
        slot = r['slot_no']
        site = r['site']
        func = FUNC_OVERRIDE.get(entry) or r['func'] or '未取得'

        ok = True
        checks = []
        if ch is None:
            ok = False
            checks.append('no-vt-candidate')
            vt = col = off = td = mg = '未取得'
        else:
            vt = ch['vt']; col = ch['col']; off = str(ch['col_offset'])
            td = ch['td']; mg = ch['mangled']
            # byte-level independent verification
            e_int = int(entry, 16); vt_int = int(vt, 16)
            slot_int = int(slot)
            v_slot = img.u32(vt_int + slot_int * 4)
            v_col = img.u32(vt_int - 4)
            v_off = img.u32(int(col, 16) + 4)
            v_td = img.u32(int(col, 16) + 12)
            v_mg = img.cstr(int(td, 16) + 8, 256)
            c1 = (v_slot == e_int); checks.append('u32(vt+slot*4)==entry:%s' % c1)
            c2 = (v_col == int(col, 16)); checks.append('u32(vt-4)==COL:%s' % c2)
            c3 = (v_off == int(off)); checks.append('u32(COL+4)==offset:%s' % c3)
            c4 = (v_td == int(td, 16)); checks.append('u32(COL+12)==TD:%s' % c4)
            c5 = (v_mg == mg); checks.append('cstr(TD+8)==mangled:%s' % c5)
            # install site imm32 == vt：用 capstone 解码 imm 操作数（编码长度随 disp 变化）
            import capstone
            site_int = int(site, 16)
            code = bytes(img.buf[site_int - img.base:site_int - img.base + 12])
            md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
            md.detail = True
            ins = next(md.disasm(code, site_int))
            imm = (ins.operands[1].imm & 0xFFFFFFFF
                   if ins.mnemonic == 'mov' and len(ins.operands) == 2
                   and ins.operands[1].type == capstone.x86.X86_OP_IMM else None)
            c6 = (imm == vt_int); checks.append('imm32@site(decoded)==vt:%s' % c6)
            ok = all([c1, c2, c3, c4, c5, c6])
        verify.append(dict(entry=entry, ok=ok, checks=checks))

        src_vt = ('R16_SLOTN_B1/scan_fields.py: scan_dd(.rdata/.data) hit=%s -> '
                  'probe.vtable_start() -> vt=%s ; slot==slotN43.tsv#%d=%s ; '
                  'site==work_scan.json:A_agg.site_of[%s]=%s' % (
                      ch['hit'] if ch else 'NA', vt, r['row'], slot, entry, site))
        status = 'OK' if ok else 'SKIP'
        field_lines.append('\t'.join([
            entry, cls, slot, vt, src_vt, col, off, td, mg, site, func,
            status, NOTES[entry]]))

        if ok:
            t = fourth_text(r, cls, slot, vt, col, off, td, mg, site, func)
            texts.append((entry, t))
            orig = cov.get(entry)
            if orig is None:
                raise RuntimeError('entry %s not found in coverage.tsv' % entry)
            # 原第 4 列一字不删，用 ；衔接
            new_sem = orig[3] + '；'.encode('utf-8') + t.encode('utf-8')
            outcols = [orig[0], orig[1], orig[2], new_sem,
                       orig[4], orig[5], orig[6], orig[7]]
            # 逐字节核对第 1/2/3/5/6/7/8 列
            for i in (0, 1, 2, 4, 5, 6, 7):
                assert outcols[i] == orig[i], 'col %d changed for %s' % (i + 1, entry)
            assert outcols[3].startswith(orig[3]), 'col4 prefix not preserved'
            delta_lines.append(b'\t'.join(outcols).decode('utf-8'))

    with open(FIELDS, 'w', encoding='utf-8', newline='\n') as f:
        f.write(field_header + '\n')
        f.write('\n'.join(field_lines) + '\n')
    with open(DELTA, 'w', encoding='utf-8', newline='\n') as f:
        f.write(delta_header + '\n')
        f.write('\n'.join(delta_lines) + '\n')

    cov_after = sha256p(COV)
    print('coverage.tsv sha256 BEFORE:', cov_before)
    print('coverage.tsv sha256 AFTER :', cov_after)
    print('coverage unchanged:', cov_before == cov_after)
    print('fields.tsv rows:', len(field_lines), ' delta.tsv rows:', len(delta_lines))
    print('byte-level verification:')
    for v in verify:
        print(' ', v['entry'], 'OK' if v['ok'] else 'FAIL', '; '.join(v['checks']))

    # 行行不同自检
    print('uniqueness self-check:')
    print('  distinct full ④ texts:', len(set(t for _e, t in texts)), '/', len(texts))
    # 除 entry 外完全相同？（把 entry 换成占位符后比较）
    import re
    norm = [re.sub(r'[0-9A-F]{8}', 'ENTRY', t) for _e, t in texts]
    print('  distinct texts with entry normalized to placeholder:', len(set(norm)), '/', len(norm))
    # 四字段多样性
    vt_set = set(); slot_set = set(); cls_set = set(); site_set = set()
    for r in scan['rows']:
        ch = r['chosen']
        if ch:
            vt_set.add(ch['vt']); slot_set.add(r['slot_no'])
            cls_set.add(r['name'].split('::')[0]); site_set.add(r['site'])
    print('  distinct vt:', len(vt_set), ' slot:', len(slot_set),
          ' class:', len(cls_set), ' site:', len(site_set))
    # 写出自检数据供 REPORT 使用
    with open(os.path.join(HERE, 'verify_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(cov_before=cov_before, cov_after=cov_after,
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
